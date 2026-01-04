-- ============================================================================
-- AZALS MODULE T2 - Migration Système de Déclencheurs & Diffusion
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-03
-- Description: Tables pour le système de triggers, notifications et rapports
-- ============================================================================

-- Types ENUM
DO $$ BEGIN
    CREATE TYPE trigger_type AS ENUM ('THRESHOLD', 'CONDITION', 'SCHEDULED', 'EVENT', 'MANUAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE trigger_status AS ENUM ('ACTIVE', 'PAUSED', 'DISABLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE condition_operator AS ENUM ('eq', 'ne', 'gt', 'ge', 'lt', 'le', 'in', 'not_in', 'contains', 'starts_with', 'ends_with', 'between', 'is_null', 'is_not_null');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('EMAIL', 'WEBHOOK', 'IN_APP', 'SMS', 'SLACK', 'TEAMS');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_status AS ENUM ('PENDING', 'SENT', 'FAILED', 'DELIVERED', 'READ');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE report_frequency AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE escalation_level AS ENUM ('L1', 'L2', 'L3', 'L4');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- TABLES PRINCIPALES
-- ============================================================================

-- Table des templates de notification
CREATE TABLE IF NOT EXISTS triggers_templates (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    subject_template VARCHAR(500),
    body_template TEXT NOT NULL,
    body_html TEXT,

    available_variables TEXT,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_template_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_templates_tenant ON triggers_templates(tenant_id);


-- Table des définitions de triggers
CREATE TABLE IF NOT EXISTS triggers_definitions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    trigger_type trigger_type NOT NULL,
    status trigger_status DEFAULT 'ACTIVE' NOT NULL,

    source_module VARCHAR(50) NOT NULL,
    source_entity VARCHAR(100),
    source_field VARCHAR(100),

    condition TEXT NOT NULL,

    threshold_value VARCHAR(255),
    threshold_operator condition_operator,

    schedule_cron VARCHAR(100),
    schedule_timezone VARCHAR(50) DEFAULT 'Europe/Paris',

    severity alert_severity DEFAULT 'WARNING' NOT NULL,
    escalation_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    escalation_delay_minutes INTEGER DEFAULT 60,
    escalation_level escalation_level DEFAULT 'L1',

    action_template_id INTEGER REFERENCES triggers_templates(id),

    cooldown_minutes INTEGER DEFAULT 60 NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0 NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_trigger_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_triggers_tenant ON triggers_definitions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_triggers_module ON triggers_definitions(source_module);
CREATE INDEX IF NOT EXISTS idx_triggers_status ON triggers_definitions(status);
CREATE INDEX IF NOT EXISTS idx_triggers_type ON triggers_definitions(trigger_type);


-- Table des abonnements
CREATE TABLE IF NOT EXISTS triggers_subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    trigger_id INTEGER REFERENCES triggers_definitions(id) ON DELETE CASCADE NOT NULL,

    user_id INTEGER,
    role_code VARCHAR(50),
    group_code VARCHAR(50),
    email_external VARCHAR(255),

    channel notification_channel DEFAULT 'IN_APP' NOT NULL,
    channel_config TEXT,

    escalation_level escalation_level DEFAULT 'L1' NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON triggers_subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_trigger ON triggers_subscriptions(trigger_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON triggers_subscriptions(user_id);


-- Table des événements de déclenchement
CREATE TABLE IF NOT EXISTS triggers_events (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    trigger_id INTEGER REFERENCES triggers_definitions(id) ON DELETE CASCADE NOT NULL,

    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    triggered_value TEXT,
    condition_details TEXT,

    severity alert_severity NOT NULL,

    escalation_level escalation_level DEFAULT 'L1' NOT NULL,
    escalated_at TIMESTAMP,

    resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_tenant ON triggers_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_events_trigger ON triggers_events(trigger_id);
CREATE INDEX IF NOT EXISTS idx_events_triggered_at ON triggers_events(triggered_at);
CREATE INDEX IF NOT EXISTS idx_events_resolved ON triggers_events(resolved);


-- Table des notifications
CREATE TABLE IF NOT EXISTS triggers_notifications (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    event_id INTEGER REFERENCES triggers_events(id) ON DELETE CASCADE NOT NULL,

    user_id INTEGER,
    email VARCHAR(255),

    channel notification_channel NOT NULL,
    subject VARCHAR(500),
    body TEXT NOT NULL,

    status notification_status DEFAULT 'PENDING' NOT NULL,

    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason TEXT,

    retry_count INTEGER DEFAULT 0 NOT NULL,
    next_retry_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_tenant ON triggers_notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notifications_event ON triggers_notifications(event_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON triggers_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON triggers_notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON triggers_notifications(sent_at);


-- Table des rapports planifiés
CREATE TABLE IF NOT EXISTS triggers_scheduled_reports (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    report_type VARCHAR(50) NOT NULL,
    report_config TEXT,

    frequency report_frequency NOT NULL,
    schedule_day INTEGER,
    schedule_time VARCHAR(5),
    schedule_timezone VARCHAR(50) DEFAULT 'Europe/Paris' NOT NULL,
    schedule_cron VARCHAR(100),

    recipients TEXT NOT NULL,

    output_format VARCHAR(20) DEFAULT 'PDF' NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    last_generated_at TIMESTAMP,
    next_generation_at TIMESTAMP,
    generation_count INTEGER DEFAULT 0 NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_report_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_reports_tenant ON triggers_scheduled_reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reports_frequency ON triggers_scheduled_reports(frequency);
CREATE INDEX IF NOT EXISTS idx_reports_next ON triggers_scheduled_reports(next_generation_at);


-- Table de l'historique des rapports
CREATE TABLE IF NOT EXISTS triggers_report_history (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    report_id INTEGER REFERENCES triggers_scheduled_reports(id) ON DELETE CASCADE NOT NULL,

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    generated_by INTEGER,

    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    file_format VARCHAR(20) NOT NULL,

    sent_to TEXT,
    sent_at TIMESTAMP,

    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_report_history_tenant ON triggers_report_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_report_history_report ON triggers_report_history(report_id);
CREATE INDEX IF NOT EXISTS idx_report_history_generated ON triggers_report_history(generated_at);


-- Table des webhooks
CREATE TABLE IF NOT EXISTS triggers_webhooks (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    url VARCHAR(500) NOT NULL,
    method VARCHAR(10) DEFAULT 'POST' NOT NULL,
    headers TEXT,
    auth_type VARCHAR(20),
    auth_config TEXT,

    max_retries INTEGER DEFAULT 3 NOT NULL,
    retry_delay_seconds INTEGER DEFAULT 60 NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0 NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_webhook_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_webhooks_tenant ON triggers_webhooks(tenant_id);


-- Table des logs
CREATE TABLE IF NOT EXISTS triggers_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,

    details TEXT,

    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trigger_logs_tenant ON triggers_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_trigger_logs_action ON triggers_logs(action);
CREATE INDEX IF NOT EXISTS idx_trigger_logs_created ON triggers_logs(created_at);


-- ============================================================================
-- TRIGGERS (Auto-update timestamps)
-- ============================================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_triggers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour auto-update
DROP TRIGGER IF EXISTS trigger_update_triggers_definitions ON triggers_definitions;
CREATE TRIGGER trigger_update_triggers_definitions
    BEFORE UPDATE ON triggers_definitions
    FOR EACH ROW
    EXECUTE FUNCTION update_triggers_updated_at();

DROP TRIGGER IF EXISTS trigger_update_triggers_templates ON triggers_templates;
CREATE TRIGGER trigger_update_triggers_templates
    BEFORE UPDATE ON triggers_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_triggers_updated_at();

DROP TRIGGER IF EXISTS trigger_update_triggers_reports ON triggers_scheduled_reports;
CREATE TRIGGER trigger_update_triggers_reports
    BEFORE UPDATE ON triggers_scheduled_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_triggers_updated_at();

DROP TRIGGER IF EXISTS trigger_update_triggers_webhooks ON triggers_webhooks;
CREATE TRIGGER trigger_update_triggers_webhooks
    BEFORE UPDATE ON triggers_webhooks
    FOR EACH ROW
    EXECUTE FUNCTION update_triggers_updated_at();


-- ============================================================================
-- DONNÉES INITIALES - Templates système
-- ============================================================================

-- Templates système par défaut (pour tous les tenants, sera copié)
INSERT INTO triggers_templates (tenant_id, code, name, description, subject_template, body_template, body_html, available_variables, is_system)
VALUES
    ('SYSTEM', 'ALERT_DEFAULT', 'Alerte Standard', 'Template par défaut pour les alertes',
     '[{{severity}}] {{trigger_name}}',
     E'Alerte AZALS\n\nTrigger: {{trigger_name}}\nCode: {{trigger_code}}\nSévérité: {{severity}}\nModule: {{source_module}}\nValeur déclenchante: {{triggered_value}}\nDate: {{triggered_at}}\n\n---\nMessage automatique AZALS',
     '<h2>Alerte AZALS</h2><p><strong>Trigger:</strong> {{trigger_name}}</p><p><strong>Sévérité:</strong> {{severity}}</p><p><strong>Module:</strong> {{source_module}}</p><p><strong>Valeur:</strong> {{triggered_value}}</p><p><strong>Date:</strong> {{triggered_at}}</p>',
     '["trigger_name","trigger_code","severity","source_module","triggered_value","triggered_at"]',
     TRUE),

    ('SYSTEM', 'ESCALATION', 'Escalade', 'Template pour les escalades',
     '[ESCALADE {{escalation_level}}] {{trigger_name}}',
     E'ESCALADE AZALS\n\nCet événement a été escaladé au niveau {{escalation_level}}.\n\nTrigger: {{trigger_name}}\nSévérité: {{severity}}\nValeur: {{triggered_value}}\nDéclenché le: {{triggered_at}}\n\nAction requise immédiatement.\n\n---\nMessage automatique AZALS',
     '<h2 style="color:red">ESCALADE AZALS</h2><p>Cet événement a été escaladé au niveau <strong>{{escalation_level}}</strong>.</p>',
     '["trigger_name","trigger_code","severity","escalation_level","triggered_value","triggered_at"]',
     TRUE),

    ('SYSTEM', 'REPORT_READY', 'Rapport Disponible', 'Template pour les rapports générés',
     'Rapport {{report_name}} disponible',
     E'Votre rapport AZALS est disponible.\n\nNom: {{report_name}}\nType: {{report_type}}\nFormat: {{output_format}}\nGénéré le: {{generated_at}}\n\n---\nMessage automatique AZALS',
     '<h2>Rapport AZALS disponible</h2><p><strong>{{report_name}}</strong> ({{report_type}})</p><p>Format: {{output_format}}</p>',
     '["report_name","report_type","output_format","generated_at"]',
     TRUE)
ON CONFLICT (tenant_id, code) DO NOTHING;


-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue des événements non résolus
CREATE OR REPLACE VIEW v_triggers_unresolved_events AS
SELECT
    e.*,
    t.code as trigger_code,
    t.name as trigger_name,
    t.source_module,
    t.source_entity
FROM triggers_events e
JOIN triggers_definitions t ON e.trigger_id = t.id
WHERE e.resolved = FALSE
ORDER BY
    CASE e.severity
        WHEN 'EMERGENCY' THEN 1
        WHEN 'CRITICAL' THEN 2
        WHEN 'WARNING' THEN 3
        ELSE 4
    END,
    e.triggered_at DESC;


-- Vue des statistiques par tenant
CREATE OR REPLACE VIEW v_triggers_stats AS
SELECT
    t.tenant_id,
    COUNT(DISTINCT t.id) as total_triggers,
    COUNT(DISTINCT CASE WHEN t.status = 'ACTIVE' THEN t.id END) as active_triggers,
    COUNT(DISTINCT e.id) as total_events,
    COUNT(DISTINCT CASE WHEN e.resolved = FALSE THEN e.id END) as unresolved_events,
    COUNT(DISTINCT CASE WHEN e.severity IN ('CRITICAL', 'EMERGENCY') AND e.resolved = FALSE THEN e.id END) as critical_events
FROM triggers_definitions t
LEFT JOIN triggers_events e ON t.id = e.trigger_id AND e.tenant_id = t.tenant_id
GROUP BY t.tenant_id;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE triggers_definitions IS 'Définitions des déclencheurs (triggers)';
COMMENT ON TABLE triggers_subscriptions IS 'Abonnements aux triggers';
COMMENT ON TABLE triggers_events IS 'Événements de déclenchement';
COMMENT ON TABLE triggers_notifications IS 'Notifications envoyées';
COMMENT ON TABLE triggers_templates IS 'Templates de notification';
COMMENT ON TABLE triggers_scheduled_reports IS 'Rapports planifiés';
COMMENT ON TABLE triggers_report_history IS 'Historique des rapports générés';
COMMENT ON TABLE triggers_webhooks IS 'Configuration des webhooks';
COMMENT ON TABLE triggers_logs IS 'Logs du système de triggers';


-- ============================================================================
-- FIN MIGRATION
-- ============================================================================
