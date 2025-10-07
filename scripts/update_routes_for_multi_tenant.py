#!/usr/bin/env python3
"""
Automated script to update route files for multi-tenant support.

This script applies the multi-tenant patterns to all route files:
1. Adds tenancy imports
2. Adds @require_organization_access() decorators  
3. Replaces Model.query with scoped_query(Model)
4. Adds organization_id to create operations

Usage:
    python scripts/update_routes_for_multi_tenant.py
"""

import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
ROUTES_DIR = BASE_DIR / 'app' / 'routes'

# Import statements to add
TENANCY_IMPORTS = """from app.utils.tenancy import (
    get_current_organization_id,
    get_current_organization,
    scoped_query,
    require_organization_access,
    ensure_organization_access
)"""

def add_tenancy_imports(content):
    """Add tenancy imports after existing imports."""
    # Find the last import statement
    import_pattern = r'(from .+ import .+\n)(?!from|import)'
    match = re.search(import_pattern, content)
    
    if match and 'tenancy' not in content:
        insert_pos = match.end()
        return content[:insert_pos] + '\n' + TENANCY_IMPORTS + '\n' + content[insert_pos:]
    return content

def add_decorator_to_route(content):
    """Add @require_organization_access() decorator to routes."""
    # Pattern: @route_bp.route(...)\n@login_required\ndef func_name
    pattern = r'(@\w+_bp\.route\([^)]+\)\n)(@login_required\n)(def \w+\([^)]*\):)'
    
    def replacement(match):
        if '@require_organization_access()' in content[max(0, match.start()-200):match.end()+50]:
            return match.group(0)  # Already has decorator
        return match.group(1) + match.group(2) + '@require_organization_access()\n' + match.group(3)
    
    return re.sub(pattern, replacement, content)

def replace_model_query(content):
    """Replace Model.query with scoped_query(Model)."""
    # Pattern: ModelName.query
    models = ['Project', 'Client', 'TimeEntry', 'Task', 'Invoice', 'Comment', 'FocusSession']
    
    for model in models:
        # Replace Model.query with scoped_query(Model)
        # But not in comments or strings
        pattern = rf'\b{model}\.query\b'
        content = re.sub(pattern, f'scoped_query({model})', content)
    
    return content

def update_route_file(filepath):
    """Update a single route file."""
    print(f"Updating {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply transformations
    content = add_tenancy_imports(content)
    content = add_decorator_to_route(content)
    content = replace_model_query(content)
    
    # Only write if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated {filepath.name}")
        return True
    else:
        print(f"  - No changes needed for {filepath.name}")
        return False

def main():
    """Main function to update all route files."""
    print("=" * 60)
    print("Multi-Tenant Route Update Script")
    print("=" * 60)
    print()
    
    # Files to update (in priority order)
    route_files = [
        'projects.py',  # Already updated manually
        'clients.py',
        'timer.py',
        'tasks.py',
        'invoices.py',
        'comments.py',
        'reports.py',
        'analytics.py',
        'api.py',
        'admin.py',
    ]
    
    updated_count = 0
    for filename in route_files:
        filepath = ROUTES_DIR / filename
        if filepath.exists():
            if update_route_file(filepath):
                updated_count += 1
        else:
            print(f"  ⚠ File not found: {filename}")
    
    print()
    print("=" * 60)
    print(f"Updated {updated_count} file(s)")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Manual review required!")
    print()
    print("The automated updates handle common patterns, but you MUST:")
    print("1. Review each file for correctness")
    print("2. Add organization_id to CREATE operations")
    print("3. Verify client/project relationships are scoped")
    print("4. Test each route thoroughly")
    print()
    print("See docs/ROUTE_MIGRATION_GUIDE.md for details.")

if __name__ == '__main__':
    main()

