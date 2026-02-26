"""
AZALS MODULE - Appointments - Repository
=========================================

Repositories specialises pour le module Rendez-vous.
Pattern Repository avec isolation tenant automatique.

Conformite AZALSCORE:
- _base_query() filtre automatiquement par tenant_id
- Soft delete transparent
- Optimistic locking avec version
"""
from __future__ import annotations


import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.repository import BaseRepository
from .models import (
    Appointment, AppointmentType, Resource, Attendee, Reminder,
    Availability, WorkingHours, WaitlistEntry, CalendarSync,
    BookingSettings, AppointmentSequence,
    AppointmentStatus, AppointmentMode, AttendeeStatus, ReminderStatus,
    AvailabilityType, RecurrencePattern
)

logger = logging.getLogger(__name__)


# ============================================================================
# REPOSITORY TYPE DE RENDEZ-VOUS
# ============================================================================

class AppointmentTypeRepository(BaseRepository[AppointmentType]):
    """Repository pour les types de rendez-vous."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        super().__init__(db, AppointmentType, tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtrage tenant et soft delete."""
        query = self.db.query(AppointmentType).filter(
            AppointmentType.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(AppointmentType.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[AppointmentType]:
        """Recupere un type par ID."""
        return self._base_query().filter(AppointmentType.id == id).first()

    def get_by_code(self, code: str) -> Optional[AppointmentType]:
        """Recupere un type par code."""
        return self._base_query().filter(AppointmentType.code == code).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(AppointmentType.code == code)
        if exclude_id:
            query = query.filter(AppointmentType.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "sort_order",
        sort_dir: str = "asc"
    ) -> Tuple[List[AppointmentType], int]:
        """Liste les types avec filtres et pagination."""
        query = self._base_query()

        if is_active is not None:
            query = query.filter(AppointmentType.is_active == is_active)
        if is_public is not None:
            query = query.filter(AppointmentType.is_public == is_public)
        if category:
            query = query.filter(AppointmentType.category == category)

        total = query.count()

        # Tri
        sort_column = getattr(AppointmentType, sort_by, AppointmentType.sort_order)
        if sort_dir == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def list_active(self) -> List[AppointmentType]:
        """Liste les types actifs et publics."""
        return self._base_query().filter(
            AppointmentType.is_active == True,
            AppointmentType.is_public == True
        ).order_by(AppointmentType.sort_order).all()

    def create(self, data: dict, user_id: UUID) -> AppointmentType:
        """Cree un nouveau type."""
        if not data.get("code"):
            data["code"] = self._generate_code()

        type_obj = AppointmentType(
            tenant_id=self.tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **data
        )
        self.db.add(type_obj)
        self.db.commit()
        self.db.refresh(type_obj)
        return type_obj

    def update(self, type_obj: AppointmentType, data: dict, user_id: UUID) -> AppointmentType:
        """Met a jour un type."""
        for key, value in data.items():
            if hasattr(type_obj, key) and value is not None:
                setattr(type_obj, key, value)

        type_obj.updated_by = user_id
        type_obj.updated_at = datetime.utcnow()
        type_obj.version += 1

        self.db.commit()
        self.db.refresh(type_obj)
        return type_obj

    def soft_delete(self, type_obj: AppointmentType, user_id: UUID) -> None:
        """Suppression logique."""
        type_obj.is_deleted = True
        type_obj.deleted_at = datetime.utcnow()
        type_obj.deleted_by = user_id
        self.db.commit()

    def _generate_code(self) -> str:
        """Genere un code unique."""
        year = datetime.utcnow().year
        prefix = "TYPE"
        count = self._base_query().filter(
            AppointmentType.code.like(f"{prefix}-{year}-%")
        ).count()
        return f"{prefix}-{year}-{count + 1:04d}"

    def autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete pour les types."""
        results = self._base_query().filter(
            AppointmentType.is_active == True,
            or_(
                AppointmentType.code.ilike(f"%{query}%"),
                AppointmentType.name.ilike(f"%{query}%")
            )
        ).limit(limit).all()

        return [{
            "id": str(t.id),
            "code": t.code,
            "label": t.name,
            "secondary": t.category,
            "type": "appointment_type"
        } for t in results]


# ============================================================================
# REPOSITORY RESSOURCE
# ============================================================================

class ResourceRepository(BaseRepository[Resource]):
    """Repository pour les ressources."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        super().__init__(db, Resource, tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtrage tenant et soft delete."""
        query = self.db.query(Resource).filter(Resource.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Resource.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Resource]:
        """Recupere une ressource par ID."""
        return self._base_query().filter(Resource.id == id).first()

    def get_by_code(self, code: str) -> Optional[Resource]:
        """Recupere une ressource par code."""
        return self._base_query().filter(Resource.code == code).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(Resource.code == code)
        if exclude_id:
            query = query.filter(Resource.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        resource_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_available: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Resource], int]:
        """Liste les ressources avec filtres."""
        query = self._base_query()

        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        if is_active is not None:
            query = query.filter(Resource.is_active == is_active)
        if is_available is not None:
            query = query.filter(Resource.is_available == is_available)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Resource.name).offset(offset).limit(page_size).all()

        return items, total

    def list_available(self, resource_type: Optional[str] = None) -> List[Resource]:
        """Liste les ressources disponibles."""
        query = self._base_query().filter(
            Resource.is_active == True,
            Resource.is_available == True
        )
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        return query.order_by(Resource.name).all()

    def create(self, data: dict, user_id: UUID) -> Resource:
        """Cree une nouvelle ressource."""
        if not data.get("code"):
            data["code"] = self._generate_code(data.get("resource_type", "ROOM"))

        resource = Resource(
            tenant_id=self.tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **data
        )
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource

    def update(self, resource: Resource, data: dict, user_id: UUID) -> Resource:
        """Met a jour une ressource."""
        for key, value in data.items():
            if hasattr(resource, key) and value is not None:
                setattr(resource, key, value)

        resource.updated_by = user_id
        resource.updated_at = datetime.utcnow()
        resource.version += 1

        self.db.commit()
        self.db.refresh(resource)
        return resource

    def soft_delete(self, resource: Resource, user_id: UUID) -> None:
        """Suppression logique."""
        resource.is_deleted = True
        resource.deleted_at = datetime.utcnow()
        resource.deleted_by = user_id
        self.db.commit()

    def _generate_code(self, resource_type: str) -> str:
        """Genere un code unique."""
        prefix = resource_type[:3].upper()
        count = self._base_query().filter(
            Resource.code.like(f"{prefix}-%")
        ).count()
        return f"{prefix}-{count + 1:04d}"

    def autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete pour les ressources."""
        results = self._base_query().filter(
            Resource.is_active == True,
            or_(
                Resource.code.ilike(f"%{query}%"),
                Resource.name.ilike(f"%{query}%")
            )
        ).limit(limit).all()

        return [{
            "id": str(r.id),
            "code": r.code,
            "label": r.name,
            "secondary": r.resource_type.value if r.resource_type else None,
            "type": "resource"
        } for r in results]


# ============================================================================
# REPOSITORY RENDEZ-VOUS
# ============================================================================

class AppointmentRepository(BaseRepository[Appointment]):
    """Repository pour les rendez-vous."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        super().__init__(db, Appointment, tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtrage tenant et soft delete."""
        query = self.db.query(Appointment).filter(
            Appointment.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(Appointment.is_deleted == False)
        return query

    def get_by_id(
        self,
        id: UUID,
        with_attendees: bool = False,
        with_reminders: bool = False
    ) -> Optional[Appointment]:
        """Recupere un rendez-vous par ID."""
        query = self._base_query().filter(Appointment.id == id)

        if with_attendees:
            query = query.options(selectinload(Appointment.attendees))
        if with_reminders:
            query = query.options(selectinload(Appointment.reminders))

        return query.first()

    def get_by_code(self, code: str) -> Optional[Appointment]:
        """Recupere un rendez-vous par code."""
        return self._base_query().filter(Appointment.code == code).first()

    def get_by_confirmation_code(self, confirmation_code: str) -> Optional[Appointment]:
        """Recupere un rendez-vous par code de confirmation."""
        return self._base_query().filter(
            Appointment.confirmation_code == confirmation_code
        ).first()

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verifie si un code existe."""
        query = self._base_query().filter(Appointment.code == code)
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "start_datetime",
        sort_dir: str = "asc"
    ) -> Tuple[List[Appointment], int]:
        """Liste les rendez-vous avec filtres et pagination."""
        query = self._base_query()

        if filters:
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(or_(
                    Appointment.code.ilike(search),
                    Appointment.title.ilike(search),
                    Appointment.contact_name.ilike(search)
                ))

            if filters.get("status"):
                query = query.filter(Appointment.status.in_(filters["status"]))

            if filters.get("mode"):
                query = query.filter(Appointment.mode.in_(filters["mode"]))

            if filters.get("type_id"):
                query = query.filter(Appointment.type_id == filters["type_id"])

            if filters.get("resource_id"):
                query = query.filter(Appointment.resource_id == filters["resource_id"])

            if filters.get("contact_id"):
                query = query.filter(Appointment.contact_id == filters["contact_id"])

            if filters.get("customer_id"):
                query = query.filter(Appointment.customer_id == filters["customer_id"])

            if filters.get("organizer_id"):
                query = query.filter(Appointment.organizer_id == filters["organizer_id"])

            if filters.get("assigned_to"):
                query = query.filter(Appointment.assigned_to == filters["assigned_to"])

            if filters.get("date_from"):
                query = query.filter(Appointment.start_datetime >= datetime.combine(
                    filters["date_from"], time.min
                ))

            if filters.get("date_to"):
                query = query.filter(Appointment.start_datetime <= datetime.combine(
                    filters["date_to"], time.max
                ))

            if filters.get("is_recurring") is not None:
                query = query.filter(Appointment.is_recurring == filters["is_recurring"])

            if filters.get("is_billable") is not None:
                query = query.filter(Appointment.is_billable == filters["is_billable"])

        total = query.count()

        # Tri
        sort_column = getattr(Appointment, sort_by, Appointment.start_datetime)
        if sort_dir == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        items = query.options(
            selectinload(Appointment.attendees)
        ).offset(offset).limit(page_size).all()

        return items, total

    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        statuses: Optional[List[AppointmentStatus]] = None
    ) -> List[Appointment]:
        """Recupere les rendez-vous dans une plage de dates."""
        query = self._base_query().filter(
            Appointment.start_datetime >= datetime.combine(start_date, time.min),
            Appointment.start_datetime <= datetime.combine(end_date, time.max)
        )

        if user_id:
            query = query.filter(or_(
                Appointment.organizer_id == user_id,
                Appointment.assigned_to == user_id
            ))

        if resource_id:
            query = query.filter(Appointment.resource_id == resource_id)

        if statuses:
            query = query.filter(Appointment.status.in_(statuses))

        return query.order_by(Appointment.start_datetime).all()

    def get_day_schedule(
        self,
        target_date: date,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """Recupere le planning d'une journee."""
        return self.get_by_date_range(
            target_date,
            target_date,
            user_id=user_id,
            resource_id=resource_id,
            statuses=[
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CHECKED_IN,
                AppointmentStatus.IN_PROGRESS
            ]
        )

    def get_upcoming(
        self,
        user_id: Optional[UUID] = None,
        contact_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Appointment]:
        """Recupere les prochains rendez-vous."""
        query = self._base_query().filter(
            Appointment.start_datetime >= datetime.utcnow(),
            Appointment.status.in_([
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.PENDING
            ])
        )

        if user_id:
            query = query.filter(or_(
                Appointment.organizer_id == user_id,
                Appointment.assigned_to == user_id
            ))

        if contact_id:
            query = query.filter(Appointment.contact_id == contact_id)

        return query.order_by(Appointment.start_datetime).limit(limit).all()

    def check_conflicts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """Verifie les conflits de planning."""
        query = self._base_query().filter(
            Appointment.status.in_([
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.PENDING,
                AppointmentStatus.CHECKED_IN,
                AppointmentStatus.IN_PROGRESS
            ]),
            # Chevauchement
            Appointment.start_datetime < end_datetime,
            Appointment.end_datetime > start_datetime
        )

        if user_id:
            query = query.filter(or_(
                Appointment.organizer_id == user_id,
                Appointment.assigned_to == user_id
            ))

        if resource_id:
            query = query.filter(Appointment.resource_id == resource_id)

        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)

        return query.all()

    def create(self, data: dict, user_id: UUID) -> Appointment:
        """Cree un nouveau rendez-vous."""
        # Generation du code
        if not data.get("code"):
            data["code"] = self._generate_code()

        # Generation du code de confirmation
        if not data.get("confirmation_code"):
            data["confirmation_code"] = self._generate_confirmation_code()

        # Extraction des sous-entites
        attendees_data = data.pop("attendees", [])
        reminders_data = data.pop("reminders", [])

        # Creation du rendez-vous
        appointment = Appointment(
            tenant_id=self.tenant_id,
            created_by=user_id,
            updated_by=user_id,
            **data
        )
        self.db.add(appointment)
        self.db.flush()

        # Ajout des participants
        for attendee_data in attendees_data:
            attendee = Attendee(
                tenant_id=self.tenant_id,
                appointment_id=appointment.id,
                created_by=user_id,
                **attendee_data
            )
            self.db.add(attendee)

        # Ajout des rappels
        for reminder_data in reminders_data:
            if not reminder_data.get("scheduled_at"):
                reminder_data["scheduled_at"] = appointment.start_datetime - timedelta(
                    minutes=reminder_data.get("minutes_before", 1440)
                )
            reminder = Reminder(
                tenant_id=self.tenant_id,
                appointment_id=appointment.id,
                **reminder_data
            )
            self.db.add(reminder)

        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def update(self, appointment: Appointment, data: dict, user_id: UUID) -> Appointment:
        """Met a jour un rendez-vous."""
        for key, value in data.items():
            if hasattr(appointment, key) and value is not None:
                setattr(appointment, key, value)

        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def confirm(self, appointment: Appointment, user_id: UUID) -> Appointment:
        """Confirme un rendez-vous."""
        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = datetime.utcnow()
        appointment.confirmed_by = user_id
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def cancel(
        self,
        appointment: Appointment,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Appointment:
        """Annule un rendez-vous."""
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancelled_by = user_id
        appointment.cancellation_reason = reason
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def reschedule(
        self,
        appointment: Appointment,
        new_start: datetime,
        new_end: datetime,
        user_id: UUID
    ) -> Appointment:
        """Replanifie un rendez-vous."""
        appointment.start_datetime = new_start
        appointment.end_datetime = new_end
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.reschedule_count += 1
        appointment.last_rescheduled_at = datetime.utcnow()
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def check_in(self, appointment: Appointment, user_id: UUID) -> Appointment:
        """Check-in d'un rendez-vous."""
        appointment.status = AppointmentStatus.CHECKED_IN
        appointment.checked_in_at = datetime.utcnow()
        appointment.checked_in_by = user_id
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def complete(
        self,
        appointment: Appointment,
        user_id: UUID,
        outcome: Optional[str] = None
    ) -> Appointment:
        """Complete un rendez-vous."""
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.utcnow()
        appointment.completed_by = user_id
        appointment.outcome = outcome
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def mark_no_show(self, appointment: Appointment, user_id: UUID) -> Appointment:
        """Marque comme absent."""
        appointment.status = AppointmentStatus.NO_SHOW
        appointment.updated_by = user_id
        appointment.updated_at = datetime.utcnow()
        appointment.version += 1
        self.db.commit()
        return appointment

    def soft_delete(self, appointment: Appointment, user_id: UUID) -> None:
        """Suppression logique."""
        appointment.is_deleted = True
        appointment.deleted_at = datetime.utcnow()
        appointment.deleted_by = user_id
        self.db.commit()

    def _generate_code(self) -> str:
        """Genere un code unique."""
        year = datetime.utcnow().year
        prefix = "RDV"

        # Utilisation de la sequence
        seq = self.db.query(AppointmentSequence).filter(
            AppointmentSequence.tenant_id == self.tenant_id,
            AppointmentSequence.year == year,
            AppointmentSequence.prefix == prefix
        ).with_for_update().first()

        if seq:
            seq.last_number += 1
            next_num = seq.last_number
        else:
            seq = AppointmentSequence(
                tenant_id=self.tenant_id,
                year=year,
                prefix=prefix,
                last_number=1
            )
            self.db.add(seq)
            next_num = 1

        self.db.flush()
        return f"{prefix}-{year}-{next_num:05d}"

    def _generate_confirmation_code(self) -> str:
        """Genere un code de confirmation unique."""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=8))

    def autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocomplete pour les rendez-vous."""
        results = self._base_query().filter(
            or_(
                Appointment.code.ilike(f"%{query}%"),
                Appointment.title.ilike(f"%{query}%"),
                Appointment.contact_name.ilike(f"%{query}%")
            )
        ).order_by(desc(Appointment.start_datetime)).limit(limit).all()

        return [{
            "id": str(a.id),
            "code": a.code,
            "label": a.title,
            "secondary": a.contact_name,
            "type": "appointment"
        } for a in results]


# ============================================================================
# REPOSITORY PARTICIPANT
# ============================================================================

class AttendeeRepository:
    """Repository pour les participants."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtrage tenant."""
        return self.db.query(Attendee).filter(
            Attendee.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[Attendee]:
        """Recupere un participant par ID."""
        return self._base_query().filter(Attendee.id == id).first()

    def get_by_appointment(self, appointment_id: UUID) -> List[Attendee]:
        """Recupere les participants d'un rendez-vous."""
        return self._base_query().filter(
            Attendee.appointment_id == appointment_id
        ).all()

    def add(self, appointment_id: UUID, data: dict, user_id: UUID) -> Attendee:
        """Ajoute un participant."""
        attendee = Attendee(
            tenant_id=self.tenant_id,
            appointment_id=appointment_id,
            created_by=user_id,
            **data
        )
        self.db.add(attendee)
        self.db.commit()
        self.db.refresh(attendee)
        return attendee

    def update(self, attendee: Attendee, data: dict) -> Attendee:
        """Met a jour un participant."""
        for key, value in data.items():
            if hasattr(attendee, key) and value is not None:
                setattr(attendee, key, value)
        attendee.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(attendee)
        return attendee

    def update_status(
        self,
        attendee: Attendee,
        status: AttendeeStatus,
        comment: Optional[str] = None
    ) -> Attendee:
        """Met a jour le statut d'un participant."""
        attendee.status = status
        attendee.responded_at = datetime.utcnow()
        if comment:
            attendee.response_comment = comment
        self.db.commit()
        return attendee

    def check_in(self, attendee: Attendee) -> Attendee:
        """Check-in d'un participant."""
        attendee.checked_in = True
        attendee.checked_in_at = datetime.utcnow()
        self.db.commit()
        return attendee

    def delete(self, attendee: Attendee) -> None:
        """Supprime un participant."""
        self.db.delete(attendee)
        self.db.commit()


# ============================================================================
# REPOSITORY RAPPEL
# ============================================================================

class ReminderRepository:
    """Repository pour les rappels."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtrage tenant."""
        return self.db.query(Reminder).filter(
            Reminder.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[Reminder]:
        """Recupere un rappel par ID."""
        return self._base_query().filter(Reminder.id == id).first()

    def get_by_appointment(self, appointment_id: UUID) -> List[Reminder]:
        """Recupere les rappels d'un rendez-vous."""
        return self._base_query().filter(
            Reminder.appointment_id == appointment_id
        ).order_by(Reminder.scheduled_at).all()

    def get_pending(self, limit: int = 100) -> List[Reminder]:
        """Recupere les rappels a envoyer."""
        return self._base_query().filter(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.scheduled_at <= datetime.utcnow()
        ).order_by(Reminder.scheduled_at).limit(limit).all()

    def add(self, appointment_id: UUID, data: dict) -> Reminder:
        """Ajoute un rappel."""
        reminder = Reminder(
            tenant_id=self.tenant_id,
            appointment_id=appointment_id,
            **data
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def mark_sent(self, reminder: Reminder) -> Reminder:
        """Marque un rappel comme envoye."""
        reminder.status = ReminderStatus.SENT
        reminder.sent_at = datetime.utcnow()
        self.db.commit()
        return reminder

    def mark_failed(self, reminder: Reminder, reason: str) -> Reminder:
        """Marque un rappel comme echoue."""
        reminder.status = ReminderStatus.FAILED
        reminder.failed_at = datetime.utcnow()
        reminder.failure_reason = reason
        reminder.retry_count += 1
        self.db.commit()
        return reminder

    def cancel(self, reminder: Reminder) -> Reminder:
        """Annule un rappel."""
        reminder.status = ReminderStatus.CANCELLED
        self.db.commit()
        return reminder

    def delete(self, reminder: Reminder) -> None:
        """Supprime un rappel."""
        self.db.delete(reminder)
        self.db.commit()


# ============================================================================
# REPOSITORY DISPONIBILITE
# ============================================================================

class AvailabilityRepository:
    """Repository pour les disponibilites."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtrage tenant."""
        return self.db.query(Availability).filter(
            Availability.tenant_id == self.tenant_id,
            Availability.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[Availability]:
        """Recupere une disponibilite par ID."""
        return self._base_query().filter(Availability.id == id).first()

    def get_by_user(
        self,
        user_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[Availability]:
        """Recupere les disponibilites d'un utilisateur."""
        return self._base_query().filter(
            Availability.user_id == user_id,
            Availability.date_start <= date_to,
            or_(
                Availability.date_end >= date_from,
                Availability.date_end.is_(None)
            )
        ).order_by(Availability.date_start).all()

    def get_by_resource(
        self,
        resource_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[Availability]:
        """Recupere les disponibilites d'une ressource."""
        return self._base_query().filter(
            Availability.resource_id == resource_id,
            Availability.date_start <= date_to,
            or_(
                Availability.date_end >= date_from,
                Availability.date_end.is_(None)
            )
        ).order_by(Availability.date_start).all()

    def create(self, data: dict, user_id: UUID) -> Availability:
        """Cree une disponibilite."""
        availability = Availability(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data
        )
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        return availability

    def update(self, availability: Availability, data: dict) -> Availability:
        """Met a jour une disponibilite."""
        for key, value in data.items():
            if hasattr(availability, key) and value is not None:
                setattr(availability, key, value)
        availability.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(availability)
        return availability

    def soft_delete(self, availability: Availability) -> None:
        """Suppression logique."""
        availability.is_deleted = True
        availability.deleted_at = datetime.utcnow()
        self.db.commit()


# ============================================================================
# REPOSITORY HORAIRES DE TRAVAIL
# ============================================================================

class WorkingHoursRepository:
    """Repository pour les horaires de travail."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtrage tenant."""
        return self.db.query(WorkingHours).filter(
            WorkingHours.tenant_id == self.tenant_id
        )

    def get_by_user(self, user_id: UUID) -> List[WorkingHours]:
        """Recupere les horaires d'un utilisateur."""
        return self._base_query().filter(
            WorkingHours.user_id == user_id
        ).order_by(WorkingHours.day_of_week).all()

    def get_by_resource(self, resource_id: UUID) -> List[WorkingHours]:
        """Recupere les horaires d'une ressource."""
        return self._base_query().filter(
            WorkingHours.resource_id == resource_id
        ).order_by(WorkingHours.day_of_week).all()

    def set(
        self,
        user_id: Optional[UUID],
        resource_id: Optional[UUID],
        day_of_week: int,
        data: dict
    ) -> WorkingHours:
        """Definit les horaires pour un jour."""
        # Recherche existant
        query = self._base_query().filter(WorkingHours.day_of_week == day_of_week)
        if user_id:
            query = query.filter(WorkingHours.user_id == user_id)
        if resource_id:
            query = query.filter(WorkingHours.resource_id == resource_id)

        wh = query.first()

        if wh:
            for key, value in data.items():
                if hasattr(wh, key):
                    setattr(wh, key, value)
            wh.updated_at = datetime.utcnow()
        else:
            wh = WorkingHours(
                tenant_id=self.tenant_id,
                user_id=user_id,
                resource_id=resource_id,
                day_of_week=day_of_week,
                **data
            )
            self.db.add(wh)

        self.db.commit()
        self.db.refresh(wh)
        return wh

    def delete(self, working_hours: WorkingHours) -> None:
        """Supprime des horaires."""
        self.db.delete(working_hours)
        self.db.commit()


# ============================================================================
# REPOSITORY LISTE D'ATTENTE
# ============================================================================

class WaitlistRepository:
    """Repository pour la liste d'attente."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtrage tenant."""
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[WaitlistEntry]:
        """Recupere une entree par ID."""
        return self._base_query().filter(WaitlistEntry.id == id).first()

    def list(
        self,
        type_id: Optional[UUID] = None,
        status: str = "waiting",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WaitlistEntry], int]:
        """Liste les entrees."""
        query = self._base_query()

        if type_id:
            query = query.filter(WaitlistEntry.type_id == type_id)
        if status:
            query = query.filter(WaitlistEntry.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(
            WaitlistEntry.priority.desc(),
            WaitlistEntry.created_at
        ).offset(offset).limit(page_size).all()

        return items, total

    def add(self, data: dict) -> WaitlistEntry:
        """Ajoute a la liste d'attente."""
        entry = WaitlistEntry(
            tenant_id=self.tenant_id,
            expires_at=datetime.utcnow() + timedelta(days=30),
            **data
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def notify(self, entry: WaitlistEntry) -> WaitlistEntry:
        """Marque comme notifie."""
        entry.status = "notified"
        entry.notified_at = datetime.utcnow()
        entry.notification_count += 1
        entry.last_notification_at = datetime.utcnow()
        self.db.commit()
        return entry

    def convert(self, entry: WaitlistEntry, appointment_id: UUID) -> WaitlistEntry:
        """Convertit en rendez-vous."""
        entry.status = "booked"
        entry.converted_appointment_id = appointment_id
        entry.converted_at = datetime.utcnow()
        self.db.commit()
        return entry

    def expire(self, entry: WaitlistEntry) -> WaitlistEntry:
        """Marque comme expire."""
        entry.status = "expired"
        self.db.commit()
        return entry

    def cancel(self, entry: WaitlistEntry) -> WaitlistEntry:
        """Annule une entree."""
        entry.status = "cancelled"
        self.db.commit()
        return entry


# ============================================================================
# REPOSITORY PARAMETRES
# ============================================================================

class BookingSettingsRepository:
    """Repository pour les parametres de reservation."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get(self) -> BookingSettings:
        """Recupere les parametres (cree si inexistants)."""
        settings = self.db.query(BookingSettings).filter(
            BookingSettings.tenant_id == self.tenant_id
        ).first()

        if not settings:
            settings = BookingSettings(tenant_id=self.tenant_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

        return settings

    def update(self, data: dict, user_id: UUID) -> BookingSettings:
        """Met a jour les parametres."""
        settings = self.get()

        for key, value in data.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)

        settings.updated_by = user_id
        settings.updated_at = datetime.utcnow()
        settings.version += 1

        self.db.commit()
        self.db.refresh(settings)
        return settings
