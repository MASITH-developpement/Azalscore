"""
AZALS MODULE 12 - E-Commerce Schemas
=====================================
Schémas Pydantic pour validation et sérialisation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from .models import (
    ProductStatus, ProductType, OrderStatus, PaymentStatus,
    ShippingStatus, DiscountType, CartStatus
)


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    """Base catégorie."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    is_visible: bool = True
    is_featured: bool = False


class CategoryCreate(CategoryBase):
    """Création catégorie."""
    pass


class CategoryUpdate(BaseModel):
    """Mise à jour catégorie."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None
    is_featured: Optional[bool] = None


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
    alt: Optional[str] = None
    position: int = 0


class ProductBase(BaseModel):
    """Base produit."""
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    barcode: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    product_type: ProductType = ProductType.PHYSICAL
    price: Decimal = Field(..., ge=0)
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    currency: str = "EUR"
    tax_class: str = "standard"
    is_taxable: bool = True
    track_inventory: bool = True
    stock_quantity: int = 0
    low_stock_threshold: int = 5
    allow_backorder: bool = False
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    images: Optional[List[ProductImageSchema]] = None
    attributes: Optional[dict] = None
    category_ids: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    is_visible: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    """Création produit."""
    pass


class ProductUpdate(BaseModel):
    """Mise à jour produit."""
    sku: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    barcode: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    tax_class: Optional[str] = None
    is_taxable: Optional[bool] = None
    track_inventory: Optional[bool] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    allow_backorder: Optional[bool] = None
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    images: Optional[List[ProductImageSchema]] = None
    attributes: Optional[dict] = None
    category_ids: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    is_visible: Optional[bool] = None
    is_featured: Optional[bool] = None


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
    items: List[ProductResponse]
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
    name: Optional[str] = None
    options: dict = {}  # {"color": "red", "size": "XL"}
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    stock_quantity: int = 0
    weight: Optional[float] = None
    image_url: Optional[str] = None
    position: int = 0
    is_default: bool = False


class VariantCreate(VariantBase):
    """Création variante."""
    product_id: int


class VariantUpdate(BaseModel):
    """Mise à jour variante."""
    sku: Optional[str] = None
    name: Optional[str] = None
    options: Optional[dict] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
    position: Optional[int] = None
    is_default: Optional[bool] = None


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
    variant_id: Optional[int] = None
    quantity: int = Field(1, ge=1)
    custom_options: Optional[dict] = None


class CartItemUpdate(BaseModel):
    """Mise à jour article panier."""
    quantity: int = Field(..., ge=0)


class CartItemResponse(BaseModel):
    """Réponse article panier."""
    id: int
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    discount_amount: Decimal
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    sku: Optional[str] = None

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Réponse panier."""
    id: int
    tenant_id: str
    session_id: Optional[str] = None
    customer_id: Optional[int] = None
    status: CartStatus
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    shipping_total: Decimal
    total: Decimal
    coupon_codes: Optional[List[str]] = None
    items: List[CartItemResponse] = []
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
    company: Optional[str] = None
    address1: str = Field(..., min_length=1, max_length=255)
    address2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)
    phone: Optional[str] = None


class CheckoutRequest(BaseModel):
    """Demande de checkout."""
    cart_id: int
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    billing_address: AddressSchema
    shipping_address: Optional[AddressSchema] = None
    shipping_method_id: int
    payment_method: str = "card"  # card, paypal, bank_transfer
    customer_notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Réponse ligne de commande."""
    id: int
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    sku: Optional[str] = None
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
    customer_id: Optional[int] = None
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
    coupon_codes: Optional[List[str]] = None
    billing_first_name: Optional[str] = None
    billing_last_name: Optional[str] = None
    billing_address1: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    shipping_first_name: Optional[str] = None
    shipping_last_name: Optional[str] = None
    shipping_address1: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    items: List[OrderItemResponse] = []
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Liste de commandes paginée."""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class OrderStatusUpdate(BaseModel):
    """Mise à jour statut commande."""
    status: Optional[OrderStatus] = None
    shipping_status: Optional[ShippingStatus] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    internal_notes: Optional[str] = None


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentIntentRequest(BaseModel):
    """Création intention de paiement."""
    order_id: int
    payment_method: str = "card"
    return_url: Optional[str] = None


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
    payment_method_id: Optional[str] = None  # From Stripe


class PaymentResponse(BaseModel):
    """Réponse paiement."""
    id: int
    order_id: int
    external_id: Optional[str] = None
    provider: Optional[str] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: Optional[str] = None
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    captured_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# SHIPPING SCHEMAS
# ============================================================================

class ShippingMethodBase(BaseModel):
    """Base méthode de livraison."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    carrier: Optional[str] = None
    price: Decimal = Field(0, ge=0)
    free_shipping_threshold: Optional[Decimal] = None
    min_delivery_days: Optional[int] = None
    max_delivery_days: Optional[int] = None
    countries: Optional[List[str]] = None
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
    postal_code: Optional[str] = None


class ShippingRateResponse(BaseModel):
    """Réponse calcul frais de port."""
    method_id: int
    method_name: str
    carrier: Optional[str] = None
    price: Decimal
    is_free: bool
    min_delivery_days: Optional[int] = None
    max_delivery_days: Optional[int] = None


class ShipmentCreate(BaseModel):
    """Création expédition."""
    order_id: int
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    items: Optional[List[dict]] = None  # [{"order_item_id": 1, "quantity": 2}]


class ShipmentResponse(BaseModel):
    """Réponse expédition."""
    id: int
    tenant_id: str
    order_id: int
    shipment_number: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    status: ShippingStatus
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# COUPON SCHEMAS
# ============================================================================

class CouponBase(BaseModel):
    """Base coupon."""
    code: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    min_order_amount: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    usage_limit_per_customer: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    product_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    is_active: bool = True
    is_first_order_only: bool = False
    is_combinable: bool = False


class CouponCreate(CouponBase):
    """Création coupon."""
    pass


class CouponUpdate(BaseModel):
    """Mise à jour coupon."""
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    min_order_amount: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


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
    message: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerRegisterRequest(BaseModel):
    """Inscription client."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
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
    company: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    postal_code: str
    country: str
    province: Optional[str] = None
    phone: Optional[str] = None
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
    title: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = None


class ReviewResponse(BaseModel):
    """Réponse avis."""
    id: int
    product_id: int
    customer_id: Optional[int] = None
    author_name: Optional[str] = None
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    is_verified_purchase: bool
    is_approved: bool
    vendor_response: Optional[str] = None
    helpful_votes: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# WISHLIST SCHEMAS
# ============================================================================

class WishlistItemAdd(BaseModel):
    """Ajout article wishlist."""
    product_id: int
    variant_id: Optional[int] = None


class WishlistResponse(BaseModel):
    """Réponse wishlist."""
    id: int
    name: str
    is_public: bool
    items: List[dict] = []
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
    top_selling_products: List[dict]

    # Commandes récentes
    recent_orders: List[dict]


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
    by_date: List[dict]
    by_product: List[dict]
    by_category: List[dict]
    by_country: List[dict]
