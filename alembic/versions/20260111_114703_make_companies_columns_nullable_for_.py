"""Make companies columns nullable for flexible data handling

This migration makes several columns in the companies table nullable to handle
cases where data might not be available from all sources.

Changes:
- companies.source_id: DROP NOT NULL
- companies.source_domain: DROP NOT NULL
- companies.primary_domain: DROP NOT NULL
- companies.red_flags_history: DROP NOT NULL
- companies.deep_research: DROP NOT NULL

Revision ID: 23991ef76b1b
Revises: a6fe5d7267f3
Create Date: 2026-01-11 11:47:03.908293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '23991ef76b1b'
down_revision: Union[str, None] = 'a6fe5d7267f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make companies columns nullable
    op.alter_column('companies', 'source_id',
                    existing_type=sa.String(100),
                    nullable=True)
    
    op.alter_column('companies', 'source_domain',
                    existing_type=sa.String(255),
                    nullable=True)
    
    op.alter_column('companies', 'primary_domain',
                    existing_type=sa.String(255),
                    nullable=True)
    
    op.alter_column('companies', 'red_flags_history',
                    existing_type=JSONB(),
                    nullable=True)
    
    op.alter_column('companies', 'deep_research',
                    existing_type=JSONB(),
                    nullable=True)


def downgrade() -> None:
    # Set defaults for NULL values before adding NOT NULL constraints
    op.execute("UPDATE companies SET source_id = '' WHERE source_id IS NULL")
    op.execute("UPDATE companies SET source_domain = '' WHERE source_domain IS NULL")
    op.execute("UPDATE companies SET primary_domain = '' WHERE primary_domain IS NULL")
    op.execute("UPDATE companies SET red_flags_history = '[]'::jsonb WHERE red_flags_history IS NULL")
    op.execute("UPDATE companies SET deep_research = '{}'::jsonb WHERE deep_research IS NULL")
    
    # Restore NOT NULL constraints
    op.alter_column('companies', 'source_id',
                    existing_type=sa.String(100),
                    nullable=False)
    
    op.alter_column('companies', 'source_domain',
                    existing_type=sa.String(255),
                    nullable=False)
    
    op.alter_column('companies', 'primary_domain',
                    existing_type=sa.String(255),
                    nullable=False)
    
    op.alter_column('companies', 'red_flags_history',
                    existing_type=JSONB(),
                    nullable=False)
    
    op.alter_column('companies', 'deep_research',
                    existing_type=JSONB(),
                    nullable=False)


