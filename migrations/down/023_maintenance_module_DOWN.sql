-- AZALS - ROLLBACK Migration Maintenance Module (M8 - GMAO)
-- Annule la creation des tables de gestion de maintenance

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS trg_maintenance_contracts_updated ON maintenance_contracts;
    DROP TRIGGER IF EXISTS trg_maintenance_spare_parts_updated ON maintenance_spare_parts;
    DROP TRIGGER IF EXISTS trg_maintenance_failures_updated ON maintenance_failures;
    DROP TRIGGER IF EXISTS trg_maintenance_work_orders_updated ON maintenance_work_orders;
    DROP TRIGGER IF EXISTS trg_maintenance_plans_updated ON maintenance_plans;
    DROP TRIGGER IF EXISTS trg_maintenance_assets_updated ON maintenance_assets;

    -- Drop function
    DROP FUNCTION IF EXISTS maintenance_update_timestamp();

    -- Drop indexes for maintenance_kpis
    DROP INDEX IF EXISTS idx_mkpi_period;
    DROP INDEX IF EXISTS idx_mkpi_asset;
    DROP INDEX IF EXISTS idx_mkpi_tenant;

    -- Drop indexes for maintenance_contracts
    DROP INDEX IF EXISTS idx_mcontract_code;
    DROP INDEX IF EXISTS idx_mcontract_tenant;

    -- Drop indexes for maintenance_part_requests
    DROP INDEX IF EXISTS idx_part_req_wo;
    DROP INDEX IF EXISTS idx_part_req_tenant;

    -- Drop indexes for maintenance_spare_part_stock
    DROP INDEX IF EXISTS idx_spare_stock_part;

    -- Drop indexes for maintenance_spare_parts
    DROP INDEX IF EXISTS idx_spare_code;
    DROP INDEX IF EXISTS idx_spare_tenant;

    -- Drop indexes for maintenance_failure_causes
    DROP INDEX IF EXISTS idx_failure_cause_failure;

    -- Drop indexes for maintenance_failures
    DROP INDEX IF EXISTS idx_failure_date;
    DROP INDEX IF EXISTS idx_failure_asset;
    DROP INDEX IF EXISTS idx_failure_tenant;

    -- Drop indexes for maintenance_wo_parts
    DROP INDEX IF EXISTS idx_wo_part_wo;

    -- Drop indexes for maintenance_wo_labor
    DROP INDEX IF EXISTS idx_wo_labor_wo;

    -- Drop indexes for maintenance_wo_tasks
    DROP INDEX IF EXISTS idx_wo_task_wo;

    -- Drop indexes for maintenance_work_orders
    DROP INDEX IF EXISTS idx_wo_scheduled;
    DROP INDEX IF EXISTS idx_wo_priority;
    DROP INDEX IF EXISTS idx_wo_status;
    DROP INDEX IF EXISTS idx_wo_asset;
    DROP INDEX IF EXISTS idx_wo_number;
    DROP INDEX IF EXISTS idx_wo_tenant;

    -- Drop indexes for maintenance_plan_tasks
    DROP INDEX IF EXISTS idx_mplan_task_plan;

    -- Drop indexes for maintenance_plans
    DROP INDEX IF EXISTS idx_mplan_code;
    DROP INDEX IF EXISTS idx_mplan_tenant;

    -- Drop indexes for maintenance_meter_readings
    DROP INDEX IF EXISTS idx_reading_date;
    DROP INDEX IF EXISTS idx_reading_meter;

    -- Drop indexes for maintenance_asset_meters
    DROP INDEX IF EXISTS idx_meter_asset;

    -- Drop indexes for maintenance_asset_documents
    DROP INDEX IF EXISTS idx_asset_doc_asset;

    -- Drop indexes for maintenance_asset_components
    DROP INDEX IF EXISTS idx_component_asset;

    -- Drop indexes for maintenance_assets
    DROP INDEX IF EXISTS idx_asset_location;
    DROP INDEX IF EXISTS idx_asset_status;
    DROP INDEX IF EXISTS idx_asset_category;
    DROP INDEX IF EXISTS idx_asset_code;
    DROP INDEX IF EXISTS idx_asset_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS maintenance_kpis CASCADE;
    DROP TABLE IF EXISTS maintenance_contracts CASCADE;
    DROP TABLE IF EXISTS maintenance_part_requests CASCADE;
    DROP TABLE IF EXISTS maintenance_spare_part_stock CASCADE;
    DROP TABLE IF EXISTS maintenance_spare_parts CASCADE;
    DROP TABLE IF EXISTS maintenance_failure_causes CASCADE;
    DROP TABLE IF EXISTS maintenance_failures CASCADE;
    DROP TABLE IF EXISTS maintenance_wo_parts CASCADE;
    DROP TABLE IF EXISTS maintenance_wo_labor CASCADE;
    DROP TABLE IF EXISTS maintenance_wo_tasks CASCADE;
    DROP TABLE IF EXISTS maintenance_work_orders CASCADE;
    DROP TABLE IF EXISTS maintenance_plan_tasks CASCADE;
    DROP TABLE IF EXISTS maintenance_plans CASCADE;
    DROP TABLE IF EXISTS maintenance_meter_readings CASCADE;
    DROP TABLE IF EXISTS maintenance_asset_meters CASCADE;
    DROP TABLE IF EXISTS maintenance_asset_documents CASCADE;
    DROP TABLE IF EXISTS maintenance_asset_components CASCADE;
    DROP TABLE IF EXISTS maintenance_assets CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS contract_status_maint;
    DROP TYPE IF EXISTS contract_type_maint;
    DROP TYPE IF EXISTS part_request_status;
    DROP TYPE IF EXISTS failure_type;
    DROP TYPE IF EXISTS work_order_priority;
    DROP TYPE IF EXISTS work_order_status;
    DROP TYPE IF EXISTS maintenance_type;
    DROP TYPE IF EXISTS asset_criticality;
    DROP TYPE IF EXISTS asset_status;
    DROP TYPE IF EXISTS asset_category;

    RAISE NOTICE 'Migration 023_maintenance_module rolled back successfully';
END $$;
