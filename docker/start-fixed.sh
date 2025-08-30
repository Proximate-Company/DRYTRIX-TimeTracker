#!/bin/bash
set -e
cd /app
export FLASK_APP=app

echo "=== Starting TimeTracker (Fixed Shell Mode) ==="

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

echo "=== RUNNING DATABASE INITIALIZATION ==="

# Step 1: Run SQL database initialization first (creates basic tables including tasks)
echo "Step 1: Running SQL database initialization..."
if python /app/docker/init-database-sql.py; then
    echo "✓ SQL database initialization completed"
else
    echo "✗ SQL database initialization failed"
    exit 1
fi

# Step 2: Run main database initialization (handles Flask-specific setup)
echo "Step 2: Running main database initialization..."
if python /app/docker/init-database.py; then
    echo "✓ Main database initialization completed"
else
    echo "✗ Main database initialization failed"
    exit 1
fi

echo "✓ All database initialization completed successfully"

echo "Starting application..."
# Start gunicorn
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --worker-class eventlet \
    --workers 1 \
    --timeout 120 \
    app:create_app()
