"""GUARDIAN AI: Add AI monitoring tables (Mode A/B/C)

Revision ID: guardian_ai_monitoring_001
Revises: guardian_incidents_001
Create Date: 2026-01-21

Tables:
- ai_incidents: Incidents détectés par l'IA (Mode A)
- ai_module_scores: Scores de fiabilité par module
- ai_audit_reports: Rapports d'audit mensuels (Mode B)
- ai_sla_metrics: Métriques SLA/Enterprise (Mode C)
- ai_config: Configuration du système IA Guardian
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'guardian_ai_monitoring_001'
down_revision = 'guardian_incidents_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AI Guardian monitoring tables."""

    # ==========================================================================
    # Table ai_incidents - Mode A (Incidents détectés par l'IA)
    # ==========================================================================
    op.create_table(
        'ai_incidents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # Identification
        sa.Column('incident_uid', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=True),

        # Contexte de l'erreur
        sa.Column('module', sa.String(100), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),

        # Détails de l'erreur
        sa.Column('error_signature', sa.String(255), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),

        # Classification
        sa.Column('incident_type', sa.String(20), nullable=False, server_default='backend'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(20), nullable=False, server_default='detected'),

        # Intervention IA
        sa.Column('analysis_started_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Actions prises
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('git_branch', sa.String(100), nullable=True),
        sa.Column('git_commit', sa.String(64), nullable=True),
        sa.Column('git_tag', sa.String(50), nullable=True),
        sa.Column('rollback_performed', sa.Boolean(), server_default='false'),

        # Résultat
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('auto_resolved', sa.Boolean(), server_default='false'),
        sa.Column('requires_human', sa.Boolean(), server_default='false'),

        # Métadonnées
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_uid'),
    )

    # Index pour ai_incidents
    op.create_index('ix_ai_incidents_incident_uid', 'ai_incidents', ['incident_uid'])
    op.create_index('ix_ai_incidents_tenant_id', 'ai_incidents', ['tenant_id'])
    op.create_index('ix_ai_incidents_module', 'ai_incidents', ['module'])
    op.create_index('ix_ai_incidents_error_signature', 'ai_incidents', ['error_signature'])
    op.create_index('ix_ai_incidents_tenant_module', 'ai_incidents', ['tenant_id', 'module'])
    op.create_index('ix_ai_incidents_status_severity', 'ai_incidents', ['status', 'severity'])
    op.create_index('ix_ai_incidents_created', 'ai_incidents', ['created_at'])

    # ==========================================================================
    # Table ai_module_scores - Mode A (Scores de fiabilité par module)
    # ==========================================================================
    op.create_table(
        'ai_module_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # Identification
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('module', sa.String(100), nullable=False),

        # Score global (0-100)
        sa.Column('score_total', sa.Integer(), nullable=False, server_default='100'),

        # Composantes du score
        sa.Column('score_errors', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('score_performance', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('score_data', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('score_security', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('score_stability', sa.Integer(), nullable=False, server_default='10'),

        # Statistiques
        sa.Column('incidents_total', sa.Integer(), server_default='0'),
        sa.Column('incidents_critical', sa.Integer(), server_default='0'),
        sa.Column('incidents_resolved', sa.Integer(), server_default='0'),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('last_incident_at', sa.DateTime(), nullable=True),

        # Période d'évaluation
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),

        # Métadonnées
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Index pour ai_module_scores
    op.create_index('ix_ai_module_scores_tenant_id', 'ai_module_scores', ['tenant_id'])
    op.create_index('ix_ai_module_scores_module', 'ai_module_scores', ['module'])
    op.create_index('ix_ai_module_scores_tenant_module', 'ai_module_scores', ['tenant_id', 'module'])
    op.create_index('ix_ai_module_scores_period', 'ai_module_scores', ['period_start', 'period_end'])

    # ==========================================================================
    # Table ai_audit_reports - Mode B (Rapports d'audit mensuels)
    # ==========================================================================
    op.create_table(
        'ai_audit_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # Identification
        sa.Column('report_uid', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=True),

        # Période
        sa.Column('audit_month', sa.Integer(), nullable=False),
        sa.Column('audit_year', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),

        # Statut
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Résumé global
        sa.Column('modules_audited', sa.Integer(), server_default='0'),
        sa.Column('total_incidents', sa.Integer(), server_default='0'),
        sa.Column('critical_incidents', sa.Integer(), server_default='0'),
        sa.Column('avg_score', sa.Float(), nullable=True),

        # Rapport détaillé (JSON)
        sa.Column('module_reports', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risks_identified', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('technical_debt', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Fichier rapport
        sa.Column('report_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_file_path', sa.String(255), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_uid'),
    )

    # Index pour ai_audit_reports
    op.create_index('ix_ai_audit_reports_report_uid', 'ai_audit_reports', ['report_uid'])
    op.create_index('ix_ai_audit_reports_tenant_id', 'ai_audit_reports', ['tenant_id'])
    op.create_index('ix_ai_audit_reports_period', 'ai_audit_reports', ['audit_year', 'audit_month'])

    # ==========================================================================
    # Table ai_sla_metrics - Mode C (Métriques SLA/Enterprise)
    # ==========================================================================
    op.create_table(
        'ai_sla_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        # Identification
        sa.Column('metric_uid', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=True),

        # Période de mesure
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),

        # Disponibilité
        sa.Column('uptime_percent', sa.Float(), nullable=True),
        sa.Column('downtime_minutes', sa.Integer(), server_default='0'),

        # Temps de réponse
        sa.Column('avg_detection_time_ms', sa.Integer(), nullable=True),
        sa.Column('avg_resolution_time_ms', sa.Integer(), nullable=True),
        sa.Column('p95_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('p99_response_time_ms', sa.Integer(), nullable=True),

        # Incidents
        sa.Column('total_incidents', sa.Integer(), server_default='0'),
        sa.Column('incidents_by_module', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rollback_count', sa.Integer(), server_default='0'),
        sa.Column('rollback_rate', sa.Float(), nullable=True),

        # Sécurité & Isolation
        sa.Column('tenant_isolation_verified', sa.Boolean(), server_default='true'),
        sa.Column('security_incidents', sa.Integer(), server_default='0'),
        sa.Column('data_integrity_score', sa.Float(), nullable=True),

        # Métadonnées
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_uid'),
    )

    # Index pour ai_sla_metrics
    op.create_index('ix_ai_sla_metrics_metric_uid', 'ai_sla_metrics', ['metric_uid'])
    op.create_index('ix_ai_sla_metrics_tenant_id', 'ai_sla_metrics', ['tenant_id'])
    op.create_index('ix_ai_sla_metrics_tenant_period', 'ai_sla_metrics', ['tenant_id', 'period_type'])
    op.create_index('ix_ai_sla_metrics_period', 'ai_sla_metrics', ['period_start', 'period_end'])

    # ==========================================================================
    # Table ai_config - Configuration du système IA Guardian
    # ==========================================================================
    op.create_table(
        'ai_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),

        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(20), server_default='string'),
        sa.Column('description', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    # Index pour ai_config
    op.create_index('ix_ai_config_key', 'ai_config', ['key'])

    # ==========================================================================
    # Insérer configuration par défaut
    # ==========================================================================
    op.execute("""
        INSERT INTO ai_config (key, value, value_type, description) VALUES
        ('mode_a_enabled', 'true', 'bool', 'Active la détection automatique des incidents'),
        ('mode_b_enabled', 'true', 'bool', 'Active les audits mensuels automatiques'),
        ('mode_c_enabled', 'true', 'bool', 'Active le calcul des métriques SLA'),
        ('incident_dedup_window_minutes', '5', 'int', 'Fenêtre de déduplication des incidents (minutes)'),
        ('critical_threshold', '3', 'int', 'Nombre d incidents critiques déclenchant une alerte'),
        ('sla_target_uptime', '99.9', 'float', 'Objectif SLA uptime (%)'),
        ('sla_target_resolution_ms', '30000', 'int', 'Objectif SLA temps de résolution (ms)')
    """)


def downgrade() -> None:
    """Remove AI Guardian monitoring tables."""

    # Drop indexes
    op.drop_index('ix_ai_config_key', table_name='ai_config')

    op.drop_index('ix_ai_sla_metrics_period', table_name='ai_sla_metrics')
    op.drop_index('ix_ai_sla_metrics_tenant_period', table_name='ai_sla_metrics')
    op.drop_index('ix_ai_sla_metrics_tenant_id', table_name='ai_sla_metrics')
    op.drop_index('ix_ai_sla_metrics_metric_uid', table_name='ai_sla_metrics')

    op.drop_index('ix_ai_audit_reports_period', table_name='ai_audit_reports')
    op.drop_index('ix_ai_audit_reports_tenant_id', table_name='ai_audit_reports')
    op.drop_index('ix_ai_audit_reports_report_uid', table_name='ai_audit_reports')

    op.drop_index('ix_ai_module_scores_period', table_name='ai_module_scores')
    op.drop_index('ix_ai_module_scores_tenant_module', table_name='ai_module_scores')
    op.drop_index('ix_ai_module_scores_module', table_name='ai_module_scores')
    op.drop_index('ix_ai_module_scores_tenant_id', table_name='ai_module_scores')

    op.drop_index('ix_ai_incidents_created', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_status_severity', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_tenant_module', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_error_signature', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_module', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_tenant_id', table_name='ai_incidents')
    op.drop_index('ix_ai_incidents_incident_uid', table_name='ai_incidents')

    # Drop tables
    op.drop_table('ai_config')
    op.drop_table('ai_sla_metrics')
    op.drop_table('ai_audit_reports')
    op.drop_table('ai_module_scores')
    op.drop_table('ai_incidents')
