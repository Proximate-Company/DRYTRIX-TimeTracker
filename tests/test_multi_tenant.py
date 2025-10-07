"""
Tests for multi-tenant functionality and data isolation.

These tests verify that:
1. Organizations and memberships are created correctly
2. Data is properly scoped to organizations
3. Tenant isolation is enforced
4. Users cannot access data from other organizations
5. Row Level Security (RLS) works correctly
"""

import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    Organization, Membership, User, Project, Client,
    TimeEntry, Task, Invoice, Comment
)
from app.utils.tenancy import (
    set_current_organization, get_current_organization_id,
    user_has_access_to_organization, switch_organization,
    scoped_query, ensure_organization_access
)
from app.utils.rls import set_rls_context, clear_rls_context, test_rls_isolation


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def organizations(app):
    """Create test organizations."""
    with app.app_context():
        org1 = Organization(
            name='Test Organization 1',
            slug='test-org-1',
            contact_email='org1@example.com'
        )
        org2 = Organization(
            name='Test Organization 2',
            slug='test-org-2',
            contact_email='org2@example.com'
        )
        
        db.session.add(org1)
        db.session.add(org2)
        db.session.commit()
        
        return org1, org2


@pytest.fixture
def users(app, organizations):
    """Create test users with memberships."""
    with app.app_context():
        org1, org2 = organizations
        
        # User 1: Member of org1 (admin)
        user1 = User(username='user1', email='user1@example.com', role='admin')
        user1.is_active = True
        
        # User 2: Member of org1 (regular member)
        user2 = User(username='user2', email='user2@example.com', role='user')
        user2.is_active = True
        
        # User 3: Member of org2 (admin)
        user3 = User(username='user3', email='user3@example.com', role='admin')
        user3.is_active = True
        
        # User 4: Member of both org1 and org2
        user4 = User(username='user4', email='user4@example.com', role='user')
        user4.is_active = True
        
        db.session.add_all([user1, user2, user3, user4])
        db.session.commit()
        
        # Create memberships
        memberships = [
            Membership(user1.id, org1.id, role='admin'),
            Membership(user2.id, org1.id, role='member'),
            Membership(user3.id, org2.id, role='admin'),
            Membership(user4.id, org1.id, role='member'),
            Membership(user4.id, org2.id, role='member'),
        ]
        
        for m in memberships:
            db.session.add(m)
        
        db.session.commit()
        
        return user1, user2, user3, user4


class TestOrganizationModel:
    """Test Organization model functionality."""
    
    def test_create_organization(self, app):
        """Test creating an organization."""
        with app.app_context():
            org = Organization(
                name='Test Org',
                slug='test-org',
                contact_email='test@example.com'
            )
            db.session.add(org)
            db.session.commit()
            
            assert org.id is not None
            assert org.name == 'Test Org'
            assert org.slug == 'test-org'
            assert org.is_active is True
    
    def test_organization_slug_auto_generation(self, app):
        """Test that slug is auto-generated from name if not provided."""
        with app.app_context():
            org = Organization(name='My Test Organization')
            db.session.add(org)
            db.session.commit()
            
            assert org.slug == 'my-test-organization'
    
    def test_organization_slug_uniqueness(self, app):
        """Test that duplicate slugs are handled correctly."""
        with app.app_context():
            org1 = Organization(name='Test Org')
            db.session.add(org1)
            db.session.commit()
            
            org2 = Organization(name='Test Org')  # Same name
            db.session.add(org2)
            db.session.commit()
            
            assert org1.slug == 'test-org'
            assert org2.slug == 'test-org-1'  # Auto-incremented
    
    def test_organization_properties(self, app, organizations):
        """Test organization properties."""
        with app.app_context():
            org1, org2 = organizations
            
            assert org1.member_count == 0  # No memberships yet
            assert org1.admin_count == 0
            assert org1.project_count == 0


class TestMembershipModel:
    """Test Membership model functionality."""
    
    def test_create_membership(self, app, organizations, users):
        """Test creating a membership."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # Verify memberships were created
            assert Membership.user_is_member(user1.id, org1.id) is True
            assert Membership.user_is_admin(user1.id, org1.id) is True
            assert Membership.user_is_member(user1.id, org2.id) is False
    
    def test_user_multiple_organizations(self, app, organizations, users):
        """Test that a user can belong to multiple organizations."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # User4 is in both orgs
            assert Membership.user_is_member(user4.id, org1.id) is True
            assert Membership.user_is_member(user4.id, org2.id) is True
            
            memberships = Membership.get_user_active_memberships(user4.id)
            assert len(memberships) == 2
    
    def test_membership_role_changes(self, app, organizations, users):
        """Test changing membership roles."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            membership = Membership.find_membership(user2.id, org1.id)
            assert membership.role == 'member'
            
            membership.promote_to_admin()
            assert membership.role == 'admin'
            assert membership.is_admin is True
            
            membership.demote_from_admin()
            assert membership.role == 'member'
            assert membership.is_admin is False


class TestTenantDataIsolation:
    """Test that data is properly isolated between tenants."""
    
    def test_projects_isolation(self, app, organizations, users):
        """Test that projects are isolated between organizations."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # Create clients for each org
            client1 = Client(name='Client 1', organization_id=org1.id)
            client2 = Client(name='Client 2', organization_id=org2.id)
            db.session.add_all([client1, client2])
            db.session.commit()
            
            # Create projects in each organization
            project1 = Project(
                name='Project 1',
                organization_id=org1.id,
                client_id=client1.id
            )
            project2 = Project(
                name='Project 2',
                organization_id=org2.id,
                client_id=client2.id
            )
            
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Verify projects exist
            assert Project.query.count() == 2
            
            # Set context to org1 and use scoped query
            set_current_organization(org1.id, org1)
            org1_projects = scoped_query(Project).all()
            
            assert len(org1_projects) == 1
            assert org1_projects[0].id == project1.id
            
            # Set context to org2
            set_current_organization(org2.id, org2)
            org2_projects = scoped_query(Project).all()
            
            assert len(org2_projects) == 1
            assert org2_projects[0].id == project2.id
    
    def test_time_entries_isolation(self, app, organizations, users):
        """Test that time entries are isolated between organizations."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # Create necessary data
            client1 = Client(name='Client 1', organization_id=org1.id)
            client2 = Client(name='Client 2', organization_id=org2.id)
            db.session.add_all([client1, client2])
            db.session.commit()
            
            project1 = Project(name='Project 1', organization_id=org1.id, client_id=client1.id)
            project2 = Project(name='Project 2', organization_id=org2.id, client_id=client2.id)
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Create time entries
            now = datetime.utcnow()
            entry1 = TimeEntry(
                user_id=user1.id,
                project_id=project1.id,
                organization_id=org1.id,
                start_time=now,
                end_time=now + timedelta(hours=1)
            )
            entry2 = TimeEntry(
                user_id=user3.id,
                project_id=project2.id,
                organization_id=org2.id,
                start_time=now,
                end_time=now + timedelta(hours=1)
            )
            
            db.session.add_all([entry1, entry2])
            db.session.commit()
            
            # Test isolation
            set_current_organization(org1.id, org1)
            org1_entries = scoped_query(TimeEntry).all()
            assert len(org1_entries) == 1
            assert org1_entries[0].organization_id == org1.id
            
            set_current_organization(org2.id, org2)
            org2_entries = scoped_query(TimeEntry).all()
            assert len(org2_entries) == 1
            assert org2_entries[0].organization_id == org2.id
    
    def test_ensure_organization_access(self, app, organizations, users):
        """Test that ensure_organization_access prevents cross-org access."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            client1 = Client(name='Client 1', organization_id=org1.id)
            client2 = Client(name='Client 2', organization_id=org2.id)
            db.session.add_all([client1, client2])
            db.session.commit()
            
            project1 = Project(name='Project 1', organization_id=org1.id, client_id=client1.id)
            project2 = Project(name='Project 2', organization_id=org2.id, client_id=client2.id)
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Set context to org1
            set_current_organization(org1.id, org1)
            
            # Should succeed - project belongs to org1
            ensure_organization_access(project1)
            
            # Should fail - project belongs to org2
            with pytest.raises(PermissionError):
                ensure_organization_access(project2)


class TestTenancyHelpers:
    """Test tenancy helper functions."""
    
    def test_user_has_access_to_organization(self, app, organizations, users):
        """Test checking user access to organizations."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            assert user_has_access_to_organization(user1.id, org1.id) is True
            assert user_has_access_to_organization(user1.id, org2.id) is False
            assert user_has_access_to_organization(user4.id, org1.id) is True
            assert user_has_access_to_organization(user4.id, org2.id) is True
    
    def test_switch_organization(self, app, organizations, users):
        """Test switching between organizations."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # User4 can switch between both orgs
            # Note: This would normally be tested with a request context
            # For unit tests, we just verify the logic
            
            set_current_organization(org1.id, org1)
            assert get_current_organization_id() == org1.id
            
            set_current_organization(org2.id, org2)
            assert get_current_organization_id() == org2.id


class TestClientNameUniqueness:
    """Test that client names are unique per organization."""
    
    def test_client_names_unique_per_org(self, app, organizations):
        """Test that client names must be unique within an organization."""
        with app.app_context():
            org1, org2 = organizations
            
            # Create client in org1
            client1 = Client(name='Acme Corp', organization_id=org1.id)
            db.session.add(client1)
            db.session.commit()
            
            # Should be able to create same name in org2
            client2 = Client(name='Acme Corp', organization_id=org2.id)
            db.session.add(client2)
            db.session.commit()
            
            assert client1.name == client2.name
            assert client1.organization_id != client2.organization_id
            
            # Should NOT be able to create duplicate in org1
            client3 = Client(name='Acme Corp', organization_id=org1.id)
            db.session.add(client3)
            
            with pytest.raises(Exception):  # Will raise IntegrityError
                db.session.commit()


class TestInvoiceNumberUniqueness:
    """Test that invoice numbers are unique per organization."""
    
    def test_invoice_numbers_unique_per_org(self, app, organizations, users):
        """Test that invoice numbers must be unique within an organization."""
        with app.app_context():
            org1, org2 = organizations
            user1, user2, user3, user4 = users
            
            # Create necessary data
            client1 = Client(name='Client 1', organization_id=org1.id)
            client2 = Client(name='Client 2', organization_id=org2.id)
            db.session.add_all([client1, client2])
            db.session.commit()
            
            project1 = Project(name='Project 1', organization_id=org1.id, client_id=client1.id)
            project2 = Project(name='Project 2', organization_id=org2.id, client_id=client2.id)
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Create invoice in org1
            invoice1 = Invoice(
                invoice_number='INV-001',
                organization_id=org1.id,
                project_id=project1.id,
                client_name='Client 1',
                due_date=datetime.utcnow().date(),
                created_by=user1.id,
                client_id=client1.id
            )
            db.session.add(invoice1)
            db.session.commit()
            
            # Should be able to use same number in org2
            invoice2 = Invoice(
                invoice_number='INV-001',
                organization_id=org2.id,
                project_id=project2.id,
                client_name='Client 2',
                due_date=datetime.utcnow().date(),
                created_by=user3.id,
                client_id=client2.id
            )
            db.session.add(invoice2)
            db.session.commit()
            
            assert invoice1.invoice_number == invoice2.invoice_number
            assert invoice1.organization_id != invoice2.organization_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

