# Stripe Billing - Quick Start Guide

Get Stripe billing up and running in 15 minutes!

## Prerequisites
- Stripe account (sign up at https://stripe.com)
- PostgreSQL database running
- SMTP configured for emails

## Step 1: Install Dependencies (1 min)

```bash
pip install stripe==7.9.0
```

## Step 2: Run Database Migration (1 min)

```bash
psql -U timetracker -d timetracker -f migrations/add_stripe_billing_fields.sql
```

## Step 3: Create Stripe Products (3 min)

1. Go to https://dashboard.stripe.com/products
2. Click "Add product"

**Product 1: Single User**
- Name: `TimeTracker Single User`
- Price: `€5.00`
- Billing: `Monthly`
- Currency: `EUR`
- Click "Save product"
- **Copy the Price ID** (starts with `price_`)

**Product 2: Team**
- Name: `TimeTracker Team`  
- Price: `€6.00`
- Billing: `Monthly`
- Currency: `EUR`
- Click "Save product"
- **Copy the Price ID** (starts with `price_`)

## Step 4: Get API Keys (1 min)

1. Go to https://dashboard.stripe.com/apikeys
2. Copy **Publishable key** (starts with `pk_test_`)
3. Copy **Secret key** (starts with `sk_test_`)

## Step 5: Configure Environment (2 min)

Add to your `.env` file:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE  # We'll get this in Step 7

# Stripe Price IDs
STRIPE_SINGLE_USER_PRICE_ID=price_YOUR_SINGLE_USER_PRICE_ID
STRIPE_TEAM_PRICE_ID=price_YOUR_TEAM_PRICE_ID

# Optional Settings
STRIPE_ENABLE_TRIALS=true
STRIPE_TRIAL_DAYS=14
STRIPE_ENABLE_PRORATION=true
```

## Step 6: Enable Customer Portal (2 min)

1. Go to https://dashboard.stripe.com/settings/billing/portal
2. Click "Activate test link"
3. Enable these features:
   - ✅ Update subscription
   - ✅ Cancel subscription  
   - ✅ Update payment method
   - ✅ View invoice history
4. Click "Save"

## Step 7: Configure Webhooks - DEVELOPMENT (2 min)

**For local development with Stripe CLI:**

```bash
# Install Stripe CLI (if not installed)
brew install stripe/stripe-cli/stripe  # macOS
scoop install stripe                   # Windows

# Login
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:5000/billing/webhooks/stripe
```

Copy the webhook signing secret (starts with `whsec_`) and add to `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_FROM_CLI
```

**For production deployment, see Step 9**

## Step 8: Restart Application (1 min)

```bash
# Restart your Flask application
flask run
# or
gunicorn app:app
```

## Step 9: Test Subscription Flow (2 min)

1. Navigate to `http://localhost:5000/billing`
2. Click "Subscribe" on either plan
3. Use test card: `4242 4242 4242 4242`
4. Expiry: Any future date (e.g., `12/34`)
5. CVC: Any 3 digits (e.g., `123`)
6. Complete checkout

✅ You should see:
- Subscription activated
- Organization status updated
- Welcome email sent (if SMTP configured)

## Step 10: Test Webhooks (1 min)

In a separate terminal:

```bash
# Trigger test events
stripe trigger invoice.paid
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.updated
```

Check your application logs - you should see:
```
Received Stripe webhook: invoice.paid
Invoice paid for organization...
```

---

## 🎉 Done!

Your Stripe billing integration is now live!

### What You Can Do Now:

✅ **Subscribe to plans** at `/billing`  
✅ **Manage subscriptions** via Customer Portal  
✅ **Add/remove team members** (seats auto-sync)  
✅ **View invoices** in billing dashboard  
✅ **Test payment failures** with test card `4000 0000 0000 0002`

### Next Steps:

1. **Configure Stripe Tax** for EU VAT:
   - Go to https://dashboard.stripe.com/settings/tax
   - Enable automatic tax calculation

2. **Set up production webhooks** when deploying:
   - Go to https://dashboard.stripe.com/webhooks
   - Add endpoint: `https://your-domain.com/billing/webhooks/stripe`
   - Select all required events (see full guide)
   - Copy signing secret to production `.env`

3. **Switch to live mode** for production:
   - Get live API keys from https://dashboard.stripe.com/apikeys
   - Create live products
   - Update `.env` with live keys

---

## 🆘 Troubleshooting

**Webhooks not working?**
- Make sure Stripe CLI is running: `stripe listen --forward-to localhost:5000/billing/webhooks/stripe`
- Check webhook secret matches in `.env`
- Check application logs for errors

**Can't see billing dashboard?**
- Make sure you're logged in
- Check you have admin access to organization
- Verify database migration ran successfully

**Payment not processing?**
- Verify API keys are correct
- Check Stripe Dashboard logs
- Try a different test card

---

## 📚 Full Documentation

For detailed information, see:
- **Setup Guide**: `STRIPE_BILLING_SETUP.md`
- **Implementation Summary**: `STRIPE_IMPLEMENTATION_SUMMARY.md`
- **Environment Template**: `env.stripe.example`

---

## 🧪 Test Cards

```
Success:      4242 4242 4242 4242
Decline:      4000 0000 0000 0002
3D Secure:    4000 0025 0000 3155
```

More test cards: https://stripe.com/docs/testing

---

**Total Setup Time: ~15 minutes**  
**Ready for testing!** 🚀

