from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Username-only login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        
        if not username:
            flash('Username is required', 'error')
            return render_template('auth/login.html')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Check if self-registration is allowed
            if Config.ALLOW_SELF_REGISTER:
                # Create new user
                user = User(username=username, role='user')
                db.session.add(user)
                db.session.commit()
                flash(f'Welcome! Your account has been created.', 'success')
            else:
                flash('User not found. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Account is disabled. Please contact an administrator.', 'error')
            return render_template('auth/login.html')
        
        # Log in the user
        login_user(user, remember=True)
        user.update_last_login()
        
        # Redirect to intended page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    
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
        # For now, just update last login timestamp
        current_user.update_last_login()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')
