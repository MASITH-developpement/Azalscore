"""
Module Events / Evenements - GAP-066
====================================

Gestion complete des evenements:
- Creation et planification d'evenements
- Lieux et salles
- Sessions et programme
- Inscriptions et billetterie
- Intervenants et sponsors
- Check-in et presences
- Certificats de participation
- Evaluations post-evenement
- Analytics evenementiels

Ce module utilise une implementation SQLAlchemy complete
avec isolation multi-tenant et soft delete.
"""

# ============================================================================
# IMPORTS MODELS
# ============================================================================
from .models import (
    # Enumerations
    EventType,
    EventStatus,
    EventFormat,
    TicketType,
    RegistrationStatus,
    PaymentStatus,
    SessionType,
    SpeakerRole,
    SponsorLevel,
    CertificateType,
    EvaluationStatus,

    # Models
    EventSequence,
    Venue,
    VenueRoom,
    Event,
    Speaker,
    EventSpeakerAssignment,
    EventSession,
    SessionSpeaker,
    EventTicketType,
    EventRegistration,
    EventCheckIn,
    SessionAttendance,
    EventSponsor,
    EventDiscountCode,
    EventCertificateTemplate,
    EventCertificate,
    EventEvaluationForm,
    EventEvaluation,
    EventInvitation,
    EventWaitlist,
    EventEmailLog,
)

# ============================================================================
# IMPORTS SCHEMAS
# ============================================================================
from .schemas import (
    # Venues
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenueListResponse,
    VenueRoomCreate,
    VenueRoomUpdate,
    VenueRoomResponse,

    # Events
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventDetailResponse,

    # Speakers
    SpeakerCreate,
    SpeakerUpdate,
    SpeakerResponse,
    SpeakerListResponse,
    SpeakerAssignmentCreate,
    SpeakerAssignmentResponse,

    # Sessions
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,

    # Tickets
    TicketTypeCreate,
    TicketTypeUpdate,
    TicketTypeResponse,
    TicketTypeListResponse,

    # Registrations
    RegistrationCreate,
    RegistrationUpdate,
    RegistrationResponse,
    RegistrationListResponse,

    # Sponsors
    SponsorCreate,
    SponsorUpdate,
    SponsorResponse,
    SponsorListResponse,

    # Discount Codes
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
    DiscountCodeValidation,

    # Certificates
    CertificateTemplateCreate,
    CertificateTemplateUpdate,
    CertificateTemplateResponse,
    CertificateResponse,
    CertificateListResponse,

    # Evaluations
    EvaluationFormCreate,
    EvaluationFormUpdate,
    EvaluationFormResponse,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationListResponse,

    # Invitations
    InvitationCreate,
    InvitationResponse,
    InvitationListResponse,

    # Waitlist
    WaitlistEntryCreate,
    WaitlistEntryResponse,
    WaitlistListResponse,

    # Check-in
    CheckInCreate,
    CheckInResponse,
    CheckInListResponse,

    # Statistics
    EventStats,
    CheckInStats,
    EvaluationStats,
    GlobalEventStats,
    EventDashboard,

    # Agenda
    EventAgenda,
    AgendaDay,
    AgendaSlot,
)

# ============================================================================
# IMPORTS EXCEPTIONS
# ============================================================================
from .exceptions import (
    EventsBaseException,
    # Evenements
    EventNotFoundException,
    EventCodeExistsException,
    EventStatusException,
    EventDatesException,
    EventCapacityException,
    # Inscriptions
    RegistrationNotFoundException,
    RegistrationClosedException,
    RegistrationDuplicateException,
    RegistrationStatusException,
    RegistrationApprovalRequired,
    # Billetterie
    TicketTypeNotFoundException,
    TicketSoldOutException,
    TicketSalesNotOpenException,
    TicketSalesClosedException,
    TicketQuantityException,
    # Codes promo
    DiscountCodeNotFoundException,
    DiscountCodeExpiredException,
    DiscountCodeExhaustedException,
    DiscountCodeInactiveException,
    DiscountCodeNotApplicableException,
    # Sessions
    SessionNotFoundException,
    SessionCapacityException,
    SessionConflictException,
    # Intervenants
    SpeakerNotFoundException,
    SpeakerAlreadyAssignedException,
    # Lieux
    VenueNotFoundException,
    RoomNotFoundException,
    VenueUnavailableException,
    # Check-in
    CheckInNotFoundException,
    CheckInAlreadyDoneException,
    CheckInNotAllowedException,
    # Certificats
    CertificateNotFoundException,
    CertificateAlreadyIssuedException,
    CertificateNotEligibleException,
    # Evaluations
    EvaluationNotFoundException,
    EvaluationAlreadySubmittedException,
    EvaluationDeadlinePassedException,
    # Invitations
    InvitationNotFoundException,
    InvitationExpiredException,
    InvitationAlreadyUsedException,
    # Paiement
    PaymentFailedException,
    RefundNotAllowedException,
)

# ============================================================================
# IMPORTS REPOSITORY
# ============================================================================
from .repository import (
    VenueRepository,
    VenueRoomRepository,
    EventRepository,
    SpeakerRepository,
    SpeakerAssignmentRepository,
    SessionRepository,
    TicketTypeRepository,
    RegistrationRepository,
    CheckInRepository,
    SponsorRepository,
    DiscountCodeRepository,
    CertificateTemplateRepository,
    CertificateRepository,
    EvaluationFormRepository,
    EvaluationRepository,
    InvitationRepository,
    WaitlistRepository,
)

# ============================================================================
# IMPORTS SERVICE
# ============================================================================
from .service_impl import (
    EventsService,
    get_events_service,
)

# ============================================================================
# IMPORTS ROUTER
# ============================================================================
from .router import router

# ============================================================================
# EXPORTS
# ============================================================================
__all__ = [
    # Router
    "router",

    # Enumerations
    "EventType",
    "EventStatus",
    "EventFormat",
    "TicketType",
    "RegistrationStatus",
    "PaymentStatus",
    "SessionType",
    "SpeakerRole",
    "SponsorLevel",
    "CertificateType",
    "EvaluationStatus",

    # Models
    "EventSequence",
    "Venue",
    "VenueRoom",
    "Event",
    "Speaker",
    "EventSpeakerAssignment",
    "EventSession",
    "SessionSpeaker",
    "EventTicketType",
    "EventRegistration",
    "EventCheckIn",
    "SessionAttendance",
    "EventSponsor",
    "EventDiscountCode",
    "EventCertificateTemplate",
    "EventCertificate",
    "EventEvaluationForm",
    "EventEvaluation",
    "EventInvitation",
    "EventWaitlist",
    "EventEmailLog",

    # Schemas - Venues
    "VenueCreate",
    "VenueUpdate",
    "VenueResponse",
    "VenueListResponse",
    "VenueRoomCreate",
    "VenueRoomUpdate",
    "VenueRoomResponse",

    # Schemas - Events
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventListResponse",
    "EventDetailResponse",

    # Schemas - Speakers
    "SpeakerCreate",
    "SpeakerUpdate",
    "SpeakerResponse",
    "SpeakerListResponse",
    "SpeakerAssignmentCreate",
    "SpeakerAssignmentResponse",

    # Schemas - Sessions
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",

    # Schemas - Tickets
    "TicketTypeCreate",
    "TicketTypeUpdate",
    "TicketTypeResponse",
    "TicketTypeListResponse",

    # Schemas - Registrations
    "RegistrationCreate",
    "RegistrationUpdate",
    "RegistrationResponse",
    "RegistrationListResponse",

    # Schemas - Sponsors
    "SponsorCreate",
    "SponsorUpdate",
    "SponsorResponse",
    "SponsorListResponse",

    # Schemas - Discount Codes
    "DiscountCodeCreate",
    "DiscountCodeUpdate",
    "DiscountCodeResponse",
    "DiscountCodeValidation",

    # Schemas - Certificates
    "CertificateTemplateCreate",
    "CertificateTemplateUpdate",
    "CertificateTemplateResponse",
    "CertificateResponse",
    "CertificateListResponse",

    # Schemas - Evaluations
    "EvaluationFormCreate",
    "EvaluationFormUpdate",
    "EvaluationFormResponse",
    "EvaluationCreate",
    "EvaluationResponse",
    "EvaluationListResponse",

    # Schemas - Invitations
    "InvitationCreate",
    "InvitationResponse",
    "InvitationListResponse",

    # Schemas - Waitlist
    "WaitlistEntryCreate",
    "WaitlistEntryResponse",
    "WaitlistListResponse",

    # Schemas - Check-in
    "CheckInCreate",
    "CheckInResponse",
    "CheckInListResponse",

    # Schemas - Statistics
    "EventStats",
    "CheckInStats",
    "EvaluationStats",
    "GlobalEventStats",
    "EventDashboard",

    # Schemas - Agenda
    "EventAgenda",
    "AgendaDay",
    "AgendaSlot",

    # Exceptions
    "EventsBaseException",
    "EventNotFoundException",
    "EventCodeExistsException",
    "EventStatusException",
    "EventDatesException",
    "EventCapacityException",
    "RegistrationNotFoundException",
    "RegistrationClosedException",
    "RegistrationDuplicateException",
    "RegistrationStatusException",
    "RegistrationApprovalRequired",
    "TicketTypeNotFoundException",
    "TicketSoldOutException",
    "TicketSalesNotOpenException",
    "TicketSalesClosedException",
    "TicketQuantityException",
    "DiscountCodeNotFoundException",
    "DiscountCodeExpiredException",
    "DiscountCodeExhaustedException",
    "DiscountCodeInactiveException",
    "DiscountCodeNotApplicableException",
    "SessionNotFoundException",
    "SessionCapacityException",
    "SessionConflictException",
    "SpeakerNotFoundException",
    "SpeakerAlreadyAssignedException",
    "VenueNotFoundException",
    "RoomNotFoundException",
    "VenueUnavailableException",
    "CheckInNotFoundException",
    "CheckInAlreadyDoneException",
    "CheckInNotAllowedException",
    "CertificateNotFoundException",
    "CertificateAlreadyIssuedException",
    "CertificateNotEligibleException",
    "EvaluationNotFoundException",
    "EvaluationAlreadySubmittedException",
    "EvaluationDeadlinePassedException",
    "InvitationNotFoundException",
    "InvitationExpiredException",
    "InvitationAlreadyUsedException",
    "PaymentFailedException",
    "RefundNotAllowedException",

    # Repositories
    "VenueRepository",
    "VenueRoomRepository",
    "EventRepository",
    "SpeakerRepository",
    "SpeakerAssignmentRepository",
    "SessionRepository",
    "TicketTypeRepository",
    "RegistrationRepository",
    "CheckInRepository",
    "SponsorRepository",
    "DiscountCodeRepository",
    "CertificateTemplateRepository",
    "CertificateRepository",
    "EvaluationFormRepository",
    "EvaluationRepository",
    "InvitationRepository",
    "WaitlistRepository",

    # Service
    "EventsService",
    "get_events_service",
]
