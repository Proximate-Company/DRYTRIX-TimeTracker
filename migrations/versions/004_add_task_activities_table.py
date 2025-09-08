"""add task_activities table

Revision ID: 004
Revises: 003
Create Date: 2025-09-07 10:35:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'task_activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('event', sa.String(length=50), nullable=False, index=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Explicit indexes (in addition to inline index=True for portability)
    op.create_index('idx_task_activities_task_id', 'task_activities', ['task_id'])
    op.create_index('idx_task_activities_user_id', 'task_activities', ['user_id'])
    op.create_index('idx_task_activities_event', 'task_activities', ['event'])
    op.create_index('idx_task_activities_created_at', 'task_activities', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_task_activities_created_at', table_name='task_activities')
    op.drop_index('idx_task_activities_event', table_name='task_activities')
    op.drop_index('idx_task_activities_user_id', table_name='task_activities')
    op.drop_index('idx_task_activities_task_id', table_name='task_activities')
    op.drop_table('task_activities')


