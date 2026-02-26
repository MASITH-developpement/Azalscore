"""
AZALS MODULE ASSETS - Router API
================================

API REST pour la gestion des immobilisations.
"""
from __future__ import annotations


from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User

from .exceptions import (
    AssetAlreadyDisposedError,
    AssetAlreadyInServiceError,
    AssetCodeExistsError,
    AssetHasComponentsError,
    AssetModuleError,
    AssetNotFoundError,
    AssetNotInServiceError,
    CategoryCodeExistsError,
    CategoryHasAssetsError,
    CategoryHasChildrenError,
    CategoryNotFoundError,
    DepreciationAlreadyPostedError,
    InventoryAlreadyCompletedError,
    InventoryInProgressError,
    InventoryNotFoundError,
    MaintenanceAlreadyCompletedError,
    MaintenanceNotFoundError,
    TransferNotFoundError,
)
from .models import AssetStatus, InventoryStatus, MaintenanceStatus
from .schemas import (
    AssetAutocompleteResponse,
    AssetCategoryCreate,
    AssetCategoryResponse,
    AssetCategoryUpdate,
    AssetDashboard,
    AssetFilters,
    AssetInventoryCreate,
    AssetInventoryItemUpdate,
    AssetInventoryResponse,
    AssetMaintenanceComplete,
    AssetMaintenanceCreate,
    AssetMaintenanceResponse,
    AssetMaintenanceUpdate,
    AssetMovementResponse,
    AssetStatistics,
    AssetTransferCreate,
    AssetTransferResponse,
    AssetTypeEnum,
    AssetValuationResponse,
    DepreciationRunCreate,
    DepreciationRunResponse,
    DepreciationScheduleResponse,
    DisposalResponse,
    DisposeAssetRequest,
    FixedAssetCreate,
    FixedAssetResponse,
    FixedAssetUpdate,
    PaginatedAssetResponse,
    PaginatedMaintenanceResponse,
    PaginatedMovementResponse,
    PutInServiceRequest,
)
from .service_db import get_asset_service

router = APIRouter(prefix="/assets", tags=["Assets - Immobilisations"])


def handle_asset_error(e: AssetModuleError):
    """Convertir les exceptions du module en HTTPException."""
    status_map = {
        "ASSET_NOT_FOUND": 404,
        "CATEGORY_NOT_FOUND": 404,
        "MAINTENANCE_NOT_FOUND": 404,
        "INVENTORY_NOT_FOUND": 404,
        "TRANSFER_NOT_FOUND": 404,
        "DEPRECIATION_RUN_NOT_FOUND": 404,
        "ASSET_CODE_EXISTS": 409,
        "CATEGORY_CODE_EXISTS": 409,
        "ASSET_ALREADY_IN_SERVICE": 400,
        "ASSET_ALREADY_DISPOSED": 400,
        "ASSET_NOT_IN_SERVICE": 400,
        "CATEGORY_HAS_ASSETS": 400,
        "CATEGORY_HAS_CHILDREN": 400,
        "ASSET_HAS_COMPONENTS": 400,
        "DEPRECIATION_ALREADY_POSTED": 400,
        "MAINTENANCE_ALREADY_COMPLETED": 400,
        "INVENTORY_ALREADY_COMPLETED": 400,
        "INVENTORY_IN_PROGRESS": 400,
        "VALIDATION_ERROR": 422,
    }
    status_code = status_map.get(e.code, 400)
    raise HTTPException(status_code=status_code, detail={"code": e.code, "message": e.message, "details": e.details})


# ============================================================================
# CATEGORIES
# ============================================================================

@router.post("/categories", response_model=AssetCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: AssetCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une categorie d'immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.create_category(data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/categories", response_model=list[AssetCategoryResponse])
async def list_categories(
    parent_id: UUID | None = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les categories."""
    service = get_asset_service(db, current_user.tenant_id)
    items, _ = service.list_categories(parent_id, active_only, skip, limit)
    return items


@router.get("/categories/{category_id}", response_model=AssetCategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une categorie."""
    service = get_asset_service(db, current_user.tenant_id)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categorie non trouvee")
    return category


@router.put("/categories/{category_id}", response_model=AssetCategoryResponse)
async def update_category(
    category_id: UUID,
    data: AssetCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une categorie."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.update_category(category_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une categorie."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        service.delete_category(category_id)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# IMMOBILISATIONS - CRUD
# ============================================================================

@router.post("/", response_model=FixedAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: FixedAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.create_asset(data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/", response_model=PaginatedAssetResponse)
async def list_assets(
    search: str | None = None,
    status: list[str] | None = Query(None),
    asset_type: list[str] | None = Query(None),
    category_id: UUID | None = None,
    location_id: UUID | None = None,
    responsible_id: UUID | None = None,
    acquisition_date_from: date | None = None,
    acquisition_date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les immobilisations avec filtres."""
    service = get_asset_service(db, current_user.tenant_id)

    filters = AssetFilters(
        search=search,
        status=[AssetStatus(s) for s in status] if status else None,
        asset_type=[AssetTypeEnum(t) for t in asset_type] if asset_type else None,
        category_id=category_id,
        location_id=location_id,
        responsible_id=responsible_id,
        acquisition_date_from=acquisition_date_from,
        acquisition_date_to=acquisition_date_to,
    )

    items, total = service.list_assets(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/autocomplete", response_model=AssetAutocompleteResponse)
async def autocomplete_assets(
    q: str = Query(..., min_length=2, description="Terme de recherche"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recherche pour autocomplete."""
    service = get_asset_service(db, current_user.tenant_id)
    suggestions = service.autocomplete_assets(q, limit)
    return {"suggestions": suggestions, "total": len(suggestions)}


@router.get("/{asset_id}", response_model=FixedAssetResponse)
async def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une immobilisation."""
    service = get_asset_service(db, current_user.tenant_id)
    asset = service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Immobilisation non trouvee")
    return asset


@router.get("/code/{asset_code}", response_model=FixedAssetResponse)
async def get_asset_by_code(
    asset_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une immobilisation par code."""
    service = get_asset_service(db, current_user.tenant_id)
    asset = service.get_asset_by_code(asset_code)
    if not asset:
        raise HTTPException(status_code=404, detail="Immobilisation non trouvee")
    return asset


@router.get("/barcode/{barcode}", response_model=FixedAssetResponse)
async def get_asset_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une immobilisation par code-barres."""
    service = get_asset_service(db, current_user.tenant_id)
    asset = service.get_asset_by_barcode(barcode)
    if not asset:
        raise HTTPException(status_code=404, detail="Immobilisation non trouvee")
    return asset


@router.put("/{asset_id}", response_model=FixedAssetResponse)
async def update_asset(
    asset_id: UUID,
    data: FixedAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.update_asset(asset_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        service.delete_asset(asset_id)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# MISE EN SERVICE
# ============================================================================

@router.post("/{asset_id}/put-in-service", response_model=FixedAssetResponse)
async def put_asset_in_service(
    asset_id: UUID,
    data: PutInServiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre en service une immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.put_in_service(asset_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# AMORTISSEMENTS
# ============================================================================

@router.get("/{asset_id}/depreciation-schedule", response_model=DepreciationScheduleResponse)
async def get_depreciation_schedule(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer le tableau d'amortissement."""
    try:
        service = get_asset_service(db, current_user.tenant_id)
        return service.get_depreciation_schedule(asset_id)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.post("/depreciation/run", response_model=DepreciationRunResponse, status_code=status.HTTP_201_CREATED)
async def run_depreciation(
    data: DepreciationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executer le calcul des amortissements."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.run_depreciation(data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/depreciation/runs", response_model=list[DepreciationRunResponse])
async def list_depreciation_runs(
    fiscal_year: int | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les executions d'amortissement."""
    service = get_asset_service(db, current_user.tenant_id)
    items, _ = service.list_depreciation_runs(fiscal_year, status, page, page_size)
    return items


@router.get("/depreciation/runs/{run_id}", response_model=DepreciationRunResponse)
async def get_depreciation_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une execution d'amortissement."""
    service = get_asset_service(db, current_user.tenant_id)
    run = service.get_depreciation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Execution non trouvee")
    return run


# ============================================================================
# CESSIONS
# ============================================================================

@router.post("/{asset_id}/dispose", response_model=DisposalResponse)
async def dispose_asset(
    asset_id: UUID,
    data: DisposeAssetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ceder ou mettre au rebut une immobilisation."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.dispose_asset(asset_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# MOUVEMENTS
# ============================================================================

@router.get("/{asset_id}/movements", response_model=list[AssetMovementResponse])
async def get_asset_movements(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les mouvements d'une immobilisation."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_asset_movements(asset_id)


@router.get("/movements", response_model=PaginatedMovementResponse)
async def list_movements(
    asset_id: UUID | None = None,
    movement_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les mouvements."""
    service = get_asset_service(db, current_user.tenant_id)
    items, total = service.list_movements(asset_id, movement_type, date_from, date_to, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ============================================================================
# MAINTENANCE
# ============================================================================

@router.post("/{asset_id}/maintenances", response_model=AssetMaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    asset_id: UUID,
    data: AssetMaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une maintenance."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.create_maintenance(asset_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/{asset_id}/maintenances", response_model=list[AssetMaintenanceResponse])
async def get_asset_maintenances(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les maintenances d'une immobilisation."""
    service = get_asset_service(db, current_user.tenant_id)
    items, _ = service.list_maintenances(asset_id=asset_id)
    return items


@router.get("/maintenances", response_model=PaginatedMaintenanceResponse)
async def list_maintenances(
    asset_id: UUID | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les maintenances."""
    service = get_asset_service(db, current_user.tenant_id)
    maint_status = MaintenanceStatus(status) if status else None
    items, total = service.list_maintenances(asset_id, maint_status, date_from, date_to, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/maintenances/upcoming", response_model=list[AssetMaintenanceResponse])
async def get_upcoming_maintenances(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les maintenances a venir."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_upcoming_maintenances(days)


@router.get("/maintenances/overdue", response_model=list[AssetMaintenanceResponse])
async def get_overdue_maintenances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les maintenances en retard."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_overdue_maintenances()


@router.get("/maintenances/{maintenance_id}", response_model=AssetMaintenanceResponse)
async def get_maintenance(
    maintenance_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une maintenance."""
    service = get_asset_service(db, current_user.tenant_id)
    maintenance = service.get_maintenance(maintenance_id)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance non trouvee")
    return maintenance


@router.put("/maintenances/{maintenance_id}", response_model=AssetMaintenanceResponse)
async def update_maintenance(
    maintenance_id: UUID,
    data: AssetMaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une maintenance."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.update_maintenance(maintenance_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.post("/maintenances/{maintenance_id}/complete", response_model=AssetMaintenanceResponse)
async def complete_maintenance(
    maintenance_id: UUID,
    data: AssetMaintenanceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer une maintenance."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.complete_maintenance(maintenance_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# INVENTAIRE PHYSIQUE
# ============================================================================

@router.post("/inventories", response_model=AssetInventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory(
    data: AssetInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un inventaire physique."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.create_inventory(data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/inventories", response_model=list[AssetInventoryResponse])
async def list_inventories(
    status: str | None = None,
    location_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les inventaires."""
    service = get_asset_service(db, current_user.tenant_id)
    inv_status = InventoryStatus(status) if status else None
    items, _ = service.list_inventories(inv_status, location_id, page, page_size)
    return items


@router.get("/inventories/{inventory_id}", response_model=AssetInventoryResponse)
async def get_inventory(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un inventaire."""
    service = get_asset_service(db, current_user.tenant_id)
    inventory = service.get_inventory(inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventaire non trouve")
    return inventory


@router.post("/inventories/{inventory_id}/start", response_model=AssetInventoryResponse)
async def start_inventory(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Demarrer un inventaire."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.start_inventory(inventory_id)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.put("/inventories/{inventory_id}/items/{item_id}")
async def scan_inventory_item(
    inventory_id: UUID,
    item_id: UUID,
    data: AssetInventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Scanner un element d'inventaire."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.scan_inventory_item(inventory_id, item_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.post("/inventories/{inventory_id}/complete", response_model=AssetInventoryResponse)
async def complete_inventory(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminer un inventaire."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.complete_inventory(inventory_id)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.post("/inventories/{inventory_id}/validate", response_model=AssetInventoryResponse)
async def validate_inventory(
    inventory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valider un inventaire."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.validate_inventory(inventory_id)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# TRANSFERTS
# ============================================================================

@router.post("/{asset_id}/transfers", response_model=AssetTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    asset_id: UUID,
    data: AssetTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un transfert."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.create_transfer(asset_id, data)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.get("/transfers", response_model=list[AssetTransferResponse])
async def list_transfers(
    asset_id: UUID | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les transferts."""
    service = get_asset_service(db, current_user.tenant_id)
    items, _ = service.list_transfers(asset_id, status, page, page_size)
    return items


@router.get("/transfers/{transfer_id}", response_model=AssetTransferResponse)
async def get_transfer(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un transfert."""
    service = get_asset_service(db, current_user.tenant_id)
    transfer = service.get_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfert non trouve")
    return transfer


@router.post("/transfers/{transfer_id}/approve", response_model=AssetTransferResponse)
async def approve_transfer(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver un transfert."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.approve_transfer(transfer_id)
    except AssetModuleError as e:
        handle_asset_error(e)


@router.post("/transfers/{transfer_id}/complete", response_model=AssetTransferResponse)
async def complete_transfer(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Completer un transfert."""
    try:
        service = get_asset_service(db, current_user.tenant_id, current_user.id)
        return service.complete_transfer(transfer_id)
    except AssetModuleError as e:
        handle_asset_error(e)


# ============================================================================
# STATISTIQUES ET DASHBOARD
# ============================================================================

@router.get("/statistics", response_model=AssetStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer les statistiques."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_statistics()


@router.get("/dashboard", response_model=AssetDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer le dashboard."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_dashboard()


@router.get("/valuation", response_model=AssetValuationResponse)
async def get_valuation(
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer la valorisation du parc."""
    service = get_asset_service(db, current_user.tenant_id)
    return service.get_valuation(as_of_date)
