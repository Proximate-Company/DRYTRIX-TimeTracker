#!/usr/bin/env python3
"""
Simple database connection test script
"""

import os
import sys
import psycopg2

def test_database_connection():
    """Test basic database connection"""
    print("=== Testing Database Connection ===")
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://timetracker:timetracker@db:5432/timetracker')
    
    # Parse the URL to get connection details
    if db_url.startswith('postgresql+psycopg2://'):
        db_url = db_url.replace('postgresql+psycopg2://', '')
    
    # Extract host, port, database, user, password
    if '@' in db_url:
        auth_part, rest = db_url.split('@', 1)
        user, password = auth_part.split(':', 1)
        if ':' in rest:
            host_port, database = rest.rsplit('/', 1)
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host, port = host_port, '5432'
        else:
            host, port, database = rest, '5432', 'timetracker'
    else:
        host, port, database, user, password = 'db', '5432', 'timetracker', 'timetracker', 'timetracker'
    
    print(f"Connection details:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {database}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password)}")
    
    try:
        print(f"\nAttempting connection...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )
        
        print("✓ Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✓ Database version: {version[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("⚠ No tables found in database")
        
        cursor.close()
        conn.close()
        print("✓ Connection closed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    success = test_database_connection()
    sys.exit(0 if success else 1)
