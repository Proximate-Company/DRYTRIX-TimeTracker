from datetime import datetime
from app import db

class Organization(db.Model):
    """Organization model for multi-tenancy support.
    
    Each organization represents a separate tenant with its own data isolation.
    This enables the SaaS model where multiple customers can use the same
    application instance while keeping their data completely separate.
    """
    
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)  # URL-safe identifier
    
    # Contact and billing information
    contact_email = db.Column(db.String(200), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    billing_email = db.Column(db.String(200), nullable=True)
    
    # Status and metadata
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'suspended', 'cancelled'
    
    # Subscription and limits (for SaaS tiers)
    subscription_plan = db.Column(db.String(50), default='free', nullable=False)  # 'free', 'starter', 'professional', 'enterprise'
    max_users = db.Column(db.Integer, nullable=True)  # null = unlimited
    max_projects = db.Column(db.Integer, nullable=True)  # null = unlimited
    
    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_status = db.Column(db.String(20), nullable=True)  # 'active', 'trialing', 'past_due', 'canceled', 'incomplete', 'incomplete_expired', 'unpaid'
    stripe_price_id = db.Column(db.String(100), nullable=True)  # Current price ID being used
    subscription_quantity = db.Column(db.Integer, default=1, nullable=False)  # Number of seats/users
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    subscription_ends_at = db.Column(db.DateTime, nullable=True)
    next_billing_date = db.Column(db.DateTime, nullable=True)
    billing_issue_detected_at = db.Column(db.DateTime, nullable=True)  # When payment failed
    last_billing_email_sent_at = db.Column(db.DateTime, nullable=True)  # For dunning management
    
    # Settings and preferences
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    currency = db.Column(db.String(3), default='EUR', nullable=False)
    date_format = db.Column(db.String(20), default='YYYY-MM-DD', nullable=False)
    
    # Branding
    logo_filename = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(7), nullable=True)  # Hex color code
    
    # Promo codes
    promo_code = db.Column(db.String(50), nullable=True)
    promo_code_applied_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete support
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    memberships = db.relationship('Membership', back_populates='organization', lazy='dynamic', cascade='all, delete-orphan')
    projects = db.relationship('Project', back_populates='organization', lazy='dynamic', cascade='all, delete-orphan')
    clients = db.relationship('Client', back_populates='organization', lazy='dynamic', cascade='all, delete-orphan')
    time_entries = db.relationship('TimeEntry', back_populates='organization', lazy='dynamic')
    tasks = db.relationship('Task', back_populates='organization', lazy='dynamic')
    invoices = db.relationship('Invoice', back_populates='organization', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='organization', lazy='dynamic')
    
    def __init__(self, name, slug=None, contact_email=None, subscription_plan='free', **kwargs):
        """Create a new organization.
        
        Args:
            name: Display name of the organization
            slug: URL-safe identifier (auto-generated from name if not provided)
            contact_email: Primary contact email
            subscription_plan: Subscription tier ('free', 'starter', 'professional', 'enterprise')
            **kwargs: Additional optional fields
        """
        self.name = name.strip()
        
        # Generate slug from name if not provided
        if slug:
            self.slug = slug.strip().lower()
        else:
            import re
            # Convert name to URL-safe slug
            slug_base = re.sub(r'[^a-z0-9]+', '-', name.lower().strip())
            slug_base = slug_base.strip('-')
            
            # Ensure uniqueness by appending number if needed
            counter = 1
            test_slug = slug_base
            while Organization.query.filter_by(slug=test_slug).first():
                test_slug = f"{slug_base}-{counter}"
                counter += 1
            
            self.slug = test_slug
        
        self.contact_email = contact_email.strip() if contact_email else None
        self.subscription_plan = subscription_plan
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<Organization {self.name} ({self.slug})>'
    
    @property
    def is_active(self):
        """Check if organization is active"""
        return self.status == 'active' and self.deleted_at is None
    
    @property
    def is_suspended(self):
        """Check if organization is suspended"""
        return self.status == 'suspended'
    
    @property
    def is_deleted(self):
        """Check if organization is soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def member_count(self):
        """Get total number of members in this organization"""
        return self.memberships.filter_by(status='active').count()
    
    @property
    def admin_count(self):
        """Get number of admin members"""
        return self.memberships.filter_by(role='admin', status='active').count()
    
    @property
    def project_count(self):
        """Get total number of projects"""
        return self.projects.filter_by(status='active').count()
    
    @property
    def has_reached_user_limit(self):
        """Check if organization has reached its user limit"""
        if self.max_users is None:
            return False
        return self.member_count >= self.max_users
    
    @property
    def has_reached_project_limit(self):
        """Check if organization has reached its project limit"""
        if self.max_projects is None:
            return False
        return self.project_count >= self.max_projects
    
    @property
    def has_active_subscription(self):
        """Check if organization has an active paid subscription"""
        return self.stripe_subscription_status in ['active', 'trialing']
    
    @property
    def has_billing_issue(self):
        """Check if organization has a billing issue"""
        return self.stripe_subscription_status in ['past_due', 'unpaid'] or self.billing_issue_detected_at is not None
    
    @property
    def is_on_trial(self):
        """Check if organization is on trial"""
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at and self.stripe_subscription_status == 'trialing'
    
    @property
    def trial_days_remaining(self):
        """Get number of trial days remaining"""
        if not self.is_on_trial:
            return 0
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def subscription_plan_display(self):
        """Get display name for subscription plan"""
        plan_names = {
            'free': 'Free',
            'single_user': 'Single User',
            'team': 'Team',
            'enterprise': 'Enterprise'
        }
        return plan_names.get(self.subscription_plan, self.subscription_plan.title())
    
    def suspend(self, reason=None):
        """Suspend the organization"""
        self.status = 'suspended'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def activate(self):
        """Activate the organization"""
        self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def soft_delete(self):
        """Soft delete the organization"""
        self.deleted_at = datetime.utcnow()
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_billing_issue(self, has_issue=True):
        """Mark or clear billing issue"""
        if has_issue:
            if not self.billing_issue_detected_at:
                self.billing_issue_detected_at = datetime.utcnow()
        else:
            self.billing_issue_detected_at = None
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_subscription_quantity(self, new_quantity):
        """Update the subscription quantity (number of seats)"""
        if new_quantity < 1:
            raise ValueError("Subscription quantity must be at least 1")
        
        self.subscription_quantity = new_quantity
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_members(self, role=None, status='active'):
        """Get organization members with optional filters"""
        query = self.memberships.filter_by(status=status)
        
        if role:
            query = query.filter_by(role=role)
        
        return query.all()
    
    def get_admins(self):
        """Get all admin members"""
        return self.get_members(role='admin')
    
    def has_member(self, user_id):
        """Check if a user is a member of this organization"""
        from .membership import Membership
        return Membership.query.filter_by(
            organization_id=self.id,
            user_id=user_id,
            status='active'
        ).first() is not None
    
    def get_user_role(self, user_id):
        """Get the role of a user in this organization"""
        from .membership import Membership
        membership = Membership.query.filter_by(
            organization_id=self.id,
            user_id=user_id,
            status='active'
        ).first()
        return membership.role if membership else None
    
    def is_admin(self, user_id):
        """Check if a user is an admin of this organization"""
        return self.get_user_role(user_id) == 'admin'
    
    def to_dict(self, include_stats=False, include_billing=False):
        """Convert organization to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'billing_email': self.billing_email,
            'status': self.status,
            'subscription_plan': self.subscription_plan,
            'subscription_plan_display': self.subscription_plan_display,
            'max_users': self.max_users,
            'max_projects': self.max_projects,
            'timezone': self.timezone,
            'currency': self.currency,
            'date_format': self.date_format,
            'logo_filename': self.logo_filename,
            'primary_color': self.primary_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_suspended': self.is_suspended,
        }
        
        if include_stats:
            data.update({
                'member_count': self.member_count,
                'admin_count': self.admin_count,
                'project_count': self.project_count,
                'has_reached_user_limit': self.has_reached_user_limit,
                'has_reached_project_limit': self.has_reached_project_limit,
            })
        
        if include_billing:
            data.update({
                'stripe_customer_id': self.stripe_customer_id,
                'stripe_subscription_status': self.stripe_subscription_status,
                'subscription_quantity': self.subscription_quantity,
                'has_active_subscription': self.has_active_subscription,
                'has_billing_issue': self.has_billing_issue,
                'is_on_trial': self.is_on_trial,
                'trial_days_remaining': self.trial_days_remaining,
                'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
                'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
                'subscription_ends_at': self.subscription_ends_at.isoformat() if self.subscription_ends_at else None,
                'billing_issue_detected_at': self.billing_issue_detected_at.isoformat() if self.billing_issue_detected_at else None,
            })
        
        return data
    
    @classmethod
    def get_active_organizations(cls):
        """Get all active organizations"""
        return cls.query.filter_by(status='active').filter(cls.deleted_at.is_(None)).order_by(cls.name).all()
    
    @classmethod
    def get_by_slug(cls, slug):
        """Get organization by slug"""
        return cls.query.filter_by(slug=slug).filter(cls.deleted_at.is_(None)).first()

