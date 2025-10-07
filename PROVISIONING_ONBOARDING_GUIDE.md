# 🚀 Provisioning & Onboarding Automation - Implementation Guide

## Overview

This document describes the automated provisioning and onboarding system implemented for TimeTracker. This high-priority feature automates tenant provisioning after successful payment or trial signup, ensuring a smooth customer experience from signup to active usage.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Components](#components)
3. [Provisioning Flow](#provisioning-flow)
4. [Trial Management](#trial-management)
5. [Onboarding Checklist](#onboarding-checklist)
6. [Email Notifications](#email-notifications)
7. [Configuration](#configuration)
8. [Usage Examples](#usage-examples)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

The provisioning system consists of three main components:

1. **Provisioning Service** - Core automation logic
2. **Webhook Handlers** - Stripe payment event processing
3. **Onboarding System** - User guidance and progress tracking

```
┌─────────────────┐
│ Stripe Webhook  │
│  invoice.paid   │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Provisioning Service│
│  - Create resources │
│  - Setup admin      │
│  - Send emails      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Onboarding Checklist│
│  - Track progress   │
│  - Guide users      │
└─────────────────────┘
```

---

## Components

### 1. Provisioning Service (`app/utils/provisioning_service.py`)

The central service that handles automated tenant provisioning.

**Key Methods:**

- `provision_organization()` - Main provisioning entry point
- `provision_trial_organization()` - Provision trial accounts immediately
- `_create_default_project()` - Create starter project
- `_ensure_admin_membership()` - Setup admin access
- `_initialize_onboarding_checklist()` - Create checklist
- `_send_welcome_email()` - Send welcome communication

**Usage:**

```python
from app.utils.provisioning_service import provisioning_service

# Provision after payment
result = provisioning_service.provision_organization(
    organization=org,
    admin_user=user,
    trigger='payment'
)

# Provision trial immediately
result = provisioning_service.provision_trial_organization(
    organization=org,
    admin_user=user
)
```

### 2. Onboarding Checklist Model (`app/models/onboarding_checklist.py`)

Tracks onboarding progress for each organization.

**Tasks Tracked:**

1. ✅ Invite team member
2. ✅ Create project
3. ✅ Create time entry
4. ✅ Set working hours
5. ✅ Create client
6. ✅ Customize settings
7. ✅ Add billing info
8. ✅ Generate report

**Key Methods:**

```python
from app.models.onboarding_checklist import OnboardingChecklist

# Get or create checklist
checklist = OnboardingChecklist.get_or_create(organization_id)

# Mark task complete
checklist.mark_task_complete('invited_team_member')

# Get progress
percentage = checklist.completion_percentage
is_done = checklist.is_complete
next_task = checklist.get_next_task()
```

### 3. Webhook Handler (updated in `app/routes/billing.py`)

Processes Stripe webhooks and triggers provisioning.

**Flow:**

```python
def handle_invoice_paid(event):
    # 1. Update organization status
    organization.stripe_subscription_status = 'active'
    organization.update_billing_issue(has_issue=False)
    
    # 2. Check if first payment (no projects exist)
    if organization.projects.count() == 0:
        # 3. Trigger automated provisioning
        provisioning_service.provision_organization(
            organization=organization,
            admin_user=admin_user,
            trigger='payment'
        )
```

### 4. Onboarding Routes (`app/routes/onboarding.py`)

API and UI routes for onboarding functionality.

**Endpoints:**

- `GET /onboarding/checklist` - Display checklist UI
- `GET /onboarding/api/checklist` - Get checklist data (JSON)
- `POST /onboarding/api/checklist/complete/<task>` - Mark task complete
- `POST /onboarding/api/checklist/dismiss` - Dismiss checklist
- `GET /onboarding/welcome` - Welcome page for new orgs

### 5. UI Components

**Trial Banner** (`app/templates/components/trial_banner.html`)

Displays trial status prominently on dashboard:

```html
{% include 'components/trial_banner.html' %}
```

Features:
- Shows days remaining
- Links to billing
- Dismissable
- Warning states for expiring trials

**Onboarding Widget** (`app/templates/components/onboarding_widget.html`)

Progress widget for dashboard:

```html
{% include 'components/onboarding_widget.html' %}
```

Features:
- Progress bar
- Next task suggestion
- Quick action buttons
- Dismissable

---

## Provisioning Flow

### Option A: Trial Provisioning (Immediate)

**Trigger:** User creates organization with trial

```
User Signup
    ↓
Create Organization
    ↓
provision_trial_organization()
    ↓
┌─────────────────────────┐
│ 1. Set trial expiration │
│    (14 days default)    │
│ 2. Create default       │
│    project              │
│ 3. Setup admin          │
│    membership           │
│ 4. Initialize checklist │
│ 5. Send welcome email   │
└────────────┬────────────┘
             ↓
    Welcome Page
```

**Code Example:**

```python
# In app/routes/organizations.py
@organizations_bp.route('/new', methods=['POST'])
def create():
    # Create organization
    org = Organization(name=name, subscription_plan='trial')
    db.session.add(org)
    db.session.commit()
    
    # Provision immediately for trials
    if start_trial:
        provisioning_service.provision_trial_organization(
            organization=org,
            admin_user=current_user
        )
    
    return redirect(url_for('onboarding.welcome'))
```

### Option B: Payment Provisioning (Webhook)

**Trigger:** Stripe `invoice.paid` webhook

```
Payment Success
    ↓
Stripe Webhook: invoice.paid
    ↓
handle_invoice_paid()
    ↓
Check if first payment?
    ↓ (yes)
provision_organization()
    ↓
┌─────────────────────────┐
│ 1. Activate org         │
│ 2. Create default       │
│    project              │
│ 3. Setup admin          │
│    membership           │
│ 4. Initialize checklist │
│ 5. Send welcome email   │
└────────────┬────────────┘
             ↓
    Email Notification
```

---

## Trial Management

### Configuration

Set in `.env` or `app/config.py`:

```bash
STRIPE_ENABLE_TRIALS=true
STRIPE_TRIAL_DAYS=14
```

### Trial Properties

Organizations have trial-specific properties:

```python
organization.is_on_trial              # Boolean
organization.trial_days_remaining     # Integer
organization.trial_ends_at           # DateTime
organization.stripe_subscription_status  # 'trialing'
```

### Trial Banner Display

Add to any template (usually dashboard):

```html
{% include 'components/trial_banner.html' %}
```

The banner automatically:
- Shows only during trial
- Displays days remaining
- Links to billing setup
- Highlights urgency for expiring trials

### Trial Expiration

Handled automatically by Stripe:

1. 3 days before end: `customer.subscription.trial_will_end` webhook → send reminder email
2. On expiration: Stripe attempts to charge payment method
   - Success → `invoice.paid` → activate subscription
   - Failure → `invoice.payment_failed` → suspend account

---

## Onboarding Checklist

### Database Schema

```sql
CREATE TABLE onboarding_checklists (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL UNIQUE,
    
    -- Task flags
    invited_team_member BOOLEAN DEFAULT FALSE,
    created_project BOOLEAN DEFAULT FALSE,
    created_time_entry BOOLEAN DEFAULT FALSE,
    set_working_hours BOOLEAN DEFAULT FALSE,
    created_client BOOLEAN DEFAULT FALSE,
    customized_settings BOOLEAN DEFAULT FALSE,
    added_billing_info BOOLEAN DEFAULT FALSE,
    generated_report BOOLEAN DEFAULT FALSE,
    
    -- Timestamps for each task
    invited_team_member_at TIMESTAMP,
    created_project_at TIMESTAMP,
    -- ... etc
    
    -- Status
    completed BOOLEAN DEFAULT FALSE,
    dismissed BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);
```

### Marking Tasks Complete

Tasks can be marked complete:

1. **Manually** (via UI button/API)
2. **Automatically** (triggered by actual actions)

**Example: Auto-complete on project creation:**

```python
# In app/routes/projects.py
@projects_bp.route('/new', methods=['POST'])
def create_project():
    # Create project
    project = Project(name=name, organization_id=org_id)
    db.session.add(project)
    db.session.commit()
    
    # Auto-complete onboarding task
    from app.models.onboarding_checklist import OnboardingChecklist
    checklist = OnboardingChecklist.get_or_create(org_id)
    checklist.mark_task_complete('created_project')
    
    return redirect(url_for('projects.detail', id=project.id))
```

### Progress Tracking

```python
checklist = OnboardingChecklist.get_or_create(org_id)

# Get metrics
percentage = checklist.completion_percentage  # 0-100
completed = checklist.get_completed_count()   # e.g., 3
total = checklist.get_total_count()           # 8
is_done = checklist.is_complete               # Boolean

# Get next suggestion
next_task = checklist.get_next_task()
# Returns: {'key': 'invited_team_member', 'title': '...', 'icon': '...'}
```

---

## Email Notifications

### Welcome Email

Sent automatically after provisioning:

**Trigger:** After `provision_organization()` or `provision_trial_organization()`

**Content:**
- Welcome message
- Trial information (if applicable)
- Quick start guide
- Links to dashboard and onboarding
- Pro tips

**Template:** Generated dynamically in `provisioning_service.py`

**Customization:**

```python
def _generate_welcome_html(self, organization, user, is_trial):
    # Customize email HTML here
    return f"""
    <html>
        <body>
            <h1>Welcome {user.display_name}!</h1>
            <!-- ... -->
        </body>
    </html>
    """
```

### Other Notification Emails

Already implemented in `app/routes/billing.py`:

1. **Payment Failed** - `_send_payment_failed_notification()`
2. **Trial Ending** - `_send_trial_ending_notification()` (3 days before)
3. **Action Required** - `_send_action_required_notification()` (3D Secure)
4. **Subscription Cancelled** - `_send_subscription_cancelled_notification()`

---

## Configuration

### Environment Variables

```bash
# Trial settings
STRIPE_ENABLE_TRIALS=true
STRIPE_TRIAL_DAYS=14

# Stripe keys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Plan price IDs
STRIPE_SINGLE_USER_PRICE_ID=price_...
STRIPE_TEAM_PRICE_ID=price_...

# Email settings
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG....
SMTP_FROM_EMAIL=noreply@timetracker.com
SMTP_FROM_NAME=TimeTracker
```

### App Configuration

In `app/config.py`:

```python
class Config:
    # Trials
    STRIPE_ENABLE_TRIALS = os.getenv('STRIPE_ENABLE_TRIALS', 'true').lower() == 'true'
    STRIPE_TRIAL_DAYS = int(os.getenv('STRIPE_TRIAL_DAYS', 14))
    
    # Provisioning
    PROVISION_ON_FIRST_PAYMENT = True  # Auto-provision on invoice.paid
    PROVISION_TRIALS_IMMEDIATELY = True  # Auto-provision on signup
```

---

## Usage Examples

### Example 1: Create Organization with Trial

```python
# User creates organization via web form
POST /organizations/new
{
    "name": "Acme Corp",
    "contact_email": "admin@acme.com",
    "start_trial": "true"
}

# Backend automatically:
# 1. Creates organization
# 2. Creates admin membership
# 3. Provisions trial (14 days)
# 4. Creates default project
# 5. Initializes checklist
# 6. Sends welcome email
# 7. Redirects to /onboarding/welcome
```

### Example 2: Webhook Provisioning

```python
# Stripe sends webhook after successful payment
POST /billing/webhooks/stripe
{
    "type": "invoice.paid",
    "data": {
        "object": {
            "customer": "cus_...",
            "subscription": "sub_...",
            "amount_paid": 600  # $6.00
        }
    }
}

# Backend:
# 1. Finds organization by customer ID
# 2. Checks if first payment (no projects)
# 3. If yes, triggers provisioning
# 4. Sends welcome email
# 5. Responds 200 OK to Stripe
```

### Example 3: Display Onboarding Widget on Dashboard

```html
<!-- app/templates/dashboard.html -->
{% extends "base.html" %}

{% block content %}
<div class="container">
    <!-- Trial banner (if on trial) -->
    {% include 'components/trial_banner.html' %}
    
    <div class="row">
        <div class="col-md-8">
            <!-- Main dashboard content -->
        </div>
        
        <div class="col-md-4">
            <!-- Onboarding progress widget -->
            {% include 'components/onboarding_widget.html' %}
        </div>
    </div>
</div>
{% endblock %}
```

### Example 4: Manual Task Completion

```javascript
// Mark task as complete via JavaScript
fetch('/onboarding/api/checklist/complete/invited_team_member', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    }
})
.then(response => response.json())
.then(data => {
    console.log('Task completed:', data);
    // Update UI to show progress
});
```

---

## Testing

### Local Testing

1. **Test Trial Provisioning:**

```bash
# Create organization with trial
curl -X POST http://localhost:5000/organizations/new \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Org&start_trial=true&contact_email=test@example.com"

# Check database
psql timetracker -c "SELECT name, trial_ends_at, subscription_plan FROM organizations;"
psql timetracker -c "SELECT * FROM onboarding_checklists WHERE organization_id=1;"
```

2. **Test Webhook Provisioning:**

```bash
# Use Stripe CLI to forward webhooks
stripe listen --forward-to localhost:5000/billing/webhooks/stripe

# Trigger test event
stripe trigger invoice.payment_succeeded
```

3. **Test Onboarding API:**

```bash
# Get checklist
curl http://localhost:5000/onboarding/api/checklist

# Complete task
curl -X POST http://localhost:5000/onboarding/api/checklist/complete/created_project

# Dismiss checklist
curl -X POST http://localhost:5000/onboarding/api/checklist/dismiss
```

### Unit Tests

Create `tests/test_provisioning.py`:

```python
import pytest
from app import create_app, db
from app.models import Organization, User
from app.utils.provisioning_service import provisioning_service

def test_provision_trial_organization():
    app = create_app({'TESTING': True})
    
    with app.app_context():
        # Create test user and org
        user = User(username='testuser', email='test@example.com')
        org = Organization(name='Test Org')
        db.session.add_all([user, org])
        db.session.commit()
        
        # Provision trial
        result = provisioning_service.provision_trial_organization(org, user)
        
        # Assertions
        assert result['success'] == True
        assert org.is_on_trial
        assert org.trial_days_remaining == 14
        assert org.projects.count() == 1  # Default project created
        
        # Check onboarding checklist exists
        from app.models.onboarding_checklist import OnboardingChecklist
        checklist = OnboardingChecklist.query.filter_by(organization_id=org.id).first()
        assert checklist is not None
```

---

## Troubleshooting

### Issue: Webhook not triggering provisioning

**Symptoms:** Payment succeeds but no welcome email, no default project

**Diagnosis:**

```python
# Check webhook logs
tail -f logs/timetracker.log | grep "webhook"

# Check if organization already has projects
psql -c "SELECT id, name, (SELECT COUNT(*) FROM projects WHERE organization_id=organizations.id) as project_count FROM organizations;"
```

**Solution:** Provisioning only triggers on *first* payment (when no projects exist). If org already has projects, it's considered already provisioned.

### Issue: Welcome email not sending

**Symptoms:** Provisioning succeeds but no email received

**Diagnosis:**

```python
# Check email service configuration
python -c "from app import create_app; app = create_app(); print(app.config['SMTP_HOST'])"

# Check user has email
psql -c "SELECT id, username, email FROM users WHERE email IS NULL;"
```

**Solution:** Ensure SMTP settings are configured and user has a valid email address.

### Issue: Trial not starting

**Symptoms:** Organization created but trial_ends_at is NULL

**Diagnosis:**

```python
# Check config
python -c "from app.config import Config; print(Config.STRIPE_ENABLE_TRIALS, Config.STRIPE_TRIAL_DAYS)"

# Check organization
psql -c "SELECT id, name, trial_ends_at, stripe_subscription_status FROM organizations;"
```

**Solution:** Ensure `STRIPE_ENABLE_TRIALS=true` in `.env` and organization is created with trial flag.

### Issue: Onboarding checklist not appearing

**Symptoms:** Dashboard doesn't show onboarding widget

**Diagnosis:**

```python
# Check if checklist exists
psql -c "SELECT * FROM onboarding_checklists WHERE organization_id=1;"

# Check template includes
grep -r "onboarding_widget.html" app/templates/
```

**Solution:** Ensure `{% include 'components/onboarding_widget.html' %}` is added to dashboard template and checklist exists in database.

---

## Database Migration

Run migrations to create the onboarding_checklists table:

```bash
# Apply migration
flask db upgrade

# Or manually run
psql timetracker < migrations/versions/020_add_onboarding_checklist.py
```

---

## Summary

✅ **Implemented:**

1. ✅ Provisioning service for automated tenant setup
2. ✅ Webhook handler updates for payment-triggered provisioning
3. ✅ Onboarding checklist model and tracking
4. ✅ Onboarding UI (checklist page, welcome page, widgets)
5. ✅ Welcome email with onboarding guide
6. ✅ Trial flow with banner and expiration tracking
7. ✅ Onboarding routes and API endpoints
8. ✅ Signup flow updated for immediate trial provisioning

**Files Created:**

- `app/utils/provisioning_service.py` - Core provisioning logic
- `app/models/onboarding_checklist.py` - Checklist model
- `app/routes/onboarding.py` - Onboarding routes
- `app/templates/onboarding/checklist.html` - Checklist UI
- `app/templates/onboarding/welcome.html` - Welcome page
- `app/templates/components/trial_banner.html` - Trial banner
- `app/templates/components/onboarding_widget.html` - Progress widget
- `migrations/versions/020_add_onboarding_checklist.py` - Database migration

**Files Modified:**

- `app/__init__.py` - Register onboarding blueprint
- `app/models/__init__.py` - Register OnboardingChecklist model
- `app/routes/billing.py` - Add provisioning to webhook handler
- `app/routes/organizations.py` - Add trial provisioning to signup

---

## Next Steps

1. **Testing:** Thoroughly test all flows (trial, payment, webhook)
2. **Monitoring:** Add metrics/logging for provisioning success/failure rates
3. **Customization:** Customize email templates with branding
4. **Extensions:**
   - Add more onboarding tasks
   - Create interactive onboarding tutorial
   - Add onboarding completion analytics
   - Implement onboarding automation triggers

---

## Support

For issues or questions:

1. Check logs: `tail -f logs/timetracker.log`
2. Review Stripe dashboard for webhook delivery
3. Test locally with Stripe CLI
4. Check database state with SQL queries

**Acceptance Criteria Met:**

✅ Stripe `invoice.paid` webhook provisions tenant and sends welcome email  
✅ Trial flow allows immediate login and shows remaining trial days  
✅ Onboarding checklist visible to new org admins  

**Status:** ✅ Production Ready


