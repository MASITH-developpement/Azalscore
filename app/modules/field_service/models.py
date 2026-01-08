"""
AZALS MODULE 17 - Field Service Models
=======================================
Modèles SQLAlchemy pour la gestion des interventions terrain.
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Numeric, Enum, Index, JSON, Date, Time
)
from sqlalchemy.orm import relationship

from app.core.database import Base


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Géographie
    country = Column(String(100))
    region = Column(String(100))
    postal_codes = Column(JSON)  # ["75001", "75002", ...]
    geo_boundaries = Column(JSON)  # GeoJSON ou coordonnées

    # Configuration
    manager_id = Column(Integer)
    default_team_id = Column(Integer)
    timezone = Column(String(50), default="Europe/Paris")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Lien utilisateur
    user_id = Column(Integer, nullable=False, index=True)
    employee_id = Column(String(50))  # Lien RH

    # Profil
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    photo_url = Column(String(500))

    # Zone et équipe
    zone_id = Column(Integer, ForeignKey("fs_zones.id"))
    team_id = Column(Integer)

    # Statut
    status = Column(Enum(TechnicianStatus), default=TechnicianStatus.OFF_DUTY)
    last_location_lat = Column(Numeric(10, 7))
    last_location_lng = Column(Numeric(10, 7))
    last_location_at = Column(DateTime)

    # Compétences
    skills = Column(JSON)  # ["electrical", "plumbing", "hvac"]
    certifications = Column(JSON)  # [{name, expiry_date}, ...]
    languages = Column(JSON, default=["fr"])

    # Véhicule
    vehicle_id = Column(Integer, ForeignKey("fs_vehicles.id"))
    has_vehicle = Column(Boolean, default=True)

    # Paramètres
    max_daily_interventions = Column(Integer, default=8)
    working_hours = Column(JSON)  # {mon: {start: "08:00", end: "17:00"}, ...}
    break_duration = Column(Integer, default=60)  # Minutes

    # Stats
    total_interventions = Column(Integer, default=0)
    completed_interventions = Column(Integer, default=0)
    avg_rating = Column(Numeric(3, 2), default=0)
    total_km_traveled = Column(Numeric(10, 2), default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    registration = Column(String(50), nullable=False)
    vin = Column(String(50))
    name = Column(String(100))

    # Caractéristiques
    make = Column(String(100))  # Marque
    model = Column(String(100))
    year = Column(Integer)
    vehicle_type = Column(String(50))  # van, truck, car
    color = Column(String(50))

    # Capacité
    max_weight = Column(Numeric(10, 2))  # kg
    max_volume = Column(Numeric(10, 2))  # m³

    # Suivi
    current_odometer = Column(Integer, default=0)
    fuel_type = Column(String(50))  # diesel, electric, hybrid
    fuel_capacity = Column(Numeric(6, 2))

    # GPS Tracker
    tracker_id = Column(String(100))
    last_location_lat = Column(Numeric(10, 7))
    last_location_lng = Column(Numeric(10, 7))
    last_location_at = Column(DateTime)

    # Maintenance
    last_service_date = Column(Date)
    next_service_date = Column(Date)
    next_service_odometer = Column(Integer)

    # Assurance
    insurance_expiry = Column(Date)
    registration_expiry = Column(Date)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Configuration
    intervention_type = Column(Enum(InterventionType), default=InterventionType.MAINTENANCE)
    estimated_duration = Column(Integer, default=60)  # Minutes
    default_priority = Column(Enum(InterventionPriority), default=InterventionPriority.NORMAL)

    # Checklist par défaut
    checklist_template = Column(JSON)  # [{task, required}, ...]

    # Compétences requises
    required_skills = Column(JSON)  # ["electrical", "hvac"]

    # Matériel requis
    required_parts = Column(JSON)  # [{part_id, quantity}, ...]

    # Prix
    base_price = Column(Numeric(10, 2), default=0)
    price_per_hour = Column(Numeric(10, 2), default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    reference = Column(String(50), nullable=False, unique=True)
    template_id = Column(Integer, ForeignKey("fs_intervention_templates.id"))

    # Type et statut
    intervention_type = Column(Enum(InterventionType), default=InterventionType.MAINTENANCE)
    status = Column(Enum(InterventionStatus), default=InterventionStatus.DRAFT)
    priority = Column(Enum(InterventionPriority), default=InterventionPriority.NORMAL)

    # Description
    title = Column(String(500), nullable=False)
    description = Column(Text)
    internal_notes = Column(Text)

    # Client
    customer_id = Column(Integer, index=True)  # CRM customer
    customer_name = Column(String(255))
    contact_name = Column(String(255))
    contact_phone = Column(String(50))
    contact_email = Column(String(255))

    # Adresse intervention
    address_street = Column(String(255))
    address_city = Column(String(100))
    address_postal_code = Column(String(20))
    address_country = Column(String(100), default="France")
    address_lat = Column(Numeric(10, 7))
    address_lng = Column(Numeric(10, 7))
    access_instructions = Column(Text)

    # Assignation
    technician_id = Column(Integer, ForeignKey("fs_technicians.id"))
    zone_id = Column(Integer, ForeignKey("fs_zones.id"))

    # Planification
    scheduled_date = Column(Date)
    scheduled_time_start = Column(Time)
    scheduled_time_end = Column(Time)
    estimated_duration = Column(Integer, default=60)  # Minutes

    # Exécution
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime)

    # Résultat
    completion_notes = Column(Text)
    failure_reason = Column(Text)
    next_action = Column(Text)

    # Signature client
    signature_data = Column(Text)  # Base64
    signature_name = Column(String(255))
    signed_at = Column(DateTime)

    # Checklist
    checklist = Column(JSON)  # [{task, completed, notes}, ...]

    # Photos
    photos = Column(JSON)  # [{url, caption, taken_at}, ...]

    # Pièces utilisées
    parts_used = Column(JSON)  # [{part_id, quantity, price}, ...]

    # Facturation
    billable = Column(Boolean, default=True)
    labor_hours = Column(Numeric(6, 2), default=0)
    labor_cost = Column(Numeric(10, 2), default=0)
    parts_cost = Column(Numeric(10, 2), default=0)
    travel_cost = Column(Numeric(10, 2), default=0)
    total_cost = Column(Numeric(10, 2), default=0)
    invoice_id = Column(Integer)

    # Satisfaction
    customer_rating = Column(Integer)  # 1-5
    customer_feedback = Column(Text)

    # Récurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSON)  # {frequency, interval, until}
    parent_intervention_id = Column(Integer, ForeignKey("fs_interventions.id"))

    # Liens
    ticket_id = Column(Integer)  # Helpdesk ticket
    maintenance_id = Column(Integer)  # M8 Maintenance
    sales_order_id = Column(Integer)  # M1 Commercial

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    intervention_id = Column(Integer, ForeignKey("fs_interventions.id"), nullable=False)

    # Changement
    action = Column(String(50), nullable=False)
    field_name = Column(String(50))
    old_value = Column(String(500))
    new_value = Column(String(500))

    # Auteur
    actor_type = Column(String(20))  # technician, dispatcher, customer, system
    actor_id = Column(Integer)
    actor_name = Column(String(255))

    # Localisation
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    technician_id = Column(Integer, ForeignKey("fs_technicians.id"), nullable=False)
    intervention_id = Column(Integer, ForeignKey("fs_interventions.id"))

    # Type
    entry_type = Column(String(50), nullable=False)  # work, travel, break, admin

    # Temps
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)

    # Localisation
    start_lat = Column(Numeric(10, 7))
    start_lng = Column(Numeric(10, 7))
    end_lat = Column(Numeric(10, 7))
    end_lng = Column(Numeric(10, 7))

    # Distance (pour travel)
    distance_km = Column(Numeric(8, 2))

    notes = Column(Text)
    is_billable = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    intervention_id = Column(Integer, ForeignKey("fs_interventions.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("fs_technicians.id"))

    # Pièce
    part_id = Column(Integer, index=True)  # Stock module
    part_code = Column(String(50))
    part_name = Column(String(255))

    # Quantité
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), default="unit")

    # Prix
    unit_price = Column(Numeric(10, 2), default=0)
    total_price = Column(Numeric(10, 2), default=0)

    # Source
    from_vehicle_stock = Column(Boolean, default=True)
    warehouse_id = Column(Integer)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    technician_id = Column(Integer, ForeignKey("fs_technicians.id"), nullable=False)
    route_date = Column(Date, nullable=False)

    # Planning
    start_location = Column(String(255))
    start_lat = Column(Numeric(10, 7))
    start_lng = Column(Numeric(10, 7))
    start_time = Column(Time)

    end_location = Column(String(255))
    end_lat = Column(Numeric(10, 7))
    end_lng = Column(Numeric(10, 7))
    end_time = Column(Time)

    # Statistiques prévues
    planned_distance = Column(Numeric(10, 2))  # km
    planned_duration = Column(Integer)  # minutes
    planned_interventions = Column(Integer)

    # Réalité
    actual_distance = Column(Numeric(10, 2))
    actual_duration = Column(Integer)
    completed_interventions = Column(Integer, default=0)

    # Optimisation
    is_optimized = Column(Boolean, default=False)
    optimization_score = Column(Numeric(5, 2))

    # Interventions ordonnées
    intervention_order = Column(JSON)  # [intervention_id1, intervention_id2, ...]

    status = Column(String(20), default="planned")  # planned, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    technician_id = Column(Integer, ForeignKey("fs_technicians.id"), nullable=False)
    intervention_id = Column(Integer, ForeignKey("fs_interventions.id"))

    # Type
    expense_type = Column(String(50), nullable=False)  # fuel, parking, toll, meal, other
    description = Column(String(255))

    # Montant
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Justificatif
    receipt_url = Column(String(500))
    receipt_number = Column(String(100))

    # Date
    expense_date = Column(Date, nullable=False)

    # Remboursement
    status = Column(String(20), default="pending")  # pending, approved, rejected, paid
    approved_by = Column(Integer)
    approved_at = Column(DateTime)
    paid_at = Column(DateTime)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    contract_number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # Client
    customer_id = Column(Integer, nullable=False, index=True)
    customer_name = Column(String(255))

    # Période
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    auto_renew = Column(Boolean, default=False)

    # Type
    contract_type = Column(String(50))  # maintenance, support, full_service

    # SLA
    response_time_hours = Column(Integer, default=24)
    resolution_time_hours = Column(Integer, default=72)
    included_interventions = Column(Integer)
    interventions_used = Column(Integer, default=0)

    # Tarifs
    monthly_fee = Column(Numeric(10, 2), default=0)
    hourly_rate = Column(Numeric(10, 2))
    parts_discount = Column(Numeric(5, 2), default=0)  # %

    # Équipements couverts
    covered_equipment = Column(JSON)  # [equipment_id, ...]

    status = Column(String(20), default="active")  # draft, active, suspended, expired
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_fs_contract_tenant', 'tenant_id'),
        Index('idx_fs_contract_number', 'tenant_id', 'contract_number', unique=True),
        Index('idx_fs_contract_customer', 'tenant_id', 'customer_id'),
    )
