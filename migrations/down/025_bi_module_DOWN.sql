-- AZALS - ROLLBACK Migration BI Module (M10)
-- Annule la creation des tables de Business Intelligence

DO $$
BEGIN
    -- Drop triggers first
    DROP TRIGGER IF EXISTS tr_bi_alert_rules_updated ON bi_alert_rules;
    DROP TRIGGER IF EXISTS tr_bi_kpi_targets_updated ON bi_kpi_targets;
    DROP TRIGGER IF EXISTS tr_bi_report_schedules_updated ON bi_report_schedules;
    DROP TRIGGER IF EXISTS tr_bi_reports_updated ON bi_reports;
    DROP TRIGGER IF EXISTS tr_bi_dashboard_widgets_updated ON bi_dashboard_widgets;
    DROP TRIGGER IF EXISTS tr_bi_kpi_definitions_updated ON bi_kpi_definitions;
    DROP TRIGGER IF EXISTS tr_bi_data_queries_updated ON bi_data_queries;
    DROP TRIGGER IF EXISTS tr_bi_data_sources_updated ON bi_data_sources;
    DROP TRIGGER IF EXISTS tr_bi_dashboards_updated ON bi_dashboards;

    -- Drop function
    DROP FUNCTION IF EXISTS bi_update_timestamp();

    -- Drop indexes for bi_export_history
    DROP INDEX IF EXISTS ix_bi_exports_date;
    DROP INDEX IF EXISTS ix_bi_exports_user;

    -- Drop indexes for bi_bookmarks
    DROP INDEX IF EXISTS ix_bi_bookmarks_user;

    -- Drop indexes for bi_alerts
    DROP INDEX IF EXISTS ix_bi_alerts_severity;
    DROP INDEX IF EXISTS ix_bi_alerts_status;
    DROP INDEX IF EXISTS ix_bi_alerts_tenant;

    -- Drop indexes for bi_alert_rules
    DROP INDEX IF EXISTS ix_bi_alert_rules_tenant;

    -- Drop indexes for bi_kpi_targets
    DROP INDEX IF EXISTS ix_bi_kpi_targets_kpi;

    -- Drop indexes for bi_kpi_values
    DROP INDEX IF EXISTS ix_bi_kpi_values_date;
    DROP INDEX IF EXISTS ix_bi_kpi_values_kpi;

    -- Drop indexes for bi_report_executions
    DROP INDEX IF EXISTS ix_bi_executions_date;
    DROP INDEX IF EXISTS ix_bi_executions_status;
    DROP INDEX IF EXISTS ix_bi_executions_report;

    -- Drop indexes for bi_report_schedules
    DROP INDEX IF EXISTS ix_bi_schedules_next_run;
    DROP INDEX IF EXISTS ix_bi_schedules_report;

    -- Drop indexes for bi_reports
    DROP INDEX IF EXISTS ix_bi_reports_tenant;

    -- Drop indexes for bi_widget_filters (no named index in UP)

    -- Drop indexes for bi_dashboard_widgets
    DROP INDEX IF EXISTS ix_bi_widgets_dashboard;

    -- Drop indexes for bi_kpi_definitions
    DROP INDEX IF EXISTS ix_bi_kpis_category;
    DROP INDEX IF EXISTS ix_bi_kpis_tenant;

    -- Drop indexes for bi_data_queries
    DROP INDEX IF EXISTS ix_bi_queries_tenant;

    -- Drop indexes for bi_data_sources
    DROP INDEX IF EXISTS ix_bi_datasources_tenant;

    -- Drop indexes for bi_dashboards
    DROP INDEX IF EXISTS ix_bi_dashboards_owner;
    DROP INDEX IF EXISTS ix_bi_dashboards_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS bi_export_history CASCADE;
    DROP TABLE IF EXISTS bi_bookmarks CASCADE;
    DROP TABLE IF EXISTS bi_alerts CASCADE;
    DROP TABLE IF EXISTS bi_alert_rules CASCADE;
    DROP TABLE IF EXISTS bi_kpi_targets CASCADE;
    DROP TABLE IF EXISTS bi_kpi_values CASCADE;
    DROP TABLE IF EXISTS bi_report_executions CASCADE;
    DROP TABLE IF EXISTS bi_report_schedules CASCADE;
    DROP TABLE IF EXISTS bi_reports CASCADE;
    DROP TABLE IF EXISTS bi_widget_filters CASCADE;
    DROP TABLE IF EXISTS bi_dashboard_widgets CASCADE;
    DROP TABLE IF EXISTS bi_kpi_definitions CASCADE;
    DROP TABLE IF EXISTS bi_data_queries CASCADE;
    DROP TABLE IF EXISTS bi_data_sources CASCADE;
    DROP TABLE IF EXISTS bi_dashboards CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS bi_refresh_frequency;
    DROP TYPE IF EXISTS bi_data_source_type;
    DROP TYPE IF EXISTS bi_alert_status;
    DROP TYPE IF EXISTS bi_alert_severity;
    DROP TYPE IF EXISTS bi_kpi_trend;
    DROP TYPE IF EXISTS bi_kpi_category;
    DROP TYPE IF EXISTS bi_report_status;
    DROP TYPE IF EXISTS bi_report_format;
    DROP TYPE IF EXISTS bi_report_type;
    DROP TYPE IF EXISTS bi_chart_type;
    DROP TYPE IF EXISTS bi_widget_type;
    DROP TYPE IF EXISTS bi_dashboard_type;

    RAISE NOTICE 'Migration 025_bi_module rolled back successfully';
END $$;
