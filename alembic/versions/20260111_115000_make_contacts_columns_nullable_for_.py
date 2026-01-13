"""Make contacts columns nullable for flexible data handling

This migration makes several columns in the contacts table nullable to support
MongoDB-style $exists queries and flexible data handling.

Changes:
- contacts.source_id: DROP NOT NULL
- contacts.webhook_sent: DROP NOT NULL
- contacts.enrichment_status: DROP NOT NULL
- contacts.is_relevant: DROP NOT NULL

Revision ID: a5b7bc1d7b03
Revises: 23991ef76b1b
Create Date: 2026-01-11 11:50:00.913635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b7bc1d7b03'
down_revision: Union[str, None] = '23991ef76b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make contacts columns nullable
    op.alter_column('contacts', 'source_id',
                    existing_type=sa.String(100),
                    nullable=True)
    
    op.alter_column('contacts', 'webhook_sent',
                    existing_type=sa.Boolean(),
                    nullable=True)
    
    op.alter_column('contacts', 'enrichment_status',
                    existing_type=sa.Boolean(),
                    nullable=True)
    
    op.alter_column('contacts', 'is_relevant',
                    existing_type=sa.Boolean(),
                    nullable=True)


def downgrade() -> None:
    # Set defaults for NULL values before adding NOT NULL constraints
    op.execute("UPDATE contacts SET source_id = '' WHERE source_id IS NULL")
    op.execute("UPDATE contacts SET webhook_sent = false WHERE webhook_sent IS NULL")
    op.execute("UPDATE contacts SET enrichment_status = false WHERE enrichment_status IS NULL")
    op.execute("UPDATE contacts SET is_relevant = false WHERE is_relevant IS NULL")
    
    # Restore NOT NULL constraints
    op.alter_column('contacts', 'source_id',
                    existing_type=sa.String(100),
                    nullable=False)
    
    op.alter_column('contacts', 'webhook_sent',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    op.alter_column('contacts', 'enrichment_status',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    op.alter_column('contacts', 'is_relevant',
                    existing_type=sa.Boolean(),
                    nullable=False)


