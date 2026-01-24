-- AZALS - ROLLBACK Migration COMMERCIAL MODULE
-- Annule la creation du module commercial CRM+Ventes (M1)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_customers_updated_at ON customers;
    DROP TRIGGER IF EXISTS trigger_contacts_updated_at ON customer_contacts;
    DROP TRIGGER IF EXISTS trigger_opportunities_updated_at ON opportunities;
    DROP TRIGGER IF EXISTS trigger_documents_updated_at ON commercial_documents;
    DROP TRIGGER IF EXISTS trigger_pipeline_updated_at ON pipeline_stages;
    DROP TRIGGER IF EXISTS trigger_products_updated_at ON products;

    -- Drop function
    DROP FUNCTION IF EXISTS update_customers_timestamp();

    -- Drop indexes for products
    DROP INDEX IF EXISTS ix_products_tenant_code;
    DROP INDEX IF EXISTS ix_products_tenant_category;
    DROP INDEX IF EXISTS ix_products_tenant_active;

    -- Drop indexes for pipeline_stages
    DROP INDEX IF EXISTS ix_pipeline_tenant_order;

    -- Drop indexes for customer_activities
    DROP INDEX IF EXISTS ix_activities_tenant_customer;
    DROP INDEX IF EXISTS ix_activities_tenant_opportunity;
    DROP INDEX IF EXISTS ix_activities_tenant_date;
    DROP INDEX IF EXISTS ix_activities_tenant_assigned;

    -- Drop indexes for payments
    DROP INDEX IF EXISTS ix_payments_tenant_document;
    DROP INDEX IF EXISTS ix_payments_tenant_date;

    -- Drop indexes for document_lines
    DROP INDEX IF EXISTS ix_doc_lines_tenant_document;

    -- Drop indexes for commercial_documents
    DROP INDEX IF EXISTS ix_documents_tenant_number;
    DROP INDEX IF EXISTS ix_documents_tenant_customer;
    DROP INDEX IF EXISTS ix_documents_tenant_type;
    DROP INDEX IF EXISTS ix_documents_tenant_status;
    DROP INDEX IF EXISTS ix_documents_tenant_date;

    -- Drop indexes for opportunities
    DROP INDEX IF EXISTS ix_opportunities_tenant_code;
    DROP INDEX IF EXISTS ix_opportunities_tenant_status;
    DROP INDEX IF EXISTS ix_opportunities_tenant_customer;
    DROP INDEX IF EXISTS ix_opportunities_tenant_assigned;
    DROP INDEX IF EXISTS ix_opportunities_tenant_close;

    -- Drop indexes for customer_contacts
    DROP INDEX IF EXISTS ix_contacts_tenant_customer;
    DROP INDEX IF EXISTS ix_contacts_tenant_email;

    -- Drop indexes for customers
    DROP INDEX IF EXISTS ix_customers_tenant_code;
    DROP INDEX IF EXISTS ix_customers_tenant_type;
    DROP INDEX IF EXISTS ix_customers_tenant_assigned;
    DROP INDEX IF EXISTS ix_customers_tenant_active;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS pipeline_stages CASCADE;
    DROP TABLE IF EXISTS customer_activities CASCADE;
    DROP TABLE IF EXISTS payments CASCADE;
    DROP TABLE IF EXISTS document_lines CASCADE;
    DROP TABLE IF EXISTS commercial_documents CASCADE;
    DROP TABLE IF EXISTS opportunities CASCADE;
    DROP TABLE IF EXISTS customer_contacts CASCADE;
    DROP TABLE IF EXISTS customers CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS activity_type;
    DROP TYPE IF EXISTS payment_terms;
    DROP TYPE IF EXISTS payment_method;
    DROP TYPE IF EXISTS document_status;
    DROP TYPE IF EXISTS document_type;
    DROP TYPE IF EXISTS opportunity_status;
    DROP TYPE IF EXISTS customer_type;

    RAISE NOTICE 'Migration 016_commercial_module rolled back successfully';
END $$;
