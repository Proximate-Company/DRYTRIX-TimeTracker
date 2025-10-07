from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, send_file, jsonify, render_template_string
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db, limiter
from app.models import User, Project, TimeEntry, Settings, Invoice
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.subscription_event import SubscriptionEvent
from datetime import datetime
from sqlalchemy import text, func, desc
import os
from werkzeug.utils import secure_filename
import uuid
from app.utils.db import safe_commit
from app.utils.backup import create_backup, restore_backup
from app.utils.stripe_service import stripe_service
import threading
import time
from app.utils.tenancy import (
    get_current_organization_id,
    scoped_query,
    require_organization_access
)

admin_bp = Blueprint('admin', __name__)

# In-memory restore progress tracking (simple, per-process)
RESTORE_PROGRESS = {}

# Allowed file extensions for logos
# Avoid SVG due to XSS risk unless sanitized server-side
ALLOWED_LOGO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
@require_organization_access()
def admin_dashboard():
    """Admin dashboard"""
    org_id = get_current_organization_id()
    
    # Get system statistics (scoped to organization)
    total_users = User.query.count()  # Users are global
    active_users = User.query.filter_by(is_active=True).count()
    total_projects = scoped_query(Project).count()
    active_projects = scoped_query(Project).filter_by(status='active').count()
    total_entries = scoped_query(TimeEntry).filter(TimeEntry.end_time.isnot(None)).count()
    active_timers = scoped_query(TimeEntry).filter_by(end_time=None).count()
    
    # Get recent activity (scoped to organization)
    recent_entries = scoped_query(TimeEntry).filter(
        TimeEntry.end_time.isnot(None)
    ).order_by(
        TimeEntry.created_at.desc()
    ).limit(10).all()
    
    # Calculate hours (scoped to organization)
    org_total_seconds = db.session.query(db.func.sum(TimeEntry.duration_seconds)).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None)
    ).scalar() or 0
    org_billable_seconds = db.session.query(db.func.sum(TimeEntry.duration_seconds)).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.billable == True
    ).scalar() or 0
    
    # Build stats object expected by the template
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_entries': total_entries,
        'total_hours': round(org_total_seconds / 3600, 2),
        'billable_hours': round(org_billable_seconds / 3600, 2),
        'last_backup': None
    }
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        active_timers=active_timers,
        recent_entries=recent_entries
    )

# Compatibility alias for code/templates that might reference 'admin.dashboard'
@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard_alias():
    """Alias endpoint so url_for('admin.dashboard') remains valid.

    Some older references may use the endpoint name 'admin.dashboard'.
    Redirect to the canonical admin dashboard endpoint.
    """
    return redirect(url_for('admin.admin_dashboard'))

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


@admin_bp.route('/admin/pdf-layout', methods=['GET', 'POST'])
@limiter.limit("30 per minute", methods=["POST"])  # editor saves
@login_required
@admin_required
def pdf_layout():
    """Edit PDF invoice layout template (HTML and CSS)."""
    settings_obj = Settings.get_settings()
    if request.method == 'POST':
        html_template = request.form.get('invoice_pdf_template_html', '')
        css_template = request.form.get('invoice_pdf_template_css', '')
        settings_obj.invoice_pdf_template_html = html_template
        settings_obj.invoice_pdf_template_css = css_template
        if not safe_commit('admin_update_pdf_layout'):
            from flask_babel import gettext as _
            flash(_('Could not update PDF layout due to a database error.'), 'error')
        else:
            from flask_babel import gettext as _
            flash(_('PDF layout updated successfully'), 'success')
        return redirect(url_for('admin.pdf_layout'))
    # Provide initial defaults to the template if no custom HTML/CSS saved
    initial_html = settings_obj.invoice_pdf_template_html or ''
    initial_css = settings_obj.invoice_pdf_template_css or ''
    try:
        if not initial_html:
            env = current_app.jinja_env
            html_src, _, _ = env.loader.get_source(env, 'invoices/pdf_default.html')
            # Extract body only for editor
            try:
                import re as _re
                m = _re.search(r'<body[^>]*>([\s\S]*?)</body>', html_src, _re.IGNORECASE)
                initial_html = (m.group(1).strip() if m else html_src)
            except Exception:
                pass
        if not initial_css:
            env = current_app.jinja_env
            css_src, _, _ = env.loader.get_source(env, 'invoices/pdf_styles_default.css')
            initial_css = css_src
    except Exception:
        pass
    return render_template('admin/pdf_layout.html', settings=settings_obj, initial_html=initial_html, initial_css=initial_css)


@admin_bp.route('/admin/pdf-layout/reset', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@admin_required
def pdf_layout_reset():
    """Reset PDF layout to defaults (clear custom templates)."""
    settings_obj = Settings.get_settings()
    settings_obj.invoice_pdf_template_html = ''
    settings_obj.invoice_pdf_template_css = ''
    if not safe_commit('admin_reset_pdf_layout'):
        flash(_('Could not reset PDF layout due to a database error.'), 'error')
    else:
        flash(_('PDF layout reset to defaults'), 'success')
    return redirect(url_for('admin.pdf_layout'))


@admin_bp.route('/admin/pdf-layout/default', methods=['GET'])
@login_required
@admin_required
def pdf_layout_default():
    """Return default HTML and CSS template sources for the PDF layout editor."""
    try:
        env = current_app.jinja_env
        # Get raw template sources, not rendered
        html_src, _, _ = env.loader.get_source(env, 'invoices/pdf_default.html')
        # Extract only the body content for GrapesJS
        try:
            import re as _re
            match = _re.search(r'<body[^>]*>([\s\S]*?)</body>', html_src, _re.IGNORECASE)
            if match:
                html_src = match.group(1).strip()
        except Exception:
            pass
    except Exception:
        html_src = '<div class="wrapper"><h1>{{ _(\'INVOICE\') }} {{ invoice.invoice_number }}</h1></div>'
    try:
        css_src, _, _ = env.loader.get_source(env, 'invoices/pdf_styles_default.css')
    except Exception:
        css_src = ''
    return jsonify({
        'html': html_src,
        'css': css_src,
    })


@admin_bp.route('/admin/pdf-layout/preview', methods=['POST'])
@limiter.limit("60 per minute")
@login_required
@admin_required
def pdf_layout_preview():
    """Render a live preview of the provided HTML/CSS using an invoice context."""
    html = request.form.get('html', '')
    css = request.form.get('css', '')
    invoice_id = request.form.get('invoice_id', type=int)
    invoice = None
    if invoice_id:
        invoice = Invoice.query.get(invoice_id)
    if invoice is None:
        invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    settings_obj = Settings.get_settings()
    
    # Provide a minimal mock invoice if none exists to avoid template errors
    from types import SimpleNamespace
    if invoice is None:
        from datetime import date
        invoice = SimpleNamespace(
            invoice_number='0000',
            issue_date=date.today(),
            due_date=date.today(),
            status='draft',
            client_name='Sample Client',
            client_email='',
            client_address='',
            project=SimpleNamespace(name='Sample Project', description=''),
            items=[],
            subtotal=0.0,
            tax_rate=0.0,
            tax_amount=0.0,
            total_amount=0.0,
            notes='',
            terms='',
        )
    # Ensure at least one sample item to avoid undefined 'item' in templates that reference it outside loops
    sample_item = SimpleNamespace(description='Sample item', quantity=1.0, unit_price=0.0, total_amount=0.0, time_entry_ids='')
    try:
        if not getattr(invoice, 'items', None):
            invoice.items = [sample_item]
    except Exception:
        try:
            invoice.items = [sample_item]
        except Exception:
            pass
    # Helper: sanitize Jinja blocks to fix entities/smart quotes inserted by editor
    def _sanitize_jinja_blocks(raw: str) -> str:
        try:
            import re as _re
            import html as _html
            smart_map = {
                '\u201c': '"', '\u201d': '"',  # “ ” -> "
                '\u2018': "'", '\u2019': "'",  # ‘ ’ -> '
                '\u00a0': ' ',                   # nbsp
                '\u200b': '', '\u200c': '', '\u200d': '',  # zero-width
            }
            def _fix_quotes(s: str) -> str:
                for k, v in smart_map.items():
                    s = s.replace(k, v)
                return s
            def _clean(match):
                open_tag = match.group(1)
                inner = match.group(2)
                # Remove any HTML tags GrapesJS may have inserted inside Jinja braces
                inner = _re.sub(r'</?[^>]+?>', '', inner)
                # Decode HTML entities
                inner = _html.unescape(inner)
                # Fix smart quotes and nbsp
                inner = _fix_quotes(inner)
                # Trim excessive whitespace around pipes and parentheses
                inner = _re.sub(r'\s+\|\s+', ' | ', inner)
                inner = _re.sub(r'\(\s+', '(', inner)
                inner = _re.sub(r'\s+\)', ')', inner)
                # Normalize _("...") -> _('...')
                inner = inner.replace('_("', "_('").replace('")', "')")
                return f"{open_tag}{inner}{' }}' if open_tag == '{{ ' else ' %}'}"
            pattern = _re.compile(r'({{\s|{%\s)([\s\S]*?)(?:}}|%})')
            return _re.sub(pattern, _clean, raw)
        except Exception:
            return raw

    sanitized = _sanitize_jinja_blocks(html)

    # Wrap provided HTML with a minimal page and CSS
    try:
        from pathlib import Path as _Path
        # Provide helpers as callables since templates may use function-style helpers
        try:
            from babel.dates import format_date as _babel_format_date
        except Exception:
            _babel_format_date = None
        def _format_date(value, format='medium'):
            try:
                if _babel_format_date:
                    if format == 'full':
                        return _babel_format_date(value, format='full')
                    if format == 'long':
                        return _babel_format_date(value, format='long')
                    if format == 'short':
                        return _babel_format_date(value, format='short')
                    return _babel_format_date(value, format='medium')
                return value.strftime('%Y-%m-%d')
            except Exception:
                return str(value)
        def _format_money(value):
            try:
                return f"{float(value):,.2f} {settings_obj.currency}"
            except Exception:
                return f"{value} {settings_obj.currency}"
        body_html = render_template_string(
            sanitized,
            invoice=invoice,
            settings=settings_obj,
            Path=_Path,
            format_date=_format_date,
            format_money=_format_money,
            item=sample_item,
        )
    except Exception as e:
        body_html = f"<div style='color:red'>Template error: {str(e)}</div>" + sanitized
    page_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <title>PDF Preview</title>
        <style>{css}</style>
    </head>
    <body>{body_html}</body>
    </html>
    """
    return page_html

@admin_bp.route('/admin/upload-logo', methods=['POST'])
@limiter.limit("10 per minute")
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
        
        # Basic server-side validation: verify image type
        try:
            from PIL import Image
            file.stream.seek(0)
            img = Image.open(file.stream)
            img.verify()
            file.stream.seek(0)
        except Exception:
            flash('Invalid image file.', 'error')
            return redirect(url_for('admin.settings'))

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
@limiter.limit("3 per minute", methods=["POST"])  # heavy operation
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

# ========================================
# Customer Management (Organizations)
# ========================================

@admin_bp.route('/admin/customers')
@login_required
@admin_required
def customers():
    """List all organizations (customers) with billing info"""
    # Get all organizations with member counts and subscription info
    organizations = Organization.query.order_by(Organization.created_at.desc()).all()
    
    # Enrich with additional data
    customer_data = []
    for org in organizations:
        # Get active member count
        active_members = Membership.query.filter_by(
            organization_id=org.id,
            status='active'
        ).count()
        
        # Get most recent activity (last login of any member)
        last_activity = db.session.query(func.max(User.last_login)).join(
            Membership, Membership.user_id == User.id
        ).filter(
            Membership.organization_id == org.id,
            Membership.status == 'active'
        ).scalar()
        
        # Get invoice count
        invoice_count = Invoice.query.filter_by(organization_id=org.id).count()
        
        customer_data.append({
            'organization': org,
            'active_members': active_members,
            'last_activity': last_activity,
            'invoice_count': invoice_count,
        })
    
    return render_template(
        'admin/customers.html',
        customer_data=customer_data,
        stripe_configured=stripe_service.is_configured()
    )

@admin_bp.route('/admin/customers/<int:org_id>')
@login_required
@admin_required
def customer_detail(org_id):
    """View detailed information about a specific organization/customer"""
    organization = Organization.query.get_or_404(org_id)
    
    # Get members
    memberships = Membership.query.filter_by(
        organization_id=org_id
    ).join(User).order_by(Membership.created_at.desc()).all()
    
    # Get subscription events
    recent_events = SubscriptionEvent.get_organization_events(
        organization_id=org_id,
        limit=20
    )
    
    # Get Stripe data if configured
    stripe_data = None
    if stripe_service.is_configured() and organization.stripe_customer_id:
        try:
            stripe_data = {
                'invoices': stripe_service.get_invoices(organization, limit=10),
                'upcoming_invoice': stripe_service.get_upcoming_invoice(organization),
                'payment_methods': stripe_service.get_payment_methods(organization),
                'refunds': stripe_service.get_refunds(organization, limit=5),
            }
        except Exception as e:
            current_app.logger.error(f"Error fetching Stripe data: {e}")
            flash('Error loading Stripe data', 'warning')
    
    return render_template(
        'admin/customer_detail.html',
        organization=organization,
        memberships=memberships,
        recent_events=recent_events,
        stripe_data=stripe_data,
        stripe_configured=stripe_service.is_configured()
    )

@admin_bp.route('/admin/customers/<int:org_id>/subscription/quantity', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def update_subscription_quantity(org_id):
    """Update the subscription quantity (seats) for an organization"""
    organization = Organization.query.get_or_404(org_id)
    
    if not organization.stripe_subscription_id:
        flash(_('Organization does not have an active subscription'), 'error')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        new_quantity = int(request.form.get('quantity', 1))
        
        if new_quantity < 1:
            flash(_('Quantity must be at least 1'), 'error')
            return redirect(url_for('admin.customer_detail', org_id=org_id))
        
        # Update via Stripe
        result = stripe_service.update_subscription_quantity(organization, new_quantity)
        
        flash(_(f'Subscription updated: {result["old_quantity"]} → {result["new_quantity"]} seats'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating subscription quantity: {e}")
        flash(_(f'Error updating subscription: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

@admin_bp.route('/admin/customers/<int:org_id>/subscription/cancel', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def cancel_subscription(org_id):
    """Cancel a subscription"""
    organization = Organization.query.get_or_404(org_id)
    
    if not organization.stripe_subscription_id:
        flash(_('Organization does not have an active subscription'), 'error')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        at_period_end = request.form.get('at_period_end', 'true') == 'true'
        
        result = stripe_service.cancel_subscription(organization, at_period_end=at_period_end)
        
        if at_period_end:
            flash(_(f'Subscription will cancel at period end: {result["ends_at"].strftime("%Y-%m-%d")}'), 'success')
        else:
            flash(_('Subscription cancelled immediately'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {e}")
        flash(_(f'Error cancelling subscription: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

@admin_bp.route('/admin/customers/<int:org_id>/subscription/reactivate', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def reactivate_subscription(org_id):
    """Reactivate a subscription that was set to cancel"""
    organization = Organization.query.get_or_404(org_id)
    
    if not organization.stripe_subscription_id:
        flash(_('Organization does not have an active subscription'), 'error')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        result = stripe_service.reactivate_subscription(organization)
        flash(_('Subscription reactivated successfully'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error reactivating subscription: {e}")
        flash(_(f'Error reactivating subscription: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

@admin_bp.route('/admin/customers/<int:org_id>/suspend', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def suspend_organization(org_id):
    """Suspend an organization"""
    organization = Organization.query.get_or_404(org_id)
    
    if organization.is_suspended:
        flash(_('Organization is already suspended'), 'info')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        reason = request.form.get('reason', 'Administrative action')
        organization.suspend(reason=reason)
        
        # Log event
        SubscriptionEvent.create_event(
            event_type='organization.suspended',
            organization_id=organization.id,
            notes=f'Suspended by admin: {reason}'
        )
        
        flash(_('Organization suspended successfully'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error suspending organization: {e}")
        flash(_(f'Error suspending organization: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

@admin_bp.route('/admin/customers/<int:org_id>/activate', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per minute")
def activate_organization(org_id):
    """Activate/reactivate an organization"""
    organization = Organization.query.get_or_404(org_id)
    
    if organization.is_active:
        flash(_('Organization is already active'), 'info')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        organization.activate()
        
        # Log event
        SubscriptionEvent.create_event(
            event_type='organization.activated',
            organization_id=organization.id,
            notes=f'Activated by admin: {current_user.username}'
        )
        
        flash(_('Organization activated successfully'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error activating organization: {e}")
        flash(_(f'Error activating organization: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

@admin_bp.route('/admin/customers/<int:org_id>/invoice/<invoice_id>/refund', methods=['POST'])
@login_required
@admin_required
@limiter.limit("3 per minute")
def create_refund(org_id, invoice_id):
    """Create a refund for an invoice"""
    organization = Organization.query.get_or_404(org_id)
    
    if not stripe_service.is_configured():
        flash(_('Stripe is not configured'), 'error')
        return redirect(url_for('admin.customer_detail', org_id=org_id))
    
    try:
        amount_str = request.form.get('amount')
        reason = request.form.get('reason', 'requested_by_customer')
        
        # Convert amount to cents if provided
        amount_cents = None
        if amount_str:
            try:
                amount_cents = int(float(amount_str) * 100)
            except ValueError:
                flash(_('Invalid amount'), 'error')
                return redirect(url_for('admin.customer_detail', org_id=org_id))
        
        result = stripe_service.create_refund(
            organization=organization,
            invoice_id=invoice_id,
            amount=amount_cents,
            reason=reason
        )
        
        flash(_(f'Refund created: {result["amount"]} {result["currency"]}'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error creating refund: {e}")
        flash(_(f'Error creating refund: {str(e)}'), 'error')
    
    return redirect(url_for('admin.customer_detail', org_id=org_id))

# ========================================
# Billing Reconciliation
# ========================================

@admin_bp.route('/admin/billing/reconciliation')
@login_required
@admin_required
def billing_reconciliation():
    """View billing reconciliation - sync status between Stripe and local DB"""
    if not stripe_service.is_configured():
        flash(_('Stripe is not configured'), 'warning')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        sync_results = stripe_service.check_all_organizations_sync()
        
        return render_template(
            'admin/billing_reconciliation.html',
            sync_results=sync_results
        )
    except Exception as e:
        current_app.logger.error(f"Error checking sync status: {e}")
        flash(_(f'Error checking sync status: {str(e)}'), 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/billing/reconciliation/<int:org_id>/sync', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def sync_organization(org_id):
    """Manually sync an organization with Stripe"""
    organization = Organization.query.get_or_404(org_id)
    
    if not stripe_service.is_configured():
        flash(_('Stripe is not configured'), 'error')
        return redirect(url_for('admin.billing_reconciliation'))
    
    try:
        result = stripe_service.sync_organization_with_stripe(organization)
        
        if result.get('synced'):
            if result.get('discrepancy_count', 0) > 0:
                flash(_(f'Synced with {result["discrepancy_count"]} discrepancy(ies) found and corrected'), 'warning')
            else:
                flash(_('Organization synced successfully - no discrepancies found'), 'success')
        else:
            flash(_(f'Sync failed: {result.get("error")}'), 'error')
    except Exception as e:
        current_app.logger.error(f"Error syncing organization: {e}")
        flash(_(f'Error syncing organization: {str(e)}'), 'error')
    
    return redirect(url_for('admin.billing_reconciliation'))

# ========================================
# Webhook Logs
# ========================================

@admin_bp.route('/admin/webhooks')
@login_required
@admin_required
def webhook_logs():
    """View webhook event logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filter options
    event_type = request.args.get('event_type')
    org_id = request.args.get('org_id', type=int)
    processed = request.args.get('processed')
    
    # Build query
    query = SubscriptionEvent.query
    
    if event_type:
        query = query.filter_by(event_type=event_type)
    
    if org_id:
        query = query.filter_by(organization_id=org_id)
    
    if processed == 'true':
        query = query.filter_by(processed=True)
    elif processed == 'false':
        query = query.filter_by(processed=False)
    
    # Order by most recent first
    query = query.order_by(desc(SubscriptionEvent.created_at))
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    events = pagination.items
    
    # Get unique event types for filter
    event_types = db.session.query(
        SubscriptionEvent.event_type
    ).distinct().order_by(SubscriptionEvent.event_type).all()
    event_types = [et[0] for et in event_types]
    
    # Get organizations for filter
    organizations = Organization.query.order_by(Organization.name).all()
    
    return render_template(
        'admin/webhook_logs.html',
        events=events,
        pagination=pagination,
        event_types=event_types,
        organizations=organizations,
        current_filters={
            'event_type': event_type,
            'org_id': org_id,
            'processed': processed
        }
    )

@admin_bp.route('/admin/webhooks/<int:event_id>')
@login_required
@admin_required
def webhook_detail(event_id):
    """View detailed information about a webhook event"""
    event = SubscriptionEvent.query.get_or_404(event_id)
    
    return render_template(
        'admin/webhook_detail.html',
        event=event
    )

@admin_bp.route('/admin/webhooks/<int:event_id>/reprocess', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per minute")
def reprocess_webhook(event_id):
    """Reprocess a failed webhook event"""
    event = SubscriptionEvent.query.get_or_404(event_id)
    
    if event.processed and not event.processing_error:
        flash(_('Event has already been processed successfully'), 'info')
        return redirect(url_for('admin.webhook_logs'))
    
    try:
        # Mark as unprocessed and reset retry count
        event.processed = False
        event.processing_error = None
        event.retry_count = 0
        db.session.commit()
        
        flash(_('Event queued for reprocessing'), 'success')
    except Exception as e:
        current_app.logger.error(f"Error queueing event for reprocessing: {e}")
        flash(_(f'Error: {str(e)}'), 'error')
    
    return redirect(url_for('admin.webhook_logs'))
