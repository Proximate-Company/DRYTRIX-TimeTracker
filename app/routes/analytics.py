from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, TimeEntry, Settings, Task
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import calendar
from app.utils.tenancy import (
    get_current_organization_id,
    scoped_query,
    require_organization_access
)

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
@require_organization_access()
def analytics_dashboard():
    """Main analytics dashboard with charts"""
    # Check if user agent indicates mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    
    if is_mobile:
        return render_template('analytics/mobile_dashboard.html')
    else:
        return render_template('analytics/dashboard.html')

@analytics_bp.route('/api/analytics/hours-by-day')
@login_required
@require_organization_access()
def hours_by_day():
    """Get hours worked per day for the last 30 days"""
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Build query based on user permissions (scoped to organization)
    query = db.session.query(
        func.date(TimeEntry.start_time).label('date'),
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(func.date(TimeEntry.start_time)).all()
    
    # Create date range and fill missing dates with 0
    date_data = {}
    current_date = start_date
    while current_date <= end_date:
        date_data[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Fill in actual data
    for date_str, total_seconds in results:
        if date_str:
            date_data[date_str.strftime('%Y-%m-%d')] = round(total_seconds / 3600, 2)
    
    return jsonify({
        'labels': list(date_data.keys()),
        'datasets': [{
            'label': 'Hours Worked',
            'data': list(date_data.values()),
            'borderColor': '#3b82f6',
            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            'tension': 0.4,
            'fill': True
        }]
    })

@analytics_bp.route('/api/analytics/hours-by-project')
@login_required
@require_organization_access()
def hours_by_project():
    """Get total hours per project"""
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        Project.name,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(TimeEntry).filter(
        Project.organization_id == org_id,
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date,
        Project.status == 'active'
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(Project.name).order_by(func.sum(TimeEntry.duration_seconds).desc()).limit(10).all()
    
    labels = [project for project, _ in results]
    data = [round(seconds / 3600, 2) for _, seconds in results]
    
    # Generate colors for each project
    colors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
    ]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Hours',
            'data': data,
            'backgroundColor': colors[:len(labels)],
            'borderColor': colors[:len(labels)],
            'borderWidth': 1
        }]
    })

@analytics_bp.route('/api/analytics/hours-by-user')
@login_required
@require_organization_access()
def hours_by_user():
    """Get total hours per user (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    results = db.session.query(
        User.username,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(TimeEntry).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date,
        User.is_active == True
    ).group_by(User.username).order_by(func.sum(TimeEntry.duration_seconds).desc()).all()
    
    labels = [username for username, _ in results]
    data = [round(seconds / 3600, 2) for _, seconds in results]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Hours',
            'data': data,
            'backgroundColor': 'rgba(59, 130, 246, 0.8)',
            'borderColor': '#3b82f6',
            'borderWidth': 2
        }]
    })

@analytics_bp.route('/api/analytics/hours-by-hour')
@login_required
@require_organization_access()
def hours_by_hour():
    """Get hours worked by hour of day (24-hour format)"""
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        extract('hour', TimeEntry.start_time).label('hour'),
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(extract('hour', TimeEntry.start_time)).order_by(extract('hour', TimeEntry.start_time)).all()
    
    # Create 24-hour array
    hours_data = [0] * 24
    for hour, total_seconds in results:
        hours_data[int(hour)] = round(total_seconds / 3600, 2)
    
    labels = [f"{hour:02d}:00" for hour in range(24)]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Hours Worked',
            'data': hours_data,
            'backgroundColor': 'rgba(16, 185, 129, 0.8)',
            'borderColor': '#10b981',
            'borderWidth': 2,
            'tension': 0.4
        }]
    })

@analytics_bp.route('/api/analytics/billable-vs-nonbillable')
@login_required
@require_organization_access()
def billable_vs_nonbillable():
    """Get billable vs non-billable hours breakdown"""
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        TimeEntry.billable,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(TimeEntry.billable).all()
    
    billable_hours = 0
    nonbillable_hours = 0
    
    for billable, total_seconds in results:
        hours = round(total_seconds / 3600, 2)
        if billable:
            billable_hours = hours
        else:
            nonbillable_hours = hours
    
    return jsonify({
        'labels': ['Billable', 'Non-Billable'],
        'datasets': [{
            'label': 'Hours',
            'data': [billable_hours, nonbillable_hours],
            'backgroundColor': ['#10b981', '#6b7280'],
            'borderColor': ['#059669', '#4b5563'],
            'borderWidth': 2
        }]
    })

@analytics_bp.route('/api/analytics/weekly-trends')
@login_required
@require_organization_access()
def weekly_trends():
    """Get weekly trends over the last 12 weeks"""
    org_id = get_current_organization_id()
    weeks = int(request.args.get('weeks', 12))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(weeks=weeks)
    
    query = db.session.query(
        func.date_trunc('week', TimeEntry.start_time).label('week'),
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).filter(
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(func.date_trunc('week', TimeEntry.start_time)).order_by(func.date_trunc('week', TimeEntry.start_time)).all()
    
    labels = []
    data = []
    
    for week, total_seconds in results:
        if week:
            # Format week as "MMM DD" (e.g., "Jan 01")
            week_date = week.date()
            labels.append(week_date.strftime('%b %d'))
            data.append(round(total_seconds / 3600, 2))
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Weekly Hours',
            'data': data,
            'borderColor': '#8b5cf6',
            'backgroundColor': 'rgba(139, 92, 246, 0.1)',
            'tension': 0.4,
            'fill': True,
            'pointBackgroundColor': '#8b5cf6',
            'pointBorderColor': '#ffffff',
            'pointBorderWidth': 2
        }]
    })

@analytics_bp.route('/api/analytics/project-efficiency')
@login_required
@require_organization_access()
def project_efficiency():
    """Get project efficiency metrics (hours vs billable amount)"""
    org_id = get_current_organization_id()
    days = int(request.args.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        Project.name,
        func.sum(TimeEntry.duration_seconds).label('total_seconds'),
        Project.hourly_rate
    ).join(TimeEntry).filter(
        Project.organization_id == org_id,
        TimeEntry.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date,
        Project.status == 'active',
        Project.billable == True,
        Project.hourly_rate.isnot(None)
    )
    
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    
    results = query.group_by(Project.name, Project.hourly_rate).order_by(func.sum(TimeEntry.duration_seconds).desc()).limit(8).all()
    
    labels = [project for project, _, _ in results]
    hours_data = [round(seconds / 3600, 2) for _, seconds, _ in results]
    revenue_data = [round((seconds / 3600) * float(rate), 2) for _, seconds, rate in results]
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Hours',
                'data': hours_data,
                'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                'borderColor': '#3b82f6',
                'borderWidth': 2,
                'yAxisID': 'y'
            },
            {
                'label': 'Revenue',
                'data': revenue_data,
                'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                'borderColor': '#10b981',
                'borderWidth': 2,
                'yAxisID': 'y1'
            }
        ]
    })


@analytics_bp.route('/api/analytics/today-by-task')
@login_required
@require_organization_access()
def today_by_task():
    """Get today's total hours grouped by task (includes project-level entries without task).

    Optional query params:
    - date: YYYY-MM-DD (defaults to today)
    - user_id: admin-only override to view a specific user's data
    """
    # Parse target date
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    else:
        target_date = datetime.now().date()

    # Base query (scoped to organization)
    org_id = get_current_organization_id()
    query = db.session.query(
        TimeEntry.task_id,
        Task.name.label('task_name'),
        TimeEntry.project_id,
        Project.name.label('project_name'),
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(
        Project, Project.id == TimeEntry.project_id
    ).outerjoin(
        Task, Task.id == TimeEntry.task_id
    ).filter(
        TimeEntry.organization_id == org_id,
        Project.organization_id == org_id,
        TimeEntry.end_time.isnot(None),
        func.date(TimeEntry.start_time) == target_date
    )

    # Scope to current user unless admin (with optional override)
    if not current_user.is_admin:
        query = query.filter(TimeEntry.user_id == current_user.id)
    else:
        user_id = request.args.get('user_id', type=int)
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)

    results = query.group_by(
        TimeEntry.task_id,
        Task.name,
        TimeEntry.project_id,
        Project.name
    ).order_by(func.sum(TimeEntry.duration_seconds).desc()).all()

    rows = []
    for task_id, task_name, project_id, project_name, total_seconds in results:
        total_seconds = int(total_seconds or 0)
        total_hours = round(total_seconds / 3600, 2)
        label = f"{project_name} • {task_name}" if task_name else f"{project_name} • No task"
        rows.append({
            'task_id': task_id,
            'task_name': task_name,
            'project_id': project_id,
            'project_name': project_name,
            'total_seconds': total_seconds,
            'total_hours': total_hours,
            'label': label
        })

    return jsonify({
        'date': target_date.strftime('%Y-%m-%d'),
        'rows': rows
    })
