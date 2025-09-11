from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, send_file
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime
from sqlalchemy import text
import os
from werkzeug.utils import secure_filename
import uuid
from app.utils.db import safe_commit
from app.utils.backup import create_backup, restore_backup
import threading
import time

admin_bp = Blueprint('admin', __name__)

# In-memory restore progress tracking (simple, per-process)
RESTORE_PROGRESS = {}

# Allowed file extensions for logos
ALLOWED_LOGO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(_('Administrator access required'), 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_logo_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_LOGO_EXTENSIONS

def get_upload_folder():
    """Get the upload folder path for logos"""
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get system statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    total_entries = TimeEntry.query.filter(TimeEntry.end_time.isnot(None)).count()
    active_timers = TimeEntry.query.filter_by(end_time=None).count()
    
    # Get recent activity
    recent_entries = TimeEntry.query.filter(
        TimeEntry.end_time.isnot(None)
    ).order_by(
        TimeEntry.created_at.desc()
    ).limit(10).all()
    
    # Build stats object expected by the template
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_entries': total_entries,
        'total_hours': TimeEntry.get_total_hours_for_period(),
        'billable_hours': TimeEntry.get_total_hours_for_period(billable_only=True),
        'last_backup': None
    }
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        active_timers=active_timers,
        recent_entries=recent_entries
    )

@admin_bp.route('/admin/users')
@login_required
@admin_required
def list_users():
    """List all users"""
    users = User.query.order_by(User.username).all()
    
    # Build stats for users page
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(role='admin').count(),
        'total_hours': TimeEntry.get_total_hours_for_period()
    }
    
    return render_template('admin/users.html', users=users, stats=stats)

@admin_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        role = request.form.get('role', 'user')
        
        if not username:
            flash('Username is required', 'error')
            return render_template('admin/user_form.html', user=None)
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('User already exists', 'error')
            return render_template('admin/user_form.html', user=None)
        
        # Create user
        user = User(username=username, role=role)
        db.session.add(user)
        if not safe_commit('admin_create_user', {'username': username}):
            flash('Could not create user due to a database error. Please check server logs.', 'error')
            return render_template('admin/user_form.html', user=None)
        
        flash(f'User "{username}" created successfully', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/user_form.html', user=None)

@admin_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        
        if not username:
            flash('Username is required', 'error')
            return render_template('admin/user_form.html', user=user)
        
        # Check if username is already taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists', 'error')
            return render_template('admin/user_form.html', user=user)
        
        # Update user
        user.username = username
        user.role = role
        user.is_active = is_active
        if not safe_commit('admin_edit_user', {'user_id': user.id}):
            flash('Could not update user due to a database error. Please check server logs.', 'error')
            return render_template('admin/user_form.html', user=user)
        
        flash(f'User "{username}" updated successfully', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/user_form.html', user=user)

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting the last admin
    if user.is_admin:
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('Cannot delete the last administrator', 'error')
            return redirect(url_for('admin.list_users'))
    
    # Don't allow deleting users with time entries
    if user.time_entries.count() > 0:
        flash('Cannot delete user with existing time entries', 'error')
        return redirect(url_for('admin.list_users'))
    
    username = user.username
    db.session.delete(user)
    if not safe_commit('admin_delete_user', {'user_id': user.id}):
        flash('Could not delete user due to a database error. Please check server logs.', 'error')
        return redirect(url_for('admin.list_users'))
    
    flash(f'User "{username}" deleted successfully', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Manage system settings"""
    settings_obj = Settings.get_settings()
    
    if request.method == 'POST':
        # Validate timezone
        timezone = request.form.get('timezone', 'Europe/Rome')
        try:
            import pytz
            pytz.timezone(timezone)  # This will raise an exception if timezone is invalid
        except pytz.exceptions.UnknownTimeZoneError:
            flash(f'Invalid timezone: {timezone}', 'error')
            return render_template('admin/settings.html', settings=settings_obj)
        
        # Update basic settings
        settings_obj.timezone = timezone
        settings_obj.currency = request.form.get('currency', 'EUR')
        settings_obj.rounding_minutes = int(request.form.get('rounding_minutes', 1))
        settings_obj.single_active_timer = request.form.get('single_active_timer') == 'on'
        settings_obj.allow_self_register = request.form.get('allow_self_register') == 'on'
        settings_obj.idle_timeout_minutes = int(request.form.get('idle_timeout_minutes', 30))
        settings_obj.backup_retention_days = int(request.form.get('backup_retention_days', 30))
        settings_obj.backup_time = request.form.get('backup_time', '02:00')
        settings_obj.export_delimiter = request.form.get('export_delimiter', ',')
        
        # Update company branding settings
        settings_obj.company_name = request.form.get('company_name', 'Your Company Name')
        settings_obj.company_address = request.form.get('company_address', 'Your Company Address')
        settings_obj.company_email = request.form.get('company_email', 'info@yourcompany.com')
        settings_obj.company_phone = request.form.get('company_phone', '+1 (555) 123-4567')
        settings_obj.company_website = request.form.get('company_website', 'www.yourcompany.com')
        settings_obj.company_tax_id = request.form.get('company_tax_id', '')
        settings_obj.company_bank_info = request.form.get('company_bank_info', '')
        
        # Update invoice defaults
        settings_obj.invoice_prefix = request.form.get('invoice_prefix', 'INV')
        settings_obj.invoice_start_number = int(request.form.get('invoice_start_number', 1000))
        settings_obj.invoice_terms = request.form.get('invoice_terms', 'Payment is due within 30 days of invoice date.')
        settings_obj.invoice_notes = request.form.get('invoice_notes', 'Thank you for your business!')
        
        # Update privacy and analytics settings
        settings_obj.allow_analytics = request.form.get('allow_analytics') == 'on'
        
        if not safe_commit('admin_update_settings'):
            flash('Could not update settings due to a database error. Please check server logs.', 'error')
            return render_template('admin/settings.html', settings=settings_obj)
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=settings_obj)

@admin_bp.route('/admin/upload-logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Upload company logo"""
    if 'logo' not in request.files:
        flash('No logo file selected', 'error')
        return redirect(url_for('admin.settings'))
    
    file = request.files['logo']
    if file.filename == '':
        flash('No logo file selected', 'error')
        return redirect(url_for('admin.settings'))
    
    if file and allowed_logo_file(file.filename):
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"company_logo_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Save file
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Update settings
        settings_obj = Settings.get_settings()
        
        # Remove old logo if it exists
        if settings_obj.company_logo_filename:
            old_logo_path = os.path.join(upload_folder, settings_obj.company_logo_filename)
            if os.path.exists(old_logo_path):
                try:
                    os.remove(old_logo_path)
                except OSError:
                    pass  # Ignore errors when removing old file
        
        settings_obj.company_logo_filename = unique_filename
        if not safe_commit('admin_upload_logo'):
            flash('Could not save logo due to a database error. Please check server logs.', 'error')
            return redirect(url_for('admin.settings'))
        
        flash('Company logo uploaded successfully', 'success')
    else:
        flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, SVG, WEBP', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/remove-logo', methods=['POST'])
@login_required
@admin_required
def remove_logo():
    """Remove company logo"""
    settings_obj = Settings.get_settings()
    
    if settings_obj.company_logo_filename:
        # Remove file from filesystem
        logo_path = settings_obj.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                os.remove(logo_path)
            except OSError:
                pass  # Ignore errors when removing file
        
        # Clear filename from database
        settings_obj.company_logo_filename = ''
        if not safe_commit('admin_remove_logo'):
            flash('Could not remove logo due to a database error. Please check server logs.', 'error')
            return redirect(url_for('admin.settings'))
        flash('Company logo removed successfully', 'success')
    else:
        flash('No logo to remove', 'info')
    
    return redirect(url_for('admin.settings'))

# Public route to serve uploaded logos from the static uploads directory
@admin_bp.route('/uploads/logos/<path:filename>')
def serve_uploaded_logo(filename):
    """Serve company logo files stored under static/uploads/logos.
    This route is intentionally public so logos render on unauthenticated pages
    like the login screen and in favicons.
    """
    upload_folder = get_upload_folder()
    return send_from_directory(upload_folder, filename)

@admin_bp.route('/admin/backup', methods=['GET'])
@login_required
@admin_required
def backup():
    """Create manual backup and return the archive for download."""
    try:
        archive_path = create_backup(current_app)
        if not archive_path or not os.path.exists(archive_path):
            flash('Backup failed: archive not created', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        # Stream file to user
        return send_file(archive_path, as_attachment=True)
    except Exception as e:
        flash(f'Backup failed: {e}', 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/restore', methods=['GET', 'POST'])
@login_required
@admin_required
def restore():
    """Restore from an uploaded backup archive."""
    if request.method == 'POST':
        if 'backup_file' not in request.files or request.files['backup_file'].filename == '':
            flash('No backup file uploaded', 'error')
            return redirect(url_for('admin.restore'))
        file = request.files['backup_file']
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.zip'):
            flash('Invalid file type. Please upload a .zip backup archive.', 'error')
            return redirect(url_for('admin.restore'))
        # Save temporarily under project backups
        backups_dir = os.path.join(os.path.abspath(os.path.join(current_app.root_path, '..')), 'backups')
        os.makedirs(backups_dir, exist_ok=True)
        temp_path = os.path.join(backups_dir, f"restore_{uuid.uuid4().hex[:8]}_{filename}")
        file.save(temp_path)

        # Initialize progress state
        token = uuid.uuid4().hex[:8]
        RESTORE_PROGRESS[token] = {'status': 'starting', 'percent': 0, 'message': 'Queued'}

        def progress_cb(label, percent):
            RESTORE_PROGRESS[token] = {'status': 'running', 'percent': int(percent), 'message': label}

        # Capture the real Flask app object for use in a background thread
        app_obj = current_app._get_current_object()

        def _do_restore():
            try:
                RESTORE_PROGRESS[token] = {'status': 'running', 'percent': 5, 'message': 'Starting restore'}
                success, message = restore_backup(app_obj, temp_path, progress_callback=progress_cb)
                RESTORE_PROGRESS[token] = {
                    'status': 'done' if success else 'error',
                    'percent': 100 if success else RESTORE_PROGRESS[token].get('percent', 0),
                    'message': message
                }
            except Exception as e:
                RESTORE_PROGRESS[token] = {'status': 'error', 'percent': RESTORE_PROGRESS[token].get('percent', 0), 'message': str(e)}
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        # Run restore in background to keep request responsive
        t = threading.Thread(target=_do_restore, daemon=True)
        t.start()

        flash('Restore started. You can monitor progress on this page.', 'info')
        return redirect(url_for('admin.restore', token=token))
    # GET
    token = request.args.get('token')
    progress = RESTORE_PROGRESS.get(token) if token else None
    return render_template('admin/restore.html', progress=progress, token=token)

@admin_bp.route('/admin/system')
@login_required
@admin_required
def system_info():
    """Show system information"""
    # Get system statistics
    total_users = User.query.count()
    total_projects = Project.query.count()
    total_entries = TimeEntry.query.count()
    active_timers = TimeEntry.query.filter_by(end_time=None).count()
    
    # Get database size
    db_size_bytes = 0
    try:
        engine = db.session.bind
        dialect = engine.dialect.name if engine else ''
        if dialect == 'sqlite':
            db_size_bytes = db.session.execute(
                text('SELECT page_count * page_size AS size FROM pragma_page_count(), pragma_page_size()')
            ).scalar() or 0
        elif dialect in ('postgresql', 'postgres'):
            db_size_bytes = db.session.execute(
                text('SELECT pg_database_size(current_database())')
            ).scalar() or 0
        else:
            db_size_bytes = 0
    except Exception:
        db_size_bytes = 0
    db_size_mb = round(db_size_bytes / (1024 * 1024), 2) if db_size_bytes else 0
    
    return render_template('admin/system_info.html',
                         total_users=total_users,
                         total_projects=total_projects,
                         total_entries=total_entries,
                         active_timers=active_timers,
                         db_size_mb=db_size_mb)

@admin_bp.route('/license-status')
@login_required
@admin_required
def license_status():
    """Show license server client status"""
    try:
        from app.utils.license_server import get_license_client
        client = get_license_client()
        if client:
            status = client.get_status()
            settings = Settings.get_settings()
            return render_template('admin/license_status.html', status=status, settings=settings)
        else:
            flash('License server client not initialized', 'warning')
            return redirect(url_for('admin.dashboard'))
    except Exception as e:
        flash(f'Error getting license status: {e}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/license-test')
@login_required
@admin_required
def license_test():
    """Test license server communication"""
    try:
        from app.utils.license_server import get_license_client, send_usage_event
        client = get_license_client()
        if client:
            # Test server health
            server_healthy = client.check_server_health()
            
            # Test usage event
            usage_sent = send_usage_event("admin_test", {"admin": current_user.username})
            
            flash(f'Server Health: {"✓ Healthy" if server_healthy else "✗ Not Responding"}, Usage Event: {"✓ Sent" if usage_sent else "✗ Failed"}', 'info')
        else:
            flash('License server client not initialized', 'warning')
    except Exception as e:
        flash(f'Error testing license server: {e}', 'error')
    
    return redirect(url_for('admin.license_status'))

@admin_bp.route('/license-restart')
@login_required
@admin_required
def license_restart():
    """Restart the license server client"""
    try:
        from app.utils.license_server import get_license_client, start_license_client
        client = get_license_client()
        if client:
            if start_license_client():
                flash('License server client restarted successfully', 'success')
            else:
                flash('Failed to restart license server client', 'error')
        else:
            flash('License server client not initialized', 'warning')
    except Exception as e:
        flash(f'Error restarting license server client: {e}', 'error')
    
    return redirect(url_for('admin.license_status'))
