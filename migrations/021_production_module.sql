-- ============================================================================
-- AZALS MODULE M6 - Migration Production (Manufacturing)
-- ============================================================================
-- Version: 1.0.0
-- Description: Tables pour la gestion de production
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE work_center_type AS ENUM ('MACHINE', 'ASSEMBLY', 'MANUAL', 'QUALITY', 'PACKAGING', 'OUTSOURCED');
CREATE TYPE work_center_status AS ENUM ('AVAILABLE', 'BUSY', 'MAINTENANCE', 'OFFLINE');
CREATE TYPE bom_type AS ENUM ('MANUFACTURING', 'KIT', 'PHANTOM', 'SUBCONTRACT');
CREATE TYPE bom_status AS ENUM ('DRAFT', 'ACTIVE', 'OBSOLETE');
CREATE TYPE operation_type AS ENUM ('SETUP', 'PRODUCTION', 'QUALITY_CHECK', 'CLEANING', 'PACKAGING', 'TRANSPORT');
CREATE TYPE mo_status AS ENUM ('DRAFT', 'CONFIRMED', 'PLANNED', 'IN_PROGRESS', 'DONE', 'CANCELLED');
CREATE TYPE mo_priority AS ENUM ('LOW', 'NORMAL', 'HIGH', 'URGENT');
CREATE TYPE work_order_status AS ENUM ('PENDING', 'READY', 'IN_PROGRESS', 'PAUSED', 'DONE', 'CANCELLED');
CREATE TYPE consumption_type AS ENUM ('MANUAL', 'AUTO_ON_START', 'AUTO_ON_COMPLETE');
CREATE TYPE scrap_reason AS ENUM ('DEFECT', 'DAMAGE', 'QUALITY', 'EXPIRED', 'OTHER');


-- ============================================================================
-- CENTRES DE TRAVAIL
-- ============================================================================

CREATE TABLE production_work_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    type work_center_type DEFAULT 'MACHINE',
    status work_center_status DEFAULT 'AVAILABLE',

    -- Localisation
    warehouse_id UUID,
    location VARCHAR(100),

    -- Capacité
    capacity NUMERIC(10,2) DEFAULT 1,
    efficiency NUMERIC(5,2) DEFAULT 100,
    oee_target NUMERIC(5,2) DEFAULT 85,

    -- Temps standards
    time_start NUMERIC(10,2) DEFAULT 0,
    time_stop NUMERIC(10,2) DEFAULT 0,
    time_before NUMERIC(10,2) DEFAULT 0,
    time_after NUMERIC(10,2) DEFAULT 0,

    -- Coûts
    cost_per_hour NUMERIC(12,4) DEFAULT 0,
    cost_per_cycle NUMERIC(12,4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Horaires
    working_hours_per_day NUMERIC(4,2) DEFAULT 8,
    working_days_per_week INTEGER DEFAULT 5,

    -- Responsable
    manager_id UUID,
    operator_ids JSONB,

    -- Configuration
    requires_approval BOOLEAN DEFAULT FALSE,
    allow_parallel BOOLEAN DEFAULT FALSE,
    notes TEXT,
    extra_data JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    CONSTRAINT unique_workcenter_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_wc_tenant ON production_work_centers(tenant_id);
CREATE INDEX idx_wc_status ON production_work_centers(tenant_id, status);


CREATE TABLE production_wc_capacity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    work_center_id UUID NOT NULL REFERENCES production_work_centers(id) ON DELETE CASCADE,

    date DATE NOT NULL,
    shift VARCHAR(20) DEFAULT 'DAY',

    available_hours NUMERIC(4,2) NOT NULL,
    planned_hours NUMERIC(4,2) DEFAULT 0,
    actual_hours NUMERIC(4,2) DEFAULT 0,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_wc_capacity UNIQUE (tenant_id, work_center_id, date, shift)
);

CREATE INDEX idx_wc_cap_date ON production_wc_capacity(tenant_id, work_center_id, date);


-- ============================================================================
-- GAMMES DE FABRICATION
-- ============================================================================

CREATE TABLE production_routings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',

    product_id UUID,
    status bom_status DEFAULT 'DRAFT',

    -- Temps totaux calculés
    total_setup_time NUMERIC(10,2) DEFAULT 0,
    total_operation_time NUMERIC(10,2) DEFAULT 0,
    total_time NUMERIC(10,2) DEFAULT 0,

    -- Coûts calculés
    total_labor_cost NUMERIC(12,4) DEFAULT 0,
    total_machine_cost NUMERIC(12,4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    notes TEXT,
    extra_data JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    CONSTRAINT unique_routing_code_version UNIQUE (tenant_id, code, version)
);

CREATE INDEX idx_routing_tenant ON production_routings(tenant_id);
CREATE INDEX idx_routing_product ON production_routings(tenant_id, product_id);


CREATE TABLE production_routing_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    routing_id UUID NOT NULL REFERENCES production_routings(id) ON DELETE CASCADE,

    sequence INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    type operation_type DEFAULT 'PRODUCTION',
    work_center_id UUID REFERENCES production_work_centers(id),

    -- Temps standards
    setup_time NUMERIC(10,2) DEFAULT 0,
    operation_time NUMERIC(10,2) DEFAULT 0,
    cleanup_time NUMERIC(10,2) DEFAULT 0,
    wait_time NUMERIC(10,2) DEFAULT 0,

    batch_size NUMERIC(10,2) DEFAULT 1,

    -- Coûts
    labor_cost_per_hour NUMERIC(12,4) DEFAULT 0,
    machine_cost_per_hour NUMERIC(12,4) DEFAULT 0,

    -- Configuration
    is_subcontracted BOOLEAN DEFAULT FALSE,
    subcontractor_id UUID,
    requires_quality_check BOOLEAN DEFAULT FALSE,
    skill_required VARCHAR(100),

    notes TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routing_op ON production_routing_operations(tenant_id, routing_id, sequence);


-- ============================================================================
-- NOMENCLATURES (BOM)
-- ============================================================================

CREATE TABLE production_bom (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',

    product_id UUID NOT NULL,
    quantity NUMERIC(12,4) DEFAULT 1,
    unit VARCHAR(20) DEFAULT 'UNIT',

    type bom_type DEFAULT 'MANUFACTURING',
    status bom_status DEFAULT 'DRAFT',

    routing_id UUID REFERENCES production_routings(id),

    -- Dates de validité
    valid_from DATE,
    valid_to DATE,

    -- Coûts calculés
    material_cost NUMERIC(12,4) DEFAULT 0,
    labor_cost NUMERIC(12,4) DEFAULT 0,
    overhead_cost NUMERIC(12,4) DEFAULT 0,
    total_cost NUMERIC(12,4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Configuration
    is_default BOOLEAN DEFAULT FALSE,
    allow_alternatives BOOLEAN DEFAULT TRUE,
    consumption_type consumption_type DEFAULT 'AUTO_ON_COMPLETE',

    notes TEXT,
    extra_data JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    CONSTRAINT unique_bom_code_version UNIQUE (tenant_id, code, version)
);

CREATE INDEX idx_bom_tenant ON production_bom(tenant_id);
CREATE INDEX idx_bom_product ON production_bom(tenant_id, product_id);


CREATE TABLE production_bom_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    bom_id UUID NOT NULL REFERENCES production_bom(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    product_id UUID NOT NULL,
    quantity NUMERIC(12,4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',

    operation_id UUID,
    scrap_rate NUMERIC(5,2) DEFAULT 0,

    is_critical BOOLEAN DEFAULT TRUE,
    alternative_group VARCHAR(50),
    consumption_type consumption_type,

    notes TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bom_line ON production_bom_lines(tenant_id, bom_id);


-- ============================================================================
-- ORDRES DE FABRICATION
-- ============================================================================

CREATE TABLE production_manufacturing_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    name VARCHAR(200),

    product_id UUID NOT NULL,
    bom_id UUID REFERENCES production_bom(id),
    routing_id UUID REFERENCES production_routings(id),

    -- Quantités
    quantity_planned NUMERIC(12,4) NOT NULL,
    quantity_produced NUMERIC(12,4) DEFAULT 0,
    quantity_scrapped NUMERIC(12,4) DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'UNIT',

    status mo_status DEFAULT 'DRAFT',
    priority mo_priority DEFAULT 'NORMAL',

    -- Dates
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    deadline TIMESTAMP,

    -- Localisation
    warehouse_id UUID,
    location_id UUID,

    -- Origine
    origin_type VARCHAR(50),
    origin_id UUID,
    origin_number VARCHAR(50),

    -- Coûts
    planned_cost NUMERIC(12,4) DEFAULT 0,
    actual_cost NUMERIC(12,4) DEFAULT 0,
    material_cost NUMERIC(12,4) DEFAULT 0,
    labor_cost NUMERIC(12,4) DEFAULT 0,
    overhead_cost NUMERIC(12,4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    responsible_id UUID,
    progress_percent NUMERIC(5,2) DEFAULT 0,

    notes TEXT,
    extra_data JSONB,

    confirmed_at TIMESTAMP,
    confirmed_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    CONSTRAINT unique_mo_number UNIQUE (tenant_id, number)
);

CREATE INDEX idx_mo_tenant ON production_manufacturing_orders(tenant_id);
CREATE INDEX idx_mo_status ON production_manufacturing_orders(tenant_id, status);
CREATE INDEX idx_mo_product ON production_manufacturing_orders(tenant_id, product_id);
CREATE INDEX idx_mo_dates ON production_manufacturing_orders(tenant_id, scheduled_start, scheduled_end);


-- ============================================================================
-- ORDRES DE TRAVAIL
-- ============================================================================

CREATE TABLE production_work_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    mo_id UUID NOT NULL REFERENCES production_manufacturing_orders(id) ON DELETE CASCADE,

    sequence INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    operation_id UUID REFERENCES production_routing_operations(id),
    work_center_id UUID REFERENCES production_work_centers(id),

    status work_order_status DEFAULT 'PENDING',

    -- Quantités
    quantity_planned NUMERIC(12,4) NOT NULL,
    quantity_done NUMERIC(12,4) DEFAULT 0,
    quantity_scrapped NUMERIC(12,4) DEFAULT 0,

    -- Temps planifiés
    setup_time_planned NUMERIC(10,2) DEFAULT 0,
    operation_time_planned NUMERIC(10,2) DEFAULT 0,

    -- Temps réels
    setup_time_actual NUMERIC(10,2) DEFAULT 0,
    operation_time_actual NUMERIC(10,2) DEFAULT 0,

    -- Dates
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,

    operator_id UUID,

    -- Coûts
    labor_cost NUMERIC(12,4) DEFAULT 0,
    machine_cost NUMERIC(12,4) DEFAULT 0,

    notes TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wo_mo ON production_work_orders(tenant_id, mo_id, sequence);
CREATE INDEX idx_wo_wc ON production_work_orders(tenant_id, work_center_id, status);


CREATE TABLE production_wo_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    work_order_id UUID NOT NULL REFERENCES production_work_orders(id) ON DELETE CASCADE,

    entry_type VARCHAR(20) NOT NULL,
    operator_id UUID NOT NULL,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes NUMERIC(10,2),

    quantity_produced NUMERIC(12,4) DEFAULT 0,
    quantity_scrapped NUMERIC(12,4) DEFAULT 0,
    scrap_reason scrap_reason,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wo_time ON production_wo_time_entries(tenant_id, work_order_id, start_time);


-- ============================================================================
-- CONSOMMATION DE MATIÈRES
-- ============================================================================

CREATE TABLE production_material_consumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    mo_id UUID NOT NULL REFERENCES production_manufacturing_orders(id) ON DELETE CASCADE,

    product_id UUID NOT NULL,
    bom_line_id UUID REFERENCES production_bom_lines(id),
    work_order_id UUID REFERENCES production_work_orders(id),

    -- Quantités
    quantity_planned NUMERIC(12,4) NOT NULL,
    quantity_consumed NUMERIC(12,4) DEFAULT 0,
    quantity_returned NUMERIC(12,4) DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'UNIT',

    -- Traçabilité
    lot_id UUID,
    serial_id UUID,
    warehouse_id UUID,
    location_id UUID,

    -- Coût
    unit_cost NUMERIC(12,4) DEFAULT 0,
    total_cost NUMERIC(12,4) DEFAULT 0,

    consumed_at TIMESTAMP,
    consumed_by UUID,

    notes TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_consumption_mo ON production_material_consumptions(tenant_id, mo_id);
CREATE INDEX idx_consumption_product ON production_material_consumptions(tenant_id, product_id);


-- ============================================================================
-- PRODUCTION OUTPUT
-- ============================================================================

CREATE TABLE production_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    mo_id UUID NOT NULL REFERENCES production_manufacturing_orders(id) ON DELETE CASCADE,
    work_order_id UUID REFERENCES production_work_orders(id),

    product_id UUID NOT NULL,
    quantity NUMERIC(12,4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',

    -- Traçabilité
    lot_id UUID,
    serial_ids JSONB,
    warehouse_id UUID,
    location_id UUID,

    -- Qualité
    is_quality_passed BOOLEAN DEFAULT TRUE,
    quality_notes TEXT,

    -- Coût
    unit_cost NUMERIC(12,4) DEFAULT 0,
    total_cost NUMERIC(12,4) DEFAULT 0,

    produced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    produced_by UUID,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_output_mo ON production_outputs(tenant_id, mo_id);
CREATE INDEX idx_output_product ON production_outputs(tenant_id, product_id);


-- ============================================================================
-- REBUTS
-- ============================================================================

CREATE TABLE production_scraps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    mo_id UUID REFERENCES production_manufacturing_orders(id),
    work_order_id UUID REFERENCES production_work_orders(id),

    product_id UUID NOT NULL,
    quantity NUMERIC(12,4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',

    lot_id UUID,
    serial_id UUID,

    reason scrap_reason DEFAULT 'DEFECT',
    reason_detail TEXT,
    work_center_id UUID,

    unit_cost NUMERIC(12,4) DEFAULT 0,
    total_cost NUMERIC(12,4) DEFAULT 0,

    scrapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scrapped_by UUID,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scrap_mo ON production_scraps(tenant_id, mo_id);
CREATE INDEX idx_scrap_product ON production_scraps(tenant_id, product_id);
CREATE INDEX idx_scrap_reason ON production_scraps(tenant_id, reason);


-- ============================================================================
-- PLANIFICATION
-- ============================================================================

CREATE TABLE production_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    planning_horizon_days INTEGER DEFAULT 30,

    status VARCHAR(20) DEFAULT 'DRAFT',
    planning_method VARCHAR(50) DEFAULT 'MRP',

    total_orders INTEGER DEFAULT 0,
    total_quantity NUMERIC(12,2) DEFAULT 0,
    total_hours NUMERIC(10,2) DEFAULT 0,

    notes TEXT,
    extra_data JSONB,

    generated_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by UUID,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    CONSTRAINT unique_plan_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_plan_tenant ON production_plans(tenant_id);
CREATE INDEX idx_plan_dates ON production_plans(tenant_id, start_date, end_date);


CREATE TABLE production_plan_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    plan_id UUID NOT NULL REFERENCES production_plans(id) ON DELETE CASCADE,

    product_id UUID NOT NULL,
    bom_id UUID,

    quantity_demanded NUMERIC(12,4) DEFAULT 0,
    quantity_available NUMERIC(12,4) DEFAULT 0,
    quantity_to_produce NUMERIC(12,4) DEFAULT 0,

    required_date DATE,
    planned_start DATE,
    planned_end DATE,

    mo_id UUID REFERENCES production_manufacturing_orders(id),

    priority mo_priority DEFAULT 'NORMAL',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plan_line ON production_plan_lines(tenant_id, plan_id);
CREATE INDEX idx_plan_line_product ON production_plan_lines(tenant_id, product_id);


-- ============================================================================
-- MAINTENANCE PRÉVENTIVE
-- ============================================================================

CREATE TABLE production_maintenance_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    work_center_id UUID NOT NULL REFERENCES production_work_centers(id) ON DELETE CASCADE,

    name VARCHAR(200) NOT NULL,
    description TEXT,

    frequency_type VARCHAR(20) NOT NULL,
    frequency_value INTEGER DEFAULT 1,
    duration_hours NUMERIC(6,2) DEFAULT 1,

    last_maintenance TIMESTAMP,
    next_maintenance TIMESTAMP,
    cycles_since_last INTEGER DEFAULT 0,
    hours_since_last NUMERIC(10,2) DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_maint_wc ON production_maintenance_schedules(tenant_id, work_center_id);
CREATE INDEX idx_maint_next ON production_maintenance_schedules(tenant_id, next_maintenance);


-- ============================================================================
-- TRIGGERS POUR updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_production_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_wc_updated_at
    BEFORE UPDATE ON production_work_centers
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_routing_updated_at
    BEFORE UPDATE ON production_routings
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_bom_updated_at
    BEFORE UPDATE ON production_bom
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_mo_updated_at
    BEFORE UPDATE ON production_manufacturing_orders
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_wo_updated_at
    BEFORE UPDATE ON production_work_orders
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_plan_updated_at
    BEFORE UPDATE ON production_plans
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();

CREATE TRIGGER trigger_maint_updated_at
    BEFORE UPDATE ON production_maintenance_schedules
    FOR EACH ROW EXECUTE FUNCTION update_production_updated_at();
