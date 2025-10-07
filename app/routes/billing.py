"""
Billing Routes

Handles Stripe webhooks, checkout flows, and billing management.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import stripe
import json

from app import db
from app.models.organization import Organization
from app.models.subscription_event import SubscriptionEvent
from app.models.membership import Membership
from app.utils.stripe_service import stripe_service
from app.utils.email_service import email_service
from app.utils.provisioning_service import provisioning_service

bp = Blueprint('billing', __name__, url_prefix='/billing')


# ========================================
# Stripe Webhook Handlers
# ========================================

@bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events.
    
    This endpoint processes webhook events from Stripe and updates
    the database accordingly. It handles subscription lifecycle events,
    payment events, and more.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except ValueError as e:
        current_app.logger.error(f"Invalid webhook payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Invalid webhook signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Log the event
    current_app.logger.info(f"Received Stripe webhook: {event.type}")
    
    # Route to appropriate handler
    handlers = {
        'invoice.paid': handle_invoice_paid,
        'invoice.payment_failed': handle_invoice_payment_failed,
        'invoice.payment_action_required': handle_invoice_payment_action_required,
        'customer.subscription.created': handle_subscription_created,
        'customer.subscription.updated': handle_subscription_updated,
        'customer.subscription.deleted': handle_subscription_deleted,
        'customer.subscription.trial_will_end': handle_subscription_trial_will_end,
    }
    
    handler = handlers.get(event.type)
    if handler:
        try:
            handler(event)
        except Exception as e:
            current_app.logger.error(f"Error processing webhook {event.type}: {e}", exc_info=True)
            return jsonify({'error': 'Processing failed'}), 500
    else:
        current_app.logger.info(f"Unhandled webhook event type: {event.type}")
    
    return jsonify({'status': 'success'}), 200


def handle_invoice_paid(event):
    """Handle invoice.paid webhook event.
    
    This is triggered when an invoice is successfully paid.
    We activate the subscription and provision the tenant.
    """
    invoice = event.data.object
    customer_id = invoice.customer
    subscription_id = invoice.subscription
    
    # Find organization by customer ID
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        current_app.logger.warning(f"Organization not found for customer {customer_id}")
        return
    
    # Clear any billing issues
    organization.update_billing_issue(has_issue=False)
    organization.stripe_subscription_status = 'active'
    
    # Update next billing date
    if invoice.period_end:
        organization.next_billing_date = datetime.fromtimestamp(invoice.period_end)
    
    # Activate organization if it was suspended
    if organization.status == 'suspended':
        organization.activate()
    
    db.session.commit()
    
    # Log event
    subscription_event = SubscriptionEvent(
        organization_id=organization.id,
        event_type='invoice.paid',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_invoice_id=invoice.id,
        amount=invoice.amount_paid / 100,
        currency=invoice.currency.upper(),
        status='paid',
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict())
    )
    db.session.add(subscription_event)
    db.session.commit()
    
    # AUTOMATED PROVISIONING: If this is the first payment, provision the organization
    # Check if organization needs provisioning (doesn't have any projects yet)
    if organization.projects.count() == 0:
        current_app.logger.info(f"First payment detected for {organization.name}, triggering provisioning")
        
        # Find admin user (first member with admin role)
        admin_membership = organization.memberships.filter_by(role='admin', status='active').first()
        admin_user = admin_membership.user if admin_membership else None
        
        # Trigger provisioning
        try:
            provisioning_result = provisioning_service.provision_organization(
                organization=organization,
                admin_user=admin_user,
                trigger='payment'
            )
            
            if provisioning_result.get('success'):
                current_app.logger.info(f"Successfully provisioned {organization.name}: {provisioning_result}")
            else:
                current_app.logger.error(f"Provisioning failed for {organization.name}: {provisioning_result.get('errors')}")
        except Exception as e:
            current_app.logger.error(f"Error during provisioning for {organization.name}: {e}", exc_info=True)
    
    current_app.logger.info(f"Invoice paid for organization {organization.name} ({organization.id})")


def handle_invoice_payment_failed(event):
    """Handle invoice.payment_failed webhook event.
    
    This is triggered when a payment attempt fails.
    We mark the billing issue and start the dunning sequence.
    """
    invoice = event.data.object
    customer_id = invoice.customer
    subscription_id = invoice.subscription
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        current_app.logger.warning(f"Organization not found for customer {customer_id}")
        return
    
    # Mark billing issue
    organization.update_billing_issue(has_issue=True)
    organization.stripe_subscription_status = 'past_due'
    db.session.commit()
    
    # Log event
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='invoice.payment_failed',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_invoice_id=invoice.id,
        amount=invoice.amount_due / 100,
        currency=invoice.currency.upper(),
        status='payment_failed',
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict()),
        notes=f"Payment failed. Attempt count: {invoice.attempt_count}"
    ).mark_processed(success=True)
    
    # Send notification email to admins
    _send_payment_failed_notification(organization, invoice)
    
    current_app.logger.warning(f"Payment failed for organization {organization.name} ({organization.id})")


def handle_invoice_payment_action_required(event):
    """Handle invoice.payment_action_required webhook event.
    
    This is triggered when additional authentication is required (e.g., 3D Secure).
    """
    invoice = event.data.object
    customer_id = invoice.customer
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        return
    
    # Log event
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='invoice.payment_action_required',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=invoice.subscription,
        stripe_invoice_id=invoice.id,
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict()),
        notes="Payment requires additional authentication"
    ).mark_processed(success=True)
    
    # Send notification to admins
    _send_action_required_notification(organization, invoice)


def handle_subscription_created(event):
    """Handle customer.subscription.created webhook event."""
    subscription = event.data.object
    customer_id = subscription.customer
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        return
    
    # Update organization
    stripe_service._update_organization_from_subscription(organization, subscription)
    
    # Log event
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='customer.subscription.created',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.id,
        status=subscription.status,
        quantity=subscription.items.data[0].quantity if subscription.items.data else 1,
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict())
    ).mark_processed(success=True)


def handle_subscription_updated(event):
    """Handle customer.subscription.updated webhook event.
    
    This handles seat changes, status updates, and proration.
    """
    subscription = event.data.object
    customer_id = subscription.customer
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        return
    
    # Get previous values
    previous_status = organization.stripe_subscription_status
    previous_quantity = organization.subscription_quantity
    
    # Update organization
    stripe_service._update_organization_from_subscription(organization, subscription)
    
    # Log event
    new_quantity = subscription.items.data[0].quantity if subscription.items.data else 1
    
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='customer.subscription.updated',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.id,
        status=subscription.status,
        previous_status=previous_status,
        quantity=new_quantity,
        previous_quantity=previous_quantity,
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict()),
        notes=f"Status: {previous_status} → {subscription.status}, Seats: {previous_quantity} → {new_quantity}"
    ).mark_processed(success=True)
    
    current_app.logger.info(f"Subscription updated for organization {organization.name}")


def handle_subscription_deleted(event):
    """Handle customer.subscription.deleted webhook event.
    
    This is triggered when a subscription is cancelled or expires.
    We disable or downgrade the account.
    """
    subscription = event.data.object
    customer_id = subscription.customer
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        return
    
    # Update organization status
    organization.stripe_subscription_status = 'canceled'
    organization.subscription_ends_at = datetime.utcnow()
    organization.status = 'suspended'  # Suspend the organization
    organization.subscription_plan = 'free'  # Downgrade to free
    db.session.commit()
    
    # Log event
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='customer.subscription.deleted',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.id,
        status='canceled',
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict()),
        notes="Subscription deleted - organization suspended"
    ).mark_processed(success=True)
    
    # Send notification
    _send_subscription_cancelled_notification(organization)
    
    current_app.logger.warning(f"Subscription deleted for organization {organization.name} ({organization.id})")


def handle_subscription_trial_will_end(event):
    """Handle customer.subscription.trial_will_end webhook event.
    
    This is triggered 3 days before a trial ends.
    """
    subscription = event.data.object
    customer_id = subscription.customer
    
    # Find organization
    organization = Organization.query.filter_by(stripe_customer_id=customer_id).first()
    if not organization:
        return
    
    # Log event
    SubscriptionEvent(
        organization_id=organization.id,
        event_type='customer.subscription.trial_will_end',
        event_id=event.id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.id,
        processed=True,
        processed_at=datetime.utcnow(),
        raw_payload=json.dumps(event.to_dict()),
        notes=f"Trial ending soon - {organization.trial_days_remaining} days remaining"
    ).mark_processed(success=True)
    
    # Send reminder email
    _send_trial_ending_notification(organization)


# ========================================
# Billing Management Views
# ========================================

@bp.route('/')
@login_required
def index():
    """Billing dashboard - view subscription, invoices, and payment methods."""
    # Get current organization (you'll need to implement organization context)
    # For now, we'll assume you have a way to get the current organization
    organization = _get_current_organization()
    
    if not organization:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user is admin
    if not Membership.user_is_admin(current_user.id, organization.id):
        flash('Only admins can access billing settings', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get billing data
    subscription_data = None
    invoices = []
    upcoming_invoice = None
    payment_methods = []
    
    if stripe_service.is_configured() and organization.stripe_customer_id:
        try:
            invoices = stripe_service.get_invoices(organization, limit=10)
            upcoming_invoice = stripe_service.get_upcoming_invoice(organization)
            payment_methods = stripe_service.get_payment_methods(organization)
        except Exception as e:
            current_app.logger.error(f"Error fetching billing data: {e}")
            flash('Error loading billing data', 'error')
    
    return render_template(
        'billing/index.html',
        organization=organization,
        invoices=invoices,
        upcoming_invoice=upcoming_invoice,
        payment_methods=payment_methods,
        stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    )


@bp.route('/subscribe/<plan>')
@login_required
def subscribe(plan):
    """Start subscription checkout flow."""
    organization = _get_current_organization()
    
    if not organization:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user is admin
    if not Membership.user_is_admin(current_user.id, organization.id):
        flash('Only admins can manage subscriptions', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Determine price ID and quantity
    if plan == 'single':
        price_id = current_app.config.get('STRIPE_SINGLE_USER_PRICE_ID')
        quantity = 1
    elif plan == 'team':
        price_id = current_app.config.get('STRIPE_TEAM_PRICE_ID')
        # Calculate current active users
        quantity = organization.member_count or 1
    else:
        flash('Invalid subscription plan', 'error')
        return redirect(url_for('billing.index'))
    
    # Create checkout session
    try:
        session_data = stripe_service.create_checkout_session(
            organization=organization,
            price_id=price_id,
            quantity=quantity,
            success_url=url_for('billing.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing.index', _external=True)
        )
        
        return redirect(session_data['url'])
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {e}")
        flash('Error starting checkout process', 'error')
        return redirect(url_for('billing.index'))


@bp.route('/success')
@login_required
def success():
    """Subscription checkout success page."""
    session_id = request.args.get('session_id')
    
    flash('Subscription activated successfully!', 'success')
    return redirect(url_for('billing.index'))


@bp.route('/portal')
@login_required
def portal():
    """Redirect to Stripe Customer Portal for managing subscription."""
    organization = _get_current_organization()
    
    if not organization:
        flash('No organization found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if user is admin
    if not Membership.user_is_admin(current_user.id, organization.id):
        flash('Only admins can access billing portal', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        portal_session = stripe_service.create_billing_portal_session(
            organization=organization,
            return_url=url_for('billing.index', _external=True)
        )
        
        return redirect(portal_session['url'])
    except Exception as e:
        current_app.logger.error(f"Error creating portal session: {e}")
        flash('Error accessing billing portal', 'error')
        return redirect(url_for('billing.index'))


# ========================================
# Helper Functions
# ========================================

def _get_current_organization():
    """Get the current user's organization.
    
    This is a placeholder - you'll need to implement proper organization
    context management based on your application's structure.
    """
    # Get the user's active memberships
    memberships = Membership.get_user_active_memberships(current_user.id)
    
    if not memberships:
        return None
    
    # Return the first organization (you might want to implement org switching)
    return memberships[0].organization


def _send_payment_failed_notification(organization, invoice):
    """Send payment failed notification to organization admins."""
    admins = organization.get_admins()
    
    for membership in admins:
        if membership.user.email:
            try:
                # TODO: Implement template-based email for payment failures
                # email_service.send_email(
                #     to_email=membership.user.email,
                #     subject=f"Payment Failed - {organization.name}",
                #     body_text=f"Your payment for {organization.name} has failed. Please update your payment method.",
                #     body_html=None
                # )
                pass
            except Exception as e:
                current_app.logger.error(f"Failed to send payment notification: {e}")
    
    # Update last email sent timestamp
    organization.last_billing_email_sent_at = datetime.utcnow()
    db.session.commit()


def _send_action_required_notification(organization, invoice):
    """Send payment action required notification."""
    admins = organization.get_admins()
    
    for membership in admins:
        if membership.user.email:
            try:
                # TODO: Implement template-based email for action required
                # email_service.send_email(
                #     to_email=membership.user.email,
                #     subject=f"Payment Action Required - {organization.name}",
                #     body_text=f"Action required for your {organization.name} subscription.",
                #     body_html=None
                # )
                pass
            except Exception as e:
                current_app.logger.error(f"Failed to send action required notification: {e}")


def _send_subscription_cancelled_notification(organization):
    """Send subscription cancelled notification."""
    admins = organization.get_admins()
    
    for membership in admins:
        if membership.user.email:
            try:
                # TODO: Implement template-based email for subscription cancelled
                # email_service.send_email(
                #     to_email=membership.user.email,
                #     subject=f"Subscription Cancelled - {organization.name}",
                #     body_text=f"Your subscription for {organization.name} has been cancelled.",
                #     body_html=None
                # )
                pass
            except Exception as e:
                current_app.logger.error(f"Failed to send cancellation notification: {e}")


def _send_trial_ending_notification(organization):
    """Send trial ending soon notification."""
    admins = organization.get_admins()
    
    for membership in admins:
        if membership.user.email:
            try:
                # TODO: Implement template-based email for trial ending
                # email_service.send_email(
                #     to_email=membership.user.email,
                #     subject=f"Your Trial is Ending Soon - {organization.name}",
                #     body_text=f"Your trial for {organization.name} ends in {organization.trial_days_remaining} days.",
                #     body_html=None
                # )
                pass
            except Exception as e:
                current_app.logger.error(f"Failed to send trial ending notification: {e}")

