"""
AZALS MODULE 17 - Field Service Schemas
========================================
Schémas Pydantic pour la gestion des interventions terrain.
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .models import (
    TechnicianStatus, InterventionStatus,
    InterventionPriority, InterventionType
)


# ============================================================================
# ZONE SCHEMAS
# ============================================================================

class ZoneBase(BaseModel):
    """Base zone."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    postal_codes: Optional[List[str]] = None
    geo_boundaries: Optional[Dict[str, Any]] = None
    manager_id: Optional[int] = None
    default_team_id: Optional[int] = None
    timezone: str = "Europe/Paris"


class ZoneCreate(ZoneBase):
    """Création zone."""
    pass


class ZoneUpdate(BaseModel):
    """Mise à jour zone."""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    postal_codes: Optional[List[str]] = None
    geo_boundaries: Optional[Dict[str, Any]] = None
    manager_id: Optional[int] = None
    default_team_id: Optional[int] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    """Réponse zone."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TECHNICIAN SCHEMAS
# ============================================================================

class TechnicianBase(BaseModel):
    """Base technicien."""
    user_id: int
    employee_id: Optional[str] = None
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    zone_id: Optional[int] = None
    team_id: Optional[int] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    languages: List[str] = ["fr"]
    has_vehicle: bool = True
    max_daily_interventions: int = 8
    working_hours: Optional[Dict[str, Any]] = None
    break_duration: int = 60


class TechnicianCreate(TechnicianBase):
    """Création technicien."""
    vehicle_id: Optional[int] = None


class TechnicianUpdate(BaseModel):
    """Mise à jour technicien."""
    employee_id: Optional[str] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    zone_id: Optional[int] = None
    team_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    languages: Optional[List[str]] = None
    has_vehicle: Optional[bool] = None
    max_daily_interventions: Optional[int] = None
    working_hours: Optional[Dict[str, Any]] = None
    break_duration: Optional[int] = None
    is_active: Optional[bool] = None


class TechnicianResponse(TechnicianBase):
    """Réponse technicien."""
    id: int
    tenant_id: str
    vehicle_id: Optional[int] = None
    status: TechnicianStatus
    last_location_lat: Optional[Decimal] = None
    last_location_lng: Optional[Decimal] = None
    last_location_at: Optional[datetime] = None
    total_interventions: int
    completed_interventions: int
    avg_rating: Decimal
    total_km_traveled: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TechnicianStatusUpdate(BaseModel):
    """Mise à jour statut technicien."""
    status: TechnicianStatus
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class TechnicianLocation(BaseModel):
    """Mise à jour position technicien."""
    latitude: Decimal
    longitude: Decimal


# ============================================================================
# VEHICLE SCHEMAS
# ============================================================================

class VehicleBase(BaseModel):
    """Base véhicule."""
    registration: str = Field(..., max_length=50)
    vin: Optional[str] = None
    name: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[str] = None
    color: Optional[str] = None
    max_weight: Optional[Decimal] = None
    max_volume: Optional[Decimal] = None
    fuel_type: Optional[str] = None
    fuel_capacity: Optional[Decimal] = None


class VehicleCreate(VehicleBase):
    """Création véhicule."""
    pass


class VehicleUpdate(BaseModel):
    """Mise à jour véhicule."""
    registration: Optional[str] = Field(None, max_length=50)
    vin: Optional[str] = None
    name: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[str] = None
    color: Optional[str] = None
    max_weight: Optional[Decimal] = None
    max_volume: Optional[Decimal] = None
    fuel_type: Optional[str] = None
    fuel_capacity: Optional[Decimal] = None
    current_odometer: Optional[int] = None
    last_service_date: Optional[date] = None
    next_service_date: Optional[date] = None
    insurance_expiry: Optional[date] = None
    registration_expiry: Optional[date] = None
    is_active: Optional[bool] = None


class VehicleResponse(VehicleBase):
    """Réponse véhicule."""
    id: int
    tenant_id: str
    tracker_id: Optional[str] = None
    current_odometer: int
    last_location_lat: Optional[Decimal] = None
    last_location_lng: Optional[Decimal] = None
    last_location_at: Optional[datetime] = None
    last_service_date: Optional[date] = None
    next_service_date: Optional[date] = None
    insurance_expiry: Optional[date] = None
    registration_expiry: Optional[date] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INTERVENTION TEMPLATE SCHEMAS
# ============================================================================

class TemplateBase(BaseModel):
    """Base template."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    intervention_type: InterventionType = InterventionType.MAINTENANCE
    estimated_duration: int = 60
    default_priority: InterventionPriority = InterventionPriority.NORMAL
    checklist_template: Optional[List[Dict[str, Any]]] = None
    required_skills: Optional[List[str]] = None
    required_parts: Optional[List[Dict[str, Any]]] = None
    base_price: Decimal = Decimal("0")
    price_per_hour: Decimal = Decimal("0")


class TemplateCreate(TemplateBase):
    """Création template."""
    pass


class TemplateUpdate(BaseModel):
    """Mise à jour template."""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    intervention_type: Optional[InterventionType] = None
    estimated_duration: Optional[int] = None
    default_priority: Optional[InterventionPriority] = None
    checklist_template: Optional[List[Dict[str, Any]]] = None
    required_skills: Optional[List[str]] = None
    required_parts: Optional[List[Dict[str, Any]]] = None
    base_price: Optional[Decimal] = None
    price_per_hour: Optional[Decimal] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INTERVENTION SCHEMAS
# ============================================================================

class InterventionBase(BaseModel):
    """Base intervention."""
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    intervention_type: InterventionType = InterventionType.MAINTENANCE
    priority: InterventionPriority = InterventionPriority.NORMAL
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: str = "France"
    address_lat: Optional[Decimal] = None
    address_lng: Optional[Decimal] = None
    access_instructions: Optional[str] = None
    estimated_duration: int = 60
    billable: bool = True


class InterventionCreate(InterventionBase):
    """Création intervention."""
    template_id: Optional[int] = None
    technician_id: Optional[int] = None
    zone_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    scheduled_time_start: Optional[time] = None
    scheduled_time_end: Optional[time] = None
    ticket_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    sales_order_id: Optional[int] = None


class InterventionUpdate(BaseModel):
    """Mise à jour intervention."""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    intervention_type: Optional[InterventionType] = None
    priority: Optional[InterventionPriority] = None
    status: Optional[InterventionStatus] = None
    technician_id: Optional[int] = None
    zone_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    scheduled_time_start: Optional[time] = None
    scheduled_time_end: Optional[time] = None
    estimated_duration: Optional[int] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_lat: Optional[Decimal] = None
    address_lng: Optional[Decimal] = None
    access_instructions: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    billable: Optional[bool] = None


class InterventionAssign(BaseModel):
    """Assignation intervention."""
    technician_id: int
    scheduled_date: Optional[date] = None
    scheduled_time_start: Optional[time] = None
    scheduled_time_end: Optional[time] = None


class InterventionStart(BaseModel):
    """Démarrage intervention."""
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class InterventionComplete(BaseModel):
    """Complétion intervention."""
    completion_notes: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    labor_hours: Optional[Decimal] = None
    signature_data: Optional[str] = None
    signature_name: Optional[str] = None
    photos: Optional[List[Dict[str, Any]]] = None


class InterventionResponse(InterventionBase):
    """Réponse intervention."""
    id: int
    tenant_id: str
    reference: str
    template_id: Optional[int] = None
    status: InterventionStatus
    technician_id: Optional[int] = None
    zone_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    scheduled_time_start: Optional[time] = None
    scheduled_time_end: Optional[time] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    internal_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    failure_reason: Optional[str] = None
    checklist: Optional[List[Dict[str, Any]]] = None
    photos: Optional[List[Dict[str, Any]]] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    labor_hours: Decimal
    labor_cost: Decimal
    parts_cost: Decimal
    travel_cost: Decimal
    total_cost: Decimal
    invoice_id: Optional[int] = None
    customer_rating: Optional[int] = None
    customer_feedback: Optional[str] = None
    ticket_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TIME ENTRY SCHEMAS
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pointage."""
    entry_type: str = Field(..., max_length=50)
    start_time: datetime
    end_time: Optional[datetime] = None
    start_lat: Optional[Decimal] = None
    start_lng: Optional[Decimal] = None
    end_lat: Optional[Decimal] = None
    end_lng: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    notes: Optional[str] = None
    is_billable: bool = True


class TimeEntryCreate(TimeEntryBase):
    """Création pointage."""
    technician_id: int
    intervention_id: Optional[int] = None


class TimeEntryUpdate(BaseModel):
    """Mise à jour pointage."""
    end_time: Optional[datetime] = None
    end_lat: Optional[Decimal] = None
    end_lng: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    notes: Optional[str] = None
    is_billable: Optional[bool] = None


class TimeEntryResponse(TimeEntryBase):
    """Réponse pointage."""
    id: int
    tenant_id: str
    technician_id: int
    intervention_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ROUTE SCHEMAS
# ============================================================================

class RouteBase(BaseModel):
    """Base tournée."""
    route_date: date
    start_location: Optional[str] = None
    start_lat: Optional[Decimal] = None
    start_lng: Optional[Decimal] = None
    start_time: Optional[time] = None
    end_location: Optional[str] = None
    end_lat: Optional[Decimal] = None
    end_lng: Optional[Decimal] = None
    end_time: Optional[time] = None


class RouteCreate(RouteBase):
    """Création tournée."""
    technician_id: int
    intervention_order: Optional[List[int]] = None


class RouteUpdate(BaseModel):
    """Mise à jour tournée."""
    start_location: Optional[str] = None
    start_lat: Optional[Decimal] = None
    start_lng: Optional[Decimal] = None
    start_time: Optional[time] = None
    end_location: Optional[str] = None
    end_lat: Optional[Decimal] = None
    end_lng: Optional[Decimal] = None
    end_time: Optional[time] = None
    intervention_order: Optional[List[int]] = None
    status: Optional[str] = None


class RouteResponse(RouteBase):
    """Réponse tournée."""
    id: int
    tenant_id: str
    technician_id: int
    planned_distance: Optional[Decimal] = None
    planned_duration: Optional[int] = None
    planned_interventions: Optional[int] = None
    actual_distance: Optional[Decimal] = None
    actual_duration: Optional[int] = None
    completed_interventions: int
    is_optimized: bool
    optimization_score: Optional[Decimal] = None
    intervention_order: Optional[List[int]] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EXPENSE SCHEMAS
# ============================================================================

class ExpenseBase(BaseModel):
    """Base frais."""
    expense_type: str = Field(..., max_length=50)
    description: Optional[str] = None
    amount: Decimal
    currency: str = "EUR"
    expense_date: date
    receipt_url: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    """Création frais."""
    technician_id: int
    intervention_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    """Mise à jour frais."""
    expense_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    receipt_url: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    """Réponse frais."""
    id: int
    tenant_id: str
    technician_id: int
    intervention_id: Optional[int] = None
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CONTRACT SCHEMAS
# ============================================================================

class ContractBase(BaseModel):
    """Base contrat."""
    contract_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    customer_id: int
    customer_name: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    auto_renew: bool = False
    contract_type: Optional[str] = None
    response_time_hours: int = 24
    resolution_time_hours: int = 72
    included_interventions: Optional[int] = None
    monthly_fee: Decimal = Decimal("0")
    hourly_rate: Optional[Decimal] = None
    parts_discount: Decimal = Decimal("0")
    covered_equipment: Optional[List[int]] = None


class ContractCreate(ContractBase):
    """Création contrat."""
    pass


class ContractUpdate(BaseModel):
    """Mise à jour contrat."""
    name: Optional[str] = Field(None, max_length=255)
    customer_name: Optional[str] = None
    end_date: Optional[date] = None
    auto_renew: Optional[bool] = None
    contract_type: Optional[str] = None
    response_time_hours: Optional[int] = None
    resolution_time_hours: Optional[int] = None
    included_interventions: Optional[int] = None
    monthly_fee: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    parts_discount: Optional[Decimal] = None
    covered_equipment: Optional[List[int]] = None
    status: Optional[str] = None


class ContractResponse(ContractBase):
    """Réponse contrat."""
    id: int
    tenant_id: str
    interventions_used: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD & STATS
# ============================================================================

class TechnicianStats(BaseModel):
    """Statistiques technicien."""
    technician_id: int
    technician_name: str
    total_interventions: int = 0
    completed: int = 0
    cancelled: int = 0
    avg_duration: float = 0.0
    avg_rating: float = 0.0
    total_km: float = 0.0
    total_revenue: float = 0.0


class InterventionStats(BaseModel):
    """Statistiques interventions."""
    total: int = 0
    scheduled: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0
    by_type: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    avg_completion_time: float = 0.0
    sla_met_rate: float = 0.0


class FieldServiceDashboard(BaseModel):
    """Dashboard Field Service."""
    intervention_stats: InterventionStats
    technician_stats: List[TechnicianStats] = []
    today_interventions: int = 0
    active_technicians: int = 0
    pending_assignments: int = 0
    overdue_interventions: int = 0
    total_revenue: Decimal = Decimal("0")
    avg_satisfaction: float = 0.0
