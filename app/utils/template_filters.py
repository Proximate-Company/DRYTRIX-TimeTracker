from flask import Blueprint
from app.utils.timezone import utc_to_local, format_local_datetime
try:
    import markdown as _md
    import bleach
except Exception:
    _md = None
    bleach = None

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

    @app.template_filter('markdown')
    def markdown_filter(text):
        """Render markdown to safe HTML using bleach sanitation."""
        if not text:
            return ""
        if _md is None:
            # Fallback: escape and basic nl2br
            try:
                from markupsafe import escape
            except Exception:
                return text
            return escape(text).replace('\n', '<br>')

        html = _md.markdown(text, extensions=['extra', 'sane_lists', 'smarty'])
        if bleach is None:
            return html
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({'p','pre','code','img','h1','h2','h3','h4','h5','h6','table','thead','tbody','tr','th','td','hr','br','ul','ol','li','strong','em','blockquote','a'})
        allowed_attrs = {
            **bleach.sanitizer.ALLOWED_ATTRIBUTES,
            'a': ['href', 'title', 'rel', 'target'],
            'img': ['src', 'alt', 'title'],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
