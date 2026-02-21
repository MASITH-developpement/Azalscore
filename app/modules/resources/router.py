"""
Routes API Resources / Réservation
==================================
"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .exceptions import (
    LocationNotFoundError, LocationDuplicateError,
    AmenityNotFoundError, AmenityDuplicateError,
    ResourceNotFoundError, ResourceDuplicateError, ResourceUnavailableError,
    BookingNotFoundError, BookingValidationError, BookingStateError,
    BookingConflictError, BookingDurationError, BookingAdvanceError,
    BlockedSlotNotFoundError, WaitlistEntryNotFoundError
)
from .schemas import (
    LocationCreate, LocationUpdate, LocationResponse, LocationListResponse,
    AmenityCreate, AmenityUpdate, AmenityResponse, AmenityListResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceListResponse,
    BookingCreate, BookingUpdate, BookingResponse, BookingListResponse,
    BlockedSlotCreate, BlockedSlotResponse, BlockedSlotListResponse,
    WaitlistCreate, WaitlistResponse, WaitlistListResponse,
    AvailabilityRequest, AvailabilityResponse,
    AutocompleteResponse
)
from .service import ResourceService


router = APIRouter(prefix="/resources", tags=["Resources"])


def get_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ResourceService:
    return ResourceService(db, user.tenant_id, user.id)


# ============== Location Routes ==============

@router.get("/locations", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    is_active: Optional[bool] = None,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:location:read")
):
    items, total, pages = service.list_locations(page, page_size, search, is_active)
    return LocationListResponse(
        items=[LocationResponse.model_validate(l) for l in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:location:read")
):
    try:
        return LocationResponse.model_validate(service.get_location(location_id))
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    data: LocationCreate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:location:create")
):
    try:
        return LocationResponse.model_validate(service.create_location(data))
    except LocationDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:location:update")
):
    try:
        return LocationResponse.model_validate(service.update_location(location_id, data))
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LocationDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/locations/{location_id}", status_code=204)
async def delete_location(
    location_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:location:delete")
):
    try:
        service.delete_location(location_id)
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Resource Routes ==============

@router.get("/", response_model=ResourceListResponse)
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    location_id: Optional[UUID] = None,
    min_capacity: Optional[int] = None,
    max_capacity: Optional[int] = None,
    is_active: Optional[bool] = None,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:read")
):
    items, total, pages = service.list_resources(
        page, page_size, search, resource_type, status,
        location_id, min_capacity, max_capacity, is_active
    )
    return ResourceListResponse(
        items=[ResourceResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:read")
):
    try:
        return ResourceResponse.model_validate(service.get_resource(resource_id))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource(
    data: ResourceCreate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:create")
):
    try:
        return ResourceResponse.model_validate(service.create_resource(data))
    except ResourceDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: UUID,
    data: ResourceUpdate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:update")
):
    try:
        return ResourceResponse.model_validate(service.update_resource(resource_id, data))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ResourceDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:delete")
):
    try:
        service.delete_resource(resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{resource_id}/status", response_model=ResourceResponse)
async def set_resource_status(
    resource_id: UUID,
    status: str,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:update")
):
    try:
        return ResourceResponse.model_validate(service.set_resource_status(resource_id, status))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Booking Routes ==============

@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    approval_status: Optional[str] = None,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:read")
):
    items, total, pages = service.list_bookings(
        page, page_size, resource_id, user_id, status,
        date_from, date_to, approval_status
    )
    return BookingListResponse(
        items=[BookingResponse.model_validate(b) for b in items],
        total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:read")
):
    try:
        return BookingResponse.model_validate(service.get_booking(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:create")
):
    try:
        return BookingResponse.model_validate(service.create_booking(data))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ResourceUnavailableError, BookingConflictError,
            BookingDurationError, BookingAdvanceError, BookingValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    data: BookingUpdate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:update")
):
    try:
        return BookingResponse.model_validate(service.update_booking(booking_id, data))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (BookingStateError, BookingConflictError, BookingValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    reason: str = "",
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:cancel")
):
    try:
        return BookingResponse.model_validate(service.cancel_booking(booking_id, reason))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:confirm")
):
    try:
        return BookingResponse.model_validate(service.confirm_booking(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:approve")
):
    try:
        return BookingResponse.model_validate(service.approve_booking(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: UUID,
    reason: str = "",
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:approve")
):
    try:
        return BookingResponse.model_validate(service.reject_booking(booking_id, reason))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/check-in", response_model=BookingResponse)
async def check_in(
    booking_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:checkin")
):
    try:
        return BookingResponse.model_validate(service.check_in(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bookings/{booking_id}/check-out", response_model=BookingResponse)
async def check_out(
    booking_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:booking:checkin")
):
    try:
        return BookingResponse.model_validate(service.check_out(booking_id))
    except BookingNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BookingStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Availability Routes ==============

@router.get("/{resource_id}/availability", response_model=AvailabilityResponse)
async def get_availability(
    resource_id: UUID,
    date_from: date,
    date_to: date,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:read")
):
    try:
        slots = service.get_availability(resource_id, date_from, date_to)
        return AvailabilityResponse(
            resource_id=resource_id,
            date_from=date_from,
            date_to=date_to,
            slots=slots
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Blocked Slot Routes ==============

@router.post("/blocked-slots", response_model=BlockedSlotResponse, status_code=201)
async def create_blocked_slot(
    data: BlockedSlotCreate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:blocked:create")
):
    try:
        return BlockedSlotResponse.model_validate(service.create_blocked_slot(data))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/blocked-slots/{slot_id}", status_code=204)
async def delete_blocked_slot(
    slot_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:blocked:delete")
):
    try:
        service.delete_blocked_slot(slot_id)
    except BlockedSlotNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Waitlist Routes ==============

@router.post("/waitlist", response_model=WaitlistResponse, status_code=201)
async def create_waitlist_entry(
    data: WaitlistCreate,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:waitlist:create")
):
    try:
        return WaitlistResponse.model_validate(service.create_waitlist_entry(data))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/waitlist/{entry_id}", status_code=204)
async def cancel_waitlist_entry(
    entry_id: UUID,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:waitlist:cancel")
):
    try:
        service.cancel_waitlist_entry(entry_id)
    except WaitlistEntryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Stats Routes ==============

@router.get("/{resource_id}/stats")
async def get_resource_stats(
    resource_id: UUID,
    date_from: date,
    date_to: date,
    service: ResourceService = Depends(get_service),
    _: None = require_permission("resources:stats")
):
    try:
        return service.get_resource_stats(resource_id, date_from, date_to)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
