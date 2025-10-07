# Route Update Plan for Multi-Tenant Implementation

## Overview

This document provides a prioritized plan for updating existing routes to work with the multi-tenant architecture. The updates are designed to be done **gradually** and **incrementally** to minimize risk and allow for thorough testing.

## Why Gradual Updates?

The route updates are intentionally left for incremental implementation because:

1. **Testing Required:** Each route should be tested after updating to ensure correct behavior
2. **Business Logic:** Route handlers contain application-specific logic that needs careful review
3. **Low Risk:** The infrastructure is complete and safe; routes can be updated at your own pace
4. **Backward Compatible:** Existing routes will continue working (though without org scoping) until updated

## Priority Matrix

### 🔴 Critical Priority (Update First - Day 1-2)

These routes handle core functionality and should be updated immediately:

| Route File | Reason | Estimated Time |
|------------|--------|----------------|
| `app/routes/projects.py` | Core project CRUD operations | 2-3 hours |
| `app/routes/timer.py` | Time entry creation and tracking | 2-3 hours |
| `app/routes/clients.py` | Client management | 1-2 hours |

**Why Critical:**
- Most frequently used features
- Data creation happens here
- High risk of cross-org data visibility

**Update Pattern:**
```python
# Add imports
from app.utils.tenancy import get_current_organization_id, scoped_query, require_organization_access

# Add decorator to all routes
@require_organization_access()

# Use scoped queries
projects = scoped_query(Project).filter_by(status='active').all()

# Include org_id when creating
org_id = get_current_organization_id()
project = Project(name='...', organization_id=org_id, client_id=...)
```

### 🟡 High Priority (Update Next - Day 3-4)

Important features that should be updated soon:

| Route File | Reason | Estimated Time |
|------------|--------|----------------|
| `app/routes/tasks.py` | Task management and assignment | 2 hours |
| `app/routes/invoices.py` | Invoice generation and management | 2-3 hours |
| `app/routes/comments.py` | Project/task discussions | 1 hour |

**Why High Priority:**
- Frequently used features
- Involve cross-table relationships
- Important for data integrity

### 🟢 Medium Priority (Update When Convenient - Day 5-7)

Features that can be updated with less urgency:

| Route File | Reason | Estimated Time |
|------------|--------|----------------|
| `app/routes/reports.py` | Report generation | 2-3 hours |
| `app/routes/analytics.py` | Analytics views | 1-2 hours |
| `app/routes/api.py` | API endpoints (if not already covered) | 1-2 hours |

**Why Medium Priority:**
- Less frequently used
- Read-only operations (lower risk)
- Can be updated after core features

### 🔵 Low Priority (Update Eventually)

Features that can be updated last:

| Route File | Reason | Estimated Time |
|------------|--------|----------------|
| `app/routes/admin.py` | System-wide admin operations | 1-2 hours |
| `app/routes/auth.py` | Authentication (may need minor updates) | 1 hour |
| `app/routes/main.py` | Dashboard/homepage | 1 hour |

**Why Low Priority:**
- Minimal org-scoping needed
- System-wide operations
- Can work without immediate updates

## Detailed Update Checklist

### For Each Route File:

- [ ] **Step 1: Add Imports**
  ```python
  from app.utils.tenancy import (
      get_current_organization_id,
      scoped_query,
      require_organization_access,
      ensure_organization_access
  )
  ```

- [ ] **Step 2: Add Route Decorators**
  ```python
  @some_bp.route('/endpoint')
  @login_required
  @require_organization_access()  # Add this
  def my_route():
      ...
  ```

- [ ] **Step 3: Update CREATE Operations**
  ```python
  org_id = get_current_organization_id()
  new_object = Model(
      name='...',
      organization_id=org_id,  # Add this
      ...
  )
  ```

- [ ] **Step 4: Update READ Operations**
  ```python
  # Before:
  objects = Model.query.filter_by(status='active').all()
  
  # After:
  objects = scoped_query(Model).filter_by(status='active').all()
  ```

- [ ] **Step 5: Update GET by ID**
  ```python
  # Before:
  obj = Model.query.get_or_404(id)
  
  # After - Option 1:
  obj = scoped_query(Model).filter_by(id=id).first_or_404()
  
  # After - Option 2:
  obj = Model.query.get_or_404(id)
  ensure_organization_access(obj)  # Raises PermissionError if wrong org
  ```

- [ ] **Step 6: Update Complex Queries**
  ```python
  org_id = get_current_organization_id()
  
  results = db.session.query(...).join(...).filter(
      Model.organization_id == org_id,  # Add to each table
      OtherModel.organization_id == org_id
  ).all()
  ```

- [ ] **Step 7: Test the Route**
  - Create test organization
  - Test CRUD operations
  - Verify data isolation
  - Check error handling

## Route-Specific Guidance

### app/routes/projects.py

**Key Updates:**
```python
# List projects
@projects_bp.route('/')
@login_required
@require_organization_access()
def index():
    projects = scoped_query(Project).filter_by(status='active').all()
    return render_template('projects/index.html', projects=projects)

# Create project
@projects_bp.route('/new', methods=['POST'])
@login_required
@require_organization_access()
def create():
    org_id = get_current_organization_id()
    
    # Verify client is in same org
    client = scoped_query(Client).filter_by(id=request.form['client_id']).first_or_404()
    
    project = Project(
        name=request.form['name'],
        organization_id=org_id,
        client_id=client.id,
        ...
    )
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('projects.detail', project_id=project.id))

# View project
@projects_bp.route('/<int:project_id>')
@login_required
@require_organization_access()
def detail(project_id):
    project = scoped_query(Project).filter_by(id=project_id).first_or_404()
    return render_template('projects/detail.html', project=project)
```

### app/routes/timer.py

**Key Updates:**
```python
# Start timer
@timer_bp.route('/start', methods=['POST'])
@login_required
@require_organization_access()
def start():
    org_id = get_current_organization_id()
    
    # Verify project is in same org
    project = scoped_query(Project).filter_by(id=request.form['project_id']).first_or_404()
    
    entry = TimeEntry(
        user_id=current_user.id,
        project_id=project.id,
        organization_id=org_id,
        start_time=datetime.utcnow(),
        ...
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'success': True})

# List entries
@timer_bp.route('/entries')
@login_required
@require_organization_access()
def entries():
    entries = scoped_query(TimeEntry).filter_by(
        user_id=current_user.id
    ).order_by(TimeEntry.start_time.desc()).all()
    return render_template('timer/entries.html', entries=entries)
```

### app/routes/reports.py

**Key Updates:**
```python
# Project summary
@reports_bp.route('/project-summary')
@login_required
@require_organization_access()
def project_summary():
    org_id = get_current_organization_id()
    
    results = db.session.query(
        Project.name,
        func.sum(TimeEntry.duration_seconds).label('total_seconds')
    ).join(TimeEntry).filter(
        Project.organization_id == org_id,
        TimeEntry.organization_id == org_id
    ).group_by(Project.id, Project.name).all()
    
    return render_template('reports/summary.html', results=results)
```

## Testing Checklist

For each updated route, test:

### Functional Testing
- [ ] Route loads without errors
- [ ] Can create new records
- [ ] Can view existing records
- [ ] Can edit records
- [ ] Can delete records
- [ ] Error handling works correctly

### Security Testing
- [ ] Cannot view other org's data via URL manipulation
- [ ] Cannot edit other org's data
- [ ] Cannot create records in other org
- [ ] Proper 403/404 errors for invalid access

### Multi-Org Testing (if applicable)
- [ ] User with multiple orgs can switch
- [ ] Data shows correctly after switch
- [ ] Breadcrumbs/navigation work correctly

## Automation Helpers

### Find All Routes to Update

```bash
# Find all route functions
grep -r "@.*_bp.route" app/routes/ --include="*.py"

# Find all Model.query usage (potential issues)
grep -r "\.query\." app/routes/ --include="*.py" -n

# Find all db.session.query usage
grep -r "db.session.query" app/routes/ --include="*.py" -n
```

### Create Update Checklist

```bash
# Generate checklist of files to update
for file in app/routes/*.py; do
    echo "- [ ] $(basename $file)"
done
```

## Progress Tracking

| Route File | Status | Updated By | Date | Notes |
|-----------|--------|------------|------|-------|
| projects.py | ⬜ Not Started | - | - | |
| timer.py | ⬜ Not Started | - | - | |
| clients.py | ⬜ Not Started | - | - | |
| tasks.py | ⬜ Not Started | - | - | |
| invoices.py | ⬜ Not Started | - | - | |
| comments.py | ⬜ Not Started | - | - | |
| reports.py | ⬜ Not Started | - | - | |
| analytics.py | ⬜ Not Started | - | - | |
| api.py | ⬜ Not Started | - | - | |
| admin.py | ⬜ Not Started | - | - | |
| auth.py | ⬜ Not Started | - | - | |
| main.py | ⬜ Not Started | - | - | |

**Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Complete & Tested
- ⏸️ On Hold

## Quick Reference

### Common Imports
```python
from app.utils.tenancy import (
    get_current_organization_id,
    get_current_organization,
    scoped_query,
    require_organization_access,
    ensure_organization_access,
    switch_organization,
)
```

### Common Patterns
```python
# Get current org
org_id = get_current_organization_id()

# Scoped list query
items = scoped_query(Model).filter_by(status='active').all()

# Scoped get query
item = scoped_query(Model).filter_by(id=item_id).first_or_404()

# Create with org
new_item = Model(name='...', organization_id=org_id, ...)

# Verify cross-reference
related = scoped_query(RelatedModel).filter_by(id=ref_id).first_or_404()
```

## Support

- **Documentation:** `docs/ROUTE_MIGRATION_GUIDE.md`
- **Examples:** `app/routes/organizations.py`
- **Tests:** `tests/test_multi_tenant.py`
- **Help:** Review this plan and the migration guide

## Conclusion

This is a **gradual migration plan**. You don't need to update all routes at once. Start with critical routes, test thoroughly, then move to the next priority level. The infrastructure is solid and will support you throughout the process.

**Remember:** 
- One route file at a time
- Test after each update
- Follow the patterns in the guide
- Don't rush - correctness over speed

Good luck! 🚀

