"""
AZALS MODULE 17 - Field Service Models
=======================================
Modèles SQLAlchemy pour la gestion des interventions terrain.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base
from app.core.types import JSON, UniversalUUID
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional

# ============================================================================
# ENUMS
# ============================================================================

class TechnicianStatus(str, PyEnum):
    """Statut technicien."""
    AVAILABLE = "available"
    ON_MISSION = "on_mission"
    TRAVELING = "traveling"
    BREAK = "break"
    OFF_DUTY = "off_duty"
    SICK = "sick"


class InterventionStatus(str, PyEnum):
    """Statut intervention."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class InterventionPriority(str, PyEnum):
    """Priorité intervention."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class InterventionType(str, PyEnum):
    """Type intervention."""
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INSPECTION = "inspection"
    DELIVERY = "delivery"
    PICKUP = "pickup"
    TRAINING = "training"
    CONSULTATION = "consultation"


# ============================================================================
# ZONES & REGIONS
# ============================================================================

class ServiceZone(Base):
    """Zone de service."""
    __tablename__ = "fs_zones"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Géographie
    country: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    postal_codes: Mapped[Optional[dict]] = mapped_column(JSON)  # ["75001", "75002", ...]
    geo_boundaries: Mapped[Optional[dict]] = mapped_column(JSON)  # GeoJSON ou coordonnées

    # Configuration
    manager_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    default_team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    timezone: Mapped[Optional[str]] = mapped_column(String(50), default="Europe/Paris")

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    technicians = relationship("app.modules.field_service.models.Technician", back_populates="zone")

    __table_args__ = (
        Index('idx_fs_zone_tenant', 'tenant_id'),
        Index('idx_fs_zone_code', 'tenant_id', 'code', unique=True),
    )


# ============================================================================
# TECHNICIANS
# ============================================================================

class Technician(Base):
    """Technicien terrain."""
    __tablename__ = "fs_technicians"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Lien utilisateur
    user_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50))  # Lien RH

    # Profil
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Zone et équipe
    zone_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_zones.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Statut
    status: Mapped[Optional[str]] = mapped_column(Enum(TechnicianStatus), default=TechnicianStatus.OFF_DUTY)
    last_location_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    last_location_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    last_location_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Compétences
    skills: Mapped[Optional[dict]] = mapped_column(JSON)  # ["electrical", "plumbing", "hvac"]
    certifications: Mapped[Optional[dict]] = mapped_column(JSON)  # [{name, expiry_date}, ...]
    languages: Mapped[Optional[dict]] = mapped_column(JSON, default=["fr"])

    # Véhicule
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_vehicles.id"))
    has_vehicle: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    # Paramètres
    max_daily_interventions: Mapped[Optional[int]] = mapped_column(Integer, default=8)
    working_hours: Mapped[Optional[dict]] = mapped_column(JSON)  # {mon: {start: "08:00", end: "17:00"}, ...}
    break_duration: Mapped[Optional[int]] = mapped_column(Integer, default=60)  # Minutes

    # Stats
    total_interventions: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    completed_interventions: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=0)
    total_km_traveled: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    zone = relationship("app.modules.field_service.models.ServiceZone", back_populates="technicians")
    vehicle = relationship("app.modules.field_service.models.Vehicle", back_populates="assigned_technician")
    interventions = relationship("app.modules.field_service.models.Intervention", back_populates="technician")
    time_entries = relationship("app.modules.field_service.models.FSTimeEntry", back_populates="technician")

    __table_args__ = (
        Index('idx_fs_tech_tenant', 'tenant_id'),
        Index('idx_fs_tech_user', 'tenant_id', 'user_id', unique=True),
        Index('idx_fs_tech_zone', 'zone_id'),
        Index('idx_fs_tech_status', 'tenant_id', 'status'),
    )


# ============================================================================
# VEHICLES
# ============================================================================

class Vehicle(Base):
    """Véhicule de service."""
    __tablename__ = "fs_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    registration: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    vin: Mapped[Optional[str]] = mapped_column(String(50))
    name: Mapped[Optional[str]] = mapped_column(String(100))

    # Caractéristiques
    make: Mapped[Optional[str]] = mapped_column(String(100))  # Marque
    model: Mapped[Optional[str]] = mapped_column(String(100))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50))  # van, truck, car
    color: Mapped[Optional[str]] = mapped_column(String(50))

    # Capacité
    max_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # kg
    max_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # m³

    # Suivi
    current_odometer: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(50))  # diesel, electric, hybrid
    fuel_capacity: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))

    # GPS Tracker
    tracker_id: Mapped[Optional[str]] = mapped_column(String(100))
    last_location_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    last_location_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    last_location_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Maintenance
    last_service_date: Mapped[Optional[date]] = mapped_column(Date)
    next_service_date: Mapped[Optional[date]] = mapped_column(Date)
    next_service_odometer: Mapped[Optional[int]] = mapped_column(Integer)

    # Assurance
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date)
    registration_expiry: Mapped[Optional[date]] = mapped_column(Date)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    assigned_technician = relationship("app.modules.field_service.models.Technician", back_populates="vehicle", uselist=False)

    __table_args__ = (
        Index('idx_fs_vehicle_tenant', 'tenant_id'),
        Index('idx_fs_vehicle_reg', 'tenant_id', 'registration', unique=True),
    )


# ============================================================================
# INTERVENTION TYPES & TEMPLATES
# ============================================================================

class InterventionTemplate(Base):
    """Template d'intervention."""
    __tablename__ = "fs_intervention_templates"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Configuration
    intervention_type: Mapped[Optional[str]] = mapped_column(Enum(InterventionType), default=InterventionType.MAINTENANCE)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, default=60)  # Minutes
    default_priority: Mapped[Optional[str]] = mapped_column(Enum(InterventionPriority), default=InterventionPriority.NORMAL)

    # Checklist par défaut
    checklist_template: Mapped[Optional[dict]] = mapped_column(JSON)  # [{task, required}, ...]

    # Compétences requises
    required_skills: Mapped[Optional[dict]] = mapped_column(JSON)  # ["electrical", "hvac"]

    # Matériel requis
    required_parts: Mapped[Optional[dict]] = mapped_column(JSON)  # [{part_id, quantity}, ...]

    # Prix
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    price_per_hour: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_template_tenant', 'tenant_id'),
        Index('idx_fs_template_code', 'tenant_id', 'code', unique=True),
    )


# ============================================================================
# INTERVENTIONS
# ============================================================================

class Intervention(Base):
    """Intervention terrain."""
    __tablename__ = "fs_interventions"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, unique=True)
    template_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_intervention_templates.id"))

    # Type et statut
    intervention_type: Mapped[Optional[str]] = mapped_column(Enum(InterventionType), default=InterventionType.MAINTENANCE)
    status: Mapped[Optional[str]] = mapped_column(Enum(InterventionStatus), default=InterventionStatus.DRAFT)
    priority: Mapped[Optional[str]] = mapped_column(Enum(InterventionPriority), default=InterventionPriority.NORMAL)

    # Description
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), index=True)  # CRM customer
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Adresse intervention
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    address_country: Mapped[Optional[str]] = mapped_column(String(100), default="France")
    address_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    address_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    access_instructions: Mapped[Optional[str]] = mapped_column(Text)

    # Assignation
    technician_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_technicians.id"))
    zone_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_zones.id"))

    # Planification
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    scheduled_time_start: Mapped[Optional[time]] = mapped_column(Time)
    scheduled_time_end: Mapped[Optional[time]] = mapped_column(Time)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, default=60)  # Minutes

    # Exécution
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    departure_time: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Résultat
    completion_notes: Mapped[Optional[str]] = mapped_column(Text)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    next_action: Mapped[Optional[str]] = mapped_column(Text)

    # Signature client
    signature_data: Mapped[Optional[str]] = mapped_column(Text)  # Base64
    signature_name: Mapped[Optional[str]] = mapped_column(String(255))
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Checklist
    checklist: Mapped[Optional[dict]] = mapped_column(JSON)  # [{task, completed, notes}, ...]

    # Photos
    photos: Mapped[Optional[dict]] = mapped_column(JSON)  # [{url, caption, taken_at}, ...]

    # Pièces utilisées
    parts_used: Mapped[Optional[dict]] = mapped_column(JSON)  # [{part_id, quantity, price}, ...]

    # Facturation
    billable: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    labor_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), default=0)
    labor_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    parts_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    travel_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    # Satisfaction
    customer_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    customer_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Récurrence
    is_recurring: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[dict]] = mapped_column(JSON)  # {frequency, interval, until}
    parent_intervention_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_interventions.id"))

    # Liens
    ticket_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # Helpdesk ticket
    maintenance_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # M8 Maintenance
    sales_order_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())  # M1 Commercial

    # Dates
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    technician = relationship("app.modules.field_service.models.Technician", back_populates="interventions")
    time_entries = relationship("app.modules.field_service.models.FSTimeEntry", back_populates="intervention")
    history = relationship("app.modules.field_service.models.InterventionHistory", back_populates="intervention")

    __table_args__ = (
        Index('idx_fs_intervention_tenant', 'tenant_id'),
        Index('idx_fs_intervention_ref', 'reference'),
        Index('idx_fs_intervention_status', 'tenant_id', 'status'),
        Index('idx_fs_intervention_tech', 'technician_id'),
        Index('idx_fs_intervention_date', 'tenant_id', 'scheduled_date'),
        Index('idx_fs_intervention_customer', 'tenant_id', 'customer_id'),
    )


class InterventionHistory(Base):
    """Historique intervention."""
    __tablename__ = "fs_intervention_history"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)
    intervention_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_interventions.id"), nullable=False)

    # Changement
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(50))
    old_value: Mapped[Optional[str]] = mapped_column(String(500))
    new_value: Mapped[Optional[str]] = mapped_column(String(500))

    # Auteur
    actor_type: Mapped[Optional[str]] = mapped_column(String(20))  # technician, dispatcher, customer, system
    actor_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    actor_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Localisation
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    intervention = relationship("app.modules.field_service.models.Intervention", back_populates="history")

    __table_args__ = (
        Index('idx_fs_history_intervention', 'intervention_id'),
    )


# ============================================================================
# TIME TRACKING
# ============================================================================

class FSTimeEntry(Base):
    """Pointage temps."""
    __tablename__ = "fs_time_entries"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    technician_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_technicians.id"), nullable=False)
    intervention_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_interventions.id"))

    # Type
    entry_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # work, travel, break, admin

    # Temps
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Localisation
    start_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    start_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    end_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    end_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))

    # Distance (pour travel)
    distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_billable: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    technician = relationship("app.modules.field_service.models.Technician", back_populates="time_entries")
    intervention = relationship("app.modules.field_service.models.Intervention", back_populates="time_entries")

    __table_args__ = (
        Index('idx_fs_time_tech', 'technician_id'),
        Index('idx_fs_time_intervention', 'intervention_id'),
        Index('idx_fs_time_date', 'tenant_id', 'start_time'),
    )


# ============================================================================
# PARTS & INVENTORY
# ============================================================================

class PartUsage(Base):
    """Utilisation pièces."""
    __tablename__ = "fs_part_usage"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    intervention_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_interventions.id"), nullable=False)
    technician_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_technicians.id"))

    # Pièce
    part_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), index=True)  # Stock module
    part_code: Mapped[Optional[str]] = mapped_column(String(50))
    part_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Quantité
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), default="unit")

    # Prix
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)

    # Source
    from_vehicle_stock: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID())

    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_parts_intervention', 'intervention_id'),
        Index('idx_fs_parts_part', 'part_id'),
    )


# ============================================================================
# SCHEDULING & ROUTING
# ============================================================================

class Route(Base):
    """Tournée planifiée."""
    __tablename__ = "fs_routes"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    technician_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_technicians.id"), nullable=False)
    route_date: Mapped[date] = mapped_column(Date)

    # Planning
    start_location: Mapped[Optional[str]] = mapped_column(String(255))
    start_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    start_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    start_time: Mapped[Optional[time]] = mapped_column(Time)

    end_location: Mapped[Optional[str]] = mapped_column(String(255))
    end_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    end_lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    end_time: Mapped[Optional[time]] = mapped_column(Time)

    # Statistiques prévues
    planned_distance: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # km
    planned_duration: Mapped[Optional[int]] = mapped_column(Integer)  # minutes
    planned_interventions: Mapped[Optional[int]] = mapped_column(Integer)

    # Réalité
    actual_distance: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    actual_duration: Mapped[Optional[int]] = mapped_column(Integer)
    completed_interventions: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Optimisation
    is_optimized: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    optimization_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Interventions ordonnées
    intervention_order: Mapped[Optional[dict]] = mapped_column(JSON)  # [intervention_id1, intervention_id2, ...]

    status: Mapped[Optional[str]] = mapped_column(String(20), default="planned")  # planned, in_progress, completed
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_route_tenant', 'tenant_id'),
        Index('idx_fs_route_tech_date', 'technician_id', 'route_date', unique=True),
    )


# ============================================================================
# EXPENSES
# ============================================================================

class Expense(Base):
    """Frais technicien."""
    __tablename__ = "fs_expenses"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    technician_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_technicians.id"), nullable=False)
    intervention_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), ForeignKey("fs_interventions.id"))

    # Type
    expense_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)  # fuel, parking, toll, meal, other
    description: Mapped[Optional[str]] = mapped_column(String(255))

    # Montant
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="EUR")

    # Justificatif
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500))
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100))

    # Date
    expense_date: Mapped[date] = mapped_column(Date)

    # Remboursement
    status: Mapped[Optional[str]] = mapped_column(String(20), default="pending")  # pending, approved, rejected, paid
    approved_by: Mapped[uuid.UUID] = mapped_column(UniversalUUID())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_expense_tech', 'technician_id'),
        Index('idx_fs_expense_date', 'tenant_id', 'expense_date'),
        Index('idx_fs_expense_status', 'tenant_id', 'status'),
    )


# ============================================================================
# SLA & CONTRACTS
# ============================================================================

class ServiceContract(Base):
    """Contrat de service."""
    __tablename__ = "fs_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, index=True)

    # Identification
    contract_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    # Client
    customer_id: Mapped[uuid.UUID] = mapped_column(UniversalUUID(), nullable=False, index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Période
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    auto_renew: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Type
    contract_type: Mapped[Optional[str]] = mapped_column(String(50))  # maintenance, support, full_service

    # SLA
    response_time_hours: Mapped[Optional[int]] = mapped_column(Integer, default=24)
    resolution_time_hours: Mapped[Optional[int]] = mapped_column(Integer, default=72)
    included_interventions: Mapped[Optional[int]] = mapped_column(Integer)
    interventions_used: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Tarifs
    monthly_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0)
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    parts_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), default=0)  # %

    # Équipements couverts
    covered_equipment: Mapped[Optional[dict]] = mapped_column(JSON)  # [equipment_id, ...]

    status: Mapped[Optional[str]] = mapped_column(String(20), default="active")  # draft, active, suspended, expired
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_contract_tenant', 'tenant_id'),
        Index('idx_fs_contract_number', 'tenant_id', 'contract_number', unique=True),
        Index('idx_fs_contract_customer', 'tenant_id', 'customer_id'),
    )
