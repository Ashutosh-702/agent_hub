"""Make status columns nullable for exists query compatibility

This migration makes several status columns nullable to support MongoDB-style
$exists: False queries which translate to IS NULL in PostgreSQL.

Changes:
- campaign_company_runs.sync_to_hubspot_status: DROP NOT NULL
- campaign_contact_runs.enrichment_status: DROP NOT NULL  
- campaign_contact_runs.personalization_status: DROP NOT NULL

Revision ID: a6fe5d7267f3
Revises: 635ab6ee7464
Create Date: 2026-01-11 11:17:19.663480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6fe5d7267f3'
down_revision: Union[str, None] = '635ab6ee7464'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make sync_to_hubspot_status nullable in campaign_company_runs
    op.alter_column('campaign_company_runs', 'sync_to_hubspot_status',
                    existing_type=sa.String(50),
                    nullable=True)
    
    # Make enrichment_status nullable in campaign_contact_runs
    op.alter_column('campaign_contact_runs', 'enrichment_status',
                    existing_type=sa.Boolean(),
                    nullable=True)
    
    # Make personalization_status nullable in campaign_contact_runs
    op.alter_column('campaign_contact_runs', 'personalization_status',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade() -> None:
    # Restore NOT NULL constraints (with default values for existing NULLs)
    
    # First update any NULL values to defaults
    op.execute("UPDATE campaign_company_runs SET sync_to_hubspot_status = '' WHERE sync_to_hubspot_status IS NULL")
    op.execute("UPDATE campaign_contact_runs SET enrichment_status = false WHERE enrichment_status IS NULL")
    op.execute("UPDATE campaign_contact_runs SET personalization_status = '' WHERE personalization_status IS NULL")
    
    # Then add NOT NULL constraints back
    op.alter_column('campaign_company_runs', 'sync_to_hubspot_status',
                    existing_type=sa.String(50),
                    nullable=False)
    
    op.alter_column('campaign_contact_runs', 'enrichment_status',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    op.alter_column('campaign_contact_runs', 'personalization_status',
                    existing_type=sa.String(50),
                    nullable=False)


