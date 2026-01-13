"""add_single_company_csv_import_webhook_columns

Revision ID: add_single_company_cols
Revises: add_sl_no_pagination
Create Date: 2026-01-12

This migration adds:
- single_company_status, csv_import_status columns to campaigns table (indexed for queries)
- single_company, csv_import JSONB columns to campaigns table (for nested data)
- webhook_sent column to companies table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'add_single_company_cols'
down_revision: Union[str, None] = 'add_sl_no_pagination'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add single_company, csv_import, and webhook_sent columns."""
    
    # Add single_company_status column to campaigns (indexed for queries)
    op.add_column(
        'campaigns',
        sa.Column('single_company_status', sa.String(50), nullable=True)
    )
    op.create_index('ix_campaigns_single_company_status', 'campaigns', ['single_company_status'])
    
    # Add csv_import_status column to campaigns (indexed for queries)
    op.add_column(
        'campaigns',
        sa.Column('csv_import_status', sa.String(50), nullable=True)
    )
    op.create_index('ix_campaigns_csv_import_status', 'campaigns', ['csv_import_status'])
    
    # Add single_company JSONB column to campaigns (for nested data)
    op.add_column(
        'campaigns',
        sa.Column('single_company', JSONB, nullable=True, server_default='{}')
    )
    
    # Add csv_import JSONB column to campaigns (for nested data)
    op.add_column(
        'campaigns',
        sa.Column('csv_import', JSONB, nullable=True, server_default='{}')
    )
    
    # Add webhook_sent column to companies
    op.add_column(
        'companies',
        sa.Column('webhook_sent', sa.Boolean(), nullable=True, server_default='false')
    )
    
    print("✅ Added single_company_status, csv_import_status, single_company, csv_import to campaigns")
    print("✅ Added webhook_sent to companies")


def downgrade() -> None:
    """Remove the added columns."""
    
    # Remove webhook_sent from companies
    op.drop_column('companies', 'webhook_sent')
    
    # Remove csv_import JSONB from campaigns
    op.drop_column('campaigns', 'csv_import')
    
    # Remove single_company JSONB from campaigns
    op.drop_column('campaigns', 'single_company')
    
    # Remove csv_import_status from campaigns
    op.drop_index('ix_campaigns_csv_import_status', table_name='campaigns')
    op.drop_column('campaigns', 'csv_import_status')
    
    # Remove single_company_status from campaigns
    op.drop_index('ix_campaigns_single_company_status', table_name='campaigns')
    op.drop_column('campaigns', 'single_company_status')
    
    print("❌ Removed single_company_status, csv_import_status, single_company, csv_import from campaigns")
    print("❌ Removed webhook_sent from companies")

