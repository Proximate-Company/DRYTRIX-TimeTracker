from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models import Project, TimeEntry, Task, Client
from datetime import datetime
from decimal import Decimal
from app.utils.db import safe_commit

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects')
@login_required
def list_projects():
    """List all projects"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'active')
    client_name = request.args.get('client', '').strip()
    search = request.args.get('search', '').strip()
    
    query = Project.query
    if status == 'active':
        query = query.filter_by(status='active')
    elif status == 'archived':
        query = query.filter_by(status='archived')
    
    if client_name:
        query = query.join(Client).filter(Client.name == client_name)
    
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Project.name.ilike(like),
                Project.description.ilike(like)
            )
        )
    
    projects = query.order_by(Project.name).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # Get clients for filter dropdown
    clients = Client.get_active_clients()
    client_list = [c.name for c in clients]
    
    return render_template(
        'projects/list.html',
        projects=projects.items,
        status=status,
        clients=client_list
    )

@projects_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create a new project"""
    if not current_user.is_admin:
        try:
            current_app.logger.warning("Non-admin user attempted to create project: user=%s", current_user.username)
        except Exception:
            pass
        flash('Only administrators can create projects', 'error')
        return redirect(url_for('projects.list_projects'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        client_id = request.form.get('client_id', '').strip()
        description = request.form.get('description', '').strip()
        billable = request.form.get('billable') == 'on'
        hourly_rate = request.form.get('hourly_rate', '').strip()
        billing_ref = request.form.get('billing_ref', '').strip()
        try:
            current_app.logger.info(
                "POST /projects/create user=%s name=%s client_id=%s billable=%s",
                current_user.username,
                name or '<empty>',
                client_id or '<empty>',
                billable,
            )
        except Exception:
            pass
        
        # Validate required fields
        if not name or not client_id:
            flash('Project name and client are required', 'error')
            try:
                current_app.logger.warning("Validation failed: missing required fields for project creation")
            except Exception:
                pass
            return render_template('projects/create.html', clients=Client.get_active_clients())
        
        # Get client and validate
        client = Client.query.get(client_id)
        if not client:
            flash('Selected client not found', 'error')
            try:
                current_app.logger.warning("Validation failed: client not found (id=%s)", client_id)
            except Exception:
                pass
            return render_template('projects/create.html', clients=Client.get_active_clients())
        
        # Validate hourly rate
        try:
            hourly_rate = Decimal(hourly_rate) if hourly_rate else None
        except ValueError:
            flash('Invalid hourly rate format', 'error')
            try:
                current_app.logger.warning("Validation failed: invalid hourly rate '%s'", hourly_rate)
            except Exception:
                pass
            return render_template('projects/create.html', clients=Client.get_active_clients())
        
        # Check if project name already exists
        if Project.query.filter_by(name=name).first():
            flash('A project with this name already exists', 'error')
            try:
                current_app.logger.warning("Validation failed: duplicate project name '%s'", name)
            except Exception:
                pass
            return render_template('projects/create.html', clients=Client.get_active_clients())
        
        # Create project
        project = Project(
            name=name,
            client_id=client_id,
            description=description,
            billable=billable,
            hourly_rate=hourly_rate,
            billing_ref=billing_ref
        )
        
        db.session.add(project)
        if not safe_commit('create_project', {'name': name, 'client_id': client_id}):
            flash('Could not create project due to a database error. Please check server logs.', 'error')
            return render_template('projects/create.html', clients=Client.get_active_clients())
        
        flash(f'Project "{name}" created successfully', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/create.html', clients=Client.get_active_clients())

@projects_bp.route('/projects/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details and time entries"""
    project = Project.query.get_or_404(project_id)
    
    # Get time entries for this project
    page = request.args.get('page', 1, type=int)
    entries_pagination = project.time_entries.filter(
        TimeEntry.end_time.isnot(None)
    ).order_by(
        TimeEntry.start_time.desc()
    ).paginate(
        page=page,
        per_page=50,
        error_out=False
    )
    
    # Get tasks for this project
    tasks = project.tasks.order_by(Task.priority.desc(), Task.due_date.asc(), Task.created_at.asc()).all()
    
    # Get user totals
    user_totals = project.get_user_totals()
    
    # Get comments for this project
    from app.models import Comment
    comments = Comment.get_project_comments(project_id, include_replies=True)
    
    return render_template('projects/view.html', 
                         project=project, 
                         entries=entries_pagination.items,
                         pagination=entries_pagination,
                         tasks=tasks,
                         user_totals=user_totals,
                         comments=comments)

@projects_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit project details"""
    if not current_user.is_admin:
        flash('Only administrators can edit projects', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        client_id = request.form.get('client_id', '').strip()
        description = request.form.get('description', '').strip()
        billable = request.form.get('billable') == 'on'
        hourly_rate = request.form.get('hourly_rate', '').strip()
        billing_ref = request.form.get('billing_ref', '').strip()
        
        # Validate required fields
        if not name or not client_id:
            flash('Project name and client are required', 'error')
            return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())
        
        # Get client and validate
        client = Client.query.get(client_id)
        if not client:
            flash('Selected client not found', 'error')
            return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())
        
        # Validate hourly rate
        try:
            hourly_rate = Decimal(hourly_rate) if hourly_rate else None
        except ValueError:
            flash('Invalid hourly rate format', 'error')
            return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())
        
        # Check if project name already exists (excluding current project)
        existing = Project.query.filter_by(name=name).first()
        if existing and existing.id != project.id:
            flash('A project with this name already exists', 'error')
            return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())
        
        # Update project
        project.name = name
        project.client_id = client_id
        project.description = description
        project.billable = billable
        project.hourly_rate = hourly_rate
        project.billing_ref = billing_ref
        project.updated_at = datetime.utcnow()
        
        if not safe_commit('edit_project', {'project_id': project.id}):
            flash('Could not update project due to a database error. Please check server logs.', 'error')
            return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())
        
        flash(f'Project "{name}" updated successfully', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/edit.html', project=project, clients=Client.get_active_clients())

@projects_bp.route('/projects/<int:project_id>/archive', methods=['POST'])
@login_required
def archive_project(project_id):
    """Archive a project"""
    if not current_user.is_admin:
        flash('Only administrators can archive projects', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project = Project.query.get_or_404(project_id)
    
    if project.status == 'archived':
        flash('Project is already archived', 'info')
    else:
        project.archive()
        flash(f'Project "{project.name}" archived successfully', 'success')
    
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/projects/<int:project_id>/unarchive', methods=['POST'])
@login_required
def unarchive_project(project_id):
    """Unarchive a project"""
    if not current_user.is_admin:
        flash('Only administrators can unarchive projects', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project = Project.query.get_or_404(project_id)
    
    if project.status == 'active':
        flash('Project is already active', 'info')
    else:
        project.unarchive()
        flash(f'Project "{project.name}" unarchived successfully', 'success')
    
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete a project (only if no time entries exist)"""
    if not current_user.is_admin:
        flash('Only administrators can delete projects', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project = Project.query.get_or_404(project_id)
    
    # Check if project has time entries
    if project.time_entries.count() > 0:
        flash('Cannot delete project with existing time entries', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    project_name = project.name
    db.session.delete(project)
    if not safe_commit('delete_project', {'project_id': project.id}):
        flash('Could not delete project due to a database error. Please check server logs.', 'error')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    flash(f'Project "{project_name}" deleted successfully', 'success')
    return redirect(url_for('projects.list_projects'))


