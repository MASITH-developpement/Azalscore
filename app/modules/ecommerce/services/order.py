"""
AZALS MODULE 12 - E-Commerce Order Service
============================================

Gestion des commandes et checkout.
"""
from __future__ import annotations


import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import desc

from app.modules.ecommerce.models import (
    CartItem,
    CartStatus,
    Coupon,
    EcommerceCart,
    EcommerceOrder,
    EcommerceProduct,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    ShippingMethod,
    ShippingStatus,
)
from app.modules.ecommerce.schemas import CheckoutRequest, OrderStatusUpdate

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class OrderService(BaseEcommerceService[EcommerceOrder]):
    """Service de gestion des commandes."""

    model = EcommerceOrder

    def checkout(
        self,
        data: CheckoutRequest,
    ) -> Tuple[Optional[EcommerceOrder], str]:
        """Processus de checkout complet."""
        logger.info(
            "Creating order | tenant=%s cart_id=%s email=%s",
            self.tenant_id,
            data.cart_id,
            data.customer_email,
        )

        cart = (
            self.db.query(EcommerceCart)
            .filter(
                EcommerceCart.tenant_id == self.tenant_id,
                EcommerceCart.id == data.cart_id,
            )
            .first()
        )

        if not cart:
            logger.warning("Checkout failed | cart_id=%s not found", data.cart_id)
            return None, "Panier non trouvé"

        if cart.status != CartStatus.ACTIVE:
            logger.warning(
                "Checkout failed | cart_id=%s invalid status=%s",
                data.cart_id,
                cart.status,
            )
            return None, "Panier invalide"

        items = (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart.id,
            )
            .all()
        )

        if not items:
            logger.warning("Checkout failed | cart_id=%s empty", data.cart_id)
            return None, "Panier vide"

        # Vérifier les stocks
        for item in items:
            product = (
                self.db.query(EcommerceProduct)
                .filter(
                    EcommerceProduct.tenant_id == self.tenant_id,
                    EcommerceProduct.id == item.product_id,
                )
                .first()
            )
            if product and product.track_inventory and not product.allow_backorder:
                if product.stock_quantity < item.quantity:
                    return None, f"Stock insuffisant pour {product.name}"

        # Récupérer la méthode de livraison
        shipping_method = (
            self.db.query(ShippingMethod)
            .filter(
                ShippingMethod.tenant_id == self.tenant_id,
                ShippingMethod.id == data.shipping_method_id,
            )
            .first()
        )

        if not shipping_method:
            return None, "Méthode de livraison invalide"

        # Calculer les frais de port
        shipping_total = shipping_method.price
        if (
            shipping_method.free_shipping_threshold
            and cart.subtotal >= shipping_method.free_shipping_threshold
        ):
            shipping_total = Decimal("0")

        cart.shipping_total = shipping_total
        self._recalculate_cart_totals(cart)

        # Créer la commande
        order_number = self._generate_order_number()
        shipping = data.shipping_address or data.billing_address

        order = EcommerceOrder(
            tenant_id=self.tenant_id,
            order_number=order_number,
            cart_id=cart.id,
            channel="web",
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            shipping_status=ShippingStatus.PENDING,
            currency=cart.currency,
            subtotal=cart.subtotal,
            discount_total=cart.discount_total,
            shipping_total=cart.shipping_total,
            tax_total=cart.tax_total,
            total=cart.total,
            coupon_codes=cart.coupon_codes,
            billing_first_name=data.billing_address.first_name,
            billing_last_name=data.billing_address.last_name,
            billing_company=data.billing_address.company,
            billing_address1=data.billing_address.address1,
            billing_address2=data.billing_address.address2,
            billing_city=data.billing_address.city,
            billing_postal_code=data.billing_address.postal_code,
            billing_country=data.billing_address.country,
            billing_phone=data.billing_address.phone,
            shipping_first_name=shipping.first_name,
            shipping_last_name=shipping.last_name,
            shipping_company=shipping.company,
            shipping_address1=shipping.address1,
            shipping_address2=shipping.address2,
            shipping_city=shipping.city,
            shipping_postal_code=shipping.postal_code,
            shipping_country=shipping.country,
            shipping_phone=shipping.phone,
            shipping_method=shipping_method.name,
            shipping_carrier=shipping_method.carrier,
            customer_notes=data.customer_notes,
        )

        self.db.add(order)
        self.db.flush()

        # Créer les lignes de commande
        for item in items:
            product = (
                self.db.query(EcommerceProduct)
                .filter(
                    EcommerceProduct.tenant_id == self.tenant_id,
                    EcommerceProduct.id == item.product_id,
                )
                .first()
            )

            order_item = OrderItem(
                tenant_id=self.tenant_id,
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                sku=product.sku if product else None,
                name=product.name if product else "Produit",
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                tax_amount=item.total_price * Decimal("0.20"),
                total=item.total_price,
                custom_options=item.custom_options,
            )
            self.db.add(order_item)

            # Décrémenter le stock
            if product and product.track_inventory:
                product.stock_quantity -= item.quantity
                product.sale_count += item.quantity

        # Marquer le panier comme converti
        cart.status = CartStatus.CONVERTED
        cart.converted_to_order_id = order.id
        cart.converted_at = datetime.utcnow()

        # Incrémenter les usages des coupons
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
                    coupon.usage_count += 1

        self.db.commit()
        self.db.refresh(order)

        logger.info(
            "Order created | order_id=%s number=%s items=%d total=%s",
            order.id,
            order.order_number,
            len(items),
            order.total,
        )
        return order, "Commande créée"

    def _generate_order_number(self) -> str:
        """Génère un numéro de commande unique."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:6].upper()
        return f"ORD-{timestamp}-{random_part}"

    def _recalculate_cart_totals(self, cart: EcommerceCart) -> None:
        """Recalcule les totaux du panier."""
        items = (
            self.db.query(CartItem)
            .filter(
                CartItem.tenant_id == self.tenant_id,
                CartItem.cart_id == cart.id,
            )
            .all()
        )

        subtotal = sum(item.total_price for item in items)
        cart.subtotal = subtotal

        taxable_amount = subtotal - cart.discount_total
        cart.tax_total = taxable_amount * Decimal("0.20")

        cart.total = (
            subtotal
            - cart.discount_total
            + cart.tax_total
            + cart.shipping_total
        )

    def get(self, order_id: int) -> Optional[EcommerceOrder]:
        """Récupère une commande."""
        return self._get_by_id(order_id)

    def get_by_number(self, order_number: str) -> Optional[EcommerceOrder]:
        """Récupère une commande par numéro."""
        return (
            self._base_query()
            .filter(EcommerceOrder.order_number == order_number)
            .first()
        )

    def get_items(self, order_id: int) -> List[OrderItem]:
        """Récupère les articles d'une commande."""
        return (
            self.db.query(OrderItem)
            .filter(
                OrderItem.tenant_id == self.tenant_id,
                OrderItem.order_id == order_id,
            )
            .all()
        )

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[OrderStatus] = None,
        customer_email: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[EcommerceOrder], int]:
        """Liste les commandes avec filtres."""
        query = self._base_query()

        if status:
            query = query.filter(EcommerceOrder.status == status)

        if customer_email:
            query = query.filter(EcommerceOrder.customer_email == customer_email)

        if date_from:
            query = query.filter(EcommerceOrder.created_at >= date_from)

        if date_to:
            query = query.filter(EcommerceOrder.created_at <= date_to)

        return self._list_paginated(
            query,
            page,
            page_size,
            EcommerceOrder.created_at,
            True,
        )

    def update_status(
        self,
        order_id: int,
        data: OrderStatusUpdate,
    ) -> Optional[EcommerceOrder]:
        """Met à jour le statut d'une commande."""
        order = self.get(order_id)
        if not order:
            return None

        if data.status:
            order.status = data.status

            if data.status == OrderStatus.CANCELLED:
                order.cancelled_at = datetime.utcnow()
            elif data.status == OrderStatus.REFUNDED:
                order.refunded_at = datetime.utcnow()

        if data.shipping_status:
            order.shipping_status = data.shipping_status

            if data.shipping_status == ShippingStatus.SHIPPED:
                order.shipped_at = datetime.utcnow()
            elif data.shipping_status == ShippingStatus.DELIVERED:
                order.delivered_at = datetime.utcnow()

        if data.tracking_number:
            order.tracking_number = data.tracking_number

        if data.tracking_url:
            order.tracking_url = data.tracking_url

        if data.internal_notes:
            order.internal_notes = data.internal_notes

        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel(self, order_id: int) -> Tuple[bool, str]:
        """Annule une commande et restaure le stock."""
        logger.info(
            "Cancelling order | tenant=%s order_id=%s",
            self.tenant_id,
            order_id,
        )

        order = self.get(order_id)
        if not order:
            return False, "Commande non trouvée"

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            logger.warning(
                "Cancel failed | order_id=%s status=%s",
                order_id,
                order.status,
            )
            return False, "Impossible d'annuler une commande expédiée"

        # Restaurer le stock
        items = self.get_items(order_id)
        for item in items:
            if item.product_id:
                product = (
                    self.db.query(EcommerceProduct)
                    .filter(
                        EcommerceProduct.tenant_id == self.tenant_id,
                        EcommerceProduct.id == item.product_id,
                    )
                    .first()
                )
                if product:
                    product.stock_quantity += item.quantity

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()

        self.db.commit()
        logger.info(
            "Order cancelled | order_id=%s items_restored=%d",
            order_id,
            len(items),
        )
        return True, "Commande annulée"
