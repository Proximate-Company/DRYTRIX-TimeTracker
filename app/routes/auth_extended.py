"""Extended authentication routes for signup, password reset, 2FA, and invitations"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User, Organization, Membership, PasswordResetToken, EmailVerificationToken
from app.utils.db import safe_commit
from app.utils.email_service import email_service
from app.utils.jwt_utils import create_token_pair, refresh_access_token, revoke_refresh_token, revoke_all_user_tokens
from app.utils.totp import generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp_token
from app.utils.permissions import get_current_user, organization_admin_required
from flask_babel import gettext as _
from datetime import datetime

auth_extended_bp = Blueprint('auth_extended', __name__)


# ============================================================================
# REGISTRATION / SIGNUP
# ============================================================================

@auth_extended_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per hour", methods=["POST"])
def signup():
    """User registration with email and password"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Check if self-registration is allowed
    if not current_app.config.get('ALLOW_SELF_REGISTER', True):
        flash(_('Self-registration is disabled. Please contact an administrator.'), 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append(_('Username must be at least 3 characters'))
        
        if not email or '@' not in email:
            errors.append(_('Valid email is required'))
        
        if not password or len(password) < 8:
            errors.append(_('Password must be at least 8 characters'))
        
        if password != password_confirm:
            errors.append(_('Passwords do not match'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            errors.append(_('Username already taken'))
        
        if User.query.filter_by(email=email).first():
            errors.append(_('Email already registered'))
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/signup.html')
        
        try:
            # Create user
            user = User(username=username, email=email, full_name=full_name)
            
            # Try to set password - this will raise ValueError if password doesn't meet requirements
            try:
                user.set_password(password)
            except ValueError as ve:
                # Password validation failed - show the specific error
                flash(str(ve), 'error')
                return render_template('auth/signup.html')
            
            user.is_active = True
            user.email_verified = False
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create default organization for the user
            org_name = f"{full_name or username}'s Organization"
            organization = Organization(name=org_name, contact_email=email)
            db.session.add(organization)
            db.session.flush()  # Get org ID
            
            # Create membership with owner/admin role
            membership = Membership(
                user_id=user.id,
                organization_id=organization.id,
                role='admin',
                status='active'
            )
            db.session.add(membership)
            
            if not safe_commit('signup_user', {'username': username}):
                raise RuntimeError('Failed to create user')
            
            # Send email verification
            if email_service.is_configured:
                verification_token = EmailVerificationToken.create_token(user.id, email)
                email_service.send_email_verification(user, verification_token)
                flash(_('Account created! Please check your email to verify your address.'), 'success')
            else:
                # Auto-verify if email not configured
                user.email_verified = True
                db.session.commit()
                flash(_('Account created successfully!'), 'success')
            
            # Log the user in
            login_user(user, remember=True)
            
            return redirect(url_for('main.dashboard'))
            
        except ValueError as ve:
            # This catches password validation errors that weren't caught in the inner try
            db.session.rollback()
            current_app.logger.error(f'Signup password validation error: {ve}')
            flash(str(ve), 'error')
            return render_template('auth/signup.html')
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'Signup error: {e}')
            flash(_('An error occurred during signup. Please try again.'), 'error')
            return render_template('auth/signup.html')
    
    return render_template('auth/signup.html')


# ============================================================================
# PASSWORD RESET
# ============================================================================

@auth_extended_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=["POST"])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash(_('Email is required'), 'error')
            return render_template('auth/forgot_password.html')
        
        # Always show success message (don't reveal if email exists)
        flash(_('If an account exists with that email, a password reset link has been sent.'), 'success')
        
        # Find user and send reset email
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active and user.has_password:
            try:
                # Revoke any existing tokens for this user
                PasswordResetToken.revoke_user_tokens(user.id)
                
                # Create new reset token
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                reset_token = PasswordResetToken.create_token(user.id, ip_address)
                
                # Send email
                if email_service.is_configured:
                    email_service.send_password_reset_email(user, reset_token)
                    current_app.logger.info(f'Password reset email sent to {email}')
                else:
                    current_app.logger.warning(f'Email service not configured, cannot send reset to {email}')
                    
            except Exception as e:
                current_app.logger.exception(f'Error sending password reset: {e}')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_extended_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour", methods=["POST"])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Validate token
    reset_token = PasswordResetToken.get_valid_token(token)
    
    if not reset_token:
        flash(_('Invalid or expired password reset link'), 'error')
        return redirect(url_for('auth_extended.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if not password or len(password) < 8:
            flash(_('Password must be at least 8 characters'), 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != password_confirm:
            flash(_('Passwords do not match'), 'error')
            return render_template('auth/reset_password.html', token=token)
        
        try:
            user = reset_token.user
            user.set_password(password)
            reset_token.mark_as_used()
            
            # Revoke all existing sessions/tokens for security
            revoke_all_user_tokens(user.id)
            
            db.session.commit()
            
            flash(_('Password reset successfully! Please log in.'), 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'Password reset error: {e}')
            flash(_('An error occurred. Please try again.'), 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token)


@auth_extended_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    verification_token = EmailVerificationToken.get_valid_token(token)
    
    if not verification_token:
        flash(_('Invalid or expired verification link'), 'error')
        return redirect(url_for('auth.login'))
    
    try:
        user = verification_token.user
        user.email = verification_token.email
        user.email_verified = True
        verification_token.mark_as_verified()
        
        db.session.commit()
        
        flash(_('Email verified successfully!'), 'success')
        
        if current_user.is_authenticated:
            return redirect(url_for('auth.profile'))
        else:
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Email verification error: {e}')
        flash(_('An error occurred during verification.'), 'error')
        return redirect(url_for('auth.login'))


# ============================================================================
# ACCOUNT SETTINGS
# ============================================================================

@auth_extended_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """User account settings page"""
    from app.models import RefreshToken
    
    # Get active sessions/devices
    active_tokens = RefreshToken.get_user_tokens(current_user.id)
    
    return render_template('auth/settings.html', active_tokens=active_tokens)


@auth_extended_bp.route('/settings/change-email', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def change_email():
    """Change user email address"""
    new_email = request.form.get('new_email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not new_email or '@' not in new_email:
        flash(_('Valid email is required'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    if not current_user.check_password(password):
        flash(_('Incorrect password'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    # Check if email already in use
    if User.query.filter_by(email=new_email).first():
        flash(_('Email already in use'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    try:
        # Send verification email to new address
        verification_token = EmailVerificationToken.create_token(current_user.id, new_email)
        
        if email_service.is_configured:
            email_service.send_email_verification(current_user, verification_token)
            flash(_('Verification email sent to new address. Please check your email.'), 'success')
        else:
            # Auto-update if email not configured
            current_user.email = new_email
            current_user.email_verified = True
            db.session.commit()
            flash(_('Email updated successfully'), 'success')
        
        return redirect(url_for('auth_extended.settings'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Email change error: {e}')
        flash(_('An error occurred. Please try again.'), 'error')
        return redirect(url_for('auth_extended.settings'))


@auth_extended_bp.route('/settings/change-password', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash(_('Current password is incorrect'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    if len(new_password) < 8:
        flash(_('New password must be at least 8 characters'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    if new_password != confirm_password:
        flash(_('New passwords do not match'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    try:
        current_user.set_password(new_password)
        
        # Revoke all other sessions for security
        from app.models import RefreshToken
        RefreshToken.revoke_user_tokens(current_user.id)
        
        db.session.commit()
        
        flash(_('Password changed successfully. Other sessions have been logged out.'), 'success')
        return redirect(url_for('auth_extended.settings'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Password change error: {e}')
        flash(_('An error occurred. Please try again.'), 'error')
        return redirect(url_for('auth_extended.settings'))


# ============================================================================
# TWO-FACTOR AUTHENTICATION (2FA)
# ============================================================================

@auth_extended_bp.route('/settings/2fa/enable', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    """Enable two-factor authentication"""
    if current_user.totp_enabled:
        flash(_('2FA is already enabled'), 'info')
        return redirect(url_for('auth_extended.settings'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        # Get secret from session
        secret = session.get('totp_secret')
        
        if not secret:
            flash(_('2FA setup session expired. Please try again.'), 'error')
            return redirect(url_for('auth_extended.enable_2fa'))
        
        # Verify token
        if not verify_totp_token(secret, token):
            flash(_('Invalid verification code. Please try again.'), 'error')
            return render_template('auth/enable_2fa.html', 
                                 secret=secret,
                                 qr_code=session.get('totp_qr'))
        
        try:
            # Enable 2FA
            current_user.totp_secret = secret
            current_user.totp_enabled = True
            
            # Generate backup codes
            backup_codes = current_user.generate_backup_codes()
            
            db.session.commit()
            
            # Clear session
            session.pop('totp_secret', None)
            session.pop('totp_qr', None)
            
            flash(_('2FA enabled successfully! Save your backup codes.'), 'success')
            return render_template('auth/2fa_backup_codes.html', backup_codes=backup_codes)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'2FA enable error: {e}')
            flash(_('An error occurred. Please try again.'), 'error')
            return redirect(url_for('auth_extended.enable_2fa'))
    
    # Generate new secret and QR code
    secret = generate_totp_secret()
    totp_uri = get_totp_uri(secret, current_user.email or current_user.username)
    qr_code = generate_qr_code(totp_uri)
    
    # Store in session temporarily
    session['totp_secret'] = secret
    session['totp_qr'] = qr_code
    
    return render_template('auth/enable_2fa.html', secret=secret, qr_code=qr_code)


@auth_extended_bp.route('/settings/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Disable two-factor authentication"""
    password = request.form.get('password', '')
    
    if not current_user.check_password(password):
        flash(_('Incorrect password'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    try:
        current_user.totp_enabled = False
        current_user.totp_secret = None
        current_user.backup_codes = None
        
        db.session.commit()
        
        flash(_('2FA disabled successfully'), 'success')
        return redirect(url_for('auth_extended.settings'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'2FA disable error: {e}')
        flash(_('An error occurred. Please try again.'), 'error')
        return redirect(url_for('auth_extended.settings'))


@auth_extended_bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA token during login"""
    # Check if user is in 2FA pending state
    user_id = session.get('2fa_user_id')
    remember = session.get('2fa_remember', False)
    
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    
    if not user or not user.totp_enabled:
        session.pop('2fa_user_id', None)
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        use_backup = request.form.get('use_backup') == 'true'
        
        verified = False
        
        if use_backup:
            verified = user.verify_backup_code(token)
            if verified:
                flash(_('Backup code used successfully'), 'info')
        else:
            verified = user.verify_totp(token)
        
        if verified:
            # Clear 2FA session data
            session.pop('2fa_user_id', None)
            session.pop('2fa_remember', None)
            
            # Complete login
            login_user(user, remember=remember)
            user.update_last_login()
            
            flash(_('Welcome back, %(username)s!', username=user.username), 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            return redirect(next_page)
        else:
            flash(_('Invalid verification code'), 'error')
            return render_template('auth/verify_2fa.html')
    
    return render_template('auth/verify_2fa.html')


# ============================================================================
# ORGANIZATION INVITATIONS
# ============================================================================

@auth_extended_bp.route('/invite', methods=['POST'])
@login_required
@organization_admin_required
@limiter.limit("10 per hour")
def send_invitation(organization):
    """Send organization invitation to user by email"""
    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', 'member')
    
    if not email or '@' not in email:
        flash(_('Valid email is required'), 'error')
        return redirect(request.referrer or url_for('organizations.members', org_slug=organization.slug))
    
    if role not in ['admin', 'member', 'viewer']:
        role = 'member'
    
    # Check if organization has reached user limit
    if organization.has_reached_user_limit:
        flash(_('Organization has reached its user limit'), 'error')
        return redirect(request.referrer or url_for('organizations.members', org_slug=organization.slug))
    
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            # Check if already a member
            if Membership.user_is_member(existing_user.id, organization.id):
                flash(_('User is already a member of this organization'), 'info')
                return redirect(request.referrer or url_for('organizations.members', org_slug=organization.slug))
            
            # Create membership with invited status
            membership = Membership(
                user_id=existing_user.id,
                organization_id=organization.id,
                role=role,
                status='invited',
                invited_by=current_user.id
            )
        else:
            # Create placeholder user for invitation
            # Generate username from email
            username = email.split('@')[0]
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{email.split('@')[0]}{counter}"
                counter += 1
            
            user = User(username=username, email=email)
            user.is_active = False  # Inactive until they accept
            db.session.add(user)
            db.session.flush()
            
            membership = Membership(
                user_id=user.id,
                organization_id=organization.id,
                role=role,
                status='invited',
                invited_by=current_user.id
            )
        
        db.session.add(membership)
        db.session.commit()
        
        # Send invitation email
        if email_service.is_configured:
            email_service.send_invitation_email(current_user, email, organization, membership)
            flash(_('Invitation sent to %(email)s', email=email), 'success')
        else:
            flash(_('Invitation created but email service not configured'), 'warning')
        
        return redirect(request.referrer or url_for('organizations.members', org_slug=organization.slug))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Invitation error: {e}')
        flash(_('An error occurred. Please try again.'), 'error')
        return redirect(request.referrer or url_for('organizations.members', org_slug=organization.slug))


@auth_extended_bp.route('/accept-invitation/<token>', methods=['GET', 'POST'])
def accept_invitation(token):
    """Accept organization invitation"""
    membership = Membership.get_by_invitation_token(token)
    
    if not membership:
        flash(_('Invalid or expired invitation'), 'error')
        return redirect(url_for('auth.login'))
    
    organization = membership.organization
    inviter = membership.inviter
    
    # If user is not active, they need to complete signup
    if not membership.user.is_active:
        if request.method == 'POST':
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            full_name = request.form.get('full_name', '').strip()
            
            if len(password) < 8:
                flash(_('Password must be at least 8 characters'), 'error')
                return render_template('auth/accept_invitation.html', 
                                     organization=organization, 
                                     inviter=inviter,
                                     token=token)
            
            if password != password_confirm:
                flash(_('Passwords do not match'), 'error')
                return render_template('auth/accept_invitation.html', 
                                     organization=organization, 
                                     inviter=inviter,
                                     token=token)
            
            try:
                # Activate user account
                user = membership.user
                user.set_password(password)
                if full_name:
                    user.full_name = full_name
                user.is_active = True
                user.email_verified = True  # Email verified through invitation
                
                # Accept membership
                membership.accept_invitation()
                
                db.session.commit()
                
                # Log them in
                login_user(user, remember=True)
                
                flash(_('Welcome to %(org)s!', org=organization.name), 'success')
                return redirect(url_for('main.dashboard'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f'Accept invitation error: {e}')
                flash(_('An error occurred. Please try again.'), 'error')
                return render_template('auth/accept_invitation.html', 
                                     organization=organization, 
                                     inviter=inviter,
                                     token=token)
        
        return render_template('auth/accept_invitation.html', 
                             organization=organization, 
                             inviter=inviter,
                             token=token)
    
    # Existing user - just accept the membership
    try:
        membership.accept_invitation()
        db.session.commit()
        
        if current_user.is_authenticated and current_user.id == membership.user_id:
            flash(_('You joined %(org)s!', org=organization.name), 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(_('Please log in to access %(org)s', org=organization.name), 'info')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Accept invitation error: {e}')
        flash(_('An error occurred. Please try again.'), 'error')
        return redirect(url_for('auth.login'))


# ============================================================================
# API ENDPOINTS (JWT)
# ============================================================================

@auth_extended_bp.route('/api/auth/token', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """API login endpoint - returns JWT tokens"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    username = data.get('username', '').strip().lower()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    totp_token = data.get('totp_token', '').strip()
    
    # Find user by username or email
    user = None
    if username:
        user = User.query.filter_by(username=username).first()
    elif email:
        user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 401
    
    # Check 2FA if enabled
    if user.totp_enabled:
        if not totp_token:
            return jsonify({'error': '2FA required', 'requires_2fa': True}), 401
        
        if not user.verify_totp(totp_token):
            return jsonify({'error': 'Invalid 2FA code'}), 401
    
    # Generate tokens
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    device_name = data.get('device_name', 'API Client')
    
    token_data = create_token_pair(
        user_id=user.id,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    user.update_last_login()
    
    return jsonify({
        'user': user.to_dict(),
        **token_data
    }), 200


@auth_extended_bp.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("20 per minute")
def api_refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return jsonify({'error': 'Refresh token required'}), 400
    
    refresh_token = data.get('refresh_token')
    
    access_token, new_refresh_token = refresh_access_token(refresh_token)
    
    if not access_token:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900
    }), 200


@auth_extended_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """API logout - revoke refresh token"""
    data = request.get_json()
    
    if not data or 'refresh_token' not in data:
        return jsonify({'error': 'Refresh token required'}), 400
    
    refresh_token = data.get('refresh_token')
    
    revoke_refresh_token(refresh_token)
    
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_extended_bp.route('/settings/sessions/<int:token_id>/revoke', methods=['POST'])
@login_required
def revoke_session(token_id):
    """Revoke a specific session/device"""
    from app.models import RefreshToken
    
    token = RefreshToken.query.get(token_id)
    
    if not token or token.user_id != current_user.id:
        flash(_('Session not found'), 'error')
        return redirect(url_for('auth_extended.settings'))
    
    try:
        token.revoke()
        flash(_('Session revoked successfully'), 'success')
    except Exception as e:
        current_app.logger.exception(f'Session revoke error: {e}')
        flash(_('An error occurred'), 'error')
    
    return redirect(url_for('auth_extended.settings'))

