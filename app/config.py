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

    # Authentication method: 'local' | 'oidc' | 'both'
    AUTH_METHOD = os.getenv('AUTH_METHOD', 'local').strip().lower()

    # OIDC settings (used when AUTH_METHOD is 'oidc' or 'both')
    OIDC_ISSUER = os.getenv('OIDC_ISSUER')  # e.g., https://login.microsoftonline.com/<tenant>/v2.0
    OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
    OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI')  # e.g., https://app.example.com/auth/oidc/callback
    OIDC_SCOPES = os.getenv('OIDC_SCOPES', 'openid profile email')
    OIDC_USERNAME_CLAIM = os.getenv('OIDC_USERNAME_CLAIM', 'preferred_username')
    OIDC_FULL_NAME_CLAIM = os.getenv('OIDC_FULL_NAME_CLAIM', 'name')
    OIDC_EMAIL_CLAIM = os.getenv('OIDC_EMAIL_CLAIM', 'email')
    OIDC_GROUPS_CLAIM = os.getenv('OIDC_GROUPS_CLAIM', 'groups')
    OIDC_ADMIN_GROUP = os.getenv('OIDC_ADMIN_GROUP')  # optional
    OIDC_ADMIN_EMAILS = [e.strip().lower() for e in os.getenv('OIDC_ADMIN_EMAILS', '').split(',') if e.strip()]
    OIDC_POST_LOGOUT_REDIRECT_URI = os.getenv('OIDC_POST_LOGOUT_REDIRECT_URI')
    
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
    WTF_CSRF_ENABLED = True  # Enabled by default, disabled only in testing
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '')  # e.g., "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    
    # Internationalization
    LANGUAGES = {
        'en': 'English',
        'nl': 'Nederlands',
        'de': 'Deutsch',
        'fr': 'Français',
        'it': 'Italiano',
        'fi': 'Suomi',
    }
    BABEL_DEFAULT_LOCALE = os.getenv('DEFAULT_LOCALE', 'en')
    # Comma-separated list of translation directories relative to instance root
    BABEL_TRANSLATION_DIRECTORIES = os.getenv('BABEL_TRANSLATION_DIRECTORIES', 'translations')
    
    # Versioning
    # Prefer explicit app version from environment (e.g., Git tag)
    APP_VERSION = os.getenv('APP_VERSION', os.getenv('GITHUB_TAG', None))
    if not APP_VERSION:
        # If no tag provided, create a dev-build identifier if available
        github_run_number = os.getenv('GITHUB_RUN_NUMBER')
        APP_VERSION = f"dev-{github_run_number}" if github_run_number else "dev-0"

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
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
