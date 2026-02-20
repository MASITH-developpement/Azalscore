"""
AZALS MODULE 12 - E-Commerce Router v2 - CORE SaaS
====================================================
Endpoints API REST pour la plateforme e-commerce avec CORE SaaS v2.

MIGRATION CORE SaaS v2:
- Utilise SaaSContext au lieu de get_current_user + get_tenant_id
- Pattern: context: SaaSContext = Depends(get_saas_context)
- Factory: get_ecommerce_service(db, context.tenant_id, context.user_id)
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import OrderStatus, ProductStatus
from .schemas import (
    ApplyCouponRequest,
    CartItemAdd,
    CartItemUpdate,
    CartResponse,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CheckoutRequest,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateResponse,
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerLoginRequest,
    CustomerRegisterRequest,
    CustomerResponse,
    EcommerceDashboard,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    PaymentIntentRequest,
    PaymentResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ReviewCreate,
    ReviewResponse,
    ShipmentCreate,
    ShipmentResponse,
    ShippingMethodCreate,
    ShippingMethodResponse,
    ShippingRateRequest,
    ShippingRateResponse,
    VariantCreate,
    VariantResponse,
    VariantUpdate,
    WishlistItemAdd,
    WishlistResponse,
)
from .service import EcommerceService

router = APIRouter(prefix="/v2/ecommerce", tags=["E-Commerce v2 - CORE SaaS"])


def get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> EcommerceService:
    """Obtenir le service e-commerce avec CORE SaaS v2."""
    return EcommerceService(db, context.tenant_id, str(context.user_id))


# ============================================================================
# SÉCURITÉ: Fonctions de vérification des rôles (CORE SaaS v2)
# ============================================================================

def require_ecommerce_admin(context: SaaSContext) -> None:
    """Vérifie que l'utilisateur a un rôle admin pour e-commerce."""
    if not context.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN, DIRIGEANT ou SUPERADMIN requis pour cette opération."
        )


# ============================================================================
# CATEGORIES
# ============================================================================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer une catégorie produit."""
    require_ecommerce_admin(context)
    return service.create_category(data)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    parent_id: int | None = None,
    visible_only: bool = True,
    service: EcommerceService = Depends(get_service)
):
    """Lister les catégories."""
    return service.get_categories(parent_id=parent_id, visible_only=visible_only)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer une catégorie."""
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour une catégorie."""
    require_ecommerce_admin(context)
    category = service.update_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Supprimer une catégorie."""
    require_ecommerce_admin(context)
    if not service.delete_category(category_id):
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")


# ============================================================================
# PRODUCTS
# ============================================================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer un produit."""
    require_ecommerce_admin(context)
    return service.create_product(data)


@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    status: ProductStatus | None = None,
    search: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock_only: bool = False,
    featured_only: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    service: EcommerceService = Depends(get_service)
):
    """Lister les produits avec filtres."""
    products, total = service.list_products(
        page=page,
        page_size=page_size,
        category_id=category_id,
        status=status,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        featured_only=featured_only,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return {
        "items": products,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un produit."""
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.get("/products/slug/{slug}", response_model=ProductResponse)
def get_product_by_slug(
    slug: str,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un produit par slug."""
    product = service.get_product_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour un produit."""
    require_ecommerce_admin(context)
    product = service.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Archiver un produit."""
    require_ecommerce_admin(context)
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Produit non trouvé")


@router.post("/products/{product_id}/publish", response_model=ProductResponse)
def publish_product(
    product_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Publier un produit."""
    require_ecommerce_admin(context)
    product = service.publish_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.post("/products/{product_id}/stock")
def update_stock(
    product_id: int,
    quantity_change: int,
    variant_id: int | None = None,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Ajuster le stock d'un produit."""
    require_ecommerce_admin(context)
    if not service.update_stock(product_id, quantity_change, variant_id):
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"success": True, "message": "Stock mis à jour"}


# ============================================================================
# VARIANTS
# ============================================================================

@router.post("/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def create_variant(
    data: VariantCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer une variante produit."""
    require_ecommerce_admin(context)
    return service.create_variant(data)


@router.get("/products/{product_id}/variants", response_model=list[VariantResponse])
def list_variants(
    product_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Lister les variantes d'un produit."""
    return service.get_variants(product_id)


@router.put("/variants/{variant_id}", response_model=VariantResponse)
def update_variant(
    variant_id: int,
    data: VariantUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour une variante."""
    require_ecommerce_admin(context)
    variant = service.update_variant(variant_id, data)
    if not variant:
        raise HTTPException(status_code=404, detail="Variante non trouvée")
    return variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    variant_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Supprimer une variante."""
    require_ecommerce_admin(context)
    if not service.delete_variant(variant_id):
        raise HTTPException(status_code=404, detail="Variante non trouvée")


# ============================================================================
# CART
# ============================================================================

@router.post("/cart", response_model=CartResponse)
def get_or_create_cart(
    session_id: str | None = None,
    customer_id: int | None = None,
    service: EcommerceService = Depends(get_service)
):
    """Créer ou récupérer un panier."""
    cart = service.get_or_create_cart(session_id=session_id, customer_id=customer_id)
    items = service.get_cart_items(cart.id)

    return {
        **cart.__dict__,
        "items": items,
        "item_count": sum(i.quantity for i in items)
    }


@router.get("/cart/{cart_id}", response_model=CartResponse)
def get_cart(
    cart_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un panier."""
    cart = service.get_cart(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")

    items = service.get_cart_items(cart_id)
    return {
        **cart.__dict__,
        "items": items,
        "item_count": sum(i.quantity for i in items)
    }


@router.post("/cart/{cart_id}/items")
def add_to_cart(
    cart_id: int,
    data: CartItemAdd,
    service: EcommerceService = Depends(get_service)
):
    """Ajouter un article au panier."""
    item, message = service.add_to_cart(cart_id, data)
    if not item:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message, "item": item}


@router.put("/cart/{cart_id}/items/{item_id}")
def update_cart_item(
    cart_id: int,
    item_id: int,
    data: CartItemUpdate,
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour la quantité d'un article."""
    result, message = service.update_cart_item(cart_id, item_id, data.quantity)
    if result is None:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.delete("/cart/{cart_id}/items/{item_id}")
def remove_from_cart(
    cart_id: int,
    item_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Retirer un article du panier."""
    success, message = service.remove_from_cart(cart_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {"success": True, "message": message}


@router.delete("/cart/{cart_id}")
def clear_cart(
    cart_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Vider le panier."""
    success = service.clear_cart(cart_id)
    if not success:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    return {"success": True, "message": "Panier vidé"}


@router.post("/cart/{cart_id}/coupon")
def apply_coupon(
    cart_id: int,
    data: ApplyCouponRequest,
    service: EcommerceService = Depends(get_service)
):
    """Appliquer un code promo."""
    success, message, discount = service.apply_coupon(cart_id, data.code)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "discount_amount": float(discount) if discount else 0
    }


@router.delete("/cart/{cart_id}/coupon/{coupon_code}")
def remove_coupon(
    cart_id: int,
    coupon_code: str,
    service: EcommerceService = Depends(get_service)
):
    """Retirer un code promo."""
    service.remove_coupon(cart_id, coupon_code)
    return {"success": True, "message": "Code promo retiré"}


# ============================================================================
# CHECKOUT & ORDERS
# ============================================================================

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    data: CheckoutRequest,
    service: EcommerceService = Depends(get_service)
):
    """Finaliser la commande."""
    order, message = service.checkout(data)
    if not order:
        raise HTTPException(status_code=400, detail=message)

    items = service.get_order_items(order.id)
    return {**order.__dict__, "items": items}


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = None,
    customer_email: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Lister les commandes."""
    orders, total = service.list_orders(
        page=page,
        page_size=page_size,
        status=status,
        customer_email=customer_email,
        date_from=date_from,
        date_to=date_to
    )

    # Enrichir avec les items
    orders_with_items = []
    for order in orders:
        items = service.get_order_items(order.id)
        orders_with_items.append({**order.__dict__, "items": items})

    return {
        "items": orders_with_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer une commande."""
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    items = service.get_order_items(order_id)
    return {**order.__dict__, "items": items}


@router.get("/orders/number/{order_number}", response_model=OrderResponse)
def get_order_by_number(
    order_number: str,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer une commande par numéro."""
    order = service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    items = service.get_order_items(order.id)
    return {**order.__dict__, "items": items}


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour le statut d'une commande."""
    require_ecommerce_admin(context)
    order = service.update_order_status(order_id, data)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    items = service.get_order_items(order_id)
    return {**order.__dict__, "items": items}


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Annuler une commande."""
    require_ecommerce_admin(context)
    success, message = service.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


# ============================================================================
# PAYMENTS
# ============================================================================

@router.post("/payments/create", response_model=PaymentResponse)
def create_payment(
    data: PaymentIntentRequest,
    service: EcommerceService = Depends(get_service)
):
    """Créer une intention de paiement."""
    order = service.get_order(data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    payment = service.create_payment(
        order_id=data.order_id,
        amount=order.total,
        payment_method=data.payment_method
    )

    return payment


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    external_id: str,
    card_brand: str | None = None,
    card_last4: str | None = None,
    service: EcommerceService = Depends(get_service)
):
    """Confirmer un paiement."""
    payment = service.confirm_payment(
        payment_id=payment_id,
        external_id=external_id,
        card_brand=card_brand,
        card_last4=card_last4
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")

    return payment


@router.post("/payments/{payment_id}/fail")
def fail_payment(
    payment_id: int,
    error_code: str,
    error_message: str,
    service: EcommerceService = Depends(get_service)
):
    """Marquer un paiement comme échoué."""
    payment = service.fail_payment(payment_id, error_code, error_message)
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")

    return {"success": True, "message": "Paiement marqué comme échoué"}


# ============================================================================
# SHIPPING
# ============================================================================

@router.post("/shipping-methods", response_model=ShippingMethodResponse, status_code=status.HTTP_201_CREATED)
def create_shipping_method(
    data: ShippingMethodCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer une méthode de livraison."""
    require_ecommerce_admin(context)
    return service.create_shipping_method(data)


@router.get("/shipping-methods", response_model=list[ShippingMethodResponse])
def list_shipping_methods(
    country: str | None = None,
    cart_subtotal: Decimal | None = None,
    service: EcommerceService = Depends(get_service)
):
    """Lister les méthodes de livraison disponibles."""
    return service.get_shipping_methods(country=country, cart_subtotal=cart_subtotal)


@router.post("/shipping-rates", response_model=list[ShippingRateResponse])
def get_shipping_rates(
    data: ShippingRateRequest,
    service: EcommerceService = Depends(get_service)
):
    """Calculer les frais de port."""
    cart = service.get_cart(data.cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Panier non trouvé")

    methods = service.get_shipping_methods(
        country=data.country,
        cart_subtotal=cart.subtotal
    )

    rates = []
    for method in methods:
        price = method.price
        is_free = False

        if method.free_shipping_threshold and cart.subtotal >= method.free_shipping_threshold:
            price = Decimal('0')
            is_free = True

        rates.append({
            "method_id": method.id,
            "method_name": method.name,
            "carrier": method.carrier,
            "price": price,
            "is_free": is_free,
            "min_delivery_days": method.min_delivery_days,
            "max_delivery_days": method.max_delivery_days
        })

    return rates


@router.post("/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    data: ShipmentCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer une expédition."""
    require_ecommerce_admin(context)
    return service.create_shipment(data)


@router.post("/shipments/{shipment_id}/ship", response_model=ShipmentResponse)
def mark_shipped(
    shipment_id: int,
    tracking_number: str | None = None,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Marquer une expédition comme expédiée."""
    require_ecommerce_admin(context)
    shipment = service.mark_shipment_shipped(shipment_id, tracking_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition non trouvée")
    return shipment


# ============================================================================
# COUPONS
# ============================================================================

@router.post("/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    data: CouponCreate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Créer un coupon."""
    require_ecommerce_admin(context)
    return service.create_coupon(data)


@router.get("/coupons", response_model=list[CouponResponse])
def list_coupons(
    active_only: bool = True,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Lister les coupons."""
    require_ecommerce_admin(context)
    return service.list_coupons(active_only=active_only)


@router.get("/coupons/{coupon_id}", response_model=CouponResponse)
def get_coupon(
    coupon_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un coupon."""
    coupon = service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon non trouvé")
    return coupon


@router.get("/coupons/code/{code}", response_model=CouponResponse)
def get_coupon_by_code(
    code: str,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un coupon par code."""
    coupon = service.get_coupon_by_code(code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon non trouvé")
    return coupon


@router.post("/coupons/validate", response_model=CouponValidateResponse)
def validate_coupon(
    code: str,
    cart_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Valider un code promo."""
    cart = service.get_cart(cart_id)
    if not cart:
        return {"valid": False, "message": "Panier non trouvé"}

    coupon = service.get_coupon_by_code(code)
    if not coupon or not coupon.is_active:
        return {"valid": False, "message": "Code promo invalide"}

    # Calculer la réduction potentielle
    discount = service._calculate_coupon_discount(cart, coupon)

    return {
        "valid": True,
        "message": "Code promo valide",
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount
    }


@router.put("/coupons/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Mettre à jour un coupon."""
    require_ecommerce_admin(context)
    coupon = service.update_coupon(coupon_id, data)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon non trouvé")
    return coupon


@router.delete("/coupons/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(
    coupon_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Désactiver un coupon."""
    require_ecommerce_admin(context)
    if not service.delete_coupon(coupon_id):
        raise HTTPException(status_code=404, detail="Coupon non trouvé")


# ============================================================================
# CUSTOMERS
# ============================================================================

@router.post("/customers/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def register_customer(
    data: CustomerRegisterRequest,
    service: EcommerceService = Depends(get_service)
):
    """Inscrire un client."""
    customer, message = service.register_customer(data)
    if not customer:
        raise HTTPException(status_code=400, detail=message)
    return customer


@router.post("/customers/login", response_model=CustomerResponse)
def login_customer(
    data: CustomerLoginRequest,
    service: EcommerceService = Depends(get_service)
):
    """Connecter un client."""
    customer = service.authenticate_customer(data.email, data.password)
    if not customer:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer un client."""
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.post("/customers/{customer_id}/addresses", response_model=CustomerAddressResponse, status_code=status.HTTP_201_CREATED)
def add_customer_address(
    customer_id: int,
    data: CustomerAddressCreate,
    service: EcommerceService = Depends(get_service)
):
    """Ajouter une adresse client."""
    return service.add_customer_address(customer_id, data)


@router.get("/customers/{customer_id}/addresses", response_model=list[CustomerAddressResponse])
def list_customer_addresses(
    customer_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Lister les adresses d'un client."""
    return service.get_customer_addresses(customer_id)


@router.get("/customers/{customer_id}/orders", response_model=list[OrderResponse])
def list_customer_orders(
    customer_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Lister les commandes d'un client."""
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")

    orders, _ = service.list_orders(customer_email=customer.email)

    orders_with_items = []
    for order in orders:
        items = service.get_order_items(order.id)
        orders_with_items.append({**order.__dict__, "items": items})

    return orders_with_items


# ============================================================================
# REVIEWS
# ============================================================================

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    customer_id: int | None = None,
    service: EcommerceService = Depends(get_service)
):
    """Créer un avis produit."""
    return service.create_review(data, customer_id=customer_id)


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse])
def list_product_reviews(
    product_id: int,
    approved_only: bool = True,
    service: EcommerceService = Depends(get_service)
):
    """Lister les avis d'un produit."""
    return service.get_product_reviews(product_id, approved_only=approved_only)


@router.post("/reviews/{review_id}/approve")
def approve_review(
    review_id: int,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Approuver un avis."""
    require_ecommerce_admin(context)
    if not service.approve_review(review_id):
        raise HTTPException(status_code=404, detail="Avis non trouvé")
    return {"success": True, "message": "Avis approuvé"}


# ============================================================================
# WISHLIST
# ============================================================================

@router.get("/customers/{customer_id}/wishlist", response_model=WishlistResponse)
def get_wishlist(
    customer_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Récupérer la wishlist d'un client."""
    wishlist = service.get_or_create_wishlist(customer_id)

    return {
        "id": wishlist.id,
        "name": wishlist.name,
        "is_public": wishlist.is_public,
        "items": [],
        "created_at": wishlist.created_at
    }


@router.post("/customers/{customer_id}/wishlist/items")
def add_to_wishlist(
    customer_id: int,
    data: WishlistItemAdd,
    service: EcommerceService = Depends(get_service)
):
    """Ajouter un article à la wishlist."""
    item = service.add_to_wishlist(customer_id, data)
    return {"success": True, "message": "Article ajouté à la wishlist", "item_id": item.id}


@router.delete("/customers/{customer_id}/wishlist/items/{product_id}")
def remove_from_wishlist(
    customer_id: int,
    product_id: int,
    service: EcommerceService = Depends(get_service)
):
    """Retirer un article de la wishlist."""
    if not service.remove_from_wishlist(customer_id, product_id):
        raise HTTPException(status_code=404, detail="Article non trouvé dans la wishlist")
    return {"success": True, "message": "Article retiré de la wishlist"}


# ============================================================================
# DASHBOARD & ANALYTICS
# ============================================================================

@router.get("/dashboard", response_model=EcommerceDashboard)
def get_dashboard(
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Récupérer les statistiques du dashboard e-commerce."""
    require_ecommerce_admin(context)
    stats = service.get_dashboard_stats()
    top_products = service.get_top_selling_products()
    recent_orders = service.get_recent_orders()

    return {
        **stats,
        "top_selling_products": top_products,
        "recent_orders": recent_orders
    }


@router.get("/analytics/sales")
def get_sales_analytics(
    period: str = "month",  # day, week, month, year
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    context: SaaSContext = Depends(get_saas_context),
    service: EcommerceService = Depends(get_service)
):
    """Obtenir les analytics de ventes."""
    require_ecommerce_admin(context)
    # Simplified analytics
    stats = service.get_dashboard_stats()

    return {
        "period": period,
        "total_revenue": stats["total_revenue"],
        "total_orders": stats["total_orders"],
        "average_order_value": stats["average_order_value"]
    }
