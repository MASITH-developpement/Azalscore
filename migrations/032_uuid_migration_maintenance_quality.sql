-- ============================================================================
-- AZALS - Migration UUID pour Maintenance et Quality
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-09
-- Description: Migration vers UUID pour les modules Maintenance et Quality
--              Production SaaS industrielle multi-tenant
-- ============================================================================

-- IMPORTANT: Cette migration est conçue pour une NOUVELLE INSTALLATION
-- Pour une migration de données existantes, un script de migration de données
-- séparé sera nécessaire.

-- ============================================================================
-- EXTENSION UUID
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- FONCTION DE GÉNÉRATION UUID v4
-- ============================================================================

CREATE OR REPLACE FUNCTION gen_random_uuid_v4()
RETURNS UUID AS $$
BEGIN
    RETURN uuid_generate_v4();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DROP DES ANCIENNES TABLES (SI MIGRATION FRESH)
-- ============================================================================

-- MAINTENANCE MODULE - Drop in reverse dependency order
DROP TABLE IF EXISTS maintenance_kpis CASCADE;
DROP TABLE IF EXISTS maintenance_part_requests CASCADE;
DROP TABLE IF EXISTS maintenance_spare_part_stock CASCADE;
DROP TABLE IF EXISTS maintenance_spare_parts CASCADE;
DROP TABLE IF EXISTS maintenance_failure_causes CASCADE;
DROP TABLE IF EXISTS maintenance_failures CASCADE;
DROP TABLE IF EXISTS maintenance_wo_parts CASCADE;
DROP TABLE IF EXISTS maintenance_wo_labor CASCADE;
DROP TABLE IF EXISTS maintenance_wo_tasks CASCADE;
DROP TABLE IF EXISTS maintenance_work_orders CASCADE;
DROP TABLE IF EXISTS maintenance_plan_tasks CASCADE;
DROP TABLE IF EXISTS maintenance_plans CASCADE;
DROP TABLE IF EXISTS maintenance_meter_readings CASCADE;
DROP TABLE IF EXISTS maintenance_asset_meters CASCADE;
DROP TABLE IF EXISTS maintenance_asset_documents CASCADE;
DROP TABLE IF EXISTS maintenance_asset_components CASCADE;
DROP TABLE IF EXISTS maintenance_assets CASCADE;
DROP TABLE IF EXISTS maintenance_contracts CASCADE;

-- QUALITY MODULE - Drop in reverse dependency order
DROP TABLE IF EXISTS quality_certification_audits CASCADE;
DROP TABLE IF EXISTS quality_certifications CASCADE;
DROP TABLE IF EXISTS quality_indicator_measurements CASCADE;
DROP TABLE IF EXISTS quality_indicators CASCADE;
DROP TABLE IF EXISTS quality_claim_actions CASCADE;
DROP TABLE IF EXISTS quality_customer_claims CASCADE;
DROP TABLE IF EXISTS quality_capa_actions CASCADE;
DROP TABLE IF EXISTS quality_capas CASCADE;
DROP TABLE IF EXISTS quality_audit_findings CASCADE;
DROP TABLE IF EXISTS quality_audits CASCADE;
DROP TABLE IF EXISTS quality_control_lines CASCADE;
DROP TABLE IF EXISTS quality_controls CASCADE;
DROP TABLE IF EXISTS quality_control_template_items CASCADE;
DROP TABLE IF EXISTS quality_control_templates CASCADE;
DROP TABLE IF EXISTS quality_nc_actions CASCADE;
DROP TABLE IF EXISTS quality_non_conformances CASCADE;

-- ============================================================================
-- MAINTENANCE MODULE - TABLES WITH UUID
-- ============================================================================

-- Actifs
CREATE TABLE IF NOT EXISTS maintenance_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    asset_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    asset_type VARCHAR(100),

    status VARCHAR(50) DEFAULT 'ACTIVE',
    criticality VARCHAR(50) DEFAULT 'MEDIUM',

    parent_id UUID REFERENCES maintenance_assets(id),

    location_id UUID,
    location_description VARCHAR(200),
    building VARCHAR(100),
    floor VARCHAR(50),
    area VARCHAR(100),

    manufacturer VARCHAR(200),
    model VARCHAR(200),
    serial_number VARCHAR(100),
    year_manufactured INTEGER,

    purchase_date DATE,
    installation_date DATE,
    warranty_start_date DATE,
    warranty_end_date DATE,
    expected_end_of_life DATE,
    last_maintenance_date DATE,
    next_maintenance_date DATE,

    purchase_cost NUMERIC(15,2),
    current_value NUMERIC(15,2),
    replacement_cost NUMERIC(15,2),
    salvage_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    depreciation_method VARCHAR(50),
    useful_life_years INTEGER,
    depreciation_rate NUMERIC(5,2),

    specifications JSONB DEFAULT '{}',
    power_rating VARCHAR(100),
    dimensions VARCHAR(200),
    weight NUMERIC(10,2),
    weight_unit VARCHAR(20),

    operating_hours NUMERIC(12,2) DEFAULT 0,
    cycle_count INTEGER DEFAULT 0,
    energy_consumption NUMERIC(15,4),

    maintenance_strategy VARCHAR(50),
    default_maintenance_plan_id UUID,

    supplier_id UUID,
    responsible_id UUID,
    department VARCHAR(100),
    contract_id UUID,

    photo_url VARCHAR(500),
    documents JSONB DEFAULT '[]',
    notes TEXT,
    barcode VARCHAR(100),
    qr_code VARCHAR(200),

    mtbf_hours NUMERIC(10,2),
    mttr_hours NUMERIC(10,2),
    availability_rate NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_asset_code UNIQUE (tenant_id, asset_code)
);

CREATE INDEX IF NOT EXISTS idx_asset_tenant ON maintenance_assets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_asset_code ON maintenance_assets(tenant_id, asset_code);
CREATE INDEX IF NOT EXISTS idx_asset_category ON maintenance_assets(tenant_id, category);
CREATE INDEX IF NOT EXISTS idx_asset_status ON maintenance_assets(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_asset_location ON maintenance_assets(tenant_id, location_id);

-- Composants
CREATE TABLE IF NOT EXISTS maintenance_asset_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    asset_id UUID NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

    component_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    manufacturer VARCHAR(200),
    part_number VARCHAR(100),
    serial_number VARCHAR(100),

    installation_date DATE,
    expected_replacement_date DATE,
    last_replacement_date DATE,

    expected_life_hours INTEGER,
    expected_life_cycles INTEGER,
    current_hours NUMERIC(10,2) DEFAULT 0,
    current_cycles INTEGER DEFAULT 0,

    criticality VARCHAR(50),
    spare_part_id UUID,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_component_tenant ON maintenance_asset_components(tenant_id);
CREATE INDEX IF NOT EXISTS idx_component_asset ON maintenance_asset_components(asset_id);

-- Documents
CREATE TABLE IF NOT EXISTS maintenance_asset_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    asset_id UUID NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_name VARCHAR(200),
    file_size INTEGER,
    mime_type VARCHAR(100),

    version VARCHAR(50),
    valid_from DATE,
    valid_until DATE,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_asset_doc_tenant ON maintenance_asset_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_asset_doc_asset ON maintenance_asset_documents(asset_id);

-- Compteurs
CREATE TABLE IF NOT EXISTS maintenance_asset_meters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    asset_id UUID NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

    meter_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    meter_type VARCHAR(50) NOT NULL,
    unit VARCHAR(50) NOT NULL,

    current_reading NUMERIC(15,4) DEFAULT 0,
    last_reading_date TIMESTAMPTZ,
    initial_reading NUMERIC(15,4) DEFAULT 0,

    alert_threshold NUMERIC(15,4),
    critical_threshold NUMERIC(15,4),
    max_reading NUMERIC(15,4),

    maintenance_trigger_value NUMERIC(15,4),
    last_maintenance_reading NUMERIC(15,4),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_asset_meter UNIQUE (asset_id, meter_code)
);

CREATE INDEX IF NOT EXISTS idx_meter_tenant ON maintenance_asset_meters(tenant_id);
CREATE INDEX IF NOT EXISTS idx_meter_asset ON maintenance_asset_meters(asset_id);

-- Relevés compteur
CREATE TABLE IF NOT EXISTS maintenance_meter_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    meter_id UUID NOT NULL REFERENCES maintenance_asset_meters(id) ON DELETE CASCADE,

    reading_date TIMESTAMPTZ NOT NULL,
    reading_value NUMERIC(15,4) NOT NULL,
    delta NUMERIC(15,4),

    source VARCHAR(50),
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_reading_tenant ON maintenance_meter_readings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reading_meter ON maintenance_meter_readings(meter_id);
CREATE INDEX IF NOT EXISTS idx_reading_date ON maintenance_meter_readings(reading_date);

-- Plans de maintenance
CREATE TABLE IF NOT EXISTS maintenance_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    plan_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    maintenance_type VARCHAR(50) NOT NULL,

    asset_id UUID REFERENCES maintenance_assets(id),
    asset_category VARCHAR(50),

    trigger_type VARCHAR(50) NOT NULL,
    frequency_value INTEGER,
    frequency_unit VARCHAR(20),

    trigger_meter_id UUID REFERENCES maintenance_asset_meters(id),
    trigger_meter_interval NUMERIC(15,4),

    last_execution_date DATE,
    next_due_date DATE,
    lead_time_days INTEGER DEFAULT 7,

    estimated_duration_hours NUMERIC(6,2),
    responsible_id UUID,
    is_active BOOLEAN DEFAULT TRUE,

    estimated_labor_cost NUMERIC(15,2),
    estimated_parts_cost NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    instructions TEXT,
    safety_instructions TEXT,
    required_tools JSONB DEFAULT '[]',
    required_certifications JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_mplan_code UNIQUE (tenant_id, plan_code)
);

CREATE INDEX IF NOT EXISTS idx_mplan_tenant ON maintenance_plans(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mplan_code ON maintenance_plans(tenant_id, plan_code);

-- Tâches plan
CREATE TABLE IF NOT EXISTS maintenance_plan_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    plan_id UUID NOT NULL REFERENCES maintenance_plans(id) ON DELETE CASCADE,

    sequence INTEGER NOT NULL,
    task_code VARCHAR(50),
    description TEXT NOT NULL,
    detailed_instructions TEXT,

    estimated_duration_minutes INTEGER,
    required_skill VARCHAR(100),
    required_parts JSONB DEFAULT '[]',
    check_points JSONB DEFAULT '[]',

    is_mandatory BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mplan_task_tenant ON maintenance_plan_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mplan_task_plan ON maintenance_plan_tasks(plan_id);

-- Pièces de rechange
CREATE TABLE IF NOT EXISTS maintenance_spare_parts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    part_code VARCHAR(100) NOT NULL,
    name VARCHAR(300) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    manufacturer VARCHAR(200),
    manufacturer_part_number VARCHAR(100),
    preferred_supplier_id UUID,
    equivalent_parts JSONB DEFAULT '[]',

    unit VARCHAR(50) NOT NULL,
    unit_cost NUMERIC(15,2),
    last_purchase_price NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    min_stock_level NUMERIC(12,3) DEFAULT 0,
    max_stock_level NUMERIC(12,3),
    reorder_point NUMERIC(12,3),
    reorder_quantity NUMERIC(12,3),
    lead_time_days INTEGER,

    criticality VARCHAR(50),
    shelf_life_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE,

    product_id UUID,
    notes TEXT,
    specifications JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_spare_code UNIQUE (tenant_id, part_code)
);

CREATE INDEX IF NOT EXISTS idx_spare_tenant ON maintenance_spare_parts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_spare_code ON maintenance_spare_parts(tenant_id, part_code);

-- Stock pièces
CREATE TABLE IF NOT EXISTS maintenance_spare_part_stock (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    spare_part_id UUID NOT NULL REFERENCES maintenance_spare_parts(id) ON DELETE CASCADE,

    location_id UUID,
    location_description VARCHAR(200),
    bin_location VARCHAR(100),

    quantity_on_hand NUMERIC(12,3) DEFAULT 0,
    quantity_reserved NUMERIC(12,3) DEFAULT 0,
    quantity_available NUMERIC(12,3) DEFAULT 0,

    last_count_date DATE,
    last_movement_date TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_spare_stock_loc UNIQUE (spare_part_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_spare_stock_tenant ON maintenance_spare_part_stock(tenant_id);
CREATE INDEX IF NOT EXISTS idx_spare_stock_part ON maintenance_spare_part_stock(spare_part_id);

-- Pannes
CREATE TABLE IF NOT EXISTS maintenance_failures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    failure_number VARCHAR(50) NOT NULL,

    asset_id UUID NOT NULL REFERENCES maintenance_assets(id),
    component_id UUID REFERENCES maintenance_asset_components(id),

    failure_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    symptoms TEXT,

    failure_date TIMESTAMPTZ NOT NULL,
    detected_date TIMESTAMPTZ,
    reported_date TIMESTAMPTZ,
    resolved_date TIMESTAMPTZ,

    production_stopped BOOLEAN DEFAULT FALSE,
    downtime_hours NUMERIC(8,2),
    production_loss_units NUMERIC(15,2),
    estimated_cost_impact NUMERIC(15,2),

    reported_by_id UUID,
    work_order_id UUID,

    resolution TEXT,
    root_cause TEXT,
    corrective_action TEXT,
    preventive_action TEXT,

    meter_reading NUMERIC(15,4),
    status VARCHAR(50) DEFAULT 'OPEN',

    notes TEXT,
    attachments JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_failure_tenant ON maintenance_failures(tenant_id);
CREATE INDEX IF NOT EXISTS idx_failure_asset ON maintenance_failures(tenant_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_failure_date ON maintenance_failures(tenant_id, failure_date);

-- Causes panne
CREATE TABLE IF NOT EXISTS maintenance_failure_causes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    failure_id UUID NOT NULL REFERENCES maintenance_failures(id) ON DELETE CASCADE,

    cause_category VARCHAR(100),
    cause_description TEXT NOT NULL,
    is_root_cause BOOLEAN DEFAULT FALSE,

    probability VARCHAR(20),
    recommended_action TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_failure_cause_tenant ON maintenance_failure_causes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_failure_cause_failure ON maintenance_failure_causes(failure_id);

-- Ordres de travail
CREATE TABLE IF NOT EXISTS maintenance_work_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    wo_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,

    maintenance_type VARCHAR(50) NOT NULL,
    priority VARCHAR(50) DEFAULT 'MEDIUM',
    status VARCHAR(50) DEFAULT 'DRAFT',

    asset_id UUID NOT NULL REFERENCES maintenance_assets(id),
    component_id UUID REFERENCES maintenance_asset_components(id),

    source VARCHAR(50),
    source_reference VARCHAR(100),
    maintenance_plan_id UUID REFERENCES maintenance_plans(id),
    failure_id UUID REFERENCES maintenance_failures(id),

    requester_id UUID,
    request_date TIMESTAMPTZ,
    request_description TEXT,

    scheduled_start_date TIMESTAMPTZ,
    scheduled_end_date TIMESTAMPTZ,
    due_date TIMESTAMPTZ,

    actual_start_date TIMESTAMPTZ,
    actual_end_date TIMESTAMPTZ,
    downtime_hours NUMERIC(8,2),

    assigned_to_id UUID,
    team_id UUID,
    external_vendor_id UUID,

    work_instructions TEXT,
    safety_precautions TEXT,
    tools_required JSONB DEFAULT '[]',
    certifications_required JSONB DEFAULT '[]',

    location_description VARCHAR(200),

    completion_notes TEXT,
    completed_by_id UUID,
    verification_required BOOLEAN DEFAULT FALSE,
    verified_by_id UUID,
    verified_date TIMESTAMPTZ,

    estimated_labor_hours NUMERIC(8,2),
    estimated_labor_cost NUMERIC(15,2),
    estimated_parts_cost NUMERIC(15,2),
    estimated_other_cost NUMERIC(15,2),
    actual_labor_hours NUMERIC(8,2),
    actual_labor_cost NUMERIC(15,2),
    actual_parts_cost NUMERIC(15,2),
    actual_other_cost NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    meter_reading_end NUMERIC(15,4),
    attachments JSONB DEFAULT '[]',
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_wo_tenant ON maintenance_work_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wo_number ON maintenance_work_orders(tenant_id, wo_number);
CREATE INDEX IF NOT EXISTS idx_wo_asset ON maintenance_work_orders(tenant_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_wo_status ON maintenance_work_orders(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_wo_priority ON maintenance_work_orders(tenant_id, priority);
CREATE INDEX IF NOT EXISTS idx_wo_scheduled ON maintenance_work_orders(tenant_id, scheduled_start_date);

-- Tâches OT
CREATE TABLE IF NOT EXISTS maintenance_wo_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
    plan_task_id UUID REFERENCES maintenance_plan_tasks(id),

    sequence INTEGER NOT NULL,
    description TEXT NOT NULL,
    instructions TEXT,

    estimated_minutes INTEGER,
    actual_minutes INTEGER,

    status VARCHAR(50) DEFAULT 'PENDING',
    completed_date TIMESTAMPTZ,
    completed_by_id UUID,

    result TEXT,
    issues_found TEXT,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wo_task_tenant ON maintenance_wo_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wo_task_wo ON maintenance_wo_tasks(work_order_id);

-- Main d'oeuvre OT
CREATE TABLE IF NOT EXISTS maintenance_wo_labor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,

    technician_id UUID NOT NULL,
    technician_name VARCHAR(200),

    work_date DATE NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    hours_worked NUMERIC(6,2) NOT NULL,
    overtime_hours NUMERIC(6,2) DEFAULT 0,

    labor_type VARCHAR(50),
    hourly_rate NUMERIC(10,2),
    total_cost NUMERIC(12,2),

    work_description TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_wo_labor_tenant ON maintenance_wo_labor(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wo_labor_wo ON maintenance_wo_labor(work_order_id);

-- Pièces OT
CREATE TABLE IF NOT EXISTS maintenance_wo_parts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    work_order_id UUID NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,

    spare_part_id UUID REFERENCES maintenance_spare_parts(id),
    part_code VARCHAR(100),
    part_description VARCHAR(300) NOT NULL,

    quantity_planned NUMERIC(12,3),
    quantity_used NUMERIC(12,3) NOT NULL,
    unit VARCHAR(50),

    unit_cost NUMERIC(15,2),
    total_cost NUMERIC(15,2),

    source VARCHAR(50),
    source_reference VARCHAR(100),
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_wo_part_tenant ON maintenance_wo_parts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wo_part_wo ON maintenance_wo_parts(work_order_id);

-- Demandes pièces
CREATE TABLE IF NOT EXISTS maintenance_part_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    request_number VARCHAR(50) NOT NULL,
    work_order_id UUID REFERENCES maintenance_work_orders(id),

    spare_part_id UUID REFERENCES maintenance_spare_parts(id),
    part_description VARCHAR(300) NOT NULL,

    quantity_requested NUMERIC(12,3) NOT NULL,
    quantity_approved NUMERIC(12,3),
    quantity_issued NUMERIC(12,3),
    unit VARCHAR(50),

    priority VARCHAR(50) DEFAULT 'MEDIUM',
    required_date DATE,
    status VARCHAR(50) DEFAULT 'REQUESTED',

    requester_id UUID,
    request_date TIMESTAMPTZ,
    request_reason TEXT,

    approved_by_id UUID,
    approved_date TIMESTAMPTZ,

    issued_by_id UUID,
    issued_date TIMESTAMPTZ,

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_part_req_tenant ON maintenance_part_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_part_req_wo ON maintenance_part_requests(work_order_id);

-- Contrats
CREATE TABLE IF NOT EXISTS maintenance_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    contract_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    contract_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'DRAFT',

    vendor_id UUID NOT NULL,
    vendor_contact VARCHAR(200),
    vendor_phone VARCHAR(50),
    vendor_email VARCHAR(200),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    renewal_date DATE,
    notice_period_days INTEGER,

    auto_renewal BOOLEAN DEFAULT FALSE,
    renewal_terms TEXT,

    covered_assets JSONB DEFAULT '[]',
    coverage_description TEXT,
    exclusions TEXT,

    response_time_hours INTEGER,
    resolution_time_hours INTEGER,
    availability_guarantee NUMERIC(5,2),

    contract_value NUMERIC(15,2),
    annual_cost NUMERIC(15,2),
    payment_frequency VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'EUR',

    includes_parts BOOLEAN DEFAULT FALSE,
    includes_labor BOOLEAN DEFAULT TRUE,
    includes_travel BOOLEAN DEFAULT FALSE,
    max_interventions INTEGER,
    interventions_used INTEGER DEFAULT 0,

    contract_file VARCHAR(500),
    documents JSONB DEFAULT '[]',
    manager_id UUID,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_mcontract_tenant ON maintenance_contracts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mcontract_code ON maintenance_contracts(tenant_id, contract_code);

-- KPIs Maintenance
CREATE TABLE IF NOT EXISTS maintenance_kpis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    asset_id UUID REFERENCES maintenance_assets(id),

    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20),

    availability_rate NUMERIC(5,2),
    uptime_hours NUMERIC(12,2),
    downtime_hours NUMERIC(12,2),
    planned_downtime_hours NUMERIC(12,2),
    unplanned_downtime_hours NUMERIC(12,2),

    mtbf_hours NUMERIC(10,2),
    mttr_hours NUMERIC(10,2),
    mttf_hours NUMERIC(10,2),
    failure_count INTEGER DEFAULT 0,

    wo_total INTEGER DEFAULT 0,
    wo_preventive INTEGER DEFAULT 0,
    wo_corrective INTEGER DEFAULT 0,
    wo_completed INTEGER DEFAULT 0,
    wo_overdue INTEGER DEFAULT 0,
    wo_on_time_rate NUMERIC(5,2),

    total_maintenance_cost NUMERIC(15,2),
    labor_cost NUMERIC(15,2),
    parts_cost NUMERIC(15,2),
    external_cost NUMERIC(15,2),
    cost_per_asset NUMERIC(15,2),
    cost_per_hour NUMERIC(15,2),

    preventive_ratio NUMERIC(5,2),
    schedule_compliance NUMERIC(5,2),
    work_order_backlog INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mkpi_tenant ON maintenance_kpis(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mkpi_asset ON maintenance_kpis(asset_id);
CREATE INDEX IF NOT EXISTS idx_mkpi_period ON maintenance_kpis(period_start, period_end);


-- ============================================================================
-- QUALITY MODULE - TABLES WITH UUID
-- ============================================================================

-- CAPA (créé en premier car référencé par d'autres tables)
CREATE TABLE IF NOT EXISTS quality_capas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    capa_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    capa_type VARCHAR(50) NOT NULL,

    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id UUID,

    status VARCHAR(50) DEFAULT 'DRAFT',
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    open_date DATE NOT NULL,
    target_close_date DATE,
    actual_close_date DATE,

    owner_id UUID NOT NULL,
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
    verified_by_id UUID,

    extension_required BOOLEAN DEFAULT FALSE,
    extension_scope TEXT,
    extension_completed BOOLEAN DEFAULT FALSE,

    closure_comments TEXT,
    closed_by_id UUID,

    attachments JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_capa_tenant ON quality_capas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_capa_number ON quality_capas(tenant_id, capa_number);
CREATE INDEX IF NOT EXISTS idx_capa_type ON quality_capas(tenant_id, capa_type);
CREATE INDEX IF NOT EXISTS idx_capa_status ON quality_capas(tenant_id, status);

-- Actions CAPA
CREATE TABLE IF NOT EXISTS quality_capa_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    capa_id UUID NOT NULL REFERENCES quality_capas(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id UUID,

    planned_date DATE,
    due_date DATE NOT NULL,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',

    result TEXT,
    evidence TEXT,

    verification_required BOOLEAN DEFAULT TRUE,
    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id UUID,
    verification_result TEXT,

    estimated_cost NUMERIC(15,2),
    actual_cost NUMERIC(15,2),

    comments TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_capa_action_tenant ON quality_capa_actions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_capa_action_capa ON quality_capa_actions(capa_id);
CREATE INDEX IF NOT EXISTS idx_capa_action_status ON quality_capa_actions(status);

-- Non-conformités
CREATE TABLE IF NOT EXISTS quality_non_conformances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    nc_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    nc_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'DRAFT',
    severity VARCHAR(50) NOT NULL,

    detected_date DATE NOT NULL,
    detected_by_id UUID,
    detection_location VARCHAR(200),
    detection_phase VARCHAR(100),

    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id UUID,

    product_id UUID,
    lot_number VARCHAR(100),
    serial_number VARCHAR(100),
    quantity_affected NUMERIC(15,3),
    unit_id UUID,

    supplier_id UUID,
    customer_id UUID,

    immediate_cause TEXT,
    root_cause TEXT,
    cause_analysis_method VARCHAR(100),
    cause_analysis_date DATE,
    cause_analyzed_by_id UUID,

    impact_description TEXT,
    estimated_cost NUMERIC(15,2),
    actual_cost NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    immediate_action TEXT,
    immediate_action_date TIMESTAMPTZ,
    immediate_action_by_id UUID,

    responsible_id UUID,
    department VARCHAR(100),

    disposition VARCHAR(50),
    disposition_date DATE,
    disposition_by_id UUID,
    disposition_justification TEXT,

    capa_id UUID REFERENCES quality_capas(id),
    capa_required BOOLEAN DEFAULT FALSE,

    closed_date DATE,
    closed_by_id UUID,
    closure_justification TEXT,
    effectiveness_verified BOOLEAN DEFAULT FALSE,
    effectiveness_date DATE,

    attachments JSONB DEFAULT '[]',
    notes TEXT,

    is_recurrent BOOLEAN DEFAULT FALSE,
    recurrence_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS idx_nc_tenant ON quality_non_conformances(tenant_id);
CREATE INDEX IF NOT EXISTS idx_nc_type ON quality_non_conformances(tenant_id, nc_type);
CREATE INDEX IF NOT EXISTS idx_nc_status ON quality_non_conformances(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_nc_severity ON quality_non_conformances(tenant_id, severity);
CREATE INDEX IF NOT EXISTS idx_nc_detected ON quality_non_conformances(tenant_id, detected_date);

-- Actions NC
CREATE TABLE IF NOT EXISTS quality_nc_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    nc_id UUID NOT NULL REFERENCES quality_non_conformances(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id UUID,

    planned_date DATE,
    due_date DATE,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',

    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id UUID,
    verification_result TEXT,

    comments TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_nc_action_tenant ON quality_nc_actions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_nc_action_nc ON quality_nc_actions(nc_id);
CREATE INDEX IF NOT EXISTS idx_nc_action_status ON quality_nc_actions(status);

-- Templates contrôle qualité
CREATE TABLE IF NOT EXISTS quality_control_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',

    control_type VARCHAR(50) NOT NULL,

    applies_to VARCHAR(50),
    product_category_id UUID,

    instructions TEXT,
    sampling_plan TEXT,
    acceptance_criteria TEXT,

    estimated_duration_minutes INTEGER,
    required_equipment JSONB DEFAULT '[]',

    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_qct_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_qct_tenant ON quality_control_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qct_code ON quality_control_templates(tenant_id, code);

-- Items template
CREATE TABLE IF NOT EXISTS quality_control_template_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    template_id UUID NOT NULL REFERENCES quality_control_templates(id) ON DELETE CASCADE,

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

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qcti_tenant ON quality_control_template_items(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qcti_template ON quality_control_template_items(template_id);

-- Contrôles qualité
CREATE TABLE IF NOT EXISTS quality_controls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    control_number VARCHAR(50) NOT NULL,
    template_id UUID REFERENCES quality_control_templates(id),
    control_type VARCHAR(50) NOT NULL,

    source_type VARCHAR(50),
    source_reference VARCHAR(100),
    source_id UUID,

    product_id UUID,
    lot_number VARCHAR(100),
    serial_number VARCHAR(100),

    quantity_to_control NUMERIC(15,3),
    quantity_controlled NUMERIC(15,3),
    quantity_conforming NUMERIC(15,3),
    quantity_non_conforming NUMERIC(15,3),
    unit_id UUID,

    supplier_id UUID,
    customer_id UUID,

    control_date DATE NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    location VARCHAR(200),

    controller_id UUID,

    status VARCHAR(50) DEFAULT 'PLANNED',
    result VARCHAR(50),
    result_date TIMESTAMPTZ,

    decision VARCHAR(50),
    decision_by_id UUID,
    decision_date TIMESTAMPTZ,
    decision_comments TEXT,

    nc_id UUID REFERENCES quality_non_conformances(id),

    observations TEXT,
    attachments JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_qc_tenant ON quality_controls(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qc_number ON quality_controls(tenant_id, control_number);
CREATE INDEX IF NOT EXISTS idx_qc_type ON quality_controls(tenant_id, control_type);
CREATE INDEX IF NOT EXISTS idx_qc_status ON quality_controls(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_qc_date ON quality_controls(tenant_id, control_date);

-- Lignes contrôle
CREATE TABLE IF NOT EXISTS quality_control_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    control_id UUID NOT NULL REFERENCES quality_controls(id) ON DELETE CASCADE,
    template_item_id UUID REFERENCES quality_control_template_items(id),

    sequence INTEGER NOT NULL,
    characteristic VARCHAR(200) NOT NULL,

    nominal_value NUMERIC(15,6),
    tolerance_min NUMERIC(15,6),
    tolerance_max NUMERIC(15,6),
    unit VARCHAR(50),

    measured_value NUMERIC(15,6),
    measured_text VARCHAR(500),
    measured_boolean BOOLEAN,
    measurement_date TIMESTAMPTZ,

    result VARCHAR(50),
    deviation NUMERIC(15,6),

    equipment_code VARCHAR(100),
    equipment_serial VARCHAR(100),

    comments TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_qcl_tenant ON quality_control_lines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qcl_control ON quality_control_lines(control_id);

-- Audits
CREATE TABLE IF NOT EXISTS quality_audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    audit_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    audit_type VARCHAR(50) NOT NULL,

    reference_standard VARCHAR(200),
    reference_version VARCHAR(50),
    audit_scope TEXT,

    planned_date DATE,
    planned_end_date DATE,
    actual_date DATE,
    actual_end_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',

    lead_auditor_id UUID,
    auditors JSONB DEFAULT '[]',

    audited_entity VARCHAR(200),
    audited_department VARCHAR(200),
    auditee_contact_id UUID,

    supplier_id UUID,

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
    closed_by_id UUID,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON quality_audits(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_number ON quality_audits(tenant_id, audit_number);
CREATE INDEX IF NOT EXISTS idx_audit_type ON quality_audits(tenant_id, audit_type);
CREATE INDEX IF NOT EXISTS idx_audit_status ON quality_audits(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_date ON quality_audits(tenant_id, planned_date);

-- Constats audit
CREATE TABLE IF NOT EXISTS quality_audit_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    audit_id UUID NOT NULL REFERENCES quality_audits(id) ON DELETE CASCADE,

    finding_number INTEGER NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,

    severity VARCHAR(50) NOT NULL,
    category VARCHAR(100),

    clause_reference VARCHAR(100),
    process_reference VARCHAR(100),
    evidence TEXT,

    risk_description TEXT,
    risk_level VARCHAR(50),

    capa_required BOOLEAN DEFAULT FALSE,
    capa_id UUID REFERENCES quality_capas(id),

    auditee_response TEXT,
    response_date DATE,

    action_due_date DATE,
    action_completed_date DATE,
    status VARCHAR(50) DEFAULT 'OPEN',

    verified BOOLEAN DEFAULT FALSE,
    verified_date DATE,
    verified_by_id UUID,
    verification_comments TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_finding_tenant ON quality_audit_findings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_finding_audit ON quality_audit_findings(audit_id);
CREATE INDEX IF NOT EXISTS idx_finding_severity ON quality_audit_findings(severity);

-- Réclamations clients
CREATE TABLE IF NOT EXISTS quality_customer_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    claim_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,

    customer_id UUID NOT NULL,
    customer_contact VARCHAR(200),
    customer_reference VARCHAR(100),

    received_date DATE NOT NULL,
    received_via VARCHAR(50),
    received_by_id UUID,

    product_id UUID,
    order_reference VARCHAR(100),
    invoice_reference VARCHAR(100),
    lot_number VARCHAR(100),
    quantity_affected NUMERIC(15,3),

    claim_type VARCHAR(50),
    severity VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    status VARCHAR(50) DEFAULT 'RECEIVED',

    owner_id UUID,

    investigation_summary TEXT,
    root_cause TEXT,
    our_responsibility BOOLEAN,

    nc_id UUID REFERENCES quality_non_conformances(id),
    capa_id UUID REFERENCES quality_capas(id),

    response_due_date DATE,
    response_date DATE,
    response_content TEXT,
    response_by_id UUID,

    resolution_type VARCHAR(50),
    resolution_description TEXT,
    resolution_date DATE,

    claim_amount NUMERIC(15,2),
    accepted_amount NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    customer_satisfied BOOLEAN,
    satisfaction_feedback TEXT,

    closed_date DATE,
    closed_by_id UUID,

    attachments JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_claim_tenant ON quality_customer_claims(tenant_id);
CREATE INDEX IF NOT EXISTS idx_claim_number ON quality_customer_claims(tenant_id, claim_number);
CREATE INDEX IF NOT EXISTS idx_claim_status ON quality_customer_claims(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_claim_customer ON quality_customer_claims(tenant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_claim_date ON quality_customer_claims(tenant_id, received_date);

-- Actions réclamation
CREATE TABLE IF NOT EXISTS quality_claim_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    claim_id UUID NOT NULL REFERENCES quality_customer_claims(id) ON DELETE CASCADE,

    action_number INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,

    responsible_id UUID,

    due_date DATE,
    completed_date DATE,

    status VARCHAR(50) DEFAULT 'PLANNED',
    result TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_claim_action_tenant ON quality_claim_actions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_claim_action_claim ON quality_claim_actions(claim_id);

-- Indicateurs qualité
CREATE TABLE IF NOT EXISTS quality_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

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

    owner_id UUID,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT uq_qi_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_qi_tenant ON quality_indicators(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qi_code ON quality_indicators(tenant_id, code);

-- Mesures indicateurs
CREATE TABLE IF NOT EXISTS quality_indicator_measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    indicator_id UUID NOT NULL REFERENCES quality_indicators(id) ON DELETE CASCADE,

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

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_qim_tenant ON quality_indicator_measurements(tenant_id);
CREATE INDEX IF NOT EXISTS idx_qim_indicator ON quality_indicator_measurements(indicator_id);
CREATE INDEX IF NOT EXISTS idx_qim_date ON quality_indicator_measurements(measurement_date);

-- Certifications
CREATE TABLE IF NOT EXISTS quality_certifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

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

    status VARCHAR(50) DEFAULT 'PLANNED',

    manager_id UUID,

    annual_cost NUMERIC(15,2),
    cost_currency VARCHAR(3) DEFAULT 'EUR',

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_cert_tenant ON quality_certifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cert_code ON quality_certifications(tenant_id, code);
CREATE INDEX IF NOT EXISTS idx_cert_status ON quality_certifications(tenant_id, status);

-- Audits certification
CREATE TABLE IF NOT EXISTS quality_certification_audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    certification_id UUID NOT NULL REFERENCES quality_certifications(id) ON DELETE CASCADE,

    audit_type VARCHAR(50) NOT NULL,

    audit_date DATE NOT NULL,
    audit_end_date DATE,

    lead_auditor VARCHAR(200),
    audit_team JSONB DEFAULT '[]',

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

    quality_audit_id UUID REFERENCES quality_audits(id),

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_cert_audit_tenant ON quality_certification_audits(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cert_audit_cert ON quality_certification_audits(certification_id);
CREATE INDEX IF NOT EXISTS idx_cert_audit_date ON quality_certification_audits(audit_date);


-- ============================================================================
-- TRIGGERS - Updated timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Maintenance triggers
CREATE TRIGGER trg_maintenance_assets_updated BEFORE UPDATE ON maintenance_assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_components_updated BEFORE UPDATE ON maintenance_asset_components FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_meters_updated BEFORE UPDATE ON maintenance_asset_meters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_plans_updated BEFORE UPDATE ON maintenance_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_plan_tasks_updated BEFORE UPDATE ON maintenance_plan_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_spare_parts_updated BEFORE UPDATE ON maintenance_spare_parts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_spare_stock_updated BEFORE UPDATE ON maintenance_spare_part_stock FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_failures_updated BEFORE UPDATE ON maintenance_failures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_work_orders_updated BEFORE UPDATE ON maintenance_work_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_wo_tasks_updated BEFORE UPDATE ON maintenance_wo_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_part_requests_updated BEFORE UPDATE ON maintenance_part_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_maintenance_contracts_updated BEFORE UPDATE ON maintenance_contracts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Quality triggers
CREATE TRIGGER trg_quality_capas_updated BEFORE UPDATE ON quality_capas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_capa_actions_updated BEFORE UPDATE ON quality_capa_actions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_non_conformances_updated BEFORE UPDATE ON quality_non_conformances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_nc_actions_updated BEFORE UPDATE ON quality_nc_actions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_control_templates_updated BEFORE UPDATE ON quality_control_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_control_template_items_updated BEFORE UPDATE ON quality_control_template_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_controls_updated BEFORE UPDATE ON quality_controls FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_audits_updated BEFORE UPDATE ON quality_audits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_audit_findings_updated BEFORE UPDATE ON quality_audit_findings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_customer_claims_updated BEFORE UPDATE ON quality_customer_claims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_claim_actions_updated BEFORE UPDATE ON quality_claim_actions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_indicators_updated BEFORE UPDATE ON quality_indicators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_certifications_updated BEFORE UPDATE ON quality_certifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_quality_certification_audits_updated BEFORE UPDATE ON quality_certification_audits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- FIN MIGRATION UUID
-- ============================================================================
