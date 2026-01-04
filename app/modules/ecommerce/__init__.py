"""
AZALS MODULE 12 - E-Commerce
=============================
Plateforme e-commerce enterprise intégrée à l'ERP.

Fonctionnalités:
- Catalogue produits avec variantes
- Paniers et checkout
- Commandes et paiements
- Livraison et expédition
- Codes promo et réductions
- Clients et comptes
- Avis produits
- Wishlist
- Dashboard et analytics

Intégrations AZALS:
- M1 Commercial (CRM clients)
- M2 Finance (facturation)
- M5 Inventory (stocks)
- T5 Country Packs (taxes multi-pays)
- T6 Broadcast (notifications)
"""

from .models import (
    EcommerceCategory,
    EcommerceProduct,
    ProductVariant,
    EcommerceCart,
    CartItem,
    EcommerceOrder,
    OrderItem,
    EcommercePayment,
    ShippingMethod,
    Shipment,
    Coupon,
    EcommerceCustomer,
    CustomerAddress,
    ProductReview,
    Wishlist,
    WishlistItem,
    ProductStatus,
    ProductType,
    OrderStatus,
    PaymentStatus,
    ShippingStatus,
    DiscountType,
    CartStatus
)

from .service import EcommerceService
from .router import router

__all__ = [
    # Models
    "EcommerceCategory",
    "EcommerceProduct",
    "ProductVariant",
    "EcommerceCart",
    "CartItem",
    "EcommerceOrder",
    "OrderItem",
    "EcommercePayment",
    "ShippingMethod",
    "Shipment",
    "Coupon",
    "EcommerceCustomer",
    "CustomerAddress",
    "ProductReview",
    "Wishlist",
    "WishlistItem",
    # Enums
    "ProductStatus",
    "ProductType",
    "OrderStatus",
    "PaymentStatus",
    "ShippingStatus",
    "DiscountType",
    "CartStatus",
    # Service & Router
    "EcommerceService",
    "router"
]
