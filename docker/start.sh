#!/bin/bash
set -e

cd /app
export FLASK_APP=app

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
        required_tables = ['users', 'projects', 'time_entries', 'settings']
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database not fully initialized. Missing tables: {missing_tables}")
            print("Will initialize database...")
            sys.exit(1)  # Exit with error to trigger initialization
        else:
            print("Database is already initialized with all required tables")
            sys.exit(0)  # Exit successfully, no initialization needed
            
    except Exception as e:
        print(f"Error checking database initialization: {e}")
        sys.exit(1)
else:
    print("No PostgreSQL database configured, skipping initialization check")
    sys.exit(0)
PY

if [ $? -eq 1 ]; then
    echo "Initializing database..."
    python /app/docker/init-database.py
    if [ $? -eq 0 ]; then
        echo "Database initialized successfully"
    else
        echo "Database initialization failed, but continuing..."
    fi
else
    echo "Database already initialized, skipping initialization"
fi

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"
