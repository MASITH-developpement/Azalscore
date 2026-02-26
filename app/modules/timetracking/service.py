"""
Module Time Tracking - GAP-080

Suivi du temps:
- Pointage entrée/sortie
- Feuilles de temps
- Projets et tâches
- Heures facturables
- Approbations
- Overtime et congés
- Rapports et analytics
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid


# ============== Énumérations ==============

class EntryType(str, Enum):
    """Type d'entrée de temps."""
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"
    MANUAL = "manual"


class TimesheetStatus(str, Enum):
    """Statut de la feuille de temps."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class TimeEntryStatus(str, Enum):
    """Statut d'une entrée de temps."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BILLED = "billed"


class BillableType(str, Enum):
    """Type de facturation."""
    BILLABLE = "billable"
    NON_BILLABLE = "non_billable"
    INTERNAL = "internal"


class OvertimeType(str, Enum):
    """Type d'heures supplémentaires."""
    REGULAR = "regular"
    OVERTIME_1_5 = "overtime_1_5"  # 1.5x
    OVERTIME_2 = "overtime_2"  # 2x
    HOLIDAY = "holiday"
    NIGHT = "night"


class AbsenceType(str, Enum):
    """Type d'absence."""
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    TRAINING = "training"
    REMOTE = "remote"
    UNPAID = "unpaid"


# ============== Data Classes ==============

@dataclass
class TimePolicy:
    """Politique de temps."""
    id: str
    tenant_id: str
    name: str
    description: str

    # Heures de travail
    standard_hours_per_day: Decimal = Decimal("8")
    standard_hours_per_week: Decimal = Decimal("40")
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])

    # Pauses
    break_duration_minutes: int = 60
    min_break_after_hours: Decimal = Decimal("6")

    # Heures supplémentaires
    overtime_after_daily: Decimal = Decimal("8")
    overtime_after_weekly: Decimal = Decimal("40")
    overtime_multiplier: Decimal = Decimal("1.5")
    double_overtime_after_daily: Decimal = Decimal("10")
    double_overtime_multiplier: Decimal = Decimal("2")

    # Nuit
    night_start: time = field(default_factory=lambda: time(21, 0))
    night_end: time = field(default_factory=lambda: time(6, 0))
    night_multiplier: Decimal = Decimal("1.25")

    # Arrondi
    rounding_minutes: int = 15  # Arrondir au quart d'heure
    rounding_method: str = "nearest"  # nearest, up, down

    # Validation
    require_break_logging: bool = False
    require_project_assignment: bool = False
    require_description: bool = False

    # Approbation
    require_approval: bool = True
    auto_approve_under_hours: Optional[Decimal] = None

    is_default: bool = False
    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Project:
    """Projet pour le suivi du temps."""
    id: str
    tenant_id: str
    code: str
    name: str
    description: str

    # Client
    client_id: str = ""
    client_name: str = ""

    # Budget
    budget_hours: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    hourly_rate: Decimal = Decimal("0")

    # Facturation
    billable_default: BillableType = BillableType.BILLABLE

    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Membres
    member_ids: List[str] = field(default_factory=list)
    manager_id: str = ""

    # Suivi
    total_hours: Decimal = Decimal("0")
    billable_hours: Decimal = Decimal("0")
    billed_hours: Decimal = Decimal("0")
    remaining_budget_hours: Optional[Decimal] = None

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Task:
    """Tâche de projet."""
    id: str
    tenant_id: str
    project_id: str
    name: str
    description: str

    # Budget
    estimated_hours: Optional[Decimal] = None
    actual_hours: Decimal = Decimal("0")

    # Facturation
    billable_type: BillableType = BillableType.BILLABLE
    hourly_rate: Optional[Decimal] = None  # Override du projet

    # Assignation
    assignee_ids: List[str] = field(default_factory=list)

    # Dates
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ClockEntry:
    """Entrée de pointage."""
    id: str
    tenant_id: str
    user_id: str

    entry_type: EntryType = EntryType.CLOCK_IN
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Géolocalisation
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    location_name: str = ""

    # Source
    source: str = ""  # web, mobile, kiosk, api

    # IP et device
    ip_address: str = ""
    device_info: str = ""

    notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TimeEntry:
    """Entrée de temps."""
    id: str
    tenant_id: str
    user_id: str
    user_name: str = ""

    # Période
    entry_date: date = field(default_factory=date.today)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_hours: Decimal = Decimal("0")

    # Projet/Tâche
    project_id: str = ""
    project_name: str = ""
    task_id: str = ""
    task_name: str = ""

    # Description
    description: str = ""

    # Facturation
    billable_type: BillableType = BillableType.BILLABLE
    hourly_rate: Decimal = Decimal("0")
    billable_amount: Decimal = Decimal("0")

    # Heures sup
    overtime_type: OvertimeType = OvertimeType.REGULAR
    overtime_hours: Decimal = Decimal("0")
    overtime_multiplier: Decimal = Decimal("1")

    # Statut
    status: TimeEntryStatus = TimeEntryStatus.PENDING

    # Timesheet
    timesheet_id: Optional[str] = None

    # Pointage lié
    clock_in_id: Optional[str] = None
    clock_out_id: Optional[str] = None

    # Tags
    tags: List[str] = field(default_factory=list)

    # Approbation
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""

    # Facturation
    invoice_id: Optional[str] = None
    billed_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Timesheet:
    """Feuille de temps."""
    id: str
    tenant_id: str
    user_id: str
    user_name: str = ""

    # Période
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    status: TimesheetStatus = TimesheetStatus.DRAFT

    # Entrées
    entry_ids: List[str] = field(default_factory=list)

    # Totaux
    total_hours: Decimal = Decimal("0")
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    billable_hours: Decimal = Decimal("0")
    non_billable_hours: Decimal = Decimal("0")

    # Par jour
    daily_totals: Dict[str, Decimal] = field(default_factory=dict)

    # Approbation
    submitted_at: Optional[datetime] = None
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""

    notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Absence:
    """Absence / Congé."""
    id: str
    tenant_id: str
    user_id: str
    user_name: str = ""

    absence_type: AbsenceType = AbsenceType.VACATION

    # Période
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    start_half_day: bool = False  # Demi-journée début
    end_half_day: bool = False  # Demi-journée fin

    # Durée calculée
    total_days: Decimal = Decimal("0")

    # Approbation
    status: str = "pending"  # pending, approved, rejected, cancelled
    requested_at: datetime = field(default_factory=datetime.utcnow)
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""

    reason: str = ""
    notes: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserTimeBalance:
    """Solde de temps d'un utilisateur."""
    user_id: str
    tenant_id: str
    period_start: date
    period_end: date

    # Heures travaillées
    expected_hours: Decimal = Decimal("0")
    worked_hours: Decimal = Decimal("0")
    balance_hours: Decimal = Decimal("0")

    # Heures sup
    overtime_earned: Decimal = Decimal("0")
    overtime_used: Decimal = Decimal("0")
    overtime_balance: Decimal = Decimal("0")

    # Congés (en jours)
    vacation_earned: Decimal = Decimal("0")
    vacation_used: Decimal = Decimal("0")
    vacation_balance: Decimal = Decimal("0")

    sick_used: Decimal = Decimal("0")
    sick_balance: Decimal = Decimal("0")

    # Par projet
    hours_by_project: Dict[str, Decimal] = field(default_factory=dict)


@dataclass
class TimeReport:
    """Rapport de temps."""
    tenant_id: str
    period_start: date
    period_end: date

    # Totaux
    total_hours: Decimal = Decimal("0")
    billable_hours: Decimal = Decimal("0")
    non_billable_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")

    # Valeur
    billable_amount: Decimal = Decimal("0")
    average_hourly_rate: Decimal = Decimal("0")

    # Utilisation
    utilization_rate: Decimal = Decimal("0")
    billability_rate: Decimal = Decimal("0")

    # Par utilisateur
    hours_by_user: Dict[str, Decimal] = field(default_factory=dict)

    # Par projet
    hours_by_project: Dict[str, Decimal] = field(default_factory=dict)

    # Par client
    hours_by_client: Dict[str, Decimal] = field(default_factory=dict)

    # Par jour
    hours_by_day: Dict[str, Decimal] = field(default_factory=dict)


# ============== Service Principal ==============

class TimeTrackingService:
    """Service de suivi du temps."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._policies: Dict[str, TimePolicy] = {}
        self._projects: Dict[str, Project] = {}
        self._tasks: Dict[str, Task] = {}
        self._clock_entries: Dict[str, ClockEntry] = {}
        self._time_entries: Dict[str, TimeEntry] = {}
        self._timesheets: Dict[str, Timesheet] = {}
        self._absences: Dict[str, Absence] = {}

    # ===== Politiques =====

    def create_policy(
        self,
        name: str,
        description: str = "",
        *,
        standard_hours_per_day: Decimal = Decimal("8"),
        standard_hours_per_week: Decimal = Decimal("40"),
        overtime_after_daily: Decimal = Decimal("8"),
        overtime_multiplier: Decimal = Decimal("1.5"),
        require_approval: bool = True,
        is_default: bool = False
    ) -> TimePolicy:
        """Créer une politique de temps."""
        policy_id = str(uuid.uuid4())

        # Désactiver l'ancien défaut
        if is_default:
            for p in self._policies.values():
                if p.tenant_id == self.tenant_id and p.is_default:
                    p.is_default = False

        policy = TimePolicy(
            id=policy_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            standard_hours_per_day=standard_hours_per_day,
            standard_hours_per_week=standard_hours_per_week,
            overtime_after_daily=overtime_after_daily,
            overtime_multiplier=overtime_multiplier,
            require_approval=require_approval,
            is_default=is_default
        )

        self._policies[policy_id] = policy
        return policy

    def get_default_policy(self) -> Optional[TimePolicy]:
        """Récupérer la politique par défaut."""
        for policy in self._policies.values():
            if policy.tenant_id == self.tenant_id and policy.is_default:
                return policy
        return None

    # ===== Projets =====

    def create_project(
        self,
        code: str,
        name: str,
        *,
        description: str = "",
        client_id: str = "",
        client_name: str = "",
        budget_hours: Optional[Decimal] = None,
        hourly_rate: Decimal = Decimal("0"),
        billable_default: BillableType = BillableType.BILLABLE,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        manager_id: str = ""
    ) -> Project:
        """Créer un projet."""
        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            client_id=client_id,
            client_name=client_name,
            budget_hours=budget_hours,
            hourly_rate=hourly_rate,
            billable_default=billable_default,
            start_date=start_date,
            end_date=end_date,
            manager_id=manager_id,
            remaining_budget_hours=budget_hours
        )

        self._projects[project_id] = project
        return project

    def add_project_member(
        self,
        project_id: str,
        user_id: str
    ) -> Optional[Project]:
        """Ajouter un membre au projet."""
        project = self._projects.get(project_id)
        if not project or project.tenant_id != self.tenant_id:
            return None

        if user_id not in project.member_ids:
            project.member_ids.append(user_id)
            project.updated_at = datetime.utcnow()

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Récupérer un projet."""
        project = self._projects.get(project_id)
        if project and project.tenant_id == self.tenant_id:
            return project
        return None

    def list_projects(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Project]:
        """Lister les projets."""
        projects = [
            p for p in self._projects.values()
            if p.tenant_id == self.tenant_id
        ]

        if active_only:
            projects = [p for p in projects if p.is_active]

        if user_id:
            projects = [p for p in projects
                       if user_id in p.member_ids or p.manager_id == user_id]

        return sorted(projects, key=lambda x: x.name)

    # ===== Tâches =====

    def create_task(
        self,
        project_id: str,
        name: str,
        *,
        description: str = "",
        estimated_hours: Optional[Decimal] = None,
        billable_type: Optional[BillableType] = None,
        hourly_rate: Optional[Decimal] = None
    ) -> Optional[Task]:
        """Créer une tâche."""
        project = self._projects.get(project_id)
        if not project or project.tenant_id != self.tenant_id:
            return None

        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            tenant_id=self.tenant_id,
            project_id=project_id,
            name=name,
            description=description,
            estimated_hours=estimated_hours,
            billable_type=billable_type or project.billable_default,
            hourly_rate=hourly_rate
        )

        self._tasks[task_id] = task
        return task

    def get_project_tasks(self, project_id: str) -> List[Task]:
        """Récupérer les tâches d'un projet."""
        return [
            t for t in self._tasks.values()
            if t.project_id == project_id and t.tenant_id == self.tenant_id and t.is_active
        ]

    # ===== Pointage =====

    def clock_in(
        self,
        user_id: str,
        *,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        location_name: str = "",
        source: str = "web",
        notes: str = ""
    ) -> ClockEntry:
        """Pointer l'entrée."""
        entry_id = str(uuid.uuid4())

        entry = ClockEntry(
            id=entry_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            entry_type=EntryType.CLOCK_IN,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            source=source,
            notes=notes
        )

        self._clock_entries[entry_id] = entry
        return entry

    def clock_out(
        self,
        user_id: str,
        *,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        location_name: str = "",
        source: str = "web",
        notes: str = ""
    ) -> Optional[Tuple[ClockEntry, TimeEntry]]:
        """Pointer la sortie et créer l'entrée de temps."""
        # Trouver le dernier clock_in
        last_clock_in = None
        for entry in sorted(self._clock_entries.values(),
                           key=lambda x: x.timestamp, reverse=True):
            if (entry.user_id == user_id and
                entry.tenant_id == self.tenant_id and
                entry.entry_type == EntryType.CLOCK_IN):
                last_clock_in = entry
                break

        if not last_clock_in:
            return None

        # Créer le clock_out
        clock_out_id = str(uuid.uuid4())
        now = datetime.utcnow()

        clock_out = ClockEntry(
            id=clock_out_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            entry_type=EntryType.CLOCK_OUT,
            timestamp=now,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            source=source,
            notes=notes
        )

        self._clock_entries[clock_out_id] = clock_out

        # Calculer la durée
        duration = (now - last_clock_in.timestamp).total_seconds() / 3600
        duration_dec = Decimal(str(duration)).quantize(Decimal("0.01"), ROUND_HALF_UP)

        # Créer l'entrée de temps
        time_entry = self.create_time_entry(
            user_id=user_id,
            entry_date=last_clock_in.timestamp.date(),
            start_time=last_clock_in.timestamp.time(),
            end_time=now.time(),
            duration_hours=duration_dec,
            clock_in_id=last_clock_in.id,
            clock_out_id=clock_out_id
        )

        return (clock_out, time_entry)

    def get_user_clock_status(self, user_id: str) -> Dict[str, Any]:
        """Obtenir le statut de pointage d'un utilisateur."""
        entries = sorted(
            [e for e in self._clock_entries.values()
             if e.user_id == user_id and e.tenant_id == self.tenant_id],
            key=lambda x: x.timestamp,
            reverse=True
        )

        if not entries:
            return {"clocked_in": False}

        last_entry = entries[0]

        if last_entry.entry_type == EntryType.CLOCK_IN:
            duration = (datetime.utcnow() - last_entry.timestamp).total_seconds() / 3600
            return {
                "clocked_in": True,
                "clock_in_time": last_entry.timestamp.isoformat(),
                "current_duration_hours": round(duration, 2)
            }

        return {
            "clocked_in": False,
            "last_clock_out": last_entry.timestamp.isoformat()
        }

    # ===== Entrées de temps =====

    def create_time_entry(
        self,
        user_id: str,
        entry_date: date,
        duration_hours: Decimal,
        *,
        user_name: str = "",
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        project_id: str = "",
        task_id: str = "",
        description: str = "",
        billable_type: Optional[BillableType] = None,
        clock_in_id: Optional[str] = None,
        clock_out_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TimeEntry:
        """Créer une entrée de temps."""
        entry_id = str(uuid.uuid4())

        # Déterminer le taux horaire et type facturable
        hourly_rate = Decimal("0")
        if not billable_type:
            billable_type = BillableType.NON_BILLABLE

        if project_id:
            project = self._projects.get(project_id)
            if project:
                hourly_rate = project.hourly_rate
                if not billable_type:
                    billable_type = project.billable_default

        if task_id:
            task = self._tasks.get(task_id)
            if task:
                if task.hourly_rate:
                    hourly_rate = task.hourly_rate
                billable_type = task.billable_type

        # Calculer montant facturable
        billable_amount = Decimal("0")
        if billable_type == BillableType.BILLABLE:
            billable_amount = duration_hours * hourly_rate

        # Calculer heures sup
        policy = self.get_default_policy()
        overtime_hours = Decimal("0")
        overtime_type = OvertimeType.REGULAR
        overtime_multiplier = Decimal("1")

        if policy and duration_hours > policy.overtime_after_daily:
            overtime_hours = duration_hours - policy.overtime_after_daily
            overtime_type = OvertimeType.OVERTIME_1_5
            overtime_multiplier = policy.overtime_multiplier

        entry = TimeEntry(
            id=entry_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            user_name=user_name,
            entry_date=entry_date,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            project_id=project_id,
            task_id=task_id,
            description=description,
            billable_type=billable_type,
            hourly_rate=hourly_rate,
            billable_amount=billable_amount,
            overtime_type=overtime_type,
            overtime_hours=overtime_hours,
            overtime_multiplier=overtime_multiplier,
            clock_in_id=clock_in_id,
            clock_out_id=clock_out_id,
            tags=tags or []
        )

        self._time_entries[entry_id] = entry

        # Mettre à jour les totaux du projet
        if project_id:
            project = self._projects.get(project_id)
            if project:
                project.total_hours += duration_hours
                if billable_type == BillableType.BILLABLE:
                    project.billable_hours += duration_hours
                if project.budget_hours:
                    project.remaining_budget_hours = project.budget_hours - project.total_hours

        # Mettre à jour les totaux de la tâche
        if task_id:
            task = self._tasks.get(task_id)
            if task:
                task.actual_hours += duration_hours

        return entry

    def update_time_entry(
        self,
        entry_id: str,
        **kwargs
    ) -> Optional[TimeEntry]:
        """Mettre à jour une entrée de temps."""
        entry = self._time_entries.get(entry_id)
        if not entry or entry.tenant_id != self.tenant_id:
            return None

        if entry.status != TimeEntryStatus.PENDING:
            return None

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        # Recalculer montant
        if entry.billable_type == BillableType.BILLABLE:
            entry.billable_amount = entry.duration_hours * entry.hourly_rate
        else:
            entry.billable_amount = Decimal("0")

        entry.updated_at = datetime.utcnow()
        return entry

    def approve_time_entry(
        self,
        entry_id: str,
        approved_by: str
    ) -> Optional[TimeEntry]:
        """Approuver une entrée de temps."""
        entry = self._time_entries.get(entry_id)
        if not entry or entry.tenant_id != self.tenant_id:
            return None

        entry.status = TimeEntryStatus.APPROVED
        entry.approved_by = approved_by
        entry.approved_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()

        return entry

    def reject_time_entry(
        self,
        entry_id: str,
        rejected_by: str,
        reason: str
    ) -> Optional[TimeEntry]:
        """Rejeter une entrée de temps."""
        entry = self._time_entries.get(entry_id)
        if not entry or entry.tenant_id != self.tenant_id:
            return None

        entry.status = TimeEntryStatus.REJECTED
        entry.approved_by = rejected_by
        entry.approved_at = datetime.utcnow()
        entry.rejection_reason = reason
        entry.updated_at = datetime.utcnow()

        return entry

    def get_time_entry(self, entry_id: str) -> Optional[TimeEntry]:
        """Récupérer une entrée de temps."""
        entry = self._time_entries.get(entry_id)
        if entry and entry.tenant_id == self.tenant_id:
            return entry
        return None

    def list_time_entries(
        self,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[TimeEntryStatus] = None
    ) -> List[TimeEntry]:
        """Lister les entrées de temps."""
        entries = [
            e for e in self._time_entries.values()
            if e.tenant_id == self.tenant_id
        ]

        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        if project_id:
            entries = [e for e in entries if e.project_id == project_id]

        if start_date:
            entries = [e for e in entries if e.entry_date >= start_date]

        if end_date:
            entries = [e for e in entries if e.entry_date <= end_date]

        if status:
            entries = [e for e in entries if e.status == status]

        return sorted(entries, key=lambda x: (x.entry_date, x.start_time or time(0, 0)))

    # ===== Feuilles de temps =====

    def create_timesheet(
        self,
        user_id: str,
        period_start: date,
        period_end: date,
        user_name: str = ""
    ) -> Timesheet:
        """Créer une feuille de temps."""
        timesheet_id = str(uuid.uuid4())

        # Récupérer les entrées de la période
        entries = self.list_time_entries(
            user_id=user_id,
            start_date=period_start,
            end_date=period_end
        )

        entry_ids = [e.id for e in entries]

        # Calculer les totaux
        total_hours = sum(e.duration_hours for e in entries)
        overtime_hours = sum(e.overtime_hours for e in entries)
        regular_hours = total_hours - overtime_hours
        billable_hours = sum(e.duration_hours for e in entries
                            if e.billable_type == BillableType.BILLABLE)
        non_billable_hours = total_hours - billable_hours

        # Totaux par jour
        daily_totals: Dict[str, Decimal] = {}
        for entry in entries:
            day = entry.entry_date.isoformat()
            daily_totals[day] = daily_totals.get(day, Decimal("0")) + entry.duration_hours

        timesheet = Timesheet(
            id=timesheet_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            user_name=user_name,
            period_start=period_start,
            period_end=period_end,
            entry_ids=entry_ids,
            total_hours=total_hours,
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            billable_hours=billable_hours,
            non_billable_hours=non_billable_hours,
            daily_totals=daily_totals
        )

        # Lier les entrées à la timesheet
        for entry in entries:
            entry.timesheet_id = timesheet_id

        self._timesheets[timesheet_id] = timesheet
        return timesheet

    def submit_timesheet(
        self,
        timesheet_id: str
    ) -> Optional[Timesheet]:
        """Soumettre une feuille de temps."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet or timesheet.tenant_id != self.tenant_id:
            return None

        if timesheet.status != TimesheetStatus.DRAFT:
            return None

        timesheet.status = TimesheetStatus.SUBMITTED
        timesheet.submitted_at = datetime.utcnow()
        timesheet.updated_at = datetime.utcnow()

        return timesheet

    def approve_timesheet(
        self,
        timesheet_id: str,
        approved_by: str
    ) -> Optional[Timesheet]:
        """Approuver une feuille de temps."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet or timesheet.tenant_id != self.tenant_id:
            return None

        if timesheet.status != TimesheetStatus.SUBMITTED:
            return None

        timesheet.status = TimesheetStatus.APPROVED
        timesheet.approved_by = approved_by
        timesheet.approved_at = datetime.utcnow()
        timesheet.updated_at = datetime.utcnow()

        # Approuver toutes les entrées
        for entry_id in timesheet.entry_ids:
            entry = self._time_entries.get(entry_id)
            if entry and entry.status == TimeEntryStatus.PENDING:
                entry.status = TimeEntryStatus.APPROVED
                entry.approved_by = approved_by
                entry.approved_at = timesheet.approved_at

        return timesheet

    def get_timesheet(self, timesheet_id: str) -> Optional[Timesheet]:
        """Récupérer une feuille de temps."""
        ts = self._timesheets.get(timesheet_id)
        if ts and ts.tenant_id == self.tenant_id:
            return ts
        return None

    # ===== Absences =====

    def request_absence(
        self,
        user_id: str,
        absence_type: AbsenceType,
        start_date: date,
        end_date: date,
        *,
        user_name: str = "",
        start_half_day: bool = False,
        end_half_day: bool = False,
        reason: str = ""
    ) -> Absence:
        """Demander une absence."""
        absence_id = str(uuid.uuid4())

        # Calculer le nombre de jours
        total_days = Decimal("0")
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Jours ouvrés
                if current == start_date and start_half_day:
                    total_days += Decimal("0.5")
                elif current == end_date and end_half_day:
                    total_days += Decimal("0.5")
                else:
                    total_days += Decimal("1")
            current += timedelta(days=1)

        absence = Absence(
            id=absence_id,
            tenant_id=self.tenant_id,
            user_id=user_id,
            user_name=user_name,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
            total_days=total_days,
            reason=reason
        )

        self._absences[absence_id] = absence
        return absence

    def approve_absence(
        self,
        absence_id: str,
        approved_by: str
    ) -> Optional[Absence]:
        """Approuver une absence."""
        absence = self._absences.get(absence_id)
        if not absence or absence.tenant_id != self.tenant_id:
            return None

        absence.status = "approved"
        absence.approved_by = approved_by
        absence.approved_at = datetime.utcnow()

        return absence

    def get_user_absences(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Absence]:
        """Récupérer les absences d'un utilisateur."""
        absences = [
            a for a in self._absences.values()
            if a.user_id == user_id and a.tenant_id == self.tenant_id
        ]

        if start_date:
            absences = [a for a in absences if a.end_date >= start_date]

        if end_date:
            absences = [a for a in absences if a.start_date <= end_date]

        return sorted(absences, key=lambda x: x.start_date)

    # ===== Soldes =====

    def get_user_balance(
        self,
        user_id: str,
        period_start: date,
        period_end: date
    ) -> UserTimeBalance:
        """Calculer le solde de temps d'un utilisateur."""
        policy = self.get_default_policy()

        # Heures attendues
        expected = Decimal("0")
        if policy:
            current = period_start
            while current <= period_end:
                if current.weekday() in policy.working_days:
                    expected += policy.standard_hours_per_day
                current += timedelta(days=1)

        # Heures travaillées
        entries = self.list_time_entries(
            user_id=user_id,
            start_date=period_start,
            end_date=period_end
        )

        worked = sum(e.duration_hours for e in entries)
        overtime = sum(e.overtime_hours for e in entries)

        # Par projet
        by_project: Dict[str, Decimal] = {}
        for entry in entries:
            if entry.project_id:
                project = self._projects.get(entry.project_id)
                name = project.name if project else entry.project_id
                by_project[name] = by_project.get(name, Decimal("0")) + entry.duration_hours

        # Absences
        absences = self.get_user_absences(user_id, period_start, period_end)
        vacation_used = sum(a.total_days for a in absences
                           if a.absence_type == AbsenceType.VACATION and a.status == "approved")
        sick_used = sum(a.total_days for a in absences
                       if a.absence_type == AbsenceType.SICK and a.status == "approved")

        return UserTimeBalance(
            user_id=user_id,
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end,
            expected_hours=expected,
            worked_hours=worked,
            balance_hours=worked - expected,
            overtime_earned=overtime,
            overtime_balance=overtime,
            vacation_used=vacation_used,
            sick_used=sick_used,
            hours_by_project=by_project
        )

    # ===== Rapports =====

    def generate_report(
        self,
        period_start: date,
        period_end: date,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> TimeReport:
        """Générer un rapport de temps."""
        entries = self.list_time_entries(
            user_id=user_id,
            project_id=project_id,
            start_date=period_start,
            end_date=period_end
        )

        # Totaux
        total = sum(e.duration_hours for e in entries)
        billable = sum(e.duration_hours for e in entries if e.billable_type == BillableType.BILLABLE)
        non_billable = total - billable
        overtime = sum(e.overtime_hours for e in entries)

        # Montant
        billable_amount = sum(e.billable_amount for e in entries)
        avg_rate = billable_amount / billable if billable > 0 else Decimal("0")

        # Par utilisateur
        by_user: Dict[str, Decimal] = {}
        for entry in entries:
            by_user[entry.user_name or entry.user_id] = (
                by_user.get(entry.user_name or entry.user_id, Decimal("0")) +
                entry.duration_hours
            )

        # Par projet
        by_project: Dict[str, Decimal] = {}
        by_client: Dict[str, Decimal] = {}
        for entry in entries:
            if entry.project_id:
                project = self._projects.get(entry.project_id)
                if project:
                    by_project[project.name] = by_project.get(project.name, Decimal("0")) + entry.duration_hours
                    if project.client_name:
                        by_client[project.client_name] = (
                            by_client.get(project.client_name, Decimal("0")) +
                            entry.duration_hours
                        )

        # Par jour
        by_day: Dict[str, Decimal] = {}
        for entry in entries:
            day = entry.entry_date.isoformat()
            by_day[day] = by_day.get(day, Decimal("0")) + entry.duration_hours

        # Taux d'utilisation (vs heures attendues)
        policy = self.get_default_policy()
        expected = Decimal("0")
        if policy:
            current = period_start
            while current <= period_end:
                if current.weekday() in policy.working_days:
                    expected += policy.standard_hours_per_day
                current += timedelta(days=1)

        utilization = (total / expected * 100) if expected > 0 else Decimal("0")
        billability = (billable / total * 100) if total > 0 else Decimal("0")

        return TimeReport(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end,
            total_hours=total,
            billable_hours=billable,
            non_billable_hours=non_billable,
            overtime_hours=overtime,
            billable_amount=billable_amount,
            average_hourly_rate=avg_rate,
            utilization_rate=utilization,
            billability_rate=billability,
            hours_by_user=by_user,
            hours_by_project=by_project,
            hours_by_client=by_client,
            hours_by_day=by_day
        )


# ============== Factory ==============

def create_timetracking_service(tenant_id: str) -> TimeTrackingService:
    """Factory pour créer une instance du service."""
    return TimeTrackingService(tenant_id)
