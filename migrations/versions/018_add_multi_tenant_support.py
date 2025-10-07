"""add multi-tenant support with organizations and memberships

Revision ID: 018
Revises: 017
Create Date: 2025-10-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add multi-tenant support with organizations and memberships.
    
    This migration:
    1. Creates organizations table
    2. Creates memberships table
    3. Creates a default organization
    4. Adds organization_id to all tenant-scoped tables
    5. Migrates existing data to the default organization
    6. Creates memberships for all existing users
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # ========================================
    # Step 1: Create organizations table
    # ========================================
    if 'organizations' not in existing_tables:
        print("Creating organizations table...")
        op.create_table('organizations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('contact_email', sa.String(length=200), nullable=True),
            sa.Column('contact_phone', sa.String(length=50), nullable=True),
            sa.Column('billing_email', sa.String(length=200), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
            sa.Column('subscription_plan', sa.String(length=50), nullable=False, server_default='free'),
            sa.Column('max_users', sa.Integer(), nullable=True),
            sa.Column('max_projects', sa.Integer(), nullable=True),
            sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
            sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
            sa.Column('date_format', sa.String(length=20), nullable=False, server_default='YYYY-MM-DD'),
            sa.Column('logo_filename', sa.String(length=255), nullable=True),
            sa.Column('primary_color', sa.String(length=7), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('slug', name='uq_organizations_slug')
        )
        
        # Create indexes
        op.create_index('ix_organizations_name', 'organizations', ['name'])
        op.create_index('ix_organizations_slug', 'organizations', ['slug'])
        op.create_index('ix_organizations_status', 'organizations', ['status'])
    
    # ========================================
    # Step 2: Create default organization
    # ========================================
    print("Creating default organization...")
    result = bind.execute(text("""
        INSERT INTO organizations (name, slug, status, subscription_plan, timezone, currency, created_at, updated_at)
        VALUES ('Default Organization', 'default', 'active', 'enterprise', 'UTC', 'EUR', :now, :now)
        RETURNING id
    """), {"now": datetime.utcnow()})
    
    default_org_id = result.scalar()
    print(f"Created default organization with ID: {default_org_id}")
    
    # ========================================
    # Step 3: Create memberships table
    # ========================================
    if 'memberships' not in existing_tables:
        print("Creating memberships table...")
        op.create_table('memberships',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
            sa.Column('invited_by', sa.Integer(), nullable=True),
            sa.Column('invited_at', sa.DateTime(), nullable=True),
            sa.Column('invitation_token', sa.String(length=100), nullable=True),
            sa.Column('invitation_accepted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('last_activity_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'organization_id', 'status', name='uq_user_org_status')
        )
        
        # Create indexes
        op.create_index('ix_memberships_user_id', 'memberships', ['user_id'])
        op.create_index('ix_memberships_organization_id', 'memberships', ['organization_id'])
        op.create_index('ix_memberships_invitation_token', 'memberships', ['invitation_token'])
        op.create_index('idx_memberships_user_org', 'memberships', ['user_id', 'organization_id'])
        op.create_index('idx_memberships_org_role', 'memberships', ['organization_id', 'role'])
    
    # ========================================
    # Step 4: Create memberships for all existing users
    # ========================================
    print("Creating memberships for existing users...")
    bind.execute(text("""
        INSERT INTO memberships (user_id, organization_id, role, status, created_at, updated_at)
        SELECT 
            id, 
            :org_id,
            CASE WHEN role = 'admin' THEN 'admin' ELSE 'member' END,
            'active',
            :now,
            :now
        FROM users
        WHERE NOT EXISTS (
            SELECT 1 FROM memberships 
            WHERE memberships.user_id = users.id 
            AND memberships.organization_id = :org_id
        )
    """), {"org_id": default_org_id, "now": datetime.utcnow()})
    
    # ========================================
    # Step 5: Add organization_id to all tables
    # ========================================
    
    tables_to_update = [
        'projects',
        'clients',
        'time_entries',
        'tasks',
        'invoices',
        'comments',
        'focus_sessions',
        'saved_filters',
        'task_activities'
    ]
    
    for table_name in tables_to_update:
        if table_name not in existing_tables:
            print(f"Table {table_name} does not exist, skipping...")
            continue
        
        # Check if organization_id column already exists
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'organization_id' in columns:
            print(f"Column organization_id already exists in {table_name}, skipping...")
            continue
        
        print(f"Adding organization_id to {table_name}...")
        
        # Add the column as nullable first
        op.add_column(table_name, 
            sa.Column('organization_id', sa.Integer(), nullable=True)
        )
        
        # Populate with default organization
        bind.execute(text(f"""
            UPDATE {table_name}
            SET organization_id = :org_id
            WHERE organization_id IS NULL
        """), {"org_id": default_org_id})
        
        # Make it non-nullable
        op.alter_column(table_name, 'organization_id', nullable=False)
        
        # Add foreign key constraint
        op.create_foreign_key(
            f'fk_{table_name}_organization_id',
            table_name, 'organizations',
            ['organization_id'], ['id'],
            ondelete='CASCADE'
        )
        
        # Create index
        op.create_index(f'ix_{table_name}_organization_id', table_name, ['organization_id'])
    
    # ========================================
    # Step 6: Create composite indexes for common queries
    # ========================================
    print("Creating composite indexes...")
    
    def safe_create_index(index_name, table_name, columns):
        """Safely create an index, ignoring if it already exists."""
        try:
            # Check if index already exists
            result = bind.execute(text(f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = :index_name
            """), {"index_name": index_name})
            
            if result.scalar():
                print(f"  Index {index_name} already exists, skipping...")
                return
            
            op.create_index(index_name, table_name, columns)
            print(f"  Created index {index_name}")
        except Exception as e:
            print(f"  Warning: Could not create index {index_name}: {e}")
    
    def safe_drop_constraint(constraint_name, table_name, type_='unique'):
        """Safely drop a constraint, ignoring if it doesn't exist."""
        try:
            # Check if constraint exists
            result = bind.execute(text("""
                SELECT 1 FROM pg_constraint 
                WHERE conname = :constraint_name
            """), {"constraint_name": constraint_name})
            
            if not result.scalar():
                print(f"  Constraint {constraint_name} doesn't exist, skipping...")
                return
            
            op.drop_constraint(constraint_name, table_name, type_=type_)
            print(f"  Dropped constraint {constraint_name}")
        except Exception as e:
            print(f"  Warning: Could not drop constraint {constraint_name}: {e}")
    
    def safe_create_constraint(constraint_name, table_name, columns, type_='unique'):
        """Safely create a constraint, ignoring if it already exists."""
        try:
            # Check if constraint already exists
            result = bind.execute(text("""
                SELECT 1 FROM pg_constraint 
                WHERE conname = :constraint_name
            """), {"constraint_name": constraint_name})
            
            if result.scalar():
                print(f"  Constraint {constraint_name} already exists, skipping...")
                return
            
            if type_ == 'unique':
                op.create_unique_constraint(constraint_name, table_name, columns)
            print(f"  Created constraint {constraint_name}")
        except Exception as e:
            print(f"  Warning: Could not create constraint {constraint_name}: {e}")
    
    # Projects
    if 'projects' in existing_tables:
        print("  Creating indexes for projects...")
        safe_create_index('idx_projects_org_status', 'projects', ['organization_id', 'status'])
        safe_create_index('idx_projects_org_client', 'projects', ['organization_id', 'client_id'])
    
    # Clients - Update unique constraint to be per-organization
    if 'clients' in existing_tables:
        print("  Updating constraints for clients...")
        safe_drop_constraint('clients_name_key', 'clients', type_='unique')
        safe_create_constraint('uq_clients_org_name', 'clients', ['organization_id', 'name'], type_='unique')
        safe_create_index('idx_clients_org_status', 'clients', ['organization_id', 'status'])
    
    # Time Entries
    if 'time_entries' in existing_tables:
        print("  Creating indexes for time_entries...")
        safe_create_index('idx_time_entries_org_user', 'time_entries', ['organization_id', 'user_id'])
        safe_create_index('idx_time_entries_org_project', 'time_entries', ['organization_id', 'project_id'])
        safe_create_index('idx_time_entries_org_dates', 'time_entries', ['organization_id', 'start_time', 'end_time'])
    
    # Tasks
    if 'tasks' in existing_tables:
        print("  Creating indexes for tasks...")
        safe_create_index('idx_tasks_org_project', 'tasks', ['organization_id', 'project_id'])
        safe_create_index('idx_tasks_org_status', 'tasks', ['organization_id', 'status'])
        safe_create_index('idx_tasks_org_assigned', 'tasks', ['organization_id', 'assigned_to'])
    
    # Invoices - Update unique constraint to be per-organization
    if 'invoices' in existing_tables:
        print("  Updating constraints for invoices...")
        safe_drop_constraint('invoices_invoice_number_key', 'invoices', type_='unique')
        safe_create_constraint('uq_invoices_org_number', 'invoices', ['organization_id', 'invoice_number'], type_='unique')
        safe_create_index('idx_invoices_org_status', 'invoices', ['organization_id', 'status'])
        safe_create_index('idx_invoices_org_client', 'invoices', ['organization_id', 'client_id'])
    
    # Comments
    if 'comments' in existing_tables:
        print("  Creating indexes for comments...")
        safe_create_index('idx_comments_org_project', 'comments', ['organization_id', 'project_id'])
        safe_create_index('idx_comments_org_task', 'comments', ['organization_id', 'task_id'])
        safe_create_index('idx_comments_org_user', 'comments', ['organization_id', 'user_id'])
    
    print("✅ Multi-tenant migration completed successfully!")


def downgrade() -> None:
    """Remove multi-tenant support.
    
    WARNING: This will remove all organization and membership data!
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    print("⚠️  WARNING: Downgrading multi-tenant support will remove organization data!")
    
    # Remove organization_id from all tables
    tables_to_update = [
        'projects',
        'clients',
        'time_entries',
        'tasks',
        'invoices',
        'comments',
        'focus_sessions',
        'saved_filters',
        'task_activities'
    ]
    
    for table_name in tables_to_update:
        if table_name not in existing_tables:
            continue
        
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'organization_id' not in columns:
            continue
        
        print(f"Removing organization_id from {table_name}...")
        
        # Drop indexes
        try:
            op.drop_index(f'ix_{table_name}_organization_id', table_name=table_name)
        except Exception:
            pass
        
        # Drop foreign key
        try:
            op.drop_constraint(f'fk_{table_name}_organization_id', table_name, type_='foreignkey')
        except Exception:
            pass
        
        # Drop column
        op.drop_column(table_name, 'organization_id')
    
    # Drop composite indexes
    print("Dropping composite indexes...")
    try:
        if 'projects' in existing_tables:
            op.drop_index('idx_projects_org_status', table_name='projects')
            op.drop_index('idx_projects_org_client', table_name='projects')
        
        if 'clients' in existing_tables:
            op.drop_constraint('uq_clients_org_name', 'clients', type_='unique')
            op.drop_index('idx_clients_org_status', table_name='clients')
            # Recreate old unique constraint
            op.create_unique_constraint('clients_name_key', 'clients', ['name'])
        
        if 'time_entries' in existing_tables:
            op.drop_index('idx_time_entries_org_user', table_name='time_entries')
            op.drop_index('idx_time_entries_org_project', table_name='time_entries')
            op.drop_index('idx_time_entries_org_dates', table_name='time_entries')
        
        if 'tasks' in existing_tables:
            op.drop_index('idx_tasks_org_project', table_name='tasks')
            op.drop_index('idx_tasks_org_status', table_name='tasks')
            op.drop_index('idx_tasks_org_assigned', table_name='tasks')
        
        if 'invoices' in existing_tables:
            op.drop_constraint('uq_invoices_org_number', 'invoices', type_='unique')
            op.drop_index('idx_invoices_org_status', table_name='invoices')
            op.drop_index('idx_invoices_org_client', table_name='invoices')
            # Recreate old unique constraint
            op.create_unique_constraint('invoices_invoice_number_key', 'invoices', ['invoice_number'])
        
        if 'comments' in existing_tables:
            op.drop_index('idx_comments_org_project', table_name='comments')
            op.drop_index('idx_comments_org_task', table_name='comments')
            op.drop_index('idx_comments_org_user', table_name='comments')
    except Exception as e:
        print(f"Error dropping indexes: {e}")
    
    # Drop memberships table
    if 'memberships' in existing_tables:
        print("Dropping memberships table...")
        op.drop_table('memberships')
    
    # Drop organizations table
    if 'organizations' in existing_tables:
        print("Dropping organizations table...")
        op.drop_table('organizations')
    
    print("✅ Multi-tenant downgrade completed!")

