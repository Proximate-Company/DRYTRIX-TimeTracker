# Fix Migration Issue - Step by Step

## The Problem

Migration 019 references migration 018, but migration 018 isn't in your database's `alembic_version` table, even though the tables it creates (organizations, memberships) already exist.

## Quick Fix (Choose One)

### Option 1: Run from Docker Container (Recommended)

```bash
# Enter your running Docker container
docker-compose exec app bash

# Once inside the container, run:
python fix_migration_chain.py

# Then upgrade
flask db upgrade

# Exit container
exit
```

### Option 2: Manual SQL Fix (If Python script doesn't work)

```bash
# Enter your Docker container
docker-compose exec app bash

# Connect to PostgreSQL
psql -U timetracker -d timetracker

# Check current version
SELECT version_num FROM alembic_version;

# If it shows 017 or anything other than 018, update it:
UPDATE alembic_version SET version_num = '018';

# Verify
SELECT version_num FROM alembic_version;
# Should now show: 018

# Exit psql
\q

# Now run the upgrade
flask db upgrade

# Exit container
exit
```

### Option 3: Use Flask-Migrate Stamp

```bash
# Enter container
docker-compose exec app bash

# Stamp the database with migration 018
flask db stamp 018

# Then upgrade to 019
flask db upgrade

# Exit
exit
```

## Verification

After running one of the above, verify success:

```bash
# Check migration version
docker-compose exec app flask db current
# Should show: 019_add_auth_features (head)

# Check that new tables exist
docker-compose exec app psql -U timetracker -d timetracker -c "\dt" | grep -E "(password_reset|email_verification|refresh_tokens|subscription_events)"
```

You should see:
- `password_reset_tokens`
- `email_verification_tokens`
- `refresh_tokens`
- `subscription_events`

## If Still Having Issues

If the above doesn't work, the issue might be that migration 018 file has a different revision ID than expected. Let's check:

```bash
# Check what's in migration 018 file
docker-compose exec app head -20 /app/migrations/versions/018_add_multi_tenant_support.py
```

Look for the line that says `revision = '...'`. It should be `'018'`.

If it's something else (like `'018_add_multi_tenant_support'`), then update it:

```bash
# Inside container
cd /app/migrations/versions

# Edit the file (if vi is available)
vi 018_add_multi_tenant_support.py

# Change:
# revision = '018_add_multi_tenant_support'
# To:
# revision = '018'
```

Then run `flask db upgrade` again.

## Complete Commands (Copy-Paste)

Here's the complete set of commands to run:

```bash
# Stop the container if running
docker-compose down

# Start it again
docker-compose up -d

# Enter the container
docker-compose exec app bash

# Inside container - try the stamp method first
flask db stamp 018

# Then upgrade
flask db upgrade

# Check it worked
flask db current

# Exit
exit

# View logs to confirm app started
docker-compose logs -f app
```

## What This Does

1. **Stamps migration 018**: Tells Alembic that migration 018 is already applied (which it is - the tables exist)
2. **Upgrades to 019**: Applies the auth features migration
3. **Creates new tables**: Adds password_reset_tokens, email_verification_tokens, refresh_tokens, subscription_events
4. **Adds new columns**: Updates users and organizations tables with auth and billing fields

## After Migration Success

Once migrations are complete, your app will have:
- ✅ Password authentication
- ✅ JWT tokens
- ✅ 2FA support
- ✅ Email verification
- ✅ Password reset
- ✅ Stripe billing fields
- ✅ Subscription event tracking

Restart your app:
```bash
docker-compose restart app
```

## Still Stuck?

If you're still getting errors, share the output of:

```bash
docker-compose exec app flask db current
docker-compose exec app psql -U timetracker -d timetracker -c "SELECT version_num FROM alembic_version;"
docker-compose exec app psql -U timetracker -d timetracker -c "\dt" | head -20
```

This will help me see exactly what state your database is in.

