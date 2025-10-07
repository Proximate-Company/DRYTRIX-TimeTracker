"""
Rate Limiting Configuration

This module provides comprehensive rate limiting rules for different
endpoint types to prevent abuse and DoS attacks.
"""

from functools import wraps
from flask import request, jsonify
from app import limiter


# Authentication endpoints - strict limits
AUTH_RATE_LIMITS = {
    'login': '5 per minute',
    'register': '3 per hour',
    'password_reset': '3 per hour',
    'password_change': '10 per hour',
    '2fa_setup': '5 per hour',
    '2fa_verify': '10 per 5 minutes',
}

# API endpoints - moderate limits
API_RATE_LIMITS = {
    'read': '100 per minute',
    'write': '60 per minute',
    'delete': '30 per minute',
    'bulk': '10 per minute',
}

# Administrative endpoints - moderate limits with higher ceiling
ADMIN_RATE_LIMITS = {
    'general': '200 per minute',
    'write': '100 per minute',
}

# Public endpoints - lenient limits
PUBLIC_RATE_LIMITS = {
    'general': '1000 per hour',
}

# GDPR endpoints - very strict limits
GDPR_RATE_LIMITS = {
    'export': '5 per hour',
    'delete': '2 per hour',
}


def apply_rate_limit(limit_type='general', limit_string=None):
    """
    Decorator to apply rate limiting to routes.
    
    Args:
        limit_type: Type of limit ('auth', 'api', 'admin', 'public', 'gdpr')
        limit_string: Custom limit string (e.g., '100 per minute')
    
    Example:
        @apply_rate_limit('auth', 'login')
        def login():
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        
        # Apply the limit
        if limit_string:
            limiter.limit(limit_string)(wrapper)
        elif limit_type == 'auth':
            limiter.limit(AUTH_RATE_LIMITS.get('general', '10 per minute'))(wrapper)
        elif limit_type == 'api':
            limiter.limit(API_RATE_LIMITS.get('read', '100 per minute'))(wrapper)
        elif limit_type == 'admin':
            limiter.limit(ADMIN_RATE_LIMITS.get('general', '200 per minute'))(wrapper)
        elif limit_type == 'gdpr':
            limiter.limit(GDPR_RATE_LIMITS.get('export', '5 per hour'))(wrapper)
        else:
            limiter.limit(PUBLIC_RATE_LIMITS.get('general', '1000 per hour'))(wrapper)
        
        return wrapper
    
    return decorator


def get_client_ip():
    """Get the real client IP address, accounting for proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def rate_limit_error_handler(e):
    """Custom error handler for rate limit exceeded"""
    return jsonify({
        'error': 'rate_limit_exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': e.description
    }), 429


# Rate limit exemptions (e.g., for health checks, webhooks)
RATE_LIMIT_EXEMPTIONS = [
    '/_health',
    '/health',
    '/metrics',
    '/webhooks/stripe',  # Stripe webhooks should not be rate limited
]


def is_exempt_from_rate_limit():
    """Check if the current request should be exempt from rate limiting"""
    return request.path in RATE_LIMIT_EXEMPTIONS

