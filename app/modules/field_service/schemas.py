"""
AZALS MODULE 17 - Field Service Schemas
========================================
Schémas Pydantic pour la gestion des interventions terrain.
"""
from __future__ import annotations


import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import InterventionPriority, InterventionStatus, InterventionType, TechnicianStatus

# ============================================================================
# ZONE SCHEMAS
# ============================================================================

class ZoneBase(BaseModel):
    """Base zone."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = None
    country: str | None = None
    region: str | None = None
    postal_codes: list[str] | None = None
    geo_boundaries: dict[str, Any] | None = None
    manager_id: int | None = None
    default_team_id: int | None = None
    timezone: str = "Europe/Paris"


class ZoneCreate(ZoneBase):
    """Création zone."""
    pass


class ZoneUpdate(BaseModel):
    """Mise à jour zone."""
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    country: str | None = None
    region: str | None = None
    postal_codes: list[str] | None = None
    geo_boundaries: dict[str, Any] | None = None
    manager_id: int | None = None
    default_team_id: int | None = None
    timezone: str | None = None
    is_active: bool | None = None


class ZoneResponse(ZoneBase):
    """Réponse zone."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TECHNICIAN SCHEMAS
# ============================================================================

class TechnicianBase(BaseModel):
    """Base technicien."""
    user_id: int
    employee_id: str | None = None
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: str | None = None
    phone: str | None = None
    photo_url: str | None = None
    zone_id: int | None = None
    team_id: int | None = None
    skills: list[str] | None = None
    certifications: list[dict[str, Any]] | None = None
    languages: list[str] = ["fr"]
    has_vehicle: bool = True
    max_daily_interventions: int = 8
    working_hours: dict[str, Any] | None = None
    break_duration: int = 60


class TechnicianCreate(TechnicianBase):
    """Création technicien."""
    vehicle_id: int | None = None


class TechnicianUpdate(BaseModel):
    """Mise à jour technicien."""
    employee_id: str | None = None
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    email: str | None = None
    phone: str | None = None
    photo_url: str | None = None
    zone_id: int | None = None
    team_id: int | None = None
    vehicle_id: int | None = None
    skills: list[str] | None = None
    certifications: list[dict[str, Any]] | None = None
    languages: list[str] | None = None
    has_vehicle: bool | None = None
    max_daily_interventions: int | None = None
    working_hours: dict[str, Any] | None = None
    break_duration: int | None = None
    is_active: bool | None = None


class TechnicianResponse(TechnicianBase):
    """Réponse technicien."""
    id: int
    tenant_id: str
    vehicle_id: int | None = None
    status: TechnicianStatus
    last_location_lat: Decimal | None = None
    last_location_lng: Decimal | None = None
    last_location_at: datetime.datetime | None = None
    total_interventions: int
    completed_interventions: int
    avg_rating: Decimal
    total_km_traveled: Decimal
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class TechnicianStatusUpdate(BaseModel):
    """Mise à jour statut technicien."""
    status: TechnicianStatus
    latitude: Decimal | None = None
    longitude: Decimal | None = None


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
    vin: str | None = None
    name: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    vehicle_type: str | None = None
    color: str | None = None
    max_weight: Decimal | None = None
    max_volume: Decimal | None = None
    fuel_type: str | None = None
    fuel_capacity: Decimal | None = None


class VehicleCreate(VehicleBase):
    """Création véhicule."""
    pass


class VehicleUpdate(BaseModel):
    """Mise à jour véhicule."""
    registration: str | None = Field(None, max_length=50)
    vin: str | None = None
    name: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    vehicle_type: str | None = None
    color: str | None = None
    max_weight: Decimal | None = None
    max_volume: Decimal | None = None
    fuel_type: str | None = None
    fuel_capacity: Decimal | None = None
    current_odometer: int | None = None
    last_service_date: datetime.date | None = None
    next_service_date: datetime.date | None = None
    insurance_expiry: datetime.date | None = None
    registration_expiry: datetime.date | None = None
    is_active: bool | None = None


class VehicleResponse(VehicleBase):
    """Réponse véhicule."""
    id: int
    tenant_id: str
    tracker_id: str | None = None
    current_odometer: int
    last_location_lat: Decimal | None = None
    last_location_lng: Decimal | None = None
    last_location_at: datetime.datetime | None = None
    last_service_date: datetime.date | None = None
    next_service_date: datetime.date | None = None
    insurance_expiry: datetime.date | None = None
    registration_expiry: datetime.date | None = None
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INTERVENTION TEMPLATE SCHEMAS
# ============================================================================

class TemplateBase(BaseModel):
    """Base template."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: str | None = None
    intervention_type: InterventionType = InterventionType.MAINTENANCE
    estimated_duration: int = 60
    default_priority: InterventionPriority = InterventionPriority.NORMAL
    checklist_template: list[dict[str, Any]] | None = None
    required_skills: list[str] | None = None
    required_parts: list[dict[str, Any]] | None = None
    base_price: Decimal = Decimal("0")
    price_per_hour: Decimal = Decimal("0")


class TemplateCreate(TemplateBase):
    """Création template."""
    pass


class TemplateUpdate(BaseModel):
    """Mise à jour template."""
    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    intervention_type: InterventionType | None = None
    estimated_duration: int | None = None
    default_priority: InterventionPriority | None = None
    checklist_template: list[dict[str, Any]] | None = None
    required_skills: list[str] | None = None
    required_parts: list[dict[str, Any]] | None = None
    base_price: Decimal | None = None
    price_per_hour: Decimal | None = None
    is_active: bool | None = None


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: int
    tenant_id: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INTERVENTION SCHEMAS
# ============================================================================

class InterventionBase(BaseModel):
    """Base intervention."""
    title: str = Field(..., max_length=500)
    description: str | None = None
    intervention_type: InterventionType = InterventionType.MAINTENANCE
    priority: InterventionPriority = InterventionPriority.NORMAL
    customer_id: int | None = None
    customer_name: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None
    address_country: str = "France"
    address_lat: Decimal | None = None
    address_lng: Decimal | None = None
    access_instructions: str | None = None
    estimated_duration: int = 60
    billable: bool = True


class InterventionCreate(InterventionBase):
    """Création intervention."""
    template_id: int | None = None
    technician_id: int | None = None
    zone_id: int | None = None
    scheduled_date: datetime.date | None = None
    scheduled_time_start: datetime.time | None = None
    scheduled_time_end: datetime.time | None = None
    ticket_id: int | None = None
    maintenance_id: int | None = None
    sales_order_id: int | None = None


class InterventionUpdate(BaseModel):
    """Mise à jour intervention."""
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    internal_notes: str | None = None
    intervention_type: InterventionType | None = None
    priority: InterventionPriority | None = None
    status: InterventionStatus | None = None
    technician_id: int | None = None
    zone_id: int | None = None
    scheduled_date: datetime.date | None = None
    scheduled_time_start: datetime.time | None = None
    scheduled_time_end: datetime.time | None = None
    estimated_duration: int | None = None
    customer_id: int | None = None
    customer_name: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None
    address_lat: Decimal | None = None
    address_lng: Decimal | None = None
    access_instructions: str | None = None
    checklist: list[dict[str, Any]] | None = None
    billable: bool | None = None


class InterventionAssign(BaseModel):
    """Assignation intervention."""
    technician_id: int
    scheduled_date: datetime.date | None = None
    scheduled_time_start: datetime.time | None = None
    scheduled_time_end: datetime.time | None = None


class InterventionStart(BaseModel):
    """Démarrage intervention."""
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class InterventionComplete(BaseModel):
    """Complétion intervention."""
    completion_notes: str | None = None
    checklist: list[dict[str, Any]] | None = None
    parts_used: list[dict[str, Any]] | None = None
    labor_hours: Decimal | None = None
    signature_data: str | None = None
    signature_name: str | None = None
    photos: list[dict[str, Any]] | None = None


class InterventionResponse(InterventionBase):
    """Réponse intervention."""
    id: int
    tenant_id: str
    reference: str
    template_id: int | None = None
    status: InterventionStatus
    technician_id: int | None = None
    zone_id: int | None = None
    scheduled_date: datetime.date | None = None
    scheduled_time_start: datetime.time | None = None
    scheduled_time_end: datetime.time | None = None
    actual_start: datetime.datetime | None = None
    actual_end: datetime.datetime | None = None
    arrival_time: datetime.datetime | None = None
    departure_time: datetime.datetime | None = None
    internal_notes: str | None = None
    completion_notes: str | None = None
    failure_reason: str | None = None
    checklist: list[dict[str, Any]] | None = None
    photos: list[dict[str, Any]] | None = None
    parts_used: list[dict[str, Any]] | None = None
    labor_hours: Decimal
    labor_cost: Decimal
    parts_cost: Decimal
    travel_cost: Decimal
    total_cost: Decimal
    invoice_id: int | None = None
    customer_rating: int | None = None
    customer_feedback: str | None = None
    ticket_id: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TIME ENTRY SCHEMAS
# ============================================================================

class TimeEntryBase(BaseModel):
    """Base pointage."""
    entry_type: str = Field(..., max_length=50)
    start_time: datetime.datetime
    end_time: datetime.datetime | None = None
    start_lat: Decimal | None = None
    start_lng: Decimal | None = None
    end_lat: Decimal | None = None
    end_lng: Decimal | None = None
    distance_km: Decimal | None = None
    notes: str | None = None
    is_billable: bool = True


class TimeEntryCreate(TimeEntryBase):
    """Création pointage."""
    technician_id: int
    intervention_id: int | None = None


class TimeEntryUpdate(BaseModel):
    """Mise à jour pointage."""
    end_time: datetime.datetime | None = None
    end_lat: Decimal | None = None
    end_lng: Decimal | None = None
    distance_km: Decimal | None = None
    notes: str | None = None
    is_billable: bool | None = None


class TimeEntryResponse(TimeEntryBase):
    """Réponse pointage."""
    id: int
    tenant_id: str
    technician_id: int
    intervention_id: int | None = None
    duration_minutes: int | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ROUTE SCHEMAS
# ============================================================================

class RouteBase(BaseModel):
    """Base tournée."""
    route_date: datetime.date
    start_location: str | None = None
    start_lat: Decimal | None = None
    start_lng: Decimal | None = None
    start_time: datetime.time | None = None
    end_location: str | None = None
    end_lat: Decimal | None = None
    end_lng: Decimal | None = None
    end_time: datetime.time | None = None


class RouteCreate(RouteBase):
    """Création tournée."""
    technician_id: int
    intervention_order: list[int] | None = None


class RouteUpdate(BaseModel):
    """Mise à jour tournée."""
    start_location: str | None = None
    start_lat: Decimal | None = None
    start_lng: Decimal | None = None
    start_time: datetime.time | None = None
    end_location: str | None = None
    end_lat: Decimal | None = None
    end_lng: Decimal | None = None
    end_time: datetime.time | None = None
    intervention_order: list[int] | None = None
    status: str | None = None


class RouteResponse(RouteBase):
    """Réponse tournée."""
    id: int
    tenant_id: str
    technician_id: int
    planned_distance: Decimal | None = None
    planned_duration: int | None = None
    planned_interventions: int | None = None
    actual_distance: Decimal | None = None
    actual_duration: int | None = None
    completed_interventions: int
    is_optimized: bool
    optimization_score: Decimal | None = None
    intervention_order: list[int] | None = None
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EXPENSE SCHEMAS
# ============================================================================

class ExpenseBase(BaseModel):
    """Base frais."""
    expense_type: str = Field(..., max_length=50)
    description: str | None = None
    amount: Decimal
    currency: str = "EUR"
    expense_date: datetime.date
    receipt_url: str | None = None
    receipt_number: str | None = None
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    """Création frais."""
    technician_id: int
    intervention_id: int | None = None


class ExpenseUpdate(BaseModel):
    """Mise à jour frais."""
    expense_type: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    expense_date: datetime.date | None = None
    receipt_url: str | None = None
    receipt_number: str | None = None
    notes: str | None = None
    status: str | None = None


class ExpenseResponse(ExpenseBase):
    """Réponse frais."""
    id: int
    tenant_id: str
    technician_id: int
    intervention_id: int | None = None
    status: str
    approved_by: int | None = None
    approved_at: datetime.datetime | None = None
    paid_at: datetime.datetime | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CONTRACT SCHEMAS
# ============================================================================

class ContractBase(BaseModel):
    """Base contrat."""
    contract_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    customer_id: int
    customer_name: str | None = None
    start_date: datetime.date
    end_date: datetime.date | None = None
    auto_renew: bool = False
    contract_type: str | None = None
    response_time_hours: int = 24
    resolution_time_hours: int = 72
    included_interventions: int | None = None
    monthly_fee: Decimal = Decimal("0")
    hourly_rate: Decimal | None = None
    parts_discount: Decimal = Decimal("0")
    covered_equipment: list[int] | None = None


class ContractCreate(ContractBase):
    """Création contrat."""
    pass


class ContractUpdate(BaseModel):
    """Mise à jour contrat."""
    name: str | None = Field(None, max_length=255)
    customer_name: str | None = None
    end_date: datetime.date | None = None
    auto_renew: bool | None = None
    contract_type: str | None = None
    response_time_hours: int | None = None
    resolution_time_hours: int | None = None
    included_interventions: int | None = None
    monthly_fee: Decimal | None = None
    hourly_rate: Decimal | None = None
    parts_discount: Decimal | None = None
    covered_equipment: list[int] | None = None
    status: str | None = None


class ContractResponse(ContractBase):
    """Réponse contrat."""
    id: int
    tenant_id: str
    interventions_used: int
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


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
    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    avg_completion_time: float = 0.0
    sla_met_rate: float = 0.0


class FieldServiceDashboard(BaseModel):
    """Dashboard Field Service."""
    intervention_stats: InterventionStats
    technician_stats: list[TechnicianStats] = []
    today_interventions: int = 0
    active_technicians: int = 0
    pending_assignments: int = 0
    overdue_interventions: int = 0
    total_revenue: Decimal = Decimal("0")
    avg_satisfaction: float = 0.0
