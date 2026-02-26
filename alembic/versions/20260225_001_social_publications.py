"""Social Publications - Publications et Leads Réseaux Sociaux

Revision ID: 20260225_001
Revises: 20260221_005_integrations_module
Create Date: 2026-02-25

Module de création de publications sur les réseaux sociaux
pour générer des leads vers azalscore.com.

Tables créées:
- social_campaigns: Campagnes marketing
- social_posts: Publications programmées
- social_leads: Leads générés
- social_post_templates: Templates réutilisables
- social_publishing_slots: Créneaux de publication optimaux
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'social_publications_001'
down_revision = '20260220_ui_style'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === CAMPAGNES ===
    op.create_table(
        'social_campaigns',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),

        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),

        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),

        sa.Column('objective', sa.String(100), nullable=True),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('target_leads', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('budget', sa.Numeric(12, 2), nullable=False, server_default='0'),

        sa.Column('platforms', sa.JSON(), nullable=False, server_default='[]'),

        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),

        sa.Column('total_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_leads', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('actual_spend', sa.Numeric(12, 2), nullable=False, server_default='0'),
    )

    op.create_index('ix_social_campaigns_tenant_status', 'social_campaigns', ['tenant_id', 'status'], if_not_exists=True)

    # === PUBLICATIONS ===
    op.create_table(
        'social_posts',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),

        sa.Column('campaign_id', sa.String(36), sa.ForeignKey('social_campaigns.id'), nullable=True),

        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('post_type', sa.String(50), nullable=False, server_default='text'),

        sa.Column('media_urls', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),

        sa.Column('link_url', sa.String(500), nullable=True),
        sa.Column('link_title', sa.String(255), nullable=True),
        sa.Column('link_description', sa.Text(), nullable=True),

        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('platforms', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),

        sa.Column('external_ids', sa.JSON(), nullable=False, server_default='{}'),

        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),

        sa.Column('hashtags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('mentions', sa.JSON(), nullable=False, server_default='[]'),

        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reach', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shares', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('saves', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('last_error', sa.Text(), nullable=True),
    )

    op.create_index('ix_social_posts_tenant_status', 'social_posts', ['tenant_id', 'status'], if_not_exists=True)
    op.create_index('ix_social_posts_scheduled', 'social_posts', ['tenant_id', 'scheduled_at'], if_not_exists=True)

    # === LEADS ===
    op.create_table(
        'social_leads',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('source_platform', sa.String(50), nullable=True),
        sa.Column('campaign_id', sa.String(36), sa.ForeignKey('social_campaigns.id'), nullable=True),
        sa.Column('post_id', sa.String(36), sa.ForeignKey('social_posts.id'), nullable=True),

        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),
        sa.Column('landing_page', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),

        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),

        sa.Column('social_profile_url', sa.String(500), nullable=True),
        sa.Column('social_username', sa.String(100), nullable=True),
        sa.Column('followers_count', sa.Integer(), nullable=True),

        sa.Column('status', sa.String(50), nullable=False, server_default='new'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interest', sa.String(255), nullable=True),
        sa.Column('budget_range', sa.String(50), nullable=True),
        sa.Column('timeline', sa.String(50), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('assigned_to', sa.String(255), nullable=True),

        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('contact_id', sa.String(36), nullable=True),
        sa.Column('opportunity_id', sa.String(36), nullable=True),

        sa.Column('interactions', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('emails_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_opened', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_index('ix_social_leads_tenant_status', 'social_leads', ['tenant_id', 'status'], if_not_exists=True)
    op.create_index('ix_social_leads_email', 'social_leads', ['tenant_id', 'email'], if_not_exists=True)
    op.create_index('ix_social_leads_campaign', 'social_leads', ['tenant_id', 'campaign_id'], if_not_exists=True)

    # === TEMPLATES ===
    op.create_table(
        'social_post_templates',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),

        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.Column('content_template', sa.Text(), nullable=False),
        sa.Column('post_type', sa.String(50), nullable=False, server_default='text'),
        sa.Column('suggested_hashtags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('suggested_media', sa.JSON(), nullable=False, server_default='[]'),

        sa.Column('recommended_platforms', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('variables', sa.JSON(), nullable=False, server_default='[]'),

        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_engagement_rate', sa.Numeric(10, 4), nullable=False, server_default='0'),

        sa.UniqueConstraint('tenant_id', 'name', name='uq_post_template_name'),
    )

    # === CRÉNEAUX DE PUBLICATION ===
    op.create_table(
        'social_publishing_slots',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text')),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),

        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=False),
        sa.Column('minute', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('is_optimal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('avg_engagement', sa.Numeric(10, 4), nullable=False, server_default='0'),
        sa.Column('posts_count', sa.Integer(), nullable=False, server_default='0'),

        sa.UniqueConstraint('tenant_id', 'platform', 'day_of_week', 'hour', name='uq_publishing_slot'),
    )


def downgrade() -> None:
    op.drop_table('social_publishing_slots')
    op.drop_table('social_post_templates')
    op.drop_table('social_leads')
    op.drop_table('social_posts')
    op.drop_table('social_campaigns')
