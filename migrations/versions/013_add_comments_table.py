"""add comments table for project and task discussions

Revision ID: 013
Revises: 012
Create Date: 2025-09-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if comments table already exists
    if 'comments' not in inspector.get_table_names():
        op.create_table('comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=True),
            sa.Column('task_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for better performance
        op.create_index('ix_comments_project_id', 'comments', ['project_id'], unique=False)
        op.create_index('ix_comments_task_id', 'comments', ['task_id'], unique=False)
        op.create_index('ix_comments_user_id', 'comments', ['user_id'], unique=False)
        op.create_index('ix_comments_parent_id', 'comments', ['parent_id'], unique=False)
        op.create_index('ix_comments_created_at', 'comments', ['created_at'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if comments table exists before trying to drop it
    if 'comments' in inspector.get_table_names():
        try:
            # Drop indexes first
            op.drop_index('ix_comments_created_at', table_name='comments')
            op.drop_index('ix_comments_parent_id', table_name='comments')
            op.drop_index('ix_comments_user_id', table_name='comments')
            op.drop_index('ix_comments_task_id', table_name='comments')
            op.drop_index('ix_comments_project_id', table_name='comments')
            
            # Drop the table
            op.drop_table('comments')
        except Exception:
            # If dropping fails, just pass
            pass
