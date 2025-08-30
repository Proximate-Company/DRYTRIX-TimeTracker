from flask import Blueprint
from app.utils.timezone import utc_to_local, format_local_datetime

def register_template_filters(app):
    """Register custom template filters for the application"""
    
    @app.template_filter('local_datetime')
    def local_datetime_filter(utc_dt, format_str='%Y-%m-%d %H:%M'):
        """Convert UTC datetime to local timezone for display"""
        if utc_dt is None:
            return ""
        return format_local_datetime(utc_dt, format_str)
    
    @app.template_filter('local_date')
    def local_date_filter(utc_dt):
        """Convert UTC datetime to local date only"""
        if utc_dt is None:
            return ""
        return format_local_datetime(utc_dt, '%Y-%m-%d')
    
    @app.template_filter('local_time')
    def local_time_filter(utc_dt):
        """Convert UTC datetime to local time only"""
        if utc_dt is None:
            return ""
        return format_local_datetime(utc_dt, '%H:%M')
    
    @app.template_filter('local_datetime_short')
    def local_datetime_short_filter(utc_dt):
        """Convert UTC datetime to local timezone in short format"""
        if utc_dt is None:
            return ""
        return format_local_datetime(utc_dt, '%m/%d %H:%M')
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks"""
        if text is None:
            return ""
        return text.replace('\n', '<br>')
