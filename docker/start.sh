#!/bin/bash
set -e

cd /app
export FLASK_APP=app
export DATABASE_URL=postgresql+psycopg2://timetracker@localhost:5432/timetracker

echo "=== Starting Flask Application ==="

# Wait for PostgreSQL to be ready (basic connection)
echo "Waiting for PostgreSQL to be ready..."
echo "Checking PostgreSQL process and port..."

# Wait for PostgreSQL process to be running
echo "Waiting for PostgreSQL process to start..."
until pgrep postgres > /dev/null; do
    echo "PostgreSQL process not running yet, waiting..."
    sleep 2
done
echo "PostgreSQL process is running"

# Wait additional time for PostgreSQL to fully initialize
echo "Waiting for PostgreSQL to fully initialize..."
sleep 10

# Additional wait to ensure PostgreSQL is fully initialized
echo "Waiting additional time for PostgreSQL to be fully ready..."
sleep 5

# Try to reload PostgreSQL configuration to ensure pg_hba.conf changes take effect
echo "Reloading PostgreSQL configuration..."
su - postgres -c "pg_ctl reload -D /var/lib/postgresql/data" 2>/dev/null || echo "Could not reload PostgreSQL config"
sleep 2

# Verify PostgreSQL configuration
echo "Verifying PostgreSQL configuration..."
echo "pg_hba.conf contents:"
cat /etc/postgresql/main/pg_hba.conf || echo "Could not read pg_hba.conf"
echo "postgresql.conf contents:"
cat /etc/postgresql/main/postgresql.conf || echo "Could not read postgresql.conf"

# Create database and user immediately
echo "Setting up database..."
su - postgres -c "createdb timetracker" 2>/dev/null || echo "Database timetracker already exists"
su - postgres -c "createuser -s timetracker" 2>/dev/null || echo "User timetracker already exists"

# Wait for the specific database to be ready using psql instead of pg_isready
echo "Waiting for timetracker database..."
echo "Attempting to create database if it doesn't exist..."
su - postgres -c "createdb timetracker" 2>/dev/null || echo "Database timetracker already exists"

# Try to connect to the database
echo "Testing database connection..."
until su - postgres -c "psql -d timetracker -c 'SELECT 1;'" 2>/dev/null; do
    echo "Database not ready yet, waiting..."
    echo "Current PostgreSQL status:"
    pgrep postgres || echo "No postgres process found"
    echo "PostgreSQL process status: $(pgrep postgres | wc -l) processes running"
    sleep 2
done
echo "timetracker database is ready"

# Initialize database schema if needed
if [ ! -f /var/lib/postgresql/data/.initialized ]; then
    echo "Running database schema initialization..."
    echo "Running initialization SQL..."
    su - postgres -c "psql -d timetracker -f /app/docker/init.sql"
    touch /var/lib/postgresql/data/.initialized
    echo "Database schema initialization completed"
else
    echo "Database already initialized"
fi

# List databases to verify
echo "Available databases:"
su - postgres -c "psql -l" || echo "Failed to list databases"

echo "Starting Flask application..."
echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Binding to 0.0.0.0:8080"

# Test PostgreSQL connection
echo "Testing PostgreSQL connection..."
echo "Current user: $(whoami)"
echo "PostgreSQL process status:"
pgrep postgres || echo "No postgres process found"
echo "PostgreSQL process count: $(pgrep postgres | wc -l)"
echo "Testing psql connection:"
su - postgres -c "psql -c 'SELECT version();'" || echo "Failed to connect to PostgreSQL"

# Start gunicorn directly
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 --access-logfile - --error-logfile - "app:create_app()"
