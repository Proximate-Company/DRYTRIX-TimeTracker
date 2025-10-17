import pytest
from app import db
from app.models import User, Project, TimeEntry
from datetime import datetime, timedelta
from app.models import Task

@pytest.fixture
def sample_data(app):
    with app.app_context():
        # Create test user
        user = User(username='testuser', role='user')
        user.is_active = True
        db.session.add(user)
        
        # Create test project
        project = Project(name='Test Project', client='Test Client')
        db.session.add(project)
        
        db.session.commit()
        
        # Store IDs before session ends
        user_id = user.id
        project_id = project.id
        
        # Create test time entries
        base_time = datetime.now() - timedelta(days=5)
        for i in range(5):
            entry = TimeEntry(
                user_id=user_id,
                project_id=project_id,
                start_time=base_time + timedelta(days=i),
                end_time=base_time + timedelta(days=i, hours=8),
                billable=True
            )
            db.session.add(entry)
        
        # Create some tasks for task-completion endpoint
        t1 = Task(project_id=project_id, name='T1', status='done', created_by=user_id, assigned_to=user_id)
        t1.completed_at = datetime.now() - timedelta(days=1)
        db.session.add(t1)
        t2 = Task(project_id=project_id, name='T2', status='in_progress', created_by=user_id, assigned_to=user_id)
        db.session.add(t2)
        t3 = Task(project_id=project_id, name='T3', status='todo', created_by=user_id, assigned_to=user_id)
        db.session.add(t3)

        db.session.commit()
        
        return {'user_id': user_id, 'project_id': project_id}

@pytest.mark.integration
@pytest.mark.routes
def test_analytics_dashboard_requires_login(client):
    """Test that analytics dashboard requires authentication"""
    response = client.get('/analytics')
    assert response.status_code == 302  # Redirect to login

@pytest.mark.integration
@pytest.mark.routes
def test_analytics_dashboard_accessible_when_logged_in(client, app, sample_data):
    """Test that analytics dashboard is accessible when logged in"""
    with app.app_context():
        with client.session_transaction() as sess:
            # Simulate login
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/analytics')
        assert response.status_code == 200
        assert b'Analytics Dashboard' in response.data

@pytest.mark.integration
@pytest.mark.api
def test_hours_by_day_api(client, app, sample_data):
    """Test hours by day API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/hours-by-day?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data
        assert len(data['datasets']) > 0

@pytest.mark.integration
@pytest.mark.api
def test_hours_by_project_api(client, app, sample_data):
    """Test hours by project API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/hours-by-project?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data
        assert len(data['labels']) > 0

@pytest.mark.integration
@pytest.mark.api
def test_billable_vs_nonbillable_api(client, app, sample_data):
    """Test billable vs non-billable API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/billable-vs-nonbillable?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data
        assert len(data['labels']) == 2  # Billable and Non-Billable

@pytest.mark.integration
@pytest.mark.api
def test_hours_by_hour_api(client, app, sample_data):
    """Test hours by hour API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/hours-by-hour?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data
        assert len(data['labels']) == 24  # 24 hours

@pytest.mark.integration
@pytest.mark.api
def test_weekly_trends_api(client, app, sample_data):
    """Test weekly trends API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/weekly-trends?weeks=4')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data

@pytest.mark.integration
@pytest.mark.api
def test_task_completion_api(client, app, sample_data):
    """Test task completion analytics API endpoint structure"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True

        response = client.get('/api/analytics/task-completion?days=7')
        assert response.status_code == 200

        data = response.get_json()
        assert 'status_breakdown' in data
        sb = data['status_breakdown'] or {}
        # Ensure essential keys exist
        for key in ['done', 'in_progress', 'todo', 'review', 'cancelled']:
            assert key in sb

@pytest.mark.integration
@pytest.mark.api
def test_project_efficiency_api(client, app, sample_data):
    """Test project efficiency API endpoint"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/project-efficiency?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data

@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
def test_user_performance_api_requires_admin(client, app, sample_data):
    """Test that user performance API requires admin access"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/hours-by-user?days=7')
        assert response.status_code == 403  # Forbidden for non-admin users

@pytest.mark.integration
@pytest.mark.api
def test_user_performance_api_accessible_by_admin(client, app, sample_data):
    """Test that user performance API is accessible by admin users"""
    with app.app_context():
        # Make user admin
        user_id = sample_data['user_id']
        user = db.session.get(User, user_id)
        user.role = 'admin'
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get('/api/analytics/hours-by-user?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'datasets' in data

@pytest.mark.integration
@pytest.mark.api
def test_api_endpoints_with_invalid_parameters(client, app, sample_data):
    """Test API endpoints with invalid parameters"""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_data['user_id'])
            sess['_fresh'] = True
        
        # Test with invalid days parameter
        response = client.get('/api/analytics/hours-by-day?days=invalid')
        assert response.status_code == 400  # Should return 400 for invalid parameter
        
        # Test with missing parameter (should use default)
        response = client.get('/api/analytics/hours-by-day')
        assert response.status_code == 200
