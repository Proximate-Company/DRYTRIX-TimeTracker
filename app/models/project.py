from datetime import datetime
from decimal import Decimal
from app import db

class Project(db.Model):
    """Project model for client projects with billing information"""
    
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    client = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    billable = db.Column(db.Boolean, default=True, nullable=False)
    hourly_rate = db.Column(db.Numeric(9, 2), nullable=True)
    billing_ref = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' or 'archived'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    time_entries = db.relationship('TimeEntry', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, client, description=None, billable=True, hourly_rate=None, billing_ref=None):
        self.name = name.strip()
        self.client = client.strip()
        self.description = description.strip() if description else None
        self.billable = billable
        self.hourly_rate = Decimal(str(hourly_rate)) if hourly_rate else None
        self.billing_ref = billing_ref.strip() if billing_ref else None
    
    def __repr__(self):
        return f'<Project {self.name} ({self.client})>'
    
    @property
    def is_active(self):
        """Check if project is active"""
        return self.status == 'active'
    
    @property
    def total_hours(self):
        """Calculate total hours spent on this project"""
        from .time_entry import TimeEntry
        total_seconds = db.session.query(
            db.func.sum(TimeEntry.duration_seconds)
        ).filter(
            TimeEntry.project_id == self.id,
            TimeEntry.end_time.isnot(None)
        ).scalar() or 0
        return round(total_seconds / 3600, 2)
    
    @property
    def total_billable_hours(self):
        """Calculate total billable hours spent on this project"""
        from .time_entry import TimeEntry
        total_seconds = db.session.query(
            db.func.sum(TimeEntry.duration_seconds)
        ).filter(
            TimeEntry.project_id == self.id,
            TimeEntry.end_time.isnot(None),
            TimeEntry.billable == True
        ).scalar() or 0
        return round(total_seconds / 3600, 2)
    
    @property
    def estimated_cost(self):
        """Calculate estimated cost based on billable hours and hourly rate"""
        if not self.billable or not self.hourly_rate:
            return 0.0
        return float(self.total_billable_hours) * float(self.hourly_rate)
    
    def get_entries_by_user(self, user_id=None, start_date=None, end_date=None):
        """Get time entries for this project, optionally filtered by user and date range"""
        from .time_entry import TimeEntry
        query = self.time_entries.filter(TimeEntry.end_time.isnot(None))
        
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        
        if start_date:
            query = query.filter(TimeEntry.start_time >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.start_time <= end_date)
        
        return query.order_by(TimeEntry.start_time.desc()).all()
    
    def get_user_totals(self, start_date=None, end_date=None):
        """Get total hours per user for this project"""
        from .time_entry import TimeEntry
        from .user import User
        
        query = db.session.query(
            User.username,
            db.func.sum(TimeEntry.duration_seconds).label('total_seconds')
        ).join(TimeEntry).filter(
            TimeEntry.project_id == self.id,
            TimeEntry.end_time.isnot(None)
        )
        
        if start_date:
            query = query.filter(TimeEntry.start_time >= start_date)
        
        if end_date:
            query = query.filter(TimeEntry.start_time <= end_date)
        
        results = query.group_by(User.username).all()
        
        return [
            {
                'username': username,
                'total_hours': round(total_seconds / 3600, 2)
            }
            for username, total_seconds in results
        ]
    
    def archive(self):
        """Archive the project"""
        self.status = 'archived'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def unarchive(self):
        """Unarchive the project"""
        self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert project to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'client': self.client,
            'description': self.description,
            'billable': self.billable,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'billing_ref': self.billing_ref,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_hours': self.total_hours,
            'total_billable_hours': self.total_billable_hours,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None
        }
