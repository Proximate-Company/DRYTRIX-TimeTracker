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
    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # HTTPS enforcement
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'true').lower() == 'true'
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'
    }
    
    # Content Security Policy
    # Allows inline scripts/styles for now (needed for dynamic content), but can be tightened with nonces
    CONTENT_SECURITY_POLICY = os.getenv(
        'CONTENT_SECURITY_POLICY',
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.stripe.com; "
        "frame-src https://js.stripe.com https://hooks.stripe.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests"
    )

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '')  # e.g., "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true'
    
    # Password policy
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 12))
    PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_DIGITS = os.getenv('PASSWORD_REQUIRE_DIGITS', 'true').lower() == 'true'
    PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'
    PASSWORD_EXPIRY_DAYS = int(os.getenv('PASSWORD_EXPIRY_DAYS', 0))  # 0 = no expiry
    PASSWORD_HISTORY_COUNT = int(os.getenv('PASSWORD_HISTORY_COUNT', 5))  # Number of previous passwords to check
    
    # Data retention and GDPR
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', 0))  # 0 = no automatic deletion
    GDPR_EXPORT_ENABLED = os.getenv('GDPR_EXPORT_ENABLED', 'true').lower() == 'true'
    GDPR_DELETION_ENABLED = os.getenv('GDPR_DELETION_ENABLED', 'true').lower() == 'true'
    GDPR_DELETION_DELAY_DAYS = int(os.getenv('GDPR_DELETION_DELAY_DAYS', 30))  # Grace period before actual deletion
    
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
    
    # Email settings (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'noreply@timetracker.local')
    SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'TimeTracker')
    
    # Versioning
    # Prefer explicit app version from environment (e.g., Git tag)
    APP_VERSION = os.getenv('APP_VERSION', os.getenv('GITHUB_TAG', None))
    if not APP_VERSION:
        # If no tag provided, create a dev-build identifier if available
        github_run_number = os.getenv('GITHUB_RUN_NUMBER')
        APP_VERSION = f"dev-{github_run_number}" if github_run_number else "dev-0"

    # Stripe billing settings
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    STRIPE_SINGLE_USER_PRICE_ID = os.getenv('STRIPE_SINGLE_USER_PRICE_ID')  # €5/month
    STRIPE_TEAM_PRICE_ID = os.getenv('STRIPE_TEAM_PRICE_ID')  # €6/user/month
    STRIPE_ENABLE_TRIALS = os.getenv('STRIPE_ENABLE_TRIALS', 'true').lower() == 'true'
    STRIPE_TRIAL_DAYS = int(os.getenv('STRIPE_TRIAL_DAYS', 14))
    STRIPE_ENABLE_PRORATION = os.getenv('STRIPE_ENABLE_PRORATION', 'true').lower() == 'true'
    STRIPE_TAX_BEHAVIOR = os.getenv('STRIPE_TAX_BEHAVIOR', 'exclusive')  # 'inclusive' or 'exclusive'

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
    
    # Force HTTPS and secure cookies
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # CSRF protection enabled in production
    WTF_CSRF_ENABLED = True
    
    # Stronger password requirements in production
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 12))

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
