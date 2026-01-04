-- ============================================================================
-- AZALS MODULE T6 - DIFFUSION D'INFORMATION PÉRIODIQUE
-- Migration: 012_broadcast_module.sql
-- Description: Tables pour la gestion des diffusions automatiques
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE delivery_channel AS ENUM (
        'EMAIL', 'IN_APP', 'WEBHOOK', 'PDF_DOWNLOAD', 'SMS'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE broadcast_frequency AS ENUM (
        'ONCE', 'DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE broadcast_content_type AS ENUM (
        'DIGEST', 'NEWSLETTER', 'REPORT', 'ALERT', 'KPI_SUMMARY'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE broadcast_status AS ENUM (
        'DRAFT', 'SCHEDULED', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED', 'ERROR'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE delivery_status AS ENUM (
        'PENDING', 'SENDING', 'DELIVERED', 'FAILED', 'BOUNCED', 'OPENED', 'CLICKED'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE recipient_type AS ENUM (
        'USER', 'GROUP', 'ROLE', 'EXTERNAL', 'DYNAMIC'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- TABLE: TEMPLATES DE DIFFUSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_templates (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Type et contenu
    content_type broadcast_content_type NOT NULL,
    subject_template VARCHAR(500),
    body_template TEXT,
    html_template TEXT,

    -- Configuration
    default_channel delivery_channel DEFAULT 'EMAIL',
    available_channels JSONB,
    variables JSONB,
    styling JSONB,

    -- Data sources
    data_sources JSONB,
    aggregation_config JSONB,

    -- Localisation
    language VARCHAR(5) DEFAULT 'fr',
    country_code VARCHAR(2),

    -- État
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_broadcast_templates_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_broadcast_templates_tenant ON broadcast_templates(tenant_id);
CREATE INDEX IF NOT EXISTS ix_broadcast_templates_type ON broadcast_templates(tenant_id, content_type);
CREATE INDEX IF NOT EXISTS ix_broadcast_templates_active ON broadcast_templates(tenant_id, is_active);

-- ============================================================================
-- TABLE: LISTES DE DESTINATAIRES
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_recipient_lists (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Configuration
    is_dynamic BOOLEAN DEFAULT false,
    query_config JSONB,

    -- Statistiques
    total_recipients INTEGER DEFAULT 0,
    active_recipients INTEGER DEFAULT 0,

    -- État
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_recipient_lists_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_recipient_lists_tenant ON broadcast_recipient_lists(tenant_id);
CREATE INDEX IF NOT EXISTS ix_recipient_lists_active ON broadcast_recipient_lists(tenant_id, is_active);

-- ============================================================================
-- TABLE: MEMBRES DES LISTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_recipient_members (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    list_id INTEGER NOT NULL REFERENCES broadcast_recipient_lists(id) ON DELETE CASCADE,

    -- Type et référence
    recipient_type recipient_type NOT NULL,
    user_id INTEGER,
    group_id INTEGER,
    role_code VARCHAR(50),
    external_email VARCHAR(255),
    external_name VARCHAR(200),

    -- Préférences
    preferred_channel delivery_channel,
    preferred_language VARCHAR(5),
    preferred_format VARCHAR(20),

    -- État
    is_active BOOLEAN DEFAULT true,
    is_unsubscribed BOOLEAN DEFAULT false,
    unsubscribed_at TIMESTAMP,

    -- Audit
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER
);

CREATE INDEX IF NOT EXISTS ix_recipient_members_list ON broadcast_recipient_members(tenant_id, list_id);
CREATE INDEX IF NOT EXISTS ix_recipient_members_user ON broadcast_recipient_members(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS ix_recipient_members_active ON broadcast_recipient_members(tenant_id, is_active);

-- ============================================================================
-- TABLE: DIFFUSIONS PROGRAMMÉES
-- ============================================================================

CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Template et destinataires
    template_id INTEGER REFERENCES broadcast_templates(id),
    recipient_list_id INTEGER REFERENCES broadcast_recipient_lists(id),

    -- Contenu personnalisé
    content_type broadcast_content_type NOT NULL,
    subject VARCHAR(500),
    body_content TEXT,
    html_content TEXT,

    -- Configuration livraison
    delivery_channel delivery_channel NOT NULL DEFAULT 'EMAIL',
    additional_channels JSONB,

    -- Planification
    frequency broadcast_frequency NOT NULL,
    cron_expression VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',

    -- Fenêtre de diffusion
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    send_time VARCHAR(5),

    -- Pour fréquence spécifique
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6),
    day_of_month INTEGER CHECK (day_of_month >= 1 AND day_of_month <= 31),
    month_of_year INTEGER CHECK (month_of_year >= 1 AND month_of_year <= 12),

    -- Data dynamique
    data_query JSONB,
    data_filters JSONB,

    -- État
    status broadcast_status DEFAULT 'DRAFT',
    is_active BOOLEAN DEFAULT true,

    -- Statistiques
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,

    -- Exécution
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    last_error TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_scheduled_broadcasts_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS ix_scheduled_broadcasts_tenant ON scheduled_broadcasts(tenant_id);
CREATE INDEX IF NOT EXISTS ix_scheduled_broadcasts_status ON scheduled_broadcasts(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_scheduled_broadcasts_next_run ON scheduled_broadcasts(tenant_id, next_run_at);
CREATE INDEX IF NOT EXISTS ix_scheduled_broadcasts_active ON scheduled_broadcasts(tenant_id, is_active);

-- ============================================================================
-- TABLE: EXÉCUTIONS DE DIFFUSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_executions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    scheduled_broadcast_id INTEGER NOT NULL REFERENCES scheduled_broadcasts(id) ON DELETE CASCADE,

    -- Exécution
    execution_number INTEGER DEFAULT 1,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,

    -- Résultats
    status delivery_status DEFAULT 'PENDING',
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,

    -- Contenu généré
    generated_subject VARCHAR(500),
    generated_content TEXT,
    attachments JSONB,

    -- Erreurs
    error_message TEXT,
    error_details JSONB,

    -- Métriques engagement
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,

    -- Audit
    triggered_by VARCHAR(50) DEFAULT 'scheduler',
    triggered_user INTEGER
);

CREATE INDEX IF NOT EXISTS ix_broadcast_executions_scheduled ON broadcast_executions(tenant_id, scheduled_broadcast_id);
CREATE INDEX IF NOT EXISTS ix_broadcast_executions_date ON broadcast_executions(tenant_id, started_at);
CREATE INDEX IF NOT EXISTS ix_broadcast_executions_status ON broadcast_executions(tenant_id, status);

-- ============================================================================
-- TABLE: DÉTAILS DE LIVRAISON
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_delivery_details (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    execution_id INTEGER NOT NULL REFERENCES broadcast_executions(id) ON DELETE CASCADE,

    -- Destinataire
    recipient_type recipient_type NOT NULL,
    user_id INTEGER,
    email VARCHAR(255),
    phone VARCHAR(20),

    -- Livraison
    channel delivery_channel NOT NULL,
    status delivery_status DEFAULT 'PENDING',

    -- Timing
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,

    -- Engagement
    opened_at TIMESTAMP,
    opened_count INTEGER DEFAULT 0,
    clicked_at TIMESTAMP,
    click_count INTEGER DEFAULT 0,

    -- Erreurs
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,

    -- Tracking
    tracking_id VARCHAR(100),
    user_agent VARCHAR(500),
    ip_address VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_delivery_details_execution ON broadcast_delivery_details(tenant_id, execution_id);
CREATE INDEX IF NOT EXISTS ix_delivery_details_user ON broadcast_delivery_details(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS ix_delivery_details_status ON broadcast_delivery_details(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_delivery_details_tracking ON broadcast_delivery_details(tracking_id);

-- ============================================================================
-- TABLE: PRÉFÉRENCES DE DIFFUSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_preferences (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,

    -- Préférences globales
    receive_digests BOOLEAN DEFAULT true,
    receive_newsletters BOOLEAN DEFAULT true,
    receive_reports BOOLEAN DEFAULT true,
    receive_alerts BOOLEAN DEFAULT true,

    -- Canal préféré
    preferred_channel delivery_channel DEFAULT 'EMAIL',
    preferred_language VARCHAR(5) DEFAULT 'fr',
    preferred_format VARCHAR(20) DEFAULT 'HTML',

    -- Fréquence
    digest_frequency broadcast_frequency DEFAULT 'DAILY',
    report_frequency broadcast_frequency DEFAULT 'WEEKLY',

    -- Horaires
    preferred_send_time VARCHAR(5),
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',

    -- Exclusions
    excluded_content_types JSONB,
    excluded_broadcasts JSONB,

    -- État
    is_unsubscribed_all BOOLEAN DEFAULT false,
    unsubscribed_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_broadcast_preferences_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_broadcast_preferences_tenant ON broadcast_preferences(tenant_id);
CREATE INDEX IF NOT EXISTS ix_broadcast_preferences_user ON broadcast_preferences(tenant_id, user_id);

-- ============================================================================
-- TABLE: MÉTRIQUES DE DIFFUSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS broadcast_metrics (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Période
    metric_date TIMESTAMP NOT NULL,
    period_type VARCHAR(20) DEFAULT 'DAILY',

    -- Volumes
    total_broadcasts INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,

    -- Par type
    digest_count INTEGER DEFAULT 0,
    newsletter_count INTEGER DEFAULT 0,
    report_count INTEGER DEFAULT 0,
    alert_count INTEGER DEFAULT 0,

    -- Par canal
    email_count INTEGER DEFAULT 0,
    in_app_count INTEGER DEFAULT 0,
    webhook_count INTEGER DEFAULT 0,
    sms_count INTEGER DEFAULT 0,

    -- Taux de succès
    delivered_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    delivery_rate FLOAT,

    -- Engagement
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    open_rate FLOAT,
    click_rate FLOAT,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_broadcast_metrics_tenant_date ON broadcast_metrics(tenant_id, metric_date);
CREATE INDEX IF NOT EXISTS ix_broadcast_metrics_period ON broadcast_metrics(tenant_id, period_type, metric_date);

-- ============================================================================
-- TRIGGERS UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_broadcast_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_broadcast_templates_updated ON broadcast_templates;
CREATE TRIGGER trg_broadcast_templates_updated
    BEFORE UPDATE ON broadcast_templates
    FOR EACH ROW EXECUTE FUNCTION update_broadcast_timestamp();

DROP TRIGGER IF EXISTS trg_recipient_lists_updated ON broadcast_recipient_lists;
CREATE TRIGGER trg_recipient_lists_updated
    BEFORE UPDATE ON broadcast_recipient_lists
    FOR EACH ROW EXECUTE FUNCTION update_broadcast_timestamp();

DROP TRIGGER IF EXISTS trg_scheduled_broadcasts_updated ON scheduled_broadcasts;
CREATE TRIGGER trg_scheduled_broadcasts_updated
    BEFORE UPDATE ON scheduled_broadcasts
    FOR EACH ROW EXECUTE FUNCTION update_broadcast_timestamp();

DROP TRIGGER IF EXISTS trg_broadcast_preferences_updated ON broadcast_preferences;
CREATE TRIGGER trg_broadcast_preferences_updated
    BEFORE UPDATE ON broadcast_preferences
    FOR EACH ROW EXECUTE FUNCTION update_broadcast_timestamp();

-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue: Résumé des diffusions actives
CREATE OR REPLACE VIEW v_active_broadcasts AS
SELECT
    sb.tenant_id,
    sb.id,
    sb.code,
    sb.name,
    sb.content_type,
    sb.frequency,
    sb.delivery_channel,
    sb.status,
    sb.total_sent,
    sb.total_delivered,
    sb.last_run_at,
    sb.next_run_at,
    rl.name AS recipient_list_name,
    rl.active_recipients,
    bt.name AS template_name
FROM scheduled_broadcasts sb
LEFT JOIN broadcast_recipient_lists rl ON sb.recipient_list_id = rl.id
LEFT JOIN broadcast_templates bt ON sb.template_id = bt.id
WHERE sb.is_active = true
  AND sb.status IN ('ACTIVE', 'SCHEDULED');

-- Vue: Statistiques par tenant
CREATE OR REPLACE VIEW v_broadcast_stats AS
SELECT
    tenant_id,
    COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_broadcasts,
    COUNT(*) FILTER (WHERE status = 'PAUSED') AS paused_broadcasts,
    COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed_broadcasts,
    SUM(total_sent) AS total_messages_sent,
    SUM(total_delivered) AS total_messages_delivered,
    SUM(total_opened) AS total_messages_opened,
    CASE
        WHEN SUM(total_sent) > 0
        THEN ROUND((SUM(total_delivered)::numeric / SUM(total_sent) * 100), 2)
        ELSE 0
    END AS delivery_rate,
    CASE
        WHEN SUM(total_delivered) > 0
        THEN ROUND((SUM(total_opened)::numeric / SUM(total_delivered) * 100), 2)
        ELSE 0
    END AS open_rate
FROM scheduled_broadcasts
GROUP BY tenant_id;

-- ============================================================================
-- TEMPLATES SYSTÈME
-- ============================================================================

-- Template: Digest quotidien
INSERT INTO broadcast_templates (tenant_id, code, name, description, content_type, subject_template, body_template, default_channel, language, is_active, is_system)
VALUES
    ('SYSTEM', 'DAILY_DIGEST', 'Digest Quotidien', 'Résumé quotidien des activités et KPIs', 'DIGEST',
     'AZALS - Votre résumé du {{date}}',
     E'Bonjour {{user.name}},\n\nVoici votre résumé quotidien:\n\n{{#each kpis}}\n- {{name}}: {{value}}\n{{/each}}\n\nCordialement,\nL''équipe AZALS',
     'EMAIL', 'fr', true, true),

    ('SYSTEM', 'WEEKLY_REPORT', 'Rapport Hebdomadaire', 'Rapport de performance hebdomadaire', 'REPORT',
     'AZALS - Rapport Semaine {{week_number}}',
     E'Bonjour {{user.name}},\n\nVoici votre rapport hebdomadaire.\n\n{{report_content}}\n\nCordialement,\nL''équipe AZALS',
     'EMAIL', 'fr', true, true),

    ('SYSTEM', 'MONTHLY_KPI', 'KPIs Mensuels', 'Tableau de bord KPIs du mois', 'KPI_SUMMARY',
     'AZALS - KPIs du mois de {{month_name}}',
     E'Bonjour {{user.name}},\n\nVoici vos indicateurs clés du mois:\n\n{{#each metrics}}\n{{category}}:\n{{#each items}}\n  - {{name}}: {{value}} ({{trend}})\n{{/each}}\n{{/each}}\n\nCordialement,\nL''équipe AZALS',
     'EMAIL', 'fr', true, true),

    ('SYSTEM', 'ALERT_CRITICAL', 'Alerte Critique', 'Notification d''alerte critique', 'ALERT',
     '⚠️ AZALS - Alerte Critique: {{alert.title}}',
     E'ATTENTION\n\n{{alert.message}}\n\nDétails:\n{{alert.details}}\n\nAction requise: {{alert.action}}\n\nL''équipe AZALS',
     'EMAIL', 'fr', true, true),

    ('SYSTEM', 'NEWSLETTER', 'Newsletter Générale', 'Template newsletter personnalisable', 'NEWSLETTER',
     '{{newsletter.title}}',
     E'{{newsletter.content}}',
     'EMAIL', 'fr', true, true)
ON CONFLICT (tenant_id, code) DO NOTHING;

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE broadcast_templates IS 'Templates réutilisables pour les diffusions';
COMMENT ON TABLE broadcast_recipient_lists IS 'Listes de destinataires pour les diffusions';
COMMENT ON TABLE broadcast_recipient_members IS 'Membres des listes de destinataires';
COMMENT ON TABLE scheduled_broadcasts IS 'Diffusions programmées et récurrentes';
COMMENT ON TABLE broadcast_executions IS 'Historique des exécutions de diffusion';
COMMENT ON TABLE broadcast_delivery_details IS 'Détails de livraison par destinataire';
COMMENT ON TABLE broadcast_preferences IS 'Préférences de diffusion par utilisateur';
COMMENT ON TABLE broadcast_metrics IS 'Métriques agrégées de diffusion';

-- ============================================================================
-- FIN MIGRATION T6
-- ============================================================================
