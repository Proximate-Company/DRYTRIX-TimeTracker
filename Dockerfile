FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data and logs directories with proper permissions
RUN mkdir -p /data /app/logs && chmod 755 /data && chmod 755 /app/logs

# Make startup scripts executable
RUN chmod +x /app/docker/start.sh /app/docker/init-database.py /app/docker/test-db.py

# Create non-root user
RUN useradd -m -u 1000 timetracker && \
    chown -R timetracker:timetracker /app /data /app/logs
USER timetracker

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_health || exit 1

# Create startup script with database initialization
RUN echo '#!/bin/bash\n\
set -e\n\
cd /app\n\
export FLASK_APP=app\n\
\n\
echo "Waiting for database to be ready..."\n\
# Wait for Postgres to be ready\n\
python - <<"PY"\n\
import os\n\
import time\n\
import sys\n\
from sqlalchemy import create_engine, text\n\
from sqlalchemy.exc import OperationalError\n\
\n\
url = os.getenv("DATABASE_URL", "")\n\
if url.startswith("postgresql"):\n\
    for attempt in range(30):\n\
        try:\n\
            engine = create_engine(url, pool_pre_ping=True)\n\
            with engine.connect() as conn:\n\
                conn.execute(text("SELECT 1"))\n\
            print("Database connection established successfully")\n\
            break\n\
        except Exception as e:\n\
            print(f"Waiting for database... (attempt {attempt+1}/30): {e}")\n\
            time.sleep(2)\n\
    else:\n\
        print("Database not ready after waiting, exiting...")\n\
        sys.exit(1)\n\
else:\n\
    print("No PostgreSQL database configured, skipping connection check")\n\
PY\n\
\n\
echo "Checking if database is initialized..."\n\
# Check if database is initialized by looking for tables\n\
python - <<"PY"\n\
import os\n\
import sys\n\
from sqlalchemy import create_engine, text, inspect\n\
\n\
url = os.getenv("DATABASE_URL", "")\n\
if url.startswith("postgresql"):\n\
    try:\n\
        engine = create_engine(url, pool_pre_ping=True)\n\
        inspector = inspect(engine)\n\
        \n\
        # Check if our main tables exist\n\
        existing_tables = inspector.get_table_names()\n\
        required_tables = ["users", "projects", "time_entries", "settings"]\n\
        \n\
        missing_tables = [table for table in required_tables if table not in existing_tables]\n\
        \n\
        if missing_tables:\n\
            print(f"Database not fully initialized. Missing tables: {missing_tables}")\n\
            print("Will initialize database...")\n\
            sys.exit(1)  # Exit with error to trigger initialization\n\
        else:\n\
            print("Database is already initialized with all required tables")\n\
            sys.exit(0)  # Exit successfully, no initialization needed\n\
            \n\
    except Exception as e:\n\
        print(f"Error checking database initialization: {e}")\n\
        sys.exit(1)\n\
else:\n\
    print("No PostgreSQL database configured, skipping initialization check")\n\
    sys.exit(0)\n\
PY\n\
\n\
if [ $? -eq 1 ]; then\n\
    echo "Initializing database..."\n\
    python /app/docker/init-database.py\n\
    if [ $? -eq 0 ]; then\n\
        echo "Database initialized successfully"\n\
    else\n\
        echo "Database initialization failed, but continuing..."\n\
    fi\n\
else\n\
    echo "Database already initialized, skipping initialization"\n\
fi\n\
\n\
echo "Starting application..."\n\
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
