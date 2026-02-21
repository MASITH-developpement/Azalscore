"""
Service Resources / Réservation
===============================
Logique métier avec tenant isolation.
"""
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    ResourceLocation, Amenity, Resource, ResourceType, ResourceStatus,
    Booking, BookingStatus, ApprovalStatus, RecurrenceType,
    BlockedSlot, WaitlistEntry, WaitlistStatus
)

# Alias pour compatibilité
Location = ResourceLocation
from .repository import (
    LocationRepository, AmenityRepository, ResourceRepository,
    BookingRepository, BlockedSlotRepository, WaitlistRepository
)
from .schemas import (
    LocationCreate, LocationUpdate,
    AmenityCreate, AmenityUpdate,
    ResourceCreate, ResourceUpdate,
    BookingCreate, BookingUpdate,
    BlockedSlotCreate, BlockedSlotUpdate,
    WaitlistCreate, AvailabilitySlot
)
from .exceptions import (
    LocationNotFoundError, LocationDuplicateError,
    AmenityNotFoundError, AmenityDuplicateError,
    ResourceNotFoundError, ResourceDuplicateError, ResourceUnavailableError,
    BookingNotFoundError, BookingValidationError, BookingStateError,
    BookingConflictError, BookingDurationError, BookingAdvanceError,
    BookingAlreadyCheckedInError, BookingNotCheckedInError,
    BlockedSlotNotFoundError,
    WaitlistEntryNotFoundError
)


class ResourceService:
    """Service de gestion des ressources et réservations."""

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

        self.location_repo = LocationRepository(db, tenant_id)
        self.amenity_repo = AmenityRepository(db, tenant_id)
        self.resource_repo = ResourceRepository(db, tenant_id)
        self.booking_repo = BookingRepository(db, tenant_id)
        self.blocked_repo = BlockedSlotRepository(db, tenant_id)
        self.waitlist_repo = WaitlistRepository(db, tenant_id)

    # ============== Location ==============

    def get_location(self, location_id: UUID) -> Location:
        location = self.location_repo.get_by_id(location_id)
        if not location:
            raise LocationNotFoundError(f"Location {location_id} not found")
        return location

    def list_locations(
        self, page: int = 1, page_size: int = 20,
        search: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Tuple[List[Location], int, int]:
        return self.location_repo.list_all(page, page_size, search, is_active)

    def create_location(self, data: LocationCreate) -> Location:
        if self.location_repo.get_by_code(data.code):
            raise LocationDuplicateError(f"Location code {data.code} already exists")

        location = Location(
            **data.model_dump(),
            created_by=self.user_id
        )
        return self.location_repo.create(location)

    def update_location(self, location_id: UUID, data: LocationUpdate) -> Location:
        location = self.get_location(location_id)

        if data.code and data.code != location.code:
            if self.location_repo.get_by_code(data.code):
                raise LocationDuplicateError(f"Location code {data.code} already exists")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(location, field, value)

        location.updated_by = self.user_id
        return self.location_repo.update(location)

    def delete_location(self, location_id: UUID) -> bool:
        self.get_location(location_id)
        return self.location_repo.soft_delete(location_id, self.user_id)

    def restore_location(self, location_id: UUID) -> Location:
        location = self.location_repo.restore(location_id)
        if not location:
            raise LocationNotFoundError(f"Location {location_id} not found")
        return location

    def autocomplete_location(self, search: str) -> List[dict]:
        return self.location_repo.autocomplete(search)

    # ============== Amenity ==============

    def get_amenity(self, amenity_id: UUID) -> Amenity:
        amenity = self.amenity_repo.get_by_id(amenity_id)
        if not amenity:
            raise AmenityNotFoundError(f"Amenity {amenity_id} not found")
        return amenity

    def list_amenities(
        self, page: int = 1, page_size: int = 20,
        search: Optional[str] = None, category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Amenity], int, int]:
        return self.amenity_repo.list_all(page, page_size, search, category, is_active)

    def create_amenity(self, data: AmenityCreate) -> Amenity:
        if self.amenity_repo.get_by_code(data.code):
            raise AmenityDuplicateError(f"Amenity code {data.code} already exists")

        amenity = Amenity(**data.model_dump(), created_by=self.user_id)
        return self.amenity_repo.create(amenity)

    def delete_amenity(self, amenity_id: UUID) -> bool:
        self.get_amenity(amenity_id)
        return self.amenity_repo.soft_delete(amenity_id, self.user_id)

    # ============== Resource ==============

    def get_resource(self, resource_id: UUID) -> Resource:
        resource = self.resource_repo.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")
        return resource

    def list_resources(
        self, page: int = 1, page_size: int = 20,
        search: Optional[str] = None, resource_type: Optional[str] = None,
        status: Optional[str] = None, location_id: Optional[UUID] = None,
        min_capacity: Optional[int] = None, max_capacity: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Resource], int, int]:
        type_enum = ResourceType(resource_type) if resource_type else None
        status_enum = ResourceStatus(status) if status else None
        return self.resource_repo.list_all(
            page, page_size, search, type_enum, status_enum,
            location_id, min_capacity, max_capacity, is_active
        )

    def create_resource(self, data: ResourceCreate) -> Resource:
        if self.resource_repo.get_by_code(data.code):
            raise ResourceDuplicateError(f"Resource code {data.code} already exists")

        if data.location_id:
            self.get_location(data.location_id)

        resource = Resource(
            name=data.name,
            code=data.code,
            description=data.description,
            resource_type=ResourceType(data.resource_type),
            location_id=data.location_id,
            location_details=data.location_details,
            capacity=data.capacity,
            min_capacity=data.min_capacity,
            amenity_ids=data.amenity_ids,
            equipment=data.equipment,
            hourly_rate=data.hourly_rate,
            half_day_rate=data.half_day_rate,
            daily_rate=data.daily_rate,
            currency=data.currency,
            min_duration_minutes=data.min_duration_minutes,
            max_duration_minutes=data.max_duration_minutes,
            min_advance_hours=data.min_advance_hours,
            max_advance_days=data.max_advance_days,
            buffer_minutes=data.buffer_minutes,
            available_days=data.available_days,
            available_start_time=data.available_start_time,
            available_end_time=data.available_end_time,
            requires_approval=data.requires_approval,
            approver_ids=data.approver_ids,
            allowed_user_ids=data.allowed_user_ids,
            allowed_department_ids=data.allowed_department_ids,
            priority_user_ids=data.priority_user_ids,
            images=data.images,
            thumbnail=data.thumbnail,
            tags=data.tags,
            is_active=data.is_active,
            created_by=self.user_id
        )
        return self.resource_repo.create(resource)

    def update_resource(self, resource_id: UUID, data: ResourceUpdate) -> Resource:
        resource = self.get_resource(resource_id)

        if data.code and data.code != resource.code:
            if self.resource_repo.get_by_code(data.code):
                raise ResourceDuplicateError(f"Resource code {data.code} already exists")

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "resource_type" and value:
                setattr(resource, field, ResourceType(value))
            elif field == "status" and value:
                setattr(resource, field, ResourceStatus(value))
            else:
                setattr(resource, field, value)

        resource.updated_by = self.user_id
        return self.resource_repo.update(resource)

    def delete_resource(self, resource_id: UUID) -> bool:
        self.get_resource(resource_id)
        return self.resource_repo.soft_delete(resource_id, self.user_id)

    def restore_resource(self, resource_id: UUID) -> Resource:
        resource = self.resource_repo.restore(resource_id)
        if not resource:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")
        return resource

    def autocomplete_resource(self, search: str) -> List[dict]:
        return self.resource_repo.autocomplete(search)

    def set_resource_status(self, resource_id: UUID, status: str) -> Resource:
        resource = self.get_resource(resource_id)
        resource.status = ResourceStatus(status)
        resource.updated_by = self.user_id
        return self.resource_repo.update(resource)

    # ============== Booking ==============

    def get_booking(self, booking_id: UUID) -> Booking:
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking {booking_id} not found")
        return booking

    def list_bookings(
        self, page: int = 1, page_size: int = 20,
        resource_id: Optional[UUID] = None, user_id: Optional[UUID] = None,
        status: Optional[str] = None, date_from: Optional[date] = None,
        date_to: Optional[date] = None, approval_status: Optional[str] = None
    ) -> Tuple[List[Booking], int, int]:
        status_enum = BookingStatus(status) if status else None
        approval_enum = ApprovalStatus(approval_status) if approval_status else None
        return self.booking_repo.list_all(
            page, page_size, resource_id, user_id, status_enum,
            date_from, date_to, approval_enum
        )

    def create_booking(self, data: BookingCreate) -> Booking:
        resource = self.get_resource(data.resource_id)

        # Validation
        if resource.status != ResourceStatus.AVAILABLE:
            raise ResourceUnavailableError(f"Resource {resource.name} is not available")

        self._validate_booking_rules(resource, data.start_datetime, data.end_datetime)
        self._check_conflicts(resource.id, data.start_datetime, data.end_datetime)

        # Calculate cost
        duration_hours = (data.end_datetime - data.start_datetime).total_seconds() / 3600
        total_cost = resource.hourly_rate * Decimal(str(duration_hours))

        booking = Booking(
            resource_id=data.resource_id,
            user_id=self.user_id,
            start_datetime=data.start_datetime,
            end_datetime=data.end_datetime,
            timezone=data.timezone,
            title=data.title,
            description=data.description,
            purpose=data.purpose,
            attendee_ids=data.attendee_ids,
            attendee_count=data.attendee_count,
            external_attendees=data.external_attendees,
            requested_amenity_ids=data.requested_amenity_ids,
            special_requests=data.special_requests,
            total_cost=total_cost,
            status=BookingStatus.PENDING,
            approval_status=ApprovalStatus.PENDING if resource.requires_approval else ApprovalStatus.NOT_REQUIRED,
            created_by=self.user_id
        )

        booking = self.booking_repo.create(booking)

        # Auto-confirm if no approval required
        if not resource.requires_approval:
            booking.status = BookingStatus.CONFIRMED
            self.booking_repo.update(booking)

        return booking

    def _validate_booking_rules(
        self, resource: Resource, start: datetime, end: datetime
    ):
        """Validate booking against resource rules."""
        duration_minutes = (end - start).total_seconds() / 60

        if duration_minutes < resource.min_duration_minutes:
            raise BookingDurationError(
                f"Minimum duration is {resource.min_duration_minutes} minutes"
            )

        if duration_minutes > resource.max_duration_minutes:
            raise BookingDurationError(
                f"Maximum duration is {resource.max_duration_minutes} minutes"
            )

        advance_hours = (start - datetime.utcnow()).total_seconds() / 3600
        if advance_hours < resource.min_advance_hours:
            raise BookingAdvanceError(
                f"Must book at least {resource.min_advance_hours} hours in advance"
            )

        advance_days = advance_hours / 24
        if advance_days > resource.max_advance_days:
            raise BookingAdvanceError(
                f"Cannot book more than {resource.max_advance_days} days in advance"
            )

        # Check day of week
        if start.weekday() not in resource.available_days:
            raise BookingValidationError("Resource not available on this day")

        # Check time
        if resource.available_start_time and start.time() < resource.available_start_time:
            raise BookingValidationError("Booking starts before available hours")

        if resource.available_end_time and end.time() > resource.available_end_time:
            raise BookingValidationError("Booking ends after available hours")

    def _check_conflicts(
        self, resource_id: UUID, start: datetime, end: datetime,
        exclude_booking_id: Optional[UUID] = None
    ):
        """Check for booking conflicts."""
        conflicts = self.booking_repo.find_conflicts(
            resource_id, start, end, exclude_booking_id
        )
        if conflicts:
            raise BookingConflictError("Time slot conflicts with existing booking")

        blocked = self.blocked_repo.find_conflicts(resource_id, start, end)
        if blocked:
            raise BookingConflictError("Time slot is blocked")

    def update_booking(self, booking_id: UUID, data: BookingUpdate) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise BookingStateError("Cannot update booking in current status")

        if data.start_datetime or data.end_datetime:
            start = data.start_datetime or booking.start_datetime
            end = data.end_datetime or booking.end_datetime
            resource = self.get_resource(booking.resource_id)
            self._validate_booking_rules(resource, start, end)
            self._check_conflicts(booking.resource_id, start, end, booking_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(booking, field, value)

        booking.updated_by = self.user_id
        return self.booking_repo.update(booking)

    def cancel_booking(self, booking_id: UUID, reason: str = "") -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise BookingStateError("Cannot cancel booking in current status")

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_by = self.user_id
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def confirm_booking(self, booking_id: UUID) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status != BookingStatus.PENDING:
            raise BookingStateError("Only pending bookings can be confirmed")

        booking.status = BookingStatus.CONFIRMED
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def approve_booking(self, booking_id: UUID) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.approval_status != ApprovalStatus.PENDING:
            raise BookingStateError("Booking is not pending approval")

        booking.approval_status = ApprovalStatus.APPROVED
        booking.approved_by = self.user_id
        booking.approved_at = datetime.utcnow()
        booking.status = BookingStatus.CONFIRMED
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def reject_booking(self, booking_id: UUID, reason: str = "") -> Booking:
        booking = self.get_booking(booking_id)

        if booking.approval_status != ApprovalStatus.PENDING:
            raise BookingStateError("Booking is not pending approval")

        booking.approval_status = ApprovalStatus.REJECTED
        booking.rejection_reason = reason
        booking.status = BookingStatus.REJECTED
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def check_in(self, booking_id: UUID) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingStateError("Only confirmed bookings can check in")

        if booking.checked_in_at:
            raise BookingAlreadyCheckedInError("Already checked in")

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = datetime.utcnow()
        booking.checked_in_by = self.user_id
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def check_out(self, booking_id: UUID) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status != BookingStatus.CHECKED_IN:
            raise BookingStateError("Only checked-in bookings can check out")

        booking.status = BookingStatus.COMPLETED
        booking.checked_out_at = datetime.utcnow()
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    def mark_no_show(self, booking_id: UUID) -> Booking:
        booking = self.get_booking(booking_id)

        if booking.status != BookingStatus.CONFIRMED:
            raise BookingStateError("Only confirmed bookings can be marked as no-show")

        booking.status = BookingStatus.NO_SHOW
        booking.updated_by = self.user_id

        return self.booking_repo.update(booking)

    # ============== Availability ==============

    def get_availability(
        self, resource_id: UUID, date_from: date, date_to: date
    ) -> List[AvailabilitySlot]:
        resource = self.get_resource(resource_id)
        bookings = self.booking_repo.list_for_resource(resource_id, date_from, date_to)
        blocked_slots = self.blocked_repo.list_for_resource(resource_id, date_from, date_to)

        slots = []
        current = datetime.combine(date_from, resource.available_start_time)
        end_date = datetime.combine(date_to, resource.available_end_time)

        while current < end_date:
            slot_end = current + timedelta(minutes=resource.min_duration_minutes)

            is_available = True
            conflict_id = None
            conflict_reason = ""

            # Check against bookings
            for booking in bookings:
                if current < booking.end_datetime and slot_end > booking.start_datetime:
                    is_available = False
                    conflict_id = booking.id
                    conflict_reason = "Booked"
                    break

            # Check against blocked slots
            if is_available:
                for blocked in blocked_slots:
                    if current < blocked.end_datetime and slot_end > blocked.start_datetime:
                        is_available = False
                        conflict_reason = blocked.reason or "Blocked"
                        break

            slots.append(AvailabilitySlot(
                start_datetime=current,
                end_datetime=slot_end,
                is_available=is_available,
                conflict_booking_id=conflict_id,
                conflict_reason=conflict_reason
            ))

            current = slot_end

        return slots

    # ============== BlockedSlot ==============

    def get_blocked_slot(self, slot_id: UUID) -> BlockedSlot:
        slot = self.blocked_repo.get_by_id(slot_id)
        if not slot:
            raise BlockedSlotNotFoundError(f"Blocked slot {slot_id} not found")
        return slot

    def create_blocked_slot(self, data: BlockedSlotCreate) -> BlockedSlot:
        self.get_resource(data.resource_id)

        slot = BlockedSlot(
            resource_id=data.resource_id,
            start_datetime=data.start_datetime,
            end_datetime=data.end_datetime,
            reason=data.reason,
            blocked_by=self.user_id,
            is_recurring=data.is_recurring,
            recurrence_rule=data.recurrence_rule.model_dump() if data.recurrence_rule else None,
            created_by=self.user_id
        )
        return self.blocked_repo.create(slot)

    def delete_blocked_slot(self, slot_id: UUID) -> bool:
        self.get_blocked_slot(slot_id)
        return self.blocked_repo.soft_delete(slot_id, self.user_id)

    # ============== Waitlist ==============

    def get_waitlist_entry(self, entry_id: UUID) -> WaitlistEntry:
        entry = self.waitlist_repo.get_by_id(entry_id)
        if not entry:
            raise WaitlistEntryNotFoundError(f"Waitlist entry {entry_id} not found")
        return entry

    def create_waitlist_entry(self, data: WaitlistCreate) -> WaitlistEntry:
        self.get_resource(data.resource_id)

        entry = WaitlistEntry(
            resource_id=data.resource_id,
            user_id=self.user_id,
            desired_start=data.desired_start,
            desired_end=data.desired_end,
            flexible_time=data.flexible_time,
            flexible_date=data.flexible_date,
            alternative_resource_ids=data.alternative_resource_ids,
            priority=data.priority,
            expires_at=data.expires_at,
            created_by=self.user_id
        )
        return self.waitlist_repo.create(entry)

    def cancel_waitlist_entry(self, entry_id: UUID) -> bool:
        entry = self.get_waitlist_entry(entry_id)
        entry.status = WaitlistStatus.CANCELLED
        self.waitlist_repo.update(entry)
        return True

    def list_waitlist(
        self, resource_id: Optional[UUID] = None, user_id: Optional[UUID] = None
    ) -> List[WaitlistEntry]:
        if resource_id:
            return self.waitlist_repo.list_for_resource(resource_id)
        elif user_id:
            return self.waitlist_repo.list_for_user(user_id)
        return []

    # ============== Stats ==============

    def get_resource_stats(
        self, resource_id: UUID, date_from: date, date_to: date
    ) -> dict:
        self.get_resource(resource_id)
        return self.booking_repo.get_stats(resource_id, date_from, date_to)
