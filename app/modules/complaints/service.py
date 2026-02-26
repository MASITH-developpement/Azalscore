"""
AZALS MODULE - Complaints Service
==================================

Service metier pour la gestion des reclamations clients.
Orchestre les repositories et implemente la logique metier.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from .exceptions import (
    AgentNotAvailableError,
    AgentNotFoundError,
    ApprovalRequiredError,
    CategoryNotFoundError,
    CompensationLimitExceededError,
    ComplaintAlreadyClosedError,
    ComplaintNotFoundError,
    ComplaintNotResolvedError,
    CustomerInfoRequiredError,
    DuplicateCodeError,
    InsufficientPermissionError,
    InvalidEscalationLevelError,
    InvalidStatusTransitionError,
    SLAPolicyNotFoundError,
    TeamNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateVariableError,
)
from .models import (
    Complaint,
    ComplaintAction,
    ComplaintAgent,
    ComplaintAttachment,
    ComplaintAutomationRule,
    ComplaintCategory,
    ComplaintCategoryConfig,
    ComplaintChannel,
    ComplaintEscalation,
    ComplaintExchange,
    ComplaintHistory,
    ComplaintMetrics,
    ComplaintPriority,
    ComplaintSLAPolicy,
    ComplaintStatus,
    ComplaintTeam,
    ComplaintTemplate,
    EscalationLevel,
    ResolutionType,
    RootCauseCategory,
    SatisfactionRating,
)
from .repository import (
    ActionRepository,
    AgentRepository,
    AttachmentRepository,
    AutomationRuleRepository,
    CategoryConfigRepository,
    ComplaintRepository,
    EscalationRepository,
    ExchangeRepository,
    HistoryRepository,
    MetricsRepository,
    SLAPolicyRepository,
    TeamRepository,
    TemplateRepository,
)
from .schemas import (
    ActionComplete,
    ActionCreate,
    ActionUpdate,
    AgentCreate,
    AgentUpdate,
    AutomationRuleCreate,
    AutomationRuleUpdate,
    CategoryConfigCreate,
    CategoryConfigUpdate,
    ComplaintAssign,
    ComplaintClose,
    ComplaintCreate,
    ComplaintDashboard,
    ComplaintEscalate,
    ComplaintFilter,
    ComplaintReopen,
    ComplaintResolve,
    ComplaintStats,
    ComplaintStatusChange,
    ComplaintUpdate,
    ExchangeCreate,
    AttachmentCreate,
    SatisfactionSubmit,
    SLAPolicyCreate,
    SLAPolicyUpdate,
    TeamCreate,
    TeamUpdate,
    TemplateCreate,
    TemplateRender,
    TemplateUpdate,
)

logger = logging.getLogger(__name__)


# Transitions de statut valides
VALID_STATUS_TRANSITIONS = {
    ComplaintStatus.DRAFT: [ComplaintStatus.NEW],
    ComplaintStatus.NEW: [
        ComplaintStatus.ACKNOWLEDGED,
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.CANCELLED
    ],
    ComplaintStatus.ACKNOWLEDGED: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.PENDING_INFO,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.CANCELLED
    ],
    ComplaintStatus.IN_PROGRESS: [
        ComplaintStatus.PENDING_INFO,
        ComplaintStatus.PENDING_CUSTOMER,
        ComplaintStatus.UNDER_INVESTIGATION,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.PENDING_APPROVAL,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CANCELLED
    ],
    ComplaintStatus.PENDING_INFO: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.CANCELLED
    ],
    ComplaintStatus.PENDING_CUSTOMER: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CANCELLED
    ],
    ComplaintStatus.UNDER_INVESTIGATION: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.PENDING_APPROVAL,
        ComplaintStatus.RESOLVED
    ],
    ComplaintStatus.ESCALATED: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.PENDING_APPROVAL,
        ComplaintStatus.RESOLVED
    ],
    ComplaintStatus.PENDING_APPROVAL: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.RESOLVED
    ],
    ComplaintStatus.RESOLVED: [
        ComplaintStatus.CLOSED,
        ComplaintStatus.REOPENED
    ],
    ComplaintStatus.CLOSED: [ComplaintStatus.REOPENED],
    ComplaintStatus.REOPENED: [
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.ESCALATED,
        ComplaintStatus.RESOLVED
    ],
    ComplaintStatus.CANCELLED: []
}


class ComplaintService:
    """
    Service de gestion des reclamations.

    Gere:
    - Creation et mise a jour des reclamations
    - Workflow de traitement
    - SLA et escalade
    - Resolution et compensation
    - Satisfaction client
    - Reporting et KPI
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.complaints = ComplaintRepository(db, tenant_id)
        self.teams = TeamRepository(db, tenant_id)
        self.agents = AgentRepository(db, tenant_id)
        self.categories = CategoryConfigRepository(db, tenant_id)
        self.sla_policies = SLAPolicyRepository(db, tenant_id)
        self.exchanges = ExchangeRepository(db, tenant_id)
        self.attachments = AttachmentRepository(db, tenant_id)
        self.actions = ActionRepository(db, tenant_id)
        self.escalations = EscalationRepository(db, tenant_id)
        self.history = HistoryRepository(db, tenant_id)
        self.templates = TemplateRepository(db, tenant_id)
        self.automation_rules = AutomationRuleRepository(db, tenant_id)
        self.metrics = MetricsRepository(db, tenant_id)

    # ========================================================================
    # COMPLAINTS - CRUD
    # ========================================================================

    def create_complaint(
        self,
        data: ComplaintCreate,
        created_by: UUID | None = None,
        created_by_name: str | None = None
    ) -> Complaint:
        """Cree une nouvelle reclamation."""
        # Validation client
        if not data.customer_email and not data.customer_name:
            raise CustomerInfoRequiredError()

        # Generer la reference
        reference = self.complaints.generate_reference()

        # Determiner la politique SLA
        sla_policy = None
        if data.sla_policy_id:
            sla_policy = self.sla_policies.get_by_id(data.sla_policy_id)
        elif data.category_config_id:
            cat_config = self.categories.get_by_id(data.category_config_id)
            if cat_config and cat_config.sla_policy_id:
                sla_policy = self.sla_policies.get_by_id(cat_config.sla_policy_id)

        if not sla_policy:
            sla_policy = self.sla_policies.get_default()

        # Auto-prioritisation
        priority = data.priority
        if not priority or priority == ComplaintPriority.MEDIUM:
            priority = self._auto_prioritize(data)

        # Creer la reclamation
        complaint = Complaint(
            tenant_id=self.tenant_id,
            reference=reference,
            subject=data.subject,
            description=data.description,
            category=data.category,
            category_config_id=data.category_config_id,
            priority=priority,
            channel=data.channel,
            original_message_id=data.original_message_id,
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            customer_company=data.customer_company,
            customer_account_number=data.customer_account_number,
            order_id=data.order_id,
            order_reference=data.order_reference,
            invoice_id=data.invoice_id,
            invoice_reference=data.invoice_reference,
            product_id=data.product_id,
            product_reference=data.product_reference,
            product_name=data.product_name,
            contract_id=data.contract_id,
            disputed_amount=data.disputed_amount,
            currency=data.currency,
            team_id=data.team_id,
            assigned_to_id=data.assigned_to_id,
            sla_policy_id=sla_policy.id if sla_policy else None,
            tags=data.tags,
            custom_fields=data.custom_fields,
            source_system=data.source_system,
            created_by=created_by,
            status=ComplaintStatus.NEW
        )

        # Calculer les echeances SLA
        if sla_policy:
            complaint = self._calculate_sla_deadlines(complaint, sla_policy)

        # Analyser le sentiment
        complaint.sentiment = self._analyze_sentiment(data.description)

        # Sauvegarder
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="created",
            actor_type="user",
            actor_id=created_by,
            actor_name=created_by_name
        )

        # Auto-assignation
        if not complaint.assigned_to_id and data.team_id:
            self._auto_assign(complaint)

        # Executer les automatisations
        self._execute_automations("complaint_created", complaint)

        logger.info(
            "complaint_created",
            extra={
                "complaint_id": str(complaint.id),
                "reference": complaint.reference,
                "tenant_id": self.tenant_id
            }
        )

        return complaint

    def get_complaint(self, complaint_id: UUID) -> Complaint:
        """Recupere une reclamation par ID."""
        complaint = self.complaints.get_by_id(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(complaint_id=str(complaint_id))
        return complaint

    def get_complaint_by_reference(self, reference: str) -> Complaint:
        """Recupere une reclamation par reference."""
        complaint = self.complaints.get_by_reference(reference)
        if not complaint:
            raise ComplaintNotFoundError(reference=reference)
        return complaint

    def get_complaint_detail(self, complaint_id: UUID) -> Complaint:
        """Recupere une reclamation avec toutes ses relations."""
        complaint = self.complaints.get_with_details(complaint_id)
        if not complaint:
            raise ComplaintNotFoundError(complaint_id=str(complaint_id))
        return complaint

    def update_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintUpdate,
        updated_by: UUID | None = None,
        updated_by_name: str | None = None
    ) -> Complaint:
        """Met a jour une reclamation."""
        complaint = self.get_complaint(complaint_id)

        # Verifier si cloturee
        if complaint.status == ComplaintStatus.CLOSED:
            raise ComplaintAlreadyClosedError(str(complaint_id), complaint.reference)

        # Mise a jour des champs
        update_data = data.model_dump(exclude_unset=True)
        changes = []

        for field, value in update_data.items():
            if hasattr(complaint, field):
                old_value = getattr(complaint, field)
                if old_value != value:
                    setattr(complaint, field, value)
                    changes.append((field, str(old_value), str(value)))

        if changes:
            complaint.updated_at = datetime.utcnow()
            complaint.updated_by = updated_by
            complaint.version += 1

            self.db.commit()
            self.db.refresh(complaint)

            # Historique
            for field, old_val, new_val in changes:
                self.history.add_entry(
                    complaint_id=complaint.id,
                    action="updated",
                    field_name=field,
                    old_value=old_val,
                    new_value=new_val,
                    actor_type="user",
                    actor_id=updated_by,
                    actor_name=updated_by_name
                )

            # Automatisations
            self._execute_automations("complaint_updated", complaint)

        return complaint

    def search_complaints(
        self,
        filters: ComplaintFilter,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Complaint], int]:
        """Recherche des reclamations."""
        return self.complaints.search(
            query=filters.query,
            status=filters.status,
            priority=filters.priority,
            category=filters.category,
            channel=filters.channel,
            team_id=filters.team_id,
            assigned_to_id=filters.assigned_to_id,
            customer_id=filters.customer_id,
            customer_email=filters.customer_email,
            order_id=filters.order_id,
            sla_breached=filters.sla_breached,
            sla_at_risk=filters.sla_at_risk,
            escalated=filters.escalated,
            has_compensation=filters.has_compensation,
            date_from=filters.date_from,
            date_to=filters.date_to,
            tags=filters.tags,
            skip=skip,
            limit=limit
        )

    def delete_complaint(
        self,
        complaint_id: UUID,
        deleted_by: UUID | None = None,
        deleted_by_name: str | None = None
    ) -> bool:
        """Supprime (soft delete) une reclamation."""
        complaint = self.get_complaint(complaint_id)

        complaint.is_deleted = True
        complaint.deleted_at = datetime.utcnow()
        complaint.deleted_by = deleted_by

        self.db.commit()

        self.history.add_entry(
            complaint_id=complaint.id,
            action="deleted",
            actor_type="user",
            actor_id=deleted_by,
            actor_name=deleted_by_name
        )

        return True

    # ========================================================================
    # WORKFLOW
    # ========================================================================

    def acknowledge_complaint(
        self,
        complaint_id: UUID,
        acknowledged_by: UUID | None = None,
        acknowledged_by_name: str | None = None,
        send_notification: bool = True
    ) -> Complaint:
        """Accuse reception de la reclamation."""
        complaint = self.get_complaint(complaint_id)

        if complaint.status not in [ComplaintStatus.NEW, ComplaintStatus.DRAFT]:
            raise InvalidStatusTransitionError(
                complaint.status.value,
                ComplaintStatus.ACKNOWLEDGED.value,
                str(complaint_id)
            )

        old_status = complaint.status
        complaint.status = ComplaintStatus.ACKNOWLEDGED
        complaint.acknowledged_at = datetime.utcnow()
        complaint.updated_at = datetime.utcnow()

        # Verifier SLA accuse reception
        if complaint.acknowledgment_due:
            complaint.acknowledgment_breached = datetime.utcnow() > complaint.acknowledgment_due

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="acknowledged",
            field_name="status",
            old_value=old_status.value,
            new_value=ComplaintStatus.ACKNOWLEDGED.value,
            actor_type="user",
            actor_id=acknowledged_by,
            actor_name=acknowledged_by_name
        )

        return complaint

    def assign_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintAssign,
        assigned_by: UUID | None = None,
        assigned_by_name: str | None = None
    ) -> Complaint:
        """Assigne une reclamation a un agent."""
        complaint = self.get_complaint(complaint_id)
        agent = self.agents.get_by_id(data.agent_id)

        if not agent:
            raise AgentNotFoundError(str(data.agent_id))

        if not agent.is_active or not agent.is_available:
            raise AgentNotAvailableError(str(data.agent_id))

        # Verifier la charge
        team = None
        if data.team_id:
            team = self.teams.get_by_id(data.team_id)
        elif agent.team_id:
            team = self.teams.get_by_id(agent.team_id)

        if team and agent.current_load >= team.max_complaints_per_agent:
            raise AgentNotAvailableError(
                str(data.agent_id),
                f"charge maximale atteinte ({agent.current_load}/{team.max_complaints_per_agent})"
            )

        # Mise a jour
        old_agent_id = complaint.assigned_to_id
        old_team_id = complaint.team_id

        complaint.assigned_to_id = data.agent_id
        complaint.assigned_at = datetime.utcnow()
        if data.team_id:
            complaint.team_id = data.team_id
        elif team:
            complaint.team_id = team.id

        if complaint.status == ComplaintStatus.NEW:
            complaint.status = ComplaintStatus.IN_PROGRESS
        elif complaint.status == ComplaintStatus.ACKNOWLEDGED:
            complaint.status = ComplaintStatus.IN_PROGRESS

        complaint.updated_at = datetime.utcnow()

        # Mettre a jour les charges des agents
        if old_agent_id:
            self.agents.update_load(old_agent_id, -1)
        self.agents.update_load(data.agent_id, 1)

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="assigned",
            field_name="assigned_to_id",
            old_value=str(old_agent_id) if old_agent_id else None,
            new_value=str(data.agent_id),
            actor_type="user",
            actor_id=assigned_by,
            actor_name=assigned_by_name,
            context={"note": data.note} if data.note else None
        )

        return complaint

    def change_status(
        self,
        complaint_id: UUID,
        data: ComplaintStatusChange,
        changed_by: UUID | None = None,
        changed_by_name: str | None = None
    ) -> Complaint:
        """Change le statut d'une reclamation."""
        complaint = self.get_complaint(complaint_id)

        # Verifier la transition
        valid_transitions = VALID_STATUS_TRANSITIONS.get(complaint.status, [])
        if data.status not in valid_transitions:
            raise InvalidStatusTransitionError(
                complaint.status.value,
                data.status.value,
                str(complaint_id)
            )

        old_status = complaint.status
        complaint.status = data.status
        complaint.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="status_changed",
            field_name="status",
            old_value=old_status.value,
            new_value=data.status.value,
            actor_type="user",
            actor_id=changed_by,
            actor_name=changed_by_name,
            context={"comment": data.comment} if data.comment else None
        )

        # Automatisations
        self._execute_automations("status_changed", complaint, {
            "old_status": old_status.value,
            "new_status": data.status.value
        })

        return complaint

    def escalate_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintEscalate,
        escalated_by: UUID | None = None,
        escalated_by_name: str | None = None,
        is_automatic: bool = False
    ) -> Complaint:
        """Escalade une reclamation."""
        complaint = self.get_complaint(complaint_id)

        # Verifier le niveau d'escalade
        current_level_order = self._get_escalation_order(complaint.current_escalation_level)
        target_level_order = self._get_escalation_order(data.to_level)

        if target_level_order <= current_level_order:
            raise InvalidEscalationLevelError(
                complaint.current_escalation_level.value,
                data.to_level.value
            )

        # Creer l'escalade
        escalation = ComplaintEscalation(
            tenant_id=self.tenant_id,
            complaint_id=complaint.id,
            from_level=complaint.current_escalation_level,
            to_level=data.to_level,
            reason=data.reason,
            is_automatic=is_automatic,
            escalated_by_id=escalated_by,
            escalated_by_name=escalated_by_name,
            assigned_to_id=data.assign_to_id
        )

        self.db.add(escalation)

        # Mettre a jour la reclamation
        complaint.current_escalation_level = data.to_level
        complaint.escalated_at = datetime.utcnow()
        complaint.escalation_count += 1
        complaint.status = ComplaintStatus.ESCALATED
        complaint.updated_at = datetime.utcnow()

        # Augmenter la priorite si niveau 3+
        if target_level_order >= 3 and complaint.priority not in [
            ComplaintPriority.CRITICAL, ComplaintPriority.URGENT
        ]:
            complaint.priority = ComplaintPriority.HIGH

        # Reassigner si specifie
        if data.assign_to_id:
            old_agent_id = complaint.assigned_to_id
            complaint.assigned_to_id = data.assign_to_id
            complaint.assigned_at = datetime.utcnow()

            if old_agent_id:
                self.agents.update_load(old_agent_id, -1)
            self.agents.update_load(data.assign_to_id, 1)

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="escalated",
            field_name="escalation_level",
            old_value=escalation.from_level.value,
            new_value=escalation.to_level.value,
            actor_type="automation" if is_automatic else "user",
            actor_id=escalated_by,
            actor_name=escalated_by_name,
            context={"reason": data.reason}
        )

        return complaint

    def resolve_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintResolve,
        resolved_by: UUID | None = None,
        resolved_by_name: str | None = None
    ) -> Complaint:
        """Resout une reclamation."""
        complaint = self.get_complaint(complaint_id)
        agent = self.agents.get_by_id(resolved_by) if resolved_by else None

        # Verifier les permissions pour compensation
        if data.compensation_amount and data.compensation_amount > 0:
            if agent and not agent.can_approve_compensation:
                raise InsufficientPermissionError("approve_compensation", str(resolved_by))

            if agent and data.compensation_amount > agent.max_compensation_amount:
                if not data.requires_approval:
                    raise CompensationLimitExceededError(
                        float(data.compensation_amount),
                        float(agent.max_compensation_amount),
                        str(resolved_by)
                    )

        # Mettre a jour
        old_status = complaint.status
        complaint.resolution_type = data.resolution_type
        complaint.resolution_summary = data.resolution_summary
        complaint.compensation_amount = data.compensation_amount
        complaint.compensation_type = data.compensation_type
        complaint.root_cause_category = data.root_cause_category
        complaint.root_cause_description = data.root_cause_description
        complaint.resolved_at = datetime.utcnow()
        complaint.updated_at = datetime.utcnow()

        # Verifier SLA resolution
        if complaint.resolution_due:
            complaint.resolution_breached = datetime.utcnow() > complaint.resolution_due

        if data.requires_approval:
            complaint.status = ComplaintStatus.PENDING_APPROVAL
        else:
            complaint.status = ComplaintStatus.RESOLVED

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="resolved",
            field_name="status",
            old_value=old_status.value,
            new_value=complaint.status.value,
            actor_type="user",
            actor_id=resolved_by,
            actor_name=resolved_by_name,
            context={
                "resolution_type": data.resolution_type.value,
                "compensation_amount": str(data.compensation_amount) if data.compensation_amount else None
            }
        )

        return complaint

    def close_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintClose,
        closed_by: UUID | None = None,
        closed_by_name: str | None = None
    ) -> Complaint:
        """Cloture une reclamation."""
        complaint = self.get_complaint(complaint_id)

        if complaint.status != ComplaintStatus.RESOLVED:
            raise ComplaintNotResolvedError(str(complaint_id))

        old_status = complaint.status
        complaint.status = ComplaintStatus.CLOSED
        complaint.closed_at = datetime.utcnow()
        complaint.updated_at = datetime.utcnow()

        if data.root_cause_category:
            complaint.root_cause_category = data.root_cause_category
        if data.root_cause_description:
            complaint.root_cause_description = data.root_cause_description

        # Liberer la charge de l'agent
        if complaint.assigned_to_id:
            self.agents.update_load(complaint.assigned_to_id, -1)

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="closed",
            field_name="status",
            old_value=old_status.value,
            new_value=ComplaintStatus.CLOSED.value,
            actor_type="user",
            actor_id=closed_by,
            actor_name=closed_by_name,
            context={"final_notes": data.final_notes} if data.final_notes else None
        )

        return complaint

    def reopen_complaint(
        self,
        complaint_id: UUID,
        data: ComplaintReopen,
        reopened_by: UUID | None = None,
        reopened_by_name: str | None = None
    ) -> Complaint:
        """Reouvre une reclamation."""
        complaint = self.get_complaint(complaint_id)

        if complaint.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            raise InvalidStatusTransitionError(
                complaint.status.value,
                ComplaintStatus.REOPENED.value,
                str(complaint_id)
            )

        old_status = complaint.status
        complaint.status = ComplaintStatus.REOPENED
        complaint.reopened_at = datetime.utcnow()
        complaint.reopen_count += 1
        complaint.resolved_at = None
        complaint.closed_at = None
        complaint.resolution_type = None
        complaint.resolution_summary = None
        complaint.updated_at = datetime.utcnow()

        # Reactiver la charge de l'agent si assigne
        if complaint.assigned_to_id:
            self.agents.update_load(complaint.assigned_to_id, 1)

        self.db.commit()
        self.db.refresh(complaint)

        # Historique
        self.history.add_entry(
            complaint_id=complaint.id,
            action="reopened",
            field_name="status",
            old_value=old_status.value,
            new_value=ComplaintStatus.REOPENED.value,
            actor_type="user",
            actor_id=reopened_by,
            actor_name=reopened_by_name,
            context={"reason": data.reason}
        )

        return complaint

    # ========================================================================
    # EXCHANGES
    # ========================================================================

    def add_exchange(
        self,
        complaint_id: UUID,
        data: ExchangeCreate,
        author_type: str = "agent",
        author_id: UUID | None = None,
        author_name: str | None = None,
        author_email: str | None = None
    ) -> ComplaintExchange:
        """Ajoute un echange a une reclamation."""
        complaint = self.get_complaint(complaint_id)

        # Verifier si premiere reponse
        is_first_response = False
        if author_type == "agent" and not data.is_internal:
            existing = self.exchanges.get_first_response(complaint_id)
            if not existing:
                is_first_response = True

        exchange = ComplaintExchange(
            tenant_id=self.tenant_id,
            complaint_id=complaint_id,
            author_type=author_type,
            author_id=author_id,
            author_name=author_name,
            author_email=author_email,
            subject=data.subject,
            body=data.body,
            body_html=data.body_html,
            exchange_type=data.exchange_type,
            is_internal=data.is_internal,
            is_first_response=is_first_response,
            channel=data.channel,
            cc_emails=data.cc_emails,
            sentiment=self._analyze_sentiment(data.body)
        )

        self.db.add(exchange)

        # Mettre a jour les compteurs
        if data.is_internal:
            complaint.internal_note_count += 1
        else:
            complaint.exchange_count += 1

        complaint.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(exchange)

        # Historique
        self.history.add_entry(
            complaint_id=complaint_id,
            action="exchange_added",
            actor_type=author_type,
            actor_id=author_id,
            actor_name=author_name,
            context={
                "exchange_type": data.exchange_type,
                "is_internal": data.is_internal
            }
        )

        return exchange

    def get_exchanges(
        self,
        complaint_id: UUID,
        include_internal: bool = True
    ) -> list[ComplaintExchange]:
        """Recupere les echanges d'une reclamation."""
        return self.exchanges.get_by_complaint(complaint_id, include_internal)

    # ========================================================================
    # ATTACHMENTS
    # ========================================================================

    def add_attachment(
        self,
        complaint_id: UUID,
        data: AttachmentCreate,
        uploaded_by_id: UUID | None = None,
        uploaded_by_name: str | None = None
    ) -> ComplaintAttachment:
        """Ajoute une piece jointe."""
        complaint = self.get_complaint(complaint_id)

        attachment = ComplaintAttachment(
            tenant_id=self.tenant_id,
            complaint_id=complaint_id,
            exchange_id=data.exchange_id,
            filename=data.filename,
            original_filename=data.original_filename,
            file_path=data.file_path,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type,
            description=data.description,
            is_evidence=data.is_evidence,
            uploaded_by_id=uploaded_by_id,
            uploaded_by_name=uploaded_by_name
        )

        self.db.add(attachment)

        complaint.attachment_count += 1
        complaint.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(attachment)

        return attachment

    def get_attachments(self, complaint_id: UUID) -> list[ComplaintAttachment]:
        """Recupere les pieces jointes d'une reclamation."""
        return self.attachments.get_by_complaint(complaint_id)

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def create_action(
        self,
        complaint_id: UUID,
        data: ActionCreate,
        created_by: UUID | None = None
    ) -> ComplaintAction:
        """Cree une action corrective."""
        complaint = self.get_complaint(complaint_id)

        action = ComplaintAction(
            tenant_id=self.tenant_id,
            complaint_id=complaint_id,
            action_type=data.action_type,
            title=data.title,
            description=data.description,
            assigned_to_id=data.assigned_to_id,
            assigned_to_name=data.assigned_to_name,
            assigned_at=datetime.utcnow() if data.assigned_to_id else None,
            due_date=data.due_date,
            reminder_date=data.reminder_date,
            status="pending",
            created_by=created_by
        )

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        return action

    def update_action(
        self,
        action_id: UUID,
        data: ActionUpdate
    ) -> ComplaintAction:
        """Met a jour une action."""
        action = self.actions.get_by_id(action_id)
        if not action:
            from .exceptions import ActionNotFoundError
            raise ActionNotFoundError(str(action_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(action, field):
                setattr(action, field, value)

        action.updated_at = datetime.utcnow()
        action.version += 1

        self.db.commit()
        self.db.refresh(action)

        return action

    def complete_action(
        self,
        action_id: UUID,
        data: ActionComplete,
        completed_by: UUID | None = None
    ) -> ComplaintAction:
        """Complete une action."""
        action = self.actions.get_by_id(action_id)
        if not action:
            from .exceptions import ActionNotFoundError
            raise ActionNotFoundError(str(action_id))

        action.status = "completed"
        action.completed_at = datetime.utcnow()
        action.completed_by_id = completed_by
        action.completion_notes = data.completion_notes
        action.outcome = data.outcome
        action.follow_up_required = data.follow_up_required
        action.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(action)

        return action

    def get_actions(self, complaint_id: UUID) -> list[ComplaintAction]:
        """Recupere les actions d'une reclamation."""
        return self.actions.get_by_complaint(complaint_id)

    # ========================================================================
    # SATISFACTION
    # ========================================================================

    def submit_satisfaction(
        self,
        complaint_id: UUID,
        data: SatisfactionSubmit
    ) -> Complaint:
        """Enregistre la satisfaction client."""
        complaint = self.get_complaint(complaint_id)

        complaint.satisfaction_rating = data.rating
        complaint.satisfaction_comment = data.comment
        complaint.satisfaction_submitted_at = datetime.utcnow()
        complaint.nps_score = data.nps_score
        complaint.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(complaint)

        # Mettre a jour le score de l'agent
        if complaint.assigned_to_id:
            self._update_agent_satisfaction(complaint.assigned_to_id)

        return complaint

    # ========================================================================
    # TEAMS
    # ========================================================================

    def create_team(self, data: TeamCreate) -> ComplaintTeam:
        """Cree une equipe."""
        team = ComplaintTeam(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        return self.teams.create(team)

    def update_team(self, team_id: UUID, data: TeamUpdate) -> ComplaintTeam:
        """Met a jour une equipe."""
        team = self.teams.get_by_id(team_id)
        if not team:
            raise TeamNotFoundError(str(team_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(team, field):
                setattr(team, field, value)

        return self.teams.update(team)

    def get_teams(self, active_only: bool = True) -> list[ComplaintTeam]:
        """Recupere les equipes."""
        if active_only:
            return self.teams.get_active()
        return self.teams.list_all()[0]

    # ========================================================================
    # AGENTS
    # ========================================================================

    def create_agent(self, data: AgentCreate) -> ComplaintAgent:
        """Cree un agent."""
        agent = ComplaintAgent(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        return self.agents.create(agent)

    def update_agent(self, agent_id: UUID, data: AgentUpdate) -> ComplaintAgent:
        """Met a jour un agent."""
        agent = self.agents.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(str(agent_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(agent, field):
                setattr(agent, field, value)

        return self.agents.update(agent)

    def get_agents(
        self,
        team_id: UUID | None = None,
        available_only: bool = False
    ) -> list[ComplaintAgent]:
        """Recupere les agents."""
        if available_only:
            return self.agents.get_available(team_id)

        agents, _ = self.agents.list_all(filters={"is_active": True})
        if team_id:
            agents = [a for a in agents if a.team_id == team_id]
        return agents

    # ========================================================================
    # SLA POLICIES
    # ========================================================================

    def create_sla_policy(self, data: SLAPolicyCreate) -> ComplaintSLAPolicy:
        """Cree une politique SLA."""
        policy = ComplaintSLAPolicy(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        return self.sla_policies.create(policy)

    def update_sla_policy(self, sla_id: UUID, data: SLAPolicyUpdate) -> ComplaintSLAPolicy:
        """Met a jour une politique SLA."""
        policy = self.sla_policies.get_by_id(sla_id)
        if not policy:
            raise SLAPolicyNotFoundError(str(sla_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(policy, field):
                setattr(policy, field, value)

        return self.sla_policies.update(policy)

    def get_sla_policies(self, active_only: bool = True) -> list[ComplaintSLAPolicy]:
        """Recupere les politiques SLA."""
        if active_only:
            return self.sla_policies.get_active()
        return self.sla_policies.list_all()[0]

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    def create_category(self, data: CategoryConfigCreate) -> ComplaintCategoryConfig:
        """Cree une categorie."""
        # Verifier l'unicite du code
        existing = self.categories.get_by_code(data.code)
        if existing:
            raise DuplicateCodeError(data.code, "category")

        category = ComplaintCategoryConfig(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        return self.categories.create(category)

    def update_category(self, category_id: UUID, data: CategoryConfigUpdate) -> ComplaintCategoryConfig:
        """Met a jour une categorie."""
        category = self.categories.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(category_id=str(category_id))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(category, field):
                setattr(category, field, value)

        return self.categories.update(category)

    def get_categories(
        self,
        active_only: bool = True,
        public_only: bool = False
    ) -> list[ComplaintCategoryConfig]:
        """Recupere les categories."""
        return self.categories.get_active(public_only)

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def create_template(
        self,
        data: TemplateCreate,
        owner_id: UUID | None = None
    ) -> ComplaintTemplate:
        """Cree un modele de reponse."""
        existing = self.templates.get_by_code(data.code)
        if existing:
            raise DuplicateCodeError(data.code, "template")

        # Extraire les variables
        variables = re.findall(r'\{\{(\w+)\}\}', data.body)

        template = ComplaintTemplate(
            tenant_id=self.tenant_id,
            owner_id=owner_id,
            variables=list(set(variables)),
            **data.model_dump()
        )
        return self.templates.create(template)

    def render_template(
        self,
        template_id: UUID,
        data: TemplateRender
    ) -> dict[str, str]:
        """Rend un modele avec les variables."""
        template = self.templates.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id=str(template_id))

        # Verifier les variables requises
        required_vars = template.variables or []
        missing = [v for v in required_vars if v not in data.variables]
        if missing:
            raise TemplateVariableError(str(template_id), missing)

        try:
            subject = template.subject or ""
            body = template.body
            body_html = template.body_html

            for var_name, var_value in data.variables.items():
                pattern = f"{{{{{var_name}}}}}"
                subject = subject.replace(pattern, var_value)
                body = body.replace(pattern, var_value)
                if body_html:
                    body_html = body_html.replace(pattern, var_value)

            # Incrementer le compteur
            self.templates.increment_usage(template_id)

            return {
                "subject": subject,
                "body": body,
                "body_html": body_html
            }
        except Exception as e:
            raise TemplateRenderError(str(template_id), str(e))

    def get_templates(
        self,
        category: ComplaintCategory | None = None,
        template_type: str | None = None,
        team_id: UUID | None = None,
        search: str | None = None
    ) -> list[ComplaintTemplate]:
        """Recupere les modeles."""
        return self.templates.get_active(
            category=category,
            template_type=template_type,
            team_id=team_id,
            search=search
        )

    # ========================================================================
    # AUTOMATION RULES
    # ========================================================================

    def create_automation_rule(self, data: AutomationRuleCreate) -> ComplaintAutomationRule:
        """Cree une regle d'automatisation."""
        rule = ComplaintAutomationRule(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        return self.automation_rules.create(rule)

    def get_automation_rules(self, active_only: bool = True) -> list[ComplaintAutomationRule]:
        """Recupere les regles d'automatisation."""
        if active_only:
            return self.automation_rules.get_active()
        return self.automation_rules.list_all()[0]

    # ========================================================================
    # HISTORY
    # ========================================================================

    def get_history(self, complaint_id: UUID) -> list[ComplaintHistory]:
        """Recupere l'historique d'une reclamation."""
        return self.history.get_by_complaint(complaint_id)

    # ========================================================================
    # STATISTICS & DASHBOARD
    # ========================================================================

    def get_stats(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        team_id: UUID | None = None,
        agent_id: UUID | None = None
    ) -> ComplaintStats:
        """Calcule les statistiques."""
        stats = self.complaints.get_stats(date_from, date_to, team_id, agent_id)

        return ComplaintStats(
            total=stats["total"],
            new=stats["by_status"].get(ComplaintStatus.NEW.value, 0),
            in_progress=stats["by_status"].get(ComplaintStatus.IN_PROGRESS.value, 0),
            pending=stats["by_status"].get(ComplaintStatus.PENDING_INFO.value, 0) +
                   stats["by_status"].get(ComplaintStatus.PENDING_CUSTOMER.value, 0),
            escalated=stats["by_status"].get(ComplaintStatus.ESCALATED.value, 0),
            resolved=stats["by_status"].get(ComplaintStatus.RESOLVED.value, 0),
            closed=stats["by_status"].get(ComplaintStatus.CLOSED.value, 0),
            sla_breached=stats["sla_breached"],
            avg_resolution_hours=stats["avg_resolution_hours"],
            resolution_rate=stats["resolution_rate"]
        )

    def get_dashboard(self, days: int = 30) -> ComplaintDashboard:
        """Genere le dashboard complet."""
        date_from = datetime.utcnow() - timedelta(days=days)

        # Stats globales
        stats = self.get_stats(date_from=date_from)

        # TODO: Implementer les autres metriques du dashboard
        # - by_category, by_priority, by_channel, by_status
        # - sla_performance, satisfaction
        # - agent_performance, team_performance
        # - trends, recent_complaints, top_root_causes

        return ComplaintDashboard(
            stats=stats,
            by_category=[],
            by_priority=[],
            by_channel=[],
            by_status=[],
            sla_performance=None,
            satisfaction=None,
            agent_performance=[],
            team_performance=[],
            trends=[],
            recent_complaints=[],
            top_root_causes=[]
        )

    # ========================================================================
    # SLA MANAGEMENT
    # ========================================================================

    def check_sla_breaches(self) -> list[Complaint]:
        """Verifie et marque les depassements SLA."""
        now = datetime.utcnow()

        # Reclamations avec SLA resolution depasse
        complaints = self.complaints._base_query().filter(
            Complaint.resolution_due < now,
            Complaint.resolution_breached == False,  # noqa: E712
            Complaint.status.not_in([
                ComplaintStatus.RESOLVED,
                ComplaintStatus.CLOSED,
                ComplaintStatus.CANCELLED
            ])
        ).all()

        for complaint in complaints:
            complaint.resolution_breached = True
            self.history.add_entry(
                complaint_id=complaint.id,
                action="sla_breached",
                field_name="resolution_breached",
                old_value="false",
                new_value="true",
                actor_type="system"
            )
            self._execute_automations("sla_breached", complaint)

        self.db.commit()

        return complaints

    def process_auto_escalations(self) -> list[Complaint]:
        """Traite les escalades automatiques."""
        complaints = self.complaints.get_pending_sla_breach(hours_before=0)
        escalated = []

        for complaint in complaints:
            if complaint.current_escalation_level == EscalationLevel.LEVEL_1:
                try:
                    self.escalate_complaint(
                        complaint.id,
                        ComplaintEscalate(
                            to_level=EscalationLevel.LEVEL_2,
                            reason="Escalade automatique - SLA depasse"
                        ),
                        is_automatic=True
                    )
                    escalated.append(complaint)
                except Exception as e:
                    logger.error(f"Erreur escalade auto: {e}")

        return escalated

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _auto_prioritize(self, data: ComplaintCreate) -> ComplaintPriority:
        """Determine automatiquement la priorite."""
        # RGPD = critique
        if data.category == ComplaintCategory.GDPR:
            return ComplaintPriority.CRITICAL

        # Fraude = urgente
        if data.category == ComplaintCategory.FRAUD:
            return ComplaintPriority.URGENT

        # Mots-cles urgents
        urgent_keywords = [
            "urgent", "immediat", "avocat", "juridique", "plainte",
            "mediation", "litige", "scandale", "reseaux sociaux",
            "presse", "autorite"
        ]
        desc_lower = data.description.lower()
        if any(kw in desc_lower for kw in urgent_keywords):
            return ComplaintPriority.HIGH

        # Montant eleve
        if data.disputed_amount and data.disputed_amount > Decimal("1000"):
            return ComplaintPriority.HIGH

        # Categories sensibles
        if data.category in [ComplaintCategory.PRODUCT_DEFECT, ComplaintCategory.BILLING]:
            return ComplaintPriority.MEDIUM

        return ComplaintPriority.MEDIUM

    def _calculate_sla_deadlines(
        self,
        complaint: Complaint,
        policy: ComplaintSLAPolicy
    ) -> Complaint:
        """Calcule les echeances SLA."""
        now = datetime.utcnow()
        priority = complaint.priority

        # Heures selon priorite
        if priority == ComplaintPriority.LOW:
            ack_hours = policy.ack_hours_low
            resolution_hours = policy.resolution_hours_low
            escalation_hours = policy.escalation_hours_low
        elif priority == ComplaintPriority.MEDIUM:
            ack_hours = policy.ack_hours_medium
            resolution_hours = policy.resolution_hours_medium
            escalation_hours = policy.escalation_hours_medium
        elif priority == ComplaintPriority.HIGH:
            ack_hours = policy.ack_hours_high
            resolution_hours = policy.resolution_hours_high
            escalation_hours = policy.escalation_hours_high
        elif priority == ComplaintPriority.URGENT:
            ack_hours = policy.ack_hours_urgent
            resolution_hours = policy.resolution_hours_urgent
            escalation_hours = policy.escalation_hours_urgent
        else:  # CRITICAL
            ack_hours = policy.ack_hours_critical
            resolution_hours = policy.resolution_hours_critical
            escalation_hours = policy.escalation_hours_critical

        # TODO: Gerer les heures ouvrees si business_hours_only

        complaint.acknowledgment_due = now + timedelta(hours=ack_hours)
        complaint.resolution_due = now + timedelta(hours=resolution_hours)
        complaint.escalation_due = now + timedelta(hours=escalation_hours)

        return complaint

    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment du texte."""
        text_lower = text.lower()

        negative_words = [
            "inacceptable", "scandaleux", "honteux", "inadmissible",
            "furieux", "decu", "mecontent", "catastrophe", "nul",
            "arnaque", "vol", "menteur", "incompetent", "honte",
            "deplorable", "lamentable", "horrible", "detestable"
        ]

        positive_words = [
            "merci", "satisfait", "content", "bien", "correct",
            "parfait", "excellent", "bravo", "super", "genial"
        ]

        negative_count = sum(1 for w in negative_words if w in text_lower)
        positive_count = sum(1 for w in positive_words if w in text_lower)

        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        return "neutral"

    def _auto_assign(self, complaint: Complaint) -> Complaint | None:
        """Assigne automatiquement une reclamation."""
        if not complaint.team_id:
            return None

        team = self.teams.get_by_id(complaint.team_id)
        if not team or not team.auto_assign_method:
            return None

        agent = None

        if team.auto_assign_method == "round_robin":
            agents = self.agents.get_available(team.id)
            if agents:
                # Trier par derniere assignation
                agents.sort(key=lambda a: a.last_assigned_at or datetime.min)
                agent = agents[0]

        elif team.auto_assign_method == "least_busy":
            agent = self.agents.get_least_busy(team.id)

        if agent:
            complaint.assigned_to_id = agent.id
            complaint.assigned_at = datetime.utcnow()
            self.agents.update_load(agent.id, 1)
            self.db.commit()
            self.db.refresh(complaint)

        return complaint

    def _get_escalation_order(self, level: EscalationLevel) -> int:
        """Retourne l'ordre d'un niveau d'escalade."""
        order = {
            EscalationLevel.LEVEL_1: 1,
            EscalationLevel.LEVEL_2: 2,
            EscalationLevel.LEVEL_3: 3,
            EscalationLevel.LEVEL_4: 4,
            EscalationLevel.LEGAL: 5,
            EscalationLevel.MEDIATOR: 6,
            EscalationLevel.EXTERNAL: 7
        }
        return order.get(level, 0)

    def _update_agent_satisfaction(self, agent_id: UUID) -> None:
        """Met a jour le score de satisfaction d'un agent."""
        # Calculer la moyenne des 30 derniers jours
        date_from = datetime.utcnow() - timedelta(days=30)

        complaints = self.complaints._base_query().filter(
            Complaint.assigned_to_id == agent_id,
            Complaint.satisfaction_rating.isnot(None),
            Complaint.satisfaction_submitted_at >= date_from
        ).all()

        if complaints:
            ratings = {
                SatisfactionRating.VERY_DISSATISFIED: 1,
                SatisfactionRating.DISSATISFIED: 2,
                SatisfactionRating.NEUTRAL: 3,
                SatisfactionRating.SATISFIED: 4,
                SatisfactionRating.VERY_SATISFIED: 5
            }
            scores = [ratings.get(c.satisfaction_rating, 3) for c in complaints]
            avg_score = Decimal(str(sum(scores) / len(scores))).quantize(Decimal("0.01"))

            agent = self.agents.get_by_id(agent_id)
            if agent:
                agent.satisfaction_score = avg_score
                self.db.commit()

    def _execute_automations(
        self,
        trigger_event: str,
        complaint: Complaint,
        context: dict | None = None
    ) -> None:
        """Execute les regles d'automatisation."""
        rules = self.automation_rules.get_by_trigger(trigger_event)

        for rule in rules:
            try:
                if self._check_automation_conditions(rule, complaint, context):
                    self._execute_automation_actions(rule, complaint)
                    self.automation_rules.increment_execution(rule.id)

                    if rule.stop_processing:
                        break

            except Exception as e:
                logger.error(f"Erreur automation {rule.id}: {e}")
                self.automation_rules.increment_execution(rule.id, str(e))

    def _check_automation_conditions(
        self,
        rule: ComplaintAutomationRule,
        complaint: Complaint,
        context: dict | None = None
    ) -> bool:
        """Verifie les conditions d'une regle."""
        if not rule.trigger_conditions:
            return True

        for condition in rule.trigger_conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            if not field or not operator:
                continue

            actual = getattr(complaint, field, None)
            if actual is None:
                if context:
                    actual = context.get(field)

            if actual is None:
                return False

            # Convertir les enums
            if hasattr(actual, "value"):
                actual = actual.value

            # Evaluer
            if operator == "equals" and actual != value:
                return False
            elif operator == "not_equals" and actual == value:
                return False
            elif operator == "in" and actual not in value:
                return False
            elif operator == "not_in" and actual in value:
                return False
            elif operator == "contains" and value not in str(actual):
                return False
            elif operator == "greater_than" and actual <= value:
                return False
            elif operator == "less_than" and actual >= value:
                return False

        return True

    def _execute_automation_actions(
        self,
        rule: ComplaintAutomationRule,
        complaint: Complaint
    ) -> None:
        """Execute les actions d'une regle."""
        for action in rule.actions:
            action_type = action.get("type")
            params = action.get("params", {})

            if action_type == "assign":
                team_id = params.get("team_id")
                agent_id = params.get("agent_id")
                if team_id or agent_id:
                    # TODO: Implementer l'assignation automatique
                    pass

            elif action_type == "change_priority":
                new_priority = params.get("priority")
                if new_priority:
                    complaint.priority = ComplaintPriority(new_priority)

            elif action_type == "add_tag":
                tag = params.get("tag")
                if tag:
                    if complaint.tags is None:
                        complaint.tags = []
                    if tag not in complaint.tags:
                        complaint.tags.append(tag)

            elif action_type == "send_notification":
                # TODO: Implementer l'envoi de notifications
                pass

            elif action_type == "create_action":
                # TODO: Creer une action automatiquement
                pass

        self.db.commit()
