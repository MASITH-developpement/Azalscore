"""
AZALS MODULE M8 - Service Maintenance (GMAO)
=============================================

Service métier pour la gestion de la maintenance.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple

from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session, joinedload

from .models import (
    Asset, AssetMeter, MeterReading,
    MaintenancePlan, MaintenancePlanTask, MaintenanceWorkOrder as WorkOrder, WorkOrderTask,
    WorkOrderLabor, WorkOrderPart, Failure, SparePart,
    PartRequest, MaintenanceContract, AssetCategory, AssetStatus, AssetCriticality, WorkOrderStatus, WorkOrderPriority, PartRequestStatus,
    ContractStatus
)
from .schemas import (
    AssetCreate, AssetUpdate, MeterCreate, MeterReadingCreate,
    MaintenancePlanCreate, MaintenancePlanUpdate, WorkOrderCreate, WorkOrderUpdate, WorkOrderComplete, WorkOrderLaborCreate, WorkOrderPartCreate,
    FailureCreate, FailureUpdate,
    SparePartCreate, SparePartUpdate, PartRequestCreate,
    ContractCreate, ContractUpdate,
    MaintenanceDashboard
)


class MaintenanceService:
    """Service de gestion de la maintenance GMAO."""

    def __init__(self, db: Session, tenant_id: int, user_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ========================================================================
    # ACTIFS
    # ========================================================================

    def create_asset(self, data: AssetCreate) -> Asset:
        """Créer un nouvel actif."""
        asset = Asset(
            tenant_id=self.tenant_id,
            asset_code=data.asset_code,
            name=data.name,
            description=data.description,
            category=data.category,
            asset_type=data.asset_type,
            status=AssetStatus.ACTIVE,
            criticality=data.criticality,
            parent_id=data.parent_id,
            location_id=data.location_id,
            location_description=data.location_description,
            building=data.building,
            floor=data.floor,
            area=data.area,
            manufacturer=data.manufacturer,
            model=data.model,
            serial_number=data.serial_number,
            year_manufactured=data.year_manufactured,
            purchase_date=data.purchase_date,
            installation_date=data.installation_date,
            warranty_end_date=data.warranty_end_date,
            purchase_cost=data.purchase_cost,
            replacement_cost=data.replacement_cost,
            specifications=data.specifications,
            power_rating=data.power_rating,
            supplier_id=data.supplier_id,
            responsible_id=data.responsible_id,
            department=data.department,
            maintenance_strategy=data.maintenance_strategy,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_asset(self, asset_id: int) -> Optional[Asset]:
        """Récupérer un actif par ID."""
        return self.db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.tenant_id == self.tenant_id
        ).first()

    def list_assets(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[AssetCategory] = None,
        status: Optional[AssetStatus] = None,
        criticality: Optional[AssetCriticality] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Asset], int]:
        """Lister les actifs avec filtres."""
        query = self.db.query(Asset).filter(Asset.tenant_id == self.tenant_id)

        if category:
            query = query.filter(Asset.category == category)
        if status:
            query = query.filter(Asset.status == status)
        if criticality:
            query = query.filter(Asset.criticality == criticality)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Asset.asset_code.ilike(search_term),
                    Asset.name.ilike(search_term),
                    Asset.serial_number.ilike(search_term)
                )
            )

        total = query.count()
        assets = query.order_by(Asset.asset_code).offset(skip).limit(limit).all()
        return assets, total

    def update_asset(self, asset_id: int, data: AssetUpdate) -> Optional[Asset]:
        """Mettre à jour un actif."""
        asset = self.get_asset(asset_id)
        if not asset:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)

        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete_asset(self, asset_id: int) -> bool:
        """Supprimer un actif (soft delete)."""
        asset = self.get_asset(asset_id)
        if not asset:
            return False

        asset.status = AssetStatus.DISPOSED
        self.db.commit()
        return True

    # ========================================================================
    # COMPTEURS
    # ========================================================================

    def create_meter(self, asset_id: int, data: MeterCreate) -> Optional[AssetMeter]:
        """Créer un compteur pour un actif."""
        asset = self.get_asset(asset_id)
        if not asset:
            return None

        meter = AssetMeter(
            tenant_id=self.tenant_id,
            asset_id=asset_id,
            meter_code=data.meter_code,
            name=data.name,
            description=data.description,
            meter_type=data.meter_type,
            unit=data.unit,
            initial_reading=data.initial_reading,
            current_reading=data.initial_reading,
            alert_threshold=data.alert_threshold,
            critical_threshold=data.critical_threshold,
            maintenance_trigger_value=data.maintenance_trigger_value,
            created_by=self.user_id
        )
        self.db.add(meter)
        self.db.commit()
        self.db.refresh(meter)
        return meter

    def record_meter_reading(
        self,
        meter_id: int,
        data: MeterReadingCreate
    ) -> Optional[MeterReading]:
        """Enregistrer un relevé de compteur."""
        meter = self.db.query(AssetMeter).filter(
            AssetMeter.id == meter_id,
            AssetMeter.tenant_id == self.tenant_id
        ).first()

        if not meter:
            return None

        # Calculer le delta
        delta = data.reading_value - meter.current_reading

        reading = MeterReading(
            tenant_id=self.tenant_id,
            meter_id=meter_id,
            reading_date=datetime.now(),
            reading_value=data.reading_value,
            delta=delta,
            source=data.source,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(reading)

        # Mettre à jour le compteur
        meter.current_reading = data.reading_value
        meter.last_reading_date = datetime.now()

        self.db.commit()
        self.db.refresh(reading)
        return reading

    # ========================================================================
    # PLANS DE MAINTENANCE
    # ========================================================================

    def create_maintenance_plan(self, data: MaintenancePlanCreate) -> MaintenancePlan:
        """Créer un plan de maintenance."""
        plan = MaintenancePlan(
            tenant_id=self.tenant_id,
            plan_code=data.plan_code,
            name=data.name,
            description=data.description,
            maintenance_type=data.maintenance_type,
            asset_id=data.asset_id,
            asset_category=data.asset_category,
            trigger_type=data.trigger_type,
            frequency_value=data.frequency_value,
            frequency_unit=data.frequency_unit,
            trigger_meter_id=data.trigger_meter_id,
            trigger_meter_interval=data.trigger_meter_interval,
            lead_time_days=data.lead_time_days,
            estimated_duration_hours=data.estimated_duration_hours,
            responsible_id=data.responsible_id,
            estimated_labor_cost=data.estimated_labor_cost,
            estimated_parts_cost=data.estimated_parts_cost,
            instructions=data.instructions,
            safety_instructions=data.safety_instructions,
            required_tools=data.required_tools,
            is_active=True,
            created_by=self.user_id
        )
        self.db.add(plan)
        self.db.commit()

        # Ajouter les tâches
        if data.tasks:
            for task_data in data.tasks:
                task = MaintenancePlanTask(
                    tenant_id=self.tenant_id,
                    plan_id=plan.id,
                    sequence=task_data.sequence,
                    task_code=task_data.task_code,
                    description=task_data.description,
                    detailed_instructions=task_data.detailed_instructions,
                    estimated_duration_minutes=task_data.estimated_duration_minutes,
                    required_skill=task_data.required_skill,
                    required_parts=task_data.required_parts,
                    check_points=task_data.check_points,
                    is_mandatory=task_data.is_mandatory
                )
                self.db.add(task)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_maintenance_plan(self, plan_id: int) -> Optional[MaintenancePlan]:
        """Récupérer un plan de maintenance."""
        return self.db.query(MaintenancePlan).options(
            joinedload(MaintenancePlan.tasks)
        ).filter(
            MaintenancePlan.id == plan_id,
            MaintenancePlan.tenant_id == self.tenant_id
        ).first()

    def list_maintenance_plans(
        self,
        skip: int = 0,
        limit: int = 50,
        asset_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[MaintenancePlan], int]:
        """Lister les plans de maintenance."""
        query = self.db.query(MaintenancePlan).filter(
            MaintenancePlan.tenant_id == self.tenant_id
        )

        if asset_id:
            query = query.filter(MaintenancePlan.asset_id == asset_id)
        if is_active is not None:
            query = query.filter(MaintenancePlan.is_active == is_active)

        total = query.count()
        plans = query.options(joinedload(MaintenancePlan.tasks)).offset(skip).limit(limit).all()
        return plans, total

    def update_maintenance_plan(
        self,
        plan_id: int,
        data: MaintenancePlanUpdate
    ) -> Optional[MaintenancePlan]:
        """Mettre à jour un plan de maintenance."""
        plan = self.get_maintenance_plan(plan_id)
        if not plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    # ========================================================================
    # ORDRES DE TRAVAIL
    # ========================================================================

    def _generate_wo_number(self) -> str:
        """Générer un numéro d'ordre de travail."""
        today = date.today()
        prefix = f"WO-{today.strftime('%Y%m')}"

        last_wo = self.db.query(WorkOrder).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.wo_number.like(f"{prefix}%")
        ).order_by(desc(WorkOrder.wo_number)).first()

        if last_wo:
            last_num = int(last_wo.wo_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:04d}"

    def create_work_order(self, data: WorkOrderCreate) -> WorkOrder:
        """Créer un ordre de travail."""
        wo = WorkOrder(
            tenant_id=self.tenant_id,
            wo_number=self._generate_wo_number(),
            title=data.title,
            description=data.description,
            maintenance_type=data.maintenance_type,
            priority=data.priority,
            status=WorkOrderStatus.DRAFT,
            asset_id=data.asset_id,
            component_id=data.component_id,
            source="MANUAL",
            maintenance_plan_id=data.maintenance_plan_id,
            failure_id=data.failure_id,
            requester_id=data.requester_id or self.user_id,
            request_date=datetime.now(),
            request_description=data.request_description,
            scheduled_start_date=data.scheduled_start_date,
            scheduled_end_date=data.scheduled_end_date,
            due_date=data.due_date,
            assigned_to_id=data.assigned_to_id,
            external_vendor_id=data.external_vendor_id,
            work_instructions=data.work_instructions,
            safety_precautions=data.safety_precautions,
            tools_required=data.tools_required,
            location_description=data.location_description,
            estimated_labor_hours=data.estimated_labor_hours,
            estimated_parts_cost=data.estimated_parts_cost,
            created_by=self.user_id
        )
        self.db.add(wo)
        self.db.commit()

        # Ajouter les tâches
        if data.tasks:
            for task_data in data.tasks:
                task = WorkOrderTask(
                    tenant_id=self.tenant_id,
                    work_order_id=wo.id,
                    sequence=task_data.sequence,
                    description=task_data.description,
                    instructions=task_data.instructions,
                    estimated_minutes=task_data.estimated_minutes,
                    status="PENDING"
                )
                self.db.add(task)

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def get_work_order(self, wo_id: int) -> Optional[WorkOrder]:
        """Récupérer un ordre de travail."""
        return self.db.query(WorkOrder).options(
            joinedload(WorkOrder.tasks),
            joinedload(WorkOrder.labor_entries),
            joinedload(WorkOrder.parts_used)
        ).filter(
            WorkOrder.id == wo_id,
            WorkOrder.tenant_id == self.tenant_id
        ).first()

    def list_work_orders(
        self,
        skip: int = 0,
        limit: int = 50,
        asset_id: Optional[int] = None,
        status: Optional[WorkOrderStatus] = None,
        priority: Optional[WorkOrderPriority] = None,
        assigned_to_id: Optional[int] = None
    ) -> Tuple[List[WorkOrder], int]:
        """Lister les ordres de travail."""
        query = self.db.query(WorkOrder).filter(
            WorkOrder.tenant_id == self.tenant_id
        )

        if asset_id:
            query = query.filter(WorkOrder.asset_id == asset_id)
        if status:
            query = query.filter(WorkOrder.status == status)
        if priority:
            query = query.filter(WorkOrder.priority == priority)
        if assigned_to_id:
            query = query.filter(WorkOrder.assigned_to_id == assigned_to_id)

        total = query.count()
        work_orders = query.order_by(desc(WorkOrder.created_at)).offset(skip).limit(limit).all()
        return work_orders, total

    def update_work_order(
        self,
        wo_id: int,
        data: WorkOrderUpdate
    ) -> Optional[WorkOrder]:
        """Mettre à jour un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(wo, field, value)

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def start_work_order(self, wo_id: int) -> Optional[WorkOrder]:
        """Démarrer un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status not in [WorkOrderStatus.APPROVED, WorkOrderStatus.PLANNED, WorkOrderStatus.ASSIGNED]:
            return None

        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.actual_start_date = datetime.now()

        # Mettre l'actif en maintenance
        if wo.asset:
            wo.asset.status = AssetStatus.IN_MAINTENANCE

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def complete_work_order(
        self,
        wo_id: int,
        data: WorkOrderComplete
    ) -> Optional[WorkOrder]:
        """Terminer un ordre de travail."""
        wo = self.get_work_order(wo_id)
        if not wo or wo.status != WorkOrderStatus.IN_PROGRESS:
            return None

        wo.status = WorkOrderStatus.COMPLETED
        wo.actual_end_date = datetime.now()
        wo.completion_notes = data.completion_notes
        wo.completed_by_id = self.user_id
        wo.meter_reading_end = data.meter_reading_end

        # Calculer le temps d'arrêt
        if wo.actual_start_date and wo.actual_end_date:
            delta = wo.actual_end_date - wo.actual_start_date
            wo.downtime_hours = Decimal(str(delta.total_seconds() / 3600))

        # Calculer les coûts réels
        total_labor = self.db.query(func.sum(WorkOrderLabor.total_cost)).filter(
            WorkOrderLabor.work_order_id == wo_id
        ).scalar() or Decimal("0")

        total_parts = self.db.query(func.sum(WorkOrderPart.total_cost)).filter(
            WorkOrderPart.work_order_id == wo_id
        ).scalar() or Decimal("0")

        wo.actual_labor_cost = total_labor
        wo.actual_parts_cost = total_parts

        # Remettre l'actif en service
        if wo.asset:
            wo.asset.status = AssetStatus.ACTIVE
            wo.asset.last_maintenance_date = date.today()

        self.db.commit()
        self.db.refresh(wo)
        return wo

    def add_labor_entry(
        self,
        wo_id: int,
        data: WorkOrderLaborCreate
    ) -> Optional[WorkOrderLabor]:
        """Ajouter une entrée de main d'œuvre."""
        wo = self.get_work_order(wo_id)
        if not wo:
            return None

        total_cost = None
        if data.hourly_rate:
            hours = data.hours_worked + data.overtime_hours
            total_cost = data.hourly_rate * hours

        labor = WorkOrderLabor(
            tenant_id=self.tenant_id,
            work_order_id=wo_id,
            technician_id=data.technician_id,
            work_date=data.work_date,
            hours_worked=data.hours_worked,
            overtime_hours=data.overtime_hours,
            labor_type=data.labor_type,
            hourly_rate=data.hourly_rate,
            total_cost=total_cost,
            work_description=data.work_description,
            created_by=self.user_id
        )
        self.db.add(labor)

        # Mettre à jour les heures réelles
        wo.actual_labor_hours = (wo.actual_labor_hours or Decimal("0")) + data.hours_worked + data.overtime_hours

        self.db.commit()
        self.db.refresh(labor)
        return labor

    def add_part_used(
        self,
        wo_id: int,
        data: WorkOrderPartCreate
    ) -> Optional[WorkOrderPart]:
        """Ajouter une pièce utilisée."""
        wo = self.get_work_order(wo_id)
        if not wo:
            return None

        total_cost = None
        if data.unit_cost:
            total_cost = data.unit_cost * data.quantity_used

        part = WorkOrderPart(
            tenant_id=self.tenant_id,
            work_order_id=wo_id,
            spare_part_id=data.spare_part_id,
            part_description=data.part_description,
            quantity_used=data.quantity_used,
            unit=data.unit,
            unit_cost=data.unit_cost,
            total_cost=total_cost,
            source=data.source,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(part)
        self.db.commit()
        self.db.refresh(part)
        return part

    # ========================================================================
    # PANNES
    # ========================================================================

    def _generate_failure_number(self) -> str:
        """Générer un numéro de panne."""
        today = date.today()
        prefix = f"FL-{today.strftime('%Y%m')}"

        last = self.db.query(Failure).filter(
            Failure.tenant_id == self.tenant_id,
            Failure.failure_number.like(f"{prefix}%")
        ).order_by(desc(Failure.failure_number)).first()

        if last:
            last_num = int(last.failure_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:04d}"

    def create_failure(self, data: FailureCreate) -> Failure:
        """Enregistrer une panne."""
        failure = Failure(
            tenant_id=self.tenant_id,
            failure_number=self._generate_failure_number(),
            asset_id=data.asset_id,
            component_id=data.component_id,
            failure_type=data.failure_type,
            description=data.description,
            symptoms=data.symptoms,
            failure_date=data.failure_date,
            detected_date=datetime.now(),
            reported_date=datetime.now(),
            production_stopped=data.production_stopped,
            downtime_hours=data.downtime_hours,
            meter_reading=data.meter_reading,
            notes=data.notes,
            reported_by_id=self.user_id,
            status="OPEN",
            created_by=self.user_id
        )
        self.db.add(failure)

        # Mettre l'actif en panne
        asset = self.get_asset(data.asset_id)
        if asset:
            asset.status = AssetStatus.UNDER_REPAIR

        self.db.commit()
        self.db.refresh(failure)
        return failure

    def get_failure(self, failure_id: int) -> Optional[Failure]:
        """Récupérer une panne."""
        return self.db.query(Failure).filter(
            Failure.id == failure_id,
            Failure.tenant_id == self.tenant_id
        ).first()

    def list_failures(
        self,
        skip: int = 0,
        limit: int = 50,
        asset_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Failure], int]:
        """Lister les pannes."""
        query = self.db.query(Failure).filter(
            Failure.tenant_id == self.tenant_id
        )

        if asset_id:
            query = query.filter(Failure.asset_id == asset_id)
        if status:
            query = query.filter(Failure.status == status)

        total = query.count()
        failures = query.order_by(desc(Failure.failure_date)).offset(skip).limit(limit).all()
        return failures, total

    def update_failure(
        self,
        failure_id: int,
        data: FailureUpdate
    ) -> Optional[Failure]:
        """Mettre à jour une panne."""
        failure = self.get_failure(failure_id)
        if not failure:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(failure, field, value)

        if data.status == "RESOLVED":
            failure.resolved_date = datetime.now()

        self.db.commit()
        self.db.refresh(failure)
        return failure

    # ========================================================================
    # PIÈCES DE RECHANGE
    # ========================================================================

    def create_spare_part(self, data: SparePartCreate) -> SparePart:
        """Créer une pièce de rechange."""
        part = SparePart(
            tenant_id=self.tenant_id,
            part_code=data.part_code,
            name=data.name,
            description=data.description,
            category=data.category,
            manufacturer=data.manufacturer,
            manufacturer_part_number=data.manufacturer_part_number,
            preferred_supplier_id=data.preferred_supplier_id,
            unit=data.unit,
            unit_cost=data.unit_cost,
            min_stock_level=data.min_stock_level,
            max_stock_level=data.max_stock_level,
            reorder_point=data.reorder_point,
            reorder_quantity=data.reorder_quantity,
            lead_time_days=data.lead_time_days,
            criticality=data.criticality,
            shelf_life_days=data.shelf_life_days,
            product_id=data.product_id,
            notes=data.notes,
            specifications=data.specifications,
            is_active=True,
            created_by=self.user_id
        )
        self.db.add(part)
        self.db.commit()
        self.db.refresh(part)
        return part

    def get_spare_part(self, part_id: int) -> Optional[SparePart]:
        """Récupérer une pièce de rechange."""
        return self.db.query(SparePart).filter(
            SparePart.id == part_id,
            SparePart.tenant_id == self.tenant_id
        ).first()

    def list_spare_parts(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[SparePart], int]:
        """Lister les pièces de rechange."""
        query = self.db.query(SparePart).filter(
            SparePart.tenant_id == self.tenant_id,
            SparePart.is_active == True
        )

        if category:
            query = query.filter(SparePart.category == category)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    SparePart.part_code.ilike(search_term),
                    SparePart.name.ilike(search_term)
                )
            )

        total = query.count()
        parts = query.order_by(SparePart.part_code).offset(skip).limit(limit).all()
        return parts, total

    def update_spare_part(
        self,
        part_id: int,
        data: SparePartUpdate
    ) -> Optional[SparePart]:
        """Mettre à jour une pièce de rechange."""
        part = self.get_spare_part(part_id)
        if not part:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(part, field, value)

        self.db.commit()
        self.db.refresh(part)
        return part

    # ========================================================================
    # DEMANDES DE PIÈCES
    # ========================================================================

    def _generate_request_number(self) -> str:
        """Générer un numéro de demande."""
        today = date.today()
        prefix = f"PR-{today.strftime('%Y%m')}"

        last = self.db.query(PartRequest).filter(
            PartRequest.tenant_id == self.tenant_id,
            PartRequest.request_number.like(f"{prefix}%")
        ).order_by(desc(PartRequest.request_number)).first()

        if last:
            last_num = int(last.request_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:04d}"

    def create_part_request(self, data: PartRequestCreate) -> PartRequest:
        """Créer une demande de pièce."""
        request = PartRequest(
            tenant_id=self.tenant_id,
            request_number=self._generate_request_number(),
            work_order_id=data.work_order_id,
            spare_part_id=data.spare_part_id,
            part_description=data.part_description,
            quantity_requested=data.quantity_requested,
            unit=data.unit,
            priority=data.priority,
            required_date=data.required_date,
            request_reason=data.request_reason,
            requester_id=self.user_id,
            request_date=datetime.now(),
            status=PartRequestStatus.REQUESTED,
            created_by=self.user_id
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_part_requests(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[PartRequestStatus] = None,
        work_order_id: Optional[int] = None
    ) -> Tuple[List[PartRequest], int]:
        """Lister les demandes de pièces."""
        query = self.db.query(PartRequest).filter(
            PartRequest.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(PartRequest.status == status)
        if work_order_id:
            query = query.filter(PartRequest.work_order_id == work_order_id)

        total = query.count()
        requests = query.order_by(desc(PartRequest.request_date)).offset(skip).limit(limit).all()
        return requests, total

    # ========================================================================
    # CONTRATS
    # ========================================================================

    def create_contract(self, data: ContractCreate) -> MaintenanceContract:
        """Créer un contrat de maintenance."""
        contract = MaintenanceContract(
            tenant_id=self.tenant_id,
            contract_code=data.contract_code,
            name=data.name,
            description=data.description,
            contract_type=data.contract_type,
            status=ContractStatus.DRAFT,
            vendor_id=data.vendor_id,
            vendor_contact=data.vendor_contact,
            vendor_phone=data.vendor_phone,
            vendor_email=data.vendor_email,
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_date=data.renewal_date,
            notice_period_days=data.notice_period_days,
            auto_renewal=data.auto_renewal,
            covered_assets=data.covered_assets,
            coverage_description=data.coverage_description,
            exclusions=data.exclusions,
            response_time_hours=data.response_time_hours,
            resolution_time_hours=data.resolution_time_hours,
            contract_value=data.contract_value,
            annual_cost=data.annual_cost,
            payment_frequency=data.payment_frequency,
            includes_parts=data.includes_parts,
            includes_labor=data.includes_labor,
            includes_travel=data.includes_travel,
            max_interventions=data.max_interventions,
            interventions_used=0,
            manager_id=data.manager_id,
            notes=data.notes,
            created_by=self.user_id
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_contract(self, contract_id: int) -> Optional[MaintenanceContract]:
        """Récupérer un contrat."""
        return self.db.query(MaintenanceContract).filter(
            MaintenanceContract.id == contract_id,
            MaintenanceContract.tenant_id == self.tenant_id
        ).first()

    def list_contracts(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ContractStatus] = None
    ) -> Tuple[List[MaintenanceContract], int]:
        """Lister les contrats."""
        query = self.db.query(MaintenanceContract).filter(
            MaintenanceContract.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(MaintenanceContract.status == status)

        total = query.count()
        contracts = query.order_by(desc(MaintenanceContract.created_at)).offset(skip).limit(limit).all()
        return contracts, total

    def update_contract(
        self,
        contract_id: int,
        data: ContractUpdate
    ) -> Optional[MaintenanceContract]:
        """Mettre à jour un contrat."""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        self.db.commit()
        self.db.refresh(contract)
        return contract

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> MaintenanceDashboard:
        """Obtenir les statistiques du dashboard maintenance."""
        today = date.today()
        first_day_of_month = today.replace(day=1)

        # Actifs
        assets_total = self.db.query(func.count(Asset.id)).filter(
            Asset.tenant_id == self.tenant_id
        ).scalar() or 0

        assets_active = self.db.query(func.count(Asset.id)).filter(
            Asset.tenant_id == self.tenant_id,
            Asset.status == AssetStatus.ACTIVE
        ).scalar() or 0

        assets_in_maintenance = self.db.query(func.count(Asset.id)).filter(
            Asset.tenant_id == self.tenant_id,
            Asset.status.in_([AssetStatus.IN_MAINTENANCE, AssetStatus.UNDER_REPAIR])
        ).scalar() or 0

        # Ordres de travail
        wo_total = self.db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.tenant_id == self.tenant_id
        ).scalar() or 0

        wo_open = self.db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.status.in_([
                WorkOrderStatus.DRAFT, WorkOrderStatus.REQUESTED,
                WorkOrderStatus.APPROVED, WorkOrderStatus.PLANNED,
                WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS
            ])
        ).scalar() or 0

        wo_overdue = self.db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.due_date < datetime.now(),
            WorkOrder.status.not_in([WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED, WorkOrderStatus.CANCELLED])
        ).scalar() or 0

        wo_completed_this_month = self.db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.tenant_id == self.tenant_id,
            WorkOrder.status == WorkOrderStatus.COMPLETED,
            func.date(WorkOrder.actual_end_date) >= first_day_of_month
        ).scalar() or 0

        # Pannes ce mois
        failures_this_month = self.db.query(func.count(Failure.id)).filter(
            Failure.tenant_id == self.tenant_id,
            func.date(Failure.failure_date) >= first_day_of_month
        ).scalar() or 0

        # Plans actifs
        plans_active = self.db.query(func.count(MaintenancePlan.id)).filter(
            MaintenancePlan.tenant_id == self.tenant_id,
            MaintenancePlan.is_active == True
        ).scalar() or 0

        # Plans bientôt dus
        plans_due_soon = self.db.query(func.count(MaintenancePlan.id)).filter(
            MaintenancePlan.tenant_id == self.tenant_id,
            MaintenancePlan.is_active == True,
            MaintenancePlan.next_due_date.between(today, today + timedelta(days=7))
        ).scalar() or 0

        # Contrats actifs
        contracts_active = self.db.query(func.count(MaintenanceContract.id)).filter(
            MaintenanceContract.tenant_id == self.tenant_id,
            MaintenanceContract.status == ContractStatus.ACTIVE
        ).scalar() or 0

        # Contrats expirant bientôt
        contracts_expiring_soon = self.db.query(func.count(MaintenanceContract.id)).filter(
            MaintenanceContract.tenant_id == self.tenant_id,
            MaintenanceContract.status == ContractStatus.ACTIVE,
            MaintenanceContract.end_date.between(today, today + timedelta(days=30))
        ).scalar() or 0

        # Pièces sous stock minimum
        parts_below_min = self.db.query(func.count(SparePart.id)).filter(
            SparePart.tenant_id == self.tenant_id,
            SparePart.is_active == True
        ).scalar() or 0  # Simplified - would need stock calculation

        # Demandes en attente
        pending_requests = self.db.query(func.count(PartRequest.id)).filter(
            PartRequest.tenant_id == self.tenant_id,
            PartRequest.status.in_([PartRequestStatus.REQUESTED, PartRequestStatus.APPROVED])
        ).scalar() or 0

        return MaintenanceDashboard(
            assets_total=assets_total,
            assets_active=assets_active,
            assets_in_maintenance=assets_in_maintenance,
            wo_total=wo_total,
            wo_open=wo_open,
            wo_overdue=wo_overdue,
            wo_completed_this_month=wo_completed_this_month,
            failures_this_month=failures_this_month,
            plans_active=plans_active,
            plans_due_soon=plans_due_soon,
            contracts_active=contracts_active,
            contracts_expiring_soon=contracts_expiring_soon,
            parts_below_min_stock=parts_below_min,
            pending_part_requests=pending_requests
        )


def get_maintenance_service(db: Session, tenant_id: int, user_id: int) -> MaintenanceService:
    """Factory function pour le service maintenance."""
    return MaintenanceService(db, tenant_id, user_id)
