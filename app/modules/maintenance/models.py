"""
AZALS MODULE M8 - Modèles Maintenance (GMAO)
============================================

Modèles SQLAlchemy pour le module de gestion de la maintenance.
REFACTORED: Migration vers UUID pour production SaaS industrielle.
"""

import enum
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.types import UniversalUUID, JSONB


# ============================================================================
# ENUMS
# ============================================================================

class AssetCategory(str, enum.Enum):
    """Catégories d'actifs"""
    MACHINE = "MACHINE"
    EQUIPMENT = "EQUIPMENT"
    VEHICLE = "VEHICLE"
    BUILDING = "BUILDING"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    TOOL = "TOOL"
    UTILITY = "UTILITY"
    FURNITURE = "FURNITURE"
    OTHER = "OTHER"


class AssetStatus(str, enum.Enum):
    """Statuts d'actif"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    RESERVED = "RESERVED"
    DISPOSED = "DISPOSED"
    UNDER_REPAIR = "UNDER_REPAIR"
    STANDBY = "STANDBY"


class AssetCriticality(str, enum.Enum):
    """Niveaux de criticité"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MaintenanceType(str, enum.Enum):
    """Types de maintenance"""
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    PREDICTIVE = "PREDICTIVE"
    CONDITION_BASED = "CONDITION_BASED"
    BREAKDOWN = "BREAKDOWN"
    IMPROVEMENT = "IMPROVEMENT"
    INSPECTION = "INSPECTION"
    CALIBRATION = "CALIBRATION"


class WorkOrderStatus(str, enum.Enum):
    """Statuts d'ordre de travail"""
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class WorkOrderPriority(str, enum.Enum):
    """Priorités d'ordre de travail"""
    EMERGENCY = "EMERGENCY"
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SCHEDULED = "SCHEDULED"


class FailureType(str, enum.Enum):
    """Types de panne"""
    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"
    ELECTRONIC = "ELECTRONIC"
    HYDRAULIC = "HYDRAULIC"
    PNEUMATIC = "PNEUMATIC"
    SOFTWARE = "SOFTWARE"
    OPERATOR_ERROR = "OPERATOR_ERROR"
    WEAR = "WEAR"
    CONTAMINATION = "CONTAMINATION"
    UNKNOWN = "UNKNOWN"


class PartRequestStatus(str, enum.Enum):
    """Statuts de demande de pièce"""
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    ISSUED = "ISSUED"
    CANCELLED = "CANCELLED"


class ContractType(str, enum.Enum):
    """Types de contrat de maintenance"""
    FULL_SERVICE = "FULL_SERVICE"
    PREVENTIVE = "PREVENTIVE"
    ON_CALL = "ON_CALL"
    PARTS_ONLY = "PARTS_ONLY"
    LABOR_ONLY = "LABOR_ONLY"
    WARRANTY = "WARRANTY"


class ContractStatus(str, enum.Enum):
    """Statuts de contrat"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


# ============================================================================
# MODÈLES - ACTIFS
# ============================================================================

class Asset(Base):
    """Actif/Équipement"""
    __tablename__ = "maintenance_assets"
    __table_args__ = (
        Index("idx_asset_tenant", "tenant_id"),
        Index("idx_asset_code", "tenant_id", "asset_code"),
        Index("idx_asset_category", "tenant_id", "category"),
        Index("idx_asset_status", "tenant_id", "status"),
        Index("idx_asset_location", "tenant_id", "location_id"),
        UniqueConstraint("tenant_id", "asset_code", name="uq_asset_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    asset_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(AssetCategory), nullable=False)
    asset_type = Column(String(100))

    # Statut
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.ACTIVE)
    criticality = Column(SQLEnum(AssetCriticality), default=AssetCriticality.MEDIUM)

    # Hiérarchie
    parent_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id"))

    # Localisation
    location_id = Column(UniversalUUID())  # Référence warehouse/zone (inventory_warehouses)
    location_description = Column(String(200))
    building = Column(String(100))
    floor = Column(String(50))
    area = Column(String(100))

    # Informations fabricant
    manufacturer = Column(String(200))
    model = Column(String(200))
    serial_number = Column(String(100))
    year_manufactured = Column(Integer)

    # Dates
    purchase_date = Column(Date)
    installation_date = Column(Date)
    warranty_start_date = Column(Date)
    warranty_end_date = Column(Date)
    expected_end_of_life = Column(Date)
    last_maintenance_date = Column(Date)
    next_maintenance_date = Column(Date)

    # Valeur
    purchase_cost = Column(Numeric(15, 2))
    current_value = Column(Numeric(15, 2))
    replacement_cost = Column(Numeric(15, 2))
    salvage_value = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Amortissement
    depreciation_method = Column(String(50))
    useful_life_years = Column(Integer)
    depreciation_rate = Column(Numeric(5, 2))

    # Spécifications techniques
    specifications = Column(JSONB, default=dict)
    power_rating = Column(String(100))
    dimensions = Column(String(200))
    weight = Column(Numeric(10, 2))
    weight_unit = Column(String(20))

    # Compteurs
    operating_hours = Column(Numeric(12, 2), default=0)
    cycle_count = Column(Integer, default=0)
    energy_consumption = Column(Numeric(15, 4))

    # Maintenance
    maintenance_strategy = Column(String(50))  # PREVENTIVE, REACTIVE, PREDICTIVE
    default_maintenance_plan_id = Column(UniversalUUID())

    # Fournisseur
    supplier_id = Column(UniversalUUID())  # Référence fournisseur (procurement module)

    # Responsable
    responsible_id = Column(UniversalUUID())  # Référence users
    department = Column(String(100))

    # Contrat
    contract_id = Column(UniversalUUID())

    # Média
    photo_url = Column(String(500))
    documents = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)

    # QR Code / Code-barres
    barcode = Column(String(100))
    qr_code = Column(String(200))

    # Indicateurs
    mtbf_hours = Column(Numeric(10, 2))  # Mean Time Between Failures
    mttr_hours = Column(Numeric(10, 2))  # Mean Time To Repair
    availability_rate = Column(Numeric(5, 2))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    components = relationship("AssetComponent", back_populates="asset", cascade="all, delete-orphan")
    documents_rel = relationship("AssetDocument", back_populates="asset", cascade="all, delete-orphan")
    meters = relationship("AssetMeter", back_populates="asset", cascade="all, delete-orphan")
    work_orders = relationship("MaintenanceWorkOrder", back_populates="asset")
    failures = relationship("Failure", back_populates="asset")


class AssetComponent(Base):
    """Composant d'un actif"""
    __tablename__ = "maintenance_asset_components"
    __table_args__ = (
        Index("idx_component_tenant", "tenant_id"),
        Index("idx_component_asset", "asset_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    component_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Informations
    manufacturer = Column(String(200))
    part_number = Column(String(100))
    serial_number = Column(String(100))

    # Dates
    installation_date = Column(Date)
    expected_replacement_date = Column(Date)
    last_replacement_date = Column(Date)

    # Durée de vie
    expected_life_hours = Column(Integer)
    expected_life_cycles = Column(Integer)
    current_hours = Column(Numeric(10, 2), default=0)
    current_cycles = Column(Integer, default=0)

    # Criticité
    criticality = Column(SQLEnum(AssetCriticality))

    # Pièce de rechange associée
    spare_part_id = Column(UniversalUUID(), ForeignKey("maintenance_spare_parts.id"))

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    asset = relationship("Asset", back_populates="components")


class AssetDocument(Base):
    """Document associé à un actif"""
    __tablename__ = "maintenance_asset_documents"
    __table_args__ = (
        Index("idx_asset_doc_tenant", "tenant_id"),
        Index("idx_asset_doc_asset", "asset_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id", ondelete="CASCADE"), nullable=False)

    # Document
    document_type = Column(String(50), nullable=False)  # MANUAL, DRAWING, CERTIFICATE, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_name = Column(String(200))
    file_size = Column(Integer)
    mime_type = Column(String(100))

    # Métadonnées
    version = Column(String(50))
    valid_from = Column(Date)
    valid_until = Column(Date)

    # Statut
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    asset = relationship("Asset", back_populates="documents_rel")


class AssetMeter(Base):
    """Compteur d'un actif"""
    __tablename__ = "maintenance_asset_meters"
    __table_args__ = (
        Index("idx_meter_tenant", "tenant_id"),
        Index("idx_meter_asset", "asset_id"),
        UniqueConstraint("asset_id", "meter_code", name="uq_asset_meter"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id", ondelete="CASCADE"), nullable=False)

    # Identification
    meter_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Type
    meter_type = Column(String(50), nullable=False)  # HOURS, CYCLES, DISTANCE, etc.
    unit = Column(String(50), nullable=False)

    # Valeurs
    current_reading = Column(Numeric(15, 4), default=0)
    last_reading_date = Column(DateTime)
    initial_reading = Column(Numeric(15, 4), default=0)

    # Seuils
    alert_threshold = Column(Numeric(15, 4))
    critical_threshold = Column(Numeric(15, 4))
    max_reading = Column(Numeric(15, 4))

    # Déclenchement maintenance
    maintenance_trigger_value = Column(Numeric(15, 4))
    last_maintenance_reading = Column(Numeric(15, 4))

    # Statut
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    asset = relationship("Asset", back_populates="meters")
    readings = relationship("MeterReading", back_populates="meter", cascade="all, delete-orphan")


class MeterReading(Base):
    """Relevé de compteur"""
    __tablename__ = "maintenance_meter_readings"
    __table_args__ = (
        Index("idx_reading_tenant", "tenant_id"),
        Index("idx_reading_meter", "meter_id"),
        Index("idx_reading_date", "reading_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    meter_id = Column(UniversalUUID(), ForeignKey("maintenance_asset_meters.id", ondelete="CASCADE"), nullable=False)

    # Relevé
    reading_date = Column(DateTime, nullable=False)
    reading_value = Column(Numeric(15, 4), nullable=False)
    delta = Column(Numeric(15, 4))

    # Source
    source = Column(String(50))  # MANUAL, AUTOMATIC, IMPORT

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    meter = relationship("AssetMeter", back_populates="readings")


# ============================================================================
# MODÈLES - PLANS DE MAINTENANCE
# ============================================================================

class MaintenancePlan(Base):
    """Plan de maintenance préventive"""
    __tablename__ = "maintenance_plans"
    __table_args__ = (
        Index("idx_mplan_tenant", "tenant_id"),
        Index("idx_mplan_code", "tenant_id", "plan_code"),
        UniqueConstraint("tenant_id", "plan_code", name="uq_mplan_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    plan_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Type
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)

    # Actif concerné
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id"))
    asset_category = Column(SQLEnum(AssetCategory))  # Ou applicable à une catégorie

    # Déclenchement
    trigger_type = Column(String(50), nullable=False)  # TIME, METER, CONDITION

    # Périodicité temporelle
    frequency_value = Column(Integer)
    frequency_unit = Column(String(20))  # DAYS, WEEKS, MONTHS, YEARS

    # Déclenchement compteur
    trigger_meter_id = Column(UniversalUUID(), ForeignKey("maintenance_asset_meters.id"))
    trigger_meter_interval = Column(Numeric(15, 4))

    # Planification
    last_execution_date = Column(Date)
    next_due_date = Column(Date)
    lead_time_days = Column(Integer, default=7)

    # Durée estimée
    estimated_duration_hours = Column(Numeric(6, 2))

    # Responsable
    responsible_id = Column(UniversalUUID())  # Référence users

    # Statut
    is_active = Column(Boolean, default=True)

    # Coût estimé
    estimated_labor_cost = Column(Numeric(15, 2))
    estimated_parts_cost = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Instructions
    instructions = Column(Text)
    safety_instructions = Column(Text)
    required_tools = Column(JSONB, default=list)
    required_certifications = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    tasks = relationship("MaintenancePlanTask", back_populates="plan", cascade="all, delete-orphan")


class MaintenancePlanTask(Base):
    """Tâche d'un plan de maintenance"""
    __tablename__ = "maintenance_plan_tasks"
    __table_args__ = (
        Index("idx_mplan_task_tenant", "tenant_id"),
        Index("idx_mplan_task_plan", "plan_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(UniversalUUID(), ForeignKey("maintenance_plans.id", ondelete="CASCADE"), nullable=False)

    # Tâche
    sequence = Column(Integer, nullable=False)
    task_code = Column(String(50))
    description = Column(Text, nullable=False)
    detailed_instructions = Column(Text)

    # Durée
    estimated_duration_minutes = Column(Integer)

    # Compétences
    required_skill = Column(String(100))

    # Pièces
    required_parts = Column(JSONB, default=list)

    # Points de contrôle
    check_points = Column(JSONB, default=list)

    # Criticité
    is_mandatory = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    plan = relationship("MaintenancePlan", back_populates="tasks")


# ============================================================================
# MODÈLES - ORDRES DE TRAVAIL
# ============================================================================

class MaintenanceWorkOrder(Base):
    """Ordre de travail / Bon d'intervention (GMAO - distinct de production.WorkOrder)"""
    __tablename__ = "maintenance_work_orders"
    __table_args__ = (
        Index("idx_wo_tenant", "tenant_id"),
        Index("idx_wo_number", "tenant_id", "wo_number"),
        Index("idx_wo_asset", "tenant_id", "asset_id"),
        Index("idx_wo_status", "tenant_id", "status"),
        Index("idx_wo_priority", "tenant_id", "priority"),
        Index("idx_wo_scheduled", "tenant_id", "scheduled_start_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    wo_number = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # Type et priorité
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)
    priority = Column(SQLEnum(WorkOrderPriority), default=WorkOrderPriority.MEDIUM)
    status = Column(SQLEnum(WorkOrderStatus), default=WorkOrderStatus.DRAFT)

    # Actif
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id"), nullable=False)
    component_id = Column(UniversalUUID(), ForeignKey("maintenance_asset_components.id"))

    # Origine
    source = Column(String(50))  # MANUAL, PLAN, FAILURE, REQUEST
    source_reference = Column(String(100))
    maintenance_plan_id = Column(UniversalUUID(), ForeignKey("maintenance_plans.id"))
    failure_id = Column(UniversalUUID(), ForeignKey("maintenance_failures.id"))

    # Demandeur
    requester_id = Column(UniversalUUID())  # Référence users
    request_date = Column(DateTime)
    request_description = Column(Text)

    # Planification
    scheduled_start_date = Column(DateTime)
    scheduled_end_date = Column(DateTime)
    due_date = Column(DateTime)

    # Exécution
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    downtime_hours = Column(Numeric(8, 2))

    # Affectation
    assigned_to_id = Column(UniversalUUID())  # Référence users
    team_id = Column(UniversalUUID())
    external_vendor_id = Column(UniversalUUID())  # Référence fournisseur externe

    # Instructions
    work_instructions = Column(Text)
    safety_precautions = Column(Text)
    tools_required = Column(JSONB, default=list)
    certifications_required = Column(JSONB, default=list)

    # Localisation
    location_description = Column(String(200))

    # Completion
    completion_notes = Column(Text)
    completed_by_id = Column(UniversalUUID())  # Référence users
    verification_required = Column(Boolean, default=False)
    verified_by_id = Column(UniversalUUID())  # Référence users
    verified_date = Column(DateTime)

    # Coûts
    estimated_labor_hours = Column(Numeric(8, 2))
    estimated_labor_cost = Column(Numeric(15, 2))
    estimated_parts_cost = Column(Numeric(15, 2))
    estimated_other_cost = Column(Numeric(15, 2))
    actual_labor_hours = Column(Numeric(8, 2))
    actual_labor_cost = Column(Numeric(15, 2))
    actual_parts_cost = Column(Numeric(15, 2))
    actual_other_cost = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Compteur à la fin
    meter_reading_end = Column(Numeric(15, 4))

    # Pièces jointes
    attachments = Column(JSONB, default=list)

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    asset = relationship("Asset", back_populates="work_orders")
    tasks = relationship("WorkOrderTask", back_populates="work_order", cascade="all, delete-orphan")
    labor_entries = relationship("WorkOrderLabor", back_populates="work_order", cascade="all, delete-orphan")
    parts_used = relationship("WorkOrderPart", back_populates="work_order", cascade="all, delete-orphan")


class WorkOrderTask(Base):
    """Tâche d'un ordre de travail"""
    __tablename__ = "maintenance_wo_tasks"
    __table_args__ = (
        Index("idx_wo_task_tenant", "tenant_id"),
        Index("idx_wo_task_wo", "work_order_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    plan_task_id = Column(UniversalUUID(), ForeignKey("maintenance_plan_tasks.id"))

    # Tâche
    sequence = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    instructions = Column(Text)

    # Durée
    estimated_minutes = Column(Integer)
    actual_minutes = Column(Integer)

    # Statut
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, SKIPPED
    completed_date = Column(DateTime)
    completed_by_id = Column(UniversalUUID())  # Référence users

    # Résultat
    result = Column(Text)
    issues_found = Column(Text)

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    work_order = relationship("MaintenanceWorkOrder", back_populates="tasks")


class WorkOrderLabor(Base):
    """Temps de main d'œuvre sur un OT"""
    __tablename__ = "maintenance_wo_labor"
    __table_args__ = (
        Index("idx_wo_labor_tenant", "tenant_id"),
        Index("idx_wo_labor_wo", "work_order_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)

    # Technicien
    technician_id = Column(UniversalUUID(), nullable=False)  # Référence users
    technician_name = Column(String(200))

    # Temps
    work_date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    hours_worked = Column(Numeric(6, 2), nullable=False)
    overtime_hours = Column(Numeric(6, 2), default=0)

    # Type de travail
    labor_type = Column(String(50))  # REGULAR, OVERTIME, TRAVEL, etc.

    # Coût
    hourly_rate = Column(Numeric(10, 2))
    total_cost = Column(Numeric(12, 2))

    # Description
    work_description = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    work_order = relationship("MaintenanceWorkOrder", back_populates="labor_entries")


class WorkOrderPart(Base):
    """Pièce utilisée sur un OT"""
    __tablename__ = "maintenance_wo_parts"
    __table_args__ = (
        Index("idx_wo_part_tenant", "tenant_id"),
        Index("idx_wo_part_wo", "work_order_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)

    # Pièce
    spare_part_id = Column(UniversalUUID(), ForeignKey("maintenance_spare_parts.id"))
    part_code = Column(String(100))
    part_description = Column(String(300), nullable=False)

    # Quantité
    quantity_planned = Column(Numeric(12, 3))
    quantity_used = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(50))

    # Coût
    unit_cost = Column(Numeric(15, 2))
    total_cost = Column(Numeric(15, 2))

    # Source
    source = Column(String(50))  # STOCK, PURCHASE, RETURN
    source_reference = Column(String(100))

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    work_order = relationship("MaintenanceWorkOrder", back_populates="parts_used")


# ============================================================================
# MODÈLES - PANNES
# ============================================================================

class Failure(Base):
    """Enregistrement de panne"""
    __tablename__ = "maintenance_failures"
    __table_args__ = (
        Index("idx_failure_tenant", "tenant_id"),
        Index("idx_failure_asset", "tenant_id", "asset_id"),
        Index("idx_failure_date", "tenant_id", "failure_date"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    failure_number = Column(String(50), nullable=False)

    # Actif
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id"), nullable=False)
    component_id = Column(UniversalUUID(), ForeignKey("maintenance_asset_components.id"))

    # Description
    failure_type = Column(SQLEnum(FailureType), nullable=False)
    description = Column(Text, nullable=False)
    symptoms = Column(Text)

    # Dates
    failure_date = Column(DateTime, nullable=False)
    detected_date = Column(DateTime)
    reported_date = Column(DateTime)
    resolved_date = Column(DateTime)

    # Impact
    production_stopped = Column(Boolean, default=False)
    downtime_hours = Column(Numeric(8, 2))
    production_loss_units = Column(Numeric(15, 2))
    estimated_cost_impact = Column(Numeric(15, 2))

    # Signalé par
    reported_by_id = Column(UniversalUUID())  # Référence users

    # Ordre de travail généré
    work_order_id = Column(UniversalUUID())

    # Résolution
    resolution = Column(Text)
    root_cause = Column(Text)
    corrective_action = Column(Text)
    preventive_action = Column(Text)

    # Compteur au moment de la panne
    meter_reading = Column(Numeric(15, 4))

    # Statut
    status = Column(String(50), default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, CLOSED

    # Notes
    notes = Column(Text)
    attachments = Column(JSONB, default=list)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    asset = relationship("Asset", back_populates="failures")
    causes = relationship("FailureCause", back_populates="failure", cascade="all, delete-orphan")


class FailureCause(Base):
    """Cause de panne (analyse)"""
    __tablename__ = "maintenance_failure_causes"
    __table_args__ = (
        Index("idx_failure_cause_tenant", "tenant_id"),
        Index("idx_failure_cause_failure", "failure_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    failure_id = Column(UniversalUUID(), ForeignKey("maintenance_failures.id", ondelete="CASCADE"), nullable=False)

    # Cause
    cause_category = Column(String(100))  # EQUIPMENT, HUMAN, PROCESS, etc.
    cause_description = Column(Text, nullable=False)
    is_root_cause = Column(Boolean, default=False)

    # Probabilité
    probability = Column(String(20))  # HIGH, MEDIUM, LOW

    # Action
    recommended_action = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    failure = relationship("Failure", back_populates="causes")


# ============================================================================
# MODÈLES - PIÈCES DE RECHANGE
# ============================================================================

class SparePart(Base):
    """Pièce de rechange"""
    __tablename__ = "maintenance_spare_parts"
    __table_args__ = (
        Index("idx_spare_tenant", "tenant_id"),
        Index("idx_spare_code", "tenant_id", "part_code"),
        UniqueConstraint("tenant_id", "part_code", name="uq_spare_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    part_code = Column(String(100), nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Fabricant
    manufacturer = Column(String(200))
    manufacturer_part_number = Column(String(100))

    # Fournisseur
    preferred_supplier_id = Column(UniversalUUID())  # Référence fournisseur préféré

    # Équivalences
    equivalent_parts = Column(JSONB, default=list)

    # Unité
    unit = Column(String(50), nullable=False)

    # Prix
    unit_cost = Column(Numeric(15, 2))
    last_purchase_price = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Stock
    min_stock_level = Column(Numeric(12, 3), default=0)
    max_stock_level = Column(Numeric(12, 3))
    reorder_point = Column(Numeric(12, 3))
    reorder_quantity = Column(Numeric(12, 3))

    # Délai
    lead_time_days = Column(Integer)

    # Criticité
    criticality = Column(SQLEnum(AssetCriticality))

    # Durée de vie
    shelf_life_days = Column(Integer)

    # Statut
    is_active = Column(Boolean, default=True)

    # Lien produit inventaire
    product_id = Column(UniversalUUID(), ForeignKey("inventory_products.id"))

    # Notes
    notes = Column(Text)
    specifications = Column(JSONB, default=dict)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())

    # Relations
    stock_locations = relationship("SparePartStock", back_populates="spare_part", cascade="all, delete-orphan")


class SparePartStock(Base):
    """Stock de pièce de rechange par emplacement"""
    __tablename__ = "maintenance_spare_part_stock"
    __table_args__ = (
        Index("idx_spare_stock_tenant", "tenant_id"),
        Index("idx_spare_stock_part", "spare_part_id"),
        UniqueConstraint("spare_part_id", "location_id", name="uq_spare_stock_loc"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    spare_part_id = Column(UniversalUUID(), ForeignKey("maintenance_spare_parts.id", ondelete="CASCADE"), nullable=False)

    # Emplacement
    location_id = Column(UniversalUUID())  # Référence warehouse
    location_description = Column(String(200))
    bin_location = Column(String(100))

    # Quantité
    quantity_on_hand = Column(Numeric(12, 3), default=0)
    quantity_reserved = Column(Numeric(12, 3), default=0)
    quantity_available = Column(Numeric(12, 3), default=0)

    # Dernière mise à jour
    last_count_date = Column(Date)
    last_movement_date = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    spare_part = relationship("SparePart", back_populates="stock_locations")


class PartRequest(Base):
    """Demande de pièce"""
    __tablename__ = "maintenance_part_requests"
    __table_args__ = (
        Index("idx_part_req_tenant", "tenant_id"),
        Index("idx_part_req_wo", "work_order_id"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    request_number = Column(String(50), nullable=False)

    # Ordre de travail
    work_order_id = Column(UniversalUUID(), ForeignKey("maintenance_work_orders.id"))

    # Pièce
    spare_part_id = Column(UniversalUUID(), ForeignKey("maintenance_spare_parts.id"))
    part_description = Column(String(300), nullable=False)

    # Quantité
    quantity_requested = Column(Numeric(12, 3), nullable=False)
    quantity_approved = Column(Numeric(12, 3))
    quantity_issued = Column(Numeric(12, 3))
    unit = Column(String(50))

    # Urgence
    priority = Column(SQLEnum(WorkOrderPriority), default=WorkOrderPriority.MEDIUM)
    required_date = Column(Date)

    # Statut
    status = Column(SQLEnum(PartRequestStatus), default=PartRequestStatus.REQUESTED)

    # Demandeur
    requester_id = Column(UniversalUUID())  # Référence users
    request_date = Column(DateTime)
    request_reason = Column(Text)

    # Approbation
    approved_by_id = Column(UniversalUUID())  # Référence users
    approved_date = Column(DateTime)

    # Issue
    issued_by_id = Column(UniversalUUID())  # Référence users
    issued_date = Column(DateTime)

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())


# ============================================================================
# MODÈLES - CONTRATS
# ============================================================================

class MaintenanceContract(Base):
    """Contrat de maintenance"""
    __tablename__ = "maintenance_contracts"
    __table_args__ = (
        Index("idx_mcontract_tenant", "tenant_id"),
        Index("idx_mcontract_code", "tenant_id", "contract_code"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Identification
    contract_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Type
    contract_type = Column(SQLEnum(ContractType), nullable=False)
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.DRAFT)

    # Fournisseur
    vendor_id = Column(UniversalUUID(), nullable=False)  # Référence fournisseur
    vendor_contact = Column(String(200))
    vendor_phone = Column(String(50))
    vendor_email = Column(String(200))

    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renewal_date = Column(Date)
    notice_period_days = Column(Integer)

    # Auto-renouvellement
    auto_renewal = Column(Boolean, default=False)
    renewal_terms = Column(Text)

    # Périmètre
    covered_assets = Column(JSONB, default=list)  # Liste des IDs d'actifs couverts
    coverage_description = Column(Text)
    exclusions = Column(Text)

    # SLA
    response_time_hours = Column(Integer)
    resolution_time_hours = Column(Integer)
    availability_guarantee = Column(Numeric(5, 2))

    # Coûts
    contract_value = Column(Numeric(15, 2))
    annual_cost = Column(Numeric(15, 2))
    payment_frequency = Column(String(50))  # MONTHLY, QUARTERLY, ANNUAL
    currency = Column(String(3), default="EUR")

    # Inclusions
    includes_parts = Column(Boolean, default=False)
    includes_labor = Column(Boolean, default=True)
    includes_travel = Column(Boolean, default=False)
    max_interventions = Column(Integer)
    interventions_used = Column(Integer, default=0)

    # Documents
    contract_file = Column(String(500))
    documents = Column(JSONB, default=list)

    # Responsable
    manager_id = Column(UniversalUUID())  # Référence users

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UniversalUUID())


# ============================================================================
# MODÈLES - KPIs
# ============================================================================

class MaintenanceKPI(Base):
    """KPIs de maintenance"""
    __tablename__ = "maintenance_kpis"
    __table_args__ = (
        Index("idx_mkpi_tenant", "tenant_id"),
        Index("idx_mkpi_asset", "asset_id"),
        Index("idx_mkpi_period", "period_start", "period_end"),
        {"schema": None},
    )

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    # Actif (optionnel - si null = KPIs globaux)
    asset_id = Column(UniversalUUID(), ForeignKey("maintenance_assets.id"))

    # Période
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(20))  # DAILY, WEEKLY, MONTHLY, YEARLY

    # Disponibilité
    availability_rate = Column(Numeric(5, 2))  # %
    uptime_hours = Column(Numeric(12, 2))
    downtime_hours = Column(Numeric(12, 2))
    planned_downtime_hours = Column(Numeric(12, 2))
    unplanned_downtime_hours = Column(Numeric(12, 2))

    # Fiabilité
    mtbf_hours = Column(Numeric(10, 2))  # Mean Time Between Failures
    mttr_hours = Column(Numeric(10, 2))  # Mean Time To Repair
    mttf_hours = Column(Numeric(10, 2))  # Mean Time To Failure
    failure_count = Column(Integer, default=0)

    # Ordres de travail
    wo_total = Column(Integer, default=0)
    wo_preventive = Column(Integer, default=0)
    wo_corrective = Column(Integer, default=0)
    wo_completed = Column(Integer, default=0)
    wo_overdue = Column(Integer, default=0)
    wo_on_time_rate = Column(Numeric(5, 2))

    # Coûts
    total_maintenance_cost = Column(Numeric(15, 2))
    labor_cost = Column(Numeric(15, 2))
    parts_cost = Column(Numeric(15, 2))
    external_cost = Column(Numeric(15, 2))
    cost_per_asset = Column(Numeric(15, 2))
    cost_per_hour = Column(Numeric(15, 2))

    # Préventif vs Correctif
    preventive_ratio = Column(Numeric(5, 2))  # % maintenance préventive

    # Efficacité
    schedule_compliance = Column(Numeric(5, 2))  # % respect planning
    work_order_backlog = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
