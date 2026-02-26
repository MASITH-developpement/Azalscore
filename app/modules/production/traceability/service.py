"""
AZALSCORE Traceability Service
===============================

Service de traçabilité pour lots et numéros de série.

Fonctionnalités:
- Gestion des lots avec dates d'expiration
- Numéros de série individuels
- Traçabilité complète amont/aval
- Gestion des rappels produits
- Historique des mouvements
"""
from __future__ import annotations


import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class LotStatus(str, Enum):
    """Statut d'un lot."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"
    RECALLED = "recalled"
    CONSUMED = "consumed"


class SerialStatus(str, Enum):
    """Statut d'un numéro de série."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    IN_USE = "in_use"
    RETURNED = "returned"
    DEFECTIVE = "defective"
    RECALLED = "recalled"


class MovementType(str, Enum):
    """Type de mouvement de traçabilité."""
    RECEIPT = "receipt"
    CONSUMPTION = "consumption"
    PRODUCTION = "production"
    TRANSFER = "transfer"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    RECALL = "recall"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class Lot:
    """Lot de production."""
    id: str
    tenant_id: str
    lot_number: str
    product_id: str
    product_name: str
    initial_quantity: Decimal
    current_quantity: Decimal
    unit: str = "unit"
    status: LotStatus = LotStatus.AVAILABLE
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_lot: Optional[str] = None
    supplier_id: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Vérifie si le lot est expiré."""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Jours restants avant expiration."""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days

    @property
    def consumed_quantity(self) -> Decimal:
        """Quantité consommée."""
        return self.initial_quantity - self.current_quantity


@dataclass
class SerialNumber:
    """Numéro de série individuel."""
    id: str
    tenant_id: str
    serial_number: str
    product_id: str
    product_name: str
    lot_id: Optional[str] = None
    lot_number: Optional[str] = None
    status: SerialStatus = SerialStatus.AVAILABLE
    manufacturing_date: Optional[date] = None
    warranty_end: Optional[date] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    @property
    def is_under_warranty(self) -> bool:
        """Vérifie si sous garantie."""
        if not self.warranty_end:
            return False
        return date.today() <= self.warranty_end


@dataclass
class TraceabilityMovement:
    """Mouvement de traçabilité."""
    id: str
    tenant_id: str
    movement_type: MovementType
    lot_id: Optional[str] = None
    lot_number: Optional[str] = None
    serial_id: Optional[str] = None
    serial_number: Optional[str] = None
    product_id: str = ""
    product_name: str = ""
    quantity: Decimal = Decimal("1")
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    reference_type: Optional[str] = None  # order, production, transfer
    reference_id: Optional[str] = None
    operator_id: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TraceabilityChain:
    """Chaîne de traçabilité complète."""
    product_id: str
    product_name: str
    lot_id: Optional[str] = None
    serial_id: Optional[str] = None
    upstream: list[TraceabilityMovement] = field(default_factory=list)  # Origine
    downstream: list[TraceabilityMovement] = field(default_factory=list)  # Destination


@dataclass
class RecallReport:
    """Rapport de rappel produit."""
    id: str
    tenant_id: str
    reason: str
    affected_lots: list[str] = field(default_factory=list)
    affected_serials: list[str] = field(default_factory=list)
    customers_affected: list[str] = field(default_factory=list)
    total_quantity: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# SERVICE
# =============================================================================


class TraceabilityService:
    """
    Service de traçabilité lots et numéros de série.

    Multi-tenant: OUI - Données isolées par tenant
    Fonctionnalités: Lots, Séries, Mouvements, Traçabilité, Rappels
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
        self._lots: dict[str, Lot] = {}
        self._serials: dict[str, SerialNumber] = {}
        self._movements: list[TraceabilityMovement] = []
        self._lot_counter = 1000

        logger.info(f"TraceabilityService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # LOT MANAGEMENT
    # =========================================================================

    async def create_lot(
        self,
        product_id: str,
        product_name: str,
        quantity: Decimal,
        unit: str = "unit",
        manufacturing_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        supplier_lot: Optional[str] = None,
        supplier_id: Optional[str] = None,
        location_id: Optional[str] = None,
        location_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Lot:
        """Crée un nouveau lot."""
        self._lot_counter += 1
        lot_number = f"LOT-{datetime.now().strftime('%Y%m')}-{self._lot_counter:05d}"

        lot = Lot(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            lot_number=lot_number,
            product_id=product_id,
            product_name=product_name,
            initial_quantity=quantity,
            current_quantity=quantity,
            unit=unit,
            manufacturing_date=manufacturing_date or date.today(),
            expiry_date=expiry_date,
            supplier_lot=supplier_lot,
            supplier_id=supplier_id,
            location_id=location_id,
            location_name=location_name,
            notes=notes,
        )

        self._lots[lot.id] = lot

        # Créer mouvement de réception
        await self._create_movement(
            movement_type=MovementType.RECEIPT,
            lot=lot,
            quantity=quantity,
            to_location_id=location_id,
        )

        logger.info(f"Lot créé: {lot_number} - {product_name} x {quantity}")
        return lot

    async def get_lot(self, lot_id: str) -> Optional[Lot]:
        """Récupère un lot."""
        lot = self._lots.get(lot_id)
        if lot and lot.tenant_id == self.tenant_id:
            return lot
        return None

    async def get_lot_by_number(self, lot_number: str) -> Optional[Lot]:
        """Récupère un lot par son numéro."""
        for lot in self._lots.values():
            if lot.tenant_id == self.tenant_id and lot.lot_number == lot_number:
                return lot
        return None

    async def list_lots(
        self,
        product_id: Optional[str] = None,
        status: Optional[LotStatus] = None,
        expiring_within_days: Optional[int] = None,
        location_id: Optional[str] = None,
        include_empty: bool = False,
    ) -> list[Lot]:
        """Liste les lots avec filtres."""
        lots = [l for l in self._lots.values() if l.tenant_id == self.tenant_id]

        if product_id:
            lots = [l for l in lots if l.product_id == product_id]

        if status:
            lots = [l for l in lots if l.status == status]

        if expiring_within_days is not None:
            threshold = date.today() + timedelta(days=expiring_within_days)
            lots = [l for l in lots if l.expiry_date and l.expiry_date <= threshold]

        if location_id:
            lots = [l for l in lots if l.location_id == location_id]

        if not include_empty:
            lots = [l for l in lots if l.current_quantity > 0]

        return sorted(lots, key=lambda l: (l.expiry_date or date.max, l.created_at))

    async def consume_lot(
        self,
        lot_id: str,
        quantity: Decimal,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Lot]:
        """Consomme une quantité du lot."""
        lot = await self.get_lot(lot_id)
        if not lot:
            return None

        if quantity > lot.current_quantity:
            raise ValueError(f"Quantité insuffisante: {lot.current_quantity} disponible")

        if lot.status not in [LotStatus.AVAILABLE, LotStatus.RESERVED]:
            raise ValueError(f"Lot non disponible: statut {lot.status}")

        lot.current_quantity -= quantity
        lot.updated_at = datetime.now()

        if lot.current_quantity == 0:
            lot.status = LotStatus.CONSUMED

        await self._create_movement(
            movement_type=MovementType.CONSUMPTION,
            lot=lot,
            quantity=quantity,
            from_location_id=lot.location_id,
            reference_type=reference_type,
            reference_id=reference_id,
            operator_id=operator_id,
            notes=notes,
        )

        logger.info(f"Lot consommé: {lot.lot_number} - {quantity}")
        return lot

    async def transfer_lot(
        self,
        lot_id: str,
        quantity: Decimal,
        to_location_id: str,
        to_location_name: Optional[str] = None,
        operator_id: Optional[str] = None,
    ) -> Optional[Lot]:
        """Transfère une partie du lot."""
        lot = await self.get_lot(lot_id)
        if not lot:
            return None

        if quantity > lot.current_quantity:
            raise ValueError("Quantité insuffisante")

        from_location = lot.location_id

        # Si transfert partiel, créer nouveau lot
        if quantity < lot.current_quantity:
            self._lot_counter += 1
            new_lot = Lot(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                lot_number=lot.lot_number,  # Même numéro de lot
                product_id=lot.product_id,
                product_name=lot.product_name,
                initial_quantity=quantity,
                current_quantity=quantity,
                unit=lot.unit,
                status=lot.status,
                manufacturing_date=lot.manufacturing_date,
                expiry_date=lot.expiry_date,
                supplier_lot=lot.supplier_lot,
                location_id=to_location_id,
                location_name=to_location_name,
            )
            self._lots[new_lot.id] = new_lot
            lot.current_quantity -= quantity
            lot.updated_at = datetime.now()

            await self._create_movement(
                movement_type=MovementType.TRANSFER,
                lot=new_lot,
                quantity=quantity,
                from_location_id=from_location,
                to_location_id=to_location_id,
                operator_id=operator_id,
            )

            return new_lot
        else:
            # Transfert total
            lot.location_id = to_location_id
            lot.location_name = to_location_name
            lot.updated_at = datetime.now()

            await self._create_movement(
                movement_type=MovementType.TRANSFER,
                lot=lot,
                quantity=quantity,
                from_location_id=from_location,
                to_location_id=to_location_id,
                operator_id=operator_id,
            )

            return lot

    async def quarantine_lot(
        self,
        lot_id: str,
        reason: str,
    ) -> Optional[Lot]:
        """Met un lot en quarantaine."""
        lot = await self.get_lot(lot_id)
        if not lot:
            return None

        lot.status = LotStatus.QUARANTINE
        lot.notes = f"Quarantaine: {reason}" + (f"\n{lot.notes}" if lot.notes else "")
        lot.updated_at = datetime.now()

        logger.info(f"Lot en quarantaine: {lot.lot_number}")
        return lot

    async def release_lot(self, lot_id: str) -> Optional[Lot]:
        """Libère un lot de quarantaine."""
        lot = await self.get_lot(lot_id)
        if not lot or lot.status != LotStatus.QUARANTINE:
            return None

        lot.status = LotStatus.AVAILABLE
        lot.updated_at = datetime.now()

        return lot

    async def check_expiring_lots(
        self,
        days: int = 30,
    ) -> list[Lot]:
        """Vérifie les lots qui expirent bientôt."""
        return await self.list_lots(expiring_within_days=days)

    # =========================================================================
    # SERIAL NUMBER MANAGEMENT
    # =========================================================================

    async def create_serial(
        self,
        product_id: str,
        product_name: str,
        serial_number: Optional[str] = None,
        lot_id: Optional[str] = None,
        manufacturing_date: Optional[date] = None,
        warranty_months: int = 12,
        location_id: Optional[str] = None,
        location_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SerialNumber:
        """Crée un numéro de série."""
        if not serial_number:
            serial_number = f"SN-{uuid.uuid4().hex[:12].upper()}"

        lot_number = None
        if lot_id:
            lot = await self.get_lot(lot_id)
            lot_number = lot.lot_number if lot else None

        warranty_end = None
        if warranty_months > 0:
            mfg_date = manufacturing_date or date.today()
            warranty_end = mfg_date + timedelta(days=warranty_months * 30)

        serial = SerialNumber(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            serial_number=serial_number,
            product_id=product_id,
            product_name=product_name,
            lot_id=lot_id,
            lot_number=lot_number,
            manufacturing_date=manufacturing_date or date.today(),
            warranty_end=warranty_end,
            location_id=location_id,
            location_name=location_name,
            notes=notes,
        )

        self._serials[serial.id] = serial

        # Créer mouvement
        await self._create_movement(
            movement_type=MovementType.PRODUCTION,
            serial=serial,
            to_location_id=location_id,
        )

        logger.info(f"Numéro de série créé: {serial_number}")
        return serial

    async def create_serial_batch(
        self,
        product_id: str,
        product_name: str,
        quantity: int,
        lot_id: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs,
    ) -> list[SerialNumber]:
        """Crée plusieurs numéros de série."""
        serials = []
        prefix = prefix or f"SN-{datetime.now().strftime('%Y%m%d')}"

        for i in range(quantity):
            serial_number = f"{prefix}-{i + 1:05d}"
            serial = await self.create_serial(
                product_id=product_id,
                product_name=product_name,
                serial_number=serial_number,
                lot_id=lot_id,
                **kwargs,
            )
            serials.append(serial)

        return serials

    async def get_serial(self, serial_id: str) -> Optional[SerialNumber]:
        """Récupère un numéro de série."""
        serial = self._serials.get(serial_id)
        if serial and serial.tenant_id == self.tenant_id:
            return serial
        return None

    async def get_serial_by_number(self, serial_number: str) -> Optional[SerialNumber]:
        """Récupère un numéro de série par son numéro."""
        for serial in self._serials.values():
            if serial.tenant_id == self.tenant_id and serial.serial_number == serial_number:
                return serial
        return None

    async def list_serials(
        self,
        product_id: Optional[str] = None,
        lot_id: Optional[str] = None,
        status: Optional[SerialStatus] = None,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> list[SerialNumber]:
        """Liste les numéros de série."""
        serials = [s for s in self._serials.values() if s.tenant_id == self.tenant_id]

        if product_id:
            serials = [s for s in serials if s.product_id == product_id]
        if lot_id:
            serials = [s for s in serials if s.lot_id == lot_id]
        if status:
            serials = [s for s in serials if s.status == status]
        if customer_id:
            serials = [s for s in serials if s.customer_id == customer_id]
        if location_id:
            serials = [s for s in serials if s.location_id == location_id]

        return sorted(serials, key=lambda s: s.serial_number)

    async def sell_serial(
        self,
        serial_id: str,
        customer_id: str,
        customer_name: str,
        reference_id: Optional[str] = None,
    ) -> Optional[SerialNumber]:
        """Marque un numéro de série comme vendu."""
        serial = await self.get_serial(serial_id)
        if not serial or serial.status != SerialStatus.AVAILABLE:
            return None

        serial.status = SerialStatus.SOLD
        serial.customer_id = customer_id
        serial.customer_name = customer_name
        serial.updated_at = datetime.now()

        await self._create_movement(
            movement_type=MovementType.SALE,
            serial=serial,
            from_location_id=serial.location_id,
            reference_type="sale",
            reference_id=reference_id,
        )

        return serial

    async def return_serial(
        self,
        serial_id: str,
        location_id: str,
        reason: Optional[str] = None,
    ) -> Optional[SerialNumber]:
        """Enregistre un retour."""
        serial = await self.get_serial(serial_id)
        if not serial or serial.status != SerialStatus.SOLD:
            return None

        serial.status = SerialStatus.RETURNED
        serial.location_id = location_id
        serial.notes = f"Retour: {reason}" if reason else serial.notes
        serial.updated_at = datetime.now()

        await self._create_movement(
            movement_type=MovementType.RETURN,
            serial=serial,
            to_location_id=location_id,
            notes=reason,
        )

        return serial

    async def mark_defective(
        self,
        serial_id: str,
        reason: str,
    ) -> Optional[SerialNumber]:
        """Marque un numéro de série comme défectueux."""
        serial = await self.get_serial(serial_id)
        if not serial:
            return None

        serial.status = SerialStatus.DEFECTIVE
        serial.notes = f"Défaut: {reason}"
        serial.updated_at = datetime.now()

        return serial

    # =========================================================================
    # TRACEABILITY
    # =========================================================================

    async def _create_movement(
        self,
        movement_type: MovementType,
        lot: Optional[Lot] = None,
        serial: Optional[SerialNumber] = None,
        quantity: Decimal = Decimal("1"),
        from_location_id: Optional[str] = None,
        to_location_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> TraceabilityMovement:
        """Crée un mouvement de traçabilité."""
        movement = TraceabilityMovement(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            movement_type=movement_type,
            lot_id=lot.id if lot else None,
            lot_number=lot.lot_number if lot else None,
            serial_id=serial.id if serial else None,
            serial_number=serial.serial_number if serial else None,
            product_id=lot.product_id if lot else (serial.product_id if serial else ""),
            product_name=lot.product_name if lot else (serial.product_name if serial else ""),
            quantity=quantity,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            reference_type=reference_type,
            reference_id=reference_id,
            operator_id=operator_id,
            notes=notes,
        )

        self._movements.append(movement)
        return movement

    async def get_lot_movements(self, lot_id: str) -> list[TraceabilityMovement]:
        """Récupère l'historique d'un lot."""
        return [
            m for m in self._movements
            if m.tenant_id == self.tenant_id and m.lot_id == lot_id
        ]

    async def get_serial_movements(self, serial_id: str) -> list[TraceabilityMovement]:
        """Récupère l'historique d'un numéro de série."""
        return [
            m for m in self._movements
            if m.tenant_id == self.tenant_id and m.serial_id == serial_id
        ]

    async def get_traceability_chain(
        self,
        lot_id: Optional[str] = None,
        serial_id: Optional[str] = None,
    ) -> Optional[TraceabilityChain]:
        """Récupère la chaîne de traçabilité complète."""
        if not lot_id and not serial_id:
            return None

        movements = []
        product_id = ""
        product_name = ""

        if lot_id:
            movements = await self.get_lot_movements(lot_id)
            lot = await self.get_lot(lot_id)
            if lot:
                product_id = lot.product_id
                product_name = lot.product_name

        if serial_id:
            movements = await self.get_serial_movements(serial_id)
            serial = await self.get_serial(serial_id)
            if serial:
                product_id = serial.product_id
                product_name = serial.product_name

        # Séparer amont et aval
        upstream = [
            m for m in movements
            if m.movement_type in [MovementType.RECEIPT, MovementType.PRODUCTION, MovementType.RETURN]
        ]
        downstream = [
            m for m in movements
            if m.movement_type in [MovementType.CONSUMPTION, MovementType.SALE, MovementType.TRANSFER]
        ]

        return TraceabilityChain(
            product_id=product_id,
            product_name=product_name,
            lot_id=lot_id,
            serial_id=serial_id,
            upstream=sorted(upstream, key=lambda m: m.timestamp),
            downstream=sorted(downstream, key=lambda m: m.timestamp),
        )

    # =========================================================================
    # RECALL MANAGEMENT
    # =========================================================================

    async def initiate_recall(
        self,
        lot_ids: Optional[list[str]] = None,
        serial_ids: Optional[list[str]] = None,
        reason: str = "",
    ) -> RecallReport:
        """Initie un rappel produit."""
        affected_lots = []
        affected_serials = []
        customers_affected = set()
        total_quantity = Decimal("0")

        # Rappeler les lots
        if lot_ids:
            for lot_id in lot_ids:
                lot = await self.get_lot(lot_id)
                if lot and lot.status != LotStatus.RECALLED:
                    lot.status = LotStatus.RECALLED
                    lot.updated_at = datetime.now()
                    affected_lots.append(lot.lot_number)
                    total_quantity += lot.current_quantity

                    # Rappeler aussi les séries associées
                    serials = await self.list_serials(lot_id=lot_id)
                    for serial in serials:
                        if serial.status not in [SerialStatus.RECALLED, SerialStatus.DEFECTIVE]:
                            serial.status = SerialStatus.RECALLED
                            affected_serials.append(serial.serial_number)
                            if serial.customer_id:
                                customers_affected.add(serial.customer_id)

        # Rappeler les séries individuelles
        if serial_ids:
            for serial_id in serial_ids:
                serial = await self.get_serial(serial_id)
                if serial and serial.status not in [SerialStatus.RECALLED, SerialStatus.DEFECTIVE]:
                    serial.status = SerialStatus.RECALLED
                    serial.updated_at = datetime.now()
                    affected_serials.append(serial.serial_number)
                    total_quantity += Decimal("1")
                    if serial.customer_id:
                        customers_affected.add(serial.customer_id)

        report = RecallReport(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            reason=reason,
            affected_lots=affected_lots,
            affected_serials=affected_serials,
            customers_affected=list(customers_affected),
            total_quantity=total_quantity,
        )

        logger.warning(f"Rappel initié: {len(affected_lots)} lots, {len(affected_serials)} séries")
        return report

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(self) -> dict:
        """Statistiques de traçabilité."""
        lots = [l for l in self._lots.values() if l.tenant_id == self.tenant_id]
        serials = [s for s in self._serials.values() if s.tenant_id == self.tenant_id]
        movements = [m for m in self._movements if m.tenant_id == self.tenant_id]

        # Lots
        active_lots = len([l for l in lots if l.status == LotStatus.AVAILABLE])
        expired_lots = len([l for l in lots if l.is_expired])
        expiring_soon = len([l for l in lots if l.days_until_expiry and 0 < l.days_until_expiry <= 30])
        quarantine_lots = len([l for l in lots if l.status == LotStatus.QUARANTINE])

        # Séries
        available_serials = len([s for s in serials if s.status == SerialStatus.AVAILABLE])
        sold_serials = len([s for s in serials if s.status == SerialStatus.SOLD])
        under_warranty = len([s for s in serials if s.is_under_warranty])

        return {
            "total_lots": len(lots),
            "active_lots": active_lots,
            "expired_lots": expired_lots,
            "expiring_within_30_days": expiring_soon,
            "quarantine_lots": quarantine_lots,
            "total_serials": len(serials),
            "available_serials": available_serials,
            "sold_serials": sold_serials,
            "under_warranty": under_warranty,
            "total_movements": len(movements),
        }
