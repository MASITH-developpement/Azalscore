"""
AZALS MODULE - Appointments - Schemas Pydantic
===============================================

Schemas de validation et serialisation pour le module Rendez-vous.
"""
from __future__ import annotations


from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import (
    AppointmentStatus, AppointmentMode, AppointmentPriority,
    RecurrencePattern, RecurrenceEndType,
    ReminderType, ReminderStatus,
    AttendeeRole, AttendeeStatus,
    AvailabilityType, BookingMode, ResourceType,
    SyncProvider, ConflictResolution
)


# ============================================================================
# SCHEMAS TYPE DE RENDEZ-VOUS
# ============================================================================

class AppointmentTypeBase(BaseModel):
    """Base pour les types de rendez-vous."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)

    default_duration_minutes: int = Field(default=30, ge=5, le=1440)
    min_duration_minutes: Optional[int] = Field(None, ge=5)
    max_duration_minutes: Optional[int] = Field(None, le=1440)
    buffer_before_minutes: int = Field(default=0, ge=0)
    buffer_after_minutes: int = Field(default=0, ge=0)

    default_mode: AppointmentMode = AppointmentMode.IN_PERSON
    allowed_modes: List[AppointmentMode] = Field(default_factory=list)

    is_billable: bool = False
    default_price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EUR", max_length=3)
    requires_payment: bool = False
    deposit_amount: Optional[Decimal] = None
    deposit_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    booking_mode: BookingMode = BookingMode.INSTANT
    min_notice_hours: int = Field(default=24, ge=0)
    max_advance_days: int = Field(default=60, ge=1)
    cancellation_hours: int = Field(default=24, ge=0)
    max_participants: int = Field(default=1, ge=1)
    allow_guest_booking: bool = False
    allow_waitlist: bool = True

    booking_form_fields: List[Dict[str, Any]] = Field(default_factory=list)
    booking_questions: List[Dict[str, Any]] = Field(default_factory=list)
    default_reminders: List[Dict[str, Any]] = Field(default_factory=list)

    assigned_resources: List[UUID] = Field(default_factory=list)
    assigned_staff: List[UUID] = Field(default_factory=list)
    requires_resource: bool = False

    default_location: Optional[str] = None
    video_provider: Optional[str] = None

    is_active: bool = True
    is_public: bool = True
    sort_order: int = 0


class AppointmentTypeCreate(AppointmentTypeBase):
    """Creation d'un type de rendez-vous."""
    code: Optional[str] = Field(None, max_length=30)


class AppointmentTypeUpdate(BaseModel):
    """Mise a jour d'un type de rendez-vous."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None

    default_duration_minutes: Optional[int] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None

    default_mode: Optional[AppointmentMode] = None
    allowed_modes: Optional[List[AppointmentMode]] = None

    is_billable: Optional[bool] = None
    default_price: Optional[Decimal] = None
    currency: Optional[str] = None
    requires_payment: Optional[bool] = None
    deposit_amount: Optional[Decimal] = None
    deposit_percentage: Optional[Decimal] = None

    booking_mode: Optional[BookingMode] = None
    min_notice_hours: Optional[int] = None
    max_advance_days: Optional[int] = None
    cancellation_hours: Optional[int] = None
    max_participants: Optional[int] = None
    allow_guest_booking: Optional[bool] = None
    allow_waitlist: Optional[bool] = None

    default_reminders: Optional[List[Dict[str, Any]]] = None
    assigned_resources: Optional[List[UUID]] = None
    assigned_staff: Optional[List[UUID]] = None

    default_location: Optional[str] = None
    video_provider: Optional[str] = None

    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


class AppointmentTypeResponse(AppointmentTypeBase):
    """Reponse type de rendez-vous."""
    id: UUID
    tenant_id: str
    code: str
    is_deleted: bool
    version: int
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime


class AppointmentTypeSummary(BaseModel):
    """Resume pour les listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: Optional[str] = None
    color: Optional[str] = None
    default_duration_minutes: int
    default_mode: AppointmentMode
    is_billable: bool
    default_price: Optional[Decimal] = None
    is_active: bool


# ============================================================================
# SCHEMAS RESSOURCE
# ============================================================================

class ResourceBase(BaseModel):
    """Base pour les ressources."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resource_type: ResourceType = ResourceType.ROOM
    color: Optional[str] = None
    image_url: Optional[str] = None

    capacity: Optional[int] = Field(None, ge=1)

    location: Optional[str] = None
    address: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    amenities: List[str] = Field(default_factory=list)

    is_billable: bool = False
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    currency: str = "EUR"

    is_available: bool = True
    availability_schedule: Dict[str, Any] = Field(default_factory=dict)
    conflict_resolution: ConflictResolution = ConflictResolution.BLOCK

    staff_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class ResourceCreate(ResourceBase):
    """Creation d'une ressource."""
    code: Optional[str] = Field(None, max_length=30)


class ResourceUpdate(BaseModel):
    """Mise a jour d'une ressource."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    address: Optional[str] = None
    amenities: Optional[List[str]] = None
    is_billable: Optional[bool] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    is_available: Optional[bool] = None
    availability_schedule: Optional[Dict[str, Any]] = None
    conflict_resolution: Optional[ConflictResolution] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ResourceResponse(ResourceBase):
    """Reponse ressource."""
    id: UUID
    tenant_id: str
    code: str
    is_deleted: bool
    version: int
    created_at: datetime
    updated_at: datetime


class ResourceSummary(BaseModel):
    """Resume ressource."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    resource_type: ResourceType
    capacity: Optional[int] = None
    is_available: bool
    is_active: bool


# ============================================================================
# SCHEMAS PARTICIPANT
# ============================================================================

class AttendeeBase(BaseModel):
    """Base pour les participants."""
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None

    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

    role: AttendeeRole = AttendeeRole.REQUIRED
    notes: Optional[str] = None


class AttendeeCreate(AttendeeBase):
    """Creation d'un participant."""
    pass


class AttendeeUpdate(BaseModel):
    """Mise a jour d'un participant."""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[AttendeeRole] = None
    status: Optional[AttendeeStatus] = None
    response_comment: Optional[str] = None
    notes: Optional[str] = None


class AttendeeResponse(AttendeeBase):
    """Reponse participant."""
    id: UUID
    tenant_id: str
    appointment_id: UUID
    status: AttendeeStatus
    responded_at: Optional[datetime] = None
    response_comment: Optional[str] = None
    invitation_sent_at: Optional[datetime] = None
    checked_in: bool
    checked_in_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# SCHEMAS RAPPEL
# ============================================================================

class ReminderBase(BaseModel):
    """Base pour les rappels."""
    model_config = ConfigDict(from_attributes=True)

    reminder_type: ReminderType = ReminderType.EMAIL
    minutes_before: int = Field(default=1440, ge=0)  # 24h
    recipient_type: str = "attendee"
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    template_id: Optional[UUID] = None
    subject: Optional[str] = None
    message: Optional[str] = None


class ReminderCreate(ReminderBase):
    """Creation d'un rappel."""
    scheduled_at: Optional[datetime] = None  # Calcule automatiquement si non fourni


class ReminderResponse(ReminderBase):
    """Reponse rappel."""
    id: UUID
    tenant_id: str
    appointment_id: UUID
    scheduled_at: datetime
    status: ReminderStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    retry_count: int
    created_at: datetime


# ============================================================================
# SCHEMAS RENDEZ-VOUS
# ============================================================================

class AppointmentBase(BaseModel):
    """Base pour les rendez-vous."""
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    internal_notes: Optional[str] = None

    type_id: Optional[UUID] = None
    mode: AppointmentMode = AppointmentMode.IN_PERSON
    priority: AppointmentPriority = AppointmentPriority.NORMAL

    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5)
    all_day: bool = False
    timezone: str = "Europe/Paris"

    location: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    video_provider: Optional[str] = None
    video_link: Optional[str] = None

    contact_id: Optional[UUID] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    customer_id: Optional[UUID] = None

    organizer_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None

    resource_id: Optional[UUID] = None

    is_billable: bool = False
    price: Optional[Decimal] = None
    deposit_amount: Optional[Decimal] = None
    currency: str = "EUR"

    # Recurrence
    is_recurring: bool = False
    recurrence_pattern: RecurrencePattern = RecurrencePattern.NONE
    recurrence_interval: int = 1
    recurrence_days: List[int] = Field(default_factory=list)
    recurrence_day_of_month: Optional[int] = None
    recurrence_end_type: RecurrenceEndType = RecurrenceEndType.NEVER
    recurrence_end_date: Optional[date] = None
    recurrence_end_count: Optional[int] = None

    # Liens CRM
    lead_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    ticket_id: Optional[UUID] = None

    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"


class AppointmentCreate(AppointmentBase):
    """Creation d'un rendez-vous."""
    code: Optional[str] = Field(None, max_length=30)
    attendees: List[AttendeeCreate] = Field(default_factory=list)
    reminders: List[ReminderCreate] = Field(default_factory=list)
    send_invitations: bool = True

    @model_validator(mode='after')
    def validate_datetime(self):
        if self.end_datetime and self.start_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValueError("end_datetime must be after start_datetime")
        elif self.duration_minutes:
            from datetime import timedelta
            self.end_datetime = self.start_datetime + timedelta(minutes=self.duration_minutes)
        elif not self.end_datetime:
            from datetime import timedelta
            self.end_datetime = self.start_datetime + timedelta(minutes=30)
        return self


class AppointmentUpdate(BaseModel):
    """Mise a jour d'un rendez-vous."""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None

    type_id: Optional[UUID] = None
    mode: Optional[AppointmentMode] = None
    priority: Optional[AppointmentPriority] = None

    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    all_day: Optional[bool] = None
    timezone: Optional[str] = None

    location: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    video_provider: Optional[str] = None
    video_link: Optional[str] = None

    contact_id: Optional[UUID] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    assigned_to: Optional[UUID] = None
    resource_id: Optional[UUID] = None

    is_billable: Optional[bool] = None
    price: Optional[Decimal] = None

    lead_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class AppointmentResponse(AppointmentBase):
    """Reponse rendez-vous complete."""
    id: UUID
    tenant_id: str
    code: str
    status: AppointmentStatus

    confirmation_code: Optional[str] = None
    confirmed_at: Optional[datetime] = None

    checked_in_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None

    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    rescheduled_from: Optional[UUID] = None
    reschedule_count: int = 0

    parent_appointment_id: Optional[UUID] = None
    occurrence_index: Optional[int] = None

    external_event_id: Optional[str] = None
    sync_provider: Optional[SyncProvider] = None
    last_synced_at: Optional[datetime] = None

    deposit_paid: bool = False
    payment_status: str = "pending"

    is_deleted: bool = False
    version: int
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime

    # Relations
    attendees: List[AttendeeResponse] = Field(default_factory=list)
    reminders: List[ReminderResponse] = Field(default_factory=list)
    appointment_type: Optional[AppointmentTypeSummary] = None
    resource: Optional[ResourceSummary] = None


class AppointmentSummary(BaseModel):
    """Resume rendez-vous pour les listes."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    status: AppointmentStatus
    mode: AppointmentMode
    priority: AppointmentPriority
    start_datetime: datetime
    end_datetime: datetime
    duration_minutes: int
    all_day: bool
    location: Optional[str] = None
    contact_name: Optional[str] = None
    organizer_name: Optional[str] = None
    type_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    is_recurring: bool = False
    attendee_count: int = 0


class AppointmentList(BaseModel):
    """Liste paginee de rendez-vous."""
    items: List[AppointmentSummary]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ============================================================================
# SCHEMAS DISPONIBILITE
# ============================================================================

class AvailabilityBase(BaseModel):
    """Base pour les disponibilites."""
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    availability_type: AvailabilityType = AvailabilityType.AVAILABLE

    date_start: date
    date_end: Optional[date] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None

    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_days: List[int] = Field(default_factory=list)
    recurrence_end_date: Optional[date] = None

    title: Optional[str] = None
    reason: Optional[str] = None


class AvailabilityCreate(AvailabilityBase):
    """Creation d'une disponibilite."""
    pass


class AvailabilityUpdate(BaseModel):
    """Mise a jour d'une disponibilite."""
    model_config = ConfigDict(from_attributes=True)

    availability_type: Optional[AvailabilityType] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_days: Optional[List[int]] = None
    title: Optional[str] = None
    reason: Optional[str] = None


class AvailabilityResponse(AvailabilityBase):
    """Reponse disponibilite."""
    id: UUID
    tenant_id: str
    is_deleted: bool
    created_at: datetime


# ============================================================================
# SCHEMAS HORAIRES DE TRAVAIL
# ============================================================================

class WorkingHoursBase(BaseModel):
    """Base pour les horaires de travail."""
    model_config = ConfigDict(from_attributes=True)

    day_of_week: int = Field(..., ge=0, le=6)
    is_working: bool = True
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    breaks: List[Dict[str, str]] = Field(default_factory=list)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None


class WorkingHoursCreate(WorkingHoursBase):
    """Creation d'horaires de travail."""
    user_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None


class WorkingHoursUpdate(BaseModel):
    """Mise a jour d'horaires de travail."""
    model_config = ConfigDict(from_attributes=True)

    is_working: Optional[bool] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    breaks: Optional[List[Dict[str, str]]] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None


class WorkingHoursResponse(WorkingHoursBase):
    """Reponse horaires de travail."""
    id: UUID
    tenant_id: str
    user_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    created_at: datetime


# ============================================================================
# SCHEMAS LISTE D'ATTENTE
# ============================================================================

class WaitlistEntryCreate(BaseModel):
    """Creation d'une entree en liste d'attente."""
    model_config = ConfigDict(from_attributes=True)

    type_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    staff_user_id: Optional[UUID] = None

    contact_id: Optional[UUID] = None
    contact_name: str = Field(..., min_length=1, max_length=255)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    preferred_dates: List[date] = Field(default_factory=list)
    preferred_times: List[str] = Field(default_factory=list)
    preferred_modes: List[AppointmentMode] = Field(default_factory=list)
    notes: Optional[str] = None


class WaitlistEntryResponse(WaitlistEntryCreate):
    """Reponse liste d'attente."""
    id: UUID
    tenant_id: str
    status: str
    priority: int
    notified_at: Optional[datetime] = None
    notification_count: int
    converted_appointment_id: Optional[UUID] = None
    converted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# SCHEMAS SYNCHRONISATION
# ============================================================================

class CalendarSyncCreate(BaseModel):
    """Creation d'une synchronisation calendrier."""
    model_config = ConfigDict(from_attributes=True)

    provider: SyncProvider
    calendar_id: str
    calendar_name: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    sync_direction: str = "both"
    sync_interval_minutes: int = 15


class CalendarSyncResponse(BaseModel):
    """Reponse synchronisation calendrier."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: str
    user_id: UUID
    provider: SyncProvider
    calendar_id: str
    calendar_name: Optional[str] = None
    sync_direction: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    events_imported: int
    events_exported: int
    created_at: datetime


# ============================================================================
# SCHEMAS PARAMETRES
# ============================================================================

class BookingSettingsUpdate(BaseModel):
    """Mise a jour des parametres de reservation."""
    model_config = ConfigDict(from_attributes=True)

    allow_online_booking: Optional[bool] = None
    require_account: Optional[bool] = None
    booking_page_url: Optional[str] = None
    booking_page_logo_url: Optional[str] = None

    slot_interval_minutes: Optional[int] = None
    booking_window_days: Optional[int] = None
    min_notice_hours: Optional[int] = None
    max_bookings_per_day: Optional[int] = None
    max_bookings_per_customer_day: Optional[int] = None

    show_staff_selection: Optional[bool] = None
    allow_any_staff: Optional[bool] = None

    conflict_resolution: Optional[ConflictResolution] = None
    allow_overbooking: Optional[bool] = None

    confirmation_message: Optional[str] = None
    cancellation_policy: Optional[str] = None
    default_reminders: Optional[List[Dict[str, Any]]] = None

    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None

    require_payment: Optional[bool] = None
    payment_provider: Optional[str] = None
    deposit_percentage: Optional[Decimal] = None

    notify_on_booking: Optional[bool] = None
    notify_on_cancellation: Optional[bool] = None
    notify_on_reschedule: Optional[bool] = None
    notification_emails: Optional[List[str]] = None


class BookingSettingsResponse(BookingSettingsUpdate):
    """Reponse parametres de reservation."""
    id: UUID
    tenant_id: str
    version: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# SCHEMAS CRENEAUX
# ============================================================================

class TimeSlot(BaseModel):
    """Creneau horaire disponible."""
    model_config = ConfigDict(from_attributes=True)

    start_time: datetime
    end_time: datetime
    is_available: bool = True
    staff_id: Optional[UUID] = None
    staff_name: Optional[str] = None
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None


class AvailableSlotsRequest(BaseModel):
    """Requete pour obtenir les creneaux disponibles."""
    type_id: Optional[UUID] = None
    date_start: date
    date_end: Optional[date] = None
    staff_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    duration_minutes: Optional[int] = None


class AvailableSlotsResponse(BaseModel):
    """Reponse creneaux disponibles."""
    date: date
    slots: List[TimeSlot]
    type_id: Optional[UUID] = None
    duration_minutes: int


# ============================================================================
# SCHEMAS STATISTIQUES
# ============================================================================

class AppointmentStats(BaseModel):
    """Statistiques des rendez-vous."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    period_start: date
    period_end: date

    total_appointments: int = 0
    total_confirmed: int = 0
    total_completed: int = 0
    total_cancelled: int = 0
    total_no_shows: int = 0
    total_rescheduled: int = 0

    completion_rate: Decimal = Decimal("0")
    no_show_rate: Decimal = Decimal("0")
    cancellation_rate: Decimal = Decimal("0")

    avg_duration_minutes: int = 0
    total_duration_hours: Decimal = Decimal("0")

    total_revenue: Decimal = Decimal("0")
    avg_revenue_per_appointment: Decimal = Decimal("0")

    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_mode: Dict[str, int] = Field(default_factory=dict)
    by_day_of_week: Dict[str, int] = Field(default_factory=dict)
    by_hour: Dict[str, int] = Field(default_factory=dict)
    by_staff: Dict[str, int] = Field(default_factory=dict)
    by_resource: Dict[str, int] = Field(default_factory=dict)

    busiest_day: Optional[str] = None
    busiest_hour: Optional[str] = None
    most_popular_type: Optional[str] = None


class StaffStats(BaseModel):
    """Statistiques par staff."""
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    user_name: str
    total_appointments: int = 0
    total_completed: int = 0
    total_cancelled: int = 0
    total_no_shows: int = 0
    completion_rate: Decimal = Decimal("0")
    total_hours: Decimal = Decimal("0")
    total_revenue: Decimal = Decimal("0")
    avg_rating: Optional[Decimal] = None


# ============================================================================
# SCHEMAS ACTIONS
# ============================================================================

class ConfirmAppointmentRequest(BaseModel):
    """Requete de confirmation."""
    send_notification: bool = True


class CancelAppointmentRequest(BaseModel):
    """Requete d'annulation."""
    reason: Optional[str] = None
    cancel_series: bool = False
    send_notification: bool = True
    charge_fee: bool = False


class RescheduleAppointmentRequest(BaseModel):
    """Requete de replanification."""
    new_start_datetime: datetime
    new_end_datetime: Optional[datetime] = None
    reason: Optional[str] = None
    send_notification: bool = True


class CheckInRequest(BaseModel):
    """Requete de check-in."""
    attendee_id: Optional[UUID] = None
    notes: Optional[str] = None


class CompleteAppointmentRequest(BaseModel):
    """Requete de completion."""
    outcome: Optional[str] = None
    notes: Optional[str] = None


class RateAppointmentRequest(BaseModel):
    """Requete d'evaluation."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


# ============================================================================
# SCHEMAS AUTOCOMPLETE
# ============================================================================

class AutocompleteItem(BaseModel):
    """Item pour autocomplete."""
    id: str
    code: str
    label: str
    secondary: Optional[str] = None
    type: Optional[str] = None


class AutocompleteResponse(BaseModel):
    """Reponse autocomplete."""
    items: List[AutocompleteItem]


# ============================================================================
# SCHEMAS FILTRES
# ============================================================================

class AppointmentFilters(BaseModel):
    """Filtres pour la recherche de rendez-vous."""
    search: Optional[str] = None
    status: Optional[List[AppointmentStatus]] = None
    mode: Optional[List[AppointmentMode]] = None
    type_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    organizer_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_recurring: Optional[bool] = None
    is_billable: Optional[bool] = None
    tags: Optional[List[str]] = None
