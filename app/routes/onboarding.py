"""
Onboarding Routes

Handles onboarding checklist display, task completion tracking, and
user guidance for new organizations.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.onboarding_checklist import OnboardingChecklist
from app.models.membership import Membership
from app.utils.tenancy import require_organization_access, get_current_organization


bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')


@bp.route('/')
@bp.route('/checklist')
@login_required
@require_organization_access()
def checklist():
    """Display onboarding checklist for current organization."""
    organization = get_current_organization()
    
    if not organization:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get or create checklist
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    
    return render_template(
        'onboarding/checklist.html',
        organization=organization,
        checklist=checklist_data,
        tasks=checklist_data.get_tasks_with_status()
    )


@bp.route('/api/checklist', methods=['GET'])
@login_required
@require_organization_access()
def get_checklist():
    """Get onboarding checklist data (API endpoint)."""
    organization = get_current_organization()
    
    if not organization:
        return jsonify({'error': 'No organization found'}), 404
    
    # Get or create checklist
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    
    return jsonify(checklist_data.to_dict(include_tasks=True))


@bp.route('/api/checklist/complete/<task_key>', methods=['POST'])
@login_required
@require_organization_access()
def complete_task(task_key):
    """Mark a task as complete (API endpoint).
    
    Args:
        task_key: Key of the task to complete
    """
    organization = get_current_organization()
    
    if not organization:
        return jsonify({'error': 'No organization found'}), 404
    
    # Get checklist
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    
    # Mark task complete
    success = checklist_data.mark_task_complete(task_key)
    
    if not success:
        return jsonify({'error': f'Invalid task key: {task_key}'}), 400
    
    return jsonify({
        'success': True,
        'task_key': task_key,
        'completion_percentage': checklist_data.completion_percentage,
        'is_complete': checklist_data.is_complete,
        'next_task': checklist_data.get_next_task()
    })


@bp.route('/api/checklist/dismiss', methods=['POST'])
@login_required
@require_organization_access()
def dismiss_checklist():
    """Dismiss the onboarding checklist."""
    organization = get_current_organization()
    
    if not organization:
        return jsonify({'error': 'No organization found'}), 404
    
    # Check if user is admin
    if not Membership.user_is_admin(current_user.id, organization.id):
        return jsonify({'error': 'Only admins can dismiss the checklist'}), 403
    
    # Get checklist and dismiss
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    checklist_data.dismiss()
    
    return jsonify({
        'success': True,
        'dismissed': True
    })


@bp.route('/api/checklist/restore', methods=['POST'])
@login_required
@require_organization_access()
def restore_checklist():
    """Restore a dismissed onboarding checklist."""
    organization = get_current_organization()
    
    if not organization:
        return jsonify({'error': 'No organization found'}), 404
    
    # Check if user is admin
    if not Membership.user_is_admin(current_user.id, organization.id):
        return jsonify({'error': 'Only admins can restore the checklist'}), 403
    
    # Get checklist and restore
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    checklist_data.undismiss()
    
    return jsonify({
        'success': True,
        'dismissed': False
    })


@bp.route('/guide')
@login_required
@require_organization_access()
def guide():
    """Display comprehensive onboarding guide."""
    organization = get_current_organization()
    
    if not organization:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template(
        'onboarding/guide.html',
        organization=organization
    )


@bp.route('/welcome')
@login_required
def welcome():
    """Welcome page for newly created organizations."""
    # Get user's first active organization (newly created)
    memberships = Membership.get_user_active_memberships(current_user.id)
    
    if not memberships:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    organization = memberships[0].organization
    
    # Get checklist
    checklist_data = OnboardingChecklist.get_or_create(organization.id)
    
    return render_template(
        'onboarding/welcome.html',
        organization=organization,
        checklist=checklist_data
    )

