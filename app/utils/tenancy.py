"""
Tenancy utilities for multi-tenant data isolation.

This module provides:
1. Context management for current organization
2. Scoped query helpers
3. Middleware for enforcing tenant boundaries
"""

from functools import wraps
from flask import g, request, abort, session
from flask_login import current_user
from werkzeug.local import LocalProxy


def get_current_organization_id():
    """Get the current organization ID from the request context.
    
    Returns:
        int: Organization ID if set, None otherwise
    """
    return getattr(g, 'current_organization_id', None)


def get_current_organization():
    """Get the current organization object from the request context.
    
    Returns:
        Organization: Organization object if set, None otherwise
    """
    return getattr(g, 'current_organization', None)


def set_current_organization(organization_id, organization=None):
    """Set the current organization in the request context.
    
    Args:
        organization_id: ID of the organization
        organization: Optional Organization object (will be loaded if not provided)
    """
    g.current_organization_id = organization_id
    
    if organization:
        g.current_organization = organization
    elif organization_id:
        from app.models import Organization
        g.current_organization = Organization.query.get(organization_id)


# Convenient proxy for accessing current organization
current_organization_id = LocalProxy(get_current_organization_id)
current_organization = LocalProxy(get_current_organization)


def get_user_organizations(user_id):
    """Get all organizations a user belongs to.
    
    Args:
        user_id: ID of the user
        
    Returns:
        list: List of Organization objects
    """
    from app.models import Organization, Membership
    
    memberships = Membership.get_user_active_memberships(user_id)
    return [m.organization for m in memberships if m.organization]


def get_user_default_organization(user_id):
    """Get the default organization for a user (first active membership).
    
    Args:
        user_id: ID of the user
        
    Returns:
        Organization: Default organization or None
    """
    from app.models import Membership
    
    membership = Membership.query.filter_by(
        user_id=user_id,
        status='active'
    ).order_by(Membership.created_at.asc()).first()
    
    return membership.organization if membership else None


def user_has_access_to_organization(user_id, organization_id):
    """Check if a user has access to an organization.
    
    Args:
        user_id: ID of the user
        organization_id: ID of the organization
        
    Returns:
        bool: True if user has access, False otherwise
    """
    from app.models import Membership
    
    return Membership.user_is_member(user_id, organization_id)


def user_is_organization_admin(user_id, organization_id):
    """Check if a user is an admin of an organization.
    
    Args:
        user_id: ID of the user
        organization_id: ID of the organization
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    from app.models import Membership
    
    return Membership.user_is_admin(user_id, organization_id)


def require_organization_access(admin_only=False):
    """Decorator to ensure user has access to the current organization.
    
    Args:
        admin_only: If True, require admin role in the organization
        
    Raises:
        403: If user doesn't have access or isn't an admin (when required)
        401: If user is not authenticated
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401, description="Authentication required")
            
            org_id = get_current_organization_id()
            if not org_id:
                abort(403, description="No organization context set")
            
            if not user_has_access_to_organization(current_user.id, org_id):
                abort(403, description="Access denied to this organization")
            
            if admin_only and not user_is_organization_admin(current_user.id, org_id):
                abort(403, description="Admin access required")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def scoped_query(model_class):
    """Create a query scoped to the current organization.
    
    Args:
        model_class: SQLAlchemy model class to query
        
    Returns:
        Query: Scoped query object
        
    Raises:
        ValueError: If no organization context is set or model doesn't have organization_id
    """
    from app import db
    
    org_id = get_current_organization_id()
    if not org_id:
        raise ValueError("No organization context set for scoped query")
    
    if not hasattr(model_class, 'organization_id'):
        raise ValueError(f"Model {model_class.__name__} does not have organization_id column")
    
    return db.session.query(model_class).filter(model_class.organization_id == org_id)


def ensure_organization_access(obj):
    """Verify that an object belongs to the current organization.
    
    Args:
        obj: Object with organization_id attribute
        
    Raises:
        ValueError: If no organization context is set
        PermissionError: If object doesn't belong to current organization
    """
    org_id = get_current_organization_id()
    if not org_id:
        raise ValueError("No organization context set")
    
    if not hasattr(obj, 'organization_id'):
        raise ValueError(f"Object {type(obj).__name__} does not have organization_id")
    
    if obj.organization_id != org_id:
        raise PermissionError(
            f"Object {type(obj).__name__} #{obj.id} does not belong to organization #{org_id}"
        )


def switch_organization(organization_id):
    """Switch the current organization context (stores in session).
    
    Args:
        organization_id: ID of the organization to switch to
        
    Returns:
        Organization: The new current organization
        
    Raises:
        PermissionError: If user doesn't have access to the organization
    """
    if not current_user or not current_user.is_authenticated:
        raise PermissionError("Must be authenticated to switch organizations")
    
    if not user_has_access_to_organization(current_user.id, organization_id):
        raise PermissionError(f"No access to organization #{organization_id}")
    
    from app.models import Organization
    org = Organization.query.get(organization_id)
    if not org or not org.is_active:
        raise ValueError(f"Organization #{organization_id} not found or inactive")
    
    # Store in session for persistence across requests
    session['current_organization_id'] = organization_id
    
    # Also set in request context
    set_current_organization(organization_id, org)
    
    return org


def init_tenancy_for_request():
    """Initialize tenancy context for the current request.
    
    This should be called in a before_request handler. It:
    1. Loads organization from session or URL parameter
    2. Verifies user has access
    3. Sets up request context
    
    Returns:
        Organization: Current organization or None
    """
    if not current_user or not current_user.is_authenticated:
        return None
    
    # Try to get organization from various sources (in priority order)
    org_id = None
    
    # 1. URL parameter (for API calls or explicit switching)
    org_id = request.args.get('organization_id', type=int)
    
    # 2. Session (for web UI persistence)
    if not org_id:
        org_id = session.get('current_organization_id')
    
    # 3. User's default organization
    if not org_id:
        default_org = get_user_default_organization(current_user.id)
        if default_org:
            org_id = default_org.id
    
    # Set the organization if found
    if org_id:
        if user_has_access_to_organization(current_user.id, org_id):
            from app.models import Organization
            org = Organization.query.get(org_id)
            if org and org.is_active:
                set_current_organization(org_id, org)
                # Store in session for next request
                session['current_organization_id'] = org_id
                return org
    
    return None


def auto_set_organization_id(obj):
    """Automatically set organization_id on an object from current context.
    
    Args:
        obj: Object to set organization_id on
        
    Raises:
        ValueError: If no organization context is set
    """
    org_id = get_current_organization_id()
    if not org_id:
        raise ValueError("Cannot auto-set organization_id: No organization context")
    
    if hasattr(obj, 'organization_id'):
        obj.organization_id = org_id
    else:
        raise AttributeError(f"Object {type(obj).__name__} does not have organization_id attribute")

