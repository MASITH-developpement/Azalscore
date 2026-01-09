-- =============================================================================
-- AZALS ERP - UUID Migration Script - PRODUCTION ENVIRONMENT
-- =============================================================================
-- SAFE MIGRATION: This script preserves existing data by using temporary columns
-- and careful type conversion. Always backup before running!
--
-- This script migrates all Integer PKs and FKs to UUID for PostgreSQL
-- compatibility, resolving DatatypeMismatch errors.
--
-- Created: 2026-01-09
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- BACKUP RECOMMENDATION
-- =============================================================================
-- Before running this script, create a full database backup:
-- pg_dump -Fc -f azals_backup_$(date +%Y%m%d_%H%M%S).dump your_database_name

BEGIN;

-- =============================================================================
-- HELPER: Create a function to generate deterministic UUIDs from integers
-- This ensures referential integrity during migration
-- =============================================================================

CREATE OR REPLACE FUNCTION int_to_uuid(int_val INTEGER) RETURNS UUID AS $$
BEGIN
    -- Generate deterministic UUID v5 from integer using namespace
    RETURN uuid_generate_v5(uuid_ns_url(), 'azals:id:' || int_val::text);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- STRIPE INTEGRATION TABLES (12 tables)
-- =============================================================================

-- 1. stripe_customers
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_customers') THEN
        -- Add new UUID columns
        ALTER TABLE stripe_customers ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        -- Migrate data
        UPDATE stripe_customers SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
        -- Update foreign keys in child tables
        ALTER TABLE stripe_subscriptions ADD COLUMN IF NOT EXISTS stripe_customer_id_new UUID;
        UPDATE stripe_subscriptions s SET stripe_customer_id_new = int_to_uuid(s.stripe_customer_id);
        ALTER TABLE stripe_invoices ADD COLUMN IF NOT EXISTS stripe_customer_id_new UUID;
        UPDATE stripe_invoices i SET stripe_customer_id_new = int_to_uuid(i.stripe_customer_id);
        ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS stripe_customer_id_new UUID;
        UPDATE stripe_payments p SET stripe_customer_id_new = int_to_uuid(p.stripe_customer_id);
        ALTER TABLE stripe_payment_methods ADD COLUMN IF NOT EXISTS stripe_customer_id_new UUID;
        UPDATE stripe_payment_methods pm SET stripe_customer_id_new = int_to_uuid(pm.stripe_customer_id);
    END IF;
END $$;

-- 2. stripe_products
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_products') THEN
        ALTER TABLE stripe_products ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_products SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
        -- Update foreign keys
        ALTER TABLE stripe_prices ADD COLUMN IF NOT EXISTS product_id_new UUID;
        UPDATE stripe_prices p SET product_id_new = int_to_uuid(p.product_id);
    END IF;
END $$;

-- 3. stripe_prices
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_prices') THEN
        ALTER TABLE stripe_prices ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_prices SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
        -- Update foreign keys
        ALTER TABLE stripe_subscriptions ADD COLUMN IF NOT EXISTS stripe_price_id_new UUID;
        UPDATE stripe_subscriptions s SET stripe_price_id_new = int_to_uuid(s.stripe_price_id);
    END IF;
END $$;

-- Continue for remaining stripe tables...
-- 4. stripe_subscriptions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_subscriptions') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_subscriptions SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 5. stripe_invoices
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_invoices') THEN
        ALTER TABLE stripe_invoices ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_invoices SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 6. stripe_payments
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_payments') THEN
        ALTER TABLE stripe_payments ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_payments SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 7. stripe_payment_methods
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_payment_methods') THEN
        ALTER TABLE stripe_payment_methods ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_payment_methods SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 8. stripe_coupons
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_coupons') THEN
        ALTER TABLE stripe_coupons ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_coupons SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 9. stripe_usage_records
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_usage_records') THEN
        ALTER TABLE stripe_usage_records ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_usage_records SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 10. stripe_webhooks
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_webhooks') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_webhooks SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 11. stripe_sync_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_sync_logs') THEN
        ALTER TABLE stripe_sync_logs ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_sync_logs SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- 12. stripe_audit_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'stripe_audit_logs') THEN
        ALTER TABLE stripe_audit_logs ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE stripe_audit_logs SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- =============================================================================
-- COUNTRY PACKS TABLES (7 tables)
-- =============================================================================

-- 1. country_packs (parent table)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_packs') THEN
        ALTER TABLE country_packs ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_packs SET id_new = int_to_uuid(id) WHERE id_new IS NULL;

        -- Update FKs in child tables
        ALTER TABLE country_tax_rates ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE country_tax_rates SET country_pack_id_new = int_to_uuid(country_pack_id);

        ALTER TABLE country_document_templates ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE country_document_templates SET country_pack_id_new = int_to_uuid(country_pack_id);

        ALTER TABLE country_bank_configs ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE country_bank_configs SET country_pack_id_new = int_to_uuid(country_pack_id);

        ALTER TABLE country_public_holidays ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE country_public_holidays SET country_pack_id_new = int_to_uuid(country_pack_id);

        ALTER TABLE country_legal_requirements ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE country_legal_requirements SET country_pack_id_new = int_to_uuid(country_pack_id);

        ALTER TABLE tenant_country_settings ADD COLUMN IF NOT EXISTS country_pack_id_new UUID;
        UPDATE tenant_country_settings SET country_pack_id_new = int_to_uuid(country_pack_id);
    END IF;
END $$;

-- Country pack child tables PKs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_tax_rates') THEN
        ALTER TABLE country_tax_rates ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_tax_rates SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_document_templates') THEN
        ALTER TABLE country_document_templates ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_document_templates SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_bank_configs') THEN
        ALTER TABLE country_bank_configs ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_bank_configs SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_public_holidays') THEN
        ALTER TABLE country_public_holidays ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_public_holidays SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'country_legal_requirements') THEN
        ALTER TABLE country_legal_requirements ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE country_legal_requirements SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tenant_country_settings') THEN
        ALTER TABLE tenant_country_settings ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE tenant_country_settings SET id_new = int_to_uuid(id) WHERE id_new IS NULL;
    END IF;
END $$;

-- =============================================================================
-- FRANCE PACK TABLES (11 tables)
-- =============================================================================

-- fr_fec_exports (parent) -> fr_fec_entries (child)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'fr_fec_exports') THEN
        ALTER TABLE fr_fec_exports ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE fr_fec_exports SET id_new = int_to_uuid(id) WHERE id_new IS NULL;

        ALTER TABLE fr_fec_entries ADD COLUMN IF NOT EXISTS fec_export_id_new UUID;
        UPDATE fr_fec_entries SET fec_export_id_new = int_to_uuid(fec_export_id);
    END IF;
END $$;

-- fr_dsn_declarations (parent) -> fr_dsn_employees (child)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'fr_dsn_declarations') THEN
        ALTER TABLE fr_dsn_declarations ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE fr_dsn_declarations SET id_new = int_to_uuid(id) WHERE id_new IS NULL;

        ALTER TABLE fr_dsn_employees ADD COLUMN IF NOT EXISTS dsn_declaration_id_new UUID;
        UPDATE fr_dsn_employees SET dsn_declaration_id_new = int_to_uuid(dsn_declaration_id);
    END IF;
END $$;

-- Remaining France tables (no FK dependencies, just PK migration)
DO $$
DECLARE
    table_names TEXT[] := ARRAY[
        'fr_pcg_accounts', 'fr_vat_rates', 'fr_vat_declarations',
        'fr_fec_entries', 'fr_dsn_employees', 'fr_employment_contracts',
        'fr_rgpd_consents', 'fr_rgpd_requests', 'fr_rgpd_data_processing', 'fr_rgpd_data_breaches'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY table_names LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl) THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid()', tbl);
            EXECUTE format('UPDATE %I SET id_new = int_to_uuid(id) WHERE id_new IS NULL', tbl);
        END IF;
    END LOOP;
END $$;

-- =============================================================================
-- AUTOCONFIG TABLES (7 tables)
-- =============================================================================

-- autoconfig_job_profiles (parent) -> autoconfig_profile_assignments, autoconfig_onboarding (children)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'autoconfig_job_profiles') THEN
        ALTER TABLE autoconfig_job_profiles ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid();
        UPDATE autoconfig_job_profiles SET id_new = int_to_uuid(id) WHERE id_new IS NULL;

        ALTER TABLE autoconfig_profile_assignments ADD COLUMN IF NOT EXISTS profile_id_new UUID;
        UPDATE autoconfig_profile_assignments SET profile_id_new = int_to_uuid(profile_id);

        ALTER TABLE autoconfig_onboarding ADD COLUMN IF NOT EXISTS detected_profile_id_new UUID;
        UPDATE autoconfig_onboarding SET detected_profile_id_new = int_to_uuid(detected_profile_id)
            WHERE detected_profile_id IS NOT NULL;
    END IF;
END $$;

-- Remaining autoconfig tables
DO $$
DECLARE
    table_names TEXT[] := ARRAY[
        'autoconfig_profile_assignments', 'autoconfig_permission_overrides',
        'autoconfig_onboarding', 'autoconfig_offboarding',
        'autoconfig_rules', 'autoconfig_logs'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY table_names LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl) THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS id_new UUID DEFAULT gen_random_uuid()', tbl);
            EXECUTE format('UPDATE %I SET id_new = int_to_uuid(id) WHERE id_new IS NULL', tbl);
        END IF;
    END LOOP;
END $$;

-- =============================================================================
-- HR TABLES - Just alter user_id column type
-- =============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'hr_employees' AND column_name = 'user_id'
               AND data_type = 'integer') THEN
        -- Add new UUID column
        ALTER TABLE hr_employees ADD COLUMN IF NOT EXISTS user_id_new UUID;
        -- Migrate data (convert integer to deterministic UUID)
        UPDATE hr_employees SET user_id_new = int_to_uuid(user_id) WHERE user_id IS NOT NULL;
    END IF;
END $$;

-- =============================================================================
-- STEP 2: SWAP COLUMNS (Drop old, rename new)
-- This should be run after verifying data migration
-- =============================================================================

-- NOTE: The actual column swap should be done in a separate transaction
-- after verifying data integrity. Below is a template for the swap.

-- For each table, run:
-- ALTER TABLE table_name DROP CONSTRAINT IF EXISTS table_name_pkey CASCADE;
-- ALTER TABLE table_name DROP COLUMN id;
-- ALTER TABLE table_name RENAME COLUMN id_new TO id;
-- ALTER TABLE table_name ADD PRIMARY KEY (id);

-- For FK columns:
-- ALTER TABLE child_table DROP CONSTRAINT IF EXISTS fk_name;
-- ALTER TABLE child_table DROP COLUMN parent_id;
-- ALTER TABLE child_table RENAME COLUMN parent_id_new TO parent_id;
-- ALTER TABLE child_table ADD CONSTRAINT fk_name FOREIGN KEY (parent_id) REFERENCES parent_table(id);

COMMIT;

-- =============================================================================
-- CLEANUP: Drop helper function after migration
-- =============================================================================
-- DROP FUNCTION IF EXISTS int_to_uuid(INTEGER);

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- After migration, run:
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE column_name IN ('id', 'user_id')
--   AND table_schema = 'public'
-- ORDER BY table_name, column_name;
