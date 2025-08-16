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

# Create data directory with proper permissions
RUN mkdir -p /data && chmod 755 /data

# Create non-root user
RUN useradd -m -u 1000 timetracker && \
    chown -R timetracker:timetracker /app /data
USER timetracker

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
cd /app\n\
export FLASK_APP=app\n\
# Wait for Postgres if configured\n\
python - <<"PY"\n\
import os, time, sys\n\
from sqlalchemy import create_engine, text\n\nurl = os.getenv("DATABASE_URL", "")\nif url.startswith("postgresql"):\n    for attempt in range(30):\n        try:\n            engine = create_engine(url, pool_pre_ping=True)\n            with engine.connect() as conn:\n                conn.execute(text("SELECT 1"))\n            print("Database is ready")\n            break\n        except Exception as e:\n            print(f"Waiting for database... (attempt {attempt+1}/30): {e}")\n            time.sleep(2)\n    else:\n        print("Database not ready after waiting, continuing anyway...")\n\nPY\n\
echo "Initializing database..."\n\
flask init-db || echo "Database initialization failed, continuing..."\n\
echo "Starting application..."\n\
exec gunicorn --bind 0.0.0.0:8080 --worker-class eventlet --workers 1 --timeout 120 "app:create_app()"\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
