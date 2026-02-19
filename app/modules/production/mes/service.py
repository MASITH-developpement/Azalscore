"""
MES Service - Manufacturing Execution System
=============================================

Suivi de production en temps réel avec postes de travail et opérations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class WorkstationStatus(str, Enum):
    """Statuts de poste de travail."""
    OFFLINE = "offline"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    BREAKDOWN = "breakdown"


class OperationStatus(str, Enum):
    """Statuts d'opération."""
    PENDING = "pending"
    SETUP = "setup"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DowntimeReason(str, Enum):
    """Raisons d'arrêt."""
    BREAKDOWN = "breakdown"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"
    MAINTENANCE_UNSCHEDULED = "maintenance_unscheduled"
    CHANGEOVER = "changeover"
    MATERIAL_SHORTAGE = "material_shortage"
    OPERATOR_UNAVAILABLE = "operator_unavailable"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"


class CheckResult(str, Enum):
    """Résultats de contrôle qualité."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class Workstation:
    """Poste de travail / Machine."""
    id: str
    tenant_id: str
    code: str
    name: str
    workstation_type: str
    status: WorkstationStatus = WorkstationStatus.OFFLINE
    location: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    current_operator_id: Optional[str] = None
    current_operation_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class ProductionOperation:
    """Opération de production."""
    id: str
    tenant_id: str
    workstation_id: str
    order_id: str
    product_id: str
    operation_code: str
    operation_name: str
    planned_qty: float
    produced_qty: float = 0
    scrap_qty: float = 0
    status: OperationStatus = OperationStatus.PENDING
    operator_id: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    setup_time: float = 0.0  # minutes
    run_time: float = 0.0  # minutes
    created_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    @property
    def good_qty(self) -> float:
        """Quantité conforme."""
        return self.produced_qty - self.scrap_qty

    @property
    def yield_rate(self) -> float:
        """Taux de rendement."""
        if self.produced_qty == 0:
            return 0.0
        return round(self.good_qty / self.produced_qty * 100, 1)

    @property
    def completion_rate(self) -> float:
        """Taux de complétion."""
        if self.planned_qty == 0:
            return 0.0
        return round(self.good_qty / self.planned_qty * 100, 1)

    @property
    def total_time(self) -> float:
        """Temps total (setup + run)."""
        return self.setup_time + self.run_time


@dataclass
class TimeEntry:
    """Entrée de temps (pointage)."""
    id: str
    tenant_id: str
    operation_id: str
    workstation_id: str
    operator_id: str
    entry_type: str  # "start", "pause", "resume", "stop"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


@dataclass
class QualityCheck:
    """Contrôle qualité en ligne."""
    id: str
    tenant_id: str
    operation_id: str
    workstation_id: str
    check_type: str
    check_name: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    result: CheckResult = CheckResult.PENDING
    checked_by: Optional[str] = None
    checked_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Downtime:
    """Arrêt de production."""
    id: str
    tenant_id: str
    workstation_id: str
    operation_id: Optional[str]
    reason: DowntimeReason
    description: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    reported_by: Optional[str] = None
    resolved_by: Optional[str] = None

    def close(self, resolved_by: Optional[str] = None) -> None:
        """Ferme l'arrêt."""
        self.end_time = datetime.utcnow()
        self.resolved_by = resolved_by
        delta = self.end_time - self.start_time
        self.duration_minutes = delta.total_seconds() / 60


@dataclass
class OEEMetrics:
    """Métriques OEE."""
    workstation_id: str
    period_start: datetime
    period_end: datetime
    availability: float  # % temps disponible
    performance: float  # % performance théorique
    quality: float  # % pièces conformes
    oee: float  # availability * performance * quality
    total_time: float  # minutes
    run_time: float
    downtime: float
    planned_qty: float
    produced_qty: float
    good_qty: float


class MESService:
    """Service MES (Manufacturing Execution System)."""

    def __init__(self, db: Any, tenant_id: str):
        """
        Initialise le service MES.

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
        self._workstations: dict[str, Workstation] = {}
        self._operations: dict[str, ProductionOperation] = {}
        self._time_entries: dict[str, TimeEntry] = {}
        self._quality_checks: dict[str, QualityCheck] = {}
        self._downtimes: dict[str, Downtime] = {}

    # ========================
    # WORKSTATIONS
    # ========================

    async def create_workstation(
        self,
        code: str,
        name: str,
        workstation_type: str,
        location: Optional[str] = None,
        capacity_per_hour: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> Workstation:
        """Crée un poste de travail."""
        workstation = Workstation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            workstation_type=workstation_type,
            location=location,
            capacity_per_hour=capacity_per_hour,
            metadata=metadata or {}
        )
        self._workstations[workstation.id] = workstation
        return workstation

    async def get_workstation(self, workstation_id: str) -> Optional[Workstation]:
        """Récupère un poste de travail."""
        ws = self._workstations.get(workstation_id)
        if ws and ws.tenant_id == self.tenant_id:
            return ws
        return None

    async def get_workstation_by_code(self, code: str) -> Optional[Workstation]:
        """Récupère un poste par son code."""
        for ws in self._workstations.values():
            if ws.tenant_id == self.tenant_id and ws.code == code:
                return ws
        return None

    async def list_workstations(
        self,
        workstation_type: Optional[str] = None,
        status: Optional[WorkstationStatus] = None,
        is_active: Optional[bool] = None
    ) -> list[Workstation]:
        """Liste les postes de travail."""
        workstations = [
            ws for ws in self._workstations.values()
            if ws.tenant_id == self.tenant_id
        ]

        if workstation_type:
            workstations = [ws for ws in workstations if ws.workstation_type == workstation_type]

        if status:
            workstations = [ws for ws in workstations if ws.status == status]

        if is_active is not None:
            workstations = [ws for ws in workstations if ws.is_active == is_active]

        return sorted(workstations, key=lambda x: x.code)

    async def update_workstation_status(
        self,
        workstation_id: str,
        status: WorkstationStatus,
        operator_id: Optional[str] = None
    ) -> Optional[Workstation]:
        """Met à jour le statut d'un poste."""
        ws = await self.get_workstation(workstation_id)
        if not ws:
            return None

        ws.status = status
        if operator_id is not None:
            ws.current_operator_id = operator_id

        return ws

    # ========================
    # OPERATIONS
    # ========================

    async def create_operation(
        self,
        workstation_id: str,
        order_id: str,
        product_id: str,
        operation_code: str,
        operation_name: str,
        planned_qty: float,
        planned_start: Optional[datetime] = None,
        planned_end: Optional[datetime] = None
    ) -> ProductionOperation:
        """Crée une opération de production."""
        operation = ProductionOperation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            workstation_id=workstation_id,
            order_id=order_id,
            product_id=product_id,
            operation_code=operation_code,
            operation_name=operation_name,
            planned_qty=planned_qty,
            planned_start=planned_start,
            planned_end=planned_end
        )
        self._operations[operation.id] = operation
        return operation

    async def get_operation(self, operation_id: str) -> Optional[ProductionOperation]:
        """Récupère une opération."""
        op = self._operations.get(operation_id)
        if op and op.tenant_id == self.tenant_id:
            return op
        return None

    async def list_operations(
        self,
        workstation_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[OperationStatus] = None
    ) -> list[ProductionOperation]:
        """Liste les opérations."""
        operations = [
            op for op in self._operations.values()
            if op.tenant_id == self.tenant_id
        ]

        if workstation_id:
            operations = [op for op in operations if op.workstation_id == workstation_id]

        if order_id:
            operations = [op for op in operations if op.order_id == order_id]

        if status:
            operations = [op for op in operations if op.status == status]

        return sorted(operations, key=lambda x: x.created_at, reverse=True)

    async def start_operation(
        self,
        operation_id: str,
        operator_id: str,
        setup_time: float = 0.0
    ) -> Optional[ProductionOperation]:
        """Démarre une opération."""
        operation = await self.get_operation(operation_id)
        if not operation:
            return None

        operation.status = OperationStatus.RUNNING
        operation.operator_id = operator_id
        operation.actual_start = datetime.utcnow()
        operation.setup_time = setup_time

        # Update workstation
        ws = await self.get_workstation(operation.workstation_id)
        if ws:
            ws.status = WorkstationStatus.RUNNING
            ws.current_operator_id = operator_id
            ws.current_operation_id = operation.id

        # Create time entry
        await self._create_time_entry(
            operation_id=operation.id,
            workstation_id=operation.workstation_id,
            operator_id=operator_id,
            entry_type="start"
        )

        return operation

    async def pause_operation(
        self,
        operation_id: str,
        notes: Optional[str] = None
    ) -> Optional[ProductionOperation]:
        """Met en pause une opération."""
        operation = await self.get_operation(operation_id)
        if not operation:
            return None

        operation.status = OperationStatus.PAUSED

        # Update workstation
        ws = await self.get_workstation(operation.workstation_id)
        if ws:
            ws.status = WorkstationStatus.PAUSED

        # Create time entry
        if operation.operator_id:
            await self._create_time_entry(
                operation_id=operation.id,
                workstation_id=operation.workstation_id,
                operator_id=operation.operator_id,
                entry_type="pause",
                notes=notes
            )

        return operation

    async def resume_operation(
        self,
        operation_id: str
    ) -> Optional[ProductionOperation]:
        """Reprend une opération."""
        operation = await self.get_operation(operation_id)
        if not operation:
            return None

        operation.status = OperationStatus.RUNNING

        # Update workstation
        ws = await self.get_workstation(operation.workstation_id)
        if ws:
            ws.status = WorkstationStatus.RUNNING

        # Create time entry
        if operation.operator_id:
            await self._create_time_entry(
                operation_id=operation.id,
                workstation_id=operation.workstation_id,
                operator_id=operation.operator_id,
                entry_type="resume"
            )

        return operation

    async def complete_operation(
        self,
        operation_id: str,
        produced_qty: float,
        scrap_qty: float = 0
    ) -> Optional[ProductionOperation]:
        """Termine une opération."""
        operation = await self.get_operation(operation_id)
        if not operation:
            return None

        operation.status = OperationStatus.COMPLETED
        operation.produced_qty = produced_qty
        operation.scrap_qty = scrap_qty
        operation.actual_end = datetime.utcnow()

        # Calculate run time
        if operation.actual_start:
            delta = operation.actual_end - operation.actual_start
            total_minutes = delta.total_seconds() / 60
            operation.run_time = max(0.0, total_minutes - operation.setup_time)

        # Update workstation
        ws = await self.get_workstation(operation.workstation_id)
        if ws:
            ws.status = WorkstationStatus.IDLE
            ws.current_operation_id = None

        # Create time entry
        if operation.operator_id:
            await self._create_time_entry(
                operation_id=operation.id,
                workstation_id=operation.workstation_id,
                operator_id=operation.operator_id,
                entry_type="stop"
            )

        return operation

    async def report_production(
        self,
        operation_id: str,
        quantity: float,
        scrap_qty: float = 0
    ) -> Optional[ProductionOperation]:
        """Déclare une production partielle."""
        operation = await self.get_operation(operation_id)
        if not operation:
            return None

        operation.produced_qty += quantity
        operation.scrap_qty += scrap_qty

        return operation

    async def _create_time_entry(
        self,
        operation_id: str,
        workstation_id: str,
        operator_id: str,
        entry_type: str,
        notes: Optional[str] = None
    ) -> TimeEntry:
        """Crée une entrée de temps."""
        entry = TimeEntry(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            operation_id=operation_id,
            workstation_id=workstation_id,
            operator_id=operator_id,
            entry_type=entry_type,
            notes=notes
        )
        self._time_entries[entry.id] = entry
        return entry

    async def get_time_entries(
        self,
        operation_id: Optional[str] = None,
        workstation_id: Optional[str] = None,
        operator_id: Optional[str] = None
    ) -> list[TimeEntry]:
        """Récupère les entrées de temps."""
        entries = [
            e for e in self._time_entries.values()
            if e.tenant_id == self.tenant_id
        ]

        if operation_id:
            entries = [e for e in entries if e.operation_id == operation_id]

        if workstation_id:
            entries = [e for e in entries if e.workstation_id == workstation_id]

        if operator_id:
            entries = [e for e in entries if e.operator_id == operator_id]

        return sorted(entries, key=lambda x: x.timestamp)

    # ========================
    # QUALITY CHECKS
    # ========================

    async def create_quality_check(
        self,
        operation_id: str,
        workstation_id: str,
        check_type: str,
        check_name: str,
        expected_value: Optional[str] = None
    ) -> QualityCheck:
        """Crée un contrôle qualité."""
        check = QualityCheck(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            operation_id=operation_id,
            workstation_id=workstation_id,
            check_type=check_type,
            check_name=check_name,
            expected_value=expected_value
        )
        self._quality_checks[check.id] = check
        return check

    async def get_quality_check(self, check_id: str) -> Optional[QualityCheck]:
        """Récupère un contrôle qualité."""
        check = self._quality_checks.get(check_id)
        if check and check.tenant_id == self.tenant_id:
            return check
        return None

    async def record_quality_check(
        self,
        check_id: str,
        actual_value: str,
        result: CheckResult,
        checked_by: str,
        notes: Optional[str] = None
    ) -> Optional[QualityCheck]:
        """Enregistre un résultat de contrôle."""
        check = await self.get_quality_check(check_id)
        if not check:
            return None

        check.actual_value = actual_value
        check.result = result
        check.checked_by = checked_by
        check.checked_at = datetime.utcnow()
        check.notes = notes

        return check

    async def list_quality_checks(
        self,
        operation_id: Optional[str] = None,
        workstation_id: Optional[str] = None,
        result: Optional[CheckResult] = None
    ) -> list[QualityCheck]:
        """Liste les contrôles qualité."""
        checks = [
            c for c in self._quality_checks.values()
            if c.tenant_id == self.tenant_id
        ]

        if operation_id:
            checks = [c for c in checks if c.operation_id == operation_id]

        if workstation_id:
            checks = [c for c in checks if c.workstation_id == workstation_id]

        if result:
            checks = [c for c in checks if c.result == result]

        return sorted(checks, key=lambda x: x.created_at, reverse=True)

    # ========================
    # DOWNTIME
    # ========================

    async def report_downtime(
        self,
        workstation_id: str,
        reason: DowntimeReason,
        operation_id: Optional[str] = None,
        description: Optional[str] = None,
        reported_by: Optional[str] = None
    ) -> Downtime:
        """Déclare un arrêt."""
        downtime = Downtime(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            workstation_id=workstation_id,
            operation_id=operation_id,
            reason=reason,
            description=description,
            reported_by=reported_by
        )
        self._downtimes[downtime.id] = downtime

        # Update workstation status
        ws = await self.get_workstation(workstation_id)
        if ws:
            if reason == DowntimeReason.BREAKDOWN:
                ws.status = WorkstationStatus.BREAKDOWN
            elif reason in (DowntimeReason.MAINTENANCE_SCHEDULED, DowntimeReason.MAINTENANCE_UNSCHEDULED):
                ws.status = WorkstationStatus.MAINTENANCE

        return downtime

    async def get_downtime(self, downtime_id: str) -> Optional[Downtime]:
        """Récupère un arrêt."""
        dt = self._downtimes.get(downtime_id)
        if dt and dt.tenant_id == self.tenant_id:
            return dt
        return None

    async def resolve_downtime(
        self,
        downtime_id: str,
        resolved_by: Optional[str] = None
    ) -> Optional[Downtime]:
        """Résout un arrêt."""
        downtime = await self.get_downtime(downtime_id)
        if not downtime:
            return None

        downtime.close(resolved_by)

        # Update workstation
        ws = await self.get_workstation(downtime.workstation_id)
        if ws:
            ws.status = WorkstationStatus.IDLE

        return downtime

    async def list_downtimes(
        self,
        workstation_id: Optional[str] = None,
        reason: Optional[DowntimeReason] = None,
        active_only: bool = False
    ) -> list[Downtime]:
        """Liste les arrêts."""
        downtimes = [
            dt for dt in self._downtimes.values()
            if dt.tenant_id == self.tenant_id
        ]

        if workstation_id:
            downtimes = [dt for dt in downtimes if dt.workstation_id == workstation_id]

        if reason:
            downtimes = [dt for dt in downtimes if dt.reason == reason]

        if active_only:
            downtimes = [dt for dt in downtimes if dt.end_time is None]

        return sorted(downtimes, key=lambda x: x.start_time, reverse=True)

    # ========================
    # OEE & STATISTICS
    # ========================

    async def calculate_oee(
        self,
        workstation_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> OEEMetrics:
        """Calcule les métriques OEE pour un poste."""
        # Get operations in period
        operations = [
            op for op in await self.list_operations(workstation_id=workstation_id)
            if op.actual_start and op.actual_start >= period_start
            and (not op.actual_end or op.actual_end <= period_end)
        ]

        # Get downtimes in period
        downtimes = [
            dt for dt in await self.list_downtimes(workstation_id=workstation_id)
            if dt.start_time >= period_start and dt.start_time <= period_end
        ]

        # Calculate totals
        total_time = (period_end - period_start).total_seconds() / 60
        downtime_minutes = sum(dt.duration_minutes or 0 for dt in downtimes)
        run_time = sum(op.run_time for op in operations)

        planned_qty = sum(op.planned_qty for op in operations)
        produced_qty = sum(op.produced_qty for op in operations)
        good_qty = sum(op.good_qty for op in operations)

        # Calculate OEE components
        available_time = total_time - downtime_minutes
        availability = (available_time / total_time * 100) if total_time > 0 else 0

        ws = await self.get_workstation(workstation_id)
        # Calculate performance - use run_time only if significant (> 1 minute)
        if ws and ws.capacity_per_hour and run_time > 1:
            theoretical_output = ws.capacity_per_hour * (run_time / 60)
            performance = (produced_qty / theoretical_output * 100) if theoretical_output > 0 else 100
        else:
            # Fallback: compare to planned
            performance = 100 if produced_qty >= planned_qty else (produced_qty / planned_qty * 100 if planned_qty > 0 else 100)

        # Cap performance at 100%
        performance = min(performance, 100.0)

        quality = (good_qty / produced_qty * 100) if produced_qty > 0 else 100

        # OEE = Availability × Performance × Quality (all capped at 100)
        oee = (min(availability, 100) / 100) * (min(performance, 100) / 100) * (min(quality, 100) / 100) * 100

        return OEEMetrics(
            workstation_id=workstation_id,
            period_start=period_start,
            period_end=period_end,
            availability=round(availability, 1),
            performance=round(min(performance, 100), 1),
            quality=round(quality, 1),
            oee=round(oee, 1),
            total_time=total_time,
            run_time=run_time,
            downtime=downtime_minutes,
            planned_qty=planned_qty,
            produced_qty=produced_qty,
            good_qty=good_qty
        )

    async def get_workstation_stats(
        self,
        workstation_id: str
    ) -> dict:
        """Retourne les statistiques d'un poste."""
        operations = await self.list_operations(workstation_id=workstation_id)
        downtimes = await self.list_downtimes(workstation_id=workstation_id)
        quality_checks = await self.list_quality_checks(workstation_id=workstation_id)

        completed_ops = [op for op in operations if op.status == OperationStatus.COMPLETED]
        active_downtimes = [dt for dt in downtimes if dt.end_time is None]
        failed_checks = [c for c in quality_checks if c.result == CheckResult.FAIL]

        return {
            "workstation_id": workstation_id,
            "total_operations": len(operations),
            "completed_operations": len(completed_ops),
            "running_operations": len([op for op in operations if op.status == OperationStatus.RUNNING]),
            "total_produced": sum(op.produced_qty for op in completed_ops),
            "total_scrap": sum(op.scrap_qty for op in completed_ops),
            "total_run_time": sum(op.run_time for op in completed_ops),
            "active_downtimes": len(active_downtimes),
            "total_downtimes": len(downtimes),
            "quality_checks": len(quality_checks),
            "failed_checks": len(failed_checks)
        }

    async def get_operator_stats(
        self,
        operator_id: str
    ) -> dict:
        """Retourne les statistiques d'un opérateur."""
        operations = [
            op for op in self._operations.values()
            if op.tenant_id == self.tenant_id and op.operator_id == operator_id
        ]

        completed_ops = [op for op in operations if op.status == OperationStatus.COMPLETED]

        return {
            "operator_id": operator_id,
            "total_operations": len(operations),
            "completed_operations": len(completed_ops),
            "total_produced": sum(op.produced_qty for op in completed_ops),
            "total_scrap": sum(op.scrap_qty for op in completed_ops),
            "total_run_time": sum(op.run_time for op in completed_ops),
            "avg_yield_rate": (
                sum(op.yield_rate for op in completed_ops) / len(completed_ops)
                if completed_ops else 0
            )
        }

    async def get_dashboard_data(self) -> dict:
        """Retourne les données du tableau de bord MES."""
        workstations = await self.list_workstations()
        operations = await self.list_operations()
        downtimes = await self.list_downtimes(active_only=True)

        running = [ws for ws in workstations if ws.status == WorkstationStatus.RUNNING]
        idle = [ws for ws in workstations if ws.status == WorkstationStatus.IDLE]
        down = [ws for ws in workstations if ws.status in (WorkstationStatus.BREAKDOWN, WorkstationStatus.MAINTENANCE)]

        today = datetime.utcnow().date()
        today_ops = [
            op for op in operations
            if op.actual_start and op.actual_start.date() == today
        ]

        return {
            "workstations": {
                "total": len(workstations),
                "running": len(running),
                "idle": len(idle),
                "down": len(down)
            },
            "operations_today": {
                "total": len(today_ops),
                "completed": len([op for op in today_ops if op.status == OperationStatus.COMPLETED]),
                "running": len([op for op in today_ops if op.status == OperationStatus.RUNNING]),
                "produced_qty": sum(op.produced_qty for op in today_ops)
            },
            "active_downtimes": len(downtimes),
            "downtime_by_reason": self._count_by_reason(downtimes)
        }

    def _count_by_reason(self, downtimes: list[Downtime]) -> dict:
        """Compte les arrêts par raison."""
        counts = {}
        for dt in downtimes:
            reason = dt.reason.value
            counts[reason] = counts.get(reason, 0) + 1
        return counts
