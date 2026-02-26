"""
AZALS MODULE 12 - E-Commerce Schemas
=====================================
Schémas Pydantic pour validation et sérialisation.
"""
from __future__ import annotations


from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from .models import CartStatus, DiscountType, OrderStatus, PaymentStatus, ProductStatus, ProductType, ShippingStatus

# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    """Base catégorie."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    parent_id: int | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    image_url: str | None = None
    sort_order: int = 0
    is_visible: bool = True
    is_featured: bool = False


class CategoryCreate(CategoryBase):
    """Création catégorie."""
    pass


class CategoryUpdate(BaseModel):
    """Mise à jour catégorie."""
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: int | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    image_url: str | None = None
    sort_order: int | None = None
    is_visible: bool | None = None
    is_featured: bool | None = None


class CategoryResponse(CategoryBase):
    """Réponse catégorie."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductImageSchema(BaseModel):
    """Image produit."""
    url: str
    alt: str | None = None
    position: int = 0


class ProductBase(BaseModel):
    """Base produit."""
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    barcode: str | None = None
    short_description: str | None = None
    description: str | None = None
    product_type: ProductType = ProductType.PHYSICAL
    price: Decimal = Field(..., ge=0)
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    currency: str = "EUR"
    tax_class: str = "standard"
    is_taxable: bool = True
    track_inventory: bool = True
    stock_quantity: int = 0
    low_stock_threshold: int = 5
    allow_backorder: bool = False
    weight: float | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    images: list[ProductImageSchema] | None = None
    attributes: dict | None = None
    category_ids: list[int] | None = None
    tags: list[str] | None = None
    is_visible: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    """Création produit."""
    pass


class ProductUpdate(BaseModel):
    """Mise à jour produit."""
    sku: str | None = None
    name: str | None = None
    slug: str | None = None
    barcode: str | None = None
    short_description: str | None = None
    description: str | None = None
    product_type: ProductType | None = None
    status: ProductStatus | None = None
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    cost_price: Decimal | None = None
    tax_class: str | None = None
    is_taxable: bool | None = None
    track_inventory: bool | None = None
    stock_quantity: int | None = None
    low_stock_threshold: int | None = None
    allow_backorder: bool | None = None
    weight: float | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    images: list[ProductImageSchema] | None = None
    attributes: dict | None = None
    category_ids: list[int] | None = None
    tags: list[str] | None = None
    is_visible: bool | None = None
    is_featured: bool | None = None


class ProductResponse(ProductBase):
    """Réponse produit."""
    id: int
    tenant_id: str
    status: ProductStatus
    view_count: int
    sale_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Liste de produits paginée."""
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# VARIANT SCHEMAS
# ============================================================================

class VariantBase(BaseModel):
    """Base variante."""
    sku: str = Field(..., min_length=1, max_length=100)
    name: str | None = None
    options: dict = {}  # {"color": "red", "size": "XL"}
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    stock_quantity: int = 0
    weight: float | None = None
    image_url: str | None = None
    position: int = 0
    is_default: bool = False


class VariantCreate(VariantBase):
    """Création variante."""
    product_id: int


class VariantUpdate(BaseModel):
    """Mise à jour variante."""
    sku: str | None = None
    name: str | None = None
    options: dict | None = None
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    stock_quantity: int | None = None
    weight: float | None = None
    image_url: str | None = None
    position: int | None = None
    is_default: bool | None = None


class VariantResponse(VariantBase):
    """Réponse variante."""
    id: int
    tenant_id: str
    product_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# CART SCHEMAS
# ============================================================================

class CartItemAdd(BaseModel):
    """Ajout article au panier."""
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(1, ge=1)
    custom_options: dict | None = None


class CartItemUpdate(BaseModel):
    """Mise à jour article panier."""
    quantity: int = Field(..., ge=0)


class CartItemResponse(BaseModel):
    """Réponse article panier."""
    id: int
    product_id: int
    variant_id: int | None = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    discount_amount: Decimal
    product_name: str | None = None
    product_image: str | None = None
    sku: str | None = None

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Réponse panier."""
    id: int
    tenant_id: str
    session_id: str | None = None
    customer_id: int | None = None
    status: CartStatus
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    shipping_total: Decimal
    total: Decimal
    coupon_codes: list[str] | None = None
    items: list[CartItemResponse] = []
    item_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplyCouponRequest(BaseModel):
    """Appliquer un coupon."""
    code: str = Field(..., min_length=1, max_length=50)


# ============================================================================
# ORDER SCHEMAS
# ============================================================================

class AddressSchema(BaseModel):
    """Adresse."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: str | None = None
    address1: str = Field(..., min_length=1, max_length=255)
    address2: str | None = None
    city: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)
    phone: str | None = None


class CheckoutRequest(BaseModel):
    """Demande de checkout."""
    cart_id: int
    customer_email: EmailStr
    customer_phone: str | None = None
    billing_address: AddressSchema
    shipping_address: AddressSchema | None = None
    shipping_method_id: int
    payment_method: str = "card"  # card, paypal, bank_transfer
    customer_notes: str | None = None


class OrderItemResponse(BaseModel):
    """Réponse ligne de commande."""
    id: int
    product_id: int | None = None
    variant_id: int | None = None
    sku: str | None = None
    name: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    status: str

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Réponse commande."""
    id: int
    tenant_id: str
    order_number: str
    channel: str
    customer_id: int | None = None
    customer_email: str
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_status: ShippingStatus
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    shipping_total: Decimal
    tax_total: Decimal
    total: Decimal
    coupon_codes: list[str] | None = None
    billing_first_name: str | None = None
    billing_last_name: str | None = None
    billing_address1: str | None = None
    billing_city: str | None = None
    billing_postal_code: str | None = None
    billing_country: str | None = None
    shipping_first_name: str | None = None
    shipping_last_name: str | None = None
    shipping_address1: str | None = None
    shipping_city: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str | None = None
    shipping_method: str | None = None
    tracking_number: str | None = None
    items: list[OrderItemResponse] = []
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Liste de commandes paginée."""
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class OrderStatusUpdate(BaseModel):
    """Mise à jour statut commande."""
    status: OrderStatus | None = None
    shipping_status: ShippingStatus | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    internal_notes: str | None = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentIntentRequest(BaseModel):
    """Création intention de paiement."""
    order_id: int
    payment_method: str = "card"
    return_url: str | None = None


class PaymentIntentResponse(BaseModel):
    """Réponse intention de paiement."""
    id: int
    client_secret: str
    amount: Decimal
    currency: str
    status: PaymentStatus

    model_config = {"from_attributes": True}


class PaymentConfirmRequest(BaseModel):
    """Confirmation de paiement."""
    payment_id: int
    payment_method_id: str | None = None  # From Stripe


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    order_id: int
    external_id: str | None = None
    provider: str | None = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str | None = None
    card_brand: str | None = None
    card_last4: str | None = None
    captured_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# SHIPPING SCHEMAS
# ============================================================================

class ShippingMethodBase(BaseModel):
    """Base méthode de livraison."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    carrier: str | None = None
    price: Decimal = Field(0, ge=0)
    free_shipping_threshold: Decimal | None = None
    min_delivery_days: int | None = None
    max_delivery_days: int | None = None
    countries: list[str] | None = None
    is_active: bool = True


class ShippingMethodCreate(ShippingMethodBase):
    """Création méthode de livraison."""
    pass


class ShippingMethodResponse(ShippingMethodBase):
    """Réponse méthode de livraison."""
    id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShippingRateRequest(BaseModel):
    """Demande de calcul de frais de port."""
    cart_id: int
    country: str = Field(..., min_length=2, max_length=2)
    postal_code: str | None = None


class ShippingRateResponse(BaseModel):
    """Réponse calcul frais de port."""
    method_id: int
    method_name: str
    carrier: str | None = None
    price: Decimal
    is_free: bool
    min_delivery_days: int | None = None
    max_delivery_days: int | None = None


class ShipmentCreate(BaseModel):
    """Création expédition."""
    order_id: int
    carrier: str | None = None
    tracking_number: str | None = None
    items: list[dict] | None = None  # [{"order_item_id": 1, "quantity": 2}]


class ShipmentResponse(BaseModel):
    """Réponse expédition."""
    id: int
    tenant_id: str
    order_id: int
    shipment_number: str
    carrier: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None
    status: ShippingStatus
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# COUPON SCHEMAS
# ============================================================================

class CouponBase(BaseModel):
    """Base coupon."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str | None = None
    description: str | None = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    min_order_amount: Decimal | None = None
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    usage_limit_per_customer: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    product_ids: list[int] | None = None
    category_ids: list[int] | None = None
    is_active: bool = True
    is_first_order_only: bool = False
    is_combinable: bool = False


class CouponCreate(CouponBase):
    """Création coupon."""
    pass


class CouponUpdate(BaseModel):
    """Mise à jour coupon."""
    name: str | None = None
    description: str | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    min_order_amount: Decimal | None = None
    max_discount_amount: Decimal | None = None
    usage_limit: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class CouponResponse(CouponBase):
    """Réponse coupon."""
    id: int
    tenant_id: str
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CouponValidateResponse(BaseModel):
    """Validation coupon."""
    valid: bool
    message: str | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    discount_amount: Decimal | None = None


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerRegisterRequest(BaseModel):
    """Inscription client."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = None
    accepts_marketing: bool = False


class CustomerLoginRequest(BaseModel):
    """Connexion client."""
    email: EmailStr
    password: str


class CustomerResponse(BaseModel):
    """Réponse client."""
    id: int
    tenant_id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    accepts_marketing: bool
    total_orders: int
    total_spent: Decimal
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerAddressCreate(BaseModel):
    """Création adresse client."""
    address_type: str = "both"
    first_name: str
    last_name: str
    company: str | None = None
    address1: str
    address2: str | None = None
    city: str
    postal_code: str
    country: str
    province: str | None = None
    phone: str | None = None
    is_default: bool = False


class CustomerAddressResponse(CustomerAddressCreate):
    """Réponse adresse client."""
    id: int

    model_config = {"from_attributes": True}


# ============================================================================
# REVIEW SCHEMAS
# ============================================================================

class ReviewCreate(BaseModel):
    """Création avis."""
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    title: str | None = None
    content: str | None = None
    author_name: str | None = None


class ReviewResponse(BaseModel):
    """Réponse avis."""
    id: int
    product_id: int
    customer_id: int | None = None
    author_name: str | None = None
    rating: int
    title: str | None = None
    content: str | None = None
    is_verified_purchase: bool
    is_approved: bool
    vendor_response: str | None = None
    helpful_votes: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# WISHLIST SCHEMAS
# ============================================================================

class WishlistItemAdd(BaseModel):
    """Ajout article wishlist."""
    product_id: int
    variant_id: int | None = None


class WishlistResponse(BaseModel):
    """Réponse wishlist."""
    id: int
    name: str
    is_public: bool
    items: list[dict] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class EcommerceDashboard(BaseModel):
    """Dashboard e-commerce."""
    # Ventes
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal

    # Période
    revenue_today: Decimal
    orders_today: int
    revenue_this_month: Decimal
    orders_this_month: int

    # Produits
    total_products: int
    active_products: int
    out_of_stock_products: int
    low_stock_products: int

    # Clients
    total_customers: int
    new_customers_this_month: int

    # Paniers
    active_carts: int
    abandoned_carts: int
    cart_abandonment_rate: float

    # Top produits
    top_selling_products: list[dict]

    # Commandes récentes
    recent_orders: list[dict]


class SalesReport(BaseModel):
    """Rapport de ventes."""
    period: str
    start_date: datetime
    end_date: datetime
    total_revenue: Decimal
    total_orders: int
    total_items_sold: int
    average_order_value: Decimal
    refunds: Decimal
    net_revenue: Decimal
    by_date: list[dict]
    by_product: list[dict]
    by_category: list[dict]
    by_country: list[dict]
