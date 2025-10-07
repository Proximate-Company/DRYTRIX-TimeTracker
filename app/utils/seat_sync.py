"""
Seat Synchronization Service

This module handles automatic synchronization of subscription quantities
with Stripe when users are added or removed from an organization.
"""

from flask import current_app
from app import db
from app.models.organization import Organization
from app.models.membership import Membership
from app.utils.stripe_service import stripe_service


class SeatSyncService:
    """Service for synchronizing subscription seats with Stripe."""
    
    @staticmethod
    def calculate_required_seats(organization):
        """Calculate the number of seats required for an organization.
        
        Args:
            organization: Organization instance
        
        Returns:
            int: Number of active members in the organization
        """
        return organization.member_count
    
    @staticmethod
    def should_sync_seats(organization):
        """Check if an organization should sync seats with Stripe.
        
        Args:
            organization: Organization instance
        
        Returns:
            bool: True if seats should be synced
        """
        # Only sync for team plans with active subscriptions
        return (
            organization.subscription_plan == 'team' and
            organization.has_active_subscription and
            organization.stripe_subscription_id is not None
        )
    
    @staticmethod
    def sync_seats(organization, new_quantity=None, prorate=None):
        """Synchronize subscription seats with Stripe.
        
        Args:
            organization: Organization instance
            new_quantity: Optional explicit seat count (defaults to member_count)
            prorate: Whether to prorate charges (uses config default if not provided)
        
        Returns:
            dict: Result of sync operation with 'success' and 'message' keys
        """
        if not stripe_service.is_configured():
            return {
                'success': False,
                'message': 'Stripe is not configured'
            }
        
        if not SeatSyncService.should_sync_seats(organization):
            return {
                'success': False,
                'message': 'Seat sync not applicable for this organization'
            }
        
        # Calculate required seats
        if new_quantity is None:
            new_quantity = SeatSyncService.calculate_required_seats(organization)
        
        # Ensure minimum of 1 seat
        new_quantity = max(1, new_quantity)
        
        # Check if quantity changed
        if new_quantity == organization.subscription_quantity:
            return {
                'success': True,
                'message': 'Seat count is already up to date',
                'quantity': new_quantity
            }
        
        try:
            # Update subscription in Stripe
            result = stripe_service.update_subscription_quantity(
                organization=organization,
                new_quantity=new_quantity,
                prorate=prorate
            )
            
            return {
                'success': True,
                'message': f"Seats updated from {result['old_quantity']} to {result['new_quantity']}",
                'old_quantity': result['old_quantity'],
                'new_quantity': result['new_quantity'],
                'prorated': prorate if prorate is not None else current_app.config.get('STRIPE_ENABLE_PRORATION', True)
            }
        except Exception as e:
            current_app.logger.error(f"Failed to sync seats for organization {organization.id}: {e}")
            return {
                'success': False,
                'message': f"Failed to update seats: {str(e)}"
            }
    
    @staticmethod
    def on_member_added(organization, user):
        """Handle member addition - sync seats if needed.
        
        Args:
            organization: Organization instance
            user: User that was added
        
        Returns:
            dict: Result of sync operation
        """
        current_app.logger.info(
            f"Member {user.username} added to organization {organization.name} ({organization.id})"
        )
        
        # Sync seats
        result = SeatSyncService.sync_seats(organization)
        
        if result['success']:
            current_app.logger.info(
                f"Seats synced for organization {organization.id}: {result['message']}"
            )
        else:
            current_app.logger.warning(
                f"Seat sync failed for organization {organization.id}: {result['message']}"
            )
        
        return result
    
    @staticmethod
    def on_member_removed(organization, user):
        """Handle member removal - sync seats if needed.
        
        Args:
            organization: Organization instance
            user: User that was removed
        
        Returns:
            dict: Result of sync operation
        """
        current_app.logger.info(
            f"Member {user.username} removed from organization {organization.name} ({organization.id})"
        )
        
        # Sync seats
        result = SeatSyncService.sync_seats(organization)
        
        if result['success']:
            current_app.logger.info(
                f"Seats synced for organization {organization.id}: {result['message']}"
            )
        else:
            current_app.logger.warning(
                f"Seat sync failed for organization {organization.id}: {result['message']}"
            )
        
        return result
    
    @staticmethod
    def on_invitation_accepted(organization, user):
        """Handle invitation acceptance - sync seats if needed.
        
        Args:
            organization: Organization instance
            user: User that accepted invitation
        
        Returns:
            dict: Result of sync operation
        """
        return SeatSyncService.on_member_added(organization, user)
    
    @staticmethod
    def check_seat_limit(organization):
        """Check if organization has reached its seat limit.
        
        Args:
            organization: Organization instance
        
        Returns:
            dict: Result with 'can_add', 'current_count', 'limit', and 'message'
        """
        current_count = organization.member_count
        
        # For team plans, check against subscription quantity
        if organization.subscription_plan == 'team':
            limit = organization.subscription_quantity
            
            if current_count >= limit:
                return {
                    'can_add': False,
                    'current_count': current_count,
                    'limit': limit,
                    'message': f'Organization has reached its seat limit ({limit} seats). Please upgrade to add more users.'
                }
            
            return {
                'can_add': True,
                'current_count': current_count,
                'limit': limit,
                'remaining': limit - current_count,
                'message': f'{limit - current_count} seat(s) remaining'
            }
        
        # For other plans, check against max_users
        if organization.max_users is not None:
            if current_count >= organization.max_users:
                return {
                    'can_add': False,
                    'current_count': current_count,
                    'limit': organization.max_users,
                    'message': f'Organization has reached its user limit ({organization.max_users} users)'
                }
        
        # No limit or under limit
        return {
            'can_add': True,
            'current_count': current_count,
            'limit': organization.max_users,
            'message': 'Can add users'
        }


# Create singleton instance
seat_sync_service = SeatSyncService()


# Convenience functions for use in routes

def sync_seats_on_member_change(organization_id, action='sync', user_id=None):
    """Convenience function to sync seats when membership changes.
    
    Args:
        organization_id: Organization ID
        action: Type of action ('add', 'remove', 'sync')
        user_id: User ID involved in the change (optional)
    
    Returns:
        dict: Result of sync operation
    """
    organization = Organization.query.get(organization_id)
    if not organization:
        return {'success': False, 'message': 'Organization not found'}
    
    from app.models.user import User
    user = User.query.get(user_id) if user_id else None
    
    if action == 'add' and user:
        return seat_sync_service.on_member_added(organization, user)
    elif action == 'remove' and user:
        return seat_sync_service.on_member_removed(organization, user)
    else:
        return seat_sync_service.sync_seats(organization)


def check_can_add_member(organization_id):
    """Check if a new member can be added to an organization.
    
    Args:
        organization_id: Organization ID
    
    Returns:
        dict: Result with 'can_add' and other details
    """
    organization = Organization.query.get(organization_id)
    if not organization:
        return {'can_add': False, 'message': 'Organization not found'}
    
    return seat_sync_service.check_seat_limit(organization)

