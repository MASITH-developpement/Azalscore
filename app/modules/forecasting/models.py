"""
Modèles SQLAlchemy - Module Forecasting (GAP-076)

Multi-tenant obligatoire, Soft delete, Audit complet, Versioning.

Entités:
- Forecast: Prévisions (ventes, trésorerie, stocks)
- ForecastModel: Modèles statistiques
- Scenario: Scénarios What-If
- Budget: Budgétisation
- KPI: Indicateurs de performance
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
import uuid

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Numeric, Enum as SQLEnum, event
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


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


class ForecastStatus(str, Enum):
    """Statut de la prévision."""
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    ARCHIVED = "archived"

    @classmethod
    def allowed_transitions(cls) -> dict:
        return {
            cls.DRAFT: [cls.ACTIVE, cls.ARCHIVED],
            cls.ACTIVE: [cls.APPROVED, cls.ARCHIVED],
            cls.APPROVED: [cls.ARCHIVED],
            cls.ARCHIVED: []
        }


class ScenarioType(str, Enum):
    """Type de scénario."""
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    CUSTOM = "custom"


class BudgetStatus(str, Enum):
    """Statut du budget."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class KPIStatus(str, Enum):
    """Statut du KPI."""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# ============== Modèles ==============

class Forecast(Base):
    """
    Prévision financière ou opérationnelle.

    Multi-tenant, Soft delete, Audit complet.
    """
    __tablename__ = "forecasts"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Type et méthode ===
    forecast_type = Column(
        SQLEnum(ForecastType),
        default=ForecastType.SALES,
        nullable=False
    )
    method = Column(
        SQLEnum(ForecastMethod),
        default=ForecastMethod.MOVING_AVERAGE,
        nullable=False
    )
    status = Column(
        SQLEnum(ForecastStatus),
        default=ForecastStatus.DRAFT,
        nullable=False
    )

    # === Période ===
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    granularity = Column(
        SQLEnum(Granularity),
        default=Granularity.MONTHLY,
        nullable=False
    )

    # === Données de prévision ===
    periods = Column(JSONB, default=list)
    # Format: [{"period": "2024-01", "value": 10000, "confidence_low": 9000, "confidence_high": 11000}]

    # === Agrégats ===
    total_forecasted = Column(Numeric(18, 2), default=Decimal("0"))
    average_per_period = Column(Numeric(18, 2), default=Decimal("0"))

    # === Comparaison avec réel ===
    actual_to_date = Column(Numeric(18, 2), default=Decimal("0"))
    variance = Column(Numeric(18, 2), default=Decimal("0"))
    variance_percent = Column(Numeric(8, 2), default=Decimal("0"))

    # === Catégorisation ===
    category = Column(String(100), nullable=True)
    tags = Column(JSONB, default=list)  # List of strings

    # === Modèle utilisé ===
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey('forecast_models.id', ondelete='SET NULL'),
        nullable=True
    )

    # === Hypothèses ===
    assumptions = Column(JSONB, default=list)
    notes = Column(Text, nullable=True)

    # === Approbation ===
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_forecast_tenant', 'tenant_id'),
        Index('ix_forecast_tenant_code', 'tenant_id', 'code'),
        Index('ix_forecast_tenant_type', 'tenant_id', 'forecast_type'),
        Index('ix_forecast_tenant_status', 'tenant_id', 'status'),
        Index('ix_forecast_tenant_deleted', 'tenant_id', 'is_deleted'),
        UniqueConstraint('tenant_id', 'code', name='uq_forecast_tenant_code'),
        CheckConstraint('end_date >= start_date', name='ck_forecast_dates_valid'),
    )

    # === Relations ===
    model = relationship('ForecastModel', back_populates='forecasts')
    scenarios = relationship('Scenario', back_populates='base_forecast', cascade='all, delete-orphan')

    # === Validateurs ===
    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @validates('status')
    def validate_status_transition(self, key: str, new_status: ForecastStatus) -> ForecastStatus:
        if self.status is not None and new_status != self.status:
            allowed = ForecastStatus.allowed_transitions().get(self.status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        return new_status

    # === Propriétés ===
    @hybrid_property
    def is_approved(self) -> bool:
        return self.status == ForecastStatus.APPROVED

    @hybrid_property
    def display_name(self) -> str:
        return f"[{self.code}] {self.name}"

    def can_delete(self) -> tuple[bool, str]:
        """Vérifie si la prévision peut être supprimée."""
        if self.status == ForecastStatus.APPROVED:
            return False, "Cannot delete approved forecast"
        return True, ""

    def __repr__(self) -> str:
        return f"<Forecast {self.code}: {self.name}>"


class ForecastModel(Base):
    """
    Modèle statistique de prévision.

    Stocke les paramètres et métriques de performance.
    """
    __tablename__ = "forecast_models"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Configuration ===
    forecast_type = Column(
        SQLEnum(ForecastType),
        default=ForecastType.SALES,
        nullable=False
    )
    method = Column(
        SQLEnum(ForecastMethod),
        default=ForecastMethod.MOVING_AVERAGE,
        nullable=False
    )

    # === Paramètres ===
    parameters = Column(JSONB, default=dict)
    # Ex: {"window_size": 3, "alpha": 0.3, "seasonal_period": 12}

    training_period_months = Column(Integer, default=12)

    # === Métriques ===
    accuracy_metrics = Column(JSONB, default=dict)
    # Ex: {"mape": 5.2, "mae": 1200, "rmse": 1500}

    last_trained_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_fmodel_tenant', 'tenant_id'),
        Index('ix_fmodel_tenant_code', 'tenant_id', 'code'),
        UniqueConstraint('tenant_id', 'code', name='uq_fmodel_tenant_code'),
    )

    # === Relations ===
    forecasts = relationship('Forecast', back_populates='model')

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        if self.forecasts:
            return False, "Cannot delete model with associated forecasts"
        return True, ""

    def __repr__(self) -> str:
        return f"<ForecastModel {self.code}: {self.name}>"


class Scenario(Base):
    """
    Scénario What-If basé sur une prévision.
    """
    __tablename__ = "scenarios"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Type ===
    scenario_type = Column(
        SQLEnum(ScenarioType),
        default=ScenarioType.BASELINE,
        nullable=False
    )

    # === Prévision de base ===
    base_forecast_id = Column(
        UUID(as_uuid=True),
        ForeignKey('forecasts.id', ondelete='CASCADE'),
        nullable=False
    )

    # === Ajustements ===
    adjustment_type = Column(String(20), default="percent")  # percent, absolute
    adjustment_value = Column(Numeric(12, 4), default=Decimal("0"))

    # === Hypothèses ===
    assumptions = Column(JSONB, default=dict)

    # === Résultats ===
    periods = Column(JSONB, default=list)
    total_forecasted = Column(Numeric(18, 2), default=Decimal("0"))

    # === Comparaison ===
    variance_from_baseline = Column(Numeric(18, 2), default=Decimal("0"))
    variance_percent = Column(Numeric(8, 2), default=Decimal("0"))

    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_scenario_tenant', 'tenant_id'),
        Index('ix_scenario_tenant_code', 'tenant_id', 'code'),
        Index('ix_scenario_forecast', 'base_forecast_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_scenario_tenant_code'),
    )

    # === Relations ===
    base_forecast = relationship('Forecast', back_populates='scenarios')

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        return True, ""

    def __repr__(self) -> str:
        return f"<Scenario {self.code}: {self.name}>"


class ForecastBudget(Base):
    """
    Budget annuel ou périodique pour le module forecasting.
    Renomme pour eviter conflit avec budget/models.py
    """
    __tablename__ = "forecasting_budgets"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Période ===
    fiscal_year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    granularity = Column(
        SQLEnum(Granularity),
        default=Granularity.MONTHLY,
        nullable=False
    )

    # === Statut ===
    status = Column(
        SQLEnum(BudgetStatus),
        default=BudgetStatus.DRAFT,
        nullable=False
    )

    # === Département ===
    department_id = Column(UUID(as_uuid=True), nullable=True)
    department_name = Column(String(100), nullable=True)

    # === Lignes (stockées en JSONB pour flexibilité) ===
    lines = Column(JSONB, default=list)
    # Format: [{"account_code": "601", "account_name": "...", "period_amounts": {"2024-01": 5000}}]

    # === Totaux ===
    total_budget = Column(Numeric(18, 2), default=Decimal("0"))
    total_actual = Column(Numeric(18, 2), default=Decimal("0"))
    total_variance = Column(Numeric(18, 2), default=Decimal("0"))
    variance_percent = Column(Numeric(8, 2), default=Decimal("0"))

    # === Workflow ===
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # === Versioning budget ===
    parent_budget_id = Column(
        UUID(as_uuid=True),
        ForeignKey('budgets.id', ondelete='SET NULL'),
        nullable=True
    )

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_budget_tenant', 'tenant_id'),
        Index('ix_budget_tenant_code', 'tenant_id', 'code'),
        Index('ix_budget_tenant_year', 'tenant_id', 'fiscal_year'),
        Index('ix_budget_tenant_status', 'tenant_id', 'status'),
        UniqueConstraint('tenant_id', 'code', name='uq_budget_tenant_code'),
        CheckConstraint('end_date >= start_date', name='ck_budget_dates_valid'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    @hybrid_property
    def is_approved(self) -> bool:
        return self.status == BudgetStatus.APPROVED

    def can_delete(self) -> tuple[bool, str]:
        if self.status in [BudgetStatus.APPROVED, BudgetStatus.LOCKED]:
            return False, "Cannot delete approved or locked budget"
        return True, ""

    def __repr__(self) -> str:
        return f"<Budget {self.code}: {self.name} ({self.fiscal_year})>"


class KPI(Base):
    """
    Indicateur clé de performance.
    """
    __tablename__ = "kpis"

    # === Identifiants ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # === Configuration ===
    category = Column(String(100), nullable=True)
    formula = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)

    # === Valeurs ===
    current_value = Column(Numeric(18, 4), default=Decimal("0"))
    target_value = Column(Numeric(18, 4), default=Decimal("0"))
    previous_value = Column(Numeric(18, 4), default=Decimal("0"))

    # === Performance ===
    achievement_percent = Column(Numeric(8, 2), default=Decimal("0"))
    trend = Column(String(20), default="stable")  # up, down, stable

    # === Seuils ===
    green_threshold = Column(Numeric(18, 4), default=Decimal("0"))
    amber_threshold = Column(Numeric(18, 4), default=Decimal("0"))
    red_threshold = Column(Numeric(18, 4), default=Decimal("0"))

    # === Statut ===
    status = Column(
        SQLEnum(KPIStatus),
        default=KPIStatus.GREEN,
        nullable=False
    )

    # === Fréquence ===
    update_frequency = Column(String(20), default="monthly")
    last_measured_at = Column(DateTime, nullable=True)

    # === Historique ===
    historical_values = Column(JSONB, default=list)
    # Format: [{"date": "2024-01-01", "value": 100, "status": "green"}]

    is_active = Column(Boolean, default=True, nullable=False)

    # === Audit ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # === Soft Delete ===
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # === Version ===
    version = Column(Integer, default=1, nullable=False)

    # === Contraintes ===
    __table_args__ = (
        Index('ix_kpi_tenant', 'tenant_id'),
        Index('ix_kpi_tenant_code', 'tenant_id', 'code'),
        Index('ix_kpi_tenant_category', 'tenant_id', 'category'),
        Index('ix_kpi_tenant_status', 'tenant_id', 'status'),
        UniqueConstraint('tenant_id', 'code', name='uq_kpi_tenant_code'),
    )

    @validates('code')
    def validate_code(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Code cannot be empty")
        return value.upper().strip()

    def can_delete(self) -> tuple[bool, str]:
        return True, ""

    def __repr__(self) -> str:
        return f"<KPI {self.code}: {self.name}>"


# === Event Listeners ===

@event.listens_for(Forecast, 'before_update')
def forecast_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(ForecastModel, 'before_update')
def model_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(Scenario, 'before_update')
def scenario_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(ForecastBudget, 'before_update')
def budget_before_update(mapper, connection, target):
    target.version += 1


@event.listens_for(KPI, 'before_update')
def kpi_before_update(mapper, connection, target):
    target.version += 1
