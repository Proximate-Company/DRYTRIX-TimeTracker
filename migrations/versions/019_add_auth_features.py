"""Add authentication features (passwords, 2FA, tokens)

Revision ID: 019_add_auth_features
Revises: 018_add_multi_tenant_support
Create Date: 2025-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    """Add authentication features"""
    
    # Add password and 2FA fields to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('totp_secret', sa.String(32), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('backup_codes', sa.Text(), nullable=True))
    
    # Make email unique
    try:
        op.create_unique_constraint('uq_users_email', 'users', ['email'])
    except Exception:
        pass  # Constraint may already exist
    
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)
    
    # Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.Column('token', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'])
    op.create_index('ix_email_verification_tokens_token', 'email_verification_tokens', ['token'], unique=True)
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(100), nullable=False),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('device_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_device_id', 'refresh_tokens', ['device_id'])
    op.create_index('idx_refresh_tokens_user_device', 'refresh_tokens', ['user_id', 'device_id'])
    
    # Add Stripe fields to organizations table
    op.add_column('organizations', sa.Column('stripe_customer_id', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('stripe_subscription_id', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('stripe_subscription_status', sa.String(20), nullable=True))
    op.add_column('organizations', sa.Column('stripe_price_id', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('subscription_quantity', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('organizations', sa.Column('trial_ends_at', sa.DateTime(), nullable=True))
    op.add_column('organizations', sa.Column('subscription_ends_at', sa.DateTime(), nullable=True))
    op.add_column('organizations', sa.Column('next_billing_date', sa.DateTime(), nullable=True))
    op.add_column('organizations', sa.Column('billing_issue_detected_at', sa.DateTime(), nullable=True))
    op.add_column('organizations', sa.Column('last_billing_email_sent_at', sa.DateTime(), nullable=True))
    
    try:
        op.create_index('ix_organizations_stripe_customer_id', 'organizations', ['stripe_customer_id'], unique=True)
    except Exception:
        pass  # Index may already exist
    
    # Create subscription_events table for tracking Stripe webhooks
    op.create_table(
        'subscription_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stripe_event_id', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_subscription_events_stripe_event_id', 'subscription_events', ['stripe_event_id'], unique=True)
    op.create_index('idx_subscription_events_org', 'subscription_events', ['organization_id'])
    op.create_index('idx_subscription_events_type', 'subscription_events', ['event_type'])
    op.create_index('idx_subscription_events_created', 'subscription_events', ['created_at'])


def downgrade():
    """Remove authentication features"""
    
    # Drop subscription_events table
    op.drop_index('idx_subscription_events_created', table_name='subscription_events')
    op.drop_index('idx_subscription_events_type', table_name='subscription_events')
    op.drop_index('idx_subscription_events_org', table_name='subscription_events')
    op.drop_index('ix_subscription_events_stripe_event_id', table_name='subscription_events')
    op.drop_table('subscription_events')
    
    # Drop Stripe fields from organizations
    op.drop_column('organizations', 'last_billing_email_sent_at')
    op.drop_column('organizations', 'billing_issue_detected_at')
    op.drop_column('organizations', 'next_billing_date')
    op.drop_column('organizations', 'subscription_ends_at')
    op.drop_column('organizations', 'trial_ends_at')
    op.drop_column('organizations', 'subscription_quantity')
    op.drop_column('organizations', 'stripe_price_id')
    op.drop_column('organizations', 'stripe_subscription_status')
    op.drop_column('organizations', 'stripe_subscription_id')
    op.drop_column('organizations', 'stripe_customer_id')
    
    # Drop refresh_tokens table
    op.drop_index('idx_refresh_tokens_user_device', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_device_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    
    # Drop email_verification_tokens table
    op.drop_index('ix_email_verification_tokens_token', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_user_id', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    
    # Drop password_reset_tokens table
    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    
    # Remove email unique constraint
    try:
        op.drop_constraint('uq_users_email', 'users', type_='unique')
    except Exception:
        pass
    
    # Remove password and 2FA fields from users
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'password_hash')

