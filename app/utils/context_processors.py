from flask import g, request
from app.models import Settings
from app.utils.timezone import get_timezone_offset_for_timezone

def register_context_processors(app):
    """Register context processors for the application"""
    
    @app.context_processor
    def inject_settings():
        """Inject settings into all templates"""
        try:
            from app import db
            # Check if we have an active database session
            if db.session.is_active:
                settings = Settings.get_settings()
                return {
                    'settings': settings,
                    'currency': settings.currency,
                    'timezone': settings.timezone
                }
        except Exception as e:
            # Log the error but continue with defaults
            print(f"Warning: Could not inject settings: {e}")
            pass
        
        # Return defaults if settings not available
        return {
            'settings': None,
            'currency': 'EUR',
            'timezone': 'Europe/Rome'
        }
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates"""
        try:
            from app import db
            # Check if we have an active database session
            if db.session.is_active:
                settings = Settings.get_settings()
                timezone_name = settings.timezone if settings else 'Europe/Rome'
            else:
                timezone_name = 'Europe/Rome'
        except Exception as e:
            # Log the error but continue with defaults
            print(f"Warning: Could not inject globals: {e}")
            timezone_name = 'Europe/Rome'

        # Determine app version from environment or config
        try:
            import os
            from app.config import Config
            env_version = os.getenv('APP_VERSION')
            # If running in GitHub Actions build, prefer tag-like versions
            version_value = env_version or getattr(Config, 'APP_VERSION', None) or 'dev-0'
        except Exception:
            version_value = 'dev-0'
        
        return {
            'app_name': 'Time Tracker',
            'app_version': version_value,
            'timezone': timezone_name,
            'timezone_offset': get_timezone_offset_for_timezone(timezone_name)
        }
    
    @app.before_request
    def before_request():
        """Set up request-specific data"""
        g.request_start_time = request.start_time if hasattr(request, 'start_time') else None
