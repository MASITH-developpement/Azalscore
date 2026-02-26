"""
Modeles SQLAlchemy - Module Fleet Management (GAP-062)

Gestion complete de flotte de vehicules:
- Vehicules (immatriculation, marque, modele)
- Affectation conducteurs
- Contrats (leasing, assurance, entretien)
- Suivi kilometrage
- Consommation carburant
- Entretiens et reparations
- Controles techniques
- Amendes et sinistres
- Couts TCO
- Alertes echeances

Multi-tenant, Soft delete, Audit complet.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from app.core.types import UniversalUUID as UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


# ============== Enumerations ==============

class VehicleType(str, Enum):
    """Type de vehicule."""
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    UTILITY = "utility"
    BUS = "bus"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    SCOOTER = "scooter"


class VehicleStatus(str, Enum):
    """Statut d'un vehicule."""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    OUT_OF_SERVICE = "out_of_service"
    RESERVED = "reserved"
    SOLD = "sold"
    SCRAPPED = "scrapped"


class FuelType(str, Enum):
    """Type de carburant."""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"
    E85 = "e85"


class ContractType(str, Enum):
    """Type de contrat."""
    PURCHASE = "purchase"
    LEASING = "leasing"
    LLD = "lld"  # Location Longue Duree
    LOA = "loa"  # Location avec Option d'Achat
    RENTAL = "rental"
    COMPANY_CAR = "company_car"


class ContractStatus(str, Enum):
    """Statut d'un contrat."""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class MaintenanceType(str, Enum):
    """Type de maintenance."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"
    TECHNICAL_CONTROL = "technical_control"
    TIRE_CHANGE = "tire_change"
    OIL_CHANGE = "oil_change"
    BRAKE_SERVICE = "brake_service"
    BATTERY = "battery"
    BODYWORK = "bodywork"
    OTHER = "other"


class MaintenanceStatus(str, Enum):
    """Statut de maintenance."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class DocumentType(str, Enum):
    """Type de document vehicule."""
    REGISTRATION = "registration"
    INSURANCE = "insurance"
    TECHNICAL_INSPECTION = "technical_inspection"
    POLLUTION_CERTIFICATE = "pollution_certificate"
    LEASE_CONTRACT = "lease_contract"
    WARRANTY = "warranty"
    DRIVER_LICENSE = "driver_license"
    MEDICAL_CERTIFICATE = "medical_certificate"
    OTHER = "other"


class AlertType(str, Enum):
    """Type d'alerte."""
    MAINTENANCE_DUE = "maintenance_due"
    DOCUMENT_EXPIRY = "document_expiry"
    INSURANCE_EXPIRY = "insurance_expiry"
    INSPECTION_DUE = "inspection_due"
    CONTRACT_EXPIRY = "contract_expiry"
    LICENSE_EXPIRY = "license_expiry"
    MILEAGE_EXCEEDED = "mileage_exceeded"
    MILEAGE_THRESHOLD = "mileage_threshold"
    FUEL_ANOMALY = "fuel_anomaly"
    COST_THRESHOLD = "cost_threshold"


class AlertSeverity(str, Enum):
    """Severite d'alerte."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Type d'incident/sinistre."""
    ACCIDENT = "accident"
    THEFT = "theft"
    VANDALISM = "vandalism"
    BREAKDOWN = "breakdown"
    FINE = "fine"
    PARKING_FINE = "parking_fine"
    SPEED_FINE = "speed_fine"
    OTHER_FINE = "other_fine"


class IncidentStatus(str, Enum):
    """Statut d'un incident."""
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    INSURANCE_CLAIM = "insurance_claim"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ============== Models ==============

class FleetVehicle(Base):
    """Vehicule de la flotte."""
    __tablename__ = "fleet_vehicles"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    registration_number = Column(String(20), nullable=False)
    vin = Column(String(17))  # Vehicle Identification Number
    internal_number = Column(String(50))

    # Caracteristiques
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    version = Column(String(100))
    year = Column(Integer, nullable=False)
    vehicle_type = Column(SQLEnum(VehicleType), default=VehicleType.CAR, nullable=False)
    fuel_type = Column(SQLEnum(FuelType), default=FuelType.DIESEL, nullable=False)
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False)

    # Details techniques
    color = Column(String(50))
    seats = Column(Integer, default=5)
    doors = Column(Integer, default=4)
    engine_capacity_cc = Column(Integer)
    power_hp = Column(Integer)
    power_kw = Column(Integer)
    fiscal_power = Column(Integer)  # CV fiscaux
    co2_emissions = Column(Integer)  # g/km
    transmission = Column(String(20), default="manual")  # manual, automatic, semi_auto

    # Kilometrage
    initial_mileage = Column(Integer, default=0)
    current_mileage = Column(Integer, default=0)
    annual_mileage_limit = Column(Integer)  # Pour contrats
    average_daily_mileage = Column(Numeric(10, 2))

    # Carburant
    fuel_capacity_liters = Column(Integer)
    average_consumption = Column(Numeric(6, 2))  # L/100km ou kWh/100km
    battery_capacity_kwh = Column(Numeric(8, 2))  # Pour electriques

    # Financier
    purchase_date = Column(Date)
    purchase_price = Column(Numeric(12, 2))
    current_value = Column(Numeric(12, 2))
    residual_value = Column(Numeric(12, 2))
    monthly_cost = Column(Numeric(10, 2))  # TCO mensuel estime

    # Affectation
    assigned_driver_id = Column(UUID(), ForeignKey("fleet_drivers.id"))
    department = Column(String(100))
    cost_center = Column(String(50))
    project_id = Column(UUID())

    # Geolocalisation
    location_lat = Column(Numeric(10, 8))
    location_lng = Column(Numeric(11, 8))
    last_location_update = Column(DateTime)
    gps_device_id = Column(String(100))

    # Dates cles
    first_registration_date = Column(Date)
    last_technical_inspection = Column(Date)
    next_technical_inspection = Column(Date)
    last_service_date = Column(Date)
    next_service_date = Column(Date)
    next_service_mileage = Column(Integer)

    # Metadata
    photo_url = Column(String(500))
    notes = Column(Text)
    custom_fields = Column(JSONB, default=dict)
    tags = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_fleet_vehicle_tenant', 'tenant_id'),
        Index('ix_fleet_vehicle_tenant_code', 'tenant_id', 'code'),
        Index('ix_fleet_vehicle_tenant_reg', 'tenant_id', 'registration_number'),
        Index('ix_fleet_vehicle_tenant_status', 'tenant_id', 'status'),
        Index('ix_fleet_vehicle_tenant_driver', 'tenant_id', 'assigned_driver_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_fleet_vehicle_tenant_code'),
        UniqueConstraint('tenant_id', 'registration_number', name='uq_fleet_vehicle_tenant_reg'),
    )

    # Relations
    driver = relationship("FleetDriver", back_populates="assigned_vehicle", foreign_keys=[assigned_driver_id])
    contracts = relationship("FleetContract", back_populates="vehicle", cascade="all, delete-orphan")
    mileage_logs = relationship("FleetMileageLog", back_populates="vehicle", cascade="all, delete-orphan")
    fuel_entries = relationship("FleetFuelEntry", back_populates="vehicle", cascade="all, delete-orphan")
    maintenances = relationship("FleetMaintenance", back_populates="vehicle", cascade="all, delete-orphan")
    documents = relationship("FleetDocument", back_populates="vehicle", cascade="all, delete-orphan")
    incidents = relationship("FleetIncident", back_populates="vehicle", cascade="all, delete-orphan")
    costs = relationship("FleetCost", back_populates="vehicle", cascade="all, delete-orphan")
    alerts = relationship("FleetAlert", back_populates="vehicle", cascade="all, delete-orphan")

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('registration_number')
    def validate_registration(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Registration number cannot be empty")
        return value.upper().strip().replace(" ", "-")

    @hybrid_property
    def display_name(self) -> str:
        return f"{self.make} {self.model} ({self.registration_number})"

    @hybrid_property
    def age_years(self) -> int:
        if self.year:
            return datetime.now().year - self.year
        return 0

    def can_delete(self) -> tuple[bool, str]:
        if self.status == VehicleStatus.IN_USE:
            return False, "Vehicle is currently in use"
        return True, ""

    def __repr__(self) -> str:
        return f"<FleetVehicle {self.registration_number}: {self.make} {self.model}>"


class FleetDriver(Base):
    """Conducteur de la flotte."""
    __tablename__ = "fleet_drivers"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    employee_id = Column(UUID())  # Lien module RH
    user_id = Column(UUID())  # Lien compte utilisateur

    # Informations personnelles
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))

    # Permis de conduire
    license_number = Column(String(50))
    license_type = Column(String(20))  # B, C, D, BE, CE, etc.
    license_issue_date = Column(Date)
    license_expiry_date = Column(Date)
    license_country = Column(String(100), default="France")

    # Informations professionnelles
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(Date)
    cost_center = Column(String(50))

    # Certificats medicaux
    medical_certificate_date = Column(Date)
    medical_certificate_expiry = Column(Date)

    # Statistiques
    total_trips = Column(Integer, default=0)
    total_distance_km = Column(Integer, default=0)
    total_fuel_cost = Column(Numeric(12, 2), default=0)

    # Contact urgence
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(50))
    emergency_contact_relation = Column(String(100))

    # Metadata
    photo_url = Column(String(500))
    notes = Column(Text)
    custom_fields = Column(JSONB, default=dict)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_fleet_driver_tenant', 'tenant_id'),
        Index('ix_fleet_driver_tenant_code', 'tenant_id', 'code'),
        Index('ix_fleet_driver_tenant_name', 'tenant_id', 'last_name', 'first_name'),
        UniqueConstraint('tenant_id', 'code', name='uq_fleet_driver_tenant_code'),
    )

    # Relations
    assigned_vehicle = relationship("FleetVehicle", back_populates="driver",
                                    foreign_keys="FleetVehicle.assigned_driver_id")
    fuel_entries = relationship("FleetFuelEntry", back_populates="driver")
    incidents = relationship("FleetIncident", back_populates="driver")

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @hybrid_property
    def license_valid(self) -> bool:
        if not self.license_expiry_date:
            return True
        return self.license_expiry_date >= date.today()

    def can_delete(self) -> tuple[bool, str]:
        if self.assigned_vehicle:
            return False, "Driver has assigned vehicle"
        return True, ""

    def __repr__(self) -> str:
        return f"<FleetDriver {self.code}: {self.full_name}>"


class FleetContract(Base):
    """Contrat vehicule (leasing, assurance, entretien)."""
    __tablename__ = "fleet_contracts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)
    contract_type = Column(SQLEnum(ContractType), nullable=False)
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.ACTIVE, nullable=False)

    # Fournisseur
    provider_name = Column(String(200), nullable=False)
    provider_contact = Column(String(200))
    provider_phone = Column(String(50))
    provider_email = Column(String(255))
    contract_number = Column(String(100))

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    duration_months = Column(Integer)
    renewal_date = Column(Date)
    notice_period_days = Column(Integer, default=90)

    # Financier
    monthly_payment = Column(Numeric(12, 2))
    deposit = Column(Numeric(12, 2))
    total_amount = Column(Numeric(14, 2))
    currency = Column(String(3), default="EUR")

    # Conditions
    mileage_limit_annual = Column(Integer)
    mileage_limit_total = Column(Integer)
    excess_mileage_rate = Column(Numeric(6, 4))  # EUR/km
    services_included = Column(JSONB, default=list)  # Liste des services inclus
    coverage_details = Column(Text)

    # Pour assurance
    insurance_company = Column(String(200))
    policy_number = Column(String(100))
    coverage_type = Column(String(100))  # tous_risques, tiers, tiers_plus
    deductible = Column(Numeric(10, 2))
    bonus_malus = Column(Numeric(4, 2))

    # Documents
    document_url = Column(String(500))

    # Alertes
    reminder_days = Column(Integer, default=60)
    reminder_sent = Column(Boolean, default=False)

    notes = Column(Text)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_fleet_contract_tenant', 'tenant_id'),
        Index('ix_fleet_contract_tenant_code', 'tenant_id', 'code'),
        Index('ix_fleet_contract_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_contract_tenant_type', 'tenant_id', 'contract_type'),
        Index('ix_fleet_contract_tenant_status', 'tenant_id', 'status'),
        Index('ix_fleet_contract_end_date', 'tenant_id', 'end_date'),
        UniqueConstraint('tenant_id', 'code', name='uq_fleet_contract_tenant_code'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="contracts")

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def days_until_expiry(self) -> int:
        if not self.end_date:
            return 9999
        return (self.end_date - date.today()).days

    @hybrid_property
    def is_expiring_soon(self) -> bool:
        return 0 < self.days_until_expiry <= self.reminder_days

    def can_delete(self) -> tuple[bool, str]:
        return True, ""

    def __repr__(self) -> str:
        return f"<FleetContract {self.code}: {self.contract_type.value}>"


class FleetMileageLog(Base):
    """Releve kilometrique."""
    __tablename__ = "fleet_mileage_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)
    driver_id = Column(UUID())

    log_date = Column(Date, nullable=False)
    mileage = Column(Integer, nullable=False)
    previous_mileage = Column(Integer)
    distance_since_last = Column(Integer)

    source = Column(String(50), default="manual")  # manual, gps, obd, fuel
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID())

    __table_args__ = (
        Index('ix_fleet_mileage_tenant', 'tenant_id'),
        Index('ix_fleet_mileage_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_mileage_tenant_date', 'tenant_id', 'log_date'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="mileage_logs")

    def __repr__(self) -> str:
        return f"<FleetMileageLog {self.log_date}: {self.mileage}km>"


class FleetFuelEntry(Base):
    """Entree de carburant."""
    __tablename__ = "fleet_fuel_entries"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)
    driver_id = Column(UUID(), ForeignKey("fleet_drivers.id"))

    # Date et lieu
    fill_date = Column(Date, nullable=False)
    fill_time = Column(DateTime)
    station_name = Column(String(200))
    station_address = Column(String(300))
    station_city = Column(String(100))

    # Carburant
    fuel_type = Column(SQLEnum(FuelType), nullable=False)
    quantity_liters = Column(Numeric(8, 2), nullable=False)
    price_per_liter = Column(Numeric(6, 4), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")

    # Kilometrage
    mileage_at_fill = Column(Integer, nullable=False)
    previous_mileage = Column(Integer)
    distance_since_last = Column(Integer)
    consumption_per_100km = Column(Numeric(6, 2))

    full_tank = Column(Boolean, default=True)

    # Paiement
    payment_method = Column(String(50))  # card, cash, fuel_card
    fuel_card_number = Column(String(50))
    receipt_number = Column(String(100))
    receipt_url = Column(String(500))

    # Validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID())
    validated_at = Column(DateTime)
    anomaly_detected = Column(Boolean, default=False)
    anomaly_reason = Column(String(200))

    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_fleet_fuel_tenant', 'tenant_id'),
        Index('ix_fleet_fuel_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_fuel_tenant_driver', 'tenant_id', 'driver_id'),
        Index('ix_fleet_fuel_tenant_date', 'tenant_id', 'fill_date'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="fuel_entries")
    driver = relationship("FleetDriver", back_populates="fuel_entries")

    def __repr__(self) -> str:
        return f"<FleetFuelEntry {self.fill_date}: {self.quantity_liters}L>"


class FleetMaintenance(Base):
    """Entretien et reparation."""
    __tablename__ = "fleet_maintenances"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)
    status = Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED, nullable=False)

    # Description
    title = Column(String(200), nullable=False)
    description = Column(Text)
    work_performed = Column(Text)

    # Planification
    scheduled_date = Column(Date)
    scheduled_mileage = Column(Integer)
    completed_date = Column(Date)
    mileage_at_maintenance = Column(Integer)

    # Prochaine maintenance
    next_maintenance_date = Column(Date)
    next_maintenance_mileage = Column(Integer)

    # Prestataire
    provider_name = Column(String(200))
    provider_address = Column(String(300))
    provider_contact = Column(String(200))
    provider_phone = Column(String(50))

    # Couts
    cost_parts = Column(Numeric(12, 2), default=0)
    cost_labor = Column(Numeric(12, 2), default=0)
    cost_other = Column(Numeric(12, 2), default=0)
    cost_total = Column(Numeric(12, 2), default=0)
    currency = Column(String(3), default="EUR")
    vat_rate = Column(Numeric(5, 2), default=20)
    vat_amount = Column(Numeric(12, 2), default=0)

    # Pieces
    parts_replaced = Column(JSONB, default=list)  # [{name, quantity, unit_price}]
    warranty_parts = Column(Boolean, default=False)
    warranty_labor = Column(Boolean, default=False)

    # Documents
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    invoice_url = Column(String(500))
    work_order_number = Column(String(100))

    # Technicien
    technician_name = Column(String(200))
    technician_notes = Column(Text)

    # Alertes
    reminder_sent = Column(Boolean, default=False)

    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_fleet_maint_tenant', 'tenant_id'),
        Index('ix_fleet_maint_tenant_code', 'tenant_id', 'code'),
        Index('ix_fleet_maint_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_maint_tenant_status', 'tenant_id', 'status'),
        Index('ix_fleet_maint_tenant_type', 'tenant_id', 'maintenance_type'),
        Index('ix_fleet_maint_scheduled', 'tenant_id', 'scheduled_date'),
        UniqueConstraint('tenant_id', 'code', name='uq_fleet_maint_tenant_code'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="maintenances")

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def is_overdue(self) -> bool:
        if self.status != MaintenanceStatus.SCHEDULED:
            return False
        if self.scheduled_date and self.scheduled_date < date.today():
            return True
        return False

    def can_delete(self) -> tuple[bool, str]:
        if self.status == MaintenanceStatus.IN_PROGRESS:
            return False, "Maintenance is in progress"
        return True, ""

    def __repr__(self) -> str:
        return f"<FleetMaintenance {self.code}: {self.title}>"


class FleetDocument(Base):
    """Document vehicule ou conducteur."""
    __tablename__ = "fleet_documents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Reference
    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"))
    driver_id = Column(UUID())

    # Document
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    document_number = Column(String(100))

    # Dates
    issue_date = Column(Date)
    expiry_date = Column(Date)
    issuing_authority = Column(String(200))

    # Fichier
    file_name = Column(String(255))
    file_url = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))

    # Alertes
    reminder_days = Column(Integer, default=30)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)

    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    __table_args__ = (
        Index('ix_fleet_doc_tenant', 'tenant_id'),
        Index('ix_fleet_doc_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_doc_tenant_driver', 'tenant_id', 'driver_id'),
        Index('ix_fleet_doc_tenant_type', 'tenant_id', 'document_type'),
        Index('ix_fleet_doc_expiry', 'tenant_id', 'expiry_date'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="documents")

    @hybrid_property
    def days_until_expiry(self) -> int:
        if not self.expiry_date:
            return 9999
        return (self.expiry_date - date.today()).days

    @hybrid_property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @hybrid_property
    def is_expiring_soon(self) -> bool:
        return 0 < self.days_until_expiry <= self.reminder_days

    def __repr__(self) -> str:
        return f"<FleetDocument {self.document_type.value}: {self.name}>"


class FleetIncident(Base):
    """Incident, sinistre ou amende."""
    __tablename__ = "fleet_incidents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False)
    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)
    driver_id = Column(UUID(), ForeignKey("fleet_drivers.id"))
    incident_type = Column(SQLEnum(IncidentType), nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.REPORTED, nullable=False)

    # Details incident
    incident_date = Column(DateTime, nullable=False)
    incident_location = Column(String(300))
    description = Column(Text, nullable=False)
    circumstances = Column(Text)

    # Pour sinistre
    third_party_involved = Column(Boolean, default=False)
    third_party_details = Column(Text)
    police_report_number = Column(String(100))
    police_report_date = Column(Date)

    # Pour amende
    fine_number = Column(String(100))
    fine_amount = Column(Numeric(10, 2))
    fine_points = Column(Integer)  # Points retires
    fine_due_date = Column(Date)
    fine_paid = Column(Boolean, default=False)
    fine_paid_date = Column(Date)
    fine_contested = Column(Boolean, default=False)
    fine_contest_date = Column(Date)

    # Assurance
    insurance_claim_number = Column(String(100))
    insurance_claim_date = Column(Date)
    insurance_status = Column(String(50))
    insurance_payout = Column(Numeric(12, 2))
    deductible_amount = Column(Numeric(10, 2))

    # Couts
    repair_cost = Column(Numeric(12, 2))
    other_costs = Column(Numeric(12, 2))
    total_cost = Column(Numeric(12, 2))
    cost_recovered = Column(Numeric(12, 2))

    # Resolution
    resolution_date = Column(Date)
    resolution_notes = Column(Text)

    # Documents
    photos = Column(JSONB, default=list)  # URLs
    documents = Column(JSONB, default=list)  # URLs

    # Responsabilite
    driver_responsible = Column(Boolean)
    responsibility_percentage = Column(Integer)  # 0-100

    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID())
    updated_by = Column(UUID())

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID())

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_fleet_incident_tenant', 'tenant_id'),
        Index('ix_fleet_incident_tenant_code', 'tenant_id', 'code'),
        Index('ix_fleet_incident_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_incident_tenant_driver', 'tenant_id', 'driver_id'),
        Index('ix_fleet_incident_tenant_type', 'tenant_id', 'incident_type'),
        Index('ix_fleet_incident_tenant_status', 'tenant_id', 'status'),
        Index('ix_fleet_incident_date', 'tenant_id', 'incident_date'),
        UniqueConstraint('tenant_id', 'code', name='uq_fleet_incident_tenant_code'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="incidents")
    driver = relationship("FleetDriver", back_populates="incidents")

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        if self.status == IncidentStatus.UNDER_INVESTIGATION:
            return False, "Incident is under investigation"
        return True, ""

    def __repr__(self) -> str:
        return f"<FleetIncident {self.code}: {self.incident_type.value}>"


class FleetCost(Base):
    """Cout vehicule pour calcul TCO."""
    __tablename__ = "fleet_costs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"), nullable=False)

    # Categorie
    category = Column(String(50), nullable=False)  # fuel, maintenance, insurance, tax, toll, parking, fine, other
    subcategory = Column(String(50))

    # Details
    description = Column(String(300))
    cost_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    vat_amount = Column(Numeric(12, 2))

    # Reference
    reference_type = Column(String(50))  # fuel_entry, maintenance, incident, contract
    reference_id = Column(UUID())

    # Kilometrage
    mileage_at_cost = Column(Integer)

    # Documents
    invoice_number = Column(String(100))
    invoice_url = Column(String(500))

    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID())

    __table_args__ = (
        Index('ix_fleet_cost_tenant', 'tenant_id'),
        Index('ix_fleet_cost_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_cost_tenant_category', 'tenant_id', 'category'),
        Index('ix_fleet_cost_tenant_date', 'tenant_id', 'cost_date'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="costs")

    def __repr__(self) -> str:
        return f"<FleetCost {self.category}: {self.amount}>"


class FleetAlert(Base):
    """Alerte de la flotte."""
    __tablename__ = "fleet_alerts"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    # Reference
    vehicle_id = Column(UUID(), ForeignKey("fleet_vehicles.id"))
    driver_id = Column(UUID())
    contract_id = Column(UUID())
    document_id = Column(UUID())
    maintenance_id = Column(UUID())

    # Alerte
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Echeance
    due_date = Column(Date)
    days_before_due = Column(Integer)

    # Seuils
    threshold_value = Column(Numeric(12, 2))
    current_value = Column(Numeric(12, 2))

    # Statut
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    read_by = Column(UUID())
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID())
    resolution_notes = Column(Text)

    # Notifications
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime)
    sms_sent = Column(Boolean, default=False)

    extra_data = Column(JSONB, default=dict)  # Renomme car 'metadata' reserve SQLAlchemy

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_fleet_alert_tenant', 'tenant_id'),
        Index('ix_fleet_alert_tenant_vehicle', 'tenant_id', 'vehicle_id'),
        Index('ix_fleet_alert_tenant_type', 'tenant_id', 'alert_type'),
        Index('ix_fleet_alert_tenant_severity', 'tenant_id', 'severity'),
        Index('ix_fleet_alert_tenant_resolved', 'tenant_id', 'is_resolved'),
        Index('ix_fleet_alert_due_date', 'tenant_id', 'due_date'),
    )

    # Relations
    vehicle = relationship("FleetVehicle", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<FleetAlert {self.alert_type.value}: {self.title}>"


# === Event Listeners ===

@event.listens_for(FleetVehicle, 'before_update')
def vehicle_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FleetDriver, 'before_update')
def driver_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FleetContract, 'before_update')
def contract_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FleetMaintenance, 'before_update')
def maintenance_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FleetIncident, 'before_update')
def incident_before_update(mapper, connection, target):
    target.version += 1
