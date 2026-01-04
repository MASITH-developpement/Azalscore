-- ============================================================================
-- AZALS MODULE M8 - Migration Maintenance (GMAO)
-- ============================================================================
-- Version: 1.0.0
-- Module: M8 - Maintenance / Asset Management
-- Date: 2026-01-04
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE asset_category AS ENUM (
        'MACHINE', 'EQUIPMENT', 'VEHICLE', 'BUILDING', 'INFRASTRUCTURE',
        'IT_EQUIPMENT', 'TOOL', 'UTILITY', 'FURNITURE', 'OTHER'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE asset_status AS ENUM (
        'ACTIVE', 'INACTIVE', 'IN_MAINTENANCE', 'RESERVED',
        'DISPOSED', 'UNDER_REPAIR', 'STANDBY'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE asset_criticality AS ENUM (
        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE maintenance_type AS ENUM (
        'PREVENTIVE', 'CORRECTIVE', 'PREDICTIVE', 'CONDITION_BASED',
        'BREAKDOWN', 'IMPROVEMENT', 'INSPECTION', 'CALIBRATION'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE work_order_status AS ENUM (
        'DRAFT', 'REQUESTED', 'APPROVED', 'PLANNED', 'ASSIGNED',
        'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'VERIFIED', 'CLOSED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE work_order_priority AS ENUM (
        'EMERGENCY', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SCHEDULED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE failure_type AS ENUM (
        'MECHANICAL', 'ELECTRICAL', 'ELECTRONIC', 'HYDRAULIC', 'PNEUMATIC',
        'SOFTWARE', 'OPERATOR_ERROR', 'WEAR', 'CONTAMINATION', 'UNKNOWN'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE part_request_status AS ENUM (
        'REQUESTED', 'APPROVED', 'ORDERED', 'RECEIVED', 'ISSUED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE contract_type_maint AS ENUM (
        'FULL_SERVICE', 'PREVENTIVE', 'ON_CALL', 'PARTS_ONLY', 'LABOR_ONLY', 'WARRANTY'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE contract_status_maint AS ENUM (
        'DRAFT', 'ACTIVE', 'SUSPENDED', 'EXPIRED', 'TERMINATED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================================
-- TABLES - ACTIFS
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_assets (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    -- Identification
    asset_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category asset_category NOT NULL,
    asset_type VARCHAR(100),

    -- Statut
    status asset_status DEFAULT 'ACTIVE',
    criticality asset_criticality DEFAULT 'MEDIUM',

    -- Hiérarchie
    parent_id BIGINT REFERENCES maintenance_assets(id),

    -- Localisation
    location_id BIGINT,
    location_description VARCHAR(200),
    building VARCHAR(100),
    floor VARCHAR(50),
    area VARCHAR(100),

    -- Fabricant
    manufacturer VARCHAR(200),
    model VARCHAR(200),
    serial_number VARCHAR(100),
    year_manufactured INTEGER,

    -- Dates
    purchase_date DATE,
    installation_date DATE,
    warranty_start_date DATE,
    warranty_end_date DATE,
    expected_end_of_life DATE,
    last_maintenance_date DATE,
    next_maintenance_date DATE,

    -- Valeur
    purchase_cost NUMERIC(15,2),
    current_value NUMERIC(15,2),
    replacement_cost NUMERIC(15,2),
    salvage_value NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Amortissement
    depreciation_method VARCHAR(50),
    useful_life_years INTEGER,
    depreciation_rate NUMERIC(5,2),

    -- Spécifications
    specifications JSONB,
    power_rating VARCHAR(100),
    dimensions VARCHAR(200),
    weight NUMERIC(10,2),
    weight_unit VARCHAR(20),

    -- Compteurs
    operating_hours NUMERIC(12,2) DEFAULT 0,
    cycle_count BIGINT DEFAULT 0,
    energy_consumption NUMERIC(15,4),

    -- Maintenance
    maintenance_strategy VARCHAR(50),
    default_maintenance_plan_id BIGINT,

    -- Fournisseur
    supplier_id BIGINT,

    -- Responsable
    responsible_id BIGINT REFERENCES users(id),
    department VARCHAR(100),

    -- Contrat
    contract_id BIGINT,

    -- Média
    photo_url VARCHAR(500),
    documents JSONB,

    -- Notes
    notes TEXT,

    -- QR Code
    barcode VARCHAR(100),
    qr_code VARCHAR(200),

    -- KPIs
    mtbf_hours NUMERIC(10,2),
    mttr_hours NUMERIC(10,2),
    availability_rate NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id),

    CONSTRAINT uq_asset_code UNIQUE (tenant_id, asset_code)
);

CREATE INDEX IF NOT EXISTS idx_asset_tenant ON maintenance_assets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_asset_code ON maintenance_assets(tenant_id, asset_code);
CREATE INDEX IF NOT EXISTS idx_asset_category ON maintenance_assets(tenant_id, category);
CREATE INDEX IF NOT EXISTS idx_asset_status ON maintenance_assets(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_asset_location ON maintenance_assets(tenant_id, location_id);


-- Table composants
CREATE TABLE IF NOT EXISTS maintenance_asset_components (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    asset_id BIGINT NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

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
    current_cycles BIGINT DEFAULT 0,

    criticality asset_criticality,
    spare_part_id BIGINT,

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_component_asset ON maintenance_asset_components(asset_id);


-- Table documents actif
CREATE TABLE IF NOT EXISTS maintenance_asset_documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    asset_id BIGINT NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

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
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_asset_doc_asset ON maintenance_asset_documents(asset_id);


-- Table compteurs
CREATE TABLE IF NOT EXISTS maintenance_asset_meters (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    asset_id BIGINT NOT NULL REFERENCES maintenance_assets(id) ON DELETE CASCADE,

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
    created_by BIGINT REFERENCES users(id),

    CONSTRAINT uq_asset_meter UNIQUE (asset_id, meter_code)
);

CREATE INDEX IF NOT EXISTS idx_meter_asset ON maintenance_asset_meters(asset_id);


-- Table relevés compteur
CREATE TABLE IF NOT EXISTS maintenance_meter_readings (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    meter_id BIGINT NOT NULL REFERENCES maintenance_asset_meters(id) ON DELETE CASCADE,

    reading_date TIMESTAMPTZ NOT NULL,
    reading_value NUMERIC(15,4) NOT NULL,
    delta NUMERIC(15,4),

    source VARCHAR(50),
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_reading_meter ON maintenance_meter_readings(meter_id);
CREATE INDEX IF NOT EXISTS idx_reading_date ON maintenance_meter_readings(reading_date);


-- ============================================================================
-- TABLES - PLANS DE MAINTENANCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_plans (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    plan_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    maintenance_type maintenance_type NOT NULL,

    asset_id BIGINT REFERENCES maintenance_assets(id),
    asset_category asset_category,

    trigger_type VARCHAR(50) NOT NULL,
    frequency_value INTEGER,
    frequency_unit VARCHAR(20),

    trigger_meter_id BIGINT REFERENCES maintenance_asset_meters(id),
    trigger_meter_interval NUMERIC(15,4),

    last_execution_date DATE,
    next_due_date DATE,
    lead_time_days INTEGER DEFAULT 7,

    estimated_duration_hours NUMERIC(6,2),

    responsible_id BIGINT REFERENCES users(id),

    is_active BOOLEAN DEFAULT TRUE,

    estimated_labor_cost NUMERIC(15,2),
    estimated_parts_cost NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    instructions TEXT,
    safety_instructions TEXT,
    required_tools JSONB,
    required_certifications JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id),

    CONSTRAINT uq_mplan_code UNIQUE (tenant_id, plan_code)
);

CREATE INDEX IF NOT EXISTS idx_mplan_tenant ON maintenance_plans(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mplan_code ON maintenance_plans(tenant_id, plan_code);


-- Table tâches plan
CREATE TABLE IF NOT EXISTS maintenance_plan_tasks (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    plan_id BIGINT NOT NULL REFERENCES maintenance_plans(id) ON DELETE CASCADE,

    sequence INTEGER NOT NULL,
    task_code VARCHAR(50),
    description TEXT NOT NULL,
    detailed_instructions TEXT,

    estimated_duration_minutes INTEGER,
    required_skill VARCHAR(100),
    required_parts JSONB,
    check_points JSONB,

    is_mandatory BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mplan_task_plan ON maintenance_plan_tasks(plan_id);


-- ============================================================================
-- TABLES - ORDRES DE TRAVAIL
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_work_orders (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    wo_number VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,

    maintenance_type maintenance_type NOT NULL,
    priority work_order_priority DEFAULT 'MEDIUM',
    status work_order_status DEFAULT 'DRAFT',

    asset_id BIGINT NOT NULL REFERENCES maintenance_assets(id),
    component_id BIGINT REFERENCES maintenance_asset_components(id),

    source VARCHAR(50),
    source_reference VARCHAR(100),
    maintenance_plan_id BIGINT REFERENCES maintenance_plans(id),
    failure_id BIGINT,

    requester_id BIGINT REFERENCES users(id),
    request_date TIMESTAMPTZ,
    request_description TEXT,

    scheduled_start_date TIMESTAMPTZ,
    scheduled_end_date TIMESTAMPTZ,
    due_date TIMESTAMPTZ,

    actual_start_date TIMESTAMPTZ,
    actual_end_date TIMESTAMPTZ,
    downtime_hours NUMERIC(8,2),

    assigned_to_id BIGINT REFERENCES users(id),
    team_id BIGINT,
    external_vendor_id BIGINT,

    work_instructions TEXT,
    safety_precautions TEXT,
    tools_required JSONB,
    certifications_required JSONB,

    location_description VARCHAR(200),

    completion_notes TEXT,
    completed_by_id BIGINT REFERENCES users(id),
    verification_required BOOLEAN DEFAULT FALSE,
    verified_by_id BIGINT REFERENCES users(id),
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

    attachments JSONB,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_wo_tenant ON maintenance_work_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_wo_number ON maintenance_work_orders(tenant_id, wo_number);
CREATE INDEX IF NOT EXISTS idx_wo_asset ON maintenance_work_orders(tenant_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_wo_status ON maintenance_work_orders(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_wo_priority ON maintenance_work_orders(tenant_id, priority);
CREATE INDEX IF NOT EXISTS idx_wo_scheduled ON maintenance_work_orders(tenant_id, scheduled_start_date);


-- Table tâches OT
CREATE TABLE IF NOT EXISTS maintenance_wo_tasks (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    work_order_id BIGINT NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
    plan_task_id BIGINT REFERENCES maintenance_plan_tasks(id),

    sequence INTEGER NOT NULL,
    description TEXT NOT NULL,
    instructions TEXT,

    estimated_minutes INTEGER,
    actual_minutes INTEGER,

    status VARCHAR(50) DEFAULT 'PENDING',
    completed_date TIMESTAMPTZ,
    completed_by_id BIGINT REFERENCES users(id),

    result TEXT,
    issues_found TEXT,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wo_task_wo ON maintenance_wo_tasks(work_order_id);


-- Table main d'œuvre OT
CREATE TABLE IF NOT EXISTS maintenance_wo_labor (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    work_order_id BIGINT NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,

    technician_id BIGINT NOT NULL REFERENCES users(id),
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
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_wo_labor_wo ON maintenance_wo_labor(work_order_id);


-- Table pièces OT
CREATE TABLE IF NOT EXISTS maintenance_wo_parts (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    work_order_id BIGINT NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,

    spare_part_id BIGINT,
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
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_wo_part_wo ON maintenance_wo_parts(work_order_id);


-- ============================================================================
-- TABLES - PANNES
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_failures (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    failure_number VARCHAR(50) NOT NULL,

    asset_id BIGINT NOT NULL REFERENCES maintenance_assets(id),
    component_id BIGINT REFERENCES maintenance_asset_components(id),

    failure_type failure_type NOT NULL,
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

    reported_by_id BIGINT REFERENCES users(id),

    work_order_id BIGINT,

    resolution TEXT,
    root_cause TEXT,
    corrective_action TEXT,
    preventive_action TEXT,

    meter_reading NUMERIC(15,4),

    status VARCHAR(50) DEFAULT 'OPEN',

    notes TEXT,
    attachments JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_failure_tenant ON maintenance_failures(tenant_id);
CREATE INDEX IF NOT EXISTS idx_failure_asset ON maintenance_failures(tenant_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_failure_date ON maintenance_failures(tenant_id, failure_date);


-- Table causes panne
CREATE TABLE IF NOT EXISTS maintenance_failure_causes (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    failure_id BIGINT NOT NULL REFERENCES maintenance_failures(id) ON DELETE CASCADE,

    cause_category VARCHAR(100),
    cause_description TEXT NOT NULL,
    is_root_cause BOOLEAN DEFAULT FALSE,

    probability VARCHAR(20),
    recommended_action TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_failure_cause_failure ON maintenance_failure_causes(failure_id);


-- ============================================================================
-- TABLES - PIÈCES DE RECHANGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_spare_parts (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    part_code VARCHAR(100) NOT NULL,
    name VARCHAR(300) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    manufacturer VARCHAR(200),
    manufacturer_part_number VARCHAR(100),

    preferred_supplier_id BIGINT,

    equivalent_parts JSONB,

    unit VARCHAR(50) NOT NULL,

    unit_cost NUMERIC(15,2),
    last_purchase_price NUMERIC(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    min_stock_level NUMERIC(12,3) DEFAULT 0,
    max_stock_level NUMERIC(12,3),
    reorder_point NUMERIC(12,3),
    reorder_quantity NUMERIC(12,3),

    lead_time_days INTEGER,

    criticality asset_criticality,

    shelf_life_days INTEGER,

    is_active BOOLEAN DEFAULT TRUE,

    product_id BIGINT,

    notes TEXT,
    specifications JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id),

    CONSTRAINT uq_spare_code UNIQUE (tenant_id, part_code)
);

CREATE INDEX IF NOT EXISTS idx_spare_tenant ON maintenance_spare_parts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_spare_code ON maintenance_spare_parts(tenant_id, part_code);


-- Table stock pièces
CREATE TABLE IF NOT EXISTS maintenance_spare_part_stock (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),
    spare_part_id BIGINT NOT NULL REFERENCES maintenance_spare_parts(id) ON DELETE CASCADE,

    location_id BIGINT,
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

CREATE INDEX IF NOT EXISTS idx_spare_stock_part ON maintenance_spare_part_stock(spare_part_id);


-- Table demandes pièces
CREATE TABLE IF NOT EXISTS maintenance_part_requests (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    request_number VARCHAR(50) NOT NULL,

    work_order_id BIGINT REFERENCES maintenance_work_orders(id),

    spare_part_id BIGINT REFERENCES maintenance_spare_parts(id),
    part_description VARCHAR(300) NOT NULL,

    quantity_requested NUMERIC(12,3) NOT NULL,
    quantity_approved NUMERIC(12,3),
    quantity_issued NUMERIC(12,3),
    unit VARCHAR(50),

    priority work_order_priority DEFAULT 'MEDIUM',
    required_date DATE,

    status part_request_status DEFAULT 'REQUESTED',

    requester_id BIGINT REFERENCES users(id),
    request_date TIMESTAMPTZ,
    request_reason TEXT,

    approved_by_id BIGINT REFERENCES users(id),
    approved_date TIMESTAMPTZ,

    issued_by_id BIGINT REFERENCES users(id),
    issued_date TIMESTAMPTZ,

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_part_req_tenant ON maintenance_part_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_part_req_wo ON maintenance_part_requests(work_order_id);


-- ============================================================================
-- TABLES - CONTRATS
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_contracts (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    contract_code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    contract_type contract_type_maint NOT NULL,
    status contract_status_maint DEFAULT 'DRAFT',

    vendor_id BIGINT NOT NULL,
    vendor_contact VARCHAR(200),
    vendor_phone VARCHAR(50),
    vendor_email VARCHAR(200),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    renewal_date DATE,
    notice_period_days INTEGER,

    auto_renewal BOOLEAN DEFAULT FALSE,
    renewal_terms TEXT,

    covered_assets JSONB,
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
    documents JSONB,

    manager_id BIGINT REFERENCES users(id),

    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_mcontract_tenant ON maintenance_contracts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mcontract_code ON maintenance_contracts(tenant_id, contract_code);


-- ============================================================================
-- TABLES - KPIs
-- ============================================================================

CREATE TABLE IF NOT EXISTS maintenance_kpis (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id),

    asset_id BIGINT REFERENCES maintenance_assets(id),

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
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour les tables principales
CREATE OR REPLACE FUNCTION maintenance_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_maintenance_assets_updated ON maintenance_assets;
CREATE TRIGGER trg_maintenance_assets_updated
    BEFORE UPDATE ON maintenance_assets
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();

DROP TRIGGER IF EXISTS trg_maintenance_plans_updated ON maintenance_plans;
CREATE TRIGGER trg_maintenance_plans_updated
    BEFORE UPDATE ON maintenance_plans
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();

DROP TRIGGER IF EXISTS trg_maintenance_work_orders_updated ON maintenance_work_orders;
CREATE TRIGGER trg_maintenance_work_orders_updated
    BEFORE UPDATE ON maintenance_work_orders
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();

DROP TRIGGER IF EXISTS trg_maintenance_failures_updated ON maintenance_failures;
CREATE TRIGGER trg_maintenance_failures_updated
    BEFORE UPDATE ON maintenance_failures
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();

DROP TRIGGER IF EXISTS trg_maintenance_spare_parts_updated ON maintenance_spare_parts;
CREATE TRIGGER trg_maintenance_spare_parts_updated
    BEFORE UPDATE ON maintenance_spare_parts
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();

DROP TRIGGER IF EXISTS trg_maintenance_contracts_updated ON maintenance_contracts;
CREATE TRIGGER trg_maintenance_contracts_updated
    BEFORE UPDATE ON maintenance_contracts
    FOR EACH ROW EXECUTE FUNCTION maintenance_update_timestamp();


-- ============================================================================
-- FIN MIGRATION M8
-- ============================================================================
