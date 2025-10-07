"""
Row Level Security (RLS) integration for PostgreSQL multi-tenancy.

This module provides utilities to set and manage PostgreSQL RLS context
for tenant isolation at the database level.
"""

from functools import wraps
from flask import g
from sqlalchemy import text
from app import db
import logging

logger = logging.getLogger(__name__)


def set_rls_context(organization_id, is_super_admin=False):
    """Set the PostgreSQL RLS context for the current request.
    
    This function sets session variables that are used by Row Level Security
    policies to filter data at the database level.
    
    Args:
        organization_id: ID of the organization to set context for
        is_super_admin: Whether the current user is a super admin (can access all orgs)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not organization_id and not is_super_admin:
        logger.warning("Attempted to set RLS context without organization_id and not super admin")
        return False
    
    try:
        # Check if we're using PostgreSQL
        if 'postgresql' not in str(db.engine.url):
            logger.debug("RLS context setting skipped - not using PostgreSQL")
            return True
        
        # Set the organization context in PostgreSQL
        org_id_str = str(organization_id) if organization_id else ''
        
        db.session.execute(text(
            "SELECT set_config('app.current_organization_id', :org_id, false)"
        ), {"org_id": org_id_str})
        
        db.session.execute(text(
            "SELECT set_config('app.is_super_admin', :is_admin, false)"
        ), {"is_admin": str(is_super_admin).lower()})
        
        logger.debug(f"RLS context set: org_id={organization_id}, super_admin={is_super_admin}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        return False


def clear_rls_context():
    """Clear the PostgreSQL RLS context.
    
    This should be called at the end of each request to clean up.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if we're using PostgreSQL
        if 'postgresql' not in str(db.engine.url):
            return True
        
        db.session.execute(text(
            "SELECT set_config('app.current_organization_id', '', false)"
        ))
        
        db.session.execute(text(
            "SELECT set_config('app.is_super_admin', 'false', false)"
        ))
        
        logger.debug("RLS context cleared")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear RLS context: {e}")
        return False


def init_rls_for_request():
    """Initialize RLS context for the current request.
    
    This should be called in a before_request handler. It:
    1. Gets the current organization from the request context
    2. Determines if the user is a super admin
    3. Sets the RLS context in PostgreSQL
    """
    from app.utils.tenancy import get_current_organization_id
    from flask_login import current_user
    
    try:
        # Get current organization from tenancy context
        org_id = get_current_organization_id()
        
        # Check if user is a super admin (global admin, not org admin)
        is_super_admin = False
        if current_user and current_user.is_authenticated:
            # Super admins are users with 'admin' role at the application level
            # (not just organization-level admins)
            is_super_admin = getattr(current_user, 'is_admin', False)
        
        # Set RLS context if we have an organization
        if org_id or is_super_admin:
            set_rls_context(org_id, is_super_admin)
            
    except Exception as e:
        logger.error(f"Error initializing RLS for request: {e}")


def cleanup_rls_for_request():
    """Cleanup RLS context after the request.
    
    This should be called in an after_request or teardown_request handler.
    """
    try:
        clear_rls_context()
    except Exception as e:
        logger.error(f"Error cleaning up RLS after request: {e}")


def with_rls_context(organization_id, is_super_admin=False):
    """Decorator to temporarily set RLS context for a function.
    
    Useful for background tasks or CLI commands that need to operate
    within a specific organization context.
    
    Args:
        organization_id: ID of the organization
        is_super_admin: Whether to run as super admin
        
    Example:
        @with_rls_context(organization_id=1)
        def process_org_data():
            # This function runs within organization 1's context
            projects = Project.query.all()  # Only sees org 1 projects
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Set context
            set_rls_context(organization_id, is_super_admin)
            
            try:
                # Execute function
                result = f(*args, **kwargs)
                return result
            finally:
                # Always clear context
                clear_rls_context()
        
        return decorated_function
    return decorator


def verify_rls_is_active():
    """Verify that RLS is active and working correctly.
    
    This is useful for testing and deployment verification.
    
    Returns:
        dict: Status information about RLS
    """
    try:
        # Check if we're using PostgreSQL
        if 'postgresql' not in str(db.engine.url):
            return {
                'enabled': False,
                'reason': 'Not using PostgreSQL',
                'database_type': str(db.engine.url).split(':')[0]
            }
        
        # Check if RLS policies exist
        result = db.session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                policyname,
                permissive,
                roles,
                cmd,
                qual,
                with_check
            FROM pg_policies 
            WHERE schemaname = 'public'
            AND policyname LIKE '%tenant_isolation%'
        """))
        
        policies = list(result)
        
        # Check if helper functions exist
        functions_result = db.session.execute(text("""
            SELECT 
                proname
            FROM pg_proc
            WHERE proname IN (
                'current_organization_id',
                'is_super_admin',
                'set_organization_context',
                'clear_organization_context'
            )
        """))
        
        functions = [row[0] for row in functions_result]
        
        return {
            'enabled': len(policies) > 0,
            'policies_count': len(policies),
            'policies': [
                {
                    'table': p.tablename,
                    'policy': p.policyname,
                    'command': p.cmd
                } for p in policies
            ],
            'functions': functions,
            'all_functions_present': len(functions) == 4
        }
        
    except Exception as e:
        logger.error(f"Error verifying RLS status: {e}")
        return {
            'enabled': False,
            'error': str(e)
        }


def test_rls_isolation(org1_id, org2_id):
    """Test that RLS properly isolates data between organizations.
    
    This creates test data in two organizations and verifies that
    setting the context for one org only shows that org's data.
    
    Args:
        org1_id: ID of first test organization
        org2_id: ID of second test organization
        
    Returns:
        dict: Test results
    """
    from app.models import Project, Organization
    
    results = {
        'success': True,
        'tests': []
    }
    
    try:
        # Test 1: Set context to org1 and verify we only see org1 data
        set_rls_context(org1_id)
        
        org1_projects = Project.query.filter_by(organization_id=org1_id).count()
        org2_projects_visible = Project.query.filter_by(organization_id=org2_id).count()
        
        results['tests'].append({
            'name': 'Org 1 Context - Isolation Test',
            'passed': org2_projects_visible == 0,
            'org1_visible': org1_projects,
            'org2_visible': org2_projects_visible,
            'expected_org2': 0
        })
        
        # Test 2: Set context to org2 and verify we only see org2 data
        set_rls_context(org2_id)
        
        org2_projects = Project.query.filter_by(organization_id=org2_id).count()
        org1_projects_visible = Project.query.filter_by(organization_id=org1_id).count()
        
        results['tests'].append({
            'name': 'Org 2 Context - Isolation Test',
            'passed': org1_projects_visible == 0,
            'org2_visible': org2_projects,
            'org1_visible': org1_projects_visible,
            'expected_org1': 0
        })
        
        # Test 3: Super admin can see all data
        set_rls_context(None, is_super_admin=True)
        
        all_projects = Project.query.count()
        
        results['tests'].append({
            'name': 'Super Admin - Can See All Data',
            'passed': all_projects >= (org1_projects + org2_projects),
            'visible_count': all_projects,
            'expected_minimum': org1_projects + org2_projects
        })
        
        # Determine overall success
        results['success'] = all(test['passed'] for test in results['tests'])
        
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
    
    finally:
        clear_rls_context()
    
    return results

