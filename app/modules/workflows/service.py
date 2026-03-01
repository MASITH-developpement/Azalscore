"""
Service de Workflows BPM - GAP-048

Gestion complete des workflows avec persistence SQLAlchemy:
- Definitions de workflows configurables
- Instances d'execution
- Etapes et transitions
- Taches et approbations
- Conditions et regles
- Historique complet

CRITIQUE: Utilise les repositories pour l'isolation multi-tenant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import (
    WorkflowDefinition,
    WorkflowInstance,
    StepExecution,
    TaskInstance,
    WorkflowHistory,
    WorkflowStep,
    WorkflowTransition,
    WorkflowStatusDB,
    InstanceStatusDB,
    StepTypeDB,
    TaskStatusDB,
    ApprovalTypeDB,
)
from .repository import (
    WorkflowDefinitionRepository,
    WorkflowInstanceRepository,
    StepExecutionRepository,
    TaskInstanceRepository,
    WorkflowHistoryRepository,
    WorkflowStepRepository,
    WorkflowTransitionRepository,
)


# ============================================================
# ENUMERATIONS LOCALES
# ============================================================

class WorkflowStatus:
    """Statuts de workflow."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class InstanceStatus:
    """Statuts d'instance."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class StepType:
    """Types d'etapes."""
    START = "start"
    END = "end"
    TASK = "task"
    APPROVAL = "approval"
    CONDITION = "condition"
    PARALLEL = "parallel"
    JOIN = "join"
    TIMER = "timer"
    NOTIFICATION = "notification"
    SCRIPT = "script"


class TaskStatus:
    """Statuts de tache."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    EXPIRED = "expired"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class StepResult:
    """Resultat d'execution d'une etape."""
    success: bool
    next_step_id: Optional[str] = None
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class WorkflowProgress:
    """Progression d'un workflow."""
    instance_id: str
    workflow_name: str
    status: str
    current_step: Optional[str] = None
    progress_percent: float = 0.0
    steps_completed: int = 0
    steps_total: int = 0
    pending_tasks: int = 0
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class WorkflowService:
    """Service de gestion des workflows avec persistence SQLAlchemy."""

    def __init__(
        self,
        db: Session,
        tenant_id: str,
        notification_service: Optional[Any] = None,
        script_executor: Optional[Callable] = None
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.notification_service = notification_service
        self.script_executor = script_executor

        # Repositories avec isolation tenant
        self.definition_repo = WorkflowDefinitionRepository(db, tenant_id)
        self.instance_repo = WorkflowInstanceRepository(db, tenant_id)
        self.step_exec_repo = StepExecutionRepository(db, tenant_id)
        self.task_repo = TaskInstanceRepository(db, tenant_id)
        self.history_repo = WorkflowHistoryRepository(db, tenant_id)
        self.step_repo = WorkflowStepRepository(db, tenant_id)
        self.transition_repo = WorkflowTransitionRepository(db, tenant_id)

        # Handlers d'etapes personnalises
        self._step_handlers: Dict[str, Callable] = {}

    # =========================================================================
    # Definitions de workflows
    # =========================================================================

    def create_workflow(
        self,
        code: str,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        created_by: Optional[str] = None,
        **kwargs
    ) -> WorkflowDefinition:
        """Cree une definition de workflow."""
        # Verifier unicite du code
        existing = self.definition_repo.get_by_code(code)
        if existing:
            raise ValueError(f"Workflow {code} existe deja")

        data = {
            "code": code,
            "name": name,
            "description": description,
            "category": category,
            "entity_type": entity_type,
            "status": WorkflowStatusDB.DRAFT,
            "version": 1,
            "created_by": created_by,
            **kwargs
        }
        return self.definition_repo.create(data)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Recupere une definition de workflow."""
        return self.definition_repo.get_by_id(workflow_id)

    def get_workflow_by_code(self, code: str) -> Optional[WorkflowDefinition]:
        """Recupere un workflow par code."""
        return self.definition_repo.get_by_code(code)

    def list_workflows(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WorkflowDefinition], int]:
        """Liste les workflows."""
        return self.definition_repo.list(
            status=status,
            category=category,
            search=search,
            page=page,
            page_size=page_size
        )

    def update_workflow(
        self,
        workflow_id: str,
        updated_by: Optional[str] = None,
        **updates
    ) -> Optional[WorkflowDefinition]:
        """Met a jour un workflow."""
        workflow = self.definition_repo.get_by_id(workflow_id)
        if not workflow:
            return None
        return self.definition_repo.update(workflow, updates, updated_by)

    def activate_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Active un workflow."""
        workflow = self.definition_repo.get_by_id(workflow_id)
        if not workflow:
            return None

        # Verifier qu'il a au moins une etape START et END
        steps = self.step_repo.list_by_workflow(workflow_id)
        has_start = any(s.step_type == StepTypeDB.START for s in steps)
        has_end = any(s.step_type == StepTypeDB.END for s in steps)

        if not has_start or not has_end:
            raise ValueError("Le workflow doit avoir au moins une etape START et END")

        return self.definition_repo.update(workflow, {"status": WorkflowStatusDB.ACTIVE})

    def archive_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Archive un workflow."""
        workflow = self.definition_repo.get_by_id(workflow_id)
        if not workflow:
            return None
        return self.definition_repo.update(workflow, {"status": WorkflowStatusDB.ARCHIVED})

    # =========================================================================
    # Etapes
    # =========================================================================

    def add_step(
        self,
        workflow_id: str,
        code: str,
        name: str,
        step_type: str,
        config: Optional[Dict[str, Any]] = None,
        position: int = 0,
        **kwargs
    ) -> WorkflowStep:
        """Ajoute une etape a un workflow."""
        workflow = self.definition_repo.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} non trouve")

        data = {
            "workflow_id": workflow_id,
            "code": code,
            "name": name,
            "step_type": step_type,
            "config": config or {},
            "position": position,
            **kwargs
        }
        return self.step_repo.create(data)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Recupere une etape."""
        return self.step_repo.get_by_id(step_id)

    def list_steps(self, workflow_id: str) -> List[WorkflowStep]:
        """Liste les etapes d'un workflow."""
        return self.step_repo.list_by_workflow(workflow_id)

    def update_step(self, step_id: str, **updates) -> Optional[WorkflowStep]:
        """Met a jour une etape."""
        step = self.step_repo.get_by_id(step_id)
        if not step:
            return None
        return self.step_repo.update(step, updates)

    def delete_step(self, step_id: str) -> bool:
        """Supprime une etape."""
        step = self.step_repo.get_by_id(step_id)
        if not step:
            return False
        return self.step_repo.delete(step)

    # =========================================================================
    # Transitions
    # =========================================================================

    def add_transition(
        self,
        workflow_id: str,
        from_step_id: str,
        to_step_id: str,
        condition: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs
    ) -> WorkflowTransition:
        """Ajoute une transition entre etapes."""
        data = {
            "workflow_id": workflow_id,
            "from_step_id": from_step_id,
            "to_step_id": to_step_id,
            "condition": condition,
            "label": label,
            **kwargs
        }
        return self.transition_repo.create(data)

    def list_transitions(self, workflow_id: str) -> List[WorkflowTransition]:
        """Liste les transitions d'un workflow."""
        return self.transition_repo.list_by_workflow(workflow_id)

    def delete_transition(self, transition_id: str) -> bool:
        """Supprime une transition."""
        transition = self.transition_repo.get_by_id(transition_id)
        if not transition:
            return False
        return self.transition_repo.delete(transition)

    # =========================================================================
    # Instances de workflow
    # =========================================================================

    def start_workflow(
        self,
        workflow_code: str,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        started_by: Optional[str] = None,
        priority: str = "normal"
    ) -> WorkflowInstance:
        """Demarre une nouvelle instance de workflow."""
        workflow = self.definition_repo.get_by_code(workflow_code)
        if not workflow:
            raise ValueError(f"Workflow {workflow_code} non trouve")

        if workflow.status != WorkflowStatusDB.ACTIVE:
            raise ValueError(f"Workflow {workflow_code} n'est pas actif")

        # Creer l'instance
        instance_data = {
            "workflow_id": str(workflow.id),
            "workflow_code": workflow.code,
            "workflow_version": workflow.version,
            "entity_id": entity_id,
            "entity_type": entity_type or workflow.entity_type,
            "context": context or {},
            "status": InstanceStatusDB.RUNNING,
            "priority": priority,
            "started_by": started_by,
            "started_at": datetime.utcnow(),
        }
        instance = self.instance_repo.create(instance_data)

        # Logger l'historique
        self._log_history(str(instance.id), "started", "Instance demarree", started_by)

        # Trouver et executer l'etape START
        steps = self.step_repo.list_by_workflow(str(workflow.id))
        start_step = next((s for s in steps if s.step_type == StepTypeDB.START), None)

        if start_step:
            self._execute_step(instance, start_step)

        return instance

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Recupere une instance."""
        return self.instance_repo.get_by_id(instance_id)

    def list_instances(
        self,
        workflow_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WorkflowInstance], int]:
        """Liste les instances."""
        return self.instance_repo.list(
            workflow_id=workflow_id,
            entity_id=entity_id,
            status=status,
            page=page,
            page_size=page_size
        )

    def get_instance_progress(self, instance_id: str) -> Optional[WorkflowProgress]:
        """Recupere la progression d'une instance."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        workflow = self.definition_repo.get_by_id(str(instance.workflow_id))
        if not workflow:
            return None

        steps = self.step_repo.list_by_workflow(str(workflow.id))
        step_execs = self.step_exec_repo.list_by_instance(instance_id)
        pending_tasks = self.task_repo.count_pending_for_instance(instance_id)

        completed = len([s for s in step_execs if s.status == "completed"])
        total = len(steps)

        return WorkflowProgress(
            instance_id=instance_id,
            workflow_name=workflow.name,
            status=instance.status.value if hasattr(instance.status, 'value') else instance.status,
            current_step=instance.current_step_id,
            progress_percent=(completed / total * 100) if total > 0 else 0,
            steps_completed=completed,
            steps_total=total,
            pending_tasks=pending_tasks,
            started_at=instance.started_at
        )

    def suspend_instance(
        self,
        instance_id: str,
        reason: Optional[str] = None,
        suspended_by: Optional[str] = None
    ) -> Optional[WorkflowInstance]:
        """Suspend une instance."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        instance = self.instance_repo.update(instance, {"status": InstanceStatusDB.SUSPENDED})
        self._log_history(instance_id, "suspended", reason, suspended_by)
        return instance

    def resume_instance(
        self,
        instance_id: str,
        resumed_by: Optional[str] = None
    ) -> Optional[WorkflowInstance]:
        """Reprend une instance suspendue."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance or instance.status != InstanceStatusDB.SUSPENDED:
            return None

        instance = self.instance_repo.update(instance, {"status": InstanceStatusDB.RUNNING})
        self._log_history(instance_id, "resumed", "Instance reprise", resumed_by)
        return instance

    def cancel_instance(
        self,
        instance_id: str,
        reason: Optional[str] = None,
        cancelled_by: Optional[str] = None
    ) -> Optional[WorkflowInstance]:
        """Annule une instance."""
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            return None

        instance = self.instance_repo.update(instance, {
            "status": InstanceStatusDB.CANCELLED,
            "completed_at": datetime.utcnow()
        })
        self._log_history(instance_id, "cancelled", reason, cancelled_by)
        return instance

    # =========================================================================
    # Taches
    # =========================================================================

    def get_pending_tasks(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TaskInstance], int]:
        """Recupere les taches en attente."""
        return self.task_repo.list_pending(
            user_id=user_id,
            role=role,
            page=page,
            page_size=page_size
        )

    def assign_task(
        self,
        task_id: str,
        assignee_id: str,
        assigned_by: Optional[str] = None
    ) -> Optional[TaskInstance]:
        """Assigne une tache a un utilisateur."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None

        task = self.task_repo.update(task, {
            "assignee_id": assignee_id,
            "assigned_at": datetime.utcnow(),
            "status": TaskStatusDB.ASSIGNED
        })

        self._log_history(
            str(task.instance_id),
            "task_assigned",
            f"Tache assignee a {assignee_id}",
            assigned_by
        )
        return task

    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        completed_by: Optional[str] = None
    ) -> Optional[TaskInstance]:
        """Complete une tache."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None

        task = self.task_repo.update(task, {
            "status": TaskStatusDB.COMPLETED,
            "result": result or {},
            "completed_at": datetime.utcnow(),
            "completed_by": completed_by
        })

        self._log_history(
            str(task.instance_id),
            "task_completed",
            f"Tache completee",
            completed_by
        )

        # Continuer le workflow
        instance = self.instance_repo.get_by_id(str(task.instance_id))
        if instance and instance.status == InstanceStatusDB.WAITING:
            self._continue_workflow(instance, result)

        return task

    def reject_task(
        self,
        task_id: str,
        reason: Optional[str] = None,
        rejected_by: Optional[str] = None
    ) -> Optional[TaskInstance]:
        """Rejette une tache."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None

        task = self.task_repo.update(task, {
            "status": TaskStatusDB.REJECTED,
            "rejection_reason": reason,
            "completed_at": datetime.utcnow()
        })

        self._log_history(
            str(task.instance_id),
            "task_rejected",
            reason,
            rejected_by
        )
        return task

    # =========================================================================
    # Execution interne
    # =========================================================================

    def _execute_step(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        input_data: Optional[Dict[str, Any]] = None
    ) -> StepResult:
        """Execute une etape de workflow."""
        # Creer l'execution
        exec_data = {
            "instance_id": str(instance.id),
            "step_id": str(step.id),
            "step_code": step.code,
            "input_data": input_data or {},
            "status": "running",
            "started_at": datetime.utcnow()
        }
        step_exec = self.step_exec_repo.create(exec_data)

        # Mettre a jour l'instance
        self.instance_repo.update(instance, {"current_step_id": str(step.id)})

        try:
            result = self._process_step(instance, step, step_exec)

            # Mettre a jour l'execution
            self.step_exec_repo.update(step_exec, {
                "status": "completed" if result.success else "failed",
                "output_data": result.output,
                "error_message": result.error,
                "completed_at": datetime.utcnow()
            })

            # Continuer vers l'etape suivante
            if result.success and result.next_step_id:
                next_step = self.step_repo.get_by_id(result.next_step_id)
                if next_step:
                    self._execute_step(instance, next_step, result.output)

            return result

        except Exception as e:
            self.step_exec_repo.update(step_exec, {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })
            return StepResult(success=False, error=str(e))

    def _process_step(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep,
        step_exec: StepExecution
    ) -> StepResult:
        """Traite une etape selon son type."""
        step_type = step.step_type.value if hasattr(step.step_type, 'value') else step.step_type

        if step_type == StepType.START:
            return self._get_next_step(instance, step)

        elif step_type == StepType.END:
            self.instance_repo.update(instance, {
                "status": InstanceStatusDB.COMPLETED,
                "completed_at": datetime.utcnow()
            })
            self._log_history(str(instance.id), "completed", "Workflow termine")
            return StepResult(success=True)

        elif step_type == StepType.TASK:
            return self._create_task(instance, step)

        elif step_type == StepType.APPROVAL:
            return self._create_approval_task(instance, step)

        elif step_type == StepType.CONDITION:
            return self._evaluate_condition(instance, step)

        elif step_type == StepType.NOTIFICATION:
            return self._send_notification(instance, step)

        elif step_type == StepType.SCRIPT:
            return self._execute_script(instance, step)

        else:
            return self._get_next_step(instance, step)

    def _get_next_step(
        self,
        instance: WorkflowInstance,
        current_step: WorkflowStep
    ) -> StepResult:
        """Determine la prochaine etape."""
        transitions = self.transition_repo.list_from_step(str(current_step.id))

        if not transitions:
            return StepResult(success=True)

        # Pour l'instant, prendre la premiere transition sans condition
        for trans in transitions:
            if not trans.condition:
                return StepResult(success=True, next_step_id=str(trans.to_step_id))

        return StepResult(success=True, next_step_id=str(transitions[0].to_step_id))

    def _create_task(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep
    ) -> StepResult:
        """Cree une tache."""
        config = step.config or {}

        task_data = {
            "instance_id": str(instance.id),
            "step_id": str(step.id),
            "name": step.name,
            "description": config.get("description"),
            "assignee_id": config.get("assignee_id"),
            "assignee_role": config.get("assignee_role"),
            "due_date": config.get("due_date"),
            "status": TaskStatusDB.PENDING,
        }
        self.task_repo.create(task_data)

        # Mettre l'instance en attente
        self.instance_repo.update(instance, {"status": InstanceStatusDB.WAITING})

        return StepResult(success=True)

    def _create_approval_task(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep
    ) -> StepResult:
        """Cree une tache d'approbation."""
        config = step.config or {}

        task_data = {
            "instance_id": str(instance.id),
            "step_id": str(step.id),
            "name": f"Approbation: {step.name}",
            "description": config.get("description"),
            "assignee_role": config.get("approver_role"),
            "approval_type": config.get("approval_type", "single"),
            "status": TaskStatusDB.PENDING,
        }
        self.task_repo.create(task_data)

        self.instance_repo.update(instance, {"status": InstanceStatusDB.WAITING})

        return StepResult(success=True)

    def _evaluate_condition(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep
    ) -> StepResult:
        """Evalue une condition."""
        config = step.config or {}
        condition = config.get("condition", "true")
        context = instance.context or {}

        # Evaluation simple
        try:
            # WARNING: eval est dangereux - utiliser un evaluateur securise en prod
            result = eval(condition, {"context": context})
            transitions = self.transition_repo.list_from_step(str(step.id))

            for trans in transitions:
                if trans.label == "true" and result:
                    return StepResult(success=True, next_step_id=str(trans.to_step_id))
                elif trans.label == "false" and not result:
                    return StepResult(success=True, next_step_id=str(trans.to_step_id))

            return StepResult(success=True)

        except Exception as e:
            return StepResult(success=False, error=f"Erreur condition: {e}")

    def _send_notification(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep
    ) -> StepResult:
        """Envoie une notification."""
        if not self.notification_service:
            return self._get_next_step(instance, step)

        config = step.config or {}
        try:
            self.notification_service.send_notification(
                template_code=config.get("template_code"),
                recipient_id=config.get("recipient_id"),
                variables=instance.context
            )
            return self._get_next_step(instance, step)
        except Exception as e:
            return StepResult(success=False, error=str(e))

    def _execute_script(
        self,
        instance: WorkflowInstance,
        step: WorkflowStep
    ) -> StepResult:
        """Execute un script."""
        if not self.script_executor:
            return self._get_next_step(instance, step)

        config = step.config or {}
        try:
            result = self.script_executor(
                script=config.get("script"),
                context=instance.context
            )
            return StepResult(
                success=True,
                output=result if isinstance(result, dict) else {"result": result},
                next_step_id=self._get_next_step(instance, step).next_step_id
            )
        except Exception as e:
            return StepResult(success=False, error=str(e))

    def _continue_workflow(
        self,
        instance: WorkflowInstance,
        task_result: Optional[Dict[str, Any]] = None
    ):
        """Continue le workflow apres completion d'une tache."""
        if not instance.current_step_id:
            return

        current_step = self.step_repo.get_by_id(instance.current_step_id)
        if not current_step:
            return

        # Mettre a jour le contexte
        context = instance.context or {}
        if task_result:
            context.update(task_result)
            self.instance_repo.update(instance, {"context": context})

        # Passer a l'etape suivante
        result = self._get_next_step(instance, current_step)
        if result.next_step_id:
            next_step = self.step_repo.get_by_id(result.next_step_id)
            if next_step:
                self.instance_repo.update(instance, {"status": InstanceStatusDB.RUNNING})
                self._execute_step(instance, next_step, context)

    def _log_history(
        self,
        instance_id: str,
        action: str,
        details: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log dans l'historique."""
        self.history_repo.create({
            "instance_id": instance_id,
            "action": action,
            "details": details,
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        })

    # =========================================================================
    # Handlers personnalises
    # =========================================================================

    def register_step_handler(
        self,
        step_type: str,
        handler: Callable[[WorkflowInstance, WorkflowStep], StepResult]
    ):
        """Enregistre un handler personnalise pour un type d'etape."""
        self._step_handlers[step_type] = handler

    # =========================================================================
    # Historique
    # =========================================================================

    def get_instance_history(self, instance_id: str) -> List[WorkflowHistory]:
        """Recupere l'historique d'une instance."""
        return self.history_repo.list_by_instance(instance_id)


# ============================================================
# FACTORY
# ============================================================

def create_workflow_service(
    db: Session,
    tenant_id: str,
    notification_service: Optional[Any] = None,
    script_executor: Optional[Callable] = None
) -> WorkflowService:
    """Cree un service de workflows."""
    return WorkflowService(
        db=db,
        tenant_id=tenant_id,
        notification_service=notification_service,
        script_executor=script_executor
    )
