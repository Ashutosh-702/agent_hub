"""add_ai_prospecting_columns

Revision ID: add_ai_prospecting_cols
Revises: add_single_company_cols
Create Date: 2026-01-12

This migration adds:
- ai_prospecting_status column to campaigns table (indexed for queries)
- ai_prospecting JSONB column to campaigns table (for nested data)

Used by multiple campaign types where AI company prospecting occurs:
- similar_companies: Find companies similar to a reference company
- nl_filter: Find companies using natural language search
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'add_ai_prospecting_cols'
down_revision: Union[str, None] = 'add_single_company_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ai_prospecting columns."""
    
    # Add ai_prospecting_status column to campaigns (indexed for queries)
    op.add_column(
        'campaigns',
        sa.Column('ai_prospecting_status', sa.String(50), nullable=True)
    )
    op.create_index('ix_campaigns_ai_prospecting_status', 'campaigns', ['ai_prospecting_status'])
    
    # Add ai_prospecting JSONB column to campaigns (for nested data)
    op.add_column(
        'campaigns',
        sa.Column('ai_prospecting', JSONB, nullable=True, server_default='{}')
    )
    
    print("✅ Added ai_prospecting_status, ai_prospecting to campaigns")


def downgrade() -> None:
    """Remove the added columns."""
    
    # Remove ai_prospecting JSONB from campaigns
    op.drop_column('campaigns', 'ai_prospecting')
    
    # Remove ai_prospecting_status from campaigns
    op.drop_index('ix_campaigns_ai_prospecting_status', table_name='campaigns')
    op.drop_column('campaigns', 'ai_prospecting_status')
    
    print("❌ Removed ai_prospecting_status, ai_prospecting from campaigns")

