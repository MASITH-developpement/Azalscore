"""
AZALS - API Predictions ML ÉLITE
=================================
Endpoints pour les prédictions ML.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id, get_current_user
from app.core.models import User
from app.core.ml_predictions import (
    get_ml_service,
    PredictionResult,
    TreasuryPrediction,
    PredictionType,
    RiskLevel
)


router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


# ============================================================================
# SCHEMAS
# ============================================================================

class HistoricalDataPoint(BaseModel):
    """Point de données historique."""
    date: str
    amount: float


class PlannedFlow(BaseModel):
    """Flux planifié (entrée ou sortie)."""
    date: str
    amount: float
    description: Optional[str] = None


class TreasuryPredictionRequest(BaseModel):
    """Requête de prédiction de trésorerie."""
    historical_balances: List[HistoricalDataPoint] = Field(
        ...,
        description="Historique des soldes (minimum 7 jours recommandé)"
    )
    planned_inflows: Optional[List[PlannedFlow]] = None
    planned_outflows: Optional[List[PlannedFlow]] = None
    horizon_days: int = Field(default=30, ge=1, le=90)


class TreasuryPredictionResponse(BaseModel):
    """Réponse de prédiction de trésorerie."""
    date: str
    predicted_balance: float
    min_balance: float
    max_balance: float
    confidence: float
    risk_level: str
    warning: Optional[str] = None


class SalesPredictionRequest(BaseModel):
    """Requête de prédiction de ventes."""
    historical_sales: List[HistoricalDataPoint] = Field(
        ...,
        description="Historique des ventes"
    )
    horizon_days: int = Field(default=30, ge=1, le=90)


class PredictionResultResponse(BaseModel):
    """Réponse de prédiction."""
    prediction_type: str
    predicted_value: float
    confidence: float
    horizon_days: int
    trend: str
    risk_level: Optional[str] = None
    explanation: Optional[str] = None
    details: Optional[dict] = None


class RiskAnalysisRequest(BaseModel):
    """Requête d'analyse de risque."""
    historical_balances: List[HistoricalDataPoint]
    historical_sales: Optional[List[HistoricalDataPoint]] = None
    horizon_days: int = Field(default=30, ge=1, le=90)


class AnomalyDetectionRequest(BaseModel):
    """Requête de détection d'anomalies."""
    values: List[float]
    threshold_sigma: float = Field(default=2.5, ge=1.0, le=5.0)


class AnomalyResponse(BaseModel):
    """Anomalie détectée."""
    index: int
    value: float
    z_score: float
    expected_range: dict
    deviation_percent: float


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/treasury", response_model=List[TreasuryPredictionResponse])
def predict_treasury(
    request: TreasuryPredictionRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Prédit la trésorerie future basée sur l'historique.

    Utilise un ensemble de modèles ML:
    - Moyenne mobile (SMA)
    - Lissage exponentiel
    - Détection de saisonnalité

    Retourne des prédictions avec intervalles de confiance et niveaux de risque.
    """
    ml_service = get_ml_service()

    # Convertir les données
    historical = [{"date": h.date, "balance": h.amount} for h in request.historical_balances]
    inflows = [{"date": f.date, "amount": f.amount} for f in request.planned_inflows] if request.planned_inflows else None
    outflows = [{"date": f.date, "amount": f.amount} for f in request.planned_outflows] if request.planned_outflows else None

    # Prédire
    predictions = ml_service.predict_treasury(
        historical_balances=historical,
        planned_inflows=inflows,
        planned_outflows=outflows,
        horizon_days=request.horizon_days
    )

    return [
        TreasuryPredictionResponse(
            date=p.date.isoformat(),
            predicted_balance=p.predicted_balance,
            min_balance=p.min_balance,
            max_balance=p.max_balance,
            confidence=p.confidence,
            risk_level=p.risk_level.value,
            warning=p.warning
        )
        for p in predictions
    ]


@router.post("/sales", response_model=PredictionResultResponse)
def predict_sales(
    request: SalesPredictionRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Prédit les ventes futures.

    Analyse les tendances historiques et projette les ventes attendues.
    """
    ml_service = get_ml_service()

    historical = [{"date": h.date, "amount": h.amount} for h in request.historical_sales]

    result = ml_service.predict_sales(
        historical_sales=historical,
        horizon_days=request.horizon_days
    )

    return PredictionResultResponse(
        prediction_type=result.prediction_type.value,
        predicted_value=result.predicted_value,
        confidence=result.confidence,
        horizon_days=result.horizon_days,
        trend=result.trend,
        risk_level=result.risk_level.value if result.risk_level else None,
        explanation=result.explanation,
        details=result.details
    )


@router.post("/risk-analysis", response_model=PredictionResultResponse)
def analyze_risk(
    request: RiskAnalysisRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Analyse le risque financier global.

    Combine les prédictions de trésorerie et de ventes pour évaluer le risque.
    """
    ml_service = get_ml_service()

    # Prédire la trésorerie
    historical = [{"date": h.date, "balance": h.amount} for h in request.historical_balances]
    treasury_predictions = ml_service.predict_treasury(
        historical_balances=historical,
        horizon_days=request.horizon_days
    )

    # Prédire les ventes si données fournies
    sales_prediction = None
    if request.historical_sales:
        sales_data = [{"date": h.date, "amount": h.amount} for h in request.historical_sales]
        sales_prediction = ml_service.predict_sales(
            historical_sales=sales_data,
            horizon_days=request.horizon_days
        )

    # Analyser le risque
    result = ml_service.analyze_risk(
        treasury_predictions=treasury_predictions,
        sales_prediction=sales_prediction
    )

    return PredictionResultResponse(
        prediction_type=result.prediction_type.value,
        predicted_value=result.predicted_value,
        confidence=result.confidence,
        horizon_days=result.horizon_days,
        trend=result.trend,
        risk_level=result.risk_level.value if result.risk_level else None,
        explanation=result.explanation,
        details=result.details
    )


@router.post("/anomalies", response_model=List[AnomalyResponse])
def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Détecte les anomalies dans une série de données.

    Utilise la méthode z-score pour identifier les valeurs aberrantes.
    """
    ml_service = get_ml_service()

    anomalies = ml_service.detect_anomalies(
        values=request.values,
        threshold_sigma=request.threshold_sigma
    )

    return [
        AnomalyResponse(
            index=a["index"],
            value=a["value"],
            z_score=a["z_score"],
            expected_range=a["expected_range"],
            deviation_percent=a["deviation_percent"]
        )
        for a in anomalies
    ]


@router.get("/demo")
def get_demo_prediction(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Retourne une prédiction démo avec des données simulées.
    Utile pour tester l'API.
    """
    ml_service = get_ml_service()

    # Générer des données de démo
    import random
    base_balance = 50000
    historical = []
    today = datetime.now()

    for i in range(30, 0, -1):
        date = today - timedelta(days=i)
        # Simulation réaliste avec tendance et bruit
        trend = i * 100  # Tendance légèrement à la hausse
        noise = random.gauss(0, 2000)
        seasonality = 5000 * (1 if date.weekday() < 5 else 0.5)  # Weekend plus bas
        balance = base_balance + trend + noise + seasonality
        historical.append({
            "date": date.isoformat(),
            "balance": round(balance, 2)
        })

    # Prédire
    predictions = ml_service.predict_treasury(
        historical_balances=historical,
        horizon_days=14
    )

    return {
        "historical_data_points": len(historical),
        "prediction_horizon_days": 14,
        "predictions": [
            {
                "date": p.date.strftime("%Y-%m-%d"),
                "balance": p.predicted_balance,
                "confidence": p.confidence,
                "risk_level": p.risk_level.value
            }
            for p in predictions[:7]  # Premiers 7 jours seulement pour la démo
        ],
        "summary": {
            "average_predicted_balance": round(sum(p.predicted_balance for p in predictions) / len(predictions), 2),
            "critical_days": sum(1 for p in predictions if p.risk_level.value == "critical"),
            "high_risk_days": sum(1 for p in predictions if p.risk_level.value == "high")
        }
    }
