"""
AZALSCORE Delivery Notes Router V3
===================================

Endpoints REST pour les bons de livraison.

Endpoints BL:
- GET  /v3/production/delivery/notes - Liste BL
- POST /v3/production/delivery/notes - Créer BL
- GET  /v3/production/delivery/notes/{id} - Détails BL
- POST /v3/production/delivery/notes/{id}/confirm - Confirmer
- POST /v3/production/delivery/notes/{id}/cancel - Annuler

Endpoints Picking:
- POST /v3/production/delivery/notes/{id}/picking - Créer picking
- GET  /v3/production/delivery/picking - Liste picking
- GET  /v3/production/delivery/picking/{id} - Détails picking
- POST /v3/production/delivery/picking/{id}/start - Démarrer
- POST /v3/production/delivery/picking/{id}/pick - Picker ligne
- POST /v3/production/delivery/picking/{id}/complete - Terminer

Endpoints Expédition:
- POST /v3/production/delivery/notes/{id}/ship - Expédier
- GET  /v3/production/delivery/shipments - Liste expéditions
- GET  /v3/production/delivery/shipments/{id} - Détails
- POST /v3/production/delivery/shipments/{id}/update - Maj statut
- POST /v3/production/delivery/shipments/{id}/deliver - Confirmer livraison
"""
from __future__ import annotations


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
    DeliveryService,
    DeliveryNote,
    DeliveryLine,
    PickingList,
    Shipment,
    DeliveryStatus,
    ShipmentStatus,
    PickingStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/production/delivery", tags=["Production Delivery"])


# =============================================================================
# SCHEMAS
# =============================================================================


class DeliveryLineInput(BaseModel):
    """Ligne de BL en entrée."""
    product_id: str
    product_name: str = ""
    quantity: Decimal = Field(..., gt=0)
    unit: str = "unit"
    lot_id: Optional[str] = None
    lot_number: Optional[str] = None
    location_id: Optional[str] = None


class CreateDeliveryNoteRequest(BaseModel):
    """Requête création BL."""
    customer_id: str
    customer_name: str
    lines: list[DeliveryLineInput]
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str = "FR"
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None


class DeliveryLineResponse(BaseModel):
    """Ligne de BL en réponse."""
    id: str
    product_id: str
    product_name: str
    quantity_ordered: Decimal
    quantity_shipped: Decimal
    quantity_delivered: Decimal
    quantity_remaining: Decimal
    unit: str
    lot_number: Optional[str]
    is_complete: bool


class DeliveryNoteResponse(BaseModel):
    """Réponse BL."""
    id: str
    delivery_number: str
    order_id: Optional[str]
    order_number: Optional[str]
    customer_id: str
    customer_name: str
    status: str
    lines: list[DeliveryLineResponse]
    total_items: int
    total_quantity: Decimal
    shipped_quantity: Decimal
    completion_rate: Decimal
    shipping_address: Optional[str]
    shipping_city: Optional[str]
    shipping_postal_code: Optional[str]
    scheduled_date: Optional[str]
    shipped_date: Optional[str]
    delivered_date: Optional[str]
    carrier_name: Optional[str]
    tracking_number: Optional[str]
    created_at: str


class CreatePickingRequest(BaseModel):
    """Requête création picking."""
    assigned_to: Optional[str] = None


class PickLineRequest(BaseModel):
    """Requête pick ligne."""
    line_id: str
    quantity_picked: Decimal = Field(..., ge=0)
    picker_id: Optional[str] = None


class PickingLineResponse(BaseModel):
    """Ligne picking en réponse."""
    id: str
    product_id: str
    product_name: str
    location_name: str
    quantity_to_pick: Decimal
    quantity_picked: Decimal
    lot_number: Optional[str]
    picked_at: Optional[str]


class PickingListResponse(BaseModel):
    """Réponse picking."""
    id: str
    picking_number: str
    delivery_note_id: str
    delivery_number: str
    status: str
    lines: list[PickingLineResponse]
    progress: Decimal
    assigned_to: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class ShipRequest(BaseModel):
    """Requête expédition."""
    carrier_id: str
    carrier_name: str
    tracking_number: str
    weight_kg: Decimal = Field(Decimal("0"), ge=0)
    packages_count: int = Field(1, ge=1)
    shipping_cost: Decimal = Field(Decimal("0"), ge=0)
    estimated_delivery: Optional[date] = None


class UpdateShipmentRequest(BaseModel):
    """Requête maj statut expédition."""
    status: ShipmentStatus
    location: Optional[str] = None
    message: Optional[str] = None


class ConfirmDeliveryRequest(BaseModel):
    """Requête confirmation livraison."""
    signature: Optional[str] = None
    proof_url: Optional[str] = None


class ShipmentResponse(BaseModel):
    """Réponse expédition."""
    id: str
    shipment_number: str
    delivery_note_id: str
    delivery_number: str
    carrier_id: str
    carrier_name: str
    tracking_number: str
    status: str
    shipped_at: Optional[str]
    estimated_delivery: Optional[str]
    actual_delivery: Optional[str]
    signature: Optional[str]
    weight_kg: Decimal
    packages_count: int
    shipping_cost: Decimal
    tracking_history: list[dict]


class CancelRequest(BaseModel):
    """Requête annulation."""
    reason: Optional[str] = None


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_delivery_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> DeliveryService:
    """Dépendance pour obtenir le service Delivery."""
    return DeliveryService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def note_to_response(note: DeliveryNote) -> DeliveryNoteResponse:
    """Convertit un BL en réponse."""
    return DeliveryNoteResponse(
        id=note.id,
        delivery_number=note.delivery_number,
        order_id=note.order_id,
        order_number=note.order_number,
        customer_id=note.customer_id,
        customer_name=note.customer_name,
        status=note.status.value,
        lines=[
            DeliveryLineResponse(
                id=line.id,
                product_id=line.product_id,
                product_name=line.product_name,
                quantity_ordered=line.quantity_ordered,
                quantity_shipped=line.quantity_shipped,
                quantity_delivered=line.quantity_delivered,
                quantity_remaining=line.quantity_remaining,
                unit=line.unit,
                lot_number=line.lot_number,
                is_complete=line.is_complete,
            )
            for line in note.lines
        ],
        total_items=note.total_items,
        total_quantity=note.total_quantity,
        shipped_quantity=note.shipped_quantity,
        completion_rate=note.completion_rate,
        shipping_address=note.shipping_address,
        shipping_city=note.shipping_city,
        shipping_postal_code=note.shipping_postal_code,
        scheduled_date=note.scheduled_date.isoformat() if note.scheduled_date else None,
        shipped_date=note.shipped_date.isoformat() if note.shipped_date else None,
        delivered_date=note.delivered_date.isoformat() if note.delivered_date else None,
        carrier_name=note.carrier_name,
        tracking_number=note.tracking_number,
        created_at=note.created_at.isoformat(),
    )


def picking_to_response(picking: PickingList) -> PickingListResponse:
    """Convertit un picking en réponse."""
    return PickingListResponse(
        id=picking.id,
        picking_number=picking.picking_number,
        delivery_note_id=picking.delivery_note_id,
        delivery_number=picking.delivery_number,
        status=picking.status.value,
        lines=[
            PickingLineResponse(
                id=line.id,
                product_id=line.product_id,
                product_name=line.product_name,
                location_name=line.location_name,
                quantity_to_pick=line.quantity_to_pick,
                quantity_picked=line.quantity_picked,
                lot_number=line.lot_number,
                picked_at=line.picked_at.isoformat() if line.picked_at else None,
            )
            for line in picking.lines
        ],
        progress=picking.progress,
        assigned_to=picking.assigned_to,
        started_at=picking.started_at.isoformat() if picking.started_at else None,
        completed_at=picking.completed_at.isoformat() if picking.completed_at else None,
    )


def shipment_to_response(shipment: Shipment) -> ShipmentResponse:
    """Convertit une expédition en réponse."""
    return ShipmentResponse(
        id=shipment.id,
        shipment_number=shipment.shipment_number,
        delivery_note_id=shipment.delivery_note_id,
        delivery_number=shipment.delivery_number,
        carrier_id=shipment.carrier_id,
        carrier_name=shipment.carrier_name,
        tracking_number=shipment.tracking_number,
        status=shipment.status.value,
        shipped_at=shipment.shipped_at.isoformat() if shipment.shipped_at else None,
        estimated_delivery=shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
        actual_delivery=shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
        signature=shipment.signature,
        weight_kg=shipment.weight_kg,
        packages_count=shipment.packages_count,
        shipping_cost=shipment.shipping_cost,
        tracking_history=shipment.tracking_history,
    )


# =============================================================================
# ENDPOINTS - DELIVERY NOTES
# =============================================================================


@router.get(
    "/notes",
    response_model=list[DeliveryNoteResponse],
    summary="Liste des bons de livraison",
)
async def list_delivery_notes(
    status: Optional[DeliveryStatus] = Query(None),
    customer_id: Optional[str] = Query(None),
    order_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Liste les bons de livraison."""
    notes = await service.list_delivery_notes(
        status=status,
        customer_id=customer_id,
        order_id=order_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [note_to_response(n) for n in notes]


@router.post(
    "/notes",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un bon de livraison",
)
async def create_delivery_note(
    request: CreateDeliveryNoteRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Crée un nouveau bon de livraison."""
    note = await service.create_delivery_note(
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        lines=[line.model_dump() for line in request.lines],
        order_id=request.order_id,
        order_number=request.order_number,
        shipping_address=request.shipping_address,
        shipping_city=request.shipping_city,
        shipping_postal_code=request.shipping_postal_code,
        shipping_country=request.shipping_country,
        contact_name=request.contact_name,
        contact_phone=request.contact_phone,
        scheduled_date=request.scheduled_date,
        notes=request.notes,
    )
    return note_to_response(note)


@router.get(
    "/notes/{note_id}",
    response_model=DeliveryNoteResponse,
    summary="Détails d'un bon de livraison",
)
async def get_delivery_note(
    note_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Récupère les détails d'un BL."""
    note = await service.get_delivery_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Bon de livraison non trouvé")
    return note_to_response(note)


@router.post(
    "/notes/{note_id}/confirm",
    response_model=DeliveryNoteResponse,
    summary="Confirmer un BL",
)
async def confirm_delivery_note(
    note_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Confirme un bon de livraison."""
    note = await service.confirm_delivery_note(note_id)
    if not note:
        raise HTTPException(status_code=400, detail="Impossible de confirmer ce BL")
    return note_to_response(note)


@router.post(
    "/notes/{note_id}/cancel",
    response_model=DeliveryNoteResponse,
    summary="Annuler un BL",
)
async def cancel_delivery_note(
    note_id: str,
    request: CancelRequest = CancelRequest(),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Annule un bon de livraison."""
    note = await service.cancel_delivery_note(note_id, request.reason)
    if not note:
        raise HTTPException(status_code=400, detail="Impossible d'annuler ce BL")
    return note_to_response(note)


# =============================================================================
# ENDPOINTS - PICKING
# =============================================================================


@router.post(
    "/notes/{note_id}/picking",
    response_model=PickingListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une liste de picking",
)
async def create_picking_list(
    note_id: str,
    request: CreatePickingRequest = CreatePickingRequest(),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Crée une liste de picking pour un BL."""
    picking = await service.create_picking_list(note_id, request.assigned_to)
    if not picking:
        raise HTTPException(status_code=400, detail="Impossible de créer le picking")
    return picking_to_response(picking)


@router.get(
    "/picking",
    response_model=list[PickingListResponse],
    summary="Liste des pickings",
)
async def list_picking_lists(
    status: Optional[PickingStatus] = Query(None),
    assigned_to: Optional[str] = Query(None),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Liste les listes de picking."""
    pickings = await service.list_picking_lists(status=status, assigned_to=assigned_to)
    return [picking_to_response(p) for p in pickings]


@router.get(
    "/picking/{picking_id}",
    response_model=PickingListResponse,
    summary="Détails d'un picking",
)
async def get_picking_list(
    picking_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Récupère les détails d'un picking."""
    picking = await service.get_picking_list(picking_id)
    if not picking:
        raise HTTPException(status_code=404, detail="Picking non trouvé")
    return picking_to_response(picking)


@router.post(
    "/picking/{picking_id}/start",
    response_model=PickingListResponse,
    summary="Démarrer le picking",
)
async def start_picking(
    picking_id: str,
    picker_id: str = Query(...),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Démarre le picking."""
    picking = await service.start_picking(picking_id, picker_id)
    if not picking:
        raise HTTPException(status_code=400, detail="Impossible de démarrer")
    return picking_to_response(picking)


@router.post(
    "/picking/{picking_id}/pick",
    response_model=PickingListResponse,
    summary="Picker une ligne",
)
async def pick_line(
    picking_id: str,
    request: PickLineRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Confirme le picking d'une ligne."""
    picking = await service.pick_line(
        picking_id=picking_id,
        line_id=request.line_id,
        quantity_picked=request.quantity_picked,
        picker_id=request.picker_id,
    )
    if not picking:
        raise HTTPException(status_code=400, detail="Impossible de picker")
    return picking_to_response(picking)


@router.post(
    "/picking/{picking_id}/complete",
    response_model=PickingListResponse,
    summary="Terminer le picking",
)
async def complete_picking(
    picking_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Termine le picking."""
    picking = await service.complete_picking(picking_id)
    if not picking:
        raise HTTPException(status_code=400, detail="Picking non trouvé")
    return picking_to_response(picking)


# =============================================================================
# ENDPOINTS - SHIPPING
# =============================================================================


@router.post(
    "/notes/{note_id}/ship",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Expédier un BL",
)
async def ship_delivery_note(
    note_id: str,
    request: ShipRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Expédie un bon de livraison."""
    shipment = await service.ship(
        note_id=note_id,
        carrier_id=request.carrier_id,
        carrier_name=request.carrier_name,
        tracking_number=request.tracking_number,
        weight_kg=request.weight_kg,
        packages_count=request.packages_count,
        shipping_cost=request.shipping_cost,
        estimated_delivery=request.estimated_delivery,
    )
    if not shipment:
        raise HTTPException(status_code=400, detail="Impossible d'expédier")
    return shipment_to_response(shipment)


@router.get(
    "/shipments",
    response_model=list[ShipmentResponse],
    summary="Liste des expéditions",
)
async def list_shipments(
    status: Optional[ShipmentStatus] = Query(None),
    carrier_id: Optional[str] = Query(None),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Liste les expéditions."""
    shipments = await service.list_shipments(status=status, carrier_id=carrier_id)
    return [shipment_to_response(s) for s in shipments]


@router.get(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    summary="Détails d'une expédition",
)
async def get_shipment(
    shipment_id: str,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Récupère les détails d'une expédition."""
    shipment = await service.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition non trouvée")
    return shipment_to_response(shipment)


@router.post(
    "/shipments/{shipment_id}/update",
    response_model=ShipmentResponse,
    summary="Mettre à jour le statut",
)
async def update_shipment_status(
    shipment_id: str,
    request: UpdateShipmentRequest,
    service: DeliveryService = Depends(get_delivery_service),
):
    """Met à jour le statut d'expédition."""
    shipment = await service.update_shipment_status(
        shipment_id=shipment_id,
        status=request.status,
        location=request.location,
        message=request.message,
    )
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition non trouvée")
    return shipment_to_response(shipment)


@router.post(
    "/shipments/{shipment_id}/deliver",
    response_model=ShipmentResponse,
    summary="Confirmer la livraison",
)
async def confirm_delivery(
    shipment_id: str,
    request: ConfirmDeliveryRequest = ConfirmDeliveryRequest(),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Confirme la livraison."""
    shipment = await service.confirm_delivery(
        shipment_id=shipment_id,
        signature=request.signature,
        proof_url=request.proof_url,
    )
    if not shipment:
        raise HTTPException(status_code=404, detail="Expédition non trouvée")
    return shipment_to_response(shipment)


# =============================================================================
# ENDPOINTS - STATS & HEALTH
# =============================================================================


@router.get(
    "/stats",
    summary="Statistiques des livraisons",
)
async def get_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: DeliveryService = Depends(get_delivery_service),
):
    """Statistiques des livraisons."""
    return await service.get_statistics(start_date, end_date)


@router.get(
    "/health",
    summary="Health check Delivery",
)
async def health_check():
    """Health check du service Delivery."""
    return {
        "status": "healthy",
        "service": "production-delivery",
        "features": [
            "delivery_notes",
            "picking_lists",
            "shipments",
            "tracking",
            "proof_of_delivery",
        ],
        "delivery_statuses": [s.value for s in DeliveryStatus],
        "shipment_statuses": [s.value for s in ShipmentStatus],
    }
