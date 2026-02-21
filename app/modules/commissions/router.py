"""
Router API - Module Commissions (GAP-041)

Endpoints REST pour la gestion des commissions commerciales.
"""
import math
from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import PlanStatus, CommissionStatus
from .schemas import (
    # Plans
    CommissionPlanCreate, CommissionPlanUpdate, CommissionPlanResponse,
    CommissionPlanList, CommissionPlanListItem, PlanFilters,
    CommissionTierCreate, CommissionTierUpdate, CommissionTierResponse,
    AcceleratorCreate, AcceleratorUpdate, AcceleratorResponse,
    # Assignments
    AssignmentCreate, AssignmentUpdate, AssignmentResponse, AssignmentList,
    # Team
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse,
    # Transactions
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionList, TransactionFilters,
    # Calculations
    CalculationResponse, CalculationList, CalculationFilters,
    CalculationRequest, BulkCalculationRequest, BulkActionResult,
    # Periods
    PeriodCreate, PeriodUpdate, PeriodResponse, PeriodList,
    # Statements
    StatementResponse, StatementList,
    # Adjustments
    AdjustmentCreate, AdjustmentUpdate, AdjustmentResponse, AdjustmentList,
    # Clawbacks
    ClawbackCreate, ClawbackUpdate, ClawbackResponse, ClawbackList,
    # Workflow
    WorkflowAction, WorkflowResponse,
    # Stats & Dashboard
    SalesRepPerformance, TeamPerformance, CommissionDashboard, Leaderboard,
    # Common
    AutocompleteResponse, AutocompleteItem, ExportRequest
)
from .service import CommissionService, create_commission_service
from .exceptions import (
    PlanNotFoundError, PlanDuplicateError, PlanInvalidStateError,
    AssignmentNotFoundError, AssignmentOverlapError,
    TransactionNotFoundError, TransactionDuplicateError, TransactionLockedError,
    CalculationNotFoundError, CalculationError, CalculationAlreadyExistsError,
    PeriodNotFoundError, PeriodDuplicateError, PeriodLockedError,
    StatementNotFoundError, StatementAlreadyPaidError,
    AdjustmentNotFoundError, AdjustmentNotPendingError,
    ClawbackNotFoundError, ClawbackNotEligibleError,
    TeamMemberNotFoundError
)

router = APIRouter(prefix="/commissions", tags=["Commissions"])


def get_commission_service(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> CommissionService:
    """Dependency pour obtenir le service de commissions."""
    return create_commission_service(
        db=db,
        tenant_id=str(current_user.tenant_id),
        user_id=current_user.id
    )


# ============================================================================
# PLANS DE COMMISSION
# ============================================================================

@router.get("/plans", response_model=CommissionPlanList)
async def list_plans(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[PlanStatus]] = Query(None),
    effective_date: Optional[date] = Query(None),
    include_expired: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.read")
):
    """Lister les plans de commission."""
    filters = PlanFilters(
        search=search,
        status=status,
        effective_date=effective_date,
        include_expired=include_expired
    )

    items, total = service.plan_repo.list(
        filters, page, page_size, sort_by, sort_dir
    )

    return CommissionPlanList(
        items=[CommissionPlanListItem(
            id=p.id,
            code=p.code,
            name=p.name,
            basis=p.basis,
            tier_type=p.tier_type,
            status=p.status,
            payment_frequency=p.payment_frequency,
            effective_from=p.effective_from,
            effective_to=p.effective_to,
            tier_count=len(p.tiers) if p.tiers else 0,
            assignment_count=len(p.assignments) if p.assignments else 0,
            is_active=p.status == PlanStatus.ACTIVE.value
        ) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/plans/{plan_id}", response_model=CommissionPlanResponse)
async def get_plan(
    plan_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.read")
):
    """Obtenir un plan de commission."""
    plan = service.plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    return plan


@router.post("/plans", response_model=CommissionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: CommissionPlanCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.create")
):
    """Creer un plan de commission."""
    try:
        return service.create_plan(data)
    except PlanDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/plans/{plan_id}", response_model=CommissionPlanResponse)
async def update_plan(
    plan_id: UUID,
    data: CommissionPlanUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Mettre a jour un plan de commission."""
    try:
        return service.update_plan(plan_id, data)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    except PlanDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PlanInvalidStateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plans/{plan_id}/activate", response_model=CommissionPlanResponse)
async def activate_plan(
    plan_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.activate")
):
    """Activer un plan de commission."""
    try:
        return service.activate_plan(plan_id)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    except (PlanInvalidStateError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plans/{plan_id}/suspend", response_model=CommissionPlanResponse)
async def suspend_plan(
    plan_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Suspendre un plan de commission."""
    try:
        return service.suspend_plan(plan_id)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plans/{plan_id}/archive", response_model=CommissionPlanResponse)
async def archive_plan(
    plan_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Archiver un plan de commission."""
    try:
        return service.archive_plan(plan_id)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.delete")
):
    """Supprimer un plan de commission (soft delete)."""
    plan = service.plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouve")

    service.plan_repo.soft_delete(plan, service.user_id)


# ============================================================================
# PALIERS (TIERS)
# ============================================================================

@router.post("/plans/{plan_id}/tiers", response_model=CommissionTierResponse, status_code=status.HTTP_201_CREATED)
async def add_tier(
    plan_id: UUID,
    data: CommissionTierCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Ajouter un palier a un plan."""
    plan = service.plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouve")

    try:
        return service.plan_repo.add_tier(plan, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/plans/{plan_id}/tiers/{tier_id}", response_model=CommissionTierResponse)
async def update_tier(
    plan_id: UUID,
    tier_id: UUID,
    data: CommissionTierUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Mettre a jour un palier."""
    plan = service.plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouve")

    tier = next((t for t in plan.tiers if t.id == tier_id), None)
    if not tier:
        raise HTTPException(status_code=404, detail="Palier non trouve")

    return service.plan_repo.update_tier(tier, data.model_dump(exclude_unset=True))


@router.delete("/plans/{plan_id}/tiers/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(
    plan_id: UUID,
    tier_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.plan.update")
):
    """Supprimer un palier."""
    plan = service.plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan non trouve")

    tier = next((t for t in plan.tiers if t.id == tier_id), None)
    if not tier:
        raise HTTPException(status_code=404, detail="Palier non trouve")

    service.plan_repo.delete_tier(tier)


# ============================================================================
# ATTRIBUTIONS
# ============================================================================

@router.get("/assignments", response_model=AssignmentList)
async def list_assignments(
    plan_id: Optional[UUID] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
    effective_date: Optional[date] = Query(None),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.assignment.read")
):
    """Lister les attributions de plans."""
    if plan_id:
        items = service.assignment_repo.get_by_plan(plan_id)
    elif assignee_id:
        items = service.assignment_repo.get_by_assignee(assignee_id, effective_date)
    else:
        items = service.assignment_repo.get_by_plan(None)  # Tous

    return AssignmentList(items=items, total=len(items))


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.assignment.create")
):
    """Assigner un plan a un commercial/equipe."""
    try:
        return service.assign_plan(data)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    except PlanInvalidStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AssignmentOverlapError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.assignment.update")
):
    """Mettre a jour une attribution."""
    try:
        return service.update_assignment(assignment_id, data.model_dump(exclude_unset=True))
    except AssignmentNotFoundError:
        raise HTTPException(status_code=404, detail="Attribution non trouvee")


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_assignment(
    assignment_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.assignment.delete")
):
    """Desactiver une attribution."""
    try:
        service.deactivate_assignment(assignment_id)
    except AssignmentNotFoundError:
        raise HTTPException(status_code=404, detail="Attribution non trouvee")


# ============================================================================
# EQUIPE COMMERCIALE
# ============================================================================

@router.get("/team/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.team.read")
):
    """Lister les membres de l'equipe commerciale."""
    if team_id:
        items = service.team_repo.get_team_members(team_id)
    else:
        items = service.team_repo.list_active() if active_only else service.team_repo._base_query().all()
    return items


@router.get("/team/members/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(
    member_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.team.read")
):
    """Obtenir un membre de l'equipe."""
    member = service.team_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membre non trouve")
    return member


@router.post("/team/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    data: TeamMemberCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.team.create")
):
    """Ajouter un membre a l'equipe commerciale."""
    return service.team_repo.create(data.model_dump())


@router.put("/team/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: UUID,
    data: TeamMemberUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.team.update")
):
    """Mettre a jour un membre de l'equipe."""
    member = service.team_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membre non trouve")

    return service.team_repo.update(member, data.model_dump(exclude_unset=True))


@router.get("/team/members/{member_id}/subordinates", response_model=List[TeamMemberResponse])
async def get_subordinates(
    member_id: UUID,
    recursive: bool = Query(False),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.team.read")
):
    """Obtenir les subordonnes d'un membre."""
    if recursive:
        return service.team_repo.get_all_subordinates_recursive(member_id)
    return service.team_repo.get_subordinates(member_id)


# ============================================================================
# TRANSACTIONS
# ============================================================================

@router.get("/transactions", response_model=TransactionList)
async def list_transactions(
    search: Optional[str] = Query(None, min_length=2),
    sales_rep_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    source_type: Optional[str] = Query(None),
    commission_status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("source_date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.transaction.read")
):
    """Lister les transactions de vente."""
    filters = TransactionFilters(
        search=search,
        sales_rep_id=sales_rep_id,
        customer_id=customer_id,
        source_type=source_type,
        commission_status=commission_status,
        date_from=date_from,
        date_to=date_to
    )

    items, total = service.transaction_repo.list(
        filters, page, page_size, sort_by, sort_dir
    )

    return TransactionList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.transaction.read")
):
    """Obtenir une transaction."""
    transaction = service.transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvee")
    return transaction


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.transaction.create")
):
    """Enregistrer une transaction de vente."""
    try:
        return service.record_transaction(data)
    except TransactionDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.transaction.update")
):
    """Mettre a jour une transaction."""
    transaction = service.transaction_repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvee")

    try:
        return service.transaction_repo.update(
            transaction,
            data.model_dump(exclude_unset=True)
        )
    except TransactionLockedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transactions/{transaction_id}/payment-status")
async def update_transaction_payment(
    transaction_id: UUID,
    payment_status: str = Query(...),
    payment_date: Optional[date] = Query(None),
    payment_amount: Optional[Decimal] = Query(None),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.transaction.update")
):
    """Mettre a jour le statut de paiement d'une transaction."""
    try:
        return service.update_transaction_payment(
            transaction_id,
            payment_status,
            payment_date,
            payment_amount
        )
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction non trouvee")
    except TransactionLockedError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CALCULS
# ============================================================================

@router.get("/calculations", response_model=CalculationList)
async def list_calculations(
    sales_rep_id: Optional[UUID] = Query(None),
    plan_id: Optional[UUID] = Query(None),
    period_id: Optional[UUID] = Query(None),
    status: Optional[List[CommissionStatus]] = Query(None),
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("calculated_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.read")
):
    """Lister les calculs de commission."""
    filters = CalculationFilters(
        sales_rep_id=sales_rep_id,
        plan_id=plan_id,
        period_id=period_id,
        status=status,
        period_start=period_start,
        period_end=period_end
    )

    items, total = service.calculation_repo.list(
        filters, page, page_size, sort_by, sort_dir
    )

    return CalculationList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/calculations/{calculation_id}", response_model=CalculationResponse)
async def get_calculation(
    calculation_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.read")
):
    """Obtenir un calcul de commission."""
    calculation = service.calculation_repo.get_by_id(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail="Calcul non trouve")
    return calculation


@router.post("/calculations/calculate", response_model=CalculationResponse)
async def calculate_commission(
    request: CalculationRequest,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.create")
):
    """Calculer la commission pour un commercial sur une periode."""
    try:
        return service.calculate_commission(request)
    except PlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan non trouve")
    except CalculationAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculations/calculate-bulk", response_model=BulkActionResult)
async def calculate_all_commissions(
    request: BulkCalculationRequest,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.create")
):
    """Calculer toutes les commissions pour une periode."""
    try:
        results = service.calculate_all_for_period(request)
        return BulkActionResult(
            success_count=len(results["success"]),
            error_count=len(results["errors"]),
            errors=results["errors"],
            created_ids=[UUID(r["calculation_id"]) for r in results["success"]]
        )
    except PeriodNotFoundError:
        raise HTTPException(status_code=404, detail="Periode non trouvee")


@router.post("/calculations/calculate-split", response_model=List[CalculationResponse])
async def calculate_split_commissions(
    transaction_id: UUID = Query(...),
    plan_id: UUID = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.create")
):
    """Calculer les commissions splitees pour une transaction."""
    try:
        return service.calculate_split_commissions(transaction_id, plan_id)
    except (TransactionNotFoundError, PlanNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculations/calculate-override", response_model=CalculationResponse)
async def calculate_manager_override(
    manager_id: UUID = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.create")
):
    """Calculer l'override manager."""
    try:
        return service.calculate_manager_override(manager_id, period_start, period_end)
    except TeamMemberNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculations/{calculation_id}/approve", response_model=CalculationResponse)
async def approve_calculation(
    calculation_id: UUID,
    comments: Optional[str] = Body(None, embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.approve")
):
    """Approuver un calcul de commission."""
    try:
        return service.approve_calculation(calculation_id, comments)
    except CalculationNotFoundError:
        raise HTTPException(status_code=404, detail="Calcul non trouve")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculations/{calculation_id}/reject", response_model=CalculationResponse)
async def reject_calculation(
    calculation_id: UUID,
    reason: str = Body(..., embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.approve")
):
    """Rejeter un calcul de commission."""
    try:
        return service.reject_calculation(calculation_id, reason)
    except CalculationNotFoundError:
        raise HTTPException(status_code=404, detail="Calcul non trouve")


@router.post("/calculations/{calculation_id}/validate", response_model=CalculationResponse)
async def validate_calculation(
    calculation_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.validate")
):
    """Valider un calcul pour paiement."""
    try:
        return service.validate_for_payment(calculation_id)
    except CalculationNotFoundError:
        raise HTTPException(status_code=404, detail="Calcul non trouve")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculations/bulk-approve", response_model=BulkActionResult)
async def bulk_approve_calculations(
    calculation_ids: List[UUID] = Body(..., embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.calculation.approve")
):
    """Approuver plusieurs calculs en masse."""
    results = service.bulk_approve_calculations(calculation_ids)
    return BulkActionResult(
        success_count=len(results["approved"]),
        error_count=len(results["errors"]),
        errors=results["errors"]
    )


# ============================================================================
# PERIODES
# ============================================================================

@router.get("/periods", response_model=PeriodList)
async def list_periods(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.read")
):
    """Lister les periodes de commissionnement."""
    items, total = service.period_repo.list(page, page_size, status, sort_dir)

    return PeriodList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/periods/current", response_model=PeriodResponse)
async def get_current_period(
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.read")
):
    """Obtenir la periode courante."""
    period = service.period_repo.get_current()
    if not period:
        raise HTTPException(status_code=404, detail="Aucune periode courante")
    return period


@router.get("/periods/{period_id}", response_model=PeriodResponse)
async def get_period(
    period_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.read")
):
    """Obtenir une periode."""
    period = service.period_repo.get_by_id(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Periode non trouvee")
    return period


@router.post("/periods", response_model=PeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_period(
    data: PeriodCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.create")
):
    """Creer une periode de commissionnement."""
    try:
        return service.create_period(data)
    except PeriodDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/periods/{period_id}", response_model=PeriodResponse)
async def update_period(
    period_id: UUID,
    data: PeriodUpdate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.update")
):
    """Mettre a jour une periode."""
    period = service.period_repo.get_by_id(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Periode non trouvee")

    if period.is_locked:
        raise HTTPException(status_code=400, detail="Periode verrouillee")

    return service.period_repo.update(period, data.model_dump(exclude_unset=True))


@router.post("/periods/{period_id}/close", response_model=PeriodResponse)
async def close_period(
    period_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.period.close")
):
    """Cloturer une periode."""
    try:
        return service.close_period(period_id)
    except PeriodNotFoundError:
        raise HTTPException(status_code=404, detail="Periode non trouvee")
    except PeriodLockedError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RELEVES (STATEMENTS)
# ============================================================================

@router.get("/statements", response_model=StatementList)
async def list_statements(
    sales_rep_id: Optional[UUID] = Query(None),
    period_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.statement.read")
):
    """Lister les releves de commission."""
    items, total = service.statement_repo.list(
        sales_rep_id, period_id, status, page, page_size
    )

    return StatementList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/statements/{statement_id}", response_model=StatementResponse)
async def get_statement(
    statement_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.statement.read")
):
    """Obtenir un releve."""
    statement = service.statement_repo.get_by_id(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Releve non trouve")
    return statement


@router.post("/statements/generate", response_model=StatementResponse)
async def generate_statement(
    period_id: UUID = Query(...),
    sales_rep_id: UUID = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.statement.create")
):
    """Generer un releve de commission."""
    try:
        return service.generate_statement(period_id, sales_rep_id)
    except PeriodNotFoundError:
        raise HTTPException(status_code=404, detail="Periode non trouvee")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/statements/{statement_id}/approve", response_model=StatementResponse)
async def approve_statement(
    statement_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.statement.approve")
):
    """Approuver un releve."""
    try:
        return service.approve_statement(statement_id)
    except StatementNotFoundError:
        raise HTTPException(status_code=404, detail="Releve non trouve")


@router.post("/statements/{statement_id}/pay", response_model=StatementResponse)
async def pay_statement(
    statement_id: UUID,
    payment_reference: str = Body(..., embed=True),
    payment_method: Optional[str] = Body(None, embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.statement.pay")
):
    """Marquer un releve comme paye."""
    try:
        return service.pay_statement(statement_id, payment_reference, payment_method)
    except StatementNotFoundError:
        raise HTTPException(status_code=404, detail="Releve non trouve")
    except StatementAlreadyPaidError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AJUSTEMENTS
# ============================================================================

@router.get("/adjustments", response_model=AdjustmentList)
async def list_adjustments(
    sales_rep_id: Optional[UUID] = Query(None),
    adjustment_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.adjustment.read")
):
    """Lister les ajustements."""
    items, total = service.adjustment_repo.list(
        sales_rep_id, adjustment_type, status, page, page_size
    )

    return AdjustmentList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/adjustments/{adjustment_id}", response_model=AdjustmentResponse)
async def get_adjustment(
    adjustment_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.adjustment.read")
):
    """Obtenir un ajustement."""
    adjustment = service.adjustment_repo.get_by_id(adjustment_id)
    if not adjustment:
        raise HTTPException(status_code=404, detail="Ajustement non trouve")
    return adjustment


@router.post("/adjustments", response_model=AdjustmentResponse, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    data: AdjustmentCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.adjustment.create")
):
    """Creer un ajustement de commission."""
    return service.create_adjustment(data)


@router.post("/adjustments/{adjustment_id}/approve", response_model=AdjustmentResponse)
async def approve_adjustment(
    adjustment_id: UUID,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.adjustment.approve")
):
    """Approuver un ajustement."""
    try:
        return service.approve_adjustment(adjustment_id)
    except AdjustmentNotFoundError:
        raise HTTPException(status_code=404, detail="Ajustement non trouve")
    except AdjustmentNotPendingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/adjustments/{adjustment_id}/reject", response_model=AdjustmentResponse)
async def reject_adjustment(
    adjustment_id: UUID,
    reason: str = Body(..., embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.adjustment.approve")
):
    """Rejeter un ajustement."""
    try:
        return service.reject_adjustment(adjustment_id, reason)
    except AdjustmentNotFoundError:
        raise HTTPException(status_code=404, detail="Ajustement non trouve")


# ============================================================================
# CLAWBACKS
# ============================================================================

@router.get("/clawbacks", response_model=ClawbackList)
async def list_clawbacks(
    sales_rep_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.clawback.read")
):
    """Lister les clawbacks."""
    items, total = service.clawback_repo.list(
        sales_rep_id, status, page, page_size
    )

    return ClawbackList(items=items, total=total)


@router.get("/clawbacks/check-eligibility")
async def check_clawback_eligibility(
    transaction_id: UUID = Query(...),
    cancellation_date: date = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.clawback.read")
):
    """Verifier l'eligibilite au clawback."""
    return service.check_clawback_eligibility(transaction_id, cancellation_date)


@router.post("/clawbacks", response_model=ClawbackResponse, status_code=status.HTTP_201_CREATED)
async def create_clawback(
    data: ClawbackCreate,
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.clawback.create")
):
    """Creer un clawback."""
    try:
        return service.create_clawback(data)
    except CalculationNotFoundError:
        raise HTTPException(status_code=404, detail="Calcul original non trouve")
    except ClawbackPeriodExpiredError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/clawbacks/{clawback_id}/waive", response_model=ClawbackResponse)
async def waive_clawback(
    clawback_id: UUID,
    reason: str = Body(..., embed=True),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.clawback.waive")
):
    """Annuler un clawback."""
    try:
        return service.waive_clawback(clawback_id, reason)
    except ClawbackNotFoundError:
        raise HTTPException(status_code=404, detail="Clawback non trouve")


# ============================================================================
# DASHBOARD & REPORTING
# ============================================================================

@router.get("/dashboard", response_model=CommissionDashboard)
async def get_dashboard(
    period_start: date = Query(...),
    period_end: date = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.dashboard.read")
):
    """Obtenir le dashboard des commissions."""
    return service.get_dashboard(period_start, period_end)


@router.get("/performance/{sales_rep_id}", response_model=SalesRepPerformance)
async def get_sales_rep_performance(
    sales_rep_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.report.read")
):
    """Obtenir les performances d'un commercial."""
    return service.get_sales_rep_performance(sales_rep_id, period_start, period_end)


@router.get("/leaderboard", response_model=Leaderboard)
async def get_leaderboard(
    period_start: date = Query(...),
    period_end: date = Query(...),
    metric: str = Query("revenue", pattern="^(revenue|margin|commissions|quota_achievement|transactions)$"),
    limit: int = Query(10, ge=1, le=100),
    service: CommissionService = Depends(get_commission_service),
    _: None = require_permission("commissions.report.read")
):
    """Obtenir le classement des commerciaux."""
    return service.get_leaderboard(period_start, period_end, metric, limit)


@router.get("/my/performance", response_model=SalesRepPerformance)
async def get_my_performance(
    period_start: date = Query(...),
    period_end: date = Query(...),
    service: CommissionService = Depends(get_commission_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("commissions.report.read")
):
    """Obtenir mes performances."""
    return service.get_sales_rep_performance(
        current_user.id, period_start, period_end
    )


@router.get("/my/statements", response_model=StatementList)
async def get_my_statements(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CommissionService = Depends(get_commission_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("commissions.statement.read")
):
    """Obtenir mes releves de commission."""
    items, total = service.statement_repo.list(
        current_user.id, None, status, page, page_size
    )

    return StatementList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/my/plans", response_model=List[CommissionPlanResponse])
async def get_my_plans(
    effective_date: Optional[date] = Query(None),
    service: CommissionService = Depends(get_commission_service),
    current_user=Depends(get_current_user),
    _: None = require_permission("commissions.plan.read")
):
    """Obtenir mes plans de commission."""
    return service.get_plans_for_employee(current_user.id, effective_date)
