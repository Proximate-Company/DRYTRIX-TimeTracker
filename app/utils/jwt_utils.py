"""JWT utilities for authentication"""
import jwt
from datetime import datetime, timedelta
from flask import current_app
from functools import wraps
from flask import request, jsonify
from flask_login import current_user

def generate_access_token(user_id, organization_id=None, expires_in_minutes=15):
    """Generate a JWT access token.
    
    Args:
        user_id: ID of the user
        organization_id: Optional organization context
        expires_in_minutes: Token validity period in minutes (default 15)
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        'iat': datetime.utcnow(),
    }
    
    if organization_id:
        payload['organization_id'] = organization_id
    
    secret = current_app.config.get('SECRET_KEY')
    return jwt.encode(payload, secret, algorithm='HS256')


def decode_access_token(token):
    """Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        secret = current_app.config.get('SECRET_KEY')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Verify it's an access token
        if payload.get('type') != 'access':
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.debug('JWT token expired')
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.debug(f'Invalid JWT token: {e}')
        return None


def jwt_required(f):
    """Decorator to require a valid JWT token for API endpoints.
    
    Usage:
        @app.route('/api/protected')
        @jwt_required
        def protected_endpoint():
            # Access user via g.current_user or request.jwt_user
            return jsonify({'user_id': request.jwt_user['user_id']})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.replace('Bearer ', '', 1)
        payload = decode_access_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Load user and verify they're still active
        from app.models import User
        user = User.query.get(payload['user_id'])
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Store user info in request context
        g.current_user = user
        request.jwt_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def jwt_optional(f):
    """Decorator that accepts but doesn't require a JWT token.
    
    If a valid token is provided, user info is available in request context.
    If no token or invalid token, the endpoint still executes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '', 1)
            payload = decode_access_token(token)
            
            if payload:
                from app.models import User
                user = User.query.get(payload['user_id'])
                
                if user and user.is_active:
                    g.current_user = user
                    request.jwt_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_jwt_identity():
    """Get the current JWT user ID from request context.
    
    Returns:
        int: User ID if authenticated via JWT, None otherwise
    """
    if hasattr(request, 'jwt_user'):
        return request.jwt_user.get('user_id')
    return None


def refresh_access_token(refresh_token_string):
    """Generate a new access token using a refresh token.
    
    Args:
        refresh_token_string: Refresh token string
    
    Returns:
        tuple: (access_token, refresh_token) if successful, (None, None) otherwise
    """
    from app.models import RefreshToken
    
    refresh_token = RefreshToken.get_valid_token(refresh_token_string)
    
    if not refresh_token:
        return None, None
    
    # Update last used timestamp
    refresh_token.update_last_used()
    
    # Generate new access token
    access_token = generate_access_token(refresh_token.user_id)
    
    # Optionally rotate refresh token (more secure but requires client to update)
    # For now, we'll keep the same refresh token
    
    return access_token, refresh_token.token


def create_token_pair(user_id, organization_id=None, device_id=None, device_name=None, 
                     ip_address=None, user_agent=None):
    """Create both access and refresh tokens for a user.
    
    Args:
        user_id: ID of the user
        organization_id: Optional organization context
        device_id: Unique device identifier
        device_name: User-friendly device name
        ip_address: IP address of the client
        user_agent: User agent string
    
    Returns:
        dict: Contains 'access_token', 'refresh_token', and 'expires_in'
    """
    from app.models import RefreshToken
    
    # Generate access token
    access_token = generate_access_token(user_id, organization_id)
    
    # Create refresh token in database
    refresh_token_obj = RefreshToken.create_token(
        user_id=user_id,
        device_id=device_id,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token_obj.token,
        'token_type': 'Bearer',
        'expires_in': 900,  # 15 minutes in seconds
    }


def revoke_refresh_token(refresh_token_string):
    """Revoke a refresh token.
    
    Args:
        refresh_token_string: Refresh token to revoke
    
    Returns:
        bool: True if revoked, False if not found
    """
    from app.models import RefreshToken
    
    token = RefreshToken.query.filter_by(token=refresh_token_string).first()
    
    if token:
        token.revoke()
        return True
    
    return False


def revoke_all_user_tokens(user_id):
    """Revoke all refresh tokens for a user (e.g., on password change).
    
    Args:
        user_id: ID of the user
    
    Returns:
        int: Number of tokens revoked
    """
    from app.models import RefreshToken
    
    tokens = RefreshToken.query.filter_by(user_id=user_id, revoked=False).all()
    
    for token in tokens:
        token.revoke()
    
    return len(tokens)

