-- ============================================================================
-- AZALS MODULE GUARDIAN - Migration Correction Automatique Gouvernée
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-08
-- Description: Tables pour le système de correction automatique gouvernée
--              et auditable (GUARDIAN)
--
-- PRINCIPES FONDAMENTAUX:
-- - Aucune correction non explicable
-- - Aucune correction non traçable
-- - Aucune correction non justifiable
-- - Registre append-only obligatoire
-- - Tests post-correction obligatoires
--
-- GUARDIAN agit. GUARDIAN explique. GUARDIAN assume.
-- ============================================================================


-- ============================================================================
-- TYPES ENUM GUARDIAN
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE guardian_error_severity AS ENUM (
        'CRITICAL', 'MAJOR', 'MINOR', 'WARNING', 'INFO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_error_source AS ENUM (
        'FRONTEND_LOG', 'BACKEND_LOG', 'SYSTEM_ALERT', 'DATABASE_ERROR',
        'API_ERROR', 'SECURITY_ALERT', 'PERFORMANCE_ALERT', 'SCHEDULED_CHECK',
        'USER_REPORT', 'EXTERNAL_WEBHOOK'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_error_type AS ENUM (
        'EXCEPTION', 'VALIDATION', 'AUTHENTICATION', 'AUTHORIZATION',
        'DATABASE', 'NETWORK', 'TIMEOUT', 'RATE_LIMIT', 'CONFIGURATION',
        'DATA_INTEGRITY', 'BUSINESS_LOGIC', 'DEPENDENCY', 'MEMORY',
        'STORAGE', 'UNKNOWN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_correction_status AS ENUM (
        'PENDING', 'ANALYZING', 'PROPOSED', 'APPROVED', 'IN_PROGRESS',
        'TESTING', 'APPLIED', 'FAILED', 'ROLLED_BACK', 'REJECTED',
        'DEFERRED', 'BLOCKED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_correction_action AS ENUM (
        'AUTO_FIX', 'CONFIG_UPDATE', 'CACHE_CLEAR', 'SERVICE_RESTART',
        'DATABASE_REPAIR', 'DATA_MIGRATION', 'PERMISSION_FIX',
        'DEPENDENCY_UPDATE', 'ROLLBACK', 'MANUAL_INTERVENTION',
        'WORKAROUND', 'MONITORING_ONLY', 'ESCALATION'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_test_result AS ENUM (
        'PASSED', 'FAILED', 'SKIPPED', 'ERROR', 'TIMEOUT', 'NOT_APPLICABLE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE guardian_environment AS ENUM (
        'SANDBOX', 'BETA', 'PRODUCTION'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- TABLE: DÉTECTIONS D'ERREURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS guardian_error_detections (
    id BIGSERIAL PRIMARY KEY,
    error_uid VARCHAR(36) NOT NULL UNIQUE,
    tenant_id VARCHAR(255) NOT NULL,

    -- Classification
    severity guardian_error_severity NOT NULL,
    source guardian_error_source NOT NULL,
    error_type guardian_error_type NOT NULL,
    environment guardian_environment NOT NULL,

    -- Localisation
    module VARCHAR(100),
    route VARCHAR(500),
    component VARCHAR(200),
    function_name VARCHAR(200),
    line_number INTEGER,
    file_path VARCHAR(500),

    -- Contexte utilisateur (pseudonymisé pour RGPD)
    user_role VARCHAR(50),
    user_id_hash VARCHAR(64),
    session_id_hash VARCHAR(64),

    -- Détails de l'erreur
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    request_id VARCHAR(255),
    correlation_id VARCHAR(255),

    -- Contexte technique (JSONB)
    context_data JSONB,
    http_status INTEGER,
    http_method VARCHAR(10),

    -- Récurrence
    occurrence_count INTEGER DEFAULT 1 NOT NULL,
    first_occurrence_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_occurrence_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Statut de traitement
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    is_acknowledged BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP,

    -- Relation avec correction
    correction_id BIGINT,

    -- Timestamp
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guardian_errors_uid ON guardian_error_detections(error_uid);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_tenant ON guardian_error_detections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_severity ON guardian_error_detections(severity);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_source ON guardian_error_detections(source);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_type ON guardian_error_detections(error_type);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_env ON guardian_error_detections(environment);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_module ON guardian_error_detections(module);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_processed ON guardian_error_detections(is_processed);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_tenant_detected ON guardian_error_detections(tenant_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_severity_env ON guardian_error_detections(severity, environment);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_module_type ON guardian_error_detections(module, error_type);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_error_code ON guardian_error_detections(error_code);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_correlation ON guardian_error_detections(correlation_id);
CREATE INDEX IF NOT EXISTS idx_guardian_errors_request ON guardian_error_detections(request_id);


-- ============================================================================
-- TABLE: REGISTRE DES CORRECTIONS (APPEND-ONLY)
-- ============================================================================
-- IMPORTANT: Ce registre est IMMUABLE. Seuls les INSERT sont autorisés.
-- Les UPDATE et DELETE sont INTERDITS par trigger.

CREATE TABLE IF NOT EXISTS guardian_correction_registry (
    id BIGSERIAL PRIMARY KEY,
    correction_uid VARCHAR(36) NOT NULL UNIQUE,
    tenant_id VARCHAR(255) NOT NULL,

    -- Horodatage précis (server-side pour garantie)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Environnement concerné
    environment guardian_environment NOT NULL,

    -- Source de l'erreur
    error_source guardian_error_source NOT NULL,
    error_detection_id BIGINT,

    -- Type d'erreur détectée
    error_type guardian_error_type NOT NULL,

    -- Niveau de gravité
    severity guardian_error_severity NOT NULL,

    -- Module concerné
    module VARCHAR(100) NOT NULL,

    -- Route, composant ou fonction impactée
    route VARCHAR(500),
    component VARCHAR(200),
    function_impacted VARCHAR(200),

    -- Rôle utilisateur concerné
    affected_user_role VARCHAR(50),

    -- Cause probable identifiée (OBLIGATOIRE)
    probable_cause TEXT NOT NULL,

    -- Action corrective (OBLIGATOIRE)
    correction_action guardian_correction_action NOT NULL,
    correction_description TEXT NOT NULL,
    correction_details JSONB,

    -- Impact estimé (OBLIGATOIRE)
    estimated_impact TEXT NOT NULL,
    impact_scope VARCHAR(100),
    affected_entities_count INTEGER,

    -- Réversibilité (OBLIGATOIRE)
    is_reversible BOOLEAN NOT NULL,
    reversibility_justification TEXT NOT NULL,
    rollback_procedure TEXT,

    -- Tests exécutés
    tests_executed JSONB,

    -- Résultat de la correction
    correction_result TEXT,
    correction_successful BOOLEAN,

    -- Statut final
    status guardian_correction_status NOT NULL,

    -- Erreur originale
    original_error_message TEXT,
    original_error_code VARCHAR(50),
    original_stack_trace TEXT,

    -- Validation humaine
    requires_human_validation BOOLEAN DEFAULT FALSE NOT NULL,
    validated_by INTEGER,
    validated_at TIMESTAMP,
    validation_comment TEXT,

    -- Exécution
    executed_by VARCHAR(100),
    executed_at TIMESTAMP,
    execution_duration_ms FLOAT,

    -- Rollback
    rolled_back BOOLEAN DEFAULT FALSE NOT NULL,
    rollback_at TIMESTAMP,
    rollback_reason TEXT,
    rollback_by VARCHAR(100),

    -- Audit trail (JSONB append-only)
    decision_trail JSONB
);

CREATE INDEX IF NOT EXISTS idx_guardian_registry_uid ON guardian_correction_registry(correction_uid);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_tenant ON guardian_correction_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_created ON guardian_correction_registry(created_at);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_env ON guardian_correction_registry(environment);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_status ON guardian_correction_registry(status);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_severity ON guardian_correction_registry(severity);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_module ON guardian_correction_registry(module);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_tenant_created ON guardian_correction_registry(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_env_status ON guardian_correction_registry(environment, status);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_severity_module ON guardian_correction_registry(severity, module);
CREATE INDEX IF NOT EXISTS idx_guardian_registry_requires_validation ON guardian_correction_registry(requires_human_validation, status);

-- Ajouter la clé étrangère vers error_detections
ALTER TABLE guardian_error_detections
    ADD CONSTRAINT fk_guardian_error_correction
    FOREIGN KEY (correction_id)
    REFERENCES guardian_correction_registry(id)
    ON DELETE SET NULL;


-- ============================================================================
-- TABLE: RÈGLES DE CORRECTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS guardian_correction_rules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    rule_uid VARCHAR(36) NOT NULL UNIQUE,

    -- Identification
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0' NOT NULL,

    -- Conditions de déclenchement
    trigger_error_type guardian_error_type,
    trigger_error_code VARCHAR(50),
    trigger_module VARCHAR(100),
    trigger_severity_min guardian_error_severity,
    trigger_conditions JSONB,

    -- Action
    correction_action guardian_correction_action NOT NULL,
    action_config JSONB,
    action_script TEXT,

    -- Environnements autorisés
    allowed_environments JSONB NOT NULL,

    -- Seuils et limites
    max_auto_corrections_per_hour INTEGER DEFAULT 10 NOT NULL,
    cooldown_seconds INTEGER DEFAULT 60 NOT NULL,
    requires_human_validation BOOLEAN DEFAULT FALSE NOT NULL,

    -- Évaluation des risques
    risk_level VARCHAR(20) DEFAULT 'LOW' NOT NULL,
    is_reversible BOOLEAN DEFAULT TRUE NOT NULL,

    -- Tests requis
    required_tests JSONB,

    -- Statistiques
    total_executions INTEGER DEFAULT 0 NOT NULL,
    successful_executions INTEGER DEFAULT 0 NOT NULL,
    failed_executions INTEGER DEFAULT 0 NOT NULL,
    last_execution_at TIMESTAMP,

    -- Statut
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system_rule BOOLEAN DEFAULT FALSE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_guardian_rules_uid ON guardian_correction_rules(rule_uid);
CREATE INDEX IF NOT EXISTS idx_guardian_rules_tenant ON guardian_correction_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_guardian_rules_active ON guardian_correction_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_guardian_rules_trigger ON guardian_correction_rules(trigger_error_type, trigger_module);


-- ============================================================================
-- TABLE: TESTS POST-CORRECTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS guardian_correction_tests (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    -- Lien avec correction
    correction_id BIGINT NOT NULL REFERENCES guardian_correction_registry(id) ON DELETE CASCADE,

    -- Test identifiant
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(50) NOT NULL,

    -- Configuration
    test_config JSONB,
    test_input JSONB,

    -- Exécution
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms FLOAT,

    -- Résultat
    result guardian_test_result NOT NULL,
    result_details JSONB,
    expected_output JSONB,
    actual_output JSONB,

    -- Erreur
    error_message TEXT,
    error_trace TEXT,

    -- Impact sur correction
    triggers_rollback BOOLEAN DEFAULT FALSE NOT NULL,
    blocking BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guardian_tests_tenant ON guardian_correction_tests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_guardian_tests_correction ON guardian_correction_tests(correction_id);
CREATE INDEX IF NOT EXISTS idx_guardian_tests_result ON guardian_correction_tests(result);


-- ============================================================================
-- TABLE: ALERTES GUARDIAN
-- ============================================================================

CREATE TABLE IF NOT EXISTS guardian_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_uid VARCHAR(36) NOT NULL UNIQUE,
    tenant_id VARCHAR(255) NOT NULL,

    -- Type d'alerte
    alert_type VARCHAR(50) NOT NULL,
    severity guardian_error_severity NOT NULL,

    -- Contenu
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,

    -- Liens
    error_detection_id BIGINT,
    correction_id BIGINT,

    -- Destinataires
    target_roles JSONB,
    target_users JSONB,

    -- Statut
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_by INTEGER,
    read_at TIMESTAMP,

    is_acknowledged BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP,

    is_resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_by INTEGER,
    resolved_at TIMESTAMP,
    resolution_comment TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guardian_alerts_uid ON guardian_alerts(alert_uid);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_tenant ON guardian_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_type ON guardian_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_severity ON guardian_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_read ON guardian_alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_resolved ON guardian_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_tenant_created ON guardian_alerts(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_guardian_alerts_unread ON guardian_alerts(is_read, is_resolved);


-- ============================================================================
-- TABLE: CONFIGURATION GUARDIAN PAR TENANT
-- ============================================================================

CREATE TABLE IF NOT EXISTS guardian_config (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL UNIQUE,

    -- Activation
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    auto_correction_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Environnements autorisés
    auto_correction_environments JSONB DEFAULT '["SANDBOX", "BETA"]',

    -- Seuils
    max_auto_corrections_per_day INTEGER DEFAULT 100 NOT NULL,
    max_auto_corrections_production INTEGER DEFAULT 10 NOT NULL,
    cooldown_between_corrections_seconds INTEGER DEFAULT 30 NOT NULL,

    -- Notifications
    alert_on_critical BOOLEAN DEFAULT TRUE NOT NULL,
    alert_on_major BOOLEAN DEFAULT TRUE NOT NULL,
    alert_on_correction_failed BOOLEAN DEFAULT TRUE NOT NULL,
    alert_on_rollback BOOLEAN DEFAULT TRUE NOT NULL,

    -- Rétention des données (RGPD)
    error_retention_days INTEGER DEFAULT 90 NOT NULL,
    correction_retention_days INTEGER DEFAULT 3650 NOT NULL,  -- 10 ans légal
    alert_retention_days INTEGER DEFAULT 180 NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_guardian_config_tenant ON guardian_config(tenant_id);


-- ============================================================================
-- TRIGGER: PROTECTION APPEND-ONLY DU REGISTRE
-- ============================================================================
-- Ce trigger empêche toute modification ou suppression dans le registre

CREATE OR REPLACE FUNCTION guardian_registry_protect_immutable()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Seuls certains champs peuvent être mis à jour (statut, résultat, rollback)
        -- Mais JAMAIS les champs d'audit originaux
        IF OLD.correction_uid != NEW.correction_uid OR
           OLD.tenant_id != NEW.tenant_id OR
           OLD.created_at != NEW.created_at OR
           OLD.environment != NEW.environment OR
           OLD.error_source != NEW.error_source OR
           OLD.error_type != NEW.error_type OR
           OLD.severity != NEW.severity OR
           OLD.module != NEW.module OR
           OLD.probable_cause != NEW.probable_cause OR
           OLD.correction_action != NEW.correction_action OR
           OLD.correction_description != NEW.correction_description OR
           OLD.estimated_impact != NEW.estimated_impact OR
           OLD.is_reversible != NEW.is_reversible OR
           OLD.reversibility_justification != NEW.reversibility_justification
        THEN
            RAISE EXCEPTION 'GUARDIAN: Les champs d''audit du registre sont immuables';
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'GUARDIAN: Les suppressions sont interdites dans le registre des corrections';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_guardian_registry_protect ON guardian_correction_registry;
CREATE TRIGGER trigger_guardian_registry_protect
    BEFORE UPDATE OR DELETE ON guardian_correction_registry
    FOR EACH ROW
    EXECUTE FUNCTION guardian_registry_protect_immutable();


-- ============================================================================
-- TRIGGER: AUTO-UPDATE TIMESTAMPS
-- ============================================================================

CREATE OR REPLACE FUNCTION guardian_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_guardian_rules_updated ON guardian_correction_rules;
CREATE TRIGGER trigger_guardian_rules_updated
    BEFORE UPDATE ON guardian_correction_rules
    FOR EACH ROW
    EXECUTE FUNCTION guardian_update_timestamp();

DROP TRIGGER IF EXISTS trigger_guardian_config_updated ON guardian_config;
CREATE TRIGGER trigger_guardian_config_updated
    BEFORE UPDATE ON guardian_config
    FOR EACH ROW
    EXECUTE FUNCTION guardian_update_timestamp();


-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue des erreurs non traitées par tenant
CREATE OR REPLACE VIEW v_guardian_pending_errors AS
SELECT
    e.*,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - e.detected_at)) / 60 AS minutes_since_detection
FROM guardian_error_detections e
WHERE e.is_processed = FALSE
ORDER BY
    CASE e.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'MAJOR' THEN 2
        WHEN 'MINOR' THEN 3
        WHEN 'WARNING' THEN 4
        ELSE 5
    END,
    e.detected_at DESC;


-- Vue des corrections en attente de validation
CREATE OR REPLACE VIEW v_guardian_pending_validations AS
SELECT
    r.*,
    e.error_message,
    e.occurrence_count
FROM guardian_correction_registry r
LEFT JOIN guardian_error_detections e ON r.error_detection_id = e.id
WHERE r.requires_human_validation = TRUE
  AND r.status IN ('BLOCKED', 'PROPOSED')
ORDER BY
    CASE r.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'MAJOR' THEN 2
        WHEN 'MINOR' THEN 3
        ELSE 4
    END,
    r.created_at DESC;


-- Vue des statistiques GUARDIAN par tenant
CREATE OR REPLACE VIEW v_guardian_stats AS
SELECT
    tenant_id,
    DATE(created_at) as stat_date,
    COUNT(*) as total_corrections,
    SUM(CASE WHEN correction_successful = TRUE THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN correction_successful = FALSE THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN rolled_back = TRUE THEN 1 ELSE 0 END) as rolled_back,
    SUM(CASE WHEN executed_by = 'GUARDIAN' THEN 1 ELSE 0 END) as auto_corrections,
    AVG(execution_duration_ms) as avg_duration_ms
FROM guardian_correction_registry
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY tenant_id, DATE(created_at)
ORDER BY tenant_id, stat_date DESC;


-- ============================================================================
-- RÈGLES SYSTÈME PAR DÉFAUT
-- ============================================================================

INSERT INTO guardian_correction_rules (
    tenant_id, rule_uid, name, description,
    trigger_error_type, correction_action,
    allowed_environments, risk_level, is_reversible,
    required_tests, is_system_rule, is_active
) VALUES
(
    'SYSTEM',
    'guardian-rule-rate-limit-001',
    'Rate Limit Auto-Recovery',
    'Réinitialise automatiquement les compteurs de rate limiting après détection',
    'RATE_LIMIT',
    'CACHE_CLEAR',
    '["SANDBOX", "BETA"]',
    'LOW',
    TRUE,
    '["SCENARIO"]',
    TRUE,
    TRUE
),
(
    'SYSTEM',
    'guardian-rule-cache-error-001',
    'Cache Error Auto-Clear',
    'Vide le cache en cas d''erreur de désérialisation',
    'EXCEPTION',
    'CACHE_CLEAR',
    '["SANDBOX", "BETA", "PRODUCTION"]',
    'LOW',
    TRUE,
    '["SCENARIO", "REGRESSION"]',
    TRUE,
    TRUE
),
(
    'SYSTEM',
    'guardian-rule-critical-alert-001',
    'Critical Error Escalation',
    'Escalade automatique vers les administrateurs pour erreurs critiques',
    'EXCEPTION',
    'ESCALATION',
    '["SANDBOX", "BETA", "PRODUCTION"]',
    'LOW',
    TRUE,
    '[]',
    TRUE,
    TRUE
),
(
    'SYSTEM',
    'guardian-rule-auth-monitor-001',
    'Authentication Monitoring',
    'Surveillance des erreurs d''authentification',
    'AUTHENTICATION',
    'MONITORING_ONLY',
    '["SANDBOX", "BETA", "PRODUCTION"]',
    'LOW',
    TRUE,
    '[]',
    TRUE,
    TRUE
)
ON CONFLICT (rule_uid) DO NOTHING;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE guardian_error_detections IS 'Erreurs détectées par GUARDIAN pour analyse et correction';
COMMENT ON TABLE guardian_correction_registry IS 'Registre APPEND-ONLY des corrections - preuve d''audit';
COMMENT ON TABLE guardian_correction_rules IS 'Règles de correction automatique configurables';
COMMENT ON TABLE guardian_correction_tests IS 'Tests post-correction pour validation';
COMMENT ON TABLE guardian_alerts IS 'Alertes GUARDIAN pour notification';
COMMENT ON TABLE guardian_config IS 'Configuration GUARDIAN par tenant';

COMMENT ON COLUMN guardian_correction_registry.probable_cause IS 'Cause probable identifiée - OBLIGATOIRE pour audit';
COMMENT ON COLUMN guardian_correction_registry.estimated_impact IS 'Impact estimé - OBLIGATOIRE pour audit';
COMMENT ON COLUMN guardian_correction_registry.reversibility_justification IS 'Justification réversibilité - OBLIGATOIRE pour audit';
COMMENT ON COLUMN guardian_correction_registry.decision_trail IS 'Historique des décisions - APPEND-ONLY';


-- ============================================================================
-- FIN MIGRATION GUARDIAN
-- ============================================================================
