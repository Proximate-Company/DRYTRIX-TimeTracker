# Migration Chain Fix

## Problem
Migration 019 references migration 018, but migration 018 isn't registered in your database's `alembic_version` table, even though the tables it creates already exist.

## Quick Fix

### Option 1: Run the Fix Script (Recommended)

```bash
python fix_migration_chain.py
```

This script will:
1. Check if the organizations table exists
2. Check your current migration version
3. Stamp the database with migration 018 if needed
4. Tell you what to do next

After running this, execute:
```bash
flask db upgrade
```

### Option 2: Manual Fix (If you have database access)

**Step 1:** Check current migration version:
```sql
SELECT version_num FROM alembic_version;
```

**Step 2:** If it shows `017`, update it to `018`:
```sql
UPDATE alembic_version SET version_num = '018';
```

**Step 3:** Run the upgrade:
```bash
flask db upgrade
```

### Option 3: Alternative - Modify Migration 019

If the above doesn't work, modify `migrations/versions/019_add_auth_features.py`:

Change line 15 from:
```python
down_revision = '018_add_multi_tenant_support'
```

To:
```python
down_revision = '017'  # Skip 018 if already applied
```

But **ONLY** do this if:
- The organizations table already exists in your database
- Migration 018 was somehow applied but not recorded

## What Happened?

The `organizations` and `memberships` tables were created (by migration 018), but the migration wasn't properly recorded in the `alembic_version` table. This can happen if:

1. Tables were created manually
2. Migration was partially applied
3. Database was initialized with `db.create_all()` instead of migrations

## After Fixing

Once fixed, you should be able to run:
```bash
flask db upgrade
```

This will apply migration 019 which adds:
- Password authentication fields
- 2FA fields  
- Email verification tokens
- Password reset tokens
- JWT refresh tokens
- Stripe billing fields

## Verify Success

After running the upgrade, check that these tables exist:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('password_reset_tokens', 'email_verification_tokens', 'refresh_tokens')
ORDER BY table_name;
```

You should see all three new tables.

## Still Having Issues?

If you're still getting errors:

1. **Check if tables exist:**
   ```sql
   \dt  -- PostgreSQL
   ```

2. **Check migration history:**
   ```bash
   flask db history
   ```

3. **Check current version:**
   ```bash
   flask db current
   ```

4. **Force stamp to 018 (last resort):**
   ```bash
   flask db stamp 018
   ```
   
   Then run:
   ```bash
   flask db upgrade
   ```

## Prevention

To avoid this in the future:
- Always use `flask db upgrade` instead of `db.create_all()`
- Don't manually create tables that migrations will create
- Keep migration history in sync with actual database state

