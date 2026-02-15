"""Performance Indexes - Optimisation des requetes frequentes

Revision ID: performance_indexes_001
Revises: enrichment_module_001
Create Date: 2026-02-13

Index Strategy:
- Composite indexes pour les requetes multi-criteres
- Partial indexes pour les statuts actifs
- Covering indexes pour eviter les table scans

Tables concernees:
- subscriptions: tenant_id, status, customer_id
- subscription_invoices: tenant_id, status, due_date
- subscription_payments: tenant_id, status
- commercial_documents: tenant_id, type, status, date
- customers: tenant_id, type, is_active
- contacts: tenant_id, type
- iam_users: tenant_id, is_active
- iam_audit_log: tenant_id, created_at
- guardian_errors: tenant_id, occurred_at
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'performance_indexes_001'
down_revision = 'enrichment_module_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Creer les index de performance."""

    # ==========================================================================
    # SUBSCRIPTIONS MODULE
    # ==========================================================================

    # Index composite pour list_subscriptions (tenant + status)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_subscriptions_tenant_status
        ON subscriptions (tenant_id, status)
        WHERE status IN ('active', 'trialing', 'past_due');
    """)

    # Index pour recherche par customer
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_subscriptions_tenant_customer
        ON subscriptions (tenant_id, customer_id);
    """)

    # Index pour les factures en attente
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_subscription_invoices_tenant_status
        ON subscription_invoices (tenant_id, status)
        WHERE status IN ('draft', 'open');
    """)

    # Index pour les factures par echeance
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_subscription_invoices_due_date
        ON subscription_invoices (tenant_id, due_date)
        WHERE status = 'open';
    """)

    # Index pour les paiements
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_subscription_payments_tenant_status
        ON subscription_payments (tenant_id, status);
    """)

    # ==========================================================================
    # COMMERCIAL MODULE
    # ==========================================================================

    # Index composite pour list_documents (tenant + type + status)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_commercial_documents_tenant_type_status
        ON commercial_documents (tenant_id, type, status);
    """)

    # Index pour recherche par date
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_commercial_documents_tenant_date
        ON commercial_documents (tenant_id, date DESC);
    """)

    # Index pour les factures echues (partial index)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_commercial_documents_overdue
        ON commercial_documents (tenant_id, due_date)
        WHERE type = 'INVOICE' AND status = 'VALIDATED' AND due_date IS NOT NULL;
    """)

    # Index pour list_customers
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_customers_tenant_type_active
        ON customers (tenant_id, type, is_active);
    """)

    # Index pour recherche texte sur customers
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_customers_tenant_name
        ON customers (tenant_id, name varchar_pattern_ops);
    """)

    # ==========================================================================
    # CONTACTS MODULE
    # ==========================================================================

    # Index pour les contacts unifies
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_unified_contacts_tenant_active
        ON unified_contacts (tenant_id, is_active)
        WHERE deleted_at IS NULL;
    """)

    # Index pour recherche par email
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_unified_contacts_tenant_email
        ON unified_contacts (tenant_id, email)
        WHERE email IS NOT NULL AND deleted_at IS NULL;
    """)

    # Index pour recherche par code
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_unified_contacts_tenant_code
        ON unified_contacts (tenant_id, code)
        WHERE deleted_at IS NULL;
    """)

    # ==========================================================================
    # IAM MODULE
    # ==========================================================================

    # Index pour les utilisateurs actifs
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_iam_users_tenant_active
        ON iam_users (tenant_id, is_active)
        WHERE is_active = true;
    """)

    # Index pour l'audit log (requetes frequentes dans admin dashboard)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_iam_audit_log_tenant_created
        ON iam_audit_log (tenant_id, created_at DESC);
    """)

    # ==========================================================================
    # GUARDIAN MODULE
    # ==========================================================================

    # Index pour les erreurs (dashboard admin)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_guardian_errors_tenant_occurred
        ON guardian_errors (tenant_id, occurred_at DESC);
    """)

    # ==========================================================================
    # HELPDESK MODULE
    # ==========================================================================

    # Index pour les tickets ouverts
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_support_tickets_tenant_status_priority
        ON support_tickets (tenant_id, status, priority)
        WHERE status IN ('open', 'in_progress');
    """)

    # ==========================================================================
    # INVENTORY MODULE
    # ==========================================================================

    # Index pour les produits actifs
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_inventory_products_tenant_status
        ON inventory_products (tenant_id, status)
        WHERE status = 'active';
    """)

    # Index pour les niveaux de stock
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_stock_levels_tenant_product
        ON stock_levels (tenant_id, product_id);
    """)

    # ==========================================================================
    # COCKPIT QUERIES OPTIMIZATION
    # ==========================================================================

    # Index pour bank_accounts (tresorerie)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            idx_bank_accounts_tenant_active
        ON bank_accounts (tenant_id, is_active)
        WHERE is_active = true;
    """)


def downgrade() -> None:
    """Supprimer les index de performance."""

    # Subscriptions
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_subscriptions_tenant_status;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_subscriptions_tenant_customer;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_subscription_invoices_tenant_status;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_subscription_invoices_due_date;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_subscription_payments_tenant_status;")

    # Commercial
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_commercial_documents_tenant_type_status;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_commercial_documents_tenant_date;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_commercial_documents_overdue;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_customers_tenant_type_active;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_customers_tenant_name;")

    # Contacts
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_unified_contacts_tenant_active;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_unified_contacts_tenant_email;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_unified_contacts_tenant_code;")

    # IAM
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_iam_users_tenant_active;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_iam_audit_log_tenant_created;")

    # Guardian
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_guardian_errors_tenant_occurred;")

    # Helpdesk
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_support_tickets_tenant_status_priority;")

    # Inventory
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_inventory_products_tenant_status;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_stock_levels_tenant_product;")

    # Cockpit
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_bank_accounts_tenant_active;")
