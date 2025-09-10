from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.config import Config
from app.utils.db import safe_commit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Username-only login page"""
    if request.method == 'GET':
        try:
            current_app.logger.info("GET /login from %s", request.headers.get('X-Forwarded-For') or request.remote_addr)
        except Exception:
            pass
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip().lower()
            current_app.logger.info("POST /login (username=%s) from %s", username or '<empty>', request.headers.get('X-Forwarded-For') or request.remote_addr)
            
            if not username:
                flash('Username is required', 'error')
                return render_template('auth/login.html')
            
            # Normalize admin usernames from config
            try:
                admin_usernames = [u.strip().lower() for u in (Config.ADMIN_USERNAMES or [])]
            except Exception:
                admin_usernames = ['admin']

            # Check if user exists
            user = User.query.filter_by(username=username).first()
            current_app.logger.info("User lookup for '%s': %s", username, 'found' if user else 'not found')
            
            if not user:
                # Check if self-registration is allowed
                if Config.ALLOW_SELF_REGISTER:
                    # Create new user, promote to admin if username is configured as admin
                    role = 'admin' if username in admin_usernames else 'user'
                    user = User(username=username, role=role)
                    db.session.add(user)
                    if not safe_commit('self_register_user', {'username': username}):
                        current_app.logger.error("Self-registration failed for '%s' due to DB error", username)
                        flash('Could not create your account due to a database error. Please try again later.', 'error')
                        return render_template('auth/login.html')
                    current_app.logger.info("Created new user '%s'", username)
                    flash(f'Welcome! Your account has been created.', 'success')
                else:
                    flash('User not found. Please contact an administrator.', 'error')
                    return render_template('auth/login.html')
            else:
                # If existing user matches admin usernames, ensure admin role
                if username in admin_usernames and user.role != 'admin':
                    user.role = 'admin'
                    if not safe_commit('promote_admin_user', {'username': username}):
                        current_app.logger.error("Failed to promote '%s' to admin due to DB error", username)
                        flash('Could not update your account role due to a database error.', 'error')
                        return render_template('auth/login.html')
            
            # Check if user is active
            if not user.is_active:
                flash('Account is disabled. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            # Log in the user
            login_user(user, remember=True)
            user.update_last_login()
            current_app.logger.info("User '%s' logged in successfully", user.username)
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            current_app.logger.info("Redirecting '%s' to %s", user.username, next_page)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        except Exception as e:
            current_app.logger.exception("Login error: %s", e)
            flash('Unexpected error during login. Please try again or check server logs.', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        # Update real name if provided
        full_name = request.form.get('full_name', '').strip()
        current_user.full_name = full_name or None
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception:
            db.session.rollback()
            flash('Could not update your profile due to a database error.', 'error')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')


@auth_bp.route('/profile/theme', methods=['POST'])
@login_required
def update_theme_preference():
    """Persist user theme preference (light|dark|system)."""
    try:
        value = (request.json.get('theme') if request.is_json else request.form.get('theme') or '').strip().lower()
    except Exception:
        value = (request.form.get('theme') or '').strip().lower()

    if value not in ('light', 'dark', 'system'):
        return ({'error': 'invalid theme value'}, 400)

    # Store None for system to allow fallback to system preference
    current_user.theme_preference = None if value == 'system' else value
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return ({'error': 'failed to save preference'}, 500)

    return ({'ok': True, 'theme': value}, 200)
