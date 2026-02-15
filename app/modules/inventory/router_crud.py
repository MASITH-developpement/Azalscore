"""
AZALS MODULE - INVENTORY: Router Unifié
========================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.inventory.router_unified import router as inventory_router

    # Double enregistrement pour compatibilité
    app.include_router(inventory_router, prefix="/v2")
    app.include_router(inventory_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (45 total):
- Categories (4): CRUD
- Warehouses (5): CRUD + stock
- Locations (3): create + list + get
- Products (6): CRUD + activate + stock
- Lots (3): create + list + get
- Serials (2): create + get
- Movements (5): CRUD + confirm/cancel
- Counts (6): CRUD + start/validate + update line
- Pickings (8): CRUD + assign/start/complete + pick line
- Dashboard (1)
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import InventoryStatus, LotStatus, MovementStatus, MovementType, PickingStatus, ProductStatus
from .schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CountLineUpdate,
    InventoryCountCreate,
    InventoryCountResponse,
    InventoryDashboard,
    LocationCreate,
    LocationResponse,
    LineOperationResponse,
    LotCreate,
    LotResponse,
    MovementCreate,
    MovementList,
    MovementResponse,
    PickingCreate,
    PickingLineUpdate,
    PickingResponse,
    ProductCreate,
    ProductList,
    ProductResponse,
    ProductUpdate,
    SerialCreate,
    SerialResponse,
    StockLevelResponse,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from .service import get_inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory - Stocks"])

# ============================================================================
# CATÉGORIES
# ============================================================================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une catégorie de produits."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_category(data)

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    parent_id: UUID | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les catégories."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_categories(parent_id=parent_id, is_active=is_active)

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une catégorie par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une catégorie."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_category(category_id, data)

# ============================================================================
# ENTREPÔTS
# ============================================================================

@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un entrepôt."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_warehouse(data)

@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les entrepôts."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_warehouses(is_active=is_active)

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un entrepôt par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    warehouse = service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Entrepôt non trouvé")
    return warehouse

@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un entrepôt."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_warehouse(warehouse_id, data)

@router.get("/warehouses/{warehouse_id}/stock", response_model=list[StockLevelResponse])
async def get_warehouse_stock(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le stock d'un entrepôt."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.get_warehouse_stock(warehouse_id)

# ============================================================================
# EMPLACEMENTS
# ============================================================================

@router.post("/warehouses/{warehouse_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    warehouse_id: UUID,
    data: LocationCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un emplacement dans un entrepôt."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_location(warehouse_id, data)

@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(
    warehouse_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les emplacements."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_locations(warehouse_id=warehouse_id)

@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un emplacement par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Emplacement non trouvé")
    return location

# ============================================================================
# PRODUITS
# ============================================================================

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un produit."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_product(data)

@router.get("/products", response_model=ProductList)
async def list_products(
    category_id: UUID | None = None,
    product_status: ProductStatus | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les produits."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    products, total = service.list_products(
        category_id=category_id,
        status=product_status,
        search=search,
        page=page,
        page_size=page_size
    )
    return ProductList(products=products, total=total, page=page, page_size=page_size)

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un produit par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour un produit."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_product(product_id, data)

@router.post("/products/{product_id}/activate", response_model=ProductResponse)
async def activate_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Activer un produit."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.activate_product(product_id)

@router.get("/products/{product_id}/stock", response_model=list[StockLevelResponse])
async def get_product_stock(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le stock d'un produit."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.get_product_stock(product_id)

# ============================================================================
# LOTS
# ============================================================================

@router.post("/lots", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot(
    data: LotCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un lot."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_lot(data)

@router.get("/lots", response_model=list[LotResponse])
async def list_lots(
    product_id: UUID | None = None,
    lot_status: LotStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les lots."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_lots(product_id=product_id, status=lot_status)

@router.get("/lots/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un lot par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    lot = service.get_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot non trouvé")
    return lot

# ============================================================================
# NUMÉROS DE SÉRIE
# ============================================================================

@router.post("/serials", response_model=SerialResponse, status_code=status.HTTP_201_CREATED)
async def create_serial(
    data: SerialCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un numéro de série."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_serial(data)

@router.get("/serials/{serial_id}", response_model=SerialResponse)
async def get_serial(
    serial_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un numéro de série par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    serial = service.get_serial(serial_id)
    if not serial:
        raise HTTPException(status_code=404, detail="Numéro de série non trouvé")
    return serial

# ============================================================================
# MOUVEMENTS DE STOCK
# ============================================================================

@router.post("/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def create_movement(
    data: MovementCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un mouvement de stock."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_movement(data)

@router.get("/movements", response_model=MovementList)
async def list_movements(
    product_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    movement_type: MovementType | None = None,
    movement_status: MovementStatus | None = Query(None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les mouvements de stock."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    movements, total = service.list_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        status=movement_status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return MovementList(movements=movements, total=total, page=page, page_size=page_size)

@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un mouvement par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    movement = service.get_movement(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Mouvement non trouvé")
    return movement

@router.post("/movements/{movement_id}/confirm", response_model=MovementResponse)
async def confirm_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Confirmer un mouvement de stock."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.confirm_movement(movement_id)

@router.post("/movements/{movement_id}/cancel", response_model=MovementResponse)
async def cancel_movement(
    movement_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Annuler un mouvement de stock."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.cancel_movement(movement_id, reason=reason)

# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

@router.post("/counts", response_model=InventoryCountResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_count(
    data: InventoryCountCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer un inventaire physique."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_inventory_count(data)

@router.get("/counts", response_model=list[InventoryCountResponse])
async def list_inventory_counts(
    warehouse_id: UUID | None = None,
    count_status: InventoryStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les inventaires physiques."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_inventory_counts(warehouse_id=warehouse_id, status=count_status)

@router.get("/counts/{count_id}", response_model=InventoryCountResponse)
async def get_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer un inventaire par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    count = service.get_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Inventaire non trouvé")
    return count

@router.post("/counts/{count_id}/start", response_model=InventoryCountResponse)
async def start_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer un inventaire physique."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.start_inventory_count(count_id)

@router.put("/counts/{count_id}/lines/{line_id}", response_model=LineOperationResponse)
async def update_count_line(
    count_id: UUID,
    line_id: UUID,
    data: CountLineUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Mettre à jour une ligne d'inventaire."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    line = service.update_count_line(count_id, line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    return LineOperationResponse(message="Ligne mise à jour", line_id=str(line_id))

@router.post("/counts/{count_id}/validate", response_model=InventoryCountResponse)
async def validate_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Valider un inventaire physique."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.validate_inventory_count(count_id)

# ============================================================================
# PRÉPARATIONS DE COMMANDES
# ============================================================================

@router.post("/pickings", response_model=PickingResponse, status_code=status.HTTP_201_CREATED)
async def create_picking(
    data: PickingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Créer une préparation de commande."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_picking(data)

@router.get("/pickings", response_model=list[PickingResponse])
async def list_pickings(
    warehouse_id: UUID | None = None,
    picking_status: PickingStatus | None = Query(None, alias="status"),
    assigned_to: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Lister les préparations de commandes."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_pickings(
        warehouse_id=warehouse_id,
        status=picking_status,
        assigned_to=assigned_to
    )

@router.get("/pickings/{picking_id}", response_model=PickingResponse)
async def get_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer une préparation par son ID."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    picking = service.get_picking(picking_id)
    if not picking:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return picking

@router.post("/pickings/{picking_id}/assign/{user_id}", response_model=PickingResponse)
async def assign_picking(
    picking_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Assigner une préparation à un utilisateur."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.assign_picking(picking_id, user_id)

@router.post("/pickings/{picking_id}/start", response_model=PickingResponse)
async def start_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Démarrer une préparation."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.start_picking(picking_id)

@router.put("/pickings/{picking_id}/lines/{line_id}/pick", response_model=LineOperationResponse)
async def pick_line(
    picking_id: UUID,
    line_id: UUID,
    data: PickingLineUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Marquer une ligne comme préparée."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    line = service.pick_line(picking_id, line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    return LineOperationResponse(message="Ligne préparée", line_id=str(line_id))

@router.post("/pickings/{picking_id}/complete", response_model=PickingResponse)
async def complete_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Finaliser une préparation."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.complete_picking(picking_id)

# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=InventoryDashboard)
async def get_inventory_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
):
    """Récupérer le dashboard inventaire."""
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.get_inventory_dashboard()
