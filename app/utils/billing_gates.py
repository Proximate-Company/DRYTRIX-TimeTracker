"""
Billing Gates and Subscription Checks

This module provides decorators and utilities for enforcing subscription
requirements and limits throughout the application.
"""

from functools import wraps
from flask import redirect, url_for, flash, request, current_app
from flask_login import current_user
from app.models.organization import Organization
from app.utils.tenancy import get_current_organization


def require_active_subscription(allow_trial=True, redirect_to='billing.index'):
    """Decorator to require an active subscription for a route.
    
    Args:
        allow_trial: Whether to allow trial subscriptions (default: True)
        redirect_to: Route name to redirect to if check fails
    
    Usage:
        @app.route('/premium-feature')
        @login_required
        @require_active_subscription()
        def premium_feature():
            return render_template('premium.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            org = get_current_organization()
            
            if not org:
                flash('No organization selected', 'warning')
                return redirect(url_for('organizations.index'))
            
            # Check if subscription is active
            if not org.has_active_subscription:
                flash('This feature requires an active subscription. Please upgrade your plan.', 'warning')
                return redirect(url_for(redirect_to))
            
            # Check trial if not allowed
            if not allow_trial and org.is_on_trial:
                flash('This feature is not available during trial period. Please upgrade to a paid plan.', 'warning')
                return redirect(url_for(redirect_to))
            
            # Check for billing issues
            if org.has_billing_issue:
                flash('Your account has a billing issue. Please update your payment method to continue.', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_plan(min_plan='single_user', redirect_to='billing.index'):
    """Decorator to require a specific subscription plan or higher.
    
    Plan hierarchy: free < single_user < team < enterprise
    
    Args:
        min_plan: Minimum required plan ('single_user', 'team', 'enterprise')
        redirect_to: Route name to redirect to if check fails
    
    Usage:
        @app.route('/team-feature')
        @login_required
        @require_plan('team')
        def team_feature():
            return render_template('team.html')
    """
    plan_hierarchy = {
        'free': 0,
        'single_user': 1,
        'team': 2,
        'enterprise': 3
    }
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            org = get_current_organization()
            
            if not org:
                flash('No organization selected', 'warning')
                return redirect(url_for('organizations.index'))
            
            current_level = plan_hierarchy.get(org.subscription_plan, 0)
            required_level = plan_hierarchy.get(min_plan, 1)
            
            if current_level < required_level:
                flash(f'This feature requires a {min_plan.replace("_", " ").title()} plan or higher. Please upgrade.', 'warning')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_user_limit(organization):
    """Check if organization can add more users.
    
    Args:
        organization: Organization instance
    
    Returns:
        dict with 'allowed', 'current', 'limit', 'message'
    """
    if not organization:
        return {
            'allowed': False,
            'current': 0,
            'limit': 0,
            'message': 'No organization found'
        }
    
    current_count = organization.member_count
    
    # For team plans, check against subscription quantity
    if organization.subscription_plan == 'team':
        limit = organization.subscription_quantity
        
        if current_count >= limit:
            return {
                'allowed': False,
                'current': current_count,
                'limit': limit,
                'message': f'User limit reached ({limit} users). Upgrade seats to add more users.',
                'can_upgrade': True
            }
        
        return {
            'allowed': True,
            'current': current_count,
            'limit': limit,
            'remaining': limit - current_count,
            'message': f'{limit - current_count} user slot(s) available'
        }
    
    # For single user plan
    if organization.subscription_plan == 'single_user':
        if current_count >= 1:
            return {
                'allowed': False,
                'current': current_count,
                'limit': 1,
                'message': 'Single User plan supports only 1 user. Upgrade to Team plan for multiple users.',
                'can_upgrade': True,
                'upgrade_to': 'team'
            }
        
        return {
            'allowed': True,
            'current': current_count,
            'limit': 1,
            'message': 'Can add 1 user'
        }
    
    # For free plan or others, check max_users
    if organization.max_users is not None:
        if current_count >= organization.max_users:
            return {
                'allowed': False,
                'current': current_count,
                'limit': organization.max_users,
                'message': f'User limit reached ({organization.max_users} users). Upgrade to add more users.',
                'can_upgrade': True
            }
    
    # No limit
    return {
        'allowed': True,
        'current': current_count,
        'limit': organization.max_users,
        'message': 'Can add users'
    }


def check_project_limit(organization):
    """Check if organization can add more projects.
    
    Args:
        organization: Organization instance
    
    Returns:
        dict with 'allowed', 'current', 'limit', 'message'
    """
    if not organization:
        return {
            'allowed': False,
            'current': 0,
            'limit': 0,
            'message': 'No organization found'
        }
    
    current_count = organization.project_count
    
    # Free plan limits
    if organization.subscription_plan == 'free':
        limit = organization.max_projects or 3  # Default limit for free
        
        if current_count >= limit:
            return {
                'allowed': False,
                'current': current_count,
                'limit': limit,
                'message': f'Project limit reached ({limit} projects). Upgrade to create more projects.',
                'can_upgrade': True
            }
        
        return {
            'allowed': True,
            'current': current_count,
            'limit': limit,
            'remaining': limit - current_count,
            'message': f'{limit - current_count} project slot(s) available'
        }
    
    # Paid plans - check max_projects if set
    if organization.max_projects is not None:
        if current_count >= organization.max_projects:
            return {
                'allowed': False,
                'current': current_count,
                'limit': organization.max_projects,
                'message': f'Project limit reached ({organization.max_projects} projects)'
            }
    
    # No limit for paid plans
    return {
        'allowed': True,
        'current': current_count,
        'limit': organization.max_projects,
        'message': 'Can create projects'
    }


def check_feature_access(organization, feature_name):
    """Check if organization has access to a specific feature.
    
    Args:
        organization: Organization instance
        feature_name: Name of feature to check
    
    Returns:
        dict with 'allowed', 'reason', 'upgrade_required'
    """
    if not organization:
        return {
            'allowed': False,
            'reason': 'No organization found',
            'upgrade_required': False
        }
    
    # Define feature access matrix
    features = {
        'advanced_reports': ['team', 'enterprise'],
        'api_access': ['team', 'enterprise'],
        'custom_branding': ['enterprise'],
        'priority_support': ['team', 'enterprise'],
        'integrations': ['team', 'enterprise'],
        'audit_logs': ['enterprise'],
        'sso': ['enterprise'],
    }
    
    allowed_plans = features.get(feature_name, [])
    
    if not allowed_plans:
        # Feature not defined, allow access
        return {
            'allowed': True,
            'reason': 'Feature available to all'
        }
    
    if organization.subscription_plan in allowed_plans:
        return {
            'allowed': True,
            'reason': f'Available on {organization.subscription_plan_display} plan'
        }
    
    return {
        'allowed': False,
        'reason': f'Requires {" or ".join([p.replace("_", " ").title() for p in allowed_plans])} plan',
        'upgrade_required': True,
        'required_plans': allowed_plans
    }


def get_subscription_warning(organization):
    """Get any warnings related to subscription status.
    
    Args:
        organization: Organization instance
    
    Returns:
        dict with 'type' ('warning', 'danger', 'info'), 'message', or None
    """
    if not organization:
        return None
    
    # Billing issue
    if organization.has_billing_issue:
        return {
            'type': 'danger',
            'message': 'Payment failed. Please update your payment method to avoid service interruption.',
            'action_url': url_for('billing.portal'),
            'action_text': 'Update Payment Method'
        }
    
    # Trial ending soon (< 3 days)
    if organization.is_on_trial and organization.trial_days_remaining <= 3:
        return {
            'type': 'warning',
            'message': f'Your trial ends in {organization.trial_days_remaining} day(s). Upgrade to continue using premium features.',
            'action_url': url_for('billing.index'),
            'action_text': 'View Plans'
        }
    
    # Subscription ending soon
    if organization.subscription_ends_at:
        from datetime import datetime
        days_until_end = (organization.subscription_ends_at - datetime.utcnow()).days
        
        if days_until_end <= 7:
            return {
                'type': 'warning',
                'message': f'Your subscription ends in {days_until_end} day(s). Renew to continue service.',
                'action_url': url_for('billing.index'),
                'action_text': 'Manage Subscription'
            }
    
    # Near user limit (> 90% capacity)
    if organization.subscription_plan == 'team' and organization.subscription_quantity:
        usage_percent = (organization.member_count / organization.subscription_quantity) * 100
        
        if usage_percent >= 90:
            return {
                'type': 'info',
                'message': f'You\'re using {organization.member_count} of {organization.subscription_quantity} seats. Consider adding more seats.',
                'action_url': url_for('billing.portal'),
                'action_text': 'Add Seats'
            }
    
    return None


# Context processor to inject billing info into all templates
def inject_billing_context():
    """Inject billing context into all templates."""
    if not current_user.is_authenticated:
        return {}
    
    org = get_current_organization()
    if not org:
        return {}
    
    return {
        'subscription_warning': get_subscription_warning(org),
        'has_active_subscription': org.has_active_subscription,
        'has_billing_issue': org.has_billing_issue,
        'is_on_trial': org.is_on_trial,
        'trial_days_remaining': org.trial_days_remaining if org.is_on_trial else 0,
    }

