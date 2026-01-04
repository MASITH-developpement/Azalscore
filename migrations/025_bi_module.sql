-- ============================================================================
-- AZALS ERP - Module M10: BI & Reporting
-- Migration SQL pour Business Intelligence
-- ============================================================================

-- ============================================================================
-- TYPES ÉNUMÉRÉS
-- ============================================================================

CREATE TYPE bi_dashboard_type AS ENUM (
    'executive', 'operational', 'analytical', 'strategic', 'tactical', 'custom'
);

CREATE TYPE bi_widget_type AS ENUM (
    'chart', 'table', 'kpi', 'map', 'gauge', 'text', 'image', 'iframe', 'filter', 'list'
);

CREATE TYPE bi_chart_type AS ENUM (
    'line', 'bar', 'horizontal_bar', 'pie', 'donut', 'area', 'scatter',
    'bubble', 'radar', 'heatmap', 'treemap', 'funnel', 'waterfall', 'combo'
);

CREATE TYPE bi_report_type AS ENUM (
    'financial', 'sales', 'hr', 'production', 'inventory',
    'quality', 'maintenance', 'project', 'custom', 'regulatory', 'audit'
);

CREATE TYPE bi_report_format AS ENUM (
    'pdf', 'excel', 'csv', 'json', 'html', 'xml'
);

CREATE TYPE bi_report_status AS ENUM (
    'pending', 'running', 'completed', 'failed', 'cancelled'
);

CREATE TYPE bi_kpi_category AS ENUM (
    'financial', 'commercial', 'operational', 'hr',
    'quality', 'customer', 'process', 'innovation'
);

CREATE TYPE bi_kpi_trend AS ENUM (
    'up', 'down', 'stable', 'unknown'
);

CREATE TYPE bi_alert_severity AS ENUM (
    'info', 'warning', 'error', 'critical'
);

CREATE TYPE bi_alert_status AS ENUM (
    'active', 'acknowledged', 'resolved', 'snoozed'
);

CREATE TYPE bi_data_source_type AS ENUM (
    'database', 'api', 'file', 'manual'
);

CREATE TYPE bi_refresh_frequency AS ENUM (
    'realtime', 'minute_1', 'minute_5', 'minute_15', 'minute_30',
    'hourly', 'daily', 'weekly', 'monthly', 'on_demand'
);

-- ============================================================================
-- TABLE: bi_dashboards
-- ============================================================================

CREATE TABLE bi_dashboards (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    dashboard_type bi_dashboard_type DEFAULT 'custom',

    -- Propriétaire
    owner_id INTEGER NOT NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    shared_with JSONB,

    -- Configuration
    layout JSONB,
    theme VARCHAR(50) DEFAULT 'default',
    refresh_frequency bi_refresh_frequency DEFAULT 'on_demand',
    auto_refresh BOOLEAN DEFAULT FALSE,

    -- Filtres
    global_filters JSONB,
    default_date_range VARCHAR(50),

    -- Favoris et accès
    is_default BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,

    CONSTRAINT uq_bi_dashboard_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_dashboards_tenant ON bi_dashboards(tenant_id);
CREATE INDEX ix_bi_dashboards_owner ON bi_dashboards(tenant_id, owner_id);

-- ============================================================================
-- TABLE: bi_data_sources
-- ============================================================================

CREATE TABLE bi_data_sources (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    source_type bi_data_source_type NOT NULL,

    -- Configuration
    connection_config JSONB,
    schema_definition JSONB,
    refresh_frequency bi_refresh_frequency DEFAULT 'daily',
    last_synced_at TIMESTAMP,

    -- Cache
    cache_enabled BOOLEAN DEFAULT TRUE,
    cache_ttl_seconds INTEGER DEFAULT 3600,

    -- Sécurité
    is_encrypted BOOLEAN DEFAULT TRUE,
    allowed_roles JSONB,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_bi_datasource_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_datasources_tenant ON bi_data_sources(tenant_id);

-- ============================================================================
-- TABLE: bi_data_queries
-- ============================================================================

CREATE TABLE bi_data_queries (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    data_source_id INTEGER REFERENCES bi_data_sources(id),

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Requête
    query_type VARCHAR(50) DEFAULT 'sql',
    query_text TEXT,
    parameters JSONB,

    -- Résultat
    result_columns JSONB,
    sample_data JSONB,

    -- Cache
    cache_enabled BOOLEAN DEFAULT FALSE,
    cache_ttl_seconds INTEGER DEFAULT 300,
    last_executed_at TIMESTAMP,
    last_execution_time_ms INTEGER,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_bi_query_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_queries_tenant ON bi_data_queries(tenant_id);

-- ============================================================================
-- TABLE: bi_kpi_definitions
-- ============================================================================

CREATE TABLE bi_kpi_definitions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category bi_kpi_category NOT NULL,

    -- Calcul
    formula TEXT,
    unit VARCHAR(50),
    precision INTEGER DEFAULT 2,
    aggregation_method VARCHAR(50) DEFAULT 'sum',

    -- Source de données
    data_source_id INTEGER REFERENCES bi_data_sources(id),
    query TEXT,

    -- Affichage
    display_format VARCHAR(50),
    good_threshold NUMERIC(15,4),
    warning_threshold NUMERIC(15,4),
    bad_threshold NUMERIC(15,4),
    higher_is_better BOOLEAN DEFAULT TRUE,

    -- Fréquence
    refresh_frequency bi_refresh_frequency DEFAULT 'daily',
    last_calculated_at TIMESTAMP,

    -- Comparaison
    compare_to_previous BOOLEAN DEFAULT TRUE,
    comparison_period VARCHAR(50) DEFAULT 'previous_period',

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_bi_kpi_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_kpis_tenant ON bi_kpi_definitions(tenant_id);
CREATE INDEX ix_bi_kpis_category ON bi_kpi_definitions(tenant_id, category);

-- ============================================================================
-- TABLE: bi_dashboard_widgets
-- ============================================================================

CREATE TABLE bi_dashboard_widgets (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    dashboard_id INTEGER NOT NULL REFERENCES bi_dashboards(id) ON DELETE CASCADE,

    -- Identification
    title VARCHAR(200) NOT NULL,
    widget_type bi_widget_type NOT NULL,
    chart_type bi_chart_type,

    -- Position et taille
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 4,
    height INTEGER DEFAULT 3,

    -- Sources
    data_source_id INTEGER REFERENCES bi_data_sources(id),
    query_id INTEGER REFERENCES bi_data_queries(id),
    kpi_id INTEGER REFERENCES bi_kpi_definitions(id),

    -- Configuration
    config JSONB,
    chart_options JSONB,
    colors JSONB,
    static_data JSONB,
    data_mapping JSONB,

    -- Interactions
    drill_down_config JSONB,
    click_action JSONB,

    -- Affichage
    show_title BOOLEAN DEFAULT TRUE,
    show_legend BOOLEAN DEFAULT TRUE,
    show_toolbar BOOLEAN DEFAULT TRUE,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_bi_widgets_dashboard ON bi_dashboard_widgets(dashboard_id);

-- ============================================================================
-- TABLE: bi_widget_filters
-- ============================================================================

CREATE TABLE bi_widget_filters (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    widget_id INTEGER NOT NULL REFERENCES bi_dashboard_widgets(id) ON DELETE CASCADE,

    -- Filtre
    field_name VARCHAR(100) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    value JSONB,
    is_dynamic BOOLEAN DEFAULT FALSE,

    -- Métadonnées
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE: bi_reports
-- ============================================================================

CREATE TABLE bi_reports (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    report_type bi_report_type NOT NULL,

    -- Template
    template TEXT,
    template_file VARCHAR(255),

    -- Sources
    data_sources JSONB,
    queries JSONB,
    parameters JSONB,

    -- Formats
    available_formats JSONB DEFAULT '["pdf", "excel"]',
    default_format bi_report_format DEFAULT 'pdf',

    -- Options
    page_size VARCHAR(20) DEFAULT 'A4',
    orientation VARCHAR(20) DEFAULT 'portrait',
    margins JSONB,
    header_template TEXT,
    footer_template TEXT,

    -- Accès
    owner_id INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    allowed_roles JSONB,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,

    CONSTRAINT uq_bi_report_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_reports_tenant ON bi_reports(tenant_id);

-- ============================================================================
-- TABLE: bi_report_schedules
-- ============================================================================

CREATE TABLE bi_report_schedules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    report_id INTEGER NOT NULL REFERENCES bi_reports(id) ON DELETE CASCADE,

    -- Planification
    name VARCHAR(200) NOT NULL,
    cron_expression VARCHAR(100),
    frequency bi_refresh_frequency,

    -- Exécution
    next_run_at TIMESTAMP,
    last_run_at TIMESTAMP,
    last_status bi_report_status,

    -- Paramètres
    parameters JSONB,
    output_format bi_report_format DEFAULT 'pdf',

    -- Distribution
    recipients JSONB,
    distribution_method VARCHAR(50) DEFAULT 'email',

    -- Options
    is_enabled BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

CREATE INDEX ix_bi_schedules_report ON bi_report_schedules(report_id);
CREATE INDEX ix_bi_schedules_next_run ON bi_report_schedules(next_run_at);

-- ============================================================================
-- TABLE: bi_report_executions
-- ============================================================================

CREATE TABLE bi_report_executions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    report_id INTEGER NOT NULL REFERENCES bi_reports(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES bi_report_schedules(id),

    -- Exécution
    status bi_report_status DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Paramètres
    parameters JSONB,
    output_format bi_report_format NOT NULL,

    -- Résultat
    file_path VARCHAR(500),
    file_size INTEGER,
    file_url VARCHAR(500),
    row_count INTEGER,

    -- Erreur
    error_message TEXT,
    error_details JSONB,

    -- Métadonnées
    triggered_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_bi_executions_report ON bi_report_executions(report_id);
CREATE INDEX ix_bi_executions_status ON bi_report_executions(status);
CREATE INDEX ix_bi_executions_date ON bi_report_executions(started_at);

-- ============================================================================
-- TABLE: bi_kpi_values
-- ============================================================================

CREATE TABLE bi_kpi_values (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    kpi_id INTEGER NOT NULL REFERENCES bi_kpi_definitions(id) ON DELETE CASCADE,

    -- Période
    period_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,

    -- Valeur
    value NUMERIC(20,4) NOT NULL,
    previous_value NUMERIC(20,4),
    change_percentage NUMERIC(10,2),
    trend bi_kpi_trend DEFAULT 'unknown',

    -- Contexte
    dimension VARCHAR(100),
    dimension_value VARCHAR(100),
    extra_data JSONB,

    -- Métadonnées
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'calculated'
);

CREATE INDEX ix_bi_kpi_values_kpi ON bi_kpi_values(kpi_id);
CREATE INDEX ix_bi_kpi_values_date ON bi_kpi_values(kpi_id, period_date);

-- ============================================================================
-- TABLE: bi_kpi_targets
-- ============================================================================

CREATE TABLE bi_kpi_targets (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    kpi_id INTEGER NOT NULL REFERENCES bi_kpi_definitions(id) ON DELETE CASCADE,

    -- Période
    year INTEGER NOT NULL,
    month INTEGER,
    quarter INTEGER,

    -- Objectif
    target_value NUMERIC(20,4) NOT NULL,
    min_value NUMERIC(20,4),
    max_value NUMERIC(20,4),

    -- Progression
    current_value NUMERIC(20,4),
    achievement_percentage NUMERIC(10,2),

    -- Métadonnées
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

CREATE INDEX ix_bi_kpi_targets_kpi ON bi_kpi_targets(kpi_id);

-- ============================================================================
-- TABLE: bi_alert_rules
-- ============================================================================

CREATE TABLE bi_alert_rules (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    severity bi_alert_severity NOT NULL,

    -- Condition
    source_type VARCHAR(50) NOT NULL,
    source_id INTEGER,
    condition JSONB NOT NULL,

    -- Fréquence
    check_frequency bi_refresh_frequency DEFAULT 'hourly',
    last_checked_at TIMESTAMP,
    last_triggered_at TIMESTAMP,

    -- Notifications
    notification_channels JSONB,
    recipients JSONB,
    cooldown_minutes INTEGER DEFAULT 60,

    -- Options
    is_enabled BOOLEAN DEFAULT TRUE,
    auto_resolve BOOLEAN DEFAULT FALSE,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT uq_bi_alert_rule_code UNIQUE (tenant_id, code)
);

CREATE INDEX ix_bi_alert_rules_tenant ON bi_alert_rules(tenant_id);

-- ============================================================================
-- TABLE: bi_alerts
-- ============================================================================

CREATE TABLE bi_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    rule_id INTEGER REFERENCES bi_alert_rules(id),

    -- Alerte
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity bi_alert_severity NOT NULL,
    status bi_alert_status DEFAULT 'active',

    -- Source
    source_type VARCHAR(50),
    source_id INTEGER,
    source_value NUMERIC(20,4),
    threshold_value NUMERIC(20,4),

    -- Contexte
    context JSONB,
    link VARCHAR(500),

    -- Gestion
    acknowledged_at TIMESTAMP,
    acknowledged_by INTEGER,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT,

    -- Snooze
    snoozed_until TIMESTAMP,

    -- Notifications
    notifications_sent JSONB,

    -- Métadonnées
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_bi_alerts_tenant ON bi_alerts(tenant_id);
CREATE INDEX ix_bi_alerts_status ON bi_alerts(tenant_id, status);
CREATE INDEX ix_bi_alerts_severity ON bi_alerts(tenant_id, severity);

-- ============================================================================
-- TABLE: bi_bookmarks
-- ============================================================================

CREATE TABLE bi_bookmarks (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,

    -- Élément
    item_type VARCHAR(50) NOT NULL,
    item_id INTEGER NOT NULL,
    item_name VARCHAR(200),

    -- Organisation
    folder VARCHAR(100),
    display_order INTEGER DEFAULT 0,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_bi_bookmarks_user ON bi_bookmarks(tenant_id, user_id);

-- ============================================================================
-- TABLE: bi_export_history
-- ============================================================================

CREATE TABLE bi_export_history (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,

    -- Export
    export_type VARCHAR(50) NOT NULL,
    item_type VARCHAR(50),
    item_id INTEGER,
    item_name VARCHAR(200),

    -- Format
    format bi_report_format NOT NULL,

    -- Fichier
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    file_url VARCHAR(500),

    -- Statut
    status bi_report_status DEFAULT 'pending',
    error_message TEXT,

    -- Métadonnées
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX ix_bi_exports_user ON bi_export_history(tenant_id, user_id);
CREATE INDEX ix_bi_exports_date ON bi_export_history(created_at);

-- ============================================================================
-- TRIGGERS pour updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION bi_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER tr_bi_dashboards_updated
    BEFORE UPDATE ON bi_dashboards
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_data_sources_updated
    BEFORE UPDATE ON bi_data_sources
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_data_queries_updated
    BEFORE UPDATE ON bi_data_queries
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_kpi_definitions_updated
    BEFORE UPDATE ON bi_kpi_definitions
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_dashboard_widgets_updated
    BEFORE UPDATE ON bi_dashboard_widgets
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_reports_updated
    BEFORE UPDATE ON bi_reports
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_report_schedules_updated
    BEFORE UPDATE ON bi_report_schedules
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_kpi_targets_updated
    BEFORE UPDATE ON bi_kpi_targets
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

CREATE TRIGGER tr_bi_alert_rules_updated
    BEFORE UPDATE ON bi_alert_rules
    FOR EACH ROW EXECUTE FUNCTION bi_update_timestamp();

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE bi_dashboards IS 'Tableaux de bord personnalisables';
COMMENT ON TABLE bi_dashboard_widgets IS 'Widgets des tableaux de bord';
COMMENT ON TABLE bi_widget_filters IS 'Filtres appliqués aux widgets';
COMMENT ON TABLE bi_reports IS 'Définitions des rapports';
COMMENT ON TABLE bi_report_schedules IS 'Planifications des rapports';
COMMENT ON TABLE bi_report_executions IS 'Historique des exécutions de rapports';
COMMENT ON TABLE bi_kpi_definitions IS 'Définitions des KPIs';
COMMENT ON TABLE bi_kpi_values IS 'Valeurs historiques des KPIs';
COMMENT ON TABLE bi_kpi_targets IS 'Objectifs des KPIs';
COMMENT ON TABLE bi_alerts IS 'Alertes déclenchées';
COMMENT ON TABLE bi_alert_rules IS 'Règles de déclenchement des alertes';
COMMENT ON TABLE bi_data_sources IS 'Sources de données pour BI';
COMMENT ON TABLE bi_data_queries IS 'Requêtes réutilisables';
COMMENT ON TABLE bi_bookmarks IS 'Favoris utilisateurs';
COMMENT ON TABLE bi_export_history IS 'Historique des exports';
