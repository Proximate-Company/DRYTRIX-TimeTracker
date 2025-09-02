#!/bin/bash
set -e

echo "=== Simple Test Script ==="
echo "Timestamp: $(date)"
echo "Container ID: $(hostname)"
echo "Current directory: $(pwd)"
echo "User: $(whoami)"
echo

# Test 1: Basic environment
echo "=== Test 1: Environment ==="
echo "DATABASE_URL: ${DATABASE_URL:-'NOT SET'}"
echo "FLASK_APP: ${FLASK_APP:-'NOT SET'}"
echo "PATH: $PATH"
echo

# Test 2: Basic commands
echo "=== Test 2: Basic Commands ==="
echo "Python version: $(python --version)"
echo "Flask version: $(flask --version 2>/dev/null || echo 'Flask CLI not available')"
echo "psql available: $(command -v psql >/dev/null 2>&1 && echo 'YES' || echo 'NO')"
echo

# Test 3: File access
echo "=== Test 3: File Access ==="
echo "Can access /app: $(test -d /app && echo 'YES' || echo 'NO')"
echo "Can access /app/docker: $(test -d /app/docker && echo 'YES' || echo 'NO')"
echo "Entrypoint script exists: $(test -f /app/docker/entrypoint.sh && echo 'YES' || echo 'NO')"
echo "Entrypoint script executable: $(test -x /app/docker/entrypoint.sh && echo 'YES' || echo 'NO')"
echo

# Test 4: Network connectivity
echo "=== Test 4: Network Connectivity ==="
if ping -c 1 db >/dev/null 2>&1; then
    echo "✓ Can ping database host 'db'"
else
    echo "✗ Cannot ping database host 'db'"
fi

if command -v nc >/dev/null 2>&1; then
    if nc -zv db 5432 2>/dev/null; then
        echo "✓ Database port 5432 is accessible"
    else
        echo "✗ Database port 5432 is not accessible"
    fi
else
    echo "⚠ netcat not available, skipping port test"
fi
echo

# Test 5: Python connection test
echo "=== Test 5: Python Connection Test ==="
if [[ -n "${DATABASE_URL}" ]]; then
    echo "Testing connection with Python..."
    if python -c "
import psycopg2
import sys
try:
    # Parse connection string to remove +psycopg2 if present
    conn_str = '${DATABASE_URL}'.replace('+psycopg2://', '://')
    print(f'Trying to connect to: {conn_str}')
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print(f'✓ Connection successful, test query result: {result}')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'✗ Connection failed: {e}')
    sys.exit(1)
"; then
        echo "✓ Python connection test successful"
    else
        echo "✗ Python connection test failed"
    fi
else
    echo "⚠ DATABASE_URL not set, skipping connection test"
fi
echo

echo "=== Test Complete ==="
echo "If you see this message, the basic script execution is working."
echo "Check the output above for any specific failures."
