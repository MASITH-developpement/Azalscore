"""
AZALS MODULE 12 - E-Commerce
=============================
Modèles SQLAlchemy pour la plateforme e-commerce enterprise.

Benchmark: Shopify, WooCommerce, Magento, BigCommerce
Target: ERP-native e-commerce avec intégration complète
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Float, Numeric, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Hiérarchie
    parent_id = Column(Integer, ForeignKey("ecommerce_categories.id"))

    # Informations
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text)

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))

    # Affichage
    image_url = Column(String(500))
    icon = Column(String(100))
    sort_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Configuration
    settings = Column(JSON)  # {"show_in_menu": true, "filters": [...]}

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Index
    __table_args__ = (
        Index('idx_ecom_cat_tenant_slug', 'tenant_id', 'slug', unique=True),
    )


class EcommerceProduct(Base):
    """Produit e-commerce."""
    __tablename__ = "ecommerce_products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identifiants
    sku = Column(String(100), nullable=False)
    barcode = Column(String(100))

    # Lien avec module Articles existant
    item_id = Column(Integer)  # FK vers items si applicable

    # Informations produit
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    short_description = Column(Text)
    description = Column(Text)

    # Type et statut
    product_type = Column(Enum(ProductType), default=ProductType.PHYSICAL)
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT)

    # Prix
    price = Column(Numeric(15, 2), nullable=False)
    compare_at_price = Column(Numeric(15, 2))  # Prix barré
    cost_price = Column(Numeric(15, 2))  # Prix de revient
    currency = Column(String(3), default="EUR")

    # Taxes
    tax_class = Column(String(50), default="standard")
    is_taxable = Column(Boolean, default=True)

    # Stock (synchronisé avec module Inventory)
    track_inventory = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    allow_backorder = Column(Boolean, default=False)

    # Poids et dimensions (livraison)
    weight = Column(Float)  # kg
    weight_unit = Column(String(10), default="kg")
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    dimension_unit = Column(String(10), default="cm")

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))

    # Médias
    images = Column(JSON)  # [{"url": "...", "alt": "...", "position": 1}]

    # Attributs personnalisés
    attributes = Column(JSON)  # {"color": "red", "size": "M"}

    # Catégories
    category_ids = Column(JSON)  # [1, 2, 3]

    # Tags
    tags = Column(JSON)  # ["new", "sale", "featured"]

    # Visibilité
    is_visible = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    published_at = Column(DateTime)

    # Configuration
    settings = Column(JSON)

    # Statistiques
    view_count = Column(Integer, default=0)
    sale_count = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    __table_args__ = (
        Index('idx_ecom_prod_tenant_sku', 'tenant_id', 'sku', unique=True),
        Index('idx_ecom_prod_tenant_slug', 'tenant_id', 'slug'),
        Index('idx_ecom_prod_status', 'tenant_id', 'status'),
    )


class ProductVariant(Base):
    """Variante de produit (taille, couleur, etc.)."""
    __tablename__ = "ecommerce_product_variants"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("ecommerce_products.id"), nullable=False)

    # Identifiants
    sku = Column(String(100), nullable=False)
    barcode = Column(String(100))

    # Attributs de la variante
    name = Column(String(255))  # "Rouge - XL"
    options = Column(JSON)  # {"color": "red", "size": "XL"}

    # Prix (peut différer du produit parent)
    price = Column(Numeric(15, 2))
    compare_at_price = Column(Numeric(15, 2))
    cost_price = Column(Numeric(15, 2))

    # Stock
    stock_quantity = Column(Integer, default=0)

    # Poids/dimensions spécifiques
    weight = Column(Float)

    # Image spécifique
    image_url = Column(String(500))

    # Position
    position = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_var_tenant_sku', 'tenant_id', 'sku', unique=True),
    )


# ============================================================================
# MODÈLES PANIER
# ============================================================================

class EcommerceCart(Base):
    """Panier d'achat."""
    __tablename__ = "ecommerce_carts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identifiant unique pour visiteurs anonymes
    session_id = Column(String(255), index=True)

    # Client (si connecté)
    customer_id = Column(Integer)

    # Statut
    status = Column(Enum(CartStatus), default=CartStatus.ACTIVE)

    # Devise
    currency = Column(String(3), default="EUR")

    # Totaux (calculés)
    subtotal = Column(Numeric(15, 2), default=0)
    discount_total = Column(Numeric(15, 2), default=0)
    tax_total = Column(Numeric(15, 2), default=0)
    shipping_total = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Codes promo appliqués
    coupon_codes = Column(JSON)  # ["CODE1", "CODE2"]

    # Notes
    notes = Column(Text)

    # Métadonnées
    metadata = Column(JSON)  # Infos tracking, UTM, etc.

    # Abandon
    abandoned_at = Column(DateTime)
    recovery_email_sent = Column(Boolean, default=False)

    # Conversion
    converted_to_order_id = Column(Integer)
    converted_at = Column(DateTime)

    # Expiration
    expires_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_cart_session', 'tenant_id', 'session_id'),
        Index('idx_ecom_cart_customer', 'tenant_id', 'customer_id'),
        Index('idx_ecom_cart_status', 'tenant_id', 'status'),
    )


class CartItem(Base):
    """Article dans un panier."""
    __tablename__ = "ecommerce_cart_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    cart_id = Column(Integer, ForeignKey("ecommerce_carts.id"), nullable=False)

    # Produit
    product_id = Column(Integer, ForeignKey("ecommerce_products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("ecommerce_product_variants.id"))

    # Quantité
    quantity = Column(Integer, nullable=False, default=1)

    # Prix au moment de l'ajout
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Réductions sur cette ligne
    discount_amount = Column(Numeric(15, 2), default=0)

    # Options personnalisées
    custom_options = Column(JSON)  # {"engraving": "John"}

    # Audit
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MODÈLES COMMANDE
# ============================================================================

class EcommerceOrder(Base):
    """Commande e-commerce."""
    __tablename__ = "ecommerce_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Numéro de commande
    order_number = Column(String(50), nullable=False)

    # Origine
    cart_id = Column(Integer, ForeignKey("ecommerce_carts.id"))
    channel = Column(String(50), default="web")  # web, mobile, api, pos

    # Client
    customer_id = Column(Integer)  # FK vers commercial.customers
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50))

    # Statuts
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    shipping_status = Column(Enum(ShippingStatus), default=ShippingStatus.PENDING)

    # Devise
    currency = Column(String(3), default="EUR")
    exchange_rate = Column(Numeric(10, 6), default=1)

    # Montants
    subtotal = Column(Numeric(15, 2), nullable=False)
    discount_total = Column(Numeric(15, 2), default=0)
    shipping_total = Column(Numeric(15, 2), default=0)
    tax_total = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)

    # Coupons
    coupon_codes = Column(JSON)

    # Adresse de facturation
    billing_first_name = Column(String(100))
    billing_last_name = Column(String(100))
    billing_company = Column(String(255))
    billing_address1 = Column(String(255))
    billing_address2 = Column(String(255))
    billing_city = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(2))
    billing_phone = Column(String(50))

    # Adresse de livraison
    shipping_first_name = Column(String(100))
    shipping_last_name = Column(String(100))
    shipping_company = Column(String(255))
    shipping_address1 = Column(String(255))
    shipping_address2 = Column(String(255))
    shipping_city = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(2))
    shipping_phone = Column(String(50))

    # Livraison
    shipping_method = Column(String(100))
    shipping_carrier = Column(String(100))
    tracking_number = Column(String(255))
    tracking_url = Column(String(500))

    # Dates estimées
    estimated_delivery_date = Column(DateTime)

    # Notes
    customer_notes = Column(Text)
    internal_notes = Column(Text)

    # Métadonnées
    metadata = Column(JSON)

    # Lien avec facturation AZALS
    invoice_id = Column(Integer)  # FK vers finance.invoices

    # IP et infos client
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # Dates importantes
    paid_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    refunded_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    __table_args__ = (
        Index('idx_ecom_order_number', 'tenant_id', 'order_number', unique=True),
        Index('idx_ecom_order_customer', 'tenant_id', 'customer_id'),
        Index('idx_ecom_order_status', 'tenant_id', 'status'),
        Index('idx_ecom_order_date', 'tenant_id', 'created_at'),
    )


class OrderItem(Base):
    """Ligne de commande."""
    __tablename__ = "ecommerce_order_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("ecommerce_orders.id"), nullable=False)

    # Produit (snapshot au moment de la commande)
    product_id = Column(Integer)
    variant_id = Column(Integer)
    sku = Column(String(100))
    name = Column(String(255), nullable=False)

    # Quantité
    quantity = Column(Integer, nullable=False)

    # Prix
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)

    # Taxes détaillées
    tax_rate = Column(Numeric(5, 2))
    tax_class = Column(String(50))

    # Options personnalisées
    custom_options = Column(JSON)

    # Statut de la ligne
    status = Column(String(50), default="pending")

    # Fulfillment
    quantity_fulfilled = Column(Integer, default=0)
    quantity_refunded = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# MODÈLES PAIEMENT
# ============================================================================

class EcommercePayment(Base):
    """Paiement de commande."""
    __tablename__ = "ecommerce_payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("ecommerce_orders.id"), nullable=False)

    # Référence externe (Stripe, PayPal, etc.)
    external_id = Column(String(255))
    provider = Column(String(50))  # stripe, paypal, bank_transfer

    # Montant
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Statut
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Méthode
    payment_method = Column(String(50))  # card, sepa, paypal
    card_brand = Column(String(20))  # visa, mastercard
    card_last4 = Column(String(4))

    # Détails
    details = Column(JSON)

    # Erreurs
    error_code = Column(String(50))
    error_message = Column(Text)

    # Dates
    authorized_at = Column(DateTime)
    captured_at = Column(DateTime)
    failed_at = Column(DateTime)
    refunded_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Informations
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)

    # Transporteur
    carrier = Column(String(100))

    # Prix
    price = Column(Numeric(15, 2), default=0)
    free_shipping_threshold = Column(Numeric(15, 2))  # Gratuit au-dessus de X€

    # Délais
    min_delivery_days = Column(Integer)
    max_delivery_days = Column(Integer)

    # Zones
    countries = Column(JSON)  # ["FR", "BE", "CH"]

    # Conditions
    min_order_amount = Column(Numeric(15, 2))
    max_order_amount = Column(Numeric(15, 2))
    min_weight = Column(Float)
    max_weight = Column(Float)

    # Statut
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_ship_method', 'tenant_id', 'code', unique=True),
    )


class Shipment(Base):
    """Expédition de commande."""
    __tablename__ = "ecommerce_shipments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("ecommerce_orders.id"), nullable=False)

    # Numéro d'expédition
    shipment_number = Column(String(50), nullable=False)

    # Transporteur
    carrier = Column(String(100))
    shipping_method = Column(String(100))

    # Tracking
    tracking_number = Column(String(255))
    tracking_url = Column(String(500))

    # Statut
    status = Column(Enum(ShippingStatus), default=ShippingStatus.PENDING)

    # Poids
    weight = Column(Float)

    # Articles inclus
    items = Column(JSON)  # [{"order_item_id": 1, "quantity": 2}]

    # Dates
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Notes
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Code
    code = Column(String(50), nullable=False)
    name = Column(String(255))
    description = Column(Text)

    # Type de réduction
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Numeric(15, 2), nullable=False)

    # Conditions
    min_order_amount = Column(Numeric(15, 2))
    max_discount_amount = Column(Numeric(15, 2))  # Plafond

    # Limites d'utilisation
    usage_limit = Column(Integer)  # Total
    usage_limit_per_customer = Column(Integer)  # Par client
    usage_count = Column(Integer, default=0)

    # Validité
    starts_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Restrictions
    product_ids = Column(JSON)  # Produits spécifiques
    category_ids = Column(JSON)  # Catégories spécifiques
    customer_ids = Column(JSON)  # Clients spécifiques

    # Options
    is_active = Column(Boolean, default=True)
    is_first_order_only = Column(Boolean, default=False)
    is_combinable = Column(Boolean, default=False)  # Cumulable

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    __table_args__ = (
        Index('idx_ecom_coupon_code', 'tenant_id', 'code', unique=True),
    )


# ============================================================================
# MODÈLES CLIENT E-COMMERCE
# ============================================================================

class EcommerceCustomer(Base):
    """Client e-commerce (extension du CRM)."""
    __tablename__ = "ecommerce_customers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien CRM
    crm_customer_id = Column(Integer)  # FK vers commercial.customers

    # Compte
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255))  # Si compte créé

    # Informations
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))

    # Adresses par défaut
    default_billing_address_id = Column(Integer)
    default_shipping_address_id = Column(Integer)

    # Marketing
    accepts_marketing = Column(Boolean, default=False)
    marketing_opt_in_at = Column(DateTime)

    # Statistiques
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(15, 2), default=0)
    average_order_value = Column(Numeric(15, 2), default=0)
    last_order_at = Column(DateTime)

    # Tags
    tags = Column(JSON)

    # Notes
    notes = Column(Text)

    # Statut
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_customer_email', 'tenant_id', 'email', unique=True),
    )


class CustomerAddress(Base):
    """Adresse client."""
    __tablename__ = "ecommerce_customer_addresses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("ecommerce_customers.id"), nullable=False)

    # Type
    address_type = Column(String(20), default="both")  # billing, shipping, both

    # Adresse
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    address1 = Column(String(255), nullable=False)
    address2 = Column(String(255))
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False)
    province = Column(String(100))  # État/Région
    phone = Column(String(50))

    # Défaut
    is_default = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MODÈLES REVIEWS
# ============================================================================

class ProductReview(Base):
    """Avis produit."""
    __tablename__ = "ecommerce_product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("ecommerce_products.id"), nullable=False)

    # Auteur
    customer_id = Column(Integer, ForeignKey("ecommerce_customers.id"))
    author_name = Column(String(100))
    author_email = Column(String(255))

    # Avis
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255))
    content = Column(Text)

    # Commande vérifiée
    order_id = Column(Integer)
    is_verified_purchase = Column(Boolean, default=False)

    # Modération
    is_approved = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)

    # Réponse vendeur
    vendor_response = Column(Text)
    vendor_responded_at = Column(DateTime)

    # Utilité
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ecom_review_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# MODÈLES WISHLIST
# ============================================================================

class Wishlist(Base):
    """Liste de souhaits."""
    __tablename__ = "ecommerce_wishlists"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("ecommerce_customers.id"), nullable=False)

    # Informations
    name = Column(String(255), default="Ma liste")
    is_public = Column(Boolean, default=False)
    share_token = Column(String(100))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WishlistItem(Base):
    """Article dans une wishlist."""
    __tablename__ = "ecommerce_wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    wishlist_id = Column(Integer, ForeignKey("ecommerce_wishlists.id"), nullable=False)

    product_id = Column(Integer, ForeignKey("ecommerce_products.id"), nullable=False)
    variant_id = Column(Integer)

    # Prix au moment de l'ajout (pour alertes)
    added_price = Column(Numeric(15, 2))

    # Audit
    added_at = Column(DateTime, default=datetime.utcnow)
