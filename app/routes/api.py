from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db, socketio
from app.models import User, Project, TimeEntry, Settings, Task
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/timer/status')
@login_required
def timer_status():
    """Get current timer status"""
    active_timer = current_user.active_timer
    
    if not active_timer:
        return jsonify({
            'active': False,
            'timer': None
        })
    
    return jsonify({
        'active': True,
        'timer': {
            'id': active_timer.id,
            'project_name': active_timer.project.name,
            'project_id': active_timer.project_id,
            'start_time': active_timer.start_time.isoformat(),
            'current_duration': active_timer.current_duration_seconds,
            'duration_formatted': active_timer.duration_formatted
        }
    })

@api_bp.route('/api/tasks')
@login_required
def list_tasks_for_project():
    """List tasks for a given project (optionally filter by status)."""
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status')
    if not project_id:
        return jsonify({'error': 'project_id is required'}), 400
    
    # Validate project exists and is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Invalid project'}), 400
    
    query = Task.query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)
    else:
        # Default to tasks not done/cancelled
        query = query.filter(Task.status.in_(['todo', 'in_progress', 'review']))
    
    tasks = query.order_by(Task.priority.desc(), Task.name.asc()).all()
    return jsonify({'tasks': [
        {
            'id': t.id,
            'name': t.name,
            'status': t.status,
            'priority': t.priority
        } for t in tasks
    ]})

@api_bp.route('/api/timer/start', methods=['POST'])
@login_required
def api_start_timer():
    """Start timer via API"""
    data = request.get_json()
    project_id = data.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Project ID is required'}), 400
    
    # Check if project exists and is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Invalid project'}), 400
    
    # Check if user already has an active timer
    active_timer = current_user.active_timer
    if active_timer:
        settings = Settings.get_settings()
        if settings.single_active_timer:
            active_timer.stop_timer()
        else:
            return jsonify({'error': 'User already has an active timer'}), 400
    
    # Create new timer
    from app.models.time_entry import local_now
    new_timer = TimeEntry(
        user_id=current_user.id,
        project_id=project_id,
        start_time=local_now(),
        source='auto'
    )
    
    db.session.add(new_timer)
    db.session.commit()
    
    # Emit WebSocket event
    socketio.emit('timer_started', {
        'user_id': current_user.id,
        'timer_id': new_timer.id,
        'project_name': project.name,
        'start_time': new_timer.start_time.isoformat()
    })
    
    return jsonify({
        'success': True,
        'timer_id': new_timer.id,
        'project_name': project.name
    })

@api_bp.route('/api/timer/stop', methods=['POST'])
@login_required
def api_stop_timer():
    """Stop timer via API"""
    active_timer = current_user.active_timer
    
    if not active_timer:
        return jsonify({'error': 'No active timer to stop'}), 400
    
    # Stop the timer
    active_timer.stop_timer()
    
    # Emit WebSocket event
    socketio.emit('timer_stopped', {
        'user_id': current_user.id,
        'timer_id': active_timer.id,
        'duration': active_timer.duration_formatted
    })
    
    return jsonify({
        'success': True,
        'duration': active_timer.duration_formatted,
        'duration_hours': active_timer.duration_hours
    })

@api_bp.route('/api/entries')
@login_required
def get_entries():
    """Get time entries with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    project_id = request.args.get('project_id', type=int)
    
    query = TimeEntry.query.filter(TimeEntry.end_time.isnot(None))
    
    # Filter by user (if admin or own entries)
    if user_id and current_user.is_admin:
        query = query.filter(TimeEntry.user_id == user_id)
    elif not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    # Filter by project
    if project_id:
        query = query.filter(TimeEntry.project_id == project_id)
    
    entries = query.order_by(TimeEntry.start_time.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'entries': [entry.to_dict() for entry in entries.items],
        'total': entries.total,
        'pages': entries.pages,
        'current_page': entries.page,
        'has_next': entries.has_next,
        'has_prev': entries.has_prev
    })

@api_bp.route('/api/projects')
@login_required
def get_projects():
    """Get active projects"""
    projects = Project.query.filter_by(status='active').order_by(Project.name).all()
    return jsonify({
        'projects': [project.to_dict() for project in projects]
    })

@api_bp.route('/api/users')
@login_required
def get_users():
    """Get active users (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@api_bp.route('/api/stats')
@login_required
def get_stats():
    """Get user statistics"""
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Calculate statistics
    today_hours = TimeEntry.get_total_hours_for_period(
        start_date=end_date.date(),
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    week_hours = TimeEntry.get_total_hours_for_period(
        start_date=end_date.date() - timedelta(days=7),
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    month_hours = TimeEntry.get_total_hours_for_period(
        start_date=start_date.date(),
        user_id=current_user.id if not current_user.is_admin else None
    )
    
    return jsonify({
        'today_hours': today_hours,
        'week_hours': week_hours,
        'month_hours': month_hours,
        'total_hours': current_user.total_hours
    })

@api_bp.route('/api/entry/<int:entry_id>', methods=['PUT'])
@login_required
def update_entry(entry_id):
    """Update a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    
    # Check permissions
    if entry.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'notes' in data:
        entry.notes = data['notes'].strip() if data['notes'] else None
    
    if 'tags' in data:
        entry.tags = data['tags'].strip() if data['tags'] else None
    
    if 'billable' in data:
        entry.billable = bool(data['billable'])
    
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'entry': entry.to_dict()
    })

@api_bp.route('/api/entry/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_entry(entry_id):
    """Delete a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    
    # Check permissions
    if entry.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Don't allow deletion of active timers
    if entry.is_active:
        return jsonify({'error': 'Cannot delete active timer'}), 400
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({'success': True})

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Join user-specific room for real-time updates"""
    user_id = data.get('user_id')
    if user_id and current_user.is_authenticated and current_user.id == user_id:
        socketio.join_room(f'user_{user_id}')
        print(f'User {user_id} joined room')

@socketio.on('leave_user_room')
def handle_leave_user_room(data):
    """Leave user-specific room"""
    user_id = data.get('user_id')
    if user_id:
        socketio.leave_room(f'user_{user_id}')
        print(f'User {user_id} left room')
