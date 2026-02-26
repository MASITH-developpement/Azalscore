"""
Service de Workflows et BPM - GAP-045

Gestion des processus métier:
- Définition de workflows visuels
- Étapes et transitions
- Conditions et règles
- Actions automatiques
- Approbations multi-niveaux
- Escalade automatique
- Délégation
- Historique et audit
- Parallélisme et jonctions
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import json


class WorkflowStatus(Enum):
    """Statut d'un workflow."""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class InstanceStatus(Enum):
    """Statut d'une instance de workflow."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"  # En attente d'action
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SUSPENDED = "suspended"


class StepType(Enum):
    """Type d'étape."""
    START = "start"
    END = "end"
    TASK = "task"  # Tâche manuelle
    APPROVAL = "approval"  # Approbation
    DECISION = "decision"  # Branchement conditionnel
    PARALLEL_SPLIT = "parallel_split"  # Fork
    PARALLEL_JOIN = "parallel_join"  # Join (AND)
    INCLUSIVE_JOIN = "inclusive_join"  # Join (OR)
    TIMER = "timer"  # Attente temporisée
    SUBPROCESS = "subprocess"  # Sous-workflow
    SCRIPT = "script"  # Exécution de script
    NOTIFICATION = "notification"  # Envoi de notification
    INTEGRATION = "integration"  # Appel externe


class TaskStatus(Enum):
    """Statut d'une tâche."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    DELEGATED = "delegated"
    ESCALATED = "escalated"


class ApprovalType(Enum):
    """Type d'approbation."""
    SINGLE = "single"  # Un seul approbateur
    SEQUENTIAL = "sequential"  # Séquentiel
    PARALLEL = "parallel"  # Tous en parallèle
    QUORUM = "quorum"  # Majorité
    FIRST_RESPONSE = "first_response"  # Premier qui répond


class ConditionOperator(Enum):
    """Opérateur de condition."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IN_LIST = "in_list"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class Condition:
    """Condition pour une transition."""
    field: str
    operator: ConditionOperator
    value: Any
    logic: str = "and"  # and, or

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Évalue la condition."""
        field_value = self._get_field_value(context, self.field)

        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == ConditionOperator.CONTAINS:
            return self.value in str(field_value)
        elif self.operator == ConditionOperator.IN_LIST:
            return field_value in self.value
        elif self.operator == ConditionOperator.IS_TRUE:
            return bool(field_value) is True
        elif self.operator == ConditionOperator.IS_FALSE:
            return bool(field_value) is False
        elif self.operator == ConditionOperator.IS_NULL:
            return field_value is None
        elif self.operator == ConditionOperator.IS_NOT_NULL:
            return field_value is not None

        return False

    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """Récupère la valeur d'un champ (supporte la notation pointée)."""
        parts = field.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value


@dataclass
class Transition:
    """Transition entre étapes."""
    transition_id: str
    from_step_id: str
    to_step_id: str
    name: str = ""
    conditions: List[Condition] = field(default_factory=list)
    is_default: bool = False
    priority: int = 0

    def can_transition(self, context: Dict[str, Any]) -> bool:
        """Vérifie si la transition est possible."""
        if not self.conditions:
            return True

        # Évaluer toutes les conditions
        results = []
        for condition in self.conditions:
            results.append((condition.evaluate(context), condition.logic))

        # Combiner avec les opérateurs logiques
        result = results[0][0]
        for i in range(1, len(results)):
            value, logic = results[i]
            if logic == "and":
                result = result and value
            else:
                result = result or value

        return result


@dataclass
class AssignmentRule:
    """Règle d'assignation de tâche."""
    rule_type: str  # "user", "role", "group", "expression", "supervisor"
    value: str
    fallback: Optional[str] = None


@dataclass
class EscalationRule:
    """Règle d'escalade."""
    after_hours: int
    escalate_to: AssignmentRule
    notification_template: Optional[str] = None
    max_escalations: int = 3


@dataclass
class Step:
    """Étape de workflow."""
    step_id: str
    name: str
    step_type: StepType
    description: str = ""

    # Assignation
    assignment_rules: List[AssignmentRule] = field(default_factory=list)

    # Approbation
    approval_type: ApprovalType = ApprovalType.SINGLE
    approvers: List[str] = field(default_factory=list)
    quorum_percent: int = 50
    allow_delegation: bool = True
    allow_rejection: bool = True

    # Délais
    due_hours: Optional[int] = None
    reminder_hours: Optional[int] = None
    escalation_rules: List[EscalationRule] = field(default_factory=list)

    # Actions automatiques
    on_enter_actions: List[Dict[str, Any]] = field(default_factory=list)
    on_exit_actions: List[Dict[str, Any]] = field(default_factory=list)
    on_complete_actions: List[Dict[str, Any]] = field(default_factory=list)

    # Script (pour StepType.SCRIPT)
    script_code: Optional[str] = None
    script_language: str = "python"

    # Timer
    timer_duration_hours: Optional[int] = None
    timer_expression: Optional[str] = None  # Cron

    # Sous-workflow
    subprocess_workflow_id: Optional[str] = None

    # UI
    form_definition: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Définition d'un workflow."""
    workflow_id: str
    tenant_id: str
    name: str
    description: str
    version: int
    status: WorkflowStatus

    # Structure
    steps: List[Step] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    start_step_id: Optional[str] = None
    end_step_ids: List[str] = field(default_factory=list)

    # Variables
    variables: Dict[str, Any] = field(default_factory=dict)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None

    # Déclencheurs
    triggers: List[Dict[str, Any]] = field(default_factory=list)

    # SLA global
    sla_hours: Optional[int] = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_at: Optional[datetime] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)


@dataclass
class TaskInstance:
    """Instance de tâche."""
    task_id: str
    instance_id: str
    step_id: str
    status: TaskStatus

    # Assignation
    assigned_to: Optional[str] = None
    assigned_role: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Délégation
    delegated_by: Optional[str] = None
    delegated_at: Optional[datetime] = None
    original_assignee: Optional[str] = None

    # Délais
    due_at: Optional[datetime] = None
    reminded_at: Optional[datetime] = None
    escalation_level: int = 0

    # Résultat
    outcome: Optional[str] = None  # "approved", "rejected", "completed"
    decision_data: Dict[str, Any] = field(default_factory=dict)
    comments: str = ""

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepExecution:
    """Exécution d'une étape."""
    execution_id: str
    instance_id: str
    step_id: str
    step_name: str
    step_type: StepType
    status: str = "pending"  # pending, running, completed, failed, skipped

    # Tâches
    tasks: List[TaskInstance] = field(default_factory=list)

    # Données
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Erreur
    error_message: Optional[str] = None

    # Parallélisme
    is_parallel_branch: bool = False
    parallel_branch_id: Optional[str] = None


@dataclass
class WorkflowInstance:
    """Instance de workflow."""
    instance_id: str
    tenant_id: str
    workflow_id: str
    workflow_name: str
    version: int
    status: InstanceStatus

    # Contexte
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    # État
    current_step_ids: List[str] = field(default_factory=list)
    step_executions: List[StepExecution] = field(default_factory=list)

    # Référence
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reference_name: Optional[str] = None

    # Initiateur
    initiated_by: str = ""
    initiated_at: datetime = field(default_factory=datetime.now)

    # Délais
    due_at: Optional[datetime] = None
    sla_breached: bool = False

    # Completion
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None

    # Métadonnées
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowHistory:
    """Historique d'une instance."""
    history_id: str
    instance_id: str
    event_type: str  # step_started, step_completed, task_assigned, etc.
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    actor: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class WorkflowService:
    """Service de gestion des workflows."""

    def __init__(
        self,
        tenant_id: str,
        workflow_repository: Optional[Any] = None,
        instance_repository: Optional[Any] = None,
        user_service: Optional[Any] = None,
        notification_service: Optional[Any] = None,
        script_executor: Optional[Callable] = None
    ):
        self.tenant_id = tenant_id
        self.workflow_repo = workflow_repository or {}
        self.instance_repo = instance_repository or {}
        self.user_service = user_service
        self.notification_service = notification_service
        self.script_executor = script_executor

        # Caches
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._instances: Dict[str, WorkflowInstance] = {}
        self._history: Dict[str, List[WorkflowHistory]] = {}

        # Actions enregistrées
        self._action_handlers: Dict[str, Callable] = {}

    # =========================================================================
    # Définition de Workflows
    # =========================================================================

    def create_workflow(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> WorkflowDefinition:
        """Crée un nouveau workflow."""
        workflow_id = f"wf_{uuid4().hex[:12]}"

        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            version=1,
            status=WorkflowStatus.DRAFT,
            variables=kwargs.get("variables", {}),
            input_schema=kwargs.get("input_schema"),
            output_schema=kwargs.get("output_schema"),
            triggers=kwargs.get("triggers", []),
            sla_hours=kwargs.get("sla_hours"),
            created_by=kwargs.get("created_by", "system"),
            category=kwargs.get("category", "general"),
            tags=kwargs.get("tags", [])
        )

        self._workflows[workflow_id] = workflow
        return workflow

    def add_step(
        self,
        workflow_id: str,
        name: str,
        step_type: StepType,
        **kwargs
    ) -> Step:
        """Ajoute une étape au workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        step_id = f"step_{uuid4().hex[:8]}"

        # Construire les règles d'assignation
        assignment_rules = []
        for rule_data in kwargs.get("assignment_rules", []):
            rule = AssignmentRule(
                rule_type=rule_data.get("type", "user"),
                value=rule_data.get("value", ""),
                fallback=rule_data.get("fallback")
            )
            assignment_rules.append(rule)

        # Construire les règles d'escalade
        escalation_rules = []
        for esc_data in kwargs.get("escalation_rules", []):
            esc = EscalationRule(
                after_hours=esc_data.get("after_hours", 24),
                escalate_to=AssignmentRule(
                    rule_type=esc_data.get("escalate_type", "supervisor"),
                    value=esc_data.get("escalate_value", "")
                ),
                notification_template=esc_data.get("notification_template")
            )
            escalation_rules.append(esc)

        step = Step(
            step_id=step_id,
            name=name,
            step_type=step_type,
            description=kwargs.get("description", ""),
            assignment_rules=assignment_rules,
            approval_type=kwargs.get("approval_type", ApprovalType.SINGLE),
            approvers=kwargs.get("approvers", []),
            quorum_percent=kwargs.get("quorum_percent", 50),
            allow_delegation=kwargs.get("allow_delegation", True),
            allow_rejection=kwargs.get("allow_rejection", True),
            due_hours=kwargs.get("due_hours"),
            reminder_hours=kwargs.get("reminder_hours"),
            escalation_rules=escalation_rules,
            on_enter_actions=kwargs.get("on_enter_actions", []),
            on_exit_actions=kwargs.get("on_exit_actions", []),
            on_complete_actions=kwargs.get("on_complete_actions", []),
            script_code=kwargs.get("script_code"),
            timer_duration_hours=kwargs.get("timer_duration_hours"),
            subprocess_workflow_id=kwargs.get("subprocess_workflow_id"),
            form_definition=kwargs.get("form_definition"),
            instructions=kwargs.get("instructions"),
            metadata=kwargs.get("metadata", {})
        )

        workflow.steps.append(step)

        # Définir l'étape de départ si c'est START
        if step_type == StepType.START:
            workflow.start_step_id = step_id
        elif step_type == StepType.END:
            workflow.end_step_ids.append(step_id)

        workflow.updated_at = datetime.now()
        return step

    def add_transition(
        self,
        workflow_id: str,
        from_step_id: str,
        to_step_id: str,
        name: str = "",
        conditions: Optional[List[Dict[str, Any]]] = None,
        is_default: bool = False
    ) -> Transition:
        """Ajoute une transition entre étapes."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        transition_id = f"tr_{uuid4().hex[:8]}"

        # Construire les conditions
        condition_objects = []
        for cond_data in (conditions or []):
            cond = Condition(
                field=cond_data["field"],
                operator=ConditionOperator(cond_data["operator"]),
                value=cond_data.get("value"),
                logic=cond_data.get("logic", "and")
            )
            condition_objects.append(cond)

        transition = Transition(
            transition_id=transition_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
            name=name,
            conditions=condition_objects,
            is_default=is_default,
            priority=len(workflow.transitions)
        )

        workflow.transitions.append(transition)
        workflow.updated_at = datetime.now()
        return transition

    def activate_workflow(self, workflow_id: str) -> WorkflowDefinition:
        """Active un workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        # Validation
        if not workflow.start_step_id:
            raise ValueError("Le workflow n'a pas d'étape de départ")
        if not workflow.end_step_ids:
            raise ValueError("Le workflow n'a pas d'étape de fin")

        workflow.status = WorkflowStatus.ACTIVE
        workflow.updated_at = datetime.now()
        return workflow

    def create_new_version(
        self,
        workflow_id: str
    ) -> WorkflowDefinition:
        """Crée une nouvelle version du workflow."""
        original = self._workflows.get(workflow_id)
        if not original:
            raise ValueError(f"Workflow {workflow_id} non trouvé")

        new_id = f"wf_{uuid4().hex[:12]}"

        # Copier le workflow
        new_workflow = WorkflowDefinition(
            workflow_id=new_id,
            tenant_id=self.tenant_id,
            name=original.name,
            description=original.description,
            version=original.version + 1,
            status=WorkflowStatus.DRAFT,
            steps=[s for s in original.steps],  # Copie des étapes
            transitions=[t for t in original.transitions],
            start_step_id=original.start_step_id,
            end_step_ids=original.end_step_ids.copy(),
            variables=original.variables.copy(),
            input_schema=original.input_schema,
            output_schema=original.output_schema,
            triggers=original.triggers.copy(),
            sla_hours=original.sla_hours,
            category=original.category,
            tags=original.tags.copy()
        )

        # Archiver l'ancienne version
        original.status = WorkflowStatus.ARCHIVED

        self._workflows[new_id] = new_workflow
        return new_workflow

    # =========================================================================
    # Exécution de Workflows
    # =========================================================================

    def start_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any],
        initiated_by: str,
        **kwargs
    ) -> WorkflowInstance:
        """Démarre une instance de workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow {workflow_id} non disponible")

        instance_id = f"inst_{uuid4().hex[:12]}"

        # Calculer la date d'échéance
        due_at = None
        if workflow.sla_hours:
            due_at = datetime.now() + timedelta(hours=workflow.sla_hours)

        instance = WorkflowInstance(
            instance_id=instance_id,
            tenant_id=self.tenant_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            version=workflow.version,
            status=InstanceStatus.RUNNING,
            context=context,
            variables=workflow.variables.copy(),
            reference_type=kwargs.get("reference_type"),
            reference_id=kwargs.get("reference_id"),
            reference_name=kwargs.get("reference_name"),
            initiated_by=initiated_by,
            due_at=due_at,
            metadata=kwargs.get("metadata", {}),
            tags=kwargs.get("tags", [])
        )

        self._instances[instance_id] = instance
        self._history[instance_id] = []

        # Log le démarrage
        self._add_history(
            instance_id,
            "workflow_started",
            actor=initiated_by,
            details={"context": context}
        )

        # Exécuter l'étape de départ
        if workflow.start_step_id:
            self._execute_step(instance, workflow.start_step_id, workflow)

        return instance

    def _execute_step(
        self,
        instance: WorkflowInstance,
        step_id: str,
        workflow: WorkflowDefinition
    ) -> StepExecution:
        """Exécute une étape."""
        step = self._get_step(workflow, step_id)
        if not step:
            raise ValueError(f"Étape {step_id} non trouvée")

        execution_id = f"exec_{uuid4().hex[:8]}"

        execution = StepExecution(
            execution_id=execution_id,
            instance_id=instance.instance_id,
            step_id=step_id,
            step_name=step.name,
            step_type=step.step_type,
            status="running",
            started_at=datetime.now(),
            input_data=instance.context.copy()
        )

        instance.step_executions.append(execution)
        instance.current_step_ids = [step_id]

        # Log
        self._add_history(
            instance.instance_id,
            "step_started",
            step_id=step_id,
            details={"step_name": step.name, "step_type": step.step_type.value}
        )

        # Exécuter les actions d'entrée
        self._execute_actions(step.on_enter_actions, instance)

        # Traiter selon le type d'étape
        if step.step_type == StepType.START:
            # Passer directement aux transitions suivantes
            self._complete_step(instance, execution, workflow)

        elif step.step_type == StepType.END:
            # Terminer le workflow
            execution.status = "completed"
            execution.completed_at = datetime.now()
            self._complete_workflow(instance, "completed")

        elif step.step_type in (StepType.TASK, StepType.APPROVAL):
            # Créer les tâches
            self._create_tasks(instance, execution, step)
            instance.status = InstanceStatus.WAITING

        elif step.step_type == StepType.DECISION:
            # Évaluer les conditions et choisir la transition
            self._complete_step(instance, execution, workflow)

        elif step.step_type == StepType.PARALLEL_SPLIT:
            # Créer les branches parallèles
            self._create_parallel_branches(instance, execution, step, workflow)

        elif step.step_type == StepType.PARALLEL_JOIN:
            # Vérifier si toutes les branches sont terminées
            self._check_parallel_join(instance, execution, step, workflow)

        elif step.step_type == StepType.TIMER:
            # Programmer le timer
            self._schedule_timer(instance, execution, step)

        elif step.step_type == StepType.SCRIPT:
            # Exécuter le script
            self._execute_script(instance, execution, step)
            self._complete_step(instance, execution, workflow)

        elif step.step_type == StepType.NOTIFICATION:
            # Envoyer la notification
            self._send_step_notification(instance, step)
            self._complete_step(instance, execution, workflow)

        return execution

    def _get_step(
        self,
        workflow: WorkflowDefinition,
        step_id: str
    ) -> Optional[Step]:
        """Récupère une étape par ID."""
        for step in workflow.steps:
            if step.step_id == step_id:
                return step
        return None

    def _create_tasks(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        step: Step
    ):
        """Crée les tâches pour une étape."""
        assignees = self._resolve_assignees(step, instance)

        if step.step_type == StepType.APPROVAL:
            if step.approval_type == ApprovalType.SEQUENTIAL:
                # Créer une seule tâche pour le premier approbateur
                assignees = [assignees[0]] if assignees else []

        for assignee in assignees:
            task = TaskInstance(
                task_id=f"task_{uuid4().hex[:8]}",
                instance_id=instance.instance_id,
                step_id=step.step_id,
                status=TaskStatus.ASSIGNED,
                assigned_to=assignee,
                assigned_at=datetime.now()
            )

            # Calculer l'échéance
            if step.due_hours:
                task.due_at = datetime.now() + timedelta(hours=step.due_hours)

            execution.tasks.append(task)

            # Log
            self._add_history(
                instance.instance_id,
                "task_assigned",
                step_id=step.step_id,
                task_id=task.task_id,
                actor="system",
                details={"assigned_to": assignee}
            )

            # Notification
            if self.notification_service:
                self.notification_service(
                    "task_assigned",
                    {
                        "task_id": task.task_id,
                        "assignee": assignee,
                        "step_name": step.name,
                        "due_at": task.due_at.isoformat() if task.due_at else None,
                        "instructions": step.instructions
                    }
                )

    def _resolve_assignees(
        self,
        step: Step,
        instance: WorkflowInstance
    ) -> List[str]:
        """Résout les assignataires selon les règles."""
        assignees = []

        # Approbateurs explicites
        if step.approvers:
            assignees.extend(step.approvers)

        # Règles d'assignation
        for rule in step.assignment_rules:
            if rule.rule_type == "user":
                assignees.append(rule.value)
            elif rule.rule_type == "role":
                # Récupérer les utilisateurs avec ce rôle
                if self.user_service:
                    users = self.user_service.get_users_by_role(rule.value)
                    assignees.extend(users)
            elif rule.rule_type == "expression":
                # Évaluer l'expression dans le contexte
                value = self._evaluate_expression(rule.value, instance.context)
                if value:
                    assignees.append(value)
            elif rule.rule_type == "supervisor":
                # Récupérer le superviseur de l'initiateur
                if self.user_service:
                    supervisor = self.user_service.get_supervisor(
                        instance.context.get("user_id") or instance.initiated_by
                    )
                    if supervisor:
                        assignees.append(supervisor)

        return list(set(assignees))  # Dédupliquer

    def _evaluate_expression(
        self,
        expression: str,
        context: Dict[str, Any]
    ) -> Any:
        """Évalue une expression simple."""
        # Expression de type ${field.subfield}
        if expression.startswith("${") and expression.endswith("}"):
            field = expression[2:-1]
            parts = field.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return expression

    def complete_task(
        self,
        task_id: str,
        completed_by: str,
        outcome: str,
        decision_data: Optional[Dict[str, Any]] = None,
        comments: str = ""
    ) -> TaskInstance:
        """Complète une tâche."""
        # Trouver la tâche
        task = None
        instance = None
        execution = None

        for inst in self._instances.values():
            for exec_ in inst.step_executions:
                for t in exec_.tasks:
                    if t.task_id == task_id:
                        task = t
                        instance = inst
                        execution = exec_
                        break

        if not task:
            raise ValueError(f"Tâche {task_id} non trouvée")

        if task.status not in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
            raise ValueError(f"Tâche ne peut pas être complétée: {task.status}")

        # Mettre à jour la tâche
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.completed_by = completed_by
        task.outcome = outcome
        task.decision_data = decision_data or {}
        task.comments = comments

        # Log
        self._add_history(
            instance.instance_id,
            "task_completed",
            step_id=task.step_id,
            task_id=task_id,
            actor=completed_by,
            details={"outcome": outcome, "comments": comments}
        )

        # Vérifier si l'étape est terminée
        workflow = self._workflows.get(instance.workflow_id)
        step = self._get_step(workflow, task.step_id)

        if self._is_step_completed(execution, step):
            # Mettre à jour le contexte avec les données de décision
            if decision_data:
                instance.context.update(decision_data)

            # Définir le résultat de l'exécution
            execution.output_data = {
                "outcome": outcome,
                "completed_by": completed_by,
                "decision_data": decision_data
            }

            self._complete_step(instance, execution, workflow)

        return task

    def _is_step_completed(
        self,
        execution: StepExecution,
        step: Step
    ) -> bool:
        """Vérifie si toutes les tâches de l'étape sont terminées."""
        completed_tasks = [
            t for t in execution.tasks
            if t.status == TaskStatus.COMPLETED
        ]

        if step.step_type == StepType.APPROVAL:
            if step.approval_type == ApprovalType.SINGLE:
                return len(completed_tasks) >= 1

            elif step.approval_type == ApprovalType.PARALLEL:
                # Tous doivent approuver
                return len(completed_tasks) == len(execution.tasks)

            elif step.approval_type == ApprovalType.QUORUM:
                # Majorité
                approved = len([t for t in completed_tasks if t.outcome == "approved"])
                total = len(execution.tasks)
                return (approved / total * 100) >= step.quorum_percent

            elif step.approval_type == ApprovalType.FIRST_RESPONSE:
                return len(completed_tasks) >= 1

            elif step.approval_type == ApprovalType.SEQUENTIAL:
                # Vérifier si c'était le dernier approbateur
                if completed_tasks and completed_tasks[-1].outcome == "approved":
                    # Créer la tâche pour le suivant s'il y en a
                    return len(completed_tasks) == len(step.approvers)
                elif completed_tasks and completed_tasks[-1].outcome == "rejected":
                    return True

        else:
            return len(completed_tasks) == len(execution.tasks)

        return False

    def _complete_step(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        workflow: WorkflowDefinition
    ):
        """Complète une étape et passe aux suivantes."""
        step = self._get_step(workflow, execution.step_id)

        execution.status = "completed"
        execution.completed_at = datetime.now()

        # Exécuter les actions de sortie
        self._execute_actions(step.on_exit_actions, instance)
        self._execute_actions(step.on_complete_actions, instance)

        # Log
        self._add_history(
            instance.instance_id,
            "step_completed",
            step_id=execution.step_id,
            details={"output": execution.output_data}
        )

        # Trouver les transitions possibles
        next_step_ids = self._find_next_steps(
            workflow, execution.step_id, instance.context
        )

        if not next_step_ids:
            # Pas de transition, vérifier si c'est une fin
            if execution.step_id in workflow.end_step_ids:
                self._complete_workflow(instance, "completed")
            else:
                instance.status = InstanceStatus.FAILED
                self._add_history(
                    instance.instance_id,
                    "workflow_failed",
                    details={"reason": "No transition found"}
                )
        else:
            # Exécuter les prochaines étapes
            for step_id in next_step_ids:
                self._execute_step(instance, step_id, workflow)

    def _find_next_steps(
        self,
        workflow: WorkflowDefinition,
        from_step_id: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Trouve les prochaines étapes possibles."""
        possible = []
        default = None

        # Trier les transitions par priorité
        transitions = sorted(
            [t for t in workflow.transitions if t.from_step_id == from_step_id],
            key=lambda t: t.priority
        )

        for transition in transitions:
            if transition.is_default:
                default = transition.to_step_id
            elif transition.can_transition(context):
                possible.append(transition.to_step_id)

        # Si aucune transition conditionnelle, utiliser la défaut
        if not possible and default:
            possible.append(default)

        return possible

    def _complete_workflow(
        self,
        instance: WorkflowInstance,
        outcome: str
    ):
        """Termine le workflow."""
        instance.status = InstanceStatus.COMPLETED
        instance.completed_at = datetime.now()
        instance.outcome = outcome

        # Log
        self._add_history(
            instance.instance_id,
            "workflow_completed",
            details={"outcome": outcome}
        )

    def _create_parallel_branches(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        step: Step,
        workflow: WorkflowDefinition
    ):
        """Crée des branches parallèles."""
        # Trouver toutes les transitions sortantes
        next_steps = [
            t.to_step_id for t in workflow.transitions
            if t.from_step_id == step.step_id
        ]

        execution.status = "completed"
        execution.completed_at = datetime.now()

        # Démarrer toutes les branches
        branch_id = f"branch_{uuid4().hex[:6]}"
        for step_id in next_steps:
            branch_exec = self._execute_step(instance, step_id, workflow)
            branch_exec.is_parallel_branch = True
            branch_exec.parallel_branch_id = branch_id

        instance.current_step_ids = next_steps

    def _check_parallel_join(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        step: Step,
        workflow: WorkflowDefinition
    ):
        """Vérifie si un join parallèle peut continuer."""
        # Trouver les transitions entrantes
        incoming_steps = [
            t.from_step_id for t in workflow.transitions
            if t.to_step_id == step.step_id
        ]

        # Vérifier si toutes les branches sont terminées
        completed_branches = []
        for exec_ in instance.step_executions:
            if exec_.step_id in incoming_steps and exec_.status == "completed":
                completed_branches.append(exec_.step_id)

        if step.step_type == StepType.PARALLEL_JOIN:
            # AND join - toutes les branches doivent être terminées
            if set(completed_branches) == set(incoming_steps):
                self._complete_step(instance, execution, workflow)
            else:
                # Attendre
                execution.status = "waiting"
                instance.status = InstanceStatus.WAITING

        elif step.step_type == StepType.INCLUSIVE_JOIN:
            # OR join - au moins une branche doit être terminée
            if completed_branches:
                self._complete_step(instance, execution, workflow)

    def _schedule_timer(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        step: Step
    ):
        """Programme un timer."""
        # Dans une implémentation réelle, utiliser un scheduler
        execution.status = "waiting"
        instance.status = InstanceStatus.WAITING

        # Stocker la date de déclenchement
        if step.timer_duration_hours:
            execution.metadata["timer_triggers_at"] = (
                datetime.now() + timedelta(hours=step.timer_duration_hours)
            ).isoformat()

    def _execute_script(
        self,
        instance: WorkflowInstance,
        execution: StepExecution,
        step: Step
    ):
        """Exécute un script."""
        if not step.script_code:
            return

        if self.script_executor:
            try:
                result = self.script_executor(
                    step.script_code,
                    step.script_language,
                    instance.context
                )
                execution.output_data = {"script_result": result}
            except Exception as e:
                execution.error_message = str(e)
                execution.status = "failed"

    def _send_step_notification(
        self,
        instance: WorkflowInstance,
        step: Step
    ):
        """Envoie une notification pour l'étape."""
        if self.notification_service and step.metadata.get("notification_template"):
            self.notification_service(
                step.metadata["notification_template"],
                {
                    "instance_id": instance.instance_id,
                    "workflow_name": instance.workflow_name,
                    "context": instance.context
                }
            )

    def _execute_actions(
        self,
        actions: List[Dict[str, Any]],
        instance: WorkflowInstance
    ):
        """Exécute une liste d'actions."""
        for action in actions:
            action_type = action.get("type")
            handler = self._action_handlers.get(action_type)

            if handler:
                try:
                    handler(action, instance)
                except Exception as e:
                    self._add_history(
                        instance.instance_id,
                        "action_failed",
                        details={"action": action_type, "error": str(e)}
                    )

    def register_action_handler(
        self,
        action_type: str,
        handler: Callable
    ):
        """Enregistre un gestionnaire d'action."""
        self._action_handlers[action_type] = handler

    def _add_history(
        self,
        instance_id: str,
        event_type: str,
        step_id: Optional[str] = None,
        task_id: Optional[str] = None,
        actor: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Ajoute une entrée d'historique."""
        history = WorkflowHistory(
            history_id=f"hist_{uuid4().hex[:8]}",
            instance_id=instance_id,
            event_type=event_type,
            step_id=step_id,
            task_id=task_id,
            actor=actor,
            details=details or {}
        )

        if instance_id not in self._history:
            self._history[instance_id] = []
        self._history[instance_id].append(history)

    # =========================================================================
    # Délégation et Escalade
    # =========================================================================

    def delegate_task(
        self,
        task_id: str,
        delegated_by: str,
        delegate_to: str,
        comments: str = ""
    ) -> TaskInstance:
        """Délègue une tâche."""
        task = self._find_task(task_id)
        if not task:
            raise ValueError(f"Tâche {task_id} non trouvée")

        # Vérifier si la délégation est autorisée
        instance = self._instances.get(task.instance_id)
        workflow = self._workflows.get(instance.workflow_id)
        step = self._get_step(workflow, task.step_id)

        if not step.allow_delegation:
            raise ValueError("La délégation n'est pas autorisée pour cette étape")

        task.original_assignee = task.assigned_to
        task.assigned_to = delegate_to
        task.delegated_by = delegated_by
        task.delegated_at = datetime.now()
        task.status = TaskStatus.DELEGATED

        self._add_history(
            task.instance_id,
            "task_delegated",
            step_id=task.step_id,
            task_id=task_id,
            actor=delegated_by,
            details={"delegate_to": delegate_to, "comments": comments}
        )

        return task

    def escalate_task(
        self,
        task_id: str,
        escalate_to: str,
        reason: str
    ) -> TaskInstance:
        """Escalade une tâche."""
        task = self._find_task(task_id)
        if not task:
            raise ValueError(f"Tâche {task_id} non trouvée")

        task.original_assignee = task.assigned_to
        task.assigned_to = escalate_to
        task.escalation_level += 1
        task.status = TaskStatus.ESCALATED

        self._add_history(
            task.instance_id,
            "task_escalated",
            step_id=task.step_id,
            task_id=task_id,
            actor="system",
            details={
                "escalate_to": escalate_to,
                "reason": reason,
                "level": task.escalation_level
            }
        )

        return task

    def _find_task(self, task_id: str) -> Optional[TaskInstance]:
        """Trouve une tâche par ID."""
        for instance in self._instances.values():
            for execution in instance.step_executions:
                for task in execution.tasks:
                    if task.task_id == task_id:
                        return task
        return None

    # =========================================================================
    # Récupération et Recherche
    # =========================================================================

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Récupère une instance."""
        return self._instances.get(instance_id)

    def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """Récupère les tâches d'un utilisateur."""
        tasks = []

        for instance in self._instances.values():
            if instance.tenant_id != self.tenant_id:
                continue

            for execution in instance.step_executions:
                for task in execution.tasks:
                    if task.assigned_to != user_id:
                        continue
                    if status and task.status != status:
                        continue

                    tasks.append({
                        "task": task,
                        "instance": instance,
                        "step_name": execution.step_name
                    })

        return tasks

    def get_instance_history(
        self,
        instance_id: str
    ) -> List[WorkflowHistory]:
        """Récupère l'historique d'une instance."""
        return self._history.get(instance_id, [])

    def cancel_instance(
        self,
        instance_id: str,
        cancelled_by: str,
        reason: str
    ) -> WorkflowInstance:
        """Annule une instance de workflow."""
        instance = self._instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} non trouvée")

        instance.status = InstanceStatus.CANCELLED
        instance.completed_at = datetime.now()
        instance.outcome = "cancelled"

        # Annuler les tâches en cours
        for execution in instance.step_executions:
            for task in execution.tasks:
                if task.status in (TaskStatus.PENDING, TaskStatus.ASSIGNED,
                                   TaskStatus.IN_PROGRESS):
                    task.status = TaskStatus.CANCELLED

        self._add_history(
            instance_id,
            "workflow_cancelled",
            actor=cancelled_by,
            details={"reason": reason}
        )

        return instance


def create_workflow_service(
    tenant_id: str,
    **kwargs
) -> WorkflowService:
    """Factory pour créer un service de workflows."""
    return WorkflowService(tenant_id=tenant_id, **kwargs)
