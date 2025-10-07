# Migration Fix Summary

## Problem
You got an error about migration 018 not being found, even though:
- Migration 018 file exists in `migrations/versions/`
- The tables it creates (`organizations`, `memberships`) already exist in your database
- The issue is that migration 018 wasn't **stamped** in the `alembic_version` table

## What I Fixed

### 1. Created Fix Script
**File:** `fix_migration_chain.py`

This script will:
- Check if the organizations table exists
- Check your current migration version  
- Automatically stamp migration 018 if needed
- Tell you what to do next

### 2. Updated Migration 019
**File:** `migrations/versions/019_add_auth_features.py`

Added support for:
- All Stripe billing fields you added to Organization model
- New `subscription_events` table for tracking webhooks
- Proper upgrade and downgrade paths

### 3. Created SubscriptionEvent Model
**File:** `app/models/subscription_event.py`

New model for tracking Stripe webhook events with:
- Event ID and type tracking
- Processing status
- Retry logic for failed events
- Event data storage
- Cleanup utilities

### 4. Created Documentation
**File:** `MIGRATION_FIX.md`

Complete guide with multiple fix options if the script doesn't work.

## How to Fix (Choose One)

### Option 1: Use the Fix Script (Easiest)

```bash
# In your Docker container or local environment
python fix_migration_chain.py
```

Then run:
```bash
flask db upgrade
```

### Option 2: Manual Database Fix

If you have direct database access:

```sql
-- Check current version
SELECT version_num FROM alembic_version;

-- If it shows 017, update to 018
UPDATE alembic_version SET version_num = '018';
```

Then run:
```bash
flask db upgrade
```

### Option 3: Using Flask-Migrate

```bash
# Stamp the database with migration 018
flask db stamp 018

# Then upgrade to 019
flask db upgrade
```

## What Gets Created by Migration 019

Once the fix is applied and you run `flask db upgrade`, you'll get:

**New Tables:**
- `password_reset_tokens` - For password reset functionality
- `email_verification_tokens` - For email verification
- `refresh_tokens` - For JWT refresh tokens
- `subscription_events` - For tracking Stripe webhooks

**New Fields on `users` table:**
- `password_hash` - Encrypted password
- `email_verified` - Email verification status
- `totp_secret` - 2FA secret key
- `totp_enabled` - 2FA enabled flag
- `backup_codes` - 2FA backup codes

**New Fields on `organizations` table:**
- `stripe_customer_id` - Stripe customer ID
- `stripe_subscription_id` - Subscription ID
- `stripe_subscription_status` - Subscription status
- `stripe_price_id` - Current price ID
- `subscription_quantity` - Number of seats
- `trial_ends_at` - Trial end date
- `subscription_ends_at` - Subscription end date
- `next_billing_date` - Next billing date
- `billing_issue_detected_at` - Billing issue timestamp
- `last_billing_email_sent_at` - Last dunning email

## Verify Success

After running the migration, check that it worked:

```sql
-- Check migration version (should be 019)
SELECT version_num FROM alembic_version;

-- Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'password_reset_tokens', 
    'email_verification_tokens', 
    'refresh_tokens',
    'subscription_events'
)
ORDER BY table_name;

-- Should return all 4 tables
```

## If You're Still Having Issues

1. **Check the full error message** - Look for specific column or table conflicts
2. **Check if tables already exist** - Some columns might already be there
3. **Look at the logs** - Check `logs/timetracker.log` for details
4. **Try a clean migration** - If in development, you could drop and recreate
5. **Contact support** - Share the full error message

## Prevention for Next Time

To avoid this issue in the future:

1. **Always use migrations** - Don't use `db.create_all()` in production
2. **Keep alembic_version in sync** - If you manually create tables, stamp the database
3. **Test migrations** - Run on a test database first
4. **Use version control** - Track both migration files and database state

## Notes

- The fix script is safe to run multiple times
- It only updates if needed
- It doesn't modify any data, just the migration version
- All your existing data will be preserved

## Quick Commands Reference

```bash
# Check current migration
flask db current

# See migration history
flask db history

# Stamp to specific version
flask db stamp 018

# Upgrade to latest
flask db upgrade

# Downgrade one version
flask db downgrade -1

# Show pending migrations
flask db show
```

