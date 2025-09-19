"""add payment status tracking to invoices

Revision ID: 014
Revises: 013
Create Date: 2025-09-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if invoices table exists
    if 'invoices' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('invoices')]
        
        # Add payment tracking columns to invoices table if they don't exist
        if 'payment_date' not in existing_columns:
            op.add_column('invoices', sa.Column('payment_date', sa.Date(), nullable=True))
        
        if 'payment_method' not in existing_columns:
            op.add_column('invoices', sa.Column('payment_method', sa.String(50), nullable=True))
        
        if 'payment_reference' not in existing_columns:
            op.add_column('invoices', sa.Column('payment_reference', sa.String(100), nullable=True))
        
        if 'payment_notes' not in existing_columns:
            op.add_column('invoices', sa.Column('payment_notes', sa.Text(), nullable=True))
        
        if 'amount_paid' not in existing_columns:
            # Add the column as nullable first
            op.add_column('invoices', sa.Column('amount_paid', sa.Numeric(10, 2), nullable=True))
            
            # Update existing records to have 0 as default amount_paid
            bind = op.get_bind()
            bind.execute(sa.text("UPDATE invoices SET amount_paid = 0 WHERE amount_paid IS NULL"))
        
        if 'payment_status' not in existing_columns:
            # Add the column as nullable first
            op.add_column('invoices', sa.Column('payment_status', sa.String(20), nullable=True))
            
            # Update existing records based on their current status
            bind = op.get_bind()
            # Set payment status based on existing invoice status
            bind.execute(sa.text("""
                UPDATE invoices SET payment_status = CASE 
                    WHEN status = 'paid' THEN 'fully_paid'
                    ELSE 'unpaid'
                END 
                WHERE payment_status IS NULL
            """))
            
            # For invoices marked as 'paid', also set amount_paid to total_amount
            bind.execute(sa.text("""
                UPDATE invoices SET amount_paid = total_amount, payment_date = CURRENT_DATE 
                WHERE status = 'paid' AND amount_paid = 0
            """))
            
            # Now make the column NOT NULL
            op.alter_column('invoices', 'payment_status', nullable=False)
        
        # Create indexes for better performance
        try:
            op.create_index('ix_invoices_payment_date', 'invoices', ['payment_date'], unique=False)
        except:
            pass  # Index might already exist
        
        try:
            op.create_index('ix_invoices_payment_status', 'invoices', ['payment_status'], unique=False)
        except:
            pass  # Index might already exist


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if invoices table exists
    if 'invoices' in inspector.get_table_names():
        try:
            # Drop indexes first
            op.drop_index('ix_invoices_payment_status', table_name='invoices')
            op.drop_index('ix_invoices_payment_date', table_name='invoices')
        except:
            pass  # Indexes might not exist
        
        existing_columns = [col['name'] for col in inspector.get_columns('invoices')]
        
        # Remove payment tracking columns if they exist
        if 'payment_status' in existing_columns:
            op.drop_column('invoices', 'payment_status')
        
        if 'amount_paid' in existing_columns:
            op.drop_column('invoices', 'amount_paid')
        
        if 'payment_notes' in existing_columns:
            op.drop_column('invoices', 'payment_notes')
        
        if 'payment_reference' in existing_columns:
            op.drop_column('invoices', 'payment_reference')
        
        if 'payment_method' in existing_columns:
            op.drop_column('invoices', 'payment_method')
        
        if 'payment_date' in existing_columns:
            op.drop_column('invoices', 'payment_date')
