-- AZALS - ROLLBACK Migration COUNTRY PACKS MODULE
-- Annule la creation du module de configuration pays (T5)

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_active_vat_rates;
    DROP VIEW IF EXISTS v_country_pack_summary;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_update_country_packs ON country_packs;
    DROP TRIGGER IF EXISTS trigger_update_country_tax_rates ON country_tax_rates;
    DROP TRIGGER IF EXISTS trigger_update_country_document_templates ON country_document_templates;
    DROP TRIGGER IF EXISTS trigger_update_country_bank_configs ON country_bank_configs;
    DROP TRIGGER IF EXISTS trigger_update_country_public_holidays ON country_public_holidays;
    DROP TRIGGER IF EXISTS trigger_update_country_legal_requirements ON country_legal_requirements;

    -- Drop function
    DROP FUNCTION IF EXISTS update_country_packs_updated_at();

    -- Drop indexes for tenant_country_settings
    DROP INDEX IF EXISTS idx_tenant_settings_tenant;
    DROP INDEX IF EXISTS idx_tenant_settings_pack;
    DROP INDEX IF EXISTS idx_tenant_settings_primary;

    -- Drop indexes for country_legal_requirements
    DROP INDEX IF EXISTS idx_legal_req_tenant;
    DROP INDEX IF EXISTS idx_legal_req_country;
    DROP INDEX IF EXISTS idx_legal_req_category;

    -- Drop indexes for country_public_holidays
    DROP INDEX IF EXISTS idx_holidays_tenant;
    DROP INDEX IF EXISTS idx_holidays_country;
    DROP INDEX IF EXISTS idx_holidays_date;
    DROP INDEX IF EXISTS idx_holidays_month_day;

    -- Drop indexes for country_bank_configs
    DROP INDEX IF EXISTS idx_bank_configs_tenant;
    DROP INDEX IF EXISTS idx_bank_configs_country;
    DROP INDEX IF EXISTS idx_bank_configs_format;

    -- Drop indexes for country_document_templates
    DROP INDEX IF EXISTS idx_doc_templates_tenant;
    DROP INDEX IF EXISTS idx_doc_templates_country;
    DROP INDEX IF EXISTS idx_doc_templates_type;

    -- Drop indexes for country_tax_rates
    DROP INDEX IF EXISTS idx_tax_rates_tenant;
    DROP INDEX IF EXISTS idx_tax_rates_country;
    DROP INDEX IF EXISTS idx_tax_rates_code;
    DROP INDEX IF EXISTS idx_tax_rates_type;

    -- Drop indexes for country_packs
    DROP INDEX IF EXISTS idx_country_packs_tenant;
    DROP INDEX IF EXISTS idx_country_packs_status;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS tenant_country_settings CASCADE;
    DROP TABLE IF EXISTS country_legal_requirements CASCADE;
    DROP TABLE IF EXISTS country_public_holidays CASCADE;
    DROP TABLE IF EXISTS country_bank_configs CASCADE;
    DROP TABLE IF EXISTS country_document_templates CASCADE;
    DROP TABLE IF EXISTS country_tax_rates CASCADE;
    DROP TABLE IF EXISTS country_packs CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS pack_status;
    DROP TYPE IF EXISTS number_format_style;
    DROP TYPE IF EXISTS date_format_style;
    DROP TYPE IF EXISTS bank_format;
    DROP TYPE IF EXISTS document_type;
    DROP TYPE IF EXISTS tax_type;

    RAISE NOTICE 'Migration 011_country_packs_module rolled back successfully';
END $$;
