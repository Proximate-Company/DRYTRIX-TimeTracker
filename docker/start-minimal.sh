#!/bin/bash
set -e
cd /app
export FLASK_APP=app

echo "=== Starting TimeTracker (Minimal Mode) ==="
echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"
