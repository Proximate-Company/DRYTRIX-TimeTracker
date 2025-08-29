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
        required_tables = ["users", "projects", "time_entries", "settings", "tasks"]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database not fully initialized. Missing tables: {missing_tables}")
            print("Will initialize database...")
            sys.exit(1)  # Exit with error to trigger initialization
        else:
            print("Database is already initialized with all required tables")
                            # Check if Task Management migration is needed
                try:
                    # Check if tasks table exists
                    if 'tasks' not in existing_tables:
                        print("Task Management tables missing, will initialize...")
                        sys.exit(1)  # Exit to trigger initialization
                    
                    # Check if task_id column exists in time_entries table
                    columns = inspector.get_columns("time_entries")
                    column_names = [col['name'] for col in columns]
                    if 'task_id' not in column_names:
                        print("Task Management columns missing, will run migration...")
                        sys.exit(3)  # Special exit code for Task Management migration
                    
                    # Check if migration is needed for field names
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
    echo "Initializing database with Python-based script..."
    python /app/docker/init-database.py
    if [ $? -ne 0 ]; then
        echo "Database initialization failed. Exiting to prevent infinite loop."
        exit 1
    fi
    echo "Database initialized successfully"
    
    # Run migration if needed
    echo "Running database migration..."
    python /app/docker/migrate-field-names.py
    
    # Run Task Management migration if needed
    echo "Running Task Management migration..."
    python /app/docker/migrate-add-task-columns.py
    
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
    
    # Also run Task Management migration for existing databases
    echo "Running Task Management migration for existing database..."
    python /app/docker/migrate-add-task-columns.py
    if [ $? -ne 0 ]; then
        echo "Task Management migration failed. Exiting."
        exit 1
    fi
    echo "Task Management migration completed successfully"
elif [ $? -eq 3 ]; then
    echo "Running Task Management migration for existing database..."
    python /app/docker/migrate-add-task-columns.py
    if [ $? -ne 0 ]; then
        echo "Task Management migration failed. Exiting."
        exit 1
    fi
    echo "Task Management migration completed successfully"
    
    # Verify the migration worked
    echo "Verifying Task Management migration..."
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
        required_tables = ["users", "projects", "time_entries", "settings", "tasks"]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database verification failed. Missing tables: {missing_tables}")
            sys.exit(1)
        
        # Check if task_id column exists in time_entries table
        try:
            columns = inspector.get_columns("time_entries")
            column_names = [col['name'] for col in columns]
            if 'task_id' not in column_names:
                print("Database verification failed. Missing task_id column in time_entries table")
                sys.exit(1)
        except Exception as e:
            print(f"Error checking time_entries columns: {e}")
            sys.exit(1)
        
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
