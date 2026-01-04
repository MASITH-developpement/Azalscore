-- ============================================================================
-- AZALS MODULE T4 - Migration Contrôle Qualité Central
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-03
-- Description: Tables pour le système de contrôle qualité AZALS
-- ============================================================================

-- Types ENUM
DO $$ BEGIN
    CREATE TYPE qc_rule_category AS ENUM (
        'ARCHITECTURE', 'SECURITY', 'PERFORMANCE', 'CODE_QUALITY',
        'TESTING', 'DOCUMENTATION', 'API', 'DATABASE', 'INTEGRATION', 'COMPLIANCE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE qc_rule_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL', 'BLOCKER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE qc_check_status AS ENUM ('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE module_status AS ENUM (
        'DRAFT', 'IN_DEVELOPMENT', 'READY_FOR_QC', 'QC_IN_PROGRESS',
        'QC_PASSED', 'QC_FAILED', 'PRODUCTION', 'DEPRECATED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE test_type AS ENUM ('UNIT', 'INTEGRATION', 'E2E', 'PERFORMANCE', 'SECURITY', 'REGRESSION');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE validation_phase AS ENUM ('PRE_QC', 'AUTOMATED', 'MANUAL', 'FINAL', 'POST_DEPLOY');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- TABLES PRINCIPALES
-- ============================================================================

-- Table des règles QC
CREATE TABLE IF NOT EXISTS qc_rules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    category qc_rule_category NOT NULL,
    severity qc_rule_severity DEFAULT 'WARNING' NOT NULL,

    applies_to_modules TEXT,
    applies_to_phases TEXT,

    check_type VARCHAR(50) NOT NULL,
    check_config TEXT,

    threshold_value FLOAT,
    threshold_operator VARCHAR(10),

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_qc_rule_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_qc_rules_tenant ON qc_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_rules_category ON qc_rules(tenant_id, category);
CREATE INDEX IF NOT EXISTS idx_qc_rules_active ON qc_rules(tenant_id, is_active);


-- Table du registre des modules
CREATE TABLE IF NOT EXISTS qc_module_registry (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    module_code VARCHAR(10) NOT NULL,
    module_name VARCHAR(200) NOT NULL,
    module_version VARCHAR(20) DEFAULT '1.0.0' NOT NULL,
    module_type VARCHAR(20) NOT NULL,

    description TEXT,
    dependencies TEXT,

    status module_status DEFAULT 'DRAFT' NOT NULL,

    overall_score FLOAT DEFAULT 0.0,
    architecture_score FLOAT DEFAULT 0.0,
    security_score FLOAT DEFAULT 0.0,
    performance_score FLOAT DEFAULT 0.0,
    code_quality_score FLOAT DEFAULT 0.0,
    testing_score FLOAT DEFAULT 0.0,
    documentation_score FLOAT DEFAULT 0.0,

    total_checks INTEGER DEFAULT 0,
    passed_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    blocked_checks INTEGER DEFAULT 0,

    last_qc_run TIMESTAMP,
    validated_at TIMESTAMP,
    validated_by INTEGER,
    production_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_module_code UNIQUE (tenant_id, module_code)
);

CREATE INDEX IF NOT EXISTS idx_module_registry_tenant ON qc_module_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_module_registry_status ON qc_module_registry(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_module_registry_type ON qc_module_registry(tenant_id, module_type);


-- Table des validations QC
CREATE TABLE IF NOT EXISTS qc_validations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    module_id INTEGER REFERENCES qc_module_registry(id) ON DELETE CASCADE NOT NULL,
    validation_phase validation_phase NOT NULL,

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    started_by INTEGER,

    status qc_check_status DEFAULT 'PENDING' NOT NULL,
    overall_score FLOAT,

    total_rules INTEGER DEFAULT 0,
    passed_rules INTEGER DEFAULT 0,
    failed_rules INTEGER DEFAULT 0,
    skipped_rules INTEGER DEFAULT 0,
    blocked_rules INTEGER DEFAULT 0,

    category_scores TEXT,

    report_summary TEXT,
    report_details TEXT
);

CREATE INDEX IF NOT EXISTS idx_validations_tenant ON qc_validations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_validations_module ON qc_validations(tenant_id, module_id);
CREATE INDEX IF NOT EXISTS idx_validations_status ON qc_validations(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_validations_started ON qc_validations(started_at);


-- Table des résultats de checks
CREATE TABLE IF NOT EXISTS qc_check_results (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    validation_id INTEGER REFERENCES qc_validations(id) ON DELETE CASCADE NOT NULL,
    rule_id INTEGER REFERENCES qc_rules(id) ON DELETE SET NULL,

    rule_code VARCHAR(50) NOT NULL,
    rule_name VARCHAR(200),
    category qc_rule_category NOT NULL,
    severity qc_rule_severity NOT NULL,

    status qc_check_status DEFAULT 'PENDING' NOT NULL,

    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,

    expected_value VARCHAR(255),
    actual_value VARCHAR(255),
    score FLOAT,

    message TEXT,
    error_details TEXT,
    recommendation TEXT,

    evidence TEXT
);

CREATE INDEX IF NOT EXISTS idx_check_results_tenant ON qc_check_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_check_results_validation ON qc_check_results(validation_id);
CREATE INDEX IF NOT EXISTS idx_check_results_status ON qc_check_results(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_check_results_category ON qc_check_results(tenant_id, category);


-- Table des exécutions de tests
CREATE TABLE IF NOT EXISTS qc_test_runs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    module_id INTEGER REFERENCES qc_module_registry(id) ON DELETE CASCADE NOT NULL,
    validation_id INTEGER REFERENCES qc_validations(id) ON DELETE SET NULL,

    test_type test_type NOT NULL,
    test_suite VARCHAR(200),

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,

    status qc_check_status DEFAULT 'PENDING' NOT NULL,

    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    error_tests INTEGER DEFAULT 0,

    coverage_percent FLOAT,

    failed_test_details TEXT,
    output_log TEXT,

    triggered_by VARCHAR(50),
    triggered_user INTEGER
);

CREATE INDEX IF NOT EXISTS idx_test_runs_tenant ON qc_test_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_module ON qc_test_runs(tenant_id, module_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_type ON qc_test_runs(tenant_id, test_type);
CREATE INDEX IF NOT EXISTS idx_test_runs_started ON qc_test_runs(started_at);


-- Table des métriques QC
CREATE TABLE IF NOT EXISTS qc_metrics (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    module_id INTEGER REFERENCES qc_module_registry(id) ON DELETE CASCADE,
    metric_date TIMESTAMP NOT NULL,

    modules_total INTEGER DEFAULT 0,
    modules_validated INTEGER DEFAULT 0,
    modules_production INTEGER DEFAULT 0,
    modules_failed INTEGER DEFAULT 0,

    avg_overall_score FLOAT,
    avg_architecture_score FLOAT,
    avg_security_score FLOAT,
    avg_performance_score FLOAT,
    avg_code_quality_score FLOAT,
    avg_testing_score FLOAT,
    avg_documentation_score FLOAT,

    total_tests_run INTEGER DEFAULT 0,
    total_tests_passed INTEGER DEFAULT 0,
    avg_coverage FLOAT,

    total_checks_run INTEGER DEFAULT 0,
    total_checks_passed INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    blocker_issues INTEGER DEFAULT 0,

    score_trend VARCHAR(10),
    score_delta FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qc_metrics_tenant ON qc_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_metrics_date ON qc_metrics(tenant_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_qc_metrics_module ON qc_metrics(tenant_id, module_id);


-- Table des alertes QC
CREATE TABLE IF NOT EXISTS qc_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    module_id INTEGER REFERENCES qc_module_registry(id) ON DELETE CASCADE,
    validation_id INTEGER REFERENCES qc_validations(id) ON DELETE SET NULL,
    check_result_id BIGINT REFERENCES qc_check_results(id) ON DELETE SET NULL,

    alert_type VARCHAR(50) NOT NULL,
    severity qc_rule_severity DEFAULT 'WARNING' NOT NULL,

    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    details TEXT,

    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qc_alerts_tenant ON qc_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_alerts_unresolved ON qc_alerts(tenant_id, is_resolved);
CREATE INDEX IF NOT EXISTS idx_qc_alerts_severity ON qc_alerts(tenant_id, severity);
CREATE INDEX IF NOT EXISTS idx_qc_alerts_module ON qc_alerts(tenant_id, module_id);


-- Table des dashboards QC
CREATE TABLE IF NOT EXISTS qc_dashboards (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    name VARCHAR(200) NOT NULL,
    description TEXT,

    layout TEXT,
    widgets TEXT,
    filters TEXT,

    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    owner_id INTEGER,
    shared_with TEXT,

    auto_refresh BOOLEAN DEFAULT TRUE NOT NULL,
    refresh_interval INTEGER DEFAULT 60,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qc_dashboards_tenant ON qc_dashboards(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_dashboards_owner ON qc_dashboards(tenant_id, owner_id);


-- Table des templates QC
CREATE TABLE IF NOT EXISTS qc_templates (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    rules TEXT NOT NULL,
    category VARCHAR(50),

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_qc_template_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_qc_templates_tenant ON qc_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_templates_category ON qc_templates(tenant_id, category);


-- ============================================================================
-- TRIGGERS (Auto-update timestamps)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_qc_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_qc_rules ON qc_rules;
CREATE TRIGGER trigger_update_qc_rules
    BEFORE UPDATE ON qc_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_qc_updated_at();

DROP TRIGGER IF EXISTS trigger_update_qc_module_registry ON qc_module_registry;
CREATE TRIGGER trigger_update_qc_module_registry
    BEFORE UPDATE ON qc_module_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_qc_updated_at();

DROP TRIGGER IF EXISTS trigger_update_qc_dashboards ON qc_dashboards;
CREATE TRIGGER trigger_update_qc_dashboards
    BEFORE UPDATE ON qc_dashboards
    FOR EACH ROW
    EXECUTE FUNCTION update_qc_updated_at();

DROP TRIGGER IF EXISTS trigger_update_qc_templates ON qc_templates;
CREATE TRIGGER trigger_update_qc_templates
    BEFORE UPDATE ON qc_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_qc_updated_at();


-- ============================================================================
-- DONNÉES INITIALES - Règles système AZALS
-- ============================================================================

-- Règles système par défaut pour tous les tenants
INSERT INTO qc_rules (tenant_id, code, name, description, category, severity, check_type, check_config, is_system, is_active)
VALUES
    -- Architecture
    ('SYSTEM', 'ARCH_001', 'Structure module standard', 'Vérifie la structure de fichiers du module',
     'ARCHITECTURE', 'BLOCKER', 'file_exists',
     '{"files": ["__init__.py", "models.py", "service.py", "schemas.py", "router.py"]}',
     TRUE, TRUE),

    ('SYSTEM', 'ARCH_002', 'Migration SQL présente', 'Vérifie la présence du fichier de migration',
     'ARCHITECTURE', 'CRITICAL', 'file_exists',
     '{"pattern": "migrations/*_module.sql"}',
     TRUE, TRUE),

    -- Sécurité
    ('SYSTEM', 'SEC_001', 'Isolation multi-tenant', 'Vérifie tenant_id sur toutes les tables',
     'SECURITY', 'BLOCKER', 'database_schema',
     '{"check": "tenant_id_column"}',
     TRUE, TRUE),

    ('SYSTEM', 'SEC_002', 'Authentification requise', 'Vérifie que tous les endpoints requièrent auth',
     'SECURITY', 'BLOCKER', 'api_endpoints',
     '{"check": "auth_required"}',
     TRUE, TRUE),

    -- Tests
    ('SYSTEM', 'TEST_001', 'Couverture tests minimum', 'Vérifie couverture tests >= 80%',
     'TESTING', 'CRITICAL', 'test_coverage',
     '{}', TRUE, TRUE),

    ('SYSTEM', 'TEST_002', 'Tests unitaires présents', 'Vérifie présence fichier tests',
     'TESTING', 'BLOCKER', 'file_exists',
     '{"pattern": "tests/test_*.py"}',
     TRUE, TRUE),

    -- Documentation
    ('SYSTEM', 'DOC_001', 'Benchmark présent', 'Vérifie la présence du document benchmark',
     'DOCUMENTATION', 'WARNING', 'file_exists',
     '{"pattern": "docs/modules/*_BENCHMARK.md"}',
     TRUE, TRUE),

    ('SYSTEM', 'DOC_002', 'Rapport QC présent', 'Vérifie la présence du rapport QC',
     'DOCUMENTATION', 'WARNING', 'file_exists',
     '{"pattern": "docs/modules/*_QC_REPORT.md"}',
     TRUE, TRUE),

    -- Performance
    ('SYSTEM', 'PERF_001', 'Temps réponse API', 'Vérifie temps de réponse < 200ms',
     'PERFORMANCE', 'WARNING', 'performance',
     '{"max_response_ms": 200}',
     TRUE, TRUE),

    -- API
    ('SYSTEM', 'API_001', 'Endpoints minimum', 'Vérifie au moins 10 endpoints par module métier',
     'API', 'CRITICAL', 'api_endpoints',
     '{"min_endpoints": 10}',
     TRUE, TRUE)

ON CONFLICT (tenant_id, code) DO NOTHING;


-- Templates système
INSERT INTO qc_templates (tenant_id, code, name, description, rules, category, is_system)
VALUES
    ('SYSTEM', 'TRANSVERSE_BASIC', 'Module Transverse - Basique',
     'Template QC de base pour modules transverses',
     '[{"code":"ARCH_001","name":"Structure standard","category":"ARCHITECTURE","severity":"BLOCKER","check_type":"file_exists"},{"code":"SEC_001","name":"Isolation tenant","category":"SECURITY","severity":"BLOCKER","check_type":"database_schema"},{"code":"TEST_001","name":"Tests présents","category":"TESTING","severity":"CRITICAL","check_type":"file_exists"}]',
     'TRANSVERSE', TRUE),

    ('SYSTEM', 'METIER_FULL', 'Module Métier - Complet',
     'Template QC complet pour modules métiers',
     '[{"code":"ARCH_001","name":"Structure standard","category":"ARCHITECTURE","severity":"BLOCKER","check_type":"file_exists"},{"code":"SEC_001","name":"Isolation tenant","category":"SECURITY","severity":"BLOCKER","check_type":"database_schema"},{"code":"SEC_002","name":"Auth requise","category":"SECURITY","severity":"BLOCKER","check_type":"api_endpoints"},{"code":"TEST_001","name":"Couverture 80%","category":"TESTING","severity":"CRITICAL","check_type":"test_coverage"},{"code":"DOC_001","name":"Benchmark","category":"DOCUMENTATION","severity":"WARNING","check_type":"file_exists"},{"code":"PERF_001","name":"Performance","category":"PERFORMANCE","severity":"WARNING","check_type":"performance"}]',
     'METIER', TRUE)

ON CONFLICT (tenant_id, code) DO NOTHING;


-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue des modules non validés
CREATE OR REPLACE VIEW v_qc_modules_pending AS
SELECT
    m.*,
    (SELECT COUNT(*) FROM qc_validations v WHERE v.module_id = m.id) as validation_count,
    (SELECT MAX(v.started_at) FROM qc_validations v WHERE v.module_id = m.id) as last_validation
FROM qc_module_registry m
WHERE m.status NOT IN ('QC_PASSED', 'PRODUCTION')
ORDER BY
    CASE m.module_type
        WHEN 'TRANSVERSE' THEN 1
        ELSE 2
    END,
    m.module_code;


-- Vue des alertes critiques non résolues
CREATE OR REPLACE VIEW v_qc_critical_alerts AS
SELECT
    a.*,
    m.module_code,
    m.module_name
FROM qc_alerts a
LEFT JOIN qc_module_registry m ON a.module_id = m.id
WHERE a.is_resolved = FALSE
  AND a.severity IN ('CRITICAL', 'BLOCKER')
ORDER BY a.created_at DESC;


-- Vue résumé par module
CREATE OR REPLACE VIEW v_qc_module_summary AS
SELECT
    m.tenant_id,
    m.module_code,
    m.module_name,
    m.module_type,
    m.status,
    m.overall_score,
    m.last_qc_run,
    (SELECT COUNT(*) FROM qc_validations v WHERE v.module_id = m.id AND v.status = 'PASSED') as passed_validations,
    (SELECT COUNT(*) FROM qc_validations v WHERE v.module_id = m.id AND v.status = 'FAILED') as failed_validations,
    (SELECT COUNT(*) FROM qc_test_runs t WHERE t.module_id = m.id) as total_test_runs,
    (SELECT COUNT(*) FROM qc_alerts a WHERE a.module_id = m.id AND a.is_resolved = FALSE) as open_alerts
FROM qc_module_registry m;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE qc_rules IS 'Règles de contrôle qualité';
COMMENT ON TABLE qc_module_registry IS 'Registre des modules avec statut QC';
COMMENT ON TABLE qc_validations IS 'Sessions de validation QC';
COMMENT ON TABLE qc_check_results IS 'Résultats individuels des checks QC';
COMMENT ON TABLE qc_test_runs IS 'Exécutions de tests par module';
COMMENT ON TABLE qc_metrics IS 'Métriques QC agrégées';
COMMENT ON TABLE qc_alerts IS 'Alertes QC';
COMMENT ON TABLE qc_dashboards IS 'Dashboards QC personnalisés';
COMMENT ON TABLE qc_templates IS 'Templates de règles QC';


-- ============================================================================
-- FIN MIGRATION
-- ============================================================================
