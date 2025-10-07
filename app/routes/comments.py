from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models import Comment, Project, Task
from app.utils.db import safe_commit
from app.utils.tenancy import (
    get_current_organization_id,
    scoped_query,
    require_organization_access
)

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/comments/create', methods=['POST'])
@login_required
@require_organization_access()
def create_comment():
    """Create a new comment for a project or task"""
    try:
        org_id = get_current_organization_id()
        content = request.form.get('content', '').strip()
        project_id = request.form.get('project_id', type=int)
        task_id = request.form.get('task_id', type=int)
        parent_id = request.form.get('parent_id', type=int)
        
        # Validation
        if not content:
            flash(_('Comment content cannot be empty'), 'error')
            return redirect(request.referrer or url_for('main.dashboard'))
        
        if not project_id and not task_id:
            flash(_('Comment must be associated with a project or task'), 'error')
            return redirect(request.referrer or url_for('main.dashboard'))
        
        if project_id and task_id:
            flash(_('Comment cannot be associated with both a project and a task'), 'error')
            return redirect(request.referrer or url_for('main.dashboard'))
        
        # Verify project or task exists (scoped to organization)
        if project_id:
            target = scoped_query(Project).filter_by(id=project_id).first_or_404()
            target_type = 'project'
        else:
            target = scoped_query(Task).filter_by(id=task_id).first_or_404()
            target_type = 'task'
            project_id = target.project_id  # For redirects
        
        # If this is a reply, verify parent comment exists (scoped to organization)
        if parent_id:
            parent_comment = scoped_query(Comment).filter_by(id=parent_id).first_or_404()
            # Verify parent is for the same target
            if (project_id and parent_comment.project_id != project_id) or \
               (task_id and parent_comment.task_id != task_id):
                flash(_('Invalid parent comment'), 'error')
                return redirect(request.referrer or url_for('main.dashboard'))
        
        # Create the comment with organization_id
        comment = Comment(
            content=content,
            user_id=current_user.id,
            organization_id=org_id,
            project_id=project_id if target_type == 'project' else None,
            task_id=task_id if target_type == 'task' else None,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        if safe_commit():
            flash(_('Comment added successfully'), 'success')
        else:
            flash(_('Error adding comment'), 'error')
    
    except Exception as e:
        flash(_('Error adding comment: %(error)s', error=str(e)), 'error')
    
    # Redirect back to the source page
    if project_id:
        return redirect(url_for('projects.view_project', project_id=project_id))
    elif task_id:
        return redirect(url_for('tasks.view_task', task_id=task_id))
    else:
        return redirect(url_for('main.dashboard'))

@comments_bp.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
@require_organization_access()
def edit_comment(comment_id):
    """Edit an existing comment"""
    comment = scoped_query(Comment).filter_by(id=comment_id).first_or_404()
    
    # Check permissions
    if not comment.can_edit(current_user):
        flash(_('You do not have permission to edit this comment'), 'error')
        return redirect(request.referrer or url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            content = request.form.get('content', '').strip()
            
            if not content:
                flash(_('Comment content cannot be empty'), 'error')
                return render_template('comments/edit.html', comment=comment)
            
            comment.edit_content(content, current_user)
            flash(_('Comment updated successfully'), 'success')
            
            # Redirect back to the source page
            if comment.project_id:
                return redirect(url_for('projects.view_project', project_id=comment.project_id))
            elif comment.task_id:
                return redirect(url_for('tasks.view_task', task_id=comment.task_id))
            else:
                return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            flash(_('Error updating comment: %(error)s', error=str(e)), 'error')
    
    return render_template('comments/edit.html', comment=comment)

@comments_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@require_organization_access()
def delete_comment(comment_id):
    """Delete a comment"""
    comment = scoped_query(Comment).filter_by(id=comment_id).first_or_404()
    
    # Check permissions
    if not comment.can_delete(current_user):
        flash(_('You do not have permission to delete this comment'), 'error')
        return redirect(request.referrer or url_for('main.dashboard'))
    
    try:
        project_id = comment.project_id
        task_id = comment.task_id
        
        comment.delete_comment(current_user)
        flash(_('Comment deleted successfully'), 'success')
        
        # Redirect back to the source page
        if project_id:
            return redirect(url_for('projects.view_project', project_id=project_id))
        elif task_id:
            return redirect(url_for('tasks.view_task', task_id=task_id))
        else:
            return redirect(url_for('main.dashboard'))
    
    except Exception as e:
        flash(_('Error deleting comment: %(error)s', error=str(e)), 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

@comments_bp.route('/api/comments')
@login_required
@require_organization_access()
def list_comments():
    """API endpoint to get comments for a project or task"""
    project_id = request.args.get('project_id', type=int)
    task_id = request.args.get('task_id', type=int)
    include_replies = request.args.get('include_replies', 'true').lower() == 'true'
    
    if not project_id and not task_id:
        return jsonify({'error': 'project_id or task_id is required'}), 400
    
    if project_id and task_id:
        return jsonify({'error': 'Cannot specify both project_id and task_id'}), 400
    
    try:
        if project_id:
            # Verify project exists (scoped to organization)
            project = scoped_query(Project).filter_by(id=project_id).first_or_404()
            comments = Comment.get_project_comments(project_id, include_replies)
        else:
            # Verify task exists (scoped to organization)
            task = scoped_query(Task).filter_by(id=task_id).first_or_404()
            comments = Comment.get_task_comments(task_id, include_replies)
        
        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comments_bp.route('/api/comments/<int:comment_id>')
@login_required
@require_organization_access()
def get_comment(comment_id):
    """API endpoint to get a single comment"""
    try:
        comment = scoped_query(Comment).filter_by(id=comment_id).first_or_404()
        return jsonify({
            'success': True,
            'comment': comment.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comments_bp.route('/api/comments/recent')
@login_required
@require_organization_access()
def get_recent_comments():
    """API endpoint to get recent comments"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        # Get recent comments scoped to organization
        comments = scoped_query(Comment).order_by(Comment.created_at.desc()).limit(limit).all()
        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comments_bp.route('/api/comments/user/<int:user_id>')
@login_required
@require_organization_access()
def get_user_comments(user_id):
    """API endpoint to get comments by a specific user"""
    limit = request.args.get('limit', type=int)
    
    # Only allow users to see their own comments unless they're admin
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Get user comments scoped to organization
        query = scoped_query(Comment).filter_by(user_id=user_id).order_by(Comment.created_at.desc())
        if limit:
            query = query.limit(limit)
        comments = query.all()
        return jsonify({
            'success': True,
            'comments': [comment.to_dict() for comment in comments]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
