-- AZALS - ROLLBACK Migration Performance Indexes
-- Annule la creation des indexes de performance

DO $$
BEGIN
    -- ============================================================================
    -- 1. E-COMMERCE MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_cart_items_tenant_cart;
    DROP INDEX IF EXISTS idx_cart_items_tenant_product;
    DROP INDEX IF EXISTS idx_cart_items_tenant_variant;
    DROP INDEX IF EXISTS idx_order_items_tenant_order;
    DROP INDEX IF EXISTS idx_customer_addresses_tenant_customer;
    DROP INDEX IF EXISTS idx_wishlists_tenant_customer;
    DROP INDEX IF EXISTS idx_wishlist_items_tenant_wishlist;
    DROP INDEX IF EXISTS idx_wishlist_items_tenant_product;
    DROP INDEX IF EXISTS idx_product_variants_tenant_product;
    DROP INDEX IF EXISTS idx_ecom_categories_tenant_parent;
    DROP INDEX IF EXISTS idx_ecom_categories_tenant_visible;
    DROP INDEX IF EXISTS idx_ecom_coupons_tenant_active;
    DROP INDEX IF EXISTS idx_ecom_coupons_tenant_dates;
    DROP INDEX IF EXISTS idx_product_reviews_tenant_approved;
    DROP INDEX IF EXISTS idx_product_reviews_tenant_customer;
    DROP INDEX IF EXISTS idx_ecom_carts_tenant_abandoned;

    -- ============================================================================
    -- 2. IAM & SECURITE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_iam_users_tenant_locked;
    DROP INDEX IF EXISTS idx_iam_users_tenant_failed_login;
    DROP INDEX IF EXISTS idx_iam_roles_tenant_active;
    DROP INDEX IF EXISTS idx_iam_roles_tenant_assignable;
    DROP INDEX IF EXISTS idx_iam_permissions_tenant_active;
    DROP INDEX IF EXISTS idx_iam_groups_tenant_active;
    DROP INDEX IF EXISTS idx_iam_password_history_tenant_user_date;
    DROP INDEX IF EXISTS idx_iam_token_blacklist_tenant;

    -- ============================================================================
    -- 3. TENANT MANAGEMENT
    -- ============================================================================
    DROP INDEX IF EXISTS idx_tenants_status;
    DROP INDEX IF EXISTS idx_tenants_email;
    DROP INDEX IF EXISTS idx_tenants_country;
    DROP INDEX IF EXISTS idx_tenant_subs_tenant_active;
    DROP INDEX IF EXISTS idx_tenant_subs_tenant_dates;
    DROP INDEX IF EXISTS idx_tenant_subs_expiring;
    DROP INDEX IF EXISTS idx_tenant_modules_tenant_status;
    DROP INDEX IF EXISTS idx_tenant_invitations_tenant_status;
    DROP INDEX IF EXISTS idx_tenant_invitations_expires;
    DROP INDEX IF EXISTS idx_tenant_onboarding_progress;

    -- ============================================================================
    -- 4. MAINTENANCE MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_assets_tenant_next_maintenance;
    DROP INDEX IF EXISTS idx_assets_tenant_criticality;
    DROP INDEX IF EXISTS idx_maint_plans_tenant_asset;
    DROP INDEX IF EXISTS idx_maint_plans_tenant_due;
    DROP INDEX IF EXISTS idx_maint_plans_tenant_active;
    DROP INDEX IF EXISTS idx_wo_tasks_wo_status;
    DROP INDEX IF EXISTS idx_wo_labor_tenant_technician;
    DROP INDEX IF EXISTS idx_wo_labor_tenant_date;
    DROP INDEX IF EXISTS idx_part_requests_tenant_spare;
    DROP INDEX IF EXISTS idx_part_requests_tenant_required;
    DROP INDEX IF EXISTS idx_spare_parts_tenant_criticality;
    DROP INDEX IF EXISTS idx_spare_parts_tenant_product;
    DROP INDEX IF EXISTS idx_failures_tenant_type;
    DROP INDEX IF EXISTS idx_failures_tenant_status;

    -- ============================================================================
    -- 5. QUALITY & COMPLIANCE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_quality_templates_tenant_active;
    DROP INDEX IF EXISTS idx_quality_findings_tenant_open;
    DROP INDEX IF EXISTS idx_quality_indicators_tenant_active;
    DROP INDEX IF EXISTS idx_certifications_tenant_expiry;
    DROP INDEX IF EXISTS idx_certifications_expiring_soon;
    DROP INDEX IF EXISTS idx_compliance_training_tenant_active;
    DROP INDEX IF EXISTS idx_training_completions_tenant_current;
    DROP INDEX IF EXISTS idx_regulations_tenant_active;
    DROP INDEX IF EXISTS idx_regulations_tenant_mandatory;
    DROP INDEX IF EXISTS idx_compliance_actions_tenant_due;
    DROP INDEX IF EXISTS idx_compliance_actions_overdue;

    -- ============================================================================
    -- 6. PRODUCTION MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_bom_tenant_active;
    DROP INDEX IF EXISTS idx_routing_tenant_active;
    DROP INDEX IF EXISTS idx_wo_time_tenant_operator;
    DROP INDEX IF EXISTS idx_production_output_tenant_quality;

    -- ============================================================================
    -- 7. BROADCAST MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_broadcast_templates_tenant_active;
    DROP INDEX IF EXISTS idx_recipient_lists_tenant_active;
    DROP INDEX IF EXISTS idx_recipient_members_tenant_active;
    DROP INDEX IF EXISTS idx_broadcast_prefs_tenant_unsub;

    -- ============================================================================
    -- 8. FINANCE MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_fiscal_periods_tenant_closed;
    DROP INDEX IF EXISTS idx_fiscal_periods_tenant_open;

    -- ============================================================================
    -- 9. COMMERCIAL MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_customers_tenant_email;
    DROP INDEX IF EXISTS idx_customers_tenant_segment;
    DROP INDEX IF EXISTS idx_customers_tenant_source;
    DROP INDEX IF EXISTS idx_contacts_tenant_active;
    DROP INDEX IF EXISTS idx_contacts_tenant_decision;
    DROP INDEX IF EXISTS idx_pipeline_stages_tenant_won;
    DROP INDEX IF EXISTS idx_pipeline_stages_tenant_lost;

    -- ============================================================================
    -- 10. AUDIT MODULE
    -- ============================================================================
    DROP INDEX IF EXISTS idx_metric_definitions_tenant_active;
    DROP INDEX IF EXISTS idx_benchmarks_tenant_status;
    DROP INDEX IF EXISTS idx_benchmarks_tenant_active;
    DROP INDEX IF EXISTS idx_retention_rules_tenant_active;
    DROP INDEX IF EXISTS idx_audit_dashboards_tenant_default;

    RAISE NOTICE 'Migration 026_performance_indexes rolled back successfully';
END $$;
