"""
WMS Router - API REST V3
========================

Endpoints pour la gestion d'entrepôt.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .service import (
    WMSService,
    LocationType,
    MovementType,
    CountStatus,
    WaveStatus,
)


router = APIRouter(prefix="/v3/production/wms", tags=["WMS"])


# ========================
# SCHEMAS
# ========================

class WarehouseCreate(BaseModel):
    """Création d'entrepôt."""
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    address: Optional[str] = None
    metadata: Optional[dict] = None


class WarehouseResponse(BaseModel):
    """Réponse entrepôt."""
    id: str
    code: str
    name: str
    address: Optional[str]
    is_active: bool
    created_at: datetime


class LocationCreate(BaseModel):
    """Création d'emplacement."""
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    location_type: LocationType
    parent_id: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None


class LocationUpdate(BaseModel):
    """Mise à jour d'emplacement."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_pickable: Optional[bool] = None
    is_receivable: Optional[bool] = None
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None


class LocationResponse(BaseModel):
    """Réponse emplacement."""
    id: str
    warehouse_id: str
    code: str
    name: str
    location_type: LocationType
    full_code: str
    is_active: bool
    is_pickable: bool
    is_receivable: bool


class MovementCreate(BaseModel):
    """Création de mouvement."""
    movement_type: MovementType
    product_id: str
    quantity: float = Field(..., gt=0)
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    lot_id: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class MovementResponse(BaseModel):
    """Réponse mouvement."""
    id: str
    movement_type: MovementType
    product_id: str
    quantity: float
    from_location_id: Optional[str]
    to_location_id: Optional[str]
    lot_id: Optional[str]
    reference: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


class TransferRequest(BaseModel):
    """Requête de transfert."""
    from_location_id: str
    to_location_id: str
    product_id: str
    quantity: float = Field(..., gt=0)
    lot_id: Optional[str] = None
    reference: Optional[str] = None


class ReceiptRequest(BaseModel):
    """Requête de réception."""
    location_id: str
    product_id: str
    quantity: float = Field(..., gt=0)
    lot_id: Optional[str] = None
    reference: Optional[str] = None


class PickRequest(BaseModel):
    """Requête de prélèvement."""
    location_id: str
    product_id: str
    quantity: float = Field(..., gt=0)
    lot_id: Optional[str] = None
    reference: Optional[str] = None


class InventoryCountCreate(BaseModel):
    """Création de comptage."""
    name: str = Field(..., min_length=1)
    locations: Optional[list[str]] = None
    scheduled_date: Optional[datetime] = None


class CountRecordRequest(BaseModel):
    """Enregistrement de comptage."""
    location_id: str
    product_id: str
    counted_qty: float


class InventoryCountResponse(BaseModel):
    """Réponse comptage."""
    id: str
    warehouse_id: str
    name: str
    status: CountStatus
    scheduled_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    location_count: int


class WaveCreate(BaseModel):
    """Création de vague."""
    name: str = Field(..., min_length=1)
    order_ids: Optional[list[str]] = None


class WaveAddOrders(BaseModel):
    """Ajout de commandes à une vague."""
    order_ids: list[str]


class WaveResponse(BaseModel):
    """Réponse vague."""
    id: str
    warehouse_id: str
    name: str
    status: WaveStatus
    order_count: int
    pick_count: int
    picked_count: int
    progress: float
    created_at: datetime
    released_at: Optional[datetime]
    completed_at: Optional[datetime]


class ReplenishmentRuleCreate(BaseModel):
    """Création de règle de réappro."""
    product_id: str
    location_id: str
    min_qty: float = Field(..., ge=0)
    max_qty: float = Field(..., gt=0)
    reorder_qty: float = Field(..., gt=0)
    source_location_id: Optional[str] = None


class ReplenishmentNeed(BaseModel):
    """Besoin de réapprovisionnement."""
    rule_id: str
    product_id: str
    location_id: str
    current_qty: float
    min_qty: float
    suggested_qty: float
    source_location_id: Optional[str]


# ========================
# DEPENDENCIES
# ========================

async def get_wms_service(
    tenant_id: str = Query(..., alias="tenant_id")
) -> WMSService:
    """Dépendance pour obtenir le service WMS."""
    return WMSService(db=None, tenant_id=tenant_id)


# ========================
# WAREHOUSE ENDPOINTS
# ========================

@router.post("/warehouses", status_code=201, response_model=WarehouseResponse)
async def create_warehouse(
    data: WarehouseCreate,
    service: WMSService = Depends(get_wms_service)
):
    """Crée un entrepôt."""
    warehouse = await service.create_warehouse(
        code=data.code,
        name=data.name,
        address=data.address,
        metadata=data.metadata
    )
    return WarehouseResponse(
        id=warehouse.id,
        code=warehouse.code,
        name=warehouse.name,
        address=warehouse.address,
        is_active=warehouse.is_active,
        created_at=warehouse.created_at
    )


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    is_active: Optional[bool] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Liste les entrepôts."""
    warehouses = await service.list_warehouses(is_active=is_active)
    return [
        WarehouseResponse(
            id=w.id,
            code=w.code,
            name=w.name,
            address=w.address,
            is_active=w.is_active,
            created_at=w.created_at
        )
        for w in warehouses
    ]


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère un entrepôt."""
    warehouse = await service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return WarehouseResponse(
        id=warehouse.id,
        code=warehouse.code,
        name=warehouse.name,
        address=warehouse.address,
        is_active=warehouse.is_active,
        created_at=warehouse.created_at
    )


# ========================
# LOCATION ENDPOINTS
# ========================

@router.post(
    "/warehouses/{warehouse_id}/locations",
    status_code=201,
    response_model=LocationResponse
)
async def create_location(
    warehouse_id: str,
    data: LocationCreate,
    service: WMSService = Depends(get_wms_service)
):
    """Crée un emplacement."""
    location = await service.create_location(
        warehouse_id=warehouse_id,
        code=data.code,
        name=data.name,
        location_type=data.location_type,
        parent_id=data.parent_id,
        aisle=data.aisle,
        rack=data.rack,
        level=data.level,
        position=data.position,
        max_weight=data.max_weight,
        max_volume=data.max_volume
    )
    return LocationResponse(
        id=location.id,
        warehouse_id=location.warehouse_id,
        code=location.code,
        name=location.name,
        location_type=location.location_type,
        full_code=location.full_code,
        is_active=location.is_active,
        is_pickable=location.is_pickable,
        is_receivable=location.is_receivable
    )


@router.get(
    "/warehouses/{warehouse_id}/locations",
    response_model=list[LocationResponse]
)
async def list_locations(
    warehouse_id: str,
    location_type: Optional[LocationType] = None,
    is_pickable: Optional[bool] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Liste les emplacements."""
    locations = await service.list_locations(
        warehouse_id=warehouse_id,
        location_type=location_type,
        is_pickable=is_pickable
    )
    return [
        LocationResponse(
            id=loc.id,
            warehouse_id=loc.warehouse_id,
            code=loc.code,
            name=loc.name,
            location_type=loc.location_type,
            full_code=loc.full_code,
            is_active=loc.is_active,
            is_pickable=loc.is_pickable,
            is_receivable=loc.is_receivable
        )
        for loc in locations
    ]


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère un emplacement."""
    location = await service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationResponse(
        id=location.id,
        warehouse_id=location.warehouse_id,
        code=location.code,
        name=location.name,
        location_type=location.location_type,
        full_code=location.full_code,
        is_active=location.is_active,
        is_pickable=location.is_pickable,
        is_receivable=location.is_receivable
    )


@router.patch("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    data: LocationUpdate,
    service: WMSService = Depends(get_wms_service)
):
    """Met à jour un emplacement."""
    location = await service.update_location(
        location_id,
        **data.model_dump(exclude_unset=True)
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationResponse(
        id=location.id,
        warehouse_id=location.warehouse_id,
        code=location.code,
        name=location.name,
        location_type=location.location_type,
        full_code=location.full_code,
        is_active=location.is_active,
        is_pickable=location.is_pickable,
        is_receivable=location.is_receivable
    )


# ========================
# STOCK ENDPOINTS
# ========================

@router.get("/locations/{location_id}/stock")
async def get_location_stock(
    location_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère le stock d'un emplacement."""
    stocks = await service.get_location_stock(location_id)
    return [
        {
            "product_id": s.product_id,
            "lot_id": s.lot_id,
            "quantity": s.quantity,
            "reserved_quantity": s.reserved_quantity,
            "available_quantity": s.available_quantity
        }
        for s in stocks
    ]


@router.get("/products/{product_id}/stock")
async def get_product_stock(
    product_id: str,
    warehouse_id: Optional[str] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère le stock d'un produit."""
    stocks = await service.get_product_stock(
        product_id=product_id,
        warehouse_id=warehouse_id
    )
    return [
        {
            "location_id": s.location_id,
            "lot_id": s.lot_id,
            "quantity": s.quantity,
            "reserved_quantity": s.reserved_quantity,
            "available_quantity": s.available_quantity
        }
        for s in stocks
    ]


# ========================
# MOVEMENT ENDPOINTS
# ========================

@router.post("/movements/receive", status_code=201, response_model=MovementResponse)
async def receive_stock(
    data: ReceiptRequest,
    service: WMSService = Depends(get_wms_service)
):
    """Réceptionne du stock."""
    movement = await service.receive(
        location_id=data.location_id,
        product_id=data.product_id,
        quantity=data.quantity,
        lot_id=data.lot_id,
        reference=data.reference
    )
    return MovementResponse(
        id=movement.id,
        movement_type=movement.movement_type,
        product_id=movement.product_id,
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        lot_id=movement.lot_id,
        reference=movement.reference,
        status=movement.status.value,
        created_at=movement.created_at,
        completed_at=movement.completed_at
    )


@router.post("/movements/transfer", status_code=201, response_model=MovementResponse)
async def transfer_stock(
    data: TransferRequest,
    service: WMSService = Depends(get_wms_service)
):
    """Transfère du stock."""
    movement = await service.transfer(
        from_location_id=data.from_location_id,
        to_location_id=data.to_location_id,
        product_id=data.product_id,
        quantity=data.quantity,
        lot_id=data.lot_id,
        reference=data.reference
    )
    return MovementResponse(
        id=movement.id,
        movement_type=movement.movement_type,
        product_id=movement.product_id,
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        lot_id=movement.lot_id,
        reference=movement.reference,
        status=movement.status.value,
        created_at=movement.created_at,
        completed_at=movement.completed_at
    )


@router.post("/movements/pick", status_code=201, response_model=MovementResponse)
async def pick_stock(
    data: PickRequest,
    service: WMSService = Depends(get_wms_service)
):
    """Prélève du stock."""
    movement = await service.pick(
        location_id=data.location_id,
        product_id=data.product_id,
        quantity=data.quantity,
        lot_id=data.lot_id,
        reference=data.reference
    )
    return MovementResponse(
        id=movement.id,
        movement_type=movement.movement_type,
        product_id=movement.product_id,
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        lot_id=movement.lot_id,
        reference=movement.reference,
        status=movement.status.value,
        created_at=movement.created_at,
        completed_at=movement.completed_at
    )


@router.get("/movements", response_model=list[MovementResponse])
async def list_movements(
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    limit: int = Query(default=100, le=500),
    service: WMSService = Depends(get_wms_service)
):
    """Liste les mouvements."""
    movements = await service.list_movements(
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type=movement_type,
        limit=limit
    )
    return [
        MovementResponse(
            id=m.id,
            movement_type=m.movement_type,
            product_id=m.product_id,
            quantity=m.quantity,
            from_location_id=m.from_location_id,
            to_location_id=m.to_location_id,
            lot_id=m.lot_id,
            reference=m.reference,
            status=m.status.value,
            created_at=m.created_at,
            completed_at=m.completed_at
        )
        for m in movements
    ]


# ========================
# INVENTORY COUNT ENDPOINTS
# ========================

@router.post(
    "/warehouses/{warehouse_id}/counts",
    status_code=201,
    response_model=InventoryCountResponse
)
async def create_inventory_count(
    warehouse_id: str,
    data: InventoryCountCreate,
    service: WMSService = Depends(get_wms_service)
):
    """Crée un comptage d'inventaire."""
    count = await service.create_inventory_count(
        warehouse_id=warehouse_id,
        name=data.name,
        locations=data.locations,
        scheduled_date=data.scheduled_date
    )
    return InventoryCountResponse(
        id=count.id,
        warehouse_id=count.warehouse_id,
        name=count.name,
        status=count.status,
        scheduled_date=count.scheduled_date,
        started_at=count.started_at,
        completed_at=count.completed_at,
        location_count=len(count.locations)
    )


@router.get(
    "/warehouses/{warehouse_id}/counts",
    response_model=list[InventoryCountResponse]
)
async def list_inventory_counts(
    warehouse_id: str,
    status: Optional[CountStatus] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Liste les comptages."""
    counts = await service.list_inventory_counts(
        warehouse_id=warehouse_id,
        status=status
    )
    return [
        InventoryCountResponse(
            id=c.id,
            warehouse_id=c.warehouse_id,
            name=c.name,
            status=c.status,
            scheduled_date=c.scheduled_date,
            started_at=c.started_at,
            completed_at=c.completed_at,
            location_count=len(c.locations)
        )
        for c in counts
    ]


@router.post("/counts/{count_id}/start", response_model=InventoryCountResponse)
async def start_inventory_count(
    count_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Démarre un comptage."""
    count = await service.start_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Count not found")
    return InventoryCountResponse(
        id=count.id,
        warehouse_id=count.warehouse_id,
        name=count.name,
        status=count.status,
        scheduled_date=count.scheduled_date,
        started_at=count.started_at,
        completed_at=count.completed_at,
        location_count=len(count.locations)
    )


@router.post("/counts/{count_id}/record")
async def record_count(
    count_id: str,
    data: CountRecordRequest,
    service: WMSService = Depends(get_wms_service)
):
    """Enregistre un comptage."""
    line = await service.record_count(
        count_id=count_id,
        location_id=data.location_id,
        product_id=data.product_id,
        counted_qty=data.counted_qty
    )
    if not line:
        raise HTTPException(status_code=404, detail="Count not found")
    return {
        "id": line.id,
        "location_id": line.location_id,
        "product_id": line.product_id,
        "expected_qty": line.expected_qty,
        "counted_qty": line.counted_qty,
        "variance": line.variance
    }


@router.post("/counts/{count_id}/complete", response_model=InventoryCountResponse)
async def complete_inventory_count(
    count_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Termine un comptage."""
    count = await service.complete_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Count not found")
    return InventoryCountResponse(
        id=count.id,
        warehouse_id=count.warehouse_id,
        name=count.name,
        status=count.status,
        scheduled_date=count.scheduled_date,
        started_at=count.started_at,
        completed_at=count.completed_at,
        location_count=len(count.locations)
    )


@router.post("/counts/{count_id}/validate", response_model=InventoryCountResponse)
async def validate_inventory_count(
    count_id: str,
    apply_adjustments: bool = True,
    service: WMSService = Depends(get_wms_service)
):
    """Valide un comptage."""
    count = await service.validate_inventory_count(
        count_id,
        apply_adjustments=apply_adjustments
    )
    if not count:
        raise HTTPException(status_code=404, detail="Count not found")
    return InventoryCountResponse(
        id=count.id,
        warehouse_id=count.warehouse_id,
        name=count.name,
        status=count.status,
        scheduled_date=count.scheduled_date,
        started_at=count.started_at,
        completed_at=count.completed_at,
        location_count=len(count.locations)
    )


# ========================
# WAVE PICKING ENDPOINTS
# ========================

@router.post(
    "/warehouses/{warehouse_id}/waves",
    status_code=201,
    response_model=WaveResponse
)
async def create_wave(
    warehouse_id: str,
    data: WaveCreate,
    service: WMSService = Depends(get_wms_service)
):
    """Crée une vague de préparation."""
    wave = await service.create_wave(
        warehouse_id=warehouse_id,
        name=data.name,
        order_ids=data.order_ids
    )
    return WaveResponse(
        id=wave.id,
        warehouse_id=wave.warehouse_id,
        name=wave.name,
        status=wave.status,
        order_count=len(wave.order_ids),
        pick_count=wave.pick_count,
        picked_count=wave.picked_count,
        progress=wave.progress,
        created_at=wave.created_at,
        released_at=wave.released_at,
        completed_at=wave.completed_at
    )


@router.get(
    "/warehouses/{warehouse_id}/waves",
    response_model=list[WaveResponse]
)
async def list_waves(
    warehouse_id: str,
    status: Optional[WaveStatus] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Liste les vagues."""
    waves = await service.list_waves(
        warehouse_id=warehouse_id,
        status=status
    )
    return [
        WaveResponse(
            id=w.id,
            warehouse_id=w.warehouse_id,
            name=w.name,
            status=w.status,
            order_count=len(w.order_ids),
            pick_count=w.pick_count,
            picked_count=w.picked_count,
            progress=w.progress,
            created_at=w.created_at,
            released_at=w.released_at,
            completed_at=w.completed_at
        )
        for w in waves
    ]


@router.post("/waves/{wave_id}/orders", response_model=WaveResponse)
async def add_orders_to_wave(
    wave_id: str,
    data: WaveAddOrders,
    service: WMSService = Depends(get_wms_service)
):
    """Ajoute des commandes à une vague."""
    wave = await service.add_orders_to_wave(wave_id, data.order_ids)
    if not wave:
        raise HTTPException(status_code=404, detail="Wave not found")
    return WaveResponse(
        id=wave.id,
        warehouse_id=wave.warehouse_id,
        name=wave.name,
        status=wave.status,
        order_count=len(wave.order_ids),
        pick_count=wave.pick_count,
        picked_count=wave.picked_count,
        progress=wave.progress,
        created_at=wave.created_at,
        released_at=wave.released_at,
        completed_at=wave.completed_at
    )


@router.post("/waves/{wave_id}/release", response_model=WaveResponse)
async def release_wave(
    wave_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Libère une vague pour préparation."""
    wave = await service.release_wave(wave_id)
    if not wave:
        raise HTTPException(status_code=404, detail="Wave not found")
    return WaveResponse(
        id=wave.id,
        warehouse_id=wave.warehouse_id,
        name=wave.name,
        status=wave.status,
        order_count=len(wave.order_ids),
        pick_count=wave.pick_count,
        picked_count=wave.picked_count,
        progress=wave.progress,
        created_at=wave.created_at,
        released_at=wave.released_at,
        completed_at=wave.completed_at
    )


@router.post("/waves/{wave_id}/start", response_model=WaveResponse)
async def start_wave(
    wave_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Démarre une vague."""
    wave = await service.start_wave(wave_id)
    if not wave:
        raise HTTPException(status_code=404, detail="Wave not found")
    return WaveResponse(
        id=wave.id,
        warehouse_id=wave.warehouse_id,
        name=wave.name,
        status=wave.status,
        order_count=len(wave.order_ids),
        pick_count=wave.pick_count,
        picked_count=wave.picked_count,
        progress=wave.progress,
        created_at=wave.created_at,
        released_at=wave.released_at,
        completed_at=wave.completed_at
    )


@router.post("/waves/{wave_id}/complete", response_model=WaveResponse)
async def complete_wave(
    wave_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Termine une vague."""
    wave = await service.complete_wave(wave_id)
    if not wave:
        raise HTTPException(status_code=404, detail="Wave not found")
    return WaveResponse(
        id=wave.id,
        warehouse_id=wave.warehouse_id,
        name=wave.name,
        status=wave.status,
        order_count=len(wave.order_ids),
        pick_count=wave.pick_count,
        picked_count=wave.picked_count,
        progress=wave.progress,
        created_at=wave.created_at,
        released_at=wave.released_at,
        completed_at=wave.completed_at
    )


# ========================
# REPLENISHMENT ENDPOINTS
# ========================

@router.post("/replenishment/rules", status_code=201)
async def create_replenishment_rule(
    data: ReplenishmentRuleCreate,
    service: WMSService = Depends(get_wms_service)
):
    """Crée une règle de réapprovisionnement."""
    rule = await service.create_replenishment_rule(
        product_id=data.product_id,
        location_id=data.location_id,
        min_qty=data.min_qty,
        max_qty=data.max_qty,
        reorder_qty=data.reorder_qty,
        source_location_id=data.source_location_id
    )
    return {
        "id": rule.id,
        "product_id": rule.product_id,
        "location_id": rule.location_id,
        "min_qty": rule.min_qty,
        "max_qty": rule.max_qty,
        "reorder_qty": rule.reorder_qty,
        "source_location_id": rule.source_location_id,
        "is_active": rule.is_active
    }


@router.get(
    "/warehouses/{warehouse_id}/replenishment/needs",
    response_model=list[ReplenishmentNeed]
)
async def get_replenishment_needs(
    warehouse_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère les besoins de réapprovisionnement."""
    needs = await service.check_replenishment_needs(warehouse_id)
    return [ReplenishmentNeed(**n) for n in needs]


@router.post("/replenishment/execute/{rule_id}", response_model=MovementResponse)
async def execute_replenishment(
    rule_id: str,
    quantity: Optional[float] = None,
    service: WMSService = Depends(get_wms_service)
):
    """Exécute un réapprovisionnement."""
    movement = await service.execute_replenishment(rule_id, quantity=quantity)
    if not movement:
        raise HTTPException(
            status_code=404,
            detail="Rule not found or no source location"
        )
    return MovementResponse(
        id=movement.id,
        movement_type=movement.movement_type,
        product_id=movement.product_id,
        quantity=movement.quantity,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        lot_id=movement.lot_id,
        reference=movement.reference,
        status=movement.status.value,
        created_at=movement.created_at,
        completed_at=movement.completed_at
    )


# ========================
# STATISTICS
# ========================

@router.get("/warehouses/{warehouse_id}/stats")
async def get_warehouse_stats(
    warehouse_id: str,
    service: WMSService = Depends(get_wms_service)
):
    """Récupère les statistiques d'un entrepôt."""
    return await service.get_statistics(warehouse_id)
