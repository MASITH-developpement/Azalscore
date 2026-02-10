-- AZALS - ROLLBACK Migration TRIGGERS MODULE
-- Annule la creation du systeme de declencheurs, notifications et rapports

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_triggers_stats;
    DROP VIEW IF EXISTS v_triggers_unresolved_events;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trigger_update_triggers_definitions ON triggers_definitions;
    DROP TRIGGER IF EXISTS trigger_update_triggers_templates ON triggers_templates;
    DROP TRIGGER IF EXISTS trigger_update_triggers_reports ON triggers_scheduled_reports;
    DROP TRIGGER IF EXISTS trigger_update_triggers_webhooks ON triggers_webhooks;

    -- Drop function
    DROP FUNCTION IF EXISTS update_triggers_updated_at();

    -- Drop indexes for triggers_logs
    DROP INDEX IF EXISTS idx_trigger_logs_tenant;
    DROP INDEX IF EXISTS idx_trigger_logs_action;
    DROP INDEX IF EXISTS idx_trigger_logs_created;

    -- Drop indexes for triggers_webhooks
    DROP INDEX IF EXISTS idx_webhooks_tenant;

    -- Drop indexes for triggers_report_history
    DROP INDEX IF EXISTS idx_report_history_tenant;
    DROP INDEX IF EXISTS idx_report_history_report;
    DROP INDEX IF EXISTS idx_report_history_generated;

    -- Drop indexes for triggers_scheduled_reports
    DROP INDEX IF EXISTS idx_reports_tenant;
    DROP INDEX IF EXISTS idx_reports_frequency;
    DROP INDEX IF EXISTS idx_reports_next;

    -- Drop indexes for triggers_notifications
    DROP INDEX IF EXISTS idx_notifications_tenant;
    DROP INDEX IF EXISTS idx_notifications_event;
    DROP INDEX IF EXISTS idx_notifications_user;
    DROP INDEX IF EXISTS idx_notifications_status;
    DROP INDEX IF EXISTS idx_notifications_sent_at;

    -- Drop indexes for triggers_events
    DROP INDEX IF EXISTS idx_events_tenant;
    DROP INDEX IF EXISTS idx_events_trigger;
    DROP INDEX IF EXISTS idx_events_triggered_at;
    DROP INDEX IF EXISTS idx_events_resolved;

    -- Drop indexes for triggers_subscriptions
    DROP INDEX IF EXISTS idx_subscriptions_tenant;
    DROP INDEX IF EXISTS idx_subscriptions_trigger;
    DROP INDEX IF EXISTS idx_subscriptions_user;

    -- Drop indexes for triggers_definitions
    DROP INDEX IF EXISTS idx_triggers_tenant;
    DROP INDEX IF EXISTS idx_triggers_module;
    DROP INDEX IF EXISTS idx_triggers_status;
    DROP INDEX IF EXISTS idx_triggers_type;

    -- Drop indexes for triggers_templates
    DROP INDEX IF EXISTS idx_templates_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS triggers_logs CASCADE;
    DROP TABLE IF EXISTS triggers_webhooks CASCADE;
    DROP TABLE IF EXISTS triggers_report_history CASCADE;
    DROP TABLE IF EXISTS triggers_scheduled_reports CASCADE;
    DROP TABLE IF EXISTS triggers_notifications CASCADE;
    DROP TABLE IF EXISTS triggers_events CASCADE;
    DROP TABLE IF EXISTS triggers_subscriptions CASCADE;
    DROP TABLE IF EXISTS triggers_definitions CASCADE;
    DROP TABLE IF EXISTS triggers_templates CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS escalation_level;
    DROP TYPE IF EXISTS report_frequency;
    DROP TYPE IF EXISTS notification_status;
    DROP TYPE IF EXISTS notification_channel;
    DROP TYPE IF EXISTS alert_severity;
    DROP TYPE IF EXISTS condition_operator;
    DROP TYPE IF EXISTS trigger_status;
    DROP TYPE IF EXISTS trigger_type;

    RAISE NOTICE 'Migration 008_triggers_module rolled back successfully';
END $$;
