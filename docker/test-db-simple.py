#!/usr/bin/env python3
"""
Simple database test script to debug connection and table creation issues
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def test_database():
    """Test database connection and basic operations"""
    url = os.getenv("DATABASE_URL", "")
    
    if not url.startswith("postgresql"):
        print("No PostgreSQL database configured")
        return False
    
    print(f"Testing database URL: {url}")
    
    try:
        # Test connection
        print("Testing database connection...")
        engine = create_engine(url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
        
        # Test table inspection
        print("Testing table inspection...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ Found {len(tables)} tables: {tables}")
        
        # Test creating a simple table
        print("Testing table creation...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """))
            conn.commit()
            print("✓ Test table created successfully")
        
        # Verify table was created
        tables_after = inspector.get_table_names()
        if 'test_table' in tables_after:
            print("✓ Test table verification successful")
        else:
            print("✗ Test table verification failed")
            return False
        
        # Clean up test table
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE test_table"))
            conn.commit()
            print("✓ Test table cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
