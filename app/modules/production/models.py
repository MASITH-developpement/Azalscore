"""
AZALS MODULE M6 - Modèles Production
=====================================

Modèles SQLAlchemy pour la gestion de production.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base

# ============================================================================
# ENUMS
# ============================================================================

class WorkCenterType(str, enum.Enum):
    """Types de centre de travail."""
    MACHINE = "MACHINE"
    ASSEMBLY = "ASSEMBLY"
    MANUAL = "MANUAL"
    QUALITY = "QUALITY"
    PACKAGING = "PACKAGING"
    OUTSOURCED = "OUTSOURCED"


class WorkCenterStatus(str, enum.Enum):
    """Statuts de centre de travail."""
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class BOMType(str, enum.Enum):
    """Types de nomenclature."""
    MANUFACTURING = "MANUFACTURING"
    KIT = "KIT"
    PHANTOM = "PHANTOM"
    SUBCONTRACT = "SUBCONTRACT"


class BOMStatus(str, enum.Enum):
    """Statuts de nomenclature."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OBSOLETE = "OBSOLETE"


class OperationType(str, enum.Enum):
    """Types d'opération."""
    SETUP = "SETUP"
    PRODUCTION = "PRODUCTION"
    QUALITY_CHECK = "QUALITY_CHECK"
    CLEANING = "CLEANING"
    PACKAGING = "PACKAGING"
    TRANSPORT = "TRANSPORT"


class MOStatus(str, enum.Enum):
    """Statuts d'ordre de fabrication."""
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class MOPriority(str, enum.Enum):
    """Priorités d'ordre de fabrication."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class WorkOrderStatus(str, enum.Enum):
    """Statuts d'ordre de travail."""
    PENDING = "PENDING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class ConsumptionType(str, enum.Enum):
    """Types de consommation."""
    MANUAL = "MANUAL"
    AUTO_ON_START = "AUTO_ON_START"
    AUTO_ON_COMPLETE = "AUTO_ON_COMPLETE"


class ScrapReason(str, enum.Enum):
    """Raisons de rebut."""
    DEFECT = "DEFECT"
    DAMAGE = "DAMAGE"
    QUALITY = "QUALITY"
    EXPIRED = "EXPIRED"
    OTHER = "OTHER"


# ============================================================================
# CENTRES DE TRAVAIL
# ============================================================================

class WorkCenter(Base):
    """Centre de travail (machine, poste d'assemblage, etc.)."""
    __tablename__ = "production_work_centers"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(WorkCenterType), default=WorkCenterType.MACHINE)
    status = Column(SQLEnum(WorkCenterStatus), default=WorkCenterStatus.AVAILABLE)

    # Localisation
    warehouse_id = Column(UniversalUUID(), nullable=True)
    location = Column(String(100), nullable=True)

    # Capacité
    capacity = Column(Numeric(10, 2), default=1)  # Nombre d'opérations simultanées
    efficiency = Column(Numeric(5, 2), default=100)  # Pourcentage d'efficacité
    oee_target = Column(Numeric(5, 2), default=85)  # OEE cible (%)

    # Temps standards
    time_start = Column(Numeric(10, 2), default=0)  # Temps de démarrage (minutes)
    time_stop = Column(Numeric(10, 2), default=0)  # Temps d'arrêt (minutes)
    time_before = Column(Numeric(10, 2), default=0)  # Temps avant opération
    time_after = Column(Numeric(10, 2), default=0)  # Temps après opération

    # Coûts
    cost_per_hour = Column(Numeric(12, 4), default=0)
    cost_per_cycle = Column(Numeric(12, 4), default=0)
    currency = Column(String(3), default="EUR")

    # Horaires
    working_hours_per_day = Column(Numeric(4, 2), default=8)
    working_days_per_week = Column(Integer, default=5)

    # Responsable
    manager_id = Column(UniversalUUID(), nullable=True)
    operator_ids = Column(JSONB, nullable=True)  # Liste des opérateurs autorisés

    # Configuration
    requires_approval = Column(Boolean, default=False)
    allow_parallel = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_workcenter_code'),
        Index('idx_wc_tenant', 'tenant_id'),
        Index('idx_wc_status', 'tenant_id', 'status'),
    )


class WorkCenterCapacity(Base):
    """Capacité planifiée d'un centre de travail."""
    __tablename__ = "production_wc_capacity"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_center_id = Column(UniversalUUID(), ForeignKey("production_work_centers.id"), nullable=False)

    date = Column(Date, nullable=False)
    shift = Column(String(20), default="DAY")  # DAY, NIGHT, MORNING, etc.

    available_hours = Column(Numeric(4, 2), nullable=False)
    planned_hours = Column(Numeric(4, 2), default=0)
    actual_hours = Column(Numeric(4, 2), default=0)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'work_center_id', 'date', 'shift', name='unique_wc_capacity'),
        Index('idx_wc_cap_date', 'tenant_id', 'work_center_id', 'date'),
    )


# ============================================================================
# NOMENCLATURES (BOM)
# ============================================================================

class BillOfMaterials(Base):
    """Nomenclature (Bill of Materials)."""
    __tablename__ = "production_bom"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0")

    # Produit fabriqué
    product_id = Column(UniversalUUID(), nullable=False)  # Produit fini
    quantity = Column(Numeric(12, 4), default=1)  # Quantité produite
    unit = Column(String(20), default="UNIT")

    type = Column(SQLEnum(BOMType), default=BOMType.MANUFACTURING)
    status = Column(SQLEnum(BOMStatus), default=BOMStatus.DRAFT)

    # Gamme associée
    routing_id = Column(UniversalUUID(), ForeignKey("production_routings.id"), nullable=True)

    # Dates de validité
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    # Coûts calculés
    material_cost = Column(Numeric(12, 4), default=0)
    labor_cost = Column(Numeric(12, 4), default=0)
    overhead_cost = Column(Numeric(12, 4), default=0)
    total_cost = Column(Numeric(12, 4), default=0)
    currency = Column(String(3), default="EUR")

    # Configuration
    is_default = Column(Boolean, default=False)
    allow_alternatives = Column(Boolean, default=True)
    consumption_type = Column(SQLEnum(ConsumptionType), default=ConsumptionType.AUTO_ON_COMPLETE)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    lines = relationship("BOMLine", back_populates="bom", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', 'version', name='unique_bom_code_version'),
        Index('idx_bom_tenant', 'tenant_id'),
        Index('idx_bom_product', 'tenant_id', 'product_id'),
    )


class BOMLine(Base):
    """Ligne de nomenclature (composant)."""
    __tablename__ = "production_bom_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    bom_id = Column(UniversalUUID(), ForeignKey("production_bom.id"), nullable=False)

    line_number = Column(Integer, nullable=False)
    product_id = Column(UniversalUUID(), nullable=False)  # Composant
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), default="UNIT")

    # Opération associée (si consommé à une étape spécifique)
    operation_id = Column(UniversalUUID(), nullable=True)

    # Gestion des pertes
    scrap_rate = Column(Numeric(5, 2), default=0)  # Taux de rebut (%)

    # Alternatives
    is_critical = Column(Boolean, default=True)  # Si absent, bloque la production
    alternative_group = Column(String(50), nullable=True)  # Groupe d'alternatives

    # Consommation
    consumption_type = Column(SQLEnum(ConsumptionType), nullable=True)  # Override BOM default

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    bom = relationship("BillOfMaterials", back_populates="lines")

    __table_args__ = (
        Index('idx_bom_line', 'tenant_id', 'bom_id'),
    )


# ============================================================================
# GAMMES DE FABRICATION (ROUTINGS)
# ============================================================================

class Routing(Base):
    """Gamme de fabrication (séquence d'opérations)."""
    __tablename__ = "production_routings"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0")

    # Produit concerné
    product_id = Column(UniversalUUID(), nullable=True)

    status = Column(SQLEnum(BOMStatus), default=BOMStatus.DRAFT)

    # Temps totaux calculés
    total_setup_time = Column(Numeric(10, 2), default=0)  # Minutes
    total_operation_time = Column(Numeric(10, 2), default=0)  # Minutes
    total_time = Column(Numeric(10, 2), default=0)  # Minutes

    # Coûts calculés
    total_labor_cost = Column(Numeric(12, 4), default=0)
    total_machine_cost = Column(Numeric(12, 4), default=0)
    currency = Column(String(3), default="EUR")

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    operations = relationship("RoutingOperation", back_populates="routing", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', 'version', name='unique_routing_code_version'),
        Index('idx_routing_tenant', 'tenant_id'),
        Index('idx_routing_product', 'tenant_id', 'product_id'),
    )


class RoutingOperation(Base):
    """Opération dans une gamme de fabrication."""
    __tablename__ = "production_routing_operations"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    routing_id = Column(UniversalUUID(), ForeignKey("production_routings.id"), nullable=False)

    sequence = Column(Integer, nullable=False)  # Ordre d'exécution
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    type = Column(SQLEnum(OperationType), default=OperationType.PRODUCTION)
    work_center_id = Column(UniversalUUID(), ForeignKey("production_work_centers.id"), nullable=True)

    # Temps standards
    setup_time = Column(Numeric(10, 2), default=0)  # Minutes
    operation_time = Column(Numeric(10, 2), default=0)  # Minutes par unité
    cleanup_time = Column(Numeric(10, 2), default=0)  # Minutes
    wait_time = Column(Numeric(10, 2), default=0)  # Temps d'attente

    # Quantités
    batch_size = Column(Numeric(10, 2), default=1)  # Taille de lot

    # Coûts
    labor_cost_per_hour = Column(Numeric(12, 4), default=0)
    machine_cost_per_hour = Column(Numeric(12, 4), default=0)

    # Configuration
    is_subcontracted = Column(Boolean, default=False)
    subcontractor_id = Column(UniversalUUID(), nullable=True)
    requires_quality_check = Column(Boolean, default=False)
    skill_required = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    routing = relationship("Routing", back_populates="operations")

    __table_args__ = (
        Index('idx_routing_op', 'tenant_id', 'routing_id', 'sequence'),
    )


# ============================================================================
# ORDRES DE FABRICATION
# ============================================================================

class ManufacturingOrder(Base):
    """Ordre de fabrication (Manufacturing Order)."""
    __tablename__ = "production_manufacturing_orders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    number = Column(String(50), nullable=False)
    name = Column(String(200), nullable=True)

    # Produit à fabriquer
    product_id = Column(UniversalUUID(), nullable=False)
    bom_id = Column(UniversalUUID(), ForeignKey("production_bom.id"), nullable=True)
    routing_id = Column(UniversalUUID(), ForeignKey("production_routings.id"), nullable=True)

    # Quantités
    quantity_planned = Column(Numeric(12, 4), nullable=False)
    quantity_produced = Column(Numeric(12, 4), default=0)
    quantity_scrapped = Column(Numeric(12, 4), default=0)
    unit = Column(String(20), default="UNIT")

    status = Column(SQLEnum(MOStatus), default=MOStatus.DRAFT)
    priority = Column(SQLEnum(MOPriority), default=MOPriority.NORMAL)

    # Dates
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Localisation
    warehouse_id = Column(UniversalUUID(), nullable=True)
    location_id = Column(UniversalUUID(), nullable=True)

    # Origine
    origin_type = Column(String(50), nullable=True)  # SALES_ORDER, REORDER, MANUAL
    origin_id = Column(UniversalUUID(), nullable=True)
    origin_number = Column(String(50), nullable=True)

    # Coûts
    planned_cost = Column(Numeric(12, 4), default=0)
    actual_cost = Column(Numeric(12, 4), default=0)
    material_cost = Column(Numeric(12, 4), default=0)
    labor_cost = Column(Numeric(12, 4), default=0)
    overhead_cost = Column(Numeric(12, 4), default=0)
    currency = Column(String(3), default="EUR")

    # Responsable
    responsible_id = Column(UniversalUUID(), nullable=True)

    # Progression
    progress_percent = Column(Numeric(5, 2), default=0)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(UniversalUUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    # Relations
    work_orders = relationship("WorkOrder", back_populates="manufacturing_order", cascade="all, delete-orphan")
    consumptions = relationship("MaterialConsumption", back_populates="manufacturing_order", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'number', name='unique_mo_number'),
        Index('idx_mo_tenant', 'tenant_id'),
        Index('idx_mo_status', 'tenant_id', 'status'),
        Index('idx_mo_product', 'tenant_id', 'product_id'),
        Index('idx_mo_dates', 'tenant_id', 'scheduled_start', 'scheduled_end'),
    )


class WorkOrder(Base):
    """Ordre de travail (opération d'un MO)."""
    __tablename__ = "production_work_orders"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    mo_id = Column(UniversalUUID(), ForeignKey("production_manufacturing_orders.id"), nullable=False)

    sequence = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Opération de référence
    operation_id = Column(UniversalUUID(), ForeignKey("production_routing_operations.id"), nullable=True)
    work_center_id = Column(UniversalUUID(), ForeignKey("production_work_centers.id"), nullable=True)

    status = Column(SQLEnum(WorkOrderStatus), default=WorkOrderStatus.PENDING)

    # Quantités
    quantity_planned = Column(Numeric(12, 4), nullable=False)
    quantity_done = Column(Numeric(12, 4), default=0)
    quantity_scrapped = Column(Numeric(12, 4), default=0)

    # Temps planifiés
    setup_time_planned = Column(Numeric(10, 2), default=0)
    operation_time_planned = Column(Numeric(10, 2), default=0)

    # Temps réels
    setup_time_actual = Column(Numeric(10, 2), default=0)
    operation_time_actual = Column(Numeric(10, 2), default=0)

    # Dates
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Opérateur
    operator_id = Column(UniversalUUID(), nullable=True)

    # Coûts
    labor_cost = Column(Numeric(12, 4), default=0)
    machine_cost = Column(Numeric(12, 4), default=0)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    manufacturing_order = relationship("ManufacturingOrder", back_populates="work_orders")
    time_entries = relationship("WorkOrderTimeEntry", back_populates="work_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_wo_mo', 'tenant_id', 'mo_id', 'sequence'),
        Index('idx_wo_wc', 'tenant_id', 'work_center_id', 'status'),
    )


class WorkOrderTimeEntry(Base):
    """Saisie de temps sur un ordre de travail."""
    __tablename__ = "production_wo_time_entries"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("production_work_orders.id"), nullable=False)

    entry_type = Column(String(20), nullable=False)  # SETUP, PRODUCTION, PAUSE, QUALITY
    operator_id = Column(UniversalUUID(), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Numeric(10, 2), nullable=True)

    quantity_produced = Column(Numeric(12, 4), default=0)
    quantity_scrapped = Column(Numeric(12, 4), default=0)
    scrap_reason = Column(SQLEnum(ScrapReason), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    work_order = relationship("WorkOrder", back_populates="time_entries")

    __table_args__ = (
        Index('idx_wo_time', 'tenant_id', 'work_order_id', 'start_time'),
    )


# ============================================================================
# CONSOMMATION DE MATIÈRES
# ============================================================================

class MaterialConsumption(Base):
    """Consommation de matières premières."""
    __tablename__ = "production_material_consumptions"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    mo_id = Column(UniversalUUID(), ForeignKey("production_manufacturing_orders.id"), nullable=False)

    # Composant consommé
    product_id = Column(UniversalUUID(), nullable=False)
    bom_line_id = Column(UniversalUUID(), ForeignKey("production_bom_lines.id"), nullable=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("production_work_orders.id"), nullable=True)

    # Quantités
    quantity_planned = Column(Numeric(12, 4), nullable=False)
    quantity_consumed = Column(Numeric(12, 4), default=0)
    quantity_returned = Column(Numeric(12, 4), default=0)
    unit = Column(String(20), default="UNIT")

    # Traçabilité
    lot_id = Column(UniversalUUID(), nullable=True)
    serial_id = Column(UniversalUUID(), nullable=True)
    warehouse_id = Column(UniversalUUID(), nullable=True)
    location_id = Column(UniversalUUID(), nullable=True)

    # Coût
    unit_cost = Column(Numeric(12, 4), default=0)
    total_cost = Column(Numeric(12, 4), default=0)

    consumed_at = Column(DateTime, nullable=True)
    consumed_by = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    manufacturing_order = relationship("ManufacturingOrder", back_populates="consumptions")

    __table_args__ = (
        Index('idx_consumption_mo', 'tenant_id', 'mo_id'),
        Index('idx_consumption_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# PRODUCTION (OUTPUT)
# ============================================================================

class ProductionOutput(Base):
    """Sortie de production (produits finis)."""
    __tablename__ = "production_outputs"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    mo_id = Column(UniversalUUID(), ForeignKey("production_manufacturing_orders.id"), nullable=False)
    work_order_id = Column(UniversalUUID(), ForeignKey("production_work_orders.id"), nullable=True)

    # Produit fabriqué
    product_id = Column(UniversalUUID(), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), default="UNIT")

    # Traçabilité
    lot_id = Column(UniversalUUID(), nullable=True)
    serial_ids = Column(JSONB, nullable=True)  # Liste de numéros de série
    warehouse_id = Column(UniversalUUID(), nullable=True)
    location_id = Column(UniversalUUID(), nullable=True)

    # Qualité
    is_quality_passed = Column(Boolean, default=True)
    quality_notes = Column(Text, nullable=True)

    # Coût
    unit_cost = Column(Numeric(12, 4), default=0)
    total_cost = Column(Numeric(12, 4), default=0)

    produced_at = Column(DateTime, default=datetime.utcnow)
    produced_by = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_output_mo', 'tenant_id', 'mo_id'),
        Index('idx_output_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# REBUTS
# ============================================================================

class ProductionScrap(Base):
    """Enregistrement de rebuts."""
    __tablename__ = "production_scraps"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    mo_id = Column(UniversalUUID(), ForeignKey("production_manufacturing_orders.id"), nullable=True)
    work_order_id = Column(UniversalUUID(), ForeignKey("production_work_orders.id"), nullable=True)

    # Produit rebuté
    product_id = Column(UniversalUUID(), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(20), default="UNIT")

    # Traçabilité
    lot_id = Column(UniversalUUID(), nullable=True)
    serial_id = Column(UniversalUUID(), nullable=True)

    # Raison
    reason = Column(SQLEnum(ScrapReason), default=ScrapReason.DEFECT)
    reason_detail = Column(Text, nullable=True)
    work_center_id = Column(UniversalUUID(), nullable=True)

    # Coût
    unit_cost = Column(Numeric(12, 4), default=0)
    total_cost = Column(Numeric(12, 4), default=0)

    scrapped_at = Column(DateTime, default=datetime.utcnow)
    scrapped_by = Column(UniversalUUID(), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_scrap_mo', 'tenant_id', 'mo_id'),
        Index('idx_scrap_product', 'tenant_id', 'product_id'),
        Index('idx_scrap_reason', 'tenant_id', 'reason'),
    )


# ============================================================================
# PLANIFICATION
# ============================================================================

class ProductionPlan(Base):
    """Plan de production."""
    __tablename__ = "production_plans"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Période
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    planning_horizon_days = Column(Integer, default=30)

    # Statut
    status = Column(String(20), default="DRAFT")  # DRAFT, ACTIVE, COMPLETED, CANCELLED

    # Méthode de planification
    planning_method = Column(String(50), default="MRP")  # MRP, KANBAN, MIXED

    # Résumé
    total_orders = Column(Integer, default=0)
    total_quantity = Column(Numeric(12, 2), default=0)
    total_hours = Column(Numeric(10, 2), default=0)

    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    generated_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(UniversalUUID(), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UniversalUUID(), nullable=True)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='unique_plan_code'),
        Index('idx_plan_tenant', 'tenant_id'),
        Index('idx_plan_dates', 'tenant_id', 'start_date', 'end_date'),
    )


class ProductionPlanLine(Base):
    """Ligne de plan de production."""
    __tablename__ = "production_plan_lines"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    plan_id = Column(UniversalUUID(), ForeignKey("production_plans.id"), nullable=False)

    product_id = Column(UniversalUUID(), nullable=False)
    bom_id = Column(UniversalUUID(), nullable=True)

    # Quantités
    quantity_demanded = Column(Numeric(12, 4), default=0)  # Demande
    quantity_available = Column(Numeric(12, 4), default=0)  # Stock disponible
    quantity_to_produce = Column(Numeric(12, 4), default=0)  # À produire

    # Dates
    required_date = Column(Date, nullable=True)
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)

    # Ordre de fabrication généré
    mo_id = Column(UniversalUUID(), ForeignKey("production_manufacturing_orders.id"), nullable=True)

    priority = Column(SQLEnum(MOPriority), default=MOPriority.NORMAL)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_plan_line', 'tenant_id', 'plan_id'),
        Index('idx_plan_line_product', 'tenant_id', 'product_id'),
    )


# ============================================================================
# MAINTENANCE PRÉVENTIVE (lié aux centres de travail)
# ============================================================================

class MaintenanceSchedule(Base):
    """Calendrier de maintenance préventive."""
    __tablename__ = "production_maintenance_schedules"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), nullable=False, index=True)
    work_center_id = Column(UniversalUUID(), ForeignKey("production_work_centers.id"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Fréquence
    frequency_type = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, HOURS, CYCLES
    frequency_value = Column(Integer, default=1)

    # Durée estimée
    duration_hours = Column(Numeric(6, 2), default=1)

    # Suivi
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    cycles_since_last = Column(Integer, default=0)
    hours_since_last = Column(Numeric(10, 2), default=0)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_maint_wc', 'tenant_id', 'work_center_id'),
        Index('idx_maint_next', 'tenant_id', 'next_maintenance'),
    )
