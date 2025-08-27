#!/usr/bin/env python3
"""
Database initialization script for TimeTracker
This script checks if the database is connected and initialized,
and initializes it if needed.
"""

import os
import sys
import time
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

def wait_for_database(url, max_attempts=30, delay=2):
    """Wait for database to be ready"""
    print(f"Waiting for database to be ready...")
    
    for attempt in range(max_attempts):
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection established successfully")
            return engine
        except Exception as e:
            print(f"Waiting for database... (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print("Database not ready after waiting, exiting...")
                sys.exit(1)
    
    return None

def check_database_initialization(engine):
    """Check if database is initialized by looking for required tables"""
    print("Checking if database is initialized...")
    
    try:
        inspector = inspect(engine)
        
        # Check if our main tables exist
        existing_tables = inspector.get_table_names()
        required_tables = ['users', 'projects', 'time_entries', 'settings']
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"Database not fully initialized. Missing tables: {missing_tables}")
            return False
        else:
            print("Database is already initialized with all required tables")
            return True
            
    except Exception as e:
        print(f"Error checking database initialization: {e}")
        return False

def initialize_database(engine):
    """Initialize database using Flask CLI command"""
    print("Initializing database...")
    
    try:
        # Set environment variables for Flask
        os.environ['FLASK_APP'] = 'app'
        
        # Import Flask app and initialize database
        from app import create_app, db
        from app.models import User, Project, TimeEntry, Settings
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create default admin user if it doesn't exist
            admin_username = os.getenv('ADMIN_USERNAMES', 'admin').split(',')[0]
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(
                    username=admin_username,
                    role='admin'
                )
                admin_user.is_active = True
                db.session.add(admin_user)
                db.session.commit()
                print(f"Created default admin user: {admin_username}")
            
            # Create default settings if they don't exist
            if not Settings.query.first():
                settings = Settings()
                db.session.add(settings)
                db.session.commit()
                print("Created default settings")
            
            # Create default project if it doesn't exist
            if not Project.query.first():
                project = Project(
                    name='General',
                    client='Default Client',
                    description='Default project for general tasks',
                    billable=True,
                    status='active'
                )
                db.session.add(project)
                db.session.commit()
                print("Created default project")
            
            print("Database initialized successfully")
            return True
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def main():
    """Main function"""
    url = os.getenv("DATABASE_URL", "")
    
    if not url.startswith("postgresql"):
        print("No PostgreSQL database configured, skipping initialization")
        return
    
    # Wait for database to be ready
    engine = wait_for_database(url)
    
    # Check if database is initialized
    if not check_database_initialization(engine):
        # Initialize database
        if initialize_database(engine):
            print("Database initialization completed successfully")
        else:
            print("Database initialization failed")
            sys.exit(1)
    else:
        print("Database already initialized, no action needed")

if __name__ == "__main__":
    main()
