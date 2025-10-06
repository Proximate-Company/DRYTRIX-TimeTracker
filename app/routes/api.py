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
            'task_id': active_timer.task_id,
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
    task_id = data.get('task_id')
    
    if not project_id:
        return jsonify({'error': 'Project ID is required'}), 400
    
    # Check if project exists and is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Invalid project'}), 400
    
    # Validate task if provided
    task = None
    if task_id:
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        if not task:
            return jsonify({'error': 'Invalid task for selected project'}), 400

    # Check if user already has an active timer
    active_timer = current_user.active_timer
    if active_timer:
        return jsonify({'error': 'User already has an active timer'}), 400
    
    # Create new timer
    from app.models.time_entry import local_now
    new_timer = TimeEntry(
        user_id=current_user.id,
        project_id=project_id,
        task_id=task.id if task else None,
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
        'task_id': task.id if task else None,
        'start_time': new_timer.start_time.isoformat()
    })
    
    return jsonify({
        'success': True,
        'timer_id': new_timer.id,
        'project_name': project.name,
        'task_id': task.id if task else None
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

# --- Idle control: stop at specific time ---
@api_bp.route('/api/timer/stop_at', methods=['POST'])
@login_required
def api_stop_timer_at():
    """Stop the active timer at a specific timestamp (idle adjustment)."""
    active_timer = current_user.active_timer
    if not active_timer:
        return jsonify({'error': 'No active timer to stop'}), 400

    data = request.get_json() or {}
    stop_time_str = data.get('stop_time')  # ISO string
    if not stop_time_str:
        return jsonify({'error': 'stop_time is required'}), 400

    try:
        # Accept ISO; handle trailing Z
        ts = stop_time_str.strip()
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        parsed = datetime.fromisoformat(ts)
        # Convert to local naive for storage consistency
        if parsed.tzinfo is not None:
            parsed_local_aware = utc_to_local(parsed)
            stop_time_local = parsed_local_aware.replace(tzinfo=None)
        else:
            stop_time_local = parsed
    except Exception:
        return jsonify({'error': 'Invalid stop_time format'}), 400

    if stop_time_local <= active_timer.start_time:
        return jsonify({'error': 'stop_time must be after start time'}), 400

    # Do not allow stopping in the future
    now_local = local_now()
    if stop_time_local > now_local:
        stop_time_local = now_local

    try:
        active_timer.stop_timer(end_time=stop_time_local)
    except Exception as e:
        current_app.logger.warning('Failed to stop timer at specific time: %s', e)
        return jsonify({'error': 'Failed to stop timer'}), 500

    socketio.emit('timer_stopped', {
        'user_id': current_user.id,
        'timer_id': active_timer.id,
        'duration': active_timer.duration_formatted
    })

    return jsonify({'success': True, 'duration': active_timer.duration_formatted})

# --- Resume last timer/project ---
@api_bp.route('/api/timer/resume', methods=['POST'])
@login_required
def api_resume_timer():
    """Resume timer for last used project/task or provided project/task."""
    if current_user.active_timer:
        return jsonify({'error': 'Timer already running'}), 400

    data = request.get_json() or {}
    project_id = data.get('project_id')
    task_id = data.get('task_id')

    if not project_id:
        # Find most recent finished entry
        last = (
            TimeEntry.query
            .filter(TimeEntry.user_id == current_user.id)
            .order_by(TimeEntry.end_time.desc().nullslast(), TimeEntry.start_time.desc())
            .first()
        )
        if not last:
            return jsonify({'error': 'No previous entry to resume'}), 404
        project_id = last.project_id
        task_id = last.task_id

    # Validate project is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Invalid or inactive project'}), 400

    if task_id:
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        if not task:
            return jsonify({'error': 'Invalid task for selected project'}), 400

    # Create new timer
    new_timer = TimeEntry(
        user_id=current_user.id,
        project_id=project_id,
        task_id=task_id,
        start_time=local_now(),
        source='auto'
    )
    db.session.add(new_timer)
    db.session.commit()

    socketio.emit('timer_started', {
        'user_id': current_user.id,
        'timer_id': new_timer.id,
        'project_name': project.name,
        'task_id': task_id,
        'start_time': new_timer.start_time.isoformat()
    })

    return jsonify({'success': True, 'timer_id': new_timer.id})

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

@api_bp.route('/api/entries', methods=['POST'])
@login_required
def create_entry():
    """Create a finished time entry (used by calendar drag-create)."""
    data = request.get_json() or {}
    project_id = data.get('project_id')
    task_id = data.get('task_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    notes = (data.get('notes') or '').strip() or None
    tags = (data.get('tags') or '').strip() or None
    billable = bool(data.get('billable', True))

    if not (project_id and start_time_str and end_time_str):
        return jsonify({'error': 'project_id, start_time, end_time are required'}), 400

    # Validate project
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        return jsonify({'error': 'Invalid project'}), 400

    if task_id:
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        if not task:
            return jsonify({'error': 'Invalid task for selected project'}), 400

    def parse_iso_local(s: str):
        try:
            ts = s.strip()
            if ts.endswith('Z'):
                ts = ts[:-1] + '+00:00'
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is not None:
                return utc_to_local(dt).replace(tzinfo=None)
            return dt
        except Exception:
            return None

    start_dt = parse_iso_local(start_time_str)
    end_dt = parse_iso_local(end_time_str)
    if not (start_dt and end_dt) or end_dt <= start_dt:
        return jsonify({'error': 'Invalid start/end time'}), 400

    entry = TimeEntry(
        user_id=current_user.id if not current_user.is_admin else (data.get('user_id') or current_user.id),
        project_id=project_id,
        task_id=task_id,
        start_time=start_dt,
        end_time=end_dt,
        notes=notes,
        tags=tags,
        source='manual',
        billable=billable
    )
    db.session.add(entry)
    if not safe_commit('api_create_entry', {'project_id': project_id}):
        return jsonify({'error': 'Database error while creating entry'}), 500

    payload = entry.to_dict()
    payload['project_name'] = entry.project.name if entry.project else None
    return jsonify({'success': True, 'entry': payload})

@api_bp.route('/api/entries/bulk', methods=['POST'])
@login_required
def bulk_entries_action():
    """Perform bulk actions on time entries: delete, set billable, add/remove tag."""
    data = request.get_json() or {}
    entry_ids = data.get('entry_ids') or []
    action = (data.get('action') or '').strip()
    value = data.get('value')

    if not entry_ids or not isinstance(entry_ids, list):
        return jsonify({'error': 'entry_ids must be a non-empty list'}), 400
    if action not in {'delete', 'set_billable', 'add_tag', 'remove_tag'}:
        return jsonify({'error': 'Unsupported action'}), 400

    # Load entries with permission checks
    q = TimeEntry.query.filter(TimeEntry.id.in_(entry_ids))
    entries = q.all()
    if not entries:
        return jsonify({'error': 'No entries found'}), 404

    # Permission: non-admins can only modify own entries
    if not current_user.is_admin:
        for e in entries:
            if e.user_id != current_user.id:
                return jsonify({'error': 'Access denied for one or more entries'}), 403

    affected = 0
    if action == 'delete':
        for e in entries:
            if e.is_active:
                continue
            db.session.delete(e)
            affected += 1
    elif action == 'set_billable':
        flag = bool(value)
        for e in entries:
            if e.is_active:
                continue
            e.billable = flag
            e.updated_at = local_now()
            affected += 1
    elif action in {'add_tag', 'remove_tag'}:
        tag = (value or '').strip()
        if not tag:
            return jsonify({'error': 'Tag value is required'}), 400
        for e in entries:
            if e.is_active:
                continue
            tags = set(e.tag_list)
            if action == 'add_tag':
                tags.add(tag)
            else:
                tags.discard(tag)
            e.tags = ', '.join(sorted(tags)) if tags else None
            e.updated_at = local_now()
            affected += 1

    if affected > 0:
        if not safe_commit('api_bulk_entries', {'action': action, 'count': affected}):
            return jsonify({'error': 'Database error during bulk operation'}), 500
    else:
        db.session.rollback()

    return jsonify({'success': True, 'affected': affected})

@api_bp.route('/api/calendar/events')
@login_required
def calendar_events():
    """Return calendar events for the current user in a date range."""
    start = request.args.get('start')
    end = request.args.get('end')
    if not (start and end):
        return jsonify({'error': 'start and end are required'}), 400

    def parse_iso(s: str):
        try:
            ts = s.strip()
            if ts.endswith('Z'):
                ts = ts[:-1] + '+00:00'
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is not None:
                return utc_to_local(dt).replace(tzinfo=None)
            return dt
        except Exception:
            return None

    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    if not (start_dt and end_dt):
        return jsonify({'error': 'Invalid date range'}), 400

    q = TimeEntry.query.filter(TimeEntry.user_id == current_user.id)
    q = q.filter(TimeEntry.start_time < end_dt, (TimeEntry.end_time.is_(None)) | (TimeEntry.end_time > start_dt))
    items = q.order_by(TimeEntry.start_time.asc()).all()

    events = []
    now_local = local_now()
    for e in items:
        ev = {
            'id': e.id,
            'title': f"{e.project.name if e.project else 'Project'}" + (f" • {e.task.name}" if e.task else (f" • {e.notes[:24]}…" if e.notes else '')),
            'start': e.start_time.isoformat(),
            'end': (e.end_time or now_local).isoformat(),
            'editable': False,
            'allDay': False,
        }
        events.append(ev)

    return jsonify({'events': events})

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
