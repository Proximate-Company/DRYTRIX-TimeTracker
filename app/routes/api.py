from flask import Blueprint, jsonify, request, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db, socketio
from app.models import User, Project, TimeEntry, Settings, Task
from datetime import datetime, timedelta
from app.utils.db import safe_commit
from app.utils.timezone import parse_local_datetime, utc_to_local
from app.models.time_entry import local_now
import json
import os
import uuid
from werkzeug.utils import secure_filename

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
    
    # Ensure frontend receives project_name like other endpoints
    entries_payload = []
    for entry in entries.items:
        e = entry.to_dict()
        e['project_name'] = e.get('project') or (entry.project.name if entry.project else None)
        entries_payload.append(e)

    return jsonify({
        'entries': entries_payload,
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

@api_bp.route('/api/projects/<int:project_id>/tasks')
@login_required
def get_project_tasks(project_id):
    """Get tasks for a specific project"""
    # Check if project exists and is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Project not found or inactive'}), 404
    
    # Get tasks for the project
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.name).all()
    
    return jsonify({
        'success': True,
        'tasks': [{
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'status': task.status,
            'priority': task.priority
        } for task in tasks]
    })

# Fetch a single time entry (details for edit modal)
@api_bp.route('/api/entry/<int:entry_id>', methods=['GET'])
@login_required
def get_entry(entry_id):
    entry = TimeEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    payload = entry.to_dict()
    payload['project_name'] = entry.project.name if entry.project else None
    return jsonify(payload)

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
    
    data = request.get_json() or {}

    # Optional: project change (admin only)
    new_project_id = data.get('project_id')
    if new_project_id is not None and current_user.is_admin:
        if new_project_id != entry.project_id:
            project = Project.query.filter_by(id=new_project_id, status='active').first()
            if not project:
                return jsonify({'error': 'Invalid project'}), 400
            entry.project_id = new_project_id

    # Optional: start/end time updates (admin only for safety)
    # Accept HTML datetime-local format: YYYY-MM-DDTHH:MM
    def parse_dt_local(dt_str):
        if not dt_str:
            return None
        try:
            if 'T' in dt_str:
                date_part, time_part = dt_str.split('T', 1)
            else:
                date_part, time_part = dt_str.split(' ', 1)
            # Parse as UTC-aware then convert to local naive to match model storage
            parsed_utc = parse_local_datetime(date_part, time_part)
            parsed_local_aware = utc_to_local(parsed_utc)
            return parsed_local_aware.replace(tzinfo=None)
        except Exception:
            return None

    if current_user.is_admin:
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if start_time_str:
            parsed_start = parse_dt_local(start_time_str)
            if not parsed_start:
                return jsonify({'error': 'Invalid start time format'}), 400
            entry.start_time = parsed_start

        if end_time_str is not None:
            if end_time_str == '' or end_time_str is False:
                entry.end_time = None
                entry.duration_seconds = None
            else:
                parsed_end = parse_dt_local(end_time_str)
                if not parsed_end:
                    return jsonify({'error': 'Invalid end time format'}), 400
                if parsed_end <= (entry.start_time or parsed_end):
                    return jsonify({'error': 'End time must be after start time'}), 400
                entry.end_time = parsed_end
                # Recalculate duration
                entry.calculate_duration()

    # Prevent multiple active timers for the same user when editing
    if entry.end_time is None:
        conflict = (
            TimeEntry.query
            .filter(TimeEntry.user_id == entry.user_id)
            .filter(TimeEntry.end_time.is_(None))
            .filter(TimeEntry.id != entry.id)
            .first()
        )
        if conflict:
            return jsonify({'error': 'User already has an active timer'}), 400

    # Notes, tags, billable (both admin and owner can change)
    if 'notes' in data:
        entry.notes = data['notes'].strip() if data['notes'] else None

    if 'tags' in data:
        entry.tags = data['tags'].strip() if data['tags'] else None

    if 'billable' in data:
        entry.billable = bool(data['billable'])

    # Prefer local time for updated_at per project preference
    entry.updated_at = local_now()

    if not safe_commit('api_update_entry', {'entry_id': entry_id}):
        return jsonify({'error': 'Database error while updating entry'}), 500

    payload = entry.to_dict()
    payload['project_name'] = entry.project.name if entry.project else None
    return jsonify({'success': True, 'entry': payload})

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

# ================================
# Editor image uploads
# ================================

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_image_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def get_editor_upload_folder() -> str:
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'editor')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

@api_bp.route('/api/uploads/images', methods=['POST'])
@login_required
def upload_editor_image():
    """Handle image uploads from the markdown editor."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No image provided'}), 400
    if not allowed_image_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"editor_{uuid.uuid4().hex[:12]}.{ext}"
    folder = get_editor_upload_folder()
    path = os.path.join(folder, unique_name)
    file.save(path)

    url = f"/uploads/editor/{unique_name}"
    return jsonify({'success': True, 'url': url})

@api_bp.route('/uploads/editor/<path:filename>')
def serve_editor_image(filename):
    """Serve uploaded editor images from static/uploads/editor."""
    folder = get_editor_upload_folder()
    return send_from_directory(folder, filename)

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
