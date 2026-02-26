"""
AZALS MODULE 17 - Field Service Router Unifié
==============================================
Router unifié compatible v1/v2 avec get_context().
Migration: Remplace router.py et router_v2.py.
"""
from __future__ import annotations


from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.azals import SaaSContext, get_context, get_db

from .models import InterventionPriority, InterventionStatus, InterventionType, TechnicianStatus
from .schemas import (
    ContractCreate,
    ContractResponse,
    ContractUpdate,
    ExpenseCreate,
    ExpenseResponse,
    FieldServiceDashboard,
    InterventionAssign,
    InterventionComplete,
    InterventionCreate,
    InterventionResponse,
    InterventionStart,
    InterventionStats,
    InterventionUpdate,
    RouteCreate,
    RouteResponse,
    RouteUpdate,
    TechnicianCreate,
    TechnicianLocation,
    TechnicianResponse,
    TechnicianStatusUpdate,
    TechnicianUpdate,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryUpdate,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
    ZoneCreate,
    ZoneResponse,
    ZoneUpdate,
)
from .service import FieldServiceService

router = APIRouter(prefix="/field-service", tags=["Field Service - Interventions Terrain"])

def get_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_context)
) -> FieldServiceService:
    """Factory service avec tenant et authentification obligatoire."""
    return FieldServiceService(db, context.tenant_id, str(context.user_id))

# ============================================================================
# ZONES
# ============================================================================

@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(
    active_only: bool = True,
    service: FieldServiceService = Depends(get_service)
):
    """Liste des zones de service."""
    return service.list_zones(active_only)

@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère une zone."""
    zone = service.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone non trouvée")
    return zone

@router.post("/zones", response_model=ZoneResponse)
async def create_zone(
    data: ZoneCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée une zone de service."""
    return service.create_zone(data)

@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    data: ZoneUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour une zone."""
    zone = service.update_zone(zone_id, data)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone non trouvée")
    return zone

@router.delete("/zones/{zone_id}")
async def delete_zone(
    zone_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Supprime une zone."""
    if not service.delete_zone(zone_id):
        raise HTTPException(status_code=404, detail="Zone non trouvée")
    return {"status": "deleted"}

# ============================================================================
# TECHNICIANS
# ============================================================================

@router.get("/technicians", response_model=list[TechnicianResponse])
async def list_technicians(
    active_only: bool = True,
    zone_id: int | None = None,
    status: TechnicianStatus | None = None,
    available_only: bool = False,
    service: FieldServiceService = Depends(get_service)
):
    """Liste des techniciens."""
    return service.list_technicians(active_only, zone_id, status, available_only)

@router.get("/technicians/{tech_id}", response_model=TechnicianResponse)
async def get_technician(
    tech_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère un technicien."""
    tech = service.get_technician(tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Technicien non trouvé")
    return tech

@router.post("/technicians", response_model=TechnicianResponse)
async def create_technician(
    data: TechnicianCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée un technicien."""
    return service.create_technician(data)

@router.put("/technicians/{tech_id}", response_model=TechnicianResponse)
async def update_technician(
    tech_id: int,
    data: TechnicianUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour un technicien."""
    tech = service.update_technician(tech_id, data)
    if not tech:
        raise HTTPException(status_code=404, detail="Technicien non trouvé")
    return tech

@router.post("/technicians/{tech_id}/status", response_model=TechnicianResponse)
async def update_technician_status(
    tech_id: int,
    data: TechnicianStatusUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour le statut d'un technicien."""
    tech = service.update_technician_status(
        tech_id, data.status, data.latitude, data.longitude
    )
    if not tech:
        raise HTTPException(status_code=404, detail="Technicien non trouvé")
    return tech

@router.post("/technicians/{tech_id}/location", response_model=TechnicianResponse)
async def update_technician_location(
    tech_id: int,
    data: TechnicianLocation,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour la position GPS d'un technicien."""
    tech = service.update_technician_location(tech_id, data.latitude, data.longitude)
    if not tech:
        raise HTTPException(status_code=404, detail="Technicien non trouvé")
    return tech

@router.delete("/technicians/{tech_id}")
async def delete_technician(
    tech_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Supprime un technicien."""
    if not service.delete_technician(tech_id):
        raise HTTPException(status_code=404, detail="Technicien non trouvé")
    return {"status": "deleted"}

@router.get("/technicians/{tech_id}/schedule")
async def get_technician_schedule(
    tech_id: int,
    date_from: date,
    date_to: date,
    service: FieldServiceService = Depends(get_service)
):
    """Planning d'un technicien."""
    return service.get_technician_schedule(tech_id, date_from, date_to)

# ============================================================================
# VEHICLES
# ============================================================================

@router.get("/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(
    active_only: bool = True,
    service: FieldServiceService = Depends(get_service)
):
    """Liste des véhicules."""
    return service.list_vehicles(active_only)

@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère un véhicule."""
    vehicle = service.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    return vehicle

@router.post("/vehicles", response_model=VehicleResponse)
async def create_vehicle(
    data: VehicleCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée un véhicule."""
    return service.create_vehicle(data)

@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour un véhicule."""
    vehicle = service.update_vehicle(vehicle_id, data)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    return vehicle

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Supprime un véhicule."""
    if not service.delete_vehicle(vehicle_id):
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    return {"status": "deleted"}

# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    active_only: bool = True,
    service: FieldServiceService = Depends(get_service)
):
    """Liste des templates d'intervention."""
    return service.list_templates(active_only)

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère un template."""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template

@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée un template d'intervention."""
    return service.create_template(data)

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour un template."""
    template = service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Supprime un template."""
    if not service.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return {"status": "deleted"}

# ============================================================================
# INTERVENTIONS
# ============================================================================

@router.get("/interventions")
async def list_interventions(
    status: InterventionStatus | None = None,
    priority: InterventionPriority | None = None,
    intervention_type: InterventionType | None = None,
    technician_id: int | None = None,
    zone_id: int | None = None,
    customer_id: int | None = None,
    scheduled_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: FieldServiceService = Depends(get_service)
):
    """Liste des interventions."""
    interventions, total = service.list_interventions(
        status=status,
        priority=priority,
        intervention_type=intervention_type,
        technician_id=technician_id,
        zone_id=zone_id,
        customer_id=customer_id,
        scheduled_date=scheduled_date,
        date_from=date_from,
        date_to=date_to,
        search=search,
        skip=skip,
        limit=limit
    )
    return {"items": interventions, "total": total, "skip": skip, "limit": limit}

@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère une intervention."""
    intervention = service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.get("/interventions/ref/{reference}", response_model=InterventionResponse)
async def get_intervention_by_reference(
    reference: str,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère une intervention par référence."""
    intervention = service.get_intervention_by_reference(reference)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions", response_model=InterventionResponse)
async def create_intervention(
    data: InterventionCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée une intervention."""
    return service.create_intervention(data)

@router.put("/interventions/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: int,
    data: InterventionUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour une intervention."""
    intervention = service.update_intervention(intervention_id, data)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/assign", response_model=InterventionResponse)
async def assign_intervention(
    intervention_id: int,
    data: InterventionAssign,
    service: FieldServiceService = Depends(get_service)
):
    """Assigne une intervention à un technicien."""
    intervention = service.assign_intervention(intervention_id, data)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention ou technicien non trouvé")
    return intervention

@router.post("/interventions/{intervention_id}/start-travel", response_model=InterventionResponse)
async def start_travel(
    intervention_id: int,
    tech_id: int,
    data: InterventionStart | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Démarre le trajet vers l'intervention."""
    lat = data.latitude if data else None
    lng = data.longitude if data else None
    intervention = service.start_travel(intervention_id, tech_id, lat, lng)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/arrive", response_model=InterventionResponse)
async def arrive_on_site(
    intervention_id: int,
    tech_id: int,
    data: InterventionStart | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Arrive sur le site d'intervention."""
    lat = data.latitude if data else None
    lng = data.longitude if data else None
    intervention = service.arrive_on_site(intervention_id, tech_id, lat, lng)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/start", response_model=InterventionResponse)
async def start_intervention(
    intervention_id: int,
    tech_id: int,
    data: InterventionStart | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Démarre l'intervention."""
    lat = data.latitude if data else None
    lng = data.longitude if data else None
    intervention = service.start_intervention(intervention_id, tech_id, lat, lng)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/complete", response_model=InterventionResponse)
async def complete_intervention(
    intervention_id: int,
    tech_id: int,
    data: InterventionComplete,
    service: FieldServiceService = Depends(get_service)
):
    """Complète l'intervention."""
    intervention = service.complete_intervention(intervention_id, tech_id, data)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/cancel", response_model=InterventionResponse)
async def cancel_intervention(
    intervention_id: int,
    reason: str,
    service: FieldServiceService = Depends(get_service)
):
    """Annule une intervention."""
    intervention = service.cancel_intervention(intervention_id, reason)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.post("/interventions/{intervention_id}/rate", response_model=InterventionResponse)
async def rate_intervention(
    intervention_id: int,
    rating: int = Query(..., ge=1, le=5),
    feedback: str | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Note une intervention (satisfaction client)."""
    intervention = service.rate_intervention(intervention_id, rating, feedback)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention non trouvée")
    return intervention

@router.get("/interventions/{intervention_id}/history")
async def get_intervention_history(
    intervention_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Historique d'une intervention."""
    return service.get_intervention_history(intervention_id)

# ============================================================================
# TIME ENTRIES
# ============================================================================

@router.get("/time-entries", response_model=list[TimeEntryResponse])
async def list_time_entries(
    technician_id: int | None = None,
    intervention_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    entry_type: str | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Liste les entrées de temps."""
    return service.list_time_entries(
        technician_id, intervention_id, date_from, date_to, entry_type
    )

@router.post("/time-entries", response_model=TimeEntryResponse)
async def create_time_entry(
    data: TimeEntryCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée une entrée de temps."""
    return service.create_time_entry(data)

@router.put("/time-entries/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour une entrée de temps."""
    entry = service.update_time_entry(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée non trouvée")
    return entry

# ============================================================================
# ROUTES
# ============================================================================

@router.get("/routes/{tech_id}/{route_date}", response_model=RouteResponse)
async def get_route(
    tech_id: int,
    route_date: date,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère la tournée d'un technicien."""
    route = service.get_route(tech_id, route_date)
    if not route:
        raise HTTPException(status_code=404, detail="Tournée non trouvée")
    return route

@router.post("/routes", response_model=RouteResponse)
async def create_route(
    data: RouteCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée une tournée."""
    return service.create_route(data)

@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: int,
    data: RouteUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour une tournée."""
    route = service.update_route(route_id, data)
    if not route:
        raise HTTPException(status_code=404, detail="Tournée non trouvée")
    return route

# ============================================================================
# EXPENSES
# ============================================================================

@router.get("/expenses", response_model=list[ExpenseResponse])
async def list_expenses(
    technician_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Liste les frais."""
    return service.list_expenses(technician_id, status, date_from, date_to)

@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(
    data: ExpenseCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée un frais."""
    return service.create_expense(data)

@router.post("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: int,
    approved_by: int,
    service: FieldServiceService = Depends(get_service)
):
    """Approuve un frais."""
    expense = service.approve_expense(expense_id, approved_by)
    if not expense:
        raise HTTPException(status_code=404, detail="Frais non trouvé")
    return expense

@router.post("/expenses/{expense_id}/reject", response_model=ExpenseResponse)
async def reject_expense(
    expense_id: int,
    reason: str,
    service: FieldServiceService = Depends(get_service)
):
    """Rejette un frais."""
    expense = service.reject_expense(expense_id, reason)
    if not expense:
        raise HTTPException(status_code=404, detail="Frais non trouvé")
    return expense

# ============================================================================
# CONTRACTS
# ============================================================================

@router.get("/contracts", response_model=list[ContractResponse])
async def list_contracts(
    customer_id: int | None = None,
    status: str | None = None,
    service: FieldServiceService = Depends(get_service)
):
    """Liste des contrats de service."""
    return service.list_contracts(customer_id, status)

@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    service: FieldServiceService = Depends(get_service)
):
    """Récupère un contrat."""
    contract = service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract

@router.post("/contracts", response_model=ContractResponse)
async def create_contract(
    data: ContractCreate,
    service: FieldServiceService = Depends(get_service)
):
    """Crée un contrat de service."""
    return service.create_contract(data)

@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    service: FieldServiceService = Depends(get_service)
):
    """Met à jour un contrat."""
    contract = service.update_contract(contract_id, data)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")
    return contract

# ============================================================================
# DASHBOARD & STATS
# ============================================================================

@router.get("/stats/interventions", response_model=InterventionStats)
async def get_intervention_stats(
    days: int = Query(30, ge=1, le=365),
    service: FieldServiceService = Depends(get_service)
):
    """Statistiques des interventions."""
    return service.get_intervention_stats(days)

@router.get("/stats/technicians")
async def get_technician_stats(
    days: int = Query(30, ge=1, le=365),
    service: FieldServiceService = Depends(get_service)
):
    """Statistiques par technicien."""
    return service.get_technician_stats(days)

@router.get("/dashboard", response_model=FieldServiceDashboard)
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    service: FieldServiceService = Depends(get_service)
):
    """Dashboard Field Service complet."""
    return service.get_dashboard(days)
