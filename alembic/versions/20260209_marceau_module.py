"""Marceau AI Assistant Module - Agent IA Polyvalent

Revision ID: marceau_module_001
Revises: trial_registrations_001
Create Date: 2026-02-09

Tables:
- marceau_configs: Configuration par tenant (modules, autonomie, integrations)
- marceau_actions: Journal des actions (tracabilite complete)
- marceau_memory: Memoire contextuelle (RAG + ChromaDB)
- marceau_conversations: Conversations telephoniques
- marceau_knowledge_documents: Documents uploades
- marceau_feedback: Feedback utilisateur pour apprentissage
- marceau_scheduled_tasks: Taches planifiees (cron)

Ce module implemente Marceau, un agent IA polyvalent capable de gerer
9 domaines metiers de maniere 100% autonome par defaut.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'marceau_module_001'
down_revision = 'trial_registrations_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Marceau module tables and enums."""

    # ==========================================================================
    # ENUM TYPES
    # ==========================================================================

    # Action Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marceau_action_status AS ENUM (
                'pending',
                'in_progress',
                'completed',
                'failed',
                'needs_validation',
                'validated',
                'rejected'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Memory Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marceau_memory_type AS ENUM (
                'conversation',
                'customer_profile',
                'decision',
                'learning',
                'knowledge'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Conversation Outcome
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marceau_conversation_outcome AS ENUM (
                'quote_created',
                'appointment_scheduled',
                'transferred',
                'voicemail',
                'abandoned',
                'information_provided',
                'callback_scheduled',
                'complaint_recorded'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Module Name
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marceau_module_name AS ENUM (
                'telephonie',
                'marketing',
                'seo',
                'commercial',
                'comptabilite',
                'juridique',
                'recrutement',
                'support',
                'orchestration'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==========================================================================
    # TABLE: marceau_configs
    # ==========================================================================
    op.create_table(
        'marceau_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, unique=True, index=True),

        # Modules actives
        sa.Column('enabled_modules', postgresql.JSONB, nullable=False, server_default='{}'),

        # Niveaux d'autonomie
        sa.Column('autonomy_levels', postgresql.JSONB, nullable=False, server_default='{}'),

        # Configuration IA
        sa.Column('llm_temperature', sa.Float, nullable=False, server_default='0.2'),
        sa.Column('llm_model', sa.String(100), nullable=False, server_default="'llama3-8b-instruct'"),
        sa.Column('stt_model', sa.String(100), nullable=False, server_default="'whisper-small'"),
        sa.Column('tts_voice', sa.String(100), nullable=False, server_default="'fr_FR-sise-medium'"),

        # Configuration telephonie
        sa.Column('telephony_config', postgresql.JSONB, nullable=False, server_default='{}'),

        # Integrations externes
        sa.Column('integrations', postgresql.JSONB, nullable=False, server_default='{}'),

        # Statistiques
        sa.Column('total_actions', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_conversations', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_quotes_created', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_appointments_scheduled', sa.Integer, nullable=False, server_default='0'),

        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_marceau_config_tenant', 'marceau_configs', ['tenant_id'], unique=True)

    # ==========================================================================
    # TABLE: marceau_conversations
    # ==========================================================================
    op.create_table(
        'marceau_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Appelant
        sa.Column('caller_phone', sa.String(50), nullable=False),
        sa.Column('caller_name', sa.String(255), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),

        # Contenu
        sa.Column('transcript', sa.Text, nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('intent', sa.String(100), nullable=True),

        # Metriques
        sa.Column('duration_seconds', sa.Integer, nullable=False, server_default='0'),
        sa.Column('satisfaction_score', sa.Float, nullable=True),

        # Resultat
        sa.Column('outcome', postgresql.ENUM('quote_created', 'appointment_scheduled', 'transferred',
                                             'voicemail', 'abandoned', 'information_provided',
                                             'callback_scheduled', 'complaint_recorded',
                                             name='marceau_conversation_outcome', create_type=False),
                  nullable=True),

        # Fichiers
        sa.Column('recording_url', sa.String(500), nullable=True),

        # Asterisk
        sa.Column('asterisk_call_id', sa.String(100), nullable=True, index=True),
        sa.Column('asterisk_channel', sa.String(255), nullable=True),

        # Transfert
        sa.Column('transferred_to', sa.String(100), nullable=True),
        sa.Column('transfer_reason', sa.String(255), nullable=True),

        # Dates
        sa.Column('started_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_marceau_conv_tenant', 'marceau_conversations', ['tenant_id'])
    op.create_index('idx_marceau_conv_customer', 'marceau_conversations', ['tenant_id', 'customer_id'])
    op.create_index('idx_marceau_conv_phone', 'marceau_conversations', ['tenant_id', 'caller_phone'])
    op.create_index('idx_marceau_conv_outcome', 'marceau_conversations', ['tenant_id', 'outcome'])
    op.create_index('idx_marceau_conv_date', 'marceau_conversations', ['tenant_id', 'started_at'])

    # ==========================================================================
    # TABLE: marceau_actions
    # ==========================================================================
    op.create_table(
        'marceau_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Module et type
        sa.Column('module', postgresql.ENUM('telephonie', 'marketing', 'seo', 'commercial',
                                            'comptabilite', 'juridique', 'recrutement',
                                            'support', 'orchestration',
                                            name='marceau_module_name', create_type=False),
                  nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed',
                                            'needs_validation', 'validated', 'rejected',
                                            name='marceau_action_status', create_type=False),
                  nullable=False, server_default='pending'),

        # Donnees
        sa.Column('input_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('output_data', postgresql.JSONB, nullable=False, server_default='{}'),

        # Scoring et validation
        sa.Column('confidence_score', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('required_human_validation', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validated_at', sa.DateTime, nullable=True),
        sa.Column('validation_notes', sa.Text, nullable=True),

        # Entite liee
        sa.Column('related_entity_type', sa.String(100), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Conversation
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('marceau_conversations.id'), nullable=True),

        # Metriques
        sa.Column('duration_seconds', sa.Float, nullable=False, server_default='0'),
        sa.Column('tokens_used', sa.Integer, nullable=False, server_default='0'),

        # Erreur
        sa.Column('error_message', sa.Text, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_marceau_action_tenant', 'marceau_actions', ['tenant_id'])
    op.create_index('idx_marceau_action_module', 'marceau_actions', ['tenant_id', 'module'])
    op.create_index('idx_marceau_action_status', 'marceau_actions', ['tenant_id', 'status'])
    op.create_index('idx_marceau_action_date', 'marceau_actions', ['tenant_id', 'created_at'])
    op.create_index('idx_marceau_action_validation', 'marceau_actions',
                    ['tenant_id', 'required_human_validation', 'status'])

    # ==========================================================================
    # TABLE: marceau_memory
    # ==========================================================================
    op.create_table(
        'marceau_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Type
        sa.Column('memory_type', postgresql.ENUM('conversation', 'customer_profile', 'decision',
                                                 'learning', 'knowledge',
                                                 name='marceau_memory_type', create_type=False),
                  nullable=False),

        # Contenu
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),

        # ChromaDB
        sa.Column('embedding_id', sa.String(255), nullable=True, index=True),
        sa.Column('collection_name', sa.String(100), nullable=True),

        # Relations
        sa.Column('related_action_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Classification
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('importance_score', sa.Float, nullable=False, server_default='0.5'),

        # Expiration
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('is_permanent', sa.Boolean, nullable=False, server_default='false'),

        # Source
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('source_file_name', sa.String(255), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_marceau_memory_tenant', 'marceau_memory', ['tenant_id'])
    op.create_index('idx_marceau_memory_type', 'marceau_memory', ['tenant_id', 'memory_type'])
    op.create_index('idx_marceau_memory_embedding', 'marceau_memory', ['embedding_id'])
    op.create_index('idx_marceau_memory_importance', 'marceau_memory', ['tenant_id', 'importance_score'])

    # ==========================================================================
    # TABLE: marceau_knowledge_documents
    # ==========================================================================
    op.create_table(
        'marceau_knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Fichier
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False, server_default='0'),
        sa.Column('file_url', sa.String(500), nullable=True),

        # Traitement
        sa.Column('is_processed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('chunks_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('processing_error', sa.Text, nullable=True),

        # Classification
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),

        # Audit
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_marceau_doc_tenant', 'marceau_knowledge_documents', ['tenant_id'])
    op.create_index('idx_marceau_doc_processed', 'marceau_knowledge_documents', ['tenant_id', 'is_processed'])
    op.create_index('idx_marceau_doc_category', 'marceau_knowledge_documents', ['tenant_id', 'category'])

    # ==========================================================================
    # TABLE: marceau_feedback
    # ==========================================================================
    op.create_table(
        'marceau_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Action
        sa.Column('action_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('marceau_actions.id'), nullable=False),

        # Feedback
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('comment', sa.Text, nullable=True),

        # Correction
        sa.Column('correction_data', postgresql.JSONB, nullable=True),

        # Auteur
        sa.Column('given_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Traitement
        sa.Column('is_processed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('applied_to_learning', sa.Boolean, nullable=False, server_default='false'),

        # Audit
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_marceau_feedback_tenant', 'marceau_feedback', ['tenant_id'])
    op.create_index('idx_marceau_feedback_action', 'marceau_feedback', ['action_id'])
    op.create_index('idx_marceau_feedback_processed', 'marceau_feedback', ['tenant_id', 'is_processed'])

    # ==========================================================================
    # TABLE: marceau_scheduled_tasks
    # ==========================================================================
    op.create_table(
        'marceau_scheduled_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False, index=True),

        # Identification
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Module et action
        sa.Column('module', postgresql.ENUM('telephonie', 'marketing', 'seo', 'commercial',
                                            'comptabilite', 'juridique', 'recrutement',
                                            'support', 'orchestration',
                                            name='marceau_module_name', create_type=False),
                  nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('action_params', postgresql.JSONB, nullable=False, server_default='{}'),

        # Planification
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=False, server_default="'Europe/Paris'"),

        # Statut
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('last_run_status', sa.String(50), nullable=True),
        sa.Column('last_run_error', sa.Text, nullable=True),

        # Statistiques
        sa.Column('run_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer, nullable=False, server_default='0'),

        # Audit
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_marceau_task_tenant', 'marceau_scheduled_tasks', ['tenant_id'])
    op.create_index('idx_marceau_task_active', 'marceau_scheduled_tasks', ['tenant_id', 'is_active'])
    op.create_index('idx_marceau_task_next_run', 'marceau_scheduled_tasks', ['next_run_at'])


def downgrade() -> None:
    """Drop Marceau module tables and enums."""

    # Drop tables
    op.drop_table('marceau_scheduled_tasks')
    op.drop_table('marceau_feedback')
    op.drop_table('marceau_knowledge_documents')
    op.drop_table('marceau_memory')
    op.drop_table('marceau_actions')
    op.drop_table('marceau_conversations')
    op.drop_table('marceau_configs')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS marceau_module_name CASCADE")
    op.execute("DROP TYPE IF EXISTS marceau_conversation_outcome CASCADE")
    op.execute("DROP TYPE IF EXISTS marceau_memory_type CASCADE")
    op.execute("DROP TYPE IF EXISTS marceau_action_status CASCADE")
