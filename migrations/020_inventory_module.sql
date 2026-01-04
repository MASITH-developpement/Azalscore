-- ============================================================================
-- AZALS MODULE M5 - STOCK (INVENTAIRE + LOGISTIQUE)
-- Migration SQL pour PostgreSQL
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE product_type AS ENUM ('STOCKABLE', 'CONSUMABLE', 'SERVICE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE product_status AS ENUM ('DRAFT', 'ACTIVE', 'DISCONTINUED', 'BLOCKED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE warehouse_type AS ENUM ('INTERNAL', 'EXTERNAL', 'TRANSIT', 'VIRTUAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE location_type AS ENUM ('STORAGE', 'RECEIVING', 'SHIPPING', 'PRODUCTION', 'QUALITY', 'VIRTUAL');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE movement_type AS ENUM ('IN', 'OUT', 'TRANSFER', 'ADJUSTMENT', 'PRODUCTION', 'RETURN', 'SCRAP');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE movement_status AS ENUM ('DRAFT', 'CONFIRMED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE inventory_status AS ENUM ('DRAFT', 'IN_PROGRESS', 'VALIDATED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE lot_status AS ENUM ('AVAILABLE', 'RESERVED', 'BLOCKED', 'EXPIRED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE valuation_method AS ENUM ('FIFO', 'LIFO', 'AVG', 'STANDARD');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE picking_status AS ENUM ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'DONE', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================================
-- TABLE: CATÉGORIES DE PRODUITS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES inventory_categories(id),

    default_valuation valuation_method DEFAULT 'AVG',
    default_account_id UUID,

    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_category_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_categories_tenant ON inventory_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON inventory_categories(tenant_id, parent_id);


-- ============================================================================
-- TABLE: ENTREPÔTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    type warehouse_type DEFAULT 'INTERNAL',

    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'France',

    manager_name VARCHAR(200),
    phone VARCHAR(50),
    email VARCHAR(255),

    is_default BOOLEAN DEFAULT FALSE,
    allow_negative BOOLEAN DEFAULT FALSE,

    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_warehouse_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_warehouses_tenant ON inventory_warehouses(tenant_id);


-- ============================================================================
-- TABLE: EMPLACEMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES inventory_warehouses(id) ON DELETE CASCADE,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    type location_type DEFAULT 'STORAGE',

    aisle VARCHAR(20),
    rack VARCHAR(20),
    level VARCHAR(20),
    position VARCHAR(20),

    max_weight_kg DECIMAL(10, 2),
    max_volume_m3 DECIMAL(10, 3),

    is_default BOOLEAN DEFAULT FALSE,
    requires_lot BOOLEAN DEFAULT FALSE,
    requires_serial BOOLEAN DEFAULT FALSE,

    barcode VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_location_code UNIQUE (tenant_id, warehouse_id, code)
);

CREATE INDEX IF NOT EXISTS idx_locations_tenant ON inventory_locations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_locations_warehouse ON inventory_locations(tenant_id, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_locations_barcode ON inventory_locations(tenant_id, barcode);


-- ============================================================================
-- TABLE: PRODUITS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    type product_type DEFAULT 'STOCKABLE',
    status product_status DEFAULT 'DRAFT',

    category_id UUID REFERENCES inventory_categories(id),

    barcode VARCHAR(100),
    ean13 VARCHAR(13),
    sku VARCHAR(100),
    manufacturer_code VARCHAR(100),

    unit VARCHAR(20) DEFAULT 'UNIT',
    purchase_unit VARCHAR(20),
    purchase_unit_factor DECIMAL(10, 4) DEFAULT 1,
    sale_unit VARCHAR(20),
    sale_unit_factor DECIMAL(10, 4) DEFAULT 1,

    standard_cost DECIMAL(15, 4) DEFAULT 0,
    average_cost DECIMAL(15, 4) DEFAULT 0,
    last_purchase_price DECIMAL(15, 4),
    sale_price DECIMAL(15, 4),
    currency VARCHAR(3) DEFAULT 'EUR',

    valuation_method valuation_method DEFAULT 'AVG',

    min_stock DECIMAL(15, 4) DEFAULT 0,
    max_stock DECIMAL(15, 4),
    reorder_point DECIMAL(15, 4),
    reorder_quantity DECIMAL(15, 4),
    lead_time_days INTEGER DEFAULT 0,

    weight_kg DECIMAL(10, 4),
    volume_m3 DECIMAL(10, 6),
    length_cm DECIMAL(10, 2),
    width_cm DECIMAL(10, 2),
    height_cm DECIMAL(10, 2),

    track_lot BOOLEAN DEFAULT FALSE,
    track_serial BOOLEAN DEFAULT FALSE,
    track_expiry BOOLEAN DEFAULT FALSE,
    expiry_warning_days INTEGER DEFAULT 30,

    default_warehouse_id UUID REFERENCES inventory_warehouses(id),
    default_location_id UUID REFERENCES inventory_locations(id),
    default_supplier_id UUID,

    stock_account_id UUID,
    expense_account_id UUID,
    income_account_id UUID,

    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    image_url VARCHAR(500),
    notes TEXT,

    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_product_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_products_tenant ON inventory_products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON inventory_products(tenant_id, category_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON inventory_products(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON inventory_products(tenant_id, barcode);
CREATE INDEX IF NOT EXISTS idx_products_sku ON inventory_products(tenant_id, sku);


-- ============================================================================
-- TABLE: NIVEAUX DE STOCK
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_stock_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    product_id UUID NOT NULL REFERENCES inventory_products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES inventory_warehouses(id),
    location_id UUID REFERENCES inventory_locations(id),

    quantity_on_hand DECIMAL(15, 4) DEFAULT 0,
    quantity_reserved DECIMAL(15, 4) DEFAULT 0,
    quantity_available DECIMAL(15, 4) DEFAULT 0,
    quantity_incoming DECIMAL(15, 4) DEFAULT 0,
    quantity_outgoing DECIMAL(15, 4) DEFAULT 0,

    total_value DECIMAL(15, 2) DEFAULT 0,
    average_cost DECIMAL(15, 4) DEFAULT 0,

    last_movement_at TIMESTAMP,
    last_count_at TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_stock_level UNIQUE (tenant_id, product_id, warehouse_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_stock_levels_tenant ON inventory_stock_levels(tenant_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_product ON inventory_stock_levels(tenant_id, product_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_warehouse ON inventory_stock_levels(tenant_id, warehouse_id);


-- ============================================================================
-- TABLE: LOTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_lots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    product_id UUID NOT NULL REFERENCES inventory_products(id) ON DELETE CASCADE,
    number VARCHAR(100) NOT NULL,
    status lot_status DEFAULT 'AVAILABLE',

    production_date DATE,
    expiry_date DATE,
    reception_date DATE,

    supplier_id UUID,
    supplier_lot VARCHAR(100),
    purchase_order_id UUID,

    initial_quantity DECIMAL(15, 4) DEFAULT 0,
    current_quantity DECIMAL(15, 4) DEFAULT 0,

    unit_cost DECIMAL(15, 4),

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_lot_number UNIQUE (tenant_id, product_id, number)
);

CREATE INDEX IF NOT EXISTS idx_lots_tenant ON inventory_lots(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lots_product ON inventory_lots(tenant_id, product_id);
CREATE INDEX IF NOT EXISTS idx_lots_expiry ON inventory_lots(tenant_id, expiry_date);
CREATE INDEX IF NOT EXISTS idx_lots_status ON inventory_lots(tenant_id, status);


-- ============================================================================
-- TABLE: NUMÉROS DE SÉRIE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_serial_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    product_id UUID NOT NULL REFERENCES inventory_products(id) ON DELETE CASCADE,
    lot_id UUID REFERENCES inventory_lots(id),
    number VARCHAR(100) NOT NULL,
    status lot_status DEFAULT 'AVAILABLE',

    warehouse_id UUID REFERENCES inventory_warehouses(id),
    location_id UUID REFERENCES inventory_locations(id),

    supplier_id UUID,
    purchase_order_id UUID,
    reception_date DATE,

    customer_id UUID,
    sale_order_id UUID,
    sale_date DATE,

    warranty_end_date DATE,

    unit_cost DECIMAL(15, 4),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_serial_number UNIQUE (tenant_id, product_id, number)
);

CREATE INDEX IF NOT EXISTS idx_serials_tenant ON inventory_serial_numbers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_serials_product ON inventory_serial_numbers(tenant_id, product_id);
CREATE INDEX IF NOT EXISTS idx_serials_status ON inventory_serial_numbers(tenant_id, status);


-- ============================================================================
-- TABLE: MOUVEMENTS DE STOCK
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    type movement_type NOT NULL,
    status movement_status DEFAULT 'DRAFT',

    movement_date TIMESTAMP NOT NULL,

    from_warehouse_id UUID REFERENCES inventory_warehouses(id),
    from_location_id UUID REFERENCES inventory_locations(id),
    to_warehouse_id UUID REFERENCES inventory_warehouses(id),
    to_location_id UUID REFERENCES inventory_locations(id),

    reference_type VARCHAR(50),
    reference_id UUID,
    reference_number VARCHAR(100),

    reason VARCHAR(255),
    notes TEXT,

    total_items INTEGER DEFAULT 0,
    total_quantity DECIMAL(15, 4) DEFAULT 0,
    total_value DECIMAL(15, 2) DEFAULT 0,

    created_by UUID,
    confirmed_by UUID,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_movement_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_movements_tenant ON inventory_movements(tenant_id);
CREATE INDEX IF NOT EXISTS idx_movements_type ON inventory_movements(tenant_id, type);
CREATE INDEX IF NOT EXISTS idx_movements_status ON inventory_movements(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_movements_date ON inventory_movements(tenant_id, movement_date);
CREATE INDEX IF NOT EXISTS idx_movements_reference ON inventory_movements(tenant_id, reference_type, reference_id);


-- ============================================================================
-- TABLE: LIGNES DE MOUVEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_movement_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    movement_id UUID NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    product_id UUID NOT NULL REFERENCES inventory_products(id),

    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',

    lot_id UUID REFERENCES inventory_lots(id),
    serial_id UUID REFERENCES inventory_serial_numbers(id),

    from_location_id UUID REFERENCES inventory_locations(id),
    to_location_id UUID REFERENCES inventory_locations(id),

    unit_cost DECIMAL(15, 4),
    total_cost DECIMAL(15, 2),

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movement_lines_movement ON inventory_movement_lines(movement_id);
CREATE INDEX IF NOT EXISTS idx_movement_lines_tenant ON inventory_movement_lines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_movement_lines_product ON inventory_movement_lines(tenant_id, product_id);


-- ============================================================================
-- TABLE: INVENTAIRES PHYSIQUES
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    status inventory_status DEFAULT 'DRAFT',

    warehouse_id UUID REFERENCES inventory_warehouses(id),
    location_id UUID REFERENCES inventory_locations(id),
    category_id UUID REFERENCES inventory_categories(id),

    planned_date DATE NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    total_items INTEGER DEFAULT 0,
    counted_items INTEGER DEFAULT 0,
    discrepancy_items INTEGER DEFAULT 0,
    total_discrepancy_value DECIMAL(15, 2) DEFAULT 0,

    notes TEXT,

    created_by UUID,
    validated_by UUID,
    validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_count_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_counts_tenant ON inventory_counts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_counts_status ON inventory_counts(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_counts_warehouse ON inventory_counts(tenant_id, warehouse_id);


-- ============================================================================
-- TABLE: LIGNES D'INVENTAIRE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_count_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    count_id UUID NOT NULL REFERENCES inventory_counts(id) ON DELETE CASCADE,

    product_id UUID NOT NULL REFERENCES inventory_products(id),
    location_id UUID REFERENCES inventory_locations(id),
    lot_id UUID REFERENCES inventory_lots(id),

    theoretical_quantity DECIMAL(15, 4) DEFAULT 0,
    counted_quantity DECIMAL(15, 4),
    discrepancy DECIMAL(15, 4),

    unit_cost DECIMAL(15, 4),
    discrepancy_value DECIMAL(15, 2),

    counted_at TIMESTAMP,
    counted_by UUID,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_count_lines_count ON inventory_count_lines(count_id);
CREATE INDEX IF NOT EXISTS idx_count_lines_tenant ON inventory_count_lines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_count_lines_product ON inventory_count_lines(tenant_id, product_id);


-- ============================================================================
-- TABLE: PRÉPARATIONS (PICKING)
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_pickings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    type movement_type DEFAULT 'OUT',
    status picking_status DEFAULT 'PENDING',

    warehouse_id UUID NOT NULL REFERENCES inventory_warehouses(id),

    reference_type VARCHAR(50),
    reference_id UUID,
    reference_number VARCHAR(100),

    scheduled_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    assigned_to UUID,

    total_lines INTEGER DEFAULT 0,
    picked_lines INTEGER DEFAULT 0,

    priority VARCHAR(20) DEFAULT 'NORMAL',
    notes TEXT,

    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_picking_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_pickings_tenant ON inventory_pickings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pickings_status ON inventory_pickings(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_pickings_assigned ON inventory_pickings(tenant_id, assigned_to);
CREATE INDEX IF NOT EXISTS idx_pickings_reference ON inventory_pickings(tenant_id, reference_type, reference_id);


-- ============================================================================
-- TABLE: LIGNES DE PRÉPARATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_picking_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    picking_id UUID NOT NULL REFERENCES inventory_pickings(id) ON DELETE CASCADE,

    product_id UUID NOT NULL REFERENCES inventory_products(id),
    location_id UUID REFERENCES inventory_locations(id),

    quantity_demanded DECIMAL(15, 4) NOT NULL,
    quantity_picked DECIMAL(15, 4) DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'UNIT',

    lot_id UUID REFERENCES inventory_lots(id),
    serial_id UUID REFERENCES inventory_serial_numbers(id),

    is_picked BOOLEAN DEFAULT FALSE,
    picked_at TIMESTAMP,
    picked_by UUID,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_picking_lines_picking ON inventory_picking_lines(picking_id);
CREATE INDEX IF NOT EXISTS idx_picking_lines_tenant ON inventory_picking_lines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_picking_lines_product ON inventory_picking_lines(tenant_id, product_id);


-- ============================================================================
-- TABLE: RÈGLES DE RÉAPPROVISIONNEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_replenishment_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    product_id UUID NOT NULL REFERENCES inventory_products(id) ON DELETE CASCADE,
    warehouse_id UUID REFERENCES inventory_warehouses(id),

    min_stock DECIMAL(15, 4) NOT NULL,
    max_stock DECIMAL(15, 4),
    reorder_point DECIMAL(15, 4) NOT NULL,
    reorder_quantity DECIMAL(15, 4) NOT NULL,

    supplier_id UUID,
    lead_time_days INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_replenishment_rule UNIQUE (tenant_id, product_id, warehouse_id)
);

CREATE INDEX IF NOT EXISTS idx_replenishment_tenant ON inventory_replenishment_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_replenishment_product ON inventory_replenishment_rules(tenant_id, product_id);


-- ============================================================================
-- TABLE: VALORISATION DES STOCKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    valuation_date DATE NOT NULL,
    warehouse_id UUID REFERENCES inventory_warehouses(id),

    total_products INTEGER DEFAULT 0,
    total_quantity DECIMAL(15, 4) DEFAULT 0,
    total_value DECIMAL(15, 2) DEFAULT 0,

    value_fifo DECIMAL(15, 2) DEFAULT 0,
    value_lifo DECIMAL(15, 2) DEFAULT 0,
    value_avg DECIMAL(15, 2) DEFAULT 0,
    value_standard DECIMAL(15, 2) DEFAULT 0,

    details JSONB DEFAULT '[]',

    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_valuations_tenant ON inventory_valuations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_valuations_date ON inventory_valuations(tenant_id, valuation_date);
CREATE INDEX IF NOT EXISTS idx_valuations_warehouse ON inventory_valuations(tenant_id, warehouse_id);


-- ============================================================================
-- TRIGGERS: updated_at automatique
-- ============================================================================

CREATE OR REPLACE FUNCTION update_inventory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'inventory_categories',
        'inventory_warehouses',
        'inventory_locations',
        'inventory_products',
        'inventory_stock_levels',
        'inventory_lots',
        'inventory_serial_numbers',
        'inventory_movements',
        'inventory_counts',
        'inventory_pickings',
        'inventory_replenishment_rules'
    ]
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trigger_update_%s_updated_at ON %s;
            CREATE TRIGGER trigger_update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW EXECUTE FUNCTION update_inventory_updated_at();
        ', t, t, t, t);
    END LOOP;
END $$;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE inventory_categories IS 'Catégories de produits - Module M5 Stock';
COMMENT ON TABLE inventory_warehouses IS 'Entrepôts de stockage';
COMMENT ON TABLE inventory_locations IS 'Emplacements de stockage dans les entrepôts';
COMMENT ON TABLE inventory_products IS 'Catalogue des produits/articles';
COMMENT ON TABLE inventory_stock_levels IS 'Niveaux de stock par produit/emplacement';
COMMENT ON TABLE inventory_lots IS 'Lots de produits avec suivi DLUO/DLC';
COMMENT ON TABLE inventory_serial_numbers IS 'Numéros de série des produits';
COMMENT ON TABLE inventory_movements IS 'Mouvements de stock (entrées/sorties/transferts)';
COMMENT ON TABLE inventory_movement_lines IS 'Lignes de mouvement de stock';
COMMENT ON TABLE inventory_counts IS 'Inventaires physiques';
COMMENT ON TABLE inventory_count_lines IS 'Lignes d''inventaire physique';
COMMENT ON TABLE inventory_pickings IS 'Préparations de commandes';
COMMENT ON TABLE inventory_picking_lines IS 'Lignes de préparation';
COMMENT ON TABLE inventory_replenishment_rules IS 'Règles de réapprovisionnement automatique';
COMMENT ON TABLE inventory_valuations IS 'Valorisation périodique des stocks';


-- ============================================================================
-- FIN DE LA MIGRATION M5 - STOCK
-- ============================================================================
