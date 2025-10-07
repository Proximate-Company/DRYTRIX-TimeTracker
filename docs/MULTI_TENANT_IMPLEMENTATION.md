# Multi-Tenant Implementation Guide

## Overview

TimeTracker now supports **multi-tenancy**, allowing multiple organizations to use the same application instance while keeping their data completely isolated. This implementation uses a **shared database with Row Level Security (RLS)** approach for maximum efficiency and security.

## Architecture

### Data Model

The multi-tenant architecture consists of two core tables:

1. **Organizations** - Represents each tenant/customer organization
2. **Memberships** - Links users to organizations with roles

All data tables now include an `organization_id` foreign key that scopes data to a specific organization.

### Key Components

#### 1. Organization Model (`app/models/organization.py`)

```python
class Organization(db.Model):
    """Represents a tenant organization"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active')
    subscription_plan = db.Column(db.String(50), default='free')
    # ... more fields
```

#### 2. Membership Model (`app/models/membership.py`)

```python
class Membership(db.Model):
    """Links users to organizations with roles"""
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    role = db.Column(db.String(20))  # 'admin', 'member', 'viewer'
    status = db.Column(db.String(20))  # 'active', 'invited', 'suspended'
```

#### 3. Tenancy Middleware (`app/utils/tenancy.py`)

Provides helpers for managing organization context:

- `get_current_organization_id()` - Get current org from context
- `set_current_organization(org_id)` - Set org in context
- `scoped_query(Model)` - Create org-scoped queries
- `require_organization_access()` - Decorator to enforce access

#### 4. Row Level Security (`migrations/enable_row_level_security.sql`)

PostgreSQL RLS policies that enforce data isolation at the database level.

## Database Schema Changes

### New Tables

#### `organizations`
```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    contact_email VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    subscription_plan VARCHAR(50) DEFAULT 'free',
    max_users INTEGER,
    max_projects INTEGER,
    timezone VARCHAR(50) DEFAULT 'UTC',
    currency VARCHAR(3) DEFAULT 'EUR',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);
```

#### `memberships`
```sql
CREATE TABLE memberships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    role VARCHAR(20) DEFAULT 'member',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE (user_id, organization_id, status)
);
```

### Modified Tables

All core data tables now have:
- `organization_id` column (NOT NULL, FOREIGN KEY to organizations.id)
- Composite indexes on (`organization_id`, common_filter_column)
- Updated unique constraints to be per-organization

Tables updated:
- `projects`
- `clients`
- `time_entries`
- `tasks`
- `invoices`
- `comments`
- `focus_sessions`
- `saved_filters`
- `task_activity`

## Migration Guide

### Step 1: Run Database Migration

```bash
# Run the Alembic migration
flask db upgrade head

# Or manually run the migration
alembic upgrade 018
```

This migration will:
1. Create `organizations` and `memberships` tables
2. Create a default organization named "Default Organization"
3. Add `organization_id` to all existing tables
4. Migrate all existing data to the default organization
5. Create memberships for all existing users

### Step 2: Enable Row Level Security (PostgreSQL only)

For PostgreSQL databases, optionally enable RLS for additional security:

```bash
psql -U timetracker -d timetracker -f migrations/enable_row_level_security.sql
```

This creates:
- RLS policies on all tenant-scoped tables
- Helper functions for context management
- Verification queries

### Step 3: Update Application Code

The tenancy middleware is automatically enabled. For existing routes that create/modify data, ensure they use the current organization context:

```python
from app.utils.tenancy import get_current_organization_id

@app.route('/projects/new', methods=['POST'])
@login_required
def create_project():
    org_id = get_current_organization_id()
    
    project = Project(
        name=request.form['name'],
        organization_id=org_id,  # Always set organization_id
        client_id=request.form['client_id']
    )
    
    db.session.add(project)
    db.session.commit()
```

## Usage Examples

### Creating an Organization

```python
from app.models import Organization
from app import db

org = Organization(
    name="Acme Corp",
    slug="acme-corp",  # Auto-generated if not provided
    contact_email="admin@acme.com",
    subscription_plan="professional"
)

db.session.add(org)
db.session.commit()
```

### Adding Users to Organizations

```python
from app.models import Membership

# Add user as admin
membership = Membership(
    user_id=user.id,
    organization_id=org.id,
    role='admin',
    status='active'
)

db.session.add(membership)
db.session.commit()
```

### Inviting Users

```python
# Create pending membership with invitation token
membership = Membership(
    user_id=new_user.id,
    organization_id=org.id,
    role='member',
    status='invited',
    invited_by=current_user.id
)

db.session.add(membership)
db.session.commit()

# Send invitation email with token
invitation_url = url_for('auth.accept_invitation', 
                        token=membership.invitation_token)
```

### Scoped Queries

```python
from app.utils.tenancy import scoped_query

# Get projects for current organization only
projects = scoped_query(Project).filter_by(status='active').all()

# Get time entries for current organization
entries = scoped_query(TimeEntry).filter(
    TimeEntry.start_time >= start_date
).all()
```

### Switching Organizations

```python
from app.utils.tenancy import switch_organization

# Switch to a different organization (if user has access)
try:
    org = switch_organization(new_org_id)
    # Now all queries will be scoped to new_org_id
except PermissionError:
    flash("You don't have access to that organization")
```

### Protecting Routes

```python
from app.utils.tenancy import require_organization_access

@app.route('/admin/settings')
@login_required
@require_organization_access(admin_only=True)
def organization_settings():
    """Only accessible to organization admins"""
    org = get_current_organization()
    return render_template('admin/org_settings.html', org=org)
```

## Row Level Security (RLS)

### How It Works

RLS provides defense-in-depth by enforcing tenant isolation at the PostgreSQL level:

```sql
-- Example policy on projects table
CREATE POLICY projects_tenant_isolation ON projects
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );
```

### Setting Context

The application automatically sets the RLS context for each request:

```python
# In app/__init__.py before_request handler
from app.utils.rls import init_rls_for_request

@app.before_request
def setup_request():
    init_rls_for_request()  # Sets PostgreSQL session variables
```

### Testing RLS

```python
from app.utils.rls import test_rls_isolation

# Test that org1 data is isolated from org2
results = test_rls_isolation(org1.id, org2.id)

if results['success']:
    print("✅ RLS is working correctly!")
else:
    print("❌ RLS isolation failed!")
    print(results)
```

## API Endpoints

### Organization Management

#### List Organizations
```http
GET /api/organizations
Authorization: Bearer <token>

Response:
{
  "organizations": [
    {
      "id": 1,
      "name": "Acme Corp",
      "slug": "acme-corp",
      "member_count": 5,
      "subscription_plan": "professional"
    }
  ]
}
```

#### Create Organization
```http
POST /api/organizations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Corp",
  "contact_email": "admin@newcorp.com",
  "subscription_plan": "starter"
}
```

#### Switch Organization
```http
POST /api/organizations/:id/switch
Authorization: Bearer <token>

Response:
{
  "success": true,
  "organization": {
    "id": 1,
    "name": "Acme Corp"
  }
}
```

### Membership Management

#### List Members
```http
GET /api/organizations/:id/members
Authorization: Bearer <token>

Response:
{
  "members": [
    {
      "user_id": 1,
      "username": "john",
      "role": "admin",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Invite User
```http
POST /api/organizations/:id/members/invite
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "role": "member"
}
```

## Testing

### Running Tests

```bash
# Run all multi-tenant tests
pytest tests/test_multi_tenant.py -v

# Run specific test class
pytest tests/test_multi_tenant.py::TestTenantDataIsolation -v

# Run with coverage
pytest tests/test_multi_tenant.py --cov=app --cov-report=html
```

### Manual Testing

```bash
# Start Python shell in app context
flask shell

# Create test organizations
from app.models import Organization
org1 = Organization(name="Test Org 1")
org2 = Organization(name="Test Org 2")
db.session.add_all([org1, org2])
db.session.commit()

# Test scoped queries
from app.utils.tenancy import set_current_organization, scoped_query
from app.models import Project

set_current_organization(org1.id, org1)
projects = scoped_query(Project).all()
print(f"Org 1 has {len(projects)} projects")
```

## Security Considerations

### 1. Application-Level Security
- ✅ Tenancy middleware enforces organization scoping on all requests
- ✅ Scoped queries automatically filter by organization_id
- ✅ Access decorators prevent cross-organization access

### 2. Database-Level Security
- ✅ Row Level Security (RLS) policies enforce isolation in PostgreSQL
- ✅ Foreign key constraints ensure referential integrity
- ✅ Unique constraints are scoped per-organization

### 3. Best Practices
- Always use `scoped_query()` instead of raw queries
- Never bypass `organization_id` filters
- Use `require_organization_access()` decorator on sensitive routes
- Enable RLS in production for defense-in-depth
- Regular audit logs for cross-organization access attempts

## Troubleshooting

### Problem: Users can see data from other organizations

**Check:**
1. Is tenancy middleware enabled? (`init_tenancy_for_request` called?)
2. Are you using `scoped_query()` or raw queries?
3. Is `organization_id` set on new records?
4. Is RLS enabled and working? (PostgreSQL only)

**Debug:**
```python
from app.utils.tenancy import get_current_organization_id
print(f"Current org: {get_current_organization_id()}")

from app.utils.rls import verify_rls_is_active
print(verify_rls_is_active())
```

### Problem: Migration fails

**Common issues:**
- Existing data without organization
- Unique constraint violations
- Foreign key constraint violations

**Solution:**
Check migration logs and manually fix data if needed:
```sql
-- Find records without organization_id
SELECT * FROM projects WHERE organization_id IS NULL;

-- Fix manually
UPDATE projects SET organization_id = 1 WHERE organization_id IS NULL;
```

### Problem: RLS is too restrictive

If RLS blocks legitimate access:
1. Check that `set_organization_context()` is being called
2. Verify user has active membership
3. For admin tasks, use `is_super_admin=True`

```python
from app.utils.rls import set_rls_context

# Allow super admin access for migrations/admin tasks
set_rls_context(None, is_super_admin=True)
```

## Performance Optimization

### Indexes

The migration creates these composite indexes:
- `(organization_id, status)` on most tables
- `(organization_id, user_id)` on user-scoped tables
- `(organization_id, start_time)` on time-based tables

### Query Patterns

```python
# ✅ Good - Uses composite index
projects = Project.query.filter_by(
    organization_id=org_id,
    status='active'
).all()

# ❌ Bad - Doesn't use index efficiently
projects = Project.query.filter_by(status='active').filter_by(
    organization_id=org_id
).all()
```

### Connection Pooling

With RLS, ensure connection pool is configured properly:

```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 300,  # Recycle connections every 5 minutes
}
```

## Future Enhancements

### Planned Features
- [ ] Organization-level settings inheritance
- [ ] Billing and subscription management
- [ ] Organization transfer (change ownership)
- [ ] Bulk user import/export
- [ ] Organization templates
- [ ] Usage analytics per organization
- [ ] Schema-per-tenant option for extreme isolation

### Migration Path to Schema-per-Tenant

If stronger isolation is needed:

1. Export organization data
2. Create dedicated schema per organization
3. Update connection string to use schema
4. Migrate data to new schema

```python
# Example schema-per-tenant approach
def get_schema_for_org(org_id):
    return f"org_{org_id}"

# Set schema for queries
db.session.execute(f"SET search_path TO {schema_name}")
```

## Support

For issues or questions:
- Check logs: `logs/timetracker.log`
- Run tests: `pytest tests/test_multi_tenant.py -v`
- Enable debug logging: Set `LOG_LEVEL=DEBUG`

## Changelog

### Version 2.0.0 (2025-10-07)
- ✅ Initial multi-tenant implementation
- ✅ Organizations and memberships models
- ✅ Tenancy middleware
- ✅ Row Level Security policies
- ✅ Database migration (018)
- ✅ Comprehensive test suite
- ✅ API endpoints for org management

