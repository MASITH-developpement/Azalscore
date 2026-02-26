"""
Routes API - Module Fleet Management (GAP-062)

CRUD complet, Autocomplete, Dashboard, Rapports.
Permissions verifiees sur chaque endpoint.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import (
    VehicleStatus, VehicleType, FuelType,
    ContractType, ContractStatus,
    MaintenanceType, MaintenanceStatus,
    DocumentType, IncidentType, IncidentStatus,
    AlertType, AlertSeverity
)
from .service import FleetService
from .schemas import (
    # Vehicles
    VehicleCreate, VehicleUpdate, VehicleResponse, VehicleList, VehicleFilters,
    VehicleLocationUpdate, VehicleMileageUpdate, VehicleListItem,
    # Drivers
    DriverCreate, DriverUpdate, DriverResponse, DriverList, DriverFilters, DriverListItem,
    # Contracts
    ContractCreate, ContractUpdate, ContractResponse, ContractList, ContractFilters, ContractListItem,
    # Fuel
    FuelEntryCreate, FuelEntryUpdate, FuelEntryResponse, FuelEntryList, FuelEntryListItem,
    # Maintenance
    MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse, MaintenanceList, MaintenanceFilters, MaintenanceListItem,
    # Documents
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList, DocumentListItem,
    # Incidents
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentList, IncidentFilters, IncidentListItem,
    # Alerts
    AlertResponse, AlertList, AlertFilters, AlertListItem,
    # Dashboard/Reports
    FleetDashboard, TCOReport, ConsumptionStats,
    # Common
    AutocompleteResponse, BulkResult
)
from .exceptions import (
    FleetError, VehicleNotFoundError, VehicleDuplicateError, VehicleStateError,
    DriverNotFoundError, DriverDuplicateError, DriverLicenseExpiredError,
    ContractNotFoundError, ContractDuplicateError,
    MaintenanceNotFoundError, MaintenanceDuplicateError,
    IncidentNotFoundError, IncidentDuplicateError,
    DocumentNotFoundError, AlertNotFoundError,
    MileageDecrementError
)

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])


# ============== Helpers ==============

def get_fleet_service(db: Session = Depends(get_db), user=Depends(get_current_user)) -> FleetService:
    return FleetService(db, user.tenant_id, user.id)


def handle_fleet_exception(e: FleetError):
    """Convertit les exceptions metier en HTTPException."""
    if isinstance(e, (VehicleNotFoundError, DriverNotFoundError, ContractNotFoundError,
                      MaintenanceNotFoundError, IncidentNotFoundError, DocumentNotFoundError,
                      AlertNotFoundError)):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, (VehicleDuplicateError, DriverDuplicateError, ContractDuplicateError,
                        MaintenanceDuplicateError, IncidentDuplicateError)):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, (VehicleStateError, DriverLicenseExpiredError, MileageDecrementError)):
        raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail=str(e))


# ============== VEHICLE ROUTES ==============

@router.get("/vehicles", response_model=VehicleList)
async def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[VehicleStatus]] = Query(None),
    vehicle_type: Optional[List[VehicleType]] = Query(None),
    fuel_type: Optional[List[FuelType]] = Query(None),
    department: Optional[str] = Query(None),
    assigned_driver_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des vehicules."""
    filters = VehicleFilters(
        search=search, status=status, vehicle_type=vehicle_type,
        fuel_type=fuel_type, department=department,
        assigned_driver_id=assigned_driver_id, is_active=is_active
    )
    items, total = service.list_vehicles(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/vehicles/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_vehicles(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Autocomplete pour les vehicules."""
    items = service.vehicle_repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/vehicles/available")
async def list_available_vehicles(
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les vehicules disponibles."""
    return service.vehicle_repo.get_available()


@router.get("/vehicles/{id}", response_model=VehicleResponse)
async def get_vehicle(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere un vehicule."""
    try:
        return service.get_vehicle(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/vehicles", response_model=VehicleResponse, status_code=201)
async def create_vehicle(
    data: VehicleCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree un vehicule."""
    try:
        return service.create_vehicle(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/vehicles/{id}", response_model=VehicleResponse)
async def update_vehicle(
    id: UUID,
    data: VehicleUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour un vehicule."""
    try:
        return service.update_vehicle(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.delete("/vehicles/{id}", status_code=204)
async def delete_vehicle(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.delete")
):
    """Supprime un vehicule."""
    try:
        service.delete_vehicle(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/vehicles/{id}/assign-driver", response_model=VehicleResponse)
async def assign_driver(
    id: UUID,
    driver_id: UUID = Query(...),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Affecte un conducteur a un vehicule."""
    try:
        return service.assign_driver(id, driver_id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/vehicles/{id}/unassign-driver", response_model=VehicleResponse)
async def unassign_driver(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Retire l'affectation du conducteur."""
    try:
        return service.unassign_driver(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/vehicles/{id}/location", response_model=VehicleResponse)
async def update_vehicle_location(
    id: UUID,
    data: VehicleLocationUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour la position GPS."""
    try:
        return service.update_vehicle_location(id, data.latitude, data.longitude)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/vehicles/{id}/mileage", response_model=VehicleResponse)
async def update_vehicle_mileage(
    id: UUID,
    data: VehicleMileageUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour le kilometrage."""
    try:
        return service.update_vehicle_mileage(
            id, data.mileage, data.log_date, data.source, data.notes
        )
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/contracts")
async def get_vehicle_contracts(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les contrats d'un vehicule."""
    try:
        return service.get_vehicle_contracts(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/maintenances")
async def get_vehicle_maintenances(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les maintenances d'un vehicule."""
    try:
        return service.get_vehicle_maintenances(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/documents")
async def get_vehicle_documents(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les documents d'un vehicule."""
    try:
        return service.get_vehicle_documents(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/incidents")
async def get_vehicle_incidents(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les incidents d'un vehicule."""
    try:
        return service.get_vehicle_incidents(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/fuel-entries")
async def get_vehicle_fuel_entries(
    id: UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les entrees carburant d'un vehicule."""
    items, total = service.get_fuel_entries(id, None, date_from, date_to, page, page_size)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/vehicles/{id}/consumption", response_model=ConsumptionStats)
async def get_vehicle_consumption(
    id: UUID,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Statistiques de consommation d'un vehicule."""
    try:
        return service.get_consumption_stats(id, date_from, date_to)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/vehicles/{id}/tco", response_model=TCOReport)
async def get_vehicle_tco(
    id: UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Rapport TCO d'un vehicule."""
    try:
        return service.get_tco_report(id, date_from, date_to)
    except FleetError as e:
        handle_fleet_exception(e)


# ============== DRIVER ROUTES ==============

@router.get("/drivers", response_model=DriverList)
async def list_drivers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    license_expiring_days: Optional[int] = Query(None),
    sort_by: str = Query("last_name"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des conducteurs."""
    filters = DriverFilters(
        search=search, department=department,
        is_active=is_active, license_expiring_days=license_expiring_days
    )
    items, total = service.list_drivers(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/drivers/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_drivers(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Autocomplete pour les conducteurs."""
    items = service.driver_repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/drivers/expiring-licenses")
async def list_expiring_licenses(
    days: int = Query(30, ge=1),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les conducteurs avec permis expirant."""
    return service.driver_repo.get_with_expiring_licenses(days)


@router.get("/drivers/{id}", response_model=DriverResponse)
async def get_driver(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere un conducteur."""
    try:
        return service.get_driver(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/drivers", response_model=DriverResponse, status_code=201)
async def create_driver(
    data: DriverCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree un conducteur."""
    try:
        return service.create_driver(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/drivers/{id}", response_model=DriverResponse)
async def update_driver(
    id: UUID,
    data: DriverUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour un conducteur."""
    try:
        return service.update_driver(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.delete("/drivers/{id}", status_code=204)
async def delete_driver(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.delete")
):
    """Supprime un conducteur."""
    try:
        service.delete_driver(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.get("/drivers/{id}/documents")
async def get_driver_documents(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les documents d'un conducteur."""
    try:
        return service.get_driver_documents(id)
    except FleetError as e:
        handle_fleet_exception(e)


# ============== CONTRACT ROUTES ==============

@router.get("/contracts", response_model=ContractList)
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    vehicle_id: Optional[UUID] = Query(None),
    contract_type: Optional[List[ContractType]] = Query(None),
    status: Optional[List[ContractStatus]] = Query(None),
    expiring_days: Optional[int] = Query(None),
    sort_by: str = Query("end_date"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des contrats."""
    filters = ContractFilters(
        search=search, vehicle_id=vehicle_id,
        contract_type=contract_type, status=status,
        expiring_days=expiring_days
    )
    items, total = service.list_contracts(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/contracts/expiring")
async def list_expiring_contracts(
    days: int = Query(30, ge=1),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les contrats expirant bientot."""
    return service.get_expiring_contracts(days)


@router.get("/contracts/{id}", response_model=ContractResponse)
async def get_contract(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere un contrat."""
    try:
        return service.get_contract(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/contracts", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree un contrat."""
    try:
        return service.create_contract(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/contracts/{id}", response_model=ContractResponse)
async def update_contract(
    id: UUID,
    data: ContractUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour un contrat."""
    try:
        return service.update_contract(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


# ============== FUEL ROUTES ==============

@router.get("/fuel-entries", response_model=FuelEntryList)
async def list_fuel_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vehicle_id: Optional[UUID] = Query(None),
    driver_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des entrees carburant."""
    items, total = service.get_fuel_entries(vehicle_id, driver_id, date_from, date_to, page, page_size)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/fuel-entries/{id}", response_model=FuelEntryResponse)
async def get_fuel_entry(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere une entree carburant."""
    entry = service.fuel_repo.get_by_id(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Fuel entry not found")
    return entry


@router.post("/fuel-entries", response_model=FuelEntryResponse, status_code=201)
async def create_fuel_entry(
    data: FuelEntryCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree une entree carburant."""
    try:
        return service.add_fuel_entry(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


# ============== MAINTENANCE ROUTES ==============

@router.get("/maintenances", response_model=MaintenanceList)
async def list_maintenances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    vehicle_id: Optional[UUID] = Query(None),
    maintenance_type: Optional[List[MaintenanceType]] = Query(None),
    status: Optional[List[MaintenanceStatus]] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sort_by: str = Query("scheduled_date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des maintenances."""
    filters = MaintenanceFilters(
        search=search, vehicle_id=vehicle_id,
        maintenance_type=maintenance_type, status=status,
        date_from=date_from, date_to=date_to
    )
    items, total = service.list_maintenances(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/maintenances/scheduled")
async def list_scheduled_maintenances(
    days: int = Query(30, ge=1),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les maintenances planifiees."""
    return service.get_scheduled_maintenances(days)


@router.get("/maintenances/overdue")
async def list_overdue_maintenances(
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les maintenances en retard."""
    return service.get_overdue_maintenances()


@router.get("/maintenances/{id}", response_model=MaintenanceResponse)
async def get_maintenance(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere une maintenance."""
    try:
        return service.get_maintenance(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/maintenances", response_model=MaintenanceResponse, status_code=201)
async def create_maintenance(
    data: MaintenanceCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree une maintenance."""
    try:
        return service.create_maintenance(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/maintenances/{id}", response_model=MaintenanceResponse)
async def update_maintenance(
    id: UUID,
    data: MaintenanceUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour une maintenance."""
    try:
        maintenance = service.get_maintenance(id)
        return service.maintenance_repo.update(maintenance, data.model_dump(exclude_unset=True), service.user_id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/maintenances/{id}/complete", response_model=MaintenanceResponse)
async def complete_maintenance(
    id: UUID,
    data: MaintenanceUpdate = Body(...),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Complete une maintenance."""
    try:
        return service.complete_maintenance(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


# ============== DOCUMENT ROUTES ==============

@router.get("/documents", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vehicle_id: Optional[UUID] = Query(None),
    driver_id: Optional[UUID] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des documents."""
    items = []
    if vehicle_id:
        items = service.get_vehicle_documents(vehicle_id)
    elif driver_id:
        items = service.get_driver_documents(driver_id)
    else:
        # Liste tous les documents (pagination simplifiee)
        v_items = service.document_repo.get_expiring(365)
        items = v_items

    total = len(items)
    pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size

    return {"items": items[start:end], "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/documents/expiring")
async def list_expiring_documents(
    days: int = Query(30, ge=1),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les documents expirant bientot."""
    return service.get_expiring_documents(days)


@router.get("/documents/{id}", response_model=DocumentResponse)
async def get_document(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere un document."""
    try:
        return service.get_document(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    data: DocumentCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree un document."""
    try:
        return service.add_document(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/documents/{id}", response_model=DocumentResponse)
async def update_document(
    id: UUID,
    data: DocumentUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour un document."""
    try:
        return service.update_document(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


# ============== INCIDENT ROUTES ==============

@router.get("/incidents", response_model=IncidentList)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    vehicle_id: Optional[UUID] = Query(None),
    driver_id: Optional[UUID] = Query(None),
    incident_type: Optional[List[IncidentType]] = Query(None),
    status: Optional[List[IncidentStatus]] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("incident_date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des incidents."""
    filters = IncidentFilters(
        search=search, vehicle_id=vehicle_id, driver_id=driver_id,
        incident_type=incident_type, status=status,
        date_from=date_from, date_to=date_to
    )
    items, total = service.list_incidents(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/incidents/unpaid-fines")
async def list_unpaid_fines(
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les amendes non payees."""
    return service.get_unpaid_fines()


@router.get("/incidents/{id}", response_model=IncidentResponse)
async def get_incident(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Recupere un incident."""
    try:
        return service.get_incident(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.create")
):
    """Cree un incident."""
    try:
        return service.create_incident(data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.put("/incidents/{id}", response_model=IncidentResponse)
async def update_incident(
    id: UUID,
    data: IncidentUpdate,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Met a jour un incident."""
    try:
        return service.update_incident(id, data.model_dump(exclude_unset=True))
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/incidents/{id}/pay", response_model=IncidentResponse)
async def pay_fine(
    id: UUID,
    paid_date: Optional[date] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Marque une amende comme payee."""
    try:
        return service.pay_fine(id, paid_date)
    except FleetError as e:
        handle_fleet_exception(e)


# ============== ALERT ROUTES ==============

@router.get("/alerts", response_model=AlertList)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vehicle_id: Optional[UUID] = Query(None),
    alert_type: Optional[List[AlertType]] = Query(None),
    severity: Optional[List[AlertSeverity]] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste paginee des alertes."""
    filters = AlertFilters(
        vehicle_id=vehicle_id, alert_type=alert_type,
        severity=severity, is_resolved=is_resolved
    )
    items, total = service.get_alerts(filters, page, page_size)
    return {"items": items, "total": total}


@router.get("/alerts/unresolved")
async def list_unresolved_alerts(
    vehicle_id: Optional[UUID] = Query(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Liste les alertes non resolues."""
    return service.get_unresolved_alerts(vehicle_id)


@router.post("/alerts/{id}/read", response_model=AlertResponse)
async def mark_alert_read(
    id: UUID,
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Marque une alerte comme lue."""
    try:
        return service.mark_alert_read(id)
    except FleetError as e:
        handle_fleet_exception(e)


@router.post("/alerts/{id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    id: UUID,
    notes: Optional[str] = Body(None),
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.edit")
):
    """Resout une alerte."""
    try:
        return service.resolve_alert(id, notes)
    except FleetError as e:
        handle_fleet_exception(e)


# ============== DASHBOARD & REPORTS ==============

@router.get("/dashboard", response_model=FleetDashboard)
async def get_dashboard(
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.view")
):
    """Dashboard de la flotte."""
    return service.get_dashboard()


@router.post("/run-checks")
async def run_scheduled_checks(
    service: FleetService = Depends(get_fleet_service),
    _: None = require_permission("fleet.admin")
):
    """Execute les verifications planifiees manuellement."""
    service.run_scheduled_checks()
    return {"status": "ok", "message": "Scheduled checks completed"}
