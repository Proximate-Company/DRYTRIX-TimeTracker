#!/bin/bash
set -e
cd /app
export FLASK_APP=app

echo "=== Starting TimeTracker ==="

echo "Waiting for database to be ready..."
# Wait for Postgres to be ready
python - <<"PY"
import os
import time
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

url = os.getenv("DATABASE_URL", "")
if url.startswith("postgresql"):
    for attempt in range(30):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection established successfully")
            break
        except Exception as e:
            print(f"Waiting for database... (attempt {attempt+1}/30): {e}")
            time.sleep(2)
    else:
        print("Database not ready after waiting, exiting...")
        sys.exit(1)
else:
    print("No PostgreSQL database configured, skipping connection check")
PY

echo "Checking if database is initialized..."
# Check if database is initialized by looking for tables
python - <<"PY"
import os
import sys
from sqlalchemy import create_engine, text, inspect

url = os.getenv("DATABASE_URL", "")
if url.startswith("postgresql"):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        inspector = inspect(engine)
        
        # Check if our main tables exist
        existing_tables = inspector.get_table_names()
        required_tables = ["users", "projects", "time_entries", "settings"]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database not fully initialized. Missing tables: {missing_tables}")
            print("Will initialize database...")
            sys.exit(1)  # Exit with error to trigger initialization
        else:
            print("Database is already initialized with all required tables")
            # Check if migration is needed
            try:
                columns = inspector.get_columns("time_entries")
                column_names = [col['name'] for col in columns]
                has_old_fields = 'start_utc' in column_names or 'end_utc' in column_names
                if has_old_fields:
                    print("Migration needed for field names")
                    sys.exit(2)  # Special exit code for migration
                else:
                    print("No migration needed")
                    sys.exit(0)  # Exit successfully, no initialization needed
            except Exception as e:
                print(f"Error checking migration status: {e}")
                sys.exit(0)  # Assume no migration needed
            
    except Exception as e:
        print(f"Error checking database initialization: {e}")
        sys.exit(1)
else:
    print("No PostgreSQL database configured, skipping initialization check")
    sys.exit(0)
PY

if [ $? -eq 1 ]; then
    echo "Initializing database with SQL-based script..."
    python /app/docker/init-database-sql.py
    if [ $? -ne 0 ]; then
        echo "Database initialization failed. Exiting to prevent infinite loop."
        exit 1
    fi
    echo "Database initialized successfully"
    
    # Run migration if needed
    echo "Running database migration..."
    python /app/docker/migrate-field-names.py
    
    # Verify initialization worked
    echo "Verifying database initialization..."
elif [ $? -eq 2 ]; then
    echo "Running database migration for existing database..."
    python /app/docker/migrate-field-names.py
    if [ $? -ne 0 ]; then
        echo "Database migration failed. Exiting."
        exit 1
    fi
    echo "Database migration completed successfully"
    python - <<"PY"
import os
import sys
from sqlalchemy import create_engine, text, inspect

url = os.getenv("DATABASE_URL", "")
if url.startswith("postgresql"):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        inspector = inspect(engine)
        
        existing_tables = inspector.get_table_names()
        required_tables = ["users", "projects", "time_entries", "settings"]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database verification failed. Missing tables: {missing_tables}")
            sys.exit(1)
        else:
            print("Database verification successful")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error verifying database: {e}")
        sys.exit(1)
else:
    print("No PostgreSQL database configured, skipping verification")
    sys.exit(0)
PY
    
    if [ $? -eq 1 ]; then
        echo "Database verification failed after initialization. Exiting to prevent infinite loop."
        exit 1
    fi
else
    echo "Database already initialized, skipping initialization"
fi

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"
