"""
Tests Ecommerce - Fixtures et configurations pytest
====================================================
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock
from uuid import uuid4

from app.core.saas_context import SaaSContext, UserRole, TenantScope


# ============================================================================
# MOCK SAAS CONTEXT
# ============================================================================

@pytest.fixture
def mock_saas_context():
    """Mock SaaSContext pour les tests."""
    return SaaSContext(
        tenant_id="test-tenant",
        user_id=uuid4(),
        role=UserRole.DIRIGEANT,
        permissions={"ecommerce.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id"
    )


@pytest.fixture
def mock_admin_context():
    """Mock SaaSContext avec rôle ADMIN."""
    return SaaSContext(
        tenant_id="test-tenant",
        user_id=uuid4(),
        role=UserRole.ADMIN,
        permissions={"ecommerce.*"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id"
    )


@pytest.fixture
def mock_employee_context():
    """Mock SaaSContext avec rôle EMPLOYE (accès limité)."""
    return SaaSContext(
        tenant_id="test-tenant",
        user_id=uuid4(),
        role=UserRole.EMPLOYE,
        permissions={"ecommerce.product.read"},
        scope=TenantScope.TENANT,
        ip_address="127.0.0.1",
        user_agent="pytest",
        correlation_id="test-correlation-id"
    )


# ============================================================================
# FIXTURES DATA
# ============================================================================

@pytest.fixture
def category_data():
    """Données de catégorie."""
    return {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic products",
        "is_visible": True,
        "sort_order": 1
    }


@pytest.fixture
def product_data():
    """Données de produit."""
    return {
        "name": "Laptop HP",
        "slug": "laptop-hp",
        "sku": "LAP-HP-001",
        "description": "High-performance laptop",
        "price": Decimal("999.99"),
        "compare_at_price": Decimal("1299.99"),
        "stock_quantity": 10,
        "category_ids": [1, 2],
        "is_featured": True,
        "track_inventory": True
    }


@pytest.fixture
def variant_data():
    """Données de variante."""
    return {
        "product_id": 1,
        "name": "16GB RAM",
        "sku": "LAP-HP-001-16GB",
        "price": Decimal("1099.99"),
        "stock_quantity": 5,
        "position": 1,
        "option_values": {"ram": "16GB", "color": "Silver"}
    }


@pytest.fixture
def customer_data():
    """Données de client."""
    return {
        "email": "customer@test.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+33612345678",
        "accepts_marketing": True
    }


@pytest.fixture
def customer_address_data():
    """Données d'adresse client."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Corp",
        "address1": "123 Test St",
        "address2": "Apt 4",
        "city": "Paris",
        "postal_code": "75001",
        "country": "FR",
        "phone": "+33612345678",
        "is_default": True
    }


@pytest.fixture
def cart_item_data():
    """Données d'item de panier."""
    return {
        "product_id": 1,
        "variant_id": None,
        "quantity": 2,
        "custom_options": {"engraving": "Test"}
    }


@pytest.fixture
def checkout_data():
    """Données de checkout."""
    return {
        "cart_id": 1,
        "customer_email": "customer@test.com",
        "customer_phone": "+33612345678",
        "billing_address": {
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Test St",
            "city": "Paris",
            "postal_code": "75001",
            "country": "FR",
            "phone": "+33612345678"
        },
        "shipping_address": None,
        "shipping_method_id": 1,
        "customer_notes": "Please deliver after 6pm"
    }


@pytest.fixture
def payment_intent_data():
    """Données d'intention de paiement."""
    return {
        "order_id": 1,
        "payment_method": "card"
    }


@pytest.fixture
def shipping_method_data():
    """Données de méthode de livraison."""
    return {
        "name": "Standard Shipping",
        "carrier": "La Poste",
        "price": Decimal("5.99"),
        "min_delivery_days": 3,
        "max_delivery_days": 5,
        "is_active": True,
        "countries": ["FR", "BE", "LU"],
        "sort_order": 1
    }


@pytest.fixture
def shipment_data():
    """Données d'expédition."""
    return {
        "order_id": 1,
        "carrier": "La Poste",
        "tracking_number": "FR123456789",
        "items": [{"product_id": 1, "quantity": 2}]
    }


@pytest.fixture
def review_data():
    """Données d'avis."""
    return {
        "product_id": 1,
        "rating": 5,
        "title": "Excellent product",
        "content": "Very satisfied with this purchase",
        "author_name": "John D."
    }


@pytest.fixture
def coupon_data():
    """Données de coupon."""
    return {
        "code": "SAVE20",
        "discount_type": "percentage",
        "discount_value": Decimal("20"),
        "min_order_amount": Decimal("50"),
        "max_discount_amount": Decimal("100"),
        "usage_limit": 100,
        "is_active": True,
        "starts_at": datetime.utcnow(),
        "expires_at": None
    }


@pytest.fixture
def wishlist_item_data():
    """Données d'item de wishlist."""
    return {
        "product_id": 1,
        "variant_id": None
    }


# ============================================================================
# FIXTURES ENTITÉS
# ============================================================================

@pytest.fixture
def mock_category():
    """Mock d'une catégorie."""
    category = Mock()
    category.id = 1
    category.tenant_id = "test-tenant"
    category.name = "Electronics"
    category.slug = "electronics"
    category.description = "Electronic products"
    category.is_visible = True
    category.sort_order = 1
    category.parent_id = None
    category.created_at = datetime.utcnow()
    category.updated_at = datetime.utcnow()
    return category


@pytest.fixture
def mock_product():
    """Mock d'un produit."""
    product = Mock()
    product.id = 1
    product.tenant_id = "test-tenant"
    product.name = "Laptop HP"
    product.slug = "laptop-hp"
    product.sku = "LAP-HP-001"
    product.description = "High-performance laptop"
    product.price = Decimal("999.99")
    product.compare_at_price = Decimal("1299.99")
    product.status = "active"
    product.stock_quantity = 10
    product.category_ids = [1, 2]
    product.is_featured = True
    product.track_inventory = True
    product.created_at = datetime.utcnow()
    product.updated_at = datetime.utcnow()
    return product


@pytest.fixture
def mock_variant():
    """Mock d'une variante."""
    variant = Mock()
    variant.id = 1
    variant.tenant_id = "test-tenant"
    variant.product_id = 1
    variant.name = "16GB RAM"
    variant.sku = "LAP-HP-001-16GB"
    variant.price = Decimal("1099.99")
    variant.stock_quantity = 5
    variant.position = 1
    variant.option_values = {"ram": "16GB", "color": "Silver"}
    variant.created_at = datetime.utcnow()
    variant.updated_at = datetime.utcnow()
    return variant


@pytest.fixture
def mock_customer():
    """Mock d'un client."""
    customer = Mock()
    customer.id = 1
    customer.tenant_id = "test-tenant"
    customer.email = "customer@test.com"
    customer.first_name = "John"
    customer.last_name = "Doe"
    customer.phone = "+33612345678"
    customer.accepts_marketing = True
    customer.created_at = datetime.utcnow()
    customer.updated_at = datetime.utcnow()
    return customer


@pytest.fixture
def mock_cart():
    """Mock d'un panier."""
    cart = Mock()
    cart.id = 1
    cart.tenant_id = "test-tenant"
    cart.session_id = "test-session"
    cart.customer_id = None
    cart.status = "active"
    cart.currency = "EUR"
    cart.subtotal = Decimal("999.99")
    cart.discount_total = Decimal("0")
    cart.tax_total = Decimal("199.99")
    cart.shipping_total = Decimal("5.99")
    cart.total = Decimal("1205.97")
    cart.coupon_codes = []
    cart.created_at = datetime.utcnow()
    cart.updated_at = datetime.utcnow()
    return cart


@pytest.fixture
def mock_cart_item():
    """Mock d'un item de panier."""
    item = Mock()
    item.id = 1
    item.tenant_id = "test-tenant"
    item.cart_id = 1
    item.product_id = 1
    item.variant_id = None
    item.quantity = 2
    item.unit_price = Decimal("999.99")
    item.total_price = Decimal("1999.98")
    item.custom_options = {}
    item.created_at = datetime.utcnow()
    return item


@pytest.fixture
def mock_order():
    """Mock d'une commande."""
    order = Mock()
    order.id = 1
    order.tenant_id = "test-tenant"
    order.order_number = "ORD-20250125-ABC123"
    order.cart_id = 1
    order.customer_email = "customer@test.com"
    order.customer_phone = "+33612345678"
    order.status = "pending"
    order.payment_status = "pending"
    order.shipping_status = "pending"
    order.currency = "EUR"
    order.subtotal = Decimal("999.99")
    order.discount_total = Decimal("0")
    order.tax_total = Decimal("199.99")
    order.shipping_total = Decimal("5.99")
    order.total = Decimal("1205.97")
    order.created_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    return order


@pytest.fixture
def mock_payment():
    """Mock d'un paiement."""
    payment = Mock()
    payment.id = 1
    payment.tenant_id = "test-tenant"
    payment.order_id = 1
    payment.amount = Decimal("1205.97")
    payment.currency = "EUR"
    payment.provider = "stripe"
    payment.payment_method = "card"
    payment.status = "pending"
    payment.created_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()
    return payment


@pytest.fixture
def mock_shipping_method():
    """Mock d'une méthode de livraison."""
    method = Mock()
    method.id = 1
    method.tenant_id = "test-tenant"
    method.name = "Standard Shipping"
    method.carrier = "La Poste"
    method.price = Decimal("5.99")
    method.min_delivery_days = 3
    method.max_delivery_days = 5
    method.is_active = True
    method.countries = ["FR", "BE", "LU"]
    method.free_shipping_threshold = None
    method.sort_order = 1
    method.created_at = datetime.utcnow()
    return method


@pytest.fixture
def mock_shipment():
    """Mock d'une expédition."""
    shipment = Mock()
    shipment.id = 1
    shipment.tenant_id = "test-tenant"
    shipment.order_id = 1
    shipment.shipment_number = "SHP-20250125-DEF456"
    shipment.carrier = "La Poste"
    shipment.tracking_number = "FR123456789"
    shipment.status = "ready_to_ship"
    shipment.created_at = datetime.utcnow()
    shipment.updated_at = datetime.utcnow()
    return shipment


@pytest.fixture
def mock_coupon():
    """Mock d'un coupon."""
    coupon = Mock()
    coupon.id = 1
    coupon.tenant_id = "test-tenant"
    coupon.code = "SAVE20"
    coupon.discount_type = "percentage"
    coupon.discount_value = Decimal("20")
    coupon.min_order_amount = Decimal("50")
    coupon.max_discount_amount = Decimal("100")
    coupon.usage_limit = 100
    coupon.usage_count = 10
    coupon.is_active = True
    coupon.starts_at = datetime.utcnow()
    coupon.expires_at = None
    coupon.created_at = datetime.utcnow()
    return coupon


@pytest.fixture
def mock_review():
    """Mock d'un avis."""
    review = Mock()
    review.id = 1
    review.tenant_id = "test-tenant"
    review.product_id = 1
    review.customer_id = 1
    review.rating = 5
    review.title = "Excellent product"
    review.content = "Very satisfied with this purchase"
    review.author_name = "John D."
    review.is_approved = False
    review.created_at = datetime.utcnow()
    return review


@pytest.fixture
def mock_wishlist():
    """Mock d'une wishlist."""
    wishlist = Mock()
    wishlist.id = 1
    wishlist.tenant_id = "test-tenant"
    wishlist.customer_id = 1
    wishlist.name = "My Wishlist"
    wishlist.is_public = False
    wishlist.created_at = datetime.utcnow()
    return wishlist


# ============================================================================
# HELPERS ASSERTIONS
# ============================================================================

def assert_category_response(response_data: dict):
    """Vérifie qu'une réponse de catégorie est valide."""
    assert "id" in response_data
    assert "name" in response_data
    assert "slug" in response_data
    assert "is_visible" in response_data


def assert_product_response(response_data: dict):
    """Vérifie qu'une réponse de produit est valide."""
    assert "id" in response_data
    assert "name" in response_data
    assert "sku" in response_data
    assert "price" in response_data
    assert "status" in response_data


def assert_order_response(response_data: dict):
    """Vérifie qu'une réponse de commande est valide."""
    assert "id" in response_data
    assert "order_number" in response_data
    assert "customer_email" in response_data
    assert "status" in response_data
    assert "total" in response_data


def assert_cart_response(response_data: dict):
    """Vérifie qu'une réponse de panier est valide."""
    assert "id" in response_data
    assert "status" in response_data
    assert "total" in response_data
    assert "items" in response_data
    assert "item_count" in response_data


def assert_payment_response(response_data: dict):
    """Vérifie qu'une réponse de paiement est valide."""
    assert "id" in response_data
    assert "order_id" in response_data
    assert "amount" in response_data
    assert "status" in response_data
    assert "payment_method" in response_data


def assert_coupon_response(response_data: dict):
    """Vérifie qu'une réponse de coupon est valide."""
    assert "id" in response_data
    assert "code" in response_data
    assert "discount_type" in response_data
    assert "discount_value" in response_data
    assert "is_active" in response_data
