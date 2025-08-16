from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime
import json

timer_bp = Blueprint('timer', __name__)

@timer_bp.route('/timer/start', methods=['POST'])
@login_required
def start_timer():
    """Start a new timer for the current user"""
    project_id = request.form.get('project_id', type=int)
    
    if not project_id:
        flash('Project is required', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if project exists and is active
    project = Project.query.filter_by(id=project_id, status='active').first()
    if not project:
        flash('Invalid project selected', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user already has an active timer
    active_timer = current_user.active_timer
    if active_timer:
        # If single active timer is enabled, stop the current one
        settings = Settings.get_settings()
        if settings.single_active_timer:
            active_timer.stop_timer()
            flash('Previous timer stopped', 'info')
        else:
            flash('You already have an active timer', 'error')
            return redirect(url_for('main.dashboard'))
    
    # Create new timer
    new_timer = TimeEntry(
        user_id=current_user.id,
        project_id=project_id,
        start_utc=datetime.utcnow(),
        source='auto'
    )
    
    db.session.add(new_timer)
    db.session.commit()
    
    # Emit WebSocket event for real-time updates
    socketio.emit('timer_started', {
        'user_id': current_user.id,
        'timer_id': new_timer.id,
        'project_name': project.name,
        'start_time': new_timer.start_utc.isoformat()
    })
    
    flash(f'Timer started for {project.name}', 'success')
    return redirect(url_for('main.dashboard'))

@timer_bp.route('/timer/stop', methods=['POST'])
@login_required
def stop_timer():
    """Stop the current user's active timer"""
    active_timer = current_user.active_timer
    
    if not active_timer:
        flash('No active timer to stop', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Stop the timer
    active_timer.stop_timer()
    
    # Emit WebSocket event for real-time updates
    socketio.emit('timer_stopped', {
        'user_id': current_user.id,
        'timer_id': active_timer.id,
        'duration': active_timer.duration_formatted
    })
    
    flash(f'Timer stopped. Duration: {active_timer.duration_formatted}', 'success')
    return redirect(url_for('main.dashboard'))

@timer_bp.route('/timer/status')
@login_required
def timer_status():
    """Get current timer status as JSON"""
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
            'start_time': active_timer.start_utc.isoformat(),
            'current_duration': active_timer.current_duration_seconds,
            'duration_formatted': active_timer.duration_formatted
        }
    })

@timer_bp.route('/timer/edit/<int:timer_id>', methods=['GET', 'POST'])
@login_required
def edit_timer(timer_id):
    """Edit a completed timer entry"""
    timer = TimeEntry.query.get_or_404(timer_id)
    
    # Check if user can edit this timer
    if timer.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own timers', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Update timer details
        timer.notes = request.form.get('notes', '').strip()
        timer.tags = request.form.get('tags', '').strip()
        timer.billable = request.form.get('billable') == 'on'
        
        db.session.commit()
        flash('Timer updated successfully', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('timer/edit_timer.html', timer=timer)

@timer_bp.route('/timer/delete/<int:timer_id>', methods=['POST'])
@login_required
def delete_timer(timer_id):
    """Delete a timer entry"""
    timer = TimeEntry.query.get_or_404(timer_id)
    
    # Check if user can delete this timer
    if timer.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own timers', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Don't allow deletion of active timers
    if timer.is_active:
        flash('Cannot delete an active timer', 'error')
        return redirect(url_for('main.dashboard'))
    
    project_name = timer.project.name
    db.session.delete(timer)
    db.session.commit()
    
    flash(f'Timer for {project_name} deleted successfully', 'success')
    return redirect(url_for('main.dashboard'))

@timer_bp.route('/timer/manual', methods=['GET', 'POST'])
@login_required
def manual_entry():
    """Create a manual time entry"""
    # Get active projects for dropdown (used for both GET and error re-renders on POST)
    active_projects = Project.query.filter_by(status='active').order_by(Project.name).all()
    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        notes = request.form.get('notes', '').strip()
        tags = request.form.get('tags', '').strip()
        billable = request.form.get('billable') == 'on'
        
        # Validate required fields
        if not all([project_id, start_date, start_time, end_date, end_time]):
            flash('All fields are required', 'error')
            return render_template('timer/manual_entry.html', projects=active_projects)
        
        # Check if project exists and is active
        project = Project.query.filter_by(id=project_id, status='active').first()
        if not project:
            flash('Invalid project selected', 'error')
            return render_template('timer/manual_entry.html', projects=active_projects)
        
        # Parse datetime
        try:
            start_utc = datetime.strptime(f'{start_date} {start_time}', '%Y-%m-%d %H:%M')
            end_utc = datetime.strptime(f'{end_date} {end_time}', '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format', 'error')
            return render_template('timer/manual_entry.html', projects=active_projects)
        
        # Validate time range
        if end_utc <= start_utc:
            flash('End time must be after start time', 'error')
            return render_template('timer/manual_entry.html', projects=active_projects)
        
        # Create manual entry
        entry = TimeEntry(
            user_id=current_user.id,
            project_id=project_id,
            start_utc=start_utc,
            end_utc=end_utc,
            notes=notes,
            tags=tags,
            source='manual',
            billable=billable
        )
        
        db.session.add(entry)
        db.session.commit()
        
        flash(f'Manual entry created for {project.name}', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('timer/manual_entry.html', projects=active_projects)
