from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime, timedelta
import pytz
from app import db
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing active timer and recent entries"""
    # Get user's active timer
    active_timer = current_user.active_timer
    
    # Get recent entries for the user
    recent_entries = current_user.get_recent_entries(limit=10)
    
    # Get active projects for timer dropdown
    active_projects = Project.query.filter_by(status='active').order_by(Project.name).all()
    
    # Get user statistics
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    today_hours = TimeEntry.get_total_hours_for_period(
        start_date=today,
        user_id=current_user.id
    )
    
    week_hours = TimeEntry.get_total_hours_for_period(
        start_date=week_start,
        user_id=current_user.id
    )
    
    month_hours = TimeEntry.get_total_hours_for_period(
        start_date=month_start,
        user_id=current_user.id
    )
    
    return render_template('main/dashboard.html',
                         active_timer=active_timer,
                         recent_entries=recent_entries,
                         active_projects=active_projects,
                         today_hours=today_hours,
                         week_hours=week_hours,
                         month_hours=month_hours)

@main_bp.route('/_health')
def health_check():
    """Liveness probe: shallow checks only, no DB access"""
    return {'status': 'healthy'}, 200

@main_bp.route('/_ready')
def readiness_check():
    """Readiness probe: verify DB connectivity and critical dependencies"""
    try:
        db.session.execute(text('SELECT 1'))
        return {'status': 'ready', 'timestamp': datetime.utcnow().isoformat()}, 200
    except Exception as e:
        return {'status': 'not_ready', 'error': 'db_unreachable'}, 503

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/help')
def help():
    """Help page"""
    return render_template('main/help.html')

@main_bp.route('/i18n/set-language', methods=['POST', 'GET'])
def set_language():
    """Set preferred UI language via session or user profile."""
    lang = request.args.get('lang') or (request.form.get('lang') if request.method == 'POST' else None) or (request.json.get('lang') if request.is_json else None) or 'en'
    lang = lang.strip().lower()
    from flask import current_app
    supported = list(current_app.config.get('LANGUAGES', {}).keys()) or ['en']
    if lang not in supported:
        lang = current_app.config.get('BABEL_DEFAULT_LOCALE', 'en')
    # Persist in session for guests
    session['preferred_language'] = lang
    # If authenticated, persist to user profile
    try:
        from flask_login import current_user
        from app.utils.db import safe_commit
        if current_user and getattr(current_user, 'is_authenticated', False):
            if getattr(current_user, 'preferred_language', None) != lang:
                current_user.preferred_language = lang
                safe_commit('set_language', {'user_id': current_user.id, 'lang': lang})
    except Exception:
        pass
    # Redirect back if referer exists
    next_url = request.headers.get('Referer') or url_for('main.dashboard')
    return redirect(next_url)

@main_bp.route('/search')
@login_required
def search():
    """Search time entries"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('main.dashboard'))
    
    # Search in time entries
    entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.end_time.isnot(None),
        db.or_(
            TimeEntry.notes.contains(query),
            TimeEntry.tags.contains(query)
        )
    ).order_by(TimeEntry.start_time.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('main/search.html', entries=entries, query=query)
