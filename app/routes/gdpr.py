"""
GDPR Routes - Data Export and Deletion
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Organization
from app.utils.gdpr import GDPRExporter, GDPRDeleter
from app.utils.tenancy import get_current_organization_id, require_organization_access
from flask_babel import gettext as _
import json
import io
from datetime import datetime

gdpr_bp = Blueprint('gdpr', __name__, url_prefix='/gdpr')


@gdpr_bp.route('/export', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
@require_organization_access()
def export_data():
    """Export organization data for GDPR compliance"""
    org_id = get_current_organization_id()
    
    if not org_id:
        flash(_('No organization selected.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    organization = Organization.query.get(org_id)
    
    # Check if user is an admin of the organization
    if not organization.is_admin(current_user.id):
        flash(_('You must be an organization admin to export data.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('gdpr/export.html', organization=organization)
    
    # POST - perform export
    export_format = request.form.get('format', 'json')
    
    try:
        data = GDPRExporter.export_organization_data(org_id, format=export_format)
        
        if export_format == 'json':
            # Create JSON file
            buffer = io.BytesIO()
            buffer.write(json.dumps(data, indent=2).encode('utf-8'))
            buffer.seek(0)
            
            filename = f"gdpr_export_{organization.slug}_{datetime.utcnow().strftime('%Y%m%d')}.json"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        else:
            # CSV format
            buffer = io.BytesIO()
            buffer.write(data.encode('utf-8'))
            buffer.seek(0)
            
            filename = f"gdpr_export_{organization.slug}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
    
    except Exception as e:
        current_app.logger.error(f"GDPR export failed: {e}")
        flash(_('Failed to export data. Please try again.'), 'error')
        return redirect(url_for('gdpr.export_data'))


@gdpr_bp.route('/export/user', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def export_user_data():
    """Export current user's data for GDPR compliance"""
    if request.method == 'GET':
        return render_template('gdpr/export_user.html')
    
    # POST - perform export
    export_format = request.form.get('format', 'json')
    
    try:
        data = GDPRExporter.export_user_data(current_user.id, format=export_format)
        
        if export_format == 'json':
            buffer = io.BytesIO()
            buffer.write(json.dumps(data, indent=2).encode('utf-8'))
            buffer.seek(0)
            
            filename = f"user_data_export_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d')}.json"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
        else:
            buffer = io.BytesIO()
            buffer.write(data.encode('utf-8'))
            buffer.seek(0)
            
            filename = f"user_data_export_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
    
    except Exception as e:
        current_app.logger.error(f"User data export failed: {e}")
        flash(_('Failed to export data. Please try again.'), 'error')
        return redirect(url_for('gdpr.export_user_data'))


@gdpr_bp.route('/delete/request', methods=['GET', 'POST'])
@login_required
@limiter.limit("3 per hour")
@require_organization_access()
def request_deletion():
    """Request deletion of organization data"""
    org_id = get_current_organization_id()
    
    if not org_id:
        flash(_('No organization selected.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    organization = Organization.query.get(org_id)
    
    # Check if user is an admin
    if not organization.is_admin(current_user.id):
        flash(_('You must be an organization admin to request deletion.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        grace_days = current_app.config.get('GDPR_DELETION_DELAY_DAYS', 30)
        return render_template('gdpr/delete_request.html', 
                             organization=organization,
                             grace_days=grace_days)
    
    # POST - request deletion
    confirmation = request.form.get('confirmation', '')
    
    if confirmation != organization.name:
        flash(_('Organization name confirmation does not match.'), 'error')
        return redirect(url_for('gdpr.request_deletion'))
    
    try:
        result = GDPRDeleter.request_organization_deletion(org_id, current_user.id)
        
        flash(
            _('Organization deletion has been scheduled for %(date)s. You can cancel this request until that date.',
              date=result['deletion_scheduled_for']),
            'warning'
        )
        
        return redirect(url_for('main.dashboard'))
    
    except PermissionError:
        flash(_('You do not have permission to request deletion.'), 'error')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        current_app.logger.error(f"Deletion request failed: {e}")
        flash(_('Failed to request deletion. Please try again.'), 'error')
        return redirect(url_for('gdpr.request_deletion'))


@gdpr_bp.route('/delete/cancel', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
@require_organization_access()
def cancel_deletion():
    """Cancel a pending deletion request"""
    org_id = get_current_organization_id()
    
    if not org_id:
        flash(_('No organization selected.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        GDPRDeleter.cancel_organization_deletion(org_id, current_user.id)
        flash(_('Organization deletion request has been cancelled.'), 'success')
    
    except PermissionError:
        flash(_('You do not have permission to cancel deletion.'), 'error')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        current_app.logger.error(f"Deletion cancellation failed: {e}")
        flash(_('Failed to cancel deletion. Please try again.'), 'error')
    
    return redirect(url_for('main.dashboard'))


@gdpr_bp.route('/delete/user', methods=['GET', 'POST'])
@login_required
@limiter.limit("2 per hour")
def delete_user_account():
    """Delete current user's account"""
    if request.method == 'GET':
        return render_template('gdpr/delete_user.html')
    
    # POST - delete account
    password = request.form.get('password', '')
    confirmation = request.form.get('confirmation', '')
    
    # Verify password
    if not current_user.check_password(password):
        flash(_('Incorrect password.'), 'error')
        return redirect(url_for('gdpr.delete_user_account'))
    
    # Verify confirmation
    if confirmation != current_user.username:
        flash(_('Username confirmation does not match.'), 'error')
        return redirect(url_for('gdpr.delete_user_account'))
    
    try:
        user_id = current_user.id
        
        # Log out before deleting
        from flask_login import logout_user
        logout_user()
        
        # Delete user data
        GDPRDeleter.delete_user_data(user_id)
        
        flash(_('Your account has been deleted.'), 'info')
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        current_app.logger.error(f"User deletion failed: {e}")
        flash(_('Failed to delete account. Please contact support.'), 'error')
        return redirect(url_for('main.dashboard'))

