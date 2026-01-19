"""Add tasks module tables and owner_user_id columns

Revision ID: 20260118_tasks
Revises: 20260112_add_single_company_csv_import_columns
Create Date: 2026-01-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_tasks'
down_revision: Union[str, None] = 'add_ai_prospecting_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Add owner_user_id columns to existing tables
    # =========================================================================
    
    # Add owner_user_id to companies (if not exists)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    companies_columns = [col['name'] for col in inspector.get_columns('companies')]
    
    if 'owner_user_id' not in companies_columns:
        op.add_column('companies', sa.Column('owner_user_id', sa.String(24), nullable=True))
        op.create_index('ix_companies_owner_user_id', 'companies', ['owner_user_id'])
    
    # Add owner_user_id to contacts (if not exists)
    contacts_columns = [col['name'] for col in inspector.get_columns('contacts')]
    if 'owner_user_id' not in contacts_columns:
        op.add_column('contacts', sa.Column('owner_user_id', sa.String(24), nullable=True))
        op.create_index('ix_contacts_owner_user_id', 'contacts', ['owner_user_id'])
    
    # =========================================================================
    # Create deals table (if not exists)
    # =========================================================================
    existing_tables = inspector.get_table_names()
    if 'deals' not in existing_tables:
        op.create_table(
            'deals',
            sa.Column('id', sa.String(24), primary_key=True),
            sa.Column('sl_no', sa.BigInteger(), sa.Identity(always=True), unique=True, nullable=False),
            sa.Column('company_id', sa.String(24), sa.ForeignKey('companies.id'), nullable=True),
            sa.Column('owner_user_id', sa.String(24), nullable=True),
            sa.Column('name', sa.String(255), nullable=True),
            sa.Column('stage', sa.String(50), nullable=True),
            sa.Column('amount', sa.Numeric(), nullable=True),
            sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_deals_sl_no', 'deals', ['sl_no'])
        op.create_index('ix_deals_company_id', 'deals', ['company_id'])
        op.create_index('ix_deals_owner_user_id', 'deals', ['owner_user_id'])
        op.create_index('ix_deals_stage', 'deals', ['stage'])
    else:
        # Add owner_user_id to existing deals table if missing
        deals_columns = [col['name'] for col in inspector.get_columns('deals')]
        if 'owner_user_id' not in deals_columns:
            op.add_column('deals', sa.Column('owner_user_id', sa.String(24), nullable=True))
            op.create_index('ix_deals_owner_user_id', 'deals', ['owner_user_id'])
    
    # =========================================================================
    # Create task_type_policies table (if not exists)
    # =========================================================================
    if 'task_type_policies' not in existing_tables:
        op.create_table(
            'task_type_policies',
            sa.Column('type', sa.String(40), primary_key=True),
            sa.Column('default_sla_minutes', sa.Integer(), nullable=False),
            sa.Column('default_priority', sa.SmallInteger(), nullable=False, server_default='3'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        
        # Seed task type policies
        op.execute("""
            INSERT INTO task_type_policies (type, default_sla_minutes, default_priority, created_at, updated_at) VALUES
            ('call', 120, 2, NOW(), NOW()),
            ('followup_email', 1440, 3, NOW(), NOW()),
            ('reply_email', 60, 2, NOW(), NOW()),
            ('data_clean', 2880, 4, NOW(), NOW())
            ON CONFLICT (type) DO NOTHING
        """)
    
    # =========================================================================
    # Create tasks table (if not exists)
    # =========================================================================
    if 'tasks' not in existing_tables:
        op.create_table(
            'tasks',
            sa.Column('id', sa.String(24), primary_key=True),
            sa.Column('sl_no', sa.BigInteger(), sa.Identity(always=True), unique=True, nullable=False),
            
            # Primary entity association
            sa.Column('primary_entity_type', sa.String(20), nullable=False),  # contact|company|deal
            sa.Column('primary_entity_id', sa.String(24), nullable=False),
            
            # Task details
            sa.Column('type', sa.String(40), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('priority', sa.SmallInteger(), nullable=False, server_default='3'),
            
            # Dates
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('snoozed_until', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            
            # User associations
            sa.Column('assigned_to_user_id', sa.String(24), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('owner_user_id', sa.String(24), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_by_user_id', sa.String(24), sa.ForeignKey('users.id'), nullable=True),
            
            # Content
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            
            # Source tracking
            sa.Column('source', sa.String(40), nullable=True),
            sa.Column('source_ref', sa.String(255), nullable=True),
            sa.Column('idempotency_key', sa.String(255), unique=True, nullable=True),
            
            # Context data
            sa.Column('context_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            
            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        
        # Task indexes
        op.create_index('ix_tasks_sl_no', 'tasks', ['sl_no'])
        op.create_index('ix_tasks_inbox', 'tasks', ['status', 'assigned_to_user_id', 'due_at', 'sl_no'])
        op.create_index('ix_tasks_primary_entity', 'tasks', ['primary_entity_type', 'primary_entity_id', 'sl_no'])
        op.create_index('ix_tasks_type_status_due', 'tasks', ['type', 'status', 'due_at'])
        op.create_index('ix_tasks_source_ref', 'tasks', ['source', 'source_ref'])
        op.create_index('ix_tasks_context_gin', 'tasks', ['context_json'], postgresql_using='gin')
    
    # =========================================================================
    # Create task_links table (if not exists)
    # =========================================================================
    if 'task_links' not in existing_tables:
        op.create_table(
            'task_links',
            sa.Column('id', sa.String(24), primary_key=True),
            sa.Column('sl_no', sa.BigInteger(), sa.Identity(always=True), unique=True, nullable=False),
            
            sa.Column('task_id', sa.String(24), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('entity_type', sa.String(20), nullable=False),
            sa.Column('entity_id', sa.String(24), nullable=False),
            sa.Column('link_reason', sa.String(30), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            
            sa.UniqueConstraint('task_id', 'entity_type', 'entity_id', name='uq_task_links_task_entity'),
        )
        
        # Task links indexes
        op.create_index('ix_task_links_sl_no', 'task_links', ['sl_no'])
        op.create_index('ix_task_links_entity', 'task_links', ['entity_type', 'entity_id', 'sl_no'])
        op.create_index('ix_task_links_task', 'task_links', ['task_id'])
    
    # =========================================================================
    # Create task_activity table (if not exists)
    # =========================================================================
    if 'task_activity' not in existing_tables:
        op.create_table(
            'task_activity',
            sa.Column('id', sa.String(24), primary_key=True),
            sa.Column('sl_no', sa.BigInteger(), sa.Identity(always=True), unique=True, nullable=False),
            
            sa.Column('task_id', sa.String(24), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('at', sa.DateTime(), nullable=False),
            sa.Column('actor_user_id', sa.String(24), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('event_type', sa.String(40), nullable=False),
            sa.Column('diff_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        )
        
        # Task activity indexes
        op.create_index('ix_task_activity_sl_no', 'task_activity', ['sl_no'])
        op.create_index('ix_task_activity_task_at', 'task_activity', ['task_id', 'at'])


def downgrade() -> None:
    # Drop task_activity table
    op.drop_index('ix_task_activity_task_at', table_name='task_activity')
    op.drop_index('ix_task_activity_sl_no', table_name='task_activity')
    op.drop_table('task_activity')
    
    # Drop task_links table
    op.drop_index('ix_task_links_task', table_name='task_links')
    op.drop_index('ix_task_links_entity', table_name='task_links')
    op.drop_index('ix_task_links_sl_no', table_name='task_links')
    op.drop_table('task_links')
    
    # Drop tasks table
    op.drop_index('ix_tasks_context_gin', table_name='tasks')
    op.drop_index('ix_tasks_source_ref', table_name='tasks')
    op.drop_index('ix_tasks_type_status_due', table_name='tasks')
    op.drop_index('ix_tasks_primary_entity', table_name='tasks')
    op.drop_index('ix_tasks_inbox', table_name='tasks')
    op.drop_index('ix_tasks_sl_no', table_name='tasks')
    op.drop_table('tasks')
    
    # Drop task_type_policies table
    op.drop_table('task_type_policies')
    
    # Drop deals table
    op.drop_index('ix_deals_stage', table_name='deals')
    op.drop_index('ix_deals_owner_user_id', table_name='deals')
    op.drop_index('ix_deals_company_id', table_name='deals')
    op.drop_index('ix_deals_sl_no', table_name='deals')
    op.drop_table('deals')
    
    # Remove owner_user_id from contacts
    op.drop_index('ix_contacts_owner_user_id', table_name='contacts')
    op.drop_column('contacts', 'owner_user_id')
    
    # Remove owner_user_id from companies
    op.drop_index('ix_companies_owner_user_id', table_name='companies')
    op.drop_column('companies', 'owner_user_id')
