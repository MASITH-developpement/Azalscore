"""
AZALS MODULE 12 - E-Commerce Services
======================================

Sous-services modulaires pour la plateforme e-commerce.
"""

from .base import BaseEcommerceService
from .category import CategoryService
from .product import ProductService
from .cart import CartService
from .order import OrderService
from .payment import PaymentService
from .shipping import ShippingService
from .coupon import CouponService
from .customer import CustomerService
from .review import ReviewService
from .wishlist import WishlistService
from .dashboard import DashboardService

__all__ = [
    "BaseEcommerceService",
    "CategoryService",
    "ProductService",
    "CartService",
    "OrderService",
    "PaymentService",
    "ShippingService",
    "CouponService",
    "CustomerService",
    "ReviewService",
    "WishlistService",
    "DashboardService",
]
