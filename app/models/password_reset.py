from datetime import datetime, timedelta
from app import db
import secrets

class PasswordResetToken(db.Model):
    """Model for password reset tokens"""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    
    # Relationships
    user = db.relationship('User', backref='password_reset_tokens')
    
    def __init__(self, user_id, ip_address=None, expires_in_hours=24):
        """Create a new password reset token.
        
        Args:
            user_id: ID of the user requesting password reset
            ip_address: IP address of the requester
            expires_in_hours: Token validity period in hours (default 24)
        """
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.ip_address = ip_address
        self.used = False
    
    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id} expires={self.expires_at}>'
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_token(cls, user_id, ip_address=None):
        """Create a new password reset token for a user"""
        token = cls(user_id=user_id, ip_address=ip_address)
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
    def cleanup_expired_tokens(cls):
        """Delete expired tokens (cleanup utility)"""
        expired_tokens = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired_tokens
    
    @classmethod
    def revoke_user_tokens(cls, user_id):
        """Revoke all active tokens for a user"""
        cls.query.filter_by(user_id=user_id, used=False).update({'used': True, 'used_at': datetime.utcnow()})
        db.session.commit()


class EmailVerificationToken(db.Model):
    """Model for email verification tokens"""
    
    __tablename__ = 'email_verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    email = db.Column(db.String(200), nullable=False)  # Email to verify
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='email_verification_tokens')
    
    def __init__(self, user_id, email, expires_in_hours=48):
        """Create a new email verification token.
        
        Args:
            user_id: ID of the user
            email: Email address to verify
            expires_in_hours: Token validity period in hours (default 48)
        """
        self.user_id = user_id
        self.email = email.lower().strip()
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.verified = False
    
    def __repr__(self):
        return f'<EmailVerificationToken user_id={self.user_id} email={self.email}>'
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not verified and not expired)"""
        return not self.verified and not self.is_expired
    
    def mark_as_verified(self):
        """Mark token as verified"""
        self.verified = True
        self.verified_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_token(cls, user_id, email):
        """Create a new email verification token"""
        token = cls(user_id=user_id, email=email)
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
    def cleanup_expired_tokens(cls):
        """Delete expired tokens (cleanup utility)"""
        expired_tokens = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired_tokens

