from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Project, TimeEntry
from datetime import datetime
from decimal import Decimal

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
        query = query.filter(Project.client == client_name)
    
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
    
    # Distinct clients for filter dropdown
    clients = db.session.query(Project.client).distinct().order_by(Project.client).all()
    client_list = [c[0] for c in clients]
    
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
        flash('Only administrators can create projects', 'error')
        return redirect(url_for('projects.list_projects'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        client = request.form.get('client', '').strip()
        description = request.form.get('description', '').strip()
        billable = request.form.get('billable') == 'on'
        hourly_rate = request.form.get('hourly_rate', '').strip()
        billing_ref = request.form.get('billing_ref', '').strip()
        
        # Validate required fields
        if not name or not client:
            flash('Project name and client are required', 'error')
            return render_template('projects/create.html')
        
        # Validate hourly rate
        try:
            hourly_rate = Decimal(hourly_rate) if hourly_rate else None
        except ValueError:
            flash('Invalid hourly rate format', 'error')
            return render_template('projects/create.html')
        
        # Check if project name already exists
        if Project.query.filter_by(name=name).first():
            flash('A project with this name already exists', 'error')
            return render_template('projects/create.html')
        
        # Create project
        project = Project(
            name=name,
            client=client,
            description=description,
            billable=billable,
            hourly_rate=hourly_rate,
            billing_ref=billing_ref
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash(f'Project "{name}" created successfully', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/create.html')

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
    
    # Get user totals
    user_totals = project.get_user_totals()
    
    return render_template('projects/view.html', 
                         project=project, 
                         entries=entries_pagination.items,
                         pagination=entries_pagination,
                         user_totals=user_totals)

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
        client = request.form.get('client', '').strip()
        description = request.form.get('description', '').strip()
        billable = request.form.get('billable') == 'on'
        hourly_rate = request.form.get('hourly_rate', '').strip()
        billing_ref = request.form.get('billing_ref', '').strip()
        
        # Validate required fields
        if not name or not client:
            flash('Project name and client are required', 'error')
            return render_template('projects/edit.html', project=project)
        
        # Validate hourly rate
        try:
            hourly_rate = Decimal(hourly_rate) if hourly_rate else None
        except ValueError:
            flash('Invalid hourly rate format', 'error')
            return render_template('projects/edit.html', project=project)
        
        # Check if project name already exists (excluding current project)
        existing = Project.query.filter_by(name=name).first()
        if existing and existing.id != project.id:
            flash('A project with this name already exists', 'error')
            return render_template('projects/edit.html', project=project)
        
        # Update project
        project.name = name
        project.client = client
        project.description = description
        project.billable = billable
        project.hourly_rate = hourly_rate
        project.billing_ref = billing_ref
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Project "{name}" updated successfully', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    return render_template('projects/edit.html', project=project)

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
    db.session.commit()
    
    flash(f'Project "{project_name}" deleted successfully', 'success')
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/clients')
@login_required
def list_clients():
    """List all clients"""
    clients = db.session.query(Project.client).distinct().order_by(Project.client).all()
    client_list = [client[0] for client in clients]
    
    return render_template('projects/clients.html', clients=client_list)

@projects_bp.route('/clients/<client_name>')
@login_required
def view_client(client_name):
    """View projects for a specific client"""
    projects = Project.query.filter_by(client=client_name).order_by(Project.name).all()
    
    # Calculate totals for this client
    total_hours = sum(project.total_hours for project in projects)
    total_billable_hours = sum(project.total_billable_hours for project in projects)
    total_cost = sum(project.estimated_cost for project in projects)
    
    return render_template('projects/client_view.html',
                         client_name=client_name,
                         projects=projects,
                         total_hours=total_hours,
                         total_billable_hours=total_billable_hours,
                         total_cost=total_cost)
