"""
Repository Resources / Réservation
==================================
Pattern Repository avec tenant isolation obligatoire.
"""
from __future__ import annotations

from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from .models import (
    ResourceLocation, Amenity, Resource, ResourceType, ResourceStatus,
    Booking, BookingStatus, ApprovalStatus, RecurrenceType,
    BlockedSlot, WaitlistEntry, WaitlistStatus
)

# Alias pour compatibilité
Location = ResourceLocation


class LocationRepository:
    """Repository pour Location avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Location).filter(
            Location.tenant_id == self.tenant_id,
            Location.is_deleted == False
        )

    def get_by_id(self, location_id: UUID) -> Optional[Location]:
        return self._base_query().filter(Location.id == location_id).first()

    def get_by_code(self, code: str) -> Optional[Location]:
        return self._base_query().filter(Location.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Location], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Location.code.ilike(search_filter),
                    Location.name.ilike(search_filter),
                    Location.building.ilike(search_filter)
                )
            )

        if is_active is not None:
            query = query.filter(Location.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Location.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, location: Location) -> Location:
        location.tenant_id = self.tenant_id
        self.db.add(location)
        self.db.flush()
        return location

    def update(self, location: Location) -> Location:
        location.version += 1
        self.db.flush()
        return location

    def soft_delete(self, location_id: UUID, deleted_by: UUID) -> bool:
        location = self.get_by_id(location_id)
        if not location:
            return False
        location.is_deleted = True
        location.deleted_at = datetime.utcnow()
        location.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore(self, location_id: UUID) -> Optional[Location]:
        location = self.db.query(Location).filter(
            Location.tenant_id == self.tenant_id,
            Location.id == location_id,
            Location.is_deleted == True
        ).first()
        if location:
            location.is_deleted = False
            location.deleted_at = None
            location.deleted_by = None
            self.db.flush()
        return location

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        locations = self._base_query().filter(
            Location.is_active == True,
            or_(
                Location.code.ilike(f"%{search}%"),
                Location.name.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": l.id, "code": l.code, "name": l.name} for l in locations]


class AmenityRepository:
    """Repository pour Amenity avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Amenity).filter(
            Amenity.tenant_id == self.tenant_id,
            Amenity.is_deleted == False
        )

    def get_by_id(self, amenity_id: UUID) -> Optional[Amenity]:
        return self._base_query().filter(Amenity.id == amenity_id).first()

    def get_by_code(self, code: str) -> Optional[Amenity]:
        return self._base_query().filter(Amenity.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Amenity], int, int]:
        query = self._base_query()

        if search:
            query = query.filter(
                or_(
                    Amenity.code.ilike(f"%{search}%"),
                    Amenity.name.ilike(f"%{search}%")
                )
            )

        if category:
            query = query.filter(Amenity.category == category)

        if is_active is not None:
            query = query.filter(Amenity.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Amenity.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, amenity: Amenity) -> Amenity:
        amenity.tenant_id = self.tenant_id
        self.db.add(amenity)
        self.db.flush()
        return amenity

    def soft_delete(self, amenity_id: UUID, deleted_by: UUID) -> bool:
        amenity = self.get_by_id(amenity_id)
        if not amenity:
            return False
        amenity.is_deleted = True
        amenity.deleted_at = datetime.utcnow()
        amenity.deleted_by = deleted_by
        self.db.flush()
        return True


class ResourceRepository:
    """Repository pour Resource avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Resource).filter(
            Resource.tenant_id == self.tenant_id,
            Resource.is_deleted == False
        )

    def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        return self._base_query().filter(Resource.id == resource_id).first()

    def get_by_code(self, code: str) -> Optional[Resource]:
        return self._base_query().filter(Resource.code == code).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        status: Optional[ResourceStatus] = None,
        location_id: Optional[UUID] = None,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Resource], int, int]:
        query = self._base_query()

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Resource.code.ilike(search_filter),
                    Resource.name.ilike(search_filter),
                    Resource.description.ilike(search_filter)
                )
            )

        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)

        if status:
            query = query.filter(Resource.status == status)

        if location_id:
            query = query.filter(Resource.location_id == location_id)

        if min_capacity is not None:
            query = query.filter(Resource.capacity >= min_capacity)

        if max_capacity is not None:
            query = query.filter(Resource.capacity <= max_capacity)

        if is_active is not None:
            query = query.filter(Resource.is_active == is_active)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Resource.name).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def create(self, resource: Resource) -> Resource:
        resource.tenant_id = self.tenant_id
        self.db.add(resource)
        self.db.flush()
        return resource

    def update(self, resource: Resource) -> Resource:
        resource.version += 1
        self.db.flush()
        return resource

    def soft_delete(self, resource_id: UUID, deleted_by: UUID) -> bool:
        resource = self.get_by_id(resource_id)
        if not resource:
            return False
        resource.is_deleted = True
        resource.deleted_at = datetime.utcnow()
        resource.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore(self, resource_id: UUID) -> Optional[Resource]:
        resource = self.db.query(Resource).filter(
            Resource.tenant_id == self.tenant_id,
            Resource.id == resource_id,
            Resource.is_deleted == True
        ).first()
        if resource:
            resource.is_deleted = False
            resource.deleted_at = None
            resource.deleted_by = None
            self.db.flush()
        return resource

    def bulk_delete(self, resource_ids: List[UUID], deleted_by: UUID) -> int:
        count = 0
        for resource_id in resource_ids:
            if self.soft_delete(resource_id, deleted_by):
                count += 1
        return count

    def autocomplete(self, search: str, limit: int = 10) -> List[dict]:
        resources = self._base_query().filter(
            Resource.is_active == True,
            or_(
                Resource.code.ilike(f"%{search}%"),
                Resource.name.ilike(f"%{search}%")
            )
        ).limit(limit).all()
        return [{"id": r.id, "code": r.code, "name": r.name} for r in resources]


class BookingRepository:
    """Repository pour Booking avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Booking).filter(
            Booking.tenant_id == self.tenant_id,
            Booking.is_deleted == False
        )

    def get_by_id(self, booking_id: UUID) -> Optional[Booking]:
        return self._base_query().filter(Booking.id == booking_id).first()

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        resource_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        status: Optional[BookingStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        approval_status: Optional[ApprovalStatus] = None
    ) -> Tuple[List[Booking], int, int]:
        query = self._base_query()

        if resource_id:
            query = query.filter(Booking.resource_id == resource_id)

        if user_id:
            query = query.filter(Booking.user_id == user_id)

        if status:
            query = query.filter(Booking.status == status)

        if date_from:
            query = query.filter(func.date(Booking.start_datetime) >= date_from)

        if date_to:
            query = query.filter(func.date(Booking.end_datetime) <= date_to)

        if approval_status:
            query = query.filter(Booking.approval_status == approval_status)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.order_by(Booking.start_datetime.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total, pages

    def find_conflicts(
        self,
        resource_id: UUID,
        start: datetime,
        end: datetime,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[Booking]:
        query = self._base_query().filter(
            Booking.resource_id == resource_id,
            Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.REJECTED]),
            or_(
                and_(Booking.start_datetime <= start, Booking.end_datetime > start),
                and_(Booking.start_datetime < end, Booking.end_datetime >= end),
                and_(Booking.start_datetime >= start, Booking.end_datetime <= end)
            )
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        return query.all()

    def list_for_resource(
        self,
        resource_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[Booking]:
        return self._base_query().filter(
            Booking.resource_id == resource_id,
            Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.REJECTED]),
            func.date(Booking.start_datetime) >= date_from,
            func.date(Booking.end_datetime) <= date_to
        ).order_by(Booking.start_datetime).all()

    def list_pending_approval(
        self,
        approver_id: Optional[UUID] = None
    ) -> List[Booking]:
        query = self._base_query().filter(
            Booking.approval_status == ApprovalStatus.PENDING
        )
        return query.order_by(Booking.created_at).all()

    def create(self, booking: Booking) -> Booking:
        booking.tenant_id = self.tenant_id
        self.db.add(booking)
        self.db.flush()
        return booking

    def update(self, booking: Booking) -> Booking:
        booking.version += 1
        booking.updated_at = datetime.utcnow()
        self.db.flush()
        return booking

    def soft_delete(self, booking_id: UUID, deleted_by: UUID) -> bool:
        booking = self.get_by_id(booking_id)
        if not booking:
            return False
        booking.is_deleted = True
        booking.deleted_at = datetime.utcnow()
        booking.deleted_by = deleted_by
        self.db.flush()
        return True

    def get_stats(self, resource_id: UUID, date_from: date, date_to: date) -> dict:
        query = self._base_query().filter(
            Booking.resource_id == resource_id,
            func.date(Booking.start_datetime) >= date_from,
            func.date(Booking.end_datetime) <= date_to
        )

        total = query.count()
        completed = query.filter(Booking.status == BookingStatus.COMPLETED).count()
        cancelled = query.filter(Booking.status == BookingStatus.CANCELLED).count()
        no_show = query.filter(Booking.status == BookingStatus.NO_SHOW).count()

        return {
            "total": total,
            "completed": completed,
            "cancelled": cancelled,
            "no_show": no_show
        }


class BlockedSlotRepository:
    """Repository pour BlockedSlot avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(BlockedSlot).filter(
            BlockedSlot.tenant_id == self.tenant_id,
            BlockedSlot.is_deleted == False
        )

    def get_by_id(self, slot_id: UUID) -> Optional[BlockedSlot]:
        return self._base_query().filter(BlockedSlot.id == slot_id).first()

    def list_for_resource(
        self,
        resource_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[BlockedSlot]:
        return self._base_query().filter(
            BlockedSlot.resource_id == resource_id,
            BlockedSlot.is_active == True,
            func.date(BlockedSlot.start_datetime) >= date_from,
            func.date(BlockedSlot.end_datetime) <= date_to
        ).order_by(BlockedSlot.start_datetime).all()

    def find_conflicts(
        self,
        resource_id: UUID,
        start: datetime,
        end: datetime
    ) -> List[BlockedSlot]:
        return self._base_query().filter(
            BlockedSlot.resource_id == resource_id,
            BlockedSlot.is_active == True,
            or_(
                and_(BlockedSlot.start_datetime <= start, BlockedSlot.end_datetime > start),
                and_(BlockedSlot.start_datetime < end, BlockedSlot.end_datetime >= end),
                and_(BlockedSlot.start_datetime >= start, BlockedSlot.end_datetime <= end)
            )
        ).all()

    def create(self, slot: BlockedSlot) -> BlockedSlot:
        slot.tenant_id = self.tenant_id
        self.db.add(slot)
        self.db.flush()
        return slot

    def update(self, slot: BlockedSlot) -> BlockedSlot:
        self.db.flush()
        return slot

    def soft_delete(self, slot_id: UUID, deleted_by: UUID) -> bool:
        slot = self.get_by_id(slot_id)
        if not slot:
            return False
        slot.is_deleted = True
        slot.deleted_at = datetime.utcnow()
        slot.deleted_by = deleted_by
        self.db.flush()
        return True


class WaitlistRepository:
    """Repository pour WaitlistEntry avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(WaitlistEntry).filter(
            WaitlistEntry.tenant_id == self.tenant_id,
            WaitlistEntry.is_deleted == False
        )

    def get_by_id(self, entry_id: UUID) -> Optional[WaitlistEntry]:
        return self._base_query().filter(WaitlistEntry.id == entry_id).first()

    def list_for_resource(
        self,
        resource_id: UUID,
        status: Optional[WaitlistStatus] = None
    ) -> List[WaitlistEntry]:
        query = self._base_query().filter(
            WaitlistEntry.resource_id == resource_id
        )
        if status:
            query = query.filter(WaitlistEntry.status == status)
        return query.order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()

    def list_for_user(
        self,
        user_id: UUID
    ) -> List[WaitlistEntry]:
        return self._base_query().filter(
            WaitlistEntry.user_id == user_id
        ).order_by(WaitlistEntry.created_at.desc()).all()

    def create(self, entry: WaitlistEntry) -> WaitlistEntry:
        entry.tenant_id = self.tenant_id
        self.db.add(entry)
        self.db.flush()
        return entry

    def update(self, entry: WaitlistEntry) -> WaitlistEntry:
        self.db.flush()
        return entry

    def soft_delete(self, entry_id: UUID, deleted_by: UUID) -> bool:
        entry = self.get_by_id(entry_id)
        if not entry:
            return False
        entry.is_deleted = True
        entry.deleted_at = datetime.utcnow()
        entry.deleted_by = deleted_by
        self.db.flush()
        return True
