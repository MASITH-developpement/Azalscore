"""
AZALS MODULE - WORKFLOWS: Repository
=====================================

Repositories SQLAlchemy pour la gestion des workflows BPM.
Conforme aux normes AZALSCORE (isolation tenant, type hints).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload

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


class WorkflowDefinitionRepository:
    """Repository pour les definitions de workflow."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WorkflowDefinition).filter(
            WorkflowDefinition.tenant_id == self.tenant_id
        )

    def get_by_id(self, workflow_id: UUID) -> Optional[WorkflowDefinition]:
        """Recupere un workflow par ID."""
        return self._base_query().filter(
            WorkflowDefinition.id == workflow_id
        ).first()

    def get_by_code(self, code: str) -> Optional[WorkflowDefinition]:
        """Recupere un workflow par code."""
        return self._base_query().filter(
            WorkflowDefinition.code == code,
            WorkflowDefinition.status == WorkflowStatusDB.ACTIVE
        ).first()

    def list(
        self,
        status: Optional[WorkflowStatusDB] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WorkflowDefinition], int]:
        """Liste les workflows avec filtres."""
        query = self._base_query()

        if status:
            query = query.filter(WorkflowDefinition.status == status)
        if category:
            query = query.filter(WorkflowDefinition.category == category)
        if search:
            query = query.filter(
                or_(
                    WorkflowDefinition.name.ilike(f"%{search}%"),
                    WorkflowDefinition.code.ilike(f"%{search}%"),
                    WorkflowDefinition.description.ilike(f"%{search}%")
                )
            )

        total = query.count()
        items = query.order_by(desc(WorkflowDefinition.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def create(self, data: Dict[str, Any], user_id: Optional[UUID] = None) -> WorkflowDefinition:
        """Cree un nouveau workflow."""
        workflow = WorkflowDefinition(
            tenant_id=self.tenant_id,
            created_by=user_id,
            **data
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def update(
        self,
        workflow: WorkflowDefinition,
        data: Dict[str, Any]
    ) -> WorkflowDefinition:
        """Met a jour un workflow."""
        for key, value in data.items():
            if hasattr(workflow, key) and value is not None:
                setattr(workflow, key, value)
        workflow.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def activate(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        """Active un workflow."""
        workflow.status = WorkflowStatusDB.ACTIVE
        workflow.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def archive(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        """Archive un workflow."""
        workflow.status = WorkflowStatusDB.ARCHIVED
        workflow.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def new_version(
        self,
        workflow: WorkflowDefinition,
        user_id: Optional[UUID] = None
    ) -> WorkflowDefinition:
        """Cree une nouvelle version d'un workflow."""
        new_workflow = WorkflowDefinition(
            tenant_id=self.tenant_id,
            name=workflow.name,
            description=workflow.description,
            code=workflow.code,
            version=workflow.version + 1,
            status=WorkflowStatusDB.DRAFT,
            steps=workflow.steps,
            transitions=workflow.transitions,
            start_step_id=workflow.start_step_id,
            end_step_ids=workflow.end_step_ids,
            variables=workflow.variables,
            input_schema=workflow.input_schema,
            output_schema=workflow.output_schema,
            triggers=workflow.triggers,
            sla_hours=workflow.sla_hours,
            category=workflow.category,
            tags=workflow.tags,
            created_by=user_id
        )
        self.db.add(new_workflow)
        self.db.commit()
        self.db.refresh(new_workflow)
        return new_workflow


class WorkflowInstanceRepository:
    """Repository pour les instances de workflow."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WorkflowInstance).filter(
            WorkflowInstance.tenant_id == self.tenant_id
        )

    def get_by_id(
        self,
        instance_id: UUID,
        with_executions: bool = False
    ) -> Optional[WorkflowInstance]:
        """Recupere une instance par ID."""
        query = self._base_query().filter(WorkflowInstance.id == instance_id)
        if with_executions:
            query = query.options(joinedload(WorkflowInstance.step_executions))
        return query.first()

    def list(
        self,
        workflow_id: Optional[UUID] = None,
        status: Optional[InstanceStatusDB] = None,
        initiated_by: Optional[UUID] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[WorkflowInstance], int]:
        """Liste les instances avec filtres."""
        query = self._base_query()

        if workflow_id:
            query = query.filter(WorkflowInstance.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowInstance.status == status)
        if initiated_by:
            query = query.filter(WorkflowInstance.initiated_by == initiated_by)
        if reference_type:
            query = query.filter(WorkflowInstance.reference_type == reference_type)
        if reference_id:
            query = query.filter(WorkflowInstance.reference_id == reference_id)
        if overdue_only:
            query = query.filter(
                WorkflowInstance.due_at < datetime.utcnow(),
                WorkflowInstance.status.in_([
                    InstanceStatusDB.RUNNING,
                    InstanceStatusDB.WAITING
                ])
            )

        total = query.count()
        items = query.order_by(desc(WorkflowInstance.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_active_for_reference(
        self,
        reference_type: str,
        reference_id: UUID
    ) -> List[WorkflowInstance]:
        """Recupere les instances actives pour une reference."""
        return self._base_query().filter(
            WorkflowInstance.reference_type == reference_type,
            WorkflowInstance.reference_id == reference_id,
            WorkflowInstance.status.in_([
                InstanceStatusDB.PENDING,
                InstanceStatusDB.RUNNING,
                InstanceStatusDB.WAITING
            ])
        ).all()

    def create(self, data: Dict[str, Any]) -> WorkflowInstance:
        """Cree une nouvelle instance."""
        instance = WorkflowInstance(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(
        self,
        instance: WorkflowInstance,
        data: Dict[str, Any]
    ) -> WorkflowInstance:
        """Met a jour une instance."""
        for key, value in data.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        instance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update_status(
        self,
        instance: WorkflowInstance,
        status: InstanceStatusDB,
        outcome: Optional[str] = None
    ) -> WorkflowInstance:
        """Met a jour le statut d'une instance."""
        instance.status = status
        if outcome:
            instance.outcome = outcome
        if status == InstanceStatusDB.COMPLETED:
            instance.completed_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update_current_steps(
        self,
        instance: WorkflowInstance,
        step_ids: List[str]
    ) -> WorkflowInstance:
        """Met a jour les etapes courantes."""
        instance.current_step_ids = step_ids
        instance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def mark_sla_breached(self, instance: WorkflowInstance) -> WorkflowInstance:
        """Marque une instance comme en depassement SLA."""
        instance.sla_breached = True
        instance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instance)
        return instance


class StepExecutionRepository:
    """Repository pour les executions d'etapes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(StepExecution).filter(
            StepExecution.tenant_id == self.tenant_id
        )

    def get_by_id(self, execution_id: UUID) -> Optional[StepExecution]:
        """Recupere une execution par ID."""
        return self._base_query().filter(
            StepExecution.id == execution_id
        ).first()

    def get_by_instance(self, instance_id: UUID) -> List[StepExecution]:
        """Recupere les executions d'une instance."""
        return self._base_query().filter(
            StepExecution.instance_id == instance_id
        ).order_by(StepExecution.created_at).all()

    def get_current(self, instance_id: UUID) -> List[StepExecution]:
        """Recupere les executions en cours d'une instance."""
        return self._base_query().filter(
            StepExecution.instance_id == instance_id,
            StepExecution.status == "pending"
        ).all()

    def create(self, data: Dict[str, Any]) -> StepExecution:
        """Cree une nouvelle execution."""
        execution = StepExecution(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update(
        self,
        execution: StepExecution,
        data: Dict[str, Any]
    ) -> StepExecution:
        """Met a jour une execution."""
        for key, value in data.items():
            if hasattr(execution, key) and value is not None:
                setattr(execution, key, value)
        execution.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def start(self, execution: StepExecution) -> StepExecution:
        """Demarre une execution."""
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        execution.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def complete(
        self,
        execution: StepExecution,
        output_data: Optional[Dict[str, Any]] = None
    ) -> StepExecution:
        """Complete une execution."""
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        if output_data:
            execution.output_data = output_data
        execution.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def fail(
        self,
        execution: StepExecution,
        error_message: str
    ) -> StepExecution:
        """Marque une execution comme echouee."""
        execution.status = "failed"
        execution.error_message = error_message
        execution.completed_at = datetime.utcnow()
        execution.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(execution)
        return execution


class TaskInstanceRepository:
    """Repository pour les taches de workflow."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(TaskInstance).filter(
            TaskInstance.tenant_id == self.tenant_id
        )

    def get_by_id(self, task_id: UUID) -> Optional[TaskInstance]:
        """Recupere une tache par ID."""
        return self._base_query().filter(
            TaskInstance.id == task_id
        ).first()

    def list(
        self,
        instance_id: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        status: Optional[TaskStatusDB] = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TaskInstance], int]:
        """Liste les taches avec filtres."""
        query = self._base_query()

        if instance_id:
            query = query.filter(TaskInstance.instance_id == instance_id)
        if assigned_to:
            query = query.filter(TaskInstance.assigned_to == assigned_to)
        if status:
            query = query.filter(TaskInstance.status == status)
        if overdue_only:
            query = query.filter(
                TaskInstance.due_at < datetime.utcnow(),
                TaskInstance.status.in_([
                    TaskStatusDB.PENDING,
                    TaskStatusDB.ASSIGNED,
                    TaskStatusDB.IN_PROGRESS
                ])
            )

        total = query.count()
        items = query.order_by(desc(TaskInstance.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def get_user_tasks(
        self,
        user_id: UUID,
        include_completed: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[TaskInstance], int]:
        """Recupere les taches d'un utilisateur."""
        query = self._base_query().filter(
            TaskInstance.assigned_to == user_id
        )

        if not include_completed:
            query = query.filter(
                TaskInstance.status.notin_([
                    TaskStatusDB.COMPLETED,
                    TaskStatusDB.CANCELLED
                ])
            )

        total = query.count()
        items = query.order_by(
            TaskInstance.due_at.asc().nullslast(),
            TaskInstance.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def get_for_escalation(self, hours_overdue: int = 24) -> List[TaskInstance]:
        """Recupere les taches a escalader."""
        cutoff = datetime.utcnow() - timedelta(hours=hours_overdue)
        return self._base_query().filter(
            TaskInstance.status.in_([
                TaskStatusDB.PENDING,
                TaskStatusDB.ASSIGNED
            ]),
            or_(
                TaskInstance.due_at < datetime.utcnow(),
                and_(
                    TaskInstance.due_at.is_(None),
                    TaskInstance.created_at < cutoff
                )
            )
        ).all()

    def create(self, data: Dict[str, Any]) -> TaskInstance:
        """Cree une nouvelle tache."""
        task = TaskInstance(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(
        self,
        task: TaskInstance,
        data: Dict[str, Any]
    ) -> TaskInstance:
        """Met a jour une tache."""
        for key, value in data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def assign(
        self,
        task: TaskInstance,
        user_id: UUID,
        role: Optional[str] = None
    ) -> TaskInstance:
        """Assigne une tache a un utilisateur."""
        task.assigned_to = user_id
        task.assigned_role = role
        task.assigned_at = datetime.utcnow()
        task.status = TaskStatusDB.ASSIGNED
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def delegate(
        self,
        task: TaskInstance,
        to_user_id: UUID,
        by_user_id: UUID
    ) -> TaskInstance:
        """Delegue une tache."""
        task.original_assignee = task.assigned_to
        task.assigned_to = to_user_id
        task.delegated_by = by_user_id
        task.delegated_at = datetime.utcnow()
        task.status = TaskStatusDB.DELEGATED
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def start(self, task: TaskInstance) -> TaskInstance:
        """Demarre une tache."""
        task.status = TaskStatusDB.IN_PROGRESS
        task.started_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def complete(
        self,
        task: TaskInstance,
        user_id: UUID,
        outcome: str,
        decision_data: Optional[Dict[str, Any]] = None,
        comments: Optional[str] = None
    ) -> TaskInstance:
        """Complete une tache."""
        task.status = TaskStatusDB.COMPLETED
        task.outcome = outcome
        task.completed_by = user_id
        task.completed_at = datetime.utcnow()
        if decision_data:
            task.decision_data = decision_data
        if comments:
            task.comments = comments
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def reject(
        self,
        task: TaskInstance,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> TaskInstance:
        """Rejette une tache."""
        task.status = TaskStatusDB.REJECTED
        task.outcome = "rejected"
        task.completed_by = user_id
        task.completed_at = datetime.utcnow()
        task.comments = reason
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def escalate(
        self,
        task: TaskInstance,
        new_assignee: Optional[UUID] = None
    ) -> TaskInstance:
        """Escalade une tache."""
        task.status = TaskStatusDB.ESCALATED
        task.escalation_level += 1
        if new_assignee:
            task.original_assignee = task.assigned_to
            task.assigned_to = new_assignee
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task


class WorkflowHistoryRepository:
    """Repository pour l'historique des workflows."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WorkflowHistory).filter(
            WorkflowHistory.tenant_id == self.tenant_id
        )

    def get_by_instance(
        self,
        instance_id: UUID,
        event_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[WorkflowHistory], int]:
        """Recupere l'historique d'une instance."""
        query = self._base_query().filter(
            WorkflowHistory.instance_id == instance_id
        )

        if event_type:
            query = query.filter(WorkflowHistory.event_type == event_type)

        total = query.count()
        items = query.order_by(WorkflowHistory.timestamp.asc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return items, total

    def add(
        self,
        instance_id: UUID,
        event_type: str,
        actor: Optional[UUID] = None,
        step_id: Optional[str] = None,
        task_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WorkflowHistory:
        """Ajoute une entree d'historique."""
        entry = WorkflowHistory(
            tenant_id=self.tenant_id,
            instance_id=instance_id,
            event_type=event_type,
            actor=actor,
            step_id=step_id,
            task_id=task_id,
            details=details or {}
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry


class WorkflowStepRepository:
    """Repository pour les etapes de workflow."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WorkflowStep).filter(
            WorkflowStep.tenant_id == self.tenant_id
        )

    def get_by_id(self, step_id: UUID) -> Optional[WorkflowStep]:
        """Recupere une etape par ID."""
        return self._base_query().filter(
            WorkflowStep.id == step_id
        ).first()

    def get_by_workflow(self, workflow_id: UUID) -> List[WorkflowStep]:
        """Recupere les etapes d'un workflow."""
        return self._base_query().filter(
            WorkflowStep.workflow_id == workflow_id
        ).order_by(WorkflowStep.position).all()

    def get_by_step_id(
        self,
        workflow_id: UUID,
        step_id: str
    ) -> Optional[WorkflowStep]:
        """Recupere une etape par workflow_id et step_id."""
        return self._base_query().filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.step_id == step_id
        ).first()

    def create(self, data: Dict[str, Any]) -> WorkflowStep:
        """Cree une nouvelle etape."""
        step = WorkflowStep(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def update(
        self,
        step: WorkflowStep,
        data: Dict[str, Any]
    ) -> WorkflowStep:
        """Met a jour une etape."""
        for key, value in data.items():
            if hasattr(step, key) and value is not None:
                setattr(step, key, value)
        step.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(step)
        return step

    def delete(self, step: WorkflowStep) -> None:
        """Supprime une etape."""
        self.db.delete(step)
        self.db.commit()


class WorkflowTransitionRepository:
    """Repository pour les transitions de workflow."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        """Query de base avec filtre tenant obligatoire."""
        return self.db.query(WorkflowTransition).filter(
            WorkflowTransition.tenant_id == self.tenant_id
        )

    def get_by_id(self, transition_id: UUID) -> Optional[WorkflowTransition]:
        """Recupere une transition par ID."""
        return self._base_query().filter(
            WorkflowTransition.id == transition_id
        ).first()

    def get_by_workflow(self, workflow_id: UUID) -> List[WorkflowTransition]:
        """Recupere les transitions d'un workflow."""
        return self._base_query().filter(
            WorkflowTransition.workflow_id == workflow_id
        ).order_by(WorkflowTransition.priority.desc()).all()

    def get_from_step(
        self,
        workflow_id: UUID,
        from_step_id: str
    ) -> List[WorkflowTransition]:
        """Recupere les transitions sortantes d'une etape."""
        return self._base_query().filter(
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.from_step_id == from_step_id
        ).order_by(WorkflowTransition.priority.desc()).all()

    def create(self, data: Dict[str, Any]) -> WorkflowTransition:
        """Cree une nouvelle transition."""
        transition = WorkflowTransition(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(transition)
        self.db.commit()
        self.db.refresh(transition)
        return transition

    def update(
        self,
        transition: WorkflowTransition,
        data: Dict[str, Any]
    ) -> WorkflowTransition:
        """Met a jour une transition."""
        for key, value in data.items():
            if hasattr(transition, key) and value is not None:
                setattr(transition, key, value)
        transition.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(transition)
        return transition

    def delete(self, transition: WorkflowTransition) -> None:
        """Supprime une transition."""
        self.db.delete(transition)
        self.db.commit()
