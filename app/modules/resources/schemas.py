"""
Schémas Pydantic Resources / Réservation
========================================
"""
from __future__ import annotations

from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============== Location Schemas ==============

class LocationCreate(BaseModel):
    """Création localisation"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    building: str = ""
    floor: str = ""
    zone: str = ""
    address: str = ""
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    capacity: Optional[int] = None
    timezone: str = "Europe/Paris"
    is_active: bool = True


class LocationUpdate(BaseModel):
    """Mise à jour localisation"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    building: Optional[str] = None
    floor: Optional[str] = None
    zone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    capacity: Optional[int] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(BaseModel):
    """Réponse localisation"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    building: str
    floor: str
    zone: str
    address: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    capacity: Optional[int]
    timezone: str
    is_active: bool
    created_at: datetime
    version: int


class LocationListResponse(BaseModel):
    """Liste paginée localisations"""
    items: List[LocationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Amenity Schemas ==============

class AmenityCreate(BaseModel):
    """Création équipement"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    icon: str = ""
    description: str = ""
    category: str = ""
    is_active: bool = True


class AmenityUpdate(BaseModel):
    """Mise à jour équipement"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    icon: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class AmenityResponse(BaseModel):
    """Réponse équipement"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    icon: str
    description: str
    category: str
    is_active: bool
    created_at: datetime


class AmenityListResponse(BaseModel):
    """Liste paginée équipements"""
    items: List[AmenityResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Resource Schemas ==============

class ResourceCreate(BaseModel):
    """Création ressource"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    resource_type: str = "meeting_room"
    location_id: Optional[UUID] = None
    location_details: str = ""
    capacity: Optional[int] = None
    min_capacity: int = 1
    amenity_ids: List[UUID] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    hourly_rate: Decimal = Decimal("0")
    half_day_rate: Decimal = Decimal("0")
    daily_rate: Decimal = Decimal("0")
    currency: str = "EUR"
    min_duration_minutes: int = 30
    max_duration_minutes: int = 480
    min_advance_hours: int = 1
    max_advance_days: int = 90
    buffer_minutes: int = 0
    available_days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    available_start_time: time = time(8, 0)
    available_end_time: time = time(20, 0)
    requires_approval: bool = False
    approver_ids: List[UUID] = Field(default_factory=list)
    allowed_user_ids: List[UUID] = Field(default_factory=list)
    allowed_department_ids: List[UUID] = Field(default_factory=list)
    priority_user_ids: List[UUID] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    thumbnail: str = ""
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class ResourceUpdate(BaseModel):
    """Mise à jour ressource"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None
    location_id: Optional[UUID] = None
    location_details: Optional[str] = None
    capacity: Optional[int] = None
    min_capacity: Optional[int] = None
    amenity_ids: Optional[List[UUID]] = None
    equipment: Optional[List[str]] = None
    hourly_rate: Optional[Decimal] = None
    half_day_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    currency: Optional[str] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    min_advance_hours: Optional[int] = None
    max_advance_days: Optional[int] = None
    buffer_minutes: Optional[int] = None
    available_days: Optional[List[int]] = None
    available_start_time: Optional[time] = None
    available_end_time: Optional[time] = None
    requires_approval: Optional[bool] = None
    approver_ids: Optional[List[UUID]] = None
    allowed_user_ids: Optional[List[UUID]] = None
    allowed_department_ids: Optional[List[UUID]] = None
    priority_user_ids: Optional[List[UUID]] = None
    images: Optional[List[str]] = None
    thumbnail: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
    """Réponse ressource"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: str
    resource_type: str
    status: str
    location_id: Optional[UUID]
    location_details: str
    capacity: Optional[int]
    min_capacity: int
    amenity_ids: List[UUID]
    equipment: List[str]
    hourly_rate: Decimal
    half_day_rate: Decimal
    daily_rate: Decimal
    currency: str
    min_duration_minutes: int
    max_duration_minutes: int
    min_advance_hours: int
    max_advance_days: int
    buffer_minutes: int
    available_days: List[int]
    available_start_time: time
    available_end_time: time
    requires_approval: bool
    approver_ids: List[UUID]
    images: List[str]
    thumbnail: str
    tags: List[str]
    is_active: bool
    created_at: datetime
    version: int


class ResourceListResponse(BaseModel):
    """Liste paginée ressources"""
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ResourceFilters(BaseModel):
    """Filtres pour liste ressources"""
    resource_type: Optional[str] = None
    status: Optional[str] = None
    location_id: Optional[UUID] = None
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    amenity_ids: Optional[List[UUID]] = None
    available_on: Optional[date] = None
    available_from: Optional[time] = None
    available_to: Optional[time] = None


# ============== Booking Schemas ==============

class RecurrenceRule(BaseModel):
    """Règle de récurrence"""
    type: str = "none"
    interval: int = 1
    days_of_week: List[int] = Field(default_factory=list)
    day_of_month: Optional[int] = None
    end_date: Optional[date] = None
    occurrences: Optional[int] = None


class BookingCreate(BaseModel):
    """Création réservation"""
    resource_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = "Europe/Paris"
    recurrence_rule: Optional[RecurrenceRule] = None
    title: str = ""
    description: str = ""
    purpose: str = ""
    attendee_ids: List[UUID] = Field(default_factory=list)
    attendee_count: int = 1
    external_attendees: List[str] = Field(default_factory=list)
    requested_amenity_ids: List[UUID] = Field(default_factory=list)
    special_requests: str = ""


class BookingUpdate(BaseModel):
    """Mise à jour réservation"""
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    timezone: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    attendee_ids: Optional[List[UUID]] = None
    attendee_count: Optional[int] = None
    external_attendees: Optional[List[str]] = None
    requested_amenity_ids: Optional[List[UUID]] = None
    special_requests: Optional[str] = None


class BookingResponse(BaseModel):
    """Réponse réservation"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    resource_id: UUID
    user_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    timezone: str
    recurrence_type: str
    is_recurring: bool
    parent_booking_id: Optional[UUID]
    status: str
    approval_status: str
    title: str
    description: str
    purpose: str
    attendee_ids: List[UUID]
    attendee_count: int
    external_attendees: List[str]
    requested_amenity_ids: List[UUID]
    special_requests: str
    total_cost: Decimal
    is_paid: bool
    checked_in_at: Optional[datetime]
    checked_out_at: Optional[datetime]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: str
    cancelled_by: Optional[UUID]
    cancelled_at: Optional[datetime]
    cancellation_reason: str
    created_at: datetime
    version: int


class BookingListResponse(BaseModel):
    """Liste paginée réservations"""
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BookingFilters(BaseModel):
    """Filtres pour liste réservations"""
    resource_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    approval_status: Optional[str] = None


# ============== BlockedSlot Schemas ==============

class BlockedSlotCreate(BaseModel):
    """Création créneau bloqué"""
    resource_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    reason: str = ""
    is_recurring: bool = False
    recurrence_rule: Optional[RecurrenceRule] = None


class BlockedSlotUpdate(BaseModel):
    """Mise à jour créneau bloqué"""
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None


class BlockedSlotResponse(BaseModel):
    """Réponse créneau bloqué"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    resource_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    reason: str
    blocked_by: Optional[UUID]
    is_recurring: bool
    is_active: bool
    created_at: datetime


class BlockedSlotListResponse(BaseModel):
    """Liste paginée créneaux bloqués"""
    items: List[BlockedSlotResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Waitlist Schemas ==============

class WaitlistCreate(BaseModel):
    """Création entrée liste d'attente"""
    resource_id: UUID
    desired_start: datetime
    desired_end: datetime
    flexible_time: bool = False
    flexible_date: bool = False
    alternative_resource_ids: List[UUID] = Field(default_factory=list)
    priority: int = 0
    expires_at: Optional[datetime] = None


class WaitlistResponse(BaseModel):
    """Réponse entrée liste d'attente"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    resource_id: UUID
    user_id: UUID
    desired_start: datetime
    desired_end: datetime
    flexible_time: bool
    flexible_date: bool
    alternative_resource_ids: List[UUID]
    priority: int
    is_notified: bool
    notified_at: Optional[datetime]
    expires_at: Optional[datetime]
    status: str
    created_at: datetime


class WaitlistListResponse(BaseModel):
    """Liste paginée liste d'attente"""
    items: List[WaitlistResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============== Availability Schemas ==============

class AvailabilitySlot(BaseModel):
    """Créneau de disponibilité"""
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool = True
    conflict_booking_id: Optional[UUID] = None
    conflict_reason: str = ""


class AvailabilityRequest(BaseModel):
    """Demande de disponibilité"""
    resource_id: UUID
    date_from: date
    date_to: date
    time_from: Optional[time] = None
    time_to: Optional[time] = None


class AvailabilityResponse(BaseModel):
    """Réponse disponibilité"""
    resource_id: UUID
    date_from: date
    date_to: date
    slots: List[AvailabilitySlot]


# ============== Utilization Schemas ==============

class ResourceUtilization(BaseModel):
    """Statistiques d'utilisation"""
    resource_id: UUID
    period_start: date
    period_end: date
    total_available_hours: Decimal = Decimal("0")
    total_booked_hours: Decimal = Decimal("0")
    total_used_hours: Decimal = Decimal("0")
    booking_rate: Decimal = Decimal("0")
    utilization_rate: Decimal = Decimal("0")
    no_show_rate: Decimal = Decimal("0")
    total_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    no_show_bookings: int = 0
    total_revenue: Decimal = Decimal("0")


# ============== Common Schemas ==============

class AutocompleteResponse(BaseModel):
    """Réponse autocomplete"""
    items: List[Dict[str, Any]]


class BulkResult(BaseModel):
    """Résultat opération en masse"""
    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
