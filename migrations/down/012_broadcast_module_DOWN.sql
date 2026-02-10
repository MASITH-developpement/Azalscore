-- AZALS - ROLLBACK Migration BROADCAST MODULE
-- Annule la creation du module de diffusion periodique (T6)

DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS v_broadcast_stats;
    DROP VIEW IF EXISTS v_active_broadcasts;

    -- Drop triggers
    DROP TRIGGER IF EXISTS trg_broadcast_templates_updated ON broadcast_templates;
    DROP TRIGGER IF EXISTS trg_recipient_lists_updated ON broadcast_recipient_lists;
    DROP TRIGGER IF EXISTS trg_scheduled_broadcasts_updated ON scheduled_broadcasts;
    DROP TRIGGER IF EXISTS trg_broadcast_preferences_updated ON broadcast_preferences;

    -- Drop function
    DROP FUNCTION IF EXISTS update_broadcast_timestamp();

    -- Drop indexes for broadcast_metrics
    DROP INDEX IF EXISTS ix_broadcast_metrics_tenant_date;
    DROP INDEX IF EXISTS ix_broadcast_metrics_period;

    -- Drop indexes for broadcast_preferences
    DROP INDEX IF EXISTS ix_broadcast_preferences_tenant;
    DROP INDEX IF EXISTS ix_broadcast_preferences_user;

    -- Drop indexes for broadcast_delivery_details
    DROP INDEX IF EXISTS ix_delivery_details_execution;
    DROP INDEX IF EXISTS ix_delivery_details_user;
    DROP INDEX IF EXISTS ix_delivery_details_status;
    DROP INDEX IF EXISTS ix_delivery_details_tracking;

    -- Drop indexes for broadcast_executions
    DROP INDEX IF EXISTS ix_broadcast_executions_scheduled;
    DROP INDEX IF EXISTS ix_broadcast_executions_date;
    DROP INDEX IF EXISTS ix_broadcast_executions_status;

    -- Drop indexes for scheduled_broadcasts
    DROP INDEX IF EXISTS ix_scheduled_broadcasts_tenant;
    DROP INDEX IF EXISTS ix_scheduled_broadcasts_status;
    DROP INDEX IF EXISTS ix_scheduled_broadcasts_next_run;
    DROP INDEX IF EXISTS ix_scheduled_broadcasts_active;

    -- Drop indexes for broadcast_recipient_members
    DROP INDEX IF EXISTS ix_recipient_members_list;
    DROP INDEX IF EXISTS ix_recipient_members_user;
    DROP INDEX IF EXISTS ix_recipient_members_active;

    -- Drop indexes for broadcast_recipient_lists
    DROP INDEX IF EXISTS ix_recipient_lists_tenant;
    DROP INDEX IF EXISTS ix_recipient_lists_active;

    -- Drop indexes for broadcast_templates
    DROP INDEX IF EXISTS ix_broadcast_templates_tenant;
    DROP INDEX IF EXISTS ix_broadcast_templates_type;
    DROP INDEX IF EXISTS ix_broadcast_templates_active;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS broadcast_metrics CASCADE;
    DROP TABLE IF EXISTS broadcast_preferences CASCADE;
    DROP TABLE IF EXISTS broadcast_delivery_details CASCADE;
    DROP TABLE IF EXISTS broadcast_executions CASCADE;
    DROP TABLE IF EXISTS scheduled_broadcasts CASCADE;
    DROP TABLE IF EXISTS broadcast_recipient_members CASCADE;
    DROP TABLE IF EXISTS broadcast_recipient_lists CASCADE;
    DROP TABLE IF EXISTS broadcast_templates CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS recipient_type;
    DROP TYPE IF EXISTS delivery_status;
    DROP TYPE IF EXISTS broadcast_status;
    DROP TYPE IF EXISTS broadcast_content_type;
    DROP TYPE IF EXISTS broadcast_frequency;
    DROP TYPE IF EXISTS delivery_channel;

    RAISE NOTICE 'Migration 012_broadcast_module rolled back successfully';
END $$;
