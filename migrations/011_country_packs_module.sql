-- ============================================================================
-- AZALS MODULE T5 - Migration Packs Pays
-- ============================================================================
-- Version: 1.0.0
-- Date: 2026-01-03
-- Description: Tables pour les configurations pays (fiscal, légal, bancaire)
-- ============================================================================

-- Types ENUM
DO $$ BEGIN
    CREATE TYPE tax_type AS ENUM (
        'VAT', 'SALES_TAX', 'CORPORATE_TAX', 'PAYROLL_TAX',
        'WITHHOLDING', 'CUSTOMS', 'EXCISE', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE document_type AS ENUM (
        'INVOICE', 'CREDIT_NOTE', 'PURCHASE_ORDER', 'DELIVERY_NOTE',
        'PAYSLIP', 'TAX_RETURN', 'BALANCE_SHEET', 'INCOME_STATEMENT',
        'CONTRACT', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE bank_format AS ENUM (
        'SEPA', 'SWIFT', 'ACH', 'BACS', 'CMI', 'RTGS', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE date_format_style AS ENUM (
        'DMY', 'MDY', 'YMD', 'DDMMYYYY', 'MMDDYYYY', 'YYYYMMDD'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE number_format_style AS ENUM ('EU', 'US', 'CH');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE pack_status AS ENUM ('DRAFT', 'ACTIVE', 'DEPRECATED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ============================================================================
-- TABLES PRINCIPALES
-- ============================================================================

-- Table des packs pays
CREATE TABLE IF NOT EXISTS country_packs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    country_name_local VARCHAR(100),

    status pack_status DEFAULT 'ACTIVE' NOT NULL,

    default_language VARCHAR(5) DEFAULT 'fr',
    default_currency VARCHAR(3) NOT NULL,
    currency_symbol VARCHAR(10),
    currency_position VARCHAR(10) DEFAULT 'after',

    date_format date_format_style DEFAULT 'DMY',
    time_format VARCHAR(20) DEFAULT 'HH:mm',
    number_format number_format_style DEFAULT 'EU',
    decimal_separator VARCHAR(1) DEFAULT ',',
    thousands_separator VARCHAR(1) DEFAULT ' ',

    timezone VARCHAR(50) DEFAULT 'Europe/Paris',
    week_start INTEGER DEFAULT 1,

    fiscal_year_start_month INTEGER DEFAULT 1,
    fiscal_year_start_day INTEGER DEFAULT 1,
    default_vat_rate FLOAT DEFAULT 20.0,
    has_regional_taxes BOOLEAN DEFAULT FALSE,

    company_id_label VARCHAR(50) DEFAULT 'SIRET',
    company_id_format VARCHAR(100),
    vat_id_label VARCHAR(50) DEFAULT 'TVA',
    vat_id_format VARCHAR(100),

    config JSONB,

    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER,

    CONSTRAINT uq_country_pack_code UNIQUE (tenant_id, country_code)
);

CREATE INDEX IF NOT EXISTS idx_country_packs_tenant ON country_packs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_country_packs_status ON country_packs(tenant_id, status);


-- Table des taux de taxe
CREATE TABLE IF NOT EXISTS country_tax_rates (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    tax_type tax_type NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    rate FLOAT NOT NULL,
    is_percentage BOOLEAN DEFAULT TRUE,

    applies_to VARCHAR(50),
    region VARCHAR(100),

    account_collected VARCHAR(20),
    account_deductible VARCHAR(20),
    account_payable VARCHAR(20),

    valid_from DATE DEFAULT CURRENT_DATE,
    valid_to DATE,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tax_rates_tenant ON country_tax_rates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tax_rates_country ON country_tax_rates(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_tax_rates_code ON country_tax_rates(tenant_id, code);
CREATE INDEX IF NOT EXISTS idx_tax_rates_type ON country_tax_rates(tenant_id, tax_type);


-- Table des templates de documents
CREATE TABLE IF NOT EXISTS country_document_templates (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    document_type document_type NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    template_format VARCHAR(20) DEFAULT 'html',
    template_content TEXT,
    template_path VARCHAR(500),

    mandatory_fields JSONB,
    legal_mentions TEXT,

    numbering_prefix VARCHAR(20),
    numbering_pattern VARCHAR(50),
    numbering_reset VARCHAR(20) DEFAULT 'yearly',

    language VARCHAR(5) DEFAULT 'fr',
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_doc_templates_tenant ON country_document_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_doc_templates_country ON country_document_templates(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_doc_templates_type ON country_document_templates(tenant_id, document_type);


-- Table des configurations bancaires
CREATE TABLE IF NOT EXISTS country_bank_configs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    bank_format bank_format NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    iban_prefix VARCHAR(2),
    iban_length INTEGER,
    bic_required BOOLEAN DEFAULT TRUE,

    export_format VARCHAR(20),
    export_encoding VARCHAR(20) DEFAULT 'utf-8',
    export_template TEXT,

    config JSONB,

    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bank_configs_tenant ON country_bank_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bank_configs_country ON country_bank_configs(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_bank_configs_format ON country_bank_configs(tenant_id, bank_format);


-- Table des jours fériés
CREATE TABLE IF NOT EXISTS country_public_holidays (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    name VARCHAR(200) NOT NULL,
    name_local VARCHAR(200),

    holiday_date DATE,
    month INTEGER,
    day INTEGER,
    is_fixed BOOLEAN DEFAULT TRUE,
    calculation_rule VARCHAR(100),

    year INTEGER,
    region VARCHAR(100),
    is_national BOOLEAN DEFAULT TRUE,

    is_work_day BOOLEAN DEFAULT FALSE,
    affects_banks BOOLEAN DEFAULT TRUE,
    affects_business BOOLEAN DEFAULT TRUE,

    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_holidays_tenant ON country_public_holidays(tenant_id);
CREATE INDEX IF NOT EXISTS idx_holidays_country ON country_public_holidays(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON country_public_holidays(tenant_id, holiday_date);
CREATE INDEX IF NOT EXISTS idx_holidays_month_day ON country_public_holidays(tenant_id, month, day);


-- Table des exigences légales
CREATE TABLE IF NOT EXISTS country_legal_requirements (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    category VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    requirement_type VARCHAR(50),
    frequency VARCHAR(20),
    deadline_rule VARCHAR(100),

    config JSONB,

    legal_reference VARCHAR(200),
    effective_date DATE,
    end_date DATE,

    is_mandatory BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_legal_req_tenant ON country_legal_requirements(tenant_id);
CREATE INDEX IF NOT EXISTS idx_legal_req_country ON country_legal_requirements(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_legal_req_category ON country_legal_requirements(tenant_id, category);


-- Table des paramètres tenant
CREATE TABLE IF NOT EXISTS tenant_country_settings (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,

    country_pack_id INTEGER REFERENCES country_packs(id) ON DELETE CASCADE NOT NULL,

    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    custom_currency VARCHAR(3),
    custom_language VARCHAR(5),
    custom_timezone VARCHAR(50),
    custom_config JSONB,

    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant ON tenant_country_settings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_pack ON tenant_country_settings(country_pack_id);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_primary ON tenant_country_settings(tenant_id, is_primary);


-- ============================================================================
-- TRIGGERS (Auto-update timestamps)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_country_packs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_country_packs ON country_packs;
CREATE TRIGGER trigger_update_country_packs
    BEFORE UPDATE ON country_packs
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();

DROP TRIGGER IF EXISTS trigger_update_country_tax_rates ON country_tax_rates;
CREATE TRIGGER trigger_update_country_tax_rates
    BEFORE UPDATE ON country_tax_rates
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();

DROP TRIGGER IF EXISTS trigger_update_country_document_templates ON country_document_templates;
CREATE TRIGGER trigger_update_country_document_templates
    BEFORE UPDATE ON country_document_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();

DROP TRIGGER IF EXISTS trigger_update_country_bank_configs ON country_bank_configs;
CREATE TRIGGER trigger_update_country_bank_configs
    BEFORE UPDATE ON country_bank_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();

DROP TRIGGER IF EXISTS trigger_update_country_public_holidays ON country_public_holidays;
CREATE TRIGGER trigger_update_country_public_holidays
    BEFORE UPDATE ON country_public_holidays
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();

DROP TRIGGER IF EXISTS trigger_update_country_legal_requirements ON country_legal_requirements;
CREATE TRIGGER trigger_update_country_legal_requirements
    BEFORE UPDATE ON country_legal_requirements
    FOR EACH ROW
    EXECUTE FUNCTION update_country_packs_updated_at();


-- ============================================================================
-- DONNÉES INITIALES - Pack France
-- ============================================================================

-- Pack France par défaut (pour tous les tenants, sera copié)
INSERT INTO country_packs (
    tenant_id, country_code, country_name, country_name_local,
    default_language, default_currency, currency_symbol, currency_position,
    date_format, number_format, timezone, fiscal_year_start_month,
    default_vat_rate, company_id_label, vat_id_label, is_default
) VALUES (
    'SYSTEM', 'FR', 'France', 'France',
    'fr', 'EUR', '€', 'after',
    'DMY', 'EU', 'Europe/Paris', 1,
    20.0, 'SIRET', 'TVA Intra', TRUE
) ON CONFLICT (tenant_id, country_code) DO NOTHING;

-- Pack Maroc
INSERT INTO country_packs (
    tenant_id, country_code, country_name, country_name_local,
    default_language, default_currency, currency_symbol, currency_position,
    date_format, number_format, timezone, fiscal_year_start_month,
    default_vat_rate, company_id_label, vat_id_label, is_default
) VALUES (
    'SYSTEM', 'MA', 'Morocco', 'المغرب',
    'fr', 'MAD', 'DH', 'after',
    'DMY', 'EU', 'Africa/Casablanca', 1,
    20.0, 'RC', 'IF', FALSE
) ON CONFLICT (tenant_id, country_code) DO NOTHING;

-- Pack Sénégal
INSERT INTO country_packs (
    tenant_id, country_code, country_name, country_name_local,
    default_language, default_currency, currency_symbol, currency_position,
    date_format, number_format, timezone, fiscal_year_start_month,
    default_vat_rate, company_id_label, vat_id_label, is_default
) VALUES (
    'SYSTEM', 'SN', 'Senegal', 'Sénégal',
    'fr', 'XOF', 'FCFA', 'after',
    'DMY', 'EU', 'Africa/Dakar', 1,
    18.0, 'NINEA', 'NINEA', FALSE
) ON CONFLICT (tenant_id, country_code) DO NOTHING;

-- Pack Belgique
INSERT INTO country_packs (
    tenant_id, country_code, country_name, country_name_local,
    default_language, default_currency, currency_symbol, currency_position,
    date_format, number_format, timezone, fiscal_year_start_month,
    default_vat_rate, company_id_label, vat_id_label, is_default
) VALUES (
    'SYSTEM', 'BE', 'Belgium', 'Belgique',
    'fr', 'EUR', '€', 'after',
    'DMY', 'EU', 'Europe/Brussels', 1,
    21.0, 'BCE', 'TVA', FALSE
) ON CONFLICT (tenant_id, country_code) DO NOTHING;

-- Pack Suisse
INSERT INTO country_packs (
    tenant_id, country_code, country_name, country_name_local,
    default_language, default_currency, currency_symbol, currency_position,
    date_format, number_format, timezone, fiscal_year_start_month,
    default_vat_rate, company_id_label, vat_id_label, is_default
) VALUES (
    'SYSTEM', 'CH', 'Switzerland', 'Suisse',
    'fr', 'CHF', 'CHF', 'before',
    'DMY', 'CH', 'Europe/Zurich', 1,
    8.1, 'IDE', 'TVA', FALSE
) ON CONFLICT (tenant_id, country_code) DO NOTHING;


-- ============================================================================
-- VUES UTILITAIRES
-- ============================================================================

-- Vue résumé des packs par tenant
CREATE OR REPLACE VIEW v_country_pack_summary AS
SELECT
    cp.tenant_id,
    cp.country_code,
    cp.country_name,
    cp.default_currency,
    cp.status,
    cp.is_default,
    (SELECT COUNT(*) FROM country_tax_rates tr WHERE tr.country_pack_id = cp.id AND tr.is_active = TRUE) as tax_rates_count,
    (SELECT COUNT(*) FROM country_document_templates dt WHERE dt.country_pack_id = cp.id AND dt.is_active = TRUE) as templates_count,
    (SELECT COUNT(*) FROM country_public_holidays ph WHERE ph.country_pack_id = cp.id AND ph.is_active = TRUE) as holidays_count,
    (SELECT COUNT(*) FROM country_legal_requirements lr WHERE lr.country_pack_id = cp.id AND lr.is_active = TRUE) as requirements_count
FROM country_packs cp;


-- Vue des taux TVA actifs
CREATE OR REPLACE VIEW v_active_vat_rates AS
SELECT
    tr.*,
    cp.country_code,
    cp.country_name
FROM country_tax_rates tr
JOIN country_packs cp ON tr.country_pack_id = cp.id
WHERE tr.tax_type = 'VAT'
  AND tr.is_active = TRUE
  AND (tr.valid_to IS NULL OR tr.valid_to >= CURRENT_DATE)
ORDER BY cp.country_code, tr.rate DESC;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE country_packs IS 'Configurations par pays (fiscal, légal, bancaire)';
COMMENT ON TABLE country_tax_rates IS 'Taux de taxe par pays';
COMMENT ON TABLE country_document_templates IS 'Templates de documents légaux par pays';
COMMENT ON TABLE country_bank_configs IS 'Configurations bancaires par pays';
COMMENT ON TABLE country_public_holidays IS 'Jours fériés par pays';
COMMENT ON TABLE country_legal_requirements IS 'Exigences légales par pays';
COMMENT ON TABLE tenant_country_settings IS 'Paramètres pays activés par tenant';


-- ============================================================================
-- FIN MIGRATION
-- ============================================================================
