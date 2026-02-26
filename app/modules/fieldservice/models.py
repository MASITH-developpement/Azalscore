"""
Modèles SQLAlchemy - Module Field Service (GAP-081)

Gestion des interventions terrain.
Multi-tenant, Soft delete, Audit complet.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from app.core.types import UniversalUUID as UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


# ============== Énumérations ==============

class WorkOrderType(str, Enum):
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INSPECTION = "inspection"
    EMERGENCY = "emergency"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    UPGRADE = "upgrade"


class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.SCHEDULED, cls.CANCELLED],
            cls.SCHEDULED: [cls.DISPATCHED, cls.CANCELLED],
            cls.DISPATCHED: [cls.EN_ROUTE, cls.CANCELLED],
            cls.EN_ROUTE: [cls.ON_SITE, cls.CANCELLED],
            cls.ON_SITE: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.IN_PROGRESS: [cls.PENDING_PARTS, cls.COMPLETED, cls.CANCELLED],
            cls.PENDING_PARTS: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.COMPLETED: [],
            cls.CANCELLED: []
        }


class TechnicianStatus(str, Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"
    UNAVAILABLE = "unavailable"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SkillLevel(str, Enum):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"


# ============== Modèles ==============

class FSTechnician(Base):
    """Technicien terrain."""
    __tablename__ = "technicians"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    employee_id = Column(UUID(), nullable=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    status = Column(SQLEnum(TechnicianStatus), default=TechnicianStatus.AVAILABLE, nullable=False)

    # Géolocalisation
    current_location_lat = Column(Numeric(10, 8), nullable=True)
    current_location_lng = Column(Numeric(11, 8), nullable=True)
    last_location_update = Column(DateTime, nullable=True)

    # Configuration
    home_zone_id = Column(UUID(), ForeignKey('service_zones.id'), nullable=True)
    vehicle_id = Column(UUID(), nullable=True)
    max_daily_work_orders = Column(Integer, default=8)

    # Tarification
    hourly_rate = Column(Numeric(10, 2), default=Decimal("0"))
    overtime_rate = Column(Numeric(10, 2), default=Decimal("0"))

    # Compétences (JSON)
    skills = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    # Soft Delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_tech_tenant', 'tenant_id'),
        Index('ix_tech_tenant_code', 'tenant_id', 'code'),
        Index('ix_tech_tenant_status', 'tenant_id', 'status'),
        UniqueConstraint('tenant_id', 'code', name='uq_tech_tenant_code'),
    )

    home_zone = relationship('FSServiceZone', foreign_keys=[home_zone_id])
    work_orders = relationship('FSWorkOrder', back_populates='technician')

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def can_delete(self) -> tuple[bool, str]:
        return True, ""

    def __repr__(self) -> str:
        return f"<FSTechnician {self.code}: {self.full_name}>"


class FSServiceZone(Base):
    """Zone de service."""
    __tablename__ = "service_zones"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Géographie
    polygon_coordinates = Column(JSONB, default=list)
    center_lat = Column(Numeric(10, 8), nullable=True)
    center_lng = Column(Numeric(11, 8), nullable=True)
    radius_km = Column(Numeric(8, 2), nullable=True)

    assigned_technicians = Column(JSONB, default=list)  # List of UUID strings
    travel_time_minutes = Column(Integer, default=30)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_zone_tenant', 'tenant_id'),
        Index('ix_zone_tenant_code', 'tenant_id', 'code'),
        UniqueConstraint('tenant_id', 'code', name='uq_zone_tenant_code'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        return True, ""


class FSCustomerSite(Base):
    """Site client pour intervention."""
    __tablename__ = "customer_sites"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)

    customer_id = Column(UUID(), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)

    # Adresse
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="France")

    # Géolocalisation
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)

    # Contact
    contact_name = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Instructions
    access_instructions = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)

    equipment_list = Column(JSONB, default=list)
    zone_id = Column(UUID(), ForeignKey('service_zones.id'), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_site_tenant', 'tenant_id'),
        Index('ix_site_tenant_code', 'tenant_id', 'code'),
        Index('ix_site_tenant_customer', 'tenant_id', 'customer_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_site_tenant_code'),
    )

    zone = relationship('FSServiceZone')
    work_orders = relationship('FSWorkOrder', back_populates='site')

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        return True, ""


class FSWorkOrder(Base):
    """Ordre de travail / Intervention."""
    __tablename__ = "work_orders"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Type et statut
    work_order_type = Column(SQLEnum(WorkOrderType), default=WorkOrderType.MAINTENANCE, nullable=False)
    status = Column(SQLEnum(WorkOrderStatus), default=WorkOrderStatus.DRAFT, nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM, nullable=False)

    # Relations
    customer_id = Column(UUID(), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)
    site_id = Column(UUID(), ForeignKey('customer_sites.id'), nullable=True)
    technician_id = Column(UUID(), ForeignKey('technicians.id'), nullable=True)

    # Planification
    scheduled_date = Column(Date, nullable=True)
    scheduled_start_time = Column(DateTime, nullable=True)
    scheduled_end_time = Column(DateTime, nullable=True)
    estimated_duration_minutes = Column(Integer, default=60)

    # Exécution
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)

    # Détails intervention
    lines = Column(JSONB, default=list)
    parts_used = Column(JSONB, default=list)
    labor_entries = Column(JSONB, default=list)

    # Résultat
    resolution_notes = Column(Text, nullable=True)
    customer_signature = Column(Text, nullable=True)  # Base64
    technician_signature = Column(Text, nullable=True)
    photos = Column(JSONB, default=list)

    # Facturation
    billable = Column(Boolean, default=True)
    labor_total = Column(Numeric(12, 2), default=Decimal("0"))
    parts_total = Column(Numeric(12, 2), default=Decimal("0"))
    total_amount = Column(Numeric(12, 2), default=Decimal("0"))
    invoice_id = Column(UUID(), nullable=True)

    # SLA
    sla_due_date = Column(DateTime, nullable=True)
    sla_met = Column(Boolean, nullable=True)

    tags = Column(JSONB, default=list)  # List of strings

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_wo_tenant', 'tenant_id'),
        Index('ix_wo_tenant_code', 'tenant_id', 'code'),
        Index('ix_wo_tenant_status', 'tenant_id', 'status'),
        Index('ix_wo_tenant_date', 'tenant_id', 'scheduled_date'),
        Index('ix_wo_tenant_customer', 'tenant_id', 'customer_id'),
        Index('ix_wo_tenant_technician', 'tenant_id', 'technician_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_wo_tenant_code'),
    )

    site = relationship('FSCustomerSite', back_populates='work_orders')
    technician = relationship('FSTechnician', back_populates='work_orders')

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('status')
    def validate_status_transition(self, key: str, new_status: WorkOrderStatus) -> WorkOrderStatus:
        if self.status is not None and new_status != self.status:
            allowed = WorkOrderStatus.allowed_transitions().get(self.status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        return new_status

    @hybrid_property
    def is_completed(self) -> bool:
        return self.status == WorkOrderStatus.COMPLETED

    @hybrid_property
    def is_overdue(self) -> bool:
        if not self.sla_due_date:
            return False
        return datetime.utcnow() > self.sla_due_date and self.status != WorkOrderStatus.COMPLETED

    def can_delete(self) -> tuple[bool, str]:
        if self.status in [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.COMPLETED]:
            return False, "Cannot delete work order in progress or completed"
        return True, ""

    def __repr__(self) -> str:
        return f"<FSWorkOrder {self.code}: {self.title}>"


class FSSkill(Base):
    """Compétence technique."""
    __tablename__ = "skills"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    certification_required = Column(Boolean, default=False)
    certification_validity_days = Column(Integer, default=365)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(), nullable=True)
    updated_by = Column(UUID(), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index('ix_skill_tenant', 'tenant_id'),
        Index('ix_skill_tenant_code', 'tenant_id', 'code'),
        UniqueConstraint('tenant_id', 'code', name='uq_skill_tenant_code'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        return True, ""


# === Event Listeners ===

@event.listens_for(FSTechnician, 'before_update')
def tech_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FSWorkOrder, 'before_update')
def wo_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FSCustomerSite, 'before_update')
def site_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FSServiceZone, 'before_update')
def zone_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(FSSkill, 'before_update')
def skill_before_update(mapper, connection, target):
    target.version += 1
