"""
AZALS MODULE 12 - E-Commerce
=============================
Modèles SQLAlchemy pour la plateforme e-commerce enterprise.

Benchmark: Shopify, WooCommerce, Magento, BigCommerce
Target: ERP-native e-commerce avec intégration complète
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import JSON, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class ProductStatus(str, enum.Enum):
    """Statuts produit."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class ProductType(str, enum.Enum):
    """Types de produit."""
    PHYSICAL = "PHYSICAL"
    DIGITAL = "DIGITAL"
    SERVICE = "SERVICE"
    BUNDLE = "BUNDLE"
    SUBSCRIPTION = "SUBSCRIPTION"


class OrderStatus(str, enum.Enum):
    """Statuts commande."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class PaymentStatus(str, enum.Enum):
    """Statuts paiement."""
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class ShippingStatus(str, enum.Enum):
    """Statuts livraison."""
    PENDING = "PENDING"
    READY_TO_SHIP = "READY_TO_SHIP"
    SHIPPED = "SHIPPED"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"


class DiscountType(str, enum.Enum):
    """Types de réduction."""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    FREE_SHIPPING = "FREE_SHIPPING"
    BUY_X_GET_Y = "BUY_X_GET_Y"


class CartStatus(str, enum.Enum):
    """Statuts panier."""
    ACTIVE = "ACTIVE"
    ABANDONED = "ABANDONED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"


# ============================================================================
# MODÈLES CATALOGUE
# ============================================================================

class EcommerceCategory(Base):
    """Catégorie de produits e-commerce."""
    __tablename__ = "ecommerce_categories"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Hiérarchie
    parent_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_categories.id"))

    # Informations
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(Text)
    meta_keywords: Mapped[str | None] = mapped_column(String(500))

    # Affichage
    image_url: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Configuration
    settings: Mapped[dict | None] = mapped_column(JSON)  # {"show_in_menu": true, "filters": [...]}

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Index
    __table_args__ = (
        Index('idx_ecom_cat_tenant_slug', 'tenant_id', 'slug', unique=True),
    )


class EcommerceProduct(Base):
    """Produit e-commerce."""
    __tablename__ = "ecommerce_products"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identifiants
    sku: Mapped[str | None] = mapped_column(String(100), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100))

    # Lien avec module Articles existant
    item_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers items si applicable

    # Informations produit
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    # Type et statut
    product_type: Mapped[str | None] = mapped_column(Enum(ProductType), default=ProductType.PHYSICAL)
    status: Mapped[str | None] = mapped_column(Enum(ProductStatus), default=ProductStatus.DRAFT)

    # Prix
    price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Prix barré
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Prix de revient
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")

    # Taxes
    tax_class: Mapped[str | None] = mapped_column(String(50), default="standard")
    is_taxable: Mapped[bool | None] = mapped_column(Boolean, default=True)

    # Stock (synchronisé avec module Inventory)
    track_inventory: Mapped[bool | None] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int | None] = mapped_column(Integer, default=5)
    allow_backorder: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Poids et dimensions (livraison)
    weight: Mapped[float | None] = mapped_column(Float)  # kg
    weight_unit: Mapped[str | None] = mapped_column(String(10), default="kg")
    length: Mapped[float | None] = mapped_column(Float)
    width: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    dimension_unit: Mapped[str | None] = mapped_column(String(10), default="cm")

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(Text)
    meta_keywords: Mapped[str | None] = mapped_column(String(500))

    # Médias
    images: Mapped[dict | None] = mapped_column(JSON)  # [{"url": "...", "alt": "...", "position": 1}]

    # Attributs personnalisés
    attributes: Mapped[dict | None] = mapped_column(JSON)  # {"color": "red", "size": "M"}

    # Catégories
    category_ids: Mapped[dict | None] = mapped_column(JSON)  # [1, 2, 3]

    # Tags
    tags: Mapped[dict | None] = mapped_column(JSON)  # ["new", "sale", "featured"]

    # Visibilité
    is_visible: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Configuration
    settings: Mapped[dict | None] = mapped_column(JSON)

    # Statistiques
    view_count: Mapped[int | None] = mapped_column(Integer, default=0)
    sale_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index('idx_ecom_prod_tenant_sku', 'tenant_id', 'sku', unique=True),
        Index('idx_ecom_prod_tenant_slug', 'tenant_id', 'slug'),
        Index('idx_ecom_prod_status', 'tenant_id', 'status'),
    )


class ProductVariant(Base):
    """Variante de produit (taille, couleur, etc.)."""
    __tablename__ = "ecommerce_product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_products.id"), nullable=False)

    # Identifiants
    sku: Mapped[str | None] = mapped_column(String(100), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100))

    # Attributs de la variante
    name: Mapped[str | None] = mapped_column(String(255))  # "Rouge - XL"
    options: Mapped[dict | None] = mapped_column(JSON)  # {"color": "red", "size": "XL"}

    # Prix (peut différer du produit parent)
    price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Stock
    stock_quantity: Mapped[int | None] = mapped_column(Integer, default=0)

    # Poids/dimensions spécifiques
    weight: Mapped[float | None] = mapped_column(Float)

    # Image spécifique
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Position
    position: Mapped[int | None] = mapped_column(Integer, default=0)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_var_tenant_sku', 'tenant_id', 'sku', unique=True),
    )


# ============================================================================
# MODÈLES PANIER
# ============================================================================

class EcommerceCart(Base):
    """Panier d'achat."""
    __tablename__ = "ecommerce_carts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Identifiant unique pour visiteurs anonymes
    session_id: Mapped[str | None] = mapped_column(String(255), index=True)

    # Client (si connecté)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(CartStatus), default=CartStatus.ACTIVE)

    # Devise
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")

    # Totaux (calculés)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    discount_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    shipping_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Codes promo appliqués
    coupon_codes: Mapped[dict | None] = mapped_column(JSON)  # ["CODE1", "CODE2"]

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Métadonnées
    extra_data: Mapped[dict | None] = mapped_column(JSON)  # Infos tracking, UTM, etc.

    # Abandon
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime)
    recovery_email_sent: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Conversion
    converted_to_order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    converted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_cart_session', 'tenant_id', 'session_id'),
        Index('idx_ecom_cart_customer', 'tenant_id', 'customer_id'),
        Index('idx_ecom_cart_status', 'tenant_id', 'status'),
    )


class CartItem(Base):
    """Article dans un panier."""
    __tablename__ = "ecommerce_cart_items"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    cart_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_carts.id"), nullable=False)

    # Produit
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_products.id"), nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_product_variants.id"))

    # Quantité
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Prix au moment de l'ajout
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    total_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Réductions sur cette ligne
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)

    # Options personnalisées
    custom_options: Mapped[dict | None] = mapped_column(JSON)  # {"engraving": "John"}

    # Audit
    added_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MODÈLES COMMANDE
# ============================================================================

class EcommerceOrder(Base):
    """Commande e-commerce."""
    __tablename__ = "ecommerce_orders"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Numéro de commande
    order_number: Mapped[str | None] = mapped_column(String(50), nullable=False)

    # Origine
    cart_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_carts.id"))
    channel: Mapped[str | None] = mapped_column(String(50), default="web")  # web, mobile, api, pos

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers commercial.customers
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(50))

    # Statuts
    status: Mapped[str | None] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status: Mapped[str | None] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    shipping_status: Mapped[str | None] = mapped_column(Enum(ShippingStatus), default=ShippingStatus.PENDING)

    # Devise
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), default=1)

    # Montants
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    discount_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    shipping_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Coupons
    coupon_codes: Mapped[dict | None] = mapped_column(JSON)

    # Adresse de facturation
    billing_first_name: Mapped[str | None] = mapped_column(String(100))
    billing_last_name: Mapped[str | None] = mapped_column(String(100))
    billing_company: Mapped[str | None] = mapped_column(String(255))
    billing_address1: Mapped[str | None] = mapped_column(String(255))
    billing_address2: Mapped[str | None] = mapped_column(String(255))
    billing_city: Mapped[str | None] = mapped_column(String(100))
    billing_postal_code: Mapped[str | None] = mapped_column(String(20))
    billing_country: Mapped[str | None] = mapped_column(String(2))
    billing_phone: Mapped[str | None] = mapped_column(String(50))

    # Adresse de livraison
    shipping_first_name: Mapped[str | None] = mapped_column(String(100))
    shipping_last_name: Mapped[str | None] = mapped_column(String(100))
    shipping_company: Mapped[str | None] = mapped_column(String(255))
    shipping_address1: Mapped[str | None] = mapped_column(String(255))
    shipping_address2: Mapped[str | None] = mapped_column(String(255))
    shipping_city: Mapped[str | None] = mapped_column(String(100))
    shipping_postal_code: Mapped[str | None] = mapped_column(String(20))
    shipping_country: Mapped[str | None] = mapped_column(String(2))
    shipping_phone: Mapped[str | None] = mapped_column(String(50))

    # Livraison
    shipping_method: Mapped[str | None] = mapped_column(String(100))
    shipping_carrier: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(255))
    tracking_url: Mapped[str | None] = mapped_column(String(500))

    # Dates estimées
    estimated_delivery_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Notes
    customer_notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Métadonnées
    extra_data: Mapped[dict | None] = mapped_column(JSON)

    # Lien avec facturation AZALS
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers finance.invoices

    # IP et infos client
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    # Dates importantes
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index('idx_ecom_order_number', 'tenant_id', 'order_number', unique=True),
        Index('idx_ecom_order_customer', 'tenant_id', 'customer_id'),
        Index('idx_ecom_order_status', 'tenant_id', 'status'),
        Index('idx_ecom_order_date', 'tenant_id', 'created_at'),
    )


class OrderItem(Base):
    """Ligne de commande."""
    __tablename__ = "ecommerce_order_items"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_orders.id"), nullable=False)

    # Produit (snapshot au moment de la commande)
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    variant_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    sku: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)

    # Quantité
    quantity: Mapped[int] = mapped_column(Integer)

    # Prix
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Taxes détaillées
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    tax_class: Mapped[str | None] = mapped_column(String(50))

    # Options personnalisées
    custom_options: Mapped[dict | None] = mapped_column(JSON)

    # Statut de la ligne
    status: Mapped[str | None] = mapped_column(String(50), default="pending")

    # Fulfillment
    quantity_fulfilled: Mapped[int | None] = mapped_column(Integer, default=0)
    quantity_refunded: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


# ============================================================================
# MODÈLES PAIEMENT
# ============================================================================

class EcommercePayment(Base):
    """Paiement de commande."""
    __tablename__ = "ecommerce_payments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_orders.id"), nullable=False)

    # Référence externe (Stripe, PayPal, etc.)
    external_id: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(50))  # stripe, paypal, bank_transfer

    # Montant
    amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), default="EUR")

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Méthode
    payment_method: Mapped[str | None] = mapped_column(String(50))  # card, sepa, paypal
    card_brand: Mapped[str | None] = mapped_column(String(20))  # visa, mastercard
    card_last4: Mapped[str | None] = mapped_column(String(4))

    # Détails
    details: Mapped[dict | None] = mapped_column(JSON)

    # Erreurs
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Dates
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_payment_order', 'tenant_id', 'order_id'),
        Index('idx_ecom_payment_external', 'tenant_id', 'external_id'),
    )


# ============================================================================
# MODÈLES LIVRAISON
# ============================================================================

class ShippingMethod(Base):
    """Méthode de livraison."""
    __tablename__ = "ecommerce_shipping_methods"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Informations
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Transporteur
    carrier: Mapped[str | None] = mapped_column(String(100))

    # Prix
    price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    free_shipping_threshold: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Gratuit au-dessus de X€

    # Délais
    min_delivery_days: Mapped[int | None] = mapped_column(Integer)
    max_delivery_days: Mapped[int | None] = mapped_column(Integer)

    # Zones
    countries: Mapped[dict | None] = mapped_column(JSON)  # ["FR", "BE", "CH"]

    # Conditions
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    max_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    min_weight: Mapped[float | None] = mapped_column(Float)
    max_weight: Mapped[float | None] = mapped_column(Float)

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_ship_method', 'tenant_id', 'code', unique=True),
    )


class Shipment(Base):
    """Expédition de commande."""
    __tablename__ = "ecommerce_shipments"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_orders.id"), nullable=False)

    # Numéro d'expédition
    shipment_number: Mapped[str | None] = mapped_column(String(50), nullable=False)

    # Transporteur
    carrier: Mapped[str | None] = mapped_column(String(100))
    shipping_method: Mapped[str | None] = mapped_column(String(100))

    # Tracking
    tracking_number: Mapped[str | None] = mapped_column(String(255))
    tracking_url: Mapped[str | None] = mapped_column(String(500))

    # Statut
    status: Mapped[str | None] = mapped_column(Enum(ShippingStatus), default=ShippingStatus.PENDING)

    # Poids
    weight: Mapped[float | None] = mapped_column(Float)

    # Articles inclus
    items: Mapped[dict | None] = mapped_column(JSON)  # [{"order_item_id": 1, "quantity": 2}]

    # Dates
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_shipment_order', 'tenant_id', 'order_id'),
        Index('idx_ecom_shipment_tracking', 'tenant_id', 'tracking_number'),
    )


# ============================================================================
# MODÈLES PROMOTIONS
# ============================================================================

class Coupon(Base):
    """Code promo / Coupon."""
    __tablename__ = "ecommerce_coupons"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Code
    code: Mapped[str | None] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    # Type de réduction
    discount_type: Mapped[str | None] = mapped_column(Enum(DiscountType), nullable=False)
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=False)

    # Conditions
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Plafond

    # Limites d'utilisation
    usage_limit: Mapped[int | None] = mapped_column(Integer)  # Total
    usage_limit_per_customer: Mapped[int | None] = mapped_column(Integer)  # Par client
    usage_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Validité
    starts_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Restrictions
    product_ids: Mapped[dict | None] = mapped_column(JSON)  # Produits spécifiques
    category_ids: Mapped[dict | None] = mapped_column(JSON)  # Catégories spécifiques
    customer_ids: Mapped[dict | None] = mapped_column(JSON)  # Clients spécifiques

    # Options
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_first_order_only: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_combinable: Mapped[bool | None] = mapped_column(Boolean, default=False)  # Cumulable

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index('idx_ecom_coupon_code', 'tenant_id', 'code', unique=True),
    )


# ============================================================================
# MODÈLES CLIENT E-COMMERCE
# ============================================================================

class EcommerceCustomer(Base):
    """Client e-commerce (extension du CRM)."""
    __tablename__ = "ecommerce_customers"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)

    # Lien CRM
    crm_customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # FK vers commercial.customers

    # Compte
    email: Mapped[str | None] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))  # Si compte créé

    # Informations
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(50))

    # Adresses par défaut
    default_billing_address_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    default_shipping_address_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Marketing
    accepts_marketing: Mapped[bool | None] = mapped_column(Boolean, default=False)
    marketing_opt_in_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Statistiques
    total_orders: Mapped[int | None] = mapped_column(Integer, default=0)
    total_spent: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    average_order_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Tags
    tags: Mapped[dict | None] = mapped_column(JSON)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Statut
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_customer_email', 'tenant_id', 'email', unique=True),
    )


class CustomerAddress(Base):
    """Adresse client."""
    __tablename__ = "ecommerce_customer_addresses"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_customers.id"), nullable=False)

    # Type
    address_type: Mapped[str | None] = mapped_column(String(20), default="both")  # billing, shipping, both

    # Adresse
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(255))
    address1: Mapped[str | None] = mapped_column(String(255), nullable=False)
    address2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2), nullable=False)
    province: Mapped[str | None] = mapped_column(String(100))  # État/Région
    phone: Mapped[str | None] = mapped_column(String(50))

    # Défaut
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MODÈLES REVIEWS
# ============================================================================

class ProductReview(Base):
    """Avis produit."""
    __tablename__ = "ecommerce_product_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_products.id"), nullable=False)

    # Auteur
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_customers.id"))
    author_name: Mapped[str | None] = mapped_column(String(100))
    author_email: Mapped[str | None] = mapped_column(String(255))

    # Avis
    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)

    # Commande vérifiée
    order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    is_verified_purchase: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Modération
    is_approved: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Réponse vendeur
    vendor_response: Mapped[str | None] = mapped_column(Text)
    vendor_responded_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Utilité
    helpful_votes: Mapped[int | None] = mapped_column(Integer, default=0)
    unhelpful_votes: Mapped[int | None] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_review_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# MODÈLES WISHLIST
# ============================================================================

class Wishlist(Base):
    """Liste de souhaits."""
    __tablename__ = "ecommerce_wishlists"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_customers.id"), nullable=False)

    # Informations
    name: Mapped[str | None] = mapped_column(String(255), default="Ma liste")
    is_public: Mapped[bool | None] = mapped_column(Boolean, default=False)
    share_token: Mapped[str | None] = mapped_column(String(100))

    # Audit
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WishlistItem(Base):
    """Article dans une wishlist."""
    __tablename__ = "ecommerce_wishlist_items"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(50), nullable=False, index=True)
    wishlist_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_wishlists.id"), nullable=False)

    product_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("ecommerce_products.id"), nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Prix au moment de l'ajout (pour alertes)
    added_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Audit
    added_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
