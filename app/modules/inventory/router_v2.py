"""
AZALS MODULE INVENTORY - Router API v2 (CORE SaaS)
===================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

API REST pour la gestion des stocks et logistique.
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .models import InventoryStatus, LotStatus, MovementStatus, MovementType, PickingStatus, ProductStatus
from .schemas import (
    # Catégories
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CountLineUpdate,
    # Inventaires
    InventoryCountCreate,
    InventoryCountResponse,
    # Valorisation
    InventoryDashboard,
    # Emplacements
    LocationCreate,
    LocationResponse,
    LotCreate,
    LotResponse,
    # Mouvements
    MovementCreate,
    MovementList,
    MovementResponse,
    # Préparations
    PickingCreate,
    PickingLineUpdate,
    PickingResponse,
    # Produits
    ProductCreate,
    ProductList,
    ProductResponse,
    ProductUpdate,
    # Numéros de série
    SerialCreate,
    SerialResponse,
    # Stock
    StockLevelResponse,
    # Entrepôts
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from .service import get_inventory_service

router = APIRouter(prefix="/v2/inventory", tags=["M5 - Inventaire"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> object:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id"""
    return get_inventory_service(db, context.tenant_id, context.user_id)


# ============================================================================
# CATÉGORIES
# ============================================================================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer une catégorie de produits.

    Changements:
    - current_user.tenant_id → context.tenant_id
    - current_user.id → context.user_id
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_category(data)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    parent_id: UUID | None = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les catégories.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_categories(parent_id=parent_id, is_active=is_active)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer une catégorie par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Mettre à jour une catégorie.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_category(category_id, data)


# ============================================================================
# ENTREPÔTS
# ============================================================================

@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un entrepôt.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_warehouse(data)


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    is_active: bool = True,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les entrepôts.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_warehouses(is_active=is_active)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un entrepôt par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Mettre à jour un entrepôt.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_warehouse(warehouse_id, data)


@router.get("/warehouses/{warehouse_id}/stock", response_model=list[StockLevelResponse])
async def get_warehouse_stock(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer le stock d'un entrepôt.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un emplacement dans un entrepôt.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_location(warehouse_id, data)


@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(
    warehouse_id: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les emplacements.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_locations(warehouse_id=warehouse_id)


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un emplacement par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un produit.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_product(data)


@router.get("/products", response_model=ProductList)
async def list_products(
    category_id: UUID | None = None,
    status: ProductStatus | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les produits.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    products, total = service.list_products(
        category_id=category_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    return ProductList(
        products=products,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un produit par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Mettre à jour un produit.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_product(product_id, data)


@router.post("/products/{product_id}/activate", response_model=ProductResponse)
async def activate_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Activer un produit.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.activate_product(product_id)


@router.get("/products/{product_id}/stock", response_model=list[StockLevelResponse])
async def get_product_stock(
    product_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer le stock d'un produit.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.get_product_stock(product_id)


# ============================================================================
# LOTS
# ============================================================================

@router.post("/lots", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot(
    data: LotCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un lot.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_lot(data)


@router.get("/lots", response_model=list[LotResponse])
async def list_lots(
    product_id: UUID | None = None,
    status: LotStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les lots.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_lots(product_id=product_id, status=status)


@router.get("/lots/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un lot par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un numéro de série.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_serial(data)


@router.get("/serials/{serial_id}", response_model=SerialResponse)
async def get_serial(
    serial_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un numéro de série par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un mouvement de stock.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_movement(data)


@router.get("/movements", response_model=MovementList)
async def list_movements(
    product_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    movement_type: MovementType | None = None,
    status: MovementStatus | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les mouvements de stock.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    movements, total = service.list_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return MovementList(
        movements=movements,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un mouvement par son ID.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    movement = service.get_movement(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Mouvement non trouvé")
    return movement


@router.post("/movements/{movement_id}/confirm", response_model=MovementResponse)
async def confirm_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Confirmer un mouvement de stock.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.confirm_movement(movement_id)


@router.post("/movements/{movement_id}/cancel", response_model=MovementResponse)
async def cancel_movement(
    movement_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Annuler un mouvement de stock.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.cancel_movement(movement_id, reason=reason)


# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

@router.post("/counts", response_model=InventoryCountResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_count(
    data: InventoryCountCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer un inventaire physique.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_inventory_count(data)


@router.get("/counts", response_model=list[InventoryCountResponse])
async def list_inventory_counts(
    warehouse_id: UUID | None = None,
    status: InventoryStatus | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les inventaires physiques.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_inventory_counts(warehouse_id=warehouse_id, status=status)


@router.get("/counts/{count_id}", response_model=InventoryCountResponse)
async def get_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer un inventaire par son ID.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    count = service.get_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Inventaire non trouvé")
    return count


@router.post("/counts/{count_id}/start", response_model=InventoryCountResponse)
async def start_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Démarrer un inventaire physique.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.start_inventory_count(count_id)


@router.put("/counts/{count_id}/lines/{line_id}", response_model=dict)
async def update_count_line(
    count_id: UUID,
    line_id: UUID,
    data: CountLineUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Mettre à jour une ligne d'inventaire.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.update_count_line(count_id, line_id, data)


@router.post("/counts/{count_id}/validate", response_model=InventoryCountResponse)
async def validate_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Valider un inventaire physique.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.validate_inventory_count(count_id)


# ============================================================================
# PRÉPARATIONS DE COMMANDES
# ============================================================================

@router.post("/pickings", response_model=PickingResponse, status_code=status.HTTP_201_CREATED)
async def create_picking(
    data: PickingCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Créer une préparation de commande.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.create_picking(data)


@router.get("/pickings", response_model=list[PickingResponse])
async def list_pickings(
    warehouse_id: UUID | None = None,
    status: PickingStatus | None = None,
    assigned_to: UUID | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lister les préparations de commandes.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.list_pickings(
        warehouse_id=warehouse_id,
        status=status,
        assigned_to=assigned_to
    )


@router.get("/pickings/{picking_id}", response_model=PickingResponse)
async def get_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer une préparation par son ID.

    Changements:
    - current_user → context
    """
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
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Assigner une préparation à un utilisateur.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.assign_picking(picking_id, user_id)


@router.post("/pickings/{picking_id}/start", response_model=PickingResponse)
async def start_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Démarrer une préparation.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.start_picking(picking_id)


@router.put("/pickings/{picking_id}/lines/{line_id}/pick", response_model=dict)
async def pick_line(
    picking_id: UUID,
    line_id: UUID,
    data: PickingLineUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Marquer une ligne comme préparée.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.pick_line(picking_id, line_id, data)


@router.post("/pickings/{picking_id}/complete", response_model=PickingResponse)
async def complete_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Finaliser une préparation.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.complete_picking(picking_id)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=InventoryDashboard)
async def get_inventory_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Récupérer le dashboard inventaire.

    Changements:
    - current_user → context
    """
    service = get_inventory_service(db, context.tenant_id, context.user_id)
    return service.get_inventory_dashboard()
