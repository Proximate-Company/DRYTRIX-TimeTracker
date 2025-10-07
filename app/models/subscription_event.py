"""Subscription event model for tracking Stripe webhooks and subscription changes"""
from datetime import datetime
from app import db
import json

class SubscriptionEvent(db.Model):
    """Model for tracking subscription events from Stripe webhooks.
    
    This helps with auditing, debugging, and handling webhook delivery issues.
    """
    
    __tablename__ = 'subscription_events'
    __table_args__ = (
        db.Index('idx_subscription_events_org', 'organization_id'),
        db.Index('idx_subscription_events_type', 'event_type'),
        db.Index('idx_subscription_events_created', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Stripe event details
    stripe_event_id = db.Column(db.String(100), unique=True, nullable=True, index=True)  # Made nullable for manual events
    event_type = db.Column(db.String(100), nullable=False)  # e.g., 'customer.subscription.created'
    event_id = db.Column(db.String(100), nullable=True)  # For Stripe webhook event ID
    
    # Organization reference
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True, index=True)
    
    # Event data
    event_data = db.Column(db.Text, nullable=True)  # JSON string of the full event
    raw_payload = db.Column(db.Text, nullable=True)  # Raw webhook payload
    
    # Transaction details (for financial events)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    stripe_invoice_id = db.Column(db.String(100), nullable=True)
    stripe_charge_id = db.Column(db.String(100), nullable=True)
    stripe_refund_id = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    
    # Status tracking
    status = db.Column(db.String(50), nullable=True)  # Event-specific status
    previous_status = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)  # For subscription quantity changes
    previous_quantity = db.Column(db.Integer, nullable=True)
    
    # Processing status
    processed = db.Column(db.Boolean, default=False, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    processing_error = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text, nullable=True)  # Additional notes or context
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = db.relationship('Organization', backref='subscription_events')
    
    def __init__(self, event_type, stripe_event_id=None, organization_id=None, **kwargs):
        """Create a new subscription event.
        
        Args:
            event_type: Type of event (e.g., 'customer.subscription.updated')
            stripe_event_id: Stripe's unique event ID (optional for manual events)
            organization_id: Optional organization ID
            **kwargs: Additional fields
        """
        self.stripe_event_id = stripe_event_id
        self.event_type = event_type
        self.organization_id = organization_id
        
        # Set additional fields from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Convert dict to JSON string for text fields
                if key in ('event_data', 'raw_payload') and isinstance(value, dict):
                    setattr(self, key, json.dumps(value))
                else:
                    setattr(self, key, value)
        
        if not hasattr(self, 'processed') or self.processed is None:
            self.processed = False
        if not hasattr(self, 'retry_count') or self.retry_count is None:
            self.retry_count = 0
    
    def __repr__(self):
        return f'<SubscriptionEvent {self.stripe_event_id} type={self.event_type}>'
    
    @property
    def event_data_dict(self):
        """Get event data as a dictionary"""
        if not self.event_data:
            return {}
        
        try:
            return json.loads(self.event_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def mark_as_processed(self, success=True, error_message=None):
        """Mark event as processed.
        
        Args:
            success: Whether processing was successful
            error_message: Error message if processing failed
        """
        self.processed = success
        self.processed_at = datetime.utcnow()
        
        if not success and error_message:
            self.processing_error = error_message
            self.retry_count += 1
        
        db.session.commit()
    
    def to_dict(self):
        """Convert event to dictionary for API responses"""
        return {
            'id': self.id,
            'stripe_event_id': self.stripe_event_id,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'organization_id': self.organization_id,
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_invoice_id': self.stripe_invoice_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'previous_status': self.previous_status,
            'quantity': self.quantity,
            'previous_quantity': self.previous_quantity,
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_error': self.processing_error,
            'retry_count': self.retry_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def create_event(cls, event_type, stripe_event_id=None, event_data=None, organization_id=None, **kwargs):
        """Create a new subscription event.
        
        Args:
            event_type: Type of event
            stripe_event_id: Stripe's unique event ID (optional)
            event_data: Full event data
            organization_id: Optional organization ID
            **kwargs: Additional fields
        
        Returns:
            SubscriptionEvent: The created event
        """
        event = cls(
            event_type=event_type,
            stripe_event_id=stripe_event_id,
            event_data=event_data,
            organization_id=organization_id,
            **kwargs
        )
        db.session.add(event)
        db.session.commit()
        return event
    
    @classmethod
    def get_by_stripe_id(cls, stripe_event_id):
        """Get event by Stripe event ID.
        
        Args:
            stripe_event_id: Stripe's event ID
        
        Returns:
            SubscriptionEvent or None
        """
        return cls.query.filter_by(stripe_event_id=stripe_event_id).first()
    
    @classmethod
    def get_unprocessed_events(cls, limit=100):
        """Get unprocessed events.
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            list: List of unprocessed events
        """
        return cls.query.filter_by(processed=False).order_by(cls.created_at).limit(limit).all()
    
    @classmethod
    def get_failed_events(cls, max_retries=3):
        """Get events that failed processing and haven't exceeded retry limit.
        
        Args:
            max_retries: Maximum number of retries before giving up
        
        Returns:
            list: List of failed events eligible for retry
        """
        return cls.query.filter(
            cls.processed == False,
            cls.processing_error.isnot(None),
            cls.retry_count < max_retries
        ).order_by(cls.updated_at).all()
    
    @classmethod
    def get_organization_events(cls, organization_id, event_type=None, limit=50):
        """Get events for an organization.
        
        Args:
            organization_id: Organization ID
            event_type: Optional filter by event type
            limit: Maximum number of events to return
        
        Returns:
            list: List of events
        """
        query = cls.query.filter_by(organization_id=organization_id)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def cleanup_old_events(cls, days_old=90):
        """Delete old processed events.
        
        Args:
            days_old: Delete events older than this many days
        
        Returns:
            int: Number of events deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted = cls.query.filter(
            cls.processed == True,
            cls.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        return deleted
