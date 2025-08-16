from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Administrator access required', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

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
    total_entries = TimeEntry.query.filter(TimeEntry.end_utc.isnot(None)).count()
    active_timers = TimeEntry.query.filter_by(end_utc=None).count()
    
    # Get recent activity
    recent_entries = TimeEntry.query.filter(
        TimeEntry.end_utc.isnot(None)
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
        db.session.commit()
        
        flash(f'User "{username}" created successfully', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/user_form.html', user=None)

@admin_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        
        # Don't allow deactivating the last admin
        if not is_active and user.is_admin:
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                flash('Cannot deactivate the last administrator', 'error')
                return render_template('admin/user_form.html', user=user)
        
        user.role = role
        user.is_active = is_active
        db.session.commit()
        
        flash(f'User "{user.username}" updated successfully', 'success')
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
    db.session.commit()
    
    flash(f'User "{username}" deleted successfully', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Manage system settings"""
    settings_obj = Settings.get_settings()
    
    if request.method == 'POST':
        # Update settings
        settings_obj.timezone = request.form.get('timezone', 'Europe/Brussels')
        settings_obj.currency = request.form.get('currency', 'EUR')
        settings_obj.rounding_minutes = int(request.form.get('rounding_minutes', 1))
        settings_obj.single_active_timer = request.form.get('single_active_timer') == 'on'
        settings_obj.allow_self_register = request.form.get('allow_self_register') == 'on'
        settings_obj.idle_timeout_minutes = int(request.form.get('idle_timeout_minutes', 30))
        settings_obj.backup_retention_days = int(request.form.get('backup_retention_days', 30))
        settings_obj.backup_time = request.form.get('backup_time', '02:00')
        settings_obj.export_delimiter = request.form.get('export_delimiter', ',')
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=settings_obj)

@admin_bp.route('/admin/backup')
@login_required
@admin_required
def backup():
    """Create manual backup"""
    # This would typically trigger a backup process
    # For now, just show a success message
    flash('Backup process initiated', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/system')
@login_required
@admin_required
def system_info():
    """Show system information"""
    # Get system statistics
    total_users = User.query.count()
    total_projects = Project.query.count()
    total_entries = TimeEntry.query.count()
    active_timers = TimeEntry.query.filter_by(end_utc=None).count()
    
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
