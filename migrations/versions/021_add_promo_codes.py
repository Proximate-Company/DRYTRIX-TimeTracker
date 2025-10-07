"""Add promo codes support

Revision ID: 021_add_promo_codes
Revises: 020
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    # Create promo_codes table
    op.create_table('promo_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=False, server_default='percent'),
        sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('duration', sa.String(length=20), nullable=False, server_default='once'),
        sa.Column('duration_in_months', sa.Integer(), nullable=True),
        sa.Column('max_redemptions', sa.Integer(), nullable=True),
        sa.Column('times_redeemed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_from', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('stripe_coupon_id', sa.String(length=100), nullable=True),
        sa.Column('stripe_promotion_code_id', sa.String(length=100), nullable=True),
        sa.Column('first_time_only', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('min_seats', sa.Integer(), nullable=True),
        sa.Column('max_seats', sa.Integer(), nullable=True),
        sa.Column('plan_restrictions', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_promo_codes_active', 'promo_codes', ['is_active'])
    op.create_index('idx_promo_codes_code', 'promo_codes', ['code'])
    
    # Create promo_code_redemptions table
    op.create_table('promo_code_redemptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('redeemed_by', sa.Integer(), nullable=True),
        sa.Column('redeemed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ),
        sa.ForeignKeyConstraint(['redeemed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_redemptions_org', 'promo_code_redemptions', ['organization_id'])
    op.create_index('idx_redemptions_promo_code', 'promo_code_redemptions', ['promo_code_id'])
    
    # Add promo code columns to organizations table
    op.add_column('organizations', sa.Column('promo_code', sa.String(length=50), nullable=True))
    op.add_column('organizations', sa.Column('promo_code_applied_at', sa.DateTime(), nullable=True))
    
    # Insert early adopter promo code
    op.execute("""
        INSERT INTO promo_codes (
            code, description, discount_type, discount_value, 
            duration, duration_in_months, is_active, first_time_only,
            valid_from, valid_until
        ) VALUES (
            'EARLY2025', 
            'Early Adopter Discount - 20% off for 3 months',
            'percent',
            20.00,
            'repeating',
            3,
            true,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP + INTERVAL '6 months'
        )
    """)


def downgrade():
    # Drop columns from organizations table
    op.drop_column('organizations', 'promo_code_applied_at')
    op.drop_column('organizations', 'promo_code')
    
    op.drop_index('idx_redemptions_promo_code', table_name='promo_code_redemptions')
    op.drop_index('idx_redemptions_org', table_name='promo_code_redemptions')
    op.drop_table('promo_code_redemptions')
    op.drop_index('idx_promo_codes_code', table_name='promo_codes')
    op.drop_index('idx_promo_codes_active', table_name='promo_codes')
    op.drop_table('promo_codes')

