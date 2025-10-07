"""Add onboarding checklist table

Revision ID: 020_add_onboarding_checklist
Revises: 019_add_auth_features
Create Date: 2025-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    """Create onboarding_checklists table."""
    op.create_table(
        'onboarding_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        
        # Task completion flags
        sa.Column('invited_team_member', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('invited_team_member_at', sa.DateTime(), nullable=True),
        
        sa.Column('created_project', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_project_at', sa.DateTime(), nullable=True),
        
        sa.Column('created_time_entry', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_time_entry_at', sa.DateTime(), nullable=True),
        
        sa.Column('set_working_hours', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('set_working_hours_at', sa.DateTime(), nullable=True),
        
        sa.Column('customized_settings', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('customized_settings_at', sa.DateTime(), nullable=True),
        
        sa.Column('added_billing_info', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('added_billing_info_at', sa.DateTime(), nullable=True),
        
        sa.Column('created_client', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_client_at', sa.DateTime(), nullable=True),
        
        sa.Column('generated_report', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generated_report_at', sa.DateTime(), nullable=True),
        
        # Overall status
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        # Dismiss/skip tracking
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        
        # Unique constraint - one checklist per organization
        sa.UniqueConstraint('organization_id', name='uq_onboarding_checklist_org'),
    )
    
    # Create indexes
    op.create_index('ix_onboarding_checklists_organization_id', 'onboarding_checklists', ['organization_id'])
    
    print("✅ Created onboarding_checklists table")


def downgrade():
    """Drop onboarding_checklists table."""
    op.drop_index('ix_onboarding_checklists_organization_id', table_name='onboarding_checklists')
    op.drop_table('onboarding_checklists')
    print("❌ Dropped onboarding_checklists table")

