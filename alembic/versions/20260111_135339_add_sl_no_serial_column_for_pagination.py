"""add_sl_no_serial_column_for_pagination

Revision ID: add_sl_no_pagination
Revises: make_contacts_columns_nullable
Create Date: 2026-01-11 13:53:39

This migration adds sl_no (serial number) column to all tables for efficient pagination.
sl_no is a BIGSERIAL auto-increment column that provides:
- Stable ordering for pagination (no duplicates/gaps between pages)
- Efficient keyset pagination (WHERE sl_no > last_seen)
- Better performance than OFFSET on large datasets (1M+ rows)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sl_no_pagination'
down_revision: Union[str, None] = 'a5b7bc1d7b03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All tables that need sl_no column
TABLES = [
    'users',
    'user_tokens', 
    'campaigns',
    'companies',
    'contacts',
    'campaign_company_runs',
    'campaign_contact_runs',
    'meetings',
    'inbox_leads',
    'inbox_events',
    'inbox_notes',
]


def upgrade() -> None:
    """Add sl_no BIGSERIAL column to all tables."""
    for table in TABLES:
        # Create a sequence for each table
        seq_name = f'{table}_sl_no_seq'
        op.execute(f'CREATE SEQUENCE IF NOT EXISTS {seq_name}')
        
        # Add sl_no column with BIGINT type
        op.add_column(
            table,
            sa.Column('sl_no', sa.BigInteger(), nullable=True)
        )
        
        # Populate existing rows with sequential values
        op.execute(f'''
            UPDATE {table} 
            SET sl_no = nextval('{seq_name}')
            WHERE sl_no IS NULL
        ''')
        
        # Make column NOT NULL after populating
        op.alter_column(table, 'sl_no', nullable=False)
        
        # Set default value to use the sequence
        op.execute(f"ALTER TABLE {table} ALTER COLUMN sl_no SET DEFAULT nextval('{seq_name}')")
        
        # Make sequence owned by the column (for cleanup on column drop)
        op.execute(f"ALTER SEQUENCE {seq_name} OWNED BY {table}.sl_no")
        
        # Add unique constraint
        op.create_unique_constraint(f'uq_{table}_sl_no', table, ['sl_no'])
        
        # Add index for efficient sorting
        op.create_index(f'ix_{table}_sl_no', table, ['sl_no'])
        
        print(f"✅ Added sl_no to {table}")


def downgrade() -> None:
    """Remove sl_no column from all tables."""
    for table in TABLES:
        # Drop index
        op.drop_index(f'ix_{table}_sl_no', table_name=table)
        
        # Drop unique constraint
        op.drop_constraint(f'uq_{table}_sl_no', table, type_='unique')
        
        # Drop column (sequence will be dropped automatically due to OWNED BY)
        op.drop_column(table, 'sl_no')
        
        print(f"❌ Removed sl_no from {table}")
