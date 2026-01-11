"""
AZALS - API Trésorerie
Calcul de trésorerie prévisionnelle avec déclenchement RED automatique
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user_and_tenant
from app.services.treasury import TreasuryService


router = APIRouter(prefix="/treasury", tags=["treasury"])


class ForecastRequest(BaseModel):
    """Demande de calcul de trésorerie prévisionnelle."""
    opening_balance: int
    inflows: int
    outflows: int


class ForecastResponse(BaseModel):
    """Réponse avec calcul de trésorerie."""
    id: str
    opening_balance: float
    inflows: float
    outflows: float
    forecast_balance: float
    red_triggered: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/forecast", response_model=ForecastResponse)
def create_treasury_forecast(
    request: ForecastRequest,
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Calcule une prévision de trésorerie.
    
    Règle : Si forecast_balance < 0, déclenche automatiquement une décision RED.
    """
    service = TreasuryService(db)
    forecast = service.calculate_forecast(
        opening_balance=request.opening_balance,
        inflows=request.inflows,
        outflows=request.outflows,
        tenant_id=context["tenant_id"],
        user_id=context["user_id"]
    )
    
    red_triggered = forecast.forecast_balance < 0
    
    return ForecastResponse(
        id=str(forecast.id),
        opening_balance=float(forecast.opening_balance),
        inflows=float(forecast.inflows),
        outflows=float(forecast.outflows),
        forecast_balance=float(forecast.forecast_balance),
        red_triggered=red_triggered,
        created_at=forecast.created_at.isoformat()
    )


@router.get("/latest", response_model=Optional[ForecastResponse])
def get_latest_treasury_forecast(
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Récupère la dernière prévision de trésorerie du tenant.
    """
    service = TreasuryService(db)
    forecast = service.get_latest_forecast(context["tenant_id"])
    
    if not forecast:
        return None
    
    red_triggered = forecast.forecast_balance < 0
    
    return ForecastResponse(
        id=str(forecast.id),
        opening_balance=float(forecast.opening_balance),
        inflows=float(forecast.inflows),
        outflows=float(forecast.outflows),
        forecast_balance=float(forecast.forecast_balance),
        red_triggered=red_triggered,
        created_at=forecast.created_at.isoformat()
    )
