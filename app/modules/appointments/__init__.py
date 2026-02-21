"""
AZALS MODULE - Appointments / Rendez-vous
==========================================

Module complet de gestion des rendez-vous pour AZALSCORE ERP.

Fonctionnalites inspirees de:
- Sage CRM: rendez-vous recurrents, planification
- Axonaut: integration CRM, rappels automatiques
- Odoo: multi-participants, types configurables, ressources
- Microsoft Dynamics 365: schedule board, AI scheduling
- Pennylane: mobilite, synchronisation calendrier

Conformite AZALSCORE:
- tenant_id sur toutes les entites
- Soft delete: is_deleted, deleted_at, deleted_by
- Audit: created_at, created_by, updated_at, updated_by
- Version pour optimistic locking
- _base_query() filtre par tenant_id
"""

# Enumerations
from .models import (
    AppointmentStatus,
    AppointmentMode,
    AppointmentPriority,
    RecurrencePattern,
    RecurrenceEndType,
    ReminderType,
    ReminderStatus,
    AttendeeRole,
    AttendeeStatus,
    AvailabilityType,
    BookingMode,
    ResourceType,
    SyncProvider,
    ConflictResolution,
)

# Modeles SQLAlchemy
from .models import (
    Appointment,
    AppointmentType,
    Resource,
    Attendee,
    Reminder,
    Availability,
    WorkingHours,
    WaitlistEntry,
    CalendarSync,
    BookingSettings,
    AppointmentSequence,
)

# Schemas Pydantic
from .schemas import (
    # Types
    AppointmentTypeCreate,
    AppointmentTypeUpdate,
    AppointmentTypeResponse,
    AppointmentTypeSummary,
    # Resources
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceSummary,
    # Appointments
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentSummary,
    AppointmentList,
    AppointmentFilters,
    # Attendees
    AttendeeCreate,
    AttendeeUpdate,
    AttendeeResponse,
    # Reminders
    ReminderCreate,
    ReminderResponse,
    # Availability
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    # Working Hours
    WorkingHoursCreate,
    WorkingHoursUpdate,
    WorkingHoursResponse,
    # Waitlist
    WaitlistEntryCreate,
    WaitlistEntryResponse,
    # Slots
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    TimeSlot,
    # Settings
    BookingSettingsUpdate,
    BookingSettingsResponse,
    # Stats
    AppointmentStats,
    StaffStats,
    # Actions
    ConfirmAppointmentRequest,
    CancelAppointmentRequest,
    RescheduleAppointmentRequest,
    CheckInRequest,
    CompleteAppointmentRequest,
    RateAppointmentRequest,
    # Autocomplete
    AutocompleteItem,
    AutocompleteResponse,
)

# Repositories
from .repository import (
    AppointmentRepository,
    AppointmentTypeRepository,
    ResourceRepository,
    AttendeeRepository,
    ReminderRepository,
    AvailabilityRepository,
    WorkingHoursRepository,
    WaitlistRepository,
    BookingSettingsRepository,
)

# Service
from .service import AppointmentService, create_appointment_service

# Exceptions
from .exceptions import (
    AppointmentError,
    AppointmentNotFoundError,
    AppointmentConflictError,
    AppointmentStateError,
    AppointmentValidationError,
    AppointmentDuplicateError,
    TypeNotFoundError,
    TypeDuplicateError,
    ResourceNotFoundError,
    ResourceNotAvailableError,
    SlotNotAvailableError,
    NoSlotsAvailableError,
    BookingNotAllowedError,
    BookingTooEarlyError,
    BookingTooLateError,
    MaxBookingsExceededError,
    AttendeeNotFoundError,
    MaxAttendeesExceededError,
    ReminderNotFoundError,
    WaitlistEntryNotFoundError,
    CalendarSyncError,
    RecurrenceError,
    PaymentRequiredError,
    PermissionDeniedError,
)

# Router
from .router import router

__all__ = [
    # Enumerations
    "AppointmentStatus",
    "AppointmentMode",
    "AppointmentPriority",
    "RecurrencePattern",
    "RecurrenceEndType",
    "ReminderType",
    "ReminderStatus",
    "AttendeeRole",
    "AttendeeStatus",
    "AvailabilityType",
    "BookingMode",
    "ResourceType",
    "SyncProvider",
    "ConflictResolution",
    # Models
    "Appointment",
    "AppointmentType",
    "Resource",
    "Attendee",
    "Reminder",
    "Availability",
    "WorkingHours",
    "WaitlistEntry",
    "CalendarSync",
    "BookingSettings",
    "AppointmentSequence",
    # Schemas
    "AppointmentTypeCreate",
    "AppointmentTypeUpdate",
    "AppointmentTypeResponse",
    "AppointmentTypeSummary",
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceResponse",
    "ResourceSummary",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AppointmentSummary",
    "AppointmentList",
    "AppointmentFilters",
    "AttendeeCreate",
    "AttendeeUpdate",
    "AttendeeResponse",
    "ReminderCreate",
    "ReminderResponse",
    "AvailabilityCreate",
    "AvailabilityUpdate",
    "AvailabilityResponse",
    "WorkingHoursCreate",
    "WorkingHoursUpdate",
    "WorkingHoursResponse",
    "WaitlistEntryCreate",
    "WaitlistEntryResponse",
    "AvailableSlotsRequest",
    "AvailableSlotsResponse",
    "TimeSlot",
    "BookingSettingsUpdate",
    "BookingSettingsResponse",
    "AppointmentStats",
    "StaffStats",
    "ConfirmAppointmentRequest",
    "CancelAppointmentRequest",
    "RescheduleAppointmentRequest",
    "CheckInRequest",
    "CompleteAppointmentRequest",
    "RateAppointmentRequest",
    "AutocompleteItem",
    "AutocompleteResponse",
    # Repositories
    "AppointmentRepository",
    "AppointmentTypeRepository",
    "ResourceRepository",
    "AttendeeRepository",
    "ReminderRepository",
    "AvailabilityRepository",
    "WorkingHoursRepository",
    "WaitlistRepository",
    "BookingSettingsRepository",
    # Service
    "AppointmentService",
    "create_appointment_service",
    # Exceptions
    "AppointmentError",
    "AppointmentNotFoundError",
    "AppointmentConflictError",
    "AppointmentStateError",
    "AppointmentValidationError",
    "AppointmentDuplicateError",
    "TypeNotFoundError",
    "TypeDuplicateError",
    "ResourceNotFoundError",
    "ResourceNotAvailableError",
    "SlotNotAvailableError",
    "NoSlotsAvailableError",
    "BookingNotAllowedError",
    "BookingTooEarlyError",
    "BookingTooLateError",
    "MaxBookingsExceededError",
    "AttendeeNotFoundError",
    "MaxAttendeesExceededError",
    "ReminderNotFoundError",
    "WaitlistEntryNotFoundError",
    "CalendarSyncError",
    "RecurrenceError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    # Router
    "router",
]
