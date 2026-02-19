"""
AZALSCORE Traceability Router V3
=================================

Endpoints REST pour la traçabilité lots et séries.

Endpoints Lots:
- GET  /v3/production/traceability/lots - Liste lots
- POST /v3/production/traceability/lots - Créer lot
- GET  /v3/production/traceability/lots/{id} - Détails lot
- POST /v3/production/traceability/lots/{id}/consume - Consommer
- POST /v3/production/traceability/lots/{id}/transfer - Transférer
- POST /v3/production/traceability/lots/{id}/quarantine - Quarantaine
- POST /v3/production/traceability/lots/{id}/release - Libérer
- GET  /v3/production/traceability/lots/expiring - Lots expirant

Endpoints Séries:
- GET  /v3/production/traceability/serials - Liste séries
- POST /v3/production/traceability/serials - Créer série
- POST /v3/production/traceability/serials/batch - Créer lot de séries
- GET  /v3/production/traceability/serials/{id} - Détails série
- POST /v3/production/traceability/serials/{id}/sell - Vendre
- POST /v3/production/traceability/serials/{id}/return - Retourner
- POST /v3/production/traceability/serials/{id}/defective - Défectueux

Endpoints Traçabilité:
- GET  /v3/production/traceability/lots/{id}/movements - Historique lot
- GET  /v3/production/traceability/serials/{id}/movements - Historique série
- GET  /v3/production/traceability/chain - Chaîne complète
- POST /v3/production/traceability/recall - Initier rappel
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    TraceabilityService,
    Lot,
    SerialNumber,
    TraceabilityMovement,
    LotStatus,
    SerialStatus,
    MovementType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/production/traceability", tags=["Production Traceability"])


# =============================================================================
# SCHEMAS
# =============================================================================


class CreateLotRequest(BaseModel):
    """Requête création lot."""
    product_id: str
    product_name: str
    quantity: Decimal = Field(..., gt=0)
    unit: str = "unit"
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_lot: Optional[str] = None
    supplier_id: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    notes: Optional[str] = None


class LotResponse(BaseModel):
    """Réponse lot."""
    id: str
    lot_number: str
    product_id: str
    product_name: str
    initial_quantity: Decimal
    current_quantity: Decimal
    consumed_quantity: Decimal
    unit: str
    status: str
    manufacturing_date: Optional[str]
    expiry_date: Optional[str]
    is_expired: bool
    days_until_expiry: Optional[int]
    supplier_lot: Optional[str]
    location_id: Optional[str]
    location_name: Optional[str]
    created_at: str


class ConsumeLotRequest(BaseModel):
    """Requête consommation lot."""
    quantity: Decimal = Field(..., gt=0)
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    operator_id: Optional[str] = None
    notes: Optional[str] = None


class TransferLotRequest(BaseModel):
    """Requête transfert lot."""
    quantity: Decimal = Field(..., gt=0)
    to_location_id: str
    to_location_name: Optional[str] = None
    operator_id: Optional[str] = None


class QuarantineRequest(BaseModel):
    """Requête quarantaine."""
    reason: str


class CreateSerialRequest(BaseModel):
    """Requête création série."""
    product_id: str
    product_name: str
    serial_number: Optional[str] = None
    lot_id: Optional[str] = None
    manufacturing_date: Optional[date] = None
    warranty_months: int = Field(12, ge=0)
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    notes: Optional[str] = None


class CreateSerialBatchRequest(BaseModel):
    """Requête création lot de séries."""
    product_id: str
    product_name: str
    quantity: int = Field(..., gt=0, le=1000)
    lot_id: Optional[str] = None
    prefix: Optional[str] = None
    manufacturing_date: Optional[date] = None
    warranty_months: int = Field(12, ge=0)
    location_id: Optional[str] = None
    location_name: Optional[str] = None


class SerialResponse(BaseModel):
    """Réponse série."""
    id: str
    serial_number: str
    product_id: str
    product_name: str
    lot_id: Optional[str]
    lot_number: Optional[str]
    status: str
    manufacturing_date: Optional[str]
    warranty_end: Optional[str]
    is_under_warranty: bool
    location_id: Optional[str]
    location_name: Optional[str]
    customer_id: Optional[str]
    customer_name: Optional[str]
    created_at: str


class SellSerialRequest(BaseModel):
    """Requête vente série."""
    customer_id: str
    customer_name: str
    reference_id: Optional[str] = None


class ReturnSerialRequest(BaseModel):
    """Requête retour série."""
    location_id: str
    reason: Optional[str] = None


class DefectiveRequest(BaseModel):
    """Requête défaut."""
    reason: str


class MovementResponse(BaseModel):
    """Réponse mouvement."""
    id: str
    movement_type: str
    lot_number: Optional[str]
    serial_number: Optional[str]
    product_id: str
    product_name: str
    quantity: Decimal
    from_location_id: Optional[str]
    to_location_id: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[str]
    timestamp: str


class TraceabilityChainResponse(BaseModel):
    """Réponse chaîne de traçabilité."""
    product_id: str
    product_name: str
    lot_id: Optional[str]
    serial_id: Optional[str]
    upstream: list[MovementResponse]
    downstream: list[MovementResponse]


class RecallRequest(BaseModel):
    """Requête rappel."""
    lot_ids: Optional[list[str]] = None
    serial_ids: Optional[list[str]] = None
    reason: str


class RecallResponse(BaseModel):
    """Réponse rappel."""
    id: str
    reason: str
    affected_lots: list[str]
    affected_serials: list[str]
    customers_affected: list[str]
    total_quantity: Decimal
    created_at: str


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_traceability_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> TraceabilityService:
    """Dépendance pour obtenir le service Traceability."""
    return TraceabilityService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def lot_to_response(lot: Lot) -> LotResponse:
    """Convertit un lot en réponse."""
    return LotResponse(
        id=lot.id,
        lot_number=lot.lot_number,
        product_id=lot.product_id,
        product_name=lot.product_name,
        initial_quantity=lot.initial_quantity,
        current_quantity=lot.current_quantity,
        consumed_quantity=lot.consumed_quantity,
        unit=lot.unit,
        status=lot.status.value,
        manufacturing_date=lot.manufacturing_date.isoformat() if lot.manufacturing_date else None,
        expiry_date=lot.expiry_date.isoformat() if lot.expiry_date else None,
        is_expired=lot.is_expired,
        days_until_expiry=lot.days_until_expiry,
        supplier_lot=lot.supplier_lot,
        location_id=lot.location_id,
        location_name=lot.location_name,
        created_at=lot.created_at.isoformat(),
    )


def serial_to_response(serial: SerialNumber) -> SerialResponse:
    """Convertit une série en réponse."""
    return SerialResponse(
        id=serial.id,
        serial_number=serial.serial_number,
        product_id=serial.product_id,
        product_name=serial.product_name,
        lot_id=serial.lot_id,
        lot_number=serial.lot_number,
        status=serial.status.value,
        manufacturing_date=serial.manufacturing_date.isoformat() if serial.manufacturing_date else None,
        warranty_end=serial.warranty_end.isoformat() if serial.warranty_end else None,
        is_under_warranty=serial.is_under_warranty,
        location_id=serial.location_id,
        location_name=serial.location_name,
        customer_id=serial.customer_id,
        customer_name=serial.customer_name,
        created_at=serial.created_at.isoformat(),
    )


def movement_to_response(movement: TraceabilityMovement) -> MovementResponse:
    """Convertit un mouvement en réponse."""
    return MovementResponse(
        id=movement.id,
        movement_type=movement.movement_type.value,
        lot_number=movement.lot_number,
        serial_number=movement.serial_number,
        product_id=movement.product_id,
        product_name=movement.product_name,
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        reference_type=movement.reference_type,
        reference_id=movement.reference_id,
        timestamp=movement.timestamp.isoformat(),
    )


# =============================================================================
# ENDPOINTS - LOTS
# =============================================================================


@router.get(
    "/lots",
    response_model=list[LotResponse],
    summary="Liste des lots",
)
async def list_lots(
    product_id: Optional[str] = Query(None),
    status: Optional[LotStatus] = Query(None),
    location_id: Optional[str] = Query(None),
    include_empty: bool = Query(False),
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Liste les lots avec filtres."""
    lots = await service.list_lots(
        product_id=product_id,
        status=status,
        location_id=location_id,
        include_empty=include_empty,
    )
    return [lot_to_response(l) for l in lots]


@router.post(
    "/lots",
    response_model=LotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un lot",
)
async def create_lot(
    request: CreateLotRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Crée un nouveau lot."""
    lot = await service.create_lot(
        product_id=request.product_id,
        product_name=request.product_name,
        quantity=request.quantity,
        unit=request.unit,
        manufacturing_date=request.manufacturing_date,
        expiry_date=request.expiry_date,
        supplier_lot=request.supplier_lot,
        supplier_id=request.supplier_id,
        location_id=request.location_id,
        location_name=request.location_name,
        notes=request.notes,
    )
    return lot_to_response(lot)


@router.get(
    "/lots/expiring",
    response_model=list[LotResponse],
    summary="Lots expirant bientôt",
)
async def get_expiring_lots(
    days: int = Query(30, ge=1, le=365),
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Liste les lots expirant dans les X jours."""
    lots = await service.check_expiring_lots(days=days)
    return [lot_to_response(l) for l in lots]


@router.get(
    "/lots/{lot_id}",
    response_model=LotResponse,
    summary="Détails d'un lot",
)
async def get_lot(
    lot_id: str,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Récupère les détails d'un lot."""
    lot = await service.get_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot non trouvé")
    return lot_to_response(lot)


@router.post(
    "/lots/{lot_id}/consume",
    response_model=LotResponse,
    summary="Consommer du lot",
)
async def consume_lot(
    lot_id: str,
    request: ConsumeLotRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Consomme une quantité du lot."""
    try:
        lot = await service.consume_lot(
            lot_id=lot_id,
            quantity=request.quantity,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            operator_id=request.operator_id,
            notes=request.notes,
        )
        if not lot:
            raise HTTPException(status_code=404, detail="Lot non trouvé")
        return lot_to_response(lot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/lots/{lot_id}/transfer",
    response_model=LotResponse,
    summary="Transférer du lot",
)
async def transfer_lot(
    lot_id: str,
    request: TransferLotRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Transfère une quantité du lot."""
    try:
        lot = await service.transfer_lot(
            lot_id=lot_id,
            quantity=request.quantity,
            to_location_id=request.to_location_id,
            to_location_name=request.to_location_name,
            operator_id=request.operator_id,
        )
        if not lot:
            raise HTTPException(status_code=404, detail="Lot non trouvé")
        return lot_to_response(lot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/lots/{lot_id}/quarantine",
    response_model=LotResponse,
    summary="Mettre en quarantaine",
)
async def quarantine_lot(
    lot_id: str,
    request: QuarantineRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Met un lot en quarantaine."""
    lot = await service.quarantine_lot(lot_id, request.reason)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot non trouvé")
    return lot_to_response(lot)


@router.post(
    "/lots/{lot_id}/release",
    response_model=LotResponse,
    summary="Libérer de quarantaine",
)
async def release_lot(
    lot_id: str,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Libère un lot de quarantaine."""
    lot = await service.release_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot non trouvé ou pas en quarantaine")
    return lot_to_response(lot)


@router.get(
    "/lots/{lot_id}/movements",
    response_model=list[MovementResponse],
    summary="Historique du lot",
)
async def get_lot_movements(
    lot_id: str,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Récupère l'historique des mouvements d'un lot."""
    movements = await service.get_lot_movements(lot_id)
    return [movement_to_response(m) for m in movements]


# =============================================================================
# ENDPOINTS - SERIALS
# =============================================================================


@router.get(
    "/serials",
    response_model=list[SerialResponse],
    summary="Liste des numéros de série",
)
async def list_serials(
    product_id: Optional[str] = Query(None),
    lot_id: Optional[str] = Query(None),
    status: Optional[SerialStatus] = Query(None),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Liste les numéros de série avec filtres."""
    serials = await service.list_serials(
        product_id=product_id,
        lot_id=lot_id,
        status=status,
        customer_id=customer_id,
        location_id=location_id,
    )
    return [serial_to_response(s) for s in serials]


@router.post(
    "/serials",
    response_model=SerialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un numéro de série",
)
async def create_serial(
    request: CreateSerialRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Crée un nouveau numéro de série."""
    serial = await service.create_serial(
        product_id=request.product_id,
        product_name=request.product_name,
        serial_number=request.serial_number,
        lot_id=request.lot_id,
        manufacturing_date=request.manufacturing_date,
        warranty_months=request.warranty_months,
        location_id=request.location_id,
        location_name=request.location_name,
        notes=request.notes,
    )
    return serial_to_response(serial)


@router.post(
    "/serials/batch",
    response_model=list[SerialResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Créer plusieurs numéros de série",
)
async def create_serial_batch(
    request: CreateSerialBatchRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Crée plusieurs numéros de série en lot."""
    serials = await service.create_serial_batch(
        product_id=request.product_id,
        product_name=request.product_name,
        quantity=request.quantity,
        lot_id=request.lot_id,
        prefix=request.prefix,
        manufacturing_date=request.manufacturing_date,
        warranty_months=request.warranty_months,
        location_id=request.location_id,
        location_name=request.location_name,
    )
    return [serial_to_response(s) for s in serials]


@router.get(
    "/serials/{serial_id}",
    response_model=SerialResponse,
    summary="Détails d'un numéro de série",
)
async def get_serial(
    serial_id: str,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Récupère les détails d'un numéro de série."""
    serial = await service.get_serial(serial_id)
    if not serial:
        raise HTTPException(status_code=404, detail="Numéro de série non trouvé")
    return serial_to_response(serial)


@router.post(
    "/serials/{serial_id}/sell",
    response_model=SerialResponse,
    summary="Vendre un article",
)
async def sell_serial(
    serial_id: str,
    request: SellSerialRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Marque un numéro de série comme vendu."""
    serial = await service.sell_serial(
        serial_id=serial_id,
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        reference_id=request.reference_id,
    )
    if not serial:
        raise HTTPException(status_code=400, detail="Série non disponible ou non trouvée")
    return serial_to_response(serial)


@router.post(
    "/serials/{serial_id}/return",
    response_model=SerialResponse,
    summary="Retourner un article",
)
async def return_serial(
    serial_id: str,
    request: ReturnSerialRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Enregistre un retour."""
    serial = await service.return_serial(
        serial_id=serial_id,
        location_id=request.location_id,
        reason=request.reason,
    )
    if not serial:
        raise HTTPException(status_code=400, detail="Retour impossible")
    return serial_to_response(serial)


@router.post(
    "/serials/{serial_id}/defective",
    response_model=SerialResponse,
    summary="Marquer comme défectueux",
)
async def mark_defective(
    serial_id: str,
    request: DefectiveRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Marque un numéro de série comme défectueux."""
    serial = await service.mark_defective(serial_id, request.reason)
    if not serial:
        raise HTTPException(status_code=404, detail="Numéro de série non trouvé")
    return serial_to_response(serial)


@router.get(
    "/serials/{serial_id}/movements",
    response_model=list[MovementResponse],
    summary="Historique de la série",
)
async def get_serial_movements(
    serial_id: str,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Récupère l'historique des mouvements d'un numéro de série."""
    movements = await service.get_serial_movements(serial_id)
    return [movement_to_response(m) for m in movements]


# =============================================================================
# ENDPOINTS - TRACEABILITY
# =============================================================================


@router.get(
    "/chain",
    response_model=TraceabilityChainResponse,
    summary="Chaîne de traçabilité",
)
async def get_traceability_chain(
    lot_id: Optional[str] = Query(None),
    serial_id: Optional[str] = Query(None),
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Récupère la chaîne de traçabilité complète."""
    if not lot_id and not serial_id:
        raise HTTPException(status_code=400, detail="lot_id ou serial_id requis")

    chain = await service.get_traceability_chain(lot_id=lot_id, serial_id=serial_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Élément non trouvé")

    return TraceabilityChainResponse(
        product_id=chain.product_id,
        product_name=chain.product_name,
        lot_id=chain.lot_id,
        serial_id=chain.serial_id,
        upstream=[movement_to_response(m) for m in chain.upstream],
        downstream=[movement_to_response(m) for m in chain.downstream],
    )


@router.post(
    "/recall",
    response_model=RecallResponse,
    summary="Initier un rappel",
)
async def initiate_recall(
    request: RecallRequest,
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Initie un rappel produit."""
    if not request.lot_ids and not request.serial_ids:
        raise HTTPException(status_code=400, detail="lot_ids ou serial_ids requis")

    report = await service.initiate_recall(
        lot_ids=request.lot_ids,
        serial_ids=request.serial_ids,
        reason=request.reason,
    )

    return RecallResponse(
        id=report.id,
        reason=report.reason,
        affected_lots=report.affected_lots,
        affected_serials=report.affected_serials,
        customers_affected=report.customers_affected,
        total_quantity=report.total_quantity,
        created_at=report.created_at.isoformat(),
    )


# =============================================================================
# ENDPOINTS - STATS & HEALTH
# =============================================================================


@router.get(
    "/stats",
    summary="Statistiques de traçabilité",
)
async def get_stats(
    service: TraceabilityService = Depends(get_traceability_service),
):
    """Statistiques de traçabilité."""
    return await service.get_statistics()


@router.get(
    "/health",
    summary="Health check Traceability",
)
async def health_check():
    """Health check du service Traceability."""
    return {
        "status": "healthy",
        "service": "production-traceability",
        "features": [
            "lot_management",
            "serial_numbers",
            "expiry_tracking",
            "traceability_chain",
            "recall_management",
        ],
        "lot_statuses": [s.value for s in LotStatus],
        "serial_statuses": [s.value for s in SerialStatus],
        "movement_types": [m.value for m in MovementType],
    }
