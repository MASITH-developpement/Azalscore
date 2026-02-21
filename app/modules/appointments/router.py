"""
AZALS MODULE - Appointments - Router
=====================================

Endpoints REST pour le module Rendez-vous.

Fonctionnalites:
- CRUD complet pour rendez-vous, types, ressources
- Gestion des participants et rappels
- Creneaux disponibles
- Liste d'attente
- Statistiques
- Autocomplete
"""

import math
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import AppointmentStatus, AppointmentMode, AttendeeStatus
from .schemas import (
    # Types
    AppointmentTypeCreate, AppointmentTypeUpdate, AppointmentTypeResponse,
    AppointmentTypeSummary,
    # Resources
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceSummary,
    # Appointments
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentSummary, AppointmentList, AppointmentFilters,
    # Attendees
    AttendeeCreate, AttendeeUpdate, AttendeeResponse,
    # Reminders
    ReminderCreate, ReminderResponse,
    # Availability
    AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse,
    # Working Hours
    WorkingHoursCreate, WorkingHoursUpdate, WorkingHoursResponse,
    # Waitlist
    WaitlistEntryCreate, WaitlistEntryResponse,
    # Slots
    AvailableSlotsRequest, AvailableSlotsResponse, TimeSlot,
    # Settings
    BookingSettingsUpdate, BookingSettingsResponse,
    # Stats
    AppointmentStats,
    # Actions
    ConfirmAppointmentRequest, CancelAppointmentRequest,
    RescheduleAppointmentRequest, CheckInRequest,
    CompleteAppointmentRequest, RateAppointmentRequest,
    # Autocomplete
    AutocompleteResponse, AutocompleteItem,
)
from .service import AppointmentService
from .exceptions import (
    AppointmentNotFoundError, AppointmentConflictError,
    AppointmentStateError, AppointmentValidationError,
    TypeNotFoundError, ResourceNotFoundError
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def get_appointment_service(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> AppointmentService:
    """Factory pour le service de rendez-vous."""
    return AppointmentService(db, current_user.tenant_id)


# ============================================================================
# TYPES DE RENDEZ-VOUS
# ============================================================================

@router.get("/types", response_model=List[AppointmentTypeSummary])
async def list_types(
    is_active: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.type.read"))
):
    """Lister les types de rendez-vous."""
    items, total = service.list_types(
        is_active=is_active,
        is_public=is_public,
        category=category,
        page=page,
        page_size=page_size
    )
    return items


@router.get("/types/{type_id}", response_model=AppointmentTypeResponse)
async def get_type(
    type_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.type.read"))
):
    """Obtenir un type de rendez-vous."""
    apt_type = service.types.get_by_id(type_id)
    if not apt_type:
        raise HTTPException(status_code=404, detail="Type de rendez-vous non trouve")
    return apt_type


@router.post("/types", response_model=AppointmentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_type(
    data: AppointmentTypeCreate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.type.create"))
):
    """Creer un type de rendez-vous."""
    if data.code and service.types.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code deja existant")

    apt_type = service.create_type(data.model_dump(), current_user.id)
    return apt_type


@router.put("/types/{type_id}", response_model=AppointmentTypeResponse)
async def update_type(
    type_id: UUID,
    data: AppointmentTypeUpdate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.type.update"))
):
    """Mettre a jour un type de rendez-vous."""
    try:
        apt_type = service.update_type(type_id, data.model_dump(exclude_unset=True), current_user.id)
        return apt_type
    except TypeNotFoundError:
        raise HTTPException(status_code=404, detail="Type de rendez-vous non trouve")


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_type(
    type_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.type.delete"))
):
    """Supprimer un type de rendez-vous."""
    try:
        service.delete_type(type_id, current_user.id)
    except TypeNotFoundError:
        raise HTTPException(status_code=404, detail="Type de rendez-vous non trouve")


# ============================================================================
# RESSOURCES
# ============================================================================

@router.get("/resources", response_model=List[ResourceSummary])
async def list_resources(
    resource_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_available: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.resource.read"))
):
    """Lister les ressources."""
    items, _ = service.list_resources(
        resource_type=resource_type,
        is_active=is_active,
        is_available=is_available,
        page=page,
        page_size=page_size
    )
    return items


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.resource.read"))
):
    """Obtenir une ressource."""
    resource = service.resources.get_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource non trouvee")
    return resource


@router.post("/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: ResourceCreate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.resource.create"))
):
    """Creer une ressource."""
    if data.code and service.resources.code_exists(data.code):
        raise HTTPException(status_code=409, detail="Code deja existant")

    resource = service.create_resource(data.model_dump(), current_user.id)
    return resource


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: UUID,
    data: ResourceUpdate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.resource.update"))
):
    """Mettre a jour une ressource."""
    try:
        resource = service.update_resource(resource_id, data.model_dump(exclude_unset=True), current_user.id)
        return resource
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Ressource non trouvee")


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.resource.delete"))
):
    """Supprimer une ressource."""
    try:
        service.delete_resource(resource_id, current_user.id)
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Ressource non trouvee")


# ============================================================================
# CRENEAUX DISPONIBLES
# ============================================================================

@router.get("/slots/available")
async def get_available_slots(
    date_start: date = Query(...),
    date_end: Optional[date] = Query(None),
    type_id: Optional[UUID] = Query(None),
    staff_id: Optional[UUID] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    duration_minutes: Optional[int] = Query(None),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.slots.read"))
):
    """Obtenir les creneaux disponibles."""
    end_date = date_end or date_start
    results = []

    current_date = date_start
    while current_date <= end_date:
        slots = service.get_available_slots(
            target_date=current_date,
            type_id=type_id,
            staff_id=staff_id,
            resource_id=resource_id,
            duration_minutes=duration_minutes
        )
        results.append({
            "date": current_date,
            "slots": slots,
            "type_id": type_id,
            "duration_minutes": duration_minutes or 30
        })
        current_date = current_date + __import__('datetime').timedelta(days=1)

    return results


# ============================================================================
# RENDEZ-VOUS
# ============================================================================

@router.get("", response_model=AppointmentList)
async def list_appointments(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[AppointmentStatus]] = Query(None),
    mode: Optional[List[AppointmentMode]] = Query(None),
    type_id: Optional[UUID] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    contact_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    organizer_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_recurring: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("start_datetime"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Lister les rendez-vous."""
    filters = {
        "search": search,
        "status": [s.value for s in status] if status else None,
        "mode": [m.value for m in mode] if mode else None,
        "type_id": type_id,
        "resource_id": resource_id,
        "contact_id": contact_id,
        "customer_id": customer_id,
        "organizer_id": organizer_id,
        "assigned_to": assigned_to,
        "date_from": date_from,
        "date_to": date_to,
        "is_recurring": is_recurring,
    }

    items, total = service.appointments.list(
        filters={k: v for k, v in filters.items() if v is not None},
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    return AppointmentList(
        items=[AppointmentSummary(
            id=a.id,
            code=a.code,
            title=a.title,
            status=a.status,
            mode=a.mode,
            priority=a.priority,
            start_datetime=a.start_datetime,
            end_datetime=a.end_datetime,
            duration_minutes=a.duration_minutes,
            all_day=a.all_day,
            location=a.location,
            contact_name=a.contact_name,
            organizer_name=a.organizer_name,
            type_id=a.type_id,
            resource_id=a.resource_id,
            is_recurring=a.is_recurring,
            attendee_count=len(list(a.attendees)) if a.attendees else 0
        ) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/my", response_model=AppointmentList)
async def list_my_appointments(
    status: Optional[List[AppointmentStatus]] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.read"))
):
    """Lister mes rendez-vous."""
    filters = {
        "status": [s.value for s in status] if status else None,
        "organizer_id": current_user.id,
        "date_from": date_from,
        "date_to": date_to,
    }

    items, total = service.appointments.list(
        filters={k: v for k, v in filters.items() if v is not None},
        page=page,
        page_size=page_size
    )

    return AppointmentList(
        items=[AppointmentSummary(
            id=a.id,
            code=a.code,
            title=a.title,
            status=a.status,
            mode=a.mode,
            priority=a.priority,
            start_datetime=a.start_datetime,
            end_datetime=a.end_datetime,
            duration_minutes=a.duration_minutes,
            all_day=a.all_day,
            location=a.location,
            contact_name=a.contact_name,
            organizer_name=a.organizer_name,
            type_id=a.type_id,
            resource_id=a.resource_id,
            is_recurring=a.is_recurring,
            attendee_count=len(list(a.attendees)) if a.attendees else 0
        ) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/upcoming", response_model=List[AppointmentSummary])
async def get_upcoming_appointments(
    limit: int = Query(10, ge=1, le=50),
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.read"))
):
    """Obtenir les prochains rendez-vous."""
    appointments = service.appointments.get_upcoming(
        user_id=current_user.id,
        limit=limit
    )
    return [AppointmentSummary(
        id=a.id,
        code=a.code,
        title=a.title,
        status=a.status,
        mode=a.mode,
        priority=a.priority,
        start_datetime=a.start_datetime,
        end_datetime=a.end_datetime,
        duration_minutes=a.duration_minutes,
        all_day=a.all_day,
        location=a.location,
        contact_name=a.contact_name,
        organizer_name=a.organizer_name,
        type_id=a.type_id,
        resource_id=a.resource_id,
        is_recurring=a.is_recurring,
        attendee_count=len(list(a.attendees)) if a.attendees else 0
    ) for a in appointments]


@router.get("/day/{target_date}", response_model=List[AppointmentSummary])
async def get_day_schedule(
    target_date: date,
    user_id: Optional[UUID] = Query(None),
    resource_id: Optional[UUID] = Query(None),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Obtenir le planning d'une journee."""
    appointments = service.appointments.get_day_schedule(
        target_date=target_date,
        user_id=user_id,
        resource_id=resource_id
    )
    return [AppointmentSummary(
        id=a.id,
        code=a.code,
        title=a.title,
        status=a.status,
        mode=a.mode,
        priority=a.priority,
        start_datetime=a.start_datetime,
        end_datetime=a.end_datetime,
        duration_minutes=a.duration_minutes,
        all_day=a.all_day,
        location=a.location,
        contact_name=a.contact_name,
        organizer_name=a.organizer_name,
        type_id=a.type_id,
        resource_id=a.resource_id,
        is_recurring=a.is_recurring,
        attendee_count=len(list(a.attendees)) if a.attendees else 0
    ) for a in appointments]


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_appointments(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Autocomplete rendez-vous."""
    results = service.appointments.autocomplete(q, limit)
    return AutocompleteResponse(items=[AutocompleteItem(**r) for r in results])


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Obtenir un rendez-vous."""
    appointment = service.appointments.get_by_id(
        appointment_id,
        with_attendees=True,
        with_reminders=True
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    return appointment


@router.get("/code/{confirmation_code}", response_model=AppointmentResponse)
async def get_appointment_by_code(
    confirmation_code: str,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Obtenir un rendez-vous par code de confirmation."""
    appointment = service.appointments.get_by_confirmation_code(confirmation_code)
    if not appointment:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    return appointment


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    check_conflicts: bool = Query(True),
    send_notifications: bool = Query(True),
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.create"))
):
    """Creer un rendez-vous."""
    try:
        appointment = service.create_appointment(
            data.model_dump(),
            current_user.id,
            check_conflicts=check_conflicts,
            send_notifications=send_notifications
        )
        return appointment
    except AppointmentConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AppointmentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    check_conflicts: bool = Query(True),
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.update"))
):
    """Mettre a jour un rendez-vous."""
    try:
        appointment = service.update_appointment(
            appointment_id,
            data.model_dump(exclude_unset=True),
            current_user.id,
            check_conflicts=check_conflicts
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: UUID,
    data: Optional[ConfirmAppointmentRequest] = None,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.confirm"))
):
    """Confirmer un rendez-vous."""
    try:
        send_notification = data.send_notification if data else True
        appointment = service.confirm_appointment(
            appointment_id,
            current_user.id,
            send_notification=send_notification
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    data: Optional[CancelAppointmentRequest] = None,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.cancel"))
):
    """Annuler un rendez-vous."""
    try:
        appointment = service.cancel_appointment(
            appointment_id,
            current_user.id,
            reason=data.reason if data else None,
            cancel_series=data.cancel_series if data else False,
            send_notification=data.send_notification if data else True
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: UUID,
    data: RescheduleAppointmentRequest,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.reschedule"))
):
    """Replanifier un rendez-vous."""
    try:
        appointment = service.reschedule_appointment(
            appointment_id,
            data.new_start_datetime,
            data.new_end_datetime,
            current_user.id,
            reason=data.reason,
            send_notification=data.send_notification
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/check-in", response_model=AppointmentResponse)
async def check_in_appointment(
    appointment_id: UUID,
    data: Optional[CheckInRequest] = None,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.checkin"))
):
    """Check-in d'un rendez-vous."""
    try:
        appointment = service.check_in_appointment(
            appointment_id,
            current_user.id,
            attendee_id=data.attendee_id if data else None
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: UUID,
    data: Optional[CompleteAppointmentRequest] = None,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.complete"))
):
    """Completer un rendez-vous."""
    try:
        appointment = service.complete_appointment(
            appointment_id,
            current_user.id,
            outcome=data.outcome if data else None
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/no-show", response_model=AppointmentResponse)
async def mark_no_show(
    appointment_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.update"))
):
    """Marquer un rendez-vous comme absent."""
    try:
        appointment = service.mark_no_show(appointment_id, current_user.id)
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{appointment_id}/rate", response_model=AppointmentResponse)
async def rate_appointment(
    appointment_id: UUID,
    data: RateAppointmentRequest,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Evaluer un rendez-vous."""
    try:
        appointment = service.rate_appointment(
            appointment_id,
            data.rating,
            data.feedback
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.delete"))
):
    """Supprimer un rendez-vous."""
    try:
        service.delete_appointment(appointment_id, current_user.id)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")
    except AppointmentStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PARTICIPANTS
# ============================================================================

@router.get("/{appointment_id}/attendees", response_model=List[AttendeeResponse])
async def list_attendees(
    appointment_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Lister les participants d'un rendez-vous."""
    appointment = service.appointments.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")

    return service.attendees.get_by_appointment(appointment_id)


@router.post("/{appointment_id}/attendees", response_model=AttendeeResponse, status_code=status.HTTP_201_CREATED)
async def add_attendee(
    appointment_id: UUID,
    data: AttendeeCreate,
    send_invitation: bool = Query(True),
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.update"))
):
    """Ajouter un participant."""
    try:
        attendee = service.add_attendee(
            appointment_id,
            data.model_dump(),
            current_user.id,
            send_invitation=send_invitation
        )
        return attendee
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")


@router.put("/{appointment_id}/attendees/{attendee_id}", response_model=AttendeeResponse)
async def update_attendee(
    appointment_id: UUID,
    attendee_id: UUID,
    data: AttendeeUpdate,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.update"))
):
    """Mettre a jour un participant."""
    try:
        attendee = service.update_attendee(attendee_id, data.model_dump(exclude_unset=True))
        return attendee
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Participant non trouve")


@router.post("/{appointment_id}/attendees/{attendee_id}/respond", response_model=AttendeeResponse)
async def respond_to_invitation(
    appointment_id: UUID,
    attendee_id: UUID,
    status: AttendeeStatus = Query(...),
    comment: Optional[str] = Query(None),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Repondre a une invitation."""
    try:
        attendee = service.respond_to_invitation(attendee_id, status, comment)
        return attendee
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Participant non trouve")


@router.delete("/{appointment_id}/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_attendee(
    appointment_id: UUID,
    attendee_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.update"))
):
    """Retirer un participant."""
    try:
        service.remove_attendee(attendee_id)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Participant non trouve")


# ============================================================================
# RAPPELS
# ============================================================================

@router.get("/{appointment_id}/reminders", response_model=List[ReminderResponse])
async def list_reminders(
    appointment_id: UUID,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.read"))
):
    """Lister les rappels d'un rendez-vous."""
    return service.reminders.get_by_appointment(appointment_id)


@router.post("/{appointment_id}/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def add_reminder(
    appointment_id: UUID,
    data: ReminderCreate,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.update"))
):
    """Ajouter un rappel."""
    try:
        reminder = service.add_reminder(appointment_id, data.model_dump())
        return reminder
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouve")


# ============================================================================
# LISTE D'ATTENTE
# ============================================================================

@router.get("/waitlist", response_model=List[WaitlistEntryResponse])
async def list_waitlist(
    type_id: Optional[UUID] = Query(None),
    status: str = Query("waiting"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.waitlist.read"))
):
    """Lister la liste d'attente."""
    items, _ = service.get_waitlist(type_id, status, page, page_size)
    return items


@router.post("/waitlist", response_model=WaitlistEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_to_waitlist(
    data: WaitlistEntryCreate,
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.waitlist.create"))
):
    """Ajouter a la liste d'attente."""
    entry = service.add_to_waitlist(data.model_dump())
    return entry


@router.post("/waitlist/{entry_id}/convert", response_model=AppointmentResponse)
async def convert_waitlist_to_appointment(
    entry_id: UUID,
    data: AppointmentCreate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.create"))
):
    """Convertir une entree de liste d'attente en rendez-vous."""
    try:
        appointment = service.convert_waitlist_to_appointment(
            entry_id,
            data.model_dump(),
            current_user.id
        )
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(status_code=404, detail="Entree liste d'attente non trouvee")


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=AppointmentStats)
async def get_statistics(
    period_start: date = Query(...),
    period_end: date = Query(...),
    type_id: Optional[UUID] = Query(None),
    staff_id: Optional[UUID] = Query(None),
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.stats.read"))
):
    """Obtenir les statistiques des rendez-vous."""
    stats = service.get_statistics(
        period_start=period_start,
        period_end=period_end,
        type_id=type_id,
        staff_id=staff_id
    )
    return stats


# ============================================================================
# PARAMETRES
# ============================================================================

@router.get("/settings", response_model=BookingSettingsResponse)
async def get_settings(
    service: AppointmentService = Depends(get_appointment_service),
    _: None = Depends(require_permission("appointments.settings.read"))
):
    """Obtenir les parametres de reservation."""
    return service.get_settings()


@router.put("/settings", response_model=BookingSettingsResponse)
async def update_settings(
    data: BookingSettingsUpdate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user=Depends(get_current_user),
    _: None = Depends(require_permission("appointments.settings.update"))
):
    """Mettre a jour les parametres de reservation."""
    return service.update_settings(data.model_dump(exclude_unset=True), current_user.id)
