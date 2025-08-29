FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
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

# Copy the fixed startup script
COPY docker/start-fixed.sh /app/start.sh

# Make startup scripts executable
RUN chmod +x /app/start.sh /app/docker/init-database.py /app/docker/init-database-sql.py /app/docker/test-db.py /app/docker/start-fixed.sh

# Create non-root user
RUN useradd -m -u 1000 timetracker && \
    chown -R timetracker:timetracker /app /data /app/logs && \
    chmod +x /app/start.sh

# Verify startup script exists and is accessible
RUN ls -la /app/start.sh && \
    head -1 /app/start.sh

USER timetracker

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_health || exit 1

# Run the application
CMD ["/app/start.sh"]
