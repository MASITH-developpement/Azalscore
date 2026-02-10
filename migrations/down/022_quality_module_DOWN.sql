-- AZALS - ROLLBACK Migration Quality Module (M7)
-- Annule la creation des tables de gestion qualite

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS trg_quality_cert_audits_updated ON quality_certification_audits;
    DROP TRIGGER IF EXISTS trg_quality_certifications_updated ON quality_certifications;
    DROP TRIGGER IF EXISTS trg_quality_indicators_updated ON quality_indicators;
    DROP TRIGGER IF EXISTS trg_quality_claim_actions_updated ON quality_claim_actions;
    DROP TRIGGER IF EXISTS trg_quality_claims_updated ON quality_customer_claims;
    DROP TRIGGER IF EXISTS trg_quality_capa_actions_updated ON quality_capa_actions;
    DROP TRIGGER IF EXISTS trg_quality_capas_updated ON quality_capas;
    DROP TRIGGER IF EXISTS trg_quality_audit_findings_updated ON quality_audit_findings;
    DROP TRIGGER IF EXISTS trg_quality_audits_updated ON quality_audits;
    DROP TRIGGER IF EXISTS trg_quality_controls_updated ON quality_controls;
    DROP TRIGGER IF EXISTS trg_quality_control_templates_updated ON quality_control_templates;
    DROP TRIGGER IF EXISTS trg_quality_nc_actions_updated ON quality_nc_actions;
    DROP TRIGGER IF EXISTS trg_quality_nc_updated ON quality_non_conformances;

    -- Drop function
    DROP FUNCTION IF EXISTS update_quality_timestamp();

    -- Drop foreign key constraints added after table creation
    ALTER TABLE IF EXISTS quality_non_conformances DROP CONSTRAINT IF EXISTS fk_nc_capa;
    ALTER TABLE IF EXISTS quality_audit_findings DROP CONSTRAINT IF EXISTS fk_finding_capa;

    -- Drop indexes for quality_certification_audits
    DROP INDEX IF EXISTS idx_cert_audit_date;
    DROP INDEX IF EXISTS idx_cert_audit_cert;

    -- Drop indexes for quality_certifications
    DROP INDEX IF EXISTS idx_cert_status;
    DROP INDEX IF EXISTS idx_cert_code;
    DROP INDEX IF EXISTS idx_cert_tenant;

    -- Drop indexes for quality_indicator_measurements
    DROP INDEX IF EXISTS idx_qim_date;
    DROP INDEX IF EXISTS idx_qim_indicator;

    -- Drop indexes for quality_indicators
    DROP INDEX IF EXISTS idx_qi_code;
    DROP INDEX IF EXISTS idx_qi_tenant;

    -- Drop indexes for quality_claim_actions
    DROP INDEX IF EXISTS idx_claim_action_claim;

    -- Drop indexes for quality_customer_claims
    DROP INDEX IF EXISTS idx_claim_date;
    DROP INDEX IF EXISTS idx_claim_customer;
    DROP INDEX IF EXISTS idx_claim_status;
    DROP INDEX IF EXISTS idx_claim_number;
    DROP INDEX IF EXISTS idx_claim_tenant;

    -- Drop indexes for quality_capa_actions
    DROP INDEX IF EXISTS idx_capa_action_status;
    DROP INDEX IF EXISTS idx_capa_action_capa;

    -- Drop indexes for quality_capas
    DROP INDEX IF EXISTS idx_capa_status;
    DROP INDEX IF EXISTS idx_capa_type;
    DROP INDEX IF EXISTS idx_capa_number;
    DROP INDEX IF EXISTS idx_capa_tenant;

    -- Drop indexes for quality_audit_findings
    DROP INDEX IF EXISTS idx_finding_severity;
    DROP INDEX IF EXISTS idx_finding_audit;

    -- Drop indexes for quality_audits
    DROP INDEX IF EXISTS idx_audit_date;
    DROP INDEX IF EXISTS idx_audit_status;
    DROP INDEX IF EXISTS idx_audit_type;
    DROP INDEX IF EXISTS idx_audit_number;
    DROP INDEX IF EXISTS idx_audit_tenant;

    -- Drop indexes for quality_control_lines
    DROP INDEX IF EXISTS idx_qcl_control;

    -- Drop indexes for quality_controls
    DROP INDEX IF EXISTS idx_qc_date;
    DROP INDEX IF EXISTS idx_qc_status;
    DROP INDEX IF EXISTS idx_qc_type;
    DROP INDEX IF EXISTS idx_qc_number;
    DROP INDEX IF EXISTS idx_qc_tenant;

    -- Drop indexes for quality_control_template_items
    DROP INDEX IF EXISTS idx_qcti_template;

    -- Drop indexes for quality_control_templates
    DROP INDEX IF EXISTS idx_qct_code;
    DROP INDEX IF EXISTS idx_qct_tenant;

    -- Drop indexes for quality_nc_actions
    DROP INDEX IF EXISTS idx_nc_action_status;
    DROP INDEX IF EXISTS idx_nc_action_nc;

    -- Drop indexes for quality_non_conformances
    DROP INDEX IF EXISTS idx_nc_detected;
    DROP INDEX IF EXISTS idx_nc_severity;
    DROP INDEX IF EXISTS idx_nc_status;
    DROP INDEX IF EXISTS idx_nc_type;
    DROP INDEX IF EXISTS idx_nc_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS quality_certification_audits CASCADE;
    DROP TABLE IF EXISTS quality_certifications CASCADE;
    DROP TABLE IF EXISTS quality_indicator_measurements CASCADE;
    DROP TABLE IF EXISTS quality_indicators CASCADE;
    DROP TABLE IF EXISTS quality_claim_actions CASCADE;
    DROP TABLE IF EXISTS quality_customer_claims CASCADE;
    DROP TABLE IF EXISTS quality_capa_actions CASCADE;
    DROP TABLE IF EXISTS quality_audit_findings CASCADE;
    DROP TABLE IF EXISTS quality_audits CASCADE;
    DROP TABLE IF EXISTS quality_control_lines CASCADE;
    DROP TABLE IF EXISTS quality_controls CASCADE;
    DROP TABLE IF EXISTS quality_control_template_items CASCADE;
    DROP TABLE IF EXISTS quality_control_templates CASCADE;
    DROP TABLE IF EXISTS quality_nc_actions CASCADE;
    DROP TABLE IF EXISTS quality_capas CASCADE;
    DROP TABLE IF EXISTS quality_non_conformances CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS certification_status;
    DROP TYPE IF EXISTS claim_status;
    DROP TYPE IF EXISTS capa_status;
    DROP TYPE IF EXISTS capa_type;
    DROP TYPE IF EXISTS finding_severity;
    DROP TYPE IF EXISTS audit_status;
    DROP TYPE IF EXISTS audit_type;
    DROP TYPE IF EXISTS control_result;
    DROP TYPE IF EXISTS control_status;
    DROP TYPE IF EXISTS control_type;
    DROP TYPE IF EXISTS non_conformance_severity;
    DROP TYPE IF EXISTS non_conformance_status;
    DROP TYPE IF EXISTS non_conformance_type;

    RAISE NOTICE 'Migration 022_quality_module rolled back successfully';
END $$;
