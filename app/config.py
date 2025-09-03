import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Database settings (default to PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://timetracker:timetracker@localhost:5432/timetracker'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))
    )

    # Flask-Login remember cookie settings
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.getenv('REMEMBER_COOKIE_DAYS', 365)))
    REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE', 'false').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Application settings
    TZ = os.getenv('TZ', 'Europe/Rome')
    CURRENCY = os.getenv('CURRENCY', 'EUR')
    ROUNDING_MINUTES = int(os.getenv('ROUNDING_MINUTES', 1))
    SINGLE_ACTIVE_TIMER = os.getenv('SINGLE_ACTIVE_TIMER', 'true').lower() == 'true'
    IDLE_TIMEOUT_MINUTES = int(os.getenv('IDLE_TIMEOUT_MINUTES', 30))
    
    # User management
    ALLOW_SELF_REGISTER = os.getenv('ALLOW_SELF_REGISTER', 'true').lower() == 'true'
    ADMIN_USERNAMES = os.getenv('ADMIN_USERNAMES', 'admin').split(',')
    
    # Backup settings
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
    BACKUP_TIME = os.getenv('BACKUP_TIME', '02:00')
    
    # Pagination
    ENTRIES_PER_PAGE = 50
    PROJECTS_PER_PAGE = 20
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = '/data/uploads'
    
    # CSRF protection
    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Versioning
    # Prefer explicit app version from environment (e.g., Git tag)
    APP_VERSION = os.getenv('APP_VERSION', os.getenv('GITHUB_TAG', None))
    if not APP_VERSION:
        # If no tag provided, create a dev-build identifier if available
        github_run_number = os.getenv('GITHUB_RUN_NUMBER')
        APP_VERSION = f"dev-{github_run_number}" if github_run_number else "dev-0"

    # License server settings (no license required)
    # All settings are hardcoded since clients cannot change license server configuration
    LICENSE_SERVER_ENABLED = True  # Always enabled by default
    LICENSE_SERVER_API_KEY = "no-license-required"  # Hardcoded placeholder
    LICENSE_SERVER_APP_ID = "timetracker"  # Hardcoded app identifier
    LICENSE_SERVER_APP_VERSION = APP_VERSION  # Match application version
    LICENSE_SERVER_HEARTBEAT_INTERVAL = 3600  # Hardcoded heartbeat interval (1 hour)

class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://timetracker:timetracker@localhost:5432/timetracker'
    )
    WTF_CSRF_ENABLED = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

class ProductionConfig(Config):
    """Production configuration"""
    FLASK_DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
