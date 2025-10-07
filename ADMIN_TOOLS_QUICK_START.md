# Admin Tools & Internal Dashboard - Quick Start Guide

## 🚀 Getting Started

The Admin Tools & Internal Dashboard provides a comprehensive interface for managing customers, subscriptions, billing, and support operations.

---

## 🔑 Access

### Prerequisites
- Must be logged in as a user with **admin role** (`user.is_admin == True`)
- Stripe must be configured (for billing features)

### URL Access Points
- **Main Admin Dashboard**: `/admin`
- **Customer Management**: `/admin/customers`
- **Billing Reconciliation**: `/admin/billing/reconciliation`
- **Webhook Logs**: `/admin/webhooks`

---

## 📊 Main Features

### 1. Customer Management (`/admin/customers`)

View all organizations with key metrics at a glance.

**What you see:**
- Total organizations
- Active organizations  
- Total active users
- Paying customers
- Detailed table with subscription status, users, invoices, last activity

**Actions:**
- Click **"View"** on any organization to see detailed information

---

### 2. Customer Detail (`/admin/customers/<id>`)

Comprehensive view of a single customer/organization.

#### Organization Status Section
- View: Status, created date, active members, contact email
- **Actions:**
  - **Suspend Organization**: Temporarily disable access (with reason)
  - **Activate Organization**: Restore access

#### Subscription Section
- View: Plan, status, seats, next billing date
- **Actions:**
  - **Update Seats**: Change subscription quantity (syncs to Stripe)
  - **Cancel at Period End**: Schedule cancellation
  - **Cancel Immediately**: Instant cancellation
  - **Reactivate Subscription**: Undo scheduled cancellation

#### Members Section
- View all organization members
- See: User, email, role, status, last activity, join date

#### Invoices Section
- View recent invoices with amounts and status
- **Actions:**
  - **View invoice** (external link to Stripe)
  - **Create refund** (full or partial)

#### Events Section
- Timeline of all billing and subscription events
- See: Date, event type, status, notes

---

### 3. Billing Reconciliation (`/admin/billing/reconciliation`)

Monitor sync health between Stripe and your local database.

**What it checks:**
- Subscription status mismatches
- Quantity differences (seats)
- Missing subscriptions
- Billing cycle inconsistencies

**Summary Stats:**
- Total organizations with Stripe
- Successfully synced
- Organizations with discrepancies
- Sync errors

**Actions:**
- **View Details**: See specific discrepancies
- **Re-sync**: Manually trigger sync for an organization

**Note:** Discrepancies are automatically corrected when detected!

---

### 4. Webhook Logs (`/admin/webhooks`)

View and manage Stripe webhook events.

**Filters:**
- Event Type (e.g., `invoice.paid`, `subscription.updated`)
- Organization
- Processing Status (processed/pending)

**What you see:**
- Date and time
- Event type
- Organization
- Processing status
- Amount (if applicable)
- Notes
- Retry count

**Actions:**
- **View Detail**: See complete event information
- **Reprocess**: Retry failed webhook events

---

## 🛠️ Common Tasks

### How to Update Subscription Seats

```
1. Go to Admin → Customers
2. Click "View" on the organization
3. In the "Subscription" card, find the "Seats" input
4. Enter new quantity (must be ≥ 1)
5. Click "Update"
6. ✅ Confirmation shows: "Subscription updated: 5 → 10 seats"
7. Change is immediately reflected in Stripe
```

### How to Cancel a Subscription

```
Option 1: Cancel at Period End (Recommended)
1. Go to customer detail page
2. In "Subscription Management" section
3. Click "Cancel at Period End"
4. Confirm the action
5. ✅ User keeps access until billing cycle ends

Option 2: Cancel Immediately
1. Same steps but click "Cancel Immediately"
2. Confirm the PERMANENT action
3. ⚠️ User loses access instantly
```

### How to Create a Refund

```
1. Go to customer detail page
2. Scroll to "Recent Invoices"
3. Click the refund icon (undo) on the invoice
4. In the modal:
   - Amount: Leave empty for full refund, or enter partial amount
   - Reason: Select from dropdown
5. Click "Create Refund"
6. ✅ Refund created in Stripe
7. Appears in "Recent Refunds" section
```

### How to Suspend an Organization

```
1. Go to customer detail page
2. In "Organization Status" card
3. Click "Suspend Organization"
4. Optionally provide a reason
5. Confirm action
6. ✅ Organization status changes to "Suspended"
7. All members lose access
8. Event is logged with reason
```

### How to Check Billing Sync Health

```
1. Go to Admin → Billing Reconciliation
2. View summary stats at the top
3. Review organization-by-organization results
4. For orgs with discrepancies:
   - Click "View Details" to see what's wrong
   - Discrepancies are shown with local vs. Stripe values
5. Click "Re-sync" to manually check again
6. ✅ Discrepancies are automatically corrected
```

### How to Investigate a Failed Webhook

```
1. Go to Admin → Webhook Logs
2. Filter by "Status" → "Pending" or look for red error badges
3. Click the eye icon to view details
4. In webhook detail page:
   - Review error message
   - Check processing status
   - View raw payload for debugging
5. Click "Reprocess" to retry
6. Event is queued for reprocessing
```

---

## 🎯 Dashboard Navigation

### From Main Admin Dashboard (`/admin`)

The dashboard has 3 main sections:

#### 1. Customer Management (Left)
- **Manage Customers** → Customer list
- **Billing Sync** → Reconciliation view
- **Webhook Logs** → Event logs

#### 2. User Management (Center)
- **Manage Users** → User list
- **Create New User** → User creation form

#### 3. System Settings (Right)
- **Configure Settings** → System settings
- **Create Backup** → Database backup

---

## 🔐 Permissions & Rate Limits

### Access Control
All admin routes require:
- ✅ Authenticated user (`@login_required`)
- ✅ Admin role (`@admin_required`)

### Rate Limits
To prevent abuse, certain operations have rate limits:

| Operation | Limit |
|-----------|-------|
| Update subscription quantity | 10/minute |
| Cancel/reactivate subscription | 5/minute |
| Suspend/activate organization | 5/minute |
| Create refund | 3/minute |
| Manual sync | 10/minute |
| Reprocess webhook | 10/minute |

If you hit a rate limit, wait 1 minute and try again.

---

## 💡 Tips & Best Practices

### Subscription Management
- ✅ **DO** use "Cancel at Period End" for graceful cancellations
- ✅ **DO** communicate with customers before suspending
- ⚠️ **CAUTION** with "Cancel Immediately" - it's permanent
- ✅ **DO** check billing reconciliation regularly

### Refunds
- ✅ **DO** provide a reason for all refunds
- ✅ **DO** verify invoice amount before refunding
- ℹ️ Partial refunds are supported (enter amount)
- ℹ️ Leave amount empty for full refund

### Webhook Management
- ✅ **DO** investigate failed webhooks promptly
- ✅ **DO** reprocess failed events after fixing issues
- ℹ️ Events automatically retry up to 3 times
- ℹ️ Check raw payload for debugging

### Billing Reconciliation
- ✅ **DO** run reconciliation weekly
- ✅ **DO** investigate errors immediately
- ℹ️ Discrepancies are auto-corrected
- ℹ️ Use re-sync to force a check

---

## 🐛 Troubleshooting

### "Stripe is not configured" warning

**Problem:** Stripe service is not initialized.

**Solution:**
1. Check environment variables:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_WEBHOOK_SECRET`
2. Restart application
3. Verify in Settings that Stripe is configured

### "Organization does not have a Stripe customer" error

**Problem:** Organization not linked to Stripe.

**Solution:**
1. Organization must create a subscription first
2. Or manually create Stripe customer
3. Link via `organization.stripe_customer_id`

### Webhook shows "Pending" indefinitely

**Problem:** Webhook processing failed silently.

**Solution:**
1. View webhook detail
2. Check for processing errors
3. Review raw payload
4. Click "Reprocess"
5. Check server logs for errors

### Sync shows discrepancies but doesn't fix them

**Problem:** Auto-correction may have failed.

**Solution:**
1. Click "Re-sync" to try again
2. If still failing, check server logs
3. Verify Stripe API access
4. Check organization has valid Stripe IDs

### Can't create refund

**Problem:** Various causes.

**Common Solutions:**
1. Verify invoice is paid (can't refund unpaid)
2. Check refund amount ≤ invoice amount
3. Verify charge exists on invoice
4. Check Stripe API access
5. Review rate limits (3/minute)

---

## 📚 Additional Resources

- **Implementation Summary**: `ADMIN_TOOLS_IMPLEMENTATION_SUMMARY.md`
- **Stripe Documentation**: https://stripe.com/docs/api
- **Application Logs**: Check `/logs/timetracker.log`

---

## 🆘 Need Help?

### For Developers
1. Check server logs: `logs/timetracker.log`
2. Review implementation: `ADMIN_TOOLS_IMPLEMENTATION_SUMMARY.md`
3. Check Stripe dashboard for API errors
4. Review webhook signatures

### For Support Staff
1. Use webhook logs for debugging
2. Check billing reconciliation first
3. Verify organization status
4. Document issues for developers

---

## ✅ Quick Reference

| Task | URL | Action |
|------|-----|--------|
| View all customers | `/admin/customers` | Click "View" |
| Update seats | Customer detail | Enter quantity → Update |
| Cancel subscription | Customer detail | Cancel at Period End / Immediately |
| Create refund | Customer detail | Click refund icon on invoice |
| Suspend org | Customer detail | Click "Suspend Organization" |
| Check sync | `/admin/billing/reconciliation` | Review and re-sync |
| View webhooks | `/admin/webhooks` | Filter and investigate |
| Reprocess webhook | Webhook detail | Click "Reprocess" |

---

**Enjoy managing your customers efficiently! 🚀**

