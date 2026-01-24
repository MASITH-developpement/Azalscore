-- AZALS - ROLLBACK Migration PROCUREMENT MODULE
-- Annule la creation du module achats (M4)

DO $$
BEGIN
    -- Drop triggers (created by dynamic loop in UP migration)
    DROP TRIGGER IF EXISTS trigger_update_procurement_suppliers_updated_at ON procurement_suppliers;
    DROP TRIGGER IF EXISTS trigger_update_procurement_supplier_contacts_updated_at ON procurement_supplier_contacts;
    DROP TRIGGER IF EXISTS trigger_update_procurement_requisitions_updated_at ON procurement_requisitions;
    DROP TRIGGER IF EXISTS trigger_update_procurement_quotations_updated_at ON procurement_quotations;
    DROP TRIGGER IF EXISTS trigger_update_procurement_orders_updated_at ON procurement_orders;
    DROP TRIGGER IF EXISTS trigger_update_procurement_receipts_updated_at ON procurement_receipts;
    DROP TRIGGER IF EXISTS trigger_update_procurement_invoices_updated_at ON procurement_invoices;

    -- Drop function
    DROP FUNCTION IF EXISTS update_procurement_updated_at();

    -- Drop indexes for procurement_evaluations
    DROP INDEX IF EXISTS idx_evaluations_tenant;
    DROP INDEX IF EXISTS idx_evaluations_supplier;
    DROP INDEX IF EXISTS idx_evaluations_date;

    -- Drop indexes for procurement_payment_allocations
    DROP INDEX IF EXISTS idx_allocations_payment;
    DROP INDEX IF EXISTS idx_allocations_invoice;
    DROP INDEX IF EXISTS idx_allocations_tenant;

    -- Drop indexes for procurement_payments
    DROP INDEX IF EXISTS idx_payments_tenant;
    DROP INDEX IF EXISTS idx_payments_supplier;
    DROP INDEX IF EXISTS idx_payments_date;

    -- Drop indexes for procurement_invoice_lines
    DROP INDEX IF EXISTS idx_invoice_lines_invoice;
    DROP INDEX IF EXISTS idx_invoice_lines_tenant;

    -- Drop indexes for procurement_invoices
    DROP INDEX IF EXISTS idx_purchase_invoices_tenant;
    DROP INDEX IF EXISTS idx_purchase_invoices_supplier;
    DROP INDEX IF EXISTS idx_purchase_invoices_status;
    DROP INDEX IF EXISTS idx_purchase_invoices_due;

    -- Drop indexes for procurement_receipt_lines
    DROP INDEX IF EXISTS idx_receipt_lines_receipt;
    DROP INDEX IF EXISTS idx_receipt_lines_tenant;

    -- Drop indexes for procurement_receipts
    DROP INDEX IF EXISTS idx_receipts_tenant;
    DROP INDEX IF EXISTS idx_receipts_order;
    DROP INDEX IF EXISTS idx_receipts_supplier;

    -- Drop indexes for procurement_order_lines
    DROP INDEX IF EXISTS idx_order_lines_order;
    DROP INDEX IF EXISTS idx_order_lines_tenant;
    DROP INDEX IF EXISTS idx_order_lines_product;

    -- Drop indexes for procurement_orders
    DROP INDEX IF EXISTS idx_orders_tenant;
    DROP INDEX IF EXISTS idx_orders_supplier;
    DROP INDEX IF EXISTS idx_orders_status;
    DROP INDEX IF EXISTS idx_orders_date;

    -- Drop indexes for procurement_quotation_lines
    DROP INDEX IF EXISTS idx_quotation_lines_quotation;
    DROP INDEX IF EXISTS idx_quotation_lines_tenant;

    -- Drop indexes for procurement_quotations
    DROP INDEX IF EXISTS idx_quotations_tenant;
    DROP INDEX IF EXISTS idx_quotations_supplier;
    DROP INDEX IF EXISTS idx_quotations_status;

    -- Drop indexes for procurement_requisition_lines
    DROP INDEX IF EXISTS idx_requisition_lines_requisition;
    DROP INDEX IF EXISTS idx_requisition_lines_tenant;

    -- Drop indexes for procurement_requisitions
    DROP INDEX IF EXISTS idx_requisitions_tenant;
    DROP INDEX IF EXISTS idx_requisitions_status;
    DROP INDEX IF EXISTS idx_requisitions_requester;

    -- Drop indexes for procurement_supplier_contacts
    DROP INDEX IF EXISTS idx_supplier_contacts_tenant;
    DROP INDEX IF EXISTS idx_supplier_contacts_supplier;

    -- Drop indexes for procurement_suppliers
    DROP INDEX IF EXISTS idx_suppliers_tenant;
    DROP INDEX IF EXISTS idx_suppliers_status;
    DROP INDEX IF EXISTS idx_suppliers_category;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS procurement_evaluations CASCADE;
    DROP TABLE IF EXISTS procurement_payment_allocations CASCADE;
    DROP TABLE IF EXISTS procurement_payments CASCADE;
    DROP TABLE IF EXISTS procurement_invoice_lines CASCADE;
    DROP TABLE IF EXISTS procurement_invoices CASCADE;
    DROP TABLE IF EXISTS procurement_receipt_lines CASCADE;
    DROP TABLE IF EXISTS procurement_receipts CASCADE;
    DROP TABLE IF EXISTS procurement_order_lines CASCADE;
    DROP TABLE IF EXISTS procurement_orders CASCADE;
    DROP TABLE IF EXISTS procurement_quotation_lines CASCADE;
    DROP TABLE IF EXISTS procurement_quotations CASCADE;
    DROP TABLE IF EXISTS procurement_requisition_lines CASCADE;
    DROP TABLE IF EXISTS procurement_requisitions CASCADE;
    DROP TABLE IF EXISTS procurement_supplier_contacts CASCADE;
    DROP TABLE IF EXISTS procurement_suppliers CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS quotation_status;
    DROP TYPE IF EXISTS purchase_invoice_status;
    DROP TYPE IF EXISTS receiving_status;
    DROP TYPE IF EXISTS purchase_order_status;
    DROP TYPE IF EXISTS requisition_status;
    DROP TYPE IF EXISTS supplier_type;
    DROP TYPE IF EXISTS supplier_status;

    RAISE NOTICE 'Migration 019_procurement_module rolled back successfully';
END $$;
