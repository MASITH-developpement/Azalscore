"""
Repository - Module Commissions (GAP-041)

CRITIQUE: Toutes les requetes filtrees par tenant_id.
Utilise _base_query() pour garantir l'isolation multi-tenant.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, extract
from sqlalchemy.orm import Session, joinedload

from .models import (
    CommissionPlan, CommissionTier, CommissionAccelerator,
    CommissionAssignment, SalesTeamMember,
    CommissionTransaction, CommissionCalculation,
    CommissionPeriod, CommissionStatement,
    CommissionAdjustment, CommissionClawback,
    CommissionWorkflow, CommissionAuditLog,
    PlanStatus, CommissionStatus, WorkflowStatus
)
from .schemas import (
    PlanFilters, CalculationFilters, TransactionFilters
)


class CommissionPlanRepository:
    """Repository CommissionPlan avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base avec filtrage tenant obligatoire."""
        query = self.db.query(CommissionPlan).filter(
            CommissionPlan.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(CommissionPlan.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[CommissionPlan]:
        return self._base_query().options(
            joinedload(CommissionPlan.tiers),
            joinedload(CommissionPlan.accelerators)
        ).filter(CommissionPlan.id == id).first()

    def get_by_code(self, code: str) -> Optional[CommissionPlan]:
        return self._base_query().filter(
            CommissionPlan.code == code.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        return self._base_query().filter(CommissionPlan.id == id).count() > 0

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(CommissionPlan.code == code.upper())
        if exclude_id:
            query = query.filter(CommissionPlan.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        filters: PlanFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[CommissionPlan], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    CommissionPlan.name.ilike(term),
                    CommissionPlan.code.ilike(term),
                    CommissionPlan.description.ilike(term)
                ))
            if filters.status:
                query = query.filter(
                    CommissionPlan.status.in_([s.value for s in filters.status])
                )
            if filters.basis:
                query = query.filter(
                    CommissionPlan.basis.in_([b.value for b in filters.basis])
                )
            if filters.effective_date:
                query = query.filter(
                    CommissionPlan.effective_from <= filters.effective_date,
                    or_(
                        CommissionPlan.effective_to.is_(None),
                        CommissionPlan.effective_to >= filters.effective_date
                    )
                )
            if not filters.include_expired:
                today = date.today()
                query = query.filter(
                    or_(
                        CommissionPlan.effective_to.is_(None),
                        CommissionPlan.effective_to >= today
                    )
                )

        total = query.count()

        sort_col = getattr(CommissionPlan, sort_by, CommissionPlan.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_active_plans(self, effective_date: date = None) -> List[CommissionPlan]:
        """Recupere les plans actifs a une date donnee."""
        effective_date = effective_date or date.today()
        return self._base_query().filter(
            CommissionPlan.status == PlanStatus.ACTIVE.value,
            CommissionPlan.effective_from <= effective_date,
            or_(
                CommissionPlan.effective_to.is_(None),
                CommissionPlan.effective_to >= effective_date
            )
        ).order_by(CommissionPlan.priority).all()

    def get_plans_for_employee(
        self,
        employee_id: UUID,
        effective_date: date = None
    ) -> List[CommissionPlan]:
        """Recupere les plans assignes a un employe."""
        effective_date = effective_date or date.today()

        # Sous-requete pour les assignments actifs
        assignment_subq = self.db.query(CommissionAssignment.plan_id).filter(
            CommissionAssignment.tenant_id == self.tenant_id,
            CommissionAssignment.assignee_id == employee_id,
            CommissionAssignment.is_active == True,
            CommissionAssignment.effective_from <= effective_date,
            or_(
                CommissionAssignment.effective_to.is_(None),
                CommissionAssignment.effective_to >= effective_date
            )
        ).subquery()

        return self._base_query().filter(
            CommissionPlan.id.in_(assignment_subq),
            CommissionPlan.status == PlanStatus.ACTIVE.value
        ).order_by(CommissionPlan.priority).all()

    def get_next_code(self, prefix: str = "PLAN") -> str:
        """Generer le prochain code."""
        last = self.db.query(CommissionPlan).filter(
            CommissionPlan.tenant_id == self.tenant_id,
            CommissionPlan.code.like(f"{prefix}-%")
        ).order_by(desc(CommissionPlan.code)).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                return f"{prefix}-{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}-0001"

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> CommissionPlan:
        tiers_data = data.pop("tiers", [])
        accelerators_data = data.pop("accelerators", [])

        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code()

        plan = CommissionPlan(
            tenant_id=self.tenant_id,
            created_by=created_by,
            status=PlanStatus.DRAFT.value,
            **data
        )
        self.db.add(plan)
        self.db.flush()

        # Ajouter les paliers
        for tier_data in tiers_data:
            tier = CommissionTier(
                tenant_id=self.tenant_id,
                plan_id=plan.id,
                **tier_data
            )
            self.db.add(tier)

        # Ajouter les accelerateurs
        for acc_data in accelerators_data:
            acc = CommissionAccelerator(
                tenant_id=self.tenant_id,
                plan_id=plan.id,
                **acc_data
            )
            self.db.add(acc)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update(
        self,
        plan: CommissionPlan,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> CommissionPlan:
        for key, value in data.items():
            if hasattr(plan, key) and key not in ["tiers", "accelerators"]:
                setattr(plan, key, value)

        plan.updated_by = updated_by
        plan.version += 1
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def activate(self, plan: CommissionPlan, approved_by: UUID = None) -> CommissionPlan:
        """Active un plan."""
        if plan.status not in [PlanStatus.DRAFT.value, PlanStatus.SUSPENDED.value]:
            raise ValueError(f"Plan ne peut etre active depuis l'etat {plan.status}")

        # Verifier qu'il y a au moins un palier
        if not plan.tiers:
            raise ValueError("Le plan doit avoir au moins un palier")

        plan.status = PlanStatus.ACTIVE.value
        plan.approved_at = datetime.utcnow()
        plan.approved_by = approved_by
        plan.version += 1
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def suspend(self, plan: CommissionPlan) -> CommissionPlan:
        """Suspend un plan."""
        if plan.status != PlanStatus.ACTIVE.value:
            raise ValueError("Seul un plan actif peut etre suspendu")

        plan.status = PlanStatus.SUSPENDED.value
        plan.version += 1
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def archive(self, plan: CommissionPlan) -> CommissionPlan:
        """Archive un plan."""
        plan.status = PlanStatus.ARCHIVED.value
        plan.version += 1
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def soft_delete(self, plan: CommissionPlan, deleted_by: UUID = None) -> bool:
        plan.is_deleted = True
        plan.deleted_at = datetime.utcnow()
        plan.deleted_by = deleted_by
        self.db.commit()
        return True

    def restore(self, plan: CommissionPlan) -> CommissionPlan:
        plan.is_deleted = False
        plan.deleted_at = None
        plan.deleted_by = None
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def add_tier(
        self,
        plan: CommissionPlan,
        tier_data: Dict[str, Any]
    ) -> CommissionTier:
        tier = CommissionTier(
            tenant_id=self.tenant_id,
            plan_id=plan.id,
            **tier_data
        )
        self.db.add(tier)
        plan.version += 1
        self.db.commit()
        self.db.refresh(tier)
        return tier

    def update_tier(
        self,
        tier: CommissionTier,
        data: Dict[str, Any]
    ) -> CommissionTier:
        for key, value in data.items():
            if hasattr(tier, key):
                setattr(tier, key, value)
        self.db.commit()
        self.db.refresh(tier)
        return tier

    def delete_tier(self, tier: CommissionTier) -> bool:
        self.db.delete(tier)
        self.db.commit()
        return True


class CommissionAssignmentRepository:
    """Repository CommissionAssignment avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(CommissionAssignment).filter(
            CommissionAssignment.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[CommissionAssignment]:
        return self._base_query().filter(CommissionAssignment.id == id).first()

    def get_by_assignee(
        self,
        assignee_id: UUID,
        effective_date: date = None
    ) -> List[CommissionAssignment]:
        effective_date = effective_date or date.today()
        return self._base_query().filter(
            CommissionAssignment.assignee_id == assignee_id,
            CommissionAssignment.is_active == True,
            CommissionAssignment.effective_from <= effective_date,
            or_(
                CommissionAssignment.effective_to.is_(None),
                CommissionAssignment.effective_to >= effective_date
            )
        ).all()

    def get_by_plan(self, plan_id: UUID) -> List[CommissionAssignment]:
        return self._base_query().filter(
            CommissionAssignment.plan_id == plan_id,
            CommissionAssignment.is_active == True
        ).all()

    def exists_for_period(
        self,
        assignee_id: UUID,
        plan_id: UUID,
        effective_from: date,
        effective_to: date = None,
        exclude_id: UUID = None
    ) -> bool:
        """Verifie s'il existe un chevauchement."""
        query = self._base_query().filter(
            CommissionAssignment.assignee_id == assignee_id,
            CommissionAssignment.plan_id == plan_id,
            CommissionAssignment.is_active == True
        )

        if exclude_id:
            query = query.filter(CommissionAssignment.id != exclude_id)

        # Verifier chevauchement
        if effective_to:
            query = query.filter(
                CommissionAssignment.effective_from <= effective_to,
                or_(
                    CommissionAssignment.effective_to.is_(None),
                    CommissionAssignment.effective_to >= effective_from
                )
            )
        else:
            query = query.filter(
                or_(
                    CommissionAssignment.effective_to.is_(None),
                    CommissionAssignment.effective_to >= effective_from
                )
            )

        return query.count() > 0

    def create(
        self,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> CommissionAssignment:
        assignment = CommissionAssignment(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def update(
        self,
        assignment: CommissionAssignment,
        data: Dict[str, Any]
    ) -> CommissionAssignment:
        for key, value in data.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def deactivate(self, assignment: CommissionAssignment) -> bool:
        assignment.is_active = False
        assignment.effective_to = date.today()
        self.db.commit()
        return True


class SalesTeamMemberRepository:
    """Repository SalesTeamMember avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(SalesTeamMember).filter(
            SalesTeamMember.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[SalesTeamMember]:
        return self._base_query().filter(SalesTeamMember.id == id).first()

    def get_by_employee_id(self, employee_id: UUID) -> Optional[SalesTeamMember]:
        return self._base_query().filter(
            SalesTeamMember.employee_id == employee_id,
            SalesTeamMember.is_active == True
        ).first()

    def get_subordinates(self, manager_id: UUID) -> List[SalesTeamMember]:
        return self._base_query().filter(
            SalesTeamMember.parent_id == manager_id,
            SalesTeamMember.is_active == True
        ).all()

    def get_all_subordinates_recursive(
        self,
        manager_id: UUID,
        max_depth: int = 10
    ) -> List[SalesTeamMember]:
        """Recupere tous les subordonnes de maniere recursive."""
        all_subordinates = []

        def _get_subs(parent_id: UUID, depth: int):
            if depth > max_depth:
                return
            subs = self.get_subordinates(parent_id)
            for sub in subs:
                all_subordinates.append(sub)
                _get_subs(sub.id, depth + 1)

        _get_subs(manager_id, 0)
        return all_subordinates

    def get_team_members(self, team_id: UUID) -> List[SalesTeamMember]:
        return self._base_query().filter(
            SalesTeamMember.team_id == team_id,
            SalesTeamMember.is_active == True
        ).all()

    def list_active(self) -> List[SalesTeamMember]:
        return self._base_query().filter(
            SalesTeamMember.is_active == True
        ).order_by(SalesTeamMember.employee_name).all()

    def create(
        self,
        data: Dict[str, Any]
    ) -> SalesTeamMember:
        member = SalesTeamMember(tenant_id=self.tenant_id, **data)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update(
        self,
        member: SalesTeamMember,
        data: Dict[str, Any]
    ) -> SalesTeamMember:
        for key, value in data.items():
            if hasattr(member, key):
                setattr(member, key, value)
        self.db.commit()
        self.db.refresh(member)
        return member


class CommissionTransactionRepository:
    """Repository CommissionTransaction avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(CommissionTransaction).filter(
            CommissionTransaction.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(CommissionTransaction.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[CommissionTransaction]:
        return self._base_query().filter(CommissionTransaction.id == id).first()

    def get_by_source(
        self,
        source_type: str,
        source_id: UUID
    ) -> Optional[CommissionTransaction]:
        return self._base_query().filter(
            CommissionTransaction.source_type == source_type,
            CommissionTransaction.source_id == source_id
        ).first()

    def list(
        self,
        filters: TransactionFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "source_date",
        sort_dir: str = "desc"
    ) -> Tuple[List[CommissionTransaction], int]:
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    CommissionTransaction.source_number.ilike(term),
                    CommissionTransaction.customer_name.ilike(term),
                    CommissionTransaction.product_name.ilike(term)
                ))
            if filters.sales_rep_id:
                query = query.filter(
                    CommissionTransaction.sales_rep_id == filters.sales_rep_id
                )
            if filters.customer_id:
                query = query.filter(
                    CommissionTransaction.customer_id == filters.customer_id
                )
            if filters.source_type:
                query = query.filter(
                    CommissionTransaction.source_type == filters.source_type
                )
            if filters.commission_status:
                query = query.filter(
                    CommissionTransaction.commission_status == filters.commission_status
                )
            if filters.date_from:
                query = query.filter(
                    CommissionTransaction.source_date >= filters.date_from
                )
            if filters.date_to:
                query = query.filter(
                    CommissionTransaction.source_date <= filters.date_to
                )
            if filters.min_revenue is not None:
                query = query.filter(
                    CommissionTransaction.revenue >= filters.min_revenue
                )
            if filters.max_revenue is not None:
                query = query.filter(
                    CommissionTransaction.revenue <= filters.max_revenue
                )

        total = query.count()

        sort_col = getattr(
            CommissionTransaction, sort_by, CommissionTransaction.source_date
        )
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_for_period(
        self,
        sales_rep_id: UUID,
        start_date: date,
        end_date: date,
        commission_status: str = None
    ) -> List[CommissionTransaction]:
        query = self._base_query().filter(
            CommissionTransaction.sales_rep_id == sales_rep_id,
            CommissionTransaction.source_date >= start_date,
            CommissionTransaction.source_date <= end_date
        )
        if commission_status:
            query = query.filter(
                CommissionTransaction.commission_status == commission_status
            )
        return query.order_by(CommissionTransaction.source_date).all()

    def get_pending_commissions(
        self,
        sales_rep_id: UUID = None
    ) -> List[CommissionTransaction]:
        query = self._base_query().filter(
            CommissionTransaction.commission_status == "pending",
            CommissionTransaction.commission_locked == False
        )
        if sales_rep_id:
            query = query.filter(
                CommissionTransaction.sales_rep_id == sales_rep_id
            )
        return query.all()

    def create(
        self,
        data: Dict[str, Any]
    ) -> CommissionTransaction:
        # Calculer la marge si non fournie
        if "margin" not in data and "revenue" in data and "cost" in data:
            revenue = Decimal(str(data["revenue"]))
            cost = Decimal(str(data.get("cost", 0)))
            data["margin"] = revenue - cost
            if revenue > 0:
                data["margin_percent"] = (
                    (data["margin"] / revenue * 100)
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )

        # Determiner si split
        data["has_split"] = bool(data.get("split_config"))

        transaction = CommissionTransaction(tenant_id=self.tenant_id, **data)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def update(
        self,
        transaction: CommissionTransaction,
        data: Dict[str, Any]
    ) -> CommissionTransaction:
        if transaction.commission_locked:
            raise ValueError("Transaction verrouillee")

        for key, value in data.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def update_commission_status(
        self,
        transaction: CommissionTransaction,
        status: str,
        lock: bool = False
    ) -> CommissionTransaction:
        transaction.commission_status = status
        if lock:
            transaction.commission_locked = True
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def soft_delete(
        self,
        transaction: CommissionTransaction
    ) -> bool:
        transaction.is_deleted = True
        transaction.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class CommissionCalculationRepository:
    """Repository CommissionCalculation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(CommissionCalculation).filter(
            CommissionCalculation.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(CommissionCalculation.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[CommissionCalculation]:
        return self._base_query().filter(CommissionCalculation.id == id).first()

    def list(
        self,
        filters: CalculationFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "calculated_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[CommissionCalculation], int]:
        query = self._base_query()

        if filters:
            if filters.sales_rep_id:
                query = query.filter(
                    CommissionCalculation.sales_rep_id == filters.sales_rep_id
                )
            if filters.plan_id:
                query = query.filter(
                    CommissionCalculation.plan_id == filters.plan_id
                )
            if filters.period_id:
                query = query.filter(
                    CommissionCalculation.period_id == filters.period_id
                )
            if filters.status:
                query = query.filter(
                    CommissionCalculation.status.in_(
                        [s.value for s in filters.status]
                    )
                )
            if filters.period_start:
                query = query.filter(
                    CommissionCalculation.period_start >= filters.period_start
                )
            if filters.period_end:
                query = query.filter(
                    CommissionCalculation.period_end <= filters.period_end
                )
            if filters.min_amount is not None:
                query = query.filter(
                    CommissionCalculation.net_commission >= filters.min_amount
                )
            if filters.max_amount is not None:
                query = query.filter(
                    CommissionCalculation.net_commission <= filters.max_amount
                )

        total = query.count()

        sort_col = getattr(
            CommissionCalculation, sort_by, CommissionCalculation.calculated_at
        )
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_for_period(
        self,
        sales_rep_id: UUID,
        period_start: date,
        period_end: date,
        status: List[str] = None
    ) -> List[CommissionCalculation]:
        query = self._base_query().filter(
            CommissionCalculation.sales_rep_id == sales_rep_id,
            CommissionCalculation.period_start >= period_start,
            CommissionCalculation.period_end <= period_end
        )
        if status:
            query = query.filter(CommissionCalculation.status.in_(status))
        return query.all()

    def get_by_transaction(
        self,
        transaction_id: UUID
    ) -> List[CommissionCalculation]:
        return self._base_query().filter(
            CommissionCalculation.transaction_id == transaction_id
        ).all()

    def get_pending_approval(self) -> List[CommissionCalculation]:
        return self._base_query().filter(
            CommissionCalculation.status == CommissionStatus.CALCULATED.value
        ).order_by(CommissionCalculation.calculated_at).all()

    def get_ytd_totals(
        self,
        sales_rep_id: UUID,
        year: int
    ) -> Dict[str, Decimal]:
        """Recupere les totaux YTD pour un commercial."""
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        result = self._base_query().filter(
            CommissionCalculation.sales_rep_id == sales_rep_id,
            CommissionCalculation.period_start >= year_start,
            CommissionCalculation.period_end <= year_end,
            CommissionCalculation.status.in_([
                CommissionStatus.APPROVED.value,
                CommissionStatus.VALIDATED.value,
                CommissionStatus.PAID.value
            ])
        ).with_entities(
            func.sum(CommissionCalculation.base_amount).label("total_sales"),
            func.sum(CommissionCalculation.net_commission).label("total_commission")
        ).first()

        return {
            "total_sales": result.total_sales or Decimal("0"),
            "total_commission": result.total_commission or Decimal("0")
        }

    def create(self, data: Dict[str, Any]) -> CommissionCalculation:
        calculation = CommissionCalculation(tenant_id=self.tenant_id, **data)
        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def update(
        self,
        calculation: CommissionCalculation,
        data: Dict[str, Any]
    ) -> CommissionCalculation:
        for key, value in data.items():
            if hasattr(calculation, key):
                setattr(calculation, key, value)
        calculation.version += 1
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def approve(
        self,
        calculation: CommissionCalculation,
        approved_by: UUID
    ) -> CommissionCalculation:
        calculation.status = CommissionStatus.APPROVED.value
        calculation.approved_at = datetime.utcnow()
        calculation.approved_by = approved_by
        calculation.version += 1
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def validate(
        self,
        calculation: CommissionCalculation,
        validated_by: UUID
    ) -> CommissionCalculation:
        calculation.status = CommissionStatus.VALIDATED.value
        calculation.validated_at = datetime.utcnow()
        calculation.validated_by = validated_by
        calculation.version += 1
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def mark_paid(
        self,
        calculation: CommissionCalculation,
        payment_reference: str = None
    ) -> CommissionCalculation:
        calculation.status = CommissionStatus.PAID.value
        calculation.paid_at = datetime.utcnow()
        calculation.payment_reference = payment_reference
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def soft_delete(self, calculation: CommissionCalculation) -> bool:
        calculation.is_deleted = True
        calculation.deleted_at = datetime.utcnow()
        self.db.commit()
        return True


class CommissionPeriodRepository:
    """Repository CommissionPeriod avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(CommissionPeriod).filter(
            CommissionPeriod.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[CommissionPeriod]:
        return self._base_query().filter(CommissionPeriod.id == id).first()

    def get_by_code(self, code: str) -> Optional[CommissionPeriod]:
        return self._base_query().filter(
            CommissionPeriod.code == code.upper()
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(CommissionPeriod.code == code.upper())
        if exclude_id:
            query = query.filter(CommissionPeriod.id != exclude_id)
        return query.count() > 0

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str = None,
        sort_dir: str = "desc"
    ) -> Tuple[List[CommissionPeriod], int]:
        query = self._base_query()

        if status:
            query = query.filter(CommissionPeriod.status == status)

        total = query.count()
        query = query.order_by(
            desc(CommissionPeriod.start_date) if sort_dir == "desc"
            else asc(CommissionPeriod.start_date)
        )

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_current(self) -> Optional[CommissionPeriod]:
        today = date.today()
        return self._base_query().filter(
            CommissionPeriod.start_date <= today,
            CommissionPeriod.end_date >= today,
            CommissionPeriod.status == "open"
        ).first()

    def get_open_periods(self) -> List[CommissionPeriod]:
        return self._base_query().filter(
            CommissionPeriod.status == "open"
        ).order_by(CommissionPeriod.start_date).all()

    def check_overlap(
        self,
        start_date: date,
        end_date: date,
        exclude_id: UUID = None
    ) -> bool:
        query = self._base_query().filter(
            CommissionPeriod.start_date <= end_date,
            CommissionPeriod.end_date >= start_date
        )
        if exclude_id:
            query = query.filter(CommissionPeriod.id != exclude_id)
        return query.count() > 0

    def get_next_code(self, period_type: str, year: int) -> str:
        """Genere le prochain code de periode."""
        prefix_map = {
            "monthly": "M",
            "quarterly": "Q",
            "semi_annual": "S",
            "annual": "A",
            "weekly": "W"
        }
        prefix = prefix_map.get(period_type, "P")

        last = self._base_query().filter(
            CommissionPeriod.code.like(f"{year}-{prefix}%")
        ).order_by(desc(CommissionPeriod.code)).first()

        if last:
            try:
                last_num = int(last.code.split(prefix)[-1])
                return f"{year}-{prefix}{last_num + 1:02d}"
            except (ValueError, IndexError):
                pass

        return f"{year}-{prefix}01"

    def create(
        self,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> CommissionPeriod:
        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code(
                data.get("period_type", "monthly"),
                data["start_date"].year
            )

        period = CommissionPeriod(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)
        return period

    def update(
        self,
        period: CommissionPeriod,
        data: Dict[str, Any]
    ) -> CommissionPeriod:
        for key, value in data.items():
            if hasattr(period, key):
                setattr(period, key, value)
        self.db.commit()
        self.db.refresh(period)
        return period

    def close(
        self,
        period: CommissionPeriod,
        closed_by: UUID = None
    ) -> CommissionPeriod:
        period.status = "closed"
        period.is_locked = True
        period.closed_at = datetime.utcnow()
        period.closed_by = closed_by
        self.db.commit()
        self.db.refresh(period)
        return period


class CommissionStatementRepository:
    """Repository CommissionStatement avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(CommissionStatement).filter(
            CommissionStatement.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[CommissionStatement]:
        return self._base_query().filter(CommissionStatement.id == id).first()

    def get_by_number(self, number: str) -> Optional[CommissionStatement]:
        return self._base_query().filter(
            CommissionStatement.statement_number == number
        ).first()

    def list(
        self,
        sales_rep_id: UUID = None,
        period_id: UUID = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CommissionStatement], int]:
        query = self._base_query()

        if sales_rep_id:
            query = query.filter(
                CommissionStatement.sales_rep_id == sales_rep_id
            )
        if period_id:
            query = query.filter(CommissionStatement.period_id == period_id)
        if status:
            query = query.filter(CommissionStatement.status == status)

        total = query.count()
        query = query.order_by(desc(CommissionStatement.generated_at))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_next_number(self, period_code: str) -> str:
        """Genere le prochain numero de releve."""
        last = self._base_query().filter(
            CommissionStatement.statement_number.like(f"REL-{period_code}-%")
        ).order_by(desc(CommissionStatement.statement_number)).first()

        if last:
            try:
                last_num = int(last.statement_number.split("-")[-1])
                return f"REL-{period_code}-{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"REL-{period_code}-0001"

    def create(
        self,
        data: Dict[str, Any]
    ) -> CommissionStatement:
        statement = CommissionStatement(tenant_id=self.tenant_id, **data)
        self.db.add(statement)
        self.db.commit()
        self.db.refresh(statement)
        return statement

    def update(
        self,
        statement: CommissionStatement,
        data: Dict[str, Any]
    ) -> CommissionStatement:
        for key, value in data.items():
            if hasattr(statement, key):
                setattr(statement, key, value)
        statement.version += 1
        self.db.commit()
        self.db.refresh(statement)
        return statement

    def approve(
        self,
        statement: CommissionStatement,
        approved_by: UUID
    ) -> CommissionStatement:
        statement.status = CommissionStatus.APPROVED.value
        statement.approved_at = datetime.utcnow()
        statement.approved_by = approved_by
        statement.version += 1
        self.db.commit()
        self.db.refresh(statement)
        return statement

    def mark_paid(
        self,
        statement: CommissionStatement,
        payment_reference: str,
        payment_method: str = None
    ) -> CommissionStatement:
        statement.status = CommissionStatus.PAID.value
        statement.paid_at = datetime.utcnow()
        statement.payment_reference = payment_reference
        statement.payment_method = payment_method
        self.db.commit()
        self.db.refresh(statement)
        return statement


class CommissionAdjustmentRepository:
    """Repository CommissionAdjustment avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        query = self.db.query(CommissionAdjustment).filter(
            CommissionAdjustment.tenant_id == self.tenant_id
        )
        if not self.include_deleted:
            query = query.filter(CommissionAdjustment.is_deleted == False)
        return query

    def get_by_id(self, id: UUID) -> Optional[CommissionAdjustment]:
        return self._base_query().filter(CommissionAdjustment.id == id).first()

    def get_by_code(self, code: str) -> Optional[CommissionAdjustment]:
        return self._base_query().filter(
            CommissionAdjustment.code == code.upper()
        ).first()

    def list(
        self,
        sales_rep_id: UUID = None,
        adjustment_type: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CommissionAdjustment], int]:
        query = self._base_query()

        if sales_rep_id:
            query = query.filter(
                CommissionAdjustment.sales_rep_id == sales_rep_id
            )
        if adjustment_type:
            query = query.filter(
                CommissionAdjustment.adjustment_type == adjustment_type
            )
        if status:
            query = query.filter(CommissionAdjustment.status == status)

        total = query.count()
        query = query.order_by(desc(CommissionAdjustment.created_at))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_pending_approval(self) -> List[CommissionAdjustment]:
        return self._base_query().filter(
            CommissionAdjustment.status == WorkflowStatus.PENDING.value
        ).order_by(CommissionAdjustment.requested_at).all()

    def get_next_code(self, adjustment_type: str) -> str:
        year = datetime.utcnow().year
        prefix = f"ADJ-{adjustment_type[:3].upper()}-{year}-"

        last = self._base_query().filter(
            CommissionAdjustment.code.like(f"{prefix}%")
        ).order_by(desc(CommissionAdjustment.code)).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(
        self,
        data: Dict[str, Any],
        requested_by: UUID
    ) -> CommissionAdjustment:
        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code(data["adjustment_type"])

        adjustment = CommissionAdjustment(
            tenant_id=self.tenant_id,
            requested_by=requested_by,
            **data
        )
        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment

    def approve(
        self,
        adjustment: CommissionAdjustment,
        approved_by: UUID
    ) -> CommissionAdjustment:
        adjustment.status = WorkflowStatus.APPROVED.value
        adjustment.approved_at = datetime.utcnow()
        adjustment.approved_by = approved_by
        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment

    def reject(
        self,
        adjustment: CommissionAdjustment,
        rejected_by: UUID,
        reason: str
    ) -> CommissionAdjustment:
        adjustment.status = WorkflowStatus.REJECTED.value
        adjustment.rejected_at = datetime.utcnow()
        adjustment.rejected_by = rejected_by
        adjustment.rejection_reason = reason
        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment


class CommissionClawbackRepository:
    """Repository CommissionClawback avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(CommissionClawback).filter(
            CommissionClawback.tenant_id == self.tenant_id
        )

    def get_by_id(self, id: UUID) -> Optional[CommissionClawback]:
        return self._base_query().filter(CommissionClawback.id == id).first()

    def get_by_code(self, code: str) -> Optional[CommissionClawback]:
        return self._base_query().filter(
            CommissionClawback.code == code.upper()
        ).first()

    def list(
        self,
        sales_rep_id: UUID = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CommissionClawback], int]:
        query = self._base_query()

        if sales_rep_id:
            query = query.filter(CommissionClawback.sales_rep_id == sales_rep_id)
        if status:
            query = query.filter(CommissionClawback.status == status)

        total = query.count()
        query = query.order_by(desc(CommissionClawback.created_at))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_pending_for_rep(self, sales_rep_id: UUID) -> List[CommissionClawback]:
        return self._base_query().filter(
            CommissionClawback.sales_rep_id == sales_rep_id,
            CommissionClawback.status == "pending"
        ).all()

    def get_by_calculation(
        self,
        calculation_id: UUID
    ) -> List[CommissionClawback]:
        return self._base_query().filter(
            CommissionClawback.original_calculation_id == calculation_id
        ).all()

    def get_next_code(self) -> str:
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        prefix = f"CLB-{year}{month:02d}-"

        last = self._base_query().filter(
            CommissionClawback.code.like(f"{prefix}%")
        ).order_by(desc(CommissionClawback.code)).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass

        return f"{prefix}0001"

    def create(
        self,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> CommissionClawback:
        if "code" not in data or not data["code"]:
            data["code"] = self.get_next_code()

        clawback = CommissionClawback(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(clawback)
        self.db.commit()
        self.db.refresh(clawback)
        return clawback

    def approve(
        self,
        clawback: CommissionClawback,
        approved_by: UUID
    ) -> CommissionClawback:
        clawback.status = "approved"
        clawback.approved_at = datetime.utcnow()
        clawback.approved_by = approved_by
        self.db.commit()
        self.db.refresh(clawback)
        return clawback

    def apply(
        self,
        clawback: CommissionClawback,
        statement_id: UUID
    ) -> CommissionClawback:
        clawback.status = "applied"
        clawback.applied_at = datetime.utcnow()
        clawback.applied_to_statement_id = statement_id
        clawback.applied_amount = clawback.clawback_amount
        clawback.remaining_amount = Decimal("0")
        self.db.commit()
        self.db.refresh(clawback)
        return clawback

    def waive(
        self,
        clawback: CommissionClawback,
        waived_by: UUID,
        reason: str
    ) -> CommissionClawback:
        clawback.status = "waived"
        clawback.waived_at = datetime.utcnow()
        clawback.waived_by = waived_by
        clawback.waiver_reason = reason
        self.db.commit()
        self.db.refresh(clawback)
        return clawback


class CommissionAuditLogRepository:
    """Repository CommissionAuditLog avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(CommissionAuditLog).filter(
            CommissionAuditLog.tenant_id == self.tenant_id
        )

    def list(
        self,
        entity_type: str = None,
        entity_id: UUID = None,
        action: str = None,
        user_id: UUID = None,
        date_from: datetime = None,
        date_to: datetime = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[CommissionAuditLog], int]:
        query = self._base_query()

        if entity_type:
            query = query.filter(CommissionAuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(CommissionAuditLog.entity_id == entity_id)
        if action:
            query = query.filter(CommissionAuditLog.action == action)
        if user_id:
            query = query.filter(CommissionAuditLog.user_id == user_id)
        if date_from:
            query = query.filter(CommissionAuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(CommissionAuditLog.created_at <= date_to)

        total = query.count()
        query = query.order_by(desc(CommissionAuditLog.created_at))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def create(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        user_id: UUID,
        user_name: str = None,
        user_role: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
        changes: Dict = None,
        extra_info: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ) -> CommissionAuditLog:
        log = CommissionAuditLog(
            tenant_id=self.tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            extra_info=extra_info or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        self.db.add(log)
        self.db.commit()
        return log
