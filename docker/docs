# Docker Database Initialization

This directory contains scripts and configuration for the TimeTracker Docker setup with automatic database initialization.

## Overview

The Docker setup now includes automatic database connection checking and initialization:

1. **Database Connection Check**: The app waits for the PostgreSQL database to be ready
2. **Initialization Check**: Verifies if the database has the required tables
3. **Automatic Initialization**: If needed, runs the Python initialization script to create tables and default data

## Files

### `start.sh`
Main startup script that:
- Waits for database connection
- Checks if database is initialized
- Runs initialization if needed
- Starts the Flask application

### `init-database.py`
Python script that:
- Connects to the database
- Creates all required tables using SQLAlchemy models
- Creates default admin user, settings, and project
- Handles errors gracefully

### `test-db.py`
Utility script to test database connectivity and show initialization status.

### `init.sql` and `init-db.sh`
Legacy initialization scripts (kept for reference, not used by default).

## How It Works

1. **Docker Compose** starts the PostgreSQL container
2. **Health Check** ensures PostgreSQL is ready
3. **App Container** waits for database to be healthy
4. **Startup Script** checks database connection
5. **Initialization Check** verifies required tables exist
6. **Python Script** creates tables and default data if needed
7. **Flask App** starts normally

## Environment Variables

The following environment variables are used:

- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_USERNAMES`: Comma-separated list of admin usernames
- `TZ`: Timezone setting
- `CURRENCY`: Currency setting
- `ROUNDING_MINUTES`: Time rounding setting

## Testing

To test the database setup manually:

```bash
# Test database connection and status
docker exec timetracker-app python /app/docker/test-db.py

# Manually initialize database (if needed)
docker exec timetracker-app python /app/docker/init-database.py
```

## Troubleshooting

### Database Connection Issues
- Check if PostgreSQL container is running: `docker ps`
- Check PostgreSQL logs: `docker logs timetracker-db`
- Verify environment variables are set correctly

### Initialization Issues
- Check app container logs: `docker logs timetracker-app`
- Verify database permissions
- Check if tables exist: `docker exec timetracker-db psql -U timetracker -d timetracker -c "\dt"`

### Health Check Failures
- Ensure the `/_health` endpoint is accessible
- Check if the app is binding to the correct port
- Verify network connectivity between containers
