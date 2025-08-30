#!/bin/bash
set -e
cd /app
export FLASK_APP=app

echo "=== Starting TimeTracker (Simple Mode) ==="

echo "Waiting for database to be ready..."
# Simple wait loop
sleep 5

echo "Running database initialization..."
python /app/docker/init-database.py

echo "Running SQL database initialization (for invoice tables)..."
python /app/docker/init-database-sql.py

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"
