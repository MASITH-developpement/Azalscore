-- ============================================================================
-- AZALS MODULE M1 - COMMERCIAL (CRM + VENTES)
-- Migration: 016_commercial_module.sql
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE customer_type AS ENUM (
    'PROSPECT',
    'LEAD',
    'CUSTOMER',
    'VIP',
    'PARTNER',
    'CHURNED'
);

CREATE TYPE opportunity_status AS ENUM (
    'NEW',
    'QUALIFIED',
    'PROPOSAL',
    'NEGOTIATION',
    'WON',
    'LOST'
);

CREATE TYPE document_type AS ENUM (
    'QUOTE',
    'ORDER',
    'INVOICE',
    'CREDIT_NOTE',
    'PROFORMA',
    'DELIVERY'
);

CREATE TYPE document_status AS ENUM (
    'DRAFT',
    'PENDING',
    'VALIDATED',
    'SENT',
    'ACCEPTED',
    'REJECTED',
    'DELIVERED',
    'INVOICED',
    'PAID',
    'CANCELLED'
);

CREATE TYPE payment_method AS ENUM (
    'BANK_TRANSFER',
    'CHECK',
    'CREDIT_CARD',
    'CASH',
    'DIRECT_DEBIT',
    'PAYPAL',
    'OTHER'
);

CREATE TYPE payment_terms AS ENUM (
    'IMMEDIATE',
    'NET_15',
    'NET_30',
    'NET_45',
    'NET_60',
    'NET_90',
    'END_OF_MONTH',
    'CUSTOM'
);

CREATE TYPE activity_type AS ENUM (
    'CALL',
    'EMAIL',
    'MEETING',
    'TASK',
    'NOTE',
    'FOLLOW_UP'
);

-- ============================================================================
-- TABLE: CLIENTS
-- ============================================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    type customer_type DEFAULT 'PROSPECT',

    -- Contact
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    website VARCHAR(255),

    -- Adresse
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    state VARCHAR(100),
    country_code VARCHAR(3) DEFAULT 'FR',

    -- Légal
    tax_id VARCHAR(50),
    registration_number VARCHAR(50),
    legal_form VARCHAR(50),

    -- Commercial
    assigned_to UUID,
    industry VARCHAR(100),
    size VARCHAR(50),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,

    -- Conditions
    payment_terms payment_terms DEFAULT 'NET_30',
    payment_method payment_method,
    credit_limit DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    discount_rate FLOAT DEFAULT 0.0,

    -- Classification
    tags JSONB DEFAULT '[]',
    segment VARCHAR(50),
    source VARCHAR(100),

    -- Scoring
    lead_score INTEGER DEFAULT 0,
    health_score INTEGER DEFAULT 100,

    -- Statistiques
    total_revenue DECIMAL(15,2) DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    last_order_date DATE,
    first_order_date DATE,

    -- Notes
    notes TEXT,
    internal_notes TEXT,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tenant_id, code)
);

CREATE INDEX ix_customers_tenant_code ON customers(tenant_id, code);
CREATE INDEX ix_customers_tenant_type ON customers(tenant_id, type);
CREATE INDEX ix_customers_tenant_assigned ON customers(tenant_id, assigned_to);
CREATE INDEX ix_customers_tenant_active ON customers(tenant_id, is_active);

-- ============================================================================
-- TABLE: CONTACTS
-- ============================================================================

CREATE TABLE customer_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- Identité
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    title VARCHAR(50),
    job_title VARCHAR(100),
    department VARCHAR(100),

    -- Coordonnées
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    linkedin VARCHAR(255),

    -- Rôle
    is_primary BOOLEAN DEFAULT FALSE,
    is_billing BOOLEAN DEFAULT FALSE,
    is_shipping BOOLEAN DEFAULT FALSE,
    is_decision_maker BOOLEAN DEFAULT FALSE,

    -- Préférences
    preferred_language VARCHAR(5) DEFAULT 'fr',
    preferred_contact_method VARCHAR(20),
    do_not_call BOOLEAN DEFAULT FALSE,
    do_not_email BOOLEAN DEFAULT FALSE,

    -- Notes
    notes TEXT,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_contacts_tenant_customer ON customer_contacts(tenant_id, customer_id);
CREATE INDEX ix_contacts_tenant_email ON customer_contacts(tenant_id, email);

-- ============================================================================
-- TABLE: OPPORTUNITÉS
-- ============================================================================

CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Pipeline
    status opportunity_status DEFAULT 'NEW',
    stage VARCHAR(50),
    probability INTEGER DEFAULT 10,

    -- Montants
    amount DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',
    weighted_amount DECIMAL(15,2),

    -- Dates
    expected_close_date DATE,
    actual_close_date DATE,

    -- Attribution
    assigned_to UUID,
    team VARCHAR(100),

    -- Source
    source VARCHAR(100),
    campaign VARCHAR(100),

    -- Concurrence
    competitors JSONB DEFAULT '[]',
    win_reason VARCHAR(255),
    loss_reason VARCHAR(255),

    -- Produits
    products JSONB DEFAULT '[]',

    -- Notes
    notes TEXT,
    next_steps TEXT,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tenant_id, code)
);

CREATE INDEX ix_opportunities_tenant_code ON opportunities(tenant_id, code);
CREATE INDEX ix_opportunities_tenant_status ON opportunities(tenant_id, status);
CREATE INDEX ix_opportunities_tenant_customer ON opportunities(tenant_id, customer_id);
CREATE INDEX ix_opportunities_tenant_assigned ON opportunities(tenant_id, assigned_to);
CREATE INDEX ix_opportunities_tenant_close ON opportunities(tenant_id, expected_close_date);

-- ============================================================================
-- TABLE: DOCUMENTS COMMERCIAUX
-- ============================================================================

CREATE TABLE commercial_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    opportunity_id UUID REFERENCES opportunities(id),

    -- Identification
    type document_type NOT NULL,
    number VARCHAR(50) NOT NULL,
    reference VARCHAR(100),
    status document_status DEFAULT 'DRAFT',

    -- Dates
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE,
    validity_date DATE,
    delivery_date DATE,

    -- Adresses
    billing_address JSONB,
    shipping_address JSONB,

    -- Montants
    subtotal DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    discount_percent FLOAT DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Paiement
    payment_terms payment_terms,
    payment_method payment_method,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    remaining_amount DECIMAL(15,2),

    -- Livraison
    shipping_method VARCHAR(100),
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    tracking_number VARCHAR(100),

    -- Notes
    notes TEXT,
    internal_notes TEXT,
    terms TEXT,

    -- Liens
    parent_id UUID,
    invoice_id UUID,

    -- PDF
    pdf_url VARCHAR(500),

    -- Attribution
    assigned_to UUID,
    validated_by UUID,
    validated_at TIMESTAMP,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tenant_id, type, number)
);

CREATE INDEX ix_documents_tenant_number ON commercial_documents(tenant_id, type, number);
CREATE INDEX ix_documents_tenant_customer ON commercial_documents(tenant_id, customer_id);
CREATE INDEX ix_documents_tenant_type ON commercial_documents(tenant_id, type);
CREATE INDEX ix_documents_tenant_status ON commercial_documents(tenant_id, status);
CREATE INDEX ix_documents_tenant_date ON commercial_documents(tenant_id, date);

-- ============================================================================
-- TABLE: LIGNES DE DOCUMENT
-- ============================================================================

CREATE TABLE document_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL REFERENCES commercial_documents(id) ON DELETE CASCADE,

    -- Position
    line_number INTEGER NOT NULL,

    -- Produit
    product_id UUID,
    product_code VARCHAR(50),
    description TEXT NOT NULL,

    -- Quantités
    quantity DECIMAL(10,3) DEFAULT 1,
    unit VARCHAR(20),

    -- Prix
    unit_price DECIMAL(15,4) DEFAULT 0,
    discount_percent FLOAT DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    subtotal DECIMAL(15,2) DEFAULT 0,

    -- TVA
    tax_rate FLOAT DEFAULT 20.0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,

    -- Notes
    notes TEXT,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_doc_lines_tenant_document ON document_lines(tenant_id, document_id);

-- ============================================================================
-- TABLE: PAIEMENTS
-- ============================================================================

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL REFERENCES commercial_documents(id),

    -- Identification
    reference VARCHAR(100),
    method payment_method NOT NULL,

    -- Montant
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Dates
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    received_date DATE,

    -- Banque
    bank_account VARCHAR(100),
    transaction_id VARCHAR(100),

    -- Notes
    notes TEXT,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_payments_tenant_document ON payments(tenant_id, document_id);
CREATE INDEX ix_payments_tenant_date ON payments(tenant_id, date);

-- ============================================================================
-- TABLE: ACTIVITÉS CRM
-- ============================================================================

CREATE TABLE customer_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    opportunity_id UUID REFERENCES opportunities(id),
    contact_id UUID REFERENCES customer_contacts(id),

    -- Type et sujet
    type activity_type NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,

    -- Dates
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    completed_at TIMESTAMP,

    -- Durée
    duration_minutes INTEGER,

    -- Statut
    is_completed BOOLEAN DEFAULT FALSE,

    -- Attribution
    assigned_to UUID,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_activities_tenant_customer ON customer_activities(tenant_id, customer_id);
CREATE INDEX ix_activities_tenant_opportunity ON customer_activities(tenant_id, opportunity_id);
CREATE INDEX ix_activities_tenant_date ON customer_activities(tenant_id, date);
CREATE INDEX ix_activities_tenant_assigned ON customer_activities(tenant_id, assigned_to);

-- ============================================================================
-- TABLE: ÉTAPES DU PIPELINE
-- ============================================================================

CREATE TABLE pipeline_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50),
    description TEXT,

    -- Position et probabilité
    "order" INTEGER NOT NULL,
    probability INTEGER DEFAULT 50,

    -- Couleur
    color VARCHAR(20) DEFAULT '#3B82F6',

    -- Type
    is_won BOOLEAN DEFAULT FALSE,
    is_lost BOOLEAN DEFAULT FALSE,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_pipeline_tenant_order ON pipeline_stages(tenant_id, "order");

-- ============================================================================
-- TABLE: PRODUITS/SERVICES (CATALOGUE)
-- ============================================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Type
    is_service BOOLEAN DEFAULT FALSE,

    -- Prix
    unit_price DECIMAL(15,4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',
    unit VARCHAR(20) DEFAULT 'pce',

    -- TVA
    tax_rate FLOAT DEFAULT 20.0,

    -- Stock
    track_stock BOOLEAN DEFAULT FALSE,
    stock_quantity DECIMAL(10,3) DEFAULT 0,
    min_stock DECIMAL(10,3) DEFAULT 0,

    -- Images
    image_url VARCHAR(500),
    gallery JSONB DEFAULT '[]',

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tenant_id, code)
);

CREATE INDEX ix_products_tenant_code ON products(tenant_id, code);
CREATE INDEX ix_products_tenant_category ON products(tenant_id, category);
CREATE INDEX ix_products_tenant_active ON products(tenant_id, is_active);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour customers
CREATE OR REPLACE FUNCTION update_customers_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- Trigger updated_at pour contacts
CREATE TRIGGER trigger_contacts_updated_at
    BEFORE UPDATE ON customer_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- Trigger updated_at pour opportunities
CREATE TRIGGER trigger_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- Trigger updated_at pour commercial_documents
CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON commercial_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- Trigger updated_at pour pipeline_stages
CREATE TRIGGER trigger_pipeline_updated_at
    BEFORE UPDATE ON pipeline_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- Trigger updated_at pour products
CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_customers_timestamp();

-- ============================================================================
-- DONNÉES INITIALES - ÉTAPES PIPELINE PAR DÉFAUT
-- ============================================================================

-- Les étapes du pipeline seront créées par tenant lors de l'activation du module

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE customers IS 'Clients et prospects - Module M1 Commercial';
COMMENT ON TABLE customer_contacts IS 'Contacts associés aux clients';
COMMENT ON TABLE opportunities IS 'Opportunités commerciales (Pipeline)';
COMMENT ON TABLE commercial_documents IS 'Documents commerciaux (Devis, Commandes, Factures)';
COMMENT ON TABLE document_lines IS 'Lignes de documents commerciaux';
COMMENT ON TABLE payments IS 'Paiements reçus sur factures';
COMMENT ON TABLE customer_activities IS 'Activités CRM (Appels, Emails, Réunions)';
COMMENT ON TABLE pipeline_stages IS 'Étapes du pipeline de vente';
COMMENT ON TABLE products IS 'Catalogue produits et services';
