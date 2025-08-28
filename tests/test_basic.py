import pytest
from app import create_app, db
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def user(app):
    """Create a test user"""
    user = User(username='testuser', role='user')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_user(app):
    """Create a test admin user"""
    admin = User(username='admin', role='admin')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def project(app):
    """Create a test project"""
    project = Project(
        name='Test Project',
        client='Test Client',
        description='Test project description',
        billable=True,
        hourly_rate=50.00
    )
    db.session.add(project)
    db.session.commit()
    return project

def test_app_creation(app):
    """Test that the app can be created"""
    assert app is not None
    assert app.config['TESTING'] is True

def test_database_creation(app):
    """Test that database tables can be created"""
    with app.app_context():
        # Check that tables exist
        assert db.engine.dialect.has_table(db.engine, 'users')
        assert db.engine.dialect.has_table(db.engine, 'projects')
        assert db.engine.dialect.has_table(db.engine, 'time_entries')
        assert db.engine.dialect.has_table(db.engine, 'settings')

def test_user_creation(app):
    """Test user creation"""
    with app.app_context():
        user = User(username='testuser', role='user')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.role == 'user'
        assert user.is_admin is False

def test_admin_user(app):
    """Test admin user properties"""
    with app.app_context():
        admin = User(username='admin', role='admin')
        db.session.add(admin)
        db.session.commit()
        
        assert admin.is_admin is True

def test_project_creation(app):
    """Test project creation"""
    with app.app_context():
        project = Project(
            name='Test Project',
            client='Test Client',
            description='Test description',
            billable=True,
            hourly_rate=50.00
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.id is not None
        assert project.name == 'Test Project'
        assert project.client == 'Test Client'
        assert project.billable is True
        assert float(project.hourly_rate) == 50.00

def test_time_entry_creation(app, user, project):
    """Test time entry creation"""
    with app.app_context():
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        entry = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=start_time,
            end_time=end_time,
            notes='Test entry',
            tags='test,work',
            source='manual'
        )
        db.session.add(entry)
        db.session.commit()
        
        assert entry.id is not None
        assert entry.duration_hours == 2.0
        assert entry.duration_formatted == '02:00:00'
        assert entry.tag_list == ['test', 'work']

def test_active_timer(app, user, project):
    """Test active timer functionality"""
    with app.app_context():
        # Create active timer
        timer = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=datetime.utcnow(),
            source='auto'
        )
        db.session.add(timer)
        db.session.commit()
        
        assert timer.is_active is True
        assert timer.end_time is None
        
        # Stop timer
        timer.stop_timer()
        assert timer.is_active is False
        assert timer.end_time is not None
        assert timer.duration_seconds > 0

def test_user_active_timer_property(app, user, project):
    """Test user active timer property"""
    with app.app_context():
        # No active timer initially
        assert user.active_timer is None
        
        # Create active timer
        timer = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=datetime.utcnow(),
            source='auto'
        )
        db.session.add(timer)
        db.session.commit()
        
        # Check active timer
        assert user.active_timer is not None
        assert user.active_timer.id == timer.id

def test_project_totals(app, user, project):
    """Test project total calculations"""
    with app.app_context():
        # Create time entries
        start_time = datetime.utcnow()
        entry1 = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            source='manual'
        )
        entry2 = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=start_time + timedelta(hours=3),
            end_time=start_time + timedelta(hours=5),
            source='manual'
        )
        db.session.add_all([entry1, entry2])
        db.session.commit()
        
        # Check totals
        assert project.total_hours == 4.0
        assert project.total_billable_hours == 4.0
        assert float(project.estimated_cost) == 200.00  # 4 hours * 50 EUR

def test_settings_singleton(app):
    """Test settings singleton pattern"""
    with app.app_context():
        # Get settings (should create if not exists)
        settings1 = Settings.get_settings()
        settings2 = Settings.get_settings()
        
        assert settings1.id == settings2.id
        assert settings1 is settings2

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/_health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_login_page(client):
    """Test login page accessibility"""
    response = client.get('/login')
    assert response.status_code == 200

def test_protected_route_redirect(client):
    """Test that protected routes redirect to login"""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location
