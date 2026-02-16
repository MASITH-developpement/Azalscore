"""
AZALS MODULE 12 - E-Commerce Shipping Service
===============================================

Gestion des méthodes de livraison et expéditions.
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.modules.ecommerce.models import (
    EcommerceOrder,
    OrderStatus,
    Shipment,
    ShippingMethod,
    ShippingStatus,
)
from app.modules.ecommerce.schemas import ShipmentCreate, ShippingMethodCreate

from .base import BaseEcommerceService

logger = logging.getLogger(__name__)


class ShippingService(BaseEcommerceService[ShippingMethod]):
    """Service de gestion des livraisons."""

    model = ShippingMethod

    def create_method(self, data: ShippingMethodCreate) -> ShippingMethod:
        """Crée une méthode de livraison."""
        method = ShippingMethod(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.db.add(method)
        self.db.commit()
        self.db.refresh(method)
        return method

    def get_methods(
        self,
        country: Optional[str] = None,
        cart_subtotal: Optional[Decimal] = None,
    ) -> List[ShippingMethod]:
        """Liste les méthodes de livraison disponibles."""
        query = self._base_query().filter(ShippingMethod.is_active == True)
        methods = query.order_by(ShippingMethod.sort_order).all()

        # Filtrer par pays si spécifié
        if country:
            methods = [
                m for m in methods if not m.countries or country in m.countries
            ]

        # Filtrer par montant minimum
        if cart_subtotal:
            methods = [
                m
                for m in methods
                if not m.min_order_amount or cart_subtotal >= m.min_order_amount
            ]

        return methods

    def get_method(self, method_id: int) -> Optional[ShippingMethod]:
        """Récupère une méthode de livraison."""
        return self._get_by_id(method_id)

    def update_method(
        self,
        method_id: int,
        data: dict,
    ) -> Optional[ShippingMethod]:
        """Met à jour une méthode de livraison."""
        method = self.get_method(method_id)
        if not method:
            return None

        return self._update(method, data)

    def delete_method(self, method_id: int) -> bool:
        """Désactive une méthode de livraison."""
        method = self.get_method(method_id)
        if not method:
            return False

        method.is_active = False
        self.db.commit()
        return True

    # =========================================================================
    # SHIPMENTS
    # =========================================================================

    def create_shipment(self, data: ShipmentCreate) -> Shipment:
        """Crée une expédition."""
        shipment_number = (
            f"SHP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        shipment = Shipment(
            tenant_id=self.tenant_id,
            order_id=data.order_id,
            shipment_number=shipment_number,
            carrier=data.carrier,
            tracking_number=data.tracking_number,
            items=data.items,
            status=ShippingStatus.READY_TO_SHIP,
        )
        self.db.add(shipment)

        # Mettre à jour le statut de la commande
        order = (
            self.db.query(EcommerceOrder)
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.id == data.order_id,
            )
            .first()
        )
        if order:
            order.shipping_status = ShippingStatus.READY_TO_SHIP
            if data.tracking_number:
                order.tracking_number = data.tracking_number

        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def get_shipment(self, shipment_id: int) -> Optional[Shipment]:
        """Récupère une expédition."""
        return (
            self.db.query(Shipment)
            .filter(
                Shipment.tenant_id == self.tenant_id,
                Shipment.id == shipment_id,
            )
            .first()
        )

    def get_order_shipments(self, order_id: int) -> List[Shipment]:
        """Récupère les expéditions d'une commande."""
        return (
            self.db.query(Shipment)
            .filter(
                Shipment.tenant_id == self.tenant_id,
                Shipment.order_id == order_id,
            )
            .all()
        )

    def mark_shipped(
        self,
        shipment_id: int,
        tracking_number: Optional[str] = None,
    ) -> Optional[Shipment]:
        """Marque une expédition comme expédiée."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            return None

        shipment.status = ShippingStatus.SHIPPED
        shipment.shipped_at = datetime.utcnow()

        if tracking_number:
            shipment.tracking_number = tracking_number

        # Mettre à jour la commande
        order = (
            self.db.query(EcommerceOrder)
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.id == shipment.order_id,
            )
            .first()
        )
        if order:
            order.shipping_status = ShippingStatus.SHIPPED
            order.shipped_at = datetime.utcnow()
            order.status = OrderStatus.SHIPPED
            if tracking_number:
                order.tracking_number = tracking_number

        self.db.commit()
        self.db.refresh(shipment)

        logger.info(
            "Shipment shipped | shipment_id=%s order_id=%s tracking=%s",
            shipment_id,
            shipment.order_id,
            tracking_number,
        )
        return shipment

    def mark_delivered(self, shipment_id: int) -> Optional[Shipment]:
        """Marque une expédition comme livrée."""
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            return None

        shipment.status = ShippingStatus.DELIVERED
        shipment.delivered_at = datetime.utcnow()

        # Mettre à jour la commande
        order = (
            self.db.query(EcommerceOrder)
            .filter(
                EcommerceOrder.tenant_id == self.tenant_id,
                EcommerceOrder.id == shipment.order_id,
            )
            .first()
        )
        if order:
            order.shipping_status = ShippingStatus.DELIVERED
            order.delivered_at = datetime.utcnow()
            order.status = OrderStatus.DELIVERED

        self.db.commit()
        self.db.refresh(shipment)

        logger.info(
            "Shipment delivered | shipment_id=%s order_id=%s",
            shipment_id,
            shipment.order_id,
        )
        return shipment
