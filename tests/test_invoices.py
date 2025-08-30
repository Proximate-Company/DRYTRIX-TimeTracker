import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from app import create_app, db
from app.models import User, Project, Invoice, InvoiceItem, Settings

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    user = User(username='testuser', role='user')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def sample_project(app):
    """Create a sample project for testing."""
    project = Project(
        name='Test Project',
        client='Test Client',
        description='A test project',
        billable=True,
        hourly_rate=Decimal('75.00')
    )
    db.session.add(project)
    db.session.commit()
    return project

@pytest.fixture
def sample_invoice(app, sample_user, sample_project):
    """Create a sample invoice for testing."""
    invoice = Invoice(
        invoice_number='INV-20241201-001',
        project_id=sample_project.id,
        client_name='Test Client',
        due_date=date.today() + timedelta(days=30),
        created_by=sample_user.id
    )
    db.session.add(invoice)
    db.session.commit()
    return invoice

def test_invoice_creation(app, sample_user, sample_project):
    """Test that invoices can be created correctly."""
    invoice = Invoice(
        invoice_number='INV-20241201-002',
        project_id=sample_project.id,
        client_name='Test Client',
        due_date=date.today() + timedelta(days=30),
        created_by=sample_user.id,
        tax_rate=Decimal('20.00')
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    assert invoice.id is not None
    assert invoice.invoice_number == 'INV-20241201-002'
    assert invoice.client_name == 'Test Client'
    assert invoice.status == 'draft'
    assert invoice.tax_rate == Decimal('20.00')

def test_invoice_item_creation(app, sample_invoice):
    """Test that invoice items can be created correctly."""
    item = InvoiceItem(
        invoice_id=sample_invoice.id,
        description='Development work',
        quantity=Decimal('10.00'),
        unit_price=Decimal('75.00')
    )
    
    db.session.add(item)
    db.session.commit()
    
    assert item.id is not None
    assert item.total_amount == Decimal('750.00')
    assert item.invoice_id == sample_invoice.id

def test_invoice_totals_calculation(app, sample_invoice):
    """Test that invoice totals are calculated correctly."""
    # Add multiple items
    item1 = InvoiceItem(
        invoice_id=sample_invoice.id,
        description='Development work',
        quantity=Decimal('10.00'),
        unit_price=Decimal('75.00')
    )
    
    item2 = InvoiceItem(
        invoice_id=sample_invoice.id,
        description='Design work',
        quantity=Decimal('5.00'),
        unit_price=Decimal('100.00')
    )
    
    db.session.add_all([item1, item2])
    db.session.commit()
    
    # Calculate totals
    sample_invoice.calculate_totals()
    
    assert sample_invoice.subtotal == Decimal('1250.00')  # 10*75 + 5*100
    assert sample_invoice.tax_amount == Decimal('0.00')  # 0% tax rate
    assert sample_invoice.total_amount == Decimal('1250.00')

def test_invoice_with_tax(app, sample_user, sample_project):
    """Test invoice calculation with tax."""
    invoice = Invoice(
        invoice_number='INV-20241201-003',
        project_id=sample_project.id,
        client_name='Test Client',
        due_date=date.today() + timedelta(days=30),
        created_by=sample_user.id,
        tax_rate=Decimal('20.00')
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    # Add item
    item = InvoiceItem(
        invoice_id=invoice.id,
        description='Development work',
        quantity=Decimal('10.00'),
        unit_price=Decimal('75.00')
    )
    
    db.session.add(item)
    db.session.commit()
    
    # Calculate totals
    invoice.calculate_totals()
    
    assert invoice.subtotal == Decimal('750.00')
    assert invoice.tax_amount == Decimal('150.00')  # 20% of 750
    assert invoice.total_amount == Decimal('900.00')

def test_invoice_number_generation(app):
    """Test that invoice numbers are generated correctly."""
    # This test would need to be run in isolation or with a clean database
    # as it depends on the current date and existing invoice numbers
    
    # Mock the current date to ensure consistent testing
    from unittest.mock import patch
    from datetime import datetime
    
    with patch('app.models.invoice.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 12, 1, 12, 0, 0)
        
        # First invoice of the day
        invoice_number = Invoice.generate_invoice_number()
        assert invoice_number == 'INV-20241201-001'
        
        # Create an invoice with this number
        project = Project(name='Test', client='Test Client', billable=True)
        user = User(username='testuser', role='user')
        db.session.add_all([project, user])
        db.session.commit()
        
        invoice = Invoice(
            invoice_number=invoice_number,
            project_id=project.id,
            client_name='Test Client',
            due_date=date.today() + timedelta(days=30),
            created_by=user.id
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Next invoice should be numbered 002
        next_invoice_number = Invoice.generate_invoice_number()
        assert next_invoice_number == 'INV-20241201-002'

def test_invoice_overdue_status(app, sample_user, sample_project):
    """Test that invoices are marked as overdue correctly."""
    # Create an overdue invoice
    overdue_date = date.today() - timedelta(days=5)
    invoice = Invoice(
        invoice_number='INV-20241201-004',
        project_id=sample_project.id,
        client_name='Test Client',
        due_date=overdue_date,
        created_by=sample_user.id,
        status='sent'
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    assert invoice.is_overdue == True
    assert invoice.days_overdue == 5
    
    # Test that status updates to overdue
    invoice.calculate_totals()
    assert invoice.status == 'overdue'

def test_invoice_to_dict(app, sample_invoice):
    """Test that invoice can be converted to dictionary."""
    invoice_dict = sample_invoice.to_dict()
    
    assert 'id' in invoice_dict
    assert 'invoice_number' in invoice_dict
    assert 'client_name' in invoice_dict
    assert 'status' in invoice_dict
    assert 'created_at' in invoice_dict
    assert 'updated_at' in invoice_dict

def test_invoice_item_to_dict(app, sample_invoice):
    """Test that invoice item can be converted to dictionary."""
    item = InvoiceItem(
        invoice_id=sample_invoice.id,
        description='Test item',
        quantity=Decimal('5.00'),
        unit_price=Decimal('50.00')
    )
    
    db.session.add(item)
    db.session.commit()
    
    item_dict = item.to_dict()
    
    assert 'id' in item_dict
    assert 'description' in item_dict
    assert 'quantity' in item_dict
    assert 'unit_price' in item_dict
    assert 'total_amount' in item_dict
