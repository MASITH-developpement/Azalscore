"""
Modèles SQLAlchemy Requisition / Demandes d'achat
=================================================
- Multi-tenant obligatoire
- Soft delete
- Audit complet
- Versioning
"""
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum
)
from app.core.types import UniversalUUID as UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from app.core.database import Base


# ============== Enums ==============

class RequisitionType(str, Enum):
    """Types de demande"""
    GOODS = "goods"
    SERVICES = "services"
    EQUIPMENT = "equipment"
    MAINTENANCE = "maintenance"
    IT = "it"
    OFFICE_SUPPLIES = "office_supplies"
    TRAVEL = "travel"
    TRAINING = "training"
    MARKETING = "marketing"
    OTHER = "other"


class RequisitionStatus(str, Enum):
    """Statuts de demande"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_ORDERED = "partially_ordered"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.SUBMITTED, cls.CANCELLED],
            cls.SUBMITTED: [cls.PENDING_APPROVAL, cls.APPROVED, cls.REJECTED, cls.CANCELLED],
            cls.PENDING_APPROVAL: [cls.APPROVED, cls.REJECTED, cls.CANCELLED],
            cls.APPROVED: [cls.PARTIALLY_ORDERED, cls.ORDERED, cls.CANCELLED],
            cls.REJECTED: [cls.DRAFT],
            cls.PARTIALLY_ORDERED: [cls.ORDERED, cls.PARTIALLY_RECEIVED, cls.CANCELLED],
            cls.ORDERED: [cls.PARTIALLY_RECEIVED, cls.RECEIVED, cls.CANCELLED],
            cls.PARTIALLY_RECEIVED: [cls.RECEIVED],
            cls.RECEIVED: [cls.CLOSED],
            cls.CLOSED: [],
            cls.CANCELLED: [],
        }


class LineStatus(str, Enum):
    """Statuts de ligne"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priorités"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class CatalogItemStatus(str, Enum):
    """Statuts article catalogue"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"
    DISCONTINUED = "discontinued"


class ApprovalStatus(str, Enum):
    """Statuts d'approbation"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============== Models ==============

class CatalogCategory(Base):
    """Catégorie du catalogue interne"""
    __tablename__ = "requisition_catalog_categories"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    parent_id = Column(UUID(), ForeignKey("requisition_catalog_categories.id"), nullable=True)

    gl_account = Column(String(50), default="")
    requires_approval = Column(Boolean, default=False)
    approval_threshold = Column(Numeric(15, 2), nullable=True)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    parent = relationship("CatalogCategory", remote_side=[id], backref="children")
    items = relationship("CatalogItem", back_populates="category", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_catalog_category_tenant_code"),
        Index("ix_catalog_category_tenant_active", "tenant_id", "is_active"),
        Index("ix_catalog_category_parent", "parent_id"),
    )


class CatalogItem(Base):
    """Article du catalogue interne"""
    __tablename__ = "requisition_catalog_items"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")

    category_id = Column(UUID(), ForeignKey("requisition_catalog_categories.id"), nullable=True)
    category_name = Column(String(200), default="")

    # Prix
    unit_price = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR")
    unit_of_measure = Column(String(20), default="EA")

    # Fournisseur préféré
    preferred_vendor_id = Column(UUID(), nullable=True)
    preferred_vendor_name = Column(String(200), default="")
    vendor_item_code = Column(String(50), default="")
    lead_time_days = Column(Integer, default=0)

    # Quantités
    min_order_qty = Column(Integer, default=1)
    max_order_qty = Column(Integer, nullable=True)
    order_multiple = Column(Integer, default=1)

    # Statut
    status = Column(SQLEnum(CatalogItemStatus), default=CatalogItemStatus.ACTIVE, nullable=False)

    # Métadonnées
    image_url = Column(String(500), default="")
    specifications = Column(JSONB, default=dict)
    tags = Column(ARRAY(String), default=list)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    category = relationship("CatalogCategory", back_populates="items")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_catalog_item_tenant_code"),
        Index("ix_catalog_item_tenant_status", "tenant_id", "status"),
        Index("ix_catalog_item_category", "category_id"),
        Index("ix_catalog_item_vendor", "preferred_vendor_id"),
    )


class PreferredVendor(Base):
    """Fournisseur préféré pour catégories"""
    __tablename__ = "requisition_preferred_vendors"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    vendor_id = Column(UUID(), nullable=False)
    vendor_code = Column(String(50), nullable=False)
    vendor_name = Column(String(200), nullable=False)

    category_ids = Column(ARRAY(UUID()), default=list)

    contract_id = Column(UUID(), nullable=True)
    contract_end_date = Column(Date, nullable=True)

    discount_percentage = Column(Numeric(5, 2), default=Decimal("0"))
    payment_terms = Column(String(100), default="")
    lead_time_days = Column(Integer, default=0)
    minimum_order = Column(Numeric(15, 2), default=Decimal("0"))

    rating = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "vendor_id", name="uq_preferred_vendor_tenant_vendor"),
        Index("ix_preferred_vendor_tenant_active", "tenant_id", "is_active"),
        Index("ix_preferred_vendor_contract", "contract_id"),
    )


class BudgetAllocation(Base):
    """Allocation budgétaire pour demandes"""
    __tablename__ = "requisition_budget_allocations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    budget_id = Column(UUID(), nullable=False)
    budget_name = Column(String(200), nullable=False)

    department_id = Column(UUID(), nullable=False)
    department_name = Column(String(200), nullable=False)
    cost_center_id = Column(UUID(), nullable=True)

    fiscal_year = Column(Integer, nullable=False)

    total_amount = Column(Numeric(15, 2), default=Decimal("0"))
    committed_amount = Column(Numeric(15, 2), default=Decimal("0"))
    spent_amount = Column(Numeric(15, 2), default=Decimal("0"))
    available_amount = Column(Numeric(15, 2), default=Decimal("0"))

    category_allocations = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "budget_id", "department_id", "fiscal_year",
                        name="uq_budget_alloc_tenant_budget_dept_year"),
        Index("ix_budget_alloc_tenant_year", "tenant_id", "fiscal_year"),
        Index("ix_budget_alloc_department", "department_id"),
    )


class Requisition(Base):
    """Demande d'achat"""
    __tablename__ = "requisitions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    requisition_number = Column(String(50), nullable=False)
    requisition_type = Column(SQLEnum(RequisitionType), default=RequisitionType.GOODS, nullable=False)
    status = Column(SQLEnum(RequisitionStatus), default=RequisitionStatus.DRAFT, nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM, nullable=False)

    # Demandeur
    requester_id = Column(UUID(), nullable=False)
    requester_name = Column(String(200), nullable=False)
    requester_email = Column(String(200), default="")
    department_id = Column(UUID(), nullable=True)
    department_name = Column(String(200), default="")

    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    justification = Column(Text, default="")

    # Montants
    total_amount = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR")

    # Dates
    required_date = Column(Date, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Approbation
    current_approver_id = Column(UUID(), nullable=True)
    current_approver_name = Column(String(200), default="")

    # Budget
    budget_id = Column(UUID(), nullable=True)
    budget_name = Column(String(200), default="")
    budget_check_passed = Column(Boolean, default=True)
    budget_check_message = Column(Text, default="")

    # Commandes générées
    po_ids = Column(ARRAY(UUID()), default=list)

    # Métadonnées
    tags = Column(ARRAY(String), default=list)
    attachments = Column(JSONB, default=list)
    extra_data = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    lines = relationship("RequisitionLine", back_populates="requisition", lazy="dynamic",
                        cascade="all, delete-orphan")
    approval_steps = relationship("ApprovalStep", back_populates="requisition", lazy="dynamic",
                                  cascade="all, delete-orphan")
    comments = relationship("RequisitionComment", back_populates="requisition", lazy="dynamic",
                           cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "requisition_number", name="uq_requisition_tenant_number"),
        Index("ix_requisition_tenant_status", "tenant_id", "status"),
        Index("ix_requisition_requester", "requester_id"),
        Index("ix_requisition_department", "department_id"),
        Index("ix_requisition_approver", "current_approver_id"),
        Index("ix_requisition_dates", "tenant_id", "required_date"),
    )


class RequisitionLine(Base):
    """Ligne de demande d'achat"""
    __tablename__ = "requisition_lines"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    requisition_id = Column(UUID(), ForeignKey("requisitions.id"), nullable=False)
    line_number = Column(Integer, nullable=False)

    item_id = Column(UUID(), nullable=True)
    item_code = Column(String(50), default="")
    description = Column(Text, nullable=False)

    category_id = Column(UUID(), nullable=True)
    category_name = Column(String(200), default="")

    # Quantités
    quantity = Column(Numeric(15, 4), default=Decimal("1"))
    unit_of_measure = Column(String(20), default="EA")
    unit_price = Column(Numeric(15, 2), default=Decimal("0"))
    total_price = Column(Numeric(15, 2), default=Decimal("0"))
    currency = Column(String(3), default="EUR")

    # Fournisseur suggéré
    suggested_vendor_id = Column(UUID(), nullable=True)
    suggested_vendor_name = Column(String(200), default="")

    # Statut
    status = Column(SQLEnum(LineStatus), default=LineStatus.PENDING, nullable=False)

    # Commande
    po_id = Column(UUID(), nullable=True)
    po_number = Column(String(50), default="")
    po_line_id = Column(UUID(), nullable=True)
    ordered_quantity = Column(Numeric(15, 4), default=Decimal("0"))
    received_quantity = Column(Numeric(15, 4), default=Decimal("0"))

    # Budget
    budget_id = Column(UUID(), nullable=True)
    cost_center_id = Column(UUID(), nullable=True)
    gl_account = Column(String(50), default="")

    # Métadonnées
    specifications = Column(Text, default="")
    notes = Column(Text, default="")
    attachments = Column(JSONB, default=list)

    # Relationships
    requisition = relationship("Requisition", back_populates="lines")

    __table_args__ = (
        UniqueConstraint("requisition_id", "line_number", name="uq_req_line_req_number"),
        Index("ix_req_line_tenant", "tenant_id"),
        Index("ix_req_line_requisition", "requisition_id"),
        Index("ix_req_line_item", "item_id"),
        Index("ix_req_line_status", "status"),
    )


class ApprovalStep(Base):
    """Étape d'approbation"""
    __tablename__ = "requisition_approval_steps"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    requisition_id = Column(UUID(), ForeignKey("requisitions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)

    approver_id = Column(UUID(), nullable=False)
    approver_name = Column(String(200), nullable=False)

    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    comments = Column(Text, default="")
    decided_at = Column(DateTime, nullable=True)

    # Relationships
    requisition = relationship("Requisition", back_populates="approval_steps")

    __table_args__ = (
        UniqueConstraint("requisition_id", "step_number", name="uq_approval_step_req_number"),
        Index("ix_approval_step_tenant", "tenant_id"),
        Index("ix_approval_step_requisition", "requisition_id"),
        Index("ix_approval_step_approver", "approver_id"),
        Index("ix_approval_step_status", "status"),
    )


class RequisitionComment(Base):
    """Commentaire sur demande"""
    __tablename__ = "requisition_comments"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    requisition_id = Column(UUID(), ForeignKey("requisitions.id"), nullable=False)

    author_id = Column(UUID(), nullable=False)
    author_name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    is_internal = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    requisition = relationship("Requisition", back_populates="comments")

    __table_args__ = (
        Index("ix_req_comment_tenant", "tenant_id"),
        Index("ix_req_comment_requisition", "requisition_id"),
    )


class RequisitionTemplate(Base):
    """Modèle de demande réutilisable"""
    __tablename__ = "requisition_templates"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")

    requisition_type = Column(SQLEnum(RequisitionType), default=RequisitionType.GOODS, nullable=False)
    default_lines = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(), nullable=True)

    # Version
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_req_template_tenant_code"),
        Index("ix_req_template_tenant_active", "tenant_id", "is_active"),
    )
