"""
AZALS MODULE EVENTS - Modeles SQLAlchemy
=========================================

Modeles complets pour la gestion d'evenements.
Inspire de : Sage, Axonaut, Pennylane, Odoo, Microsoft Dynamics 365

Fonctionnalites :
- Evenements (seminaires, formations, webinars)
- Lieux et salles
- Sessions multiples
- Inscriptions participants
- Capacite et liste d'attente
- Tarification et billetterie
- Intervenants/speakers
- Programme detaille
- Check-in/presence
- Certificats de participation
- Evaluations post-evenement
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class EventType(str, enum.Enum):
    """Type d'evenement."""
    CONFERENCE = "CONFERENCE"
    SEMINAR = "SEMINAR"
    WORKSHOP = "WORKSHOP"
    WEBINAR = "WEBINAR"
    TRAINING = "TRAINING"
    MEETUP = "MEETUP"
    TRADESHOW = "TRADESHOW"
    NETWORKING = "NETWORKING"
    TEAM_BUILDING = "TEAM_BUILDING"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    ANNIVERSARY = "ANNIVERSARY"
    OTHER = "OTHER"


class EventStatus(str, enum.Enum):
    """Statut d'un evenement."""
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    PUBLISHED = "PUBLISHED"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"


class EventFormat(str, enum.Enum):
    """Format de l'evenement."""
    IN_PERSON = "IN_PERSON"
    VIRTUAL = "VIRTUAL"
    HYBRID = "HYBRID"


class TicketType(str, enum.Enum):
    """Type de billet."""
    FREE = "FREE"
    PAID = "PAID"
    DONATION = "DONATION"
    INVITATION = "INVITATION"
    EARLY_BIRD = "EARLY_BIRD"
    VIP = "VIP"
    GROUP = "GROUP"


class RegistrationStatus(str, enum.Enum):
    """Statut d'inscription."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CHECKED_IN = "CHECKED_IN"
    ATTENDED = "ATTENDED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, enum.Enum):
    """Statut de paiement."""
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SessionType(str, enum.Enum):
    """Type de session."""
    KEYNOTE = "KEYNOTE"
    PRESENTATION = "PRESENTATION"
    PANEL = "PANEL"
    WORKSHOP = "WORKSHOP"
    ROUNDTABLE = "ROUNDTABLE"
    BREAK = "BREAK"
    NETWORKING = "NETWORKING"
    REGISTRATION = "REGISTRATION"
    DEMO = "DEMO"
    QA = "QA"


class SpeakerRole(str, enum.Enum):
    """Role d'un intervenant."""
    SPEAKER = "SPEAKER"
    KEYNOTE = "KEYNOTE"
    MODERATOR = "MODERATOR"
    PANELIST = "PANELIST"
    HOST = "HOST"
    TRAINER = "TRAINER"
    FACILITATOR = "FACILITATOR"


class SponsorLevel(str, enum.Enum):
    """Niveau de sponsor."""
    PLATINUM = "PLATINUM"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    PARTNER = "PARTNER"
    MEDIA = "MEDIA"
    COMMUNITY = "COMMUNITY"


class CertificateType(str, enum.Enum):
    """Type de certificat."""
    ATTENDANCE = "ATTENDANCE"
    COMPLETION = "COMPLETION"
    PARTICIPATION = "PARTICIPATION"
    SPEAKER = "SPEAKER"
    ORGANIZER = "ORGANIZER"


class EvaluationStatus(str, enum.Enum):
    """Statut d'evaluation."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


# ============================================================================
# SEQUENCE DE NUMEROTATION
# ============================================================================

class EventSequence(Base):
    """Sequence de numerotation pour les evenements."""
    __tablename__ = "event_sequences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    prefix = Column(String(10), nullable=False, default="EVT")
    last_number = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', 'prefix', name='uq_event_seq_tenant_year_prefix'),
        Index('idx_event_seq_tenant_year', 'tenant_id', 'year'),
    )


# ============================================================================
# LIEUX ET SALLES
# ============================================================================

class Venue(Base):
    """Lieu d'evenement."""
    __tablename__ = "event_venues"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    venue_type = Column(String(50), nullable=True)  # HOTEL, CONVENTION_CENTER, OFFICE, etc.

    # Adresse
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    state = Column(String(100), nullable=True)
    country_code = Column(String(3), default="FR")

    # Coordonnees GPS
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Contact
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    # Capacite et amenagements
    total_capacity = Column(Integer, nullable=True)
    amenities = Column(JSONB, default=list)  # WIFI, PARKING, CATERING, etc.
    accessibility_info = Column(Text, nullable=True)

    # Tarification
    daily_rate = Column(Numeric(12, 2), nullable=True)
    half_day_rate = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")

    # Images
    image_url = Column(String(500), nullable=True)
    gallery_urls = Column(JSONB, default=list)

    # Metadonnees
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    rooms = relationship("VenueRoom", back_populates="venue", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_venue_tenant_code'),
        Index('idx_venues_tenant', 'tenant_id'),
        Index('idx_venues_city', 'tenant_id', 'city'),
        Index('idx_venues_active', 'tenant_id', 'is_active'),
    )


class VenueRoom(Base):
    """Salle dans un lieu."""
    __tablename__ = "event_venue_rooms"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    venue_id = Column(UniversalUUID(), ForeignKey("event_venues.id", ondelete="CASCADE"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    floor = Column(String(20), nullable=True)
    room_number = Column(String(20), nullable=True)

    # Capacite selon configuration
    capacity_theater = Column(Integer, nullable=True)
    capacity_classroom = Column(Integer, nullable=True)
    capacity_banquet = Column(Integer, nullable=True)
    capacity_cocktail = Column(Integer, nullable=True)
    capacity_boardroom = Column(Integer, nullable=True)
    capacity_u_shape = Column(Integer, nullable=True)

    # Equipements
    equipment = Column(JSONB, default=list)  # PROJECTOR, SCREEN, MICROPHONE, etc.
    has_natural_light = Column(Boolean, default=False)
    has_air_conditioning = Column(Boolean, default=True)
    has_video_conference = Column(Boolean, default=False)

    # Tarification
    hourly_rate = Column(Numeric(12, 2), nullable=True)
    daily_rate = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")

    # Metadonnees
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    venue = relationship("Venue", back_populates="rooms")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'venue_id', 'code', name='uq_room_venue_code'),
        Index('idx_rooms_tenant', 'tenant_id'),
        Index('idx_rooms_venue', 'venue_id'),
    )


# ============================================================================
# EVENEMENT PRINCIPAL
# ============================================================================

class Event(Base):
    """Evenement."""
    __tablename__ = "events"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    slug = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)

    # Type et format
    event_type = Column(SQLEnum(EventType), nullable=False, default=EventType.CONFERENCE)
    format = Column(SQLEnum(EventFormat), nullable=False, default=EventFormat.IN_PERSON)
    status = Column(SQLEnum(EventStatus), nullable=False, default=EventStatus.DRAFT)

    # Dates et heures
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    timezone = Column(String(50), default="Europe/Paris")
    all_day = Column(Boolean, default=False)

    # Lieu
    venue_id = Column(UniversalUUID(), ForeignKey("event_venues.id"), nullable=True)
    room_id = Column(UniversalUUID(), ForeignKey("event_venue_rooms.id"), nullable=True)
    location_name = Column(String(255), nullable=True)  # Adresse libre si pas de venue
    location_address = Column(Text, nullable=True)

    # Virtuel
    virtual_platform = Column(String(100), nullable=True)  # ZOOM, TEAMS, GOOGLE_MEET, etc.
    virtual_link = Column(String(500), nullable=True)
    virtual_access_code = Column(String(100), nullable=True)

    # Inscriptions
    registration_required = Column(Boolean, default=True)
    registration_open = Column(Boolean, default=False)
    registration_start_date = Column(DateTime, nullable=True)
    registration_end_date = Column(DateTime, nullable=True)
    max_attendees = Column(Integer, nullable=True)
    min_attendees = Column(Integer, nullable=True)
    waitlist_enabled = Column(Boolean, default=True)
    waitlist_max = Column(Integer, nullable=True)
    approval_required = Column(Boolean, default=False)

    # Capacite et compteurs
    registered_count = Column(Integer, default=0)
    confirmed_count = Column(Integer, default=0)
    waitlist_count = Column(Integer, default=0)
    checkin_count = Column(Integer, default=0)
    cancelled_count = Column(Integer, default=0)

    # Tarification
    is_free = Column(Boolean, default=False)
    default_price = Column(Numeric(12, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))
    tax_included = Column(Boolean, default=True)

    # Revenus
    total_revenue = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_refunds = Column(Numeric(15, 2), default=Decimal("0.00"))

    # Contact organisateur
    organizer_name = Column(String(255), nullable=True)
    organizer_email = Column(String(255), nullable=True)
    organizer_phone = Column(String(50), nullable=True)
    organizer_id = Column(UniversalUUID(), nullable=True)

    # Images et media
    cover_image_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    gallery_urls = Column(JSONB, default=list)
    video_url = Column(String(500), nullable=True)

    # Site web et reseaux
    website_url = Column(String(500), nullable=True)
    social_links = Column(JSONB, default=dict)  # {twitter: url, linkedin: url, ...}

    # Communication
    confirmation_email_template = Column(Text, nullable=True)
    reminder_email_template = Column(Text, nullable=True)
    send_reminders = Column(Boolean, default=True)
    reminder_days_before = Column(JSONB, default=lambda: [7, 1])  # Jours avant l'evenement

    # Certificats
    issue_certificates = Column(Boolean, default=False)
    certificate_template_id = Column(UniversalUUID(), nullable=True)
    min_attendance_for_certificate = Column(Numeric(5, 2), default=Decimal("80.00"))

    # Evaluations
    enable_evaluations = Column(Boolean, default=True)
    evaluation_form_id = Column(UniversalUUID(), nullable=True)
    evaluation_deadline_days = Column(Integer, default=7)

    # Classification
    category = Column(String(100), nullable=True)
    tags = Column(JSONB, default=list)
    target_audience = Column(String(255), nullable=True)
    language = Column(String(10), default="fr")

    # Visibilite
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    visibility = Column(String(20), default="PUBLIC")  # PUBLIC, PRIVATE, UNLISTED

    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)

    # Custom fields
    custom_fields = Column(JSONB, default=dict)
    registration_form_fields = Column(JSONB, default=list)

    # Dates de publication
    published_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    venue = relationship("Venue", foreign_keys=[venue_id])
    room = relationship("VenueRoom", foreign_keys=[room_id])
    sessions = relationship("EventSession", back_populates="event", cascade="all, delete-orphan")
    ticket_types = relationship("EventTicketType", back_populates="event", cascade="all, delete-orphan")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    sponsors = relationship("EventSponsor", back_populates="event", cascade="all, delete-orphan")
    speakers = relationship("EventSpeakerAssignment", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_event_tenant_code'),
        Index('idx_events_tenant', 'tenant_id'),
        Index('idx_events_dates', 'tenant_id', 'start_date', 'end_date'),
        Index('idx_events_status', 'tenant_id', 'status'),
        Index('idx_events_type', 'tenant_id', 'event_type'),
        Index('idx_events_public', 'tenant_id', 'is_public', 'status'),
        Index('idx_events_slug', 'tenant_id', 'slug'),
        Index('idx_events_active', 'tenant_id', 'is_active', 'deleted_at'),
    )


# ============================================================================
# INTERVENANTS / SPEAKERS
# ============================================================================

class Speaker(Base):
    """Intervenant (catalogue global)."""
    __tablename__ = "event_speakers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Professionnel
    title = Column(String(100), nullable=True)  # Dr., Prof., etc.
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)

    # Bio
    bio_short = Column(String(500), nullable=True)
    bio_full = Column(Text, nullable=True)

    # Media
    photo_url = Column(String(500), nullable=True)
    video_intro_url = Column(String(500), nullable=True)

    # Reseaux sociaux
    linkedin_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)
    website_url = Column(String(500), nullable=True)
    social_links = Column(JSONB, default=dict)

    # Competences
    topics = Column(JSONB, default=list)
    expertise_areas = Column(JSONB, default=list)
    languages = Column(JSONB, default=list)

    # Tarification
    fee_keynote = Column(Numeric(12, 2), nullable=True)
    fee_workshop = Column(Numeric(12, 2), nullable=True)
    fee_panel = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    travel_requirements = Column(Text, nullable=True)

    # Contact
    contact_id = Column(UniversalUUID(), nullable=True)  # Lien vers contacts
    employee_id = Column(UniversalUUID(), nullable=True)  # Lien vers employes

    # Statistiques
    total_events = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    is_internal = Column(Boolean, default=False)  # Intervenant interne
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    assignments = relationship("EventSpeakerAssignment", back_populates="speaker")

    __table_args__ = (
        Index('idx_speakers_tenant', 'tenant_id'),
        Index('idx_speakers_name', 'tenant_id', 'last_name', 'first_name'),
        Index('idx_speakers_email', 'tenant_id', 'email'),
        Index('idx_speakers_active', 'tenant_id', 'is_active'),
    )

    @property
    def full_name(self) -> str:
        """Nom complet."""
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class EventSpeakerAssignment(Base):
    """Affectation d'un intervenant a un evenement."""
    __tablename__ = "event_speaker_assignments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(UniversalUUID(), ForeignKey("event_speakers.id", ondelete="CASCADE"), nullable=False)

    role = Column(SQLEnum(SpeakerRole), default=SpeakerRole.SPEAKER)
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)

    # Bio specifique evenement
    bio_override = Column(Text, nullable=True)
    photo_override_url = Column(String(500), nullable=True)

    # Remuneration
    agreed_fee = Column(Numeric(12, 2), nullable=True)
    fee_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    expenses_covered = Column(Boolean, default=False)
    travel_arranged = Column(Boolean, default=False)

    # Ordre d'affichage
    display_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    event = relationship("Event", back_populates="speakers")
    speaker = relationship("Speaker", back_populates="assignments")
    session_assignments = relationship("SessionSpeaker", back_populates="event_assignment", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('event_id', 'speaker_id', name='uq_event_speaker'),
        Index('idx_speaker_assignments_tenant', 'tenant_id'),
        Index('idx_speaker_assignments_event', 'event_id'),
        Index('idx_speaker_assignments_speaker', 'speaker_id'),
    )


# ============================================================================
# SESSIONS / PROGRAMME
# ============================================================================

class EventSession(Base):
    """Session d'un evenement."""
    __tablename__ = "event_sessions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Identification
    code = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type et format
    session_type = Column(SQLEnum(SessionType), default=SessionType.PRESENTATION)
    track = Column(String(100), nullable=True)  # Parcours thematique
    level = Column(String(50), nullable=True)  # BEGINNER, INTERMEDIATE, ADVANCED

    # Horaires
    session_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=True)

    # Lieu
    room_id = Column(UniversalUUID(), ForeignKey("event_venue_rooms.id"), nullable=True)
    room_name = Column(String(255), nullable=True)  # Si pas de room_id
    virtual_link = Column(String(500), nullable=True)

    # Capacite
    capacity = Column(Integer, nullable=True)
    registered_count = Column(Integer, default=0)
    attendee_count = Column(Integer, default=0)

    # Inscription session
    requires_registration = Column(Boolean, default=False)
    registration_open = Column(Boolean, default=True)
    extra_fee = Column(Numeric(12, 2), default=Decimal("0.00"))

    # Contenu
    objectives = Column(JSONB, default=list)
    prerequisites = Column(Text, nullable=True)
    materials_url = Column(String(500), nullable=True)
    slides_url = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    handout_url = Column(String(500), nullable=True)
    live_stream_url = Column(String(500), nullable=True)

    # Classification
    tags = Column(JSONB, default=list)
    language = Column(String(10), default="fr")

    # Affichage
    display_order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_visible = Column(Boolean, default=True)
    color = Column(String(20), nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    cancelled_reason = Column(Text, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    event = relationship("Event", back_populates="sessions")
    room = relationship("VenueRoom", foreign_keys=[room_id])
    speakers = relationship("SessionSpeaker", back_populates="session", cascade="all, delete-orphan")
    attendances = relationship("SessionAttendance", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_sessions_tenant', 'tenant_id'),
        Index('idx_sessions_event', 'event_id'),
        Index('idx_sessions_date_time', 'event_id', 'session_date', 'start_time'),
        Index('idx_sessions_track', 'event_id', 'track'),
    )


class SessionSpeaker(Base):
    """Intervenant d'une session."""
    __tablename__ = "event_session_speakers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    session_id = Column(UniversalUUID(), ForeignKey("event_sessions.id", ondelete="CASCADE"), nullable=False)
    event_assignment_id = Column(UniversalUUID(), ForeignKey("event_speaker_assignments.id", ondelete="CASCADE"), nullable=False)

    role = Column(SQLEnum(SpeakerRole), default=SpeakerRole.SPEAKER)
    display_order = Column(Integer, default=0)
    is_main_speaker = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    session = relationship("EventSession", back_populates="speakers")
    event_assignment = relationship("EventSpeakerAssignment", back_populates="session_assignments")

    __table_args__ = (
        UniqueConstraint('session_id', 'event_assignment_id', name='uq_session_speaker'),
        Index('idx_session_speakers_session', 'session_id'),
    )


# ============================================================================
# BILLETTERIE
# ============================================================================

class EventTicketType(Base):
    """Type de billet pour un evenement."""
    __tablename__ = "event_ticket_types"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ticket_type = Column(SQLEnum(TicketType), default=TicketType.PAID)

    # Tarification
    price = Column(Numeric(12, 2), default=Decimal("0.00"))
    original_price = Column(Numeric(12, 2), nullable=True)  # Prix barre
    currency = Column(String(3), default="EUR")
    tax_rate = Column(Numeric(5, 2), default=Decimal("20.00"))
    tax_included = Column(Boolean, default=True)

    # Quantite
    quantity_available = Column(Integer, nullable=True)
    quantity_sold = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    max_per_order = Column(Integer, default=10)
    min_per_order = Column(Integer, default=1)

    # Vente
    sales_start_date = Column(DateTime, nullable=True)
    sales_end_date = Column(DateTime, nullable=True)
    is_visible = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)

    # Restrictions
    requires_approval = Column(Boolean, default=False)
    eligibility_criteria = Column(Text, nullable=True)
    allowed_domains = Column(JSONB, default=list)  # Emails autorises

    # Sessions incluses
    includes_all_sessions = Column(Boolean, default=True)
    included_session_ids = Column(JSONB, default=list)

    # Avantages
    perks = Column(JSONB, default=list)  # Liste des avantages

    # Affichage
    display_order = Column(Integer, default=0)
    badge_text = Column(String(50), nullable=True)  # "BEST VALUE", "LIMITED", etc.
    color = Column(String(20), nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    event = relationship("Event", back_populates="ticket_types")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'event_id', 'code', name='uq_ticket_type_event_code'),
        Index('idx_ticket_types_event', 'event_id'),
        Index('idx_ticket_types_available', 'event_id', 'is_available', 'is_visible'),
    )

    @property
    def quantity_remaining(self) -> int | None:
        """Quantite restante."""
        if self.quantity_available is None:
            return None
        return max(0, self.quantity_available - self.quantity_sold - self.quantity_reserved)

    @property
    def is_sold_out(self) -> bool:
        """Est epuise."""
        remaining = self.quantity_remaining
        return remaining is not None and remaining <= 0


# ============================================================================
# INSCRIPTIONS
# ============================================================================

class EventRegistration(Base):
    """Inscription a un evenement."""
    __tablename__ = "event_registrations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(UniversalUUID(), ForeignKey("event_ticket_types.id"), nullable=True)

    # Numero d'inscription
    registration_number = Column(String(50), nullable=False)
    qr_code = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)

    # Participant
    attendee_id = Column(UniversalUUID(), nullable=True)  # Lien vers contact si existe
    contact_id = Column(UniversalUUID(), nullable=True)

    # Informations participant
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)

    # Statuts
    status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.PENDING)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)

    # Tarification
    ticket_price = Column(Numeric(12, 2), default=Decimal("0.00"))
    discount_code = Column(String(50), nullable=True)
    discount_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    tax_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    amount_paid = Column(Numeric(12, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")

    # Paiement
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    invoice_id = Column(UniversalUUID(), nullable=True)
    invoice_number = Column(String(50), nullable=True)

    # Sessions
    selected_sessions = Column(JSONB, default=list)

    # Informations supplementaires
    dietary_requirements = Column(String(255), nullable=True)
    accessibility_needs = Column(Text, nullable=True)
    special_requests = Column(Text, nullable=True)
    custom_answers = Column(JSONB, default=dict)

    # Communication
    marketing_consent = Column(Boolean, default=False)
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Check-in
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)
    checked_in_by = Column(UniversalUUID(), nullable=True)
    check_in_method = Column(String(50), nullable=True)  # QR, MANUAL, BADGE
    check_in_location = Column(String(255), nullable=True)

    # Badge
    badge_printed = Column(Boolean, default=False)
    badge_printed_at = Column(DateTime, nullable=True)
    badge_name = Column(String(255), nullable=True)  # Nom sur le badge si different

    # Certificat
    certificate_issued = Column(Boolean, default=False)
    certificate_issued_at = Column(DateTime, nullable=True)
    certificate_id = Column(UniversalUUID(), nullable=True)
    certificate_url = Column(String(500), nullable=True)

    # Evaluation
    evaluation_completed = Column(Boolean, default=False)
    evaluation_completed_at = Column(DateTime, nullable=True)
    evaluation_id = Column(UniversalUUID(), nullable=True)

    # Presence
    attendance_duration_minutes = Column(Integer, nullable=True)
    attendance_percentage = Column(Numeric(5, 2), nullable=True)

    # Annulation / Remboursement
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(UniversalUUID(), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    refund_requested = Column(Boolean, default=False)
    refund_amount = Column(Numeric(12, 2), default=Decimal("0.00"))
    refund_date = Column(DateTime, nullable=True)
    refund_reference = Column(String(255), nullable=True)

    # Source
    source = Column(String(100), nullable=True)  # WEBSITE, ADMIN, API, IMPORT
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    referrer = Column(String(500), nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    tags = Column(JSONB, default=list)
    is_vip = Column(Boolean, default=False)
    is_speaker = Column(Boolean, default=False)
    is_sponsor = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relations
    event = relationship("Event", back_populates="registrations")
    ticket_type = relationship("EventTicketType", foreign_keys=[ticket_type_id])
    session_attendances = relationship("SessionAttendance", back_populates="registration", cascade="all, delete-orphan")
    check_ins = relationship("EventCheckIn", back_populates="registration", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'registration_number', name='uq_registration_number'),
        Index('idx_registrations_tenant', 'tenant_id'),
        Index('idx_registrations_event', 'event_id'),
        Index('idx_registrations_status', 'event_id', 'status'),
        Index('idx_registrations_email', 'tenant_id', 'email'),
        Index('idx_registrations_qr', 'tenant_id', 'qr_code'),
        Index('idx_registrations_attendee', 'tenant_id', 'attendee_id'),
        Index('idx_registrations_active', 'tenant_id', 'deleted_at'),
    )

    @property
    def full_name(self) -> str:
        """Nom complet."""
        return f"{self.first_name} {self.last_name}"


# ============================================================================
# CHECK-IN ET PRESENCE
# ============================================================================

class EventCheckIn(Base):
    """Enregistrement de check-in."""
    __tablename__ = "event_check_ins"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UniversalUUID(), ForeignKey("event_registrations.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UniversalUUID(), ForeignKey("event_sessions.id"), nullable=True)

    check_in_type = Column(String(20), default="IN")  # IN, OUT
    method = Column(String(50), nullable=True)  # QR, MANUAL, BADGE, NFC
    location = Column(String(255), nullable=True)
    device_id = Column(String(100), nullable=True)

    checked_at = Column(DateTime, default=datetime.utcnow)
    checked_by = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)

    # Relations
    registration = relationship("EventRegistration", back_populates="check_ins")

    __table_args__ = (
        Index('idx_checkins_registration', 'registration_id'),
        Index('idx_checkins_event', 'event_id'),
        Index('idx_checkins_session', 'session_id'),
        Index('idx_checkins_time', 'event_id', 'checked_at'),
    )


class SessionAttendance(Base):
    """Presence a une session."""
    __tablename__ = "event_session_attendances"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    session_id = Column(UniversalUUID(), ForeignKey("event_sessions.id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UniversalUUID(), ForeignKey("event_registrations.id", ondelete="CASCADE"), nullable=False)

    # Inscription
    registered_at = Column(DateTime, default=datetime.utcnow)
    waitlisted = Column(Boolean, default=False)

    # Presence
    attended = Column(Boolean, default=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    session = relationship("EventSession", back_populates="attendances")
    registration = relationship("EventRegistration", back_populates="session_attendances")

    __table_args__ = (
        UniqueConstraint('session_id', 'registration_id', name='uq_session_attendance'),
        Index('idx_session_attendance_session', 'session_id'),
        Index('idx_session_attendance_registration', 'registration_id'),
    )


# ============================================================================
# SPONSORS
# ============================================================================

class EventSponsor(Base):
    """Sponsor d'un evenement."""
    __tablename__ = "event_sponsors"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Identification
    name = Column(String(255), nullable=False)
    level = Column(SQLEnum(SponsorLevel), default=SponsorLevel.PARTNER)
    description = Column(Text, nullable=True)

    # Contact
    contact_id = Column(UniversalUUID(), nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Media
    logo_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)

    # Financier
    amount_pledged = Column(Numeric(12, 2), default=Decimal("0.00"))
    amount_paid = Column(Numeric(12, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="EUR")
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    invoice_id = Column(UniversalUUID(), nullable=True)

    # Avantages
    benefits = Column(JSONB, default=list)
    booth_location = Column(String(100), nullable=True)
    booth_size = Column(String(50), nullable=True)
    speaking_slot = Column(Boolean, default=False)
    logo_on_materials = Column(Boolean, default=True)
    attendee_list_access = Column(Boolean, default=False)

    # Affichage
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Metadonnees
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    event = relationship("Event", back_populates="sponsors")

    __table_args__ = (
        Index('idx_sponsors_event', 'event_id'),
        Index('idx_sponsors_level', 'event_id', 'level'),
    )


# ============================================================================
# CODES PROMO
# ============================================================================

class EventDiscountCode(Base):
    """Code de reduction pour un evenement."""
    __tablename__ = "event_discount_codes"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Code
    code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)

    # Type de remise
    discount_type = Column(String(20), nullable=False)  # PERCENTAGE, FIXED, FREE
    discount_value = Column(Numeric(12, 2), default=Decimal("0.00"))
    max_discount_amount = Column(Numeric(12, 2), nullable=True)

    # Utilisation
    max_uses = Column(Integer, nullable=True)
    max_uses_per_user = Column(Integer, default=1)
    uses_count = Column(Integer, default=0)

    # Validite
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Restrictions
    applicable_ticket_types = Column(JSONB, default=list)  # IDs des types de billets
    min_tickets = Column(Integer, default=1)
    min_amount = Column(Numeric(12, 2), nullable=True)

    # Metadonnees
    notes = Column(Text, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'event_id', 'code', name='uq_discount_code_event'),
        Index('idx_discount_codes_event', 'event_id'),
        Index('idx_discount_codes_code', 'tenant_id', 'code'),
    )


# ============================================================================
# CERTIFICATS
# ============================================================================

class EventCertificateTemplate(Base):
    """Template de certificat."""
    __tablename__ = "event_certificate_templates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    certificate_type = Column(SQLEnum(CertificateType), default=CertificateType.ATTENDANCE)

    # Design
    template_html = Column(Text, nullable=True)
    template_url = Column(String(500), nullable=True)
    background_url = Column(String(500), nullable=True)
    signature_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)

    # Contenu
    title_text = Column(String(255), nullable=True)
    body_text = Column(Text, nullable=True)
    footer_text = Column(Text, nullable=True)
    signatory_name = Column(String(255), nullable=True)
    signatory_title = Column(String(255), nullable=True)

    # Format
    page_size = Column(String(20), default="A4")
    orientation = Column(String(20), default="LANDSCAPE")

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_cert_templates_tenant', 'tenant_id'),
    )


class EventCertificate(Base):
    """Certificat genere."""
    __tablename__ = "event_certificates"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UniversalUUID(), ForeignKey("event_registrations.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UniversalUUID(), ForeignKey("event_certificate_templates.id"), nullable=True)

    certificate_number = Column(String(50), nullable=False)
    certificate_type = Column(SQLEnum(CertificateType), default=CertificateType.ATTENDANCE)

    # Participant
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)

    # Contenu
    event_title = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    hours_attended = Column(Numeric(6, 2), nullable=True)
    grade = Column(String(20), nullable=True)
    additional_info = Column(JSONB, default=dict)

    # Fichier
    file_url = Column(String(500), nullable=True)
    verification_code = Column(String(100), nullable=True)
    verification_url = Column(String(500), nullable=True)

    # Envoi
    sent_at = Column(DateTime, nullable=True)
    downloaded_at = Column(DateTime, nullable=True)

    issued_at = Column(DateTime, default=datetime.utcnow)
    issued_by = Column(UniversalUUID(), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'certificate_number', name='uq_certificate_number'),
        Index('idx_certificates_event', 'event_id'),
        Index('idx_certificates_registration', 'registration_id'),
        Index('idx_certificates_verification', 'verification_code'),
    )


# ============================================================================
# EVALUATIONS
# ============================================================================

class EventEvaluationForm(Base):
    """Formulaire d'evaluation."""
    __tablename__ = "event_evaluation_forms"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    form_type = Column(String(50), default="EVENT")  # EVENT, SESSION, SPEAKER

    # Questions
    questions = Column(JSONB, default=list)
    # Format: [{id, type, question, required, options, ...}]

    # Parametres
    allow_anonymous = Column(Boolean, default=False)
    require_all_questions = Column(Boolean, default=False)

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_eval_forms_tenant', 'tenant_id'),
    )


class EventEvaluation(Base):
    """Evaluation soumise."""
    __tablename__ = "event_evaluations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UniversalUUID(), ForeignKey("event_registrations.id"), nullable=True)
    session_id = Column(UniversalUUID(), ForeignKey("event_sessions.id"), nullable=True)
    speaker_id = Column(UniversalUUID(), ForeignKey("event_speakers.id"), nullable=True)
    form_id = Column(UniversalUUID(), ForeignKey("event_evaluation_forms.id"), nullable=True)

    evaluation_type = Column(String(50), default="EVENT")  # EVENT, SESSION, SPEAKER
    status = Column(SQLEnum(EvaluationStatus), default=EvaluationStatus.COMPLETED)

    # Reponses
    responses = Column(JSONB, default=dict)
    # Format: {question_id: response}

    # Scores
    overall_rating = Column(Numeric(3, 2), nullable=True)  # 1-5
    nps_score = Column(Integer, nullable=True)  # 0-10 Net Promoter Score
    recommendation_likelihood = Column(Integer, nullable=True)  # 1-10

    # Commentaires
    positive_feedback = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    additional_comments = Column(Text, nullable=True)

    # Anonymat
    is_anonymous = Column(Boolean, default=False)

    submitted_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_evaluations_event', 'event_id'),
        Index('idx_evaluations_session', 'session_id'),
        Index('idx_evaluations_registration', 'registration_id'),
    )


# ============================================================================
# INVITATIONS
# ============================================================================

class EventInvitation(Base):
    """Invitation a un evenement."""
    __tablename__ = "event_invitations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(UniversalUUID(), ForeignKey("event_ticket_types.id"), nullable=True)

    # Destinataire
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    contact_id = Column(UniversalUUID(), nullable=True)

    # Code invitation
    invitation_code = Column(String(100), nullable=False)
    invitation_type = Column(String(50), default="STANDARD")  # STANDARD, VIP, SPEAKER, SPONSOR

    # Statut
    status = Column(String(50), default="PENDING")  # PENDING, SENT, VIEWED, ACCEPTED, DECLINED, EXPIRED
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response = Column(String(20), nullable=True)  # ACCEPTED, DECLINED

    # Remise
    discount_code = Column(String(50), nullable=True)
    complimentary = Column(Boolean, default=False)

    # Message
    personal_message = Column(Text, nullable=True)

    # Resultat
    registration_id = Column(UniversalUUID(), nullable=True)

    expires_at = Column(DateTime, nullable=True)
    created_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'invitation_code', name='uq_invitation_code'),
        Index('idx_invitations_event', 'event_id'),
        Index('idx_invitations_email', 'tenant_id', 'email'),
        Index('idx_invitations_code', 'invitation_code'),
    )


# ============================================================================
# WAITLIST
# ============================================================================

class EventWaitlist(Base):
    """Liste d'attente."""
    __tablename__ = "event_waitlist"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(UniversalUUID(), ForeignKey("event_ticket_types.id"), nullable=True)
    session_id = Column(UniversalUUID(), ForeignKey("event_sessions.id"), nullable=True)

    # Participant
    email = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    contact_id = Column(UniversalUUID(), nullable=True)

    # Position
    position = Column(Integer, nullable=False)

    # Statut
    status = Column(String(50), default="WAITING")  # WAITING, NOTIFIED, CONVERTED, EXPIRED, CANCELLED
    notified_at = Column(DateTime, nullable=True)
    notification_expires_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    registration_id = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_waitlist_event', 'event_id'),
        Index('idx_waitlist_position', 'event_id', 'ticket_type_id', 'position'),
        Index('idx_waitlist_email', 'tenant_id', 'email'),
    )


# ============================================================================
# COMMUNICATION
# ============================================================================

class EventEmailLog(Base):
    """Journal des emails envoyes."""
    __tablename__ = "event_email_logs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    event_id = Column(UniversalUUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UniversalUUID(), ForeignKey("event_registrations.id"), nullable=True)

    email_type = Column(String(50), nullable=False)  # CONFIRMATION, REMINDER, INVITATION, etc.
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    body_preview = Column(Text, nullable=True)

    # Statut
    status = Column(String(50), default="SENT")  # SENT, DELIVERED, OPENED, CLICKED, BOUNCED, FAILED
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Tracking
    message_id = Column(String(255), nullable=True)

    __table_args__ = (
        Index('idx_email_logs_event', 'event_id'),
        Index('idx_email_logs_registration', 'registration_id'),
        Index('idx_email_logs_type', 'event_id', 'email_type'),
    )


# ============================================================================
# EXPORT DES MODELES
# ============================================================================

__all__ = [
    # Enums
    'EventType',
    'EventStatus',
    'EventFormat',
    'TicketType',
    'RegistrationStatus',
    'PaymentStatus',
    'SessionType',
    'SpeakerRole',
    'SponsorLevel',
    'CertificateType',
    'EvaluationStatus',
    # Sequence
    'EventSequence',
    # Lieux
    'Venue',
    'VenueRoom',
    # Evenement
    'Event',
    # Intervenants
    'Speaker',
    'EventSpeakerAssignment',
    # Sessions
    'EventSession',
    'SessionSpeaker',
    # Billetterie
    'EventTicketType',
    # Inscriptions
    'EventRegistration',
    # Check-in
    'EventCheckIn',
    'SessionAttendance',
    # Sponsors
    'EventSponsor',
    # Codes promo
    'EventDiscountCode',
    # Certificats
    'EventCertificateTemplate',
    'EventCertificate',
    # Evaluations
    'EventEvaluationForm',
    'EventEvaluation',
    # Invitations
    'EventInvitation',
    # Waitlist
    'EventWaitlist',
    # Communication
    'EventEmailLog',
]
