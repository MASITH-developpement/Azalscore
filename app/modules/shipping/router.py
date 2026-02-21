"""
Router Shipping / Expédition - GAP-078
=======================================

Endpoints API pour la gestion des expéditions.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import CarrierType, ShippingMethod, ShipmentStatus, ReturnStatus
from .schemas import (
    # Zone schemas
    ZoneCreate, ZoneUpdate, ZoneResponse, ZoneListResponse,
    # Carrier schemas
    CarrierCreate, CarrierUpdate, CarrierResponse, CarrierListResponse,
    # Rate schemas
    RateCreate, RateUpdate, RateResponse, RateListResponse,
    RateCalculationRequest, RateCalculationResponse,
    # Shipment schemas
    ShipmentCreate, ShipmentUpdate, ShipmentResponse, ShipmentListResponse,
    TrackingEventCreate, LabelGenerationResponse,
    # Package schemas
    PackageUpdate, PackageResponse,
    # PickupPoint schemas
    PickupPointCreate, PickupPointUpdate, PickupPointResponse,
    PickupPointListResponse, PickupPointSearchRequest,
    # Return schemas
    ReturnCreate, ReturnResponse, ReturnListResponse,
    RefundRequest,
    # Stats
    ShippingStatsResponse
)
from .service import ShippingService
from .exceptions import (
    ZoneNotFoundError, ZoneDuplicateError, ZoneValidationError, ZoneInUseError,
    CarrierNotFoundError, CarrierDuplicateError, CarrierValidationError,
    CarrierInactiveError, CarrierInUseError,
    RateNotFoundError, RateDuplicateError, RateValidationError, NoRateAvailableError,
    ShipmentNotFoundError, ShipmentValidationError, ShipmentStateError,
    ShipmentCannotBeCancelledError, LabelAlreadyGeneratedError, TrackingNumberNotFoundError,
    PackageNotFoundError,
    PickupPointNotFoundError, PickupPointDuplicateError, PickupPointInactiveError,
    ReturnNotFoundError, ReturnStateError, ReturnAlreadyApprovedError,
    ReturnAlreadyRefundedError, ReturnNotApprovedError, ReturnNotReceivedError,
    ReturnRejectedError,
    AddressNotServiceableError
)


router = APIRouter(prefix="/shipping", tags=["shipping"])


def get_service(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ShippingService:
    """Obtenir une instance du service Shipping."""
    return ShippingService(db, current_user["tenant_id"])


# ==================== Zone Endpoints ====================

@router.post(
    "/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une zone de livraison"
)
async def create_zone(
    data: ZoneCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:create"))
):
    """Créer une nouvelle zone de livraison."""
    try:
        zone = await service.create_zone(data, current_user["id"])
        return ZoneResponse.model_validate(zone)
    except ZoneDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ZoneValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Récupérer une zone"
)
async def get_zone(
    zone_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:read"))
):
    """Récupérer une zone par son ID."""
    try:
        zone = await service.get_zone(str(zone_id))
        return ZoneResponse.model_validate(zone)
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/zones/code/{code}",
    response_model=ZoneResponse,
    summary="Récupérer une zone par code"
)
async def get_zone_by_code(
    code: str,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:read"))
):
    """Récupérer une zone par son code."""
    try:
        zone = await service.get_zone_by_code(code)
        return ZoneResponse.model_validate(zone)
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Mettre à jour une zone"
)
async def update_zone(
    zone_id: UUID,
    data: ZoneUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:update"))
):
    """Mettre à jour une zone de livraison."""
    try:
        zone = await service.update_zone(str(zone_id), data, current_user["id"])
        return ZoneResponse.model_validate(zone)
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ZoneDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Supprimer une zone"
)
async def delete_zone(
    zone_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:delete"))
):
    """Supprimer une zone (soft delete)."""
    try:
        zone = await service.delete_zone(str(zone_id), current_user["id"])
        return ZoneResponse.model_validate(zone)
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ZoneInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/zones/{zone_id}/restore",
    response_model=ZoneResponse,
    summary="Restaurer une zone"
)
async def restore_zone(
    zone_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:restore"))
):
    """Restaurer une zone supprimée."""
    try:
        zone = await service.restore_zone(str(zone_id), current_user["id"])
        return ZoneResponse.model_validate(zone)
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/zones",
    response_model=ZoneListResponse,
    summary="Lister les zones"
)
async def list_zones(
    is_active: Optional[bool] = Query(None),
    country_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:zone:read"))
):
    """Lister les zones de livraison."""
    zones, total = await service.list_zones(
        is_active=is_active,
        country_code=country_code,
        skip=skip,
        limit=limit
    )
    return ZoneListResponse(
        items=[ZoneResponse.model_validate(z) for z in zones],
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== Carrier Endpoints ====================

@router.post(
    "/carriers",
    response_model=CarrierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un transporteur"
)
async def create_carrier(
    data: CarrierCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:create"))
):
    """Créer un nouveau transporteur."""
    try:
        carrier = await service.create_carrier(data, current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CarrierValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/carriers/{carrier_id}",
    response_model=CarrierResponse,
    summary="Récupérer un transporteur"
)
async def get_carrier(
    carrier_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:read"))
):
    """Récupérer un transporteur par son ID."""
    try:
        carrier = await service.get_carrier(str(carrier_id))
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/carriers/code/{code}",
    response_model=CarrierResponse,
    summary="Récupérer un transporteur par code"
)
async def get_carrier_by_code(
    code: str,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:read"))
):
    """Récupérer un transporteur par son code."""
    try:
        carrier = await service.get_carrier_by_code(code)
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/carriers/{carrier_id}",
    response_model=CarrierResponse,
    summary="Mettre à jour un transporteur"
)
async def update_carrier(
    carrier_id: UUID,
    data: CarrierUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:update"))
):
    """Mettre à jour un transporteur."""
    try:
        carrier = await service.update_carrier(str(carrier_id), data, current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CarrierDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/carriers/{carrier_id}",
    response_model=CarrierResponse,
    summary="Supprimer un transporteur"
)
async def delete_carrier(
    carrier_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:delete"))
):
    """Supprimer un transporteur (soft delete)."""
    try:
        carrier = await service.delete_carrier(str(carrier_id), current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CarrierInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/carriers/{carrier_id}/restore",
    response_model=CarrierResponse,
    summary="Restaurer un transporteur"
)
async def restore_carrier(
    carrier_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:restore"))
):
    """Restaurer un transporteur supprimé."""
    try:
        carrier = await service.restore_carrier(str(carrier_id), current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/carriers/{carrier_id}/activate",
    response_model=CarrierResponse,
    summary="Activer un transporteur"
)
async def activate_carrier(
    carrier_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:update"))
):
    """Activer un transporteur."""
    try:
        carrier = await service.activate_carrier(str(carrier_id), current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/carriers/{carrier_id}/deactivate",
    response_model=CarrierResponse,
    summary="Désactiver un transporteur"
)
async def deactivate_carrier(
    carrier_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:update"))
):
    """Désactiver un transporteur."""
    try:
        carrier = await service.deactivate_carrier(str(carrier_id), current_user["id"])
        return CarrierResponse.model_validate(carrier)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/carriers",
    response_model=CarrierListResponse,
    summary="Lister les transporteurs"
)
async def list_carriers(
    carrier_type: Optional[CarrierType] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:carrier:read"))
):
    """Lister les transporteurs."""
    carriers, total = await service.list_carriers(
        carrier_type=carrier_type,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )
    return CarrierListResponse(
        items=[CarrierResponse.model_validate(c) for c in carriers],
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== Rate Endpoints ====================

@router.post(
    "/rates",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un tarif"
)
async def create_rate(
    data: RateCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:create"))
):
    """Créer un nouveau tarif d'expédition."""
    try:
        rate = await service.create_rate(data, current_user["id"])
        return RateResponse.model_validate(rate)
    except RateDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (RateValidationError, CarrierNotFoundError, ZoneNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/rates/{rate_id}",
    response_model=RateResponse,
    summary="Récupérer un tarif"
)
async def get_rate(
    rate_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:read"))
):
    """Récupérer un tarif par son ID."""
    try:
        rate = await service.get_rate(str(rate_id))
        return RateResponse.model_validate(rate)
    except RateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/rates/{rate_id}",
    response_model=RateResponse,
    summary="Mettre à jour un tarif"
)
async def update_rate(
    rate_id: UUID,
    data: RateUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:update"))
):
    """Mettre à jour un tarif."""
    try:
        rate = await service.update_rate(str(rate_id), data, current_user["id"])
        return RateResponse.model_validate(rate)
    except RateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RateDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ZoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/rates/{rate_id}",
    response_model=RateResponse,
    summary="Supprimer un tarif"
)
async def delete_rate(
    rate_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:delete"))
):
    """Supprimer un tarif (soft delete)."""
    try:
        rate = await service.delete_rate(str(rate_id), current_user["id"])
        return RateResponse.model_validate(rate)
    except RateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/rates/{rate_id}/restore",
    response_model=RateResponse,
    summary="Restaurer un tarif"
)
async def restore_rate(
    rate_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:restore"))
):
    """Restaurer un tarif supprimé."""
    try:
        rate = await service.restore_rate(str(rate_id), current_user["id"])
        return RateResponse.model_validate(rate)
    except RateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/rates",
    response_model=RateListResponse,
    summary="Lister les tarifs"
)
async def list_rates(
    carrier_id: Optional[UUID] = Query(None),
    zone_id: Optional[UUID] = Query(None),
    shipping_method: Optional[ShippingMethod] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:read"))
):
    """Lister les tarifs d'expédition."""
    rates, total = await service.list_rates(
        carrier_id=str(carrier_id) if carrier_id else None,
        zone_id=str(zone_id) if zone_id else None,
        shipping_method=shipping_method,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return RateListResponse(
        items=[RateResponse.model_validate(r) for r in rates],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post(
    "/rates/calculate",
    response_model=List[RateCalculationResponse],
    summary="Calculer les tarifs disponibles"
)
async def calculate_rates(
    request: RateCalculationRequest,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:rate:read"))
):
    """Calculer les tarifs disponibles pour une expédition."""
    try:
        rates = await service.calculate_shipping_rates(request)
        return rates
    except (AddressNotServiceableError, NoRateAvailableError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Shipment Endpoints ====================

@router.post(
    "/shipments",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une expédition"
)
async def create_shipment(
    data: ShipmentCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:create"))
):
    """Créer une nouvelle expédition."""
    try:
        shipment = await service.create_shipment(data, current_user["id"])
        return ShipmentResponse.model_validate(shipment)
    except (CarrierNotFoundError, CarrierInactiveError, RateNotFoundError,
            PickupPointNotFoundError, PickupPointInactiveError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ShipmentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Récupérer une expédition"
)
async def get_shipment(
    shipment_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:read"))
):
    """Récupérer une expédition par son ID."""
    try:
        shipment = await service.get_shipment(str(shipment_id))
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/shipments/number/{shipment_number}",
    response_model=ShipmentResponse,
    summary="Récupérer une expédition par numéro"
)
async def get_shipment_by_number(
    shipment_number: str,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:read"))
):
    """Récupérer une expédition par son numéro."""
    try:
        shipment = await service.get_shipment_by_number(shipment_number)
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/shipments/tracking/{tracking_number}",
    response_model=ShipmentResponse,
    summary="Récupérer une expédition par numéro de suivi"
)
async def get_shipment_by_tracking(
    tracking_number: str,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:read"))
):
    """Récupérer une expédition par son numéro de suivi."""
    try:
        shipment = await service.get_shipment_by_tracking(tracking_number)
        return ShipmentResponse.model_validate(shipment)
    except TrackingNumberNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Mettre à jour une expédition"
)
async def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:update"))
):
    """Mettre à jour une expédition."""
    try:
        shipment = await service.update_shipment(str(shipment_id), data, current_user["id"])
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/shipments/{shipment_id}/label",
    response_model=LabelGenerationResponse,
    summary="Générer l'étiquette"
)
async def generate_label(
    shipment_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:label"))
):
    """Générer l'étiquette d'expédition."""
    try:
        result = await service.generate_label(str(shipment_id), current_user["id"])
        return result
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LabelAlreadyGeneratedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (ShipmentStateError, CarrierNotFoundError, CarrierValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/shipments/{shipment_id}/tracking",
    response_model=ShipmentResponse,
    summary="Mettre à jour le suivi"
)
async def update_tracking(
    shipment_id: UUID,
    event: TrackingEventCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:tracking"))
):
    """Mettre à jour le suivi d'une expédition."""
    try:
        shipment = await service.update_tracking(str(shipment_id), event, current_user["id"])
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/shipments/{shipment_id}/cancel",
    response_model=ShipmentResponse,
    summary="Annuler une expédition"
)
async def cancel_shipment(
    shipment_id: UUID,
    reason: str = Query(...),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:cancel"))
):
    """Annuler une expédition."""
    try:
        shipment = await service.cancel_shipment(str(shipment_id), reason, current_user["id"])
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentCannotBeCancelledError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/shipments/{shipment_id}/pickup",
    response_model=ShipmentResponse,
    summary="Marquer comme enlevé"
)
async def mark_picked_up(
    shipment_id: UUID,
    pickup_confirmation: str = Query(...),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:tracking"))
):
    """Marquer une expédition comme enlevée."""
    try:
        shipment = await service.mark_picked_up(
            str(shipment_id), pickup_confirmation, current_user["id"]
        )
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/shipments/{shipment_id}/delivered",
    response_model=ShipmentResponse,
    summary="Marquer comme livré"
)
async def mark_delivered(
    shipment_id: UUID,
    signature: Optional[str] = Query(None),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:tracking"))
):
    """Marquer une expédition comme livrée."""
    try:
        shipment = await service.mark_delivered(
            str(shipment_id), None, signature, current_user["id"]
        )
        return ShipmentResponse.model_validate(shipment)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/shipments",
    response_model=ShipmentListResponse,
    summary="Lister les expéditions"
)
async def list_shipments(
    status: Optional[ShipmentStatus] = Query(None),
    carrier_id: Optional[UUID] = Query(None),
    order_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:read"))
):
    """Lister les expéditions."""
    shipments, total = await service.list_shipments(
        status=status,
        carrier_id=str(carrier_id) if carrier_id else None,
        order_id=order_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
        skip=skip,
        limit=limit
    )
    return ShipmentListResponse(
        items=[ShipmentResponse.model_validate(s) for s in shipments],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/shipments/{shipment_id}/packages",
    response_model=List[PackageResponse],
    summary="Récupérer les colis d'une expédition"
)
async def get_shipment_packages(
    shipment_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:shipment:read"))
):
    """Récupérer les colis d'une expédition."""
    try:
        packages = await service.get_shipment_packages(str(shipment_id))
        return [PackageResponse.model_validate(p) for p in packages]
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Package Endpoints ====================

@router.get(
    "/packages/{package_id}",
    response_model=PackageResponse,
    summary="Récupérer un colis"
)
async def get_package(
    package_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:package:read"))
):
    """Récupérer un colis par son ID."""
    try:
        package = await service.get_package(str(package_id))
        return PackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/packages/{package_id}",
    response_model=PackageResponse,
    summary="Mettre à jour un colis"
)
async def update_package(
    package_id: UUID,
    data: PackageUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:package:update"))
):
    """Mettre à jour un colis."""
    try:
        package = await service.update_package(str(package_id), data, current_user["id"])
        return PackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== PickupPoint Endpoints ====================

@router.post(
    "/pickup-points",
    response_model=PickupPointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un point relais"
)
async def create_pickup_point(
    data: PickupPointCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:create"))
):
    """Créer un nouveau point relais."""
    try:
        pickup_point = await service.create_pickup_point(data, current_user["id"])
        return PickupPointResponse.model_validate(pickup_point)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PickupPointDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/pickup-points/{pickup_point_id}",
    response_model=PickupPointResponse,
    summary="Récupérer un point relais"
)
async def get_pickup_point(
    pickup_point_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:read"))
):
    """Récupérer un point relais par son ID."""
    try:
        pickup_point = await service.get_pickup_point(str(pickup_point_id))
        return PickupPointResponse.model_validate(pickup_point)
    except PickupPointNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/pickup-points/{pickup_point_id}",
    response_model=PickupPointResponse,
    summary="Mettre à jour un point relais"
)
async def update_pickup_point(
    pickup_point_id: UUID,
    data: PickupPointUpdate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:update"))
):
    """Mettre à jour un point relais."""
    try:
        pickup_point = await service.update_pickup_point(
            str(pickup_point_id), data, current_user["id"]
        )
        return PickupPointResponse.model_validate(pickup_point)
    except PickupPointNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/pickup-points/{pickup_point_id}",
    response_model=PickupPointResponse,
    summary="Supprimer un point relais"
)
async def delete_pickup_point(
    pickup_point_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:delete"))
):
    """Supprimer un point relais (soft delete)."""
    try:
        pickup_point = await service.delete_pickup_point(
            str(pickup_point_id), current_user["id"]
        )
        return PickupPointResponse.model_validate(pickup_point)
    except PickupPointNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/pickup-points/search",
    response_model=List[PickupPointResponse],
    summary="Rechercher des points relais"
)
async def search_pickup_points(
    request: PickupPointSearchRequest,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:read"))
):
    """Rechercher des points relais à proximité."""
    pickup_points = await service.search_pickup_points(
        carrier_id=request.carrier_id,
        country_code=request.country_code,
        postal_code=request.postal_code,
        latitude=request.latitude,
        longitude=request.longitude,
        max_results=request.max_results,
        max_distance_km=request.max_distance_km
    )
    return [PickupPointResponse.model_validate(p) for p in pickup_points]


@router.get(
    "/pickup-points",
    response_model=PickupPointListResponse,
    summary="Lister les points relais"
)
async def list_pickup_points(
    carrier_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_locker: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:pickup-point:read"))
):
    """Lister les points relais."""
    pickup_points, total = await service.list_pickup_points(
        carrier_id=str(carrier_id) if carrier_id else None,
        is_active=is_active,
        is_locker=is_locker,
        skip=skip,
        limit=limit
    )
    return PickupPointListResponse(
        items=[PickupPointResponse.model_validate(p) for p in pickup_points],
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== Return Endpoints ====================

@router.post(
    "/returns",
    response_model=ReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une demande de retour"
)
async def create_return(
    data: ReturnCreate,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:create"))
):
    """Créer une nouvelle demande de retour."""
    try:
        ret = await service.create_return(data, current_user["id"])
        return ReturnResponse.model_validate(ret)
    except ShipmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/returns/{return_id}",
    response_model=ReturnResponse,
    summary="Récupérer un retour"
)
async def get_return(
    return_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:read"))
):
    """Récupérer un retour par son ID."""
    try:
        ret = await service.get_return(str(return_id))
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/returns/number/{return_number}",
    response_model=ReturnResponse,
    summary="Récupérer un retour par numéro"
)
async def get_return_by_number(
    return_number: str,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:read"))
):
    """Récupérer un retour par son numéro."""
    try:
        ret = await service.get_return_by_number(return_number)
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/returns/{return_id}/approve",
    response_model=ReturnResponse,
    summary="Approuver un retour"
)
async def approve_return(
    return_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:approve"))
):
    """Approuver une demande de retour."""
    try:
        ret = await service.approve_return(str(return_id), current_user["id"])
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ReturnAlreadyApprovedError, ReturnStateError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/returns/{return_id}/reject",
    response_model=ReturnResponse,
    summary="Rejeter un retour"
)
async def reject_return(
    return_id: UUID,
    reason: str = Query(...),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:reject"))
):
    """Rejeter une demande de retour."""
    try:
        ret = await service.reject_return(str(return_id), reason, current_user["id"])
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ReturnStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/returns/{return_id}/label",
    summary="Générer l'étiquette de retour"
)
async def generate_return_label(
    return_id: UUID,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:label"))
):
    """Générer l'étiquette de retour."""
    try:
        result = await service.generate_return_label(str(return_id), current_user["id"])
        return result
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ReturnNotApprovedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (ShipmentNotFoundError, CarrierNotFoundError, CarrierValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/returns/{return_id}/receive",
    response_model=ReturnResponse,
    summary="Réceptionner un retour"
)
async def receive_return(
    return_id: UUID,
    condition: str = Query(...),
    inspection_notes: str = Query(""),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:receive"))
):
    """Réceptionner un retour."""
    try:
        ret = await service.receive_return(
            str(return_id), condition, inspection_notes, current_user["id"]
        )
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ReturnStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/returns/{return_id}/inspect",
    response_model=ReturnResponse,
    summary="Inspecter un retour"
)
async def inspect_return(
    return_id: UUID,
    condition: str = Query(...),
    inspection_notes: str = Query(""),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:inspect"))
):
    """Inspecter un retour reçu."""
    try:
        ret = await service.inspect_return(
            str(return_id), condition, inspection_notes, current_user["id"]
        )
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ReturnNotReceivedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/returns/{return_id}/refund",
    response_model=ReturnResponse,
    summary="Traiter le remboursement"
)
async def process_refund(
    return_id: UUID,
    data: RefundRequest,
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:refund"))
):
    """Traiter le remboursement d'un retour."""
    try:
        ret = await service.process_refund(
            str(return_id),
            data.refund_amount,
            data.refund_method,
            restocking_fee=data.restocking_fee or Decimal("0"),
            refund_reference=data.refund_reference,
            processed_by=current_user["id"]
        )
        return ReturnResponse.model_validate(ret)
    except ReturnNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ReturnAlreadyRefundedError, ReturnRejectedError, ReturnNotReceivedError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/returns",
    response_model=ReturnListResponse,
    summary="Lister les retours"
)
async def list_returns(
    status: Optional[ReturnStatus] = Query(None),
    order_id: Optional[str] = Query(None),
    shipment_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:return:read"))
):
    """Lister les retours."""
    returns, total = await service.list_returns(
        status=status,
        order_id=order_id,
        shipment_id=str(shipment_id) if shipment_id else None,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return ReturnListResponse(
        items=[ReturnResponse.model_validate(r) for r in returns],
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== Statistics Endpoints ====================

@router.get(
    "/stats",
    response_model=ShippingStatsResponse,
    summary="Statistiques d'expédition"
)
async def get_shipping_stats(
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: ShippingService = Depends(get_service),
    current_user: dict = Depends(require_permission("shipping:stats:read"))
):
    """Récupérer les statistiques d'expédition."""
    stats = await service.get_shipping_stats(start_date, end_date)
    return ShippingStatsResponse(**stats)
