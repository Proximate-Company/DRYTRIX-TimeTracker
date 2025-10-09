# License Server Setup Guide

This guide explains how to set up and run TimeTracker with the integrated license server.

## Problem

The original setup used `host.docker.internal:8082` which doesn't work properly for container-to-container communication. This setup provides a proper Docker-based solution.

## Solution

We've created a custom license server that runs in its own Docker container and can be reached by the main TimeTracker application.

## Files Created

- `docker/license-server/Dockerfile` - License server container definition
- `docker/license-server/license_server.py` - Simple Flask-based license server
- `docker-compose.license-server.yml` - Docker Compose override for license server
- `scripts/start-with-license-server.sh` - Linux/Mac startup script
- `scripts/start-with-license-server.bat` - Windows startup script

## Network Debugging Tools

### Enhanced Dockerfile
The main Dockerfile has been enhanced with:
- Network tools (`iproute2`, `net-tools`, `iputils-ping`, `dnsutils`)
- Comprehensive network information display on startup
- Connectivity testing to `host.docker.internal`

### Network Test Scripts
Use these scripts to debug Docker network connectivity:

**Linux/Mac:**
```bash
chmod +x scripts/test-docker-network.sh
./scripts/test-docker-network.sh
```

**Windows:**
```cmd
scripts\test-docker-network.bat
```

### What the Enhanced Logging Shows
When the container starts, you'll see:
- Container hostname and IP addresses
- Docker host IP (gateway)
- Connectivity test to `host.docker.internal`
- DNS configuration
- Network interfaces
- Default gateway
- Routing information

## Quick Start

### Option 1: Use the Startup Scripts (Recommended)

**Linux/Mac:**
```bash
chmod +x scripts/start-with-license-server.sh
./scripts/start-with-license-server.sh
```

**Windows:**
```cmd
scripts\start-with-license-server.bat
```

### Option 2: Manual Docker Compose

```bash
# Start both services
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml up --build -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml logs -f

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml down
```

## What This Setup Provides

### 1. License Server Container
- Runs on port 8082
- Implements all required API endpoints:
  - `/api/v1/status` - Health check
  - `/api/v1/register` - Instance registration
  - `/api/v1/validate` - License validation
  - `/api/v1/heartbeat` - Heartbeat processing
  - `/api/v1/data` - Usage data collection

### 2. Proper Container Networking
- Uses Docker service names (`license-server:8082`) instead of `host.docker.internal`
- Allows proper container-to-container communication
- Both services are on the same Docker network

### 3. Enhanced Logging
- The TimeTracker application now has comprehensive logging for license server communication
- You'll see detailed information about requests, responses, and any errors

### 4. Network Debugging
- Container displays full network information on startup
- Network test scripts for troubleshooting connectivity issues
- Enhanced error logging with detailed network diagnostics

## API Endpoints

### Health Check
```bash
curl http://localhost:8082/api/v1/status
```

### Instance Registration
```bash
curl -X POST http://localhost:8082/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "timetracker",
    "version": "1.0.0",
    "instance_id": "test-123",
    "system_metadata": {"os": "Linux"}
  }'
```

### View Registered Instances
```bash
curl http://localhost:8082/api/v1/instances
```

### View Usage Data
```bash
curl http://localhost:8082/api/v1/usage
```

## Troubleshooting

### 1. Port Already in Use
If port 8082 is already in use, you can change it in both:
- `docker-compose.license-server.yml` (ports section)
- `app/utils/license_server.py` (server_url)

### 2. Container Communication Issues
Check if both containers are running:
```bash
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml ps
```

### 3. View Detailed Logs
```bash
# License server logs
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml logs license-server

# Main application logs
docker-compose -f docker-compose.yml -f docker-compose.license-server.yml logs app
```

### 4. Test License Server Directly
```bash
# Test from host
curl http://localhost:8082/api/v1/status

# Test from within the app container
docker exec timetracker-app curl http://license-server:8082/api/v1/status
```

### 5. Network Debugging
```bash
# Run network test script
./scripts/test-docker-network.sh

# Check container network info
docker exec timetracker-app ip addr show
docker exec timetracker-app ip route show
docker exec timetracker-app cat /etc/resolv.conf
```

## Customization

### Change License Server Port
1. Update `docker-compose.license-server.yml`:
   ```yaml
   ports:
     - "8083:8082"  # Change 8083 to your desired port
   ```

2. Update `app/utils/license_server.py`:
   ```python
   self.server_url = "http://license-server:8082"  # Keep internal port as 8082
   ```

### Add Authentication
Modify `docker/license-server/license_server.py` to add authentication logic to the endpoints.

### Persistent Storage
The current implementation uses in-memory storage. For production, consider:
- Adding a database service
- Using Redis for caching
- Implementing proper data persistence

## Security Notes

- This is a development/demo setup
- The license server accepts all requests without authentication
- For production use, implement proper security measures
- Consider using HTTPS for production deployments

## Next Steps

1. Start the services using one of the methods above
2. Check the logs to ensure both services are running
3. Run the network test script to verify connectivity
4. Test the license server endpoints
5. Monitor the TimeTracker application logs for successful license server communication

The enhanced logging and network debugging tools will now provide detailed information about all license server interactions and network configuration, making it much easier to diagnose any issues.
