"""
AZALS MODULE - TIMETRACKING: Repository
========================================

Repositories SQLAlchemy pour le suivi du temps de travail.
Conforme aux normes AZALSCORE (isolation tenant, type hints).
GAP-080 - Time Tracking
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from .models import (
    TimePolicy,
    TimeProject,
    TimeTask,
    ClockEntry,
    TimeEntry,
    Timesheet,
    Absence,
    EntryType,
    TimesheetStatus,
    TimeEntryStatus,
    BillableType,
    OvertimeType,
    AbsenceType,
    AbsenceStatus,
)


class TimePolicyRepository:
    """Repository pour les politiques de temps."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TimePolicy).filter(
            TimePolicy.tenant_id == self.tenant_id
        )

    def get_by_id(self, policy_id: UUID) -> Optional[TimePolicy]:
        """Recupere une politique par ID."""
        return self._base_query().filter(TimePolicy.id == policy_id).first()

    def get_default(self) -> Optional[TimePolicy]:
        """Recupere la politique par defaut."""
        return self._base_query().filter(
            TimePolicy.is_default == True,
            TimePolicy.is_active == True
        ).first()

    def list(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TimePolicy], int]:
        """Liste les politiques."""
        query = self._base_query()
        if is_active is not None:
            query = query.filter(TimePolicy.is_active == is_active)
        total = query.count()
        items = query.order_by(TimePolicy.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def create(self, data: Dict[str, Any]) -> TimePolicy:
        """Cree une nouvelle politique."""
        policy = TimePolicy(tenant_id=self.tenant_id, **data)
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def update(self, policy: TimePolicy, data: Dict[str, Any]) -> TimePolicy:
        """Met a jour une politique."""
        for key, value in data.items():
            if hasattr(policy, key) and value is not None:
                setattr(policy, key, value)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def set_default(self, policy: TimePolicy) -> TimePolicy:
        """Definit une politique comme defaut."""
        self._base_query().filter(TimePolicy.is_default == True).update(
            {TimePolicy.is_default: False}
        )
        policy.is_default = True
        self.db.commit()
        self.db.refresh(policy)
        return policy


class TimeProjectRepository:
    """Repository pour les projets de temps."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TimeProject).filter(
            TimeProject.tenant_id == self.tenant_id
        )

    def get_by_id(self, project_id: UUID) -> Optional[TimeProject]:
        """Recupere un projet par ID."""
        return self._base_query().filter(TimeProject.id == project_id).first()

    def get_by_code(self, code: str) -> Optional[TimeProject]:
        """Recupere un projet par code."""
        return self._base_query().filter(TimeProject.code == code).first()

    def list(
        self,
        client_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TimeProject], int]:
        """Liste les projets."""
        query = self._base_query()
        if client_id:
            query = query.filter(TimeProject.client_id == client_id)
        if is_active is not None:
            query = query.filter(TimeProject.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    TimeProject.name.ilike(f"%{search}%"),
                    TimeProject.code.ilike(f"%{search}%")
                )
            )
        total = query.count()
        items = query.order_by(TimeProject.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_user_projects(self, user_id: UUID) -> List[TimeProject]:
        """Recupere les projets d'un utilisateur."""
        return self._base_query().filter(
            TimeProject.is_active == True,
            TimeProject.member_ids.contains([str(user_id)])
        ).order_by(TimeProject.name).all()

    def create(self, data: Dict[str, Any]) -> TimeProject:
        """Cree un nouveau projet."""
        project = TimeProject(tenant_id=self.tenant_id, **data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project: TimeProject, data: Dict[str, Any]) -> TimeProject:
        """Met a jour un projet."""
        for key, value in data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_hours(self, project: TimeProject, hours: Decimal, billable: bool = True) -> TimeProject:
        """Met a jour les heures du projet."""
        project.total_hours += hours
        if billable:
            project.billable_hours += hours
        if project.budget_hours:
            project.remaining_budget_hours = project.budget_hours - project.total_hours
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project


class TimeTaskRepository:
    """Repository pour les taches de projet."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TimeTask).filter(
            TimeTask.tenant_id == self.tenant_id
        )

    def get_by_id(self, task_id: UUID) -> Optional[TimeTask]:
        """Recupere une tache par ID."""
        return self._base_query().filter(TimeTask.id == task_id).first()

    def get_by_project(self, project_id: UUID, is_active: Optional[bool] = None) -> List[TimeTask]:
        """Recupere les taches d'un projet."""
        query = self._base_query().filter(TimeTask.project_id == project_id)
        if is_active is not None:
            query = query.filter(TimeTask.is_active == is_active)
        return query.order_by(TimeTask.name).all()

    def create(self, data: Dict[str, Any]) -> TimeTask:
        """Cree une nouvelle tache."""
        task = TimeTask(tenant_id=self.tenant_id, **data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task: TimeTask, data: Dict[str, Any]) -> TimeTask:
        """Met a jour une tache."""
        for key, value in data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task


class ClockEntryRepository:
    """Repository pour les entrees de pointage."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(ClockEntry).filter(
            ClockEntry.tenant_id == self.tenant_id
        )

    def get_by_id(self, entry_id: UUID) -> Optional[ClockEntry]:
        """Recupere une entree par ID."""
        return self._base_query().filter(ClockEntry.id == entry_id).first()

    def get_user_entries(
        self,
        user_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[ClockEntry]:
        """Recupere les entrees d'un utilisateur."""
        query = self._base_query().filter(ClockEntry.user_id == user_id)
        if date_from:
            query = query.filter(func.date(ClockEntry.timestamp) >= date_from)
        if date_to:
            query = query.filter(func.date(ClockEntry.timestamp) <= date_to)
        return query.order_by(ClockEntry.timestamp).all()

    def get_last_entry(self, user_id: UUID) -> Optional[ClockEntry]:
        """Recupere la derniere entree d'un utilisateur."""
        return self._base_query().filter(
            ClockEntry.user_id == user_id
        ).order_by(desc(ClockEntry.timestamp)).first()

    def get_today_entries(self, user_id: UUID) -> List[ClockEntry]:
        """Recupere les entrees du jour."""
        today = date.today()
        return self._base_query().filter(
            ClockEntry.user_id == user_id,
            func.date(ClockEntry.timestamp) == today
        ).order_by(ClockEntry.timestamp).all()

    def create(self, data: Dict[str, Any]) -> ClockEntry:
        """Cree une nouvelle entree."""
        entry = ClockEntry(tenant_id=self.tenant_id, **data)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry


class TimeEntryRepository:
    """Repository pour les entrees de temps."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TimeEntry).filter(
            TimeEntry.tenant_id == self.tenant_id
        )

    def get_by_id(self, entry_id: UUID) -> Optional[TimeEntry]:
        """Recupere une entree par ID."""
        return self._base_query().filter(TimeEntry.id == entry_id).first()

    def list(
        self,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        status: Optional[TimeEntryStatus] = None,
        billable_type: Optional[BillableType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TimeEntry], int]:
        """Liste les entrees."""
        query = self._base_query()
        if user_id:
            query = query.filter(TimeEntry.user_id == user_id)
        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        if status:
            query = query.filter(TimeEntry.status == status)
        if billable_type:
            query = query.filter(TimeEntry.billable_type == billable_type)
        if date_from:
            query = query.filter(TimeEntry.entry_date >= date_from)
        if date_to:
            query = query.filter(TimeEntry.entry_date <= date_to)
        total = query.count()
        items = query.order_by(desc(TimeEntry.entry_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_for_timesheet(self, user_id: UUID, period_start: date, period_end: date) -> List[TimeEntry]:
        """Recupere les entrees pour une feuille de temps."""
        return self._base_query().filter(
            TimeEntry.user_id == user_id,
            TimeEntry.entry_date >= period_start,
            TimeEntry.entry_date <= period_end
        ).order_by(TimeEntry.entry_date).all()

    def create(self, data: Dict[str, Any]) -> TimeEntry:
        """Cree une nouvelle entree."""
        entry = TimeEntry(tenant_id=self.tenant_id, **data)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: TimeEntry, data: Dict[str, Any]) -> TimeEntry:
        """Met a jour une entree."""
        for key, value in data.items():
            if hasattr(entry, key) and value is not None:
                setattr(entry, key, value)
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def approve(self, entry: TimeEntry, user_id: UUID) -> TimeEntry:
        """Approuve une entree."""
        entry.status = TimeEntryStatus.APPROVED
        entry.approved_by = user_id
        entry.approved_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def reject(self, entry: TimeEntry, reason: str) -> TimeEntry:
        """Rejette une entree."""
        entry.status = TimeEntryStatus.REJECTED
        entry.rejection_reason = reason
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def mark_billed(self, entry: TimeEntry, invoice_id: UUID) -> TimeEntry:
        """Marque une entree comme facturee."""
        entry.status = TimeEntryStatus.BILLED
        entry.invoice_id = invoice_id
        entry.billed_at = datetime.utcnow()
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_totals(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date
    ) -> Dict[str, Decimal]:
        """Calcule les totaux pour une periode."""
        entries = self._base_query().filter(
            TimeEntry.user_id == user_id,
            TimeEntry.entry_date >= date_from,
            TimeEntry.entry_date <= date_to
        ).all()

        totals = {
            "total_hours": Decimal("0"),
            "regular_hours": Decimal("0"),
            "overtime_hours": Decimal("0"),
            "billable_hours": Decimal("0"),
            "non_billable_hours": Decimal("0"),
            "billable_amount": Decimal("0")
        }

        for entry in entries:
            totals["total_hours"] += entry.duration_hours
            if entry.overtime_type == OvertimeType.REGULAR:
                totals["regular_hours"] += entry.duration_hours
            else:
                totals["overtime_hours"] += entry.overtime_hours
            if entry.billable_type == BillableType.BILLABLE:
                totals["billable_hours"] += entry.duration_hours
                totals["billable_amount"] += entry.billable_amount
            else:
                totals["non_billable_hours"] += entry.duration_hours

        return totals


class TimesheetRepository:
    """Repository pour les feuilles de temps."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Timesheet).filter(
            Timesheet.tenant_id == self.tenant_id
        )

    def get_by_id(self, timesheet_id: UUID) -> Optional[Timesheet]:
        """Recupere une feuille de temps par ID."""
        return self._base_query().filter(Timesheet.id == timesheet_id).first()

    def get_by_user_period(self, user_id: UUID, period_start: date) -> Optional[Timesheet]:
        """Recupere la feuille de temps d'un utilisateur pour une periode."""
        return self._base_query().filter(
            Timesheet.user_id == user_id,
            Timesheet.period_start == period_start
        ).first()

    def list(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[TimesheetStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Timesheet], int]:
        """Liste les feuilles de temps."""
        query = self._base_query()
        if user_id:
            query = query.filter(Timesheet.user_id == user_id)
        if status:
            query = query.filter(Timesheet.status == status)
        total = query.count()
        items = query.order_by(desc(Timesheet.period_start)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_pending_approval(self) -> List[Timesheet]:
        """Recupere les feuilles en attente d'approbation."""
        return self._base_query().filter(
            Timesheet.status == TimesheetStatus.SUBMITTED
        ).order_by(Timesheet.submitted_at).all()

    def create(self, data: Dict[str, Any]) -> Timesheet:
        """Cree une nouvelle feuille de temps."""
        timesheet = Timesheet(tenant_id=self.tenant_id, **data)
        self.db.add(timesheet)
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def update(self, timesheet: Timesheet, data: Dict[str, Any]) -> Timesheet:
        """Met a jour une feuille de temps."""
        for key, value in data.items():
            if hasattr(timesheet, key) and value is not None:
                setattr(timesheet, key, value)
        timesheet.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def submit(self, timesheet: Timesheet) -> Timesheet:
        """Soumet une feuille de temps."""
        timesheet.status = TimesheetStatus.SUBMITTED
        timesheet.submitted_at = datetime.utcnow()
        timesheet.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def approve(self, timesheet: Timesheet, user_id: UUID) -> Timesheet:
        """Approuve une feuille de temps."""
        timesheet.status = TimesheetStatus.APPROVED
        timesheet.approved_by = user_id
        timesheet.approved_at = datetime.utcnow()
        timesheet.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def reject(self, timesheet: Timesheet, reason: str) -> Timesheet:
        """Rejette une feuille de temps."""
        timesheet.status = TimesheetStatus.REJECTED
        timesheet.rejection_reason = reason
        timesheet.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet


class AbsenceRepository:
    """Repository pour les absences."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(Absence).filter(
            Absence.tenant_id == self.tenant_id
        )

    def get_by_id(self, absence_id: UUID) -> Optional[Absence]:
        """Recupere une absence par ID."""
        return self._base_query().filter(Absence.id == absence_id).first()

    def list(
        self,
        user_id: Optional[UUID] = None,
        absence_type: Optional[AbsenceType] = None,
        status: Optional[AbsenceStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Absence], int]:
        """Liste les absences."""
        query = self._base_query()
        if user_id:
            query = query.filter(Absence.user_id == user_id)
        if absence_type:
            query = query.filter(Absence.absence_type == absence_type)
        if status:
            query = query.filter(Absence.status == status)
        if date_from:
            query = query.filter(Absence.end_date >= date_from)
        if date_to:
            query = query.filter(Absence.start_date <= date_to)
        total = query.count()
        items = query.order_by(desc(Absence.start_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    def get_pending_approval(self) -> List[Absence]:
        """Recupere les absences en attente d'approbation."""
        return self._base_query().filter(
            Absence.status == AbsenceStatus.PENDING
        ).order_by(Absence.requested_at).all()

    def check_overlap(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Verifie les chevauchements d'absence."""
        query = self._base_query().filter(
            Absence.user_id == user_id,
            Absence.status.notin_([AbsenceStatus.CANCELLED, AbsenceStatus.REJECTED]),
            Absence.start_date <= end_date,
            Absence.end_date >= start_date
        )
        if exclude_id:
            query = query.filter(Absence.id != exclude_id)
        return query.count() > 0

    def create(self, data: Dict[str, Any]) -> Absence:
        """Cree une nouvelle absence."""
        absence = Absence(tenant_id=self.tenant_id, **data)
        self.db.add(absence)
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def update(self, absence: Absence, data: Dict[str, Any]) -> Absence:
        """Met a jour une absence."""
        for key, value in data.items():
            if hasattr(absence, key) and value is not None:
                setattr(absence, key, value)
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def approve(self, absence: Absence, user_id: UUID) -> Absence:
        """Approuve une absence."""
        absence.status = AbsenceStatus.APPROVED
        absence.approved_by = user_id
        absence.approved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def reject(self, absence: Absence, user_id: UUID, reason: Optional[str] = None) -> Absence:
        """Rejette une absence."""
        absence.status = AbsenceStatus.REJECTED
        absence.approved_by = user_id
        absence.approved_at = datetime.utcnow()
        if reason:
            absence.notes = reason
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def cancel(self, absence: Absence) -> Absence:
        """Annule une absence."""
        absence.status = AbsenceStatus.CANCELLED
        self.db.commit()
        self.db.refresh(absence)
        return absence
