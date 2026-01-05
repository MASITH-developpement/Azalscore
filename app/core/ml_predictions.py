"""
AZALS - Machine Learning Predictions ÉLITE
============================================
Prédictions ML pour ERP: trésorerie, ventes, risques.
Utilise des modèles simples mais efficaces.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import json

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PredictionType(str, Enum):
    """Types de prédictions disponibles."""
    TREASURY = "treasury"
    SALES = "sales"
    REVENUE = "revenue"
    RISK = "risk"
    SEASONALITY = "seasonality"


class RiskLevel(str, Enum):
    """Niveaux de risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PredictionResult:
    """Résultat d'une prédiction."""
    prediction_type: PredictionType
    predicted_value: float
    confidence: float  # 0-100%
    horizon_days: int
    trend: str  # "up", "down", "stable"
    risk_level: Optional[RiskLevel] = None
    explanation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class TreasuryPrediction:
    """Prédiction de trésorerie."""
    date: datetime
    predicted_balance: float
    min_balance: float
    max_balance: float
    confidence: float
    risk_level: RiskLevel
    warning: Optional[str] = None


class SimpleMovingAverageModel:
    """
    Modèle de moyenne mobile simple.
    Rapide et efficace pour les prédictions à court terme.
    """

    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        self.history: deque = deque(maxlen=window_size * 4)

    def fit(self, values: List[float]) -> None:
        """Entraîne le modèle sur les données historiques."""
        self.history.extend(values)

    def predict(self, horizon: int = 7) -> List[float]:
        """Prédit les prochaines valeurs."""
        if len(self.history) < self.window_size:
            # Pas assez de données, retourne la moyenne
            avg = sum(self.history) / len(self.history) if self.history else 0
            return [avg] * horizon

        predictions = []
        working_history = list(self.history)

        for _ in range(horizon):
            # Moyenne mobile
            ma = sum(working_history[-self.window_size:]) / self.window_size
            predictions.append(ma)
            working_history.append(ma)

        return predictions


class ExponentialSmoothingModel:
    """
    Lissage exponentiel simple.
    Bon pour capturer les tendances récentes.
    """

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.last_value: Optional[float] = None
        self.trend: float = 0

    def fit(self, values: List[float]) -> None:
        """Entraîne le modèle."""
        if not values:
            return

        self.last_value = values[0]
        for value in values[1:]:
            self.last_value = self.alpha * value + (1 - self.alpha) * self.last_value

        # Calculer la tendance
        if len(values) >= 2:
            recent_trend = (values[-1] - values[-len(values)//2]) / (len(values)//2)
            self.trend = self.alpha * recent_trend

    def predict(self, horizon: int = 7) -> List[float]:
        """Prédit les prochaines valeurs."""
        if self.last_value is None:
            return [0] * horizon

        predictions = []
        current = self.last_value
        for i in range(horizon):
            current = current + self.trend
            predictions.append(current)

        return predictions


class SeasonalityDetector:
    """Détecte les patterns saisonniers dans les données."""

    def __init__(self, period: int = 7):
        self.period = period
        self.seasonal_factors: List[float] = []

    def fit(self, values: List[float]) -> None:
        """Analyse les patterns saisonniers."""
        if len(values) < self.period * 2:
            self.seasonal_factors = [1.0] * self.period
            return

        # Calculer les facteurs saisonniers
        n_periods = len(values) // self.period
        factors = []

        for i in range(self.period):
            period_values = [values[j * self.period + i]
                           for j in range(n_periods)
                           if j * self.period + i < len(values)]
            if period_values:
                factors.append(sum(period_values) / len(period_values))
            else:
                factors.append(1.0)

        # Normaliser
        avg = sum(factors) / len(factors) if factors else 1.0
        self.seasonal_factors = [f / avg if avg > 0 else 1.0 for f in factors]

    def get_factor(self, day_index: int) -> float:
        """Retourne le facteur saisonnier pour un jour donné."""
        if not self.seasonal_factors:
            return 1.0
        return self.seasonal_factors[day_index % self.period]


class MLPredictionService:
    """
    Service de prédictions ML ÉLITE.

    Fonctionnalités:
    - Prédiction de trésorerie
    - Prédiction de ventes
    - Analyse de risques
    - Détection de saisonnalité
    """

    def __init__(self):
        self.sma_model = SimpleMovingAverageModel(window_size=7)
        self.exp_model = ExponentialSmoothingModel(alpha=0.3)
        self.seasonality = SeasonalityDetector(period=7)

    def predict_treasury(
        self,
        historical_balances: List[Dict[str, Any]],
        planned_inflows: List[Dict[str, Any]] = None,
        planned_outflows: List[Dict[str, Any]] = None,
        horizon_days: int = 30
    ) -> List[TreasuryPrediction]:
        """
        Prédit la trésorerie future.

        Args:
            historical_balances: Historique des soldes [{date, balance}]
            planned_inflows: Entrées planifiées [{date, amount}]
            planned_outflows: Sorties planifiées [{date, amount}]
            horizon_days: Jours de prédiction

        Returns:
            Liste de prédictions de trésorerie
        """
        if not historical_balances:
            return []

        # Extraire les valeurs
        values = [float(h.get("balance", 0)) for h in historical_balances]

        # Entraîner les modèles
        self.sma_model.fit(values)
        self.exp_model.fit(values)
        self.seasonality.fit(values)

        # Prédictions de base
        sma_predictions = self.sma_model.predict(horizon_days)
        exp_predictions = self.exp_model.predict(horizon_days)

        # Combiner les prédictions (ensemble)
        combined = [
            0.4 * sma + 0.6 * exp
            for sma, exp in zip(sma_predictions, exp_predictions)
        ]

        # Appliquer la saisonnalité
        today = datetime.now()
        predictions = []

        for i, pred in enumerate(combined):
            pred_date = today + timedelta(days=i + 1)
            seasonal_factor = self.seasonality.get_factor(pred_date.weekday())
            adjusted_pred = pred * seasonal_factor

            # Ajouter les flux planifiés
            if planned_inflows:
                for inflow in planned_inflows:
                    inflow_date = inflow.get("date")
                    if isinstance(inflow_date, str):
                        inflow_date = datetime.fromisoformat(inflow_date.replace("Z", ""))
                    if inflow_date and inflow_date.date() == pred_date.date():
                        adjusted_pred += float(inflow.get("amount", 0))

            if planned_outflows:
                for outflow in planned_outflows:
                    outflow_date = outflow.get("date")
                    if isinstance(outflow_date, str):
                        outflow_date = datetime.fromisoformat(outflow_date.replace("Z", ""))
                    if outflow_date and outflow_date.date() == pred_date.date():
                        adjusted_pred -= float(outflow.get("amount", 0))

            # Calculer l'intervalle de confiance
            std_dev = np.std(values) if len(values) > 1 else abs(adjusted_pred * 0.1)
            min_balance = adjusted_pred - 1.96 * std_dev
            max_balance = adjusted_pred + 1.96 * std_dev

            # Calculer le niveau de risque
            if adjusted_pred < 0:
                risk_level = RiskLevel.CRITICAL
                warning = f"ALERTE: Trésorerie négative prévue ({adjusted_pred:,.0f}€)"
            elif adjusted_pred < values[-1] * 0.2:
                risk_level = RiskLevel.HIGH
                warning = "Trésorerie basse prévue"
            elif adjusted_pred < values[-1] * 0.5:
                risk_level = RiskLevel.MEDIUM
                warning = None
            else:
                risk_level = RiskLevel.LOW
                warning = None

            # Confiance basée sur la volatilité
            volatility = std_dev / abs(adjusted_pred) if adjusted_pred != 0 else 1
            confidence = max(0, min(100, 100 - volatility * 100))

            predictions.append(TreasuryPrediction(
                date=pred_date,
                predicted_balance=round(adjusted_pred, 2),
                min_balance=round(min_balance, 2),
                max_balance=round(max_balance, 2),
                confidence=round(confidence, 1),
                risk_level=risk_level,
                warning=warning
            ))

        return predictions

    def predict_sales(
        self,
        historical_sales: List[Dict[str, Any]],
        horizon_days: int = 30
    ) -> PredictionResult:
        """
        Prédit les ventes futures.

        Args:
            historical_sales: Historique des ventes [{date, amount}]
            horizon_days: Jours de prédiction

        Returns:
            Résultat de prédiction
        """
        if not historical_sales:
            return PredictionResult(
                prediction_type=PredictionType.SALES,
                predicted_value=0,
                confidence=0,
                horizon_days=horizon_days,
                trend="stable",
                explanation="Pas de données historiques"
            )

        values = [float(s.get("amount", 0)) for s in historical_sales]

        # Entraîner et prédire
        self.exp_model.fit(values)
        predictions = self.exp_model.predict(horizon_days)

        # Calculer les métriques
        total_predicted = sum(predictions)
        avg_historical = sum(values) / len(values)
        avg_predicted = total_predicted / horizon_days

        # Déterminer la tendance
        if avg_predicted > avg_historical * 1.1:
            trend = "up"
        elif avg_predicted < avg_historical * 0.9:
            trend = "down"
        else:
            trend = "stable"

        # Confiance
        std_dev = np.std(values) if len(values) > 1 else avg_historical * 0.1
        confidence = max(0, min(100, 100 - (std_dev / avg_historical * 50) if avg_historical else 0))

        return PredictionResult(
            prediction_type=PredictionType.SALES,
            predicted_value=round(total_predicted, 2),
            confidence=round(confidence, 1),
            horizon_days=horizon_days,
            trend=trend,
            explanation=f"Prédiction basée sur {len(values)} jours d'historique",
            details={
                "daily_predictions": [round(p, 2) for p in predictions[:7]],
                "avg_daily": round(avg_predicted, 2),
                "trend_percentage": round((avg_predicted / avg_historical - 1) * 100, 1) if avg_historical else 0
            }
        )

    def analyze_risk(
        self,
        treasury_predictions: List[TreasuryPrediction],
        sales_prediction: Optional[PredictionResult] = None
    ) -> PredictionResult:
        """
        Analyse le risque global.

        Args:
            treasury_predictions: Prédictions de trésorerie
            sales_prediction: Prédiction de ventes (optionnel)

        Returns:
            Analyse de risque
        """
        if not treasury_predictions:
            return PredictionResult(
                prediction_type=PredictionType.RISK,
                predicted_value=0,
                confidence=0,
                horizon_days=0,
                trend="stable",
                risk_level=RiskLevel.LOW,
                explanation="Pas de données pour l'analyse"
            )

        # Compter les jours par niveau de risque
        risk_counts = {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.LOW: 0
        }

        for pred in treasury_predictions:
            risk_counts[pred.risk_level] += 1

        # Calculer le score de risque (0-100)
        total = len(treasury_predictions)
        risk_score = (
            (risk_counts[RiskLevel.CRITICAL] * 100 +
             risk_counts[RiskLevel.HIGH] * 70 +
             risk_counts[RiskLevel.MEDIUM] * 40 +
             risk_counts[RiskLevel.LOW] * 10) / total
        )

        # Déterminer le niveau global
        if risk_score >= 70:
            overall_risk = RiskLevel.CRITICAL
            trend = "up"
        elif risk_score >= 50:
            overall_risk = RiskLevel.HIGH
            trend = "up"
        elif risk_score >= 30:
            overall_risk = RiskLevel.MEDIUM
            trend = "stable"
        else:
            overall_risk = RiskLevel.LOW
            trend = "down"

        # Générer l'explication
        critical_days = [p.date.strftime("%Y-%m-%d") for p in treasury_predictions
                        if p.risk_level == RiskLevel.CRITICAL]

        if critical_days:
            explanation = f"ALERTE: {len(critical_days)} jour(s) à risque critique: {', '.join(critical_days[:3])}"
        elif risk_counts[RiskLevel.HIGH] > 0:
            explanation = f"{risk_counts[RiskLevel.HIGH]} jour(s) à haut risque sur la période"
        else:
            explanation = "Situation financière stable sur la période"

        return PredictionResult(
            prediction_type=PredictionType.RISK,
            predicted_value=round(risk_score, 1),
            confidence=85.0,  # Confiance fixe pour l'analyse de risque
            horizon_days=total,
            trend=trend,
            risk_level=overall_risk,
            explanation=explanation,
            details={
                "critical_days": len(critical_days),
                "high_risk_days": risk_counts[RiskLevel.HIGH],
                "medium_risk_days": risk_counts[RiskLevel.MEDIUM],
                "low_risk_days": risk_counts[RiskLevel.LOW],
                "critical_dates": critical_days[:5]
            }
        )

    def detect_anomalies(
        self,
        values: List[float],
        threshold_sigma: float = 2.5
    ) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies dans une série de données.

        Args:
            values: Liste de valeurs
            threshold_sigma: Seuil en écarts-types

        Returns:
            Liste d'anomalies détectées
        """
        if len(values) < 3:
            return []

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return []

        anomalies = []
        for i, value in enumerate(values):
            z_score = abs(value - mean) / std
            if z_score > threshold_sigma:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": round(z_score, 2),
                    "expected_range": {
                        "min": round(mean - threshold_sigma * std, 2),
                        "max": round(mean + threshold_sigma * std, 2)
                    },
                    "deviation_percent": round((value - mean) / mean * 100, 1) if mean else 0
                })

        return anomalies


# Instance globale
ml_service = MLPredictionService()


def get_ml_service() -> MLPredictionService:
    """Retourne l'instance du service ML."""
    return ml_service
