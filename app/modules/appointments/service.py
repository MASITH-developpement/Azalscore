"""
AZALS MODULE - Appointments - Service
======================================

Service de logique metier pour le module Rendez-vous.

Fonctionnalites inspirees de:
- Sage CRM: recurrence, planification
- Axonaut: rappels, integration CRM
- Odoo: multi-participants, ressources, creneaux
- Dynamics 365: schedule board, AI scheduling, conflits
- Pennylane: mobilite, synchronisation

Conformite AZALSCORE:
- Isolation tenant via repositories
- Audit trail complet
- Gestion des conflits
"""
from __future__ import annotations


import logging
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    Appointment, AppointmentType, Resource, Attendee, Reminder,
    Availability, WorkingHours, WaitlistEntry, CalendarSync, BookingSettings,
    AppointmentStatus, AppointmentMode, AppointmentPriority,
    RecurrencePattern, RecurrenceEndType,
    ReminderType, ReminderStatus,
    AttendeeRole, AttendeeStatus,
    AvailabilityType, BookingMode, ResourceType, SyncProvider
)
from .repository import (
    AppointmentRepository, AppointmentTypeRepository, ResourceRepository,
    AttendeeRepository, ReminderRepository, AvailabilityRepository,
    WorkingHoursRepository, WaitlistRepository, BookingSettingsRepository
)
from .exceptions import (
    AppointmentNotFoundError, AppointmentConflictError,
    AppointmentStateError, AppointmentValidationError,
    TypeNotFoundError, ResourceNotFoundError,
    SlotNotAvailableError, BookingNotAllowedError
)

logger = logging.getLogger(__name__)


class AppointmentService:
    """
    Service principal de gestion des rendez-vous.

    Centralise la logique metier et coordonne les repositories.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.appointments = AppointmentRepository(db, tenant_id)
        self.types = AppointmentTypeRepository(db, tenant_id)
        self.resources = ResourceRepository(db, tenant_id)
        self.attendees = AttendeeRepository(db, tenant_id)
        self.reminders = ReminderRepository(db, tenant_id)
        self.availabilities = AvailabilityRepository(db, tenant_id)
        self.working_hours = WorkingHoursRepository(db, tenant_id)
        self.waitlist = WaitlistRepository(db, tenant_id)
        self.settings_repo = BookingSettingsRepository(db, tenant_id)

    # =========================================================================
    # TYPES DE RENDEZ-VOUS
    # =========================================================================

    def create_type(self, data: dict, user_id: UUID) -> AppointmentType:
        """Cree un nouveau type de rendez-vous."""
        logger.info(f"Creating appointment type: {data.get('name')}")
        return self.types.create(data, user_id)

    def update_type(
        self,
        type_id: UUID,
        data: dict,
        user_id: UUID
    ) -> AppointmentType:
        """Met a jour un type de rendez-vous."""
        apt_type = self.types.get_by_id(type_id)
        if not apt_type:
            raise TypeNotFoundError(f"Type {type_id} not found")

        return self.types.update(apt_type, data, user_id)

    def delete_type(self, type_id: UUID, user_id: UUID) -> None:
        """Supprime un type de rendez-vous."""
        apt_type = self.types.get_by_id(type_id)
        if not apt_type:
            raise TypeNotFoundError(f"Type {type_id} not found")

        self.types.soft_delete(apt_type, user_id)

    def list_types(
        self,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AppointmentType], int]:
        """Liste les types de rendez-vous."""
        return self.types.list(
            is_active=is_active,
            is_public=is_public,
            category=category,
            page=page,
            page_size=page_size
        )

    # =========================================================================
    # RESSOURCES
    # =========================================================================

    def create_resource(self, data: dict, user_id: UUID) -> Resource:
        """Cree une nouvelle ressource."""
        logger.info(f"Creating resource: {data.get('name')}")
        return self.resources.create(data, user_id)

    def update_resource(
        self,
        resource_id: UUID,
        data: dict,
        user_id: UUID
    ) -> Resource:
        """Met a jour une ressource."""
        resource = self.resources.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")

        return self.resources.update(resource, data, user_id)

    def delete_resource(self, resource_id: UUID, user_id: UUID) -> None:
        """Supprime une ressource."""
        resource = self.resources.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")

        self.resources.soft_delete(resource, user_id)

    def list_resources(
        self,
        resource_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_available: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Resource], int]:
        """Liste les ressources."""
        return self.resources.list(
            resource_type=resource_type,
            is_active=is_active,
            is_available=is_available,
            page=page,
            page_size=page_size
        )

    # =========================================================================
    # CRENEAUX DISPONIBLES
    # =========================================================================

    def get_available_slots(
        self,
        target_date: date,
        type_id: Optional[UUID] = None,
        staff_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        duration_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupere les creneaux disponibles pour une date.

        Algorithme inspire d'Odoo et Dynamics 365:
        1. Recuperer les horaires de travail
        2. Appliquer les exceptions (conges, absences)
        3. Retirer les rendez-vous existants
        4. Generer les creneaux disponibles
        """
        settings = self.settings_repo.get()

        # Determiner la duree
        if duration_minutes is None:
            if type_id:
                apt_type = self.types.get_by_id(type_id)
                if apt_type:
                    duration_minutes = apt_type.default_duration_minutes
            if duration_minutes is None:
                duration_minutes = 30

        # Verifier le preavis minimum
        now = datetime.utcnow()
        min_datetime = now + timedelta(hours=settings.min_notice_hours)

        if datetime.combine(target_date, time.max) < min_datetime:
            return []

        # Verifier la fenetre de reservation
        max_date = now.date() + timedelta(days=settings.booking_window_days)
        if target_date > max_date:
            return []

        slots = []
        interval = timedelta(minutes=settings.slot_interval_minutes)
        duration = timedelta(minutes=duration_minutes)

        # Si staff specifie, utiliser ses horaires
        if staff_id:
            slots.extend(self._get_slots_for_user(
                target_date, staff_id, duration, interval, min_datetime
            ))
        # Si ressource specifiee
        elif resource_id:
            slots.extend(self._get_slots_for_resource(
                target_date, resource_id, duration, interval, min_datetime
            ))
        # Sinon, agreger tous les staffs disponibles
        else:
            # TODO: Implementer la logique multi-staff
            # Pour l'instant, retourner des creneaux par defaut
            slots.extend(self._get_default_slots(
                target_date, duration, interval, min_datetime
            ))

        # Retirer les creneaux en conflit avec des RDV existants
        slots = self._filter_conflicting_slots(
            slots, target_date, staff_id, resource_id
        )

        return slots

    def _get_slots_for_user(
        self,
        target_date: date,
        user_id: UUID,
        duration: timedelta,
        interval: timedelta,
        min_datetime: datetime
    ) -> List[Dict[str, Any]]:
        """Genere les creneaux pour un utilisateur."""
        slots = []
        day_of_week = target_date.weekday()

        # Horaires de travail
        wh_list = self.working_hours.get_by_user(user_id)
        wh_day = next((wh for wh in wh_list if wh.day_of_week == day_of_week), None)

        if not wh_day or not wh_day.is_working:
            return []

        # Exceptions (conges, absences)
        exceptions = self.availabilities.get_by_user(
            user_id, target_date, target_date
        )

        is_blocked = any(
            e.availability_type in [AvailabilityType.BLOCKED, AvailabilityType.HOLIDAY, AvailabilityType.OUT_OF_OFFICE]
            for e in exceptions
        )

        if is_blocked:
            return []

        # Generer les creneaux
        start_time = wh_day.start_time or time(9, 0)
        end_time = wh_day.end_time or time(18, 0)

        current = datetime.combine(target_date, start_time)
        end = datetime.combine(target_date, end_time)

        while current + duration <= end:
            # Verifier preavis minimum
            if current >= min_datetime:
                # Verifier si pas dans une pause
                in_break = False
                for brk in (wh_day.breaks or []):
                    brk_start = datetime.combine(target_date, time.fromisoformat(brk["start"]))
                    brk_end = datetime.combine(target_date, time.fromisoformat(brk["end"]))
                    if current < brk_end and current + duration > brk_start:
                        in_break = True
                        break

                if not in_break:
                    slots.append({
                        "start_time": current,
                        "end_time": current + duration,
                        "is_available": True,
                        "staff_id": user_id,
                        "staff_name": None,  # TODO: Resoudre le nom
                        "resource_id": None,
                        "resource_name": None
                    })

            current += interval

        return slots

    def _get_slots_for_resource(
        self,
        target_date: date,
        resource_id: UUID,
        duration: timedelta,
        interval: timedelta,
        min_datetime: datetime
    ) -> List[Dict[str, Any]]:
        """Genere les creneaux pour une ressource."""
        slots = []
        resource = self.resources.get_by_id(resource_id)

        if not resource or not resource.is_available:
            return []

        # Horaires de la ressource
        wh_list = self.working_hours.get_by_resource(resource_id)
        day_of_week = target_date.weekday()
        wh_day = next((wh for wh in wh_list if wh.day_of_week == day_of_week), None)

        # Utiliser les horaires par defaut si non definis
        start_time = (wh_day.start_time if wh_day else None) or time(8, 0)
        end_time = (wh_day.end_time if wh_day else None) or time(20, 0)

        if wh_day and not wh_day.is_working:
            return []

        # Generer les creneaux
        current = datetime.combine(target_date, start_time)
        end = datetime.combine(target_date, end_time)

        while current + duration <= end:
            if current >= min_datetime:
                slots.append({
                    "start_time": current,
                    "end_time": current + duration,
                    "is_available": True,
                    "staff_id": None,
                    "staff_name": None,
                    "resource_id": resource_id,
                    "resource_name": resource.name
                })
            current += interval

        return slots

    def _get_default_slots(
        self,
        target_date: date,
        duration: timedelta,
        interval: timedelta,
        min_datetime: datetime
    ) -> List[Dict[str, Any]]:
        """Genere des creneaux par defaut."""
        slots = []

        # Horaires par defaut: 9h-18h
        start_time = time(9, 0)
        end_time = time(18, 0)

        current = datetime.combine(target_date, start_time)
        end = datetime.combine(target_date, end_time)

        # Pause dejeuner
        lunch_start = datetime.combine(target_date, time(12, 0))
        lunch_end = datetime.combine(target_date, time(14, 0))

        while current + duration <= end:
            if current >= min_datetime:
                # Verifier pause dejeuner
                if not (current < lunch_end and current + duration > lunch_start):
                    slots.append({
                        "start_time": current,
                        "end_time": current + duration,
                        "is_available": True,
                        "staff_id": None,
                        "staff_name": None,
                        "resource_id": None,
                        "resource_name": None
                    })
            current += interval

        return slots

    def _filter_conflicting_slots(
        self,
        slots: List[Dict[str, Any]],
        target_date: date,
        staff_id: Optional[UUID],
        resource_id: Optional[UUID]
    ) -> List[Dict[str, Any]]:
        """Filtre les creneaux en conflit avec des RDV existants."""
        if not slots:
            return []

        # Recuperer les RDV du jour
        existing = self.appointments.get_day_schedule(
            target_date,
            user_id=staff_id,
            resource_id=resource_id
        )

        available_slots = []
        for slot in slots:
            is_free = True
            for apt in existing:
                # Verifier chevauchement
                if slot["start_time"] < apt.end_datetime and slot["end_time"] > apt.start_datetime:
                    is_free = False
                    break

            if is_free:
                available_slots.append(slot)

        return available_slots

    # =========================================================================
    # RENDEZ-VOUS
    # =========================================================================

    def create_appointment(
        self,
        data: dict,
        user_id: UUID,
        check_conflicts: bool = True,
        send_notifications: bool = True
    ) -> Appointment:
        """
        Cree un nouveau rendez-vous.

        Etapes:
        1. Valider les donnees
        2. Verifier les conflits (optionnel)
        3. Creer le rendez-vous
        4. Ajouter les participants
        5. Creer les rappels
        6. Gerer la recurrence
        7. Envoyer les notifications
        """
        logger.info(f"Creating appointment: {data.get('title')}")

        # Validation
        self._validate_appointment_data(data)

        # Verification des conflits
        if check_conflicts:
            conflicts = self._check_conflicts(
                start_datetime=data["start_datetime"],
                end_datetime=data.get("end_datetime") or data["start_datetime"] + timedelta(
                    minutes=data.get("duration_minutes", 30)
                ),
                user_id=data.get("assigned_to") or data.get("organizer_id"),
                resource_id=data.get("resource_id")
            )

            settings = self.settings_repo.get()
            if conflicts and settings.conflict_resolution == "BLOCK":
                raise AppointmentConflictError(
                    "Time slot not available",
                    conflicts=[str(c.id) for c in conflicts]
                )

        # Calcul de end_datetime si non fourni
        if not data.get("end_datetime"):
            duration = data.get("duration_minutes", 30)
            data["end_datetime"] = data["start_datetime"] + timedelta(minutes=duration)
            data["duration_minutes"] = duration
        elif not data.get("duration_minutes"):
            delta = data["end_datetime"] - data["start_datetime"]
            data["duration_minutes"] = int(delta.total_seconds() / 60)

        # Enrichir avec les infos du type si present
        if data.get("type_id"):
            apt_type = self.types.get_by_id(data["type_id"])
            if apt_type:
                data.setdefault("mode", apt_type.default_mode)
                data.setdefault("is_billable", apt_type.is_billable)
                data.setdefault("price", apt_type.default_price)
                data.setdefault("location", apt_type.default_location)

                # Ajouter les rappels par defaut
                if not data.get("reminders") and apt_type.default_reminders:
                    data["reminders"] = apt_type.default_reminders

        # Definir le statut initial
        booking_mode = data.pop("booking_mode", None)
        if booking_mode == BookingMode.INSTANT or not booking_mode:
            data["status"] = AppointmentStatus.CONFIRMED
        else:
            data["status"] = AppointmentStatus.PENDING

        # Definir l'organisateur
        data.setdefault("organizer_id", user_id)

        # Creation
        appointment = self.appointments.create(data, user_id)

        # Gestion de la recurrence
        if appointment.is_recurring and appointment.recurrence_pattern != RecurrencePattern.NONE:
            self._create_recurring_occurrences(appointment, user_id)

        # Notifications
        if send_notifications:
            self._send_booking_notifications(appointment)

        logger.info(f"Created appointment {appointment.code}")
        return appointment

    def _validate_appointment_data(self, data: dict) -> None:
        """Valide les donnees du rendez-vous."""
        if not data.get("title"):
            raise AppointmentValidationError("Title is required")

        if not data.get("start_datetime"):
            raise AppointmentValidationError("Start datetime is required")

        # Verifier que start < end
        if data.get("end_datetime") and data["end_datetime"] <= data["start_datetime"]:
            raise AppointmentValidationError("End datetime must be after start datetime")

        # Verifier les dates futures
        if data["start_datetime"] < datetime.utcnow():
            raise AppointmentValidationError("Cannot create appointment in the past")

    def _check_conflicts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        user_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """Verifie les conflits de planning."""
        return self.appointments.check_conflicts(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            user_id=user_id,
            resource_id=resource_id,
            exclude_id=exclude_id
        )

    def _create_recurring_occurrences(
        self,
        parent: Appointment,
        user_id: UUID
    ) -> List[Appointment]:
        """Cree les occurrences d'un rendez-vous recurrent."""
        occurrences = []

        if not parent.recurrence_end_date and parent.recurrence_end_type != RecurrenceEndType.AFTER_COUNT:
            # Limiter a 1 an par defaut
            end_date = parent.start_datetime.date() + timedelta(days=365)
        else:
            end_date = parent.recurrence_end_date

        max_count = parent.recurrence_end_count or 52  # Max 1 an de weekly

        # Calcul du delta
        delta = {
            RecurrencePattern.DAILY: timedelta(days=parent.recurrence_interval),
            RecurrencePattern.WEEKLY: timedelta(weeks=parent.recurrence_interval),
            RecurrencePattern.BIWEEKLY: timedelta(weeks=2 * parent.recurrence_interval),
            RecurrencePattern.MONTHLY: None,  # Traitement special
            RecurrencePattern.QUARTERLY: None,
            RecurrencePattern.YEARLY: None,
        }.get(parent.recurrence_pattern)

        current_date = parent.start_datetime.date()
        occurrence_index = 1
        count = 0

        while count < max_count:
            # Calculer la prochaine date
            if delta:
                current_date = current_date + delta
            elif parent.recurrence_pattern == RecurrencePattern.MONTHLY:
                # Meme jour du mois suivant
                month = current_date.month + parent.recurrence_interval
                year = current_date.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                day = min(current_date.day, 28)  # Simplifie
                current_date = date(year, month, day)
            elif parent.recurrence_pattern == RecurrencePattern.QUARTERLY:
                month = current_date.month + 3 * parent.recurrence_interval
                year = current_date.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                day = min(current_date.day, 28)
                current_date = date(year, month, day)
            elif parent.recurrence_pattern == RecurrencePattern.YEARLY:
                current_date = date(
                    current_date.year + parent.recurrence_interval,
                    current_date.month,
                    min(current_date.day, 28)
                )
            else:
                break

            # Verifier les limites
            if end_date and current_date > end_date:
                break

            # Verifier les exceptions
            if str(current_date) in (parent.recurrence_exceptions or []):
                continue

            # Creer l'occurrence
            new_start = datetime.combine(current_date, parent.start_datetime.time())
            new_end = new_start + timedelta(minutes=parent.duration_minutes)

            # Verifier les conflits
            conflicts = self._check_conflicts(
                start_datetime=new_start,
                end_datetime=new_end,
                user_id=parent.assigned_to or parent.organizer_id,
                resource_id=parent.resource_id
            )

            if not conflicts:
                occurrence_data = {
                    "title": parent.title,
                    "description": parent.description,
                    "type_id": parent.type_id,
                    "mode": parent.mode,
                    "priority": parent.priority,
                    "start_datetime": new_start,
                    "end_datetime": new_end,
                    "duration_minutes": parent.duration_minutes,
                    "location": parent.location,
                    "contact_id": parent.contact_id,
                    "contact_name": parent.contact_name,
                    "contact_email": parent.contact_email,
                    "organizer_id": parent.organizer_id,
                    "assigned_to": parent.assigned_to,
                    "resource_id": parent.resource_id,
                    "is_billable": parent.is_billable,
                    "price": parent.price,
                    "status": parent.status,
                    "is_recurring": False,
                    "parent_appointment_id": parent.id,
                    "occurrence_index": occurrence_index
                }

                occurrence = self.appointments.create(occurrence_data, user_id)
                occurrences.append(occurrence)

            occurrence_index += 1
            count += 1

        logger.info(f"Created {len(occurrences)} recurring occurrences for {parent.code}")
        return occurrences

    def update_appointment(
        self,
        appointment_id: UUID,
        data: dict,
        user_id: UUID,
        check_conflicts: bool = True
    ) -> Appointment:
        """Met a jour un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        # Verifier le statut
        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise AppointmentStateError("Cannot update completed or cancelled appointment")

        # Verifier les conflits si les dates changent
        if check_conflicts and (data.get("start_datetime") or data.get("end_datetime")):
            start = data.get("start_datetime", appointment.start_datetime)
            end = data.get("end_datetime", appointment.end_datetime)

            conflicts = self._check_conflicts(
                start_datetime=start,
                end_datetime=end,
                user_id=data.get("assigned_to", appointment.assigned_to),
                resource_id=data.get("resource_id", appointment.resource_id),
                exclude_id=appointment_id
            )

            if conflicts:
                raise AppointmentConflictError(
                    "Time slot not available",
                    conflicts=[str(c.id) for c in conflicts]
                )

        return self.appointments.update(appointment, data, user_id)

    def confirm_appointment(
        self,
        appointment_id: UUID,
        user_id: UUID,
        send_notification: bool = True
    ) -> Appointment:
        """Confirme un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status not in [AppointmentStatus.PENDING, AppointmentStatus.DRAFT]:
            raise AppointmentStateError(f"Cannot confirm appointment in status {appointment.status}")

        appointment = self.appointments.confirm(appointment, user_id)

        if send_notification:
            self._send_confirmation_notification(appointment)

        return appointment

    def cancel_appointment(
        self,
        appointment_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        cancel_series: bool = False,
        send_notification: bool = True
    ) -> Appointment:
        """Annule un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise AppointmentStateError(f"Cannot cancel appointment in status {appointment.status}")

        appointment = self.appointments.cancel(appointment, user_id, reason)

        # Annuler la serie si demande
        if cancel_series and appointment.is_recurring:
            children, _ = self.appointments.list(
                filters={"parent_appointment_id": appointment.id},
                page_size=1000
            )
            for child in children:
                if child.status not in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
                    self.appointments.cancel(child, user_id, reason)

        # Notifier la liste d'attente
        self._notify_waitlist_for_slot(appointment)

        if send_notification:
            self._send_cancellation_notification(appointment)

        return appointment

    def reschedule_appointment(
        self,
        appointment_id: UUID,
        new_start: datetime,
        new_end: Optional[datetime],
        user_id: UUID,
        reason: Optional[str] = None,
        send_notification: bool = True
    ) -> Appointment:
        """Replanifie un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise AppointmentStateError(f"Cannot reschedule appointment in status {appointment.status}")

        # Calculer la nouvelle fin si non fournie
        if not new_end:
            new_end = new_start + timedelta(minutes=appointment.duration_minutes)

        # Verifier les conflits
        conflicts = self._check_conflicts(
            start_datetime=new_start,
            end_datetime=new_end,
            user_id=appointment.assigned_to or appointment.organizer_id,
            resource_id=appointment.resource_id,
            exclude_id=appointment_id
        )

        if conflicts:
            raise AppointmentConflictError(
                "New time slot not available",
                conflicts=[str(c.id) for c in conflicts]
            )

        # Liberer l'ancien creneau pour la liste d'attente
        old_start = appointment.start_datetime

        appointment = self.appointments.reschedule(appointment, new_start, new_end, user_id)

        # Mettre a jour les rappels
        self._update_reminders_for_reschedule(appointment, old_start)

        # Notifier la liste d'attente pour l'ancien creneau
        self._notify_waitlist_for_slot(appointment, old_start)

        if send_notification:
            self._send_reschedule_notification(appointment, reason)

        return appointment

    def check_in_appointment(
        self,
        appointment_id: UUID,
        user_id: UUID,
        attendee_id: Optional[UUID] = None
    ) -> Appointment:
        """Check-in d'un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id, with_attendees=True)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status != AppointmentStatus.CONFIRMED:
            raise AppointmentStateError(f"Cannot check in appointment in status {appointment.status}")

        # Check-in d'un participant specifique
        if attendee_id:
            attendee = self.attendees.get_by_id(attendee_id)
            if attendee and attendee.appointment_id == appointment_id:
                self.attendees.check_in(attendee)

        return self.appointments.check_in(appointment, user_id)

    def complete_appointment(
        self,
        appointment_id: UUID,
        user_id: UUID,
        outcome: Optional[str] = None
    ) -> Appointment:
        """Complete un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status not in [
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_PROGRESS
        ]:
            raise AppointmentStateError(f"Cannot complete appointment in status {appointment.status}")

        return self.appointments.complete(appointment, user_id, outcome)

    def mark_no_show(self, appointment_id: UUID, user_id: UUID) -> Appointment:
        """Marque un rendez-vous comme absent."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status != AppointmentStatus.CONFIRMED:
            raise AppointmentStateError(f"Cannot mark no-show for appointment in status {appointment.status}")

        return self.appointments.mark_no_show(appointment, user_id)

    def rate_appointment(
        self,
        appointment_id: UUID,
        rating: int,
        feedback: Optional[str] = None
    ) -> Appointment:
        """Evalue un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status != AppointmentStatus.COMPLETED:
            raise AppointmentStateError("Can only rate completed appointments")

        appointment.rating = rating
        appointment.feedback = feedback
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def delete_appointment(self, appointment_id: UUID, user_id: UUID) -> None:
        """Supprime un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appointment.status not in [AppointmentStatus.DRAFT, AppointmentStatus.PENDING]:
            raise AppointmentStateError("Can only delete draft or pending appointments")

        self.appointments.soft_delete(appointment, user_id)

    # =========================================================================
    # PARTICIPANTS
    # =========================================================================

    def add_attendee(
        self,
        appointment_id: UUID,
        data: dict,
        user_id: UUID,
        send_invitation: bool = True
    ) -> Attendee:
        """Ajoute un participant a un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        attendee = self.attendees.add(appointment_id, data, user_id)

        if send_invitation:
            self._send_invitation(appointment, attendee)

        return attendee

    def update_attendee(
        self,
        attendee_id: UUID,
        data: dict
    ) -> Attendee:
        """Met a jour un participant."""
        attendee = self.attendees.get_by_id(attendee_id)
        if not attendee:
            raise AppointmentNotFoundError(f"Attendee {attendee_id} not found")

        return self.attendees.update(attendee, data)

    def respond_to_invitation(
        self,
        attendee_id: UUID,
        status: AttendeeStatus,
        comment: Optional[str] = None
    ) -> Attendee:
        """Repond a une invitation."""
        attendee = self.attendees.get_by_id(attendee_id)
        if not attendee:
            raise AppointmentNotFoundError(f"Attendee {attendee_id} not found")

        return self.attendees.update_status(attendee, status, comment)

    def remove_attendee(self, attendee_id: UUID) -> None:
        """Retire un participant."""
        attendee = self.attendees.get_by_id(attendee_id)
        if not attendee:
            raise AppointmentNotFoundError(f"Attendee {attendee_id} not found")

        self.attendees.delete(attendee)

    # =========================================================================
    # RAPPELS
    # =========================================================================

    def add_reminder(
        self,
        appointment_id: UUID,
        data: dict
    ) -> Reminder:
        """Ajoute un rappel a un rendez-vous."""
        appointment = self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        # Calculer la date d'envoi
        if not data.get("scheduled_at"):
            data["scheduled_at"] = appointment.start_datetime - timedelta(
                minutes=data.get("minutes_before", 1440)
            )

        return self.reminders.add(appointment_id, data)

    def get_pending_reminders(self, limit: int = 100) -> List[Reminder]:
        """Recupere les rappels a envoyer."""
        return self.reminders.get_pending(limit)

    def send_reminder(self, reminder_id: UUID) -> Reminder:
        """Envoie un rappel."""
        reminder = self.reminders.get_by_id(reminder_id)
        if not reminder:
            raise AppointmentNotFoundError(f"Reminder {reminder_id} not found")

        try:
            # TODO: Implementer l'envoi reel (email, SMS, etc.)
            self._send_reminder_notification(reminder)
            return self.reminders.mark_sent(reminder)
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder_id}: {e}")
            return self.reminders.mark_failed(reminder, str(e))

    def _update_reminders_for_reschedule(
        self,
        appointment: Appointment,
        old_start: datetime
    ) -> None:
        """Met a jour les rappels apres replanification."""
        reminders = self.reminders.get_by_appointment(appointment.id)
        for reminder in reminders:
            if reminder.status == ReminderStatus.PENDING:
                # Recalculer la date d'envoi
                delta = old_start - reminder.scheduled_at
                reminder.scheduled_at = appointment.start_datetime - delta
                self.db.commit()

    # =========================================================================
    # LISTE D'ATTENTE
    # =========================================================================

    def add_to_waitlist(self, data: dict) -> WaitlistEntry:
        """Ajoute a la liste d'attente."""
        return self.waitlist.add(data)

    def get_waitlist(
        self,
        type_id: Optional[UUID] = None,
        status: str = "waiting",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WaitlistEntry], int]:
        """Recupere la liste d'attente."""
        return self.waitlist.list(type_id, status, page, page_size)

    def _notify_waitlist_for_slot(
        self,
        appointment: Appointment,
        slot_datetime: Optional[datetime] = None
    ) -> None:
        """Notifie la liste d'attente d'un creneau libere."""
        slot_date = (slot_datetime or appointment.start_datetime).date()

        entries, _ = self.waitlist.list(
            type_id=appointment.type_id,
            status="waiting"
        )

        for entry in entries:
            # Verifier les preferences de date
            if entry.preferred_dates and slot_date not in entry.preferred_dates:
                continue

            # Notifier
            self.waitlist.notify(entry)

            # Envoyer la notification
            # TODO: Implementer l'envoi reel
            logger.info(f"Notified waitlist entry {entry.id} for slot on {slot_date}")
            break  # Un seul a la fois

    def convert_waitlist_to_appointment(
        self,
        entry_id: UUID,
        appointment_data: dict,
        user_id: UUID
    ) -> Appointment:
        """Convertit une entree de liste d'attente en rendez-vous."""
        entry = self.waitlist.get_by_id(entry_id)
        if not entry:
            raise AppointmentNotFoundError(f"Waitlist entry {entry_id} not found")

        # Creer le rendez-vous
        appointment_data.setdefault("contact_name", entry.contact_name)
        appointment_data.setdefault("contact_email", entry.contact_email)
        appointment_data.setdefault("contact_phone", entry.contact_phone)
        appointment_data.setdefault("contact_id", entry.contact_id)
        appointment_data.setdefault("type_id", entry.type_id)

        appointment = self.create_appointment(appointment_data, user_id)

        # Marquer comme converti
        self.waitlist.convert(entry, appointment.id)

        return appointment

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_statistics(
        self,
        period_start: date,
        period_end: date,
        type_id: Optional[UUID] = None,
        staff_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calcule les statistiques des rendez-vous."""
        appointments = self.appointments.get_by_date_range(
            start_date=period_start,
            end_date=period_end,
            user_id=staff_id
        )

        if type_id:
            appointments = [a for a in appointments if a.type_id == type_id]

        stats = {
            "tenant_id": self.tenant_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_appointments": len(appointments),
            "total_confirmed": 0,
            "total_completed": 0,
            "total_cancelled": 0,
            "total_no_shows": 0,
            "total_rescheduled": 0,
            "total_duration_minutes": 0,
            "total_revenue": Decimal("0"),
            "by_status": {},
            "by_mode": {},
            "by_type": {},
            "by_day_of_week": {},
            "by_hour": {},
            "by_staff": {}
        }

        for apt in appointments:
            # Par statut
            status = apt.status.value if apt.status else "UNKNOWN"
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            if apt.status == AppointmentStatus.CONFIRMED:
                stats["total_confirmed"] += 1
            elif apt.status == AppointmentStatus.COMPLETED:
                stats["total_completed"] += 1
                stats["total_duration_minutes"] += apt.duration_minutes or 0
                if apt.price:
                    stats["total_revenue"] += apt.price
            elif apt.status == AppointmentStatus.CANCELLED:
                stats["total_cancelled"] += 1
            elif apt.status == AppointmentStatus.NO_SHOW:
                stats["total_no_shows"] += 1
            elif apt.status == AppointmentStatus.RESCHEDULED:
                stats["total_rescheduled"] += 1

            # Par mode
            mode = apt.mode.value if apt.mode else "UNKNOWN"
            stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1

            # Par type
            if apt.type_id:
                type_key = str(apt.type_id)
                stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1

            # Par jour de semaine
            day = apt.start_datetime.strftime("%A")
            stats["by_day_of_week"][day] = stats["by_day_of_week"].get(day, 0) + 1

            # Par heure
            hour = apt.start_datetime.strftime("%H:00")
            stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1

            # Par staff
            if apt.assigned_to:
                staff_key = str(apt.assigned_to)
                stats["by_staff"][staff_key] = stats["by_staff"].get(staff_key, 0) + 1

        # Calculs derives
        if stats["total_appointments"] > 0:
            stats["completion_rate"] = Decimal(stats["total_completed"]) / Decimal(stats["total_appointments"]) * 100
            stats["no_show_rate"] = Decimal(stats["total_no_shows"]) / Decimal(stats["total_appointments"]) * 100
            stats["cancellation_rate"] = Decimal(stats["total_cancelled"]) / Decimal(stats["total_appointments"]) * 100

        if stats["total_completed"] > 0:
            stats["avg_duration_minutes"] = stats["total_duration_minutes"] // stats["total_completed"]
            stats["avg_revenue_per_appointment"] = stats["total_revenue"] / stats["total_completed"]

        stats["total_duration_hours"] = Decimal(stats["total_duration_minutes"]) / 60

        # Jours/heures les plus charges
        if stats["by_day_of_week"]:
            stats["busiest_day"] = max(stats["by_day_of_week"], key=stats["by_day_of_week"].get)
        if stats["by_hour"]:
            stats["busiest_hour"] = max(stats["by_hour"], key=stats["by_hour"].get)

        return stats

    # =========================================================================
    # PARAMETRES
    # =========================================================================

    def get_settings(self) -> BookingSettings:
        """Recupere les parametres de reservation."""
        return self.settings_repo.get()

    def update_settings(self, data: dict, user_id: UUID) -> BookingSettings:
        """Met a jour les parametres de reservation."""
        return self.settings_repo.update(data, user_id)

    # =========================================================================
    # NOTIFICATIONS (stubs)
    # =========================================================================

    def _send_booking_notifications(self, appointment: Appointment) -> None:
        """Envoie les notifications de reservation."""
        logger.info(f"Sending booking notification for {appointment.code}")
        # TODO: Implementer avec le module email/notifications

    def _send_confirmation_notification(self, appointment: Appointment) -> None:
        """Envoie la notification de confirmation."""
        logger.info(f"Sending confirmation notification for {appointment.code}")

    def _send_cancellation_notification(self, appointment: Appointment) -> None:
        """Envoie la notification d'annulation."""
        logger.info(f"Sending cancellation notification for {appointment.code}")

    def _send_reschedule_notification(
        self,
        appointment: Appointment,
        reason: Optional[str]
    ) -> None:
        """Envoie la notification de replanification."""
        logger.info(f"Sending reschedule notification for {appointment.code}")

    def _send_invitation(self, appointment: Appointment, attendee: Attendee) -> None:
        """Envoie une invitation a un participant."""
        logger.info(f"Sending invitation to {attendee.email or attendee.name}")

    def _send_reminder_notification(self, reminder: Reminder) -> None:
        """Envoie un rappel."""
        logger.info(f"Sending reminder {reminder.id}")


# ============================================================================
# FACTORY
# ============================================================================

def create_appointment_service(db: Session, tenant_id: str) -> AppointmentService:
    """Factory pour creer un service de rendez-vous."""
    return AppointmentService(db, tenant_id)
