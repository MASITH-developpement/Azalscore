"""
Modèles SQLAlchemy Manufacturing / Fabrication
===============================================
- Multi-tenant obligatoire (tenant_id sur TOUTES les entités)
- Soft delete (is_deleted, deleted_at, deleted_by)
- Audit complet (created_at/by, updated_at/by)
- Versioning (optimistic locking)

Entités:
- BOM (Bill of Materials / Nomenclature)
- BOMLine (Ligne de nomenclature)
- Workcenter (Poste de travail)
- Routing (Gamme de production)
- Operation (Opération de gamme)
- WorkOrder (Ordre de fabrication)
- WorkOrderOperation (Opération d'OF)
- QualityCheck (Contrôle qualité)
- ProductionLog (Journal de production)
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from app.core.types import UniversalUUID as UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.ext.hybrid import hybrid_property

from app.db import Base, uuid_fk_column


# ============== Énumérations ==============

class BOMType(str, Enum):
    """Type de nomenclature."""
    MANUFACTURING = "manufacturing"
    ASSEMBLY = "assembly"
    SUBCONTRACTING = "subcontracting"
    PHANTOM = "phantom"
    KIT = "kit"


class BOMStatus(str, Enum):
    """Statut de nomenclature."""
    DRAFT = "draft"
    ACTIVE = "active"
    OBSOLETE = "obsolete"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.ACTIVE, cls.OBSOLETE],
            cls.ACTIVE: [cls.OBSOLETE],
            cls.OBSOLETE: []
        }


class WorkcenterType(str, Enum):
    """Type de poste de travail."""
    MACHINE = "machine"
    MANUAL = "manual"
    ASSEMBLY = "assembly"
    QUALITY = "quality"
    PACKAGING = "packaging"


class WorkcenterState(str, Enum):
    """État du poste de travail."""
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class WorkOrderStatus(str, Enum):
    """Statut d'ordre de fabrication."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.CONFIRMED, cls.CANCELLED],
            cls.CONFIRMED: [cls.PLANNED, cls.IN_PROGRESS, cls.CANCELLED],
            cls.PLANNED: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.IN_PROGRESS: [cls.PAUSED, cls.COMPLETED, cls.CANCELLED],
            cls.PAUSED: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.COMPLETED: [],
            cls.CANCELLED: []
        }


class OperationStatus(str, Enum):
    """Statut d'opération."""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class QualityCheckType(str, Enum):
    """Type de contrôle qualité."""
    INCOMING = "incoming"
    IN_PROCESS = "in_process"
    FINAL = "final"


class QualityResult(str, Enum):
    """Résultat du contrôle qualité."""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"


# ============== Modèles ==============

class BOM(Base):
    """
    Nomenclature (Bill of Materials).

    Définit les composants nécessaires pour fabriquer un produit.
    """
    __tablename__ = "manufacturing_boms"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Type et statut ===
    bom_type = Column(
        SQLEnum(BOMType, name="bom_type_enum", create_type=False),
        default=BOMType.MANUFACTURING,
        nullable=False
    )
    status = Column(
        SQLEnum(BOMStatus, name="bom_status_enum", create_type=False),
        default=BOMStatus.DRAFT,
        nullable=False
    )

    # === Produit fini ===
    product_id = Column(UUID(), nullable=False, index=True)
    product_code = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(15, 4), default=Decimal("1"), nullable=False)
    unit = Column(String(20), default="", nullable=False)

    # === Coûts calculés ===
    material_cost = Column(Numeric(15, 2), default=Decimal("0"))
    labor_cost = Column(Numeric(15, 2), default=Decimal("0"))
    overhead_cost = Column(Numeric(15, 2), default=Decimal("0"))
    total_cost = Column(Numeric(15, 2), default=Decimal("0"))

    # === Gamme associée ===
    routing_id = Column(UUID(), nullable=True)

    # === Rendement ===
    yield_rate = Column(Numeric(5, 2), default=Decimal("100"))

    # === Validité ===
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)

    # === Version ===
    bom_version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # === Optimistic Locking ===
    version = Column(Integer, default=1, nullable=False)

    # === Métadonnées ===
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    lines = relationship(
        "ManufacturingBOMLine",
        back_populates="bom",
        cascade="all, delete-orphan",
        order_by="ManufacturingBOMLine.sequence"
    )

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_bom_tenant', 'tenant_id'),
        Index('ix_mfg_bom_tenant_code', 'tenant_id', 'code'),
        Index('ix_mfg_bom_tenant_product', 'tenant_id', 'product_id'),
        Index('ix_mfg_bom_tenant_status', 'tenant_id', 'status'),
        Index('ix_mfg_bom_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_mfg_bom_tenant_code'),
        CheckConstraint('quantity > 0', name='ck_mfg_bom_quantity_positive'),
        CheckConstraint('yield_rate >= 0 AND yield_rate <= 100', name='ck_mfg_bom_yield_valid'),
    )

    # === Validateurs ===
    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('status')
    def validate_status_transition(self, key: str, new_status: BOMStatus) -> BOMStatus:
        if self.status is not None and new_status != self.status:
            allowed = BOMStatus.allowed_transitions().get(self.status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        return new_status

    # === Propriétés ===
    @hybrid_property
    def is_active(self) -> bool:
        return self.status == BOMStatus.ACTIVE and not self.is_deleted

    @hybrid_property
    def display_name(self) -> str:
        return f"[{self.code}] {self.name}"

    @hybrid_property
    def line_count(self) -> int:
        return len(self.lines) if self.lines else 0

    def can_delete(self) -> tuple[bool, str]:
        """Vérifie si la BOM peut être supprimée."""
        if self.status == BOMStatus.ACTIVE:
            return False, "Cannot delete active BOM"
        return True, ""

    def recalculate_costs(self) -> None:
        """Recalcule les coûts totaux."""
        self.material_cost = sum(
            line.total_cost for line in self.lines
            if not line.is_optional
        )
        self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost

    def __repr__(self) -> str:
        return f"<BOM {self.code}: {self.name}>"


class ManufacturingBOMLine(Base):
    """
    Ligne de nomenclature (composant) - Manufacturing.
    Renommé pour éviter conflit avec production.BOMLine.
    """
    __tablename__ = "manufacturing_bom_lines"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    bom_id = Column(
        UUID(),
        ForeignKey('manufacturing_boms.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sequence = Column(Integer, default=10, nullable=False)

    # === Composant ===
    component_id = Column(UUID(), nullable=False, index=True)
    component_code = Column(String(50), nullable=False)
    component_name = Column(String(255), nullable=False)

    # === Quantités ===
    quantity = Column(Numeric(15, 4), default=Decimal("1"), nullable=False)
    unit = Column(String(20), default="", nullable=False)

    # === Coûts ===
    unit_cost = Column(Numeric(15, 4), default=Decimal("0"))
    total_cost = Column(Numeric(15, 2), default=Decimal("0"))

    # === Options ===
    is_optional = Column(Boolean, default=False, nullable=False)
    scrap_rate = Column(Numeric(5, 2), default=Decimal("0"))

    # === Substituts ===
    substitute_ids = Column(ARRAY(UUID()), default=list)

    # === Opération liée ===
    operation_id = Column(UUID(), nullable=True)

    # === Notes ===
    notes = Column(Text, nullable=True)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)

    # === Relations ===
    bom = relationship("BOM", back_populates="lines")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_bomline_tenant', 'tenant_id'),
        Index('ix_mfg_bomline_bom', 'bom_id'),
        Index('ix_mfg_bomline_component', 'component_id'),
        CheckConstraint('quantity > 0', name='ck_mfg_bomline_quantity_positive'),
        CheckConstraint('scrap_rate >= 0 AND scrap_rate <= 100', name='ck_mfg_bomline_scrap_valid'),
    )

    @validates('quantity')
    def validate_quantity(self, key: str, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value

    def calculate_total_cost(self) -> Decimal:
        """Calcule le coût total incluant le taux de rebut."""
        effective_qty = self.quantity * (1 + self.scrap_rate / 100)
        self.total_cost = effective_qty * self.unit_cost
        return self.total_cost

    def __repr__(self) -> str:
        return f"<BOMLine {self.component_code} x{self.quantity}>"


class Workcenter(Base):
    """
    Poste de travail.
    """
    __tablename__ = "manufacturing_workcenters"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Type et état ===
    workcenter_type = Column(
        SQLEnum(WorkcenterType, name="workcenter_type_enum", create_type=False),
        default=WorkcenterType.MACHINE,
        nullable=False
    )
    state = Column(
        SQLEnum(WorkcenterState, name="workcenter_state_enum", create_type=False),
        default=WorkcenterState.AVAILABLE,
        nullable=False
    )

    # === Capacité ===
    capacity = Column(Numeric(10, 2), default=Decimal("1"))
    capacity_unit = Column(String(50), default="units/hour")

    # === Coûts ===
    hourly_cost = Column(Numeric(15, 2), default=Decimal("0"))
    setup_cost = Column(Numeric(15, 2), default=Decimal("0"))

    # === Temps par défaut ===
    default_setup_time = Column(Integer, default=0)  # Minutes
    default_cleanup_time = Column(Integer, default=0)

    # === Disponibilité ===
    working_hours_per_day = Column(Numeric(4, 2), default=Decimal("8"))
    efficiency = Column(Numeric(5, 2), default=Decimal("100"))

    # === Localisation ===
    location = Column(String(255), default="")
    department = Column(String(100), default="")

    # === Opérateurs ===
    operator_ids = Column(ARRAY(UUID()), default=list)
    max_operators = Column(Integer, default=1)

    # === Maintenance ===
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)

    # === Équipements ===
    equipment_ids = Column(ARRAY(UUID()), default=list)

    # === Statut ===
    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # === Optimistic Locking ===
    version = Column(Integer, default=1, nullable=False)

    # === Métadonnées ===
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_wc_tenant', 'tenant_id'),
        Index('ix_mfg_wc_tenant_code', 'tenant_id', 'code'),
        Index('ix_mfg_wc_tenant_state', 'tenant_id', 'state'),
        Index('ix_mfg_wc_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_mfg_wc_tenant_code'),
        CheckConstraint('capacity > 0', name='ck_mfg_wc_capacity_positive'),
        CheckConstraint('efficiency >= 0 AND efficiency <= 100', name='ck_mfg_wc_efficiency_valid'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def display_name(self) -> str:
        return f"[{self.code}] {self.name}"

    def can_delete(self) -> tuple[bool, str]:
        if self.state == WorkcenterState.BUSY:
            return False, "Cannot delete busy workcenter"
        return True, ""

    def __repr__(self) -> str:
        return f"<Workcenter {self.code}: {self.name}>"


class Routing(Base):
    """
    Gamme de production.
    """
    __tablename__ = "manufacturing_routings"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Produit ===
    product_id = Column(UUID(), nullable=False, index=True)
    bom_id = Column(UUID(), nullable=True)

    # === Temps totaux ===
    total_setup_time = Column(Integer, default=0)  # Minutes
    total_run_time = Column(Integer, default=0)
    total_time = Column(Integer, default=0)

    # === Coût par unité ===
    total_cost_per_unit = Column(Numeric(15, 4), default=Decimal("0"))

    # === Version ===
    routing_version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # === Optimistic Locking ===
    version = Column(Integer, default=1, nullable=False)

    # === Métadonnées ===
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    operations = relationship(
        "Operation",
        back_populates="routing",
        cascade="all, delete-orphan",
        order_by="Operation.sequence"
    )

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_routing_tenant', 'tenant_id'),
        Index('ix_mfg_routing_tenant_code', 'tenant_id', 'code'),
        Index('ix_mfg_routing_tenant_product', 'tenant_id', 'product_id'),
        Index('ix_mfg_routing_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_mfg_routing_tenant_code'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def recalculate_totals(self) -> None:
        """Recalcule les temps et coûts totaux."""
        self.total_setup_time = sum(op.setup_time for op in self.operations)
        self.total_run_time = sum(op.run_time for op in self.operations)
        self.total_time = self.total_setup_time + self.total_run_time
        self.total_cost_per_unit = sum(op.total_cost_per_unit for op in self.operations)

    def __repr__(self) -> str:
        return f"<Routing {self.code}: {self.name}>"


class Operation(Base):
    """
    Opération de gamme.
    """
    __tablename__ = "manufacturing_operations"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    routing_id = Column(
        UUID(),
        ForeignKey('manufacturing_routings.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sequence = Column(Integer, default=10, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Poste de travail ===
    workcenter_id = Column(UUID(), nullable=False, index=True)
    workcenter_name = Column(String(255), default="")

    # === Temps (minutes) ===
    setup_time = Column(Integer, default=0)
    run_time = Column(Integer, default=0)
    cleanup_time = Column(Integer, default=0)
    wait_time = Column(Integer, default=0)

    # === Coûts par unité ===
    labor_cost_per_unit = Column(Numeric(15, 4), default=Decimal("0"))
    machine_cost_per_unit = Column(Numeric(15, 4), default=Decimal("0"))
    total_cost_per_unit = Column(Numeric(15, 4), default=Decimal("0"))

    # === Qualité ===
    quality_check_required = Column(Boolean, default=False)
    quality_check_type = Column(
        SQLEnum(QualityCheckType, name="quality_check_type_enum", create_type=False),
        nullable=True
    )

    # === Instructions ===
    instructions = Column(Text, nullable=True)
    attachments = Column(ARRAY(String), default=list)
    tools_required = Column(ARRAY(String), default=list)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)

    # === Relations ===
    routing = relationship("Routing", back_populates="operations")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_op_tenant', 'tenant_id'),
        Index('ix_mfg_op_routing', 'routing_id'),
        Index('ix_mfg_op_workcenter', 'workcenter_id'),
        CheckConstraint('setup_time >= 0', name='ck_mfg_op_setup_positive'),
        CheckConstraint('run_time >= 0', name='ck_mfg_op_run_positive'),
    )

    def calculate_costs(self, hourly_rate: Decimal) -> None:
        """Calcule les coûts de l'opération."""
        total_time_hours = Decimal(str((self.setup_time + self.run_time + self.cleanup_time) / 60))
        self.labor_cost_per_unit = hourly_rate * total_time_hours
        self.machine_cost_per_unit = self.labor_cost_per_unit  # Simplifié
        self.total_cost_per_unit = self.labor_cost_per_unit + self.machine_cost_per_unit

    def __repr__(self) -> str:
        return f"<Operation {self.sequence}: {self.name}>"


class WorkOrder(Base):
    """
    Ordre de fabrication.
    """
    __tablename__ = "manufacturing_work_orders"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    # === Statut ===
    status = Column(
        SQLEnum(WorkOrderStatus, name="work_order_status_enum", create_type=False),
        default=WorkOrderStatus.DRAFT,
        nullable=False
    )

    # === Produit ===
    product_id = Column(UUID(), nullable=False, index=True)
    product_code = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    bom_id = Column(UUID(), nullable=True)
    routing_id = Column(UUID(), nullable=True)

    # === Quantités ===
    quantity_to_produce = Column(Numeric(15, 4), nullable=False)
    quantity_produced = Column(Numeric(15, 4), default=Decimal("0"))
    quantity_scrapped = Column(Numeric(15, 4), default=Decimal("0"))
    unit = Column(String(20), default="")

    # === Dates planifiées ===
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)

    # === Dates réelles ===
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # === Priorité ===
    priority = Column(Integer, default=0)

    # === Source ===
    source_type = Column(String(50), default="manual")
    source_id = Column(UUID(), nullable=True)

    # === Coûts planifiés ===
    planned_material_cost = Column(Numeric(15, 2), default=Decimal("0"))
    planned_labor_cost = Column(Numeric(15, 2), default=Decimal("0"))
    planned_overhead_cost = Column(Numeric(15, 2), default=Decimal("0"))
    planned_total_cost = Column(Numeric(15, 2), default=Decimal("0"))

    # === Coûts réels ===
    actual_material_cost = Column(Numeric(15, 2), default=Decimal("0"))
    actual_labor_cost = Column(Numeric(15, 2), default=Decimal("0"))
    actual_overhead_cost = Column(Numeric(15, 2), default=Decimal("0"))
    actual_total_cost = Column(Numeric(15, 2), default=Decimal("0"))

    # === Localisation ===
    production_location = Column(String(255), default="")

    # === Responsable ===
    responsible_id = Column(UUID(), nullable=True)

    # === Notes ===
    notes = Column(Text, nullable=True)

    # === Composants consommés ===
    components_consumed = Column(JSONB, default=list)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # === Optimistic Locking ===
    version = Column(Integer, default=1, nullable=False)

    # === Métadonnées ===
    tags = Column(ARRAY(String), default=list)
    extra_data = Column(JSONB, default=dict)

    # === Relations ===
    operations = relationship(
        "WorkOrderOperation",
        back_populates="work_order",
        cascade="all, delete-orphan",
        order_by="WorkOrderOperation.sequence"
    )
    quality_checks = relationship(
        "QualityCheck",
        back_populates="work_order",
        cascade="all, delete-orphan"
    )
    production_logs = relationship(
        "ProductionLog",
        back_populates="work_order",
        cascade="all, delete-orphan"
    )

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_wo_tenant', 'tenant_id'),
        Index('ix_mfg_wo_tenant_number', 'tenant_id', 'number'),
        Index('ix_mfg_wo_tenant_status', 'tenant_id', 'status'),
        Index('ix_mfg_wo_tenant_product', 'tenant_id', 'product_id'),
        Index('ix_mfg_wo_tenant_deleted', 'tenant_id', 'is_deleted'),
        Index('ix_mfg_wo_planned_start', 'planned_start'),
        UniqueConstraint('tenant_id', 'number', name='uq_mfg_wo_tenant_number'),
        CheckConstraint('quantity_to_produce > 0', name='ck_mfg_wo_qty_positive'),
        CheckConstraint('quantity_produced >= 0', name='ck_mfg_wo_qty_produced_positive'),
        CheckConstraint('quantity_scrapped >= 0', name='ck_mfg_wo_qty_scrapped_positive'),
    )

    @validates('status')
    def validate_status_transition(self, key: str, new_status: WorkOrderStatus) -> WorkOrderStatus:
        if self.status is not None and new_status != self.status:
            allowed = WorkOrderStatus.allowed_transitions().get(self.status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        return new_status

    @hybrid_property
    def is_complete(self) -> bool:
        return self.status == WorkOrderStatus.COMPLETED

    @hybrid_property
    def completion_rate(self) -> Decimal:
        if self.quantity_to_produce == 0:
            return Decimal("0")
        return (self.quantity_produced / self.quantity_to_produce * 100).quantize(Decimal("0.01"))

    @hybrid_property
    def scrap_rate(self) -> Decimal:
        total = self.quantity_produced + self.quantity_scrapped
        if total == 0:
            return Decimal("0")
        return (self.quantity_scrapped / total * 100).quantize(Decimal("0.01"))

    def can_delete(self) -> tuple[bool, str]:
        if self.status in [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.COMPLETED]:
            return False, f"Cannot delete work order in status {self.status}"
        return True, ""

    def __repr__(self) -> str:
        return f"<WorkOrder {self.number}: {self.product_code}>"


class WorkOrderOperation(Base):
    """
    Opération d'un ordre de fabrication.
    """
    __tablename__ = "manufacturing_wo_operations"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    work_order_id = Column(
        UUID(),
        ForeignKey('manufacturing_work_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    operation_id = Column(UUID(), nullable=True)
    sequence = Column(Integer, default=10, nullable=False)
    name = Column(String(255), nullable=False)

    # === Poste de travail ===
    workcenter_id = Column(UUID(), nullable=True)

    # === Statut ===
    status = Column(
        SQLEnum(OperationStatus, name="operation_status_enum", create_type=False),
        default=OperationStatus.PENDING,
        nullable=False
    )

    # === Temps planifiés ===
    planned_setup_time = Column(Integer, default=0)
    planned_run_time = Column(Integer, default=0)

    # === Temps réels ===
    actual_setup_time = Column(Integer, default=0)
    actual_run_time = Column(Integer, default=0)

    # === Dates ===
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # === Quantités ===
    quantity_to_produce = Column(Numeric(15, 4), default=Decimal("0"))
    quantity_produced = Column(Numeric(15, 4), default=Decimal("0"))
    quantity_scrapped = Column(Numeric(15, 4), default=Decimal("0"))

    # === Opérateur ===
    operator_id = Column(UUID(), nullable=True)
    operator_name = Column(String(255), default="")

    # === Qualité ===
    quality_check_passed = Column(Boolean, nullable=True)
    quality_notes = Column(Text, nullable=True)

    # === Notes ===
    notes = Column(Text, nullable=True)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Relations ===
    work_order = relationship("WorkOrder", back_populates="operations")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_woop_tenant', 'tenant_id'),
        Index('ix_mfg_woop_wo', 'work_order_id'),
        Index('ix_mfg_woop_status', 'status'),
    )

    def __repr__(self) -> str:
        return f"<WorkOrderOperation {self.sequence}: {self.name}>"


class QualityCheck(Base):
    """
    Contrôle qualité.
    """
    __tablename__ = "manufacturing_quality_checks"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    work_order_id = Column(
        UUID(),
        ForeignKey('manufacturing_work_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    operation_id = Column(UUID(), nullable=True)

    # === Type et résultat ===
    check_type = Column(
        SQLEnum(QualityCheckType, name="qc_type_enum", create_type=False),
        default=QualityCheckType.IN_PROCESS,
        nullable=False
    )
    result = Column(
        SQLEnum(QualityResult, name="qc_result_enum", create_type=False),
        nullable=True
    )

    # === Spécifications ===
    specifications = Column(JSONB, default=list)

    # === Échantillonnage ===
    sample_size = Column(Integer, default=1)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # === Inspecteur ===
    inspector_id = Column(UUID(), nullable=True)
    inspector_name = Column(String(255), default="")

    # === Date du contrôle ===
    checked_at = Column(DateTime, nullable=True)

    # === Actions ===
    corrective_actions = Column(Text, nullable=True)
    disposition = Column(String(50), default="")

    # === Notes ===
    notes = Column(Text, nullable=True)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)

    # === Relations ===
    work_order = relationship("WorkOrder", back_populates="quality_checks")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_qc_tenant', 'tenant_id'),
        Index('ix_mfg_qc_wo', 'work_order_id'),
        Index('ix_mfg_qc_type', 'check_type'),
        Index('ix_mfg_qc_result', 'result'),
    )

    @hybrid_property
    def is_passed(self) -> bool:
        return self.result == QualityResult.PASS

    def __repr__(self) -> str:
        return f"<QualityCheck {self.check_type}: {self.result}>"


class ProductionLog(Base):
    """
    Journal de production.
    """
    __tablename__ = "manufacturing_production_logs"

    # === Identifiants ===
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    work_order_id = Column(
        UUID(),
        ForeignKey('manufacturing_work_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    operation_id = Column(UUID(), nullable=True)

    # === Type d'événement ===
    event_type = Column(String(50), nullable=False)

    # === Quantité ===
    quantity = Column(Numeric(15, 4), default=Decimal("0"))
    unit = Column(String(20), default="")

    # === Temps ===
    duration_minutes = Column(Integer, default=0)

    # === Opérateur ===
    operator_id = Column(UUID(), nullable=True)

    # === Poste de travail ===
    workcenter_id = Column(UUID(), nullable=True)

    # === Détails ===
    details = Column(JSONB, default=dict)

    # === Timestamp ===
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # === Relations ===
    work_order = relationship("WorkOrder", back_populates="production_logs")

    # === Contraintes ===
    __table_args__ = (
        Index('ix_mfg_log_tenant', 'tenant_id'),
        Index('ix_mfg_log_wo', 'work_order_id'),
        Index('ix_mfg_log_type', 'event_type'),
        Index('ix_mfg_log_timestamp', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<ProductionLog {self.event_type} @ {self.timestamp}>"


# ============== Event Listeners ==============

@event.listens_for(BOM, 'before_update')
def bom_before_update(mapper, connection, target):
    """Incrémenter version avant mise à jour."""
    target.version += 1


@event.listens_for(Workcenter, 'before_update')
def workcenter_before_update(mapper, connection, target):
    """Incrémenter version avant mise à jour."""
    target.version += 1


@event.listens_for(Routing, 'before_update')
def routing_before_update(mapper, connection, target):
    """Incrémenter version avant mise à jour."""
    target.version += 1


@event.listens_for(WorkOrder, 'before_update')
def work_order_before_update(mapper, connection, target):
    """Incrémenter version avant mise à jour."""
    target.version += 1
