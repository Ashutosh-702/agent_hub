"""Initial database schema for Agent Hub.

Revision ID: 20260110_000001
Revises: 
Create Date: 2026-01-10 00:00:01.000000

This migration creates all tables for the Agent Hub application,
migrating from MongoDB to PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260110_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Users table ###
    op.create_table('users',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)

    # ### User Tokens table ###
    op.create_table('user_tokens',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('user_id', sa.String(length=24), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_tokens_token', 'user_tokens', ['token'], unique=True)
    op.create_index('ix_user_tokens_user_id', 'user_tokens', ['user_id'], unique=False)
    op.create_index('ix_user_tokens_validation', 'user_tokens', ['token', 'is_revoked', 'expires_at'], unique=False)

    # ### Campaigns table ###
    op.create_table('campaigns',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('campaign_type', sa.String(length=100), nullable=True),
        sa.Column('lifecycle_status', sa.String(length=50), nullable=True),
        sa.Column('prospecting_status', sa.String(length=50), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('shortlisting_approach', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('prompts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('segmentation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('target', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ownership', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lifecycle', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prospecting_cycle', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sequence_enrollment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_campaigns_name', 'campaigns', ['name'], unique=False)
    op.create_index('ix_campaigns_campaign_type', 'campaigns', ['campaign_type'], unique=False)
    op.create_index('ix_campaigns_lifecycle_status', 'campaigns', ['lifecycle_status'], unique=False)
    op.create_index('ix_campaigns_prospecting_status', 'campaigns', ['prospecting_status'], unique=False)
    op.create_index('ix_campaigns_user_email', 'campaigns', ['user_email'], unique=False)

    # ### Companies table ###
    op.create_table('companies',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('primary_domain', sa.String(length=255), nullable=True),
        sa.Column('source_domain', sa.String(length=255), nullable=True),
        sa.Column('industry', postgresql.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('identifiers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('deep_research', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('red_flags_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_companies_name', 'companies', ['name'], unique=False)
    op.create_index('ix_companies_source', 'companies', ['source'], unique=False)
    op.create_index('ix_companies_source_id', 'companies', ['source_id'], unique=False)
    op.create_index('ix_companies_primary_domain', 'companies', ['primary_domain'], unique=False)
    op.create_index('ix_companies_source_domain', 'companies', ['source_domain'], unique=False)
    op.create_index('ix_companies_industry', 'companies', ['industry'], unique=False, postgresql_using='gin')

    # ### Contacts table ###
    op.create_table('contacts',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('company_id', sa.String(length=24), nullable=True),
        sa.Column('firstname', sa.String(length=255), nullable=True),
        sa.Column('lastname', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('jobtitle', sa.String(length=500), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('webhook_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enrichment_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('contact_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('linkedin_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contacts_company_id', 'contacts', ['company_id'], unique=False)
    op.create_index('ix_contacts_email', 'contacts', ['email'], unique=False)
    op.create_index('ix_contacts_source_id', 'contacts', ['source_id'], unique=False)

    # ### Campaign Company Runs table ###
    op.create_table('campaign_company_runs',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('campaign_id', sa.String(length=24), nullable=False),
        sa.Column('company_id', sa.String(length=24), nullable=False),
        sa.Column('company_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('linkedin_contact_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sync_to_hubspot_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'company_id', name='uq_campaign_company')
    )
    op.create_index('ix_campaign_company_runs_campaign_id', 'campaign_company_runs', ['campaign_id'], unique=False)
    op.create_index('ix_campaign_company_runs_company_id', 'campaign_company_runs', ['company_id'], unique=False)
    op.create_index('ix_campaign_company_runs_is_relevant', 'campaign_company_runs', ['is_relevant'], unique=False)
    op.create_index('ix_campaign_company_runs_sync_to_hubspot_status', 'campaign_company_runs', ['sync_to_hubspot_status'], unique=False)
    op.create_index('ix_campaign_company_runs_composite', 'campaign_company_runs', ['campaign_id', 'company_id'], unique=False)

    # ### Campaign Contact Runs table ###
    op.create_table('campaign_contact_runs',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('campaign_id', sa.String(length=24), nullable=False),
        sa.Column('company_id', sa.String(length=24), nullable=False),
        sa.Column('contact_id', sa.String(length=24), nullable=False),
        sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enrichment_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('personalization_status', sa.String(length=50), nullable=True),
        sa.Column('email_id', sa.String(length=255), nullable=True),
        sa.Column('personalized_message', sa.Text(), nullable=True),
        sa.Column('ai_generated_deck', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sequence_enrollment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'contact_id', name='uq_campaign_contact')
    )
    op.create_index('ix_campaign_contact_runs_campaign_id', 'campaign_contact_runs', ['campaign_id'], unique=False)
    op.create_index('ix_campaign_contact_runs_company_id', 'campaign_contact_runs', ['company_id'], unique=False)
    op.create_index('ix_campaign_contact_runs_contact_id', 'campaign_contact_runs', ['contact_id'], unique=False)
    op.create_index('ix_campaign_contact_runs_is_relevant', 'campaign_contact_runs', ['is_relevant'], unique=False)
    op.create_index('ix_campaign_contact_runs_enrichment_status', 'campaign_contact_runs', ['enrichment_status'], unique=False)
    op.create_index('ix_campaign_contact_runs_personalization_status', 'campaign_contact_runs', ['personalization_status'], unique=False)
    op.create_index('ix_campaign_contact_runs_email_id', 'campaign_contact_runs', ['email_id'], unique=False)
    op.create_index('ix_campaign_contact_runs_composite', 'campaign_contact_runs', ['campaign_id', 'contact_id'], unique=False)

    # ### Meetings table ###
    op.create_table('meetings',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('meeting_id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=24), nullable=True),
        sa.Column('meeting_name', sa.String(length=500), nullable=True),
        sa.Column('call_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='scheduled'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_domain', sa.String(length=255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('contact_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('product_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('transcript', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('live_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('action_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('next_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('key_discussion_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('objections_resolutions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('products_discussed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('battlecard', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reflections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_meetings_meeting_id', 'meetings', ['meeting_id'], unique=True)
    op.create_index('ix_meetings_company_id', 'meetings', ['company_id'], unique=False)
    op.create_index('ix_meetings_status', 'meetings', ['status'], unique=False)
    op.create_index('ix_meetings_call_type', 'meetings', ['call_type'], unique=False)

    # ### Inbox Leads table ###
    op.create_table('inbox_leads',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('lead_id', sa.String(length=100), nullable=False),
        sa.Column('lemlist_inbox_id', sa.String(length=100), nullable=True),
        sa.Column('lemlist_contact_id', sa.String(length=100), nullable=True),
        sa.Column('temperature', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('in_sequence', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('owner_email', sa.String(length=255), nullable=True),
        sa.Column('last_touch_at', sa.DateTime(), nullable=True),
        sa.Column('next_step_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('company', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contact', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('owner', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sequence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_touch', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('channels_present', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('temperature_drivers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inbox_leads_lead_id', 'inbox_leads', ['lead_id'], unique=True)
    op.create_index('ix_inbox_leads_lemlist_inbox_id', 'inbox_leads', ['lemlist_inbox_id'], unique=False)
    op.create_index('ix_inbox_leads_lemlist_contact_id', 'inbox_leads', ['lemlist_contact_id'], unique=False)
    op.create_index('ix_inbox_leads_temperature', 'inbox_leads', ['temperature'], unique=False)
    op.create_index('ix_inbox_leads_status', 'inbox_leads', ['status'], unique=False)
    op.create_index('ix_inbox_leads_in_sequence', 'inbox_leads', ['in_sequence'], unique=False)
    op.create_index('ix_inbox_leads_unread_count', 'inbox_leads', ['unread_count'], unique=False)
    op.create_index('ix_inbox_leads_owner_email', 'inbox_leads', ['owner_email'], unique=False)
    op.create_index('ix_inbox_leads_last_touch_at', 'inbox_leads', ['last_touch_at'], unique=False)

    # ### Inbox Events table ###
    op.create_table('inbox_events',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('lead_id', sa.String(length=100), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=True),
        sa.Column('at', sa.DateTime(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lemlist_inbox_id', sa.String(length=100), nullable=True),
        sa.Column('lemlist_message_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['inbox_leads.lead_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inbox_events_lead_id', 'inbox_events', ['lead_id'], unique=False)
    op.create_index('ix_inbox_events_channel', 'inbox_events', ['channel'], unique=False)
    op.create_index('ix_inbox_events_at', 'inbox_events', ['at'], unique=False)
    op.create_index('ix_inbox_events_lemlist_inbox_id', 'inbox_events', ['lemlist_inbox_id'], unique=False)
    op.create_index('ix_inbox_events_lemlist_message_id', 'inbox_events', ['lemlist_message_id'], unique=True)
    op.create_index('ix_inbox_events_lead_at', 'inbox_events', ['lead_id', 'at'], unique=False)
    op.create_index('ix_inbox_events_composite', 'inbox_events', ['lead_id', 'at', 'channel'], unique=False)

    # ### Inbox Notes table ###
    op.create_table('inbox_notes',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('lead_id', sa.String(length=100), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['lead_id'], ['inbox_leads.lead_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inbox_notes_lead_id', 'inbox_notes', ['lead_id'], unique=False)
    op.create_index('ix_inbox_notes_at', 'inbox_notes', ['at'], unique=False)
    op.create_index('ix_inbox_notes_lead_at', 'inbox_notes', ['lead_id', 'at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('inbox_notes')
    op.drop_table('inbox_events')
    op.drop_table('inbox_leads')
    op.drop_table('meetings')
    op.drop_table('campaign_contact_runs')
    op.drop_table('campaign_company_runs')
    op.drop_table('contacts')
    op.drop_table('companies')
    op.drop_table('campaigns')
    op.drop_table('user_tokens')
    op.drop_table('users')


