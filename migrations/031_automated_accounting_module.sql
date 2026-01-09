-- ============================================================================
-- AZALS MODULE M2A - Comptabilité Automatisée
-- Migration 031 - Tables pour l'automatisation comptable
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Type de document source
CREATE TYPE document_type AS ENUM (
    'INVOICE_RECEIVED',      -- Facture fournisseur reçue
    'INVOICE_SENT',          -- Facture client émise
    'EXPENSE_NOTE',          -- Note de frais
    'CREDIT_NOTE_RECEIVED',  -- Avoir fournisseur
    'CREDIT_NOTE_SENT',      -- Avoir client
    'QUOTE',                 -- Devis
    'PURCHASE_ORDER',        -- Bon de commande
    'DELIVERY_NOTE',         -- Bon de livraison
    'BANK_STATEMENT',        -- Relevé bancaire
    'OTHER'                  -- Autre document
);

-- Statut de document
CREATE TYPE document_status AS ENUM (
    'RECEIVED',              -- Reçu, non traité
    'PROCESSING',            -- En cours de traitement OCR/IA
    'ANALYZED',              -- Analysé par IA
    'PENDING_VALIDATION',    -- En attente validation expert
    'VALIDATED',             -- Validé
    'ACCOUNTED',             -- Comptabilisé
    'REJECTED',              -- Rejeté
    'ERROR'                  -- Erreur de traitement
);

-- Source d'entrée du document
CREATE TYPE document_source AS ENUM (
    'EMAIL',                 -- Reçu par email
    'UPLOAD',                -- Upload manuel
    'MOBILE_SCAN',           -- Scan mobile
    'API',                   -- API fournisseur/client
    'BANK_SYNC',             -- Synchronisation bancaire
    'INTERNAL'               -- Généré en interne
);

-- Niveau de confiance IA
CREATE TYPE confidence_level AS ENUM (
    'HIGH',                  -- > 95% - Pas de validation nécessaire
    'MEDIUM',                -- 80-95% - Validation optionnelle
    'LOW',                   -- 60-80% - Validation requise
    'VERY_LOW'               -- < 60% - Révision manuelle nécessaire
);

-- Statut de connexion bancaire
CREATE TYPE bank_connection_status AS ENUM (
    'ACTIVE',                -- Connexion active
    'EXPIRED',               -- Token expiré
    'REQUIRES_ACTION',       -- Action utilisateur requise
    'ERROR',                 -- Erreur de connexion
    'DISCONNECTED'           -- Déconnecté
);

-- Statut de paiement
CREATE TYPE payment_status AS ENUM (
    'UNPAID',                -- Non payé
    'PARTIALLY_PAID',        -- Partiellement payé
    'PAID',                  -- Payé intégralement
    'OVERPAID',              -- Trop-perçu
    'CANCELLED'              -- Annulé
);

-- Type d'alerte
CREATE TYPE alert_type AS ENUM (
    'DOCUMENT_UNREADABLE',   -- Document illisible
    'MISSING_INFO',          -- Information manquante
    'LOW_CONFIDENCE',        -- Confiance IA faible
    'DUPLICATE_SUSPECTED',   -- Doublon suspecté
    'AMOUNT_MISMATCH',       -- Montant incohérent
    'TAX_ERROR',             -- Erreur de TVA
    'OVERDUE_PAYMENT',       -- Paiement en retard
    'CASH_FLOW_WARNING',     -- Alerte trésorerie
    'RECONCILIATION_ISSUE'   -- Problème de rapprochement
);

-- ============================================================================
-- TABLE: Documents Source (Pièces comptables)
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Type et source
    document_type document_type NOT NULL,
    source document_source NOT NULL,
    status document_status NOT NULL DEFAULT 'RECEIVED',

    -- Identification
    reference VARCHAR(100),                    -- Numéro de facture/document
    external_id VARCHAR(255),                  -- ID externe (API, email ID, etc.)

    -- Fichier original
    original_filename VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64),                     -- SHA-256 pour détection doublons

    -- Dates
    document_date DATE,                        -- Date du document
    due_date DATE,                             -- Date d'échéance
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Partenaire (fournisseur/client)
    partner_id UUID,                           -- Lien vers contacts
    partner_name VARCHAR(255),
    partner_tax_id VARCHAR(50),                -- SIRET, TVA intracommunautaire

    -- Montants (extraits par OCR/IA)
    amount_untaxed DECIMAL(15, 2),             -- HT
    amount_tax DECIMAL(15, 2),                 -- TVA
    amount_total DECIMAL(15, 2),               -- TTC
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Paiement
    payment_status payment_status DEFAULT 'UNPAID',
    amount_paid DECIMAL(15, 2) DEFAULT 0,
    amount_remaining DECIMAL(15, 2),

    -- OCR Data brutes
    ocr_raw_text TEXT,
    ocr_confidence DECIMAL(5, 2),              -- Score OCR global 0-100

    -- IA Classification
    ai_confidence confidence_level,
    ai_confidence_score DECIMAL(5, 2),         -- Score numérique 0-100
    ai_suggested_account VARCHAR(20),          -- Compte comptable suggéré
    ai_suggested_journal VARCHAR(20),          -- Journal suggéré
    ai_analysis JSONB,                         -- Analyse complète IA

    -- Écriture comptable générée
    journal_entry_id UUID REFERENCES journal_entries(id),

    -- Validation
    requires_validation BOOLEAN DEFAULT false,
    validated_by UUID,
    validated_at TIMESTAMP WITH TIME ZONE,
    validation_notes TEXT,

    -- Source email
    email_from VARCHAR(255),
    email_subject VARCHAR(500),
    email_received_at TIMESTAMP WITH TIME ZONE,

    -- Métadonnées
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    notes TEXT,

    -- Audit
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accounting_documents
CREATE INDEX idx_accounting_docs_tenant ON accounting_documents(tenant_id);
CREATE INDEX idx_accounting_docs_tenant_status ON accounting_documents(tenant_id, status);
CREATE INDEX idx_accounting_docs_tenant_type ON accounting_documents(tenant_id, document_type);
CREATE INDEX idx_accounting_docs_tenant_date ON accounting_documents(tenant_id, document_date);
CREATE INDEX idx_accounting_docs_tenant_partner ON accounting_documents(tenant_id, partner_id);
CREATE INDEX idx_accounting_docs_tenant_payment ON accounting_documents(tenant_id, payment_status);
CREATE INDEX idx_accounting_docs_file_hash ON accounting_documents(tenant_id, file_hash);
CREATE INDEX idx_accounting_docs_reference ON accounting_documents(tenant_id, reference);

-- ============================================================================
-- TABLE: Résultats OCR détaillés
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_ocr_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL REFERENCES accounting_documents(id) ON DELETE CASCADE,

    -- Moteur OCR utilisé
    ocr_engine VARCHAR(50) NOT NULL,           -- tesseract, aws_textract, azure_cognitive, google_vision
    ocr_version VARCHAR(20),

    -- Résultat global
    processing_time_ms INTEGER,
    overall_confidence DECIMAL(5, 2),

    -- Texte brut extrait
    raw_text TEXT,
    structured_data JSONB,                     -- Données structurées extraites

    -- Champs extraits avec confiance
    extracted_fields JSONB NOT NULL,           -- {field_name: {value, confidence, bounding_box}}

    -- Erreurs éventuelles
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',

    -- Métadonnées image
    image_quality_score DECIMAL(5, 2),
    image_resolution VARCHAR(20),
    page_count INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ocr_results_tenant_doc ON accounting_ocr_results(tenant_id, document_id);

-- ============================================================================
-- TABLE: Classifications IA
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_ai_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL REFERENCES accounting_documents(id) ON DELETE CASCADE,

    -- Modèle IA utilisé
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20),

    -- Classification document
    document_type_predicted document_type,
    document_type_confidence DECIMAL(5, 2),

    -- Extraction entités
    vendor_name VARCHAR(255),
    vendor_confidence DECIMAL(5, 2),

    invoice_number VARCHAR(100),
    invoice_number_confidence DECIMAL(5, 2),

    invoice_date DATE,
    invoice_date_confidence DECIMAL(5, 2),

    due_date DATE,
    due_date_confidence DECIMAL(5, 2),

    -- Montants
    amount_untaxed DECIMAL(15, 2),
    amount_untaxed_confidence DECIMAL(5, 2),

    amount_tax DECIMAL(15, 2),
    amount_tax_confidence DECIMAL(5, 2),

    amount_total DECIMAL(15, 2),
    amount_total_confidence DECIMAL(5, 2),

    -- Détail TVA
    tax_rates JSONB,                           -- [{rate: 20, amount: 100, confidence: 95}]

    -- Classification comptable
    suggested_account_code VARCHAR(20),
    suggested_account_confidence DECIMAL(5, 2),

    suggested_journal_code VARCHAR(20),
    suggested_journal_confidence DECIMAL(5, 2),

    -- Catégorisation
    expense_category VARCHAR(100),
    expense_category_confidence DECIMAL(5, 2),

    -- Confiance globale
    overall_confidence confidence_level NOT NULL,
    overall_confidence_score DECIMAL(5, 2) NOT NULL,

    -- Raisons de la classification
    classification_reasons JSONB,

    -- Apprentissage
    was_corrected BOOLEAN DEFAULT false,
    corrected_by UUID,
    corrected_at TIMESTAMP WITH TIME ZONE,
    correction_feedback TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_class_tenant_doc ON accounting_ai_classifications(tenant_id, document_id);
CREATE INDEX idx_ai_class_tenant_confidence ON accounting_ai_classifications(tenant_id, overall_confidence);

-- ============================================================================
-- TABLE: Écritures automatiques générées
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_auto_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    document_id UUID NOT NULL REFERENCES accounting_documents(id),

    -- Écriture générée
    journal_entry_id UUID REFERENCES journal_entries(id),

    -- Confiance IA
    confidence_level confidence_level NOT NULL,
    confidence_score DECIMAL(5, 2) NOT NULL,

    -- Schéma d'écriture appliqué
    entry_template VARCHAR(100),               -- template utilisé
    accounting_rules_applied JSONB,            -- règles appliquées

    -- Lignes proposées (avant création effective)
    proposed_lines JSONB NOT NULL,             -- [{account_code, debit, credit, label}]

    -- Validation
    auto_validated BOOLEAN DEFAULT false,      -- Validé automatiquement (haute confiance)
    requires_review BOOLEAN DEFAULT true,
    reviewed_by UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Modifications
    was_modified BOOLEAN DEFAULT false,
    original_lines JSONB,                      -- Lignes avant modification
    modification_reason TEXT,

    -- Statut
    is_posted BOOLEAN DEFAULT false,
    posted_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auto_entries_tenant_doc ON accounting_auto_entries(tenant_id, document_id);
CREATE INDEX idx_auto_entries_tenant_confidence ON accounting_auto_entries(tenant_id, confidence_level);
CREATE INDEX idx_auto_entries_tenant_review ON accounting_auto_entries(tenant_id, requires_review);

-- ============================================================================
-- TABLE: Connexions bancaires (Open Banking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_bank_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Institution bancaire
    institution_id VARCHAR(100) NOT NULL,      -- ID du provider (Plaid, Bridge, etc.)
    institution_name VARCHAR(255) NOT NULL,
    institution_logo_url VARCHAR(500),

    -- Connexion
    provider VARCHAR(50) NOT NULL,             -- plaid, bridge, nordigen, etc.
    connection_id VARCHAR(255) NOT NULL,       -- ID de connexion chez le provider
    status bank_connection_status NOT NULL DEFAULT 'ACTIVE',

    -- Tokens (chiffrés)
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Consentement
    consent_expires_at TIMESTAMP WITH TIME ZONE,
    last_consent_renewed_at TIMESTAMP WITH TIME ZONE,

    -- Dernière synchronisation
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,

    -- Comptes liés
    linked_accounts JSONB DEFAULT '[]',        -- Comptes disponibles via cette connexion

    -- Métadonnées
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bank_conn_tenant ON accounting_bank_connections(tenant_id);
CREATE INDEX idx_bank_conn_tenant_status ON accounting_bank_connections(tenant_id, status);
CREATE UNIQUE INDEX idx_bank_conn_tenant_connection ON accounting_bank_connections(tenant_id, provider, connection_id);

-- ============================================================================
-- TABLE: Comptes bancaires synchronisés
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_synced_bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    connection_id UUID NOT NULL REFERENCES accounting_bank_connections(id) ON DELETE CASCADE,

    -- Compte bancaire interne lié
    bank_account_id UUID REFERENCES bank_accounts(id),

    -- Identification externe
    external_account_id VARCHAR(255) NOT NULL, -- ID chez le provider
    account_name VARCHAR(255) NOT NULL,
    account_number_masked VARCHAR(50),         -- ****1234
    iban_masked VARCHAR(50),

    -- Type de compte
    account_type VARCHAR(50),                  -- checking, savings, credit_card
    account_subtype VARCHAR(50),

    -- Soldes (mis à jour à chaque sync)
    balance_current DECIMAL(15, 2),
    balance_available DECIMAL(15, 2),
    balance_limit DECIMAL(15, 2),              -- Pour cartes de crédit
    balance_currency VARCHAR(3) DEFAULT 'EUR',
    balance_updated_at TIMESTAMP WITH TIME ZONE,

    -- Synchronisation
    is_sync_enabled BOOLEAN DEFAULT true,
    last_transaction_date DATE,
    oldest_transaction_date DATE,

    -- Métadonnées
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_synced_accounts_tenant ON accounting_synced_bank_accounts(tenant_id);
CREATE INDEX idx_synced_accounts_connection ON accounting_synced_bank_accounts(connection_id);
CREATE UNIQUE INDEX idx_synced_accounts_external ON accounting_synced_bank_accounts(tenant_id, connection_id, external_account_id);

-- ============================================================================
-- TABLE: Transactions bancaires synchronisées
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_synced_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    synced_account_id UUID NOT NULL REFERENCES accounting_synced_bank_accounts(id) ON DELETE CASCADE,

    -- Identification
    external_transaction_id VARCHAR(255) NOT NULL,

    -- Transaction
    transaction_date DATE NOT NULL,
    value_date DATE,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Description
    description VARCHAR(500),
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),

    -- Catégorisation automatique
    ai_category VARCHAR(100),
    ai_category_confidence DECIMAL(5, 2),

    -- Rapprochement
    reconciliation_status VARCHAR(50) DEFAULT 'PENDING',
    matched_document_id UUID REFERENCES accounting_documents(id),
    matched_entry_line_id UUID REFERENCES journal_entry_lines(id),
    matched_at TIMESTAMP WITH TIME ZONE,
    match_confidence DECIMAL(5, 2),

    -- Métadonnées bancaires
    raw_data JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_synced_trans_tenant ON accounting_synced_transactions(tenant_id);
CREATE INDEX idx_synced_trans_account ON accounting_synced_transactions(synced_account_id);
CREATE INDEX idx_synced_trans_date ON accounting_synced_transactions(tenant_id, transaction_date);
CREATE INDEX idx_synced_trans_reconciliation ON accounting_synced_transactions(tenant_id, reconciliation_status);
CREATE UNIQUE INDEX idx_synced_trans_external ON accounting_synced_transactions(tenant_id, synced_account_id, external_transaction_id);

-- ============================================================================
-- TABLE: Règles de rapprochement automatique
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_reconciliation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Conditions de matching
    match_criteria JSONB NOT NULL,             -- Critères de correspondance
    -- Exemple: {
    --   "amount_tolerance": 0.01,
    --   "date_tolerance_days": 3,
    --   "match_reference": true,
    --   "vendor_patterns": ["AMAZON*", "AWS*"]
    -- }

    -- Action si match
    auto_reconcile BOOLEAN DEFAULT false,      -- Rapprocher automatiquement
    min_confidence DECIMAL(5, 2) DEFAULT 90,   -- Confiance minimum pour auto-rapprochement

    -- Compte comptable par défaut (si pas de facture)
    default_account_code VARCHAR(20),
    default_tax_code VARCHAR(20),

    -- Priorité
    priority INTEGER DEFAULT 0,

    -- Activation
    is_active BOOLEAN DEFAULT true,

    -- Stats
    times_matched INTEGER DEFAULT 0,
    last_matched_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recon_rules_tenant ON accounting_reconciliation_rules(tenant_id);
CREATE INDEX idx_recon_rules_tenant_active ON accounting_reconciliation_rules(tenant_id, is_active);

-- ============================================================================
-- TABLE: Historique des rapprochements
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_reconciliation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Éléments rapprochés
    transaction_id UUID REFERENCES accounting_synced_transactions(id),
    document_id UUID REFERENCES accounting_documents(id),
    entry_line_id UUID REFERENCES journal_entry_lines(id),

    -- Type de rapprochement
    reconciliation_type VARCHAR(50) NOT NULL,  -- auto, manual, rule_based
    rule_id UUID REFERENCES accounting_reconciliation_rules(id),

    -- Confiance
    confidence_score DECIMAL(5, 2),
    match_details JSONB,                       -- Détails du matching

    -- Montants
    transaction_amount DECIMAL(15, 2),
    document_amount DECIMAL(15, 2),
    difference DECIMAL(15, 2),

    -- Validation
    validated_by UUID,
    validated_at TIMESTAMP WITH TIME ZONE,

    -- Si annulé
    is_cancelled BOOLEAN DEFAULT false,
    cancelled_by UUID,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recon_history_tenant ON accounting_reconciliation_history(tenant_id);
CREATE INDEX idx_recon_history_transaction ON accounting_reconciliation_history(transaction_id);
CREATE INDEX idx_recon_history_document ON accounting_reconciliation_history(document_id);

-- ============================================================================
-- TABLE: Alertes comptables
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Type et sévérité
    alert_type alert_type NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'WARNING', -- INFO, WARNING, ERROR, CRITICAL

    -- Sujet
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- Entité concernée
    entity_type VARCHAR(50),                   -- document, transaction, entry, account
    entity_id UUID,

    -- Destinataires
    target_roles JSONB DEFAULT '["EXPERT_COMPTABLE"]',
    target_users JSONB DEFAULT '[]',

    -- Statut
    is_read BOOLEAN DEFAULT false,
    read_by UUID,
    read_at TIMESTAMP WITH TIME ZONE,

    is_resolved BOOLEAN DEFAULT false,
    resolved_by UUID,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- Auto-expiration
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Métadonnées
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_tenant ON accounting_alerts(tenant_id);
CREATE INDEX idx_alerts_tenant_type ON accounting_alerts(tenant_id, alert_type);
CREATE INDEX idx_alerts_tenant_unresolved ON accounting_alerts(tenant_id, is_resolved) WHERE NOT is_resolved;
CREATE INDEX idx_alerts_entity ON accounting_alerts(entity_type, entity_id);

-- ============================================================================
-- TABLE: Plan comptable universel Azalscore
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_universal_chart (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Code universel
    universal_code VARCHAR(20) NOT NULL UNIQUE,
    name_en VARCHAR(255) NOT NULL,
    name_fr VARCHAR(255) NOT NULL,

    -- Type
    account_type VARCHAR(20) NOT NULL,         -- ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE

    -- Hiérarchie
    parent_code VARCHAR(20) REFERENCES accounting_universal_chart(universal_code),
    level INTEGER NOT NULL DEFAULT 1,

    -- Mappings pays
    country_mappings JSONB DEFAULT '{}',       -- {"FR": "607100", "BE": "6041", "DE": "3400"}

    -- Règles IA
    ai_keywords JSONB DEFAULT '[]',            -- Mots-clés pour classification IA
    ai_patterns JSONB DEFAULT '[]',            -- Patterns regex

    -- Métadonnées
    description TEXT,
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_universal_chart_code ON accounting_universal_chart(universal_code);
CREATE INDEX idx_universal_chart_parent ON accounting_universal_chart(parent_code);
CREATE INDEX idx_universal_chart_type ON accounting_universal_chart(account_type);

-- ============================================================================
-- TABLE: Mappings plan comptable par tenant
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_chart_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Code universel source
    universal_code VARCHAR(20) NOT NULL REFERENCES accounting_universal_chart(universal_code),

    -- Compte local
    local_account_id UUID REFERENCES accounts(id),
    local_account_code VARCHAR(20),

    -- Priorité (si plusieurs mappings possibles)
    priority INTEGER DEFAULT 0,

    -- Conditions d'application
    conditions JSONB DEFAULT '{}',             -- Conditions pour appliquer ce mapping

    -- Activation
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chart_mappings_tenant ON accounting_chart_mappings(tenant_id);
CREATE UNIQUE INDEX idx_chart_mappings_tenant_universal ON accounting_chart_mappings(tenant_id, universal_code);

-- ============================================================================
-- TABLE: Configuration fiscale par pays
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_tax_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50),                     -- NULL = configuration globale

    -- Pays
    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100) NOT NULL,

    -- Type de taxe
    tax_type VARCHAR(50) NOT NULL,             -- VAT, GST, SALES_TAX

    -- Taux applicables
    tax_rates JSONB NOT NULL,                  -- [{name, rate, account_code, is_default}]
    -- Exemple: [
    --   {"name": "TVA normale", "rate": 20.0, "account_code": "445710", "is_default": true},
    --   {"name": "TVA réduite", "rate": 10.0, "account_code": "445711"},
    --   {"name": "TVA super-réduite", "rate": 5.5, "account_code": "445712"}
    -- ]

    -- Règles spécifiques
    special_rules JSONB DEFAULT '{}',

    -- Validation
    is_active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_to DATE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tax_config_tenant ON accounting_tax_configurations(tenant_id);
CREATE INDEX idx_tax_config_country ON accounting_tax_configurations(country_code);

-- ============================================================================
-- TABLE: Préférences utilisateur par vue
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,

    -- Type de vue
    view_type VARCHAR(50) NOT NULL,            -- DIRIGEANT, ASSISTANTE, EXPERT_COMPTABLE

    -- Préférences dashboard
    dashboard_widgets JSONB DEFAULT '[]',      -- Widgets activés et leur ordre
    default_period VARCHAR(20) DEFAULT 'MONTH',-- Période par défaut

    -- Préférences liste
    list_columns JSONB DEFAULT '[]',           -- Colonnes visibles
    default_sort JSONB,                        -- Tri par défaut
    default_filters JSONB DEFAULT '{}',        -- Filtres par défaut

    -- Alertes
    alert_preferences JSONB DEFAULT '{}',      -- Notifications activées

    -- Métadonnées
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_user_prefs_tenant_user_view ON accounting_user_preferences(tenant_id, user_id, view_type);

-- ============================================================================
-- TABLE: Sessions de synchronisation bancaire
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_bank_sync_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    connection_id UUID NOT NULL REFERENCES accounting_bank_connections(id),

    -- Type de sync
    sync_type VARCHAR(50) NOT NULL,            -- MANUAL, SCHEDULED, ON_DEMAND
    triggered_by UUID,

    -- Statut
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, FAILED

    -- Période synchronisée
    sync_from_date DATE,
    sync_to_date DATE,

    -- Résultats
    accounts_synced INTEGER DEFAULT 0,
    transactions_fetched INTEGER DEFAULT 0,
    transactions_new INTEGER DEFAULT 0,
    transactions_updated INTEGER DEFAULT 0,
    reconciliations_auto INTEGER DEFAULT 0,

    -- Erreurs
    error_message TEXT,
    error_details JSONB,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bank_sync_tenant ON accounting_bank_sync_sessions(tenant_id);
CREATE INDEX idx_bank_sync_connection ON accounting_bank_sync_sessions(connection_id);
CREATE INDEX idx_bank_sync_status ON accounting_bank_sync_sessions(tenant_id, status);

-- ============================================================================
-- TABLE: Adresses email dédiées par tenant
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_email_inboxes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Adresse email
    email_address VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL,           -- INVOICES, EXPENSE_NOTES, GENERAL

    -- Configuration
    is_active BOOLEAN DEFAULT true,
    auto_process BOOLEAN DEFAULT true,         -- Traitement automatique

    -- Provider email
    provider VARCHAR(50),                      -- gmail, outlook, custom_smtp
    provider_config JSONB,                     -- Configuration provider

    -- Stats
    emails_received INTEGER DEFAULT 0,
    emails_processed INTEGER DEFAULT 0,
    last_email_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_email_inbox_address ON accounting_email_inboxes(email_address);
CREATE INDEX idx_email_inbox_tenant ON accounting_email_inboxes(tenant_id);

-- ============================================================================
-- TABLE: Logs de traitement email
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_email_processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    inbox_id UUID NOT NULL REFERENCES accounting_email_inboxes(id),

    -- Email
    email_id VARCHAR(255) NOT NULL,
    email_from VARCHAR(255),
    email_subject VARCHAR(500),
    email_received_at TIMESTAMP WITH TIME ZONE,

    -- Traitement
    status VARCHAR(50) NOT NULL,               -- RECEIVED, PROCESSING, COMPLETED, FAILED, IGNORED

    -- Pièces jointes
    attachments_count INTEGER DEFAULT 0,
    attachments_processed INTEGER DEFAULT 0,

    -- Documents créés
    documents_created JSONB DEFAULT '[]',      -- IDs des documents créés

    -- Erreur
    error_message TEXT,

    -- Timestamps
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_logs_tenant ON accounting_email_processing_logs(tenant_id);
CREATE INDEX idx_email_logs_inbox ON accounting_email_processing_logs(inbox_id);
CREATE INDEX idx_email_logs_status ON accounting_email_processing_logs(tenant_id, status);

-- ============================================================================
-- TABLE: Métriques dashboard temps réel
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_dashboard_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Période
    metric_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,          -- DAILY, WEEKLY, MONTHLY

    -- Trésorerie
    cash_balance DECIMAL(15, 2),
    cash_balance_updated_at TIMESTAMP WITH TIME ZONE,

    -- Factures
    invoices_to_pay_count INTEGER DEFAULT 0,
    invoices_to_pay_amount DECIMAL(15, 2) DEFAULT 0,
    invoices_overdue_count INTEGER DEFAULT 0,
    invoices_overdue_amount DECIMAL(15, 2) DEFAULT 0,

    invoices_to_collect_count INTEGER DEFAULT 0,
    invoices_to_collect_amount DECIMAL(15, 2) DEFAULT 0,
    invoices_overdue_collect_count INTEGER DEFAULT 0,
    invoices_overdue_collect_amount DECIMAL(15, 2) DEFAULT 0,

    -- Résultat
    revenue_period DECIMAL(15, 2) DEFAULT 0,
    expenses_period DECIMAL(15, 2) DEFAULT 0,
    result_period DECIMAL(15, 2) DEFAULT 0,

    -- Documents
    documents_pending_count INTEGER DEFAULT 0,
    documents_error_count INTEGER DEFAULT 0,

    -- Rapprochement
    transactions_unreconciled INTEGER DEFAULT 0,

    -- Fraîcheur données
    data_freshness_score DECIMAL(5, 2),        -- 0-100
    last_bank_sync TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tenant_id, metric_date, metric_type)
);

CREATE INDEX idx_dashboard_metrics_tenant ON accounting_dashboard_metrics(tenant_id);
CREATE INDEX idx_dashboard_metrics_date ON accounting_dashboard_metrics(tenant_id, metric_date);

-- ============================================================================
-- FONCTIONS ET TRIGGERS
-- ============================================================================

-- Fonction pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_accounting_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers updated_at
CREATE TRIGGER tr_accounting_documents_updated
    BEFORE UPDATE ON accounting_documents
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

CREATE TRIGGER tr_accounting_bank_connections_updated
    BEFORE UPDATE ON accounting_bank_connections
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

CREATE TRIGGER tr_accounting_synced_accounts_updated
    BEFORE UPDATE ON accounting_synced_bank_accounts
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

CREATE TRIGGER tr_accounting_synced_transactions_updated
    BEFORE UPDATE ON accounting_synced_transactions
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

CREATE TRIGGER tr_accounting_reconciliation_rules_updated
    BEFORE UPDATE ON accounting_reconciliation_rules
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

CREATE TRIGGER tr_accounting_user_preferences_updated
    BEFORE UPDATE ON accounting_user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_accounting_updated_at();

-- ============================================================================
-- DONNÉES INITIALES - Plan comptable universel
-- ============================================================================

INSERT INTO accounting_universal_chart (universal_code, name_en, name_fr, account_type, level, ai_keywords) VALUES
-- Classe 1 - Capitaux
('1', 'Equity', 'Capitaux', 'EQUITY', 1, '[]'),
('10', 'Share Capital', 'Capital', 'EQUITY', 2, '["capital", "apport", "actions"]'),
('11', 'Reserves', 'Réserves', 'EQUITY', 2, '["réserve", "report"]'),
('12', 'Retained Earnings', 'Résultat', 'EQUITY', 2, '["résultat", "bénéfice", "perte"]'),

-- Classe 2 - Immobilisations
('2', 'Fixed Assets', 'Immobilisations', 'ASSET', 1, '[]'),
('20', 'Intangible Assets', 'Immobilisations incorporelles', 'ASSET', 2, '["logiciel", "brevet", "licence", "marque"]'),
('21', 'Tangible Assets', 'Immobilisations corporelles', 'ASSET', 2, '["matériel", "mobilier", "véhicule", "ordinateur"]'),
('27', 'Financial Assets', 'Immobilisations financières', 'ASSET', 2, '["participation", "prêt", "caution"]'),
('28', 'Depreciation', 'Amortissements', 'ASSET', 2, '["amortissement"]'),

-- Classe 3 - Stocks
('3', 'Inventory', 'Stocks', 'ASSET', 1, '[]'),
('31', 'Raw Materials', 'Matières premières', 'ASSET', 2, '["matière première", "approvisionnement"]'),
('35', 'Finished Goods', 'Produits finis', 'ASSET', 2, '["produit fini", "marchandise"]'),
('37', 'Goods for Resale', 'Marchandises', 'ASSET', 2, '["marchandise", "stock"]'),

-- Classe 4 - Tiers
('4', 'Third Parties', 'Comptes de tiers', 'ASSET', 1, '[]'),
('40', 'Suppliers', 'Fournisseurs', 'LIABILITY', 2, '["fournisseur", "achat"]'),
('401', 'Suppliers - Trade', 'Fournisseurs', 'LIABILITY', 3, '["fournisseur"]'),
('41', 'Customers', 'Clients', 'ASSET', 2, '["client", "vente"]'),
('411', 'Customers - Trade', 'Clients', 'ASSET', 3, '["client"]'),
('42', 'Personnel', 'Personnel', 'LIABILITY', 2, '["salaire", "employé", "paie"]'),
('43', 'Social Security', 'Organismes sociaux', 'LIABILITY', 2, '["urssaf", "cotisation", "social"]'),
('44', 'Tax Authorities', 'État et collectivités', 'LIABILITY', 2, '["impôt", "taxe", "tva"]'),
('445', 'VAT', 'TVA', 'LIABILITY', 3, '["tva", "taxe"]'),

-- Classe 5 - Financier
('5', 'Cash & Banks', 'Comptes financiers', 'ASSET', 1, '[]'),
('51', 'Banks', 'Banques', 'ASSET', 2, '["banque", "virement", "prélèvement"]'),
('512', 'Bank Accounts', 'Comptes bancaires', 'ASSET', 3, '["compte bancaire"]'),
('53', 'Cash', 'Caisse', 'ASSET', 2, '["espèces", "caisse", "cash"]'),

-- Classe 6 - Charges
('6', 'Expenses', 'Charges', 'EXPENSE', 1, '[]'),
('60', 'Purchases', 'Achats', 'EXPENSE', 2, '["achat", "approvisionnement"]'),
('601', 'Raw Material Purchases', 'Achats matières premières', 'EXPENSE', 3, '["matière"]'),
('607', 'Goods Purchases', 'Achats marchandises', 'EXPENSE', 3, '["marchandise"]'),
('61', 'External Services', 'Services extérieurs', 'EXPENSE', 2, '["sous-traitance", "location", "entretien"]'),
('613', 'Rent', 'Loyers', 'EXPENSE', 3, '["loyer", "bail", "location"]'),
('615', 'Maintenance', 'Entretien et réparations', 'EXPENSE', 3, '["entretien", "réparation", "maintenance"]'),
('616', 'Insurance', 'Assurances', 'EXPENSE', 3, '["assurance", "mutuelle"]'),
('62', 'Other External Services', 'Autres services extérieurs', 'EXPENSE', 2, '[]'),
('621', 'Temporary Staff', 'Personnel extérieur', 'EXPENSE', 3, '["intérim", "interim"]'),
('622', 'Fees', 'Honoraires', 'EXPENSE', 3, '["honoraire", "consultant", "avocat", "expert"]'),
('623', 'Advertising', 'Publicité', 'EXPENSE', 3, '["publicité", "marketing", "communication"]'),
('625', 'Travel', 'Déplacements', 'EXPENSE', 3, '["déplacement", "voyage", "transport", "train", "avion", "taxi"]'),
('626', 'Postal & Telecom', 'Frais postaux et télécom', 'EXPENSE', 3, '["téléphone", "internet", "mobile", "courrier"]'),
('627', 'Bank Charges', 'Frais bancaires', 'EXPENSE', 3, '["frais bancaire", "commission", "agios"]'),
('63', 'Taxes', 'Impôts et taxes', 'EXPENSE', 2, '["impôt", "taxe", "cfe", "cvae"]'),
('64', 'Personnel Costs', 'Charges de personnel', 'EXPENSE', 2, '["salaire", "charges sociales"]'),
('641', 'Wages', 'Salaires', 'EXPENSE', 3, '["salaire", "rémunération"]'),
('645', 'Social Charges', 'Charges sociales', 'EXPENSE', 3, '["cotisation", "charges sociales"]'),
('65', 'Other Operating Expenses', 'Autres charges d''exploitation', 'EXPENSE', 2, '[]'),
('66', 'Financial Charges', 'Charges financières', 'EXPENSE', 2, '["intérêt", "emprunt"]'),
('67', 'Exceptional Charges', 'Charges exceptionnelles', 'EXPENSE', 2, '["exceptionnel", "pénalité"]'),
('68', 'Depreciation Charges', 'Dotations', 'EXPENSE', 2, '["dotation", "provision"]'),

-- Classe 7 - Produits
('7', 'Revenue', 'Produits', 'REVENUE', 1, '[]'),
('70', 'Sales', 'Ventes', 'REVENUE', 2, '["vente", "chiffre d''affaires"]'),
('701', 'Product Sales', 'Ventes de produits', 'REVENUE', 3, '["vente produit"]'),
('706', 'Service Sales', 'Prestations de services', 'REVENUE', 3, '["prestation", "service", "honoraire"]'),
('707', 'Goods Sales', 'Ventes marchandises', 'REVENUE', 3, '["vente marchandise"]'),
('74', 'Operating Subsidies', 'Subventions d''exploitation', 'REVENUE', 2, '["subvention", "aide"]'),
('75', 'Other Operating Income', 'Autres produits d''exploitation', 'REVENUE', 2, '[]'),
('76', 'Financial Income', 'Produits financiers', 'REVENUE', 2, '["intérêt reçu", "dividende"]'),
('77', 'Exceptional Income', 'Produits exceptionnels', 'REVENUE', 2, '["exceptionnel", "plus-value"]'),
('78', 'Reversal of Provisions', 'Reprises', 'REVENUE', 2, '["reprise provision"]')
ON CONFLICT (universal_code) DO NOTHING;

-- ============================================================================
-- DONNÉES INITIALES - Configuration TVA France
-- ============================================================================

INSERT INTO accounting_tax_configurations (country_code, country_name, tax_type, tax_rates) VALUES
('FR', 'France', 'VAT', '[
    {"name": "TVA normale", "rate": 20.0, "account_code": "445710", "is_default": true},
    {"name": "TVA intermédiaire", "rate": 10.0, "account_code": "445711"},
    {"name": "TVA réduite", "rate": 5.5, "account_code": "445712"},
    {"name": "TVA super-réduite", "rate": 2.1, "account_code": "445713"},
    {"name": "Exonéré", "rate": 0.0, "account_code": "445714"}
]'),
('BE', 'Belgique', 'VAT', '[
    {"name": "TVA normale", "rate": 21.0, "account_code": "445710", "is_default": true},
    {"name": "TVA réduite", "rate": 12.0, "account_code": "445711"},
    {"name": "TVA super-réduite", "rate": 6.0, "account_code": "445712"}
]'),
('DE', 'Allemagne', 'VAT', '[
    {"name": "MwSt normal", "rate": 19.0, "account_code": "445710", "is_default": true},
    {"name": "MwSt ermäßigt", "rate": 7.0, "account_code": "445711"}
]'),
('ES', 'Espagne', 'VAT', '[
    {"name": "IVA general", "rate": 21.0, "account_code": "445710", "is_default": true},
    {"name": "IVA reducido", "rate": 10.0, "account_code": "445711"},
    {"name": "IVA superreducido", "rate": 4.0, "account_code": "445712"}
]'),
('IT', 'Italie', 'VAT', '[
    {"name": "IVA ordinaria", "rate": 22.0, "account_code": "445710", "is_default": true},
    {"name": "IVA ridotta", "rate": 10.0, "account_code": "445711"},
    {"name": "IVA minima", "rate": 4.0, "account_code": "445712"}
]'),
('CH', 'Suisse', 'VAT', '[
    {"name": "TVA normale", "rate": 8.1, "account_code": "445710", "is_default": true},
    {"name": "TVA réduite", "rate": 2.6, "account_code": "445711"},
    {"name": "TVA hébergement", "rate": 3.8, "account_code": "445712"}
]'),
('GB', 'Royaume-Uni', 'VAT', '[
    {"name": "Standard VAT", "rate": 20.0, "account_code": "445710", "is_default": true},
    {"name": "Reduced VAT", "rate": 5.0, "account_code": "445711"},
    {"name": "Zero VAT", "rate": 0.0, "account_code": "445712"}
]'),
('US', 'États-Unis', 'SALES_TAX', '[
    {"name": "No Federal Tax", "rate": 0.0, "account_code": "445710", "is_default": true, "note": "State-specific rates apply"}
]'),
('CA', 'Canada', 'GST', '[
    {"name": "GST", "rate": 5.0, "account_code": "445710", "is_default": true},
    {"name": "HST Ontario", "rate": 13.0, "account_code": "445711"},
    {"name": "HST Maritimes", "rate": 15.0, "account_code": "445712"}
]')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE accounting_documents IS 'Documents sources pour comptabilité automatisée (factures, notes de frais, etc.)';
COMMENT ON TABLE accounting_ocr_results IS 'Résultats OCR détaillés pour chaque document';
COMMENT ON TABLE accounting_ai_classifications IS 'Classifications IA avec niveaux de confiance';
COMMENT ON TABLE accounting_auto_entries IS 'Écritures comptables générées automatiquement';
COMMENT ON TABLE accounting_bank_connections IS 'Connexions Open Banking (mode PULL)';
COMMENT ON TABLE accounting_synced_bank_accounts IS 'Comptes bancaires synchronisés';
COMMENT ON TABLE accounting_synced_transactions IS 'Transactions bancaires synchronisées';
COMMENT ON TABLE accounting_reconciliation_rules IS 'Règles de rapprochement automatique';
COMMENT ON TABLE accounting_reconciliation_history IS 'Historique des rapprochements';
COMMENT ON TABLE accounting_alerts IS 'Alertes comptables intelligentes';
COMMENT ON TABLE accounting_universal_chart IS 'Plan comptable universel Azalscore';
COMMENT ON TABLE accounting_chart_mappings IS 'Mappings vers plans comptables locaux';
COMMENT ON TABLE accounting_tax_configurations IS 'Configurations fiscales par pays';
COMMENT ON TABLE accounting_user_preferences IS 'Préférences utilisateur par vue';
COMMENT ON TABLE accounting_bank_sync_sessions IS 'Sessions de synchronisation bancaire';
COMMENT ON TABLE accounting_email_inboxes IS 'Boîtes email dédiées par tenant';
COMMENT ON TABLE accounting_email_processing_logs IS 'Logs de traitement email';
COMMENT ON TABLE accounting_dashboard_metrics IS 'Métriques dashboard temps réel';
