from flask import g, request
from app.models import Settings

def register_context_processors(app):
    """Register context processors for the application"""
    
    @app.context_processor
    def inject_settings():
        """Inject settings into all templates"""
        try:
            settings = Settings.get_settings()
            return {
                'settings': settings,
                'currency': settings.currency,
                'timezone': settings.timezone
            }
        except:
            # Return defaults if settings not available
            return {
                'settings': None,
                'currency': 'EUR',
                'timezone': 'Europe/Brussels'
            }
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates"""
        return {
            'app_name': 'Time Tracker',
            'app_version': '1.0.0'
        }
    
    @app.before_request
    def before_request():
        """Set up request-specific data"""
        g.request_start_time = request.start_time if hasattr(request, 'start_time') else None
