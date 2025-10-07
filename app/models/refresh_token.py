from datetime import datetime, timedelta
from app import db
import secrets

class RefreshToken(db.Model):
    """Model for JWT refresh tokens"""
    
    __tablename__ = 'refresh_tokens'
    __table_args__ = (
        db.Index('idx_refresh_tokens_user_device', 'user_id', 'device_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    device_id = db.Column(db.String(100), nullable=True, index=True)  # Optional device identifier
    device_name = db.Column(db.String(200), nullable=True)  # User-friendly device name
    
    # Token lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    # Request metadata
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='refresh_tokens')
    
    def __init__(self, user_id, device_id=None, device_name=None, ip_address=None, user_agent=None, expires_in_days=30):
        """Create a new refresh token.
        
        Args:
            user_id: ID of the user
            device_id: Unique device identifier
            device_name: User-friendly device name
            ip_address: IP address of the client
            user_agent: User agent string
            expires_in_days: Token validity period in days (default 30)
        """
        self.user_id = user_id
        self.token = secrets.token_urlsafe(48)
        self.device_id = device_id
        self.device_name = device_name
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        self.last_used_at = datetime.utcnow()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.revoked = False
    
    def __repr__(self):
        return f'<RefreshToken user_id={self.user_id} device={self.device_name or self.device_id}>'
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not revoked and not expired)"""
        return not self.revoked and not self.is_expired
    
    @property
    def age_days(self):
        """Get token age in days"""
        return (datetime.utcnow() - self.created_at).days
    
    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()
    
    def revoke(self):
        """Revoke the token"""
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert token to dictionary for API responses"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ip_address': self.ip_address,
            'is_current': False,  # Can be set by caller
        }
    
    @classmethod
    def create_token(cls, user_id, device_id=None, device_name=None, ip_address=None, user_agent=None):
        """Create a new refresh token for a user"""
        token = cls(
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(token)
        db.session.commit()
        return token
    
    @classmethod
    def get_valid_token(cls, token_string):
        """Get a valid token by token string"""
        token = cls.query.filter_by(token=token_string).first()
        
        if token and token.is_valid:
            return token
        
        return None
    
    @classmethod
    def get_user_tokens(cls, user_id, include_revoked=False):
        """Get all tokens for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if not include_revoked:
            query = query.filter_by(revoked=False)
        
        return query.order_by(cls.last_used_at.desc()).all()
    
    @classmethod
    def revoke_user_tokens(cls, user_id, except_token_id=None):
        """Revoke all tokens for a user, optionally except one"""
        query = cls.query.filter_by(user_id=user_id, revoked=False)
        
        if except_token_id:
            query = query.filter(cls.id != except_token_id)
        
        tokens = query.all()
        for token in tokens:
            token.revoke()
    
    @classmethod
    def revoke_device_tokens(cls, user_id, device_id):
        """Revoke all tokens for a specific device"""
        tokens = cls.query.filter_by(user_id=user_id, device_id=device_id, revoked=False).all()
        for token in tokens:
            token.revoke()
    
    @classmethod
    def cleanup_expired_tokens(cls, days_old=90):
        """Delete old expired or revoked tokens"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted = cls.query.filter(
            db.or_(
                cls.expires_at < datetime.utcnow(),
                db.and_(cls.revoked == True, cls.revoked_at < cutoff_date)
            )
        ).delete()
        db.session.commit()
        return deleted

