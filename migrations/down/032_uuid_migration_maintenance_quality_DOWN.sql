-- AZALS - ROLLBACK Migration UUID pour Maintenance et Quality
-- Annule la creation des tables UUID pour les modules Maintenance et Quality

DO $$
BEGIN
    -- ============================================================================
    -- Drop Quality triggers first
    -- ============================================================================
    DROP TRIGGER IF EXISTS trg_quality_certification_audits_updated ON quality_certification_audits;
    DROP TRIGGER IF EXISTS trg_quality_certifications_updated ON quality_certifications;
    DROP TRIGGER IF EXISTS trg_quality_indicators_updated ON quality_indicators;
    DROP TRIGGER IF EXISTS trg_quality_claim_actions_updated ON quality_claim_actions;
    DROP TRIGGER IF EXISTS trg_quality_customer_claims_updated ON quality_customer_claims;
    DROP TRIGGER IF EXISTS trg_quality_audit_findings_updated ON quality_audit_findings;
    DROP TRIGGER IF EXISTS trg_quality_audits_updated ON quality_audits;
    DROP TRIGGER IF EXISTS trg_quality_controls_updated ON quality_controls;
    DROP TRIGGER IF EXISTS trg_quality_control_template_items_updated ON quality_control_template_items;
    DROP TRIGGER IF EXISTS trg_quality_control_templates_updated ON quality_control_templates;
    DROP TRIGGER IF EXISTS trg_quality_nc_actions_updated ON quality_nc_actions;
    DROP TRIGGER IF EXISTS trg_quality_non_conformances_updated ON quality_non_conformances;
    DROP TRIGGER IF EXISTS trg_quality_capa_actions_updated ON quality_capa_actions;
    DROP TRIGGER IF EXISTS trg_quality_capas_updated ON quality_capas;

    -- ============================================================================
    -- Drop Maintenance triggers
    -- ============================================================================
    DROP TRIGGER IF EXISTS trg_maintenance_contracts_updated ON maintenance_contracts;
    DROP TRIGGER IF EXISTS trg_maintenance_part_requests_updated ON maintenance_part_requests;
    DROP TRIGGER IF EXISTS trg_maintenance_wo_tasks_updated ON maintenance_wo_tasks;
    DROP TRIGGER IF EXISTS trg_maintenance_work_orders_updated ON maintenance_work_orders;
    DROP TRIGGER IF EXISTS trg_maintenance_failures_updated ON maintenance_failures;
    DROP TRIGGER IF EXISTS trg_maintenance_spare_stock_updated ON maintenance_spare_part_stock;
    DROP TRIGGER IF EXISTS trg_maintenance_spare_parts_updated ON maintenance_spare_parts;
    DROP TRIGGER IF EXISTS trg_maintenance_plan_tasks_updated ON maintenance_plan_tasks;
    DROP TRIGGER IF EXISTS trg_maintenance_plans_updated ON maintenance_plans;
    DROP TRIGGER IF EXISTS trg_maintenance_meters_updated ON maintenance_asset_meters;
    DROP TRIGGER IF EXISTS trg_maintenance_components_updated ON maintenance_asset_components;
    DROP TRIGGER IF EXISTS trg_maintenance_assets_updated ON maintenance_assets;

    -- Drop function (shared by all triggers)
    DROP FUNCTION IF EXISTS update_updated_at_column();

    -- ============================================================================
    -- Drop Quality indexes
    -- ============================================================================
    DROP INDEX IF EXISTS idx_cert_audit_date;
    DROP INDEX IF EXISTS idx_cert_audit_cert;
    DROP INDEX IF EXISTS idx_cert_audit_tenant;
    DROP INDEX IF EXISTS idx_cert_status;
    DROP INDEX IF EXISTS idx_cert_code;
    DROP INDEX IF EXISTS idx_cert_tenant;
    DROP INDEX IF EXISTS idx_qim_date;
    DROP INDEX IF EXISTS idx_qim_indicator;
    DROP INDEX IF EXISTS idx_qim_tenant;
    DROP INDEX IF EXISTS idx_qi_code;
    DROP INDEX IF EXISTS idx_qi_tenant;
    DROP INDEX IF EXISTS idx_claim_action_claim;
    DROP INDEX IF EXISTS idx_claim_action_tenant;
    DROP INDEX IF EXISTS idx_claim_date;
    DROP INDEX IF EXISTS idx_claim_customer;
    DROP INDEX IF EXISTS idx_claim_status;
    DROP INDEX IF EXISTS idx_claim_number;
    DROP INDEX IF EXISTS idx_claim_tenant;
    DROP INDEX IF EXISTS idx_finding_severity;
    DROP INDEX IF EXISTS idx_finding_audit;
    DROP INDEX IF EXISTS idx_finding_tenant;
    DROP INDEX IF EXISTS idx_audit_date;
    DROP INDEX IF EXISTS idx_audit_status;
    DROP INDEX IF EXISTS idx_audit_type;
    DROP INDEX IF EXISTS idx_audit_number;
    DROP INDEX IF EXISTS idx_audit_tenant;
    DROP INDEX IF EXISTS idx_qcl_control;
    DROP INDEX IF EXISTS idx_qcl_tenant;
    DROP INDEX IF EXISTS idx_qc_date;
    DROP INDEX IF EXISTS idx_qc_status;
    DROP INDEX IF EXISTS idx_qc_type;
    DROP INDEX IF EXISTS idx_qc_number;
    DROP INDEX IF EXISTS idx_qc_tenant;
    DROP INDEX IF EXISTS idx_qcti_template;
    DROP INDEX IF EXISTS idx_qcti_tenant;
    DROP INDEX IF EXISTS idx_qct_code;
    DROP INDEX IF EXISTS idx_qct_tenant;
    DROP INDEX IF EXISTS idx_nc_action_status;
    DROP INDEX IF EXISTS idx_nc_action_nc;
    DROP INDEX IF EXISTS idx_nc_action_tenant;
    DROP INDEX IF EXISTS idx_nc_detected;
    DROP INDEX IF EXISTS idx_nc_severity;
    DROP INDEX IF EXISTS idx_nc_status;
    DROP INDEX IF EXISTS idx_nc_type;
    DROP INDEX IF EXISTS idx_nc_tenant;
    DROP INDEX IF EXISTS idx_capa_action_status;
    DROP INDEX IF EXISTS idx_capa_action_capa;
    DROP INDEX IF EXISTS idx_capa_action_tenant;
    DROP INDEX IF EXISTS idx_capa_status;
    DROP INDEX IF EXISTS idx_capa_type;
    DROP INDEX IF EXISTS idx_capa_number;
    DROP INDEX IF EXISTS idx_capa_tenant;

    -- ============================================================================
    -- Drop Maintenance indexes
    -- ============================================================================
    DROP INDEX IF EXISTS idx_mkpi_period;
    DROP INDEX IF EXISTS idx_mkpi_asset;
    DROP INDEX IF EXISTS idx_mkpi_tenant;
    DROP INDEX IF EXISTS idx_mcontract_code;
    DROP INDEX IF EXISTS idx_mcontract_tenant;
    DROP INDEX IF EXISTS idx_part_req_wo;
    DROP INDEX IF EXISTS idx_part_req_tenant;
    DROP INDEX IF EXISTS idx_wo_part_wo;
    DROP INDEX IF EXISTS idx_wo_part_tenant;
    DROP INDEX IF EXISTS idx_wo_labor_wo;
    DROP INDEX IF EXISTS idx_wo_labor_tenant;
    DROP INDEX IF EXISTS idx_wo_task_wo;
    DROP INDEX IF EXISTS idx_wo_task_tenant;
    DROP INDEX IF EXISTS idx_wo_scheduled;
    DROP INDEX IF EXISTS idx_wo_priority;
    DROP INDEX IF EXISTS idx_wo_status;
    DROP INDEX IF EXISTS idx_wo_asset;
    DROP INDEX IF EXISTS idx_wo_number;
    DROP INDEX IF EXISTS idx_wo_tenant;
    DROP INDEX IF EXISTS idx_failure_cause_failure;
    DROP INDEX IF EXISTS idx_failure_cause_tenant;
    DROP INDEX IF EXISTS idx_failure_date;
    DROP INDEX IF EXISTS idx_failure_asset;
    DROP INDEX IF EXISTS idx_failure_tenant;
    DROP INDEX IF EXISTS idx_spare_stock_part;
    DROP INDEX IF EXISTS idx_spare_stock_tenant;
    DROP INDEX IF EXISTS idx_spare_code;
    DROP INDEX IF EXISTS idx_spare_tenant;
    DROP INDEX IF EXISTS idx_mplan_task_plan;
    DROP INDEX IF EXISTS idx_mplan_task_tenant;
    DROP INDEX IF EXISTS idx_mplan_code;
    DROP INDEX IF EXISTS idx_mplan_tenant;
    DROP INDEX IF EXISTS idx_reading_date;
    DROP INDEX IF EXISTS idx_reading_meter;
    DROP INDEX IF EXISTS idx_reading_tenant;
    DROP INDEX IF EXISTS idx_meter_asset;
    DROP INDEX IF EXISTS idx_meter_tenant;
    DROP INDEX IF EXISTS idx_asset_doc_asset;
    DROP INDEX IF EXISTS idx_asset_doc_tenant;
    DROP INDEX IF EXISTS idx_component_asset;
    DROP INDEX IF EXISTS idx_component_tenant;
    DROP INDEX IF EXISTS idx_asset_location;
    DROP INDEX IF EXISTS idx_asset_status;
    DROP INDEX IF EXISTS idx_asset_category;
    DROP INDEX IF EXISTS idx_asset_code;
    DROP INDEX IF EXISTS idx_asset_tenant;

    -- ============================================================================
    -- Drop Quality tables in reverse order of dependencies
    -- ============================================================================
    DROP TABLE IF EXISTS quality_certification_audits CASCADE;
    DROP TABLE IF EXISTS quality_certifications CASCADE;
    DROP TABLE IF EXISTS quality_indicator_measurements CASCADE;
    DROP TABLE IF EXISTS quality_indicators CASCADE;
    DROP TABLE IF EXISTS quality_claim_actions CASCADE;
    DROP TABLE IF EXISTS quality_customer_claims CASCADE;
    DROP TABLE IF EXISTS quality_audit_findings CASCADE;
    DROP TABLE IF EXISTS quality_audits CASCADE;
    DROP TABLE IF EXISTS quality_control_lines CASCADE;
    DROP TABLE IF EXISTS quality_controls CASCADE;
    DROP TABLE IF EXISTS quality_control_template_items CASCADE;
    DROP TABLE IF EXISTS quality_control_templates CASCADE;
    DROP TABLE IF EXISTS quality_nc_actions CASCADE;
    DROP TABLE IF EXISTS quality_non_conformances CASCADE;
    DROP TABLE IF EXISTS quality_capa_actions CASCADE;
    DROP TABLE IF EXISTS quality_capas CASCADE;

    -- ============================================================================
    -- Drop Maintenance tables in reverse order of dependencies
    -- ============================================================================
    DROP TABLE IF EXISTS maintenance_kpis CASCADE;
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
    DROP TABLE IF EXISTS maintenance_contracts CASCADE;

    -- Drop helper function
    DROP FUNCTION IF EXISTS gen_random_uuid_v4();

    -- Note: Do not drop uuid-ossp extension as it may be used elsewhere

    RAISE NOTICE 'Migration 032_uuid_migration_maintenance_quality rolled back successfully';
END $$;
