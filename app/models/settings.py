from datetime import datetime
from app import db
from app.config import Config

class Settings(db.Model):
    """Settings model for system configuration"""
    
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    timezone = db.Column(db.String(50), default='Europe/Brussels', nullable=False)
    currency = db.Column(db.String(3), default='EUR', nullable=False)
    rounding_minutes = db.Column(db.Integer, default=1, nullable=False)
    single_active_timer = db.Column(db.Boolean, default=True, nullable=False)
    allow_self_register = db.Column(db.Boolean, default=True, nullable=False)
    idle_timeout_minutes = db.Column(db.Integer, default=30, nullable=False)
    backup_retention_days = db.Column(db.Integer, default=30, nullable=False)
    backup_time = db.Column(db.String(5), default='02:00', nullable=False)  # HH:MM format
    export_delimiter = db.Column(db.String(1), default=',', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        # Set defaults from config
        self.timezone = kwargs.get('timezone', Config.TZ)
        self.currency = kwargs.get('currency', Config.CURRENCY)
        self.rounding_minutes = kwargs.get('rounding_minutes', Config.ROUNDING_MINUTES)
        self.single_active_timer = kwargs.get('single_active_timer', Config.SINGLE_ACTIVE_TIMER)
        self.allow_self_register = kwargs.get('allow_self_register', Config.ALLOW_SELF_REGISTER)
        self.idle_timeout_minutes = kwargs.get('idle_timeout_minutes', Config.IDLE_TIMEOUT_MINUTES)
        self.backup_retention_days = kwargs.get('backup_retention_days', Config.BACKUP_RETENTION_DAYS)
        self.backup_time = kwargs.get('backup_time', Config.BACKUP_TIME)
        self.export_delimiter = kwargs.get('export_delimiter', ',')
    
    def __repr__(self):
        return f'<Settings {self.id}>'
    
    def to_dict(self):
        """Convert settings to dictionary for API responses"""
        return {
            'id': self.id,
            'timezone': self.timezone,
            'currency': self.currency,
            'rounding_minutes': self.rounding_minutes,
            'single_active_timer': self.single_active_timer,
            'allow_self_register': self.allow_self_register,
            'idle_timeout_minutes': self.idle_timeout_minutes,
            'backup_retention_days': self.backup_retention_days,
            'backup_time': self.backup_time,
            'export_delimiter': self.export_delimiter,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_settings(cls):
        """Get the singleton settings instance, creating it if it doesn't exist"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    @classmethod
    def update_settings(cls, **kwargs):
        """Update settings with new values"""
        settings = cls.get_settings()
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        return settings
