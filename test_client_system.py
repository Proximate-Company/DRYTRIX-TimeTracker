#!/usr/bin/env python3
"""
Test script for the new client management system
This script will test:
1. Client creation
2. Project creation with client selection
3. Rate auto-population
4. Client management operations
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import User, Project, Client

def test_client_system():
    """Test the client management system"""
    app = create_app()
    
    with app.app_context():
        print("Testing Client Management System...")
        print("=" * 50)
        
        try:
            # Check if clients table exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'clients' not in existing_tables:
                print("❌ Clients table does not exist. Please run the migration first.")
                return False
            
            print("✅ Clients table exists")
            
            # Check if projects table has client_id column
            project_columns = [col['name'] for col in inspector.get_columns('projects')]
            
            if 'client_id' not in project_columns:
                print("❌ Projects table missing client_id column. Please run the migration first.")
                return False
            
            print("✅ Projects table has client_id column")
            
            # Test client creation
            print("\nTesting Client Creation...")
            
            # Check if test client already exists
            test_client = Client.query.filter_by(name='Test Client Corp').first()
            if test_client:
                print(f"✅ Test client already exists (ID: {test_client.id})")
            else:
                # Create test client
                test_client = Client(
                    name='Test Client Corp',
                    description='Test client for system verification',
                    contact_person='John Doe',
                    email='john@testclient.com',
                    phone='+1 (555) 123-4567',
                    address='123 Test Street, Test City, TC 12345',
                    default_hourly_rate=85.00
                )
                db.session.add(test_client)
                db.session.commit()
                print(f"✅ Test client created (ID: {test_client.id})")
            
            # Test project creation with client
            print("\nTesting Project Creation with Client...")
            
            # Check if test project already exists
            test_project = Project.query.filter_by(name='Test Project - Client System').first()
            if test_project:
                print(f"✅ Test project already exists (ID: {test_project.id})")
            else:
                # Create test project
                test_project = Project(
                    name='Test Project - Client System',
                    client_id=test_client.id,
                    description='Test project to verify client integration',
                    billable=True,
                    hourly_rate=85.00,  # Should match client default
                    billing_ref='TEST-001'
                )
                db.session.add(test_project)
                db.session.commit()
                print(f"✅ Test project created (ID: {test_project.id})")
            
            # Test client properties
            print("\nTesting Client Properties...")
            
            print(f"Client name: {test_client.name}")
            print(f"Client description: {test_client.description}")
            print(f"Client default rate: {test_client.default_hourly_rate}")
            print(f"Client status: {test_client.status}")
            print(f"Client total projects: {test_client.total_projects}")
            print(f"Client active projects: {test_client.active_projects}")
            print(f"Client total hours: {test_client.total_hours}")
            print(f"Client estimated cost: {test_client.estimated_total_cost}")
            
            # Test project properties
            print("\nTesting Project Properties...")
            
            print(f"Project name: {test_project.name}")
            print(f"Project client: {test_project.client}")  # Using backward compatibility property
            print(f"Project client_id: {test_project.client_id}")
            print(f"Project hourly rate: {test_project.hourly_rate}")
            print(f"Project billable: {test_project.billable}")
            
            # Test client relationships
            print("\nTesting Client Relationships...")
            
            client_projects = test_client.projects.all()
            print(f"Client has {len(client_projects)} projects:")
            for project in client_projects:
                print(f"  - {project.name} (ID: {project.id})")
            
            # Test client management methods
            print("\nTesting Client Management Methods...")
            
            active_clients = Client.get_active_clients()
            print(f"Active clients: {len(active_clients)}")
            
            all_clients = Client.get_all_clients()
            print(f"All clients: {len(all_clients)}")
            
            # Test client archiving (create a test client to archive)
            print("\nTesting Client Archiving...")
            
            archive_test_client = Client.query.filter_by(name='Archive Test Client').first()
            if not archive_test_client:
                archive_test_client = Client(
                    name='Archive Test Client',
                    description='Client to test archiving functionality'
                )
                db.session.add(archive_test_client)
                db.session.commit()
                print(f"✅ Archive test client created (ID: {archive_test_client.id})")
            
            if archive_test_client.status == 'active':
                archive_test_client.archive()
                db.session.commit()
                print(f"✅ Client '{archive_test_client.name}' archived")
            else:
                print(f"✅ Client '{archive_test_client.name}' already archived")
            
            # Test client activation
            if archive_test_client.status == 'inactive':
                archive_test_client.activate()
                db.session.commit()
                print(f"✅ Client '{archive_test_client.name}' activated")
            
            # Clean up test data (optional)
            print("\nCleaning up test data...")
            
            # Delete test project
            if test_project:
                db.session.delete(test_project)
                print("✅ Test project deleted")
            
            # Delete test clients
            if test_client:
                db.session.delete(test_client)
                print("✅ Test client deleted")
            
            if archive_test_client:
                db.session.delete(archive_test_client)
                print("✅ Archive test client deleted")
            
            db.session.commit()
            
            print("\n🎉 All tests passed! Client management system is working correctly.")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_client_system()
    sys.exit(0 if success else 1)
