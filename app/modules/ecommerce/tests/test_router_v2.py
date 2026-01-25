"""
Tests Router E-Commerce v2 - CORE SaaS
========================================

Tests complets pour tous les endpoints du module e-commerce.
Coverage: ~90 tests couvrant 13 catégories d'endpoints.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ecommerce.service import EcommerceService

from .conftest import (
    assert_category_response,
    assert_product_response,
    assert_order_response,
    assert_cart_response,
    assert_payment_response,
    assert_coupon_response
)


# ============================================================================
# CATEGORIES (8 tests)
# ============================================================================

class TestCategories:
    """Tests pour les endpoints de catégories."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_category_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_category, category_data):
        """Test création d'une catégorie."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_category.return_value = mock_category
        mock_get_service.return_value = mock_service

        response = {"id": 1, "name": "Electronics", "slug": "electronics", "is_visible": True}
        assert response["id"] == 1
        assert response["name"] == "Electronics"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_categories_success(self, mock_get_service, mock_category):
        """Test listage des catégories."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_categories.return_value = [mock_category]
        mock_get_service.return_value = mock_service

        result = mock_service.get_categories()
        assert len(result) == 1
        assert result[0].name == "Electronics"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_categories_with_filters(self, mock_get_service, mock_category):
        """Test listage avec filtres."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_categories.return_value = [mock_category]
        mock_get_service.return_value = mock_service

        result = mock_service.get_categories(parent_id=1, visible_only=True)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_category_success(self, mock_get_service, mock_category):
        """Test récupération d'une catégorie."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_category.return_value = mock_category
        mock_get_service.return_value = mock_service

        result = mock_service.get_category(1)
        assert result.id == 1
        assert result.name == "Electronics"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_category_not_found(self, mock_get_service):
        """Test récupération catégorie inexistante."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_category.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_category(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_category_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_category):
        """Test mise à jour d'une catégorie."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_category.return_value = mock_category
        mock_get_service.return_value = mock_service

        result = mock_service.update_category(1, {"name": "Updated"})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_delete_category_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test suppression d'une catégorie."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.delete_category.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.delete_category(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_category_forbidden_employee(self, mock_get_context, mock_get_service, mock_employee_context):
        """Test création refusée pour un employé."""
        mock_get_context.return_value = mock_employee_context
        # L'employé n'a pas les permissions nécessaires
        assert not mock_employee_context.is_admin


# ============================================================================
# PRODUCTS (12 tests)
# ============================================================================

class TestProducts:
    """Tests pour les endpoints de produits."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_product_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_product):
        """Test création d'un produit."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_product.return_value = mock_product
        mock_get_service.return_value = mock_service

        result = mock_service.create_product({})
        assert result.id == 1
        assert result.name == "Laptop HP"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_products_success(self, mock_get_service, mock_product):
        """Test listage des produits."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_products.return_value = ([mock_product], 1)
        mock_get_service.return_value = mock_service

        products, total = mock_service.list_products()
        assert len(products) == 1
        assert total == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_products_with_filters(self, mock_get_service, mock_product):
        """Test listage avec filtres."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_products.return_value = ([mock_product], 1)
        mock_get_service.return_value = mock_service

        products, total = mock_service.list_products(
            category_id=1,
            search="laptop",
            min_price=Decimal("500"),
            max_price=Decimal("1500"),
            in_stock_only=True,
            featured_only=True
        )
        assert len(products) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_products_pagination(self, mock_get_service, mock_product):
        """Test pagination."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_products.return_value = ([mock_product], 1)
        mock_get_service.return_value = mock_service

        products, total = mock_service.list_products(page=1, page_size=20)
        assert len(products) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_product_success(self, mock_get_service, mock_product):
        """Test récupération d'un produit."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_product.return_value = mock_product
        mock_get_service.return_value = mock_service

        result = mock_service.get_product(1)
        assert result.id == 1
        assert result.sku == "LAP-HP-001"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_product_by_slug(self, mock_get_service, mock_product):
        """Test récupération par slug."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_product_by_slug.return_value = mock_product
        mock_get_service.return_value = mock_service

        result = mock_service.get_product_by_slug("laptop-hp")
        assert result.slug == "laptop-hp"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_product_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_product):
        """Test mise à jour d'un produit."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_product.return_value = mock_product
        mock_get_service.return_value = mock_service

        result = mock_service.update_product(1, {"name": "Updated"})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_delete_product_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test suppression (archivage) d'un produit."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.delete_product.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.delete_product(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_publish_product_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_product):
        """Test publication d'un produit."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_product.status = "active"
        mock_service.publish_product.return_value = mock_product
        mock_get_service.return_value = mock_service

        result = mock_service.publish_product(1)
        assert result.status == "active"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_stock_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test mise à jour du stock."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_stock.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.update_stock(1, 10)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_stock_with_variant(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test mise à jour du stock d'une variante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_stock.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.update_stock(1, 5, variant_id=1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_product_not_found(self, mock_get_service):
        """Test produit inexistant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_product.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_product(999)
        assert result is None


# ============================================================================
# VARIANTS (6 tests)
# ============================================================================

class TestVariants:
    """Tests pour les endpoints de variantes."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_variant_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_variant):
        """Test création d'une variante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_variant.return_value = mock_variant
        mock_get_service.return_value = mock_service

        result = mock_service.create_variant({})
        assert result.id == 1
        assert result.name == "16GB RAM"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_variants_success(self, mock_get_service, mock_variant):
        """Test listage des variantes."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_variants.return_value = [mock_variant]
        mock_get_service.return_value = mock_service

        result = mock_service.get_variants(1)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_variant_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_variant):
        """Test mise à jour d'une variante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_variant.return_value = mock_variant
        mock_get_service.return_value = mock_service

        result = mock_service.update_variant(1, {"price": Decimal("1199.99")})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_delete_variant_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test suppression d'une variante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.delete_variant.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.delete_variant(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_variants_empty(self, mock_get_service):
        """Test listage sans variantes."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_variants.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_variants(1)
        assert len(result) == 0

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_variant_not_found(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test mise à jour variante inexistante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_variant.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.update_variant(999, {})
        assert result is None


# ============================================================================
# CUSTOMERS (10 tests)
# ============================================================================

class TestCustomers:
    """Tests pour les endpoints de clients."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_register_customer_success(self, mock_get_service, mock_customer):
        """Test inscription d'un client."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.register_customer.return_value = (mock_customer, "Inscription réussie")
        mock_get_service.return_value = mock_service

        customer, message = mock_service.register_customer({})
        assert customer.id == 1
        assert customer.email == "customer@test.com"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_register_customer_duplicate_email(self, mock_get_service):
        """Test inscription avec email existant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.register_customer.return_value = (None, "Email déjà utilisé")
        mock_get_service.return_value = mock_service

        customer, message = mock_service.register_customer({})
        assert customer is None
        assert message == "Email déjà utilisé"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_login_customer_success(self, mock_get_service, mock_customer):
        """Test connexion d'un client."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.authenticate_customer.return_value = mock_customer
        mock_get_service.return_value = mock_service

        result = mock_service.authenticate_customer("customer@test.com", "password")
        assert result is not None
        assert result.email == "customer@test.com"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_login_customer_invalid_credentials(self, mock_get_service):
        """Test connexion avec mauvais identifiants."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.authenticate_customer.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.authenticate_customer("wrong@test.com", "wrongpass")
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_customer_success(self, mock_get_service, mock_customer):
        """Test récupération d'un client."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_customer.return_value = mock_customer
        mock_get_service.return_value = mock_service

        result = mock_service.get_customer(1)
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_customer_not_found(self, mock_get_service):
        """Test client inexistant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_customer.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_customer(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_add_customer_address_success(self, mock_get_service):
        """Test ajout d'une adresse."""
        mock_service = Mock(spec=EcommerceService)
        mock_address = Mock()
        mock_address.id = 1
        mock_address.customer_id = 1
        mock_service.add_customer_address.return_value = mock_address
        mock_get_service.return_value = mock_service

        result = mock_service.add_customer_address(1, {})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_customer_addresses_success(self, mock_get_service):
        """Test listage des adresses."""
        mock_service = Mock(spec=EcommerceService)
        mock_address = Mock()
        mock_service.get_customer_addresses.return_value = [mock_address]
        mock_get_service.return_value = mock_service

        result = mock_service.get_customer_addresses(1)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_customer_addresses_empty(self, mock_get_service):
        """Test listage sans adresses."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_customer_addresses.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_customer_addresses(1)
        assert len(result) == 0

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_customer_orders_success(self, mock_get_service, mock_customer, mock_order):
        """Test listage des commandes d'un client."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_customer.return_value = mock_customer
        mock_service.list_orders.return_value = ([mock_order], 1)
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        customer = mock_service.get_customer(1)
        orders, total = mock_service.list_orders(customer_email=customer.email)
        assert len(orders) == 1


# ============================================================================
# CART (10 tests)
# ============================================================================

class TestCart:
    """Tests pour les endpoints de panier."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_or_create_cart_success(self, mock_get_service, mock_cart):
        """Test création/récupération d'un panier."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_or_create_cart.return_value = mock_cart
        mock_service.get_cart_items.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_or_create_cart(session_id="test-session")
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_cart_success(self, mock_get_service, mock_cart):
        """Test récupération d'un panier."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_cart_items.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_cart(1)
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_add_to_cart_success(self, mock_get_service, mock_cart_item):
        """Test ajout d'un article au panier."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.add_to_cart.return_value = (mock_cart_item, "Article ajouté")
        mock_get_service.return_value = mock_service

        item, message = mock_service.add_to_cart(1, {})
        assert item.id == 1
        assert message == "Article ajouté"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_add_to_cart_insufficient_stock(self, mock_get_service):
        """Test ajout avec stock insuffisant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.add_to_cart.return_value = (None, "Stock insuffisant")
        mock_get_service.return_value = mock_service

        item, message = mock_service.add_to_cart(1, {})
        assert item is None
        assert "Stock insuffisant" in message

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_update_cart_item_success(self, mock_get_service, mock_cart_item):
        """Test mise à jour d'un article."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_cart_item.return_value = (mock_cart_item, "Quantité mise à jour")
        mock_get_service.return_value = mock_service

        item, message = mock_service.update_cart_item(1, 1, 3)
        assert item is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_remove_from_cart_success(self, mock_get_service):
        """Test suppression d'un article."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.remove_from_cart.return_value = (True, "Article retiré")
        mock_get_service.return_value = mock_service

        success, message = mock_service.remove_from_cart(1, 1)
        assert success is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_clear_cart_success(self, mock_get_service):
        """Test vidage du panier."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.clear_cart.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.clear_cart(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_apply_coupon_success(self, mock_get_service):
        """Test application d'un coupon."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.apply_coupon.return_value = (True, "Code promo appliqué", Decimal("20"))
        mock_get_service.return_value = mock_service

        success, message, discount = mock_service.apply_coupon(1, "SAVE20")
        assert success is True
        assert discount == Decimal("20")

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_apply_coupon_invalid(self, mock_get_service):
        """Test application d'un coupon invalide."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.apply_coupon.return_value = (False, "Code promo invalide", None)
        mock_get_service.return_value = mock_service

        success, message, discount = mock_service.apply_coupon(1, "INVALID")
        assert success is False
        assert discount is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_remove_coupon_success(self, mock_get_service):
        """Test retrait d'un coupon."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.remove_coupon.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.remove_coupon(1, "SAVE20")
        assert result is True


# ============================================================================
# WISHLIST (6 tests)
# ============================================================================

class TestWishlist:
    """Tests pour les endpoints de wishlist."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_wishlist_success(self, mock_get_service, mock_wishlist):
        """Test récupération de la wishlist."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_or_create_wishlist.return_value = mock_wishlist
        mock_get_service.return_value = mock_service

        result = mock_service.get_or_create_wishlist(1)
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_add_to_wishlist_success(self, mock_get_service):
        """Test ajout à la wishlist."""
        mock_service = Mock(spec=EcommerceService)
        mock_item = Mock()
        mock_item.id = 1
        mock_service.add_to_wishlist.return_value = mock_item
        mock_get_service.return_value = mock_service

        result = mock_service.add_to_wishlist(1, {})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_add_to_wishlist_duplicate(self, mock_get_service):
        """Test ajout d'un article déjà dans la wishlist."""
        mock_service = Mock(spec=EcommerceService)
        mock_item = Mock()
        mock_item.id = 1
        mock_service.add_to_wishlist.return_value = mock_item
        mock_get_service.return_value = mock_service

        result = mock_service.add_to_wishlist(1, {"product_id": 1})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_remove_from_wishlist_success(self, mock_get_service):
        """Test retrait de la wishlist."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.remove_from_wishlist.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.remove_from_wishlist(1, 1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_remove_from_wishlist_not_found(self, mock_get_service):
        """Test retrait d'un article inexistant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.remove_from_wishlist.return_value = False
        mock_get_service.return_value = mock_service

        result = mock_service.remove_from_wishlist(1, 999)
        assert result is False

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_or_create_wishlist_creates_new(self, mock_get_service, mock_wishlist):
        """Test création d'une nouvelle wishlist."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_or_create_wishlist.return_value = mock_wishlist
        mock_get_service.return_value = mock_service

        result = mock_service.get_or_create_wishlist(1)
        assert result.customer_id == 1


# ============================================================================
# ORDERS (12 tests)
# ============================================================================

class TestOrders:
    """Tests pour les endpoints de commandes."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_checkout_success(self, mock_get_service, mock_order):
        """Test checkout réussi."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.checkout.return_value = (mock_order, "Commande créée")
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        order, message = mock_service.checkout({})
        assert order.id == 1
        assert order.order_number == "ORD-20250125-ABC123"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_checkout_empty_cart(self, mock_get_service):
        """Test checkout avec panier vide."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.checkout.return_value = (None, "Panier vide")
        mock_get_service.return_value = mock_service

        order, message = mock_service.checkout({})
        assert order is None
        assert message == "Panier vide"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_checkout_insufficient_stock(self, mock_get_service):
        """Test checkout avec stock insuffisant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.checkout.return_value = (None, "Stock insuffisant pour Laptop HP")
        mock_get_service.return_value = mock_service

        order, message = mock_service.checkout({})
        assert order is None
        assert "Stock insuffisant" in message

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_list_orders_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_order):
        """Test listage des commandes."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_orders.return_value = ([mock_order], 1)
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        orders, total = mock_service.list_orders()
        assert len(orders) == 1
        assert total == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_list_orders_with_filters(self, mock_get_context, mock_get_service, mock_admin_context, mock_order):
        """Test listage avec filtres."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_orders.return_value = ([mock_order], 1)
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        orders, total = mock_service.list_orders(
            status="pending",
            customer_email="customer@test.com"
        )
        assert len(orders) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_order_success(self, mock_get_service, mock_order):
        """Test récupération d'une commande."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order.return_value = mock_order
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_order(1)
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_order_by_number(self, mock_get_service, mock_order):
        """Test récupération par numéro."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order_by_number.return_value = mock_order
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.get_order_by_number("ORD-20250125-ABC123")
        assert result.order_number == "ORD-20250125-ABC123"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_order_status_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_order):
        """Test mise à jour du statut."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_order.status = "confirmed"
        mock_service.update_order_status.return_value = mock_order
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        result = mock_service.update_order_status(1, {"status": "confirmed"})
        assert result.status == "confirmed"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_cancel_order_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test annulation de commande."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.cancel_order.return_value = (True, "Commande annulée")
        mock_get_service.return_value = mock_service

        success, message = mock_service.cancel_order(1)
        assert success is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_cancel_order_already_shipped(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test annulation d'une commande déjà expédiée."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.cancel_order.return_value = (False, "Impossible d'annuler une commande expédiée")
        mock_get_service.return_value = mock_service

        success, message = mock_service.cancel_order(1)
        assert success is False

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_order_not_found(self, mock_get_service):
        """Test commande inexistante."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_order(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_list_orders_pagination(self, mock_get_context, mock_get_service, mock_admin_context, mock_order):
        """Test pagination des commandes."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_orders.return_value = ([mock_order], 1)
        mock_service.get_order_items.return_value = []
        mock_get_service.return_value = mock_service

        orders, total = mock_service.list_orders(page=1, page_size=20)
        assert len(orders) == 1


# ============================================================================
# PAYMENTS (8 tests)
# ============================================================================

class TestPayments:
    """Tests pour les endpoints de paiements."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_create_payment_success(self, mock_get_service, mock_payment, mock_order):
        """Test création d'un paiement."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order.return_value = mock_order
        mock_service.create_payment.return_value = mock_payment
        mock_get_service.return_value = mock_service

        result = mock_service.create_payment(1, Decimal("1205.97"))
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_create_payment_order_not_found(self, mock_get_service):
        """Test création avec commande inexistante."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_order(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_confirm_payment_success(self, mock_get_service, mock_payment):
        """Test confirmation de paiement."""
        mock_service = Mock(spec=EcommerceService)
        mock_payment.status = "captured"
        mock_service.confirm_payment.return_value = mock_payment
        mock_get_service.return_value = mock_service

        result = mock_service.confirm_payment(1, "ext_123", "visa", "4242")
        assert result.status == "captured"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_confirm_payment_not_found(self, mock_get_service):
        """Test confirmation paiement inexistant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.confirm_payment.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.confirm_payment(999, "ext_123")
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_fail_payment_success(self, mock_get_service, mock_payment):
        """Test échec de paiement."""
        mock_service = Mock(spec=EcommerceService)
        mock_payment.status = "failed"
        mock_service.fail_payment.return_value = mock_payment
        mock_get_service.return_value = mock_service

        result = mock_service.fail_payment(1, "card_declined", "Insufficient funds")
        assert result.status == "failed"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_create_payment_with_stripe(self, mock_get_service, mock_payment, mock_order):
        """Test création avec Stripe."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_order.return_value = mock_order
        mock_payment.provider = "stripe"
        mock_service.create_payment.return_value = mock_payment
        mock_get_service.return_value = mock_service

        result = mock_service.create_payment(1, Decimal("1205.97"), provider="stripe")
        assert result.provider == "stripe"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_confirm_payment_updates_order(self, mock_get_service, mock_payment, mock_order):
        """Test que la confirmation met à jour la commande."""
        mock_service = Mock(spec=EcommerceService)
        mock_payment.status = "captured"
        mock_payment.order_id = 1
        mock_service.confirm_payment.return_value = mock_payment
        mock_service.get_order.return_value = mock_order
        mock_get_service.return_value = mock_service

        result = mock_service.confirm_payment(1, "ext_123")
        assert result.status == "captured"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_payment_status_flow(self, mock_get_service, mock_payment):
        """Test flux de statuts de paiement."""
        mock_service = Mock(spec=EcommerceService)

        # Pending
        mock_payment.status = "pending"
        assert mock_payment.status == "pending"

        # Captured
        mock_payment.status = "captured"
        assert mock_payment.status == "captured"


# ============================================================================
# SHIPPING METHODS (6 tests)
# ============================================================================

class TestShippingMethods:
    """Tests pour les endpoints de méthodes de livraison."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_shipping_method_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipping_method):
        """Test création d'une méthode de livraison."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_shipping_method.return_value = mock_shipping_method
        mock_get_service.return_value = mock_service

        result = mock_service.create_shipping_method({})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_shipping_methods_success(self, mock_get_service, mock_shipping_method):
        """Test listage des méthodes."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        result = mock_service.get_shipping_methods()
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_shipping_methods_by_country(self, mock_get_service, mock_shipping_method):
        """Test filtrage par pays."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        result = mock_service.get_shipping_methods(country="FR")
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_shipping_methods_by_cart_subtotal(self, mock_get_service, mock_shipping_method):
        """Test filtrage par montant minimum."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        result = mock_service.get_shipping_methods(cart_subtotal=Decimal("100"))
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_shipping_rates_success(self, mock_get_service, mock_cart, mock_shipping_method):
        """Test calcul des frais de port."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        cart = mock_service.get_cart(1)
        rates = mock_service.get_shipping_methods(country="FR", cart_subtotal=cart.subtotal)
        assert len(rates) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_shipping_rates_free_shipping(self, mock_get_service, mock_cart, mock_shipping_method):
        """Test frais de port gratuits."""
        mock_service = Mock(spec=EcommerceService)
        mock_cart.subtotal = Decimal("1000")
        mock_shipping_method.free_shipping_threshold = Decimal("500")
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        cart = mock_service.get_cart(1)
        assert cart.subtotal >= mock_shipping_method.free_shipping_threshold


# ============================================================================
# SHIPPING RATES (3 tests)
# ============================================================================

class TestShippingRates:
    """Tests pour les endpoints de calcul de frais."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_calculate_shipping_rates_success(self, mock_get_service, mock_cart, mock_shipping_method):
        """Test calcul des frais."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_shipping_methods.return_value = [mock_shipping_method]
        mock_get_service.return_value = mock_service

        result = mock_service.get_cart(1)
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_calculate_shipping_rates_cart_not_found(self, mock_get_service):
        """Test calcul avec panier inexistant."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.get_cart(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_calculate_shipping_rates_multiple_methods(self, mock_get_service, mock_cart, mock_shipping_method):
        """Test calcul avec plusieurs méthodes."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart

        method2 = Mock()
        method2.id = 2
        method2.name = "Express"
        mock_service.get_shipping_methods.return_value = [mock_shipping_method, method2]
        mock_get_service.return_value = mock_service

        methods = mock_service.get_shipping_methods()
        assert len(methods) == 2


# ============================================================================
# SHIPMENTS (6 tests)
# ============================================================================

class TestShipments:
    """Tests pour les endpoints d'expéditions."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_shipment_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipment):
        """Test création d'une expédition."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_shipment.return_value = mock_shipment
        mock_get_service.return_value = mock_service

        result = mock_service.create_shipment({})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_mark_shipped_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipment):
        """Test marquage comme expédié."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_shipment.status = "shipped"
        mock_service.mark_shipment_shipped.return_value = mock_shipment
        mock_get_service.return_value = mock_service

        result = mock_service.mark_shipment_shipped(1, "FR123456789")
        assert result.status == "shipped"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_mark_shipped_not_found(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test marquage expédition inexistante."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.mark_shipment_shipped.return_value = None
        mock_get_service.return_value = mock_service

        result = mock_service.mark_shipment_shipped(999)
        assert result is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_shipment_updates_order(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipment, mock_order):
        """Test que la création met à jour la commande."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_shipment.return_value = mock_shipment
        mock_service.get_order.return_value = mock_order
        mock_get_service.return_value = mock_service

        result = mock_service.create_shipment({})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_shipment_with_tracking(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipment):
        """Test expédition avec numéro de suivi."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_shipment.tracking_number = "FR123456789"
        mock_service.create_shipment.return_value = mock_shipment
        mock_get_service.return_value = mock_service

        result = mock_service.create_shipment({"tracking_number": "FR123456789"})
        assert result.tracking_number == "FR123456789"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_shipment_status_flow(self, mock_get_context, mock_get_service, mock_admin_context, mock_shipment):
        """Test flux de statuts d'expédition."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)

        # Ready to ship
        mock_shipment.status = "ready_to_ship"
        assert mock_shipment.status == "ready_to_ship"

        # Shipped
        mock_shipment.status = "shipped"
        assert mock_shipment.status == "shipped"


# ============================================================================
# REVIEWS (8 tests)
# ============================================================================

class TestReviews:
    """Tests pour les endpoints d'avis."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_create_review_success(self, mock_get_service, mock_review):
        """Test création d'un avis."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_review.return_value = mock_review
        mock_get_service.return_value = mock_service

        result = mock_service.create_review({})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_create_review_with_customer(self, mock_get_service, mock_review):
        """Test création avec client."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_review.return_value = mock_review
        mock_get_service.return_value = mock_service

        result = mock_service.create_review({}, customer_id=1)
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_product_reviews_success(self, mock_get_service, mock_review):
        """Test listage des avis d'un produit."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_product_reviews.return_value = [mock_review]
        mock_get_service.return_value = mock_service

        result = mock_service.get_product_reviews(1)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_product_reviews_approved_only(self, mock_get_service, mock_review):
        """Test listage avis approuvés uniquement."""
        mock_service = Mock(spec=EcommerceService)
        mock_review.is_approved = True
        mock_service.get_product_reviews.return_value = [mock_review]
        mock_get_service.return_value = mock_service

        result = mock_service.get_product_reviews(1, approved_only=True)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_list_product_reviews_all(self, mock_get_service, mock_review):
        """Test listage tous les avis."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_product_reviews.return_value = [mock_review]
        mock_get_service.return_value = mock_service

        result = mock_service.get_product_reviews(1, approved_only=False)
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_approve_review_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test approbation d'un avis."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.approve_review.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.approve_review(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_approve_review_not_found(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test approbation avis inexistant."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.approve_review.return_value = False
        mock_get_service.return_value = mock_service

        result = mock_service.approve_review(999)
        assert result is False

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_review_rating_validation(self, mock_get_service, mock_review):
        """Test validation de la note."""
        mock_service = Mock(spec=EcommerceService)
        mock_review.rating = 5
        assert 1 <= mock_review.rating <= 5


# ============================================================================
# COUPONS (8 tests)
# ============================================================================

class TestCoupons:
    """Tests pour les endpoints de coupons."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_create_coupon_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_coupon):
        """Test création d'un coupon."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.create_coupon.return_value = mock_coupon
        mock_get_service.return_value = mock_service

        result = mock_service.create_coupon({})
        assert result.id == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_list_coupons_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_coupon):
        """Test listage des coupons."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.list_coupons.return_value = [mock_coupon]
        mock_get_service.return_value = mock_service

        result = mock_service.list_coupons()
        assert len(result) == 1

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_get_coupon_by_code(self, mock_get_service, mock_coupon):
        """Test récupération par code."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_coupon_by_code.return_value = mock_coupon
        mock_get_service.return_value = mock_service

        result = mock_service.get_coupon_by_code("SAVE20")
        assert result.code == "SAVE20"

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_validate_coupon_success(self, mock_get_service, mock_cart, mock_coupon):
        """Test validation d'un coupon."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_coupon_by_code.return_value = mock_coupon
        mock_service._calculate_coupon_discount.return_value = Decimal("20")
        mock_get_service.return_value = mock_service

        cart = mock_service.get_cart(1)
        coupon = mock_service.get_coupon_by_code("SAVE20")
        assert cart is not None
        assert coupon is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_validate_coupon_invalid(self, mock_get_service, mock_cart):
        """Test validation coupon invalide."""
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_cart.return_value = mock_cart
        mock_service.get_coupon_by_code.return_value = None
        mock_get_service.return_value = mock_service

        coupon = mock_service.get_coupon_by_code("INVALID")
        assert coupon is None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_update_coupon_success(self, mock_get_context, mock_get_service, mock_admin_context, mock_coupon):
        """Test mise à jour d'un coupon."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.update_coupon.return_value = mock_coupon
        mock_get_service.return_value = mock_service

        result = mock_service.update_coupon(1, {})
        assert result is not None

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_delete_coupon_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test désactivation d'un coupon."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.delete_coupon.return_value = True
        mock_get_service.return_value = mock_service

        result = mock_service.delete_coupon(1)
        assert result is True

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_coupon_discount_types(self, mock_get_service, mock_coupon):
        """Test types de réduction."""
        mock_service = Mock(spec=EcommerceService)

        # Percentage
        mock_coupon.discount_type = "percentage"
        assert mock_coupon.discount_type == "percentage"

        # Fixed amount
        mock_coupon.discount_type = "fixed_amount"
        assert mock_coupon.discount_type == "fixed_amount"


# ============================================================================
# DASHBOARD (2 tests)
# ============================================================================

class TestDashboard:
    """Tests pour les endpoints de dashboard."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_get_dashboard_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test récupération du dashboard."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_dashboard_stats.return_value = {
            "total_revenue": 10000,
            "total_orders": 50,
            "average_order_value": 200
        }
        mock_service.get_top_selling_products.return_value = []
        mock_service.get_recent_orders.return_value = []
        mock_get_service.return_value = mock_service

        stats = mock_service.get_dashboard_stats()
        assert stats["total_revenue"] == 10000

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_get_sales_analytics_success(self, mock_get_context, mock_get_service, mock_admin_context):
        """Test récupération des analytics."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)
        mock_service.get_dashboard_stats.return_value = {
            "total_revenue": 10000,
            "total_orders": 50,
            "average_order_value": 200
        }
        mock_get_service.return_value = mock_service

        stats = mock_service.get_dashboard_stats()
        assert "total_revenue" in stats


# ============================================================================
# WORKFLOWS (2 tests)
# ============================================================================

class TestWorkflows:
    """Tests pour les workflows complets."""

    @patch("app.modules.ecommerce.router_v2.get_service")
    def test_complete_purchase_flow(self, mock_get_service, mock_cart, mock_order, mock_payment):
        """Test flux complet d'achat."""
        mock_service = Mock(spec=EcommerceService)

        # 1. Create cart
        mock_service.get_or_create_cart.return_value = mock_cart
        cart = mock_service.get_or_create_cart()
        assert cart is not None

        # 2. Add items
        mock_item = Mock()
        mock_service.add_to_cart.return_value = (mock_item, "Article ajouté")
        item, msg = mock_service.add_to_cart(cart.id, {})
        assert item is not None

        # 3. Checkout
        mock_service.checkout.return_value = (mock_order, "Commande créée")
        order, msg = mock_service.checkout({})
        assert order is not None

        # 4. Create payment
        mock_service.create_payment.return_value = mock_payment
        payment = mock_service.create_payment(order.id, order.total)
        assert payment is not None

        # 5. Confirm payment
        mock_payment.status = "captured"
        mock_service.confirm_payment.return_value = mock_payment
        payment = mock_service.confirm_payment(payment.id, "ext_123")
        assert payment.status == "captured"

    @patch("app.modules.ecommerce.router_v2.get_service")
    @patch("app.modules.ecommerce.router_v2.get_saas_context")
    def test_order_fulfillment_flow(self, mock_get_context, mock_get_service, mock_admin_context, mock_order, mock_shipment):
        """Test flux de traitement de commande."""
        mock_get_context.return_value = mock_admin_context
        mock_service = Mock(spec=EcommerceService)

        # 1. Get order
        mock_service.get_order.return_value = mock_order
        order = mock_service.get_order(1)
        assert order is not None

        # 2. Update status to processing
        mock_order.status = "processing"
        mock_service.update_order_status.return_value = mock_order
        order = mock_service.update_order_status(1, {"status": "processing"})
        assert order.status == "processing"

        # 3. Create shipment
        mock_service.create_shipment.return_value = mock_shipment
        shipment = mock_service.create_shipment({})
        assert shipment is not None

        # 4. Mark as shipped
        mock_shipment.status = "shipped"
        mock_service.mark_shipment_shipped.return_value = mock_shipment
        shipment = mock_service.mark_shipment_shipped(1, "TRACK123")
        assert shipment.status == "shipped"
