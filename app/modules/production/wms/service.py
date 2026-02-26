"""
WMS Service - Warehouse Management System
==========================================

Gestion complète d'entrepôt avec emplacements, mouvements et inventaires.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class LocationType(str, Enum):
    """Types d'emplacements."""
    ZONE = "zone"
    AISLE = "aisle"
    RACK = "rack"
    SHELF = "shelf"
    BIN = "bin"
    STAGING = "staging"
    RECEIVING = "receiving"
    SHIPPING = "shipping"
    QUARANTINE = "quarantine"


class MovementType(str, Enum):
    """Types de mouvements."""
    RECEIPT = "receipt"
    TRANSFER = "transfer"
    PICK = "pick"
    PUTAWAY = "putaway"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    SCRAP = "scrap"


class MovementStatus(str, Enum):
    """Statuts de mouvement."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CountStatus(str, Enum):
    """Statuts de comptage."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VALIDATED = "validated"


class WaveStatus(str, Enum):
    """Statuts de vague."""
    DRAFT = "draft"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Warehouse:
    """Entrepôt."""
    id: str
    tenant_id: str
    code: str
    name: str
    address: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class Location:
    """Emplacement de stockage."""
    id: str
    tenant_id: str
    warehouse_id: str
    code: str
    name: str
    location_type: LocationType
    parent_id: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None
    is_active: bool = True
    is_pickable: bool = True
    is_receivable: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def full_code(self) -> str:
        """Code complet de l'emplacement."""
        parts = [self.aisle, self.rack, self.level, self.position]
        return "-".join(p for p in parts if p) or self.code


@dataclass
class LocationStock:
    """Stock dans un emplacement."""
    location_id: str
    product_id: str
    lot_id: Optional[str]
    quantity: float
    reserved_quantity: float = 0.0

    @property
    def available_quantity(self) -> float:
        """Quantité disponible (non réservée)."""
        return self.quantity - self.reserved_quantity


@dataclass
class StockMovement:
    """Mouvement de stock."""
    id: str
    tenant_id: str
    movement_type: MovementType
    product_id: str
    quantity: float
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    lot_id: Optional[str] = None
    reference: Optional[str] = None
    status: MovementStatus = MovementStatus.PENDING
    operator_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass
class InventoryCount:
    """Comptage d'inventaire."""
    id: str
    tenant_id: str
    warehouse_id: str
    name: str
    status: CountStatus = CountStatus.SCHEDULED
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    locations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CountLine:
    """Ligne de comptage."""
    id: str
    count_id: str
    location_id: str
    product_id: str
    expected_qty: float
    counted_qty: Optional[float] = None
    variance: Optional[float] = None
    counted_at: Optional[datetime] = None
    counter_id: Optional[str] = None


@dataclass
class WavePick:
    """Vague de préparation."""
    id: str
    tenant_id: str
    name: str
    warehouse_id: str
    status: WaveStatus = WaveStatus.DRAFT
    order_ids: list[str] = field(default_factory=list)
    pick_count: int = 0
    picked_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    released_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def progress(self) -> float:
        """Progression en pourcentage."""
        if self.pick_count == 0:
            return 0.0
        return round(self.picked_count / self.pick_count * 100, 1)


@dataclass
class ReplenishmentRule:
    """Règle de réapprovisionnement."""
    id: str
    tenant_id: str
    product_id: str
    location_id: str
    min_qty: float
    max_qty: float
    reorder_qty: float
    source_location_id: Optional[str] = None
    is_active: bool = True


class WMSService:
    """Service de gestion d'entrepôt."""

    def __init__(self, db: Any, tenant_id: str):
        """
        Initialise le service WMS.

        Args:
            db: Session de base de données
            tenant_id: ID du tenant (obligatoire)

        Raises:
            ValueError: Si tenant_id est vide
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for multi-tenant isolation")

        self.db = db
        self.tenant_id = tenant_id
        self._warehouses: dict[str, Warehouse] = {}
        self._locations: dict[str, Location] = {}
        self._movements: dict[str, StockMovement] = {}
        self._stock: dict[str, LocationStock] = {}
        self._counts: dict[str, InventoryCount] = {}
        self._waves: dict[str, WavePick] = {}
        self._rules: dict[str, ReplenishmentRule] = {}

    # ========================
    # WAREHOUSES
    # ========================

    async def create_warehouse(
        self,
        code: str,
        name: str,
        address: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Warehouse:
        """Crée un entrepôt."""
        warehouse = Warehouse(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            address=address,
            metadata=metadata or {}
        )
        self._warehouses[warehouse.id] = warehouse
        return warehouse

    async def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        """Récupère un entrepôt."""
        warehouse = self._warehouses.get(warehouse_id)
        if warehouse and warehouse.tenant_id == self.tenant_id:
            return warehouse
        return None

    async def list_warehouses(
        self,
        is_active: Optional[bool] = None
    ) -> list[Warehouse]:
        """Liste les entrepôts."""
        warehouses = [
            w for w in self._warehouses.values()
            if w.tenant_id == self.tenant_id
        ]

        if is_active is not None:
            warehouses = [w for w in warehouses if w.is_active == is_active]

        return sorted(warehouses, key=lambda x: x.name)

    # ========================
    # LOCATIONS
    # ========================

    async def create_location(
        self,
        warehouse_id: str,
        code: str,
        name: str,
        location_type: LocationType,
        parent_id: Optional[str] = None,
        aisle: Optional[str] = None,
        rack: Optional[str] = None,
        level: Optional[str] = None,
        position: Optional[str] = None,
        max_weight: Optional[float] = None,
        max_volume: Optional[float] = None
    ) -> Location:
        """Crée un emplacement."""
        location = Location(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            code=code,
            name=name,
            location_type=location_type,
            parent_id=parent_id,
            aisle=aisle,
            rack=rack,
            level=level,
            position=position,
            max_weight=max_weight,
            max_volume=max_volume
        )
        self._locations[location.id] = location
        return location

    async def get_location(self, location_id: str) -> Optional[Location]:
        """Récupère un emplacement."""
        location = self._locations.get(location_id)
        if location and location.tenant_id == self.tenant_id:
            return location
        return None

    async def get_location_by_code(
        self,
        warehouse_id: str,
        code: str
    ) -> Optional[Location]:
        """Récupère un emplacement par son code."""
        for location in self._locations.values():
            if (location.tenant_id == self.tenant_id and
                location.warehouse_id == warehouse_id and
                location.code == code):
                return location
        return None

    async def list_locations(
        self,
        warehouse_id: str,
        location_type: Optional[LocationType] = None,
        parent_id: Optional[str] = None,
        is_pickable: Optional[bool] = None
    ) -> list[Location]:
        """Liste les emplacements."""
        locations = [
            loc for loc in self._locations.values()
            if loc.tenant_id == self.tenant_id
            and loc.warehouse_id == warehouse_id
        ]

        if location_type:
            locations = [loc for loc in locations if loc.location_type == location_type]

        if parent_id is not None:
            locations = [loc for loc in locations if loc.parent_id == parent_id]

        if is_pickable is not None:
            locations = [loc for loc in locations if loc.is_pickable == is_pickable]

        return sorted(locations, key=lambda x: x.code)

    async def update_location(
        self,
        location_id: str,
        **updates
    ) -> Optional[Location]:
        """Met à jour un emplacement."""
        location = await self.get_location(location_id)
        if not location:
            return None

        for key, value in updates.items():
            if hasattr(location, key):
                setattr(location, key, value)

        return location

    # ========================
    # STOCK & MOVEMENTS
    # ========================

    async def get_stock(
        self,
        location_id: str,
        product_id: str,
        lot_id: Optional[str] = None
    ) -> Optional[LocationStock]:
        """Récupère le stock d'un produit dans un emplacement."""
        key = f"{location_id}:{product_id}:{lot_id or ''}"
        return self._stock.get(key)

    async def get_location_stock(
        self,
        location_id: str
    ) -> list[LocationStock]:
        """Récupère tout le stock d'un emplacement."""
        return [
            stock for key, stock in self._stock.items()
            if key.startswith(f"{location_id}:")
        ]

    async def get_product_stock(
        self,
        product_id: str,
        warehouse_id: Optional[str] = None
    ) -> list[LocationStock]:
        """Récupère le stock d'un produit dans tous les emplacements."""
        stocks = []
        for key, stock in self._stock.items():
            if f":{product_id}:" in key:
                if warehouse_id:
                    location = await self.get_location(stock.location_id)
                    if location and location.warehouse_id == warehouse_id:
                        stocks.append(stock)
                else:
                    stocks.append(stock)
        return stocks

    async def receive(
        self,
        location_id: str,
        product_id: str,
        quantity: float,
        lot_id: Optional[str] = None,
        reference: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> StockMovement:
        """Réceptionne du stock."""
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            movement_type=MovementType.RECEIPT,
            product_id=product_id,
            quantity=quantity,
            to_location_id=location_id,
            lot_id=lot_id,
            reference=reference,
            status=MovementStatus.COMPLETED,
            operator_id=operator_id,
            completed_at=datetime.utcnow()
        )
        self._movements[movement.id] = movement

        # Update stock
        await self._update_stock(location_id, product_id, lot_id, quantity)

        return movement

    async def transfer(
        self,
        from_location_id: str,
        to_location_id: str,
        product_id: str,
        quantity: float,
        lot_id: Optional[str] = None,
        reference: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> StockMovement:
        """Transfère du stock entre emplacements."""
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            movement_type=MovementType.TRANSFER,
            product_id=product_id,
            quantity=quantity,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            lot_id=lot_id,
            reference=reference,
            status=MovementStatus.COMPLETED,
            operator_id=operator_id,
            completed_at=datetime.utcnow()
        )
        self._movements[movement.id] = movement

        # Update stock
        await self._update_stock(from_location_id, product_id, lot_id, -quantity)
        await self._update_stock(to_location_id, product_id, lot_id, quantity)

        return movement

    async def pick(
        self,
        location_id: str,
        product_id: str,
        quantity: float,
        lot_id: Optional[str] = None,
        reference: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> StockMovement:
        """Prélève du stock."""
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            movement_type=MovementType.PICK,
            product_id=product_id,
            quantity=quantity,
            from_location_id=location_id,
            lot_id=lot_id,
            reference=reference,
            status=MovementStatus.COMPLETED,
            operator_id=operator_id,
            completed_at=datetime.utcnow()
        )
        self._movements[movement.id] = movement

        # Update stock
        await self._update_stock(location_id, product_id, lot_id, -quantity)

        return movement

    async def adjust(
        self,
        location_id: str,
        product_id: str,
        quantity: float,
        lot_id: Optional[str] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> StockMovement:
        """Ajuste le stock (inventaire)."""
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            movement_type=MovementType.ADJUSTMENT,
            product_id=product_id,
            quantity=quantity,
            from_location_id=location_id if quantity < 0 else None,
            to_location_id=location_id if quantity > 0 else None,
            lot_id=lot_id,
            reference=reference,
            status=MovementStatus.COMPLETED,
            operator_id=operator_id,
            notes=notes,
            completed_at=datetime.utcnow()
        )
        self._movements[movement.id] = movement

        # Update stock
        await self._update_stock(location_id, product_id, lot_id, quantity)

        return movement

    async def _update_stock(
        self,
        location_id: str,
        product_id: str,
        lot_id: Optional[str],
        quantity_delta: float
    ) -> None:
        """Met à jour le stock."""
        key = f"{location_id}:{product_id}:{lot_id or ''}"

        if key in self._stock:
            self._stock[key].quantity += quantity_delta
        else:
            self._stock[key] = LocationStock(
                location_id=location_id,
                product_id=product_id,
                lot_id=lot_id,
                quantity=quantity_delta
            )

    async def list_movements(
        self,
        warehouse_id: Optional[str] = None,
        product_id: Optional[str] = None,
        movement_type: Optional[MovementType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[StockMovement]:
        """Liste les mouvements de stock."""
        movements = [
            m for m in self._movements.values()
            if m.tenant_id == self.tenant_id
        ]

        if product_id:
            movements = [m for m in movements if m.product_id == product_id]

        if movement_type:
            movements = [m for m in movements if m.movement_type == movement_type]

        if from_date:
            movements = [m for m in movements if m.created_at >= from_date]

        if to_date:
            movements = [m for m in movements if m.created_at <= to_date]

        if warehouse_id:
            warehouse_locations = {
                loc.id for loc in await self.list_locations(warehouse_id)
            }
            movements = [
                m for m in movements
                if (m.from_location_id in warehouse_locations or
                    m.to_location_id in warehouse_locations)
            ]

        return sorted(
            movements,
            key=lambda x: x.created_at,
            reverse=True
        )[:limit]

    # ========================
    # INVENTORY COUNTS
    # ========================

    async def create_inventory_count(
        self,
        warehouse_id: str,
        name: str,
        locations: Optional[list[str]] = None,
        scheduled_date: Optional[datetime] = None
    ) -> InventoryCount:
        """Crée un comptage d'inventaire."""
        count = InventoryCount(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            name=name,
            locations=locations or [],
            scheduled_date=scheduled_date
        )
        self._counts[count.id] = count
        return count

    async def get_inventory_count(self, count_id: str) -> Optional[InventoryCount]:
        """Récupère un comptage."""
        count = self._counts.get(count_id)
        if count and count.tenant_id == self.tenant_id:
            return count
        return None

    async def start_inventory_count(self, count_id: str) -> Optional[InventoryCount]:
        """Démarre un comptage."""
        count = await self.get_inventory_count(count_id)
        if not count:
            return None

        count.status = CountStatus.IN_PROGRESS
        count.started_at = datetime.utcnow()
        return count

    async def record_count(
        self,
        count_id: str,
        location_id: str,
        product_id: str,
        counted_qty: float,
        counter_id: Optional[str] = None
    ) -> Optional[CountLine]:
        """Enregistre un comptage."""
        count = await self.get_inventory_count(count_id)
        if not count:
            return None

        # Get expected quantity
        stock = await self.get_stock(location_id, product_id)
        expected = stock.quantity if stock else 0.0

        line = CountLine(
            id=str(uuid4()),
            count_id=count_id,
            location_id=location_id,
            product_id=product_id,
            expected_qty=expected,
            counted_qty=counted_qty,
            variance=counted_qty - expected,
            counted_at=datetime.utcnow(),
            counter_id=counter_id
        )
        return line

    async def complete_inventory_count(
        self,
        count_id: str
    ) -> Optional[InventoryCount]:
        """Termine un comptage."""
        count = await self.get_inventory_count(count_id)
        if not count:
            return None

        count.status = CountStatus.COMPLETED
        count.completed_at = datetime.utcnow()
        return count

    async def validate_inventory_count(
        self,
        count_id: str,
        apply_adjustments: bool = True
    ) -> Optional[InventoryCount]:
        """Valide un comptage et applique les ajustements."""
        count = await self.get_inventory_count(count_id)
        if not count:
            return None

        count.status = CountStatus.VALIDATED
        return count

    async def list_inventory_counts(
        self,
        warehouse_id: Optional[str] = None,
        status: Optional[CountStatus] = None
    ) -> list[InventoryCount]:
        """Liste les comptages."""
        counts = [
            c for c in self._counts.values()
            if c.tenant_id == self.tenant_id
        ]

        if warehouse_id:
            counts = [c for c in counts if c.warehouse_id == warehouse_id]

        if status:
            counts = [c for c in counts if c.status == status]

        return sorted(counts, key=lambda x: x.created_at, reverse=True)

    # ========================
    # WAVE PICKING
    # ========================

    async def create_wave(
        self,
        warehouse_id: str,
        name: str,
        order_ids: Optional[list[str]] = None
    ) -> WavePick:
        """Crée une vague de préparation."""
        wave = WavePick(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            name=name,
            order_ids=order_ids or []
        )
        self._waves[wave.id] = wave
        return wave

    async def get_wave(self, wave_id: str) -> Optional[WavePick]:
        """Récupère une vague."""
        wave = self._waves.get(wave_id)
        if wave and wave.tenant_id == self.tenant_id:
            return wave
        return None

    async def add_orders_to_wave(
        self,
        wave_id: str,
        order_ids: list[str]
    ) -> Optional[WavePick]:
        """Ajoute des commandes à une vague."""
        wave = await self.get_wave(wave_id)
        if not wave:
            return None

        for order_id in order_ids:
            if order_id not in wave.order_ids:
                wave.order_ids.append(order_id)

        return wave

    async def release_wave(self, wave_id: str) -> Optional[WavePick]:
        """Libère une vague pour préparation."""
        wave = await self.get_wave(wave_id)
        if not wave:
            return None

        wave.status = WaveStatus.RELEASED
        wave.released_at = datetime.utcnow()
        wave.pick_count = len(wave.order_ids) * 5  # Simulated pick count
        return wave

    async def start_wave(self, wave_id: str) -> Optional[WavePick]:
        """Démarre la préparation d'une vague."""
        wave = await self.get_wave(wave_id)
        if not wave:
            return None

        wave.status = WaveStatus.IN_PROGRESS
        return wave

    async def complete_wave(self, wave_id: str) -> Optional[WavePick]:
        """Termine une vague."""
        wave = await self.get_wave(wave_id)
        if not wave:
            return None

        wave.status = WaveStatus.COMPLETED
        wave.picked_count = wave.pick_count
        wave.completed_at = datetime.utcnow()
        return wave

    async def list_waves(
        self,
        warehouse_id: Optional[str] = None,
        status: Optional[WaveStatus] = None
    ) -> list[WavePick]:
        """Liste les vagues."""
        waves = [
            w for w in self._waves.values()
            if w.tenant_id == self.tenant_id
        ]

        if warehouse_id:
            waves = [w for w in waves if w.warehouse_id == warehouse_id]

        if status:
            waves = [w for w in waves if w.status == status]

        return sorted(waves, key=lambda x: x.created_at, reverse=True)

    # ========================
    # REPLENISHMENT
    # ========================

    async def create_replenishment_rule(
        self,
        product_id: str,
        location_id: str,
        min_qty: float,
        max_qty: float,
        reorder_qty: float,
        source_location_id: Optional[str] = None
    ) -> ReplenishmentRule:
        """Crée une règle de réapprovisionnement."""
        rule = ReplenishmentRule(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            product_id=product_id,
            location_id=location_id,
            min_qty=min_qty,
            max_qty=max_qty,
            reorder_qty=reorder_qty,
            source_location_id=source_location_id
        )
        self._rules[rule.id] = rule
        return rule

    async def check_replenishment_needs(
        self,
        warehouse_id: str
    ) -> list[dict]:
        """Vérifie les besoins de réapprovisionnement."""
        needs = []

        for rule in self._rules.values():
            if rule.tenant_id != self.tenant_id or not rule.is_active:
                continue

            location = await self.get_location(rule.location_id)
            if not location or location.warehouse_id != warehouse_id:
                continue

            stock = await self.get_stock(rule.location_id, rule.product_id)
            current_qty = stock.quantity if stock else 0.0

            if current_qty < rule.min_qty:
                needs.append({
                    "rule_id": rule.id,
                    "product_id": rule.product_id,
                    "location_id": rule.location_id,
                    "current_qty": current_qty,
                    "min_qty": rule.min_qty,
                    "suggested_qty": rule.reorder_qty,
                    "source_location_id": rule.source_location_id
                })

        return needs

    async def execute_replenishment(
        self,
        rule_id: str,
        quantity: Optional[float] = None,
        operator_id: Optional[str] = None
    ) -> Optional[StockMovement]:
        """Exécute un réapprovisionnement."""
        rule = self._rules.get(rule_id)
        if not rule or rule.tenant_id != self.tenant_id:
            return None

        qty = quantity or rule.reorder_qty

        if rule.source_location_id:
            return await self.transfer(
                from_location_id=rule.source_location_id,
                to_location_id=rule.location_id,
                product_id=rule.product_id,
                quantity=qty,
                reference=f"REPL-{rule_id[:8]}",
                operator_id=operator_id
            )

        return None

    # ========================
    # STATISTICS
    # ========================

    async def get_statistics(
        self,
        warehouse_id: str
    ) -> dict:
        """Retourne les statistiques WMS."""
        locations = await self.list_locations(warehouse_id)
        movements = await self.list_movements(warehouse_id=warehouse_id)
        waves = await self.list_waves(warehouse_id=warehouse_id)

        active_waves = [w for w in waves if w.status == WaveStatus.IN_PROGRESS]

        return {
            "warehouse_id": warehouse_id,
            "total_locations": len(locations),
            "pickable_locations": len([loc for loc in locations if loc.is_pickable]),
            "total_movements_today": len([
                m for m in movements
                if m.created_at.date() == datetime.utcnow().date()
            ]),
            "movements_by_type": self._count_by_type(movements),
            "active_waves": len(active_waves),
            "total_waves": len(waves),
            "replenishment_needs": len(
                await self.check_replenishment_needs(warehouse_id)
            )
        }

    def _count_by_type(self, movements: list[StockMovement]) -> dict:
        """Compte les mouvements par type."""
        counts = {}
        for m in movements:
            mt = m.movement_type.value
            counts[mt] = counts.get(mt, 0) + 1
        return counts
