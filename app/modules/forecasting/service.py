"""
Module Forecasting / Prévisions - GAP-076

Prévisions et projections:
- Prévision des ventes
- Prévision de trésorerie
- Prévision de stock
- Modèles statistiques
- Scénarios What-If
- Budgétisation
- KPIs et tableaux de bord
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
import math


# ============== Énumérations ==============

class ForecastType(str, Enum):
    """Type de prévision."""
    SALES = "sales"
    REVENUE = "revenue"
    CASH_FLOW = "cash_flow"
    INVENTORY = "inventory"
    DEMAND = "demand"
    EXPENSE = "expense"
    HEADCOUNT = "headcount"
    CUSTOM = "custom"


class ForecastMethod(str, Enum):
    """Méthode de prévision."""
    MOVING_AVERAGE = "moving_average"
    WEIGHTED_AVERAGE = "weighted_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL = "seasonal"
    ARIMA = "arima"
    MANUAL = "manual"
    HYBRID = "hybrid"


class Granularity(str, Enum):
    """Granularité temporelle."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ScenarioType(str, Enum):
    """Type de scénario."""
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    CUSTOM = "custom"


class ForecastStatus(str, Enum):
    """Statut de la prévision."""
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    ARCHIVED = "archived"


class BudgetStatus(str, Enum):
    """Statut du budget."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class VarianceType(str, Enum):
    """Type d'écart."""
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    ON_TARGET = "on_target"


# ============== Data Classes ==============

@dataclass
class HistoricalData:
    """Données historiques."""
    id: str
    tenant_id: str
    forecast_type: ForecastType
    category: str = ""  # Catégorie de données

    # Période
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    granularity: Granularity = Granularity.MONTHLY

    # Données
    values: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"date": "2024-01", "value": 10000, "metadata": {...}}, ...]

    # Source
    source: str = ""
    is_verified: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ForecastModel:
    """Modèle de prévision."""
    id: str
    tenant_id: str
    name: str
    description: str

    forecast_type: ForecastType = ForecastType.SALES
    method: ForecastMethod = ForecastMethod.MOVING_AVERAGE

    # Paramètres du modèle
    parameters: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"window_size": 3, "alpha": 0.3, "seasonal_period": 12}

    # Données d'entrée
    historical_data_ids: List[str] = field(default_factory=list)
    training_period_months: int = 12

    # Métriques de performance
    accuracy_metrics: Dict[str, Decimal] = field(default_factory=dict)
    # Ex: {"mape": 5.2, "mae": 1200, "rmse": 1500}

    last_trained_at: Optional[datetime] = None
    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ForecastPeriod:
    """Période de prévision."""
    period: str  # "2024-01", "2024-Q1", etc.
    value: Decimal = Decimal("0")
    confidence_low: Decimal = Decimal("0")
    confidence_high: Decimal = Decimal("0")
    confidence_level: int = 95

    # Composantes (si décomposition)
    trend: Decimal = Decimal("0")
    seasonal: Decimal = Decimal("0")
    residual: Decimal = Decimal("0")

    # Ajustements
    manual_adjustment: Decimal = Decimal("0")
    adjusted_value: Decimal = Decimal("0")


@dataclass
class Forecast:
    """Prévision."""
    id: str
    tenant_id: str
    name: str
    description: str

    forecast_type: ForecastType = ForecastType.SALES
    status: ForecastStatus = ForecastStatus.DRAFT

    # Modèle utilisé
    model_id: Optional[str] = None
    method: ForecastMethod = ForecastMethod.MOVING_AVERAGE

    # Période de prévision
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    granularity: Granularity = Granularity.MONTHLY

    # Données
    periods: List[ForecastPeriod] = field(default_factory=list)

    # Agrégats
    total_forecasted: Decimal = Decimal("0")
    average_per_period: Decimal = Decimal("0")

    # Comparaison avec réel
    actual_to_date: Decimal = Decimal("0")
    variance: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")

    # Catégorisation
    category: str = ""
    tags: List[str] = field(default_factory=list)

    # Approbation
    approved_by: str = ""
    approved_at: Optional[datetime] = None

    # Métadonnées
    assumptions: List[str] = field(default_factory=list)
    notes: str = ""

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Scenario:
    """Scénario de prévision."""
    id: str
    tenant_id: str
    name: str
    description: str

    scenario_type: ScenarioType = ScenarioType.BASELINE

    # Prévision de base
    base_forecast_id: str = ""

    # Ajustements
    adjustment_type: str = "percent"  # percent, absolute
    adjustment_value: Decimal = Decimal("0")

    # Hypothèses spécifiques
    assumptions: Dict[str, Any] = field(default_factory=dict)

    # Résultats
    periods: List[ForecastPeriod] = field(default_factory=list)
    total_forecasted: Decimal = Decimal("0")

    # Comparaison avec baseline
    variance_from_baseline: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")

    is_active: bool = True

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BudgetLine:
    """Ligne de budget."""
    id: str
    budget_id: str
    account_code: str
    account_name: str

    # Montants par période
    period_amounts: Dict[str, Decimal] = field(default_factory=dict)
    # Ex: {"2024-01": 5000, "2024-02": 5500, ...}

    total_budget: Decimal = Decimal("0")
    total_actual: Decimal = Decimal("0")
    variance: Decimal = Decimal("0")

    notes: str = ""


@dataclass
class Budget:
    """Budget."""
    id: str
    tenant_id: str
    name: str
    description: str

    # Période
    fiscal_year: int = 2024
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    granularity: Granularity = Granularity.MONTHLY

    status: BudgetStatus = BudgetStatus.DRAFT

    # Lignes
    lines: List[BudgetLine] = field(default_factory=list)

    # Totaux
    total_budget: Decimal = Decimal("0")
    total_actual: Decimal = Decimal("0")
    total_variance: Decimal = Decimal("0")
    variance_percent: Decimal = Decimal("0")

    # Départements
    department_id: str = ""
    department_name: str = ""

    # Approbation
    submitted_by: str = ""
    submitted_at: Optional[datetime] = None
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""

    # Version
    version: int = 1
    parent_budget_id: Optional[str] = None

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KPI:
    """Indicateur clé de performance."""
    id: str
    tenant_id: str
    name: str
    code: str
    description: str

    # Type et calcul
    category: str = ""
    formula: str = ""
    unit: str = ""

    # Valeurs
    current_value: Decimal = Decimal("0")
    target_value: Decimal = Decimal("0")
    previous_value: Decimal = Decimal("0")

    # Performance
    achievement_percent: Decimal = Decimal("0")
    trend: str = "stable"  # up, down, stable

    # Seuils
    green_threshold: Decimal = Decimal("0")
    amber_threshold: Decimal = Decimal("0")
    red_threshold: Decimal = Decimal("0")

    # Statut
    status: str = "green"  # green, amber, red

    # Fréquence
    update_frequency: str = "monthly"
    last_updated: Optional[datetime] = None

    # Historique
    historical_values: List[Dict[str, Any]] = field(default_factory=list)

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ForecastAccuracy:
    """Précision des prévisions."""
    forecast_id: str
    evaluation_date: date

    # Métriques
    mape: Decimal = Decimal("0")  # Mean Absolute Percentage Error
    mae: Decimal = Decimal("0")  # Mean Absolute Error
    rmse: Decimal = Decimal("0")  # Root Mean Square Error
    bias: Decimal = Decimal("0")  # Biais systématique

    # Par période
    period_accuracy: List[Dict[str, Any]] = field(default_factory=list)

    # Score global
    accuracy_score: Decimal = Decimal("0")


@dataclass
class CashFlowForecast:
    """Prévision de trésorerie."""
    id: str
    tenant_id: str
    name: str

    # Période
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    granularity: Granularity = Granularity.WEEKLY

    # Solde initial
    opening_balance: Decimal = Decimal("0")

    # Prévisions par période
    periods: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"period": "2024-W01", "inflows": 50000, "outflows": 45000, "net": 5000, "closing": 105000}]

    # Agrégats
    total_inflows: Decimal = Decimal("0")
    total_outflows: Decimal = Decimal("0")
    net_cash_flow: Decimal = Decimal("0")
    closing_balance: Decimal = Decimal("0")

    # Alertes
    low_cash_alerts: List[Dict[str, Any]] = field(default_factory=list)
    min_balance_threshold: Decimal = Decimal("0")

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# ============== Service Principal ==============

class ForecastingService:
    """Service de prévisions."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._historical_data: Dict[str, HistoricalData] = {}
        self._models: Dict[str, ForecastModel] = {}
        self._forecasts: Dict[str, Forecast] = {}
        self._scenarios: Dict[str, Scenario] = {}
        self._budgets: Dict[str, Budget] = {}
        self._kpis: Dict[str, KPI] = {}
        self._cash_flows: Dict[str, CashFlowForecast] = {}

    # ===== Données historiques =====

    def import_historical_data(
        self,
        forecast_type: ForecastType,
        values: List[Dict[str, Any]],
        *,
        category: str = "",
        granularity: Granularity = Granularity.MONTHLY,
        source: str = ""
    ) -> HistoricalData:
        """Importer des données historiques."""
        data_id = str(uuid.uuid4())

        # Déterminer la période
        dates = [v["date"] for v in values if "date" in v]
        period_start = min(dates) if dates else date.today()
        period_end = max(dates) if dates else date.today()

        # Convertir en dates si nécessaire
        if isinstance(period_start, str):
            period_start = date.fromisoformat(period_start[:10])
        if isinstance(period_end, str):
            period_end = date.fromisoformat(period_end[:10])

        data = HistoricalData(
            id=data_id,
            tenant_id=self.tenant_id,
            forecast_type=forecast_type,
            category=category,
            period_start=period_start,
            period_end=period_end,
            granularity=granularity,
            values=values,
            source=source
        )

        self._historical_data[data_id] = data
        return data

    def get_historical_data(
        self,
        forecast_type: ForecastType,
        *,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Récupérer les données historiques."""
        all_values = []

        for data in self._historical_data.values():
            if data.tenant_id != self.tenant_id:
                continue
            if data.forecast_type != forecast_type:
                continue
            if category and data.category != category:
                continue

            for v in data.values:
                v_date = v.get("date")
                if isinstance(v_date, str):
                    v_date = date.fromisoformat(v_date[:10])

                if start_date and v_date < start_date:
                    continue
                if end_date and v_date > end_date:
                    continue

                all_values.append(v)

        return sorted(all_values, key=lambda x: x.get("date", ""))

    # ===== Modèles de prévision =====

    def create_model(
        self,
        name: str,
        forecast_type: ForecastType,
        method: ForecastMethod,
        *,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        historical_data_ids: Optional[List[str]] = None
    ) -> ForecastModel:
        """Créer un modèle de prévision."""
        model_id = str(uuid.uuid4())

        # Paramètres par défaut selon la méthode
        default_params = self._get_default_parameters(method)
        params = {**default_params, **(parameters or {})}

        model = ForecastModel(
            id=model_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            forecast_type=forecast_type,
            method=method,
            parameters=params,
            historical_data_ids=historical_data_ids or []
        )

        self._models[model_id] = model
        return model

    def _get_default_parameters(self, method: ForecastMethod) -> Dict[str, Any]:
        """Obtenir les paramètres par défaut d'une méthode."""
        defaults = {
            ForecastMethod.MOVING_AVERAGE: {"window_size": 3},
            ForecastMethod.WEIGHTED_AVERAGE: {"weights": [0.5, 0.3, 0.2]},
            ForecastMethod.EXPONENTIAL_SMOOTHING: {"alpha": 0.3},
            ForecastMethod.LINEAR_REGRESSION: {},
            ForecastMethod.SEASONAL: {"seasonal_period": 12},
            ForecastMethod.ARIMA: {"p": 1, "d": 1, "q": 1},
            ForecastMethod.MANUAL: {},
            ForecastMethod.HYBRID: {}
        }
        return defaults.get(method, {})

    def train_model(
        self,
        model_id: str,
        training_data: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ForecastModel]:
        """Entraîner un modèle."""
        model = self._models.get(model_id)
        if not model or model.tenant_id != self.tenant_id:
            return None

        # Récupérer les données d'entraînement
        if not training_data:
            training_data = []
            for data_id in model.historical_data_ids:
                data = self._historical_data.get(data_id)
                if data:
                    training_data.extend(data.values)

        if not training_data:
            return None

        # Calculer les métriques (simulation)
        values = [float(v.get("value", 0)) for v in training_data if "value" in v]
        if values:
            # MAPE simplifié
            mean_val = sum(values) / len(values)
            mape = Decimal(str(abs(values[-1] - mean_val) / mean_val * 100)) if mean_val != 0 else Decimal("0")

            model.accuracy_metrics = {
                "mape": mape.quantize(Decimal("0.01")),
                "sample_size": len(values)
            }

        model.last_trained_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()

        return model

    # ===== Génération de prévisions =====

    def generate_forecast(
        self,
        name: str,
        forecast_type: ForecastType,
        start_date: date,
        end_date: date,
        *,
        description: str = "",
        method: ForecastMethod = ForecastMethod.MOVING_AVERAGE,
        model_id: Optional[str] = None,
        granularity: Granularity = Granularity.MONTHLY,
        category: str = "",
        created_by: str = ""
    ) -> Forecast:
        """Générer une prévision."""
        forecast_id = str(uuid.uuid4())

        # Récupérer les données historiques
        historical = self.get_historical_data(
            forecast_type,
            category=category if category else None
        )

        # Générer les périodes
        periods = self._generate_periods(
            start_date, end_date, granularity, historical, method
        )

        # Calculer les totaux
        total = sum(p.adjusted_value or p.value for p in periods)
        avg = total / len(periods) if periods else Decimal("0")

        forecast = Forecast(
            id=forecast_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            forecast_type=forecast_type,
            method=method,
            model_id=model_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            periods=periods,
            total_forecasted=total,
            average_per_period=avg,
            category=category,
            created_by=created_by
        )

        self._forecasts[forecast_id] = forecast
        return forecast

    def _generate_periods(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity,
        historical: List[Dict[str, Any]],
        method: ForecastMethod
    ) -> List[ForecastPeriod]:
        """Générer les périodes de prévision."""
        periods = []

        # Extraire les valeurs historiques
        hist_values = [float(v.get("value", 0)) for v in historical if "value" in v]

        current = start_date
        period_num = 0

        while current <= end_date:
            period_str = self._format_period(current, granularity)

            # Calculer la valeur prédite
            value = self._calculate_forecast_value(
                hist_values, period_num, method
            )

            # Intervalle de confiance
            std_dev = self._calculate_std_dev(hist_values) if hist_values else Decimal("0")
            margin = std_dev * Decimal("1.96")  # 95% confidence

            period = ForecastPeriod(
                period=period_str,
                value=value,
                confidence_low=value - margin,
                confidence_high=value + margin,
                adjusted_value=value
            )

            periods.append(period)

            # Avancer à la période suivante
            current = self._next_period(current, granularity)
            period_num += 1

        return periods

    def _calculate_forecast_value(
        self,
        historical: List[float],
        period_num: int,
        method: ForecastMethod
    ) -> Decimal:
        """Calculer la valeur prévue."""
        if not historical:
            return Decimal("0")

        if method == ForecastMethod.MOVING_AVERAGE:
            window = min(3, len(historical))
            avg = sum(historical[-window:]) / window
            return Decimal(str(avg)).quantize(Decimal("0.01"))

        elif method == ForecastMethod.WEIGHTED_AVERAGE:
            window = min(3, len(historical))
            weights = [0.5, 0.3, 0.2][:window]
            total_weight = sum(weights)
            weighted_sum = sum(
                historical[-(i+1)] * weights[i]
                for i in range(window)
            )
            return Decimal(str(weighted_sum / total_weight)).quantize(Decimal("0.01"))

        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            alpha = 0.3
            forecast = historical[0]
            for val in historical[1:]:
                forecast = alpha * val + (1 - alpha) * forecast
            return Decimal(str(forecast)).quantize(Decimal("0.01"))

        elif method == ForecastMethod.LINEAR_REGRESSION:
            n = len(historical)
            if n < 2:
                return Decimal(str(historical[-1])).quantize(Decimal("0.01"))

            x_mean = (n - 1) / 2
            y_mean = sum(historical) / n

            numerator = sum((i - x_mean) * (historical[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return Decimal(str(y_mean)).quantize(Decimal("0.01"))

            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            forecast = intercept + slope * (n + period_num)
            return Decimal(str(forecast)).quantize(Decimal("0.01"))

        elif method == ForecastMethod.SEASONAL:
            # Saisonnalité simple (12 mois)
            season_length = 12
            if len(historical) >= season_length:
                season_index = period_num % season_length
                same_season_values = [
                    historical[i]
                    for i in range(season_index, len(historical), season_length)
                ]
                if same_season_values:
                    return Decimal(str(sum(same_season_values) / len(same_season_values))).quantize(Decimal("0.01"))

            return Decimal(str(sum(historical) / len(historical))).quantize(Decimal("0.01"))

        else:  # MANUAL ou autre
            return Decimal(str(historical[-1])).quantize(Decimal("0.01"))

    def _calculate_std_dev(self, values: List[float]) -> Decimal:
        """Calculer l'écart-type."""
        if len(values) < 2:
            return Decimal("0")

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return Decimal(str(math.sqrt(variance))).quantize(Decimal("0.01"))

    def _format_period(self, dt: date, granularity: Granularity) -> str:
        """Formater une période."""
        if granularity == Granularity.DAILY:
            return dt.isoformat()
        elif granularity == Granularity.WEEKLY:
            return f"{dt.year}-W{dt.isocalendar()[1]:02d}"
        elif granularity == Granularity.MONTHLY:
            return f"{dt.year}-{dt.month:02d}"
        elif granularity == Granularity.QUARTERLY:
            quarter = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{quarter}"
        else:
            return str(dt.year)

    def _next_period(self, dt: date, granularity: Granularity) -> date:
        """Obtenir la prochaine période."""
        if granularity == Granularity.DAILY:
            return dt + timedelta(days=1)
        elif granularity == Granularity.WEEKLY:
            return dt + timedelta(weeks=1)
        elif granularity == Granularity.MONTHLY:
            month = dt.month + 1
            year = dt.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            return date(year, month, 1)
        elif granularity == Granularity.QUARTERLY:
            month = dt.month + 3
            year = dt.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            return date(year, month, 1)
        else:
            return date(dt.year + 1, 1, 1)

    def adjust_forecast(
        self,
        forecast_id: str,
        period: str,
        adjustment: Decimal,
        reason: str = ""
    ) -> Optional[Forecast]:
        """Ajuster une période de prévision."""
        forecast = self._forecasts.get(forecast_id)
        if not forecast or forecast.tenant_id != self.tenant_id:
            return None

        for p in forecast.periods:
            if p.period == period:
                p.manual_adjustment = adjustment
                p.adjusted_value = p.value + adjustment
                break

        # Recalculer les totaux
        forecast.total_forecasted = sum(p.adjusted_value for p in forecast.periods)
        forecast.average_per_period = forecast.total_forecasted / len(forecast.periods) if forecast.periods else Decimal("0")
        forecast.updated_at = datetime.utcnow()

        return forecast

    def approve_forecast(
        self,
        forecast_id: str,
        approved_by: str
    ) -> Optional[Forecast]:
        """Approuver une prévision."""
        forecast = self._forecasts.get(forecast_id)
        if not forecast or forecast.tenant_id != self.tenant_id:
            return None

        forecast.status = ForecastStatus.APPROVED
        forecast.approved_by = approved_by
        forecast.approved_at = datetime.utcnow()
        forecast.updated_at = datetime.utcnow()

        return forecast

    def get_forecast(self, forecast_id: str) -> Optional[Forecast]:
        """Récupérer une prévision."""
        forecast = self._forecasts.get(forecast_id)
        if forecast and forecast.tenant_id == self.tenant_id:
            return forecast
        return None

    def list_forecasts(
        self,
        forecast_type: Optional[ForecastType] = None,
        status: Optional[ForecastStatus] = None
    ) -> List[Forecast]:
        """Lister les prévisions."""
        forecasts = [
            f for f in self._forecasts.values()
            if f.tenant_id == self.tenant_id
        ]

        if forecast_type:
            forecasts = [f for f in forecasts if f.forecast_type == forecast_type]

        if status:
            forecasts = [f for f in forecasts if f.status == status]

        return sorted(forecasts, key=lambda x: x.created_at, reverse=True)

    # ===== Scénarios =====

    def create_scenario(
        self,
        name: str,
        base_forecast_id: str,
        scenario_type: ScenarioType,
        adjustment_value: Decimal,
        *,
        description: str = "",
        adjustment_type: str = "percent",
        assumptions: Optional[Dict[str, Any]] = None,
        created_by: str = ""
    ) -> Optional[Scenario]:
        """Créer un scénario."""
        base_forecast = self._forecasts.get(base_forecast_id)
        if not base_forecast or base_forecast.tenant_id != self.tenant_id:
            return None

        scenario_id = str(uuid.uuid4())

        # Calculer les périodes ajustées
        periods = []
        for p in base_forecast.periods:
            if adjustment_type == "percent":
                adjusted = p.adjusted_value * (1 + adjustment_value / 100)
            else:
                adjusted = p.adjusted_value + adjustment_value

            periods.append(ForecastPeriod(
                period=p.period,
                value=adjusted,
                adjusted_value=adjusted
            ))

        total = sum(p.value for p in periods)
        variance = total - base_forecast.total_forecasted
        variance_pct = (variance / base_forecast.total_forecasted * 100) if base_forecast.total_forecasted else Decimal("0")

        scenario = Scenario(
            id=scenario_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            scenario_type=scenario_type,
            base_forecast_id=base_forecast_id,
            adjustment_type=adjustment_type,
            adjustment_value=adjustment_value,
            assumptions=assumptions or {},
            periods=periods,
            total_forecasted=total,
            variance_from_baseline=variance,
            variance_percent=variance_pct,
            created_by=created_by
        )

        self._scenarios[scenario_id] = scenario
        return scenario

    def compare_scenarios(
        self,
        scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """Comparer plusieurs scénarios."""
        comparison = {
            "scenarios": [],
            "periods": []
        }

        scenarios = [
            self._scenarios.get(sid)
            for sid in scenario_ids
            if sid in self._scenarios
        ]

        scenarios = [s for s in scenarios if s and s.tenant_id == self.tenant_id]

        for scenario in scenarios:
            comparison["scenarios"].append({
                "id": scenario.id,
                "name": scenario.name,
                "type": scenario.scenario_type.value,
                "total": float(scenario.total_forecasted),
                "variance": float(scenario.variance_from_baseline)
            })

        # Comparer par période
        if scenarios:
            for i, period in enumerate(scenarios[0].periods):
                period_data = {
                    "period": period.period,
                    "values": {
                        s.name: float(s.periods[i].value) if i < len(s.periods) else 0
                        for s in scenarios
                    }
                }
                comparison["periods"].append(period_data)

        return comparison

    # ===== Budgets =====

    def create_budget(
        self,
        name: str,
        fiscal_year: int,
        start_date: date,
        end_date: date,
        *,
        description: str = "",
        department_id: str = "",
        department_name: str = "",
        granularity: Granularity = Granularity.MONTHLY,
        created_by: str = ""
    ) -> Budget:
        """Créer un budget."""
        budget_id = str(uuid.uuid4())

        budget = Budget(
            id=budget_id,
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            fiscal_year=fiscal_year,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            department_id=department_id,
            department_name=department_name,
            created_by=created_by
        )

        self._budgets[budget_id] = budget
        return budget

    def add_budget_line(
        self,
        budget_id: str,
        account_code: str,
        account_name: str,
        period_amounts: Dict[str, Decimal]
    ) -> Optional[Budget]:
        """Ajouter une ligne de budget."""
        budget = self._budgets.get(budget_id)
        if not budget or budget.tenant_id != self.tenant_id:
            return None

        line_id = str(uuid.uuid4())
        total = sum(period_amounts.values())

        line = BudgetLine(
            id=line_id,
            budget_id=budget_id,
            account_code=account_code,
            account_name=account_name,
            period_amounts=period_amounts,
            total_budget=total
        )

        budget.lines.append(line)
        budget.total_budget = sum(l.total_budget for l in budget.lines)
        budget.updated_at = datetime.utcnow()

        return budget

    def record_actual(
        self,
        budget_id: str,
        account_code: str,
        period: str,
        actual_amount: Decimal
    ) -> Optional[Budget]:
        """Enregistrer une valeur réelle."""
        budget = self._budgets.get(budget_id)
        if not budget or budget.tenant_id != self.tenant_id:
            return None

        for line in budget.lines:
            if line.account_code == account_code:
                line.total_actual += actual_amount
                budgeted = line.period_amounts.get(period, Decimal("0"))
                line.variance = line.total_budget - line.total_actual
                break

        # Recalculer les totaux
        budget.total_actual = sum(l.total_actual for l in budget.lines)
        budget.total_variance = budget.total_budget - budget.total_actual
        budget.variance_percent = (budget.total_variance / budget.total_budget * 100) if budget.total_budget else Decimal("0")
        budget.updated_at = datetime.utcnow()

        return budget

    def submit_budget(
        self,
        budget_id: str,
        submitted_by: str
    ) -> Optional[Budget]:
        """Soumettre un budget pour approbation."""
        budget = self._budgets.get(budget_id)
        if not budget or budget.tenant_id != self.tenant_id:
            return None

        budget.status = BudgetStatus.SUBMITTED
        budget.submitted_by = submitted_by
        budget.submitted_at = datetime.utcnow()
        budget.updated_at = datetime.utcnow()

        return budget

    def approve_budget(
        self,
        budget_id: str,
        approved_by: str
    ) -> Optional[Budget]:
        """Approuver un budget."""
        budget = self._budgets.get(budget_id)
        if not budget or budget.tenant_id != self.tenant_id:
            return None

        budget.status = BudgetStatus.APPROVED
        budget.approved_by = approved_by
        budget.approved_at = datetime.utcnow()
        budget.updated_at = datetime.utcnow()

        return budget

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        """Récupérer un budget."""
        budget = self._budgets.get(budget_id)
        if budget and budget.tenant_id == self.tenant_id:
            return budget
        return None

    def get_budget_variance_report(
        self,
        budget_id: str
    ) -> Optional[Dict[str, Any]]:
        """Générer un rapport de variance budgétaire."""
        budget = self._budgets.get(budget_id)
        if not budget or budget.tenant_id != self.tenant_id:
            return None

        lines = []
        for line in budget.lines:
            variance_type = VarianceType.ON_TARGET
            if line.variance > 0:
                variance_type = VarianceType.FAVORABLE
            elif line.variance < 0:
                variance_type = VarianceType.UNFAVORABLE

            pct = (line.variance / line.total_budget * 100) if line.total_budget else Decimal("0")

            lines.append({
                "account_code": line.account_code,
                "account_name": line.account_name,
                "budget": float(line.total_budget),
                "actual": float(line.total_actual),
                "variance": float(line.variance),
                "variance_percent": float(pct),
                "variance_type": variance_type.value
            })

        return {
            "budget_id": budget_id,
            "name": budget.name,
            "fiscal_year": budget.fiscal_year,
            "total_budget": float(budget.total_budget),
            "total_actual": float(budget.total_actual),
            "total_variance": float(budget.total_variance),
            "variance_percent": float(budget.variance_percent),
            "lines": lines
        }

    # ===== KPIs =====

    def create_kpi(
        self,
        name: str,
        code: str,
        *,
        description: str = "",
        category: str = "",
        unit: str = "",
        target_value: Decimal = Decimal("0"),
        green_threshold: Decimal = Decimal("0"),
        amber_threshold: Decimal = Decimal("0"),
        red_threshold: Decimal = Decimal("0")
    ) -> KPI:
        """Créer un KPI."""
        kpi_id = str(uuid.uuid4())

        kpi = KPI(
            id=kpi_id,
            tenant_id=self.tenant_id,
            name=name,
            code=code,
            description=description,
            category=category,
            unit=unit,
            target_value=target_value,
            green_threshold=green_threshold,
            amber_threshold=amber_threshold,
            red_threshold=red_threshold
        )

        self._kpis[kpi_id] = kpi
        return kpi

    def update_kpi_value(
        self,
        kpi_id: str,
        value: Decimal,
        measurement_date: Optional[datetime] = None
    ) -> Optional[KPI]:
        """Mettre à jour la valeur d'un KPI."""
        kpi = self._kpis.get(kpi_id)
        if not kpi or kpi.tenant_id != self.tenant_id:
            return None

        now = measurement_date or datetime.utcnow()

        # Déterminer la tendance
        if kpi.current_value != Decimal("0"):
            if value > kpi.current_value:
                kpi.trend = "up"
            elif value < kpi.current_value:
                kpi.trend = "down"
            else:
                kpi.trend = "stable"

        kpi.previous_value = kpi.current_value
        kpi.current_value = value

        # Calculer l'achievement
        if kpi.target_value != Decimal("0"):
            kpi.achievement_percent = (value / kpi.target_value * 100).quantize(Decimal("0.01"))

        # Déterminer le statut
        if value >= kpi.green_threshold:
            kpi.status = "green"
        elif value >= kpi.amber_threshold:
            kpi.status = "amber"
        else:
            kpi.status = "red"

        # Historique
        kpi.historical_values.append({
            "date": now.isoformat(),
            "value": float(value),
            "status": kpi.status
        })

        kpi.last_updated = now

        return kpi

    def get_kpi_dashboard(self) -> Dict[str, Any]:
        """Obtenir le tableau de bord des KPIs."""
        kpis = [k for k in self._kpis.values() if k.tenant_id == self.tenant_id and k.is_active]

        by_status = {"green": 0, "amber": 0, "red": 0}
        by_category: Dict[str, List[Dict]] = {}

        for kpi in kpis:
            by_status[kpi.status] = by_status.get(kpi.status, 0) + 1

            cat = kpi.category or "Other"
            if cat not in by_category:
                by_category[cat] = []

            by_category[cat].append({
                "id": kpi.id,
                "name": kpi.name,
                "code": kpi.code,
                "current_value": float(kpi.current_value),
                "target_value": float(kpi.target_value),
                "achievement_percent": float(kpi.achievement_percent),
                "status": kpi.status,
                "trend": kpi.trend,
                "unit": kpi.unit
            })

        return {
            "total_kpis": len(kpis),
            "by_status": by_status,
            "by_category": by_category,
            "alerts": [
                {
                    "kpi_id": k.id,
                    "name": k.name,
                    "status": k.status,
                    "value": float(k.current_value)
                }
                for k in kpis if k.status == "red"
            ]
        }

    # ===== Cash Flow =====

    def create_cash_flow_forecast(
        self,
        name: str,
        start_date: date,
        end_date: date,
        opening_balance: Decimal,
        *,
        granularity: Granularity = Granularity.WEEKLY,
        min_balance_threshold: Decimal = Decimal("0")
    ) -> CashFlowForecast:
        """Créer une prévision de trésorerie."""
        cf_id = str(uuid.uuid4())

        cf = CashFlowForecast(
            id=cf_id,
            tenant_id=self.tenant_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            opening_balance=opening_balance,
            min_balance_threshold=min_balance_threshold
        )

        self._cash_flows[cf_id] = cf
        return cf

    def add_cash_flow_period(
        self,
        cf_id: str,
        period: str,
        inflows: Decimal,
        outflows: Decimal
    ) -> Optional[CashFlowForecast]:
        """Ajouter une période de trésorerie."""
        cf = self._cash_flows.get(cf_id)
        if not cf or cf.tenant_id != self.tenant_id:
            return None

        # Calculer le solde
        previous_closing = cf.opening_balance
        if cf.periods:
            previous_closing = Decimal(str(cf.periods[-1].get("closing", cf.opening_balance)))

        net = inflows - outflows
        closing = previous_closing + net

        cf.periods.append({
            "period": period,
            "inflows": float(inflows),
            "outflows": float(outflows),
            "net": float(net),
            "opening": float(previous_closing),
            "closing": float(closing)
        })

        # Mettre à jour les totaux
        cf.total_inflows += inflows
        cf.total_outflows += outflows
        cf.net_cash_flow = cf.total_inflows - cf.total_outflows
        cf.closing_balance = closing

        # Vérifier les alertes
        if closing < cf.min_balance_threshold:
            cf.low_cash_alerts.append({
                "period": period,
                "closing_balance": float(closing),
                "threshold": float(cf.min_balance_threshold),
                "shortfall": float(cf.min_balance_threshold - closing)
            })

        cf.updated_at = datetime.utcnow()

        return cf

    def get_cash_flow_forecast(self, cf_id: str) -> Optional[CashFlowForecast]:
        """Récupérer une prévision de trésorerie."""
        cf = self._cash_flows.get(cf_id)
        if cf and cf.tenant_id == self.tenant_id:
            return cf
        return None


# ============== Factory ==============

def create_forecasting_service(tenant_id: str) -> ForecastingService:
    """Factory pour créer une instance du service."""
    return ForecastingService(tenant_id)
