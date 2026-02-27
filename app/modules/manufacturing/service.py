"""
Service Manufacturing / Fabrication
====================================
- Logique métier
- Orchestration des repositories
- Validation des règles
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    BOM, ManufacturingBOMLine, BOMStatus, BOMType,
    Workcenter, WorkcenterState, WorkcenterType,
    Routing, Operation,
    WorkOrder, WorkOrderStatus, WorkOrderOperation, OperationStatus,
    QualityCheck, QualityCheckType, QualityResult,
    ProductionLog
)
from .repository import (
    BOMRepository, WorkcenterRepository, RoutingRepository,
    WorkOrderRepository, QualityCheckRepository, ProductionLogRepository
)
from .schemas import (
    BOMCreate, BOMUpdate, BOMFilters, BOMLineCreate, BOMLineUpdate,
    WorkcenterCreate, WorkcenterUpdate, WorkcenterFilters,
    RoutingCreate, RoutingUpdate, OperationCreate, OperationUpdate,
    WorkOrderCreate, WorkOrderUpdate, WorkOrderFilters,
    QualityCheckCreate, QualityCheckUpdate,
    ProductionLogCreate, ProductionStats
)
from .exceptions import (
    BOMNotFoundError, BOMDuplicateError, BOMValidationError, BOMStateError,
    BOMLineNotFoundError,
    WorkcenterNotFoundError, WorkcenterDuplicateError, WorkcenterValidationError,
    WorkcenterBusyError,
    RoutingNotFoundError, RoutingDuplicateError, RoutingValidationError,
    OperationNotFoundError,
    WorkOrderNotFoundError, WorkOrderDuplicateError, WorkOrderValidationError,
    WorkOrderStateError, WorkOrderOperationNotFoundError, WorkOrderOperationStateError,
    QualityCheckNotFoundError, QualityCheckValidationError,
    ProductionLogValidationError
)


class ManufacturingService:
    """
    Service métier Manufacturing.
    Encapsule toute la logique métier.
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        user_id: UUID = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Repositories
        self.bom_repo = BOMRepository(db, tenant_id)
        self.workcenter_repo = WorkcenterRepository(db, tenant_id)
        self.routing_repo = RoutingRepository(db, tenant_id)
        self.work_order_repo = WorkOrderRepository(db, tenant_id)
        self.quality_check_repo = QualityCheckRepository(db, tenant_id)
        self.production_log_repo = ProductionLogRepository(db, tenant_id)

    # ================== BOM ==================

    def get_bom(self, id: UUID) -> BOM:
        """Récupère une BOM par ID."""
        bom = self.bom_repo.get_by_id(id)
        if not bom:
            raise BOMNotFoundError(f"BOM {id} not found")
        return bom

    def get_bom_by_code(self, code: str) -> BOM:
        """Récupère une BOM par code."""
        bom = self.bom_repo.get_by_code(code)
        if not bom:
            raise BOMNotFoundError(f"BOM code={code} not found")
        return bom

    def list_boms(
        self,
        filters: BOMFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[BOM], int, int]:
        """Liste paginée des BOMs."""
        items, total = self.bom_repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create_bom(self, data: BOMCreate) -> BOM:
        """Crée une nouvelle BOM."""
        # Vérifier unicité code
        if self.bom_repo.code_exists(data.code):
            raise BOMDuplicateError(f"Code {data.code} already exists")

        return self.bom_repo.create(
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def update_bom(self, id: UUID, data: BOMUpdate) -> BOM:
        """Met à jour une BOM."""
        bom = self.get_bom(id)

        # Vérifier transition de statut
        if data.status and data.status != bom.status:
            allowed = BOMStatus.allowed_transitions().get(bom.status, [])
            if data.status not in allowed:
                raise BOMStateError(
                    f"Transition {bom.status} -> {data.status} not allowed"
                )

        return self.bom_repo.update(
            bom,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def delete_bom(self, id: UUID, hard: bool = False) -> bool:
        """Supprime une BOM."""
        bom = self.get_bom(id)

        can_delete, reason = bom.can_delete()
        if not can_delete:
            raise BOMValidationError(reason)

        if hard:
            return self.bom_repo.hard_delete(bom)
        return self.bom_repo.soft_delete(bom, self.user_id)

    def restore_bom(self, id: UUID) -> BOM:
        """Restaure une BOM supprimée."""
        repo_deleted = BOMRepository(self.db, self.tenant_id, include_deleted=True)
        bom = repo_deleted.get_by_id(id)

        if not bom:
            raise BOMNotFoundError(f"BOM {id} not found")
        if not bom.is_deleted:
            raise BOMValidationError("BOM is not deleted")

        return self.bom_repo.restore(bom)

    def activate_bom(self, id: UUID) -> BOM:
        """Active une BOM (et désactive les autres pour ce produit)."""
        bom = self.get_bom(id)

        if bom.status == BOMStatus.OBSOLETE:
            raise BOMStateError("Cannot activate obsolete BOM")

        # Désactiver les autres BOMs actives pour ce produit
        items, _ = self.bom_repo.list(
            BOMFilters(product_id=bom.product_id, status=[BOMStatus.ACTIVE])
        )
        for other in items:
            if other.id != bom.id:
                other.status = BOMStatus.OBSOLETE
                other.is_current = False

        bom.status = BOMStatus.ACTIVE
        bom.is_current = True
        self.db.commit()
        self.db.refresh(bom)

        return bom

    def add_bom_line(self, bom_id: UUID, data: BOMLineCreate) -> ManufacturingBOMLine:
        """Ajoute une ligne à une BOM."""
        bom = self.get_bom(bom_id)

        if bom.status == BOMStatus.ACTIVE:
            raise BOMValidationError("Cannot modify active BOM")

        return self.bom_repo.add_line(bom, data.model_dump(exclude_unset=True))

    def update_bom_line(self, bom_id: UUID, line_id: UUID, data: BOMLineUpdate) -> ManufacturingBOMLine:
        """Met à jour une ligne de BOM."""
        bom = self.get_bom(bom_id)

        if bom.status == BOMStatus.ACTIVE:
            raise BOMValidationError("Cannot modify active BOM")

        line = next((l for l in bom.lines if l.id == line_id), None)
        if not line:
            raise BOMLineNotFoundError(f"Line {line_id} not found")

        return self.bom_repo.update_line(line, data.model_dump(exclude_unset=True))

    def delete_bom_line(self, bom_id: UUID, line_id: UUID) -> bool:
        """Supprime une ligne de BOM."""
        bom = self.get_bom(bom_id)

        if bom.status == BOMStatus.ACTIVE:
            raise BOMValidationError("Cannot modify active BOM")

        line = next((l for l in bom.lines if l.id == line_id), None)
        if not line:
            raise BOMLineNotFoundError(f"Line {line_id} not found")

        return self.bom_repo.delete_line(line)

    def explode_bom(self, bom_id: UUID, quantity: Decimal = Decimal("1")) -> List[Dict[str, Any]]:
        """Explose une BOM (liste tous les composants nécessaires)."""
        bom = self.get_bom(bom_id)

        components = []
        multiplier = quantity / bom.quantity

        for line in bom.lines:
            if line.is_deleted:
                continue

            required_qty = line.quantity * multiplier * (1 + line.scrap_rate / 100)

            component = {
                "component_id": str(line.component_id),
                "component_code": line.component_code,
                "component_name": line.component_name,
                "quantity": required_qty,
                "unit": line.unit,
                "unit_cost": line.unit_cost,
                "total_cost": required_qty * line.unit_cost,
                "level": 1,
                "is_optional": line.is_optional
            }
            components.append(component)

            # Explosion récursive
            sub_bom = self.bom_repo.get_current_for_product(line.component_id)
            if sub_bom and sub_bom.bom_type != BOMType.PHANTOM:
                sub_components = self.explode_bom(sub_bom.id, required_qty)
                for sc in sub_components:
                    sc["level"] += 1
                components.extend(sub_components)

        return components

    def autocomplete_bom(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete BOMs."""
        return self.bom_repo.autocomplete(prefix, field, limit)

    # ================== Workcenter ==================

    def get_workcenter(self, id: UUID) -> Workcenter:
        """Récupère un Workcenter par ID."""
        wc = self.workcenter_repo.get_by_id(id)
        if not wc:
            raise WorkcenterNotFoundError(f"Workcenter {id} not found")
        return wc

    def get_workcenter_by_code(self, code: str) -> Workcenter:
        """Récupère un Workcenter par code."""
        wc = self.workcenter_repo.get_by_code(code)
        if not wc:
            raise WorkcenterNotFoundError(f"Workcenter code={code} not found")
        return wc

    def list_workcenters(
        self,
        filters: WorkcenterFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "code",
        sort_dir: str = "asc"
    ) -> Tuple[List[Workcenter], int, int]:
        """Liste paginée des Workcenters."""
        items, total = self.workcenter_repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create_workcenter(self, data: WorkcenterCreate) -> Workcenter:
        """Crée un nouveau Workcenter."""
        if self.workcenter_repo.code_exists(data.code):
            raise WorkcenterDuplicateError(f"Code {data.code} already exists")

        return self.workcenter_repo.create(
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def update_workcenter(self, id: UUID, data: WorkcenterUpdate) -> Workcenter:
        """Met à jour un Workcenter."""
        wc = self.get_workcenter(id)
        return self.workcenter_repo.update(
            wc,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def delete_workcenter(self, id: UUID, hard: bool = False) -> bool:
        """Supprime un Workcenter."""
        wc = self.get_workcenter(id)

        can_delete, reason = wc.can_delete()
        if not can_delete:
            raise WorkcenterValidationError(reason)

        if hard:
            return self.workcenter_repo.hard_delete(wc)
        return self.workcenter_repo.soft_delete(wc, self.user_id)

    def set_workcenter_state(
        self,
        id: UUID,
        state: WorkcenterState
    ) -> Workcenter:
        """Change l'état d'un Workcenter."""
        wc = self.get_workcenter(id)

        wc.state = state
        if state == WorkcenterState.MAINTENANCE:
            wc.last_maintenance = datetime.utcnow()

        self.db.commit()
        self.db.refresh(wc)
        return wc

    def get_available_workcenters(self) -> List[Workcenter]:
        """Liste les Workcenters disponibles."""
        return self.workcenter_repo.get_available()

    def autocomplete_workcenter(
        self,
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete Workcenters."""
        return self.workcenter_repo.autocomplete(prefix, field, limit)

    # ================== Routing ==================

    def get_routing(self, id: UUID) -> Routing:
        """Récupère une Routing par ID."""
        routing = self.routing_repo.get_by_id(id)
        if not routing:
            raise RoutingNotFoundError(f"Routing {id} not found")
        return routing

    def get_routing_by_code(self, code: str) -> Routing:
        """Récupère une Routing par code."""
        routing = self.routing_repo.get_by_code(code)
        if not routing:
            raise RoutingNotFoundError(f"Routing code={code} not found")
        return routing

    def list_routings(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "code",
        sort_dir: str = "asc",
        product_id: UUID = None,
        is_active: bool = None
    ) -> Tuple[List[Routing], int, int]:
        """Liste paginée des Routings."""
        items, total = self.routing_repo.list(
            page, page_size, sort_by, sort_dir, product_id, is_active
        )
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create_routing(self, data: RoutingCreate) -> Routing:
        """Crée une nouvelle Routing."""
        if self.routing_repo.code_exists(data.code):
            raise RoutingDuplicateError(f"Code {data.code} already exists")

        return self.routing_repo.create(
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def update_routing(self, id: UUID, data: RoutingUpdate) -> Routing:
        """Met à jour une Routing."""
        routing = self.get_routing(id)
        return self.routing_repo.update(
            routing,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def delete_routing(self, id: UUID, hard: bool = False) -> bool:
        """Supprime une Routing."""
        routing = self.get_routing(id)

        if hard:
            self.db.delete(routing)
            self.db.commit()
            return True
        return self.routing_repo.soft_delete(routing, self.user_id)

    def add_operation(self, routing_id: UUID, data: OperationCreate) -> Operation:
        """Ajoute une opération à une Routing."""
        routing = self.get_routing(routing_id)

        # Vérifier que le workcenter existe
        wc = self.workcenter_repo.get_by_id(data.workcenter_id)
        if not wc:
            raise WorkcenterNotFoundError(f"Workcenter {data.workcenter_id} not found")

        op_data = data.model_dump(exclude_unset=True)
        op_data['workcenter_name'] = wc.name

        # Calculer les coûts
        operation = self.routing_repo.add_operation(routing, op_data)
        operation.calculate_costs(wc.hourly_cost)
        self.db.commit()
        self.db.refresh(operation)

        return operation

    def autocomplete_routing(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete Routings."""
        return self.routing_repo.autocomplete(prefix, limit)

    # ================== Work Order ==================

    def get_work_order(self, id: UUID) -> WorkOrder:
        """Récupère un Work Order par ID."""
        wo = self.work_order_repo.get_by_id(id)
        if not wo:
            raise WorkOrderNotFoundError(f"Work Order {id} not found")
        return wo

    def get_work_order_by_number(self, number: str) -> WorkOrder:
        """Récupère un Work Order par numéro."""
        wo = self.work_order_repo.get_by_number(number)
        if not wo:
            raise WorkOrderNotFoundError(f"Work Order number={number} not found")
        return wo

    def list_work_orders(
        self,
        filters: WorkOrderFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[WorkOrder], int, int]:
        """Liste paginée des Work Orders."""
        items, total = self.work_order_repo.list(filters, page, page_size, sort_by, sort_dir)
        pages = (total + page_size - 1) // page_size
        return items, total, pages

    def create_work_order(self, data: WorkOrderCreate) -> WorkOrder:
        """Crée un nouveau Work Order."""
        wo_data = data.model_dump(exclude_unset=True)

        # Trouver BOM et Routing si non spécifiés
        if not wo_data.get('bom_id'):
            bom = self.bom_repo.get_current_for_product(data.product_id)
            if bom:
                wo_data['bom_id'] = bom.id
                if bom.routing_id and not wo_data.get('routing_id'):
                    wo_data['routing_id'] = bom.routing_id

        wo = self.work_order_repo.create(wo_data, self.user_id)

        # Calculer les coûts planifiés
        if wo.bom_id:
            bom = self.bom_repo.get_by_id(wo.bom_id)
            if bom:
                wo.planned_material_cost = bom.material_cost * wo.quantity_to_produce / bom.quantity

        if wo.routing_id:
            routing = self.routing_repo.get_by_id(wo.routing_id)
            if routing:
                wo.planned_labor_cost = routing.total_cost_per_unit * wo.quantity_to_produce

                # Créer les opérations
                for op in routing.operations:
                    if op.is_deleted:
                        continue
                    wo_op = WorkOrderOperation(
                        tenant_id=self.tenant_id,
                        work_order_id=wo.id,
                        operation_id=op.id,
                        sequence=op.sequence,
                        name=op.name,
                        workcenter_id=op.workcenter_id,
                        planned_setup_time=op.setup_time,
                        planned_run_time=int(op.run_time * float(wo.quantity_to_produce)),
                        quantity_to_produce=wo.quantity_to_produce
                    )
                    self.db.add(wo_op)

        wo.planned_total_cost = (
            wo.planned_material_cost +
            wo.planned_labor_cost +
            wo.planned_overhead_cost
        )
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def update_work_order(self, id: UUID, data: WorkOrderUpdate) -> WorkOrder:
        """Met à jour un Work Order."""
        wo = self.get_work_order(id)

        # Vérifier transition de statut
        if data.status and data.status != wo.status:
            allowed = WorkOrderStatus.allowed_transitions().get(wo.status, [])
            if data.status not in allowed:
                raise WorkOrderStateError(
                    f"Transition {wo.status} -> {data.status} not allowed"
                )

        return self.work_order_repo.update(
            wo,
            data.model_dump(exclude_unset=True),
            self.user_id
        )

    def delete_work_order(self, id: UUID, hard: bool = False) -> bool:
        """Supprime un Work Order."""
        wo = self.get_work_order(id)

        can_delete, reason = wo.can_delete()
        if not can_delete:
            raise WorkOrderValidationError(reason)

        if hard:
            self.db.delete(wo)
            self.db.commit()
            return True
        return self.work_order_repo.soft_delete(wo, self.user_id)

    def confirm_work_order(self, id: UUID) -> WorkOrder:
        """Confirme un Work Order."""
        wo = self.get_work_order(id)

        if wo.status != WorkOrderStatus.DRAFT:
            raise WorkOrderStateError("Can only confirm DRAFT work orders")

        wo.status = WorkOrderStatus.CONFIRMED
        self._log_production(wo.id, None, "confirmed", Decimal("0"))
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def start_work_order(self, id: UUID) -> WorkOrder:
        """Démarre un Work Order."""
        wo = self.get_work_order(id)

        if wo.status not in [WorkOrderStatus.CONFIRMED, WorkOrderStatus.PLANNED]:
            raise WorkOrderStateError(
                f"Cannot start work order in status {wo.status}"
            )

        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.actual_start = datetime.utcnow()
        self._log_production(wo.id, None, "started", Decimal("0"))
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def pause_work_order(self, id: UUID) -> WorkOrder:
        """Met en pause un Work Order."""
        wo = self.get_work_order(id)

        if wo.status != WorkOrderStatus.IN_PROGRESS:
            raise WorkOrderStateError("Can only pause IN_PROGRESS work orders")

        wo.status = WorkOrderStatus.PAUSED
        self._log_production(wo.id, None, "paused", Decimal("0"))
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def resume_work_order(self, id: UUID) -> WorkOrder:
        """Reprend un Work Order."""
        wo = self.get_work_order(id)

        if wo.status != WorkOrderStatus.PAUSED:
            raise WorkOrderStateError("Can only resume PAUSED work orders")

        wo.status = WorkOrderStatus.IN_PROGRESS
        self._log_production(wo.id, None, "resumed", Decimal("0"))
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def complete_work_order(self, id: UUID) -> WorkOrder:
        """Termine un Work Order."""
        wo = self.get_work_order(id)

        if wo.status != WorkOrderStatus.IN_PROGRESS:
            raise WorkOrderStateError("Can only complete IN_PROGRESS work orders")

        wo.status = WorkOrderStatus.COMPLETED
        wo.actual_end = datetime.utcnow()
        wo.actual_total_cost = (
            wo.actual_material_cost +
            wo.actual_labor_cost +
            wo.actual_overhead_cost
        )
        self._log_production(wo.id, None, "completed", wo.quantity_produced)
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def cancel_work_order(self, id: UUID) -> WorkOrder:
        """Annule un Work Order."""
        wo = self.get_work_order(id)

        if wo.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]:
            raise WorkOrderStateError(f"Cannot cancel work order in status {wo.status}")

        wo.status = WorkOrderStatus.CANCELLED
        self._log_production(wo.id, None, "cancelled", Decimal("0"))
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def record_production(
        self,
        id: UUID,
        quantity_produced: Decimal,
        quantity_scrapped: Decimal = Decimal("0"),
        operator_id: UUID = None
    ) -> WorkOrder:
        """Enregistre une production."""
        wo = self.get_work_order(id)

        if wo.status != WorkOrderStatus.IN_PROGRESS:
            raise WorkOrderStateError("Can only record production on IN_PROGRESS work orders")

        wo.quantity_produced += quantity_produced
        wo.quantity_scrapped += quantity_scrapped

        self._log_production(
            wo.id, None, "production",
            quantity_produced,
            {
                "quantity_produced": float(quantity_produced),
                "quantity_scrapped": float(quantity_scrapped),
                "operator_id": str(operator_id) if operator_id else None
            }
        )
        self.db.commit()
        self.db.refresh(wo)

        return wo

    def start_operation(
        self,
        wo_id: UUID,
        operation_id: UUID,
        operator_id: UUID = None,
        operator_name: str = ""
    ) -> WorkOrderOperation:
        """Démarre une opération."""
        wo = self.get_work_order(wo_id)

        op = next((o for o in wo.operations if o.id == operation_id), None)
        if not op:
            raise WorkOrderOperationNotFoundError(f"Operation {operation_id} not found")

        if op.status != OperationStatus.PENDING:
            raise WorkOrderOperationStateError(
                f"Cannot start operation in status {op.status}"
            )

        op.status = OperationStatus.IN_PROGRESS
        op.actual_start = datetime.utcnow()
        op.operator_id = operator_id
        op.operator_name = operator_name

        # Mettre le workcenter en busy
        if op.workcenter_id:
            wc = self.workcenter_repo.get_by_id(op.workcenter_id)
            if wc:
                wc.state = WorkcenterState.BUSY

        self._log_production(wo_id, op.operation_id, "op_started", Decimal("0"))
        self.db.commit()
        self.db.refresh(op)

        return op

    def complete_operation(
        self,
        wo_id: UUID,
        operation_id: UUID,
        quantity_produced: Decimal,
        quantity_scrapped: Decimal = Decimal("0")
    ) -> WorkOrderOperation:
        """Termine une opération."""
        wo = self.get_work_order(wo_id)

        op = next((o for o in wo.operations if o.id == operation_id), None)
        if not op:
            raise WorkOrderOperationNotFoundError(f"Operation {operation_id} not found")

        if op.status != OperationStatus.IN_PROGRESS:
            raise WorkOrderOperationStateError(
                f"Cannot complete operation in status {op.status}"
            )

        now = datetime.utcnow()
        op.status = OperationStatus.COMPLETED
        op.actual_end = now
        op.quantity_produced = quantity_produced
        op.quantity_scrapped = quantity_scrapped

        if op.actual_start:
            duration = (now - op.actual_start).total_seconds() / 60
            op.actual_run_time = int(duration)

        # Libérer le workcenter
        if op.workcenter_id:
            wc = self.workcenter_repo.get_by_id(op.workcenter_id)
            if wc:
                wc.state = WorkcenterState.AVAILABLE

        self._log_production(
            wo_id, op.operation_id, "op_completed",
            quantity_produced,
            {"quantity_scrapped": float(quantity_scrapped)}
        )
        self.db.commit()
        self.db.refresh(op)

        return op

    def autocomplete_work_order(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Autocomplete Work Orders."""
        return self.work_order_repo.autocomplete(prefix, limit)

    # ================== Quality Check ==================

    def create_quality_check(self, data: QualityCheckCreate) -> QualityCheck:
        """Crée un contrôle qualité."""
        # Vérifier que l'OF existe
        wo = self.work_order_repo.get_by_id(data.work_order_id)
        if not wo:
            raise WorkOrderNotFoundError(f"Work Order {data.work_order_id} not found")

        return self.quality_check_repo.create(data.model_dump(exclude_unset=True))

    def record_quality_result(
        self,
        id: UUID,
        data: QualityCheckUpdate
    ) -> QualityCheck:
        """Enregistre le résultat d'un contrôle qualité."""
        qc = self.quality_check_repo.get_by_id(id)
        if not qc:
            raise QualityCheckNotFoundError(f"Quality Check {id} not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data['checked_at'] = datetime.utcnow()

        qc = self.quality_check_repo.update(qc, update_data)

        # Mettre à jour l'opération si applicable
        if qc.operation_id and data.result:
            wo = self.work_order_repo.get_by_id(qc.work_order_id)
            if wo:
                for op in wo.operations:
                    if op.operation_id == qc.operation_id:
                        op.quality_check_passed = data.result == QualityResult.PASS
                        op.quality_notes = data.notes or ""
                        break

        self._log_production(
            qc.work_order_id, qc.operation_id, "quality_check",
            Decimal("0"),
            {"result": data.result.value if data.result else None}
        )
        self.db.commit()

        return qc

    def list_quality_checks_for_work_order(
        self,
        work_order_id: UUID
    ) -> List[QualityCheck]:
        """Liste les contrôles qualité d'un OF."""
        return self.quality_check_repo.list_for_work_order(work_order_id)

    # ================== Production Log ==================

    def _log_production(
        self,
        work_order_id: UUID,
        operation_id: Optional[UUID],
        event_type: str,
        quantity: Decimal,
        details: Dict[str, Any] = None
    ) -> ProductionLog:
        """Enregistre un événement de production (interne)."""
        return self.production_log_repo.create({
            "work_order_id": work_order_id,
            "operation_id": operation_id,
            "event_type": event_type,
            "quantity": quantity,
            "operator_id": self.user_id,
            "details": details or {}
        })

    def list_production_logs(self, work_order_id: UUID) -> List[ProductionLog]:
        """Liste les logs de production d'un OF."""
        return self.production_log_repo.list_for_work_order(work_order_id)

    # ================== Stats ==================

    def get_bom_stats(self) -> Dict[str, Any]:
        """Statistiques BOMs."""
        return self.bom_repo.get_stats()

    def get_work_order_stats(self) -> Dict[str, Any]:
        """Statistiques Work Orders."""
        return self.work_order_repo.get_stats()

    def get_production_stats(
        self,
        period_start: date,
        period_end: date
    ) -> ProductionStats:
        """Statistiques de production sur une période."""
        # Récupérer les OF de la période
        filters = WorkOrderFilters(
            planned_start_from=datetime.combine(period_start, datetime.min.time()),
            planned_start_to=datetime.combine(period_end, datetime.max.time())
        )
        wos, _, _ = self.list_work_orders(filters, page_size=10000)

        completed = [wo for wo in wos if wo.status == WorkOrderStatus.COMPLETED]

        total_produced = sum(wo.quantity_produced for wo in wos)
        total_scrapped = sum(wo.quantity_scrapped for wo in wos)
        scrap_rate = (total_scrapped / total_produced * 100) if total_produced > 0 else Decimal("0")

        on_time = 0
        late = 0
        for wo in completed:
            if wo.planned_end and wo.actual_end:
                if wo.actual_end <= wo.planned_end:
                    on_time += 1
                else:
                    late += 1

        # Temps
        total_setup = sum(
            op.actual_setup_time for wo in wos for op in wo.operations
        )
        total_run = sum(
            op.actual_run_time for wo in wos for op in wo.operations
        )

        # Coûts
        total_material = sum(wo.actual_material_cost for wo in completed)
        total_labor = sum(wo.actual_labor_cost for wo in completed)
        planned_cost = sum(wo.planned_total_cost for wo in completed)
        actual_cost = sum(wo.actual_total_cost for wo in completed)
        variance = (
            (actual_cost - planned_cost) / planned_cost * 100
            if planned_cost > 0 else Decimal("0")
        )

        return ProductionStats(
            total_work_orders=len(wos),
            completed_orders=len(completed),
            on_time_orders=on_time,
            late_orders=late,
            total_produced=total_produced,
            total_scrapped=total_scrapped,
            scrap_rate=scrap_rate,
            total_setup_time=total_setup,
            total_run_time=total_run,
            total_material_cost=total_material,
            total_labor_cost=total_labor,
            actual_vs_planned_cost=variance
        )


def create_manufacturing_service(
    db: Session,
    tenant_id: UUID,
    user_id: UUID = None
) -> ManufacturingService:
    """Factory pour créer une instance du service."""
    return ManufacturingService(db, tenant_id, user_id)
