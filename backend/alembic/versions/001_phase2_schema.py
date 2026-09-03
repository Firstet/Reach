"""Phase 2 schema extensions

Revision ID: 001_phase2_schema
Revises: 
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_phase2_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Campaign extensions
    op.add_column('campaigns', sa.Column('test_mode', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('campaigns', sa.Column('approval_mode', sa.String(length=20), server_default='auto', nullable=False))
    op.add_column('campaigns', sa.Column('min_score_threshold', sa.Float(), server_default='40.0', nullable=False))
    op.add_column('campaigns', sa.Column('discovery_query', sa.Text(), nullable=True))
    op.add_column('campaigns', sa.Column('scoring_weights', sa.JSON(), nullable=True))
    op.add_column('campaigns', sa.Column('tracking_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('campaigns', sa.Column('require_email_verification', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('campaigns', sa.Column('daily_sends_today', sa.Integer(), server_default='0', nullable=False))
    op.add_column('campaigns', sa.Column('last_tick_at', sa.DateTime(timezone=True), nullable=True))

    # Lead extensions
    op.add_column('leads', sa.Column('is_test', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('discovery_source', sa.String(length=100), nullable=True))

    # prospect_researches
    op.create_table(
        'prospect_researches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('company_context', sa.Text(), nullable=True),
        sa.Column('recent_developments', sa.Text(), nullable=True),
        sa.Column('communication_signals', sa.Text(), nullable=True),
        sa.Column('potential_challenge', sa.Text(), nullable=True),
        sa.Column('potential_opportunity', sa.Text(), nullable=True),
        sa.Column('why_rayven_relevant', sa.Text(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('source_urls', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.8', nullable=False),
        sa.Column('raw_intelligence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # email_templates
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), server_default='outreach', nullable=False),
        sa.Column('subject_template', sa.String(length=1000), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # suppressions
    op.create_table(
        'suppressions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('suppression_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False, index=True),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('added_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('suppression_type', 'value', name='uq_suppression_type_val'),
    )

    # discovery_jobs
    op.create_table(
        'discovery_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('results_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # outreach_approvals
    op.create_table(
        'outreach_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('campaign_step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('campaign_steps.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject', sa.String(length=1000), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('outreach_approvals')
    op.drop_table('discovery_jobs')
    op.drop_table('suppressions')
    op.drop_table('email_templates')
    op.drop_table('prospect_researches')
    op.drop_column('leads', 'discovery_source')
    op.drop_column('leads', 'is_test')
    op.drop_column('campaigns', 'last_tick_at')
    op.drop_column('campaigns', 'daily_sends_today')
    op.drop_column('campaigns', 'require_email_verification')
    op.drop_column('campaigns', 'tracking_enabled')
    op.drop_column('campaigns', 'scoring_weights')
    op.drop_column('campaigns', 'discovery_query')
    op.drop_column('campaigns', 'min_score_threshold')
    op.drop_column('campaigns', 'approval_mode')
    op.drop_column('campaigns', 'test_mode')
