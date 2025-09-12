# Metrics Server Integration

This document describes the implementation of the metrics server communication in the TimeTracker application.

## Overview

The TimeTracker application includes a metrics client that communicates with a metrics server for monitoring and analytics purposes. **No license is required** to use the application — this integration is purely for usage tracking and system monitoring.

## Implementation Details

### Core Components

1. **LicenseServerClient** (`app/utils/license_server.py`)
   - Main client class for communicating with the metrics server
   - Handles instance registration, heartbeats, and usage data transmission
   - Implements offline data storage for failed requests
   - Runs background heartbeat thread

2. **Configuration** (`app/utils/license_server.py` and environment)
   - Metrics server settings are environment-configurable with sane defaults
   - Default values are provided for development

3. **Integration** (`app/__init__.py`)
   - Automatic initialization during application startup
   - Graceful error handling if metrics server is unavailable

4. **Admin Interface** (`app/routes/admin.py`)
   - Metrics server status monitoring
   - Testing and restart capabilities
   - Integration with admin dashboard

### Features

- ✅ **Automatic Instance Registration**: Registers each application instance with unique ID
- ✅ **Periodic Heartbeats**: Sends status updates every hour (configurable)
- ✅ **Usage Data Collection**: Tracks application usage and features
- ✅ **Offline Storage**: Stores data locally when server is unavailable
- ✅ **Graceful Error Handling**: Continues operation even if metrics server fails
- ✅ **System Information Collection**: Gathers OS, hardware, and environment details
- ✅ **Admin Monitoring**: Web interface for status and management

## Configuration

### Environment Variables

Metrics server configuration supports environment overrides (legacy variable names are also accepted for compatibility):

- `METRICS_SERVER_URL` (legacy: `LICENSE_SERVER_BASE_URL`)
- `METRICS_SERVER_API_KEY` (legacy: `LICENSE_SERVER_API_KEY`)
- `METRICS_HEARTBEAT_SECONDS` (legacy: `LICENSE_HEARTBEAT_SECONDS`) — default 3600
- `METRICS_SERVER_TIMEOUT_SECONDS` (legacy: `LICENSE_SERVER_TIMEOUT_SECONDS`) — default 30

## API Endpoints Used

| Endpoint | Purpose | Status |
|----------|---------|---------|
| `/api/v1/register` | Instance registration | ✅ Implemented |
| `/api/v1/validate` | Token validation | ✅ Implemented (no license required) |
| `/api/v1/heartbeat` | Status updates | ✅ Implemented |
| `/api/v1/data` | Usage data transmission | ✅ Implemented |
| `/api/v1/status` | Server health check | ✅ Implemented |

## Usage

### Automatic Operation

The metrics client starts automatically when the application starts:

1. **Application Startup**: Client initializes and registers instance
2. **Background Heartbeats**: Sends status updates every hour
3. **Usage Tracking**: Collects and transmits usage data
4. **Graceful Shutdown**: Stops cleanly when application exits

### Manual Control

#### CLI Commands

```bash
# Check metrics status
flask license-status

# Test metrics communication
flask license-test

# Restart metrics client
flask license-restart
```

#### Admin Interface

- **Dashboard**: Quick access to metrics status
- **Metrics Status Page**: Detailed status information
- **Test Connection**: Verify server communication
- **Restart Client**: Restart the metrics client

### Programmatic Usage

```python
from app.utils.license_server import send_usage_event, get_license_client

# Send a usage event
send_usage_event("feature_used", {"feature": "dashboard", "user": "admin"})

# Get client status
client = get_license_client()
if client:
    status = client.get_status()
    print(f"Instance ID: {status['instance_id']}")
```

## Data Collection

### System Information (minimal)

- Operating system and version
- Hardware architecture
- Python version
- Hostname and local IP
- Processor information

### Usage Events (aggregate)

- Feature usage tracking
- User actions
- Session information
- Performance metrics

### Data Format

```json
{
  "app_identifier": "timetracker",
  "instance_id": "uuid-here",
  "data": [
    {
      "key": "usage_event",
      "value": "feature_used",
      "type": "string",
      "metadata": {"feature": "dashboard"}
    }
  ]
}
```

## Error Handling

### Network Failures

- Automatic retry with exponential backoff
- Offline data storage for failed requests
- Graceful degradation when server is unavailable

### Invalid Responses

- Logs warnings for failed requests
- Continues operation without interruption
- Reports errors to admin interface

### Startup Failures

- Application continues to function
- Metrics client marked as unavailable
- Admin interface shows error status

## Monitoring and Debugging

### Logs

Metrics client operations are logged with appropriate levels:

- **INFO**: Successful operations and status changes
- **WARNING**: Failed requests and connection issues
- **ERROR**: Unexpected errors and exceptions
- **DEBUG**: Detailed operation information

### Admin Interface

The admin panel provides:

- Real-time status information
- Connection health monitoring
- Offline data queue status
- Manual testing capabilities

### Health Checks

- Server availability monitoring
- Client status verification
- Automatic health reporting

## Security Considerations

- **No License Required**: Application functions without license validation
- **Local Data Storage**: Sensitive data not transmitted
- **Minimal Information**: Only system and usage metrics collected
- **Configurable**: Can be disabled via environment variables

## Testing

### Test Script

Run the included test script:

```bash
python test_license_server.py
```

### Manual Testing

1. Start the application
2. Check admin dashboard for metrics status
3. Use CLI commands to test functionality
4. Monitor logs for operation details

### Integration Testing

1. Start a metrics server on localhost:8081
2. Verify registration and heartbeats
3. Test usage data transmission
4. Check offline data handling

## Troubleshooting

### Common Issues

1. **Server Not Responding**
   - Check if metrics server is running on port 8081
   - Verify network connectivity
   - Check firewall settings

2. **Client Not Starting**
   - Review application logs
   - Check configuration values
   - Verify dependencies (requests library)

3. **Data Not Transmitting**
   - Check offline data queue
   - Verify server health
   - Review network configuration

### Debug Commands

```bash
# Check detailed status
flask license-status

# Test communication
flask license-test

# View application logs
tail -f logs/timetracker.log
```

## Future Enhancements

- **Geolocation**: Add IP-based location detection
- **Metrics Dashboard**: Enhanced usage analytics
- **Performance Monitoring**: System performance metrics
- **Alert System**: Notifications for server issues
- **Data Export**: Export collected usage data

## Support

For issues with the metrics server integration:

1. Check the admin interface for status
2. Review application logs
3. Use CLI commands for testing
4. Verify metrics server availability
5. Check configuration values

The integration is designed to be non-intrusive and will not prevent the application from functioning normally.
