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

def wait_for_database():
    """Wait for database to be ready"""
    print("Waiting for database to be ready...")
    time.sleep(5)  # Simple wait for now
    
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

def main():
    print("=== Starting TimeTracker (Improved Python Mode) ===")
    
    # Set environment
    os.environ['FLASK_APP'] = 'app'
    os.chdir('/app')
    
    # Wait for database
    wait_for_database()
    
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
    # Start gunicorn
    os.execv('/usr/local/bin/gunicorn', [
        'gunicorn',
        '--bind', '0.0.0.0:8080',
        '--worker-class', 'eventlet',
        '--workers', '1',
        '--timeout', '120',
        'app:create_app()'
    ])

if __name__ == '__main__':
    main()
