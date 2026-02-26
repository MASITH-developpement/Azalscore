"""
AZALS MODULE M5 - Router Inventaire
====================================

API REST pour la gestion des stocks et logistique.
"""
from __future__ import annotations


from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User

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
    # Opérations sur lignes
    LineOperationResponse,
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
    ProductAutocompleteResponse,
    ProductCreate,
    ProductList,
    ProductResponse,
    ProductSuggestion,
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

router = APIRouter(prefix="/inventory", tags=["M5 - Inventaire"])


# ============================================================================
# CATÉGORIES
# ============================================================================

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une catégorie de produits."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_category(data)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    parent_id: UUID | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les catégories."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_categories(parent_id, active_only, skip, limit)
    return items


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une catégorie."""
    service = get_inventory_service(db, current_user.tenant_id)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une catégorie."""
    service = get_inventory_service(db, current_user.tenant_id)
    category = service.update_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


# ============================================================================
# ENTREPÔTS
# ============================================================================

@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un entrepôt."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_warehouse(data)


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les entrepôts."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_warehouses(active_only, skip, limit)
    return items


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un entrepôt."""
    service = get_inventory_service(db, current_user.tenant_id)
    warehouse = service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Entrepôt non trouvé")
    return warehouse


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un entrepôt."""
    service = get_inventory_service(db, current_user.tenant_id)
    warehouse = service.update_warehouse(warehouse_id, data)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Entrepôt non trouvé")
    return warehouse


@router.get("/warehouses/{warehouse_id}/stock", response_model=list[StockLevelResponse])
async def get_warehouse_stock(
    warehouse_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le stock d'un entrepôt."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.get_warehouse_stock(warehouse_id, skip, limit)
    return items


# ============================================================================
# EMPLACEMENTS
# ============================================================================

@router.post("/warehouses/{warehouse_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    warehouse_id: UUID,
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un emplacement."""
    service = get_inventory_service(db, current_user.tenant_id)
    return service.create_location(warehouse_id, data)


@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(
    warehouse_id: UUID | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les emplacements."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_locations(warehouse_id, active_only, skip, limit)
    return items


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un emplacement."""
    service = get_inventory_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Créer un produit."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_product(data)


@router.get("/products", response_model=ProductList)
async def list_products(
    category_id: UUID | None = None,
    status: ProductStatus | None = None,
    search: str | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les produits."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, total = service.list_products(category_id, status, search, active_only, skip, limit)
    return {"items": items, "total": total}


@router.get("/products/autocomplete", response_model=ProductAutocompleteResponse)
async def autocomplete_products(
    q: str = Query(..., min_length=2, description="Terme de recherche (min 2 caractères)"),
    limit: int = Query(10, ge=1, le=50, description="Nombre max de suggestions"),
    category_id: UUID | None = Query(None, description="Filtrer par catégorie"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche de produits pour autocomplete.

    Retourne une liste légère de suggestions avec seulement les champs
    nécessaires pour remplir une ligne de document (devis, commande, facture).

    Recherche dans: code, nom, code-barres, SKU.
    """
    service = get_inventory_service(db, current_user.tenant_id)
    suggestions = service.search_products_autocomplete(q, limit, category_id)
    return {"suggestions": suggestions, "total": len(suggestions)}


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un produit."""
    service = get_inventory_service(db, current_user.tenant_id)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un produit."""
    service = get_inventory_service(db, current_user.tenant_id)
    product = service.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.post("/products/{product_id}/activate", response_model=ProductResponse)
async def activate_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer un produit."""
    service = get_inventory_service(db, current_user.tenant_id)
    product = service.activate_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.get("/products/{product_id}/stock", response_model=list[StockLevelResponse])
async def get_product_stock(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le stock d'un produit."""
    service = get_inventory_service(db, current_user.tenant_id)
    return service.get_product_stock(product_id)


# ============================================================================
# LOTS
# ============================================================================

@router.post("/lots", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot(
    data: LotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un lot."""
    service = get_inventory_service(db, current_user.tenant_id)
    return service.create_lot(data)


@router.get("/lots", response_model=list[LotResponse])
async def list_lots(
    product_id: UUID | None = None,
    status: LotStatus | None = None,
    expiring_before: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les lots."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_lots(product_id, status, expiring_before, skip, limit)
    return items


@router.get("/lots/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un lot."""
    service = get_inventory_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Créer un numéro de série."""
    service = get_inventory_service(db, current_user.tenant_id)
    return service.create_serial(data)


@router.get("/serials/{serial_id}", response_model=SerialResponse)
async def get_serial(
    serial_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un numéro de série."""
    service = get_inventory_service(db, current_user.tenant_id)
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
    current_user: User = Depends(get_current_user)
):
    """Créer un mouvement de stock."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_movement(data)


@router.get("/movements", response_model=MovementList)
async def list_movements(
    type: MovementType | None = None,
    status: MovementStatus | None = None,
    warehouse_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les mouvements."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, total = service.list_movements(type, status, warehouse_id, date_from, date_to, skip, limit)
    return {"items": items, "total": total}


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un mouvement."""
    service = get_inventory_service(db, current_user.tenant_id)
    movement = service.get_movement(movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Mouvement non trouvé")
    return movement


@router.post("/movements/{movement_id}/confirm", response_model=MovementResponse)
async def confirm_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirmer un mouvement (impacter les stocks)."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    movement = service.confirm_movement(movement_id)
    if not movement:
        raise HTTPException(status_code=400, detail="Impossible de confirmer ce mouvement")
    return movement


@router.post("/movements/{movement_id}/cancel", response_model=MovementResponse)
async def cancel_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler un mouvement brouillon."""
    service = get_inventory_service(db, current_user.tenant_id)
    movement = service.cancel_movement(movement_id)
    if not movement:
        raise HTTPException(status_code=400, detail="Impossible d'annuler ce mouvement")
    return movement


# ============================================================================
# INVENTAIRES PHYSIQUES
# ============================================================================

@router.post("/counts", response_model=InventoryCountResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_count(
    data: InventoryCountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un inventaire physique."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_inventory_count(data)


@router.get("/counts", response_model=list[InventoryCountResponse])
async def list_inventory_counts(
    status: InventoryStatus | None = None,
    warehouse_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les inventaires."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_inventory_counts(status, warehouse_id, skip, limit)
    return items


@router.get("/counts/{count_id}", response_model=InventoryCountResponse)
async def get_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un inventaire."""
    service = get_inventory_service(db, current_user.tenant_id)
    count = service.get_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Inventaire non trouvé")
    return count


@router.post("/counts/{count_id}/start", response_model=InventoryCountResponse)
async def start_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Démarrer un inventaire (générer les lignes)."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    count = service.start_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=400, detail="Impossible de démarrer cet inventaire")
    return count


@router.put("/counts/{count_id}/lines/{line_id}", response_model=LineOperationResponse)
async def update_count_line(
    count_id: UUID,
    line_id: UUID,
    data: CountLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une ligne d'inventaire (compter)."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    line = service.update_count_line(count_id, line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    return LineOperationResponse(message="Ligne mise à jour", line_id=str(line_id))


@router.post("/counts/{count_id}/validate", response_model=InventoryCountResponse)
async def validate_inventory_count(
    count_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valider un inventaire (ajuster les stocks)."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    count = service.validate_inventory_count(count_id)
    if not count:
        raise HTTPException(status_code=400, detail="Impossible de valider cet inventaire")
    return count


# ============================================================================
# PRÉPARATIONS (PICKING)
# ============================================================================

@router.post("/pickings", response_model=PickingResponse, status_code=status.HTTP_201_CREATED)
async def create_picking(
    data: PickingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une préparation de commande."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    return service.create_picking(data)


@router.get("/pickings", response_model=list[PickingResponse])
async def list_pickings(
    status: PickingStatus | None = None,
    warehouse_id: UUID | None = None,
    assigned_to: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les préparations."""
    service = get_inventory_service(db, current_user.tenant_id)
    items, _ = service.list_pickings(status, warehouse_id, assigned_to, skip, limit)
    return items


@router.get("/pickings/{picking_id}", response_model=PickingResponse)
async def get_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une préparation."""
    service = get_inventory_service(db, current_user.tenant_id)
    picking = service.get_picking(picking_id)
    if not picking:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return picking


@router.post("/pickings/{picking_id}/assign/{user_id}", response_model=PickingResponse)
async def assign_picking(
    picking_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assigner une préparation à un utilisateur."""
    service = get_inventory_service(db, current_user.tenant_id)
    picking = service.assign_picking(picking_id, user_id)
    if not picking:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return picking


@router.post("/pickings/{picking_id}/start", response_model=PickingResponse)
async def start_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Démarrer une préparation."""
    service = get_inventory_service(db, current_user.tenant_id)
    picking = service.start_picking(picking_id)
    if not picking:
        raise HTTPException(status_code=404, detail="Préparation non trouvée")
    return picking


@router.put("/pickings/{picking_id}/lines/{line_id}/pick", response_model=LineOperationResponse)
async def pick_line(
    picking_id: UUID,
    line_id: UUID,
    data: PickingLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valider une ligne de préparation."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    line = service.pick_line(picking_id, line_id, data)
    if not line:
        raise HTTPException(status_code=404, detail="Ligne non trouvée")
    return LineOperationResponse(message="Ligne préparée", line_id=str(line_id))


@router.post("/pickings/{picking_id}/complete", response_model=PickingResponse)
async def complete_picking(
    picking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer une préparation."""
    service = get_inventory_service(db, current_user.tenant_id, current_user.id)
    picking = service.complete_picking(picking_id)
    if not picking:
        raise HTTPException(status_code=400, detail="Impossible de terminer cette préparation")
    return picking


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=InventoryDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le dashboard inventaire."""
    service = get_inventory_service(db, current_user.tenant_id)
    return service.get_dashboard()
