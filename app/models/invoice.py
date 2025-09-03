from datetime import datetime
from decimal import Decimal
from app import db

class Invoice(db.Model):
    """Invoice model for client billing"""
    
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    client_name = db.Column(db.String(200), nullable=False)
    client_email = db.Column(db.String(200), nullable=True)
    client_address = db.Column(db.Text, nullable=True)
    # Link to clients table (enforced by DB schema)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False, index=True)
    
    # Invoice details
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)  # 'draft', 'sent', 'paid', 'overdue', 'cancelled'
    
    # Billing information
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)  # Percentage
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Notes and terms
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = db.relationship('Project', backref='invoices')
    client = db.relationship('Client', backref='invoices')
    creator = db.relationship('User', backref='created_invoices')
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, invoice_number, project_id, client_name, due_date, created_by, client_id, **kwargs):
        self.invoice_number = invoice_number
        self.project_id = project_id
        self.client_name = client_name
        self.due_date = due_date
        self.created_by = created_by
        self.client_id = client_id
        
        # Set optional fields
        self.client_email = kwargs.get('client_email')
        self.client_address = kwargs.get('client_address')
        self.issue_date = kwargs.get('issue_date', datetime.utcnow().date())
        self.notes = kwargs.get('notes')
        self.terms = kwargs.get('terms')
        self.tax_rate = Decimal(str(kwargs.get('tax_rate', 0)))
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number} ({self.client_name})>'
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status in ['sent', 'overdue'] and datetime.utcnow().date() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (datetime.utcnow().date() - self.due_date).days
    
    def calculate_totals(self):
        """Calculate invoice totals from items"""
        subtotal = sum(item.total_amount for item in self.items)
        self.subtotal = subtotal
        self.tax_amount = subtotal * (self.tax_rate / 100)
        self.total_amount = subtotal + self.tax_amount
        
        # Update status if overdue
        if self.status == 'sent' and self.is_overdue:
            self.status = 'overdue'
    
    def to_dict(self):
        """Convert invoice to dictionary for API responses"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'project_id': self.project_id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_address': self.client_address,
            'client_id': self.client_id,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'notes': self.notes,
            'terms': self.terms,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue
        }
    
    @classmethod
    def generate_invoice_number(cls):
        """Generate a unique invoice number"""
        from datetime import datetime
        
        # Format: INV-YYYYMMDD-XXX
        today = datetime.utcnow()
        date_prefix = today.strftime('%Y%m%d')
        
        # Find the next available number for today
        existing = cls.query.filter(
            cls.invoice_number.like(f'INV-{date_prefix}-%')
        ).order_by(cls.invoice_number.desc()).first()
        
        if existing:
            # Extract the number part and increment
            try:
                last_num = int(existing.invoice_number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f'INV-{date_prefix}-{next_num:03d}'


class InvoiceItem(db.Model):
    """Invoice line item model"""
    
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    
    # Item details
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)  # Hours
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # Hourly rate
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Time entry reference (optional)
    time_entry_ids = db.Column(db.String(500), nullable=True)  # Comma-separated IDs
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, invoice_id, description, quantity, unit_price, time_entry_ids=None):
        self.invoice_id = invoice_id
        self.description = description
        self.quantity = Decimal(str(quantity))
        self.unit_price = Decimal(str(unit_price))
        self.total_amount = self.quantity * self.unit_price
        self.time_entry_ids = time_entry_ids
    
    def __repr__(self):
        return f'<InvoiceItem {self.description} ({self.quantity}h @ {self.unit_price})>'
    
    def to_dict(self):
        """Convert invoice item to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'total_amount': float(self.total_amount),
            'time_entry_ids': self.time_entry_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
