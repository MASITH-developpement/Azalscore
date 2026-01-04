-- ============================================================================
-- AZALS ERP - Module M7: Qualité (Quality Management)
-- Migration SQL pour PostgreSQL
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE non_conformance_type AS ENUM (
    'PRODUCT', 'PROCESS', 'SERVICE', 'SUPPLIER', 'CUSTOMER',
    'INTERNAL', 'EXTERNAL', 'AUDIT', 'REGULATORY'
);

CREATE TYPE non_conformance_status AS ENUM (
    'DRAFT', 'OPEN', 'UNDER_ANALYSIS', 'ACTION_REQUIRED',
    'IN_PROGRESS', 'VERIFICATION', 'CLOSED', 'CANCELLED'
);

CREATE TYPE non_conformance_severity AS ENUM (
    'MINOR', 'MAJOR', 'CRITICAL', 'BLOCKING'
);

CREATE TYPE control_type AS ENUM (
    'INCOMING', 'IN_PROCESS', 'FINAL', 'OUTGOING', 'SAMPLING',
    'DESTRUCTIVE', 'NON_DESTRUCTIVE', 'VISUAL', 'DIMENSIONAL',
    'FUNCTIONAL', 'LABORATORY'
);

CREATE TYPE control_status AS ENUM (
    'PLANNED', 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
);

CREATE TYPE control_result AS ENUM (
    'PASSED', 'FAILED', 'CONDITIONAL', 'PENDING', 'NOT_APPLICABLE'
);

CREATE TYPE audit_type AS ENUM (
    'INTERNAL', 'EXTERNAL', 'SUPPLIER', 'CUSTOMER', 'CERTIFICATION',
    'SURVEILLANCE', 'PROCESS', 'PRODUCT', 'SYSTEM'
);

CREATE TYPE audit_status AS ENUM (
    'PLANNED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED',
    'REPORT_PENDING', 'CLOSED', 'CANCELLED'
);

CREATE TYPE finding_severity AS ENUM (
    'OBSERVATION', 'MINOR', 'MAJOR', 'CRITICAL'
);

CREATE TYPE capa_type AS ENUM (
    'CORRECTIVE', 'PREVENTIVE', 'IMPROVEMENT'
);

CREATE TYPE capa_status AS ENUM (
    'DRAFT', 'OPEN', 'ANALYSIS', 'ACTION_PLANNING', 'IN_PROGRESS',
    'VERIFICATION', 'CLOSED_EFFECTIVE', 'CLOSED_INEFFECTIVE', 'CANCELLED'
);

CREATE TYPE claim_status AS ENUM (
    'RECEIVED', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION', 'PENDING_RESPONSE',
    'RESPONSE_SENT', 'IN_RESOLUTION', 'RESOLVED', 'CLOSED', 'REJECTED'
);

CREATE TYPE certification_status AS ENUM (
    'PLANNED', 'IN_PREPARATION', 'AUDIT_SCHEDULED', 'AUDIT_COMPLETED',
    'CERTIFIED', 'SUSPENDED', 'WITHDRAWN', 'EXPIRED'
);

-- ============================================================================
-- TABLE: Non-conformités
-- ============================================================================

CREATE TABLE quality_non_conformances (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    -- Identification
    nc_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    nc_type non_conformance_type NOT NULL,
    status non_conformance_status DEFAULT 'DRAFT',
    severity non_conformance_severity NOT NULL,

    -- Détection
    detected_date DATE NOT NULL,
    detected_by_id BIGINT REFERENCES users(id),
    detection_location VARCHAR(200),
    detection_phase VARCHAR(100),

    -- Origine
    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id BIGINT,

    -- Produit concerné
    product_id BIGINT REFERENCES inventory_products(id),
    lot_number VARCHAR(100),
    serial_number VARCHAR(100),
    quantity_affected NUMERIC(15,3),
    unit_id BIGINT REFERENCES settings_units(id),

    -- Fournisseur/Client
    supplier_id BIGINT REFERENCES purchase_suppliers(id),
    customer_id BIGINT REFERENCES crm_clients(id),

    -- Analyse des causes
    immediate_cause TEXT,
    root_cause TEXT,
    cause_analysis_method VARCHAR(100),
    cause_analysis_date DATE,
    cause_analyzed_by_id BIGINT REFERENCES users(id),

    -- Impact
    impact_description TEXT,
    estimated_cost NUMERIC(15,2),
    actual_cost NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    -- Traitement immédiat
    immediate_action TEXT,
    immediate_action_date TIMESTAMP,
    immediate_action_by_id BIGINT REFERENCES users(id),

    -- Responsabilité
    responsible_id BIGINT REFERENCES users(id),
    department VARCHAR(100),

    -- Décision
    disposition VARCHAR(50),
    disposition_date DATE,
    disposition_by_id BIGINT REFERENCES users(id),
    disposition_justification TEXT,

    -- CAPA
    capa_id BIGINT,
    capa_required BOOLEAN DEFAULT FALSE,

    -- Clôture
    closed_date DATE,
    closed_by_id BIGINT REFERENCES users(id),
    closure_justification TEXT,
    effectiveness_verified BOOLEAN DEFAULT FALSE,
    effectiveness_date DATE,

    -- Métadonnées
    attachments JSONB,
    notes TEXT,
    is_recurrent BOOLEAN DEFAULT FALSE,
    recurrence_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_nc_tenant ON quality_non_conformances(tenant_id);
CREATE INDEX idx_nc_type ON quality_non_conformances(tenant_id, nc_type);
CREATE INDEX idx_nc_status ON quality_non_conformances(tenant_id, status);
CREATE INDEX idx_nc_severity ON quality_non_conformances(tenant_id, severity);
CREATE INDEX idx_nc_detected ON quality_non_conformances(tenant_id, detected_date);

-- ============================================================================
-- TABLE: Actions de non-conformité
-- ============================================================================

CREATE TABLE quality_nc_actions (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    nc_id BIGINT NOT NULL REFERENCES quality_non_conformances(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id BIGINT REFERENCES users(id),

    planned_date DATE,
    due_date DATE,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',

    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id BIGINT REFERENCES users(id),
    verification_result TEXT,

    comments TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_nc_action_nc ON quality_nc_actions(nc_id);
CREATE INDEX idx_nc_action_status ON quality_nc_actions(status);

-- ============================================================================
-- TABLE: Templates de contrôle qualité
-- ============================================================================

CREATE TABLE quality_control_templates (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',

    control_type control_type NOT NULL,

    applies_to VARCHAR(50),
    product_category_id BIGINT,

    instructions TEXT,
    sampling_plan TEXT,
    acceptance_criteria TEXT,

    estimated_duration_minutes INTEGER,
    required_equipment JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),

    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_qct_tenant ON quality_control_templates(tenant_id);
CREATE INDEX idx_qct_code ON quality_control_templates(tenant_id, code);

-- ============================================================================
-- TABLE: Items de template de contrôle
-- ============================================================================

CREATE TABLE quality_control_template_items (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    template_id BIGINT NOT NULL REFERENCES quality_control_templates(id) ON DELETE CASCADE,

    sequence INTEGER NOT NULL,
    characteristic VARCHAR(200) NOT NULL,
    description TEXT,

    measurement_type VARCHAR(50) NOT NULL,
    unit VARCHAR(50),

    nominal_value NUMERIC(15,6),
    tolerance_min NUMERIC(15,6),
    tolerance_max NUMERIC(15,6),
    upper_limit NUMERIC(15,6),
    lower_limit NUMERIC(15,6),

    expected_result VARCHAR(200),

    measurement_method TEXT,
    equipment_code VARCHAR(100),

    is_critical BOOLEAN DEFAULT FALSE,
    is_mandatory BOOLEAN DEFAULT TRUE,

    sampling_frequency VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qcti_template ON quality_control_template_items(template_id);

-- ============================================================================
-- TABLE: Contrôles qualité
-- ============================================================================

CREATE TABLE quality_controls (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    control_number VARCHAR(50) NOT NULL,
    template_id BIGINT REFERENCES quality_control_templates(id),
    control_type control_type NOT NULL,

    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id BIGINT,

    product_id BIGINT REFERENCES inventory_products(id),
    lot_number VARCHAR(100),
    serial_number VARCHAR(100),

    quantity_to_control NUMERIC(15,3),
    quantity_controlled NUMERIC(15,3),
    quantity_conforming NUMERIC(15,3),
    quantity_non_conforming NUMERIC(15,3),
    unit_id BIGINT REFERENCES settings_units(id),

    supplier_id BIGINT REFERENCES purchase_suppliers(id),
    customer_id BIGINT REFERENCES crm_clients(id),

    control_date DATE NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location VARCHAR(200),

    controller_id BIGINT REFERENCES users(id),

    status control_status DEFAULT 'PLANNED',
    result control_result,
    result_date TIMESTAMP,

    decision VARCHAR(50),
    decision_by_id BIGINT REFERENCES users(id),
    decision_date TIMESTAMP,
    decision_comments TEXT,

    nc_id BIGINT REFERENCES quality_non_conformances(id),

    observations TEXT,
    attachments JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_qc_tenant ON quality_controls(tenant_id);
CREATE INDEX idx_qc_number ON quality_controls(tenant_id, control_number);
CREATE INDEX idx_qc_type ON quality_controls(tenant_id, control_type);
CREATE INDEX idx_qc_status ON quality_controls(tenant_id, status);
CREATE INDEX idx_qc_date ON quality_controls(tenant_id, control_date);

-- ============================================================================
-- TABLE: Lignes de contrôle qualité
-- ============================================================================

CREATE TABLE quality_control_lines (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    control_id BIGINT NOT NULL REFERENCES quality_controls(id) ON DELETE CASCADE,
    template_item_id BIGINT REFERENCES quality_control_template_items(id),

    sequence INTEGER NOT NULL,
    characteristic VARCHAR(200) NOT NULL,

    nominal_value NUMERIC(15,6),
    tolerance_min NUMERIC(15,6),
    tolerance_max NUMERIC(15,6),
    unit VARCHAR(50),

    measured_value NUMERIC(15,6),
    measured_text VARCHAR(500),
    measured_boolean BOOLEAN,
    measurement_date TIMESTAMP,

    result control_result,
    deviation NUMERIC(15,6),

    equipment_code VARCHAR(100),
    equipment_serial VARCHAR(100),

    comments TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_qcl_control ON quality_control_lines(control_id);

-- ============================================================================
-- TABLE: Audits qualité
-- ============================================================================

CREATE TABLE quality_audits (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    audit_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    audit_type audit_type NOT NULL,

    reference_standard VARCHAR(200),
    reference_version VARCHAR(50),
    audit_scope TEXT,

    planned_date DATE,
    planned_end_date DATE,
    actual_date DATE,
    actual_end_date DATE,

    status audit_status DEFAULT 'PLANNED',

    lead_auditor_id BIGINT REFERENCES users(id),
    auditors JSONB,

    audited_entity VARCHAR(200),
    audited_department VARCHAR(200),
    auditee_contact_id BIGINT REFERENCES users(id),

    supplier_id BIGINT REFERENCES purchase_suppliers(id),

    total_findings INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    major_findings INTEGER DEFAULT 0,
    minor_findings INTEGER DEFAULT 0,
    observations INTEGER DEFAULT 0,

    overall_score NUMERIC(5,2),
    max_score NUMERIC(5,2),

    audit_conclusion TEXT,
    recommendation TEXT,

    report_date DATE,
    report_file VARCHAR(500),

    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    follow_up_completed BOOLEAN DEFAULT FALSE,

    closed_date DATE,
    closed_by_id BIGINT REFERENCES users(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_audit_tenant ON quality_audits(tenant_id);
CREATE INDEX idx_audit_number ON quality_audits(tenant_id, audit_number);
CREATE INDEX idx_audit_type ON quality_audits(tenant_id, audit_type);
CREATE INDEX idx_audit_status ON quality_audits(tenant_id, status);
CREATE INDEX idx_audit_date ON quality_audits(tenant_id, planned_date);

-- ============================================================================
-- TABLE: Constats d'audit
-- ============================================================================

CREATE TABLE quality_audit_findings (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    audit_id BIGINT NOT NULL REFERENCES quality_audits(id) ON DELETE CASCADE,

    finding_number INTEGER NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,

    severity finding_severity NOT NULL,
    category VARCHAR(100),

    clause_reference VARCHAR(100),
    process_reference VARCHAR(100),
    evidence TEXT,

    risk_description TEXT,
    risk_level VARCHAR(50),

    capa_required BOOLEAN DEFAULT FALSE,
    capa_id BIGINT,

    auditee_response TEXT,
    response_date DATE,

    action_due_date DATE,
    action_completed_date DATE,
    status VARCHAR(50) DEFAULT 'OPEN',

    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id BIGINT REFERENCES users(id),
    verification_comments TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_finding_audit ON quality_audit_findings(audit_id);
CREATE INDEX idx_finding_severity ON quality_audit_findings(severity);

-- ============================================================================
-- TABLE: CAPA
-- ============================================================================

CREATE TABLE quality_capas (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    capa_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    capa_type capa_type NOT NULL,

    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id BIGINT,

    status capa_status DEFAULT 'DRAFT',
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    open_date DATE NOT NULL,
    target_close_date DATE,
    actual_close_date DATE,

    owner_id BIGINT NOT NULL REFERENCES users(id),
    department VARCHAR(100),

    problem_statement TEXT,
    immediate_containment TEXT,
    root_cause_analysis TEXT,
    root_cause_method VARCHAR(100),
    root_cause_verified BOOLEAN DEFAULT FALSE,

    impact_assessment TEXT,
    risk_level VARCHAR(50),

    effectiveness_criteria TEXT,
    effectiveness_verified BOOLEAN DEFAULT FALSE,
    effectiveness_date DATE,
    effectiveness_result TEXT,
    verified_by_id BIGINT REFERENCES users(id),

    extension_required BOOLEAN DEFAULT FALSE,
    extension_scope TEXT,
    extension_completed BOOLEAN DEFAULT FALSE,

    closure_comments TEXT,
    closed_by_id BIGINT REFERENCES users(id),

    attachments JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_capa_tenant ON quality_capas(tenant_id);
CREATE INDEX idx_capa_number ON quality_capas(tenant_id, capa_number);
CREATE INDEX idx_capa_type ON quality_capas(tenant_id, capa_type);
CREATE INDEX idx_capa_status ON quality_capas(tenant_id, status);

-- Ajouter les FK après création de la table
ALTER TABLE quality_non_conformances
    ADD CONSTRAINT fk_nc_capa FOREIGN KEY (capa_id) REFERENCES quality_capas(id);
ALTER TABLE quality_audit_findings
    ADD CONSTRAINT fk_finding_capa FOREIGN KEY (capa_id) REFERENCES quality_capas(id);

-- ============================================================================
-- TABLE: Actions CAPA
-- ============================================================================

CREATE TABLE quality_capa_actions (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    capa_id BIGINT NOT NULL REFERENCES quality_capas(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id BIGINT REFERENCES users(id),

    planned_date DATE,
    due_date DATE NOT NULL,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',

    result TEXT,
    evidence TEXT,

    verification_required BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id BIGINT REFERENCES users(id),
    verification_result TEXT,

    estimated_cost NUMERIC(15,2),
    actual_cost NUMERIC(15,2),

    comments TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_capa_action_capa ON quality_capa_actions(capa_id);
CREATE INDEX idx_capa_action_status ON quality_capa_actions(status);

-- ============================================================================
-- TABLE: Réclamations clients
-- ============================================================================

CREATE TABLE quality_customer_claims (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    claim_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,

    customer_id BIGINT NOT NULL REFERENCES crm_clients(id),
    customer_contact VARCHAR(200),
    customer_reference VARCHAR(100),

    received_date DATE NOT NULL,
    received_via VARCHAR(50),
    received_by_id BIGINT REFERENCES users(id),

    product_id BIGINT REFERENCES inventory_products(id),
    order_reference VARCHAR(100),
    invoice_reference VARCHAR(100),
    lot_number VARCHAR(100),
    quantity_affected NUMERIC(15,3),

    claim_type VARCHAR(50),
    severity non_conformance_severity,
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    status claim_status DEFAULT 'RECEIVED',

    owner_id BIGINT REFERENCES users(id),

    investigation_summary TEXT,
    root_cause TEXT,
    our_responsibility BOOLEAN,

    nc_id BIGINT REFERENCES quality_non_conformances(id),
    capa_id BIGINT REFERENCES quality_capas(id),

    response_due_date DATE,
    response_date DATE,
    response_content TEXT,
    response_by_id BIGINT REFERENCES users(id),

    resolution_type VARCHAR(50),
    resolution_description TEXT,
    resolution_date DATE,

    claim_amount NUMERIC(15,2),
    accepted_amount NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    customer_satisfied BOOLEAN,
    satisfaction_feedback TEXT,

    closed_date DATE,
    closed_by_id BIGINT REFERENCES users(id),

    attachments JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_claim_tenant ON quality_customer_claims(tenant_id);
CREATE INDEX idx_claim_number ON quality_customer_claims(tenant_id, claim_number);
CREATE INDEX idx_claim_status ON quality_customer_claims(tenant_id, status);
CREATE INDEX idx_claim_customer ON quality_customer_claims(tenant_id, customer_id);
CREATE INDEX idx_claim_date ON quality_customer_claims(tenant_id, received_date);

-- ============================================================================
-- TABLE: Actions de réclamation
-- ============================================================================

CREATE TABLE quality_claim_actions (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    claim_id BIGINT NOT NULL REFERENCES quality_customer_claims(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id BIGINT REFERENCES users(id),

    due_date DATE,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',
    result TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_claim_action_claim ON quality_claim_actions(claim_id);

-- ============================================================================
-- TABLE: Indicateurs qualité
-- ============================================================================

CREATE TABLE quality_indicators (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    formula TEXT,
    unit VARCHAR(50),

    target_value NUMERIC(15,4),
    target_min NUMERIC(15,4),
    target_max NUMERIC(15,4),

    warning_threshold NUMERIC(15,4),
    critical_threshold NUMERIC(15,4),

    direction VARCHAR(20),

    measurement_frequency VARCHAR(50),

    data_source VARCHAR(100),
    calculation_query TEXT,

    owner_id BIGINT REFERENCES users(id),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),

    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_qi_tenant ON quality_indicators(tenant_id);
CREATE INDEX idx_qi_code ON quality_indicators(tenant_id, code);

-- ============================================================================
-- TABLE: Mesures d'indicateurs
-- ============================================================================

CREATE TABLE quality_indicator_measurements (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    indicator_id BIGINT NOT NULL REFERENCES quality_indicators(id) ON DELETE CASCADE,

    measurement_date DATE NOT NULL,
    period_start DATE,
    period_end DATE,

    value NUMERIC(15,4) NOT NULL,

    numerator NUMERIC(15,4),
    denominator NUMERIC(15,4),

    target_value NUMERIC(15,4),
    deviation NUMERIC(15,4),
    achievement_rate NUMERIC(5,2),

    status VARCHAR(20),

    comments TEXT,
    action_required BOOLEAN DEFAULT FALSE,

    source VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_qim_indicator ON quality_indicator_measurements(indicator_id);
CREATE INDEX idx_qim_date ON quality_indicator_measurements(measurement_date);

-- ============================================================================
-- TABLE: Certifications
-- ============================================================================

CREATE TABLE quality_certifications (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    standard VARCHAR(100) NOT NULL,
    standard_version VARCHAR(50),
    scope TEXT,

    certification_body VARCHAR(200),
    certification_body_accreditation VARCHAR(100),

    initial_certification_date DATE,
    current_certificate_date DATE,
    expiry_date DATE,
    next_surveillance_date DATE,
    next_renewal_date DATE,

    certificate_number VARCHAR(100),
    certificate_file VARCHAR(500),

    status certification_status DEFAULT 'PLANNED',

    manager_id BIGINT REFERENCES users(id),

    annual_cost NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_cert_tenant ON quality_certifications(tenant_id);
CREATE INDEX idx_cert_code ON quality_certifications(tenant_id, code);
CREATE INDEX idx_cert_status ON quality_certifications(tenant_id, status);

-- ============================================================================
-- TABLE: Audits de certification
-- ============================================================================

CREATE TABLE quality_certification_audits (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    certification_id BIGINT NOT NULL REFERENCES quality_certifications(id) ON DELETE CASCADE,

    audit_type VARCHAR(50) NOT NULL,

    audit_date DATE NOT NULL,
    audit_end_date DATE,

    lead_auditor VARCHAR(200),
    audit_team JSONB,

    result VARCHAR(50),
    findings_count INTEGER DEFAULT 0,
    major_nc_count INTEGER DEFAULT 0,
    minor_nc_count INTEGER DEFAULT 0,
    observations_count INTEGER DEFAULT 0,

    report_date DATE,
    report_file VARCHAR(500),

    corrective_actions_due DATE,
    corrective_actions_closed DATE,
    follow_up_audit_date DATE,

    quality_audit_id BIGINT REFERENCES quality_audits(id),

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX idx_cert_audit_cert ON quality_certification_audits(certification_id);
CREATE INDEX idx_cert_audit_date ON quality_certification_audits(audit_date);

-- ============================================================================
-- TRIGGERS pour updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_quality_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_quality_nc_updated
    BEFORE UPDATE ON quality_non_conformances
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_nc_actions_updated
    BEFORE UPDATE ON quality_nc_actions
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_control_templates_updated
    BEFORE UPDATE ON quality_control_templates
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_controls_updated
    BEFORE UPDATE ON quality_controls
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_audits_updated
    BEFORE UPDATE ON quality_audits
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_audit_findings_updated
    BEFORE UPDATE ON quality_audit_findings
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_capas_updated
    BEFORE UPDATE ON quality_capas
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_capa_actions_updated
    BEFORE UPDATE ON quality_capa_actions
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_claims_updated
    BEFORE UPDATE ON quality_customer_claims
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_claim_actions_updated
    BEFORE UPDATE ON quality_claim_actions
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_indicators_updated
    BEFORE UPDATE ON quality_indicators
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_certifications_updated
    BEFORE UPDATE ON quality_certifications
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

CREATE TRIGGER trg_quality_cert_audits_updated
    BEFORE UPDATE ON quality_certification_audits
    FOR EACH ROW EXECUTE FUNCTION update_quality_timestamp();

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE quality_non_conformances IS 'Gestion des non-conformités';
COMMENT ON TABLE quality_nc_actions IS 'Actions correctives pour non-conformités';
COMMENT ON TABLE quality_control_templates IS 'Templates/modèles de contrôle qualité';
COMMENT ON TABLE quality_control_template_items IS 'Points de contrôle dans les templates';
COMMENT ON TABLE quality_controls IS 'Contrôles qualité exécutés';
COMMENT ON TABLE quality_control_lines IS 'Lignes de mesure des contrôles';
COMMENT ON TABLE quality_audits IS 'Audits qualité internes et externes';
COMMENT ON TABLE quality_audit_findings IS 'Constats d audit';
COMMENT ON TABLE quality_capas IS 'Actions correctives et préventives (CAPA)';
COMMENT ON TABLE quality_capa_actions IS 'Actions des CAPA';
COMMENT ON TABLE quality_customer_claims IS 'Réclamations clients';
COMMENT ON TABLE quality_claim_actions IS 'Actions pour réclamations';
COMMENT ON TABLE quality_indicators IS 'Indicateurs qualité (KPIs)';
COMMENT ON TABLE quality_indicator_measurements IS 'Mesures des indicateurs';
COMMENT ON TABLE quality_certifications IS 'Certifications qualité (ISO, etc.)';
COMMENT ON TABLE quality_certification_audits IS 'Audits de certification';
