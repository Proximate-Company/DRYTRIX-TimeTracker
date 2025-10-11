#!/usr/bin/env python3
"""
Test script to verify kanban column refresh behavior
Run this to test if columns are being cached or loaded fresh
"""

from app import create_app, db
from app.models import KanbanColumn
import time

app = create_app()

def test_column_caching():
    """Test if columns are cached or loaded fresh"""
    with app.app_context():
        print("=" * 60)
        print("Testing Kanban Column Caching Behavior")
        print("=" * 60)
        
        # Get initial columns
        print("\n1. Initial column count:")
        initial_columns = KanbanColumn.get_active_columns()
        print(f"   Found {len(initial_columns)} active columns")
        for col in initial_columns:
            print(f"   - {col.key}: {col.label} (pos: {col.position})")
        
        # Create a test column
        print("\n2. Creating test column...")
        test_col = KanbanColumn(
            key='test_refresh',
            label='Test Refresh',
            icon='fas fa-flask',
            color='primary',
            position=99,
            is_system=False,
            is_active=True
        )
        db.session.add(test_col)
        db.session.commit()
        print("   ✓ Test column created")
        
        # Check WITHOUT clearing cache
        print("\n3. Querying columns WITHOUT cache clear:")
        columns_no_clear = KanbanColumn.get_active_columns()
        print(f"   Found {len(columns_no_clear)} columns")
        test_found = any(c.key == 'test_refresh' for c in columns_no_clear)
        print(f"   Test column found: {test_found}")
        
        # Clear cache and check again
        print("\n4. Clearing cache with expire_all()...")
        db.session.expire_all()
        print("   Cache cleared")
        
        print("\n5. Querying columns AFTER cache clear:")
        columns_after_clear = KanbanColumn.get_active_columns()
        print(f"   Found {len(columns_after_clear)} columns")
        test_found = any(c.key == 'test_refresh' for c in columns_after_clear)
        print(f"   Test column found: {test_found}")
        
        # Clean up
        print("\n6. Cleaning up test column...")
        db.session.delete(test_col)
        db.session.commit()
        print("   ✓ Test column deleted")
        
        # Final count
        print("\n7. Final column count:")
        final_columns = KanbanColumn.get_active_columns()
        print(f"   Found {len(final_columns)} columns")
        
        print("\n" + "=" * 60)
        print("CONCLUSION:")
        print("=" * 60)
        if test_found:
            print("✓ Cache clearing works correctly!")
            print("✓ New columns appear without restart")
        else:
            print("✗ Cache clearing NOT working!")
            print("✗ This explains why restart was needed")
        print("=" * 60)

if __name__ == '__main__':
    test_column_caching()

