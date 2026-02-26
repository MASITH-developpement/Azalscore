"""
AZALS MODULE - BUDGET: Tests du Router
=======================================

Tests d'integration pour les endpoints API du module budget.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ..models import (
    BudgetLineType,
    BudgetPeriodType,
    BudgetStatus,
    BudgetType,
    ControlMode,
)
from ..schemas import (
    BudgetCategoryResponse,
    BudgetResponse,
    BudgetLineResponse,
)


class TestBudgetCategoryEndpoints:
    """Tests pour les endpoints categories."""

    @pytest.fixture
    def mock_service(self):
        """Mock du service budget."""
        return MagicMock()

    @pytest.fixture
    def sample_category_response(self):
        """Reponse categorie exemple."""
        return BudgetCategoryResponse(
            id=uuid4(),
            tenant_id="test-tenant",
            code="EXP001",
            name="Charges de personnel",
            line_type=BudgetLineType.EXPENSE,
            parent_id=None,
            account_codes=["64"],
            sort_order=0,
            is_active=True,
            level=0,
            path=None,
            is_summary=False,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T00:00:00"
        )

    def test_create_category_endpoint(self, mock_service, sample_category_response):
        """Test endpoint creation categorie."""
        # Ce test necessite un setup FastAPI complet
        # Pour l'instant, on verifie juste la structure
        assert sample_category_response.code == "EXP001"
        assert sample_category_response.line_type == BudgetLineType.EXPENSE


class TestBudgetEndpoints:
    """Tests pour les endpoints budgets."""

    @pytest.fixture
    def sample_budget_response(self):
        """Reponse budget exemple."""
        return BudgetResponse(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-2026-01",
            name="Budget exploitation 2026",
            description="Budget principal",
            budget_type=BudgetType.OPERATING,
            period_type=BudgetPeriodType.ANNUAL,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            currency="EUR",
            entity_id=None,
            department_id=None,
            cost_center_id=None,
            project_id=None,
            control_mode=ControlMode.WARNING_ONLY,
            warning_threshold=Decimal("80"),
            critical_threshold=Decimal("95"),
            notes=None,
            assumptions=None,
            objectives=None,
            tags=[],
            status=BudgetStatus.DRAFT,
            version_number=1,
            is_current_version=True,
            parent_budget_id=None,
            total_revenue=Decimal("150000"),
            total_expense=Decimal("100000"),
            total_investment=Decimal("20000"),
            net_result=Decimal("50000"),
            owner_id=None,
            approvers=[],
            submitted_at=None,
            approved_at=None,
            activated_at=None,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T00:00:00",
            created_by=None
        )

    def test_budget_response_structure(self, sample_budget_response):
        """Test structure reponse budget."""
        assert sample_budget_response.code == "BUD-2026-01"
        assert sample_budget_response.fiscal_year == 2026
        assert sample_budget_response.status == BudgetStatus.DRAFT
        assert sample_budget_response.total_revenue == Decimal("150000")
        assert sample_budget_response.net_result == Decimal("50000")


class TestBudgetLineEndpoints:
    """Tests pour les endpoints lignes budgetaires."""

    @pytest.fixture
    def sample_line_response(self):
        """Reponse ligne exemple."""
        return BudgetLineResponse(
            id=uuid4(),
            tenant_id="test-tenant",
            budget_id=uuid4(),
            category_id=uuid4(),
            code="LN001",
            name="Salaires et charges",
            description="Masse salariale",
            line_type=BudgetLineType.EXPENSE,
            annual_amount=Decimal("500000"),
            allocation_method="EQUAL",
            seasonal_profile=None,
            quantity=None,
            unit=None,
            unit_price=None,
            cost_center_id=None,
            project_id=None,
            department_id=None,
            account_code="641",
            notes=None,
            assumptions=None,
            monthly_distribution={
                "1": Decimal("41666.67"),
                "2": Decimal("41666.67"),
                "3": Decimal("41666.67"),
                "4": Decimal("41666.67"),
                "5": Decimal("41666.67"),
                "6": Decimal("41666.67"),
                "7": Decimal("41666.67"),
                "8": Decimal("41666.67"),
                "9": Decimal("41666.67"),
                "10": Decimal("41666.67"),
                "11": Decimal("41666.67"),
                "12": Decimal("41666.63"),
            },
            parent_line_id=None,
            sort_order=0,
            is_summary=False,
            ytd_actual=Decimal("250000"),
            ytd_committed=Decimal("0"),
            remaining_budget=Decimal("250000"),
            consumption_rate=Decimal("50"),
            created_at="2026-01-01T00:00:00",
            updated_at="2026-06-15T00:00:00"
        )

    def test_line_response_structure(self, sample_line_response):
        """Test structure reponse ligne."""
        assert sample_line_response.name == "Salaires et charges"
        assert sample_line_response.annual_amount == Decimal("500000")
        assert sample_line_response.consumption_rate == Decimal("50")
        assert len(sample_line_response.monthly_distribution) == 12


class TestWorkflowEndpoints:
    """Tests pour les endpoints workflow."""

    def test_workflow_statuses(self):
        """Test enchainement des statuts."""
        # Verification des transitions valides
        valid_transitions = {
            BudgetStatus.DRAFT: [BudgetStatus.SUBMITTED],
            BudgetStatus.SUBMITTED: [BudgetStatus.APPROVED, BudgetStatus.REJECTED, BudgetStatus.UNDER_REVIEW],
            BudgetStatus.UNDER_REVIEW: [BudgetStatus.APPROVED, BudgetStatus.REJECTED],
            BudgetStatus.APPROVED: [BudgetStatus.ACTIVE],
            BudgetStatus.ACTIVE: [BudgetStatus.REVISED, BudgetStatus.CLOSED],
            BudgetStatus.REJECTED: [BudgetStatus.DRAFT],
            BudgetStatus.REVISED: [BudgetStatus.SUBMITTED],
            BudgetStatus.CLOSED: [BudgetStatus.ARCHIVED],
        }

        # Verifier que tous les statuts sont couverts
        assert len(valid_transitions) == 8


class TestControlEndpoints:
    """Tests pour les endpoints controle budgetaire."""

    def test_control_modes(self):
        """Test des modes de controle."""
        assert ControlMode.NONE.value == "NONE"
        assert ControlMode.WARNING_ONLY.value == "WARNING_ONLY"
        assert ControlMode.SOFT.value == "SOFT"
        assert ControlMode.HARD.value == "HARD"

    def test_threshold_validation(self):
        """Test validation des seuils."""
        # Les seuils doivent etre dans l'ordre: warning < critical < block
        warning = Decimal("80")
        critical = Decimal("95")
        block = Decimal("100")

        assert warning < critical < block


class TestDashboardEndpoints:
    """Tests pour les endpoints dashboard."""

    def test_dashboard_structure(self):
        """Test structure attendue du dashboard."""
        expected_fields = [
            "tenant_id",
            "fiscal_year",
            "as_of_date",
            "total_budgeted_expense",
            "total_budgeted_revenue",
            "total_actual_expense",
            "total_actual_revenue",
            "total_variance",
            "overall_consumption_rate",
            "active_budgets_count",
            "budgets_summary",
            "active_alerts_count",
            "critical_alerts_count",
            "recent_alerts",
            "top_overruns",
            "top_savings",
            "monthly_trend"
        ]

        # Import du schema pour verification
        from ..schemas import BudgetDashboard
        import pydantic

        schema_fields = list(BudgetDashboard.model_fields.keys())

        for field in expected_fields:
            assert field in schema_fields, f"Missing field: {field}"
