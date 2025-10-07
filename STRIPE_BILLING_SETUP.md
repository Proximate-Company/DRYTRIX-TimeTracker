# Stripe Billing Integration - Setup Guide

This guide walks you through setting up Stripe billing for your TimeTracker installation.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Stripe Dashboard Setup](#stripe-dashboard-setup)
4. [Application Configuration](#application-configuration)
5. [Database Migration](#database-migration)
6. [Webhook Configuration](#webhook-configuration)
7. [Testing](#testing)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Stripe billing integration provides:

- **Subscription Management**: Automatic billing for Single User (€5/month) and Team (€6/user/month) plans
- **Seat-Based Billing**: Automatic seat synchronization when users are added/removed
- **Trial Periods**: 14-day free trial (configurable)
- **Proration**: Automatic proration when changing seat counts
- **Dunning Management**: Automated handling of failed payments with email notifications
- **EU VAT Compliance**: Built-in VAT collection using Stripe Billing
- **Customer Portal**: Self-service billing management via Stripe Customer Portal

---

## Prerequisites

Before starting, ensure you have:

1. A Stripe account (sign up at https://stripe.com)
2. Access to your Stripe Dashboard
3. Database access (PostgreSQL)
4. SMTP server configured for email notifications
5. HTTPS enabled for webhook endpoints (required by Stripe)

---

## Stripe Dashboard Setup

### Step 1: Create Products and Prices

1. **Login to Stripe Dashboard**: https://dashboard.stripe.com

2. **Create Single User Product**:
   - Navigate to: Products → Add product
   - Name: `TimeTracker Single User`
   - Description: `Single user subscription for TimeTracker`
   - Pricing:
     - Price: `€5.00`
     - Billing period: `Monthly`
     - Currency: `EUR`
   - Save and copy the **Price ID** (starts with `price_...`)

3. **Create Team Product**:
   - Navigate to: Products → Add product
   - Name: `TimeTracker Team`
   - Description: `Per-seat team subscription for TimeTracker`
   - Pricing:
     - Price: `€6.00`
     - Billing period: `Monthly`
     - Currency: `EUR`
     - **Important**: Enable "Usage is metered" or set up quantity-based pricing
   - Save and copy the **Price ID** (starts with `price_...`)

### Step 2: Enable Customer Portal

1. Navigate to: Settings → Billing → Customer portal
2. Click "Activate test link"
3. Configure portal settings:
   - ✅ **Update subscription**: Allow customers to change plans
   - ✅ **Cancel subscription**: Allow customers to cancel
   - ✅ **Update payment method**: Allow updating cards
   - ✅ **View invoice history**: Show past invoices
4. Save settings

### Step 3: Configure Tax Settings

1. Navigate to: Settings → Tax
2. Enable **Stripe Tax** for EU VAT collection
3. Configure tax settings:
   - Enable automatic tax calculation
   - Add your business location
   - Enable invoice generation
4. Save tax settings

### Step 4: Get API Keys

1. Navigate to: Developers → API keys
2. Copy your keys:
   - **Publishable key** (starts with `pk_test_...` or `pk_live_...`)
   - **Secret key** (starts with `sk_test_...` or `sk_live_...`)
3. **Important**: Keep your Secret key secure and never commit it to version control

---

## Application Configuration

### Step 1: Install Stripe SDK

The Stripe SDK is already included in `requirements.txt`. If you're installing manually:

```bash
pip install stripe==7.9.0
```

### Step 2: Set Environment Variables

Add these variables to your `.env` file or environment configuration:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs
STRIPE_SINGLE_USER_PRICE_ID=price_xxxxx  # From Step 1.2
STRIPE_TEAM_PRICE_ID=price_xxxxx         # From Step 1.3

# Stripe Configuration
STRIPE_ENABLE_TRIALS=true
STRIPE_TRIAL_DAYS=14
STRIPE_ENABLE_PRORATION=true
STRIPE_TAX_BEHAVIOR=exclusive  # or 'inclusive'
```

**Security Notes**:
- Never commit `.env` files to version control
- Use different keys for test and production environments
- Rotate keys regularly in production
- Use environment-specific secrets management (e.g., AWS Secrets Manager, Azure Key Vault)

### Step 3: Update Configuration

The configuration is already set up in `app/config.py`. Verify these settings are present:

```python
# Stripe billing settings
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_SINGLE_USER_PRICE_ID = os.getenv('STRIPE_SINGLE_USER_PRICE_ID')
STRIPE_TEAM_PRICE_ID = os.getenv('STRIPE_TEAM_PRICE_ID')
STRIPE_ENABLE_TRIALS = os.getenv('STRIPE_ENABLE_TRIALS', 'true').lower() == 'true'
STRIPE_TRIAL_DAYS = int(os.getenv('STRIPE_TRIAL_DAYS', 14))
STRIPE_ENABLE_PRORATION = os.getenv('STRIPE_ENABLE_PRORATION', 'true').lower() == 'true'
```

---

## Database Migration

### Run the Migration

The migration adds new fields to the `organizations` table and creates the `subscription_events` table.

```bash
# Using psql
psql -U timetracker -d timetracker -f migrations/add_stripe_billing_fields.sql

# Or using Flask-Migrate (if you've created an Alembic migration)
flask db upgrade
```

### Verify Migration

Check that the migration was successful:

```sql
-- Check organizations table has new columns
\d organizations

-- Check subscription_events table was created
\d subscription_events

-- Verify indexes
\di subscription_events*
```

---

## Webhook Configuration

Webhooks are critical for billing automation. They notify your application about subscription events.

### Step 1: Set Up Local Testing (Development)

For local development, use the Stripe CLI:

```bash
# Install Stripe CLI
# macOS
brew install stripe/stripe-cli/stripe

# Windows
scoop install stripe

# Linux
wget https://github.com/stripe/stripe-cli/releases/download/vX.X.X/stripe_X.X.X_linux_x86_64.tar.gz
tar -xvf stripe_X.X.X_linux_x86_64.tar.gz

# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:5000/billing/webhooks/stripe
```

Copy the webhook signing secret (starts with `whsec_...`) and add it to your `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_from_cli
```

### Step 2: Set Up Production Webhooks

1. Navigate to: Developers → Webhooks → Add endpoint
2. Endpoint URL: `https://your-domain.com/billing/webhooks/stripe`
3. Description: `TimeTracker Billing Webhooks`
4. Events to send:
   - ✅ `invoice.paid`
   - ✅ `invoice.payment_failed`
   - ✅ `invoice.payment_action_required`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `customer.subscription.trial_will_end`
5. Click "Add endpoint"
6. Copy the **Signing secret** and update your production environment variables

### Step 3: Verify Webhook Setup

Test the webhook endpoint:

```bash
# Using Stripe CLI
stripe trigger invoice.paid

# Check your application logs for:
# "Received Stripe webhook: invoice.paid"
# "Invoice paid for organization..."
```

**Important Security Notes**:
- The webhook endpoint verifies signatures using `STRIPE_WEBHOOK_SECRET`
- The endpoint is CSRF-exempt (required for Stripe webhooks)
- Ensure HTTPS is enabled in production
- Never disable signature verification

---

## Testing

### Test Mode

All testing should be done with Stripe test mode keys (starting with `sk_test_` and `pk_test_`).

### Test Credit Cards

Use these test cards (from Stripe):

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0025 0000 3155
```

- Any future expiry date (e.g., 12/34)
- Any 3-digit CVC
- Any zip code

### Test Scenarios

#### 1. Test Single User Subscription

```bash
# Navigate to your application
http://localhost:5000/billing

# Click "Subscribe" for Single User plan
# Complete checkout with test card 4242 4242 4242 4242
# Verify subscription is active in dashboard
```

#### 2. Test Team Subscription with Seat Changes

```bash
# Subscribe to Team plan
# Add a new user to organization
# Check that seats were automatically synced in Stripe Dashboard

# Remove a user
# Verify seat count decreased
```

#### 3. Test Failed Payment

```bash
# Use declined card: 4000 0000 0000 0002
# Trigger payment
# Verify:
# - Organization status shows billing issue
# - Email notification sent
# - Subscription event logged
```

#### 4. Test Trial Period

```bash
# Create new subscription
# Verify trial_ends_at is set to 14 days from now
# Check organization.is_on_trial returns True
# Wait 11 days or manually trigger trial_will_end event
# Verify email notification sent
```

#### 5. Test Webhooks

```bash
# Use Stripe CLI to trigger events
stripe trigger invoice.paid
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted

# Check application logs and database
# Verify subscription_events table has entries
# Verify organization status updated
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Replace test API keys with live keys
- [ ] Update webhook endpoint to production URL
- [ ] Verify HTTPS is enabled
- [ ] Test webhook signature verification
- [ ] Enable Stripe Radar (fraud protection)
- [ ] Set up Stripe email notifications
- [ ] Configure backup payment retry schedule
- [ ] Test email delivery (SMTP configured)
- [ ] Set up monitoring and alerting
- [ ] Document incident response procedures

### Environment Variables (Production)

```bash
# Stripe Live Keys
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_production_webhook_secret

# Production Price IDs
STRIPE_SINGLE_USER_PRICE_ID=price_live_xxxxx
STRIPE_TEAM_PRICE_ID=price_live_xxxxx

# Production Configuration
STRIPE_ENABLE_TRIALS=true
STRIPE_TRIAL_DAYS=14
STRIPE_ENABLE_PRORATION=true
```

### Post-Deployment Verification

1. **Test Checkout Flow**:
   - Create a test subscription
   - Verify payment processing
   - Check subscription activation

2. **Verify Webhooks**:
   - Check webhook endpoint is receiving events
   - Monitor webhook logs in Stripe Dashboard
   - Verify signature verification is working

3. **Test Email Notifications**:
   - Trigger a test payment failure
   - Verify email delivery
   - Check email formatting

4. **Monitor Subscription Events**:
   ```sql
   -- Check recent subscription events
   SELECT * FROM subscription_events 
   ORDER BY created_at DESC 
   LIMIT 10;
   ```

### Monitoring

Set up monitoring for:

- Webhook failures (check Stripe Dashboard → Developers → Webhooks)
- Failed payments (check `organizations` with `billing_issue_detected_at`)
- Unprocessed events (check `subscription_events` where `processed = false`)
- Email delivery failures

---

## Troubleshooting

### Webhooks Not Receiving Events

**Problem**: Webhook endpoint not receiving events from Stripe.

**Solutions**:
1. Verify endpoint URL is correct and publicly accessible
2. Check HTTPS is enabled (required by Stripe)
3. Test webhook manually from Stripe Dashboard
4. Check application logs for errors
5. Verify webhook signature secret is correct
6. Check firewall/security groups allow Stripe IPs

**Debug**:
```bash
# Check recent webhook attempts in Stripe Dashboard
# Developers → Webhooks → [Your endpoint] → View logs

# Check application logs
grep "Received Stripe webhook" logs/timetracker.log
```

### Signature Verification Failed

**Problem**: Webhook returns "Invalid signature" error.

**Solutions**:
1. Verify `STRIPE_WEBHOOK_SECRET` matches the endpoint's signing secret
2. Ensure raw request body is passed to verification (not parsed JSON)
3. Check for proxy/middleware modifying the request
4. Verify endpoint hasn't expired (regenerate if needed)

### Payment Failed Not Triggering Emails

**Problem**: `invoice.payment_failed` webhook received but no email sent.

**Solutions**:
1. Verify SMTP configuration in environment
2. Check organization has valid `billing_email` or `contact_email`
3. Check email service logs
4. Verify email templates exist
5. Check `last_billing_email_sent_at` for rate limiting

**Debug**:
```python
# Test email service directly
from app.utils.email_service import send_email

send_email(
    to_email='test@example.com',
    subject='Test',
    template='billing/payment_failed.html',
    organization=org,
    invoice=invoice,
    user=user
)
```

### Seats Not Syncing

**Problem**: Adding/removing users doesn't update Stripe subscription quantity.

**Solutions**:
1. Verify organization has `subscription_plan = 'team'`
2. Check organization has active subscription
3. Verify Stripe API keys are correct
4. Check application logs for sync errors
5. Manually trigger sync:

```python
from app.utils.seat_sync import seat_sync_service

result = seat_sync_service.sync_seats(organization)
print(result)
```

### Subscription Events Not Logging

**Problem**: Webhook events processed but not appearing in `subscription_events` table.

**Solutions**:
1. Check database connection
2. Verify `subscription_events` table exists
3. Check for database errors in logs
4. Verify organization_id is correct
5. Check event deduplication (event_id must be unique)

**Debug**:
```sql
-- Check if events are being inserted
SELECT COUNT(*) FROM subscription_events;

-- Check for recent failed events
SELECT * FROM subscription_events 
WHERE processing_error IS NOT NULL 
ORDER BY created_at DESC;
```

### Trial Not Starting

**Problem**: New subscriptions not receiving trial period.

**Solutions**:
1. Verify `STRIPE_ENABLE_TRIALS=true`
2. Check `STRIPE_TRIAL_DAYS` is set
3. Verify product/price allows trials in Stripe Dashboard
4. Check subscription creation parameters

### Customer Portal Not Working

**Problem**: Customer Portal button returns error or doesn't redirect.

**Solutions**:
1. Verify Customer Portal is activated in Stripe Dashboard
2. Check organization has valid `stripe_customer_id`
3. Verify Stripe API keys are correct
4. Check return URL is valid

---

## API Reference

### Stripe Service

Main service class for Stripe interactions: `app/utils/stripe_service.py`

```python
from app.utils.stripe_service import stripe_service

# Create customer
customer_id = stripe_service.create_customer(organization, email='test@example.com')

# Create subscription
result = stripe_service.create_subscription(
    organization=org,
    price_id='price_xxxxx',
    quantity=5,
    trial_days=14
)

# Update seats
result = stripe_service.update_subscription_quantity(
    organization=org,
    new_quantity=10,
    prorate=True
)

# Cancel subscription
result = stripe_service.cancel_subscription(
    organization=org,
    at_period_end=True
)
```

### Seat Sync Service

Automatic seat synchronization: `app/utils/seat_sync.py`

```python
from app.utils.seat_sync import seat_sync_service

# Sync seats
result = seat_sync_service.sync_seats(organization)

# Check if can add member
check = seat_sync_service.check_seat_limit(organization)
if check['can_add']:
    # Add member
    pass
```

---

## Support

For issues related to:

- **Stripe Integration**: Check Stripe Dashboard logs and webhook history
- **Application Errors**: Check application logs (`logs/timetracker.log`)
- **Database Issues**: Check PostgreSQL logs
- **Email Delivery**: Check SMTP logs and email service status

---

## Appendix

### Webhook Event Types

| Event Type | Trigger | Handler | Action Taken |
|------------|---------|---------|--------------|
| `invoice.paid` | Successful payment | `handle_invoice_paid` | Activate subscription, clear billing issues |
| `invoice.payment_failed` | Failed payment | `handle_invoice_payment_failed` | Mark billing issue, send notification |
| `invoice.payment_action_required` | 3D Secure required | `handle_invoice_payment_action_required` | Send action required notification |
| `customer.subscription.created` | New subscription | `handle_subscription_created` | Log subscription creation |
| `customer.subscription.updated` | Subscription changed | `handle_subscription_updated` | Update org data, log changes |
| `customer.subscription.deleted` | Subscription cancelled | `handle_subscription_deleted` | Suspend organization, downgrade to free |
| `customer.subscription.trial_will_end` | 3 days before trial ends | `handle_subscription_trial_will_end` | Send reminder email |

### Database Schema

**organizations** (new fields):
```sql
stripe_price_id VARCHAR(100)           -- Current price ID
subscription_quantity INTEGER          -- Number of seats
next_billing_date TIMESTAMP           -- Next billing date
billing_issue_detected_at TIMESTAMP   -- When payment failed
last_billing_email_sent_at TIMESTAMP  -- Last dunning email sent
```

**subscription_events** (new table):
```sql
id SERIAL PRIMARY KEY
organization_id INTEGER               -- FK to organizations
event_type VARCHAR(100)              -- Stripe event type
event_id VARCHAR(100) UNIQUE         -- Stripe event ID
stripe_customer_id VARCHAR(100)      -- Stripe customer ID
stripe_subscription_id VARCHAR(100)  -- Stripe subscription ID
status VARCHAR(50)                   -- Current status
quantity INTEGER                     -- Seat count
amount NUMERIC(10,2)                -- Payment amount
processed BOOLEAN                    -- Processing status
raw_payload TEXT                     -- Full webhook JSON
created_at TIMESTAMP                -- Event creation time
...
```

---

**Last Updated**: October 7, 2025  
**Version**: 1.0.0

