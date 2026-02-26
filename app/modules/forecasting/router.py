"""
Routes API - Module Forecasting (GAP-076)

CRUD complet, Autocomplete, Permissions vérifiées.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import ForecastStatus, BudgetStatus, ForecastType, ForecastMethod, Granularity
from .repository import (
    ForecastRepository, BudgetRepository, KPIRepository,
    ScenarioRepository, ForecastModelRepository
)
from .schemas import (
    # Forecast
    ForecastCreate, ForecastUpdate, ForecastResponse, ForecastList, ForecastFilters,
    # Budget
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetList, BudgetFilters,
    # KPI
    KPICreate, KPIUpdate, KPIResponse, KPIList, KPIFilters, KPIValueUpdate, KPIDashboard,
    # Scenario
    ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioComparison,
    # Model
    ForecastModelCreate, ForecastModelUpdate, ForecastModelResponse,
    # Common
    AutocompleteResponse, BulkCreateRequest, BulkUpdateRequest, BulkDeleteRequest, BulkResult,
    VarianceReport
)
from .exceptions import (
    ForecastNotFoundError, ForecastDuplicateError, ForecastValidationError, ForecastStateError,
    BudgetNotFoundError, BudgetDuplicateError, BudgetValidationError,
    KPINotFoundError, KPIDuplicateError,
    ScenarioNotFoundError, ModelNotFoundError
)

router = APIRouter(prefix="/forecasting", tags=["Forecasting"])


# ============== Helpers ==============

def get_forecast_repo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ForecastRepository:
    return ForecastRepository(db, user.tenant_id)


def get_budget_repo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> BudgetRepository:
    return BudgetRepository(db, user.tenant_id)


def get_kpi_repo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> KPIRepository:
    return KPIRepository(db, user.tenant_id)


def get_scenario_repo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ScenarioRepository:
    return ScenarioRepository(db, user.tenant_id)


def get_model_repo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ForecastModelRepository:
    return ForecastModelRepository(db, user.tenant_id)


# ============== FORECAST ROUTES ==============

@router.get("/forecasts", response_model=ForecastList)
async def list_forecasts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    forecast_type: Optional[List[ForecastType]] = Query(None),
    status: Optional[List[ForecastStatus]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    repo: ForecastRepository = Depends(get_forecast_repo),
    _: None = require_permission("forecasting.view")
):
    """Liste paginée des prévisions."""
    filters = ForecastFilters(search=search, forecast_type=forecast_type, status=status)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/forecasts/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_forecasts(
    prefix: str = Query(..., min_length=2),
    field: str = Query("name", pattern="^(name|code)$"),
    limit: int = Query(10, ge=1, le=50),
    repo: ForecastRepository = Depends(get_forecast_repo),
    _: None = require_permission("forecasting.view")
):
    """Autocomplete pour les prévisions."""
    items = repo.autocomplete(prefix, field, limit)
    return {"items": items}


@router.get("/forecasts/stats")
async def get_forecast_stats(
    repo: ForecastRepository = Depends(get_forecast_repo),
    _: None = require_permission("forecasting.view")
):
    """Statistiques des prévisions."""
    return repo.get_stats()


@router.get("/forecasts/{id}", response_model=ForecastResponse)
async def get_forecast(
    id: UUID,
    repo: ForecastRepository = Depends(get_forecast_repo),
    _: None = require_permission("forecasting.view")
):
    """Récupère une prévision par ID."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return entity


@router.post("/forecasts", response_model=ForecastResponse, status_code=201)
async def create_forecast(
    data: ForecastCreate,
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.create")
):
    """Crée une nouvelle prévision."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/forecasts/{id}", response_model=ForecastResponse)
async def update_forecast(
    id: UUID,
    data: ForecastUpdate,
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Met à jour une prévision."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Forecast not found")

    if data.code and data.code != entity.code:
        if repo.code_exists(data.code, exclude_id=id):
            raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")

    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/forecasts/{id}", status_code=204)
async def delete_forecast(
    id: UUID,
    hard: bool = Query(False),
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.delete")
):
    """Supprime une prévision."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Forecast not found")

    can_delete, reason = entity.can_delete()
    if not can_delete:
        raise HTTPException(status_code=400, detail=reason)

    if hard:
        repo.hard_delete(entity)
    else:
        repo.soft_delete(entity, user.id)


@router.post("/forecasts/{id}/approve", response_model=ForecastResponse)
async def approve_forecast(
    id: UUID,
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.approve")
):
    """Approuve une prévision."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Forecast not found")

    from datetime import datetime
    return repo.update(entity, {
        "status": ForecastStatus.APPROVED,
        "approved_by": user.id,
        "approved_at": datetime.utcnow()
    }, user.id)


# ============== BUDGET ROUTES ==============

@router.get("/budgets", response_model=BudgetList)
async def list_budgets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    fiscal_year: Optional[int] = Query(None),
    status: Optional[List[BudgetStatus]] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    repo: BudgetRepository = Depends(get_budget_repo),
    _: None = require_permission("forecasting.view")
):
    """Liste paginée des budgets."""
    filters = BudgetFilters(search=search, fiscal_year=fiscal_year, status=status)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/budgets/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_budgets(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: BudgetRepository = Depends(get_budget_repo),
    _: None = require_permission("forecasting.view")
):
    """Autocomplete pour les budgets."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/budgets/{id}", response_model=BudgetResponse)
async def get_budget(
    id: UUID,
    repo: BudgetRepository = Depends(get_budget_repo),
    _: None = require_permission("forecasting.view")
):
    """Récupère un budget par ID."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")
    return entity


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    data: BudgetCreate,
    repo: BudgetRepository = Depends(get_budget_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.create")
):
    """Crée un nouveau budget."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/budgets/{id}", response_model=BudgetResponse)
async def update_budget(
    id: UUID,
    data: BudgetUpdate,
    repo: BudgetRepository = Depends(get_budget_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Met à jour un budget."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")

    if data.code and data.code != entity.code:
        if repo.code_exists(data.code, exclude_id=id):
            raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")

    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/budgets/{id}", status_code=204)
async def delete_budget(
    id: UUID,
    repo: BudgetRepository = Depends(get_budget_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.delete")
):
    """Supprime un budget."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")

    can_delete, reason = entity.can_delete()
    if not can_delete:
        raise HTTPException(status_code=400, detail=reason)

    repo.soft_delete(entity, user.id)


@router.post("/budgets/{id}/submit", response_model=BudgetResponse)
async def submit_budget(
    id: UUID,
    repo: BudgetRepository = Depends(get_budget_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Soumet un budget pour approbation."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")

    from datetime import datetime
    return repo.update(entity, {
        "status": BudgetStatus.SUBMITTED,
        "submitted_by": user.id,
        "submitted_at": datetime.utcnow()
    }, user.id)


@router.post("/budgets/{id}/approve", response_model=BudgetResponse)
async def approve_budget(
    id: UUID,
    repo: BudgetRepository = Depends(get_budget_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.approve")
):
    """Approuve un budget."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")

    from datetime import datetime
    return repo.update(entity, {
        "status": BudgetStatus.APPROVED,
        "approved_by": user.id,
        "approved_at": datetime.utcnow()
    }, user.id)


@router.get("/budgets/{id}/variance", response_model=VarianceReport)
async def get_budget_variance(
    id: UUID,
    repo: BudgetRepository = Depends(get_budget_repo),
    _: None = require_permission("forecasting.view")
):
    """Rapport de variance budgétaire."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Construire le rapport de variance
    lines = []
    for line in entity.lines or []:
        total_budget = sum(line.get("period_amounts", {}).values()) if isinstance(line, dict) else 0
        lines.append({
            "account_code": line.get("account_code", ""),
            "account_name": line.get("account_name", ""),
            "budget": float(total_budget),
            "actual": 0,
            "variance": float(total_budget),
            "variance_percent": 100.0,
            "variance_type": "favorable"
        })

    return {
        "budget_id": entity.id,
        "name": entity.name,
        "fiscal_year": entity.fiscal_year,
        "total_budget": float(entity.total_budget),
        "total_actual": float(entity.total_actual),
        "total_variance": float(entity.total_variance),
        "variance_percent": float(entity.variance_percent),
        "lines": lines
    }


# ============== KPI ROUTES ==============

@router.get("/kpis", response_model=KPIList)
async def list_kpis(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=2),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    repo: KPIRepository = Depends(get_kpi_repo),
    _: None = require_permission("forecasting.view")
):
    """Liste paginée des KPIs."""
    filters = KPIFilters(search=search, category=category, is_active=is_active)
    items, total = repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/kpis/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_kpis(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    repo: KPIRepository = Depends(get_kpi_repo),
    _: None = require_permission("forecasting.view")
):
    """Autocomplete pour les KPIs."""
    items = repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/kpis/dashboard", response_model=KPIDashboard)
async def get_kpi_dashboard(
    repo: KPIRepository = Depends(get_kpi_repo),
    _: None = require_permission("forecasting.view")
):
    """Tableau de bord KPI."""
    return repo.get_dashboard_data()


@router.get("/kpis/{id}", response_model=KPIResponse)
async def get_kpi(
    id: UUID,
    repo: KPIRepository = Depends(get_kpi_repo),
    _: None = require_permission("forecasting.view")
):
    """Récupère un KPI par ID."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="KPI not found")
    return entity


@router.post("/kpis", response_model=KPIResponse, status_code=201)
async def create_kpi(
    data: KPICreate,
    repo: KPIRepository = Depends(get_kpi_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.create")
):
    """Crée un nouveau KPI."""
    if data.code and repo.code_exists(data.code):
        raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")
    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/kpis/{id}", response_model=KPIResponse)
async def update_kpi(
    id: UUID,
    data: KPIUpdate,
    repo: KPIRepository = Depends(get_kpi_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Met à jour un KPI."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="KPI not found")

    if data.code and data.code != entity.code:
        if repo.code_exists(data.code, exclude_id=id):
            raise HTTPException(status_code=409, detail=f"Code {data.code} already exists")

    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.post("/kpis/{id}/value", response_model=KPIResponse)
async def update_kpi_value(
    id: UUID,
    data: KPIValueUpdate,
    repo: KPIRepository = Depends(get_kpi_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Met à jour la valeur d'un KPI."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="KPI not found")

    from datetime import datetime
    from decimal import Decimal

    # Déterminer la tendance
    trend = "stable"
    if entity.current_value != Decimal("0"):
        if data.value > entity.current_value:
            trend = "up"
        elif data.value < entity.current_value:
            trend = "down"

    # Déterminer le statut
    from .models import KPIStatus
    status = KPIStatus.GREEN
    if data.value < entity.amber_threshold:
        status = KPIStatus.AMBER
    if data.value < entity.red_threshold:
        status = KPIStatus.RED

    # Calculer achievement
    achievement = Decimal("0")
    if entity.target_value != Decimal("0"):
        achievement = (data.value / entity.target_value * 100).quantize(Decimal("0.01"))

    # Historique
    historical = entity.historical_values or []
    historical.append({
        "date": (data.measurement_date or datetime.utcnow()).isoformat(),
        "value": float(data.value),
        "status": status.value
    })

    return repo.update(entity, {
        "previous_value": entity.current_value,
        "current_value": data.value,
        "achievement_percent": achievement,
        "trend": trend,
        "status": status,
        "last_measured_at": data.measurement_date or datetime.utcnow(),
        "historical_values": historical
    }, user.id)


@router.delete("/kpis/{id}", status_code=204)
async def delete_kpi(
    id: UUID,
    repo: KPIRepository = Depends(get_kpi_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.delete")
):
    """Supprime un KPI."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="KPI not found")
    repo.soft_delete(entity, user.id)


# ============== SCENARIO ROUTES ==============

@router.get("/scenarios/forecast/{forecast_id}")
async def list_scenarios_for_forecast(
    forecast_id: UUID,
    repo: ScenarioRepository = Depends(get_scenario_repo),
    _: None = require_permission("forecasting.view")
):
    """Liste les scénarios d'une prévision."""
    return repo.get_by_forecast(forecast_id)


@router.get("/scenarios/{id}", response_model=ScenarioResponse)
async def get_scenario(
    id: UUID,
    repo: ScenarioRepository = Depends(get_scenario_repo),
    _: None = require_permission("forecasting.view")
):
    """Récupère un scénario par ID."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return entity


@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    data: ScenarioCreate,
    repo: ScenarioRepository = Depends(get_scenario_repo),
    forecast_repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.create")
):
    """Crée un nouveau scénario."""
    # Vérifier que la prévision de base existe
    base_forecast = forecast_repo.get_by_id(data.base_forecast_id)
    if not base_forecast:
        raise HTTPException(status_code=404, detail="Base forecast not found")

    return repo.create(data.model_dump(exclude_unset=True), user.id)


@router.put("/scenarios/{id}", response_model=ScenarioResponse)
async def update_scenario(
    id: UUID,
    data: ScenarioUpdate,
    repo: ScenarioRepository = Depends(get_scenario_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.edit")
):
    """Met à jour un scénario."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return repo.update(entity, data.model_dump(exclude_unset=True), user.id)


@router.delete("/scenarios/{id}", status_code=204)
async def delete_scenario(
    id: UUID,
    repo: ScenarioRepository = Depends(get_scenario_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.delete")
):
    """Supprime un scénario."""
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Scenario not found")
    repo.soft_delete(entity, user.id)


@router.post("/scenarios/compare", response_model=ScenarioComparison)
async def compare_scenarios(
    scenario_ids: List[UUID],
    repo: ScenarioRepository = Depends(get_scenario_repo),
    _: None = require_permission("forecasting.view")
):
    """Compare plusieurs scénarios."""
    scenarios = []
    for sid in scenario_ids:
        s = repo.get_by_id(sid)
        if s:
            scenarios.append({
                "id": str(s.id),
                "name": s.name,
                "type": s.scenario_type.value,
                "total": float(s.total_forecasted),
                "variance": float(s.variance_from_baseline)
            })

    # Comparer par période
    periods = []
    # TODO: implémenter la comparaison détaillée par période

    return {"scenarios": scenarios, "periods": periods}


# ============== BULK OPERATIONS ==============

@router.post("/forecasts/bulk/create", response_model=BulkResult)
async def bulk_create_forecasts(
    request: BulkCreateRequest,
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.create")
):
    """Création en masse de prévisions."""
    errors = []
    valid = []

    for i, item in enumerate(request.items):
        if item.code and repo.code_exists(item.code):
            errors.append({"index": i, "error": f"Code {item.code} already exists"})
        else:
            valid.append(item.model_dump())

    count = repo.bulk_create(valid, user.id) if valid else 0
    return {"success": count, "errors": errors}


@router.post("/forecasts/bulk/delete", response_model=BulkResult)
async def bulk_delete_forecasts(
    request: BulkDeleteRequest,
    repo: ForecastRepository = Depends(get_forecast_repo),
    user=Depends(get_current_user),
    _: None = require_permission("forecasting.delete")
):
    """Suppression en masse de prévisions."""
    errors = []
    deletable = []

    for id in request.ids:
        entity = repo.get_by_id(id)
        if not entity:
            errors.append({"id": str(id), "error": "Not found"})
        else:
            can, reason = entity.can_delete()
            if can:
                deletable.append(id)
            else:
                errors.append({"id": str(id), "error": reason})

    count = repo.bulk_delete(deletable, user.id, request.hard) if deletable else 0
    return {"success": count, "errors": errors}
