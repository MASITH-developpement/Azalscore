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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from app.core.types import UniversalUUID
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

    # Métadonnées
    metadata = Column(JSONB, default=dict)
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

# Enregistrer les workflows
WorkflowEngine.register_workflow(JOURNAL_ENTRY_WORKFLOW)
WorkflowEngine.register_workflow(PAYMENT_WORKFLOW)
WorkflowEngine.register_workflow(PERIOD_CLOSE_WORKFLOW)
