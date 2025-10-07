"""
Routes for organization management.

Handles:
- Organization CRUD operations
- Membership management
- Organization switching
- User invitations
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Organization, Membership, User
from app.utils.tenancy import (
    get_current_organization, get_current_organization_id,
    switch_organization, require_organization_access,
    get_user_organizations, user_is_organization_admin
)
from app.utils.seat_sync import seat_sync_service, check_can_add_member
from app.utils.provisioning_service import provisioning_service

organizations_bp = Blueprint('organizations', __name__, url_prefix='/organizations')


@organizations_bp.route('/')
@login_required
def index():
    """List all organizations the current user belongs to."""
    memberships = Membership.get_user_active_memberships(current_user.id)
    current_org_id = get_current_organization_id()
    
    organizations = [
        {
            'id': m.organization.id,
            'name': m.organization.name,
            'slug': m.organization.slug,
            'role': m.role,
            'member_count': m.organization.member_count,
            'project_count': m.organization.project_count,
            'is_current': m.organization.id == current_org_id,
            'is_admin': m.is_admin
        }
        for m in memberships
    ]
    
    return render_template('organizations/index.html', organizations=organizations)


@organizations_bp.route('/<int:org_id>')
@login_required
@require_organization_access()
def detail(org_id):
    """View organization details."""
    org = Organization.query.get_or_404(org_id)
    
    # Check if user is admin of this org
    is_admin = user_is_organization_admin(current_user.id, org_id)
    
    # Get membership info
    membership = Membership.find_membership(current_user.id, org_id)
    
    # Get members if admin
    members = None
    if is_admin:
        members = org.get_members()
    
    return render_template(
        'organizations/detail.html',
        organization=org,
        membership=membership,
        members=members,
        is_admin=is_admin
    )


@organizations_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new organization with optional trial provisioning."""
    if request.method == 'POST':
        try:
            # Check if user wants to start with a trial
            start_trial = request.form.get('start_trial', 'true').lower() == 'true'
            
            org = Organization(
                name=request.form['name'],
                slug=request.form.get('slug'),  # Optional, will be auto-generated
                contact_email=request.form.get('contact_email', current_user.email),
                subscription_plan='trial' if start_trial else 'free'
            )
            
            db.session.add(org)
            db.session.flush()  # Get org.id
            
            # Create membership for creator as admin
            membership = Membership(
                user_id=current_user.id,
                organization_id=org.id,
                role='admin',
                status='active'
            )
            
            db.session.add(membership)
            db.session.commit()
            
            # AUTOMATED PROVISIONING: If trial, provision immediately
            if start_trial:
                try:
                    provisioning_result = provisioning_service.provision_trial_organization(
                        organization=org,
                        admin_user=current_user
                    )
                    
                    if provisioning_result.get('success'):
                        flash(f'🎉 Organization "{org.name}" created successfully with a free trial!', 'success')
                        # Redirect to welcome page for new trial users
                        return redirect(url_for('onboarding.welcome'))
                    else:
                        flash(f'Organization "{org.name}" created, but provisioning had issues.', 'warning')
                except Exception as prov_error:
                    # Log the provisioning error but don't fail the org creation
                    from flask import current_app
                    current_app.logger.error(f"Provisioning error for {org.name}: {prov_error}")
                    flash(f'Organization "{org.name}" created successfully!', 'success')
            else:
                flash(f'Organization "{org.name}" created successfully!', 'success')
            
            return redirect(url_for('organizations.detail', org_id=org.id))
            
        except IntegrityError as e:
            db.session.rollback()
            flash('An organization with that name or slug already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating organization: {str(e)}', 'danger')
    
    return render_template('organizations/create.html')


@organizations_bp.route('/<int:org_id>/edit', methods=['GET', 'POST'])
@login_required
@require_organization_access(admin_only=True)
def edit(org_id):
    """Edit organization settings (admin only)."""
    org = Organization.query.get_or_404(org_id)
    
    if request.method == 'POST':
        try:
            org.name = request.form['name']
            org.contact_email = request.form.get('contact_email')
            org.contact_phone = request.form.get('contact_phone')
            org.billing_email = request.form.get('billing_email')
            org.timezone = request.form.get('timezone', 'UTC')
            org.currency = request.form.get('currency', 'EUR')
            
            db.session.commit()
            
            flash('Organization settings updated successfully!', 'success')
            return redirect(url_for('organizations.detail', org_id=org_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating organization: {str(e)}', 'danger')
    
    return render_template('organizations/edit.html', organization=org)


@organizations_bp.route('/<int:org_id>/switch', methods=['POST'])
@login_required
def switch(org_id):
    """Switch to a different organization."""
    try:
        org = switch_organization(org_id)
        flash(f'Switched to organization: {org.name}', 'success')
        return redirect(request.referrer or url_for('main.index'))
        
    except PermissionError:
        flash('You do not have access to that organization.', 'danger')
        return redirect(url_for('organizations.index'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('organizations.index'))


@organizations_bp.route('/<int:org_id>/members')
@login_required
@require_organization_access(admin_only=True)
def members(org_id):
    """List organization members (admin only)."""
    org = Organization.query.get_or_404(org_id)
    members = org.get_members()
    
    return render_template(
        'organizations/members.html',
        organization=org,
        members=members
    )


@organizations_bp.route('/<int:org_id>/members/invite', methods=['GET', 'POST'])
@login_required
@require_organization_access(admin_only=True)
def invite_member(org_id):
    """Invite a user to the organization (admin only)."""
    org = Organization.query.get_or_404(org_id)
    
    if request.method == 'POST':
        try:
            email = request.form['email']
            role = request.form.get('role', 'member')
            
            # Check if organization can add more members
            seat_check = check_can_add_member(org_id)
            if not seat_check['can_add']:
                flash(seat_check['message'], 'warning')
                return redirect(url_for('organizations.members', org_id=org_id))
            
            # Find or create user
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user with invitation
                username = email.split('@')[0]
                # Ensure unique username
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(username=username, email=email, role='user')
                user.is_active = False  # Inactive until they accept
                db.session.add(user)
                db.session.flush()
            
            # Check if already a member
            existing = Membership.find_membership(user.id, org_id)
            if existing and existing.status == 'active':
                flash('User is already a member of this organization.', 'warning')
                return redirect(url_for('organizations.members', org_id=org_id))
            
            # Create membership with invitation
            membership = Membership(
                user_id=user.id,
                organization_id=org_id,
                role=role,
                status='invited',
                invited_by=current_user.id
            )
            
            db.session.add(membership)
            db.session.commit()
            
            # Note: Seat sync will happen when invitation is accepted
            # No need to sync here since invited members don't count until active
            
            # TODO: Send invitation email with token
            # send_invitation_email(user.email, membership.invitation_token)
            
            flash(f'Invitation sent to {email}!', 'success')
            return redirect(url_for('organizations.members', org_id=org_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error inviting user: {str(e)}', 'danger')
    
    return render_template('organizations/invite.html', organization=org)


@organizations_bp.route('/<int:org_id>/members/<int:user_id>/role', methods=['POST'])
@login_required
@require_organization_access(admin_only=True)
def change_member_role(org_id, user_id):
    """Change a member's role (admin only)."""
    org = Organization.query.get_or_404(org_id)
    membership = Membership.find_membership(user_id, org_id)
    
    if not membership:
        flash('Member not found.', 'danger')
        return redirect(url_for('organizations.members', org_id=org_id))
    
    # Don't allow changing own role
    if user_id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('organizations.members', org_id=org_id))
    
    try:
        new_role = request.form['role']
        membership.change_role(new_role)
        
        flash(f'Role updated to {new_role}.', 'success')
    except Exception as e:
        flash(f'Error updating role: {str(e)}', 'danger')
    
    return redirect(url_for('organizations.members', org_id=org_id))


@organizations_bp.route('/<int:org_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
@require_organization_access(admin_only=True)
def remove_member(org_id, user_id):
    """Remove a member from the organization (admin only)."""
    org = Organization.query.get_or_404(org_id)
    membership = Membership.find_membership(user_id, org_id)
    
    if not membership:
        flash('Member not found.', 'danger')
        return redirect(url_for('organizations.members', org_id=org_id))
    
    # Don't allow removing self
    if user_id == current_user.id:
        flash('You cannot remove yourself from the organization.', 'warning')
        return redirect(url_for('organizations.members', org_id=org_id))
    
    # Check if this is the last admin
    if membership.is_admin and org.admin_count <= 1:
        flash('Cannot remove the last admin from the organization.', 'danger')
        return redirect(url_for('organizations.members', org_id=org_id))
    
    try:
        user = membership.user
        membership.remove()
        
        # Sync seats with Stripe
        sync_result = seat_sync_service.on_member_removed(org, user)
        if not sync_result['success']:
            flash(f"Member removed but seat sync failed: {sync_result['message']}", 'warning')
        else:
            flash('Member removed from organization.', 'success')
    except Exception as e:
        flash(f'Error removing member: {str(e)}', 'danger')
    
    return redirect(url_for('organizations.members', org_id=org_id))


# ========================================
# API Endpoints
# ========================================

@organizations_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """API: List user's organizations."""
    memberships = Membership.get_user_active_memberships(current_user.id)
    current_org_id = get_current_organization_id()
    
    organizations = [
        {
            **m.organization.to_dict(include_stats=True),
            'role': m.role,
            'is_current': m.organization.id == current_org_id
        }
        for m in memberships
    ]
    
    return jsonify({'organizations': organizations})


@organizations_bp.route('/api/<int:org_id>', methods=['GET'])
@login_required
@require_organization_access()
def api_detail(org_id):
    """API: Get organization details."""
    org = Organization.query.get_or_404(org_id)
    membership = Membership.find_membership(current_user.id, org_id)
    
    data = org.to_dict(include_stats=True)
    data['current_user_role'] = membership.role if membership else None
    
    return jsonify(data)


@organizations_bp.route('/api/<int:org_id>/switch', methods=['POST'])
@login_required
def api_switch(org_id):
    """API: Switch to different organization."""
    try:
        org = switch_organization(org_id)
        return jsonify({
            'success': True,
            'organization': org.to_dict()
        })
    except (PermissionError, ValueError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 403


@organizations_bp.route('/api/<int:org_id>/members', methods=['GET'])
@login_required
@require_organization_access(admin_only=True)
def api_members(org_id):
    """API: List organization members."""
    org = Organization.query.get_or_404(org_id)
    members = org.get_members()
    
    return jsonify({
        'members': [m.to_dict(include_user=True) for m in members]
    })

