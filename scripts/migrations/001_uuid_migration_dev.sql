-- =============================================================================
-- AZALS ERP - UUID Migration Script - DEVELOPMENT ENVIRONMENT
-- =============================================================================
-- WARNING: This script uses DROP CASCADE! DATA WILL BE LOST!
-- Only use in development environments where data loss is acceptable.
--
-- This script migrates all Integer PKs and FKs to UUID for PostgreSQL
-- compatibility, resolving DatatypeMismatch errors.
--
-- Created: 2026-01-09
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

BEGIN;

-- =============================================================================
-- STEP 1: DROP ALL AFFECTED TABLES (CASCADE)
-- =============================================================================

-- Stripe Integration Tables (12 tables)
DROP TABLE IF EXISTS stripe_audit_logs CASCADE;
DROP TABLE IF EXISTS stripe_sync_logs CASCADE;
DROP TABLE IF EXISTS stripe_webhooks CASCADE;
DROP TABLE IF EXISTS stripe_usage_records CASCADE;
DROP TABLE IF EXISTS stripe_coupons CASCADE;
DROP TABLE IF EXISTS stripe_prices CASCADE;
DROP TABLE IF EXISTS stripe_products CASCADE;
DROP TABLE IF EXISTS stripe_payment_methods CASCADE;
DROP TABLE IF EXISTS stripe_payments CASCADE;
DROP TABLE IF EXISTS stripe_invoices CASCADE;
DROP TABLE IF EXISTS stripe_subscriptions CASCADE;
DROP TABLE IF EXISTS stripe_customers CASCADE;

-- Country Packs Tables (7 tables)
DROP TABLE IF EXISTS tenant_country_settings CASCADE;
DROP TABLE IF EXISTS country_legal_requirements CASCADE;
DROP TABLE IF EXISTS country_public_holidays CASCADE;
DROP TABLE IF EXISTS country_bank_configs CASCADE;
DROP TABLE IF EXISTS country_document_templates CASCADE;
DROP TABLE IF EXISTS country_tax_rates CASCADE;
DROP TABLE IF EXISTS country_packs CASCADE;

-- France Pack Tables (11 tables)
DROP TABLE IF EXISTS fr_rgpd_data_breaches CASCADE;
DROP TABLE IF EXISTS fr_rgpd_data_processing CASCADE;
DROP TABLE IF EXISTS fr_rgpd_requests CASCADE;
DROP TABLE IF EXISTS fr_rgpd_consents CASCADE;
DROP TABLE IF EXISTS fr_employment_contracts CASCADE;
DROP TABLE IF EXISTS fr_dsn_employees CASCADE;
DROP TABLE IF EXISTS fr_dsn_declarations CASCADE;
DROP TABLE IF EXISTS fr_fec_entries CASCADE;
DROP TABLE IF EXISTS fr_fec_exports CASCADE;
DROP TABLE IF EXISTS fr_vat_declarations CASCADE;
DROP TABLE IF EXISTS fr_vat_rates CASCADE;
DROP TABLE IF EXISTS fr_pcg_accounts CASCADE;

-- Autoconfig Tables (7 tables)
DROP TABLE IF EXISTS autoconfig_logs CASCADE;
DROP TABLE IF EXISTS autoconfig_rules CASCADE;
DROP TABLE IF EXISTS autoconfig_offboarding CASCADE;
DROP TABLE IF EXISTS autoconfig_onboarding CASCADE;
DROP TABLE IF EXISTS autoconfig_permission_overrides CASCADE;
DROP TABLE IF EXISTS autoconfig_profile_assignments CASCADE;
DROP TABLE IF EXISTS autoconfig_job_profiles CASCADE;

-- =============================================================================
-- STEP 2: HR Tables - Alter column only (table already uses UUID PK)
-- =============================================================================

-- The hr_employees table already uses UUID PK, only need to alter user_id column
ALTER TABLE IF EXISTS hr_employees
    ALTER COLUMN user_id TYPE UUID USING user_id::text::uuid;

-- =============================================================================
-- STEP 3: Tables will be recreated by SQLAlchemy Base.metadata.create_all()
-- =============================================================================

-- The Python application will recreate all dropped tables with correct UUID types
-- when Base.metadata.create_all() is called at startup.

COMMIT;

-- =============================================================================
-- POST-MIGRATION: Run the following Python code to recreate tables:
-- =============================================================================
--
-- from app.core.database import engine, Base
-- from app.modules.stripe_integration.models import *
-- from app.modules.country_packs.models import *
-- from app.modules.country_packs.france.models import *
-- from app.modules.autoconfig.models import *
-- from app.modules.hr.models import *
--
-- Base.metadata.create_all(bind=engine)
--
-- =============================================================================
