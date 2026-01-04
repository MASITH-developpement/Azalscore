-- ============================================================================
-- AZALS MODULE M4 - ACHATS (PROCUREMENT)
-- Migration SQL pour PostgreSQL
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Statut fournisseur
DO $$ BEGIN
    CREATE TYPE supplier_status AS ENUM (
        'PROSPECT', 'PENDING', 'APPROVED', 'BLOCKED', 'INACTIVE'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Type de fournisseur
DO $$ BEGIN
    CREATE TYPE supplier_type AS ENUM (
        'MANUFACTURER', 'DISTRIBUTOR', 'SERVICE', 'FREELANCE', 'OTHER'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Statut demande d'achat
DO $$ BEGIN
    CREATE TYPE requisition_status AS ENUM (
        'DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'ORDERED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Statut commande d'achat
DO $$ BEGIN
    CREATE TYPE purchase_order_status AS ENUM (
        'DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL', 'RECEIVED', 'INVOICED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Statut réception
DO $$ BEGIN
    CREATE TYPE receiving_status AS ENUM (
        'DRAFT', 'VALIDATED', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Statut facture d'achat
DO $$ BEGIN
    CREATE TYPE purchase_invoice_status AS ENUM (
        'DRAFT', 'VALIDATED', 'PAID', 'PARTIAL', 'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Statut devis fournisseur
DO $$ BEGIN
    CREATE TYPE quotation_status AS ENUM (
        'REQUESTED', 'RECEIVED', 'ACCEPTED', 'REJECTED', 'EXPIRED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================================
-- TABLE: FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    type supplier_type DEFAULT 'OTHER',
    status supplier_status DEFAULT 'PROSPECT',

    -- Identification légale
    tax_id VARCHAR(50),
    vat_number VARCHAR(50),
    registration_number VARCHAR(100),

    -- Contact principal
    email VARCHAR(255),
    phone VARCHAR(50),
    fax VARCHAR(50),
    website VARCHAR(255),

    -- Adresse
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'France',

    -- Conditions commerciales
    payment_terms VARCHAR(50) DEFAULT 'NET30',
    currency VARCHAR(3) DEFAULT 'EUR',
    credit_limit DECIMAL(15, 2),
    discount_rate DECIMAL(5, 2) DEFAULT 0,

    -- Banque
    bank_name VARCHAR(255),
    iban VARCHAR(50),
    bic VARCHAR(20),

    -- Catégorie
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',

    -- Évaluation
    rating DECIMAL(3, 2),
    last_evaluation_date DATE,

    -- Comptabilité
    account_id UUID,

    -- Métadonnées
    notes TEXT,
    custom_fields JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_supplier_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_suppliers_tenant ON procurement_suppliers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_status ON procurement_suppliers(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_suppliers_category ON procurement_suppliers(tenant_id, category);


-- ============================================================================
-- TABLE: CONTACTS FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_supplier_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id) ON DELETE CASCADE,

    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    department VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_supplier_contacts_tenant ON procurement_supplier_contacts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_supplier ON procurement_supplier_contacts(tenant_id, supplier_id);


-- ============================================================================
-- TABLE: DEMANDES D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_requisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    status requisition_status DEFAULT 'DRAFT',
    priority VARCHAR(20) DEFAULT 'NORMAL',

    title VARCHAR(255) NOT NULL,
    description TEXT,
    justification TEXT,

    requester_id UUID NOT NULL,
    department_id UUID,

    requested_date DATE NOT NULL,
    required_date DATE,

    estimated_total DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',
    budget_code VARCHAR(50),

    -- Approbation
    approved_by UUID,
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    notes TEXT,
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_requisition_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_requisitions_tenant ON procurement_requisitions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_requisitions_status ON procurement_requisitions(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_requisitions_requester ON procurement_requisitions(tenant_id, requester_id);


-- ============================================================================
-- TABLE: LIGNES DE DEMANDE D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_requisition_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    requisition_id UUID NOT NULL REFERENCES procurement_requisitions(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    product_id UUID,
    product_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',
    estimated_price DECIMAL(15, 2),
    total DECIMAL(15, 2),

    preferred_supplier_id UUID REFERENCES procurement_suppliers(id),
    required_date DATE,
    notes TEXT,

    -- Lien vers commande
    ordered_quantity DECIMAL(15, 4) DEFAULT 0,
    purchase_order_id UUID,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_requisition_lines_requisition ON procurement_requisition_lines(requisition_id);
CREATE INDEX IF NOT EXISTS idx_requisition_lines_tenant ON procurement_requisition_lines(tenant_id);


-- ============================================================================
-- TABLE: DEVIS FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_quotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),
    requisition_id UUID REFERENCES procurement_requisitions(id),

    status quotation_status DEFAULT 'REQUESTED',

    request_date DATE NOT NULL,
    response_date DATE,
    expiry_date DATE,

    currency VARCHAR(3) DEFAULT 'EUR',
    subtotal DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    total DECIMAL(15, 2) DEFAULT 0,

    payment_terms VARCHAR(50),
    delivery_terms VARCHAR(255),
    delivery_date DATE,

    reference VARCHAR(100),
    notes TEXT,
    attachments JSONB DEFAULT '[]',

    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_quotation_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_quotations_tenant ON procurement_quotations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quotations_supplier ON procurement_quotations(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_quotations_status ON procurement_quotations(tenant_id, status);


-- ============================================================================
-- TABLE: LIGNES DE DEVIS FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_quotation_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    quotation_id UUID NOT NULL REFERENCES procurement_quotations(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    product_id UUID,
    product_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',
    unit_price DECIMAL(15, 4) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 20,
    total DECIMAL(15, 2) NOT NULL,

    lead_time INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quotation_lines_quotation ON procurement_quotation_lines(quotation_id);
CREATE INDEX IF NOT EXISTS idx_quotation_lines_tenant ON procurement_quotation_lines(tenant_id);


-- ============================================================================
-- TABLE: COMMANDES D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),
    requisition_id UUID REFERENCES procurement_requisitions(id),
    quotation_id UUID REFERENCES procurement_quotations(id),

    status purchase_order_status DEFAULT 'DRAFT',

    order_date DATE NOT NULL,
    expected_date DATE,
    confirmed_date DATE,

    -- Adresse de livraison
    delivery_address TEXT,
    delivery_contact VARCHAR(255),

    -- Montants
    currency VARCHAR(3) DEFAULT 'EUR',
    subtotal DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    shipping_cost DECIMAL(15, 2) DEFAULT 0,
    total DECIMAL(15, 2) DEFAULT 0,

    -- Conditions
    payment_terms VARCHAR(50),
    incoterms VARCHAR(20),

    -- Réception
    received_amount DECIMAL(15, 2) DEFAULT 0,
    invoiced_amount DECIMAL(15, 2) DEFAULT 0,

    -- Références
    supplier_reference VARCHAR(100),

    notes TEXT,
    internal_notes TEXT,
    attachments JSONB DEFAULT '[]',

    created_by UUID,
    sent_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_order_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant ON procurement_orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_supplier ON procurement_orders(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON procurement_orders(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON procurement_orders(tenant_id, order_date);


-- ============================================================================
-- TABLE: LIGNES DE COMMANDES D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_order_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    order_id UUID NOT NULL REFERENCES procurement_orders(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    product_id UUID,
    product_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,

    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',
    unit_price DECIMAL(15, 4) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 20,
    total DECIMAL(15, 2) NOT NULL,

    expected_date DATE,
    received_quantity DECIMAL(15, 4) DEFAULT 0,
    invoiced_quantity DECIMAL(15, 4) DEFAULT 0,

    -- Lien requisition
    requisition_line_id UUID,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_lines_order ON procurement_order_lines(order_id);
CREATE INDEX IF NOT EXISTS idx_order_lines_tenant ON procurement_order_lines(tenant_id);
CREATE INDEX IF NOT EXISTS idx_order_lines_product ON procurement_order_lines(tenant_id, product_id);


-- ============================================================================
-- TABLE: RÉCEPTIONS DE MARCHANDISES
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    order_id UUID NOT NULL REFERENCES procurement_orders(id),
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),

    status receiving_status DEFAULT 'DRAFT',

    receipt_date DATE NOT NULL,
    delivery_note VARCHAR(100),
    carrier VARCHAR(255),
    tracking_number VARCHAR(100),

    warehouse_id UUID,
    location VARCHAR(100),

    notes TEXT,
    attachments JSONB DEFAULT '[]',

    received_by UUID,
    validated_by UUID,
    validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_receipt_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant ON procurement_receipts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_receipts_order ON procurement_receipts(tenant_id, order_id);
CREATE INDEX IF NOT EXISTS idx_receipts_supplier ON procurement_receipts(tenant_id, supplier_id);


-- ============================================================================
-- TABLE: LIGNES DE RÉCEPTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_receipt_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    receipt_id UUID NOT NULL REFERENCES procurement_receipts(id) ON DELETE CASCADE,
    order_line_id UUID NOT NULL REFERENCES procurement_order_lines(id),

    line_number INTEGER NOT NULL,
    product_id UUID,
    product_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,

    ordered_quantity DECIMAL(15, 4) NOT NULL,
    received_quantity DECIMAL(15, 4) NOT NULL,
    rejected_quantity DECIMAL(15, 4) DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'UNIT',

    rejection_reason TEXT,
    lot_number VARCHAR(100),
    serial_numbers JSONB DEFAULT '[]',
    expiry_date DATE,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_receipt_lines_receipt ON procurement_receipt_lines(receipt_id);
CREATE INDEX IF NOT EXISTS idx_receipt_lines_tenant ON procurement_receipt_lines(tenant_id);


-- ============================================================================
-- TABLE: FACTURES D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),
    order_id UUID REFERENCES procurement_orders(id),

    status purchase_invoice_status DEFAULT 'DRAFT',

    invoice_date DATE NOT NULL,
    due_date DATE,
    supplier_invoice_number VARCHAR(100),
    supplier_invoice_date DATE,

    currency VARCHAR(3) DEFAULT 'EUR',
    subtotal DECIMAL(15, 2) DEFAULT 0,
    discount_amount DECIMAL(15, 2) DEFAULT 0,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    total DECIMAL(15, 2) DEFAULT 0,

    paid_amount DECIMAL(15, 2) DEFAULT 0,
    remaining_amount DECIMAL(15, 2) DEFAULT 0,

    payment_terms VARCHAR(50),
    payment_method VARCHAR(50),

    -- Comptabilité
    journal_entry_id UUID,
    posted_at TIMESTAMP,

    notes TEXT,
    attachments JSONB DEFAULT '[]',

    validated_by UUID,
    validated_at TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_purchase_invoice_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_purchase_invoices_tenant ON procurement_invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_purchase_invoices_supplier ON procurement_invoices(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_invoices_status ON procurement_invoices(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_purchase_invoices_due ON procurement_invoices(tenant_id, due_date);


-- ============================================================================
-- TABLE: LIGNES DE FACTURES D'ACHAT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_invoice_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    invoice_id UUID NOT NULL REFERENCES procurement_invoices(id) ON DELETE CASCADE,
    order_line_id UUID REFERENCES procurement_order_lines(id),

    line_number INTEGER NOT NULL,
    product_id UUID,
    product_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,

    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) DEFAULT 'UNIT',
    unit_price DECIMAL(15, 4) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 20,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    total DECIMAL(15, 2) NOT NULL,

    account_id UUID,
    analytic_code VARCHAR(50),

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice ON procurement_invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_tenant ON procurement_invoice_lines(tenant_id);


-- ============================================================================
-- TABLE: PAIEMENTS FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    number VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),

    payment_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    payment_method VARCHAR(50) NOT NULL,
    reference VARCHAR(100),

    bank_account_id UUID,

    -- Comptabilité
    journal_entry_id UUID,

    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_payment_number UNIQUE (tenant_id, number)
);

CREATE INDEX IF NOT EXISTS idx_payments_tenant ON procurement_payments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payments_supplier ON procurement_payments(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON procurement_payments(tenant_id, payment_date);


-- ============================================================================
-- TABLE: AFFECTATIONS DE PAIEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    payment_id UUID NOT NULL REFERENCES procurement_payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES procurement_invoices(id),

    amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_allocations_payment ON procurement_payment_allocations(payment_id);
CREATE INDEX IF NOT EXISTS idx_allocations_invoice ON procurement_payment_allocations(invoice_id);
CREATE INDEX IF NOT EXISTS idx_allocations_tenant ON procurement_payment_allocations(tenant_id);


-- ============================================================================
-- TABLE: ÉVALUATIONS FOURNISSEURS
-- ============================================================================

CREATE TABLE IF NOT EXISTS procurement_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    supplier_id UUID NOT NULL REFERENCES procurement_suppliers(id),

    evaluation_date DATE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Scores par critère (0-5)
    quality_score DECIMAL(3, 2),
    price_score DECIMAL(3, 2),
    delivery_score DECIMAL(3, 2),
    service_score DECIMAL(3, 2),
    reliability_score DECIMAL(3, 2),

    overall_score DECIMAL(3, 2),

    -- Statistiques
    total_orders INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    on_time_delivery_rate DECIMAL(5, 2),
    quality_rejection_rate DECIMAL(5, 2),

    comments TEXT,
    recommendations TEXT,

    evaluated_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluations_tenant ON procurement_evaluations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_supplier ON procurement_evaluations(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_date ON procurement_evaluations(tenant_id, evaluation_date);


-- ============================================================================
-- TRIGGERS: updated_at automatique
-- ============================================================================

-- Fonction de mise à jour timestamp
CREATE OR REPLACE FUNCTION update_procurement_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour chaque table avec updated_at
DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'procurement_suppliers',
        'procurement_supplier_contacts',
        'procurement_requisitions',
        'procurement_quotations',
        'procurement_orders',
        'procurement_receipts',
        'procurement_invoices'
    ]
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trigger_update_%s_updated_at ON %s;
            CREATE TRIGGER trigger_update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW EXECUTE FUNCTION update_procurement_updated_at();
        ', t, t, t, t);
    END LOOP;
END $$;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE procurement_suppliers IS 'Fournisseurs - Module M4 Achats';
COMMENT ON TABLE procurement_supplier_contacts IS 'Contacts des fournisseurs';
COMMENT ON TABLE procurement_requisitions IS 'Demandes d''achat internes';
COMMENT ON TABLE procurement_requisition_lines IS 'Lignes de demandes d''achat';
COMMENT ON TABLE procurement_quotations IS 'Devis reçus des fournisseurs';
COMMENT ON TABLE procurement_quotation_lines IS 'Lignes de devis fournisseurs';
COMMENT ON TABLE procurement_orders IS 'Commandes d''achat envoyées aux fournisseurs';
COMMENT ON TABLE procurement_order_lines IS 'Lignes de commandes d''achat';
COMMENT ON TABLE procurement_receipts IS 'Réceptions de marchandises';
COMMENT ON TABLE procurement_receipt_lines IS 'Lignes de réception';
COMMENT ON TABLE procurement_invoices IS 'Factures d''achat reçues';
COMMENT ON TABLE procurement_invoice_lines IS 'Lignes de factures d''achat';
COMMENT ON TABLE procurement_payments IS 'Paiements aux fournisseurs';
COMMENT ON TABLE procurement_payment_allocations IS 'Affectation des paiements aux factures';
COMMENT ON TABLE procurement_evaluations IS 'Évaluations périodiques des fournisseurs';


-- ============================================================================
-- FIN DE LA MIGRATION M4 - ACHATS
-- ============================================================================
