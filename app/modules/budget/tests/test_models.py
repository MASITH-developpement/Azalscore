"""
AZALS MODULE - BUDGET: Tests des Modeles
=========================================

Tests unitaires pour les modeles SQLAlchemy du module budget.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from ..models import (
    AlertSeverity,
    AlertStatus,
    AllocationMethod,
    Budget,
    BudgetActual,
    BudgetAlert,
    BudgetCategory,
    BudgetConsolidation,
    BudgetForecast,
    BudgetLine,
    BudgetLineType,
    BudgetPeriod,
    BudgetPeriodAmount,
    BudgetPeriodType,
    BudgetRevision,
    BudgetRevisionDetail,
    BudgetScenario,
    BudgetScenarioLine,
    BudgetStatus,
    BudgetTemplate,
    BudgetType,
    ControlMode,
    ForecastConfidence,
    RevisionStatus,
    ScenarioType,
    SeasonalProfile,
    VarianceType,
)


class TestEnumerations:
    """Tests pour les enumerations."""

    def test_budget_type_values(self):
        """Test valeurs BudgetType."""
        assert BudgetType.OPERATING.value == "OPERATING"
        assert BudgetType.INVESTMENT.value == "INVESTMENT"
        assert BudgetType.CASH.value == "CASH"
        assert BudgetType.PROJECT.value == "PROJECT"
        assert BudgetType.DEPARTMENT.value == "DEPARTMENT"

    def test_budget_status_values(self):
        """Test valeurs BudgetStatus."""
        assert BudgetStatus.DRAFT.value == "DRAFT"
        assert BudgetStatus.SUBMITTED.value == "SUBMITTED"
        assert BudgetStatus.APPROVED.value == "APPROVED"
        assert BudgetStatus.ACTIVE.value == "ACTIVE"
        assert BudgetStatus.CLOSED.value == "CLOSED"

    def test_budget_line_type_values(self):
        """Test valeurs BudgetLineType."""
        assert BudgetLineType.REVENUE.value == "REVENUE"
        assert BudgetLineType.EXPENSE.value == "EXPENSE"
        assert BudgetLineType.INVESTMENT.value == "INVESTMENT"

    def test_allocation_method_values(self):
        """Test valeurs AllocationMethod."""
        assert AllocationMethod.EQUAL.value == "EQUAL"
        assert AllocationMethod.SEASONAL.value == "SEASONAL"
        assert AllocationMethod.MANUAL.value == "MANUAL"

    def test_control_mode_values(self):
        """Test valeurs ControlMode."""
        assert ControlMode.NONE.value == "NONE"
        assert ControlMode.WARNING_ONLY.value == "WARNING_ONLY"
        assert ControlMode.SOFT.value == "SOFT"
        assert ControlMode.HARD.value == "HARD"

    def test_variance_type_values(self):
        """Test valeurs VarianceType."""
        assert VarianceType.FAVORABLE.value == "FAVORABLE"
        assert VarianceType.UNFAVORABLE.value == "UNFAVORABLE"
        assert VarianceType.ON_TARGET.value == "ON_TARGET"


class TestBudgetCategoryModel:
    """Tests pour le modele BudgetCategory."""

    def test_create_category(self):
        """Test creation categorie."""
        category = BudgetCategory(
            id=uuid4(),
            tenant_id="test-tenant",
            code="EXP001",
            name="Charges de personnel",
            line_type=BudgetLineType.EXPENSE,
            is_active=True
        )

        assert category.code == "EXP001"
        assert category.line_type == BudgetLineType.EXPENSE
        assert category.is_deleted is False

    def test_category_hierarchy(self):
        """Test hierarchie des categories."""
        parent = BudgetCategory(
            id=uuid4(),
            tenant_id="test-tenant",
            code="EXP",
            name="Charges",
            line_type=BudgetLineType.EXPENSE,
            level=0
        )

        child = BudgetCategory(
            id=uuid4(),
            tenant_id="test-tenant",
            code="EXP001",
            name="Charges de personnel",
            line_type=BudgetLineType.EXPENSE,
            parent_id=parent.id,
            level=1
        )

        assert child.parent_id == parent.id
        assert child.level == 1


class TestBudgetModel:
    """Tests pour le modele Budget."""

    def test_create_budget(self):
        """Test creation budget."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-2026-01",
            name="Budget exploitation 2026",
            budget_type=BudgetType.OPERATING,
            period_type=BudgetPeriodType.ANNUAL,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            currency="EUR"
        )

        assert budget.code == "BUD-2026-01"
        assert budget.fiscal_year == 2026
        assert budget.status == BudgetStatus.DRAFT
        assert budget.is_current_version is True

    def test_budget_defaults(self):
        """Test valeurs par defaut du budget."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert budget.status == BudgetStatus.DRAFT
        assert budget.version_number == 1
        assert budget.control_mode == ControlMode.WARNING_ONLY
        assert budget.warning_threshold == Decimal("80.00")
        assert budget.critical_threshold == Decimal("95.00")
        assert budget.is_deleted is False

    def test_budget_totals(self):
        """Test calcul des totaux."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_revenue=Decimal("150000"),
            total_expense=Decimal("100000"),
            total_investment=Decimal("20000")
        )

        budget.net_result = budget.total_revenue - budget.total_expense

        assert budget.net_result == Decimal("50000")


class TestBudgetLineModel:
    """Tests pour le modele BudgetLine."""

    def test_create_line(self):
        """Test creation ligne."""
        line = BudgetLine(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            category_id=uuid4(),
            name="Salaires",
            line_type=BudgetLineType.EXPENSE,
            annual_amount=Decimal("500000"),
            allocation_method=AllocationMethod.EQUAL
        )

        assert line.name == "Salaires"
        assert line.annual_amount == Decimal("500000")
        assert line.allocation_method == AllocationMethod.EQUAL

    def test_line_monthly_distribution(self):
        """Test distribution mensuelle."""
        line = BudgetLine(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            category_id=uuid4(),
            name="Test",
            line_type=BudgetLineType.EXPENSE,
            annual_amount=Decimal("12000"),
            monthly_distribution={
                1: Decimal("1000"),
                2: Decimal("1000"),
                3: Decimal("1000"),
                4: Decimal("1000"),
                5: Decimal("1000"),
                6: Decimal("1000"),
                7: Decimal("1000"),
                8: Decimal("1000"),
                9: Decimal("1000"),
                10: Decimal("1000"),
                11: Decimal("1000"),
                12: Decimal("1000"),
            }
        )

        total = sum(line.monthly_distribution.values())
        assert total == Decimal("12000")


class TestBudgetPeriodModel:
    """Tests pour le modele BudgetPeriod."""

    def test_create_period(self):
        """Test creation periode."""
        period = BudgetPeriod(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            period_number=1,
            name="Janvier 2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31)
        )

        assert period.period_number == 1
        assert period.is_open is True
        assert period.is_locked is False


class TestBudgetActualModel:
    """Tests pour le modele BudgetActual."""

    def test_create_actual(self):
        """Test creation realise."""
        actual = BudgetActual(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            budget_line_id=uuid4(),
            period="2026-06",
            period_date=date(2026, 6, 1),
            amount=Decimal("45000"),
            line_type=BudgetLineType.EXPENSE,
            source="ACCOUNTING"
        )

        assert actual.period == "2026-06"
        assert actual.amount == Decimal("45000")
        assert actual.source == "ACCOUNTING"


class TestBudgetAlertModel:
    """Tests pour le modele BudgetAlert."""

    def test_create_alert(self):
        """Test creation alerte."""
        alert = BudgetAlert(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            alert_type="THRESHOLD",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Seuil atteint",
            message="80% du budget consomme",
            threshold_percent=Decimal("80"),
            current_percent=Decimal("82")
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE
        assert alert.current_percent > alert.threshold_percent


class TestBudgetRevisionModel:
    """Tests pour le modele BudgetRevision."""

    def test_create_revision(self):
        """Test creation revision."""
        revision = BudgetRevision(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            revision_number=1,
            name="Revision T2",
            effective_date=date(2026, 4, 1),
            reason="Ajustement previsionnel",
            status=RevisionStatus.DRAFT,
            total_change_amount=Decimal("25000")
        )

        assert revision.revision_number == 1
        assert revision.status == RevisionStatus.DRAFT
        assert revision.total_change_amount == Decimal("25000")


class TestBudgetForecastModel:
    """Tests pour le modele BudgetForecast."""

    def test_create_forecast(self):
        """Test creation prevision."""
        forecast = BudgetForecast(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            forecast_date=date(2026, 6, 15),
            period="2026-12",
            original_budget=Decimal("100000"),
            revised_forecast=Decimal("110000"),
            variance=Decimal("10000"),
            confidence=ForecastConfidence.HIGH
        )

        assert forecast.period == "2026-12"
        assert forecast.variance == Decimal("10000")
        assert forecast.confidence == ForecastConfidence.HIGH


class TestBudgetScenarioModel:
    """Tests pour le modele BudgetScenario."""

    def test_create_scenario(self):
        """Test creation scenario."""
        scenario = BudgetScenario(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            name="Scenario optimiste",
            scenario_type=ScenarioType.OPTIMISTIC,
            revenue_adjustment_percent=Decimal("10"),
            expense_adjustment_percent=Decimal("-5")
        )

        assert scenario.name == "Scenario optimiste"
        assert scenario.scenario_type == ScenarioType.OPTIMISTIC
        assert scenario.revenue_adjustment_percent == Decimal("10")


class TestSeasonalProfileModel:
    """Tests pour le modele SeasonalProfile."""

    def test_create_profile(self):
        """Test creation profil saisonnier."""
        profile = SeasonalProfile(
            id=uuid4(),
            tenant_id="test-tenant",
            code="RETAIL",
            name="Commerce de detail",
            monthly_weights=[8, 6, 7, 8, 9, 8, 7, 6, 9, 10, 11, 11]
        )

        assert profile.code == "RETAIL"
        assert len(profile.monthly_weights) == 12
        assert sum(profile.monthly_weights) == 100  # Poids totaux


class TestSoftDelete:
    """Tests pour le soft delete."""

    def test_soft_delete_fields(self):
        """Test presence des champs soft delete."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert hasattr(budget, 'is_deleted')
        assert hasattr(budget, 'deleted_at')
        assert hasattr(budget, 'deleted_by')
        assert budget.is_deleted is False


class TestAuditFields:
    """Tests pour les champs d'audit."""

    def test_audit_fields_present(self):
        """Test presence des champs d'audit."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert hasattr(budget, 'created_at')
        assert hasattr(budget, 'created_by')
        assert hasattr(budget, 'updated_at')
        assert hasattr(budget, 'updated_by')
        assert hasattr(budget, 'version')


class TestOptimisticLocking:
    """Tests pour l'optimistic locking."""

    def test_version_field(self):
        """Test champ version."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert budget.version == 1


class TestTenantIsolation:
    """Tests pour l'isolation multi-tenant."""

    def test_tenant_id_required(self):
        """Test tenant_id obligatoire."""
        # Tous les modeles doivent avoir tenant_id
        models = [
            Budget,
            BudgetLine,
            BudgetCategory,
            BudgetPeriod,
            BudgetActual,
            BudgetAlert,
            BudgetRevision,
            BudgetForecast,
            BudgetScenario,
        ]

        for model in models:
            # Verifier que tenant_id est dans les colonnes
            assert hasattr(model, 'tenant_id'), f"{model.__name__} missing tenant_id"
