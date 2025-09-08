FROM python:3.11-slim-bullseye

# Build-time version argument with safe default
ARG APP_VERSION=dev-0

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV APP_VERSION=${APP_VERSION}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    bash \
    dos2unix \
    # Network tools for debugging
    iproute2 \
    net-tools \
    iputils-ping \
    dnsutils \
    # WeasyPrint dependencies (Debian Bullseye package names)
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    libffi-dev \
    shared-mime-info \
    # Additional fonts and rendering support
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install PostgreSQL 16 client tools (pg_dump/pg_restore) from PGDG to match server 16.x
RUN apt-get update && apt-get install -y gnupg wget lsb-release && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && apt-get install -y postgresql-client-16 && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Set default timezone
ENV TZ=Europe/Rome

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data and logs directories with proper permissions
RUN mkdir -p /data /data/uploads /app/logs && chmod 755 /data && chmod 755 /data/uploads && chmod 755 /app/logs

# Create Flask instance directory with proper permissions
RUN mkdir -p /app/instance && chmod 755 /app/instance

# Create upload directories with proper permissions
RUN mkdir -p /app/app/static/uploads/logos /app/static/uploads/logos && \
    chmod -R 755 /app/app/static/uploads && \
    chmod -R 755 /app/static/uploads

# Copy the startup script and ensure it's executable
COPY docker/start-fixed.py /app/start.py

# Fix line endings for the startup and entrypoint scripts
RUN dos2unix /app/start.py /app/docker/entrypoint_fixed.sh /app/docker/entrypoint.sh /app/docker/entrypoint_simple.sh 2>/dev/null || true

# Make startup scripts executable and ensure proper line endings
RUN chmod +x /app/start.py /app/docker/init-database.py /app/docker/init-database-sql.py /app/docker/init-database-enhanced.py /app/docker/verify-database.py /app/docker/test-db.py /app/docker/test-routing.py /app/docker/entrypoint.sh /app/docker/entrypoint_fixed.sh /app/docker/entrypoint_simple.sh /app/docker/entrypoint.py /app/docker/startup_with_migration.py /app/docker/test_db_connection.py /app/docker/debug_startup.sh /app/docker/simple_test.sh && \
    ls -la /app/docker/entrypoint.py && \
    head -5 /app/docker/entrypoint.py

# Create non-root user
RUN useradd -m -u 1000 timetracker && \
    chown -R timetracker:timetracker /app /data /app/logs /app/instance /app/app/static/uploads /app/static/uploads

# Verify startup script exists and is accessible
RUN ls -la /app/start.py && \
    head -1 /app/start.py

# Verify entrypoint script exists and is accessible
RUN ls -la /app/docker/entrypoint.py && \
    head -1 /app/docker/entrypoint.py

USER timetracker

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_health || exit 1

# Set the entrypoint back to the fixed shell script
ENTRYPOINT ["/app/docker/entrypoint_fixed.sh"]

# Run the application via python to avoid shebang/CRLF issues
CMD ["python", "/app/start.py"]
