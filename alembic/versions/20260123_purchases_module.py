"""MODULE M4 - Purchases: Create purchases tables

Revision ID: purchases_module_001
Revises: guardian_ai_monitoring_001
Create Date: 2026-01-23

Tables:
- purchases_suppliers: Fournisseurs
- purchases_orders: Commandes d'achat
- purchases_order_lines: Lignes de commandes
- purchases_invoices: Factures fournisseurs
- purchases_invoice_lines: Lignes de factures
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'purchases_module_001'
down_revision = 'guardian_ai_monitoring_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create purchases module tables."""

    # ==========================================================================
    # Table purchases_suppliers - Fournisseurs
    # ==========================================================================
    op.create_table(
        'purchases_suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('supplier_type', sa.Enum('GOODS', 'SERVICES', 'BOTH', 'RAW_MATERIALS', 'EQUIPMENT',
                                            name='purchases_suppliertype'), nullable=True),

        # Contact
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('mobile', sa.String(50), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),

        # Adresse
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), server_default='France'),

        # Informations légales
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('registration_number', sa.String(50), nullable=True),
        sa.Column('legal_form', sa.String(50), nullable=True),

        # Conditions commerciales
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('credit_limit', sa.Numeric(15, 2), nullable=True),

        # Statut
        sa.Column('status', sa.Enum('PROSPECT', 'PENDING', 'APPROVED', 'BLOCKED', 'INACTIVE',
                                     name='purchases_supplierstatus'), nullable=False, server_default='PENDING'),

        # Classification
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_purchases_suppliers_tenant_id', 'tenant_id'),
        sa.Index('idx_purchases_suppliers_code', 'tenant_id', 'code', unique=True),
        sa.Index('idx_purchases_suppliers_status', 'status'),
    )

    # ==========================================================================
    # Table purchases_orders - Commandes d'achat
    # ==========================================================================
    op.create_table(
        'purchases_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('number', sa.String(50), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Dates
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('expected_date', sa.DateTime(), nullable=True),
        sa.Column('received_date', sa.DateTime(), nullable=True),

        # Statut
        sa.Column('status', sa.Enum('DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL', 'RECEIVED', 'INVOICED', 'CANCELLED',
                                     name='purchases_orderstatus'), nullable=False, server_default='DRAFT'),

        # Référence
        sa.Column('reference', sa.String(100), nullable=True),

        # Livraison
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('delivery_contact', sa.String(255), nullable=True),
        sa.Column('delivery_phone', sa.String(50), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Totaux
        sa.Column('total_ht', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total_tax', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total_ttc', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Validation
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Métadonnées
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['purchases_suppliers.id']),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.Index('idx_purchases_orders_tenant_id', 'tenant_id'),
        sa.Index('idx_purchases_orders_number', 'tenant_id', 'number', unique=True),
        sa.Index('idx_purchases_orders_supplier', 'supplier_id'),
        sa.Index('idx_purchases_orders_status', 'status'),
        sa.Index('idx_purchases_orders_date', 'date'),
    )

    # ==========================================================================
    # Table purchases_order_lines - Lignes de commandes
    # ==========================================================================
    op.create_table(
        'purchases_order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),

        # Produit/Service
        sa.Column('product_code', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 3), nullable=False, server_default='1.000'),
        sa.Column('unit', sa.String(20), server_default='unité'),

        # Prix
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), server_default='0.00'),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='20.00'),

        # Totaux calculés
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('subtotal', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total', sa.Numeric(15, 2), server_default='0.00'),

        # Réception
        sa.Column('received_quantity', sa.Numeric(15, 3), server_default='0.000'),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['purchases_orders.id'], ondelete='CASCADE'),
        sa.Index('idx_purchases_order_lines_tenant_id', 'tenant_id'),
        sa.Index('idx_purchases_order_lines_order', 'order_id'),
    )

    # ==========================================================================
    # Table purchases_invoices - Factures fournisseurs
    # ==========================================================================
    op.create_table(
        'purchases_invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),

        # Identification
        sa.Column('number', sa.String(50), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Dates
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('payment_date', sa.DateTime(), nullable=True),

        # Statut
        sa.Column('status', sa.Enum('DRAFT', 'VALIDATED', 'PAID', 'CANCELLED',
                                     name='purchases_invoicestatus'), nullable=False, server_default='DRAFT'),

        # Référence
        sa.Column('reference', sa.String(100), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Totaux
        sa.Column('total_ht', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total_tax', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total_ttc', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('currency', sa.String(3), server_default='EUR'),

        # Validation
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),

        # Paiement
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('paid_amount', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('payment_method', sa.String(50), nullable=True),

        # Métadonnées
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['purchases_suppliers.id']),
        sa.ForeignKeyConstraint(['order_id'], ['purchases_orders.id']),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.Index('idx_purchases_invoices_tenant_id', 'tenant_id'),
        sa.Index('idx_purchases_invoices_number', 'tenant_id', 'number', unique=True),
        sa.Index('idx_purchases_invoices_supplier', 'supplier_id'),
        sa.Index('idx_purchases_invoices_order', 'order_id'),
        sa.Index('idx_purchases_invoices_status', 'status'),
        sa.Index('idx_purchases_invoices_date', 'invoice_date'),
    )

    # ==========================================================================
    # Table purchases_invoice_lines - Lignes de factures
    # ==========================================================================
    op.create_table(
        'purchases_invoice_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),

        # Produit/Service
        sa.Column('product_code', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 3), nullable=False, server_default='1.000'),
        sa.Column('unit', sa.String(20), server_default='unité'),

        # Prix
        sa.Column('unit_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), server_default='0.00'),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='20.00'),

        # Totaux calculés
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('subtotal', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0.00'),
        sa.Column('total', sa.Numeric(15, 2), server_default='0.00'),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Métadonnées
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invoice_id'], ['purchases_invoices.id'], ondelete='CASCADE'),
        sa.Index('idx_purchases_invoice_lines_tenant_id', 'tenant_id'),
        sa.Index('idx_purchases_invoice_lines_invoice', 'invoice_id'),
    )


def downgrade() -> None:
    """Drop purchases module tables."""
    op.drop_table('purchases_invoice_lines')
    op.drop_table('purchases_invoices')
    op.drop_table('purchases_order_lines')
    op.drop_table('purchases_orders')
    op.drop_table('purchases_suppliers')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS purchases_suppliertype')
    op.execute('DROP TYPE IF EXISTS purchases_supplierstatus')
    op.execute('DROP TYPE IF EXISTS purchases_orderstatus')
    op.execute('DROP TYPE IF EXISTS purchases_invoicestatus')
