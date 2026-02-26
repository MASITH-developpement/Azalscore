"""
AZALSCORE Delivery Notes Service
=================================

Service de gestion des bons de livraison.

Fonctionnalités:
- Création et gestion des BL
- Listes de picking
- Expéditions et transporteurs
- Preuves de livraison
- Retours et avoirs
"""
from __future__ import annotations


import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class DeliveryStatus(str, Enum):
    """Statut d'un bon de livraison."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PICKING = "picking"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ShipmentStatus(str, Enum):
    """Statut d'une expédition."""
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class PickingStatus(str, Enum):
    """Statut de préparation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class DeliveryLine:
    """Ligne de bon de livraison."""
    id: str
    product_id: str
    product_name: str
    quantity_ordered: Decimal
    quantity_shipped: Decimal = Decimal("0")
    quantity_delivered: Decimal = Decimal("0")
    unit: str = "unit"
    lot_id: Optional[str] = None
    lot_number: Optional[str] = None
    serial_numbers: list[str] = field(default_factory=list)
    location_id: Optional[str] = None
    notes: Optional[str] = None

    @property
    def quantity_remaining(self) -> Decimal:
        """Quantité restante à livrer."""
        return self.quantity_ordered - self.quantity_shipped

    @property
    def is_complete(self) -> bool:
        """Vérifie si la ligne est complète."""
        return self.quantity_shipped >= self.quantity_ordered


@dataclass
class DeliveryNote:
    """Bon de livraison."""
    id: str
    tenant_id: str
    delivery_number: str
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    customer_id: str = ""
    customer_name: str = ""
    status: DeliveryStatus = DeliveryStatus.DRAFT
    lines: list[DeliveryLine] = field(default_factory=list)
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str = "FR"
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    scheduled_date: Optional[date] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    carrier_id: Optional[str] = None
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    weight_kg: Decimal = Decimal("0")
    packages_count: int = 1
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        """Nombre total de lignes."""
        return len(self.lines)

    @property
    def total_quantity(self) -> Decimal:
        """Quantité totale commandée."""
        return sum(line.quantity_ordered for line in self.lines)

    @property
    def shipped_quantity(self) -> Decimal:
        """Quantité totale expédiée."""
        return sum(line.quantity_shipped for line in self.lines)

    @property
    def completion_rate(self) -> Decimal:
        """Taux de complétion."""
        if self.total_quantity == 0:
            return Decimal("100")
        return (self.shipped_quantity / self.total_quantity * 100).quantize(Decimal("0.01"))

    @property
    def is_complete(self) -> bool:
        """Vérifie si le BL est complet."""
        return all(line.is_complete for line in self.lines)


@dataclass
class PickingLine:
    """Ligne de liste de picking."""
    id: str
    delivery_line_id: str
    product_id: str
    product_name: str
    location_id: str
    location_name: str
    quantity_to_pick: Decimal
    quantity_picked: Decimal = Decimal("0")
    lot_id: Optional[str] = None
    lot_number: Optional[str] = None
    picked_at: Optional[datetime] = None
    picker_id: Optional[str] = None


@dataclass
class PickingList:
    """Liste de préparation."""
    id: str
    tenant_id: str
    picking_number: str
    delivery_note_id: str
    delivery_number: str
    status: PickingStatus = PickingStatus.PENDING
    lines: list[PickingLine] = field(default_factory=list)
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def progress(self) -> Decimal:
        """Progression du picking."""
        total = sum(line.quantity_to_pick for line in self.lines)
        if total == 0:
            return Decimal("100")
        picked = sum(line.quantity_picked for line in self.lines)
        return (picked / total * 100).quantize(Decimal("0.01"))


@dataclass
class Shipment:
    """Expédition."""
    id: str
    tenant_id: str
    shipment_number: str
    delivery_note_id: str
    delivery_number: str
    carrier_id: str
    carrier_name: str
    tracking_number: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[date] = None
    actual_delivery: Optional[datetime] = None
    signature: Optional[str] = None
    proof_of_delivery_url: Optional[str] = None
    weight_kg: Decimal = Decimal("0")
    packages_count: int = 1
    shipping_cost: Decimal = Decimal("0")
    notes: Optional[str] = None
    tracking_history: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReturnRequest:
    """Demande de retour."""
    id: str
    tenant_id: str
    return_number: str
    delivery_note_id: str
    delivery_number: str
    customer_id: str
    reason: str
    lines: list[dict] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# SERVICE
# =============================================================================


class DeliveryService:
    """
    Service de gestion des bons de livraison.

    Multi-tenant: OUI - Données isolées par tenant
    Fonctionnalités: BL, Picking, Expéditions, Livraisons
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ):
        if not tenant_id:
            raise ValueError("tenant_id est requis")

        self.db = db
        self.tenant_id = tenant_id
        self._notes: dict[str, DeliveryNote] = {}
        self._pickings: dict[str, PickingList] = {}
        self._shipments: dict[str, Shipment] = {}
        self._returns: dict[str, ReturnRequest] = {}
        self._note_counter = 1000
        self._picking_counter = 1000
        self._shipment_counter = 1000

        logger.info(f"DeliveryService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # DELIVERY NOTE MANAGEMENT
    # =========================================================================

    async def create_delivery_note(
        self,
        customer_id: str,
        customer_name: str,
        lines: list[dict],
        order_id: Optional[str] = None,
        order_number: Optional[str] = None,
        shipping_address: Optional[str] = None,
        shipping_city: Optional[str] = None,
        shipping_postal_code: Optional[str] = None,
        shipping_country: str = "FR",
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        scheduled_date: Optional[date] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> DeliveryNote:
        """Crée un bon de livraison."""
        self._note_counter += 1
        delivery_number = f"BL-{datetime.now().strftime('%Y%m')}-{self._note_counter:05d}"

        note = DeliveryNote(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            delivery_number=delivery_number,
            order_id=order_id,
            order_number=order_number,
            customer_id=customer_id,
            customer_name=customer_name,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            contact_name=contact_name,
            contact_phone=contact_phone,
            scheduled_date=scheduled_date,
            notes=notes,
            created_by=created_by,
            lines=[
                DeliveryLine(
                    id=str(uuid.uuid4()),
                    product_id=line["product_id"],
                    product_name=line.get("product_name", ""),
                    quantity_ordered=Decimal(str(line["quantity"])),
                    unit=line.get("unit", "unit"),
                    lot_id=line.get("lot_id"),
                    lot_number=line.get("lot_number"),
                    location_id=line.get("location_id"),
                )
                for line in lines
            ],
        )

        self._notes[note.id] = note

        logger.info(f"BL créé: {delivery_number} pour {customer_name}")
        return note

    async def get_delivery_note(self, note_id: str) -> Optional[DeliveryNote]:
        """Récupère un bon de livraison."""
        note = self._notes.get(note_id)
        if note and note.tenant_id == self.tenant_id:
            return note
        return None

    async def get_delivery_note_by_number(self, delivery_number: str) -> Optional[DeliveryNote]:
        """Récupère un BL par son numéro."""
        for note in self._notes.values():
            if note.tenant_id == self.tenant_id and note.delivery_number == delivery_number:
                return note
        return None

    async def list_delivery_notes(
        self,
        status: Optional[DeliveryStatus] = None,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> list[DeliveryNote]:
        """Liste les bons de livraison."""
        notes = [n for n in self._notes.values() if n.tenant_id == self.tenant_id]

        if status:
            notes = [n for n in notes if n.status == status]
        if customer_id:
            notes = [n for n in notes if n.customer_id == customer_id]
        if order_id:
            notes = [n for n in notes if n.order_id == order_id]
        if start_date:
            notes = [n for n in notes if n.created_at.date() >= start_date]
        if end_date:
            notes = [n for n in notes if n.created_at.date() <= end_date]

        return sorted(notes, key=lambda n: n.created_at, reverse=True)[:limit]

    async def confirm_delivery_note(self, note_id: str) -> Optional[DeliveryNote]:
        """Confirme un bon de livraison."""
        note = await self.get_delivery_note(note_id)
        if not note or note.status != DeliveryStatus.DRAFT:
            return None

        note.status = DeliveryStatus.CONFIRMED
        note.updated_at = datetime.now()

        logger.info(f"BL confirmé: {note.delivery_number}")
        return note

    async def cancel_delivery_note(
        self,
        note_id: str,
        reason: Optional[str] = None,
    ) -> Optional[DeliveryNote]:
        """Annule un bon de livraison."""
        note = await self.get_delivery_note(note_id)
        if not note or note.status in [DeliveryStatus.DELIVERED, DeliveryStatus.SHIPPED]:
            return None

        note.status = DeliveryStatus.CANCELLED
        note.metadata["cancel_reason"] = reason
        note.updated_at = datetime.now()

        logger.info(f"BL annulé: {note.delivery_number}")
        return note

    # =========================================================================
    # PICKING
    # =========================================================================

    async def create_picking_list(
        self,
        note_id: str,
        assigned_to: Optional[str] = None,
    ) -> Optional[PickingList]:
        """Crée une liste de picking pour un BL."""
        note = await self.get_delivery_note(note_id)
        if not note or note.status not in [DeliveryStatus.CONFIRMED, DeliveryStatus.DRAFT]:
            return None

        self._picking_counter += 1
        picking_number = f"PICK-{self._picking_counter:05d}"

        picking = PickingList(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            picking_number=picking_number,
            delivery_note_id=note.id,
            delivery_number=note.delivery_number,
            assigned_to=assigned_to,
            lines=[
                PickingLine(
                    id=str(uuid.uuid4()),
                    delivery_line_id=line.id,
                    product_id=line.product_id,
                    product_name=line.product_name,
                    location_id=line.location_id or "default",
                    location_name=line.location_id or "Stock",
                    quantity_to_pick=line.quantity_ordered,
                    lot_id=line.lot_id,
                    lot_number=line.lot_number,
                )
                for line in note.lines
            ],
        )

        self._pickings[picking.id] = picking
        note.status = DeliveryStatus.PICKING
        note.updated_at = datetime.now()

        logger.info(f"Picking créé: {picking_number}")
        return picking

    async def get_picking_list(self, picking_id: str) -> Optional[PickingList]:
        """Récupère une liste de picking."""
        picking = self._pickings.get(picking_id)
        if picking and picking.tenant_id == self.tenant_id:
            return picking
        return None

    async def start_picking(self, picking_id: str, picker_id: str) -> Optional[PickingList]:
        """Démarre le picking."""
        picking = await self.get_picking_list(picking_id)
        if not picking or picking.status != PickingStatus.PENDING:
            return None

        picking.status = PickingStatus.IN_PROGRESS
        picking.assigned_to = picker_id
        picking.started_at = datetime.now()

        return picking

    async def pick_line(
        self,
        picking_id: str,
        line_id: str,
        quantity_picked: Decimal,
        picker_id: Optional[str] = None,
    ) -> Optional[PickingList]:
        """Confirme le picking d'une ligne."""
        picking = await self.get_picking_list(picking_id)
        if not picking or picking.status not in [PickingStatus.PENDING, PickingStatus.IN_PROGRESS]:
            return None

        for line in picking.lines:
            if line.id == line_id:
                line.quantity_picked = min(quantity_picked, line.quantity_to_pick)
                line.picked_at = datetime.now()
                line.picker_id = picker_id
                break

        # Vérifier si picking complet
        if all(line.quantity_picked >= line.quantity_to_pick for line in picking.lines):
            picking.status = PickingStatus.COMPLETED
            picking.completed_at = datetime.now()
        elif picking.status == PickingStatus.PENDING:
            picking.status = PickingStatus.IN_PROGRESS
            picking.started_at = datetime.now()

        return picking

    async def complete_picking(self, picking_id: str) -> Optional[PickingList]:
        """Termine le picking."""
        picking = await self.get_picking_list(picking_id)
        if not picking:
            return None

        picking.status = PickingStatus.COMPLETED
        picking.completed_at = datetime.now()

        # Mettre à jour le BL
        note = await self.get_delivery_note(picking.delivery_note_id)
        if note:
            for pick_line in picking.lines:
                for note_line in note.lines:
                    if note_line.id == pick_line.delivery_line_id:
                        note_line.quantity_shipped = pick_line.quantity_picked
                        break

            note.status = DeliveryStatus.PACKED
            note.updated_at = datetime.now()

        return picking

    async def list_picking_lists(
        self,
        status: Optional[PickingStatus] = None,
        assigned_to: Optional[str] = None,
    ) -> list[PickingList]:
        """Liste les listes de picking."""
        pickings = [p for p in self._pickings.values() if p.tenant_id == self.tenant_id]

        if status:
            pickings = [p for p in pickings if p.status == status]
        if assigned_to:
            pickings = [p for p in pickings if p.assigned_to == assigned_to]

        return sorted(pickings, key=lambda p: p.created_at, reverse=True)

    # =========================================================================
    # SHIPPING
    # =========================================================================

    async def ship(
        self,
        note_id: str,
        carrier_id: str,
        carrier_name: str,
        tracking_number: str,
        weight_kg: Decimal = Decimal("0"),
        packages_count: int = 1,
        shipping_cost: Decimal = Decimal("0"),
        estimated_delivery: Optional[date] = None,
    ) -> Optional[Shipment]:
        """Expédie un bon de livraison."""
        note = await self.get_delivery_note(note_id)
        if not note or note.status not in [DeliveryStatus.PACKED, DeliveryStatus.CONFIRMED]:
            return None

        self._shipment_counter += 1
        shipment_number = f"SHIP-{self._shipment_counter:05d}"

        shipment = Shipment(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            shipment_number=shipment_number,
            delivery_note_id=note.id,
            delivery_number=note.delivery_number,
            carrier_id=carrier_id,
            carrier_name=carrier_name,
            tracking_number=tracking_number,
            shipped_at=datetime.now(),
            estimated_delivery=estimated_delivery,
            weight_kg=weight_kg,
            packages_count=packages_count,
            shipping_cost=shipping_cost,
            status=ShipmentStatus.PICKED_UP,
            tracking_history=[
                {
                    "status": "picked_up",
                    "timestamp": datetime.now().isoformat(),
                    "location": "Entrepôt",
                    "message": "Colis pris en charge",
                }
            ],
        )

        self._shipments[shipment.id] = shipment

        # Mettre à jour le BL
        note.status = DeliveryStatus.SHIPPED
        note.carrier_id = carrier_id
        note.carrier_name = carrier_name
        note.tracking_number = tracking_number
        note.shipped_date = datetime.now()
        note.weight_kg = weight_kg
        note.packages_count = packages_count
        note.updated_at = datetime.now()

        logger.info(f"BL expédié: {note.delivery_number} via {carrier_name}")
        return shipment

    async def get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        """Récupère une expédition."""
        shipment = self._shipments.get(shipment_id)
        if shipment and shipment.tenant_id == self.tenant_id:
            return shipment
        return None

    async def update_shipment_status(
        self,
        shipment_id: str,
        status: ShipmentStatus,
        location: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Optional[Shipment]:
        """Met à jour le statut d'expédition."""
        shipment = await self.get_shipment(shipment_id)
        if not shipment:
            return None

        shipment.status = status
        shipment.tracking_history.append({
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "message": message,
        })

        if status == ShipmentStatus.DELIVERED:
            shipment.actual_delivery = datetime.now()

            # Mettre à jour le BL
            note = await self.get_delivery_note(shipment.delivery_note_id)
            if note:
                note.status = DeliveryStatus.DELIVERED
                note.delivered_date = datetime.now()
                for line in note.lines:
                    line.quantity_delivered = line.quantity_shipped
                note.updated_at = datetime.now()

        return shipment

    async def confirm_delivery(
        self,
        shipment_id: str,
        signature: Optional[str] = None,
        proof_url: Optional[str] = None,
    ) -> Optional[Shipment]:
        """Confirme la livraison."""
        shipment = await self.get_shipment(shipment_id)
        if not shipment:
            return None

        shipment.status = ShipmentStatus.DELIVERED
        shipment.actual_delivery = datetime.now()
        shipment.signature = signature
        shipment.proof_of_delivery_url = proof_url

        shipment.tracking_history.append({
            "status": "delivered",
            "timestamp": datetime.now().isoformat(),
            "message": "Livré" + (f" - Signé par: {signature}" if signature else ""),
        })

        # Mettre à jour le BL
        note = await self.get_delivery_note(shipment.delivery_note_id)
        if note:
            note.status = DeliveryStatus.DELIVERED
            note.delivered_date = datetime.now()
            for line in note.lines:
                line.quantity_delivered = line.quantity_shipped
            note.updated_at = datetime.now()

        logger.info(f"Livraison confirmée: {shipment.shipment_number}")
        return shipment

    async def list_shipments(
        self,
        status: Optional[ShipmentStatus] = None,
        carrier_id: Optional[str] = None,
    ) -> list[Shipment]:
        """Liste les expéditions."""
        shipments = [s for s in self._shipments.values() if s.tenant_id == self.tenant_id]

        if status:
            shipments = [s for s in shipments if s.status == status]
        if carrier_id:
            shipments = [s for s in shipments if s.carrier_id == carrier_id]

        return sorted(shipments, key=lambda s: s.created_at, reverse=True)

    # =========================================================================
    # RETURNS
    # =========================================================================

    async def create_return_request(
        self,
        note_id: str,
        reason: str,
        lines: list[dict],
    ) -> Optional[ReturnRequest]:
        """Crée une demande de retour."""
        note = await self.get_delivery_note(note_id)
        if not note or note.status != DeliveryStatus.DELIVERED:
            return None

        return_number = f"RET-{uuid.uuid4().hex[:8].upper()}"

        return_req = ReturnRequest(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            return_number=return_number,
            delivery_note_id=note.id,
            delivery_number=note.delivery_number,
            customer_id=note.customer_id,
            reason=reason,
            lines=lines,
        )

        self._returns[return_req.id] = return_req

        logger.info(f"Demande de retour créée: {return_number}")
        return return_req

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Statistiques des livraisons."""
        notes = [n for n in self._notes.values() if n.tenant_id == self.tenant_id]

        if start_date:
            notes = [n for n in notes if n.created_at.date() >= start_date]
        if end_date:
            notes = [n for n in notes if n.created_at.date() <= end_date]

        total = len(notes)
        delivered = len([n for n in notes if n.status == DeliveryStatus.DELIVERED])
        shipped = len([n for n in notes if n.status == DeliveryStatus.SHIPPED])
        pending = len([n for n in notes if n.status in [DeliveryStatus.DRAFT, DeliveryStatus.CONFIRMED]])

        shipments = [s for s in self._shipments.values() if s.tenant_id == self.tenant_id]
        total_shipping_cost = sum(s.shipping_cost for s in shipments)

        # Taux de livraison à temps
        on_time = 0
        late = 0
        for note in notes:
            if note.status == DeliveryStatus.DELIVERED and note.scheduled_date and note.delivered_date:
                if note.delivered_date.date() <= note.scheduled_date:
                    on_time += 1
                else:
                    late += 1

        on_time_rate = Decimal("0")
        if on_time + late > 0:
            on_time_rate = (Decimal(on_time) / Decimal(on_time + late) * 100).quantize(Decimal("0.01"))

        return {
            "total_delivery_notes": total,
            "delivered": delivered,
            "shipped": shipped,
            "pending": pending,
            "cancelled": len([n for n in notes if n.status == DeliveryStatus.CANCELLED]),
            "total_shipments": len(shipments),
            "total_shipping_cost": str(total_shipping_cost),
            "on_time_deliveries": on_time,
            "late_deliveries": late,
            "on_time_rate": str(on_time_rate),
            "total_returns": len([r for r in self._returns.values() if r.tenant_id == self.tenant_id]),
        }
