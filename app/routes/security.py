"""
Security Routes - 2FA/MFA Management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models import User
from app.utils.db import safe_commit
from flask_babel import gettext as _
import pyotp
import qrcode
import io
import base64

security_bp = Blueprint('security', __name__, url_prefix='/security')


@security_bp.route('/2fa/setup', methods=['GET'])
@login_required
@limiter.limit("10 per hour")
def setup_2fa():
    """Display 2FA setup page"""
    if current_user.totp_enabled:
        flash(_('Two-factor authentication is already enabled for your account.'), 'info')
        return redirect(url_for('security.manage_2fa'))
    
    # Generate a new TOTP secret
    secret = pyotp.random_base32()
    session['pending_totp_secret'] = secret
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email or current_user.username,
        issuer_name=current_app.config.get('COMPANY_NAME', 'TimeTracker')
    )
    
    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('security/setup_2fa.html',
                         secret=secret,
                         qr_code_data=qr_code_data,
                         provisioning_uri=provisioning_uri)


@security_bp.route('/2fa/verify', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def verify_2fa_setup():
    """Verify and enable 2FA"""
    token = request.form.get('token', '').strip()
    secret = session.get('pending_totp_secret')
    
    if not secret:
        flash(_('2FA setup session expired. Please try again.'), 'error')
        return redirect(url_for('security.setup_2fa'))
    
    if not token:
        flash(_('Please enter the 6-digit code from your authenticator app.'), 'error')
        return redirect(url_for('security.setup_2fa'))
    
    # Verify the token
    totp = pyotp.TOTP(secret)
    if not totp.verify(token, valid_window=1):
        flash(_('Invalid code. Please try again.'), 'error')
        return redirect(url_for('security.setup_2fa'))
    
    # Enable 2FA for the user
    current_user.totp_secret = secret
    current_user.totp_enabled = True
    
    # Generate backup codes
    backup_codes = current_user.generate_backup_codes()
    
    if not safe_commit():
        flash(_('Failed to enable two-factor authentication. Please try again.'), 'error')
        return redirect(url_for('security.setup_2fa'))
    
    # Clear the pending secret from session
    session.pop('pending_totp_secret', None)
    
    flash(_('Two-factor authentication has been enabled successfully!'), 'success')
    
    return render_template('security/backup_codes.html',
                         backup_codes=backup_codes,
                         is_setup=True)


@security_bp.route('/2fa/disable', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def disable_2fa():
    """Disable 2FA for the current user"""
    password = request.form.get('password', '')
    
    # Verify password before disabling 2FA
    if not current_user.check_password(password):
        flash(_('Incorrect password. Two-factor authentication was not disabled.'), 'error')
        return redirect(url_for('security.manage_2fa'))
    
    current_user.totp_secret = None
    current_user.totp_enabled = False
    current_user.backup_codes = None
    
    if not safe_commit():
        flash(_('Failed to disable two-factor authentication. Please try again.'), 'error')
        return redirect(url_for('security.manage_2fa'))
    
    flash(_('Two-factor authentication has been disabled.'), 'warning')
    return redirect(url_for('main.dashboard'))


@security_bp.route('/2fa/manage', methods=['GET'])
@login_required
def manage_2fa():
    """Manage 2FA settings"""
    return render_template('security/manage_2fa.html')


@security_bp.route('/2fa/backup-codes/regenerate', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def regenerate_backup_codes():
    """Regenerate backup codes"""
    if not current_user.totp_enabled:
        flash(_('Two-factor authentication is not enabled.'), 'error')
        return redirect(url_for('security.manage_2fa'))
    
    password = request.form.get('password', '')
    
    # Verify password before regenerating backup codes
    if not current_user.check_password(password):
        flash(_('Incorrect password. Backup codes were not regenerated.'), 'error')
        return redirect(url_for('security.manage_2fa'))
    
    # Generate new backup codes
    backup_codes = current_user.generate_backup_codes()
    
    if not safe_commit():
        flash(_('Failed to regenerate backup codes. Please try again.'), 'error')
        return redirect(url_for('security.manage_2fa'))
    
    flash(_('New backup codes have been generated. Please save them securely.'), 'success')
    
    return render_template('security/backup_codes.html',
                         backup_codes=backup_codes,
                         is_setup=False)


@security_bp.route('/2fa/verify-login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def verify_2fa_login():
    """Verify 2FA during login"""
    # Check if user is in the 2FA verification flow
    pending_user_id = session.get('pending_2fa_user_id')
    if not pending_user_id:
        flash(_('No pending 2FA verification. Please log in again.'), 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(pending_user_id)
    if not user or not user.totp_enabled:
        session.pop('pending_2fa_user_id', None)
        flash(_('Invalid 2FA verification state. Please log in again.'), 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'GET':
        return render_template('security/verify_2fa_login.html')
    
    # POST - verify the token
    token = request.form.get('token', '').strip()
    use_backup = request.form.get('use_backup') == 'true'
    
    if not token:
        flash(_('Please enter the verification code.'), 'error')
        return render_template('security/verify_2fa_login.html')
    
    is_valid = False
    
    if use_backup:
        # Verify backup code
        is_valid = user.verify_backup_code(token)
        if is_valid:
            safe_commit()
            flash(_('Backup code used successfully. Please generate new backup codes.'), 'warning')
    else:
        # Verify TOTP token
        is_valid = user.verify_totp(token)
    
    if not is_valid:
        flash(_('Invalid verification code. Please try again.'), 'error')
        return render_template('security/verify_2fa_login.html')
    
    # 2FA verification successful - complete login
    from flask_login import login_user
    session.pop('pending_2fa_user_id', None)
    login_user(user, remember=session.get('remember_me', False))
    user.update_last_login()
    
    flash(_('Login successful!'), 'success')
    
    next_page = session.pop('next_after_2fa', None) or url_for('main.dashboard')
    return redirect(next_page)


@security_bp.route('/password/change', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per hour")
def change_password():
    """Change user password"""
    from app.utils.password_policy import PasswordPolicy
    
    if request.method == 'GET':
        # Check if password is expired
        is_expired, days_remaining = PasswordPolicy.check_password_expiry(current_user)
        policy_description = PasswordPolicy.get_policy_description()
        
        return render_template('security/change_password.html',
                             password_expired=is_expired,
                             days_remaining=days_remaining,
                             policy_description=policy_description)
    
    # POST - change password
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Verify current password
    if not current_user.check_password(current_password):
        flash(_('Current password is incorrect.'), 'error')
        return redirect(url_for('security.change_password'))
    
    # Verify new passwords match
    if new_password != confirm_password:
        flash(_('New passwords do not match.'), 'error')
        return redirect(url_for('security.change_password'))
    
    # Set new password (validation happens in set_password)
    try:
        current_user.set_password(new_password, validate=True)
        
        if not safe_commit():
            flash(_('Failed to change password. Please try again.'), 'error')
            return redirect(url_for('security.change_password'))
        
        flash(_('Your password has been changed successfully.'), 'success')
        return redirect(url_for('main.dashboard'))
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('security.change_password'))

