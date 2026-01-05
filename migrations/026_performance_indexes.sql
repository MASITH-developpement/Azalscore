-- ============================================================================
-- AZALS - Migration 026: Indexes de Performance ÉLITE
-- ============================================================================
-- Indexes critiques identifiés par audit de performance.
-- Focus: E-Commerce, IAM, Tenant Management, Maintenance
-- ============================================================================

-- ============================================================================
-- 1. E-COMMERCE MODULE (CRITIQUE - Plus gros impact)
-- ============================================================================

-- CartItem - complètement non-indexé (critique pour checkout)
CREATE INDEX IF NOT EXISTS idx_cart_items_tenant_cart
    ON ecommerce_cart_items(tenant_id, cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_tenant_product
    ON ecommerce_cart_items(tenant_id, product_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_tenant_variant
    ON ecommerce_cart_items(tenant_id, variant_id);

-- OrderItem - FK manquante
CREATE INDEX IF NOT EXISTS idx_order_items_tenant_order
    ON ecommerce_order_items(tenant_id, order_id);

-- CustomerAddress - FK manquante
CREATE INDEX IF NOT EXISTS idx_customer_addresses_tenant_customer
    ON ecommerce_customer_addresses(tenant_id, customer_id);

-- Wishlist - FK manquante
CREATE INDEX IF NOT EXISTS idx_wishlists_tenant_customer
    ON ecommerce_wishlists(tenant_id, customer_id);

-- WishlistItem - complètement non-indexé
CREATE INDEX IF NOT EXISTS idx_wishlist_items_tenant_wishlist
    ON ecommerce_wishlist_items(tenant_id, wishlist_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_items_tenant_product
    ON ecommerce_wishlist_items(tenant_id, product_id);

-- ProductVariant - product_id manquant
CREATE INDEX IF NOT EXISTS idx_product_variants_tenant_product
    ON ecommerce_product_variants(tenant_id, product_id);

-- EcommerceCategory - parent_id pour hiérarchie
CREATE INDEX IF NOT EXISTS idx_ecom_categories_tenant_parent
    ON ecommerce_categories(tenant_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_ecom_categories_tenant_visible
    ON ecommerce_categories(tenant_id, is_visible);

-- Coupon - requêtes date range
CREATE INDEX IF NOT EXISTS idx_ecom_coupons_tenant_active
    ON ecommerce_coupons(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ecom_coupons_tenant_dates
    ON ecommerce_coupons(tenant_id, starts_at, expires_at);

-- ProductReview - filtrage
CREATE INDEX IF NOT EXISTS idx_product_reviews_tenant_approved
    ON ecommerce_product_reviews(tenant_id, is_approved);
CREATE INDEX IF NOT EXISTS idx_product_reviews_tenant_customer
    ON ecommerce_product_reviews(tenant_id, customer_id);

-- EcommerceCart - cleanup carts abandonnés
CREATE INDEX IF NOT EXISTS idx_ecom_carts_tenant_abandoned
    ON ecommerce_carts(tenant_id, abandoned_at)
    WHERE abandoned_at IS NOT NULL;

-- ============================================================================
-- 2. IAM & SÉCURITÉ (CRITIQUE - Impact sécurité)
-- ============================================================================

-- IAMUser - filtrage utilisateurs bloqués
CREATE INDEX IF NOT EXISTS idx_iam_users_tenant_locked
    ON iam_users(tenant_id, is_locked);
CREATE INDEX IF NOT EXISTS idx_iam_users_tenant_failed_login
    ON iam_users(tenant_id, failed_login_attempts)
    WHERE failed_login_attempts > 0;

-- IAMRole - filtrage rôles actifs
CREATE INDEX IF NOT EXISTS idx_iam_roles_tenant_active
    ON iam_roles(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_iam_roles_tenant_assignable
    ON iam_roles(tenant_id, is_assignable)
    WHERE is_assignable = true;

-- IAMPermission - filtrage permissions actives
CREATE INDEX IF NOT EXISTS idx_iam_permissions_tenant_active
    ON iam_permissions(tenant_id, is_active);

-- IAMGroup - filtrage groupes actifs
CREATE INDEX IF NOT EXISTS idx_iam_groups_tenant_active
    ON iam_groups(tenant_id, is_active);

-- IAMPasswordHistory - recherche mots de passe récents
CREATE INDEX IF NOT EXISTS idx_iam_password_history_tenant_user_date
    ON iam_password_history(tenant_id, user_id, created_at DESC);

-- IAMTokenBlacklist - tenant_id manquant
CREATE INDEX IF NOT EXISTS idx_iam_token_blacklist_tenant
    ON iam_token_blacklist(tenant_id);

-- ============================================================================
-- 3. TENANT MANAGEMENT (CRITIQUE - Multi-tenancy)
-- ============================================================================

-- Tenant - lookups critiques
CREATE INDEX IF NOT EXISTS idx_tenants_status
    ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_email
    ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_country
    ON tenants(country);

-- TenantSubscription - abonnements actifs
CREATE INDEX IF NOT EXISTS idx_tenant_subs_tenant_active
    ON tenant_subscriptions(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_tenant_subs_tenant_dates
    ON tenant_subscriptions(tenant_id, starts_at, ends_at);
CREATE INDEX IF NOT EXISTS idx_tenant_subs_expiring
    ON tenant_subscriptions(ends_at)
    WHERE is_active = true;

-- TenantModule - modules actifs
CREATE INDEX IF NOT EXISTS idx_tenant_modules_tenant_status
    ON tenant_modules(tenant_id, status);

-- TenantInvitation - invitations en attente
CREATE INDEX IF NOT EXISTS idx_tenant_invitations_tenant_status
    ON tenant_invitations(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_tenant_invitations_expires
    ON tenant_invitations(expires_at)
    WHERE status = 'pending';

-- TenantOnboarding - onboarding incomplets
CREATE INDEX IF NOT EXISTS idx_tenant_onboarding_progress
    ON tenant_onboarding(tenant_id, progress_percent)
    WHERE progress_percent < 100;

-- ============================================================================
-- 4. MAINTENANCE MODULE (IMPORTANT)
-- ============================================================================

-- Asset - next maintenance queries
CREATE INDEX IF NOT EXISTS idx_assets_tenant_next_maintenance
    ON maintenance_assets(tenant_id, next_maintenance_date);
CREATE INDEX IF NOT EXISTS idx_assets_tenant_criticality
    ON maintenance_assets(tenant_id, criticality);

-- MaintenancePlan - planification
CREATE INDEX IF NOT EXISTS idx_maint_plans_tenant_asset
    ON maintenance_plans(tenant_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_maint_plans_tenant_due
    ON maintenance_plans(tenant_id, next_due_date);
CREATE INDEX IF NOT EXISTS idx_maint_plans_tenant_active
    ON maintenance_plans(tenant_id, is_active)
    WHERE is_active = true;

-- WorkOrderTask - status
CREATE INDEX IF NOT EXISTS idx_wo_tasks_wo_status
    ON maintenance_wo_tasks(work_order_id, status);

-- WorkOrderLabor - technician et date
CREATE INDEX IF NOT EXISTS idx_wo_labor_tenant_technician
    ON maintenance_wo_labor(tenant_id, technician_id);
CREATE INDEX IF NOT EXISTS idx_wo_labor_tenant_date
    ON maintenance_wo_labor(tenant_id, work_date);

-- PartRequest - spare_part_id
CREATE INDEX IF NOT EXISTS idx_part_requests_tenant_spare
    ON maintenance_part_requests(tenant_id, spare_part_id);
CREATE INDEX IF NOT EXISTS idx_part_requests_tenant_required
    ON maintenance_part_requests(tenant_id, required_date);

-- SparePart - criticality et product
CREATE INDEX IF NOT EXISTS idx_spare_parts_tenant_criticality
    ON maintenance_spare_parts(tenant_id, criticality);
CREATE INDEX IF NOT EXISTS idx_spare_parts_tenant_product
    ON maintenance_spare_parts(tenant_id, product_id);

-- Failure - type et status
CREATE INDEX IF NOT EXISTS idx_failures_tenant_type
    ON maintenance_failures(tenant_id, failure_type);
CREATE INDEX IF NOT EXISTS idx_failures_tenant_status
    ON maintenance_failures(tenant_id, status);

-- ============================================================================
-- 5. QUALITY & COMPLIANCE (IMPORTANT)
-- ============================================================================

-- QualityControlTemplate - is_active
CREATE INDEX IF NOT EXISTS idx_quality_templates_tenant_active
    ON quality_control_templates(tenant_id, is_active);

-- AuditFinding - status/is_closed
CREATE INDEX IF NOT EXISTS idx_quality_findings_tenant_open
    ON quality_audit_findings(tenant_id, is_closed)
    WHERE is_closed = false;

-- QualityIndicator - is_active
CREATE INDEX IF NOT EXISTS idx_quality_indicators_tenant_active
    ON quality_indicators(tenant_id, is_active);

-- Certification - expiry_date
CREATE INDEX IF NOT EXISTS idx_certifications_tenant_expiry
    ON quality_certifications(tenant_id, expiry_date);
CREATE INDEX IF NOT EXISTS idx_certifications_expiring_soon
    ON quality_certifications(expiry_date)
    WHERE expiry_date >= CURRENT_DATE;

-- ComplianceTraining - is_active
CREATE INDEX IF NOT EXISTS idx_compliance_training_tenant_active
    ON compliance_trainings(tenant_id, is_active);

-- TrainingCompletion - is_current
CREATE INDEX IF NOT EXISTS idx_training_completions_tenant_current
    ON compliance_training_completions(tenant_id, is_current)
    WHERE is_current = true;

-- Regulation - is_active et is_mandatory
CREATE INDEX IF NOT EXISTS idx_regulations_tenant_active
    ON compliance_regulations(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_regulations_tenant_mandatory
    ON compliance_regulations(tenant_id, is_mandatory)
    WHERE is_mandatory = true;

-- ComplianceAction - due_date overdue
CREATE INDEX IF NOT EXISTS idx_compliance_actions_tenant_due
    ON compliance_actions(tenant_id, due_date);
CREATE INDEX IF NOT EXISTS idx_compliance_actions_overdue
    ON compliance_actions(due_date, status)
    WHERE status NOT IN ('completed', 'cancelled');

-- ============================================================================
-- 6. PRODUCTION MODULE (IMPORTANT)
-- ============================================================================

-- BillOfMaterials - is_active
CREATE INDEX IF NOT EXISTS idx_bom_tenant_active
    ON production_bom(tenant_id, is_active)
    WHERE is_active = true;

-- Routing - is_active
CREATE INDEX IF NOT EXISTS idx_routing_tenant_active
    ON production_routings(tenant_id, is_active)
    WHERE is_active = true;

-- WorkOrderTimeEntry - operator_id
CREATE INDEX IF NOT EXISTS idx_wo_time_tenant_operator
    ON production_wo_time_entries(tenant_id, operator_id);

-- ProductionOutput - is_quality_passed
CREATE INDEX IF NOT EXISTS idx_production_output_tenant_quality
    ON production_outputs(tenant_id, is_quality_passed);

-- ============================================================================
-- 7. BROADCAST MODULE (MEDIUM)
-- ============================================================================

-- BroadcastTemplate - is_active
CREATE INDEX IF NOT EXISTS idx_broadcast_templates_tenant_active
    ON broadcast_templates(tenant_id, is_active);

-- RecipientList - is_active
CREATE INDEX IF NOT EXISTS idx_recipient_lists_tenant_active
    ON broadcast_recipient_lists(tenant_id, is_active);

-- RecipientMember - is_active
CREATE INDEX IF NOT EXISTS idx_recipient_members_tenant_active
    ON broadcast_recipient_members(tenant_id, is_active);

-- BroadcastPreference - unsubscribed
CREATE INDEX IF NOT EXISTS idx_broadcast_prefs_tenant_unsub
    ON broadcast_preferences(tenant_id, is_unsubscribed_all)
    WHERE is_unsubscribed_all = true;

-- ============================================================================
-- 8. FINANCE MODULE (ADDITIONNEL)
-- ============================================================================

-- FiscalPeriod - is_closed pour rapports
CREATE INDEX IF NOT EXISTS idx_fiscal_periods_tenant_closed
    ON fiscal_periods(tenant_id, is_closed);
CREATE INDEX IF NOT EXISTS idx_fiscal_periods_tenant_open
    ON fiscal_periods(tenant_id, is_closed)
    WHERE is_closed = false;

-- ============================================================================
-- 9. COMMERCIAL MODULE (ADDITIONNEL)
-- ============================================================================

-- Customer - email et segment pour recherche
CREATE INDEX IF NOT EXISTS idx_customers_tenant_email
    ON customers(tenant_id, email);
CREATE INDEX IF NOT EXISTS idx_customers_tenant_segment
    ON customers(tenant_id, segment);
CREATE INDEX IF NOT EXISTS idx_customers_tenant_source
    ON customers(tenant_id, source);

-- Contact - is_active et decision_maker
CREATE INDEX IF NOT EXISTS idx_contacts_tenant_active
    ON customer_contacts(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_contacts_tenant_decision
    ON customer_contacts(tenant_id, is_decision_maker)
    WHERE is_decision_maker = true;

-- PipelineStage - is_won/is_lost
CREATE INDEX IF NOT EXISTS idx_pipeline_stages_tenant_won
    ON pipeline_stages(tenant_id, is_won);
CREATE INDEX IF NOT EXISTS idx_pipeline_stages_tenant_lost
    ON pipeline_stages(tenant_id, is_lost);

-- ============================================================================
-- 10. AUDIT MODULE (ADDITIONNEL)
-- ============================================================================

-- MetricDefinition - is_active
CREATE INDEX IF NOT EXISTS idx_metric_definitions_tenant_active
    ON audit_metric_definitions(tenant_id, is_active);

-- Benchmark - status et is_active
CREATE INDEX IF NOT EXISTS idx_benchmarks_tenant_status
    ON audit_benchmarks(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_benchmarks_tenant_active
    ON audit_benchmarks(tenant_id, is_active);

-- DataRetentionRule - is_active
CREATE INDEX IF NOT EXISTS idx_retention_rules_tenant_active
    ON audit_data_retention_rules(tenant_id, is_active);

-- AuditDashboard - is_default et is_active
CREATE INDEX IF NOT EXISTS idx_audit_dashboards_tenant_default
    ON audit_dashboards(tenant_id, is_default);

-- ============================================================================
-- STATISTIQUES APRÈS CRÉATION
-- ============================================================================
-- Pour PostgreSQL, analyser les tables après ajout d'indexes
-- ANALYZE ecommerce_cart_items;
-- ANALYZE ecommerce_order_items;
-- ANALYZE iam_users;
-- ANALYZE tenants;
-- ANALYZE maintenance_assets;
-- etc.

-- ============================================================================
-- FIN DE LA MIGRATION
-- ============================================================================
