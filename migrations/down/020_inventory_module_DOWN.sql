-- AZALS - ROLLBACK Migration INVENTORY MODULE
-- Annule la creation du module stock/inventaire (M5)

DO $$
BEGIN
    -- Drop triggers (created by dynamic loop in UP migration)
    DROP TRIGGER IF EXISTS trigger_update_inventory_categories_updated_at ON inventory_categories;
    DROP TRIGGER IF EXISTS trigger_update_inventory_warehouses_updated_at ON inventory_warehouses;
    DROP TRIGGER IF EXISTS trigger_update_inventory_locations_updated_at ON inventory_locations;
    DROP TRIGGER IF EXISTS trigger_update_inventory_products_updated_at ON inventory_products;
    DROP TRIGGER IF EXISTS trigger_update_inventory_stock_levels_updated_at ON inventory_stock_levels;
    DROP TRIGGER IF EXISTS trigger_update_inventory_lots_updated_at ON inventory_lots;
    DROP TRIGGER IF EXISTS trigger_update_inventory_serial_numbers_updated_at ON inventory_serial_numbers;
    DROP TRIGGER IF EXISTS trigger_update_inventory_movements_updated_at ON inventory_movements;
    DROP TRIGGER IF EXISTS trigger_update_inventory_counts_updated_at ON inventory_counts;
    DROP TRIGGER IF EXISTS trigger_update_inventory_pickings_updated_at ON inventory_pickings;
    DROP TRIGGER IF EXISTS trigger_update_inventory_replenishment_rules_updated_at ON inventory_replenishment_rules;

    -- Drop function
    DROP FUNCTION IF EXISTS update_inventory_updated_at();

    -- Drop indexes for inventory_valuations
    DROP INDEX IF EXISTS idx_valuations_tenant;
    DROP INDEX IF EXISTS idx_valuations_date;
    DROP INDEX IF EXISTS idx_valuations_warehouse;

    -- Drop indexes for inventory_replenishment_rules
    DROP INDEX IF EXISTS idx_replenishment_tenant;
    DROP INDEX IF EXISTS idx_replenishment_product;

    -- Drop indexes for inventory_picking_lines
    DROP INDEX IF EXISTS idx_picking_lines_picking;
    DROP INDEX IF EXISTS idx_picking_lines_tenant;
    DROP INDEX IF EXISTS idx_picking_lines_product;

    -- Drop indexes for inventory_pickings
    DROP INDEX IF EXISTS idx_pickings_tenant;
    DROP INDEX IF EXISTS idx_pickings_status;
    DROP INDEX IF EXISTS idx_pickings_assigned;
    DROP INDEX IF EXISTS idx_pickings_reference;

    -- Drop indexes for inventory_count_lines
    DROP INDEX IF EXISTS idx_count_lines_count;
    DROP INDEX IF EXISTS idx_count_lines_tenant;
    DROP INDEX IF EXISTS idx_count_lines_product;

    -- Drop indexes for inventory_counts
    DROP INDEX IF EXISTS idx_counts_tenant;
    DROP INDEX IF EXISTS idx_counts_status;
    DROP INDEX IF EXISTS idx_counts_warehouse;

    -- Drop indexes for inventory_movement_lines
    DROP INDEX IF EXISTS idx_movement_lines_movement;
    DROP INDEX IF EXISTS idx_movement_lines_tenant;
    DROP INDEX IF EXISTS idx_movement_lines_product;

    -- Drop indexes for inventory_movements
    DROP INDEX IF EXISTS idx_movements_tenant;
    DROP INDEX IF EXISTS idx_movements_type;
    DROP INDEX IF EXISTS idx_movements_status;
    DROP INDEX IF EXISTS idx_movements_date;
    DROP INDEX IF EXISTS idx_movements_reference;

    -- Drop indexes for inventory_serial_numbers
    DROP INDEX IF EXISTS idx_serials_tenant;
    DROP INDEX IF EXISTS idx_serials_product;
    DROP INDEX IF EXISTS idx_serials_status;

    -- Drop indexes for inventory_lots
    DROP INDEX IF EXISTS idx_lots_tenant;
    DROP INDEX IF EXISTS idx_lots_product;
    DROP INDEX IF EXISTS idx_lots_expiry;
    DROP INDEX IF EXISTS idx_lots_status;

    -- Drop indexes for inventory_stock_levels
    DROP INDEX IF EXISTS idx_stock_levels_tenant;
    DROP INDEX IF EXISTS idx_stock_levels_product;
    DROP INDEX IF EXISTS idx_stock_levels_warehouse;

    -- Drop indexes for inventory_products
    DROP INDEX IF EXISTS idx_products_tenant;
    DROP INDEX IF EXISTS idx_products_category;
    DROP INDEX IF EXISTS idx_products_status;
    DROP INDEX IF EXISTS idx_products_barcode;
    DROP INDEX IF EXISTS idx_products_sku;

    -- Drop indexes for inventory_locations
    DROP INDEX IF EXISTS idx_locations_tenant;
    DROP INDEX IF EXISTS idx_locations_warehouse;
    DROP INDEX IF EXISTS idx_locations_barcode;

    -- Drop indexes for inventory_warehouses
    DROP INDEX IF EXISTS idx_warehouses_tenant;

    -- Drop indexes for inventory_categories
    DROP INDEX IF EXISTS idx_categories_tenant;
    DROP INDEX IF EXISTS idx_categories_parent;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS inventory_valuations CASCADE;
    DROP TABLE IF EXISTS inventory_replenishment_rules CASCADE;
    DROP TABLE IF EXISTS inventory_picking_lines CASCADE;
    DROP TABLE IF EXISTS inventory_pickings CASCADE;
    DROP TABLE IF EXISTS inventory_count_lines CASCADE;
    DROP TABLE IF EXISTS inventory_counts CASCADE;
    DROP TABLE IF EXISTS inventory_movement_lines CASCADE;
    DROP TABLE IF EXISTS inventory_movements CASCADE;
    DROP TABLE IF EXISTS inventory_serial_numbers CASCADE;
    DROP TABLE IF EXISTS inventory_lots CASCADE;
    DROP TABLE IF EXISTS inventory_stock_levels CASCADE;
    DROP TABLE IF EXISTS inventory_products CASCADE;
    DROP TABLE IF EXISTS inventory_locations CASCADE;
    DROP TABLE IF EXISTS inventory_warehouses CASCADE;
    DROP TABLE IF EXISTS inventory_categories CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS picking_status;
    DROP TYPE IF EXISTS valuation_method;
    DROP TYPE IF EXISTS lot_status;
    DROP TYPE IF EXISTS inventory_status;
    DROP TYPE IF EXISTS movement_status;
    DROP TYPE IF EXISTS movement_type;
    DROP TYPE IF EXISTS location_type;
    DROP TYPE IF EXISTS warehouse_type;
    DROP TYPE IF EXISTS product_status;
    DROP TYPE IF EXISTS product_type;

    RAISE NOTICE 'Migration 020_inventory_module rolled back successfully';
END $$;
