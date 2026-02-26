"""
AZALSCORE Finance Cash Forecast Router V3
==========================================

Endpoints REST pour les prévisions de trésorerie.

Endpoints:
- GET  /v3/finance/cash-forecast/forecast - Générer une prévision
- GET  /v3/finance/cash-forecast/position - Position de trésorerie
- POST /v3/finance/cash-forecast/simulate - Simuler une transaction
- GET  /v3/finance/cash-forecast/alerts - Alertes de trésorerie
- GET  /v3/finance/cash-forecast/scenarios - Liste des scénarios
- GET  /v3/finance/cash-forecast/health - Health check
"""
from __future__ import annotations


import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.dependencies_v2 import get_saas_context

from .service import (
    CashForecastService,
    ForecastGranularity,
    ScenarioType,
    AlertSeverity,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v3/finance/cash-forecast", tags=["Finance Cash Forecast"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ForecastEntryResponse(BaseModel):
    """Entrée de prévision."""

    date: str
    opening_balance: Decimal
    closing_balance: Decimal
    total_inflows: Decimal
    total_outflows: Decimal
    net_change: Decimal
    confidence: float


class ForecastPeriodResponse(BaseModel):
    """Période de prévision."""

    id: str
    scenario: str
    start_date: str
    end_date: str
    granularity: str

    total_inflows: Decimal
    total_outflows: Decimal
    net_change: Decimal

    min_balance: Decimal
    max_balance: Decimal
    avg_balance: Decimal
    min_balance_date: Optional[str] = None

    confidence: float
    entries: list[ForecastEntryResponse] = Field(default_factory=list)


class AlertResponse(BaseModel):
    """Alerte de trésorerie."""

    id: str
    type: str
    severity: str
    date: str
    message: str
    amount: Optional[Decimal] = None
    threshold: Optional[Decimal] = None
    recommendation: Optional[str] = None


class ForecastResponse(BaseModel):
    """Réponse de prévision complète."""

    success: bool
    tenant_id: str
    generated_at: str
    current_balance: Decimal
    current_date: str
    forecasts: list[ForecastPeriodResponse] = Field(default_factory=list)
    alerts: list[AlertResponse] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    error: Optional[str] = None


class PositionResponse(BaseModel):
    """Position de trésorerie."""

    total_balance: Decimal
    date: str
    accounts: list[dict] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    """Requête de simulation."""

    amount: Decimal = Field(..., description="Montant de la transaction")
    transaction_date: str = Field(..., description="Date de la transaction (YYYY-MM-DD)")
    is_inflow: bool = Field(..., description="True si encaissement, False si décaissement")


class AlertSummaryResponse(BaseModel):
    """Résumé des alertes."""

    total_alerts: int
    critical: int
    warning: int
    info: int
    alerts: list[dict] = Field(default_factory=list)


class ScenarioInfo(BaseModel):
    """Information sur un scénario."""

    id: str
    name: str
    description: str
    inflow_factor: float
    outflow_factor: float


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_cash_forecast_service(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context),
) -> CashForecastService:
    """Dépendance pour obtenir le service de prévision."""
    return CashForecastService(db=db, tenant_id=context.tenant_id)


# =============================================================================
# HELPERS
# =============================================================================


def forecast_result_to_response(result) -> ForecastResponse:
    """Convertit un ForecastResult en réponse API."""
    forecasts = []
    for fp in result.forecasts:
        entries = [
            ForecastEntryResponse(
                date=e.date.isoformat(),
                opening_balance=e.opening_balance,
                closing_balance=e.closing_balance,
                total_inflows=e.total_inflows,
                total_outflows=e.total_outflows,
                net_change=e.net_change,
                confidence=e.confidence,
            )
            for e in fp.entries
        ]

        forecasts.append(ForecastPeriodResponse(
            id=fp.id,
            scenario=fp.scenario.value,
            start_date=fp.start_date.isoformat(),
            end_date=fp.end_date.isoformat(),
            granularity=fp.granularity.value,
            total_inflows=fp.total_inflows,
            total_outflows=fp.total_outflows,
            net_change=fp.net_change,
            min_balance=fp.min_balance,
            max_balance=fp.max_balance,
            avg_balance=fp.avg_balance,
            min_balance_date=fp.min_balance_date.isoformat() if fp.min_balance_date else None,
            confidence=fp.confidence,
            entries=entries,
        ))

    alerts = [
        AlertResponse(
            id=a.id,
            type=a.type.value,
            severity=a.severity.value,
            date=a.date.isoformat(),
            message=a.message,
            amount=a.amount,
            threshold=a.threshold,
            recommendation=a.recommendation,
        )
        for a in result.alerts
    ]

    return ForecastResponse(
        success=result.success,
        tenant_id=result.tenant_id,
        generated_at=result.generated_at.isoformat(),
        current_balance=result.current_balance,
        current_date=result.current_date.isoformat(),
        forecasts=forecasts,
        alerts=alerts,
        summary=result.summary,
        error=result.error,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Générer une prévision de trésorerie",
    description="Génère une prévision de trésorerie avec scénarios multiples.",
)
async def get_forecast(
    days: int = Query(90, ge=1, le=365, description="Nombre de jours de prévision"),
    scenarios: Optional[str] = Query(
        None,
        description="Scénarios (base,optimistic,pessimistic,stress), séparés par virgule",
    ),
    granularity: str = Query(
        "daily",
        description="Granularité (daily, weekly, monthly)",
    ),
    include_entries: bool = Query(
        True,
        description="Inclure le détail des entrées",
    ),
    service: CashForecastService = Depends(get_cash_forecast_service),
):
    """
    Génère une prévision de trésorerie.

    Paramètres:
    - **days**: Nombre de jours de prévision (1-365)
    - **scenarios**: Scénarios à calculer (base, optimistic, pessimistic, stress)
    - **granularity**: Granularité (daily, weekly, monthly)

    Retourne les prévisions avec:
    - Soldes projetés par période
    - Alertes de trésorerie
    - Résumé avec indicateurs clés
    """
    # Parser les scénarios
    scenario_list = [ScenarioType.BASE]
    if scenarios:
        scenario_list = []
        for s in scenarios.split(","):
            s = s.strip().lower()
            try:
                scenario_list.append(ScenarioType(s))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Scénario invalide: {s}. Valeurs acceptées: base, optimistic, pessimistic, stress",
                )

    # Parser la granularité
    try:
        granularity_enum = ForecastGranularity(granularity.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Granularité invalide: {granularity}. Valeurs acceptées: daily, weekly, monthly",
        )

    result = await service.generate_forecast(
        days=days,
        scenarios=scenario_list,
        granularity=granularity_enum,
    )

    response = forecast_result_to_response(result)

    # Supprimer les entrées si non demandées
    if not include_entries:
        for forecast in response.forecasts:
            forecast.entries = []

    return response


@router.get(
    "/position",
    response_model=PositionResponse,
    summary="Position de trésorerie actuelle",
    description="Retourne la position de trésorerie actuelle.",
)
async def get_cash_position(
    service: CashForecastService = Depends(get_cash_forecast_service),
):
    """
    Retourne la position de trésorerie actuelle.

    Inclut:
    - Solde total
    - Date de la position
    - Détail par compte (si disponible)
    """
    result = await service.get_cash_position()
    return PositionResponse(
        total_balance=Decimal(result["total_balance"]),
        date=result["date"],
        accounts=result.get("accounts", []),
    )


@router.post(
    "/simulate",
    response_model=ForecastResponse,
    summary="Simuler une transaction",
    description="Simule l'impact d'une transaction sur les prévisions.",
)
async def simulate_transaction(
    request: SimulationRequest,
    service: CashForecastService = Depends(get_cash_forecast_service),
):
    """
    Simule l'impact d'une transaction sur les prévisions de trésorerie.

    Paramètres:
    - **amount**: Montant de la transaction
    - **transaction_date**: Date de la transaction
    - **is_inflow**: True si encaissement, False si décaissement

    Retourne les prévisions modifiées avec l'impact de la transaction.
    """
    try:
        transaction_date = date.fromisoformat(request.transaction_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de date invalide. Utilisez YYYY-MM-DD",
        )

    result = await service.simulate_transaction(
        amount=request.amount,
        transaction_date=transaction_date,
        is_inflow=request.is_inflow,
    )

    return forecast_result_to_response(result)


@router.get(
    "/alerts",
    response_model=AlertSummaryResponse,
    summary="Alertes de trésorerie",
    description="Retourne un résumé des alertes de trésorerie.",
)
async def get_alerts(
    service: CashForecastService = Depends(get_cash_forecast_service),
):
    """
    Retourne un résumé des alertes de trésorerie.

    Inclut:
    - Nombre d'alertes par sévérité
    - Liste des alertes les plus importantes
    """
    result = await service.get_alert_summary()
    return AlertSummaryResponse(**result)


@router.get(
    "/scenarios",
    summary="Liste des scénarios disponibles",
    description="Retourne la liste des scénarios de prévision disponibles.",
)
async def get_scenarios():
    """
    Retourne les scénarios de prévision disponibles.

    Chaque scénario applique des facteurs différents aux encaissements et décaissements.
    """
    scenarios = [
        ScenarioInfo(
            id="base",
            name="Base",
            description="Scénario de référence avec les données actuelles",
            inflow_factor=1.0,
            outflow_factor=1.0,
        ),
        ScenarioInfo(
            id="optimistic",
            name="Optimiste",
            description="Encaissements +15%, décaissements -10%",
            inflow_factor=1.15,
            outflow_factor=0.90,
        ),
        ScenarioInfo(
            id="pessimistic",
            name="Pessimiste",
            description="Encaissements -15%, décaissements +10%",
            inflow_factor=0.85,
            outflow_factor=1.10,
        ),
        ScenarioInfo(
            id="stress",
            name="Stress",
            description="Encaissements -40%, décaissements +30%",
            inflow_factor=0.60,
            outflow_factor=1.30,
        ),
    ]

    return {
        "scenarios": [s.model_dump() for s in scenarios],
        "default": "base",
    }


@router.get(
    "/health",
    summary="Health check prévision trésorerie",
    description="Vérifie que le service de prévision est fonctionnel.",
)
async def health_check():
    """Health check pour le service de prévision de trésorerie."""
    return {
        "status": "healthy",
        "service": "finance-cash-forecast",
        "features": [
            "multi_scenario_forecast",
            "daily_weekly_monthly_granularity",
            "automatic_alerts",
            "transaction_simulation",
            "recurring_items_support",
        ],
        "max_forecast_days": 365,
        "scenarios": ["base", "optimistic", "pessimistic", "stress"],
    }
