"""Add password security fields to users table

Revision ID: 022
Revises: 021
Create Date: 2025-10-07 21:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    """Add password security fields"""
    # Use connection to check if columns exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Only add columns if the users table exists
    tables = inspector.get_table_names()
    if 'users' not in tables:
        # Table doesn't exist yet, skip (will be created by earlier migrations)
        return
    
    existing_columns = {col['name'] for col in inspector.get_columns('users')}
    
    # Add each column only if it doesn't exist
    if 'password_changed_at' not in existing_columns:
        op.add_column('users', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    
    if 'password_history' not in existing_columns:
        op.add_column('users', sa.Column('password_history', sa.Text(), nullable=True))
    
    if 'failed_login_attempts' not in existing_columns:
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default=sa.text('0')))
    
    if 'account_locked_until' not in existing_columns:
        op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True))


def downgrade():
    """Remove password security fields"""
    # Check if columns exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    tables = inspector.get_table_names()
    if 'users' not in tables:
        return
    
    existing_columns = {col['name'] for col in inspector.get_columns('users')}
    
    if 'account_locked_until' in existing_columns:
        op.drop_column('users', 'account_locked_until')
    
    if 'failed_login_attempts' in existing_columns:
        op.drop_column('users', 'failed_login_attempts')
    
    if 'password_history' in existing_columns:
        op.drop_column('users', 'password_history')
    
    if 'password_changed_at' in existing_columns:
        op.drop_column('users', 'password_changed_at')

