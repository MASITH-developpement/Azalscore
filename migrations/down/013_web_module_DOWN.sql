-- AZALS - ROLLBACK Migration WEB MODULE
-- Annule la creation du module web transverse (T7)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS trg_web_themes_updated ON web_themes;
    DROP TRIGGER IF EXISTS trg_web_widgets_updated ON web_widgets;
    DROP TRIGGER IF EXISTS trg_web_dashboards_updated ON web_dashboards;
    DROP TRIGGER IF EXISTS trg_web_menu_updated ON web_menu_items;
    DROP TRIGGER IF EXISTS trg_web_components_updated ON web_ui_components;
    DROP TRIGGER IF EXISTS trg_web_prefs_updated ON web_user_preferences;
    DROP TRIGGER IF EXISTS trg_web_shortcuts_updated ON web_shortcuts;
    DROP TRIGGER IF EXISTS trg_web_pages_updated ON web_custom_pages;

    -- Drop function
    DROP FUNCTION IF EXISTS update_web_timestamp();

    -- Drop indexes for web_custom_pages
    DROP INDEX IF EXISTS ix_web_pages_tenant;
    DROP INDEX IF EXISTS ix_web_pages_slug;
    DROP INDEX IF EXISTS ix_web_pages_type;

    -- Drop indexes for web_shortcuts
    DROP INDEX IF EXISTS ix_web_shortcuts_tenant;
    DROP INDEX IF EXISTS ix_web_shortcuts_context;

    -- Drop indexes for web_user_preferences
    DROP INDEX IF EXISTS ix_web_prefs_tenant;
    DROP INDEX IF EXISTS ix_web_prefs_user;

    -- Drop indexes for web_ui_components
    DROP INDEX IF EXISTS ix_web_components_tenant;
    DROP INDEX IF EXISTS ix_web_components_category;

    -- Drop indexes for web_menu_items
    DROP INDEX IF EXISTS ix_web_menu_tenant;
    DROP INDEX IF EXISTS ix_web_menu_type;
    DROP INDEX IF EXISTS ix_web_menu_parent;

    -- Drop indexes for web_dashboards
    DROP INDEX IF EXISTS ix_web_dashboards_tenant;
    DROP INDEX IF EXISTS ix_web_dashboards_default;
    DROP INDEX IF EXISTS ix_web_dashboards_owner;

    -- Drop indexes for web_widgets
    DROP INDEX IF EXISTS ix_web_widgets_tenant;
    DROP INDEX IF EXISTS ix_web_widgets_type;

    -- Drop indexes for web_themes
    DROP INDEX IF EXISTS ix_web_themes_tenant;
    DROP INDEX IF EXISTS ix_web_themes_default;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS web_custom_pages CASCADE;
    DROP TABLE IF EXISTS web_shortcuts CASCADE;
    DROP TABLE IF EXISTS web_user_preferences CASCADE;
    DROP TABLE IF EXISTS web_ui_components CASCADE;
    DROP TABLE IF EXISTS web_menu_items CASCADE;
    DROP TABLE IF EXISTS web_dashboards CASCADE;
    DROP TABLE IF EXISTS web_widgets CASCADE;
    DROP TABLE IF EXISTS web_themes CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS page_type;
    DROP TYPE IF EXISTS menu_type;
    DROP TYPE IF EXISTS component_category;
    DROP TYPE IF EXISTS widget_size;
    DROP TYPE IF EXISTS widget_type;
    DROP TYPE IF EXISTS theme_mode;

    RAISE NOTICE 'Migration 013_web_module rolled back successfully';
END $$;
