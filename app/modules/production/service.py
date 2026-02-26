"""
AZALS MODULE M6 - Service Production
=====================================

Logique métier pour la gestion de production.
"""
from __future__ import annotations


import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.query_optimizer import QueryOptimizer

from .models import (
    BillOfMaterials,
    BOMLine,
    BOMStatus,
    MaintenanceSchedule,
    ManufacturingOrder,
    MaterialConsumption,
    MOPriority,
    MOStatus,
    ProductionOutput,
    ProductionPlan,
    ProductionPlanLine,
    ProductionScrap,
    Routing,
    RoutingOperation,
    WorkCenter,
    WorkCenterStatus,
    WorkOrder,
    WorkOrderStatus,
)
from .schemas import (
    BOMCreate,
    BOMLineCreate,
    BOMUpdate,
    CompleteWorkOrderRequest,
    ConsumeRequest,
    MaintenanceScheduleCreate,
    MOCreate,
    MOUpdate,
    PlanCreate,
    ProduceRequest,
    ProductionDashboard,
    ReturnRequest,
    RoutingCreate,
    ScrapCreate,
    StartWorkOrderRequest,
    WorkCenterCreate,
    WorkCenterUpdate,
)

logger = logging.getLogger(__name__)


class ProductionService:
    """Service de gestion de production."""

    def __init__(self, db: Session, tenant_id: str, user_id: UUID | None = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self._optimizer = QueryOptimizer(db)

    # ========================================================================
    # CENTRES DE TRAVAIL
    # ========================================================================

    def create_work_center(self, data: WorkCenterCreate) -> WorkCenter:
        """Créer un centre de travail."""
        wc = WorkCenter(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            type=data.type,
            warehouse_id=data.warehouse_id,
            location=data.location,
            capacity=data.capacity,
            efficiency=data.efficiency,
            oee_target=data.oee_target,
            time_start=data.time_start,
            time_stop=data.time_stop,
            time_before=data.time_before,
            time_after=data.time_after,
            cost_per_hour=data.cost_per_hour,
            cost_per_cycle=data.cost_per_cycle,
            currency=data.currency,
            working_hours_per_day=data.working_hours_per_day,
            working_days_per_week=data.working_days_per_week,
            manager_id=data.manager_id,
            operator_ids=data.operator_ids,
            requires_approval=data.requires_approval,
            allow_parallel=data.allow_parallel,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(wc)
        self.db.commit()
        self.db.refresh(wc)
        return wc

    def get_work_center(self, wc_id: UUID) -> WorkCenter | None:
        """Récupérer un centre de travail."""
        return self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.id == wc_id
        ).first()

    def list_work_centers(
        self,
        status: WorkCenterStatus | None = None,
        type_filter: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[WorkCenter], int]:
        """Lister les centres de travail."""
        query = self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.is_active
        )

        if status:
            query = query.filter(WorkCenter.status == status)
        if type_filter:
            query = query.filter(WorkCenter.type == type_filter)

        total = query.count()
        items = query.order_by(WorkCenter.name).offset(skip).limit(limit).all()
        return items, total

    def update_work_center(self, wc_id: UUID, data: WorkCenterUpdate) -> WorkCenter | None:
        """Mettre à jour un centre de travail."""
        wc = self.get_work_center(wc_id)
        if not wc:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(wc, field, value)

        self.db.commit()
        self.db.refresh(wc)
        return wc

    def set_work_center_status(self, wc_id: UUID, status: WorkCenterStatus) -> WorkCenter | None:
        """Changer le statut d'un centre de travail."""
        wc = self.get_work_center(wc_id)
        if not wc:
            return None

        wc.status = status
        self.db.commit()
        self.db.refresh(wc)
        return wc

    # ========================================================================
    # NOMENCLATURES (BOM)
    # ========================================================================

    def create_bom(self, data: BOMCreate) -> BillOfMaterials:
        """Créer une nomenclature."""
        logger.info(
            "Creating BOM | tenant=%s user=%s product_id=%s code=%s",
            self.tenant_id, self.user_id, data.product_id, data.code
        )
        bom = BillOfMaterials(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            version=data.version,
            product_id=data.product_id,
            quantity=data.quantity,
            unit=data.unit,
            type=data.type,
            routing_id=data.routing_id,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            is_default=data.is_default,
            allow_alternatives=data.allow_alternatives,
            consumption_type=data.consumption_type,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(bom)
        self.db.flush()

        # Ajouter les lignes
        for i, line_data in enumerate(data.lines, 1):
            line = BOMLine(
                tenant_id=self.tenant_id,
                bom_id=bom.id,
                line_number=i,
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit=line_data.unit,
                operation_id=line_data.operation_id,
                scrap_rate=line_data.scrap_rate,
                is_critical=line_data.is_critical,
                alternative_group=line_data.alternative_group,
                consumption_type=line_data.consumption_type,
                notes=line_data.notes
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(bom)
        logger.info("BOM created | bom_id=%s bom_code=%s", bom.id, bom.code)
        return bom

    def get_bom(self, bom_id: UUID) -> BillOfMaterials | None:
        """Récupérer une nomenclature."""
        return self.db.query(BillOfMaterials).filter(
            BillOfMaterials.tenant_id == self.tenant_id,
            BillOfMaterials.id == bom_id
        ).first()

    def get_bom_for_product(self, product_id: UUID) -> BillOfMaterials | None:
        """Récupérer la nomenclature par défaut d'un produit."""
        return self.db.query(BillOfMaterials).filter(
            BillOfMaterials.tenant_id == self.tenant_id,
            BillOfMaterials.product_id == product_id,
            BillOfMaterials.status == BOMStatus.ACTIVE,
            BillOfMaterials.is_default
        ).first()

    def list_boms(
        self,
        product_id: UUID | None = None,
        status: BOMStatus | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[BillOfMaterials], int]:
        """Lister les nomenclatures."""
        query = self.db.query(BillOfMaterials).filter(
            BillOfMaterials.tenant_id == self.tenant_id,
            BillOfMaterials.is_active
        )

        if product_id:
            query = query.filter(BillOfMaterials.product_id == product_id)
        if status:
            query = query.filter(BillOfMaterials.status == status)

        total = query.count()
        items = query.order_by(BillOfMaterials.code).offset(skip).limit(limit).all()
        return items, total

    def update_bom(self, bom_id: UUID, data: BOMUpdate) -> BillOfMaterials | None:
        """Mettre à jour une nomenclature."""
        bom = self.get_bom(bom_id)
        if not bom:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(bom, field, value)

        self.db.commit()
        self.db.refresh(bom)
        return bom

    def activate_bom(self, bom_id: UUID) -> BillOfMaterials | None:
        """Activer une nomenclature."""
        bom = self.get_bom(bom_id)
        if not bom:
            return None

        bom.status = BOMStatus.ACTIVE
        self.db.commit()
        self.db.refresh(bom)
        return bom

    def add_bom_line(self, bom_id: UUID, data: BOMLineCreate) -> BOMLine | None:
        """Ajouter une ligne à une nomenclature."""
        bom = self.get_bom(bom_id)
        if not bom:
            return None

        max_line = self.db.query(func.max(BOMLine.line_number)).filter(
            BOMLine.bom_id == bom_id
        ).scalar() or 0

        line = BOMLine(
            tenant_id=self.tenant_id,
            bom_id=bom_id,
            line_number=max_line + 1,
            product_id=data.product_id,
            quantity=data.quantity,
            unit=data.unit,
            operation_id=data.operation_id,
            scrap_rate=data.scrap_rate,
            is_critical=data.is_critical,
            alternative_group=data.alternative_group,
            consumption_type=data.consumption_type,
            notes=data.notes
        )
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    # ========================================================================
    # GAMMES DE FABRICATION
    # ========================================================================

    def create_routing(self, data: RoutingCreate) -> Routing:
        """Créer une gamme de fabrication."""
        logger.info(
            "Creating routing | tenant=%s user=%s product_id=%s code=%s",
            self.tenant_id, self.user_id, data.product_id, data.code
        )
        routing = Routing(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            version=data.version,
            product_id=data.product_id,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(routing)
        self.db.flush()

        total_setup = Decimal("0")
        total_operation = Decimal("0")
        total_labor = Decimal("0")
        total_machine = Decimal("0")

        # Ajouter les opérations
        for op_data in data.operations:
            op = RoutingOperation(
                tenant_id=self.tenant_id,
                routing_id=routing.id,
                sequence=op_data.sequence,
                code=op_data.code,
                name=op_data.name,
                description=op_data.description,
                type=op_data.type,
                work_center_id=op_data.work_center_id,
                setup_time=op_data.setup_time,
                operation_time=op_data.operation_time,
                cleanup_time=op_data.cleanup_time,
                wait_time=op_data.wait_time,
                batch_size=op_data.batch_size,
                labor_cost_per_hour=op_data.labor_cost_per_hour,
                machine_cost_per_hour=op_data.machine_cost_per_hour,
                is_subcontracted=op_data.is_subcontracted,
                subcontractor_id=op_data.subcontractor_id,
                requires_quality_check=op_data.requires_quality_check,
                skill_required=op_data.skill_required,
                notes=op_data.notes
            )
            self.db.add(op)

            total_setup += op_data.setup_time
            total_operation += op_data.operation_time
            # Calculer les coûts (simplifié)
            hours = (op_data.setup_time + op_data.operation_time) / Decimal("60")
            total_labor += hours * op_data.labor_cost_per_hour
            total_machine += hours * op_data.machine_cost_per_hour

        routing.total_setup_time = total_setup
        routing.total_operation_time = total_operation
        routing.total_time = total_setup + total_operation
        routing.total_labor_cost = total_labor
        routing.total_machine_cost = total_machine

        self.db.commit()
        self.db.refresh(routing)
        logger.info("Routing created | routing_id=%s routing_code=%s", routing.id, routing.code)
        return routing

    def get_routing(self, routing_id: UUID) -> Routing | None:
        """Récupérer une gamme."""
        return self.db.query(Routing).filter(
            Routing.tenant_id == self.tenant_id,
            Routing.id == routing_id
        ).first()

    def list_routings(
        self,
        product_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Routing], int]:
        """Lister les gammes."""
        query = self.db.query(Routing).filter(
            Routing.tenant_id == self.tenant_id,
            Routing.is_active
        )

        if product_id:
            query = query.filter(Routing.product_id == product_id)

        total = query.count()
        items = query.order_by(Routing.code).offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # ORDRES DE FABRICATION
    # ========================================================================

    def _generate_mo_number(self) -> str:
        """Générer un numéro d'OF."""
        today = datetime.utcnow()
        prefix = f"MO{today.strftime('%Y%m')}"

        last_mo = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.number.like(f"{prefix}%")
        ).order_by(ManufacturingOrder.number.desc()).first()

        if last_mo:
            try:
                last_num = int(last_mo.number[-4:])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def create_manufacturing_order(self, data: MOCreate) -> ManufacturingOrder:
        """Créer un ordre de fabrication."""
        logger.info(
            "Creating manufacturing order | tenant=%s user=%s product_id=%s quantity=%s",
            self.tenant_id, self.user_id, data.product_id, data.quantity_planned
        )
        mo = ManufacturingOrder(
            tenant_id=self.tenant_id,
            number=self._generate_mo_number(),
            name=data.name,
            product_id=data.product_id,
            bom_id=data.bom_id,
            routing_id=data.routing_id,
            quantity_planned=data.quantity_planned,
            unit=data.unit,
            priority=data.priority,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            deadline=data.deadline,
            warehouse_id=data.warehouse_id,
            location_id=data.location_id,
            origin_type=data.origin_type,
            origin_id=data.origin_id,
            origin_number=data.origin_number,
            responsible_id=data.responsible_id,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(mo)
        self.db.commit()
        self.db.refresh(mo)
        logger.info("Manufacturing order created | order_id=%s order_number=%s", mo.id, mo.number)
        return mo

    def get_manufacturing_order(self, mo_id: UUID) -> ManufacturingOrder | None:
        """Récupérer un ordre de fabrication."""
        return self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.id == mo_id
        ).first()

    def list_manufacturing_orders(
        self,
        status: MOStatus | None = None,
        priority: MOPriority | None = None,
        product_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ManufacturingOrder], int]:
        """Lister les ordres de fabrication."""
        query = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(ManufacturingOrder.status == status)
        if priority:
            query = query.filter(ManufacturingOrder.priority == priority)
        if product_id:
            query = query.filter(ManufacturingOrder.product_id == product_id)
        if date_from:
            query = query.filter(ManufacturingOrder.scheduled_start >= date_from)
        if date_to:
            query = query.filter(ManufacturingOrder.scheduled_end <= date_to)

        total = query.count()
        items = query.order_by(ManufacturingOrder.scheduled_start.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_manufacturing_order(self, mo_id: UUID, data: MOUpdate) -> ManufacturingOrder | None:
        """Mettre à jour un OF."""
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status not in [MOStatus.DRAFT, MOStatus.CONFIRMED]:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(mo, field, value)

        self.db.commit()
        self.db.refresh(mo)
        return mo

    def confirm_manufacturing_order(self, mo_id: UUID) -> ManufacturingOrder | None:
        """Confirmer un OF et créer les ordres de travail."""
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status != MOStatus.DRAFT:
            return None

        # Créer les ordres de travail à partir de la gamme
        if mo.routing_id:
            routing = self.get_routing(mo.routing_id)
            if routing:
                for op in routing.operations:
                    wo = WorkOrder(
                        tenant_id=self.tenant_id,
                        mo_id=mo.id,
                        sequence=op.sequence,
                        name=op.name,
                        description=op.description,
                        operation_id=op.id,
                        work_center_id=op.work_center_id,
                        quantity_planned=mo.quantity_planned,
                        setup_time_planned=op.setup_time,
                        operation_time_planned=op.operation_time * mo.quantity_planned
                    )
                    self.db.add(wo)

        # Créer les consommations prévues à partir de la BOM
        if mo.bom_id:
            bom = self.get_bom(mo.bom_id)
            if bom:
                factor = mo.quantity_planned / bom.quantity
                for line in bom.lines:
                    consumption = MaterialConsumption(
                        tenant_id=self.tenant_id,
                        mo_id=mo.id,
                        product_id=line.product_id,
                        bom_line_id=line.id,
                        quantity_planned=line.quantity * factor * (1 + line.scrap_rate / 100),
                        unit=line.unit
                    )
                    self.db.add(consumption)

        mo.status = MOStatus.CONFIRMED
        mo.confirmed_at = datetime.utcnow()
        mo.confirmed_by = self.user_id

        self.db.commit()
        self.db.refresh(mo)
        return mo

    def start_manufacturing_order(self, mo_id: UUID) -> ManufacturingOrder | None:
        """Démarrer un OF."""
        logger.info(
            "Starting manufacturing order | tenant=%s user=%s order_id=%s",
            self.tenant_id, self.user_id, mo_id
        )
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status not in [MOStatus.CONFIRMED, MOStatus.PLANNED]:
            return None

        mo.status = MOStatus.IN_PROGRESS
        mo.actual_start = datetime.utcnow()

        self.db.commit()
        self.db.refresh(mo)
        logger.info("Manufacturing order started | order_id=%s order_number=%s", mo.id, mo.number)
        return mo

    def complete_manufacturing_order(self, mo_id: UUID) -> ManufacturingOrder | None:
        """Terminer un OF."""
        logger.info(
            "Completing manufacturing order | tenant=%s user=%s order_id=%s",
            self.tenant_id, self.user_id, mo_id
        )
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status != MOStatus.IN_PROGRESS:
            return None

        mo.status = MOStatus.DONE
        mo.actual_end = datetime.utcnow()
        mo.progress_percent = Decimal("100")

        self.db.commit()
        self.db.refresh(mo)
        logger.info(
            "Manufacturing order completed | order_id=%s order_number=%s quantity_produced=%s",
            mo.id, mo.number, mo.quantity_produced
        )
        return mo

    def cancel_manufacturing_order(self, mo_id: UUID) -> ManufacturingOrder | None:
        """Annuler un OF."""
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status in [MOStatus.DONE, MOStatus.CANCELLED]:
            return None

        mo.status = MOStatus.CANCELLED

        # Annuler les ordres de travail
        for wo in mo.work_orders:
            if wo.status not in [WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED]:
                wo.status = WorkOrderStatus.CANCELLED

        self.db.commit()
        self.db.refresh(mo)
        return mo

    # ========================================================================
    # ORDRES DE TRAVAIL
    # ========================================================================

    def get_work_order(self, wo_id: UUID) -> WorkOrder | None:
        """Récupérer un ordre de travail."""
        return self.db.query(WorkOrder).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.id == wo_id
        ).first()

    def list_work_orders_for_work_center(
        self,
        work_center_id: UUID,
        status: WorkOrderStatus | None = None
    ) -> list[WorkOrder]:
        """Lister les ordres de travail pour un centre."""
        query = self.db.query(WorkOrder).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.work_center_id == work_center_id
        )

        if status:
            query = query.filter(WorkOrder.status == status)

        return query.order_by(WorkOrder.scheduled_start).all()

    def start_work_order(self, wo_id: UUID, data: StartWorkOrderRequest) -> WorkOrder | None:
        """Démarrer un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status not in [WorkOrderStatus.PENDING, WorkOrderStatus.READY]:
            return None

        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.actual_start = datetime.utcnow()
        if data.operator_id:
            wo.operator_id = data.operator_id

        # Démarrer l'OF parent si nécessaire
        mo = wo.manufacturing_order
        if mo.status == MOStatus.CONFIRMED:
            mo.status = MOStatus.IN_PROGRESS
            mo.actual_start = datetime.utcnow()

        # Mettre le centre de travail en occupation
        if wo.work_center_id:
            wc = self.get_work_center(wo.work_center_id)
            if wc:
                wc.status = WorkCenterStatus.BUSY

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def complete_work_order(self, wo_id: UUID, data: CompleteWorkOrderRequest) -> WorkOrder | None:
        """Terminer un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status != WorkOrderStatus.IN_PROGRESS:
            return None

        wo.status = WorkOrderStatus.DONE
        wo.actual_end = datetime.utcnow()
        wo.quantity_done = data.quantity_done
        wo.quantity_scrapped = data.quantity_scrapped

        # Calculer le temps réel
        if wo.actual_start:
            duration = (wo.actual_end - wo.actual_start).total_seconds() / 60
            wo.operation_time_actual = Decimal(str(duration))

        # Libérer le centre de travail
        if wo.work_center_id:
            wc = self.get_work_center(wo.work_center_id)
            if wc:
                wc.status = WorkCenterStatus.AVAILABLE

        # Mettre à jour l'OF parent
        mo = wo.manufacturing_order
        mo.quantity_produced += data.quantity_done
        mo.quantity_scrapped += data.quantity_scrapped

        # Calculer la progression
        total_wo = len(mo.work_orders)
        done_wo = sum(1 for w in mo.work_orders if w.status == WorkOrderStatus.DONE)
        mo.progress_percent = Decimal(str((done_wo / total_wo) * 100)) if total_wo > 0 else Decimal("0")

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def pause_work_order(self, wo_id: UUID) -> WorkOrder | None:
        """Mettre en pause un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status != WorkOrderStatus.IN_PROGRESS:
            return None

        wo.status = WorkOrderStatus.PAUSED

        # Libérer le centre de travail
        if wo.work_center_id:
            wc = self.get_work_center(wo.work_center_id)
            if wc:
                wc.status = WorkCenterStatus.AVAILABLE

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def resume_work_order(self, wo_id: UUID) -> WorkOrder | None:
        """Reprendre un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status != WorkOrderStatus.PAUSED:
            return None

        wo.status = WorkOrderStatus.IN_PROGRESS

        # Occuper le centre de travail
        if wo.work_center_id:
            wc = self.get_work_center(wo.work_center_id)
            if wc:
                wc.status = WorkCenterStatus.BUSY

        self.db.commit()
        self.db.refresh(wo)
        return wo

    # ========================================================================
    # CONSOMMATION DE MATIÈRES
    # ========================================================================

    def consume_material(self, mo_id: UUID, data: ConsumeRequest) -> MaterialConsumption | None:
        """Consommer des matières."""
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status not in [MOStatus.IN_PROGRESS, MOStatus.CONFIRMED]:
            return None

        # SÉCURITÉ: Chercher une consommation planifiée existante (filtrer par tenant_id)
        consumption = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.tenant_id == self.tenant_id,
            MaterialConsumption.mo_id == mo_id,
            MaterialConsumption.product_id == data.product_id,
            MaterialConsumption.quantity_consumed == 0
        ).first()

        if consumption:
            consumption.quantity_consumed = data.quantity
            consumption.lot_id = data.lot_id
            consumption.serial_id = data.serial_id
            consumption.warehouse_id = data.warehouse_id
            consumption.location_id = data.location_id
            consumption.work_order_id = data.work_order_id
            consumption.consumed_at = datetime.utcnow()
            consumption.consumed_by = self.user_id
        else:
            consumption = MaterialConsumption(
                tenant_id=self.tenant_id,
                mo_id=mo_id,
                product_id=data.product_id,
                work_order_id=data.work_order_id,
                quantity_planned=data.quantity,
                quantity_consumed=data.quantity,
                lot_id=data.lot_id,
                serial_id=data.serial_id,
                warehouse_id=data.warehouse_id,
                location_id=data.location_id,
                consumed_at=datetime.utcnow(),
                consumed_by=self.user_id,
                notes=data.notes
            )
            self.db.add(consumption)

        # NOTE: Phase 2 - Calcul coût via InventoryService.get_unit_cost()

        self.db.commit()
        self.db.refresh(consumption)
        return consumption

    def return_material(self, data: ReturnRequest) -> MaterialConsumption | None:
        """Retourner des matières non utilisées."""
        consumption = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.tenant_id == self.tenant_id,
            MaterialConsumption.id == data.consumption_id
        ).first()

        if not consumption:
            return None

        consumption.quantity_returned += data.quantity
        if data.notes:
            consumption.notes = (consumption.notes or "") + f"\nRetour: {data.notes}"

        self.db.commit()
        self.db.refresh(consumption)
        return consumption

    # ========================================================================
    # PRODUCTION (OUTPUT)
    # ========================================================================

    def produce(self, mo_id: UUID, data: ProduceRequest) -> ProductionOutput | None:
        """Déclarer une production."""
        mo = self.get_manufacturing_order(mo_id)
        if not mo or mo.status not in [MOStatus.IN_PROGRESS]:
            return None

        output = ProductionOutput(
            tenant_id=self.tenant_id,
            mo_id=mo_id,
            work_order_id=data.work_order_id,
            product_id=mo.product_id,
            quantity=data.quantity,
            unit=mo.unit,
            lot_id=data.lot_id,
            serial_ids=data.serial_ids,
            warehouse_id=data.warehouse_id or mo.warehouse_id,
            location_id=data.location_id or mo.location_id,
            is_quality_passed=data.is_quality_passed,
            quality_notes=data.quality_notes,
            produced_by=self.user_id,
            notes=data.notes
        )
        self.db.add(output)

        # Mettre à jour l'OF
        mo.quantity_produced += data.quantity

        self.db.commit()
        self.db.refresh(output)
        return output

    # ========================================================================
    # REBUTS
    # ========================================================================

    def create_scrap(self, data: ScrapCreate) -> ProductionScrap:
        """Déclarer un rebut."""
        scrap = ProductionScrap(
            tenant_id=self.tenant_id,
            mo_id=data.mo_id,
            work_order_id=data.work_order_id,
            product_id=data.product_id,
            quantity=data.quantity,
            unit=data.unit,
            lot_id=data.lot_id,
            serial_id=data.serial_id,
            reason=data.reason,
            reason_detail=data.reason_detail,
            work_center_id=data.work_center_id,
            scrapped_by=self.user_id,
            notes=data.notes
        )
        self.db.add(scrap)

        # Mettre à jour l'OF si lié
        if data.mo_id:
            mo = self.get_manufacturing_order(data.mo_id)
            if mo:
                mo.quantity_scrapped += data.quantity

        self.db.commit()
        self.db.refresh(scrap)
        return scrap

    def list_scraps(
        self,
        mo_id: UUID | None = None,
        product_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ProductionScrap], int]:
        """Lister les rebuts."""
        query = self.db.query(ProductionScrap).filter(
            ProductionScrap.tenant_id == self.tenant_id
        )

        if mo_id:
            query = query.filter(ProductionScrap.mo_id == mo_id)
        if product_id:
            query = query.filter(ProductionScrap.product_id == product_id)
        if date_from:
            query = query.filter(func.date(ProductionScrap.scrapped_at) >= date_from)
        if date_to:
            query = query.filter(func.date(ProductionScrap.scrapped_at) <= date_to)

        total = query.count()
        items = query.order_by(ProductionScrap.scrapped_at.desc()).offset(skip).limit(limit).all()
        return items, total

    # ========================================================================
    # PLANIFICATION
    # ========================================================================

    def create_production_plan(self, data: PlanCreate) -> ProductionPlan:
        """Créer un plan de production."""
        plan = ProductionPlan(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            planning_horizon_days=data.planning_horizon_days,
            planning_method=data.planning_method,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(plan)
        self.db.flush()

        # Ajouter les lignes
        for line_data in data.lines:
            line = ProductionPlanLine(
                tenant_id=self.tenant_id,
                plan_id=plan.id,
                product_id=line_data.product_id,
                bom_id=line_data.bom_id,
                quantity_demanded=line_data.quantity_demanded,
                required_date=line_data.required_date,
                priority=line_data.priority,
                notes=line_data.notes
            )
            self.db.add(line)
            plan.total_quantity += line_data.quantity_demanded

        plan.total_orders = len(data.lines)
        plan.generated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_production_plan(self, plan_id: UUID) -> ProductionPlan | None:
        """Récupérer un plan de production."""
        return self.db.query(ProductionPlan).filter(
            ProductionPlan.tenant_id == self.tenant_id,
            ProductionPlan.id == plan_id
        ).first()

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    def create_maintenance_schedule(self, data: MaintenanceScheduleCreate) -> MaintenanceSchedule:
        """Créer un calendrier de maintenance."""
        schedule = MaintenanceSchedule(
            tenant_id=self.tenant_id,
            work_center_id=data.work_center_id,
            name=data.name,
            description=data.description,
            frequency_type=data.frequency_type,
            frequency_value=data.frequency_value,
            duration_hours=data.duration_hours,
            notes=data.notes
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def list_maintenance_schedules(
        self,
        work_center_id: UUID | None = None
    ) -> list[MaintenanceSchedule]:
        """Lister les calendriers de maintenance."""
        query = self.db.query(MaintenanceSchedule).filter(
            MaintenanceSchedule.tenant_id == self.tenant_id,
            MaintenanceSchedule.is_active
        )

        if work_center_id:
            query = query.filter(MaintenanceSchedule.work_center_id == work_center_id)

        return query.all()

    def get_due_maintenance(self) -> list[MaintenanceSchedule]:
        """Récupérer les maintenances dues."""
        now = datetime.utcnow()
        return self.db.query(MaintenanceSchedule).filter(
            MaintenanceSchedule.tenant_id == self.tenant_id,
            MaintenanceSchedule.is_active,
            or_(
                MaintenanceSchedule.next_maintenance <= now,
                MaintenanceSchedule.next_maintenance is None
            )
        ).all()

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> ProductionDashboard:
        """Récupérer les données du dashboard."""
        today = date.today()
        today - timedelta(days=today.weekday())
        today.replace(day=1)

        # Ordres de fabrication
        total_orders = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id
        ).count()

        orders_draft = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.status == MOStatus.DRAFT
        ).count()

        orders_confirmed = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.status == MOStatus.CONFIRMED
        ).count()

        orders_in_progress = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.status == MOStatus.IN_PROGRESS
        ).count()

        orders_done_today = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.status == MOStatus.DONE,
            func.date(ManufacturingOrder.actual_end) == today
        ).count()

        orders_late = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.tenant_id == self.tenant_id,
            ManufacturingOrder.status.in_([MOStatus.CONFIRMED, MOStatus.IN_PROGRESS]),
            ManufacturingOrder.deadline < datetime.utcnow()
        ).count()

        # Production
        quantity_produced_today = self.db.query(func.coalesce(func.sum(ProductionOutput.quantity), 0)).filter(
            ProductionOutput.tenant_id == self.tenant_id,
            func.date(ProductionOutput.produced_at) == today
        ).scalar() or Decimal("0")

        quantity_scrapped_today = self.db.query(func.coalesce(func.sum(ProductionScrap.quantity), 0)).filter(
            ProductionScrap.tenant_id == self.tenant_id,
            func.date(ProductionScrap.scrapped_at) == today
        ).scalar() or Decimal("0")

        # Centres de travail
        total_wc = self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.is_active
        ).count()

        wc_available = self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.is_active,
            WorkCenter.status == WorkCenterStatus.AVAILABLE
        ).count()

        wc_busy = self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.is_active,
            WorkCenter.status == WorkCenterStatus.BUSY
        ).count()

        wc_maintenance = self.db.query(WorkCenter).filter(
            WorkCenter.tenant_id == self.tenant_id,
            WorkCenter.is_active,
            WorkCenter.status == WorkCenterStatus.MAINTENANCE
        ).count()

        # Maintenance due
        maintenance_due = len(self.get_due_maintenance())

        return ProductionDashboard(
            total_orders=total_orders,
            orders_draft=orders_draft,
            orders_confirmed=orders_confirmed,
            orders_in_progress=orders_in_progress,
            orders_done_today=orders_done_today,
            orders_late=orders_late,
            quantity_produced_today=quantity_produced_today,
            quantity_scrapped_today=quantity_scrapped_today,
            total_work_centers=total_wc,
            work_centers_available=wc_available,
            work_centers_busy=wc_busy,
            work_centers_maintenance=wc_maintenance,
            maintenance_due=maintenance_due
        )


def get_production_service(db: Session, tenant_id: str, user_id: UUID | None = None) -> ProductionService:
    """Factory function pour le service Production."""
    return ProductionService(db, tenant_id, user_id)
