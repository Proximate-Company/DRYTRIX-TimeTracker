FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
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
RUN mkdir -p /data /app/logs && chmod 755 /data && chmod 755 /app/logs

# Create upload directories with proper permissions
RUN mkdir -p /app/app/static/uploads/logos /app/static/uploads/logos && \
    chmod -R 755 /app/app/static/uploads && \
    chmod -R 755 /app/static/uploads

# Copy the startup script and ensure it's executable
COPY docker/start-fixed.py /app/start.py

# Make startup scripts executable
RUN chmod +x /app/start.py /app/docker/init-database.py /app/docker/init-database-sql.py /app/docker/init-database-enhanced.py /app/docker/verify-database.py /app/docker/test-db.py /app/docker/test-routing.py /app/docker/entrypoint.sh /app/docker/entrypoint_fixed.sh /app/docker/startup_with_migration.py /app/docker/test_db_connection.py /app/docker/debug_startup.sh /app/docker/simple_test.sh

# Create non-root user
RUN useradd -m -u 1000 timetracker && \
    chown -R timetracker:timetracker /app /data /app/logs /app/app/static/uploads /app/static/uploads

# Verify startup script exists and is accessible
RUN ls -la /app/start.py && \
    head -1 /app/start.py

USER timetracker

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_health || exit 1

# Set the entrypoint
ENTRYPOINT ["/app/docker/entrypoint_fixed.sh"]

# Run the application
CMD ["python", "/app/start.py"]
