"""
AZALS MODULE EVENTS - Schemas Pydantic
======================================

Schemas de validation pour la gestion d'evenements.
"""
from __future__ import annotations


import json
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import (
    CertificateType,
    EvaluationStatus,
    EventFormat,
    EventStatus,
    EventType,
    PaymentStatus,
    RegistrationStatus,
    SessionType,
    SpeakerRole,
    SponsorLevel,
    TicketType,
)


# ============================================================================
# MIXINS ET BASES
# ============================================================================

class AuditMixin(BaseModel):
    """Mixin pour les champs d'audit."""
    created_at: datetime
    updated_at: datetime
    version: int = 1

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LIEUX ET SALLES
# ============================================================================

class VenueBase(BaseModel):
    """Base pour les lieux."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    venue_type: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country_code: str = "FR"
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    website: str | None = None
    total_capacity: int | None = None
    amenities: list[str] = Field(default_factory=list)
    accessibility_info: str | None = None
    daily_rate: Decimal | None = None
    half_day_rate: Decimal | None = None
    currency: str = "EUR"
    image_url: str | None = None
    gallery_urls: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator('amenities', 'gallery_urls', mode='before')
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else []
        return v or []


class VenueCreate(VenueBase):
    """Creation d'un lieu."""
    pass


class VenueUpdate(BaseModel):
    """Mise a jour d'un lieu."""
    name: str | None = None
    description: str | None = None
    venue_type: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    website: str | None = None
    total_capacity: int | None = None
    amenities: list[str] | None = None
    accessibility_info: str | None = None
    daily_rate: Decimal | None = None
    half_day_rate: Decimal | None = None
    currency: str | None = None
    image_url: str | None = None
    gallery_urls: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


class VenueResponse(VenueBase):
    """Reponse lieu."""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VenueListResponse(BaseModel):
    """Liste paginee des lieux."""
    items: list[VenueResponse]
    total: int
    page: int = 1
    page_size: int = 50


class VenueRoomBase(BaseModel):
    """Base pour les salles."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    floor: str | None = None
    room_number: str | None = None
    capacity_theater: int | None = None
    capacity_classroom: int | None = None
    capacity_banquet: int | None = None
    capacity_cocktail: int | None = None
    capacity_boardroom: int | None = None
    capacity_u_shape: int | None = None
    equipment: list[str] = Field(default_factory=list)
    has_natural_light: bool = False
    has_air_conditioning: bool = True
    has_video_conference: bool = False
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    currency: str = "EUR"


class VenueRoomCreate(VenueRoomBase):
    """Creation d'une salle."""
    venue_id: UUID


class VenueRoomUpdate(BaseModel):
    """Mise a jour d'une salle."""
    name: str | None = None
    description: str | None = None
    floor: str | None = None
    room_number: str | None = None
    capacity_theater: int | None = None
    capacity_classroom: int | None = None
    capacity_banquet: int | None = None
    capacity_cocktail: int | None = None
    capacity_boardroom: int | None = None
    capacity_u_shape: int | None = None
    equipment: list[str] | None = None
    has_natural_light: bool | None = None
    has_air_conditioning: bool | None = None
    has_video_conference: bool | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_active: bool | None = None


class VenueRoomResponse(VenueRoomBase):
    """Reponse salle."""
    id: UUID
    venue_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VenueWithRoomsResponse(VenueResponse):
    """Lieu avec ses salles."""
    rooms: list[VenueRoomResponse] = Field(default_factory=list)


# ============================================================================
# EVENEMENTS
# ============================================================================

class EventBase(BaseModel):
    """Base pour les evenements."""
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = None
    description: str | None = None
    short_description: str | None = None
    event_type: EventType = EventType.CONFERENCE
    format: EventFormat = EventFormat.IN_PERSON
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    timezone: str = "Europe/Paris"
    all_day: bool = False

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("La date de fin doit etre apres la date de debut")
        return v


class EventCreate(EventBase):
    """Creation d'un evenement."""
    code: str | None = None  # Auto-genere si non fourni
    venue_id: UUID | None = None
    room_id: UUID | None = None
    location_name: str | None = None
    location_address: str | None = None
    virtual_platform: str | None = None
    virtual_link: str | None = None
    virtual_access_code: str | None = None
    registration_required: bool = True
    max_attendees: int | None = None
    min_attendees: int | None = None
    waitlist_enabled: bool = True
    waitlist_max: int | None = None
    approval_required: bool = False
    is_free: bool = False
    default_price: Decimal = Decimal("0.00")
    currency: str = "EUR"
    tax_rate: Decimal = Decimal("20.00")
    tax_included: bool = True
    organizer_name: str | None = None
    organizer_email: EmailStr | None = None
    organizer_phone: str | None = None
    cover_image_url: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    language: str = "fr"
    is_public: bool = True
    issue_certificates: bool = False
    enable_evaluations: bool = True
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    registration_form_fields: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None


class EventUpdate(BaseModel):
    """Mise a jour d'un evenement."""
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    short_description: str | None = None
    event_type: EventType | None = None
    format: EventFormat | None = None
    status: EventStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    timezone: str | None = None
    all_day: bool | None = None
    venue_id: UUID | None = None
    room_id: UUID | None = None
    location_name: str | None = None
    location_address: str | None = None
    virtual_platform: str | None = None
    virtual_link: str | None = None
    virtual_access_code: str | None = None
    registration_required: bool | None = None
    registration_open: bool | None = None
    registration_start_date: datetime | None = None
    registration_end_date: datetime | None = None
    max_attendees: int | None = None
    min_attendees: int | None = None
    waitlist_enabled: bool | None = None
    waitlist_max: int | None = None
    approval_required: bool | None = None
    is_free: bool | None = None
    default_price: Decimal | None = None
    currency: str | None = None
    tax_rate: Decimal | None = None
    tax_included: bool | None = None
    organizer_name: str | None = None
    organizer_email: EmailStr | None = None
    organizer_phone: str | None = None
    cover_image_url: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    website_url: str | None = None
    social_links: dict[str, str] | None = None
    send_reminders: bool | None = None
    reminder_days_before: list[int] | None = None
    issue_certificates: bool | None = None
    certificate_template_id: UUID | None = None
    min_attendance_for_certificate: Decimal | None = None
    enable_evaluations: bool | None = None
    evaluation_form_id: UUID | None = None
    category: str | None = None
    tags: list[str] | None = None
    target_audience: str | None = None
    language: str | None = None
    is_public: bool | None = None
    is_featured: bool | None = None
    visibility: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    custom_fields: dict[str, Any] | None = None
    registration_form_fields: list[dict[str, Any]] | None = None
    notes: str | None = None
    internal_notes: str | None = None
    is_active: bool | None = None


class EventResponse(EventBase):
    """Reponse evenement."""
    id: UUID
    code: str
    slug: str | None = None
    status: EventStatus = EventStatus.DRAFT
    venue_id: UUID | None = None
    room_id: UUID | None = None
    location_name: str | None = None
    location_address: str | None = None
    virtual_platform: str | None = None
    virtual_link: str | None = None
    registration_required: bool = True
    registration_open: bool = False
    registration_start_date: datetime | None = None
    registration_end_date: datetime | None = None
    max_attendees: int | None = None
    waitlist_enabled: bool = True
    approval_required: bool = False
    registered_count: int = 0
    confirmed_count: int = 0
    waitlist_count: int = 0
    checkin_count: int = 0
    is_free: bool = False
    default_price: Decimal = Decimal("0.00")
    currency: str = "EUR"
    total_revenue: Decimal = Decimal("0.00")
    organizer_name: str | None = None
    organizer_email: str | None = None
    cover_image_url: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = True
    is_featured: bool = False
    issue_certificates: bool = False
    enable_evaluations: bool = True
    published_at: datetime | None = None
    is_active: bool = True
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListItem(BaseModel):
    """Element de liste evenement."""
    id: UUID
    code: str
    title: str
    event_type: EventType
    format: EventFormat
    status: EventStatus
    start_date: date
    end_date: date
    location_name: str | None = None
    registered_count: int = 0
    max_attendees: int | None = None
    is_public: bool = True
    cover_image_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventList(BaseModel):
    """Liste d'evenements."""
    items: list[EventListItem]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# INTERVENANTS
# ============================================================================

class SpeakerBase(BaseModel):
    """Base pour les intervenants."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    title: str | None = None
    job_title: str | None = None
    company: str | None = None
    department: str | None = None
    bio_short: str | None = None
    bio_full: str | None = None
    photo_url: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    website_url: str | None = None
    topics: list[str] = Field(default_factory=list)
    expertise_areas: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class SpeakerCreate(SpeakerBase):
    """Creation d'un intervenant."""
    code: str | None = None
    fee_keynote: Decimal | None = None
    fee_workshop: Decimal | None = None
    fee_panel: Decimal | None = None
    currency: str = "EUR"
    travel_requirements: str | None = None
    contact_id: UUID | None = None
    employee_id: UUID | None = None
    is_internal: bool = False
    notes: str | None = None


class SpeakerUpdate(BaseModel):
    """Mise a jour d'un intervenant."""
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    title: str | None = None
    job_title: str | None = None
    company: str | None = None
    department: str | None = None
    bio_short: str | None = None
    bio_full: str | None = None
    photo_url: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    website_url: str | None = None
    topics: list[str] | None = None
    expertise_areas: list[str] | None = None
    languages: list[str] | None = None
    fee_keynote: Decimal | None = None
    fee_workshop: Decimal | None = None
    fee_panel: Decimal | None = None
    currency: str | None = None
    travel_requirements: str | None = None
    is_internal: bool | None = None
    is_active: bool | None = None
    notes: str | None = None


class SpeakerResponse(SpeakerBase):
    """Reponse intervenant."""
    id: UUID
    code: str | None = None
    fee_keynote: Decimal | None = None
    fee_workshop: Decimal | None = None
    fee_panel: Decimal | None = None
    currency: str = "EUR"
    contact_id: UUID | None = None
    employee_id: UUID | None = None
    total_events: int = 0
    total_sessions: int = 0
    average_rating: Decimal | None = None
    is_internal: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpeakerAssignmentCreate(BaseModel):
    """Affectation intervenant a evenement."""
    speaker_id: UUID
    role: SpeakerRole = SpeakerRole.SPEAKER
    bio_override: str | None = None
    photo_override_url: str | None = None
    agreed_fee: Decimal | None = None
    expenses_covered: bool = False
    display_order: int = 0
    is_featured: bool = False
    notes: str | None = None


class SpeakerAssignmentUpdate(BaseModel):
    """Mise a jour affectation."""
    role: SpeakerRole | None = None
    is_confirmed: bool | None = None
    bio_override: str | None = None
    photo_override_url: str | None = None
    agreed_fee: Decimal | None = None
    fee_paid: bool | None = None
    expenses_covered: bool | None = None
    travel_arranged: bool | None = None
    display_order: int | None = None
    is_featured: bool | None = None
    notes: str | None = None


class SpeakerAssignmentResponse(BaseModel):
    """Reponse affectation."""
    id: UUID
    event_id: UUID
    speaker_id: UUID
    role: SpeakerRole
    is_confirmed: bool
    confirmed_at: datetime | None = None
    agreed_fee: Decimal | None = None
    fee_paid: bool = False
    display_order: int = 0
    is_featured: bool = False
    speaker: SpeakerResponse | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SESSIONS
# ============================================================================

class SessionBase(BaseModel):
    """Base pour les sessions."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    session_type: SessionType = SessionType.PRESENTATION
    track: str | None = None
    level: str | None = None
    session_date: date
    start_time: time
    end_time: time
    duration_minutes: int | None = None
    room_name: str | None = None
    virtual_link: str | None = None
    capacity: int | None = None
    requires_registration: bool = False
    extra_fee: Decimal = Decimal("0.00")
    objectives: list[str] = Field(default_factory=list)
    prerequisites: str | None = None
    tags: list[str] = Field(default_factory=list)
    language: str = "fr"


class SessionCreate(SessionBase):
    """Creation d'une session."""
    code: str | None = None
    room_id: UUID | None = None
    materials_url: str | None = None
    display_order: int = 0
    is_featured: bool = False
    is_visible: bool = True
    color: str | None = None
    notes: str | None = None
    speaker_ids: list[UUID] = Field(default_factory=list)


class SessionUpdate(BaseModel):
    """Mise a jour d'une session."""
    title: str | None = None
    description: str | None = None
    session_type: SessionType | None = None
    track: str | None = None
    level: str | None = None
    session_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    room_id: UUID | None = None
    room_name: str | None = None
    virtual_link: str | None = None
    capacity: int | None = None
    requires_registration: bool | None = None
    registration_open: bool | None = None
    extra_fee: Decimal | None = None
    objectives: list[str] | None = None
    prerequisites: str | None = None
    materials_url: str | None = None
    slides_url: str | None = None
    recording_url: str | None = None
    handout_url: str | None = None
    live_stream_url: str | None = None
    tags: list[str] | None = None
    language: str | None = None
    display_order: int | None = None
    is_featured: bool | None = None
    is_visible: bool | None = None
    color: str | None = None
    is_cancelled: bool | None = None
    cancelled_reason: str | None = None
    notes: str | None = None


class SessionResponse(SessionBase):
    """Reponse session."""
    id: UUID
    event_id: UUID
    code: str | None = None
    room_id: UUID | None = None
    registered_count: int = 0
    attendee_count: int = 0
    registration_open: bool = True
    materials_url: str | None = None
    slides_url: str | None = None
    recording_url: str | None = None
    handout_url: str | None = None
    display_order: int = 0
    is_featured: bool = False
    is_visible: bool = True
    is_cancelled: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionWithSpeakersResponse(SessionResponse):
    """Session avec intervenants."""
    speakers: list[SpeakerAssignmentResponse] = Field(default_factory=list)


# ============================================================================
# BILLETTERIE
# ============================================================================

class TicketTypeBase(BaseModel):
    """Base pour les types de billets."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    ticket_type: TicketType = TicketType.PAID
    price: Decimal = Decimal("0.00")
    original_price: Decimal | None = None
    currency: str = "EUR"
    tax_rate: Decimal = Decimal("20.00")
    tax_included: bool = True
    quantity_available: int | None = None
    max_per_order: int = 10
    min_per_order: int = 1


class TicketTypeCreate(TicketTypeBase):
    """Creation d'un type de billet."""
    sales_start_date: datetime | None = None
    sales_end_date: datetime | None = None
    is_visible: bool = True
    requires_approval: bool = False
    eligibility_criteria: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    includes_all_sessions: bool = True
    included_session_ids: list[UUID] = Field(default_factory=list)
    perks: list[str] = Field(default_factory=list)
    display_order: int = 0
    badge_text: str | None = None
    color: str | None = None
    notes: str | None = None


class TicketTypeUpdate(BaseModel):
    """Mise a jour d'un type de billet."""
    name: str | None = None
    description: str | None = None
    ticket_type: TicketType | None = None
    price: Decimal | None = None
    original_price: Decimal | None = None
    tax_rate: Decimal | None = None
    tax_included: bool | None = None
    quantity_available: int | None = None
    max_per_order: int | None = None
    min_per_order: int | None = None
    sales_start_date: datetime | None = None
    sales_end_date: datetime | None = None
    is_visible: bool | None = None
    is_available: bool | None = None
    requires_approval: bool | None = None
    eligibility_criteria: str | None = None
    allowed_domains: list[str] | None = None
    includes_all_sessions: bool | None = None
    included_session_ids: list[UUID] | None = None
    perks: list[str] | None = None
    display_order: int | None = None
    badge_text: str | None = None
    color: str | None = None
    notes: str | None = None


class TicketTypeResponse(TicketTypeBase):
    """Reponse type de billet."""
    id: UUID
    event_id: UUID
    quantity_sold: int = 0
    quantity_reserved: int = 0
    sales_start_date: datetime | None = None
    sales_end_date: datetime | None = None
    is_visible: bool = True
    is_available: bool = True
    requires_approval: bool = False
    perks: list[str] = Field(default_factory=list)
    display_order: int = 0
    badge_text: str | None = None
    quantity_remaining: int | None = None
    is_sold_out: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INSCRIPTIONS
# ============================================================================

class RegistrationBase(BaseModel):
    """Base pour les inscriptions."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None


class RegistrationCreate(RegistrationBase):
    """Creation d'une inscription."""
    ticket_type_id: UUID
    attendee_id: UUID | None = None
    contact_id: UUID | None = None
    selected_sessions: list[UUID] = Field(default_factory=list)
    dietary_requirements: str | None = None
    accessibility_needs: str | None = None
    special_requests: str | None = None
    custom_answers: dict[str, Any] = Field(default_factory=dict)
    marketing_consent: bool = False
    discount_code: str | None = None
    payment_method: str | None = None
    badge_name: str | None = None
    source: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    notes: str | None = None
    is_vip: bool = False
    is_speaker: bool = False
    is_sponsor: bool = False
    is_staff: bool = False


class RegistrationUpdate(BaseModel):
    """Mise a jour d'une inscription."""
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    status: RegistrationStatus | None = None
    payment_status: PaymentStatus | None = None
    selected_sessions: list[UUID] | None = None
    dietary_requirements: str | None = None
    accessibility_needs: str | None = None
    special_requests: str | None = None
    custom_answers: dict[str, Any] | None = None
    marketing_consent: bool | None = None
    badge_name: str | None = None
    notes: str | None = None
    internal_notes: str | None = None
    tags: list[str] | None = None
    is_vip: bool | None = None
    is_speaker: bool | None = None
    is_sponsor: bool | None = None
    is_staff: bool | None = None


class RegistrationResponse(RegistrationBase):
    """Reponse inscription."""
    id: UUID
    event_id: UUID
    ticket_type_id: UUID | None = None
    registration_number: str
    qr_code: str | None = None
    attendee_id: UUID | None = None
    contact_id: UUID | None = None
    status: RegistrationStatus
    payment_status: PaymentStatus
    ticket_price: Decimal = Decimal("0.00")
    discount_code: str | None = None
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    currency: str = "EUR"
    selected_sessions: list[UUID] = Field(default_factory=list)
    dietary_requirements: str | None = None
    accessibility_needs: str | None = None
    special_requests: str | None = None
    custom_answers: dict[str, Any] = Field(default_factory=dict)
    checked_in: bool = False
    checked_in_at: datetime | None = None
    badge_printed: bool = False
    badge_name: str | None = None
    certificate_issued: bool = False
    certificate_url: str | None = None
    evaluation_completed: bool = False
    attendance_percentage: Decimal | None = None
    tags: list[str] = Field(default_factory=list)
    is_vip: bool = False
    is_speaker: bool = False
    is_sponsor: bool = False
    is_staff: bool = False
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationList(BaseModel):
    """Liste d'inscriptions."""
    items: list[RegistrationResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# CHECK-IN
# ============================================================================

class CheckInCreate(BaseModel):
    """Creation d'un check-in."""
    registration_id: UUID | None = None
    qr_code: str | None = None
    registration_number: str | None = None
    session_id: UUID | None = None
    method: str = "QR"
    location: str | None = None
    device_id: str | None = None
    notes: str | None = None


class CheckInResponse(BaseModel):
    """Reponse check-in."""
    id: UUID
    event_id: UUID
    registration_id: UUID
    session_id: UUID | None = None
    check_in_type: str
    method: str | None = None
    location: str | None = None
    checked_at: datetime
    checked_by: UUID | None = None
    registration: RegistrationResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CheckInStats(BaseModel):
    """Statistiques check-in."""
    total_expected: int = 0
    checked_in: int = 0
    remaining: int = 0
    check_in_rate: float = 0.0
    by_hour: dict[str, int] = Field(default_factory=dict)
    by_method: dict[str, int] = Field(default_factory=dict)


# ============================================================================
# SPONSORS
# ============================================================================

class SponsorBase(BaseModel):
    """Base pour les sponsors."""
    name: str = Field(..., min_length=1, max_length=255)
    level: SponsorLevel
    description: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    website_url: str | None = None


class SponsorCreate(SponsorBase):
    """Creation d'un sponsor."""
    contact_id: UUID | None = None
    amount_pledged: Decimal = Decimal("0.00")
    currency: str = "EUR"
    benefits: list[str] = Field(default_factory=list)
    booth_location: str | None = None
    booth_size: str | None = None
    speaking_slot: bool = False
    logo_on_materials: bool = True
    attendee_list_access: bool = False
    display_order: int = 0
    is_visible: bool = True
    is_featured: bool = False
    notes: str | None = None


class SponsorUpdate(BaseModel):
    """Mise a jour d'un sponsor."""
    name: str | None = None
    level: SponsorLevel | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    website_url: str | None = None
    amount_pledged: Decimal | None = None
    amount_paid: Decimal | None = None
    payment_status: PaymentStatus | None = None
    benefits: list[str] | None = None
    booth_location: str | None = None
    booth_size: str | None = None
    speaking_slot: bool | None = None
    logo_on_materials: bool | None = None
    attendee_list_access: bool | None = None
    display_order: int | None = None
    is_visible: bool | None = None
    is_featured: bool | None = None
    notes: str | None = None


class SponsorResponse(SponsorBase):
    """Reponse sponsor."""
    id: UUID
    event_id: UUID
    contact_id: UUID | None = None
    amount_pledged: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    currency: str = "EUR"
    payment_status: PaymentStatus
    benefits: list[str] = Field(default_factory=list)
    booth_location: str | None = None
    speaking_slot: bool = False
    display_order: int = 0
    is_visible: bool = True
    is_featured: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CODES PROMO
# ============================================================================

class DiscountCodeCreate(BaseModel):
    """Creation d'un code promo."""
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    discount_type: str  # PERCENTAGE, FIXED, FREE
    discount_value: Decimal = Decimal("0.00")
    max_discount_amount: Decimal | None = None
    max_uses: int | None = None
    max_uses_per_user: int = 1
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicable_ticket_types: list[UUID] = Field(default_factory=list)
    min_tickets: int = 1
    min_amount: Decimal | None = None
    notes: str | None = None


class DiscountCodeUpdate(BaseModel):
    """Mise a jour d'un code promo."""
    description: str | None = None
    discount_type: str | None = None
    discount_value: Decimal | None = None
    max_discount_amount: Decimal | None = None
    max_uses: int | None = None
    max_uses_per_user: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicable_ticket_types: list[UUID] | None = None
    min_tickets: int | None = None
    min_amount: Decimal | None = None
    is_active: bool | None = None
    notes: str | None = None


class DiscountCodeResponse(BaseModel):
    """Reponse code promo."""
    id: UUID
    event_id: UUID
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    max_discount_amount: Decimal | None = None
    max_uses: int | None = None
    max_uses_per_user: int = 1
    uses_count: int = 0
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscountCodeApply(BaseModel):
    """Application d'un code promo."""
    code: str
    ticket_type_id: UUID
    quantity: int = 1


class DiscountCodeResult(BaseModel):
    """Resultat application code promo."""
    valid: bool
    discount_amount: Decimal = Decimal("0.00")
    message: str | None = None
    code_id: UUID | None = None


# ============================================================================
# CERTIFICATS
# ============================================================================

class CertificateTemplateCreate(BaseModel):
    """Creation d'un template de certificat."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    certificate_type: CertificateType = CertificateType.ATTENDANCE
    template_html: str | None = None
    template_url: str | None = None
    background_url: str | None = None
    signature_url: str | None = None
    logo_url: str | None = None
    title_text: str | None = None
    body_text: str | None = None
    footer_text: str | None = None
    signatory_name: str | None = None
    signatory_title: str | None = None
    page_size: str = "A4"
    orientation: str = "LANDSCAPE"
    is_default: bool = False


class CertificateTemplateResponse(BaseModel):
    """Reponse template certificat."""
    id: UUID
    name: str
    description: str | None = None
    certificate_type: CertificateType
    page_size: str
    orientation: str
    is_default: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateIssue(BaseModel):
    """Emission d'un certificat."""
    registration_id: UUID
    template_id: UUID | None = None
    hours_attended: Decimal | None = None
    grade: str | None = None
    additional_info: dict[str, Any] = Field(default_factory=dict)


class CertificateResponse(BaseModel):
    """Reponse certificat."""
    id: UUID
    event_id: UUID
    registration_id: UUID
    certificate_number: str
    certificate_type: CertificateType
    recipient_name: str
    recipient_email: str | None = None
    event_title: str
    event_date: date
    hours_attended: Decimal | None = None
    grade: str | None = None
    file_url: str | None = None
    verification_code: str | None = None
    verification_url: str | None = None
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EVALUATIONS
# ============================================================================

class EvaluationFormCreate(BaseModel):
    """Creation d'un formulaire d'evaluation."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    form_type: str = "EVENT"
    questions: list[dict[str, Any]] = Field(default_factory=list)
    allow_anonymous: bool = False
    require_all_questions: bool = False
    is_default: bool = False


class EvaluationFormResponse(BaseModel):
    """Reponse formulaire evaluation."""
    id: UUID
    name: str
    description: str | None = None
    form_type: str
    questions: list[dict[str, Any]] = Field(default_factory=list)
    allow_anonymous: bool = False
    is_default: bool = False
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationSubmit(BaseModel):
    """Soumission d'une evaluation."""
    registration_id: UUID | None = None
    session_id: UUID | None = None
    speaker_id: UUID | None = None
    form_id: UUID | None = None
    evaluation_type: str = "EVENT"
    responses: dict[str, Any] = Field(default_factory=dict)
    overall_rating: Decimal | None = None
    nps_score: int | None = None
    recommendation_likelihood: int | None = None
    positive_feedback: str | None = None
    improvement_suggestions: str | None = None
    additional_comments: str | None = None
    is_anonymous: bool = False


class EvaluationResponse(BaseModel):
    """Reponse evaluation."""
    id: UUID
    event_id: UUID
    registration_id: UUID | None = None
    session_id: UUID | None = None
    speaker_id: UUID | None = None
    evaluation_type: str
    status: EvaluationStatus
    overall_rating: Decimal | None = None
    nps_score: int | None = None
    is_anonymous: bool = False
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationStats(BaseModel):
    """Statistiques evaluations."""
    total_evaluations: int = 0
    response_rate: float = 0.0
    average_rating: float = 0.0
    nps_score: float = 0.0
    rating_distribution: dict[int, int] = Field(default_factory=dict)
    top_positive_themes: list[str] = Field(default_factory=list)
    top_improvement_areas: list[str] = Field(default_factory=list)


# ============================================================================
# INVITATIONS
# ============================================================================

class InvitationCreate(BaseModel):
    """Creation d'une invitation."""
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    contact_id: UUID | None = None
    ticket_type_id: UUID | None = None
    invitation_type: str = "STANDARD"
    complimentary: bool = False
    discount_code: str | None = None
    personal_message: str | None = None
    expires_at: datetime | None = None


class InvitationBulkCreate(BaseModel):
    """Creation d'invitations en masse."""
    emails: list[EmailStr]
    ticket_type_id: UUID | None = None
    invitation_type: str = "STANDARD"
    complimentary: bool = False
    discount_code: str | None = None
    personal_message: str | None = None
    expires_at: datetime | None = None


class InvitationResponse(BaseModel):
    """Reponse invitation."""
    id: UUID
    event_id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    invitation_code: str
    invitation_type: str
    status: str
    complimentary: bool = False
    sent_at: datetime | None = None
    viewed_at: datetime | None = None
    responded_at: datetime | None = None
    response: str | None = None
    registration_id: UUID | None = None
    expires_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WAITLIST
# ============================================================================

class WaitlistEntry(BaseModel):
    """Entree liste d'attente."""
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    ticket_type_id: UUID | None = None
    session_id: UUID | None = None
    contact_id: UUID | None = None
    notes: str | None = None


class WaitlistResponse(BaseModel):
    """Reponse liste d'attente."""
    id: UUID
    event_id: UUID
    ticket_type_id: UUID | None = None
    session_id: UUID | None = None
    email: str
    first_name: str | None = None
    last_name: str | None = None
    position: int
    status: str
    notified_at: datetime | None = None
    converted_at: datetime | None = None
    registration_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STATISTIQUES ET DASHBOARD
# ============================================================================

class EventStats(BaseModel):
    """Statistiques d'un evenement."""
    event_id: UUID
    total_registrations: int = 0
    confirmed_registrations: int = 0
    pending_registrations: int = 0
    waitlisted: int = 0
    checked_in: int = 0
    no_shows: int = 0
    cancelled: int = 0
    total_revenue: Decimal = Decimal("0.00")
    total_refunds: Decimal = Decimal("0.00")
    net_revenue: Decimal = Decimal("0.00")
    average_ticket_price: Decimal = Decimal("0.00")
    capacity_utilization: float = 0.0
    check_in_rate: float = 0.0
    cancellation_rate: float = 0.0
    tickets_by_type: dict[str, int] = Field(default_factory=dict)
    registrations_by_day: dict[str, int] = Field(default_factory=dict)
    registrations_by_source: dict[str, int] = Field(default_factory=dict)
    checkins_by_hour: dict[str, int] = Field(default_factory=dict)


class EventDashboard(BaseModel):
    """Dashboard complet d'un evenement."""
    event: EventResponse
    stats: EventStats
    check_in_stats: CheckInStats
    evaluation_stats: EvaluationStats | None = None
    recent_registrations: list[RegistrationResponse] = Field(default_factory=list)
    top_sessions: list[SessionResponse] = Field(default_factory=list)
    sponsors: list[SponsorResponse] = Field(default_factory=list)


class GlobalEventStats(BaseModel):
    """Statistiques globales des evenements."""
    total_events: int = 0
    upcoming_events: int = 0
    ongoing_events: int = 0
    completed_events: int = 0
    total_registrations: int = 0
    total_revenue: Decimal = Decimal("0.00")
    events_by_type: dict[str, int] = Field(default_factory=dict)
    events_by_status: dict[str, int] = Field(default_factory=dict)
    events_by_month: dict[str, int] = Field(default_factory=dict)
    revenue_by_month: dict[str, Decimal] = Field(default_factory=dict)


# ============================================================================
# AGENDA
# ============================================================================

class AgendaSlot(BaseModel):
    """Creneau d'agenda."""
    start_time: time
    end_time: time
    session: SessionWithSpeakersResponse | None = None
    is_break: bool = False
    break_title: str | None = None


class AgendaDay(BaseModel):
    """Jour d'agenda."""
    date: date
    sessions: list[SessionWithSpeakersResponse] = Field(default_factory=list)
    slots: list[AgendaSlot] = Field(default_factory=list)


class EventAgenda(BaseModel):
    """Agenda complet de l'evenement."""
    event_id: UUID
    event_title: str
    days: list[AgendaDay] = Field(default_factory=list)
    tracks: list[str] = Field(default_factory=list)


# ============================================================================
# SCHEMAS LIST RESPONSE (pour compatibilite imports)
# ============================================================================

# Aliases pour uniformite avec autres modules
EventListResponse = EventList
EventDetailResponse = EventResponse  # Alias pour detail


class SpeakerListResponse(BaseModel):
    """Liste paginee des intervenants."""
    items: list[SpeakerResponse]
    total: int
    page: int = 1
    page_size: int = 50


class SessionListResponse(BaseModel):
    """Liste paginee des sessions."""
    items: list[SessionResponse]
    total: int
    page: int = 1
    page_size: int = 50


class TicketTypeListResponse(BaseModel):
    """Liste paginee des types de billets."""
    items: list[TicketTypeResponse]
    total: int
    page: int = 1
    page_size: int = 50


# Alias pour inscription
RegistrationListResponse = RegistrationList


class SponsorListResponse(BaseModel):
    """Liste paginee des sponsors."""
    items: list[SponsorResponse]
    total: int
    page: int = 1
    page_size: int = 50


class DiscountCodeValidation(BaseModel):
    """Validation d'un code promo."""
    code: str
    is_valid: bool
    discount_amount: Decimal = Decimal("0.00")
    discount_percentage: Decimal | None = None
    message: str | None = None


class CertificateTemplateUpdate(BaseModel):
    """Mise a jour template certificat."""
    name: str | None = None
    description: str | None = None
    html_template: str | None = None
    css_styles: str | None = None
    background_image_url: str | None = None
    is_active: bool | None = None


class CertificateListResponse(BaseModel):
    """Liste paginee des certificats."""
    items: list[CertificateResponse]
    total: int
    page: int = 1
    page_size: int = 50


class EvaluationFormUpdate(BaseModel):
    """Mise a jour formulaire evaluation."""
    title: str | None = None
    description: str | None = None
    questions: list[dict] | None = None
    is_anonymous: bool | None = None
    is_required: bool | None = None
    is_active: bool | None = None


class EvaluationListResponse(BaseModel):
    """Liste paginee des evaluations."""
    items: list[EvaluationResponse]
    total: int
    page: int = 1
    page_size: int = 50


# Alias pour compatibilite
EvaluationCreate = EvaluationSubmit


class InvitationListResponse(BaseModel):
    """Liste paginee des invitations."""
    items: list[InvitationResponse]
    total: int
    page: int = 1
    page_size: int = 50


class WaitlistEntryCreate(BaseModel):
    """Creation entree liste d'attente."""
    event_id: UUID
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = None
    notes: str | None = None
    priority: int = 0


class WaitlistEntryResponse(BaseModel):
    """Reponse entree liste d'attente."""
    id: UUID
    event_id: UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    position: int
    status: str = "waiting"
    notified_at: datetime | None = None
    expires_at: datetime | None = None
    converted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WaitlistListResponse(BaseModel):
    """Liste paginee de la liste d'attente."""
    items: list[WaitlistEntryResponse]
    total: int
    page: int = 1
    page_size: int = 50


class CheckInListResponse(BaseModel):
    """Liste paginee des check-ins."""
    items: list[CheckInResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Lieux
    'VenueCreate', 'VenueUpdate', 'VenueResponse', 'VenueListResponse', 'VenueWithRoomsResponse',
    'VenueRoomCreate', 'VenueRoomUpdate', 'VenueRoomResponse',
    # Evenements
    'EventCreate', 'EventUpdate', 'EventResponse', 'EventListResponse', 'EventDetailResponse',
    'EventListItem', 'EventList',
    # Intervenants
    'SpeakerCreate', 'SpeakerUpdate', 'SpeakerResponse', 'SpeakerListResponse',
    'SpeakerAssignmentCreate', 'SpeakerAssignmentUpdate', 'SpeakerAssignmentResponse',
    # Sessions
    'SessionCreate', 'SessionUpdate', 'SessionResponse', 'SessionListResponse', 'SessionWithSpeakersResponse',
    # Billetterie
    'TicketTypeCreate', 'TicketTypeUpdate', 'TicketTypeResponse', 'TicketTypeListResponse',
    # Inscriptions
    'RegistrationCreate', 'RegistrationUpdate', 'RegistrationResponse', 'RegistrationList',
    'RegistrationListResponse',
    # Check-in
    'CheckInCreate', 'CheckInResponse', 'CheckInStats', 'CheckInListResponse',
    # Sponsors
    'SponsorCreate', 'SponsorUpdate', 'SponsorResponse', 'SponsorListResponse',
    # Codes promo
    'DiscountCodeCreate', 'DiscountCodeUpdate', 'DiscountCodeResponse', 'DiscountCodeValidation',
    'DiscountCodeApply', 'DiscountCodeResult',
    # Certificats
    'CertificateTemplateCreate', 'CertificateTemplateUpdate', 'CertificateTemplateResponse',
    'CertificateIssue', 'CertificateResponse', 'CertificateListResponse',
    # Evaluations
    'EvaluationFormCreate', 'EvaluationFormUpdate', 'EvaluationFormResponse',
    'EvaluationSubmit', 'EvaluationCreate', 'EvaluationResponse', 'EvaluationStats', 'EvaluationListResponse',
    # Invitations
    'InvitationCreate', 'InvitationBulkCreate', 'InvitationResponse', 'InvitationListResponse',
    # Waitlist
    'WaitlistEntry', 'WaitlistResponse', 'WaitlistEntryCreate', 'WaitlistEntryResponse', 'WaitlistListResponse',
    # Stats
    'EventStats', 'EventDashboard', 'GlobalEventStats',
    # Agenda
    'AgendaSlot', 'AgendaDay', 'EventAgenda',
]
