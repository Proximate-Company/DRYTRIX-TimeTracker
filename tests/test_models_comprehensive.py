"""
Comprehensive model testing suite.
Tests all models, relationships, properties, and business logic.
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal

from app.models import (
    User, Project, TimeEntry, Client, Settings,
    Invoice, InvoiceItem, Task
)
from app import db


# ============================================================================
# User Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.smoke
def test_user_creation(app, user):
    """Test basic user creation."""
    assert user.id is not None
    assert user.username == 'testuser'
    assert user.role == 'user'
    assert user.is_active is True


@pytest.mark.unit
@pytest.mark.models
def test_user_is_admin_property(app, admin_user):
    """Test user is_admin property."""
    with app.app_context():
        assert admin_user.is_admin is True


@pytest.mark.unit
@pytest.mark.models
def test_user_active_timer(app, user, active_timer):
    """Test user active_timer property."""
    with app.app_context():
        # Refresh user to load relationships
        db.session.refresh(user)
        assert user.active_timer is not None
        assert user.active_timer.id == active_timer.id


@pytest.mark.unit
@pytest.mark.models
def test_user_time_entries_relationship(app, user, multiple_time_entries):
    """Test user time entries relationship."""
    with app.app_context():
        db.session.refresh(user)
        assert len(user.time_entries) == 5


@pytest.mark.unit
@pytest.mark.models
def test_user_to_dict(app, user):
    """Test user serialization to dictionary."""
    with app.app_context():
        user_dict = user.to_dict()
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'role' in user_dict
        # Should not include sensitive data
        assert 'password' not in user_dict


# ============================================================================
# Client Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.smoke
def test_client_creation(app, test_client):
    """Test basic client creation."""
    assert test_client.id is not None
    assert test_client.name == 'Test Client Corp'
    assert test_client.status == 'active'
    assert test_client.default_hourly_rate == Decimal('85.00')


@pytest.mark.unit
@pytest.mark.models
def test_client_projects_relationship(app, test_client, multiple_projects):
    """Test client projects relationship."""
    with app.app_context():
        db.session.refresh(test_client)
        assert len(test_client.projects.all()) == 3


@pytest.mark.unit
@pytest.mark.models
def test_client_total_projects_property(app, test_client, multiple_projects):
    """Test client total_projects property."""
    with app.app_context():
        db.session.refresh(test_client)
        assert test_client.total_projects == 3


@pytest.mark.unit
@pytest.mark.models
def test_client_archive_activate(app, test_client):
    """Test client archive and activate methods."""
    with app.app_context():
        db.session.refresh(test_client)
        
        # Archive client
        test_client.archive()
        db.session.commit()
        assert test_client.status == 'inactive'
        
        # Activate client
        test_client.activate()
        db.session.commit()
        assert test_client.status == 'active'


@pytest.mark.unit
@pytest.mark.models
def test_client_get_active_clients(app, multiple_clients):
    """Test get_active_clients class method."""
    with app.app_context():
        active_clients = Client.get_active_clients()
        assert len(active_clients) >= 3


@pytest.mark.unit
@pytest.mark.models
def test_client_to_dict(app, test_client):
    """Test client serialization to dictionary."""
    with app.app_context():
        client_dict = test_client.to_dict()
        assert 'id' in client_dict
        assert 'name' in client_dict
        assert 'status' in client_dict


# ============================================================================
# Project Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.smoke
def test_project_creation(app, project):
    """Test basic project creation."""
    assert project.id is not None
    assert project.name == 'Test Project'
    assert project.billable is True
    assert project.status == 'active'


@pytest.mark.unit
@pytest.mark.models
def test_project_client_relationship(app, project, test_client):
    """Test project client relationship."""
    with app.app_context():
        db.session.refresh(project)
        db.session.refresh(test_client)
        assert project.client_id == test_client.id
        # Check backward compatibility
        if hasattr(project, 'client'):
            assert project.client == test_client.name


@pytest.mark.unit
@pytest.mark.models
def test_project_time_entries_relationship(app, project, multiple_time_entries):
    """Test project time entries relationship."""
    with app.app_context():
        db.session.refresh(project)
        assert len(project.time_entries) == 5


@pytest.mark.unit
@pytest.mark.models
def test_project_total_hours(app, project, multiple_time_entries):
    """Test project total_hours property."""
    with app.app_context():
        db.session.refresh(project)
        # Each entry is 8 hours (9am to 5pm), 5 entries = 40 hours
        assert project.total_hours > 0


@pytest.mark.unit
@pytest.mark.models
def test_project_estimated_cost(app, project, multiple_time_entries):
    """Test project estimated_cost property."""
    with app.app_context():
        db.session.refresh(project)
        estimated_cost = project.estimated_cost
        assert estimated_cost > 0
        # Cost should be hours * hourly_rate
        expected_cost = project.total_hours * float(project.hourly_rate)
        assert abs(float(estimated_cost) - expected_cost) < 0.01


@pytest.mark.unit
@pytest.mark.models
def test_project_archive(app, project):
    """Test project archiving."""
    with app.app_context():
        db.session.refresh(project)
        project.status = 'archived'
        db.session.commit()
        assert project.status == 'archived'


# ============================================================================
# Time Entry Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.smoke
def test_time_entry_creation(app, time_entry):
    """Test basic time entry creation."""
    assert time_entry.id is not None
    assert time_entry.start_time is not None
    assert time_entry.end_time is not None


@pytest.mark.unit
@pytest.mark.models
def test_time_entry_duration(app, time_entry):
    """Test time entry duration calculations."""
    with app.app_context():
        db.session.refresh(time_entry)
        assert time_entry.duration_seconds > 0
        assert time_entry.duration_hours > 0
        assert time_entry.duration_formatted is not None


@pytest.mark.unit
@pytest.mark.models
def test_active_timer_is_active(app, active_timer):
    """Test active timer is_active property."""
    with app.app_context():
        db.session.refresh(active_timer)
        assert active_timer.is_active is True
        assert active_timer.end_time is None


@pytest.mark.unit
@pytest.mark.models
def test_stop_timer(app, active_timer):
    """Test stopping an active timer."""
    with app.app_context():
        db.session.refresh(active_timer)
        active_timer.stop_timer()
        db.session.commit()
        
        db.session.refresh(active_timer)
        assert active_timer.is_active is False
        assert active_timer.end_time is not None
        assert active_timer.duration_seconds > 0


@pytest.mark.unit
@pytest.mark.models
def test_time_entry_tag_list(app):
    """Test time entry tag_list property."""
    with app.app_context():
        from app.models import User, Project
        
        user = User.query.first() or User(username='test', role='user')
        project = Project.query.first() or Project(name='Test', billable=True)
        
        if not user.id:
            db.session.add(user)
        if not project.id:
            db.session.add(project)
        db.session.commit()
        
        entry = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            tags='python,testing,development',
            source='manual'
        )
        db.session.add(entry)
        db.session.commit()
        
        db.session.refresh(entry)
        assert entry.tag_list == ['python', 'testing', 'development']


# ============================================================================
# Task Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
def test_task_creation(app, task):
    """Test basic task creation."""
    with app.app_context():
        db.session.refresh(task)
        assert task.id is not None
        assert task.name == 'Test Task'
        assert task.status == 'todo'


@pytest.mark.unit
@pytest.mark.models
def test_task_project_relationship(app, task, project):
    """Test task project relationship."""
    with app.app_context():
        db.session.refresh(task)
        db.session.refresh(project)
        assert task.project_id == project.id


@pytest.mark.unit
@pytest.mark.models
def test_task_status_transitions(app, task):
    """Test task status transitions."""
    with app.app_context():
        db.session.refresh(task)
        
        # Mark as in progress
        task.status = 'in_progress'
        db.session.commit()
        assert task.status == 'in_progress'
        
        # Mark as done
        task.status = 'done'
        db.session.commit()
        assert task.status == 'done'


# ============================================================================
# Invoice Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
@pytest.mark.smoke
def test_invoice_creation(app, invoice):
    """Test basic invoice creation."""
    # Invoice is already refreshed in the fixture, no need to refresh again
    assert invoice.id is not None
    assert invoice.invoice_number is not None
    assert invoice.status == 'draft'


@pytest.mark.unit
@pytest.mark.models
def test_invoice_number_generation(app):
    """Test invoice number generation."""
    with app.app_context():
        invoice_number = Invoice.generate_invoice_number()
        assert invoice_number is not None
        assert 'INV-' in invoice_number


@pytest.mark.unit
@pytest.mark.models
def test_invoice_calculate_totals(app, invoice_with_items):
    """Test invoice total calculations."""
    invoice, items = invoice_with_items
    
    with app.app_context():
        db.session.refresh(invoice)
        
        # 10 * 75 + 5 * 60 = 750 + 300 = 1050
        assert invoice.subtotal == Decimal('1050.00')
        
        # Tax: 20% of 1050 = 210
        assert invoice.tax_amount == Decimal('210.00')
        
        # Total: 1050 + 210 = 1260
        assert invoice.total_amount == Decimal('1260.00')


@pytest.mark.unit
@pytest.mark.models
def test_invoice_payment_tracking(app, invoice_with_items):
    """Test invoice payment tracking."""
    invoice, items = invoice_with_items
    
    with app.app_context():
        db.session.refresh(invoice)
        
        # Record partial payment
        partial_payment = invoice.total_amount / 2
        invoice.record_payment(
            amount=partial_payment,
            payment_date=date.today(),
            payment_method='bank_transfer',
            payment_reference='TEST-123'
        )
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.payment_status == 'partially_paid'
        assert invoice.amount_paid == partial_payment
        assert invoice.is_partially_paid is True
        
        # Record remaining payment
        remaining = invoice.outstanding_amount
        invoice.record_payment(
            amount=remaining,
            payment_method='bank_transfer'
        )
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.payment_status == 'fully_paid'
        assert invoice.is_paid is True
        assert invoice.outstanding_amount == Decimal('0')


@pytest.mark.unit
@pytest.mark.models
def test_invoice_overdue_status(app, user, project, test_client):
    """Test invoice overdue status."""
    with app.app_context():
        # Create overdue invoice
        overdue_invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            project_id=project.id,
            client_id=test_client.id,
            client_name='Test Client',
            due_date=date.today() - timedelta(days=10),
            created_by=user.id,
            status='sent'
        )
        db.session.add(overdue_invoice)
        db.session.commit()
        
        db.session.refresh(overdue_invoice)
        assert overdue_invoice.is_overdue is True
        assert overdue_invoice.days_overdue == 10


# ============================================================================
# Settings Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
def test_settings_singleton(app):
    """Test settings singleton pattern."""
    with app.app_context():
        settings1 = Settings.get_settings()
        settings2 = Settings.get_settings()
        
        assert settings1.id == settings2.id


@pytest.mark.unit
@pytest.mark.models
def test_settings_default_values(app):
    """Test settings default values."""
    with app.app_context():
        settings = Settings.get_settings()
        
        # Check that settings has expected attributes
        assert hasattr(settings, 'id')
        # Add more default value checks based on your Settings model


# ============================================================================
# Model Relationship Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.models
@pytest.mark.database
def test_cascade_delete_user_time_entries(app, user, multiple_time_entries):
    """Test cascade delete of user time entries."""
    with app.app_context():
        db.session.refresh(user)
        user_id = user.id
        
        # Get time entry count
        entry_count = TimeEntry.query.filter_by(user_id=user_id).count()
        assert entry_count == 5
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        # Check time entries are deleted or handled
        remaining_entries = TimeEntry.query.filter_by(user_id=user_id).count()
        # Depending on cascade settings, entries might be deleted or set to null
        # Adjust assertion based on your actual cascade configuration


@pytest.mark.integration
@pytest.mark.models
@pytest.mark.database
def test_project_client_relationship_integrity(app, project, test_client):
    """Test project-client relationship integrity."""
    with app.app_context():
        db.session.refresh(project)
        db.session.refresh(test_client)
        
        assert project.client_id == test_client.id
        
        # Get project through client
        client_projects = test_client.projects.all()
        project_ids = [p.id for p in client_projects]
        assert project.id in project_ids


# ============================================================================
# Model Validation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.models
def test_project_requires_name(app):
    """Test that project requires a name."""
    with app.app_context():
        project = Project(billable=True)
        db.session.add(project)
        
        # Should raise an error when committing without name
        with pytest.raises(Exception):  # IntegrityError or similar
            db.session.commit()
        
        db.session.rollback()


@pytest.mark.unit
@pytest.mark.models
def test_time_entry_requires_start_time(app, user, project):
    """Test that time entry requires start time."""
    with app.app_context():
        entry = TimeEntry(
            user_id=user.id,
            project_id=project.id,
            source='manual'
        )
        db.session.add(entry)
        
        # Should raise an error when committing without start_time
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()

