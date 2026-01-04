-- ============================================================================
-- AZALS MODULE T3 - Migration Audit & Benchmark Évolutif
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-03
-- Description: Tables pour l'audit centralisé et les benchmarks
-- ============================================================================

-- Types ENUM
DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM (
        'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT',
        'EXPORT', 'IMPORT', 'VALIDATE', 'REJECT', 'APPROVE',
        'SUBMIT', 'CANCEL', 'ARCHIVE', 'RESTORE', 'CONFIGURE', 'EXECUTE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE audit_level AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE audit_category AS ENUM (
        'SECURITY', 'BUSINESS', 'SYSTEM', 'DATA', 'COMPLIANCE', 'PERFORMANCE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE metric_type AS ENUM ('COUNTER', 'GAUGE', 'HISTOGRAM', 'TIMER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE benchmark_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE retention_policy AS ENUM (
        'IMMEDIATE', 'SHORT', 'MEDIUM', 'LONG', 'PERMANENT', 'LEGAL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE compliance_framework AS ENUM (
        'GDPR', 'SOC2', 'ISO27001', 'HIPAA', 'PCI_DSS', 'CUSTOM'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- TABLE PRINCIPALE - LOGS D'AUDIT
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    action audit_action NOT NULL,
    level audit_level DEFAULT 'INFO' NOT NULL,
    category audit_category DEFAULT 'BUSINESS' NOT NULL,

    module VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),

    user_id INTEGER,
    user_email VARCHAR(255),
    user_role VARCHAR(50),

    session_id VARCHAR(255),
    request_id VARCHAR(255),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),

    description VARCHAR(1000),
    old_value TEXT,
    new_value TEXT,
    diff TEXT,
    metadata TEXT,

    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT,
    error_code VARCHAR(50),

    duration_ms FLOAT,

    retention_policy retention_policy DEFAULT 'MEDIUM' NOT NULL,
    expires_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_created ON audit_logs(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_module_action ON audit_logs(module, action);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_level ON audit_logs(level);
CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_logs(category);
CREATE INDEX IF NOT EXISTS idx_audit_retention ON audit_logs(retention_policy, expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);


-- ============================================================================
-- SESSIONS UTILISATEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    user_email VARCHAR(255),

    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    logout_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100),

    actions_count INTEGER DEFAULT 0 NOT NULL,
    reads_count INTEGER DEFAULT 0 NOT NULL,
    writes_count INTEGER DEFAULT 0 NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    terminated_reason VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON audit_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON audit_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON audit_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_session ON audit_sessions(session_id);


-- ============================================================================
-- DÉFINITIONS DE MÉTRIQUES
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_metric_definitions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    metric_type metric_type NOT NULL,
    unit VARCHAR(50),
    module VARCHAR(50),

    aggregation_period VARCHAR(20) DEFAULT 'HOUR' NOT NULL,
    retention_days INTEGER DEFAULT 90 NOT NULL,

    warning_threshold FLOAT,
    critical_threshold FLOAT,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_metric_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_metrics_tenant ON audit_metric_definitions(tenant_id);


-- ============================================================================
-- VALEURS DE MÉTRIQUES
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_metric_values (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    metric_id INTEGER REFERENCES audit_metric_definitions(id) ON DELETE CASCADE NOT NULL,
    metric_code VARCHAR(100) NOT NULL,

    value FLOAT NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    count INTEGER DEFAULT 1 NOT NULL,

    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,

    dimensions TEXT
);

CREATE INDEX IF NOT EXISTS idx_metric_values_tenant ON audit_metric_values(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metric_values_metric ON audit_metric_values(metric_id);
CREATE INDEX IF NOT EXISTS idx_metric_values_code ON audit_metric_values(metric_code);
CREATE INDEX IF NOT EXISTS idx_metric_values_period ON audit_metric_values(period_start, period_end);


-- ============================================================================
-- BENCHMARKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_benchmarks (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0' NOT NULL,

    benchmark_type VARCHAR(50) NOT NULL,
    module VARCHAR(50),

    config TEXT,
    baseline TEXT,

    is_scheduled BOOLEAN DEFAULT FALSE NOT NULL,
    schedule_cron VARCHAR(100),
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,

    status benchmark_status DEFAULT 'PENDING' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_benchmark_code_version UNIQUE (tenant_id, code, version)
);

CREATE INDEX IF NOT EXISTS idx_benchmarks_tenant ON audit_benchmarks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_type ON audit_benchmarks(benchmark_type);


-- ============================================================================
-- RÉSULTATS DE BENCHMARKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_benchmark_results (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    benchmark_id INTEGER REFERENCES audit_benchmarks(id) ON DELETE CASCADE NOT NULL,

    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms FLOAT,

    status benchmark_status NOT NULL,
    score FLOAT,
    passed BOOLEAN,
    results TEXT,
    summary TEXT,

    previous_score FLOAT,
    score_delta FLOAT,
    trend VARCHAR(20),

    error_message TEXT,
    warnings TEXT,

    executed_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_results_tenant ON audit_benchmark_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_results_benchmark ON audit_benchmark_results(benchmark_id);
CREATE INDEX IF NOT EXISTS idx_results_started ON audit_benchmark_results(started_at);


-- ============================================================================
-- CONTRÔLES DE CONFORMITÉ
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_compliance_checks (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    framework compliance_framework NOT NULL,
    control_id VARCHAR(50) NOT NULL,
    control_name VARCHAR(200) NOT NULL,
    control_description TEXT,

    category VARCHAR(100),
    subcategory VARCHAR(100),

    check_type VARCHAR(50) NOT NULL,
    check_query TEXT,
    expected_result TEXT,

    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    last_checked_at TIMESTAMP,
    checked_by INTEGER,

    actual_result TEXT,
    evidence TEXT,
    remediation TEXT,

    severity VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    due_date TIMESTAMP,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_compliance_control UNIQUE (tenant_id, framework, control_id)
);

CREATE INDEX IF NOT EXISTS idx_compliance_tenant ON audit_compliance_checks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_compliance_framework ON audit_compliance_checks(framework);
CREATE INDEX IF NOT EXISTS idx_compliance_status ON audit_compliance_checks(status);


-- ============================================================================
-- RÈGLES DE RÉTENTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_retention_rules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    name VARCHAR(200) NOT NULL,
    description TEXT,

    target_table VARCHAR(100) NOT NULL,
    target_module VARCHAR(50),

    policy retention_policy NOT NULL,
    retention_days INTEGER NOT NULL,

    condition TEXT,
    action VARCHAR(20) DEFAULT 'DELETE' NOT NULL,

    schedule_cron VARCHAR(100),
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    last_affected_count INTEGER DEFAULT 0 NOT NULL,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_retention_tenant ON audit_retention_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_retention_table ON audit_retention_rules(target_table);


-- ============================================================================
-- EXPORTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_exports (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    export_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) DEFAULT 'CSV' NOT NULL,

    date_from TIMESTAMP,
    date_to TIMESTAMP,
    filters TEXT,

    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    progress INTEGER DEFAULT 0 NOT NULL,

    file_path VARCHAR(500),
    file_size BIGINT,
    records_count INTEGER,

    error_message TEXT,

    requested_by INTEGER NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exports_tenant ON audit_exports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_exports_status ON audit_exports(status);
CREATE INDEX IF NOT EXISTS idx_exports_requested ON audit_exports(requested_at);


-- ============================================================================
-- TABLEAUX DE BORD
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_dashboards (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    widgets TEXT NOT NULL,
    layout TEXT,
    refresh_interval INTEGER DEFAULT 60 NOT NULL,

    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    owner_id INTEGER NOT NULL,
    shared_with TEXT,

    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_dashboard_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_dashboards_tenant ON audit_dashboards(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_owner ON audit_dashboards(owner_id);


-- ============================================================================
-- TRIGGERS AUTO-UPDATE
-- ============================================================================

CREATE OR REPLACE FUNCTION update_audit_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_audit_benchmarks ON audit_benchmarks;
CREATE TRIGGER trigger_update_audit_benchmarks
    BEFORE UPDATE ON audit_benchmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_updated_at();

DROP TRIGGER IF EXISTS trigger_update_audit_compliance ON audit_compliance_checks;
CREATE TRIGGER trigger_update_audit_compliance
    BEFORE UPDATE ON audit_compliance_checks
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_updated_at();

DROP TRIGGER IF EXISTS trigger_update_audit_retention ON audit_retention_rules;
CREATE TRIGGER trigger_update_audit_retention
    BEFORE UPDATE ON audit_retention_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_updated_at();

DROP TRIGGER IF EXISTS trigger_update_audit_dashboards ON audit_dashboards;
CREATE TRIGGER trigger_update_audit_dashboards
    BEFORE UPDATE ON audit_dashboards
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_updated_at();


-- ============================================================================
-- MÉTRIQUES SYSTÈME PAR DÉFAUT
-- ============================================================================

INSERT INTO audit_metric_definitions (tenant_id, code, name, metric_type, unit, module, is_system)
VALUES
    ('SYSTEM', 'API_RESPONSE_TIME', 'Temps de réponse API', 'TIMER', 'ms', 'api', TRUE),
    ('SYSTEM', 'API_REQUESTS_COUNT', 'Nombre de requêtes API', 'COUNTER', 'count', 'api', TRUE),
    ('SYSTEM', 'API_ERROR_RATE', 'Taux d''erreur API', 'GAUGE', '%', 'api', TRUE),
    ('SYSTEM', 'DB_QUERY_TIME', 'Temps de requête DB', 'TIMER', 'ms', 'database', TRUE),
    ('SYSTEM', 'ACTIVE_SESSIONS', 'Sessions actives', 'GAUGE', 'count', 'auth', TRUE),
    ('SYSTEM', 'LOGIN_SUCCESS_RATE', 'Taux de connexion réussie', 'GAUGE', '%', 'auth', TRUE),
    ('SYSTEM', 'MEMORY_USAGE', 'Utilisation mémoire', 'GAUGE', '%', 'system', TRUE),
    ('SYSTEM', 'CPU_USAGE', 'Utilisation CPU', 'GAUGE', '%', 'system', TRUE)
ON CONFLICT (tenant_id, code) DO NOTHING;


-- ============================================================================
-- CONTRÔLES GDPR PAR DÉFAUT
-- ============================================================================

INSERT INTO audit_compliance_checks (tenant_id, framework, control_id, control_name, check_type, category, severity)
VALUES
    ('SYSTEM', 'GDPR', 'GDPR-5.1', 'Consentement explicite', 'MANUAL', 'Consentement', 'HIGH'),
    ('SYSTEM', 'GDPR', 'GDPR-17.1', 'Droit à l''effacement', 'AUTOMATED', 'Droits', 'HIGH'),
    ('SYSTEM', 'GDPR', 'GDPR-20.1', 'Portabilité des données', 'AUTOMATED', 'Droits', 'MEDIUM'),
    ('SYSTEM', 'GDPR', 'GDPR-25.1', 'Protection dès la conception', 'MANUAL', 'Sécurité', 'HIGH'),
    ('SYSTEM', 'GDPR', 'GDPR-30.1', 'Registre des traitements', 'MANUAL', 'Documentation', 'MEDIUM'),
    ('SYSTEM', 'GDPR', 'GDPR-32.1', 'Mesures de sécurité', 'HYBRID', 'Sécurité', 'CRITICAL'),
    ('SYSTEM', 'GDPR', 'GDPR-33.1', 'Notification des violations', 'MANUAL', 'Incidents', 'CRITICAL'),
    ('SYSTEM', 'GDPR', 'GDPR-35.1', 'Analyse d''impact', 'MANUAL', 'Documentation', 'MEDIUM')
ON CONFLICT (tenant_id, framework, control_id) DO NOTHING;


-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue des statistiques par tenant
CREATE OR REPLACE VIEW v_audit_stats AS
SELECT
    tenant_id,
    DATE(created_at) as log_date,
    action,
    module,
    COUNT(*) as count,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failure_count,
    AVG(duration_ms) as avg_duration_ms
FROM audit_logs
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY tenant_id, DATE(created_at), action, module;


-- Vue des sessions actives
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT
    s.*,
    COUNT(l.id) as recent_actions
FROM audit_sessions s
LEFT JOIN audit_logs l ON s.session_id = l.session_id
    AND l.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
WHERE s.is_active = TRUE
GROUP BY s.id;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE audit_logs IS 'Journal d''audit centralisé de toutes les actions';
COMMENT ON TABLE audit_sessions IS 'Sessions utilisateurs avec statistiques d''activité';
COMMENT ON TABLE audit_metric_definitions IS 'Définitions des métriques à collecter';
COMMENT ON TABLE audit_metric_values IS 'Valeurs agrégées des métriques';
COMMENT ON TABLE audit_benchmarks IS 'Définitions des benchmarks de performance';
COMMENT ON TABLE audit_benchmark_results IS 'Résultats d''exécution des benchmarks';
COMMENT ON TABLE audit_compliance_checks IS 'Contrôles de conformité réglementaire';
COMMENT ON TABLE audit_retention_rules IS 'Règles de rétention des données';
COMMENT ON TABLE audit_exports IS 'Demandes et résultats d''export';
COMMENT ON TABLE audit_dashboards IS 'Configuration des tableaux de bord d''audit';


-- ============================================================================
-- FIN MIGRATION
-- ============================================================================
