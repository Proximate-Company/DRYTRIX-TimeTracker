# License Server Docker Setup Guide

This guide explains how to configure the license server integration when running TimeTracker in Docker containers.

## Overview

The TimeTracker application includes a license server client that communicates with a DryLicenseServer for monitoring and analytics purposes. **No license is required** to use the application - this integration is purely for usage tracking and system monitoring.

## Important: Hardcoded License Server IP

**The license server IP address is hardcoded in the application code and cannot be changed by clients.**

- **IP Address**: `192.168.1.100:8081`
- **Location**: Hardcoded in `app/utils/license_server.py`
- **Client Control**: None - clients cannot modify this
- **Purpose**: Ensures consistent monitoring across all deployments

## Docker Environment Behavior

### Expected Behavior (Server Unavailable)

When the license server at `192.168.1.100:8081` is not available:

```
[INFO] Starting license server client
[INFO] Registering instance [uuid] with license server at http://192.168.1.100:8081
[INFO] License server at http://192.168.1.100:8081 is not available - continuing without registration
[INFO] License server not available - client will run in offline mode
[INFO] License server client started successfully
```

This is **normal and expected** when no license server is running.

## Configuration Options

### 1. Disable License Server Integration

**Note**: License server integration is now always enabled by default. To disable it, you would need to modify the source code in `app/config.py`.

**Result**: No license server integration, clean logs, no warnings.

### 2. License Server Integration (Default)

By default, the license server integration is enabled and will:

- Attempt to connect to `192.168.1.100:8081`
- Run in offline mode if server is unavailable
- Store data locally for later transmission
- Continue all application functionality normally

**Result**: Application works completely offline, no blocking operations.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **N/A** | **N/A** | **All license server settings are hardcoded in the application code** |

**Note**: The license server IP address and all configuration settings are hardcoded in `app/utils/license_server.py` and `app/config.py`. Clients cannot modify these settings through environment variables.

## Common Scenarios

### Scenario 1: No License Server Needed

**Note**: To disable license server integration, you must modify the source code in `app/config.py` and rebuild the Docker image.

**Result**: No license server integration, clean logs, no warnings.

### Scenario 2: License Server Available at 192.168.1.100:8081

**Default configuration** - no changes needed. The application automatically connects to the hardcoded license server IP.

**Result**: Connects to hardcoded license server IP.

### Scenario 3: License Server in Different Network

**Note**: If your license server is not at `192.168.1.100:8081`, you will need to:

1. **Modify the source code** in `app/utils/license_server.py`
2. **Rebuild the Docker image**
3. **Or disable the integration** by modifying `app/config.py`

## Troubleshooting

### Connection Refused Errors

**Symptoms**: Info messages about license server not being available

**Cause**: License server not running at `192.168.1.100:8081`

**Solutions**:
1. **Ignore** - This is normal if no license server is needed
2. **Disable** - Modify `app/config.py` and rebuild the Docker image
3. **Verify** - Check if license server is running at the hardcoded IP

### Application Won't Start

**Symptoms**: Application crashes during startup

**Cause**: Usually not related to license server (check other logs)

**Solutions**:
1. Check database connectivity
2. Verify environment variables
3. Check application logs for other errors

## Best Practices

### 1. Development Environment

**Default configuration** - License server integration is enabled by default and will work in offline mode if no server is available.

### 2. Production Environment

**Default configuration** - License server integration is enabled by default and will connect to the hardcoded IP address.

### 3. Monitoring

Check license server status in admin panel:
- Navigate to Admin Dashboard
- Click "License Status"
- Monitor connection health

## CLI Commands

Test license server integration:

```bash
# Check status
docker-compose exec web flask license-status

# Test connection
docker-compose exec web flask license-test

# Restart client
docker-compose exec web flask license-restart
```

## Summary

- **No license required** - Application functions normally without license server
- **IP hardcoded** - License server IP is `192.168.1.100:8081` and cannot be changed by clients
- **Works offline** - Application functions completely without license server
- **Non-intrusive** - Won't prevent application from starting or functioning
- **Monitoring available** - Admin interface shows status and health

The license server integration is designed to be completely optional and won't interfere with normal application operation. The hardcoded IP ensures consistent monitoring across all deployments.
