"""
AZALS - Workflow & Approval Engine
==================================

Système de workflows d'approbation multi-niveau pour les opérations critiques.

Fonctionnalités:
- Définition de workflows avec étapes
- Approbations multi-niveau
- Escalade automatique
- Notifications
- Audit trail complet

Usage:
    from app.core.workflow import WorkflowEngine, WorkflowDefinition

    # Définir un workflow
    workflow = WorkflowDefinition(
        name="journal_entry_approval",
        steps=[
            ApprovalStep(role="accountant", action="validate"),
            ApprovalStep(role="finance_manager", action="approve", threshold=10000),
            ApprovalStep(role="cfo", action="approve", threshold=100000),
        ]
    )

    # Exécuter
    engine = WorkflowEngine(db, context)
    engine.submit(workflow, document_id, document_type)
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Session, relationship

from app.core.types import JSONB, UniversalUUID
from app.db import Base

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class WorkflowStatus(str, enum.Enum):
    """Statut d'un workflow."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ApprovalAction(str, enum.Enum):
    """Actions possibles sur une étape."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"
    REQUEST_INFO = "REQUEST_INFO"


class NotificationType(str, enum.Enum):
    """Types de notifications."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    REMINDER = "REMINDER"
    EXPIRED = "EXPIRED"


# =============================================================================
# MODELS
# =============================================================================

class WorkflowInstance(Base):
    """Instance d'un workflow en cours."""

    __tablename__ = "workflow_instances"

    id = Column(UniversalUUID, primary_key=True, default=uuid4)
    tenant_id = Column(UniversalUUID, nullable=False, index=True)

    # Identifiant du workflow
    workflow_name = Column(String(100), nullable=False)
    workflow_version = Column(Integer, default=1)

    # Document associé
    document_type = Column(String(100), nullable=False)
    document_id = Column(UniversalUUID, nullable=False)

    # Statut
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=1)

    # Métadonnées (extra_data car 'metadata' reserve SQLAlchemy)
    extra_data = Column(JSONB, default=dict)
    amount = Column(Integer, nullable=True)  # Pour seuils d'approbation

    # Initiateur
    initiated_by = Column(UniversalUUID, nullable=False)
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Dates
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Relations
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_tenant_doc", "tenant_id", "document_type", "document_id"),
        Index("ix_workflow_status", "tenant_id", "status"),
    )


class WorkflowStep(Base):
    """Étape d'un workflow."""

    __tablename__ = "workflow_steps"

    id = Column(UniversalUUID, primary_key=True, default=uuid4)
    workflow_id = Column(UniversalUUID, ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False)

    # Position dans le workflow
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)

    # Rôle requis
    required_role = Column(String(100), nullable=False)
    required_permission = Column(String(100), nullable=True)

    # Seuil (optionnel - pour approbations conditionnelles)
    threshold_amount = Column(Integer, nullable=True)
    threshold_condition = Column(String(20), nullable=True)  # >, <, >=, <=, ==

    # Statut
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    action_taken = Column(Enum(ApprovalAction), nullable=True)

    # Approbateur
    assigned_to = Column(UniversalUUID, nullable=True)
    approved_by = Column(UniversalUUID, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Commentaires
    comments = Column(Text, nullable=True)

    # Délais
    due_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    workflow = relationship("WorkflowInstance", back_populates="steps")

    __table_args__ = (
        Index("ix_step_workflow", "workflow_id", "step_number"),
        Index("ix_step_assigned", "assigned_to", "status"),
    )


class WorkflowNotification(Base):
    """Notifications de workflow."""

    __tablename__ = "workflow_notifications"

    id = Column(UniversalUUID, primary_key=True, default=uuid4)
    tenant_id = Column(UniversalUUID, nullable=False, index=True)

    workflow_id = Column(UniversalUUID, ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UniversalUUID, nullable=True)

    notification_type = Column(Enum(NotificationType), nullable=False)
    recipient_id = Column(UniversalUUID, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_notif_recipient_read", "recipient_id", "is_read"),
    )


# =============================================================================
# WORKFLOW DEFINITIONS
# =============================================================================

@dataclass
class ApprovalStep:
    """Définition d'une étape d'approbation."""
    name: str
    role: str
    action: str = "approve"
    permission: Optional[str] = None
    threshold: Optional[int] = None  # Montant minimum pour cette étape
    threshold_condition: str = ">="
    timeout_hours: int = 72
    auto_escalate: bool = True
    escalate_to_role: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Définition complète d'un workflow."""
    name: str
    description: str = ""
    steps: List[ApprovalStep] = field(default_factory=list)
    document_types: List[str] = field(default_factory=list)
    version: int = 1

    def get_applicable_steps(self, amount: Optional[int] = None) -> List[ApprovalStep]:
        """Retourne les étapes applicables selon le montant."""
        if amount is None:
            return self.steps

        applicable = []
        for step in self.steps:
            if step.threshold is None:
                applicable.append(step)
            elif step.threshold_condition == ">=" and amount >= step.threshold:
                applicable.append(step)
            elif step.threshold_condition == ">" and amount > step.threshold:
                applicable.append(step)
            elif step.threshold_condition == "<=" and amount <= step.threshold:
                applicable.append(step)
            elif step.threshold_condition == "<" and amount < step.threshold:
                applicable.append(step)
            elif step.threshold_condition == "==" and amount == step.threshold:
                applicable.append(step)

        return applicable


# =============================================================================
# WORKFLOW ENGINE
# =============================================================================

class WorkflowEngine:
    """Moteur d'exécution des workflows."""

    # Définitions de workflows prédéfinis
    PREDEFINED_WORKFLOWS: Dict[str, WorkflowDefinition] = {}

    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    @classmethod
    def register_workflow(cls, definition: WorkflowDefinition):
        """Enregistre une définition de workflow."""
        cls.PREDEFINED_WORKFLOWS[definition.name] = definition
        logger.info(f"Workflow registered: {definition.name}")

    def submit(
        self,
        workflow_name: str,
        document_type: str,
        document_id: UUID,
        amount: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowInstance:
        """Soumet un document pour approbation."""

        # Récupérer la définition
        definition = self.PREDEFINED_WORKFLOWS.get(workflow_name)
        if not definition:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        # Obtenir les étapes applicables
        applicable_steps = definition.get_applicable_steps(amount)
        if not applicable_steps:
            raise ValueError("No applicable steps for this workflow")

        # Créer l'instance
        instance = WorkflowInstance(
            tenant_id=self.tenant_id,
            workflow_name=workflow_name,
            workflow_version=definition.version,
            document_type=document_type,
            document_id=document_id,
            status=WorkflowStatus.PENDING,
            current_step=0,
            total_steps=len(applicable_steps),
            amount=amount,
            metadata=metadata or {},
            initiated_by=self.user_id,
            started_at=datetime.utcnow(),
        )
        self.db.add(instance)
        self.db.flush()

        # Créer les étapes
        for i, step_def in enumerate(applicable_steps):
            step = WorkflowStep(
                workflow_id=instance.id,
                step_number=i,
                step_name=step_def.name,
                required_role=step_def.role,
                required_permission=step_def.permission,
                threshold_amount=step_def.threshold,
                threshold_condition=step_def.threshold_condition,
                status=WorkflowStatus.PENDING if i == 0 else WorkflowStatus.DRAFT,
                due_at=datetime.utcnow() + timedelta(hours=step_def.timeout_hours) if i == 0 else None,
            )
            self.db.add(step)

        self.db.commit()

        logger.info(
            f"Workflow submitted: {workflow_name} for {document_type}/{document_id}",
            extra={"tenant_id": str(self.tenant_id), "workflow_id": str(instance.id)}
        )

        return instance

    def approve(
        self,
        workflow_id: UUID,
        step_number: int,
        comments: Optional[str] = None,
    ) -> WorkflowInstance:
        """Approuve une étape du workflow."""
        return self._process_action(workflow_id, step_number, ApprovalAction.APPROVE, comments)

    def reject(
        self,
        workflow_id: UUID,
        step_number: int,
        comments: Optional[str] = None,
    ) -> WorkflowInstance:
        """Rejette une étape du workflow."""
        return self._process_action(workflow_id, step_number, ApprovalAction.REJECT, comments)

    def _process_action(
        self,
        workflow_id: UUID,
        step_number: int,
        action: ApprovalAction,
        comments: Optional[str] = None,
    ) -> WorkflowInstance:
        """Traite une action sur une étape."""

        # Récupérer le workflow
        instance = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.id == workflow_id,
            WorkflowInstance.tenant_id == self.tenant_id,
        ).first()

        if not instance:
            raise ValueError("Workflow not found")

        if instance.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
            raise ValueError(f"Workflow is not active: {instance.status}")

        # Récupérer l'étape courante
        step = self.db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.step_number == step_number,
        ).first()

        if not step:
            raise ValueError(f"Step {step_number} not found")

        if step.status != WorkflowStatus.PENDING:
            raise ValueError(f"Step is not pending: {step.status}")

        # Mettre à jour l'étape
        step.action_taken = action
        step.approved_by = self.user_id
        step.approved_at = datetime.utcnow()
        step.comments = comments

        if action == ApprovalAction.APPROVE:
            step.status = WorkflowStatus.APPROVED

            # Vérifier s'il reste des étapes
            next_step_number = step_number + 1
            if next_step_number < instance.total_steps:
                # Activer l'étape suivante
                next_step = self.db.query(WorkflowStep).filter(
                    WorkflowStep.workflow_id == workflow_id,
                    WorkflowStep.step_number == next_step_number,
                ).first()
                if next_step:
                    next_step.status = WorkflowStatus.PENDING
                    # Récupérer le timeout depuis la définition
                    definition = self.PREDEFINED_WORKFLOWS.get(instance.workflow_name)
                    if definition and len(definition.steps) > next_step_number:
                        timeout = definition.steps[next_step_number].timeout_hours
                        next_step.due_at = datetime.utcnow() + timedelta(hours=timeout)

                instance.current_step = next_step_number
                instance.status = WorkflowStatus.IN_PROGRESS
            else:
                # Workflow terminé avec succès
                instance.status = WorkflowStatus.APPROVED
                instance.completed_at = datetime.utcnow()
                logger.info(f"Workflow approved: {workflow_id}")

        elif action == ApprovalAction.REJECT:
            step.status = WorkflowStatus.REJECTED
            instance.status = WorkflowStatus.REJECTED
            instance.completed_at = datetime.utcnow()
            logger.info(f"Workflow rejected: {workflow_id}")

        self.db.commit()
        return instance

    def get_pending_approvals(self, role: Optional[str] = None) -> List[WorkflowStep]:
        """Récupère les approbations en attente."""
        query = self.db.query(WorkflowStep).join(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id,
            WorkflowStep.status == WorkflowStatus.PENDING,
        )

        if role:
            query = query.filter(WorkflowStep.required_role == role)

        return query.order_by(WorkflowStep.due_at).all()

    def get_workflow_status(self, document_type: str, document_id: UUID) -> Optional[WorkflowInstance]:
        """Récupère le statut du workflow pour un document."""
        return self.db.query(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id,
            WorkflowInstance.document_type == document_type,
            WorkflowInstance.document_id == document_id,
        ).order_by(WorkflowInstance.initiated_at.desc()).first()


# =============================================================================
# WORKFLOWS PRÉDÉFINIS FINANCE
# =============================================================================

# Workflow approbation écriture comptable
JOURNAL_ENTRY_WORKFLOW = WorkflowDefinition(
    name="journal_entry_approval",
    description="Workflow d'approbation des écritures comptables",
    document_types=["journal_entry"],
    steps=[
        ApprovalStep(
            name="validation_comptable",
            role="accountant",
            action="validate",
            permission="accounting.entry.validate",
            timeout_hours=48,
        ),
        ApprovalStep(
            name="approbation_responsable",
            role="finance_manager",
            action="approve",
            permission="accounting.entry.approve",
            threshold=10000,  # > 10,000
            timeout_hours=72,
            auto_escalate=True,
            escalate_to_role="cfo",
        ),
        ApprovalStep(
            name="approbation_direction",
            role="cfo",
            action="approve",
            permission="accounting.entry.approve_high",
            threshold=100000,  # > 100,000
            timeout_hours=96,
        ),
    ],
)

# Workflow approbation paiement
PAYMENT_WORKFLOW = WorkflowDefinition(
    name="payment_approval",
    description="Workflow d'approbation des paiements",
    document_types=["payment", "bank_transfer"],
    steps=[
        ApprovalStep(
            name="verification_tresorier",
            role="treasurer",
            action="validate",
            permission="treasury.payment.validate",
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_finance",
            role="finance_manager",
            action="approve",
            permission="treasury.payment.approve",
            threshold=5000,
            timeout_hours=48,
        ),
        ApprovalStep(
            name="approbation_direction",
            role="cfo",
            action="approve",
            permission="treasury.payment.approve_high",
            threshold=50000,
            timeout_hours=72,
        ),
    ],
)

# Workflow clôture période
PERIOD_CLOSE_WORKFLOW = WorkflowDefinition(
    name="period_close_approval",
    description="Workflow de clôture de période comptable",
    document_types=["fiscal_period", "fiscal_year"],
    steps=[
        ApprovalStep(
            name="preparation_cloture",
            role="accountant",
            action="prepare",
            permission="accounting.period.prepare",
            timeout_hours=168,  # 1 semaine
        ),
        ApprovalStep(
            name="validation_cloture",
            role="finance_manager",
            action="validate",
            permission="accounting.period.validate",
            timeout_hours=72,
        ),
        ApprovalStep(
            name="approbation_cloture",
            role="cfo",
            action="approve",
            permission="accounting.period.close",
            timeout_hours=48,
        ),
    ],
)

# =============================================================================
# WORKFLOWS DOCUMENTS COMMERCIAUX
# =============================================================================

# Workflow approbation devis
QUOTE_WORKFLOW = WorkflowDefinition(
    name="quote_approval",
    description="Workflow d'approbation des devis",
    document_types=["quote", "estimate"],
    steps=[
        ApprovalStep(
            name="verification_commerciale",
            role="sales_rep",
            action="validate",
            permission="commercial.quote.validate",
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_responsable",
            role="sales_manager",
            action="approve",
            permission="commercial.quote.approve",
            threshold=10000,
            timeout_hours=48,
            auto_escalate=True,
            escalate_to_role="commercial_director",
        ),
        ApprovalStep(
            name="approbation_direction",
            role="commercial_director",
            action="approve",
            permission="commercial.quote.approve_high",
            threshold=50000,
            timeout_hours=72,
        ),
    ],
)

# Workflow approbation facture client
INVOICE_WORKFLOW = WorkflowDefinition(
    name="invoice_approval",
    description="Workflow d'approbation des factures clients",
    document_types=["invoice", "credit_note"],
    steps=[
        ApprovalStep(
            name="verification_comptable",
            role="accountant",
            action="validate",
            permission="invoicing.invoice.validate",
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_finance",
            role="finance_manager",
            action="approve",
            permission="invoicing.invoice.approve",
            threshold=25000,
            timeout_hours=48,
        ),
    ],
)

# Workflow approbation commande client
SALES_ORDER_WORKFLOW = WorkflowDefinition(
    name="sales_order_approval",
    description="Workflow d'approbation des commandes clients",
    document_types=["sales_order"],
    steps=[
        ApprovalStep(
            name="verification_stock",
            role="warehouse_manager",
            action="validate",
            permission="sales.order.validate_stock",
            timeout_hours=12,
        ),
        ApprovalStep(
            name="verification_credit",
            role="credit_manager",
            action="validate",
            permission="sales.order.validate_credit",
            threshold=5000,
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_commerciale",
            role="sales_manager",
            action="approve",
            permission="sales.order.approve",
            threshold=20000,
            timeout_hours=48,
        ),
    ],
)


# =============================================================================
# WORKFLOWS ACHATS
# =============================================================================

# Workflow demande d'achat
PURCHASE_REQUEST_WORKFLOW = WorkflowDefinition(
    name="purchase_request_approval",
    description="Workflow d'approbation des demandes d'achat",
    document_types=["purchase_request", "requisition"],
    steps=[
        ApprovalStep(
            name="validation_responsable",
            role="department_manager",
            action="validate",
            permission="purchase.request.validate",
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_achats",
            role="purchase_manager",
            action="approve",
            permission="purchase.request.approve",
            threshold=5000,
            timeout_hours=48,
        ),
        ApprovalStep(
            name="approbation_direction",
            role="cfo",
            action="approve",
            permission="purchase.request.approve_high",
            threshold=25000,
            timeout_hours=72,
        ),
    ],
)

# Workflow commande fournisseur
PURCHASE_ORDER_WORKFLOW = WorkflowDefinition(
    name="purchase_order_approval",
    description="Workflow d'approbation des commandes fournisseurs",
    document_types=["purchase_order"],
    steps=[
        ApprovalStep(
            name="verification_budget",
            role="budget_controller",
            action="validate",
            permission="purchase.order.validate_budget",
            timeout_hours=24,
        ),
        ApprovalStep(
            name="approbation_achats",
            role="purchase_manager",
            action="approve",
            permission="purchase.order.approve",
            threshold=10000,
            timeout_hours=48,
        ),
        ApprovalStep(
            name="approbation_finance",
            role="finance_manager",
            action="approve",
            permission="purchase.order.approve_finance",
            threshold=50000,
            timeout_hours=72,
        ),
        ApprovalStep(
            name="approbation_direction",
            role="cfo",
            action="approve",
            permission="purchase.order.approve_high",
            threshold=100000,
            timeout_hours=96,
        ),
    ],
)

# Workflow facture fournisseur
SUPPLIER_INVOICE_WORKFLOW = WorkflowDefinition(
    name="supplier_invoice_approval",
    description="Workflow d'approbation des factures fournisseurs",
    document_types=["supplier_invoice", "purchase_invoice"],
    steps=[
        ApprovalStep(
            name="rapprochement_commande",
            role="accountant",
            action="validate",
            permission="purchase.invoice.validate",
            timeout_hours=48,
        ),
        ApprovalStep(
            name="approbation_paiement",
            role="finance_manager",
            action="approve",
            permission="purchase.invoice.approve",
            threshold=10000,
            timeout_hours=72,
        ),
    ],
)


# =============================================================================
# MODELE DELEGATION APPROBATION
# =============================================================================

class ApprovalDelegation(Base):
    """Délégation de pouvoir d'approbation."""

    __tablename__ = "workflow_delegations"

    id = Column(UniversalUUID, primary_key=True, default=uuid4)
    tenant_id = Column(UniversalUUID, nullable=False, index=True)

    # Délégant
    delegator_id = Column(UniversalUUID, nullable=False)
    delegator_role = Column(String(100), nullable=False)

    # Délégataire
    delegate_id = Column(UniversalUUID, nullable=False)
    delegate_role = Column(String(100), nullable=True)

    # Périmètre
    workflow_names = Column(JSONB, default=list)  # [] = tous les workflows
    document_types = Column(JSONB, default=list)  # [] = tous les documents
    max_amount = Column(Integer, nullable=True)  # Plafond montant

    # Validité
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)  # Ex: "Congés du 01/03 au 15/03"

    # Statut
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(UniversalUUID, nullable=True)
    revoke_reason = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UniversalUUID, nullable=False)

    __table_args__ = (
        Index("ix_delegation_delegator", "tenant_id", "delegator_id"),
        Index("ix_delegation_delegate", "tenant_id", "delegate_id"),
        Index("ix_delegation_active", "tenant_id", "is_active", "valid_from", "valid_until"),
    )


# =============================================================================
# ANALYTICS APPROBATION
# =============================================================================

@dataclass
class ApprovalAnalytics:
    """Statistiques d'approbation."""
    total_workflows: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    expired_count: int = 0

    approval_rate: float = 0.0
    rejection_rate: float = 0.0

    avg_approval_time_hours: float = 0.0
    avg_steps_to_approval: float = 0.0

    by_workflow: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_approver: Dict[str, int] = field(default_factory=dict)


class WorkflowAnalyticsService:
    """Service d'analytics pour les workflows."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        workflow_name: Optional[str] = None,
    ) -> ApprovalAnalytics:
        """Calcule les statistiques d'approbation."""
        from sqlalchemy import case, extract

        query = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id
        )

        if start_date:
            query = query.filter(WorkflowInstance.initiated_at >= start_date)
        if end_date:
            query = query.filter(WorkflowInstance.initiated_at <= end_date)
        if workflow_name:
            query = query.filter(WorkflowInstance.workflow_name == workflow_name)

        instances = query.all()

        analytics = ApprovalAnalytics()
        analytics.total_workflows = len(instances)

        total_time_hours = 0.0
        total_steps = 0
        completed_count = 0

        for inst in instances:
            if inst.status == WorkflowStatus.APPROVED:
                analytics.approved_count += 1
                if inst.completed_at and inst.started_at:
                    delta = (inst.completed_at - inst.started_at).total_seconds() / 3600
                    total_time_hours += delta
                    total_steps += inst.current_step + 1
                    completed_count += 1
            elif inst.status == WorkflowStatus.REJECTED:
                analytics.rejected_count += 1
            elif inst.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
                analytics.pending_count += 1
            elif inst.status == WorkflowStatus.EXPIRED:
                analytics.expired_count += 1

            # Stats par workflow
            wf_name = inst.workflow_name
            if wf_name not in analytics.by_workflow:
                analytics.by_workflow[wf_name] = {"approved": 0, "rejected": 0, "pending": 0}
            if inst.status == WorkflowStatus.APPROVED:
                analytics.by_workflow[wf_name]["approved"] += 1
            elif inst.status == WorkflowStatus.REJECTED:
                analytics.by_workflow[wf_name]["rejected"] += 1
            else:
                analytics.by_workflow[wf_name]["pending"] += 1

        # Calcul des taux
        if analytics.total_workflows > 0:
            analytics.approval_rate = analytics.approved_count / analytics.total_workflows * 100
            analytics.rejection_rate = analytics.rejected_count / analytics.total_workflows * 100

        if completed_count > 0:
            analytics.avg_approval_time_hours = total_time_hours / completed_count
            analytics.avg_steps_to_approval = total_steps / completed_count

        # Stats par approbateur
        steps = self.db.query(WorkflowStep).join(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id,
            WorkflowStep.approved_by.isnot(None),
        ).all()

        for step in steps:
            approver_id = str(step.approved_by)
            analytics.by_approver[approver_id] = analytics.by_approver.get(approver_id, 0) + 1

        return analytics


# =============================================================================
# SERVICE ESCALADE AUTOMATIQUE
# =============================================================================

class EscalationService:
    """Service de gestion des escalades automatiques."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def check_and_escalate(self) -> List[WorkflowStep]:
        """Vérifie et escalade les étapes expirées."""
        now = datetime.utcnow()

        # Trouver les étapes en attente dépassées
        overdue_steps = self.db.query(WorkflowStep).join(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id,
            WorkflowStep.status == WorkflowStatus.PENDING,
            WorkflowStep.due_at < now,
            WorkflowStep.escalated == False,
        ).all()

        escalated = []

        for step in overdue_steps:
            # Récupérer la définition du workflow
            instance = step.workflow
            definition = WorkflowEngine.PREDEFINED_WORKFLOWS.get(instance.workflow_name)

            if not definition or step.step_number >= len(definition.steps):
                continue

            step_def = definition.steps[step.step_number]

            if step_def.auto_escalate and step_def.escalate_to_role:
                # Marquer comme escaladé
                step.escalated = True
                step.required_role = step_def.escalate_to_role
                step.due_at = now + timedelta(hours=step_def.timeout_hours)

                # Créer notification d'escalade
                notif = WorkflowNotification(
                    tenant_id=self.tenant_id,
                    workflow_id=instance.id,
                    step_id=step.id,
                    notification_type=NotificationType.ESCALATED,
                    recipient_id=step.assigned_to or instance.initiated_by,
                    title=f"Workflow escaladé: {step.step_name}",
                    message=f"L'étape '{step.step_name}' a été escaladée vers {step_def.escalate_to_role}",
                    link=f"/workflows/{instance.id}",
                )
                self.db.add(notif)

                escalated.append(step)
                logger.warning(
                    f"Workflow step escalated: {instance.id}/{step.step_number} -> {step_def.escalate_to_role}"
                )

        if escalated:
            self.db.commit()

        return escalated

    def send_reminders(self, hours_before_due: int = 24) -> List[WorkflowNotification]:
        """Envoie des rappels pour les étapes bientôt expirées."""
        reminder_threshold = datetime.utcnow() + timedelta(hours=hours_before_due)

        pending_steps = self.db.query(WorkflowStep).join(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id,
            WorkflowStep.status == WorkflowStatus.PENDING,
            WorkflowStep.due_at <= reminder_threshold,
            WorkflowStep.due_at > datetime.utcnow(),
            WorkflowStep.reminder_sent == False,
        ).all()

        notifications = []

        for step in pending_steps:
            instance = step.workflow

            notif = WorkflowNotification(
                tenant_id=self.tenant_id,
                workflow_id=instance.id,
                step_id=step.id,
                notification_type=NotificationType.REMINDER,
                recipient_id=step.assigned_to or instance.initiated_by,
                title=f"Rappel: Approbation en attente",
                message=f"L'étape '{step.step_name}' expire bientôt ({step.due_at})",
                link=f"/workflows/{instance.id}",
            )
            self.db.add(notif)
            step.reminder_sent = True
            notifications.append(notif)

        if notifications:
            self.db.commit()

        return notifications


# Enregistrer les workflows
WorkflowEngine.register_workflow(JOURNAL_ENTRY_WORKFLOW)
WorkflowEngine.register_workflow(PAYMENT_WORKFLOW)
WorkflowEngine.register_workflow(PERIOD_CLOSE_WORKFLOW)
WorkflowEngine.register_workflow(QUOTE_WORKFLOW)
WorkflowEngine.register_workflow(INVOICE_WORKFLOW)
WorkflowEngine.register_workflow(SALES_ORDER_WORKFLOW)
WorkflowEngine.register_workflow(PURCHASE_REQUEST_WORKFLOW)
WorkflowEngine.register_workflow(PURCHASE_ORDER_WORKFLOW)
WorkflowEngine.register_workflow(SUPPLIER_INVOICE_WORKFLOW)
