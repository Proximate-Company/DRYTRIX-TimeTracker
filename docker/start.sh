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
# Always run the database initialization script to ensure proper schema
echo "Running database initialization script..."
python /app/docker/init-database.py
if [ $? -ne 0 ]; then
    echo "Database initialization failed. Exiting to prevent infinite loop."
    exit 1
fi
echo "Database initialization completed successfully"

# Also run the simple schema fix to ensure task_id column exists
echo "Running schema fix script..."
python /app/docker/fix-schema.py
if [ $? -ne 0 ]; then
    echo "Schema fix failed. Exiting."
    exit 1
fi
echo "Schema fix completed successfully"

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"
