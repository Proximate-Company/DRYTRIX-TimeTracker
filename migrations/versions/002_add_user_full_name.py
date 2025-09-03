"""Add full_name to users

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('full_name', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('users', 'full_name')


