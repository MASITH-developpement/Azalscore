"""
AZALS MODULE - Appointments / Rendez-vous
==========================================

Modeles SQLAlchemy pour la gestion complete des rendez-vous.

Fonctionnalites inspirees de:
- Sage CRM (rendez-vous recurrents, planification)
- Axonaut (integration CRM, rappels automatiques)
- Odoo (multi-participants, types configurables, ressources)
- Microsoft Dynamics 365 (schedule board, AI scheduling)
- Pennylane (mobilite, synchronisation calendrier)

Conformite AZALSCORE:
- tenant_id sur toutes les entites
- Soft delete: is_deleted, deleted_at, deleted_by
- Audit: created_at, created_by, updated_at, updated_by
- Version pour optimistic locking
"""

import enum
import uuid
from datetime import datetime, date, time
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

class AppointmentStatus(str, enum.Enum):
    """Statut d'un rendez-vous."""
    DRAFT = "DRAFT"                     # Brouillon
    PENDING = "PENDING"                 # En attente de confirmation
    CONFIRMED = "CONFIRMED"             # Confirme
    CHECKED_IN = "CHECKED_IN"           # Client arrive
    IN_PROGRESS = "IN_PROGRESS"         # En cours
    COMPLETED = "COMPLETED"             # Termine
    CANCELLED = "CANCELLED"             # Annule
    NO_SHOW = "NO_SHOW"                 # Absent
    RESCHEDULED = "RESCHEDULED"         # Replanifie


class AppointmentMode(str, enum.Enum):
    """Mode du rendez-vous (inspire Odoo/Dynamics)."""
    IN_PERSON = "IN_PERSON"             # En presentiel
    PHONE = "PHONE"                     # Telephonique
    VIDEO = "VIDEO"                     # Visioconference
    HOME_VISIT = "HOME_VISIT"           # Visite a domicile
    ON_SITE = "ON_SITE"                 # Sur site client
    HYBRID = "HYBRID"                   # Hybride


class AppointmentPriority(str, enum.Enum):
    """Priorite du rendez-vous."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RecurrencePattern(str, enum.Enum):
    """Pattern de recurrence (inspire Sage CRM)."""
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class RecurrenceEndType(str, enum.Enum):
    """Type de fin de recurrence."""
    NEVER = "NEVER"
    AFTER_COUNT = "AFTER_COUNT"
    BY_DATE = "BY_DATE"


class ReminderType(str, enum.Enum):
    """Type de rappel (inspire Axonaut)."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    WHATSAPP = "WHATSAPP"


class ReminderStatus(str, enum.Enum):
    """Statut d'envoi du rappel."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AttendeeRole(str, enum.Enum):
    """Role d'un participant."""
    ORGANIZER = "ORGANIZER"             # Organisateur
    REQUIRED = "REQUIRED"               # Requis
    OPTIONAL = "OPTIONAL"               # Optionnel
    RESOURCE = "RESOURCE"               # Ressource (salle, equipement)
    OBSERVER = "OBSERVER"               # Observateur


class AttendeeStatus(str, enum.Enum):
    """Statut de participation."""
    PENDING = "PENDING"                 # En attente de reponse
    ACCEPTED = "ACCEPTED"               # Accepte
    DECLINED = "DECLINED"               # Refuse
    TENTATIVE = "TENTATIVE"             # Peut-etre
    DELEGATED = "DELEGATED"             # Delegue


class AvailabilityType(str, enum.Enum):
    """Type de disponibilite."""
    AVAILABLE = "AVAILABLE"             # Disponible
    BUSY = "BUSY"                       # Occupe
    BLOCKED = "BLOCKED"                 # Bloque
    HOLIDAY = "HOLIDAY"                 # Conge/Ferie
    OUT_OF_OFFICE = "OUT_OF_OFFICE"     # Absent
    TENTATIVE = "TENTATIVE"             # Provisoire


class BookingMode(str, enum.Enum):
    """Mode de reservation (inspire Odoo)."""
    INSTANT = "INSTANT"                 # Confirmation instantanee
    REQUEST = "REQUEST"                 # Sur demande
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"  # Approbation requise


class ResourceType(str, enum.Enum):
    """Type de ressource (inspire Odoo)."""
    ROOM = "ROOM"                       # Salle de reunion
    EQUIPMENT = "EQUIPMENT"             # Equipement
    VEHICLE = "VEHICLE"                 # Vehicule
    PERSON = "PERSON"                   # Personne/Staff
    OTHER = "OTHER"                     # Autre


class SyncProvider(str, enum.Enum):
    """Fournisseur de synchronisation calendrier."""
    GOOGLE = "GOOGLE"
    OUTLOOK = "OUTLOOK"
    APPLE = "APPLE"
    CALDAV = "CALDAV"


class ConflictResolution(str, enum.Enum):
    """Resolution de conflit de planning."""
    BLOCK = "BLOCK"                     # Bloquer
    WARN = "WARN"                       # Avertir
    ALLOW = "ALLOW"                     # Autoriser (double booking)


# ============================================================================
# SEQUENCE NUMEROTATION
# ============================================================================

class AppointmentSequence(Base):
    """Sequence de numerotation des rendez-vous par tenant et annee."""
    __tablename__ = "appointment_sequences"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    prefix = Column(String(20), nullable=False, default="RDV")
    last_number = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'year', 'prefix', name='uq_apt_seq_tenant_year_prefix'),
        Index('idx_apt_seq_tenant_year', 'tenant_id', 'year'),
    )


# ============================================================================
# TYPE DE RENDEZ-VOUS
# ============================================================================

class AppointmentType(Base):
    """
    Type de rendez-vous configurable (inspire Odoo).

    Permet de definir des types comme:
    - Consultation 30min
    - Reunion commerciale 1h
    - Visite technique 2h
    """
    __tablename__ = "appointment_types"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Commercial, RH, Technique, etc.
    color = Column(String(20), nullable=True)  # Code couleur hex

    # Duree
    default_duration_minutes = Column(Integer, nullable=False, default=30)
    min_duration_minutes = Column(Integer, nullable=True)
    max_duration_minutes = Column(Integer, nullable=True)
    buffer_before_minutes = Column(Integer, default=0)  # Temps avant
    buffer_after_minutes = Column(Integer, default=0)   # Temps apres

    # Mode par defaut
    default_mode = Column(
        SQLEnum(AppointmentMode, name='appointment_type_mode'),
        default=AppointmentMode.IN_PERSON
    )
    allowed_modes = Column(JSONB, default=list)  # Liste des modes autorises

    # Tarification
    is_billable = Column(Boolean, default=False)
    default_price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    requires_payment = Column(Boolean, default=False)
    deposit_amount = Column(Numeric(12, 2), nullable=True)
    deposit_percentage = Column(Numeric(5, 2), nullable=True)

    # Reservation
    booking_mode = Column(
        SQLEnum(BookingMode, name='appointment_type_booking_mode'),
        default=BookingMode.INSTANT
    )
    min_notice_hours = Column(Integer, default=24)      # Preavis minimum
    max_advance_days = Column(Integer, default=60)      # Reservation max a l'avance
    cancellation_hours = Column(Integer, default=24)    # Delai d'annulation
    max_participants = Column(Integer, default=1)
    allow_guest_booking = Column(Boolean, default=False)  # Reservation sans compte
    allow_waitlist = Column(Boolean, default=True)

    # Formulaire de reservation
    booking_form_fields = Column(JSONB, default=list)  # Champs supplementaires
    booking_questions = Column(JSONB, default=list)    # Questions a l'inscription

    # Rappels par defaut
    default_reminders = Column(JSONB, default=list)  # [{type, hours_before}]

    # Affectation
    assigned_resources = Column(JSONB, default=list)  # IDs ressources assignees
    assigned_staff = Column(JSONB, default=list)      # IDs staff assignes
    requires_resource = Column(Boolean, default=False)

    # Location
    default_location = Column(String(500), nullable=True)
    video_provider = Column(String(50), nullable=True)  # zoom, meet, teams

    # Statut
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Visible reservation en ligne
    sort_order = Column(Integer, default=0)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    appointments = relationship("Appointment", back_populates="appointment_type", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_apt_type_code'),
        Index('idx_apt_type_tenant', 'tenant_id'),
        Index('idx_apt_type_active', 'tenant_id', 'is_active', 'is_deleted'),
        Index('idx_apt_type_category', 'tenant_id', 'category'),
    )


# ============================================================================
# RESSOURCE
# ============================================================================

class Resource(Base):
    """
    Ressource reservable (inspire Odoo).

    Peut etre une salle, un equipement, un vehicule, etc.
    """
    __tablename__ = "appointment_resources"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    code = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(
        SQLEnum(ResourceType, name='resource_type'),
        nullable=False,
        default=ResourceType.ROOM
    )
    color = Column(String(20), nullable=True)
    image_url = Column(String(500), nullable=True)

    # Capacite
    capacity = Column(Integer, nullable=True)

    # Localisation
    location = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    building = Column(String(100), nullable=True)
    floor = Column(String(20), nullable=True)
    room_number = Column(String(50), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Equipements inclus
    amenities = Column(JSONB, default=list)  # ["projector", "whiteboard", "video_conf"]

    # Tarification
    is_billable = Column(Boolean, default=False)
    hourly_rate = Column(Numeric(12, 2), nullable=True)
    daily_rate = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")

    # Disponibilite
    is_available = Column(Boolean, default=True)
    availability_schedule = Column(JSONB, default=dict)  # Horaires par jour
    conflict_resolution = Column(
        SQLEnum(ConflictResolution, name='resource_conflict_resolution'),
        default=ConflictResolution.BLOCK
    )

    # Staff associe (si resource_type=PERSON)
    staff_id = Column(UniversalUUID(), nullable=True)
    user_id = Column(UniversalUUID(), nullable=True)

    # Tags
    tags = Column(JSONB, default=list)

    # Statut
    is_active = Column(Boolean, default=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_resource_code'),
        Index('idx_resource_tenant', 'tenant_id'),
        Index('idx_resource_type', 'tenant_id', 'resource_type'),
        Index('idx_resource_active', 'tenant_id', 'is_active', 'is_deleted'),
    )


# ============================================================================
# RENDEZ-VOUS PRINCIPAL
# ============================================================================

class Appointment(Base):
    """
    Rendez-vous principal.

    Integre les fonctionnalites de:
    - Sage CRM: recurrence, planification
    - Axonaut: rappels, integration CRM
    - Odoo: multi-participants, ressources
    - Dynamics 365: schedule board, conflits
    """
    __tablename__ = "appointments"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Code auto-genere (RDV-YYYY-XXXX)
    code = Column(String(30), nullable=False)

    # Type
    type_id = Column(
        UniversalUUID(),
        ForeignKey("appointment_types.id"),
        nullable=True,
        index=True
    )

    # Titre et description
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Notes internes

    # Statut et mode
    status = Column(
        SQLEnum(AppointmentStatus, name='appointment_status'),
        nullable=False,
        default=AppointmentStatus.DRAFT
    )
    mode = Column(
        SQLEnum(AppointmentMode, name='appointment_mode'),
        nullable=False,
        default=AppointmentMode.IN_PERSON
    )
    priority = Column(
        SQLEnum(AppointmentPriority, name='appointment_priority'),
        nullable=False,
        default=AppointmentPriority.NORMAL
    )

    # Dates et heures
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    all_day = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Paris")

    # Localisation
    location = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Video conference
    video_provider = Column(String(50), nullable=True)
    video_link = Column(String(500), nullable=True)
    video_meeting_id = Column(String(100), nullable=True)
    video_password = Column(String(100), nullable=True)

    # Client/Contact principal
    contact_id = Column(UniversalUUID(), nullable=True, index=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    customer_id = Column(UniversalUUID(), nullable=True, index=True)

    # Organisateur/Staff principal
    organizer_id = Column(UniversalUUID(), nullable=True, index=True)
    organizer_name = Column(String(255), nullable=True)
    assigned_to = Column(UniversalUUID(), nullable=True, index=True)

    # Ressource principale
    resource_id = Column(UniversalUUID(), ForeignKey("appointment_resources.id"), nullable=True)

    # Tarification
    is_billable = Column(Boolean, default=False)
    price = Column(Numeric(12, 2), nullable=True)
    deposit_amount = Column(Numeric(12, 2), nullable=True)
    deposit_paid = Column(Boolean, default=False)
    deposit_paid_at = Column(DateTime, nullable=True)
    payment_status = Column(String(50), default="pending")
    invoice_id = Column(UniversalUUID(), nullable=True)
    currency = Column(String(3), default="EUR")

    # Confirmation
    confirmation_code = Column(String(20), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(UniversalUUID(), nullable=True)

    # Check-in
    checked_in_at = Column(DateTime, nullable=True)
    checked_in_by = Column(UniversalUUID(), nullable=True)

    # Completion
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(UniversalUUID(), nullable=True)
    outcome = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    feedback = Column(Text, nullable=True)

    # Annulation
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(UniversalUUID(), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancellation_fee = Column(Numeric(12, 2), nullable=True)

    # Replanification
    rescheduled_from = Column(UniversalUUID(), nullable=True)
    reschedule_count = Column(Integer, default=0)
    last_rescheduled_at = Column(DateTime, nullable=True)

    # Recurrence (inspire Sage CRM)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(
        SQLEnum(RecurrencePattern, name='appointment_recurrence_pattern'),
        default=RecurrencePattern.NONE
    )
    recurrence_interval = Column(Integer, default=1)  # Tous les X jours/semaines
    recurrence_days = Column(JSONB, default=list)     # Jours de la semaine [0-6]
    recurrence_day_of_month = Column(Integer, nullable=True)
    recurrence_end_type = Column(
        SQLEnum(RecurrenceEndType, name='appointment_recurrence_end_type'),
        default=RecurrenceEndType.NEVER
    )
    recurrence_end_date = Column(Date, nullable=True)
    recurrence_end_count = Column(Integer, nullable=True)
    recurrence_exceptions = Column(JSONB, default=list)  # Dates exclues
    parent_appointment_id = Column(UniversalUUID(), nullable=True, index=True)
    occurrence_index = Column(Integer, nullable=True)

    # Synchronisation calendrier externe
    external_calendar_id = Column(String(255), nullable=True)
    external_event_id = Column(String(255), nullable=True)
    sync_provider = Column(
        SQLEnum(SyncProvider, name='appointment_sync_provider'),
        nullable=True
    )
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), nullable=True)

    # Liens CRM
    lead_id = Column(UniversalUUID(), nullable=True)
    opportunity_id = Column(UniversalUUID(), nullable=True)
    project_id = Column(UniversalUUID(), nullable=True)
    ticket_id = Column(UniversalUUID(), nullable=True)

    # Tags et champs personnalises
    tags = Column(JSONB, default=list)
    custom_fields = Column(JSONB, default=dict)

    # Source de creation
    source = Column(String(50), default="manual")  # manual, online, api, import

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UniversalUUID(), nullable=True)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    # Relations
    appointment_type = relationship("AppointmentType", back_populates="appointments")
    resource = relationship("Resource")
    attendees = relationship("Attendee", back_populates="appointment", cascade="all, delete-orphan", lazy="dynamic")
    reminders = relationship("Reminder", back_populates="appointment", cascade="all, delete-orphan", lazy="dynamic")
    recurring_appointments = relationship(
        "Appointment",
        backref="parent_appointment",
        remote_side=[id],
        lazy="dynamic"
    )

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_appointment_code'),
        Index('idx_appointment_tenant', 'tenant_id'),
        Index('idx_appointment_dates', 'tenant_id', 'start_datetime', 'end_datetime'),
        Index('idx_appointment_status', 'tenant_id', 'status'),
        Index('idx_appointment_organizer', 'tenant_id', 'organizer_id'),
        Index('idx_appointment_contact', 'tenant_id', 'contact_id'),
        Index('idx_appointment_customer', 'tenant_id', 'customer_id'),
        Index('idx_appointment_type', 'tenant_id', 'type_id'),
        Index('idx_appointment_resource', 'tenant_id', 'resource_id'),
        Index('idx_appointment_recurring', 'tenant_id', 'parent_appointment_id'),
        Index('idx_appointment_deleted', 'tenant_id', 'is_deleted'),
        Index('idx_appointment_confirmation', 'confirmation_code'),
    )


# ============================================================================
# PARTICIPANTS
# ============================================================================

class Attendee(Base):
    """
    Participant a un rendez-vous (inspire Odoo/Outlook).

    Permet de gerer:
    - Participants obligatoires/optionnels
    - Ressources reservees
    - Statuts de reponse (RSVP)
    """
    __tablename__ = "appointment_attendees"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    appointment_id = Column(
        UniversalUUID(),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identification du participant
    user_id = Column(UniversalUUID(), nullable=True)
    contact_id = Column(UniversalUUID(), nullable=True)
    resource_id = Column(UniversalUUID(), ForeignKey("appointment_resources.id"), nullable=True)

    # Informations directes (si pas de user/contact)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Role et statut
    role = Column(
        SQLEnum(AttendeeRole, name='attendee_role'),
        nullable=False,
        default=AttendeeRole.REQUIRED
    )
    status = Column(
        SQLEnum(AttendeeStatus, name='attendee_status'),
        nullable=False,
        default=AttendeeStatus.PENDING
    )

    # Reponse
    responded_at = Column(DateTime, nullable=True)
    response_comment = Column(Text, nullable=True)

    # Delegation
    delegated_to_id = Column(UniversalUUID(), nullable=True)
    delegated_to_name = Column(String(255), nullable=True)

    # Notifications
    invitation_sent_at = Column(DateTime, nullable=True)
    last_notification_at = Column(DateTime, nullable=True)
    notification_count = Column(Integer, default=0)

    # Check-in
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    appointment = relationship("Appointment", back_populates="attendees")
    resource = relationship("Resource")

    __table_args__ = (
        Index('idx_attendee_tenant', 'tenant_id'),
        Index('idx_attendee_appointment', 'appointment_id'),
        Index('idx_attendee_user', 'tenant_id', 'user_id'),
        Index('idx_attendee_contact', 'tenant_id', 'contact_id'),
        Index('idx_attendee_status', 'appointment_id', 'status'),
    )


# ============================================================================
# RAPPELS
# ============================================================================

class Reminder(Base):
    """
    Rappel pour un rendez-vous (inspire Axonaut).

    Supporte:
    - Email, SMS, Push, WhatsApp
    - Rappels multiples (24h, 1h avant)
    - Templates personnalises
    """
    __tablename__ = "appointment_reminders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    appointment_id = Column(
        UniversalUUID(),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Type et timing
    reminder_type = Column(
        SQLEnum(ReminderType, name='reminder_type'),
        nullable=False,
        default=ReminderType.EMAIL
    )
    minutes_before = Column(Integer, nullable=False, default=1440)  # 24h par defaut
    scheduled_at = Column(DateTime, nullable=False, index=True)

    # Destinataire
    recipient_type = Column(String(50), nullable=False, default="attendee")  # attendee, organizer, custom
    recipient_user_id = Column(UniversalUUID(), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(50), nullable=True)

    # Template
    template_id = Column(UniversalUUID(), nullable=True)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)

    # Statut
    status = Column(
        SQLEnum(ReminderStatus, name='reminder_status'),
        nullable=False,
        default=ReminderStatus.PENDING
    )
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    appointment = relationship("Appointment", back_populates="reminders")

    __table_args__ = (
        Index('idx_reminder_tenant', 'tenant_id'),
        Index('idx_reminder_appointment', 'appointment_id'),
        Index('idx_reminder_scheduled', 'tenant_id', 'scheduled_at', 'status'),
        Index('idx_reminder_status', 'status'),
    )


# ============================================================================
# DISPONIBILITES
# ============================================================================

class Availability(Base):
    """
    Disponibilite/Exception de calendrier.

    Permet de definir:
    - Horaires de travail
    - Conges et absences
    - Plages bloquees
    """
    __tablename__ = "appointment_availabilities"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Proprietaire (staff ou ressource)
    user_id = Column(UniversalUUID(), nullable=True, index=True)
    resource_id = Column(UniversalUUID(), ForeignKey("appointment_resources.id"), nullable=True)

    # Type
    availability_type = Column(
        SQLEnum(AvailabilityType, name='availability_type'),
        nullable=False,
        default=AvailabilityType.AVAILABLE
    )

    # Dates
    date_start = Column(Date, nullable=False, index=True)
    date_end = Column(Date, nullable=True)  # NULL = meme jour
    time_start = Column(Time, nullable=True)  # NULL = journee entiere
    time_end = Column(Time, nullable=True)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(
        SQLEnum(RecurrencePattern, name='availability_recurrence_pattern'),
        nullable=True
    )
    recurrence_days = Column(JSONB, default=list)  # Jours de la semaine
    recurrence_end_date = Column(Date, nullable=True)

    # Informations
    title = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_availability_tenant', 'tenant_id'),
        Index('idx_availability_user', 'tenant_id', 'user_id'),
        Index('idx_availability_resource', 'tenant_id', 'resource_id'),
        Index('idx_availability_dates', 'tenant_id', 'date_start', 'date_end'),
        Index('idx_availability_type', 'tenant_id', 'availability_type'),
    )


# ============================================================================
# HORAIRES DE TRAVAIL
# ============================================================================

class WorkingHours(Base):
    """
    Horaires de travail hebdomadaires.

    Definit les horaires standards par jour de semaine.
    """
    __tablename__ = "appointment_working_hours"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Proprietaire
    user_id = Column(UniversalUUID(), nullable=True, index=True)
    resource_id = Column(UniversalUUID(), ForeignKey("appointment_resources.id"), nullable=True)

    # Jour de la semaine (0=Lundi, 6=Dimanche)
    day_of_week = Column(Integer, nullable=False)

    # Horaires
    is_working = Column(Boolean, default=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Pauses
    breaks = Column(JSONB, default=list)  # [{start: "12:00", end: "13:00"}]

    # Validite
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_working_hours_tenant', 'tenant_id'),
        Index('idx_working_hours_user', 'tenant_id', 'user_id', 'day_of_week'),
        Index('idx_working_hours_resource', 'tenant_id', 'resource_id', 'day_of_week'),
    )


# ============================================================================
# LISTE D'ATTENTE
# ============================================================================

class WaitlistEntry(Base):
    """
    Entree dans la liste d'attente (inspire Odoo).
    """
    __tablename__ = "appointment_waitlist"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Type de rendez-vous souhaite
    type_id = Column(UniversalUUID(), ForeignKey("appointment_types.id"), nullable=True)
    resource_id = Column(UniversalUUID(), ForeignKey("appointment_resources.id"), nullable=True)
    staff_user_id = Column(UniversalUUID(), nullable=True)

    # Demandeur
    contact_id = Column(UniversalUUID(), nullable=True)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Preferences
    preferred_dates = Column(JSONB, default=list)
    preferred_times = Column(JSONB, default=list)  # ["morning", "afternoon", "evening"]
    preferred_modes = Column(JSONB, default=list)
    notes = Column(Text, nullable=True)

    # Statut
    status = Column(String(50), default="waiting")  # waiting, notified, booked, expired, cancelled
    priority = Column(Integer, default=0)

    # Notification
    notified_at = Column(DateTime, nullable=True)
    notification_count = Column(Integer, default=0)
    last_notification_at = Column(DateTime, nullable=True)

    # Conversion
    converted_appointment_id = Column(UniversalUUID(), nullable=True)
    converted_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_waitlist_tenant', 'tenant_id'),
        Index('idx_waitlist_status', 'tenant_id', 'status'),
        Index('idx_waitlist_type', 'tenant_id', 'type_id'),
        Index('idx_waitlist_contact', 'tenant_id', 'contact_id'),
    )


# ============================================================================
# SYNCHRONISATION CALENDRIER
# ============================================================================

class CalendarSync(Base):
    """
    Configuration de synchronisation avec calendrier externe.
    """
    __tablename__ = "appointment_calendar_syncs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UniversalUUID(), nullable=False, index=True)

    # Provider
    provider = Column(
        SQLEnum(SyncProvider, name='calendar_sync_provider'),
        nullable=False
    )
    calendar_id = Column(String(255), nullable=False)
    calendar_name = Column(String(255), nullable=True)

    # Authentication
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime, nullable=True)

    # Sync settings
    sync_direction = Column(String(20), default="both")  # both, import, export
    sync_interval_minutes = Column(Integer, default=15)
    sync_past_days = Column(Integer, default=7)
    sync_future_days = Column(Integer, default=90)

    # Status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)

    # Stats
    events_imported = Column(Integer, default=0)
    events_exported = Column(Integer, default=0)
    sync_count = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'provider', 'calendar_id', name='uq_calendar_sync'),
        Index('idx_calendar_sync_tenant', 'tenant_id'),
        Index('idx_calendar_sync_user', 'tenant_id', 'user_id'),
        Index('idx_calendar_sync_next', 'is_active', 'next_sync_at'),
    )


# ============================================================================
# PARAMETRES DE RESERVATION
# ============================================================================

class BookingSettings(Base):
    """
    Parametres globaux de reservation pour le tenant.
    """
    __tablename__ = "appointment_booking_settings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, unique=True, index=True)

    # Reservations en ligne
    allow_online_booking = Column(Boolean, default=True)
    require_account = Column(Boolean, default=False)
    booking_page_url = Column(String(500), nullable=True)
    booking_page_logo_url = Column(String(500), nullable=True)
    booking_page_theme = Column(JSONB, default=dict)

    # Creneaux
    slot_interval_minutes = Column(Integer, default=15)
    booking_window_days = Column(Integer, default=60)
    min_notice_hours = Column(Integer, default=2)
    max_bookings_per_day = Column(Integer, nullable=True)
    max_bookings_per_customer_day = Column(Integer, default=3)

    # Selection staff
    show_staff_selection = Column(Boolean, default=True)
    allow_any_staff = Column(Boolean, default=True)

    # Conflits
    conflict_resolution = Column(
        SQLEnum(ConflictResolution, name='booking_conflict_resolution'),
        default=ConflictResolution.BLOCK
    )
    allow_overbooking = Column(Boolean, default=False)
    max_overbooking_percent = Column(Integer, default=0)

    # Messages
    confirmation_message = Column(Text, nullable=True)
    cancellation_policy = Column(Text, nullable=True)
    reminder_template_id = Column(UniversalUUID(), nullable=True)

    # Rappels par defaut
    default_reminders = Column(JSONB, default=lambda: [
        {"type": "EMAIL", "minutes_before": 1440},
        {"type": "EMAIL", "minutes_before": 60}
    ])

    # Timezone
    timezone = Column(String(50), default="Europe/Paris")
    date_format = Column(String(20), default="DD/MM/YYYY")
    time_format = Column(String(10), default="HH:mm")

    # Paiement
    require_payment = Column(Boolean, default=False)
    payment_provider = Column(String(50), nullable=True)  # stripe, paypal
    deposit_percentage = Column(Numeric(5, 2), nullable=True)

    # Notifications
    notify_on_booking = Column(Boolean, default=True)
    notify_on_cancellation = Column(Boolean, default=True)
    notify_on_reschedule = Column(Boolean, default=True)
    notification_emails = Column(JSONB, default=list)

    # Audit
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        Index('idx_booking_settings_tenant', 'tenant_id'),
    )
