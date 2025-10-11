from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db, socketio
from app.models import KanbanColumn, Task
from app.utils.db import safe_commit
from app.routes.admin import admin_required

kanban_bp = Blueprint('kanban', __name__)

@kanban_bp.route('/kanban/columns')
@login_required
@admin_required
def list_columns():
    """List all kanban columns for management"""
    # Force fresh data from database - clear all caches
    db.session.expire_all()
    columns = KanbanColumn.get_all_columns()
    
    # Prevent browser caching
    response = render_template('kanban/columns.html', columns=columns)
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@kanban_bp.route('/kanban/columns/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_column():
    """Create a new kanban column"""
    if request.method == 'POST':
        key = request.form.get('key', '').strip().lower().replace(' ', '_')
        label = request.form.get('label', '').strip()
        icon = request.form.get('icon', 'fas fa-circle').strip()
        color = request.form.get('color', 'secondary').strip()
        is_complete_state = request.form.get('is_complete_state') == 'on'
        
        # Validate required fields
        if not key or not label:
            flash('Key and label are required', 'error')
            return render_template('kanban/create_column.html')
        
        # Check if key already exists
        existing = KanbanColumn.get_column_by_key(key)
        if existing:
            flash(f'A column with key "{key}" already exists', 'error')
            return render_template('kanban/create_column.html')
        
        # Get max position and add 1
        max_position = db.session.query(db.func.max(KanbanColumn.position)).scalar() or -1
        
        # Create column
        column = KanbanColumn(
            key=key,
            label=label,
            icon=icon,
            color=color,
            position=max_position + 1,
            is_complete_state=is_complete_state,
            is_system=False,
            is_active=True
        )
        
        db.session.add(column)
        
        # Explicitly flush to write to database immediately
        try:
            db.session.flush()
        except Exception as e:
            db.session.rollback()
            flash(f'Could not create column: {str(e)}', 'error')
            print(f"[KANBAN] Flush failed: {e}")
            return render_template('kanban/create_column.html')
        
        # Now commit the transaction
        if not safe_commit('create_kanban_column', {'key': key}):
            flash('Could not create column due to a database error. Please check server logs.', 'error')
            return render_template('kanban/create_column.html')
        
        print(f"[KANBAN] Column '{key}' committed to database successfully")
        
        flash(f'Column "{label}" created successfully', 'success')
        # Clear any SQLAlchemy cache to ensure fresh data on next load
        db.session.expire_all()
        # Notify all connected clients to refresh kanban boards
        try:
            print(f"[KANBAN] Emitting kanban_columns_updated event: created column '{key}'")
            socketio.emit('kanban_columns_updated', {'action': 'created', 'column_key': key}, broadcast=True)
            print(f"[KANBAN] Event emitted successfully")
        except Exception as e:
            print(f"[KANBAN] Failed to emit event: {e}")
        return redirect(url_for('kanban.list_columns'))
    
    return render_template('kanban/create_column.html')

@kanban_bp.route('/kanban/columns/<int:column_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_column(column_id):
    """Edit an existing kanban column"""
    column = KanbanColumn.query.get_or_404(column_id)
    
    if request.method == 'POST':
        label = request.form.get('label', '').strip()
        icon = request.form.get('icon', 'fas fa-circle').strip()
        color = request.form.get('color', 'secondary').strip()
        is_complete_state = request.form.get('is_complete_state') == 'on'
        is_active = request.form.get('is_active') == 'on'
        
        # Validate required fields
        if not label:
            flash('Label is required', 'error')
            return render_template('kanban/edit_column.html', column=column)
        
        # Update column
        column.label = label
        column.icon = icon
        column.color = color
        column.is_complete_state = is_complete_state
        column.is_active = is_active
        
        # Explicitly flush to write changes immediately
        try:
            db.session.flush()
        except Exception as e:
            db.session.rollback()
            flash(f'Could not update column: {str(e)}', 'error')
            print(f"[KANBAN] Flush failed: {e}")
            return render_template('kanban/edit_column.html', column=column)
        
        # Now commit the transaction
        if not safe_commit('edit_kanban_column', {'column_id': column_id}):
            flash('Could not update column due to a database error. Please check server logs.', 'error')
            return render_template('kanban/edit_column.html', column=column)
        
        print(f"[KANBAN] Column {column_id} updated and committed to database successfully")
        
        flash(f'Column "{label}" updated successfully', 'success')
        # Clear any SQLAlchemy cache to ensure fresh data on next load
        db.session.expire_all()
        # Notify all connected clients to refresh kanban boards
        try:
            print(f"[KANBAN] Emitting kanban_columns_updated event: updated column ID {column_id}")
            socketio.emit('kanban_columns_updated', {'action': 'updated', 'column_id': column_id}, broadcast=True)
            print(f"[KANBAN] Event emitted successfully")
        except Exception as e:
            print(f"[KANBAN] Failed to emit event: {e}")
        return redirect(url_for('kanban.list_columns'))
    
    return render_template('kanban/edit_column.html', column=column)

@kanban_bp.route('/kanban/columns/<int:column_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_column(column_id):
    """Delete a kanban column (only if not system and has no tasks)"""
    column = KanbanColumn.query.get_or_404(column_id)
    
    # Check if system column
    if column.is_system:
        flash('System columns cannot be deleted', 'error')
        return redirect(url_for('kanban.list_columns'))
    
    # Check if column has tasks
    task_count = Task.query.filter_by(status=column.key).count()
    if task_count > 0:
        flash(f'Cannot delete column with {task_count} task(s). Move or delete tasks first.', 'error')
        return redirect(url_for('kanban.list_columns'))
    
    column_name = column.label
    db.session.delete(column)
    
    # Explicitly flush to execute delete immediately
    try:
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        flash(f'Could not delete column: {str(e)}', 'error')
        print(f"[KANBAN] Flush failed: {e}")
        return redirect(url_for('kanban.list_columns'))
    
    # Now commit the transaction
    if not safe_commit('delete_kanban_column', {'column_id': column_id}):
        flash('Could not delete column due to a database error. Please check server logs.', 'error')
        return redirect(url_for('kanban.list_columns'))
    
    print(f"[KANBAN] Column {column_id} deleted and committed to database successfully")
    
    flash(f'Column "{column_name}" deleted successfully', 'success')
    # Clear any SQLAlchemy cache to ensure fresh data on next load
    db.session.expire_all()
    # Notify all connected clients to refresh kanban boards
    try:
        print(f"[KANBAN] Emitting kanban_columns_updated event: deleted column ID {column_id}")
        socketio.emit('kanban_columns_updated', {'action': 'deleted', 'column_id': column_id}, broadcast=True)
        print(f"[KANBAN] Event emitted successfully")
    except Exception as e:
        print(f"[KANBAN] Failed to emit event: {e}")
    return redirect(url_for('kanban.list_columns'))

@kanban_bp.route('/kanban/columns/<int:column_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_column(column_id):
    """Toggle column active status"""
    column = KanbanColumn.query.get_or_404(column_id)
    
    column.is_active = not column.is_active
    
    # Explicitly flush to write changes immediately
    try:
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        flash(f'Could not toggle column: {str(e)}', 'error')
        print(f"[KANBAN] Flush failed: {e}")
        return redirect(url_for('kanban.list_columns'))
    
    # Now commit the transaction
    if not safe_commit('toggle_kanban_column', {'column_id': column_id}):
        flash('Could not toggle column due to a database error. Please check server logs.', 'error')
        return redirect(url_for('kanban.list_columns'))
    
    print(f"[KANBAN] Column {column_id} toggled and committed to database successfully")
    
    status = 'activated' if column.is_active else 'deactivated'
    flash(f'Column "{column.label}" {status} successfully', 'success')
    # Clear any SQLAlchemy cache to ensure fresh data on next load
    db.session.expire_all()
    # Notify all connected clients to refresh kanban boards
    try:
        print(f"[KANBAN] Emitting kanban_columns_updated event: toggled column ID {column_id}")
        socketio.emit('kanban_columns_updated', {'action': 'toggled', 'column_id': column_id}, broadcast=True)
        print(f"[KANBAN] Event emitted successfully")
    except Exception as e:
        print(f"[KANBAN] Failed to emit event: {e}")
    return redirect(url_for('kanban.list_columns'))

@kanban_bp.route('/api/kanban/columns/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_columns():
    """Reorder kanban columns via API"""
    data = request.get_json()
    column_ids = data.get('column_ids', [])
    
    if not column_ids:
        return jsonify({'error': 'No column IDs provided'}), 400
    
    try:
        # Reorder columns
        KanbanColumn.reorder_columns(column_ids)
        
        # Explicitly flush to write changes immediately
        db.session.flush()
        
        # Force database commit
        db.session.commit()
        
        print(f"[KANBAN] Columns reordered and committed to database successfully")
        
        # Clear all caches to force fresh reads
        db.session.expire_all()
        
        # Notify all connected clients to refresh kanban boards
        try:
            print(f"[KANBAN] Emitting kanban_columns_updated event: reordered columns")
            socketio.emit('kanban_columns_updated', {'action': 'reordered'}, broadcast=True)
            print(f"[KANBAN] Event emitted successfully")
        except Exception as e:
            print(f"[KANBAN] Failed to emit event: {e}")
        
        return jsonify({'success': True, 'message': 'Columns reordered successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@kanban_bp.route('/api/kanban/columns')
@login_required
def api_list_columns():
    """API endpoint to get all active kanban columns"""
    # Force fresh data - no caching
    db.session.expire_all()
    columns = KanbanColumn.get_active_columns()
    response = jsonify({'columns': [col.to_dict() for col in columns]})
    # Add no-cache headers to avoid SW/browser caching
    try:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    except Exception:
        pass
    return response

