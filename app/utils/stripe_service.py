"""
Stripe Service Module

This module provides a clean interface for all Stripe API interactions.
It handles customer creation, subscription management, seat updates, and more.
"""

import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import current_app
from app import db
from app.models.organization import Organization
from app.models.subscription_event import SubscriptionEvent


class StripeService:
    """Service class for Stripe API interactions."""
    
    def __init__(self):
        """Initialize Stripe service (configuration loaded lazily)."""
        self._api_key = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure Stripe is initialized with API key (lazy loading)."""
        if not self._initialized:
            try:
                self._api_key = current_app.config.get('STRIPE_SECRET_KEY')
                if self._api_key:
                    stripe.api_key = self._api_key
                self._initialized = True
            except RuntimeError:
                # No application context available
                pass
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        self._ensure_initialized()
        return bool(self._api_key)
    
    # ========================================
    # Customer Management
    # ========================================
    
    def create_customer(self, organization: Organization, email: str = None, 
                       name: str = None, metadata: Dict[str, Any] = None) -> str:
        """Create a Stripe customer for an organization.
        
        Args:
            organization: Organization instance
            email: Customer email (defaults to organization billing_email)
            name: Customer name (defaults to organization name)
            metadata: Additional metadata to attach to customer
        
        Returns:
            Stripe customer ID
        
        Raises:
            stripe.error.StripeError: If customer creation fails
        """
        self._ensure_initialized()
        self._ensure_initialized()
        if not self.is_configured():
            raise ValueError("Stripe is not configured")
        
        # Use organization data as defaults
        email = email or organization.billing_email or organization.contact_email
        name = name or organization.name
        
        # Prepare metadata
        customer_metadata = {
            'organization_id': str(organization.id),
            'organization_slug': organization.slug,
        }
        if metadata:
            customer_metadata.update(metadata)
        
        # Create customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=customer_metadata,
            description=f"Organization: {organization.name}"
        )
        
        # Update organization with customer ID
        organization.stripe_customer_id = customer.id
        db.session.commit()
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='customer.created',
            stripe_customer_id=customer.id,
            notes=f"Created Stripe customer for organization {organization.name}"
        )
        
        return customer.id
    
    def get_or_create_customer(self, organization: Organization) -> str:
        """Get existing customer ID or create a new customer.
        
        Args:
            organization: Organization instance
        
        Returns:
            Stripe customer ID
        """
        self._ensure_initialized()
        if organization.stripe_customer_id:
            return organization.stripe_customer_id
        
        return self.create_customer(organization)
    
    def update_customer(self, organization: Organization, **kwargs) -> None:
        """Update a Stripe customer.
        
        Args:
            organization: Organization instance
            **kwargs: Fields to update (email, name, metadata, etc.)
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            raise ValueError("Organization does not have a Stripe customer")
        
        stripe.Customer.modify(
            organization.stripe_customer_id,
            **kwargs
        )
    
    # ========================================
    # Subscription Management
    # ========================================
    
    def create_subscription(self, organization: Organization, price_id: str, 
                           quantity: int = 1, trial_days: Optional[int] = None) -> Dict[str, Any]:
        """Create a subscription for an organization.
        
        Args:
            organization: Organization instance
            price_id: Stripe price ID (e.g., STRIPE_SINGLE_USER_PRICE_ID or STRIPE_TEAM_PRICE_ID)
            quantity: Number of seats/units
            trial_days: Number of trial days (uses config default if not provided)
        
        Returns:
            Subscription data dictionary
        
        Raises:
            stripe.error.StripeError: If subscription creation fails
        """
        self._ensure_initialized()
        if not self.is_configured():
            raise ValueError("Stripe is not configured")
        
        # Get or create customer
        customer_id = self.get_or_create_customer(organization)
        
        # Prepare subscription parameters
        subscription_params = {
            'customer': customer_id,
            'items': [{
                'price': price_id,
                'quantity': quantity,
            }],
            'metadata': {
                'organization_id': str(organization.id),
                'organization_slug': organization.slug,
            },
            'payment_behavior': 'default_incomplete',  # Requires payment method
            'expand': ['latest_invoice.payment_intent'],
        }
        
        # Add trial if enabled
        if current_app.config.get('STRIPE_ENABLE_TRIALS', True):
            trial_days = trial_days or current_app.config.get('STRIPE_TRIAL_DAYS', 14)
            if trial_days > 0:
                subscription_params['trial_period_days'] = trial_days
        
        # Enable proration if configured
        if current_app.config.get('STRIPE_ENABLE_PRORATION', True):
            subscription_params['proration_behavior'] = 'create_prorations'
        
        # Create subscription
        subscription = stripe.Subscription.create(**subscription_params)
        
        # Update organization
        self._update_organization_from_subscription(organization, subscription)
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='subscription.created',
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription.id,
            status=subscription.status,
            quantity=quantity,
            notes=f"Created subscription with {quantity} seat(s)"
        )
        
        return {
            'subscription_id': subscription.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
            'status': subscription.status,
        }
    
    def update_subscription_quantity(self, organization: Organization, new_quantity: int,
                                    prorate: Optional[bool] = None) -> Dict[str, Any]:
        """Update the quantity (number of seats) for a subscription.
        
        Args:
            organization: Organization instance
            new_quantity: New seat count
            prorate: Whether to prorate charges (uses config default if not provided)
        
        Returns:
            Updated subscription data
        
        Raises:
            ValueError: If organization doesn't have a subscription
            stripe.error.StripeError: If update fails
        """
        if not organization.stripe_subscription_id:
            raise ValueError("Organization does not have a Stripe subscription")
        
        if new_quantity < 1:
            raise ValueError("Quantity must be at least 1")
        
        # Get current subscription
        subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
        
        # Get the subscription item ID (should be the first item)
        if not subscription.items.data:
            raise ValueError("Subscription has no items")
        
        subscription_item_id = subscription.items.data[0].id
        old_quantity = subscription.items.data[0].quantity
        
        # Determine proration behavior
        if prorate is None:
            prorate = current_app.config.get('STRIPE_ENABLE_PRORATION', True)
        
        proration_behavior = 'create_prorations' if prorate else 'none'
        
        # Update subscription
        updated_subscription = stripe.Subscription.modify(
            organization.stripe_subscription_id,
            items=[{
                'id': subscription_item_id,
                'quantity': new_quantity,
            }],
            proration_behavior=proration_behavior,
        )
        
        # Update organization
        organization.subscription_quantity = new_quantity
        db.session.commit()
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='subscription.quantity_updated',
            stripe_customer_id=organization.stripe_customer_id,
            stripe_subscription_id=organization.stripe_subscription_id,
            quantity=new_quantity,
            previous_quantity=old_quantity,
            notes=f"Updated seats from {old_quantity} to {new_quantity}"
        )
        
        return {
            'subscription_id': updated_subscription.id,
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'status': updated_subscription.status,
        }
    
    def cancel_subscription(self, organization: Organization, at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a subscription.
        
        Args:
            organization: Organization instance
            at_period_end: If True, cancel at end of billing period; if False, cancel immediately
        
        Returns:
            Cancellation data
        
        Raises:
            ValueError: If organization doesn't have a subscription
            stripe.error.StripeError: If cancellation fails
        """
        if not organization.stripe_subscription_id:
            raise ValueError("Organization does not have a Stripe subscription")
        
        if at_period_end:
            # Cancel at period end
            subscription = stripe.Subscription.modify(
                organization.stripe_subscription_id,
                cancel_at_period_end=True
            )
            organization.subscription_ends_at = datetime.fromtimestamp(subscription.current_period_end)
        else:
            # Cancel immediately
            subscription = stripe.Subscription.cancel(organization.stripe_subscription_id)
            organization.stripe_subscription_status = 'canceled'
            organization.subscription_ends_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='subscription.canceled',
            stripe_customer_id=organization.stripe_customer_id,
            stripe_subscription_id=organization.stripe_subscription_id,
            notes=f"Canceled {'at period end' if at_period_end else 'immediately'}"
        )
        
        return {
            'subscription_id': subscription.id,
            'status': subscription.status,
            'cancel_at_period_end': at_period_end,
            'ends_at': organization.subscription_ends_at,
        }
    
    def reactivate_subscription(self, organization: Organization) -> Dict[str, Any]:
        """Reactivate a subscription that was set to cancel at period end.
        
        Args:
            organization: Organization instance
        
        Returns:
            Reactivation data
        """
        if not organization.stripe_subscription_id:
            raise ValueError("Organization does not have a Stripe subscription")
        
        subscription = stripe.Subscription.modify(
            organization.stripe_subscription_id,
            cancel_at_period_end=False
        )
        
        organization.subscription_ends_at = None
        db.session.commit()
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='subscription.reactivated',
            stripe_customer_id=organization.stripe_customer_id,
            stripe_subscription_id=organization.stripe_subscription_id,
            notes="Reactivated subscription"
        )
        
        return {
            'subscription_id': subscription.id,
            'status': subscription.status,
        }
    
    # ========================================
    # Checkout & Portal
    # ========================================
    
    def create_checkout_session(self, organization: Organization, price_id: str, 
                               quantity: int = 1, success_url: str = None, 
                               cancel_url: str = None) -> Dict[str, Any]:
        """Create a Stripe Checkout session for subscription.
        
        Args:
            organization: Organization instance
            price_id: Stripe price ID
            quantity: Number of seats
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if checkout is cancelled
        
        Returns:
            Checkout session data with URL
        """
        self._ensure_initialized()
        if not self.is_configured():
            raise ValueError("Stripe is not configured")
        
        # Get or create customer
        customer_id = self.get_or_create_customer(organization)
        
        # Prepare checkout session parameters
        checkout_params = {
            'customer': customer_id,
            'mode': 'subscription',
            'line_items': [{
                'price': price_id,
                'quantity': quantity,
            }],
            'success_url': success_url or f"{current_app.config.get('BASE_URL', '')}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': cancel_url or f"{current_app.config.get('BASE_URL', '')}/billing/cancelled",
            'metadata': {
                'organization_id': str(organization.id),
                'organization_slug': organization.slug,
            },
        }
        
        # Add trial if enabled
        if current_app.config.get('STRIPE_ENABLE_TRIALS', True):
            trial_days = current_app.config.get('STRIPE_TRIAL_DAYS', 14)
            if trial_days > 0:
                checkout_params['subscription_data'] = {
                    'trial_period_days': trial_days,
                    'metadata': checkout_params['metadata'],
                }
        
        # Create checkout session
        session = stripe.checkout.Session.create(**checkout_params)
        
        return {
            'session_id': session.id,
            'url': session.url,
        }
    
    def create_billing_portal_session(self, organization: Organization, 
                                     return_url: str = None) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session for managing subscription.
        
        Args:
            organization: Organization instance
            return_url: URL to return to after portal session
        
        Returns:
            Portal session data with URL
        """
        if not organization.stripe_customer_id:
            raise ValueError("Organization does not have a Stripe customer")
        
        session = stripe.billing_portal.Session.create(
            customer=organization.stripe_customer_id,
            return_url=return_url or f"{current_app.config.get('BASE_URL', '')}/billing",
        )
        
        return {
            'session_id': session.id,
            'url': session.url,
        }
    
    # ========================================
    # Invoice & Payment Info
    # ========================================
    
    def get_upcoming_invoice(self, organization: Organization) -> Optional[Dict[str, Any]]:
        """Get the upcoming invoice for an organization.
        
        Args:
            organization: Organization instance
        
        Returns:
            Invoice data or None if no upcoming invoice
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            return None
        
        try:
            invoice = stripe.Invoice.upcoming(
                customer=organization.stripe_customer_id
            )
            
            return {
                'id': invoice.id,
                'amount_due': invoice.amount_due / 100,  # Convert from cents
                'currency': invoice.currency.upper(),
                'period_start': datetime.fromtimestamp(invoice.period_start),
                'period_end': datetime.fromtimestamp(invoice.period_end),
                'lines': [
                    {
                        'description': line.description,
                        'amount': line.amount / 100,
                        'quantity': line.quantity,
                    }
                    for line in invoice.lines.data
                ],
            }
        except stripe.error.InvalidRequestError:
            return None
    
    def get_invoices(self, organization: Organization, limit: int = 10) -> List[Dict[str, Any]]:
        """Get past invoices for an organization.
        
        Args:
            organization: Organization instance
            limit: Maximum number of invoices to return
        
        Returns:
            List of invoice data dictionaries
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            return []
        
        invoices = stripe.Invoice.list(
            customer=organization.stripe_customer_id,
            limit=limit
        )
        
        return [
            {
                'id': invoice.id,
                'number': invoice.number,
                'amount_paid': invoice.amount_paid / 100,
                'amount_due': invoice.amount_due / 100,
                'currency': invoice.currency.upper(),
                'status': invoice.status,
                'paid': invoice.paid,
                'created': datetime.fromtimestamp(invoice.created),
                'due_date': datetime.fromtimestamp(invoice.due_date) if invoice.due_date else None,
                'invoice_pdf': invoice.invoice_pdf,
                'hosted_invoice_url': invoice.hosted_invoice_url,
            }
            for invoice in invoices.data
        ]
    
    def get_payment_methods(self, organization: Organization) -> List[Dict[str, Any]]:
        """Get payment methods for an organization.
        
        Args:
            organization: Organization instance
        
        Returns:
            List of payment method data
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            return []
        
        payment_methods = stripe.PaymentMethod.list(
            customer=organization.stripe_customer_id,
            type='card'
        )
        
        return [
            {
                'id': pm.id,
                'type': pm.type,
                'card': {
                    'brand': pm.card.brand,
                    'last4': pm.card.last4,
                    'exp_month': pm.card.exp_month,
                    'exp_year': pm.card.exp_year,
                }
            }
            for pm in payment_methods.data
        ]
    
    # ========================================
    # Webhook Processing
    # ========================================
    
    def construct_webhook_event(self, payload: bytes, sig_header: str) -> Any:
        """Construct and verify a Stripe webhook event.
        
        Args:
            payload: Raw request body
            sig_header: Stripe signature header
        
        Returns:
            Stripe Event object
        
        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        self._ensure_initialized()
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")
        
        return stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _update_organization_from_subscription(self, organization: Organization, 
                                              subscription: Any) -> None:
        """Update organization fields from Stripe subscription data.
        
        Args:
            organization: Organization instance
            subscription: Stripe Subscription object
        """
        organization.stripe_subscription_id = subscription.id
        organization.stripe_subscription_status = subscription.status
        
        # Update quantity
        if subscription.items.data:
            organization.subscription_quantity = subscription.items.data[0].quantity
            organization.stripe_price_id = subscription.items.data[0].price.id
        
        # Update trial info
        if subscription.trial_end:
            organization.trial_ends_at = datetime.fromtimestamp(subscription.trial_end)
        
        # Update billing dates
        if subscription.current_period_end:
            organization.next_billing_date = datetime.fromtimestamp(subscription.current_period_end)
        
        # Update subscription plan based on price ID
        single_user_price = current_app.config.get('STRIPE_SINGLE_USER_PRICE_ID')
        team_price = current_app.config.get('STRIPE_TEAM_PRICE_ID')
        
        if organization.stripe_price_id == single_user_price:
            organization.subscription_plan = 'single_user'
        elif organization.stripe_price_id == team_price:
            organization.subscription_plan = 'team'
        
        db.session.commit()
    
    # ========================================
    # Refund Management
    # ========================================
    
    def create_refund(self, organization: Organization, charge_id: str = None, 
                     invoice_id: str = None, amount: Optional[int] = None, 
                     reason: str = None) -> Dict[str, Any]:
        """Create a refund for a charge or invoice.
        
        Args:
            organization: Organization instance
            charge_id: Stripe charge ID to refund (optional if invoice_id provided)
            invoice_id: Stripe invoice ID to refund (optional if charge_id provided)
            amount: Amount to refund in cents (None = full refund)
            reason: Reason for refund ('duplicate', 'fraudulent', 'requested_by_customer')
        
        Returns:
            Refund data
        
        Raises:
            ValueError: If neither charge_id nor invoice_id provided
            stripe.error.StripeError: If refund creation fails
        """
        self._ensure_initialized()
        if not self.is_configured():
            raise ValueError("Stripe is not configured")
        
        # Get charge_id from invoice if needed
        if not charge_id and invoice_id:
            invoice = stripe.Invoice.retrieve(invoice_id)
            if invoice.charge:
                charge_id = invoice.charge
            else:
                raise ValueError("Invoice has no associated charge")
        
        if not charge_id:
            raise ValueError("Either charge_id or invoice_id must be provided")
        
        # Prepare refund parameters
        refund_params = {
            'charge': charge_id,
        }
        
        if amount:
            refund_params['amount'] = amount
        
        if reason:
            refund_params['reason'] = reason
        
        # Create refund
        refund = stripe.Refund.create(**refund_params)
        
        # Log event
        self._log_event(
            organization=organization,
            event_type='refund.created',
            stripe_customer_id=organization.stripe_customer_id,
            stripe_charge_id=charge_id,
            stripe_refund_id=refund.id,
            amount=refund.amount / 100,
            currency=refund.currency.upper(),
            status=refund.status,
            notes=f"Refund created: {reason or 'No reason specified'}"
        )
        
        return {
            'refund_id': refund.id,
            'amount': refund.amount / 100,
            'currency': refund.currency.upper(),
            'status': refund.status,
            'reason': refund.reason,
        }
    
    def get_refunds(self, organization: Organization, limit: int = 10) -> List[Dict[str, Any]]:
        """Get refunds for an organization.
        
        Args:
            organization: Organization instance
            limit: Maximum number of refunds to return
        
        Returns:
            List of refund data dictionaries
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            return []
        
        # Get all charges for the customer first
        charges = stripe.Charge.list(
            customer=organization.stripe_customer_id,
            limit=100
        )
        
        # Collect refunds from all charges
        all_refunds = []
        for charge in charges.data:
            if charge.refunds and charge.refunds.data:
                for refund in charge.refunds.data:
                    all_refunds.append({
                        'id': refund.id,
                        'amount': refund.amount / 100,
                        'currency': refund.currency.upper(),
                        'status': refund.status,
                        'reason': refund.reason,
                        'created': datetime.fromtimestamp(refund.created),
                        'charge_id': charge.id,
                    })
        
        # Sort by creation date and limit
        all_refunds.sort(key=lambda x: x['created'], reverse=True)
        return all_refunds[:limit]
    
    # ========================================
    # Sync & Reconciliation
    # ========================================
    
    def sync_organization_with_stripe(self, organization: Organization) -> Dict[str, Any]:
        """Sync organization data with Stripe to ensure consistency.
        
        Args:
            organization: Organization instance
        
        Returns:
            Dictionary with sync results and any discrepancies found
        """
        self._ensure_initialized()
        if not organization.stripe_customer_id:
            return {'synced': False, 'error': 'No Stripe customer ID'}
        
        discrepancies = []
        
        try:
            # Get customer from Stripe
            customer = stripe.Customer.retrieve(organization.stripe_customer_id)
            
            # Get subscription if exists
            if organization.stripe_subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
                    
                    # Check for discrepancies
                    if subscription.status != organization.stripe_subscription_status:
                        discrepancies.append({
                            'field': 'subscription_status',
                            'local': organization.stripe_subscription_status,
                            'stripe': subscription.status
                        })
                        # Update local status
                        organization.stripe_subscription_status = subscription.status
                    
                    # Check quantity
                    if subscription.items.data:
                        stripe_quantity = subscription.items.data[0].quantity
                        if stripe_quantity != organization.subscription_quantity:
                            discrepancies.append({
                                'field': 'subscription_quantity',
                                'local': organization.subscription_quantity,
                                'stripe': stripe_quantity
                            })
                            # Update local quantity
                            organization.subscription_quantity = stripe_quantity
                    
                    # Update other fields
                    self._update_organization_from_subscription(organization, subscription)
                    
                except stripe.error.InvalidRequestError:
                    discrepancies.append({
                        'field': 'subscription',
                        'error': 'Subscription not found in Stripe but exists locally'
                    })
            
            db.session.commit()
            
            return {
                'synced': True,
                'discrepancies': discrepancies,
                'discrepancy_count': len(discrepancies),
            }
            
        except stripe.error.StripeError as e:
            return {
                'synced': False,
                'error': str(e)
            }
    
    def check_all_organizations_sync(self) -> Dict[str, Any]:
        """Check sync status for all organizations with Stripe customers.
        
        Returns:
            Summary of sync status across all organizations
        """
        self._ensure_initialized()
        if not self.is_configured():
            return {'error': 'Stripe not configured'}
        
        organizations = Organization.query.filter(
            Organization.stripe_customer_id.isnot(None)
        ).all()
        
        results = {
            'total': len(organizations),
            'synced': 0,
            'with_discrepancies': 0,
            'errors': 0,
            'organizations': []
        }
        
        for org in organizations:
            sync_result = self.sync_organization_with_stripe(org)
            
            org_result = {
                'id': org.id,
                'name': org.name,
                'slug': org.slug,
                'synced': sync_result.get('synced', False),
                'discrepancy_count': sync_result.get('discrepancy_count', 0),
                'discrepancies': sync_result.get('discrepancies', []),
                'error': sync_result.get('error')
            }
            
            results['organizations'].append(org_result)
            
            if sync_result.get('synced'):
                results['synced'] += 1
                if sync_result.get('discrepancy_count', 0) > 0:
                    results['with_discrepancies'] += 1
            else:
                results['errors'] += 1
        
        return results
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _log_event(self, organization: Organization, event_type: str, **kwargs) -> None:
        """Log a subscription event.
        
        Args:
            organization: Organization instance
            event_type: Type of event
            **kwargs: Additional event data
        """
        event = SubscriptionEvent(
            event_type=event_type,
            organization_id=organization.id,
            **kwargs
        )
        event.processed = True
        event.processed_at = datetime.utcnow()
        
        db.session.add(event)
        db.session.commit()


# Create a singleton instance
stripe_service = StripeService()

