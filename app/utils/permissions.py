"""Permission decorators and role enforcement utilities"""
from functools import wraps
from flask import abort, jsonify, request
from flask_login import current_user
from app.models import Membership, Organization


def login_required(f):
    """Require user to be logged in (compatible with both session and JWT)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import g
        
        # Check session-based auth first
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Check JWT auth
        if hasattr(g, 'current_user') and g.current_user:
            return f(*args, **kwargs)
        
        # No authentication found
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Authentication required'}), 401
        
        abort(401)
    
    return decorated_function


def admin_required(f):
    """Require user to be an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import g
        
        user = current_user if current_user.is_authenticated else getattr(g, 'current_user', None)
        
        if not user or not user.is_admin:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Admin access required'}), 403
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def organization_member_required(f):
    """Require user to be a member of the organization (from route parameter or query).
    
    Expects organization_id or org_slug in route or query parameters.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import g
        
        user = current_user if current_user.is_authenticated else getattr(g, 'current_user', None)
        
        if not user:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        # Get organization from route or query params
        org_id = kwargs.get('organization_id') or request.args.get('organization_id')
        org_slug = kwargs.get('org_slug') or request.args.get('org_slug')
        
        if not org_id and not org_slug:
            if request.is_json:
                return jsonify({'error': 'Organization not specified'}), 400
            abort(400)
        
        # Get organization
        if org_slug:
            org = Organization.get_by_slug(org_slug)
        else:
            org = Organization.query.get(org_id)
        
        if not org or not org.is_active:
            if request.is_json:
                return jsonify({'error': 'Organization not found'}), 404
            abort(404)
        
        # Check membership
        if not Membership.user_is_member(user.id, org.id):
            if request.is_json:
                return jsonify({'error': 'You are not a member of this organization'}), 403
            abort(403)
        
        # Add organization to kwargs for convenience
        kwargs['organization'] = org
        
        return f(*args, **kwargs)
    
    return decorated_function


def organization_admin_required(f):
    """Require user to be an admin of the organization.
    
    Expects organization_id or org_slug in route or query parameters.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import g
        
        user = current_user if current_user.is_authenticated else getattr(g, 'current_user', None)
        
        if not user:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        # Global admins bypass organization checks
        if user.is_admin:
            return f(*args, **kwargs)
        
        # Get organization from route or query params
        org_id = kwargs.get('organization_id') or request.args.get('organization_id')
        org_slug = kwargs.get('org_slug') or request.args.get('org_slug')
        
        if not org_id and not org_slug:
            if request.is_json:
                return jsonify({'error': 'Organization not specified'}), 400
            abort(400)
        
        # Get organization
        if org_slug:
            org = Organization.get_by_slug(org_slug)
        else:
            org = Organization.query.get(org_id)
        
        if not org or not org.is_active:
            if request.is_json:
                return jsonify({'error': 'Organization not found'}), 404
            abort(404)
        
        # Check if user is org admin
        if not Membership.user_is_admin(user.id, org.id):
            if request.is_json:
                return jsonify({'error': 'Organization admin access required'}), 403
            abort(403)
        
        # Add organization to kwargs for convenience
        kwargs['organization'] = org
        
        return f(*args, **kwargs)
    
    return decorated_function


def can_edit_data(f):
    """Require user to have edit permissions in the organization.
    
    Members and admins can edit, but not viewers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import g
        
        user = current_user if current_user.is_authenticated else getattr(g, 'current_user', None)
        
        if not user:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        
        # Global admins bypass checks
        if user.is_admin:
            return f(*args, **kwargs)
        
        # Get organization from route or query params
        org_id = kwargs.get('organization_id') or request.args.get('organization_id')
        org_slug = kwargs.get('org_slug') or request.args.get('org_slug')
        
        if org_id or org_slug:
            # Get organization
            if org_slug:
                org = Organization.get_by_slug(org_slug)
            else:
                org = Organization.query.get(org_id)
            
            if not org or not org.is_active:
                if request.is_json:
                    return jsonify({'error': 'Organization not found'}), 404
                abort(404)
            
            # Check membership and role
            membership = Membership.find_membership(user.id, org.id)
            
            if not membership or not membership.can_edit_data:
                if request.is_json:
                    return jsonify({'error': 'You do not have permission to edit data'}), 403
                abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_user_permission(user, organization_id, required_permission):
    """Check if user has a specific permission in an organization.
    
    Args:
        user: User object
        organization_id: Organization ID
        required_permission: Permission to check ('view', 'edit', 'admin', 'manage_members', 'manage_projects')
    
    Returns:
        bool: True if user has permission
    """
    if not user:
        return False
    
    # Global admins have all permissions
    if user.is_admin:
        return True
    
    # Get membership
    membership = Membership.find_membership(user.id, organization_id)
    
    if not membership or not membership.is_active:
        return False
    
    # Check permission based on role
    if required_permission == 'view':
        return True  # All active members can view
    elif required_permission == 'edit':
        return membership.can_edit_data
    elif required_permission in ['admin', 'manage_members']:
        return membership.can_manage_members
    elif required_permission == 'manage_projects':
        return membership.can_manage_projects
    
    return False


def get_current_user():
    """Get current user from either Flask-Login session or JWT.
    
    Returns:
        User: Current user object or None
    """
    from flask_login import current_user
    from flask import g
    
    if current_user.is_authenticated:
        return current_user
    
    if hasattr(g, 'current_user'):
        return g.current_user
    
    return None


def get_user_organizations(user):
    """Get all organizations a user belongs to.
    
    Args:
        user: User object
    
    Returns:
        list: List of Organization objects
    """
    if not user:
        return []
    
    memberships = Membership.get_user_active_memberships(user.id)
    return [m.organization for m in memberships if m.organization and m.organization.is_active]


def get_user_role_in_organization(user, organization_id):
    """Get user's role in an organization.
    
    Args:
        user: User object
        organization_id: Organization ID
    
    Returns:
        str: Role name ('admin', 'member', 'viewer') or None if not a member
    """
    if not user:
        return None
    
    # Global admins are implicitly org admins
    if user.is_admin:
        return 'admin'
    
    membership = Membership.find_membership(user.id, organization_id)
    return membership.role if membership else None


def require_permission(permission):
    """Decorator factory for custom permission requirements.
    
    Args:
        permission: Permission name ('view', 'edit', 'admin', 'manage_members', 'manage_projects')
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            
            # Get organization from route or query params
            org_id = kwargs.get('organization_id') or request.args.get('organization_id')
            org_slug = kwargs.get('org_slug') or request.args.get('org_slug')
            
            if org_id or org_slug:
                # Get organization
                if org_slug:
                    org = Organization.get_by_slug(org_slug)
                else:
                    org = Organization.query.get(org_id)
                
                if not org or not org.is_active:
                    if request.is_json:
                        return jsonify({'error': 'Organization not found'}), 404
                    abort(404)
                
                # Check permission
                if not check_user_permission(user, org.id, permission):
                    if request.is_json:
                        return jsonify({'error': f'{permission.capitalize()} permission required'}), 403
                    abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

