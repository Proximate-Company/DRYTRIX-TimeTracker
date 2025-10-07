from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for username-based authentication"""
    
    __tablename__ = 'users'
    __table_args__ = (
        db.UniqueConstraint('oidc_issuer', 'oidc_sub', name='uq_users_oidc_issuer_sub'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For local auth
    full_name = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    theme_preference = db.Column(db.String(10), default=None, nullable=True)  # 'light' | 'dark' | None=system
    preferred_language = db.Column(db.String(8), default=None, nullable=True)  # e.g., 'en', 'de'
    
    # OIDC authentication
    oidc_sub = db.Column(db.String(255), nullable=True)
    oidc_issuer = db.Column(db.String(255), nullable=True)
    
    # 2FA fields
    totp_secret = db.Column(db.String(32), nullable=True)  # For TOTP 2FA
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of hashed backup codes
    
    # Password policy fields
    password_changed_at = db.Column(db.DateTime, nullable=True)
    password_history = db.Column(db.Text, nullable=True)  # JSON array of previous password hashes
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    time_entries = db.relationship('TimeEntry', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, role='user', email=None, full_name=None):
        self.username = username.lower().strip()
        self.role = role
        self.email = (email or None)
        self.full_name = (full_name or None)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    @property
    def active_timer(self):
        """Get the user's currently active timer"""
        from .time_entry import TimeEntry
        return TimeEntry.query.filter_by(
            user_id=self.id,
            end_time=None
        ).first()
    
    @property
    def total_hours(self):
        """Calculate total hours worked by this user"""
        from .time_entry import TimeEntry
        total_seconds = db.session.query(
            db.func.sum(TimeEntry.duration_seconds)
        ).filter(
            TimeEntry.user_id == self.id,
            TimeEntry.end_time.isnot(None)
        ).scalar() or 0
        return round(total_seconds / 3600, 2)

    @property
    def display_name(self):
        """Preferred display name: full name if available, else username"""
        if self.full_name and self.full_name.strip():
            return self.full_name.strip()
        return self.username
    
    def get_recent_entries(self, limit=10):
        """Get recent time entries for this user"""
        from .time_entry import TimeEntry
        return self.time_entries.filter(
            TimeEntry.end_time.isnot(None)
        ).order_by(
            TimeEntry.start_time.desc()
        ).limit(limit).all()
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def set_password(self, password, validate=True):
        """Set user password (hashed) with optional policy validation"""
        if validate:
            from app.utils.password_policy import PasswordPolicy
            is_valid, error_msg = PasswordPolicy.validate_password(password, self)
            if not is_valid:
                raise ValueError(error_msg)
        
        # Store old password in history before updating
        if self.password_hash:
            self._add_to_password_history(self.password_hash)
        
        # Set new password
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.password_changed_at = datetime.utcnow()
        
        # Reset failed login attempts when password is changed
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        # Check if account is locked
        if self.is_account_locked():
            return False
        
        if not self.password_hash:
            return False
        
        is_valid = check_password_hash(self.password_hash, password)
        
        if is_valid:
            # Reset failed attempts on successful login
            self.failed_login_attempts = 0
            self.account_locked_until = None
        else:
            # Increment failed attempts
            self.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts for 30 minutes
            from datetime import timedelta
            if self.failed_login_attempts >= 5:
                self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        return is_valid
    
    @property
    def has_password(self):
        """Check if user has a password set (for local auth)"""
        return self.password_hash is not None
    
    def verify_totp(self, token):
        """Verify TOTP token for 2FA"""
        if not self.totp_enabled or not self.totp_secret:
            return False
        
        import pyotp
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if not self.backup_codes:
            return False
        
        import json
        codes = json.loads(self.backup_codes)
        code_hash = generate_password_hash(code)
        
        for idx, stored_hash in enumerate(codes):
            if check_password_hash(stored_hash, code):
                # Remove the used code
                codes.pop(idx)
                self.backup_codes = json.dumps(codes)
                db.session.commit()
                return True
        
        return False
    
    def generate_backup_codes(self, count=10):
        """Generate new backup codes for 2FA"""
        import secrets
        import json
        
        codes = []
        hashed_codes = []
        
        for _ in range(count):
            code = '-'.join([secrets.token_hex(2) for _ in range(4)])
            codes.append(code)
            hashed_codes.append(generate_password_hash(code))
        
        self.backup_codes = json.dumps(hashed_codes)
        db.session.commit()
        
        return codes  # Return plain codes for user to save
    
    def is_account_locked(self):
        """Check if account is currently locked due to failed login attempts"""
        if not self.account_locked_until:
            return False
        
        if datetime.utcnow() < self.account_locked_until:
            return True
        
        # Lock has expired, clear it
        self.account_locked_until = None
        self.failed_login_attempts = 0
        return False
    
    def _add_to_password_history(self, password_hash):
        """Add a password hash to the user's password history"""
        import json
        from flask import current_app
        
        history_count = current_app.config.get('PASSWORD_HISTORY_COUNT', 5)
        
        if history_count == 0:
            return
        
        # Get existing history
        history = []
        if self.password_history:
            try:
                history = json.loads(self.password_history)
            except Exception:
                history = []
        
        # Add new hash to history
        history.append(password_hash)
        
        # Keep only the most recent entries
        history = history[-history_count:]
        
        self.password_history = json.dumps(history)
    
    def check_password_history(self, password):
        """Check if password was used recently"""
        import json
        
        if not self.password_history:
            return False
        
        try:
            history = json.loads(self.password_history)
        except Exception:
            return False
        
        # Check if password matches any in history
        for old_hash in history:
            if check_password_hash(old_hash, password):
                return True
        
        return False
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'totp_enabled': self.totp_enabled,
            'has_password': self.has_password,
            'total_hours': self.total_hours
        }
