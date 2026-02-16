"""
AZALS MODULE 12 - E-Commerce Cart Service
===========================================

Gestion du panier d'achat.
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from app.modules.ecommerce.models import (
    CartItem,
    CartStatus,
    Coupon,
    DiscountType,
    EcommerceCart,
    EcommerceProduct,
    ProductStatus,
    ProductVariant,
)
from app.modules.ecommerce.schemas import CartItemAdd

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class CartService(BaseEcommerceService[EcommerceCart]):
    """Service de gestion du panier."""

    model = EcommerceCart

    def get_or_create(
        self,
        session_id: Optional[str] = None,
        customer_id: Optional[int] = None,
    ) -> EcommerceCart:
        """Récupère ou crée un panier."""
        query = self._base_query().filter(EcommerceCart.status == CartStatus.ACTIVE)

        if customer_id:
            cart = query.filter(EcommerceCart.customer_id == customer_id).first()
        elif session_id:
            cart = query.filter(EcommerceCart.session_id == session_id).first()
        else:
            cart = None

        if not cart:
            cart = EcommerceCart(
                tenant_id=self.tenant_id,
                session_id=session_id or str(uuid.uuid4()),
                customer_id=customer_id,
                status=CartStatus.ACTIVE,
                currency="EUR",
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)

        return cart

    def get(self, cart_id: int) -> Optional[EcommerceCart]:
        """Récupère un panier."""
        return self._get_by_id(cart_id)

    def get_items(self, cart_id: int) -> List[CartItem]:
        """Récupère les articles du panier."""
        return (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart_id,
            )
            .all()
        )

    def add_item(
        self,
        cart_id: int,
        data: CartItemAdd,
    ) -> Tuple[Optional[CartItem], str]:
        """Ajoute un article au panier."""
        cart = self.get(cart_id)
        if not cart:
            return None, "Panier non trouvé"

        # Récupérer le produit
        product = (
            self.db.query(EcommerceProduct)
            .filter(
                EcommerceProduct.tenant_id == self.tenant_id,
                EcommerceProduct.id == data.product_id,
            )
            .first()
        )

        if not product:
            return None, "Produit non trouvé"

        if product.status != ProductStatus.ACTIVE:
            return None, "Produit non disponible"

        # Vérifier le stock
        if (
            product.track_inventory
            and not product.allow_backorder
            and product.stock_quantity < data.quantity
        ):
            return None, f"Stock insuffisant (disponible: {product.stock_quantity})"

        # Déterminer le prix
        price = product.price
        if data.variant_id:
            variant = (
                self.db.query(ProductVariant)
                .filter(
                    ProductVariant.tenant_id == self.tenant_id,
                    ProductVariant.id == data.variant_id,
                    ProductVariant.product_id == product.id,
                )
                .first()
            )
            if variant and variant.price:
                price = variant.price

        # Vérifier si l'article existe déjà
        existing_item = (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart_id,
                CartItem.product_id == data.product_id,
                CartItem.variant_id == data.variant_id,
            )
            .first()
        )

        if existing_item:
            existing_item.quantity += data.quantity
            existing_item.total_price = existing_item.unit_price * existing_item.quantity
            item = existing_item
        else:
            item = CartItem(
                tenant_id=self.tenant_id,
                cart_id=cart_id,
                product_id=data.product_id,
                variant_id=data.variant_id,
                quantity=data.quantity,
                unit_price=price,
                total_price=price * data.quantity,
                custom_options=data.custom_options,
            )
            self.db.add(item)

        self.db.flush()
        self._recalculate_totals(cart)

        self.db.commit()
        self.db.refresh(item)
        self.db.refresh(cart)
        return item, "Article ajouté"

    def update_item(
        self,
        cart_id: int,
        item_id: int,
        quantity: int,
    ) -> Tuple[Optional[CartItem], str]:
        """Met à jour la quantité d'un article."""
        item = (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart_id,
                CartItem.id == item_id,
            )
            .first()
        )

        if not item:
            return None, "Article non trouvé"

        if quantity <= 0:
            self.remove_item(cart_id, item_id)
            return None, "Article retiré"

        # Vérifier le stock
        product = (
            self.db.query(EcommerceProduct)
            .filter(
                EcommerceProduct.tenant_id == self.tenant_id,
                EcommerceProduct.id == item.product_id,
            )
            .first()
        )

        if product and product.track_inventory and not product.allow_backorder:
            if product.stock_quantity < quantity:
                return None, f"Stock insuffisant (disponible: {product.stock_quantity})"

        item.quantity = quantity
        item.total_price = item.unit_price * quantity

        cart = self.get(cart_id)
        self._recalculate_totals(cart)

        self.db.commit()
        self.db.refresh(item)
        return item, "Quantité mise à jour"

    def remove_item(self, cart_id: int, item_id: int) -> Tuple[bool, str]:
        """Retire un article du panier."""
        item = (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart_id,
                CartItem.id == item_id,
            )
            .first()
        )

        if not item:
            return False, "Article non trouvé"

        self.db.delete(item)

        cart = self.get(cart_id)
        self._recalculate_totals(cart)

        self.db.commit()
        return True, "Article retiré"

    def clear(self, cart_id: int) -> bool:
        """Vide le panier."""
        cart = self.get(cart_id)
        if not cart:
            return False

        self.db.query(CartItem).filter(
            CartItem.tenant_id == self.tenant_id,
            CartItem.cart_id == cart_id,
        ).delete()

        cart.subtotal = Decimal("0")
        cart.discount_total = Decimal("0")
        cart.tax_total = Decimal("0")
        cart.shipping_total = Decimal("0")
        cart.total = Decimal("0")
        cart.coupon_codes = None

        self.db.commit()
        return True

    def apply_coupon(
        self,
        cart_id: int,
        coupon_code: str,
    ) -> Tuple[bool, str, Optional[Decimal]]:
        """Applique un code promo au panier."""
        cart = self.get(cart_id)
        if not cart:
            return False, "Panier non trouvé", None

        coupon = (
            self.db.query(Coupon)
            .filter(
                Coupon.tenant_id == self.tenant_id,
                Coupon.code == coupon_code.upper(),
                Coupon.is_active == True,
            )
            .first()
        )

        if not coupon:
            return False, "Code promo invalide", None

        # Vérifier la validité
        now = datetime.utcnow()
        if coupon.starts_at and now < coupon.starts_at:
            return False, "Code promo pas encore actif", None

        if coupon.expires_at and now > coupon.expires_at:
            return False, "Code promo expiré", None

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return False, "Code promo épuisé", None

        if coupon.min_order_amount and cart.subtotal < coupon.min_order_amount:
            return False, f"Montant minimum requis: {coupon.min_order_amount}€", None

        # Calculer la réduction
        discount = self._calculate_coupon_discount(cart, coupon)

        # Appliquer
        existing_codes = cart.coupon_codes or []
        if coupon_code.upper() not in existing_codes:
            existing_codes.append(coupon_code.upper())
            cart.coupon_codes = existing_codes

        self._recalculate_totals(cart)
        self.db.commit()

        return True, "Code promo appliqué", discount

    def remove_coupon(self, cart_id: int, coupon_code: str) -> bool:
        """Retire un code promo du panier."""
        cart = self.get(cart_id)
        if not cart or not cart.coupon_codes:
            return False

        cart.coupon_codes = [
            c for c in cart.coupon_codes if c != coupon_code.upper()
        ]
        self._recalculate_totals(cart)
        self.db.commit()
        return True

    def _calculate_coupon_discount(
        self,
        cart: EcommerceCart,
        coupon: Coupon,
    ) -> Decimal:
        """Calcule la réduction d'un coupon."""
        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = cart.subtotal * (coupon.discount_value / 100)
        elif coupon.discount_type == DiscountType.FIXED_AMOUNT:
            discount = coupon.discount_value
        elif coupon.discount_type == DiscountType.FREE_SHIPPING:
            discount = cart.shipping_total
        else:
            discount = Decimal("0")

        if coupon.max_discount_amount and discount > coupon.max_discount_amount:
            discount = coupon.max_discount_amount

        return discount

    def _recalculate_totals(self, cart: EcommerceCart) -> None:
        """Recalcule les totaux du panier."""
        items = self.get_items(cart.id)

        subtotal = sum(item.total_price for item in items)
        cart.subtotal = subtotal

        discount_total = Decimal("0")
        if cart.coupon_codes:
            for code in cart.coupon_codes:
                coupon = (
                    self.db.query(Coupon)
                    .filter(
                        Coupon.tenant_id == self.tenant_id,
                        Coupon.code == code,
                    )
                    .first()
                )
                if coupon:
                    discount_total += self._calculate_coupon_discount(cart, coupon)

        cart.discount_total = discount_total

        taxable_amount = subtotal - discount_total
        cart.tax_total = taxable_amount * Decimal("0.20")  # TVA 20%

        cart.total = subtotal - discount_total + cart.tax_total + cart.shipping_total
