"""
AZALSCORE - Workflow Automation Engine
Moteur d'exécution principal des workflows
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from .evaluator import ConditionEvaluator
from .handlers import (
    ActionHandler,
    CreateRecordHandler,
    DelayHandler,
    ExecuteScriptHandler,
    HttpRequestHandler,
    LogHandler,
    SendEmailHandler,
    SendNotificationHandler,
    SetVariableHandler,
    UpdateRecordHandler,
)
from .types import (
    ActionConfig,
    ActionResult,
    ActionType,
    ApprovalConfig,
    ApprovalRequest,
    ApprovalStatus,
    Condition,
    ConditionGroup,
    ConditionOperator,
    ExecutionStatus,
    ScheduledWorkflow,
    TriggerType,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Moteur d'exécution de workflows."""

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._scheduled_workflows: dict[str, ScheduledWorkflow] = {}
        self._event_subscriptions: dict[str, list[str]] = defaultdict(list)

        self._action_handlers: dict[ActionType, ActionHandler] = {
            ActionType.SEND_EMAIL: SendEmailHandler(),
            ActionType.SEND_NOTIFICATION: SendNotificationHandler(),
            ActionType.UPDATE_RECORD: UpdateRecordHandler(),
            ActionType.CREATE_RECORD: CreateRecordHandler(),
            ActionType.HTTP_REQUEST: HttpRequestHandler(),
            ActionType.EXECUTE_SCRIPT: ExecuteScriptHandler(),
            ActionType.DELAY: DelayHandler(),
            ActionType.SET_VARIABLE: SetVariableHandler(),
            ActionType.LOG: LogHandler(),
        }

        self._custom_handlers: dict[str, Callable] = {}
        self._entity_loaders: dict[str, Callable] = {}

    # =========================================================================
    # WORKFLOW MANAGEMENT
    # =========================================================================

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Enregistre un workflow."""
        self._workflows[workflow.id] = workflow

        for trigger in workflow.triggers:
            if trigger.type == TriggerType.EVENT and trigger.event_name:
                self._event_subscriptions[trigger.event_name].append(workflow.id)
            elif trigger.type == TriggerType.SCHEDULED and trigger.schedule:
                self._create_schedule(workflow, trigger)

        logger.info(f"Workflow enregistré: {workflow.id} - {workflow.name}")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Récupère un workflow par son ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        tenant_id: str = None,
        status: WorkflowStatus = None
    ) -> list[WorkflowDefinition]:
        """Liste les workflows."""
        workflows = list(self._workflows.values())

        if tenant_id:
            workflows = [w for w in workflows if w.tenant_id == tenant_id]
        if status:
            workflows = [w for w in workflows if w.status == status]

        return workflows

    def activate_workflow(self, workflow_id: str) -> bool:
        """Active un workflow."""
        workflow = self._workflows.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.ACTIVE
            workflow.updated_at = datetime.utcnow()
            return True
        return False

    def pause_workflow(self, workflow_id: str) -> bool:
        """Met en pause un workflow."""
        workflow = self._workflows.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.PAUSED
            workflow.updated_at = datetime.utcnow()
            return True
        return False

    def register_entity_loader(self, entity_type: str, loader: Callable) -> None:
        """Enregistre un loader d'entité."""
        self._entity_loaders[entity_type] = loader

    def register_custom_handler(self, action_name: str, handler: Callable) -> None:
        """Enregistre un handler d'action personnalisé."""
        self._custom_handlers[action_name] = handler

    # =========================================================================
    # EVENT TRIGGERING
    # =========================================================================

    async def trigger_event(
        self,
        event_name: str,
        event_data: dict,
        tenant_id: str
    ) -> list[str]:
        """Déclenche un événement et lance les workflows associés."""
        workflow_ids = self._event_subscriptions.get(event_name, [])
        execution_ids = []

        for workflow_id in workflow_ids:
            workflow = self._workflows.get(workflow_id)
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                continue
            if workflow.tenant_id != tenant_id:
                continue

            for trigger in workflow.triggers:
                if trigger.type == TriggerType.EVENT and trigger.event_name == event_name:
                    if trigger.conditions:
                        if not ConditionEvaluator.evaluate_group(
                            trigger.conditions, event_data
                        ):
                            continue

                    execution_id = await self.start_execution(
                        workflow_id=workflow_id,
                        trigger_type=TriggerType.EVENT,
                        trigger_data={"event_name": event_name, **event_data},
                        tenant_id=tenant_id
                    )
                    execution_ids.append(execution_id)

        return execution_ids

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def start_execution(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        trigger_data: dict,
        tenant_id: str,
        entity_type: str = None,
        entity_id: str = None,
        input_variables: dict = None,
        parent_execution_id: str = None
    ) -> str:
        """Démarre l'exécution d'un workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow non trouvé: {workflow_id}")

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow non actif: {workflow_id}")

        execution_id = str(uuid.uuid4())

        # Initialiser les variables
        variables = {}
        for var in workflow.variables:
            if var.is_input and input_variables and var.name in input_variables:
                variables[var.name] = input_variables[var.name]
            elif var.value is not None:
                variables[var.name] = var.value

        # Variables système
        variables["__trigger_data__"] = trigger_data
        variables["__entity_type__"] = entity_type
        variables["__entity_id__"] = entity_id
        variables["__execution_id__"] = execution_id
        variables["__workflow_id__"] = workflow_id
        variables["__tenant_id__"] = tenant_id

        # Charger l'entité si disponible
        if entity_type and entity_id and entity_type in self._entity_loaders:
            try:
                entity_data = await self._entity_loaders[entity_type](
                    entity_id, tenant_id
                )
                variables["entity"] = entity_data
            except Exception as e:
                logger.warning(f"Erreur chargement entité: {e}")

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            workflow_version=workflow.version,
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            entity_type=entity_type,
            entity_id=entity_id,
            status=ExecutionStatus.PENDING,
            current_action_id=None,
            variables=variables,
            action_results=[],
            started_at=datetime.utcnow(),
            completed_at=None,
            parent_execution_id=parent_execution_id
        )

        self._executions[execution_id] = execution

        # Lancer l'exécution en arrière-plan
        asyncio.create_task(self._run_execution(execution, workflow))

        logger.info(f"Exécution démarrée: {execution_id} pour workflow {workflow_id}")
        return execution_id

    async def _run_execution(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition
    ) -> None:
        """Exécute le workflow."""
        execution.status = ExecutionStatus.RUNNING

        try:
            if not workflow.actions:
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                return

            current_action = workflow.actions[0]
            action_map = {a.id: a for a in workflow.actions}

            while current_action:
                execution.current_action_id = current_action.id

                # Vérifier les conditions de l'action
                if current_action.conditions:
                    if not ConditionEvaluator.evaluate_group(
                        current_action.conditions,
                        execution.variables
                    ):
                        if current_action.next_action_id:
                            current_action = action_map.get(current_action.next_action_id)
                        else:
                            current_action = None
                        continue

                # Exécuter l'action
                result = await self._execute_action(current_action, execution, action_map)
                execution.action_results.append(result)

                # Gérer les erreurs
                if result.status == ExecutionStatus.FAILED:
                    if current_action.on_error == "continue":
                        pass
                    elif current_action.on_error == "skip":
                        if current_action.next_action_id:
                            current_action = action_map.get(current_action.next_action_id)
                        else:
                            current_action = None
                        continue
                    else:
                        execution.status = ExecutionStatus.FAILED
                        execution.error = result.error
                        break

                # Attente d'approbation
                if result.status == ExecutionStatus.WAITING:
                    execution.status = ExecutionStatus.WAITING
                    return

                # Déterminer la prochaine action
                if current_action.type == ActionType.CONDITION:
                    condition_result = result.output.get("result", False) if result.output else False
                    if condition_result and current_action.on_true_action_id:
                        current_action = action_map.get(current_action.on_true_action_id)
                    elif not condition_result and current_action.on_false_action_id:
                        current_action = action_map.get(current_action.on_false_action_id)
                    else:
                        current_action = None
                elif current_action.next_action_id:
                    current_action = action_map.get(current_action.next_action_id)
                else:
                    idx = workflow.actions.index(current_action)
                    if idx + 1 < len(workflow.actions):
                        current_action = workflow.actions[idx + 1]
                    else:
                        current_action = None

            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            logger.exception(f"Erreur exécution workflow: {e}")

        finally:
            if execution.status not in (ExecutionStatus.WAITING,):
                execution.completed_at = datetime.utcnow()

    async def _execute_action(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> ActionResult:
        """Exécute une action."""
        started_at = datetime.utcnow()

        try:
            if action.type == ActionType.CONDITION:
                output, error = await self._execute_condition(action, execution)
            elif action.type == ActionType.APPROVAL:
                output, error = await self._execute_approval(action, execution)
                if error == "__WAITING__":
                    return ActionResult(
                        action_id=action.id,
                        status=ExecutionStatus.WAITING,
                        started_at=started_at,
                        completed_at=None,
                        output=output
                    )
            elif action.type == ActionType.PARALLEL:
                output, error = await self._execute_parallel(action, execution, action_map)
            elif action.type == ActionType.LOOP:
                output, error = await self._execute_loop(action, execution, action_map)
            elif action.type == ActionType.CALL_WORKFLOW:
                output, error = await self._execute_call_workflow(action, execution)
            else:
                handler = self._action_handlers.get(action.type)
                if not handler:
                    custom_handler = self._custom_handlers.get(action.type.value)
                    if custom_handler:
                        output = await custom_handler(action, execution.variables)
                        error = None
                    else:
                        raise ValueError(f"Handler non trouvé pour {action.type}")
                else:
                    output, error = await handler.execute(
                        action,
                        {"execution_id": execution.id, "tenant_id": execution.tenant_id},
                        execution.variables
                    )

            # Sauvegarder l'output
            if output and isinstance(output, dict):
                execution.variables[f"action_{action.id}_output"] = output

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ActionResult(
                action_id=action.id,
                status=ExecutionStatus.COMPLETED if not error else ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                output=output,
                error=error,
                duration_ms=duration_ms
            )

        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ActionResult(
                action_id=action.id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                error=str(e),
                duration_ms=duration_ms
            )

    async def _execute_condition(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Évalue une condition."""
        params = action.parameters
        conditions = params.get("conditions", [])
        logical_operator = params.get("logical_operator", "AND")

        condition_list = []
        for c in conditions:
            condition_list.append(Condition(
                field=c["field"],
                operator=ConditionOperator(c["operator"]),
                value=c["value"]
            ))

        group = ConditionGroup(conditions=condition_list, logical_operator=logical_operator)
        result = ConditionEvaluator.evaluate_group(group, execution.variables)

        return {"result": result}, None

    async def _execute_approval(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Crée une demande d'approbation."""
        params = action.parameters
        approval_config = ApprovalConfig(
            approvers=params.get("approvers", []),
            approval_type=params.get("approval_type", "any"),
            min_approvals=params.get("min_approvals", 1),
            escalation_timeout_hours=params.get("escalation_timeout_hours", 24),
            escalation_to=params.get("escalation_to"),
            reminder_hours=params.get("reminder_hours", [4, 12]),
            allow_delegation=params.get("allow_delegation", False),
            require_comment=params.get("require_comment", False)
        )

        # Vérifier si demande existante
        existing_request = None
        for req in self._approval_requests.values():
            if req.execution_id == execution.id and req.action_id == action.id:
                existing_request = req
                break

        if existing_request:
            if existing_request.status == ApprovalStatus.APPROVED:
                return {"approval_status": "approved", "decisions": existing_request.decisions}, None
            elif existing_request.status == ApprovalStatus.REJECTED:
                return {"approval_status": "rejected", "decisions": existing_request.decisions}, "Approbation rejetée"
            else:
                return {"approval_id": existing_request.id, "status": "pending"}, "__WAITING__"

        # Créer nouvelle demande
        request_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=approval_config.escalation_timeout_hours)

        approval_request = ApprovalRequest(
            id=request_id,
            execution_id=execution.id,
            action_id=action.id,
            tenant_id=execution.tenant_id,
            approvers=approval_config.approvers,
            approval_config=approval_config,
            entity_type=execution.entity_type or "",
            entity_id=execution.entity_id or "",
            entity_data=execution.variables.get("entity", {}),
            status=ApprovalStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

        self._approval_requests[request_id] = approval_request
        logger.info(f"Demande d'approbation créée: {request_id}")

        return {"approval_id": request_id, "status": "pending"}, "__WAITING__"

    async def _execute_parallel(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> tuple[Any, Optional[str]]:
        """Exécute des actions en parallèle."""
        params = action.parameters
        action_ids = params.get("action_ids", [])
        wait_all = params.get("wait_all", True)

        tasks = []
        for action_id in action_ids:
            sub_action = action_map.get(action_id)
            if sub_action:
                tasks.append(self._execute_action(sub_action, execution, action_map))

        if wait_all:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            done, pending = await asyncio.wait(
                [asyncio.create_task(t) for t in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            results = [t.result() for t in done]

        output = {"results": []}
        errors = []
        for r in results:
            if isinstance(r, ActionResult):
                output["results"].append({
                    "action_id": r.action_id,
                    "status": r.status.value,
                    "output": r.output
                })
                if r.error:
                    errors.append(r.error)
            elif isinstance(r, Exception):
                errors.append(str(r))

        return output, "; ".join(errors) if errors else None

    async def _execute_loop(
        self,
        action: ActionConfig,
        execution: WorkflowExecution,
        action_map: dict[str, ActionConfig]
    ) -> tuple[Any, Optional[str]]:
        """Exécute une boucle."""
        params = action.parameters
        collection_var = params.get("collection")
        item_var = params.get("item_variable", "item")
        index_var = params.get("index_variable", "index")
        action_ids = params.get("action_ids", [])
        max_iterations = params.get("max_iterations", 1000)

        collection = execution.variables.get(collection_var, [])
        if not isinstance(collection, list):
            collection = list(collection) if collection else []

        results = []
        for idx, item in enumerate(collection[:max_iterations]):
            execution.variables[item_var] = item
            execution.variables[index_var] = idx

            for action_id in action_ids:
                sub_action = action_map.get(action_id)
                if sub_action:
                    result = await self._execute_action(sub_action, execution, action_map)
                    results.append({
                        "iteration": idx,
                        "action_id": action_id,
                        "status": result.status.value,
                        "output": result.output
                    })

        return {"iterations": len(collection), "results": results}, None

    async def _execute_call_workflow(
        self,
        action: ActionConfig,
        execution: WorkflowExecution
    ) -> tuple[Any, Optional[str]]:
        """Appelle un sous-workflow."""
        params = action.parameters
        workflow_id = params.get("workflow_id")
        input_mapping = params.get("input_mapping", {})
        wait_completion = params.get("wait_completion", True)

        input_variables = {}
        for target_var, source_expr in input_mapping.items():
            if source_expr.startswith("${") and source_expr.endswith("}"):
                var_name = source_expr[2:-1]
                input_variables[target_var] = execution.variables.get(var_name)
            else:
                input_variables[target_var] = source_expr

        sub_execution_id = await self.start_execution(
            workflow_id=workflow_id,
            trigger_type=TriggerType.MANUAL,
            trigger_data={"parent_action_id": action.id},
            tenant_id=execution.tenant_id,
            input_variables=input_variables,
            parent_execution_id=execution.id
        )

        if wait_completion:
            while True:
                sub_execution = self._executions.get(sub_execution_id)
                if sub_execution and sub_execution.status in (
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.CANCELLED
                ):
                    break
                await asyncio.sleep(0.5)

            sub_execution = self._executions.get(sub_execution_id)
            if sub_execution.status == ExecutionStatus.FAILED:
                return None, sub_execution.error

            return {
                "execution_id": sub_execution_id,
                "status": sub_execution.status.value,
                "variables": sub_execution.variables
            }, None

        return {"execution_id": sub_execution_id, "status": "started"}, None

    # =========================================================================
    # APPROVAL MANAGEMENT
    # =========================================================================

    async def process_approval(
        self,
        request_id: str,
        user_id: str,
        approved: bool,
        comment: str = ""
    ) -> bool:
        """Traite une décision d'approbation."""
        request = self._approval_requests.get(request_id)
        if not request:
            return False

        if user_id not in request.approvers:
            return False

        if request.status != ApprovalStatus.PENDING:
            return False

        decision = {
            "user_id": user_id,
            "approved": approved,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        }
        request.decisions.append(decision)

        if comment:
            request.comments.append({
                "user_id": user_id,
                "comment": comment,
                "timestamp": datetime.utcnow().isoformat()
            })

        if not approved:
            request.status = ApprovalStatus.REJECTED
        else:
            if request.approval_config.approval_type == "any":
                request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "all":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count >= len(request.approvers):
                    request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "majority":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count > len(request.approvers) / 2:
                    request.status = ApprovalStatus.APPROVED
            elif request.approval_config.approval_type == "threshold":
                approved_count = sum(1 for d in request.decisions if d["approved"])
                if approved_count >= request.approval_config.min_approvals:
                    request.status = ApprovalStatus.APPROVED

        # Reprendre l'exécution si décision finale
        if request.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            execution = self._executions.get(request.execution_id)
            if execution and execution.status == ExecutionStatus.WAITING:
                workflow = self._workflows.get(execution.workflow_id)
                if workflow:
                    asyncio.create_task(self._run_execution(execution, workflow))

        return True

    def get_pending_approvals(
        self,
        user_id: str,
        tenant_id: str = None
    ) -> list[ApprovalRequest]:
        """Récupère les approbations en attente pour un utilisateur."""
        pending = []
        for request in self._approval_requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue
            if user_id not in request.approvers:
                continue
            if tenant_id and request.tenant_id != tenant_id:
                continue

            already_decided = any(d["user_id"] == user_id for d in request.decisions)
            if already_decided:
                continue

            pending.append(request)

        return sorted(pending, key=lambda x: x.created_at, reverse=True)

    # =========================================================================
    # EXECUTION MANAGEMENT
    # =========================================================================

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Récupère une exécution par son ID."""
        return self._executions.get(execution_id)

    def get_executions(
        self,
        workflow_id: str = None,
        tenant_id: str = None,
        status: ExecutionStatus = None,
        limit: int = 100
    ) -> list[WorkflowExecution]:
        """Liste les exécutions."""
        executions = list(self._executions.values())

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        if tenant_id:
            executions = [e for e in executions if e.tenant_id == tenant_id]
        if status:
            executions = [e for e in executions if e.status == status]

        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]

    async def cancel_execution(self, execution_id: str, reason: str = "") -> bool:
        """Annule une exécution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED
        ):
            return False

        execution.status = ExecutionStatus.CANCELLED
        execution.error = reason or "Annulé"
        execution.completed_at = datetime.utcnow()

        return True

    # =========================================================================
    # SCHEDULING
    # =========================================================================

    def _create_schedule(self, workflow: WorkflowDefinition, trigger) -> None:
        """Crée un planning pour un workflow."""
        schedule_id = str(uuid.uuid4())
        next_run = self._calculate_next_run(trigger.schedule)

        scheduled = ScheduledWorkflow(
            id=schedule_id,
            workflow_id=workflow.id,
            tenant_id=workflow.tenant_id,
            schedule=trigger.schedule,
            next_run_at=next_run,
            last_run_at=None,
            last_run_status=None,
            is_active=True,
            created_at=datetime.utcnow()
        )

        self._scheduled_workflows[schedule_id] = scheduled

    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calcule la prochaine exécution (format cron simplifié)."""
        now = datetime.utcnow()

        if schedule.startswith("@"):
            shortcuts = {
                "@hourly": timedelta(hours=1),
                "@daily": timedelta(days=1),
                "@weekly": timedelta(weeks=1),
                "@monthly": timedelta(days=30),
            }
            delta = shortcuts.get(schedule, timedelta(hours=1))
            return now + delta

        return now + timedelta(hours=1)

    async def run_scheduled_workflows(self) -> list[str]:
        """Exécute les workflows planifiés."""
        now = datetime.utcnow()
        execution_ids = []

        for scheduled in self._scheduled_workflows.values():
            if not scheduled.is_active:
                continue
            if scheduled.next_run_at > now:
                continue

            workflow = self._workflows.get(scheduled.workflow_id)
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                continue

            try:
                execution_id = await self.start_execution(
                    workflow_id=scheduled.workflow_id,
                    trigger_type=TriggerType.SCHEDULED,
                    trigger_data={
                        "schedule_id": scheduled.id,
                        "schedule": scheduled.schedule
                    },
                    tenant_id=scheduled.tenant_id,
                    input_variables=scheduled.input_variables
                )
                execution_ids.append(execution_id)

                scheduled.last_run_at = now
                scheduled.next_run_at = self._calculate_next_run(scheduled.schedule)

            except Exception as e:
                logger.error(f"Erreur exécution planifiée: {e}")
                scheduled.last_run_status = ExecutionStatus.FAILED

        return execution_ids


# Instance globale
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Retourne l'instance du moteur de workflow."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
