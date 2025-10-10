"""Add project costs table for tracking expenses

Revision ID: 018
Revises: 017
Create Date: 2025-01-15 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def _has_table(inspector, name: str) -> bool:
    """Check if a table exists"""
    try:
        return name in inspector.get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    """Create project_costs table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Determine database dialect for proper default values
    dialect_name = bind.dialect.name
    
    # Set appropriate boolean defaults based on database
    if dialect_name == 'sqlite':
        bool_true_default = '1'
        bool_false_default = '0'
        timestamp_default = "(datetime('now'))"
    elif dialect_name == 'postgresql':
        bool_true_default = 'true'
        bool_false_default = 'false'
        timestamp_default = 'CURRENT_TIMESTAMP'
    else:  # MySQL/MariaDB and others
        bool_true_default = '1'
        bool_false_default = '0'
        timestamp_default = 'CURRENT_TIMESTAMP'
    
    # Create project_costs table if it doesn't exist
    if not _has_table(inspector, 'project_costs'):
        op.create_table(
            'project_costs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('currency_code', sa.String(length=3), nullable=False, server_default='EUR'),
            sa.Column('billable', sa.Boolean(), nullable=False, server_default=sa.text(bool_true_default)),
            sa.Column('invoiced', sa.Boolean(), nullable=False, server_default=sa.text(bool_false_default)),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('cost_date', sa.Date(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('receipt_path', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text(timestamp_default)),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text(timestamp_default)),
        )
        
        # Create indexes
        op.create_index('ix_project_costs_project_id', 'project_costs', ['project_id'])
        op.create_index('ix_project_costs_user_id', 'project_costs', ['user_id'])
        op.create_index('ix_project_costs_cost_date', 'project_costs', ['cost_date'])
        op.create_index('ix_project_costs_invoice_id', 'project_costs', ['invoice_id'])
        
        # Create foreign keys
        op.create_foreign_key(
            'fk_project_costs_project_id',
            'project_costs', 'projects',
            ['project_id'], ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_project_costs_user_id',
            'project_costs', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
        
        # Only create FK to invoices if the table exists
        if _has_table(inspector, 'invoices'):
            op.create_foreign_key(
                'fk_project_costs_invoice_id',
                'project_costs', 'invoices',
                ['invoice_id'], ['id'],
                ondelete='SET NULL'
            )


def downgrade() -> None:
    """Drop project_costs table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if _has_table(inspector, 'project_costs'):
        try:
            op.drop_table('project_costs')
        except Exception:
            pass

