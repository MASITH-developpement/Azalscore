"""
AZALSCORE GPAO/MRP Service
===========================

Service de Gestion de Production Assistée par Ordinateur.

Fonctionnalités:
- Gestion des ordres de fabrication (OF)
- Nomenclatures multi-niveaux (BOM)
- Gammes de fabrication avec opérations
- Calcul des besoins nets (MRP)
- Planification de capacité finie
- Suivi d'avancement temps réel
"""

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


class ProductionStatus(str, Enum):
    """Statut d'un ordre de fabrication."""
    DRAFT = "draft"
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OperationType(str, Enum):
    """Type d'opération de fabrication."""
    CUTTING = "cutting"
    MACHINING = "machining"
    ASSEMBLY = "assembly"
    WELDING = "welding"
    PAINTING = "painting"
    QUALITY_CHECK = "quality_check"
    PACKAGING = "packaging"
    OTHER = "other"


class ResourceType(str, Enum):
    """Type de ressource."""
    MACHINE = "machine"
    WORKSTATION = "workstation"
    OPERATOR = "operator"
    TOOL = "tool"


class MRPActionType(str, Enum):
    """Type d'action MRP."""
    CREATE_ORDER = "create_order"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    EXPEDITE = "expedite"


class UnitOfMeasure(str, Enum):
    """Unité de mesure."""
    PIECE = "piece"
    KG = "kg"
    METER = "meter"
    LITER = "liter"
    HOUR = "hour"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class BOMComponent:
    """Composant d'une nomenclature."""
    id: str
    product_id: str
    product_name: str
    quantity: Decimal
    unit: UnitOfMeasure
    position: int = 0
    is_phantom: bool = False          # Composant fantôme (pas stocké)
    scrap_rate: Decimal = Decimal("0")  # Taux de rebut en %
    lead_time_days: int = 0
    notes: Optional[str] = None


@dataclass
class BillOfMaterials:
    """Nomenclature de fabrication (BOM)."""
    id: str
    tenant_id: str
    product_id: str
    product_name: str
    version: str
    components: list[BOMComponent] = field(default_factory=list)
    is_active: bool = True
    effective_date: date = field(default_factory=date.today)
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_components(self) -> int:
        """Nombre total de composants."""
        return len(self.components)


@dataclass
class RoutingOperation:
    """Opération de gamme de fabrication."""
    id: str
    sequence: int
    name: str
    operation_type: OperationType
    workstation_id: Optional[str] = None
    workstation_name: Optional[str] = None
    setup_time_minutes: int = 0
    run_time_minutes: int = 0
    queue_time_minutes: int = 0
    move_time_minutes: int = 0
    labor_cost_per_hour: Decimal = Decimal("0")
    machine_cost_per_hour: Decimal = Decimal("0")
    instructions: Optional[str] = None

    @property
    def total_time_minutes(self) -> int:
        """Temps total de l'opération."""
        return self.setup_time_minutes + self.run_time_minutes + self.queue_time_minutes + self.move_time_minutes


@dataclass
class Routing:
    """Gamme de fabrication."""
    id: str
    tenant_id: str
    product_id: str
    product_name: str
    version: str
    operations: list[RoutingOperation] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_time_minutes(self) -> int:
        """Temps total de la gamme."""
        return sum(op.total_time_minutes for op in self.operations)


@dataclass
class ManufacturingOrder:
    """Ordre de fabrication (OF)."""
    id: str
    tenant_id: str
    order_number: str
    product_id: str
    product_name: str
    quantity_planned: Decimal
    quantity_produced: Decimal = Decimal("0")
    quantity_scrapped: Decimal = Decimal("0")
    unit: UnitOfMeasure = UnitOfMeasure.PIECE
    status: ProductionStatus = ProductionStatus.DRAFT
    priority: int = 5  # 1-10, 10 = highest
    bom_id: Optional[str] = None
    routing_id: Optional[str] = None
    parent_order_id: Optional[str] = None  # Pour sous-assemblages
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    workstation_id: Optional[str] = None
    operator_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    @property
    def quantity_remaining(self) -> Decimal:
        """Quantité restante à produire."""
        return self.quantity_planned - self.quantity_produced - self.quantity_scrapped

    @property
    def completion_rate(self) -> Decimal:
        """Taux de complétion."""
        if self.quantity_planned == 0:
            return Decimal("0")
        return (self.quantity_produced / self.quantity_planned * 100).quantize(Decimal("0.01"))

    @property
    def scrap_rate(self) -> Decimal:
        """Taux de rebut."""
        total = self.quantity_produced + self.quantity_scrapped
        if total == 0:
            return Decimal("0")
        return (self.quantity_scrapped / total * 100).quantize(Decimal("0.01"))


@dataclass
class MRPRequirement:
    """Besoin calculé par MRP."""
    id: str
    tenant_id: str
    product_id: str
    product_name: str
    requirement_date: date
    gross_requirement: Decimal
    scheduled_receipts: Decimal
    projected_on_hand: Decimal
    net_requirement: Decimal
    planned_order_release: Optional[date] = None
    planned_order_quantity: Decimal = Decimal("0")
    action_type: Optional[MRPActionType] = None
    action_message: Optional[str] = None
    level: int = 0  # 0 = produit fini, 1+ = composants
    parent_product_id: Optional[str] = None


@dataclass
class CapacityPlan:
    """Plan de capacité."""
    id: str
    tenant_id: str
    workstation_id: str
    workstation_name: str
    date: date
    available_hours: Decimal
    planned_hours: Decimal
    actual_hours: Decimal = Decimal("0")
    orders: list[str] = field(default_factory=list)

    @property
    def utilization_rate(self) -> Decimal:
        """Taux d'utilisation."""
        if self.available_hours == 0:
            return Decimal("0")
        return (self.planned_hours / self.available_hours * 100).quantize(Decimal("0.01"))

    @property
    def is_overloaded(self) -> bool:
        """Vérifie si le poste est surchargé."""
        return self.planned_hours > self.available_hours


@dataclass
class ProductionProgress:
    """Avancement de production."""
    order_id: str
    operation_id: str
    operation_name: str
    quantity_started: Decimal
    quantity_completed: Decimal
    quantity_scrapped: Decimal
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    operator_id: Optional[str] = None


# =============================================================================
# SERVICE
# =============================================================================


class GPAOService:
    """
    Service de gestion de production (GPAO/MRP).

    Multi-tenant: OUI - Données isolées par tenant
    Fonctionnalités: OF, BOM, Gammes, MRP, Capacité
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
        self._boms: dict[str, BillOfMaterials] = {}
        self._routings: dict[str, Routing] = {}
        self._orders: dict[str, ManufacturingOrder] = {}
        self._order_counter = 1000

        logger.info(f"GPAOService initialisé pour tenant {tenant_id}")

    # =========================================================================
    # BOM MANAGEMENT
    # =========================================================================

    async def create_bom(
        self,
        product_id: str,
        product_name: str,
        components: list[dict],
        version: str = "1.0",
        effective_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> BillOfMaterials:
        """Crée une nomenclature."""
        bom = BillOfMaterials(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            product_id=product_id,
            product_name=product_name,
            version=version,
            components=[
                BOMComponent(
                    id=str(uuid.uuid4()),
                    product_id=c["product_id"],
                    product_name=c.get("product_name", ""),
                    quantity=Decimal(str(c["quantity"])),
                    unit=UnitOfMeasure(c.get("unit", "piece")),
                    position=i,
                    is_phantom=c.get("is_phantom", False),
                    scrap_rate=Decimal(str(c.get("scrap_rate", 0))),
                    lead_time_days=c.get("lead_time_days", 0),
                )
                for i, c in enumerate(components)
            ],
            effective_date=effective_date or date.today(),
            notes=notes,
        )

        self._boms[bom.id] = bom

        logger.info(f"BOM créée: {product_name} v{version}")
        return bom

    async def get_bom(self, bom_id: str) -> Optional[BillOfMaterials]:
        """Récupère une nomenclature."""
        bom = self._boms.get(bom_id)
        if bom and bom.tenant_id == self.tenant_id:
            return bom
        return None

    async def get_bom_for_product(self, product_id: str) -> Optional[BillOfMaterials]:
        """Récupère la BOM active d'un produit."""
        for bom in self._boms.values():
            if (bom.tenant_id == self.tenant_id
                and bom.product_id == product_id
                and bom.is_active):
                return bom
        return None

    async def list_boms(
        self,
        product_id: Optional[str] = None,
        active_only: bool = True,
    ) -> list[BillOfMaterials]:
        """Liste les nomenclatures."""
        boms = [b for b in self._boms.values() if b.tenant_id == self.tenant_id]

        if product_id:
            boms = [b for b in boms if b.product_id == product_id]

        if active_only:
            boms = [b for b in boms if b.is_active]

        return sorted(boms, key=lambda b: b.product_name)

    async def add_bom_component(
        self,
        bom_id: str,
        product_id: str,
        product_name: str,
        quantity: Decimal,
        unit: UnitOfMeasure = UnitOfMeasure.PIECE,
    ) -> Optional[BillOfMaterials]:
        """Ajoute un composant à une BOM."""
        bom = await self.get_bom(bom_id)
        if not bom:
            return None

        component = BOMComponent(
            id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit=unit,
            position=len(bom.components),
        )

        bom.components.append(component)
        bom.updated_at = datetime.now()

        return bom

    # =========================================================================
    # ROUTING MANAGEMENT
    # =========================================================================

    async def create_routing(
        self,
        product_id: str,
        product_name: str,
        operations: list[dict],
        version: str = "1.0",
    ) -> Routing:
        """Crée une gamme de fabrication."""
        routing = Routing(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            product_id=product_id,
            product_name=product_name,
            version=version,
            operations=[
                RoutingOperation(
                    id=str(uuid.uuid4()),
                    sequence=i + 1,
                    name=op["name"],
                    operation_type=OperationType(op.get("type", "other")),
                    workstation_id=op.get("workstation_id"),
                    workstation_name=op.get("workstation_name"),
                    setup_time_minutes=op.get("setup_time", 0),
                    run_time_minutes=op.get("run_time", 0),
                    queue_time_minutes=op.get("queue_time", 0),
                    instructions=op.get("instructions"),
                )
                for i, op in enumerate(operations)
            ],
        )

        self._routings[routing.id] = routing

        logger.info(f"Gamme créée: {product_name} v{version}")
        return routing

    async def get_routing(self, routing_id: str) -> Optional[Routing]:
        """Récupère une gamme."""
        routing = self._routings.get(routing_id)
        if routing and routing.tenant_id == self.tenant_id:
            return routing
        return None

    async def get_routing_for_product(self, product_id: str) -> Optional[Routing]:
        """Récupère la gamme active d'un produit."""
        for routing in self._routings.values():
            if (routing.tenant_id == self.tenant_id
                and routing.product_id == product_id
                and routing.is_active):
                return routing
        return None

    async def list_routings(
        self,
        product_id: Optional[str] = None,
    ) -> list[Routing]:
        """Liste les gammes."""
        routings = [r for r in self._routings.values() if r.tenant_id == self.tenant_id]

        if product_id:
            routings = [r for r in routings if r.product_id == product_id]

        return sorted(routings, key=lambda r: r.product_name)

    # =========================================================================
    # MANUFACTURING ORDERS
    # =========================================================================

    async def create_manufacturing_order(
        self,
        product_id: str,
        product_name: str,
        quantity: Decimal,
        unit: UnitOfMeasure = UnitOfMeasure.PIECE,
        planned_start: Optional[datetime] = None,
        planned_end: Optional[datetime] = None,
        priority: int = 5,
        bom_id: Optional[str] = None,
        routing_id: Optional[str] = None,
        parent_order_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ManufacturingOrder:
        """Crée un ordre de fabrication."""
        self._order_counter += 1
        order_number = f"OF-{self._order_counter:06d}"

        # Récupérer BOM et Gamme si non spécifiés
        if not bom_id:
            bom = await self.get_bom_for_product(product_id)
            bom_id = bom.id if bom else None

        if not routing_id:
            routing = await self.get_routing_for_product(product_id)
            routing_id = routing.id if routing else None

        order = ManufacturingOrder(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            order_number=order_number,
            product_id=product_id,
            product_name=product_name,
            quantity_planned=quantity,
            unit=unit,
            priority=priority,
            bom_id=bom_id,
            routing_id=routing_id,
            parent_order_id=parent_order_id,
            planned_start=planned_start,
            planned_end=planned_end,
            notes=notes,
        )

        self._orders[order.id] = order

        logger.info(f"OF créé: {order_number} - {product_name} x {quantity}")
        return order

    async def get_order(self, order_id: str) -> Optional[ManufacturingOrder]:
        """Récupère un ordre de fabrication."""
        order = self._orders.get(order_id)
        if order and order.tenant_id == self.tenant_id:
            return order
        return None

    async def get_order_by_number(self, order_number: str) -> Optional[ManufacturingOrder]:
        """Récupère un OF par son numéro."""
        for order in self._orders.values():
            if order.tenant_id == self.tenant_id and order.order_number == order_number:
                return order
        return None

    async def list_orders(
        self,
        status: Optional[ProductionStatus] = None,
        product_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> list[ManufacturingOrder]:
        """Liste les ordres de fabrication."""
        orders = [o for o in self._orders.values() if o.tenant_id == self.tenant_id]

        if status:
            orders = [o for o in orders if o.status == status]

        if product_id:
            orders = [o for o in orders if o.product_id == product_id]

        if start_date and orders:
            orders = [o for o in orders if o.planned_start and o.planned_start.date() >= start_date]

        if end_date and orders:
            orders = [o for o in orders if o.planned_start and o.planned_start.date() <= end_date]

        return sorted(orders, key=lambda o: (o.priority, o.created_at), reverse=True)[:limit]

    async def release_order(self, order_id: str) -> Optional[ManufacturingOrder]:
        """Lance un ordre de fabrication."""
        order = await self.get_order(order_id)
        if not order or order.status not in [ProductionStatus.DRAFT, ProductionStatus.PLANNED]:
            return None

        order.status = ProductionStatus.RELEASED
        order.updated_at = datetime.now()

        logger.info(f"OF lancé: {order.order_number}")
        return order

    async def start_order(self, order_id: str) -> Optional[ManufacturingOrder]:
        """Démarre un ordre de fabrication."""
        order = await self.get_order(order_id)
        if not order or order.status != ProductionStatus.RELEASED:
            return None

        order.status = ProductionStatus.IN_PROGRESS
        order.actual_start = datetime.now()
        order.updated_at = datetime.now()

        logger.info(f"OF démarré: {order.order_number}")
        return order

    async def report_production(
        self,
        order_id: str,
        quantity_produced: Decimal,
        quantity_scrapped: Decimal = Decimal("0"),
        operator_id: Optional[str] = None,
    ) -> Optional[ManufacturingOrder]:
        """Déclare de la production."""
        order = await self.get_order(order_id)
        if not order or order.status != ProductionStatus.IN_PROGRESS:
            return None

        order.quantity_produced += quantity_produced
        order.quantity_scrapped += quantity_scrapped
        order.operator_id = operator_id
        order.updated_at = datetime.now()

        # Vérifier si complété
        if order.quantity_remaining <= 0:
            order.status = ProductionStatus.COMPLETED
            order.actual_end = datetime.now()

        logger.info(
            f"Production déclarée sur {order.order_number}: "
            f"+{quantity_produced} produit, +{quantity_scrapped} rebut"
        )
        return order

    async def complete_order(self, order_id: str) -> Optional[ManufacturingOrder]:
        """Termine un ordre de fabrication."""
        order = await self.get_order(order_id)
        if not order or order.status != ProductionStatus.IN_PROGRESS:
            return None

        order.status = ProductionStatus.COMPLETED
        order.actual_end = datetime.now()
        order.updated_at = datetime.now()

        logger.info(f"OF terminé: {order.order_number}")
        return order

    async def cancel_order(
        self,
        order_id: str,
        reason: Optional[str] = None,
    ) -> Optional[ManufacturingOrder]:
        """Annule un ordre de fabrication."""
        order = await self.get_order(order_id)
        if not order or order.status in [ProductionStatus.COMPLETED, ProductionStatus.CANCELLED]:
            return None

        order.status = ProductionStatus.CANCELLED
        order.metadata["cancel_reason"] = reason
        order.updated_at = datetime.now()

        logger.info(f"OF annulé: {order.order_number}")
        return order

    # =========================================================================
    # MRP CALCULATION
    # =========================================================================

    async def calculate_requirements(
        self,
        product_id: str,
        product_name: str,
        quantity: Decimal,
        due_date: date,
        on_hand: Decimal = Decimal("0"),
        scheduled_receipts: Decimal = Decimal("0"),
    ) -> list[MRPRequirement]:
        """
        Calcule les besoins MRP pour un produit.

        Effectue l'éclatement de nomenclature et calcule les besoins nets.
        """
        requirements = []

        # Besoin niveau 0 (produit fini)
        gross_req = quantity
        net_req = max(Decimal("0"), gross_req - on_hand - scheduled_receipts)

        req = MRPRequirement(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            product_id=product_id,
            product_name=product_name,
            requirement_date=due_date,
            gross_requirement=gross_req,
            scheduled_receipts=scheduled_receipts,
            projected_on_hand=on_hand,
            net_requirement=net_req,
            level=0,
        )

        if net_req > 0:
            req.action_type = MRPActionType.CREATE_ORDER
            req.action_message = f"Créer OF pour {net_req} {product_name}"
            req.planned_order_quantity = net_req

            # Calculer date de lancement
            bom = await self.get_bom_for_product(product_id)
            routing = await self.get_routing_for_product(product_id)

            lead_time_days = 1
            if routing:
                lead_time_days = max(1, routing.total_time_minutes // 480)  # 8h/jour

            req.planned_order_release = due_date - timedelta(days=lead_time_days)

        requirements.append(req)

        # Éclatement BOM niveau 1
        if net_req > 0:
            bom = await self.get_bom_for_product(product_id)
            if bom:
                for comp in bom.components:
                    comp_qty = net_req * comp.quantity * (1 + comp.scrap_rate / 100)
                    comp_due = due_date - timedelta(days=comp.lead_time_days)

                    comp_req = MRPRequirement(
                        id=str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        product_id=comp.product_id,
                        product_name=comp.product_name,
                        requirement_date=comp_due,
                        gross_requirement=comp_qty,
                        scheduled_receipts=Decimal("0"),
                        projected_on_hand=Decimal("0"),
                        net_requirement=comp_qty,
                        level=1,
                        parent_product_id=product_id,
                        action_type=MRPActionType.CREATE_ORDER,
                        action_message=f"Besoin: {comp_qty} {comp.product_name}",
                        planned_order_quantity=comp_qty,
                        planned_order_release=comp_due - timedelta(days=1),
                    )
                    requirements.append(comp_req)

        return requirements

    async def run_mrp(
        self,
        horizon_days: int = 30,
    ) -> list[MRPRequirement]:
        """
        Exécute le calcul MRP complet.

        Analyse tous les OF planifiés et calcule les besoins.
        """
        requirements = []
        end_date = date.today() + timedelta(days=horizon_days)

        # Analyser les OF planifiés/lancés
        orders = await self.list_orders(status=ProductionStatus.PLANNED)
        orders += await self.list_orders(status=ProductionStatus.RELEASED)

        for order in orders:
            if order.planned_start and order.planned_start.date() <= end_date:
                order_reqs = await self.calculate_requirements(
                    product_id=order.product_id,
                    product_name=order.product_name,
                    quantity=order.quantity_remaining,
                    due_date=order.planned_end.date() if order.planned_end else date.today(),
                )
                requirements.extend(order_reqs)

        return requirements

    # =========================================================================
    # CAPACITY PLANNING
    # =========================================================================

    async def calculate_capacity(
        self,
        workstation_id: str,
        workstation_name: str,
        start_date: date,
        end_date: date,
        available_hours_per_day: Decimal = Decimal("8"),
    ) -> list[CapacityPlan]:
        """Calcule le plan de capacité pour un poste."""
        plans = []
        current = start_date

        while current <= end_date:
            # Collecter les OF assignés à ce poste
            orders = [
                o for o in self._orders.values()
                if o.tenant_id == self.tenant_id
                and o.workstation_id == workstation_id
                and o.planned_start
                and o.planned_start.date() == current
                and o.status in [ProductionStatus.PLANNED, ProductionStatus.RELEASED]
            ]

            # Calculer les heures planifiées
            planned_hours = Decimal("0")
            order_ids = []

            for order in orders:
                routing = await self.get_routing(order.routing_id) if order.routing_id else None
                if routing:
                    planned_hours += Decimal(routing.total_time_minutes) / 60
                order_ids.append(order.id)

            plan = CapacityPlan(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                workstation_id=workstation_id,
                workstation_name=workstation_name,
                date=current,
                available_hours=available_hours_per_day,
                planned_hours=planned_hours,
                orders=order_ids,
            )
            plans.append(plan)

            current += timedelta(days=1)

        return plans

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_production_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Statistiques de production."""
        orders = [o for o in self._orders.values() if o.tenant_id == self.tenant_id]

        if start_date:
            orders = [o for o in orders if o.created_at.date() >= start_date]
        if end_date:
            orders = [o for o in orders if o.created_at.date() <= end_date]

        total = len(orders)
        completed = len([o for o in orders if o.status == ProductionStatus.COMPLETED])
        in_progress = len([o for o in orders if o.status == ProductionStatus.IN_PROGRESS])
        planned = len([o for o in orders if o.status in [ProductionStatus.DRAFT, ProductionStatus.PLANNED]])

        total_produced = sum(o.quantity_produced for o in orders)
        total_scrapped = sum(o.quantity_scrapped for o in orders)

        avg_completion_rate = Decimal("0")
        completed_orders = [o for o in orders if o.status == ProductionStatus.COMPLETED]
        if completed_orders:
            avg_completion_rate = sum(o.completion_rate for o in completed_orders) / len(completed_orders)

        return {
            "total_orders": total,
            "completed_orders": completed,
            "in_progress_orders": in_progress,
            "planned_orders": planned,
            "total_quantity_produced": str(total_produced),
            "total_quantity_scrapped": str(total_scrapped),
            "average_completion_rate": str(avg_completion_rate),
            "scrap_rate": str(
                (total_scrapped / (total_produced + total_scrapped) * 100).quantize(Decimal("0.01"))
                if total_produced + total_scrapped > 0
                else Decimal("0")
            ),
            "bom_count": len([b for b in self._boms.values() if b.tenant_id == self.tenant_id]),
            "routing_count": len([r for r in self._routings.values() if r.tenant_id == self.tenant_id]),
        }
