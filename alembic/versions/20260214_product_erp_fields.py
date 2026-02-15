"""Add ERP compatibility fields to inventory_products

Revision ID: 20260214_product_erp
Revises: 20260214_enrichment_provider_config
Create Date: 2026-02-14

Champs ajoutés pour conformité:
- Chorus Pro / Factur-X / EN 16931 (facturation électronique)
- Axonaut, Odoo, Sellsy (compatibilité ERP)

Références EN 16931:
- BT-152: tax_rate (Taux TVA)
- BT-151: tax_id (Catégorie TVA)
- BT-156: customer_product_code (Référence acheteur)
- BT-158: cpv_code (Code classification)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'product_erp_fields_001'
down_revision = 'enrichment_provider_config_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nom commercial (Sellsy tradename)
    op.add_column('inventory_products', sa.Column(
        'trade_name', sa.String(255), nullable=True,
        comment='Nom commercial (Sellsy tradename)'
    ))

    # Code CPV marchés publics (EN 16931 BT-158)
    op.add_column('inventory_products', sa.Column(
        'cpv_code', sa.String(20), nullable=True,
        comment='Code CPV marchés publics (EN 16931 BT-158)'
    ))

    # Référence fournisseur (Odoo seller_ids.product_code)
    op.add_column('inventory_products', sa.Column(
        'supplier_product_code', sa.String(100), nullable=True,
        comment='Référence article chez le fournisseur'
    ))

    # Référence client (EN 16931 BT-156)
    op.add_column('inventory_products', sa.Column(
        'customer_product_code', sa.String(100), nullable=True,
        comment='Référence article chez le client (EN 16931 BT-156)'
    ))

    # Taux TVA vente % (EN 16931 BT-152)
    op.add_column('inventory_products', sa.Column(
        'tax_rate', sa.Numeric(5, 2), nullable=True, server_default='20.00',
        comment='Taux TVA vente en % (EN 16931 BT-152)'
    ))

    # Référence taxe vente (EN 16931 BT-151)
    op.add_column('inventory_products', sa.Column(
        'tax_id', postgresql.UUID(as_uuid=True), nullable=True,
        comment='Référence taxe vente (EN 16931 BT-151)'
    ))

    # Taux TVA achat %
    op.add_column('inventory_products', sa.Column(
        'supplier_tax_rate', sa.Numeric(5, 2), nullable=True, server_default='20.00',
        comment='Taux TVA achat en %'
    ))

    # Référence taxe achat
    op.add_column('inventory_products', sa.Column(
        'supplier_tax_id', postgresql.UUID(as_uuid=True), nullable=True,
        comment='Référence taxe achat'
    ))

    # Éco-contribution (Sellsy ecoTax)
    op.add_column('inventory_products', sa.Column(
        'eco_tax', sa.Numeric(10, 4), nullable=True, server_default='0',
        comment='Éco-contribution en EUR (Sellsy ecoTax)'
    ))

    # Flag vendable (Odoo sale_ok)
    op.add_column('inventory_products', sa.Column(
        'is_sellable', sa.Boolean(), nullable=True, server_default='true',
        comment='Produit peut être vendu (Odoo sale_ok)'
    ))

    # Flag achetable (Odoo purchase_ok)
    op.add_column('inventory_products', sa.Column(
        'is_purchasable', sa.Boolean(), nullable=True, server_default='true',
        comment='Produit peut être acheté (Odoo purchase_ok)'
    ))

    # Index pour recherche par code fournisseur
    op.create_index(
        'idx_products_supplier_code',
        'inventory_products',
        ['tenant_id', 'supplier_product_code'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_products_supplier_code', table_name='inventory_products')
    op.drop_column('inventory_products', 'is_purchasable')
    op.drop_column('inventory_products', 'is_sellable')
    op.drop_column('inventory_products', 'eco_tax')
    op.drop_column('inventory_products', 'supplier_tax_id')
    op.drop_column('inventory_products', 'supplier_tax_rate')
    op.drop_column('inventory_products', 'tax_id')
    op.drop_column('inventory_products', 'tax_rate')
    op.drop_column('inventory_products', 'customer_product_code')
    op.drop_column('inventory_products', 'supplier_product_code')
    op.drop_column('inventory_products', 'cpv_code')
    op.drop_column('inventory_products', 'trade_name')
