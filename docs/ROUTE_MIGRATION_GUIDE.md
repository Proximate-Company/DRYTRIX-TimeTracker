# Route Migration Guide for Multi-Tenancy

This guide explains how to update existing routes and queries to work with the new multi-tenant architecture.

## Overview

With multi-tenancy enabled, all data queries must be scoped to the current organization. This guide provides patterns for updating your existing routes.

## Quick Migration Checklist

For each route that handles organization-scoped data:

- [ ] Add `organization_id` when creating new records
- [ ] Use `scoped_query()` instead of `Model.query`
- [ ] Add `@require_organization_access()` decorator where appropriate
- [ ] Update form submissions to include organization context
- [ ] Update API endpoints to return organization-scoped data

## Common Patterns

### Pattern 1: Creating New Records

**Before:**
```python
@projects_bp.route('/new', methods=['POST'])
@login_required
def create_project():
    project = Project(
        name=request.form['name'],
        client_id=request.form['client_id']
    )
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('projects.index'))
```

**After:**
```python
from app.utils.tenancy import get_current_organization_id, require_organization_access

@projects_bp.route('/new', methods=['POST'])
@login_required
@require_organization_access()  # Ensure user has org access
def create_project():
    org_id = get_current_organization_id()
    
    project = Project(
        name=request.form['name'],
        organization_id=org_id,  # ✅ Add organization_id
        client_id=request.form['client_id']
    )
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('projects.index'))
```

### Pattern 2: Listing Records

**Before:**
```python
@projects_bp.route('/')
@login_required
def index():
    projects = Project.query.filter_by(status='active').all()
    return render_template('projects/index.html', projects=projects)
```

**After:**
```python
from app.utils.tenancy import scoped_query, require_organization_access

@projects_bp.route('/')
@login_required
@require_organization_access()
def index():
    # Use scoped_query to automatically filter by organization
    projects = scoped_query(Project).filter_by(status='active').all()
    return render_template('projects/index.html', projects=projects)
```

### Pattern 3: Viewing a Specific Record

**Before:**
```python
@projects_bp.route('/<int:project_id>')
@login_required
def detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('projects/detail.html', project=project)
```

**After:**
```python
from app.utils.tenancy import scoped_query, ensure_organization_access, require_organization_access

@projects_bp.route('/<int:project_id>')
@login_required
@require_organization_access()
def detail(project_id):
    # Option 1: Use scoped_query with get
    project = scoped_query(Project).filter_by(id=project_id).first_or_404()
    
    # Option 2: Get normally then verify access
    # project = Project.query.get_or_404(project_id)
    # ensure_organization_access(project)  # Raises PermissionError if wrong org
    
    return render_template('projects/detail.html', project=project)
```

### Pattern 4: Updating Records

**Before:**
```python
@projects_bp.route('/<int:project_id>/edit', methods=['POST'])
@login_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)
    project.name = request.form['name']
    db.session.commit()
    return redirect(url_for('projects.detail', project_id=project_id))
```

**After:**
```python
from app.utils.tenancy import scoped_query, require_organization_access

@projects_bp.route('/<int:project_id>/edit', methods=['POST'])
@login_required
@require_organization_access()
def edit(project_id):
    # Scoped query ensures we can only edit projects in our org
    project = scoped_query(Project).filter_by(id=project_id).first_or_404()
    
    project.name = request.form['name']
    # organization_id stays the same, no need to update
    
    db.session.commit()
    return redirect(url_for('projects.detail', project_id=project_id))
```

### Pattern 5: Deleting Records

**Before:**
```python
@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('projects.index'))
```

**After:**
```python
from app.utils.tenancy import scoped_query, require_organization_access

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@require_organization_access(admin_only=True)  # Only org admins can delete
def delete(project_id):
    # Scoped query ensures we can only delete from our org
    project = scoped_query(Project).filter_by(id=project_id).first_or_404()
    
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('projects.index'))
```

### Pattern 6: Complex Queries with Joins

**Before:**
```python
@reports_bp.route('/project-summary')
@login_required
def project_summary():
    results = db.session.query(
        Project.name,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(TimeEntry).group_by(Project.id).all()
    
    return render_template('reports/summary.html', results=results)
```

**After:**
```python
from app.utils.tenancy import get_current_organization_id, require_organization_access

@reports_bp.route('/project-summary')
@login_required
@require_organization_access()
def project_summary():
    org_id = get_current_organization_id()
    
    results = db.session.query(
        Project.name,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(TimeEntry).filter(
        Project.organization_id == org_id,  # ✅ Filter by org
        TimeEntry.organization_id == org_id  # ✅ Filter join too
    ).group_by(Project.id).all()
    
    return render_template('reports/summary.html', results=results)
```

### Pattern 7: API Endpoints

**Before:**
```python
@api_bp.route('/projects', methods=['GET'])
@login_required
def api_projects():
    projects = Project.query.all()
    return jsonify({
        'projects': [p.to_dict() for p in projects]
    })
```

**After:**
```python
from app.utils.tenancy import scoped_query, require_organization_access

@api_bp.route('/projects', methods=['GET'])
@login_required
@require_organization_access()
def api_projects():
    projects = scoped_query(Project).all()
    return jsonify({
        'projects': [p.to_dict() for p in projects]
    })
```

### Pattern 8: Background Tasks

**Before:**
```python
def send_weekly_report():
    users = User.query.filter_by(is_active=True).all()
    for user in users:
        entries = TimeEntry.query.filter_by(user_id=user.id).all()
        # Send report...
```

**After:**
```python
from app.utils.tenancy import set_current_organization
from app.utils.rls import with_rls_context

def send_weekly_report():
    # Get all organizations
    orgs = Organization.query.filter_by(status='active').all()
    
    for org in orgs:
        # Set org context for each organization
        set_current_organization(org.id, org)
        
        # Now all queries are scoped to this org
        memberships = Membership.query.filter_by(
            organization_id=org.id,
            status='active'
        ).all()
        
        for membership in memberships:
            entries = scoped_query(TimeEntry).filter_by(
                user_id=membership.user_id
            ).all()
            # Send report...

# Or use decorator for simpler code:
@with_rls_context(organization_id=1)  # Set org context
def process_org_data():
    # All queries here are automatically scoped to org 1
    projects = scoped_query(Project).all()
```

## Migration Strategy

### Phase 1: Audit Routes (Day 1)

1. List all routes that handle data operations
2. Identify which models are affected
3. Prioritize critical routes first

```bash
# Find all route files
find app/routes -name "*.py" -type f

# Search for model queries
grep -r "Model.query" app/routes/
grep -r "db.session.query" app/routes/
```

### Phase 2: Update Models (Day 1-2)

Already completed! All models now have `organization_id`.

### Phase 3: Update Routes (Day 2-5)

Update routes in this order:
1. **Authentication routes** - Add org selection after login
2. **Project routes** - Core functionality
3. **Time entry routes** - Core functionality
4. **Client routes** - Related to projects
5. **Task routes** - Related to projects
6. **Invoice routes** - Related to projects/clients
7. **Report routes** - Cross-cutting queries
8. **Admin routes** - System-wide operations

### Phase 4: Testing (Day 5-7)

1. Run test suite: `pytest tests/test_multi_tenant.py -v`
2. Manual testing with multiple organizations
3. Verify data isolation
4. Check RLS policies

### Phase 5: Deployment (Day 7)

1. Backup database
2. Run migrations
3. Enable RLS (if using PostgreSQL)
4. Monitor logs for errors
5. Verify tenant isolation in production

## Example: Complete Route File Migration

### Before: `app/routes/projects.py`

```python
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app import db
from app.models import Project

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/')
@login_required
def index():
    projects = Project.query.all()
    return render_template('projects/index.html', projects=projects)

@projects_bp.route('/new', methods=['POST'])
@login_required
def create():
    project = Project(name=request.form['name'], client_id=request.form['client_id'])
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('projects.index'))
```

### After: `app/routes/projects.py`

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Project, Client
from app.utils.tenancy import (
    get_current_organization_id,
    scoped_query,
    require_organization_access
)

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/')
@login_required
@require_organization_access()
def index():
    # ✅ Use scoped_query for automatic org filtering
    projects = scoped_query(Project).all()
    return render_template('projects/index.html', projects=projects)

@projects_bp.route('/new', methods=['POST'])
@login_required
@require_organization_access()
def create():
    org_id = get_current_organization_id()
    
    # ✅ Verify client belongs to same org
    client = scoped_query(Client).filter_by(
        id=request.form['client_id']
    ).first_or_404()
    
    # ✅ Include organization_id
    project = Project(
        name=request.form['name'],
        organization_id=org_id,
        client_id=client.id
    )
    
    db.session.add(project)
    db.session.commit()
    
    flash('Project created successfully!', 'success')
    return redirect(url_for('projects.index'))
```

## Common Pitfalls

### ❌ Pitfall 1: Forgetting organization_id

```python
# BAD - Missing organization_id
project = Project(name='Test', client_id=1)
db.session.add(project)
db.session.commit()  # Will fail - organization_id is required
```

### ✅ Solution

```python
# GOOD - Include organization_id
org_id = get_current_organization_id()
project = Project(name='Test', organization_id=org_id, client_id=1)
```

### ❌ Pitfall 2: Using unscoped queries

```python
# BAD - Shows all projects from all orgs
projects = Project.query.all()
```

### ✅ Solution

```python
# GOOD - Only shows current org's projects
projects = scoped_query(Project).all()
```

### ❌ Pitfall 3: Cross-org references

```python
# BAD - Client might be from different org
org_id = get_current_organization_id()
project = Project(
    name='Test',
    organization_id=org_id,
    client_id=request.form['client_id']  # Not verified!
)
```

### ✅ Solution

```python
# GOOD - Verify client is in same org
org_id = get_current_organization_id()
client = scoped_query(Client).filter_by(
    id=request.form['client_id']
).first_or_404()  # Will 404 if wrong org

project = Project(
    name='Test',
    organization_id=org_id,
    client_id=client.id
)
```

## Testing Your Changes

### Unit Test Example

```python
def test_project_isolation(app, organizations, users):
    with app.app_context():
        org1, org2 = organizations
        
        # Create projects in each org
        set_current_organization(org1.id, org1)
        project1 = Project(name='Org1 Project', organization_id=org1.id, client_id=...)
        db.session.add(project1)
        
        set_current_organization(org2.id, org2)
        project2 = Project(name='Org2 Project', organization_id=org2.id, client_id=...)
        db.session.add(project2)
        db.session.commit()
        
        # Verify isolation
        set_current_organization(org1.id, org1)
        org1_projects = scoped_query(Project).all()
        assert len(org1_projects) == 1
        assert org1_projects[0].id == project1.id
```

### Manual Testing Checklist

- [ ] Create test organizations
- [ ] Create test users with different org memberships
- [ ] Login as each user and verify:
  - [ ] Can only see their org's data
  - [ ] Cannot access other org's data by URL manipulation
  - [ ] Can create new records in their org
  - [ ] Cannot edit other org's records
  - [ ] Can switch between orgs (if multi-org user)

## Monitoring and Debugging

### Enable Debug Logging

```python
# config.py
LOG_LEVEL = 'DEBUG'
```

### Check Current Organization

```python
from app.utils.tenancy import get_current_organization_id

# In any route
org_id = get_current_organization_id()
print(f"Current org: {org_id}")
```

### Verify RLS is Active

```python
from app.utils.rls import verify_rls_is_active

# In Flask shell
status = verify_rls_is_active()
print(status)
```

### Monitor Query Performance

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%organization_id%'
ORDER BY total_time DESC
LIMIT 10;
```

## Need Help?

- Check logs: `logs/timetracker.log`
- Run tests: `pytest tests/test_multi_tenant.py -v`
- Review documentation: `docs/MULTI_TENANT_IMPLEMENTATION.md`
- Search for existing patterns in `app/routes/organizations.py`

## Summary

✅ **Always**:
- Use `scoped_query()` for queries
- Include `organization_id` when creating records
- Add `@require_organization_access()` decorator
- Verify cross-model references are in same org

❌ **Never**:
- Use `Model.query` directly for org-scoped data
- Forget to add `organization_id` to new records
- Trust user input for cross-org references
- Bypass org checks for "convenience"

The multi-tenant architecture ensures data isolation and security, but it requires discipline in following these patterns throughout your codebase.

