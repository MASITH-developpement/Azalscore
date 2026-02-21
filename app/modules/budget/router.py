"""
AZALS MODULE - BUDGET: Router
==============================

API REST pour la gestion budgetaire complete.

Endpoints:
- /budget/categories - Gestion des categories budgetaires
- /budget/budgets - CRUD des budgets
- /budget/budgets/{id}/lines - Lignes de budget
- /budget/budgets/{id}/workflow - Actions de workflow
- /budget/budgets/{id}/actuals - Realises
- /budget/budgets/{id}/variances - Ecarts
- /budget/budgets/{id}/revisions - Revisions
- /budget/budgets/{id}/forecasts - Previsions
- /budget/budgets/{id}/scenarios - Scenarios
- /budget/alerts - Alertes
- /budget/dashboard - Tableau de bord
- /budget/control - Controle budgetaire

Auteur: AZALSCORE Team
Version: 2.0.0
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User

from .exceptions import (
    BudgetAlreadyExistsError,
    BudgetCategoryNotFoundError,
    BudgetControlViolationError,
    BudgetException,
    BudgetLineNotFoundError,
    BudgetNotFoundError,
    BudgetNotModifiableError,
    BudgetRevisionError,
    BudgetRevisionNotFoundError,
    BudgetStatusError,
    BudgetValidationError,
)
from .models import (
    AlertSeverity,
    AlertStatus,
    BudgetStatus,
    BudgetType,
)
from .schemas import (
    AlertAcknowledge,
    AlertResolve,
    BudgetActualCreate,
    BudgetActualResponse,
    BudgetActivate,
    BudgetApprove,
    BudgetCategoryCreate,
    BudgetCategoryResponse,
    BudgetCategoryUpdate,
    BudgetControlCheck,
    BudgetControlResult,
    BudgetCreate,
    BudgetDashboard,
    BudgetDetailResponse,
    BudgetExecutionRate,
    BudgetForecastCreate,
    BudgetForecastResponse,
    BudgetLineCreate,
    BudgetLineResponse,
    BudgetLineUpdate,
    BudgetReject,
    BudgetResponse,
    BudgetRevisionCreate,
    BudgetRevisionResponse,
    BudgetScenarioCreate,
    BudgetScenarioResponse,
    BudgetSubmit,
    BudgetUpdate,
    BudgetVariance,
    PaginatedBudgetActuals,
    PaginatedBudgetAlerts,
    PaginatedBudgetCategories,
    PaginatedBudgetForecasts,
    PaginatedBudgetRevisions,
    PaginatedBudgetScenarios,
    PaginatedBudgets,
    PaginatedBudgetLines,
    RevisionApprove,
    RevisionReject,
    BudgetAlertResponse,
)
from .service import BudgetService


router = APIRouter(prefix="/budget", tags=["Budget - Gestion Budgetaire"])


def get_budget_service(db: Session, tenant_id: str) -> BudgetService:
    """Factory pour creer le service Budget."""
    return BudgetService(db, tenant_id)


def handle_budget_exception(e: BudgetException):
    """Convertit les exceptions budget en HTTPException."""
    status_code = status.HTTP_400_BAD_REQUEST

    if isinstance(e, (BudgetNotFoundError, BudgetLineNotFoundError,
                     BudgetCategoryNotFoundError, BudgetRevisionNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(e, BudgetAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(e, BudgetControlViolationError):
        status_code = status.HTTP_403_FORBIDDEN

    raise HTTPException(
        status_code=status_code,
        detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        }
    )


# ============================================================================
# BUDGET CATEGORIES
# ============================================================================

@router.post("/categories", response_model=BudgetCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: BudgetCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une nouvelle categorie budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.create_category(data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/categories", response_model=PaginatedBudgetCategories)
async def list_categories(
    parent_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les categories budgetaires."""
    service = get_budget_service(db, current_user.tenant_id)
    items, total = service.list_categories(parent_id, is_active, page, per_page)
    pages = (total + per_page - 1) // per_page

    return PaginatedBudgetCategories(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/categories/{category_id}", response_model=BudgetCategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer une categorie budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.get_category(category_id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.put("/categories/{category_id}", response_model=BudgetCategoryResponse)
async def update_category(
    category_id: UUID,
    data: BudgetCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une categorie budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.update_category(category_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une categorie budgetaire (soft delete)."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        service.delete_category(category_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# BUDGETS CRUD
# ============================================================================

@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un nouveau budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.create_budget(data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets", response_model=PaginatedBudgets)
async def list_budgets(
    budget_type: Optional[BudgetType] = Query(None, alias="type"),
    status_filter: Optional[BudgetStatus] = Query(None, alias="status"),
    fiscal_year: Optional[int] = None,
    entity_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les budgets."""
    service = get_budget_service(db, current_user.tenant_id)
    items, total = service.list_budgets(
        budget_type, status_filter, fiscal_year,
        entity_id, department_id, project_id,
        search, page, per_page
    )
    pages = (total + per_page - 1) // per_page

    return PaginatedBudgets(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        items=items
    )


@router.get("/budgets/{budget_id}", response_model=BudgetDetailResponse)
async def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recuperer un budget avec ses details."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.get_budget_detail(budget_id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.update_budget(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer un budget (soft delete)."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        service.delete_budget(budget_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# BUDGET LINES
# ============================================================================

@router.post("/budgets/{budget_id}/lines", response_model=BudgetLineResponse, status_code=status.HTTP_201_CREATED)
async def add_budget_line(
    budget_id: UUID,
    data: BudgetLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ajouter une ligne au budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.add_budget_line(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets/{budget_id}/lines", response_model=PaginatedBudgetLines)
async def list_budget_lines(
    budget_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les lignes d'un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        items = service.get_budget_lines(budget_id)
        total = len(items)
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        return PaginatedBudgetLines(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            items=items
        )
    except BudgetException as e:
        handle_budget_exception(e)


@router.put("/lines/{line_id}", response_model=BudgetLineResponse)
async def update_budget_line(
    line_id: UUID,
    data: BudgetLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre a jour une ligne de budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.update_budget_line(line_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_line(
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une ligne de budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        service.delete_budget_line(line_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# WORKFLOW
# ============================================================================

@router.post("/budgets/{budget_id}/submit", response_model=BudgetResponse)
async def submit_budget(
    budget_id: UUID,
    data: BudgetSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soumettre un budget pour approbation."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.submit_budget(budget_id, current_user.id, data.comments)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/budgets/{budget_id}/approve", response_model=BudgetResponse)
async def approve_budget(
    budget_id: UUID,
    data: BudgetApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.approve_budget(budget_id, current_user.id, data.comments)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/budgets/{budget_id}/reject", response_model=BudgetResponse)
async def reject_budget(
    budget_id: UUID,
    data: BudgetReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rejeter un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.reject_budget(budget_id, current_user.id, data.reason)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/budgets/{budget_id}/activate", response_model=BudgetResponse)
async def activate_budget(
    budget_id: UUID,
    data: BudgetActivate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.activate_budget(budget_id, current_user.id, data.effective_date)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/budgets/{budget_id}/close", response_model=BudgetResponse)
async def close_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cloturer un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.close_budget(budget_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# ACTUALS
# ============================================================================

@router.post("/budgets/{budget_id}/actuals", response_model=BudgetActualResponse, status_code=status.HTTP_201_CREATED)
async def record_actual(
    budget_id: UUID,
    data: BudgetActualCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enregistrer un montant realise."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.record_actual(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/budgets/{budget_id}/actuals/import")
async def import_actuals(
    budget_id: UUID,
    period: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Importer les realises depuis la comptabilite."""
    # Cette route serait connectee au module accounting
    service = get_budget_service(db, current_user.tenant_id)
    try:
        # Simulation d'import - en production, recuperer depuis accounting
        result = service.import_actuals_from_accounting(
            budget_id, period, [], current_user.id
        )
        return result
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# VARIANCES
# ============================================================================

@router.get("/budgets/{budget_id}/variances", response_model=list[BudgetVariance])
async def get_variances(
    budget_id: UUID,
    period: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculer les ecarts budgetaires pour une periode."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.calculate_variances(budget_id, period)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets/{budget_id}/execution-rate", response_model=BudgetExecutionRate)
async def get_execution_rate(
    budget_id: UUID,
    as_of_period: str = Query(..., pattern=r"^\d{4}-\d{2}$", alias="period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le taux d'execution du budget."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.get_execution_rate(budget_id, as_of_period)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# BUDGET CONTROL
# ============================================================================

@router.post("/control/check", response_model=BudgetControlResult)
async def check_budget_control(
    data: BudgetControlCheck,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifier le controle budgetaire avant une depense."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.check_budget_control(data)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# REVISIONS
# ============================================================================

@router.post("/budgets/{budget_id}/revisions", response_model=BudgetRevisionResponse, status_code=status.HTTP_201_CREATED)
async def create_revision(
    budget_id: UUID,
    data: BudgetRevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une revision budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.create_revision(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets/{budget_id}/revisions", response_model=PaginatedBudgetRevisions)
async def list_revisions(
    budget_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les revisions d'un budget."""
    service = get_budget_service(db, current_user.tenant_id)
    # A implementer dans le service
    return PaginatedBudgetRevisions(
        total=0,
        page=page,
        per_page=per_page,
        pages=0,
        items=[]
    )


@router.post("/revisions/{revision_id}/submit", response_model=BudgetRevisionResponse)
async def submit_revision(
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soumettre une revision pour approbation."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.submit_revision(revision_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/revisions/{revision_id}/approve", response_model=BudgetRevisionResponse)
async def approve_revision(
    revision_id: UUID,
    data: RevisionApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver une revision."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.approve_revision(revision_id, current_user.id, data.comments)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/revisions/{revision_id}/apply", response_model=BudgetRevisionResponse)
async def apply_revision(
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Appliquer une revision approuvee."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.apply_revision(revision_id, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# FORECASTS
# ============================================================================

@router.post("/budgets/{budget_id}/forecasts", response_model=BudgetForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    budget_id: UUID,
    data: BudgetForecastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer une prevision."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.create_forecast(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets/{budget_id}/forecasts", response_model=PaginatedBudgetForecasts)
async def list_forecasts(
    budget_id: UUID,
    period: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les previsions d'un budget."""
    # A implementer
    return PaginatedBudgetForecasts(
        total=0,
        page=page,
        per_page=per_page,
        pages=0,
        items=[]
    )


# ============================================================================
# SCENARIOS
# ============================================================================

@router.post("/budgets/{budget_id}/scenarios", response_model=BudgetScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    budget_id: UUID,
    data: BudgetScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creer un scenario budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.create_scenario(budget_id, data, current_user.id)
    except BudgetException as e:
        handle_budget_exception(e)


@router.get("/budgets/{budget_id}/scenarios", response_model=PaginatedBudgetScenarios)
async def list_scenarios(
    budget_id: UUID,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les scenarios d'un budget."""
    # A implementer
    return PaginatedBudgetScenarios(
        total=0,
        page=page,
        per_page=per_page,
        pages=0,
        items=[]
    )


# ============================================================================
# ALERTS
# ============================================================================

@router.get("/alerts", response_model=PaginatedBudgetAlerts)
async def list_alerts(
    budget_id: Optional[UUID] = None,
    status_filter: Optional[AlertStatus] = Query(None, alias="status"),
    severity: Optional[AlertSeverity] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100, alias="page_size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les alertes budgetaires."""
    service = get_budget_service(db, current_user.tenant_id)
    alerts = service.get_active_alerts(budget_id, severity, per_page)

    return PaginatedBudgetAlerts(
        total=len(alerts),
        page=page,
        per_page=per_page,
        pages=1,
        items=[BudgetAlertResponse.model_validate(a) for a in alerts]
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=BudgetAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acquitter une alerte."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        alert = service.acknowledge_alert(alert_id, current_user.id, data.notes)
        return BudgetAlertResponse.model_validate(alert)
    except BudgetException as e:
        handle_budget_exception(e)


@router.post("/alerts/{alert_id}/resolve", response_model=BudgetAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    data: AlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resoudre une alerte."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        alert = service.resolve_alert(alert_id, current_user.id, data.resolution_notes)
        return BudgetAlertResponse.model_validate(alert)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=BudgetDashboard)
async def get_dashboard(
    fiscal_year: Optional[int] = None,
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir le tableau de bord budgetaire."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        return service.get_dashboard(fiscal_year, as_of_date)
    except BudgetException as e:
        handle_budget_exception(e)


# ============================================================================
# SUMMARY
# ============================================================================

@router.get("/summary")
async def get_budget_summary(
    fiscal_year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtenir un resume rapide des budgets."""
    service = get_budget_service(db, current_user.tenant_id)
    try:
        dashboard = service.get_dashboard(fiscal_year)
        return {
            "fiscal_year": dashboard.fiscal_year,
            "total_budgeted_expense": float(dashboard.total_budgeted_expense),
            "total_budgeted_revenue": float(dashboard.total_budgeted_revenue),
            "total_actual_expense": float(dashboard.total_actual_expense),
            "total_actual_revenue": float(dashboard.total_actual_revenue),
            "consumption_rate": float(dashboard.overall_consumption_rate),
            "active_budgets": dashboard.active_budgets_count,
            "active_alerts": dashboard.active_alerts_count,
            "critical_alerts": dashboard.critical_alerts_count
        }
    except BudgetException as e:
        handle_budget_exception(e)
