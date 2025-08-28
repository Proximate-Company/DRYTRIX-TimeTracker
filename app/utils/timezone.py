import os
import pytz
from datetime import datetime, timezone
from flask import current_app

def get_app_timezone():
    """Get the application's configured timezone from database settings or environment"""
    try:
        # Try to get timezone from database settings first
        from app.models import Settings
        from app import db
        
        # Check if we have a database connection
        if db.session.is_active:
            try:
                settings = Settings.get_settings()
                if settings and settings.timezone:
                    return settings.timezone
            except Exception as e:
                # Log the error but continue with fallback
                print(f"Warning: Could not get timezone from database: {e}")
                pass
    except Exception as e:
        # If database is not available or settings don't exist, fall back to environment
        print(f"Warning: Database not available for timezone: {e}")
        pass
    
    # Fallback to environment variable
    return os.getenv('TZ', 'Europe/Rome')

def get_timezone_obj():
    """Get timezone object for the configured timezone"""
    tz_name = get_app_timezone()
    try:
        return pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone is invalid
        return pytz.UTC

def now_in_app_timezone():
    """Get current time in the application's timezone"""
    tz = get_timezone_obj()
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(tz)

def utc_to_local(utc_dt):
    """Convert UTC datetime to local application timezone"""
    if utc_dt is None:
        return None
    
    # If datetime is naive (no timezone), assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    tz = get_timezone_obj()
    return utc_dt.astimezone(tz)

def local_to_utc(local_dt):
    """Convert local datetime to UTC"""
    if local_dt is None:
        return None
    
    # If datetime is naive, assume it's in the application timezone
    if local_dt.tzinfo is None:
        tz = get_timezone_obj()
        local_dt = tz.localize(local_dt)
    
    return local_dt.astimezone(timezone.utc)

def parse_local_datetime(date_str, time_str):
    """Parse date and time strings in local timezone"""
    try:
        # Combine date and time
        datetime_str = f'{date_str} {time_str}'
        
        # Parse as naive datetime (assumed to be in local timezone)
        naive_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        # Localize to application timezone
        tz = get_timezone_obj()
        local_dt = tz.localize(naive_dt)
        
        # Convert to UTC for storage
        return local_dt.astimezone(timezone.utc)
    except ValueError as e:
        raise ValueError(f"Invalid date/time format: {e}")

def format_local_datetime(utc_dt, format_str='%Y-%m-%d %H:%M'):
    """Format UTC datetime in local timezone"""
    if utc_dt is None:
        return ""
    
    local_dt = utc_to_local(utc_dt)
    return local_dt.strftime(format_str)

def get_timezone_offset():
    """Get current timezone offset from UTC in hours"""
    tz = get_timezone_obj()
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(tz)
    offset = local_now.utcoffset()
    return offset.total_seconds() / 3600 if offset else 0

def get_timezone_offset_for_timezone(tz_name):
    """Get timezone offset for a specific timezone name"""
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(timezone.utc)
        local_now = now.astimezone(tz)
        offset = local_now.utcoffset()
        return offset.total_seconds() / 3600 if offset else 0
    except pytz.exceptions.UnknownTimeZoneError:
        return 0
