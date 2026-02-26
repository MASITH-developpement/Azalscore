"""
Repository - Module Approval Workflow (GAP-083)

CRITIQUE: Toutes les requêtes filtrées par tenant_id.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified

from .models import (
    Workflow, ApprovalWorkflowStep as WorkflowStep, ApprovalRequest, ApprovalAction, Delegation,
    WorkflowStatus, RequestStatus, ApprovalType, ActionType
)
from .schemas import WorkflowFilters, ApprovalRequestFilters


class WorkflowRepository:
    """Repository Workflow avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(Workflow).filter(Workflow.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Workflow.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[Workflow]:
        return self._base_query().options(
            joinedload(Workflow.steps)
        ).filter(Workflow.id == id).first()

    def get_by_code(self, code: str) -> Optional[Workflow]:
        return self._base_query().filter(Workflow.code == code.upper()).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(Workflow.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(Workflow.code == code.upper())
        if exclude_id:
            query = query.filter(Workflow.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: WorkflowFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Workflow], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Workflow.name.ilike(term),
                    Workflow.code.ilike(term),
                    Workflow.description.ilike(term)
                ))
            if filters.status:
                query = query.filter(Workflow.status.in_([s.value for s in filters.status]))
            if filters.approval_type:
                query = query.filter(Workflow.approval_type.in_([t.value for t in filters.approval_type]))

        total = query.count()
        sort_col = getattr(Workflow, sort_by, Workflow.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def find_matching(
        self,
        approval_type: ApprovalType,
        amount: Optional[Decimal] = None,
        context: Dict[str, Any] = None
    ) -> Optional[Workflow]:
        """Trouver le workflow applicable."""
        query = self._base_query().filter(
            Workflow.status == WorkflowStatus.ACTIVE.value,
            Workflow.approval_type == approval_type.value
        )

        if amount is not None:
            query = query.filter(
                or_(Workflow.min_amount.is_(None), Workflow.min_amount <= amount),
                or_(Workflow.max_amount.is_(None), Workflow.max_amount >= amount)
            )

        # Retourner le plus prioritaire
        return query.order_by(desc(Workflow.priority)).first()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, str]]:
        if len(prefix) < 2:
            return []
        query = self._base_query().filter(
            Workflow.status == WorkflowStatus.ACTIVE.value
        ).filter(or_(
            Workflow.name.ilike(f"{prefix}%"),
            Workflow.code.ilike(f"{prefix}%")
        ))
        results = query.order_by(Workflow.name).limit(limit).all()
        return [
            {"id": str(w.id), "code": w.code, "name": w.name, "label": f"[{w.code}] {w.name}"}
            for w in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Workflow:
        steps_data = data.pop("steps", [])
        entity = Workflow(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.flush()

        for i, step_data in enumerate(steps_data):
            step = WorkflowStep(
                tenant_id=self.tenant_id,
                workflow_id=entity.id,
                order=i,
                created_by=created_by,
                **step_data
            )
            self.db.add(step)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: Workflow, data: Dict[str, Any], updated_by: UUID = None) -> Workflow:
        for key, value in data.items():
            if hasattr(entity, key) and key != "steps":
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_step(self, workflow: Workflow, step_data: Dict[str, Any], created_by: UUID = None) -> WorkflowStep:
        order = len(workflow.steps)
        step = WorkflowStep(
            tenant_id=self.tenant_id,
            workflow_id=workflow.id,
            order=order,
            created_by=created_by,
            **step_data
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def activate(self, entity: Workflow, updated_by: UUID = None) -> Workflow:
        if not entity.steps:
            raise ValueError("Workflow must have at least one step")
        entity.status = WorkflowStatus.ACTIVE.value
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def deactivate(self, entity: Workflow, updated_by: UUID = None) -> Workflow:
        entity.status = WorkflowStatus.INACTIVE.value
        entity.updated_by = updated_by
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: Workflow, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, entity: Workflow) -> Workflow:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        self.db.commit()
        self.db.refresh(entity)
        return entity


class ApprovalRequestRepository:
    """Repository ApprovalRequest avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(ApprovalRequest).filter(ApprovalRequest.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(ApprovalRequest.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[ApprovalRequest]:
        return self._base_query().options(
            joinedload(ApprovalRequest.actions)
        ).filter(ApprovalRequest.id == id).first()

    def get_by_number(self, number: str) -> Optional[ApprovalRequest]:
        return self._base_query().filter(ApprovalRequest.request_number == number).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(ApprovalRequest.id == id).count() > 0

    def list(
        self,
        filters: ApprovalRequestFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[ApprovalRequest], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    ApprovalRequest.request_number.ilike(term),
                    ApprovalRequest.entity_description.ilike(term),
                    ApprovalRequest.entity_number.ilike(term)
                ))
            if filters.status:
                query = query.filter(ApprovalRequest.status.in_([s.value for s in filters.status]))
            if filters.entity_type:
                query = query.filter(ApprovalRequest.entity_type == filters.entity_type)
            if filters.requester_id:
                query = query.filter(ApprovalRequest.requester_id == filters.requester_id)
            if filters.date_from:
                query = query.filter(ApprovalRequest.submitted_at >= datetime.combine(filters.date_from, datetime.min.time()))
            if filters.date_to:
                query = query.filter(ApprovalRequest.submitted_at <= datetime.combine(filters.date_to, datetime.max.time()))

        total = query.count()
        sort_col = getattr(ApprovalRequest, sort_by, ApprovalRequest.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_pending_for_user(self, user_id: UUID) -> List[ApprovalRequest]:
        """Obtenir les demandes en attente pour un utilisateur."""
        requests = self._base_query().filter(
            ApprovalRequest.status == RequestStatus.IN_PROGRESS.value
        ).all()

        pending = []
        for req in requests:
            step_statuses = req.step_statuses or []
            if req.current_step < len(step_statuses):
                current_status = step_statuses[req.current_step]
                pending_approvers = current_status.get("pending_approvers", [])
                if str(user_id) in [str(a) for a in pending_approvers]:
                    pending.append(req)

        return pending

    def get_by_entity(self, entity_type: str, entity_id: UUID) -> List[ApprovalRequest]:
        """Obtenir les demandes pour une entité."""
        return self._base_query().filter(
            ApprovalRequest.entity_type == entity_type,
            ApprovalRequest.entity_id == entity_id
        ).order_by(desc(ApprovalRequest.created_at)).all()

    def get_next_number(self) -> str:
        """Générer le prochain numéro de demande."""
        year = datetime.utcnow().year
        prefix = f"APR-{year}-"
        last = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.tenant_id == self.tenant_id,
            ApprovalRequest.request_number.like(f"{prefix}%")
        ).order_by(desc(ApprovalRequest.request_number)).first()

        if last:
            try:
                last_num = int(last.request_number.split("-")[-1])
                return f"{prefix}{last_num + 1:06d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}000001"

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ApprovalRequest:
        if "request_number" not in data:
            data["request_number"] = self.get_next_number()
        entity = ApprovalRequest(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ApprovalRequest, data: Dict[str, Any], updated_by: UUID = None) -> ApprovalRequest:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.updated_by = updated_by
        entity.version += 1
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def submit(self, entity: ApprovalRequest) -> ApprovalRequest:
        """Soumettre une demande."""
        entity.status = RequestStatus.PENDING.value
        entity.submitted_at = datetime.utcnow()

        # Activer première étape
        if entity.step_statuses:
            step_statuses = list(entity.step_statuses)
            step_statuses[0]["status"] = "in_progress"
            step_statuses[0]["started_at"] = datetime.utcnow().isoformat()
            entity.step_statuses = step_statuses
            flag_modified(entity, "step_statuses")
            entity.status = RequestStatus.IN_PROGRESS.value

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_action(
        self,
        request: ApprovalRequest,
        step_id: UUID,
        approver_id: UUID,
        approver_name: str,
        action_type: ActionType,
        comments: str = None,
        delegated_to_id: UUID = None,
        delegated_to_name: str = None,
        ip_address: str = None
    ) -> ApprovalAction:
        """Ajouter une action."""
        action = ApprovalAction(
            tenant_id=self.tenant_id,
            request_id=request.id,
            step_id=step_id,
            approver_id=approver_id,
            approver_name=approver_name,
            action_type=action_type.value,
            comments=comments,
            delegated_to_id=delegated_to_id,
            delegated_to_name=delegated_to_name,
            ip_address=ip_address
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def soft_delete(self, entity: ApprovalRequest, deleted_by: UUID = None) -> bool:
        entity.is_deleted = True
        entity.deleted_at = datetime.utcnow()
        entity.deleted_by = deleted_by
        self.db.commit()
        return True


class DelegationRepository:
    """Repository Delegation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _base_query(self):
        return self.db.query(Delegation).filter(Delegation.tenant_id == self.tenant_id)

    def get_by_id(self, id: UUID) -> Optional[Delegation]:
        return self._base_query().filter(Delegation.id == id).first()

    def get_active_for_delegator(self, delegator_id: UUID) -> List[Delegation]:
        today = date.today()
        return self._base_query().filter(
            Delegation.delegator_id == delegator_id,
            Delegation.is_active == True,
            Delegation.start_date <= today,
            Delegation.end_date >= today
        ).all()

    def get_active_for_delegate(self, delegate_id: UUID) -> List[Delegation]:
        today = date.today()
        return self._base_query().filter(
            Delegation.delegate_id == delegate_id,
            Delegation.is_active == True,
            Delegation.start_date <= today,
            Delegation.end_date >= today
        ).all()

    def find_delegator(self, delegate_id: UUID, approval_type: ApprovalType = None) -> Optional[UUID]:
        """Trouver si quelqu'un a délégué à cet utilisateur."""
        today = date.today()
        query = self._base_query().filter(
            Delegation.delegate_id == delegate_id,
            Delegation.is_active == True,
            Delegation.start_date <= today,
            Delegation.end_date >= today
        )

        delegations = query.all()
        for d in delegations:
            if not d.approval_types or (approval_type and approval_type.value in d.approval_types):
                return d.delegator_id

        return None

    def list(
        self,
        delegator_id: UUID = None,
        delegate_id: UUID = None,
        active_only: bool = True
    ) -> List[Delegation]:
        query = self._base_query()

        if delegator_id:
            query = query.filter(Delegation.delegator_id == delegator_id)
        if delegate_id:
            query = query.filter(Delegation.delegate_id == delegate_id)
        if active_only:
            today = date.today()
            query = query.filter(
                Delegation.is_active == True,
                Delegation.start_date <= today,
                Delegation.end_date >= today
            )

        return query.order_by(desc(Delegation.created_at)).all()

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Delegation:
        entity = Delegation(tenant_id=self.tenant_id, created_by=created_by, **data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def revoke(self, entity: Delegation, revoked_by: UUID = None) -> Delegation:
        entity.is_active = False
        entity.revoked_at = datetime.utcnow()
        entity.revoked_by = revoked_by
        self.db.commit()
        self.db.refresh(entity)
        return entity
