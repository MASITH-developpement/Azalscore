"""
Modèles SQLAlchemy Resources / Réservation de ressources
========================================================
- Multi-tenant obligatoire
- Soft delete
- Audit complet
- Versioning
"""
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date, Time,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum
)
from app.core.types import UniversalUUID as UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
import uuid

from app.core.database import Base


# ============== Enums ==============

class ResourceType(str, Enum):
    """Type de ressource"""
    MEETING_ROOM = "meeting_room"
    CONFERENCE_ROOM = "conference_room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    WORKSPACE = "workspace"
    PARKING = "parking"
    LAB = "lab"
    STUDIO = "studio"
    OTHER = "other"


class ResourceStatus(str, Enum):
    """Statut d'une ressource"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    RESERVED = "reserved"


class BookingStatus(str, Enum):
    """Statut d'une réservation"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    REJECTED = "rejected"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.CONFIRMED, cls.REJECTED, cls.CANCELLED],
            cls.CONFIRMED: [cls.CHECKED_IN, cls.CANCELLED, cls.NO_SHOW],
            cls.CHECKED_IN: [cls.COMPLETED],
            cls.COMPLETED: [],
            cls.CANCELLED: [],
            cls.NO_SHOW: [],
            cls.REJECTED: [],
        }


class RecurrenceType(str, Enum):
    """Type de récurrence"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    """Statut d'approbation"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WaitlistStatus(str, Enum):
    """Statut liste d'attente"""
    WAITING = "waiting"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ============== Models ==============

class ResourceLocation(Base):
    """Localisation d'une ressource"""
    __tablename__ = "resource_locations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)

    building = Column(String(100), default="")
    floor = Column(String(50), default="")
    zone = Column(String(100), default="")
    address = Column(Text, default="")

    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    capacity = Column(Integer, nullable=True)
    timezone = Column(String(50), default="Europe/Paris")

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    resources = relationship("Resource", back_populates="location", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_location_tenant_code"),
        Index("ix_location_tenant_active", "tenant_id", "is_active"),
        {"extend_existing": True},
    )


class Amenity(Base):
    """Équipement/caractéristique disponible"""
    __tablename__ = "resource_amenities"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    icon = Column(String(100), default="")
    description = Column(Text, default="")

    category = Column(String(50), default="")
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_amenity_tenant_code"),
        Index("ix_amenity_tenant_active", "tenant_id", "is_active"),
    )


class Resource(Base):
    """Ressource réservable"""
    __tablename__ = "resources"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, default="")

    resource_type = Column(SQLEnum(ResourceType), default=ResourceType.MEETING_ROOM, nullable=False)
    status = Column(SQLEnum(ResourceStatus), default=ResourceStatus.AVAILABLE, nullable=False)

    # Localisation
    location_id = Column(UUID(), ForeignKey("resource_locations.id"), nullable=True)
    location_details = Column(String(200), default="")

    # Capacité
    capacity = Column(Integer, nullable=True)
    min_capacity = Column(Integer, default=1)

    # Équipements (array of amenity IDs)
    amenity_ids = Column(ARRAY(UUID()), default=list)
    equipment = Column(ARRAY(String), default=list)

    # Tarification
    hourly_rate = Column(Numeric(15, 2), default=Decimal("0"))
    half_day_rate = Column(Numeric(15, 2), default=Decimal("0"))
    daily_rate = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR")

    # Règles de réservation
    min_duration_minutes = Column(Integer, default=30)
    max_duration_minutes = Column(Integer, default=480)
    min_advance_hours = Column(Integer, default=1)
    max_advance_days = Column(Integer, default=90)
    buffer_minutes = Column(Integer, default=0)

    # Disponibilité
    available_days = Column(ARRAY(Integer), default=[0, 1, 2, 3, 4])
    available_start_time = Column(Time, default=time(8, 0))
    available_end_time = Column(Time, default=time(20, 0))

    # Approbation
    requires_approval = Column(Boolean, default=False)
    approver_ids = Column(ARRAY(UUID()), default=list)

    # Restrictions
    allowed_user_ids = Column(ARRAY(UUID()), default=list)
    allowed_department_ids = Column(ARRAY(UUID()), default=list)
    priority_user_ids = Column(ARRAY(UUID()), default=list)

    # Images
    images = Column(ARRAY(String), default=list)
    thumbnail = Column(String(500), default="")

    # Métadonnées
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    location = relationship("ResourceLocation", back_populates="resources")
    bookings = relationship("Booking", back_populates="resource", lazy="dynamic")
    blocked_slots = relationship("BlockedSlot", back_populates="resource", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_resource_tenant_code"),
        Index("ix_resource_tenant_type", "tenant_id", "resource_type"),
        Index("ix_resource_tenant_status", "tenant_id", "status"),
        Index("ix_resource_location", "location_id"),
        {"extend_existing": True},
    )


class Booking(Base):
    """Réservation de ressource"""
    __tablename__ = "resource_bookings"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    resource_id = Column(UUID(), ForeignKey("resources.id"), nullable=False)
    user_id = Column(UUID(), nullable=False)

    # Période
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="Europe/Paris")

    # Récurrence
    recurrence_type = Column(SQLEnum(RecurrenceType), default=RecurrenceType.NONE)
    recurrence_rule = Column(JSONB, nullable=True)
    parent_booking_id = Column(UUID(), ForeignKey("resource_bookings.id"), nullable=True)
    is_recurring = Column(Boolean, default=False)

    # Statut
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.NOT_REQUIRED)

    # Détails
    title = Column(String(300), default="")
    description = Column(Text, default="")
    purpose = Column(String(200), default="")

    # Participants
    attendee_ids = Column(ARRAY(UUID()), default=list)
    attendee_count = Column(Integer, default=1)
    external_attendees = Column(ARRAY(String), default=list)

    # Équipements demandés
    requested_amenity_ids = Column(ARRAY(UUID()), default=list)
    special_requests = Column(Text, default="")

    # Tarification
    total_cost = Column(Numeric(15, 2), default=Decimal("0"))
    is_paid = Column(Boolean, default=False)
    payment_id = Column(UUID(), nullable=True)

    # Check-in/out
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    checked_in_by = Column(UUID(), nullable=True)

    # Approbation
    approved_by = Column(UUID(), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, default="")

    # Annulation
    cancelled_by = Column(UUID(), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, default="")

    # Notification
    reminder_sent = Column(Boolean, default=False)
    confirmation_sent = Column(Boolean, default=False)

    # Source
    source = Column(String(50), default="web")
    external_reference = Column(String(200), default="")
    extra_data = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    resource = relationship("Resource", back_populates="bookings")
    parent_booking = relationship("Booking", remote_side=[id], backref="child_bookings")

    __table_args__ = (
        Index("ix_booking_tenant_status", "tenant_id", "status"),
        Index("ix_booking_resource", "resource_id"),
        Index("ix_booking_user", "user_id"),
        Index("ix_booking_dates", "tenant_id", "start_datetime", "end_datetime"),
        Index("ix_booking_parent", "parent_booking_id"),
        CheckConstraint("end_datetime > start_datetime", name="ck_booking_dates"),
    )


class BlockedSlot(Base):
    """Créneau bloqué (maintenance, événement spécial)"""
    __tablename__ = "resource_blocked_slots"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    resource_id = Column(UUID(), ForeignKey("resources.id"), nullable=False)

    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)

    reason = Column(Text, default="")
    blocked_by = Column(UUID(), nullable=True)

    # Récurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Relationships
    resource = relationship("Resource", back_populates="blocked_slots")

    __table_args__ = (
        Index("ix_blocked_slot_resource", "resource_id"),
        Index("ix_blocked_slot_dates", "tenant_id", "start_datetime", "end_datetime"),
        CheckConstraint("end_datetime > start_datetime", name="ck_blocked_slot_dates"),
    )


class WaitlistEntry(Base):
    """Entrée en liste d'attente"""
    __tablename__ = "resource_waitlist"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    resource_id = Column(UUID(), ForeignKey("resources.id"), nullable=False)
    user_id = Column(UUID(), nullable=False)

    # Période souhaitée
    desired_start = Column(DateTime, nullable=False)
    desired_end = Column(DateTime, nullable=False)

    # Flexibilité
    flexible_time = Column(Boolean, default=False)
    flexible_date = Column(Boolean, default=False)
    alternative_resource_ids = Column(ARRAY(UUID()), default=list)

    # Priorité
    priority = Column(Integer, default=0)
    is_notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    status = Column(SQLEnum(WaitlistStatus), default=WaitlistStatus.WAITING)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    __table_args__ = (
        Index("ix_waitlist_resource", "resource_id"),
        Index("ix_waitlist_user", "user_id"),
        Index("ix_waitlist_status", "tenant_id", "status"),
    )
