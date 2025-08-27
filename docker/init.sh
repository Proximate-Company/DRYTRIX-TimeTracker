#!/bin/bash
set -e

echo "=== Starting TimeTracker Initialization ==="

# Create and set up PostgreSQL data directory
echo "Setting up PostgreSQL data directory..."
mkdir -p /var/lib/postgresql/data
chown postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

# Initialize PostgreSQL database if needed
if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    echo "Initializing PostgreSQL database..."
    su - postgres -c "initdb -D /var/lib/postgresql/data"
    echo "PostgreSQL database initialized successfully"
else
    echo "PostgreSQL database already exists"
fi

# Start supervisor to manage services
echo "Starting supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
