#!/usr/bin/env python3
"""
Improved Python startup script for TimeTracker
This script ensures proper database initialization order and handles errors gracefully
"""

import os
import sys
import time
import subprocess
import traceback
import psycopg2
from urllib.parse import urlparse

def wait_for_database():
    """Wait for database to be ready with proper connection testing"""
    print("Waiting for database to be ready...")
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://timetracker:timetracker@db:5432/timetracker')
    
    # Parse the URL to get connection details
    if db_url.startswith('postgresql+psycopg2://'):
        db_url = db_url.replace('postgresql+psycopg2://', '')
    
    # Extract host, port, database, user, password
    if '@' in db_url:
        auth_part, rest = db_url.split('@', 1)
        user, password = auth_part.split(':', 1)
        if ':' in rest:
            host_port, database = rest.rsplit('/', 1)
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host, port = host_port, '5432'
        else:
            host, port, database = rest, '5432', 'timetracker'
    else:
        host, port, database, user, password = 'db', '5432', 'timetracker', 'timetracker', 'timetracker'
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            print(f"Attempting database connection to {host}:{port}/{database} as {user}...")
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5
            )
            conn.close()
            print("✓ Database connection successful!")
            return True
        except Exception as e:
            attempt += 1
            print(f"✗ Database connection attempt {attempt}/{max_attempts} failed: {e}")
            if attempt < max_attempts:
                print("Waiting 2 seconds before retry...")
                time.sleep(2)
    
    print("✗ Failed to connect to database after all attempts")
    return False

def run_script(script_path, description):
    """Run a Python script with proper error handling"""
    print(f"Running {description}...")
    try:
        result = subprocess.run(
            [sys.executable, script_path], 
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error running {description}: {e}")
        traceback.print_exc()
        return False

def display_network_info():
    """Display network information for debugging"""
    print("=== Network Information ===")
    try:
        print(f"Hostname: {os.uname().nodename}")
    except:
        print("Hostname: N/A (Windows)")
    
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"Local IP: {local_ip}")
    except:
        print("Local IP: N/A")
    
    print(f"Environment: {os.environ.get('FLASK_APP', 'N/A')}")
    print(f"Working Directory: {os.getcwd()}")
    print("==========================")

def main():
    print("=== Starting TimeTracker (Improved Python Mode) ===")
    
    # Display network information for debugging
    display_network_info()
    
    # Set environment
    os.environ['FLASK_APP'] = 'app'
    os.chdir('/app')
    
    # Wait for database
    if not wait_for_database():
        print("Database is not available, exiting...")
        sys.exit(1)
    
    # Step 1: Run SQL database initialization first (creates basic tables including tasks)
    if not run_script('/app/docker/init-database-sql.py', 'SQL database initialization'):
        print("SQL database initialization failed, exiting...")
        sys.exit(1)
    
    # Step 2: Run main database initialization (handles Flask-specific setup)
    if not run_script('/app/docker/init-database.py', 'main database initialization'):
        print("Main database initialization failed, exiting...")
        sys.exit(1)
    
    print("✓ All database initialization completed successfully")
    
    print("Starting application...")
    # Start gunicorn with access logs
    os.execv('/usr/local/bin/gunicorn', [
        'gunicorn',
        '--bind', '0.0.0.0:8080',
        '--worker-class', 'eventlet',
        '--workers', '1',
        '--timeout', '120',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'app:create_app()'
    ])

if __name__ == '__main__':
    main()
