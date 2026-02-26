"""
Service Approval Workflow / Approbations - GAP-083

Gestion des workflows d'approbation:
- Définition de workflows
- Règles et conditions
- Approbateurs et délégations
- Escalades automatiques
- Historique et audit
- Notifications
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4


# ============== Énumérations ==============

class ApprovalType(str, Enum):
    """Types d'approbation"""
    PURCHASE_ORDER = "purchase_order"
    EXPENSE_REPORT = "expense_report"
    LEAVE_REQUEST = "leave_request"
    TIMESHEET = "timesheet"
    INVOICE = "invoice"
    CONTRACT = "contract"
    BUDGET = "budget"
    REQUISITION = "requisition"
    DOCUMENT = "document"
    CUSTOM = "custom"


class WorkflowStatus(str, Enum):
    """Statuts workflow"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class RequestStatus(str, Enum):
    """Statuts demande"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class StepType(str, Enum):
    """Types d'étape"""
    SINGLE = "single"  # Un approbateur
    ANY = "any"  # N'importe quel approbateur
    ALL = "all"  # Tous les approbateurs
    MAJORITY = "majority"  # Majorité
    SEQUENCE = "sequence"  # Séquence ordonnée


class ApproverType(str, Enum):
    """Types d'approbateur"""
    USER = "user"
    ROLE = "role"
    MANAGER = "manager"
    DEPARTMENT_HEAD = "department_head"
    DYNAMIC = "dynamic"


class ActionType(str, Enum):
    """Types d'action"""
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"
    RETURN = "return"


class ConditionOperator(str, Enum):
    """Opérateurs de condition"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    IN = "in"
    BETWEEN = "between"


# ============== Data Classes ==============

@dataclass
class Condition:
    """Condition de workflow"""
    id: str
    field: str
    operator: ConditionOperator
    value: Any
    value2: Optional[Any] = None  # Pour BETWEEN


@dataclass
class Approver:
    """Approbateur"""
    id: str
    approver_type: ApproverType
    approver_id: str  # User ID, Role ID, etc.
    approver_name: str
    order: int = 0
    is_required: bool = True
    can_delegate: bool = True


@dataclass
class EscalationRule:
    """Règle d'escalade"""
    id: str
    trigger_hours: int  # Heures avant escalade
    escalate_to_type: ApproverType
    escalate_to_id: str
    escalate_to_name: str
    notify_original: bool = True
    auto_approve: bool = False


@dataclass
class WorkflowStep:
    """Étape de workflow"""
    id: str
    name: str
    description: str = ""
    order: int = 0
    step_type: StepType = StepType.SINGLE
    approvers: List[Approver] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    escalation_rules: List[EscalationRule] = field(default_factory=list)
    timeout_hours: Optional[int] = None
    auto_approve_on_timeout: bool = False
    auto_reject_on_timeout: bool = False
    notification_template: str = ""


@dataclass
class Workflow:
    """Workflow d'approbation"""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str = ""
    approval_type: ApprovalType = ApprovalType.CUSTOM
    status: WorkflowStatus = WorkflowStatus.DRAFT

    # Étapes
    steps: List[WorkflowStep] = field(default_factory=list)

    # Conditions d'activation
    conditions: List[Condition] = field(default_factory=list)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

    # Configuration
    allow_parallel_steps: bool = False
    require_comments_on_reject: bool = True
    allow_self_approval: bool = False
    skip_if_approver_is_requester: bool = True

    # Notifications
    notify_on_submit: bool = True
    notify_on_approve: bool = True
    notify_on_reject: bool = True
    notify_requester: bool = True

    # Métadonnées
    version: int = 1
    priority: int = 0
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalAction:
    """Action d'approbation"""
    id: str
    step_id: str
    approver_id: str
    approver_name: str
    action_type: ActionType
    comments: str = ""
    delegated_to_id: Optional[str] = None
    delegated_to_name: str = ""
    action_at: datetime = field(default_factory=datetime.now)
    ip_address: str = ""


@dataclass
class StepStatus:
    """Statut d'une étape"""
    step_id: str
    step_name: str
    status: str = "pending"  # pending, in_progress, approved, rejected, skipped
    required_approvals: int = 1
    received_approvals: int = 0
    received_rejections: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pending_approvers: List[str] = field(default_factory=list)
    actions: List[ApprovalAction] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    """Demande d'approbation"""
    id: str
    tenant_id: str
    workflow_id: str
    workflow_name: str
    request_number: str
    status: RequestStatus = RequestStatus.DRAFT

    # Demandeur
    requester_id: str = ""
    requester_name: str = ""
    requester_email: str = ""
    department_id: str = ""

    # Objet de la demande
    entity_type: str = ""  # purchase_order, expense_report, etc.
    entity_id: str = ""
    entity_number: str = ""
    entity_description: str = ""
    amount: Optional[Decimal] = None
    currency: str = "EUR"

    # Workflow
    current_step: int = 0
    step_statuses: List[StepStatus] = field(default_factory=list)

    # Historique
    actions: List[ApprovalAction] = field(default_factory=list)

    # Dates
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    # Métadonnées
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Delegation:
    """Délégation d'approbation"""
    id: str
    tenant_id: str
    delegator_id: str
    delegator_name: str
    delegate_id: str
    delegate_name: str
    start_date: date
    end_date: date
    approval_types: List[ApprovalType] = field(default_factory=list)
    max_amount: Optional[Decimal] = None
    is_active: bool = True
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalStats:
    """Statistiques d'approbation"""
    tenant_id: str
    period_start: date
    period_end: date
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    average_approval_time_hours: Decimal = Decimal("0")
    by_type: Dict[str, int] = field(default_factory=dict)
    by_approver: Dict[str, Dict] = field(default_factory=dict)
    by_department: Dict[str, int] = field(default_factory=dict)
    bottlenecks: List[Dict] = field(default_factory=list)


# ============== Service ==============

class ApprovalService:
    """
    Service de gestion des workflows d'approbation.

    Fonctionnalités:
    - Définition de workflows multi-étapes
    - Règles et conditions
    - Approbateurs dynamiques
    - Escalades automatiques
    - Délégations
    - Audit complet
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._workflows: Dict[str, Workflow] = {}
        self._requests: Dict[str, ApprovalRequest] = {}
        self._delegations: Dict[str, Delegation] = {}
        self._request_counter = 0

    # ========== Workflows ==========

    def create_workflow(
        self,
        name: str,
        code: str,
        approval_type: ApprovalType,
        description: str = "",
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        require_comments_on_reject: bool = True,
        created_by: str = ""
    ) -> Workflow:
        """Créer un workflow"""
        workflow = Workflow(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            code=code.upper(),
            description=description,
            approval_type=approval_type,
            min_amount=min_amount,
            max_amount=max_amount,
            require_comments_on_reject=require_comments_on_reject,
            created_by=created_by
        )
        self._workflows[workflow.id] = workflow
        return workflow

    def add_workflow_step(
        self,
        workflow_id: str,
        name: str,
        step_type: StepType = StepType.SINGLE,
        approvers: List[Dict] = None,
        timeout_hours: Optional[int] = None,
        conditions: List[Dict] = None
    ) -> Optional[WorkflowStep]:
        """Ajouter étape au workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status not in [WorkflowStatus.DRAFT, WorkflowStatus.INACTIVE]:
            return None

        step_approvers = []
        if approvers:
            for i, app in enumerate(approvers):
                step_approvers.append(Approver(
                    id=str(uuid4()),
                    approver_type=ApproverType(app.get("type", "user")),
                    approver_id=app.get("id", ""),
                    approver_name=app.get("name", ""),
                    order=i,
                    is_required=app.get("required", True),
                    can_delegate=app.get("can_delegate", True)
                ))

        step_conditions = []
        if conditions:
            for cond in conditions:
                step_conditions.append(Condition(
                    id=str(uuid4()),
                    field=cond.get("field", ""),
                    operator=ConditionOperator(cond.get("operator", "equals")),
                    value=cond.get("value"),
                    value2=cond.get("value2")
                ))

        step = WorkflowStep(
            id=str(uuid4()),
            name=name,
            order=len(workflow.steps),
            step_type=step_type,
            approvers=step_approvers,
            conditions=step_conditions,
            timeout_hours=timeout_hours
        )
        workflow.steps.append(step)
        workflow.updated_at = datetime.now()
        return step

    def add_escalation_rule(
        self,
        workflow_id: str,
        step_id: str,
        trigger_hours: int,
        escalate_to_type: ApproverType,
        escalate_to_id: str,
        escalate_to_name: str,
        notify_original: bool = True
    ) -> Optional[WorkflowStep]:
        """Ajouter règle d'escalade"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None

        for step in workflow.steps:
            if step.id == step_id:
                rule = EscalationRule(
                    id=str(uuid4()),
                    trigger_hours=trigger_hours,
                    escalate_to_type=escalate_to_type,
                    escalate_to_id=escalate_to_id,
                    escalate_to_name=escalate_to_name,
                    notify_original=notify_original
                )
                step.escalation_rules.append(rule)
                workflow.updated_at = datetime.now()
                return step

        return None

    def activate_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Activer workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow or not workflow.steps:
            return None

        workflow.status = WorkflowStatus.ACTIVE
        workflow.updated_at = datetime.now()
        return workflow

    def deactivate_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Désactiver workflow"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None

        workflow.status = WorkflowStatus.INACTIVE
        workflow.updated_at = datetime.now()
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Obtenir workflow"""
        return self._workflows.get(workflow_id)

    def find_matching_workflow(
        self,
        approval_type: ApprovalType,
        amount: Optional[Decimal] = None,
        context: Dict[str, Any] = None
    ) -> Optional[Workflow]:
        """Trouver workflow applicable"""
        matching = []

        for workflow in self._workflows.values():
            if workflow.status != WorkflowStatus.ACTIVE:
                continue
            if workflow.approval_type != approval_type:
                continue

            # Vérifier montant
            if workflow.min_amount and amount and amount < workflow.min_amount:
                continue
            if workflow.max_amount and amount and amount > workflow.max_amount:
                continue

            # Vérifier conditions
            if workflow.conditions and context:
                conditions_met = self._evaluate_conditions(workflow.conditions, context)
                if not conditions_met:
                    continue

            matching.append(workflow)

        # Retourner le plus prioritaire
        if matching:
            return sorted(matching, key=lambda x: x.priority, reverse=True)[0]
        return None

    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        approval_type: Optional[ApprovalType] = None
    ) -> List[Workflow]:
        """Lister workflows"""
        workflows = list(self._workflows.values())

        if status:
            workflows = [w for w in workflows if w.status == status]
        if approval_type:
            workflows = [w for w in workflows if w.approval_type == approval_type]

        return sorted(workflows, key=lambda x: x.name)

    # ========== Demandes ==========

    def create_request(
        self,
        workflow_id: str,
        requester_id: str,
        requester_name: str,
        entity_type: str,
        entity_id: str,
        entity_description: str,
        amount: Optional[Decimal] = None,
        requester_email: str = "",
        department_id: str = "",
        entity_number: str = "",
        due_date: Optional[datetime] = None,
        custom_data: Dict[str, Any] = None
    ) -> Optional[ApprovalRequest]:
        """Créer demande d'approbation"""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            return None

        self._request_counter += 1
        request_number = f"APR-{datetime.now().year}-{self._request_counter:06d}"

        # Initialiser statuts des étapes
        step_statuses = []
        for step in workflow.steps:
            step_statuses.append(StepStatus(
                step_id=step.id,
                step_name=step.name,
                required_approvals=self._count_required_approvals(step),
                pending_approvers=[a.approver_id for a in step.approvers]
            ))

        request = ApprovalRequest(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            request_number=request_number,
            requester_id=requester_id,
            requester_name=requester_name,
            requester_email=requester_email,
            department_id=department_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_number=entity_number,
            entity_description=entity_description,
            amount=amount,
            step_statuses=step_statuses,
            due_date=due_date,
            custom_data=custom_data or {}
        )
        self._requests[request.id] = request
        return request

    def submit_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Soumettre demande"""
        request = self._requests.get(request_id)
        if not request or request.status != RequestStatus.DRAFT:
            return None

        request.status = RequestStatus.PENDING
        request.submitted_at = datetime.now()
        request.updated_at = datetime.now()

        # Activer première étape
        if request.step_statuses:
            request.step_statuses[0].status = "in_progress"
            request.step_statuses[0].started_at = datetime.now()
            request.status = RequestStatus.IN_PROGRESS

        return request

    def take_action(
        self,
        request_id: str,
        approver_id: str,
        approver_name: str,
        action_type: ActionType,
        comments: str = "",
        delegate_to_id: Optional[str] = None,
        delegate_to_name: str = ""
    ) -> Optional[ApprovalRequest]:
        """Prendre action sur demande"""
        request = self._requests.get(request_id)
        if not request or request.status not in [RequestStatus.PENDING, RequestStatus.IN_PROGRESS]:
            return None

        workflow = self._workflows.get(request.workflow_id)
        if not workflow:
            return None

        # Vérifier si l'approbateur est valide pour l'étape courante
        current_step_status = request.step_statuses[request.current_step]
        current_step = workflow.steps[request.current_step]

        # Vérifier délégation
        actual_approver_id = approver_id
        delegator = self._find_delegator(approver_id, workflow.approval_type)
        if delegator:
            actual_approver_id = delegator

        if actual_approver_id not in current_step_status.pending_approvers:
            # Vérifier si approbateur dynamique
            is_valid = self._is_valid_approver(current_step, actual_approver_id, request)
            if not is_valid:
                return None

        # Créer action
        action = ApprovalAction(
            id=str(uuid4()),
            step_id=current_step.id,
            approver_id=approver_id,
            approver_name=approver_name,
            action_type=action_type,
            comments=comments,
            delegated_to_id=delegate_to_id,
            delegated_to_name=delegate_to_name
        )
        request.actions.append(action)
        current_step_status.actions.append(action)

        # Traiter action
        if action_type == ActionType.APPROVE:
            current_step_status.received_approvals += 1
            if actual_approver_id in current_step_status.pending_approvers:
                current_step_status.pending_approvers.remove(actual_approver_id)

            # Vérifier si étape complète
            if self._is_step_complete(current_step, current_step_status):
                current_step_status.status = "approved"
                current_step_status.completed_at = datetime.now()
                self._advance_to_next_step(request, workflow)

        elif action_type == ActionType.REJECT:
            if workflow.require_comments_on_reject and not comments:
                return None

            current_step_status.received_rejections += 1
            current_step_status.status = "rejected"
            current_step_status.completed_at = datetime.now()
            request.status = RequestStatus.REJECTED
            request.completed_at = datetime.now()

        elif action_type == ActionType.DELEGATE:
            if not delegate_to_id:
                return None
            # Remplacer approbateur
            if actual_approver_id in current_step_status.pending_approvers:
                idx = current_step_status.pending_approvers.index(actual_approver_id)
                current_step_status.pending_approvers[idx] = delegate_to_id

        elif action_type == ActionType.RETURN:
            request.status = RequestStatus.DRAFT
            request.current_step = 0
            for ss in request.step_statuses:
                ss.status = "pending"
                ss.received_approvals = 0
                ss.received_rejections = 0
                ss.started_at = None
                ss.completed_at = None

        request.updated_at = datetime.now()
        return request

    def cancel_request(
        self,
        request_id: str,
        cancelled_by: str,
        reason: str = ""
    ) -> Optional[ApprovalRequest]:
        """Annuler demande"""
        request = self._requests.get(request_id)
        if not request or request.status in [RequestStatus.APPROVED, RequestStatus.REJECTED]:
            return None

        request.status = RequestStatus.CANCELLED
        request.completed_at = datetime.now()
        request.updated_at = datetime.now()

        # Ajouter action
        action = ApprovalAction(
            id=str(uuid4()),
            step_id="",
            approver_id=cancelled_by,
            approver_name="",
            action_type=ActionType.REJECT,
            comments=f"Annulé: {reason}"
        )
        request.actions.append(action)

        return request

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Obtenir demande"""
        return self._requests.get(request_id)

    def list_requests(
        self,
        status: Optional[RequestStatus] = None,
        requester_id: Optional[str] = None,
        approval_type: Optional[ApprovalType] = None,
        pending_for_user: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """Lister demandes"""
        requests = list(self._requests.values())

        if status:
            requests = [r for r in requests if r.status == status]
        if requester_id:
            requests = [r for r in requests if r.requester_id == requester_id]
        if approval_type:
            workflow_ids = {
                w.id for w in self._workflows.values()
                if w.approval_type == approval_type
            }
            requests = [r for r in requests if r.workflow_id in workflow_ids]
        if pending_for_user:
            pending = []
            for r in requests:
                if r.status != RequestStatus.IN_PROGRESS:
                    continue
                step_status = r.step_statuses[r.current_step]
                if pending_for_user in step_status.pending_approvers:
                    pending.append(r)
                # Vérifier délégations
                elif self._is_delegate_for(pending_for_user, step_status.pending_approvers):
                    pending.append(r)
            requests = pending

        return sorted(requests, key=lambda x: x.created_at, reverse=True)

    def get_pending_approvals(self, user_id: str) -> List[ApprovalRequest]:
        """Obtenir approbations en attente pour un utilisateur"""
        return self.list_requests(
            status=RequestStatus.IN_PROGRESS,
            pending_for_user=user_id
        )

    # ========== Délégations ==========

    def create_delegation(
        self,
        delegator_id: str,
        delegator_name: str,
        delegate_id: str,
        delegate_name: str,
        start_date: date,
        end_date: date,
        approval_types: List[ApprovalType] = None,
        max_amount: Optional[Decimal] = None,
        reason: str = ""
    ) -> Delegation:
        """Créer délégation"""
        delegation = Delegation(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            delegator_id=delegator_id,
            delegator_name=delegator_name,
            delegate_id=delegate_id,
            delegate_name=delegate_name,
            start_date=start_date,
            end_date=end_date,
            approval_types=approval_types or [],
            max_amount=max_amount,
            reason=reason
        )
        self._delegations[delegation.id] = delegation
        return delegation

    def revoke_delegation(self, delegation_id: str) -> Optional[Delegation]:
        """Révoquer délégation"""
        delegation = self._delegations.get(delegation_id)
        if not delegation:
            return None

        delegation.is_active = False
        return delegation

    def get_active_delegations(
        self,
        delegator_id: Optional[str] = None,
        delegate_id: Optional[str] = None
    ) -> List[Delegation]:
        """Obtenir délégations actives"""
        today = date.today()
        delegations = [
            d for d in self._delegations.values()
            if d.is_active
            and d.start_date <= today <= d.end_date
        ]

        if delegator_id:
            delegations = [d for d in delegations if d.delegator_id == delegator_id]
        if delegate_id:
            delegations = [d for d in delegations if d.delegate_id == delegate_id]

        return delegations

    # ========== Helpers ==========

    def _evaluate_conditions(
        self,
        conditions: List[Condition],
        context: Dict[str, Any]
    ) -> bool:
        """Évaluer conditions"""
        for cond in conditions:
            value = context.get(cond.field)
            if value is None:
                return False

            if cond.operator == ConditionOperator.EQUALS:
                if value != cond.value:
                    return False
            elif cond.operator == ConditionOperator.NOT_EQUALS:
                if value == cond.value:
                    return False
            elif cond.operator == ConditionOperator.GREATER_THAN:
                if value <= cond.value:
                    return False
            elif cond.operator == ConditionOperator.LESS_THAN:
                if value >= cond.value:
                    return False
            elif cond.operator == ConditionOperator.GREATER_OR_EQUAL:
                if value < cond.value:
                    return False
            elif cond.operator == ConditionOperator.LESS_OR_EQUAL:
                if value > cond.value:
                    return False
            elif cond.operator == ConditionOperator.CONTAINS:
                if cond.value not in str(value):
                    return False
            elif cond.operator == ConditionOperator.IN:
                if value not in cond.value:
                    return False
            elif cond.operator == ConditionOperator.BETWEEN:
                if not (cond.value <= value <= cond.value2):
                    return False

        return True

    def _count_required_approvals(self, step: WorkflowStep) -> int:
        """Compter approbations requises"""
        if step.step_type == StepType.SINGLE:
            return 1
        elif step.step_type == StepType.ANY:
            return 1
        elif step.step_type == StepType.ALL:
            return len([a for a in step.approvers if a.is_required])
        elif step.step_type == StepType.MAJORITY:
            return len(step.approvers) // 2 + 1
        elif step.step_type == StepType.SEQUENCE:
            return len([a for a in step.approvers if a.is_required])
        return 1

    def _is_step_complete(
        self,
        step: WorkflowStep,
        step_status: StepStatus
    ) -> bool:
        """Vérifier si étape complète"""
        if step.step_type == StepType.SINGLE:
            return step_status.received_approvals >= 1
        elif step.step_type == StepType.ANY:
            return step_status.received_approvals >= 1
        elif step.step_type == StepType.ALL:
            return step_status.received_approvals >= step_status.required_approvals
        elif step.step_type == StepType.MAJORITY:
            return step_status.received_approvals >= step_status.required_approvals
        elif step.step_type == StepType.SEQUENCE:
            return step_status.received_approvals >= step_status.required_approvals
        return False

    def _advance_to_next_step(
        self,
        request: ApprovalRequest,
        workflow: Workflow
    ) -> None:
        """Avancer à l'étape suivante"""
        request.current_step += 1

        if request.current_step >= len(workflow.steps):
            # Workflow terminé
            request.status = RequestStatus.APPROVED
            request.completed_at = datetime.now()
        else:
            # Activer étape suivante
            next_step_status = request.step_statuses[request.current_step]
            next_step_status.status = "in_progress"
            next_step_status.started_at = datetime.now()

    def _is_valid_approver(
        self,
        step: WorkflowStep,
        user_id: str,
        request: ApprovalRequest
    ) -> bool:
        """Vérifier si utilisateur est approbateur valide"""
        for approver in step.approvers:
            if approver.approver_type == ApproverType.USER:
                if approver.approver_id == user_id:
                    return True
            elif approver.approver_type == ApproverType.MANAGER:
                # Simulation: le manager serait résolu dynamiquement
                pass
            elif approver.approver_type == ApproverType.ROLE:
                # Simulation: vérifier si user a le rôle
                pass

        return False

    def _find_delegator(
        self,
        delegate_id: str,
        approval_type: ApprovalType
    ) -> Optional[str]:
        """Trouver si quelqu'un a délégué à cet utilisateur"""
        today = date.today()
        for delegation in self._delegations.values():
            if not delegation.is_active:
                continue
            if delegation.delegate_id != delegate_id:
                continue
            if not (delegation.start_date <= today <= delegation.end_date):
                continue
            if delegation.approval_types and approval_type not in delegation.approval_types:
                continue

            return delegation.delegator_id

        return None

    def _is_delegate_for(
        self,
        user_id: str,
        pending_approvers: List[str]
    ) -> bool:
        """Vérifier si utilisateur est délégué"""
        delegations = self.get_active_delegations(delegate_id=user_id)
        delegator_ids = {d.delegator_id for d in delegations}
        return bool(delegator_ids.intersection(set(pending_approvers)))

    # ========== Escalades ==========

    def check_escalations(self) -> List[ApprovalRequest]:
        """Vérifier et traiter escalades"""
        escalated = []
        now = datetime.now()

        for request in self._requests.values():
            if request.status != RequestStatus.IN_PROGRESS:
                continue

            step_status = request.step_statuses[request.current_step]
            if not step_status.started_at:
                continue

            workflow = self._workflows.get(request.workflow_id)
            if not workflow:
                continue

            step = workflow.steps[request.current_step]

            for rule in step.escalation_rules:
                hours_elapsed = (now - step_status.started_at).total_seconds() / 3600

                if hours_elapsed >= rule.trigger_hours:
                    # Ajouter escalade
                    if rule.escalate_to_id not in step_status.pending_approvers:
                        step_status.pending_approvers.append(rule.escalate_to_id)
                        escalated.append(request)

                        if rule.auto_approve:
                            self.take_action(
                                request.id,
                                rule.escalate_to_id,
                                rule.escalate_to_name,
                                ActionType.APPROVE,
                                "Auto-approbation par escalade"
                            )

        return escalated

    # ========== Statistiques ==========

    def get_approval_stats(
        self,
        period_start: date,
        period_end: date
    ) -> ApprovalStats:
        """Calculer statistiques"""
        stats = ApprovalStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        requests = [
            r for r in self._requests.values()
            if r.submitted_at and period_start <= r.submitted_at.date() <= period_end
        ]

        stats.total_requests = len(requests)
        stats.pending_requests = len([r for r in requests if r.status in [
            RequestStatus.PENDING, RequestStatus.IN_PROGRESS
        ]])
        stats.approved_requests = len([r for r in requests if r.status == RequestStatus.APPROVED])
        stats.rejected_requests = len([r for r in requests if r.status == RequestStatus.REJECTED])

        # Temps moyen
        completed = [r for r in requests if r.completed_at and r.submitted_at]
        if completed:
            total_hours = sum(
                (r.completed_at - r.submitted_at).total_seconds() / 3600
                for r in completed
            )
            stats.average_approval_time_hours = Decimal(str(total_hours / len(completed)))

        # Par type
        for r in requests:
            workflow = self._workflows.get(r.workflow_id)
            if workflow:
                key = workflow.approval_type.value
                stats.by_type[key] = stats.by_type.get(key, 0) + 1

        # Par département
        for r in requests:
            if r.department_id:
                stats.by_department[r.department_id] = \
                    stats.by_department.get(r.department_id, 0) + 1

        return stats


def create_approval_service(tenant_id: str) -> ApprovalService:
    """Factory function pour créer le service approval"""
    return ApprovalService(tenant_id)
