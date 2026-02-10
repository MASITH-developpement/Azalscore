-- AZALS - ROLLBACK Migration Production Module (M6)
-- Annule la creation des tables de gestion de production

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS trigger_maint_updated_at ON production_maintenance_schedules;
    DROP TRIGGER IF EXISTS trigger_plan_updated_at ON production_plans;
    DROP TRIGGER IF EXISTS trigger_wo_updated_at ON production_work_orders;
    DROP TRIGGER IF EXISTS trigger_mo_updated_at ON production_manufacturing_orders;
    DROP TRIGGER IF EXISTS trigger_bom_updated_at ON production_bom;
    DROP TRIGGER IF EXISTS trigger_routing_updated_at ON production_routings;
    DROP TRIGGER IF EXISTS trigger_wc_updated_at ON production_work_centers;

    -- Drop function
    DROP FUNCTION IF EXISTS update_production_updated_at();

    -- Drop indexes for production_maintenance_schedules
    DROP INDEX IF EXISTS idx_maint_next;
    DROP INDEX IF EXISTS idx_maint_wc;

    -- Drop indexes for production_plan_lines
    DROP INDEX IF EXISTS idx_plan_line_product;
    DROP INDEX IF EXISTS idx_plan_line;

    -- Drop indexes for production_plans
    DROP INDEX IF EXISTS idx_plan_dates;
    DROP INDEX IF EXISTS idx_plan_tenant;

    -- Drop indexes for production_scraps
    DROP INDEX IF EXISTS idx_scrap_reason;
    DROP INDEX IF EXISTS idx_scrap_product;
    DROP INDEX IF EXISTS idx_scrap_mo;

    -- Drop indexes for production_outputs
    DROP INDEX IF EXISTS idx_output_product;
    DROP INDEX IF EXISTS idx_output_mo;

    -- Drop indexes for production_material_consumptions
    DROP INDEX IF EXISTS idx_consumption_product;
    DROP INDEX IF EXISTS idx_consumption_mo;

    -- Drop indexes for production_wo_time_entries
    DROP INDEX IF EXISTS idx_wo_time;

    -- Drop indexes for production_work_orders
    DROP INDEX IF EXISTS idx_wo_wc;
    DROP INDEX IF EXISTS idx_wo_mo;

    -- Drop indexes for production_manufacturing_orders
    DROP INDEX IF EXISTS idx_mo_dates;
    DROP INDEX IF EXISTS idx_mo_product;
    DROP INDEX IF EXISTS idx_mo_status;
    DROP INDEX IF EXISTS idx_mo_tenant;

    -- Drop indexes for production_bom_lines
    DROP INDEX IF EXISTS idx_bom_line;

    -- Drop indexes for production_bom
    DROP INDEX IF EXISTS idx_bom_product;
    DROP INDEX IF EXISTS idx_bom_tenant;

    -- Drop indexes for production_routing_operations
    DROP INDEX IF EXISTS idx_routing_op;

    -- Drop indexes for production_routings
    DROP INDEX IF EXISTS idx_routing_product;
    DROP INDEX IF EXISTS idx_routing_tenant;

    -- Drop indexes for production_wc_capacity
    DROP INDEX IF EXISTS idx_wc_cap_date;

    -- Drop indexes for production_work_centers
    DROP INDEX IF EXISTS idx_wc_status;
    DROP INDEX IF EXISTS idx_wc_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS production_maintenance_schedules CASCADE;
    DROP TABLE IF EXISTS production_plan_lines CASCADE;
    DROP TABLE IF EXISTS production_plans CASCADE;
    DROP TABLE IF EXISTS production_scraps CASCADE;
    DROP TABLE IF EXISTS production_outputs CASCADE;
    DROP TABLE IF EXISTS production_material_consumptions CASCADE;
    DROP TABLE IF EXISTS production_wo_time_entries CASCADE;
    DROP TABLE IF EXISTS production_work_orders CASCADE;
    DROP TABLE IF EXISTS production_manufacturing_orders CASCADE;
    DROP TABLE IF EXISTS production_bom_lines CASCADE;
    DROP TABLE IF EXISTS production_bom CASCADE;
    DROP TABLE IF EXISTS production_routing_operations CASCADE;
    DROP TABLE IF EXISTS production_routings CASCADE;
    DROP TABLE IF EXISTS production_wc_capacity CASCADE;
    DROP TABLE IF EXISTS production_work_centers CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS scrap_reason;
    DROP TYPE IF EXISTS consumption_type;
    DROP TYPE IF EXISTS work_order_status;
    DROP TYPE IF EXISTS mo_priority;
    DROP TYPE IF EXISTS mo_status;
    DROP TYPE IF EXISTS operation_type;
    DROP TYPE IF EXISTS bom_status;
    DROP TYPE IF EXISTS bom_type;
    DROP TYPE IF EXISTS work_center_status;
    DROP TYPE IF EXISTS work_center_type;

    RAISE NOTICE 'Migration 021_production_module rolled back successfully';
END $$;
