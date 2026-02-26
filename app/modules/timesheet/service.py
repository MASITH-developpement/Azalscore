"""
Module de Gestion des Temps et Activités (Timesheet) - GAP-034

Fonctionnalités complètes de suivi du temps de travail:
- Saisie des temps par projet/tâche/client
- Feuilles de temps hebdomadaires/mensuelles
- Workflow de validation manager
- Calcul automatique des heures supplémentaires
- Gestion des absences et congés
- Intégration paie
- Facturation temps passé
- Reporting et analytics

Conformité:
- Code du travail (durées maximales, repos)
- Convention collective
- Accord d'entreprise sur le temps de travail

Architecture multi-tenant avec isolation stricte.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import calendar


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class TimeEntryType(Enum):
    """Type d'entrée de temps."""
    WORK = "work"  # Travail effectif
    MEETING = "meeting"  # Réunion
    TRAVEL = "travel"  # Déplacement
    TRAINING = "training"  # Formation
    SUPPORT = "support"  # Support/maintenance
    ADMINISTRATIVE = "administrative"  # Administratif
    OTHER = "other"  # Autre


class AbsenceType(Enum):
    """Type d'absence."""
    PAID_LEAVE = "paid_leave"  # Congés payés
    RTT = "rtt"  # RTT
    SICK_LEAVE = "sick_leave"  # Maladie
    MATERNITY = "maternity"  # Maternité
    PATERNITY = "paternity"  # Paternité
    UNPAID_LEAVE = "unpaid_leave"  # Congé sans solde
    FAMILY_EVENT = "family_event"  # Événement familial
    REMOTE_WORK = "remote_work"  # Télétravail
    COMPENSATORY_REST = "compensatory_rest"  # Repos compensateur
    PUBLIC_HOLIDAY = "public_holiday"  # Jour férié
    OTHER = "other"  # Autre


class TimesheetStatus(Enum):
    """Statut d'une feuille de temps."""
    DRAFT = "draft"  # Brouillon
    SUBMITTED = "submitted"  # Soumise
    APPROVED = "approved"  # Validée
    REJECTED = "rejected"  # Rejetée
    LOCKED = "locked"  # Verrouillée (paie)


class WorkScheduleType(Enum):
    """Type d'horaire de travail."""
    STANDARD_35H = "standard_35h"  # 35h standard
    STANDARD_39H = "standard_39h"  # 39h avec RTT
    FORFAIT_JOURS = "forfait_jours"  # Forfait jours (218j)
    FORFAIT_HEURES = "forfait_heures"  # Forfait heures
    PART_TIME = "part_time"  # Temps partiel
    FLEXIBLE = "flexible"  # Horaires flexibles
    SHIFT = "shift"  # Travail posté


class OvertimeType(Enum):
    """Type d'heures supplémentaires."""
    OVERTIME_25 = "overtime_25"  # Majorées 25%
    OVERTIME_50 = "overtime_50"  # Majorées 50%
    OVERTIME_100 = "overtime_100"  # Majorées 100%
    NIGHT_WORK = "night_work"  # Travail de nuit
    SUNDAY_WORK = "sunday_work"  # Travail dimanche
    HOLIDAY_WORK = "holiday_work"  # Travail jour férié


# ============================================================================
# CONSTANTES LÉGALES
# ============================================================================

# Durées légales (Code du travail)
LEGAL_LIMITS = {
    "daily_max_hours": Decimal("10"),  # Maximum 10h/jour
    "weekly_max_hours": Decimal("48"),  # Maximum 48h/semaine
    "weekly_max_average_12w": Decimal("44"),  # Moyenne 44h sur 12 semaines
    "daily_rest_hours": Decimal("11"),  # Repos quotidien minimum
    "weekly_rest_hours": Decimal("35"),  # Repos hebdomadaire minimum
    "standard_weekly_hours": Decimal("35"),  # Durée légale
    "overtime_threshold": Decimal("35"),  # Seuil heures sup
    "annual_working_days_forfait": 218,  # Forfait jours
}

# Majoration heures supplémentaires (légal)
OVERTIME_RATES = {
    OvertimeType.OVERTIME_25: Decimal("1.25"),  # 8 premières heures
    OvertimeType.OVERTIME_50: Decimal("1.50"),  # Au-delà
    OvertimeType.OVERTIME_100: Decimal("2.00"),  # Exceptionnel
    OvertimeType.NIGHT_WORK: Decimal("1.25"),  # 21h-6h
    OvertimeType.SUNDAY_WORK: Decimal("2.00"),  # Dimanche
    OvertimeType.HOLIDAY_WORK: Decimal("2.00"),  # Jour férié
}

# Jours fériés France 2024
PUBLIC_HOLIDAYS_FR_2024 = [
    date(2024, 1, 1),   # Jour de l'an
    date(2024, 4, 1),   # Lundi de Pâques
    date(2024, 5, 1),   # Fête du travail
    date(2024, 5, 8),   # Victoire 1945
    date(2024, 5, 9),   # Ascension
    date(2024, 5, 20),  # Lundi de Pentecôte
    date(2024, 7, 14),  # Fête nationale
    date(2024, 8, 15),  # Assomption
    date(2024, 11, 1),  # Toussaint
    date(2024, 11, 11), # Armistice
    date(2024, 12, 25), # Noël
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class WorkSchedule:
    """Planning de travail d'un employé."""
    id: str
    employee_id: str
    schedule_type: WorkScheduleType

    # Horaires standard
    weekly_hours: Decimal = Decimal("35")
    daily_hours: Decimal = Decimal("7")

    # Jours travaillés (0=Lundi, 6=Dimanche)
    working_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])

    # Horaires par jour
    start_time: time = time(9, 0)
    end_time: time = time(17, 0)
    lunch_break_minutes: int = 60

    # Forfait jours
    annual_days: int = 218
    rtt_days: int = 0

    # Flexibilité
    flex_start_min: Optional[time] = None  # Plage arrivée min
    flex_start_max: Optional[time] = None  # Plage arrivée max

    # Validité
    effective_from: date = field(default_factory=date.today)
    effective_to: Optional[date] = None


@dataclass
class TimeEntry:
    """Entrée de temps."""
    id: str
    employee_id: str
    entry_date: date

    # Horaires
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: int = 0

    # Durée (si pas d'horaires précis)
    duration_hours: Decimal = Decimal("0")
    duration_minutes: int = 0

    # Classification
    entry_type: TimeEntryType = TimeEntryType.WORK

    # Affectation
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    client_id: Optional[str] = None
    activity_code: Optional[str] = None

    # Description
    description: Optional[str] = None
    notes: Optional[str] = None

    # Facturation
    billable: bool = False
    billing_rate: Optional[Decimal] = None
    billed: bool = False

    # Validation
    is_validated: bool = False
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: str = "manual"  # manual, timer, import

    def calculate_duration(self) -> Decimal:
        """Calcule la durée en heures."""
        if self.start_time and self.end_time:
            start_dt = datetime.combine(self.entry_date, self.start_time)
            end_dt = datetime.combine(self.entry_date, self.end_time)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            delta = end_dt - start_dt
            total_minutes = delta.total_seconds() / 60 - self.break_minutes
            return Decimal(str(total_minutes / 60)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            return self.duration_hours + Decimal(str(self.duration_minutes)) / 60


@dataclass
class AbsenceEntry:
    """Entrée d'absence."""
    id: str
    employee_id: str
    absence_type: AbsenceType

    # Période
    start_date: date
    end_date: date
    start_half_day: bool = False  # Début après-midi
    end_half_day: bool = False  # Fin matin

    # Durée
    days_count: Decimal = Decimal("0")
    hours_count: Decimal = Decimal("0")

    # Justification
    reason: Optional[str] = None
    attachment_id: Optional[str] = None

    # Validation
    status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)

    def calculate_days(self, working_days: List[int]) -> Decimal:
        """Calcule le nombre de jours ouvrés."""
        total = Decimal("0")
        current = self.start_date

        while current <= self.end_date:
            if current.weekday() in working_days:
                if current == self.start_date and self.start_half_day:
                    total += Decimal("0.5")
                elif current == self.end_date and self.end_half_day:
                    total += Decimal("0.5")
                else:
                    total += Decimal("1")
            current += timedelta(days=1)

        return total


@dataclass
class Timesheet:
    """Feuille de temps (hebdomadaire ou mensuelle)."""
    id: str
    tenant_id: str
    employee_id: str

    # Période
    period_type: str = "weekly"  # weekly, monthly
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)

    # Entrées
    time_entries: List[TimeEntry] = field(default_factory=list)
    absence_entries: List[AbsenceEntry] = field(default_factory=list)

    # Totaux
    total_worked_hours: Decimal = Decimal("0")
    total_overtime_hours: Decimal = Decimal("0")
    total_billable_hours: Decimal = Decimal("0")
    total_absence_days: Decimal = Decimal("0")

    # Statut
    status: TimesheetStatus = TimesheetStatus.DRAFT
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Commentaires
    employee_comments: Optional[str] = None
    manager_comments: Optional[str] = None

    # Dates système
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def recalculate_totals(self, schedule: WorkSchedule):
        """Recalcule tous les totaux."""
        self.total_worked_hours = sum(
            e.calculate_duration() for e in self.time_entries
        )

        self.total_billable_hours = sum(
            e.calculate_duration() for e in self.time_entries
            if e.billable
        )

        self.total_absence_days = sum(
            a.days_count for a in self.absence_entries
            if a.status == "approved"
        )

        # Calcul heures supplémentaires
        expected_hours = self._calculate_expected_hours(schedule)
        if self.total_worked_hours > expected_hours:
            self.total_overtime_hours = self.total_worked_hours - expected_hours
        else:
            self.total_overtime_hours = Decimal("0")

    def _calculate_expected_hours(self, schedule: WorkSchedule) -> Decimal:
        """Calcule les heures attendues pour la période."""
        working_days = 0
        current = self.period_start

        while current <= self.period_end:
            if current.weekday() in schedule.working_days:
                # Vérifier si absence
                is_absent = any(
                    a.start_date <= current <= a.end_date
                    for a in self.absence_entries
                    if a.status == "approved"
                )
                if not is_absent:
                    working_days += 1
            current += timedelta(days=1)

        return Decimal(str(working_days)) * schedule.daily_hours


@dataclass
class OvertimeCalculation:
    """Calcul des heures supplémentaires."""
    timesheet_id: str
    calculation_date: date

    # Heures par type
    overtime_25_hours: Decimal = Decimal("0")  # 8 premières HS
    overtime_50_hours: Decimal = Decimal("0")  # Au-delà
    night_hours: Decimal = Decimal("0")
    sunday_hours: Decimal = Decimal("0")
    holiday_hours: Decimal = Decimal("0")

    # Montants (si taux horaire connu)
    hourly_rate: Optional[Decimal] = None
    overtime_25_amount: Decimal = Decimal("0")
    overtime_50_amount: Decimal = Decimal("0")
    total_overtime_amount: Decimal = Decimal("0")

    # Repos compensateur
    compensatory_rest_hours: Decimal = Decimal("0")


@dataclass
class Timer:
    """Chronomètre pour saisie temps réel."""
    id: str
    employee_id: str
    started_at: datetime
    stopped_at: Optional[datetime] = None

    # Affectation
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    description: Optional[str] = None

    # Pauses
    pauses: List[Dict[str, datetime]] = field(default_factory=list)
    total_pause_seconds: int = 0

    # Statut
    is_running: bool = True
    is_paused: bool = False

    def get_elapsed_seconds(self) -> int:
        """Retourne le temps écoulé en secondes."""
        end = self.stopped_at or datetime.now()
        elapsed = (end - self.started_at).total_seconds()
        return int(elapsed - self.total_pause_seconds)

    def get_elapsed_hours(self) -> Decimal:
        """Retourne le temps écoulé en heures."""
        return Decimal(str(self.get_elapsed_seconds() / 3600)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass
class LeaveBalance:
    """Solde de congés."""
    employee_id: str
    year: int
    balance_type: AbsenceType

    # Acquis
    earned_days: Decimal = Decimal("0")
    carried_over_days: Decimal = Decimal("0")
    adjustment_days: Decimal = Decimal("0")

    # Utilisés
    used_days: Decimal = Decimal("0")
    pending_days: Decimal = Decimal("0")  # Demandes en attente

    # Solde
    @property
    def available_days(self) -> Decimal:
        return (
            self.earned_days +
            self.carried_over_days +
            self.adjustment_days -
            self.used_days -
            self.pending_days
        )


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class TimesheetService:
    """
    Service de gestion des temps et activités.

    Gère:
    - Saisie et validation des temps
    - Calcul des heures supplémentaires
    - Gestion des absences
    - Intégration paie
    - Reporting
    """

    def __init__(
        self,
        tenant_id: str,
        default_schedule_type: WorkScheduleType = WorkScheduleType.STANDARD_35H
    ):
        self.tenant_id = tenant_id
        self.default_schedule_type = default_schedule_type

        # Stockage (à remplacer par DB)
        self._schedules: Dict[str, WorkSchedule] = {}
        self._timesheets: Dict[str, Timesheet] = {}
        self._time_entries: Dict[str, TimeEntry] = {}
        self._absences: Dict[str, AbsenceEntry] = {}
        self._timers: Dict[str, Timer] = {}
        self._leave_balances: Dict[str, LeaveBalance] = {}

    # ========================================================================
    # GESTION DES PLANNINGS
    # ========================================================================

    def create_work_schedule(
        self,
        employee_id: str,
        schedule_type: WorkScheduleType,
        weekly_hours: Decimal = Decimal("35"),
        working_days: Optional[List[int]] = None,
        start_time: time = time(9, 0),
        end_time: time = time(17, 0),
        effective_from: Optional[date] = None
    ) -> WorkSchedule:
        """Crée un planning de travail pour un employé."""
        schedule = WorkSchedule(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            schedule_type=schedule_type,
            weekly_hours=weekly_hours,
            daily_hours=weekly_hours / Decimal(str(len(working_days or [0,1,2,3,4]))),
            working_days=working_days or [0, 1, 2, 3, 4],
            start_time=start_time,
            end_time=end_time,
            effective_from=effective_from or date.today()
        )

        # RTT pour 39h
        if schedule_type == WorkScheduleType.STANDARD_39H:
            schedule.weekly_hours = Decimal("39")
            schedule.rtt_days = 23  # Environ 23 RTT/an

        # Forfait jours
        if schedule_type == WorkScheduleType.FORFAIT_JOURS:
            schedule.annual_days = 218

        self._schedules[schedule.id] = schedule
        return schedule

    def get_employee_schedule(
        self,
        employee_id: str,
        as_of_date: Optional[date] = None
    ) -> Optional[WorkSchedule]:
        """Récupère le planning actif d'un employé."""
        as_of = as_of_date or date.today()

        for schedule in self._schedules.values():
            if schedule.employee_id != employee_id:
                continue
            if schedule.effective_from > as_of:
                continue
            if schedule.effective_to and schedule.effective_to < as_of:
                continue
            return schedule

        return None

    # ========================================================================
    # SAISIE DES TEMPS
    # ========================================================================

    def create_time_entry(
        self,
        employee_id: str,
        entry_date: date,
        duration_hours: Optional[Decimal] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        break_minutes: int = 0,
        entry_type: TimeEntryType = TimeEntryType.WORK,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        client_id: Optional[str] = None,
        description: Optional[str] = None,
        billable: bool = False,
        billing_rate: Optional[Decimal] = None
    ) -> TimeEntry:
        """Crée une entrée de temps."""
        # Vérifier les limites légales
        self._check_legal_limits(employee_id, entry_date, duration_hours or Decimal("0"))

        entry = TimeEntry(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            entry_date=entry_date,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
            duration_hours=duration_hours or Decimal("0"),
            entry_type=entry_type,
            project_id=project_id,
            task_id=task_id,
            client_id=client_id,
            description=description,
            billable=billable,
            billing_rate=billing_rate
        )

        self._time_entries[entry.id] = entry

        # Ajouter à la feuille de temps si existante
        timesheet = self._get_or_create_timesheet(employee_id, entry_date)
        timesheet.time_entries.append(entry)

        return entry

    def _check_legal_limits(
        self,
        employee_id: str,
        entry_date: date,
        additional_hours: Decimal
    ):
        """Vérifie les limites légales de temps de travail."""
        # Heures déjà travaillées ce jour
        daily_hours = self._get_daily_hours(employee_id, entry_date)
        new_daily = daily_hours + additional_hours

        if new_daily > LEGAL_LIMITS["daily_max_hours"]:
            raise ValueError(
                f"Dépassement durée maximale journalière: "
                f"{new_daily}h > {LEGAL_LIMITS['daily_max_hours']}h"
            )

        # Heures cette semaine
        week_start = entry_date - timedelta(days=entry_date.weekday())
        weekly_hours = self._get_weekly_hours(employee_id, week_start)
        new_weekly = weekly_hours + additional_hours

        if new_weekly > LEGAL_LIMITS["weekly_max_hours"]:
            raise ValueError(
                f"Dépassement durée maximale hebdomadaire: "
                f"{new_weekly}h > {LEGAL_LIMITS['weekly_max_hours']}h"
            )

    def _get_daily_hours(self, employee_id: str, entry_date: date) -> Decimal:
        """Calcule les heures travaillées un jour donné."""
        return sum(
            e.calculate_duration()
            for e in self._time_entries.values()
            if e.employee_id == employee_id and e.entry_date == entry_date
        )

    def _get_weekly_hours(self, employee_id: str, week_start: date) -> Decimal:
        """Calcule les heures travaillées une semaine donnée."""
        week_end = week_start + timedelta(days=6)
        return sum(
            e.calculate_duration()
            for e in self._time_entries.values()
            if e.employee_id == employee_id
            and week_start <= e.entry_date <= week_end
        )

    # ========================================================================
    # CHRONOMÈTRE
    # ========================================================================

    def start_timer(
        self,
        employee_id: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Timer:
        """Démarre un chronomètre."""
        # Arrêter les timers existants
        for timer in self._timers.values():
            if timer.employee_id == employee_id and timer.is_running:
                self.stop_timer(timer.id)

        timer = Timer(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            started_at=datetime.now(),
            project_id=project_id,
            task_id=task_id,
            description=description
        )

        self._timers[timer.id] = timer
        return timer

    def pause_timer(self, timer_id: str) -> Timer:
        """Met en pause un chronomètre."""
        timer = self._timers.get(timer_id)
        if not timer:
            raise ValueError(f"Timer {timer_id} non trouvé")

        if timer.is_paused:
            raise ValueError("Timer déjà en pause")

        timer.pauses.append({"start": datetime.now()})
        timer.is_paused = True

        return timer

    def resume_timer(self, timer_id: str) -> Timer:
        """Reprend un chronomètre."""
        timer = self._timers.get(timer_id)
        if not timer:
            raise ValueError(f"Timer {timer_id} non trouvé")

        if not timer.is_paused:
            raise ValueError("Timer n'est pas en pause")

        if timer.pauses:
            last_pause = timer.pauses[-1]
            if "end" not in last_pause:
                last_pause["end"] = datetime.now()
                pause_duration = (
                    last_pause["end"] - last_pause["start"]
                ).total_seconds()
                timer.total_pause_seconds += int(pause_duration)

        timer.is_paused = False
        return timer

    def stop_timer(
        self,
        timer_id: str,
        create_entry: bool = True
    ) -> Tuple[Timer, Optional[TimeEntry]]:
        """Arrête un chronomètre et crée optionnellement une entrée."""
        timer = self._timers.get(timer_id)
        if not timer:
            raise ValueError(f"Timer {timer_id} non trouvé")

        # Finaliser les pauses
        if timer.is_paused and timer.pauses:
            last_pause = timer.pauses[-1]
            if "end" not in last_pause:
                last_pause["end"] = datetime.now()
                pause_duration = (
                    last_pause["end"] - last_pause["start"]
                ).total_seconds()
                timer.total_pause_seconds += int(pause_duration)

        timer.stopped_at = datetime.now()
        timer.is_running = False
        timer.is_paused = False

        entry = None
        if create_entry:
            duration = timer.get_elapsed_hours()
            if duration > Decimal("0"):
                entry = self.create_time_entry(
                    employee_id=timer.employee_id,
                    entry_date=timer.started_at.date(),
                    start_time=timer.started_at.time(),
                    end_time=timer.stopped_at.time(),
                    break_minutes=timer.total_pause_seconds // 60,
                    project_id=timer.project_id,
                    task_id=timer.task_id,
                    description=timer.description,
                    entry_type=TimeEntryType.WORK
                )

        return timer, entry

    # ========================================================================
    # FEUILLES DE TEMPS
    # ========================================================================

    def _get_or_create_timesheet(
        self,
        employee_id: str,
        entry_date: date,
        period_type: str = "weekly"
    ) -> Timesheet:
        """Récupère ou crée une feuille de temps."""
        # Calculer la période
        if period_type == "weekly":
            period_start = entry_date - timedelta(days=entry_date.weekday())
            period_end = period_start + timedelta(days=6)
        else:  # monthly
            period_start = entry_date.replace(day=1)
            last_day = calendar.monthrange(entry_date.year, entry_date.month)[1]
            period_end = entry_date.replace(day=last_day)

        # Chercher existante
        for ts in self._timesheets.values():
            if (ts.employee_id == employee_id and
                ts.period_start == period_start and
                ts.period_type == period_type):
                return ts

        # Créer nouvelle
        timesheet = Timesheet(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end
        )

        self._timesheets[timesheet.id] = timesheet
        return timesheet

    def get_timesheet(
        self,
        employee_id: str,
        period_start: date,
        period_type: str = "weekly"
    ) -> Optional[Timesheet]:
        """Récupère une feuille de temps."""
        for ts in self._timesheets.values():
            if (ts.employee_id == employee_id and
                ts.period_start == period_start and
                ts.period_type == period_type):
                return ts
        return None

    def submit_timesheet(
        self,
        timesheet_id: str,
        comments: Optional[str] = None
    ) -> Timesheet:
        """Soumet une feuille de temps pour validation."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet:
            raise ValueError(f"Feuille de temps {timesheet_id} non trouvée")

        if timesheet.status != TimesheetStatus.DRAFT:
            raise ValueError("Feuille de temps déjà soumise")

        # Recalculer les totaux
        schedule = self.get_employee_schedule(
            timesheet.employee_id,
            timesheet.period_start
        )
        if schedule:
            timesheet.recalculate_totals(schedule)

        timesheet.status = TimesheetStatus.SUBMITTED
        timesheet.submitted_at = datetime.now()
        timesheet.employee_comments = comments
        timesheet.updated_at = datetime.now()

        return timesheet

    def approve_timesheet(
        self,
        timesheet_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Timesheet:
        """Approuve une feuille de temps."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet:
            raise ValueError(f"Feuille de temps {timesheet_id} non trouvée")

        if timesheet.status != TimesheetStatus.SUBMITTED:
            raise ValueError("Feuille de temps non soumise")

        timesheet.status = TimesheetStatus.APPROVED
        timesheet.approved_at = datetime.now()
        timesheet.approved_by = approver_id
        timesheet.manager_comments = comments
        timesheet.updated_at = datetime.now()

        # Valider les entrées
        for entry in timesheet.time_entries:
            entry.is_validated = True
            entry.validated_by = approver_id
            entry.validated_at = datetime.now()

        return timesheet

    def reject_timesheet(
        self,
        timesheet_id: str,
        approver_id: str,
        reason: str
    ) -> Timesheet:
        """Rejette une feuille de temps."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet:
            raise ValueError(f"Feuille de temps {timesheet_id} non trouvée")

        timesheet.status = TimesheetStatus.REJECTED
        timesheet.rejection_reason = reason
        timesheet.manager_comments = reason
        timesheet.updated_at = datetime.now()

        return timesheet

    # ========================================================================
    # HEURES SUPPLÉMENTAIRES
    # ========================================================================

    def calculate_overtime(
        self,
        timesheet_id: str,
        hourly_rate: Optional[Decimal] = None
    ) -> OvertimeCalculation:
        """Calcule les heures supplémentaires d'une feuille de temps."""
        timesheet = self._timesheets.get(timesheet_id)
        if not timesheet:
            raise ValueError(f"Feuille de temps {timesheet_id} non trouvée")

        schedule = self.get_employee_schedule(
            timesheet.employee_id,
            timesheet.period_start
        )

        calculation = OvertimeCalculation(
            timesheet_id=timesheet_id,
            calculation_date=date.today(),
            hourly_rate=hourly_rate
        )

        # Heures par jour
        for entry in timesheet.time_entries:
            duration = entry.calculate_duration()

            # Travail dimanche
            if entry.entry_date.weekday() == 6:
                calculation.sunday_hours += duration
                continue

            # Jour férié
            if entry.entry_date in PUBLIC_HOLIDAYS_FR_2024:
                calculation.holiday_hours += duration
                continue

            # Travail de nuit (21h-6h)
            if entry.start_time and entry.end_time:
                night_start = time(21, 0)
                night_end = time(6, 0)
                if entry.start_time >= night_start or entry.end_time <= night_end:
                    calculation.night_hours += duration

        # Heures supplémentaires classiques
        weekly_hours = timesheet.total_worked_hours
        threshold = schedule.weekly_hours if schedule else Decimal("35")

        if weekly_hours > threshold:
            overtime = weekly_hours - threshold

            # 8 premières heures à 25%
            if overtime <= 8:
                calculation.overtime_25_hours = overtime
            else:
                calculation.overtime_25_hours = Decimal("8")
                calculation.overtime_50_hours = overtime - Decimal("8")

        # Calcul des montants
        if hourly_rate:
            calculation.overtime_25_amount = (
                calculation.overtime_25_hours * hourly_rate *
                OVERTIME_RATES[OvertimeType.OVERTIME_25]
            )
            calculation.overtime_50_amount = (
                calculation.overtime_50_hours * hourly_rate *
                OVERTIME_RATES[OvertimeType.OVERTIME_50]
            )
            calculation.total_overtime_amount = (
                calculation.overtime_25_amount +
                calculation.overtime_50_amount +
                calculation.sunday_hours * hourly_rate *
                OVERTIME_RATES[OvertimeType.SUNDAY_WORK] +
                calculation.holiday_hours * hourly_rate *
                OVERTIME_RATES[OvertimeType.HOLIDAY_WORK] +
                calculation.night_hours * hourly_rate *
                OVERTIME_RATES[OvertimeType.NIGHT_WORK]
            )

        return calculation

    # ========================================================================
    # ABSENCES ET CONGÉS
    # ========================================================================

    def create_absence_request(
        self,
        employee_id: str,
        absence_type: AbsenceType,
        start_date: date,
        end_date: date,
        start_half_day: bool = False,
        end_half_day: bool = False,
        reason: Optional[str] = None
    ) -> AbsenceEntry:
        """Crée une demande d'absence."""
        schedule = self.get_employee_schedule(employee_id, start_date)
        working_days = schedule.working_days if schedule else [0, 1, 2, 3, 4]

        absence = AbsenceEntry(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
            reason=reason
        )

        # Calculer le nombre de jours
        absence.days_count = absence.calculate_days(working_days)

        # Vérifier le solde
        balance = self._get_leave_balance(employee_id, start_date.year, absence_type)
        if balance and absence.days_count > balance.available_days:
            raise ValueError(
                f"Solde insuffisant: {balance.available_days} jours disponibles, "
                f"{absence.days_count} demandés"
            )

        self._absences[absence.id] = absence

        # Mettre à jour le solde (pending)
        if balance:
            balance.pending_days += absence.days_count

        return absence

    def approve_absence(
        self,
        absence_id: str,
        approver_id: str
    ) -> AbsenceEntry:
        """Approuve une demande d'absence."""
        absence = self._absences.get(absence_id)
        if not absence:
            raise ValueError(f"Absence {absence_id} non trouvée")

        absence.status = "approved"
        absence.approved_by = approver_id
        absence.approved_at = datetime.now()

        # Mettre à jour le solde
        balance = self._get_leave_balance(
            absence.employee_id,
            absence.start_date.year,
            absence.absence_type
        )
        if balance:
            balance.pending_days -= absence.days_count
            balance.used_days += absence.days_count

        # Ajouter aux feuilles de temps
        current = absence.start_date
        while current <= absence.end_date:
            timesheet = self._get_or_create_timesheet(absence.employee_id, current)
            if absence not in timesheet.absence_entries:
                timesheet.absence_entries.append(absence)
            current += timedelta(days=1)

        return absence

    def _get_leave_balance(
        self,
        employee_id: str,
        year: int,
        absence_type: AbsenceType
    ) -> Optional[LeaveBalance]:
        """Récupère le solde de congés."""
        key = f"{employee_id}_{year}_{absence_type.value}"
        return self._leave_balances.get(key)

    def set_leave_balance(
        self,
        employee_id: str,
        year: int,
        absence_type: AbsenceType,
        earned_days: Decimal,
        carried_over_days: Decimal = Decimal("0")
    ) -> LeaveBalance:
        """Définit le solde de congés."""
        key = f"{employee_id}_{year}_{absence_type.value}"

        balance = LeaveBalance(
            employee_id=employee_id,
            year=year,
            balance_type=absence_type,
            earned_days=earned_days,
            carried_over_days=carried_over_days
        )

        self._leave_balances[key] = balance
        return balance

    # ========================================================================
    # EXPORT PAIE
    # ========================================================================

    def export_for_payroll(
        self,
        employee_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """Exporte les données pour la paie."""
        period_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        period_end = date(year, month, last_day)

        # Collecter les feuilles de temps approuvées
        timesheets = [
            ts for ts in self._timesheets.values()
            if ts.employee_id == employee_id
            and ts.period_start >= period_start
            and ts.period_end <= period_end
            and ts.status == TimesheetStatus.APPROVED
        ]

        # Agréger
        total_worked = sum(ts.total_worked_hours for ts in timesheets)
        total_overtime = sum(ts.total_overtime_hours for ts in timesheets)
        total_billable = sum(ts.total_billable_hours for ts in timesheets)

        # Absences
        absences = [
            a for a in self._absences.values()
            if a.employee_id == employee_id
            and a.start_date <= period_end
            and a.end_date >= period_start
            and a.status == "approved"
        ]

        absences_by_type = {}
        for absence in absences:
            atype = absence.absence_type.value
            if atype not in absences_by_type:
                absences_by_type[atype] = Decimal("0")
            absences_by_type[atype] += absence.days_count

        # Heures supplémentaires détaillées
        overtime_details = {
            "overtime_25": Decimal("0"),
            "overtime_50": Decimal("0"),
            "night": Decimal("0"),
            "sunday": Decimal("0"),
            "holiday": Decimal("0")
        }

        for ts in timesheets:
            calc = self.calculate_overtime(ts.id)
            overtime_details["overtime_25"] += calc.overtime_25_hours
            overtime_details["overtime_50"] += calc.overtime_50_hours
            overtime_details["night"] += calc.night_hours
            overtime_details["sunday"] += calc.sunday_hours
            overtime_details["holiday"] += calc.holiday_hours

        return {
            "employee_id": employee_id,
            "period": f"{year}-{month:02d}",
            "total_worked_hours": float(total_worked),
            "total_overtime_hours": float(total_overtime),
            "total_billable_hours": float(total_billable),
            "overtime_details": {k: float(v) for k, v in overtime_details.items()},
            "absences": {k: float(v) for k, v in absences_by_type.items()},
            "timesheets_count": len(timesheets),
            "all_approved": all(ts.status == TimesheetStatus.APPROVED for ts in timesheets)
        }

    # ========================================================================
    # REPORTING
    # ========================================================================

    def get_project_hours(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Rapport des heures par projet."""
        entries = [
            e for e in self._time_entries.values()
            if e.project_id == project_id
            and (not start_date or e.entry_date >= start_date)
            and (not end_date or e.entry_date <= end_date)
        ]

        by_employee = {}
        by_task = {}
        by_type = {}

        for entry in entries:
            duration = entry.calculate_duration()

            # Par employé
            if entry.employee_id not in by_employee:
                by_employee[entry.employee_id] = Decimal("0")
            by_employee[entry.employee_id] += duration

            # Par tâche
            task_key = entry.task_id or "non_affecté"
            if task_key not in by_task:
                by_task[task_key] = Decimal("0")
            by_task[task_key] += duration

            # Par type
            if entry.entry_type.value not in by_type:
                by_type[entry.entry_type.value] = Decimal("0")
            by_type[entry.entry_type.value] += duration

        total_hours = sum(e.calculate_duration() for e in entries)
        billable_hours = sum(
            e.calculate_duration() for e in entries if e.billable
        )

        return {
            "project_id": project_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "total_hours": float(total_hours),
            "billable_hours": float(billable_hours),
            "billable_percentage": float(
                billable_hours / total_hours * 100 if total_hours else 0
            ),
            "by_employee": {k: float(v) for k, v in by_employee.items()},
            "by_task": {k: float(v) for k, v in by_task.items()},
            "by_type": {k: float(v) for k, v in by_type.items()},
            "entry_count": len(entries)
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_timesheet_service(
    tenant_id: str,
    default_schedule_type: WorkScheduleType = WorkScheduleType.STANDARD_35H
) -> TimesheetService:
    """Crée un service de gestion des temps."""
    return TimesheetService(
        tenant_id=tenant_id,
        default_schedule_type=default_schedule_type
    )
