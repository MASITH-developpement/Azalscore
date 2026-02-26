"""
AZALS MODULE - BUDGET: Tests du Service
========================================

Tests unitaires pour le service de gestion budgetaire.
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from ..exceptions import (
    BudgetAlreadyExistsError,
    BudgetCategoryNotFoundError,
    BudgetNotFoundError,
    BudgetNotModifiableError,
    BudgetStatusError,
)
from ..models import (
    AllocationMethod,
    Budget,
    BudgetCategory,
    BudgetLine,
    BudgetLineType,
    BudgetPeriodType,
    BudgetStatus,
    BudgetType,
    ControlMode,
)
from ..schemas import (
    BudgetCategoryCreate,
    BudgetCreate,
    BudgetLineCreate,
    BudgetUpdate,
)
from ..service import BudgetService


class TestBudgetService:
    """Tests pour BudgetService."""

    @pytest.fixture
    def mock_db(self):
        """Mock de la session DB."""
        return MagicMock()

    @pytest.fixture
    def tenant_id(self):
        """ID tenant de test."""
        return "test-tenant-001"

    @pytest.fixture
    def service(self, mock_db, tenant_id):
        """Instance du service."""
        return BudgetService(mock_db, tenant_id)

    @pytest.fixture
    def sample_category(self, tenant_id):
        """Categorie de test."""
        return BudgetCategory(
            id=uuid4(),
            tenant_id=tenant_id,
            code="EXP001",
            name="Charges de personnel",
            line_type=BudgetLineType.EXPENSE,
            is_active=True
        )

    @pytest.fixture
    def sample_budget(self, tenant_id):
        """Budget de test."""
        return Budget(
            id=uuid4(),
            tenant_id=tenant_id,
            code="BUD-2026-01",
            name="Budget exploitation 2026",
            budget_type=BudgetType.OPERATING,
            period_type=BudgetPeriodType.ANNUAL,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=BudgetStatus.DRAFT,
            currency="EUR",
            total_expense=Decimal("100000"),
            total_revenue=Decimal("150000"),
            net_result=Decimal("50000")
        )

    # =========================================================================
    # Tests Categories
    # =========================================================================

    def test_create_category_success(self, service, sample_category):
        """Test creation categorie reussie."""
        with patch.object(service.repo, 'get_category_by_code', return_value=None):
            with patch.object(service.repo, 'create_category', return_value=sample_category):
                with patch.object(service.repo, 'commit'):
                    data = BudgetCategoryCreate(
                        code="EXP001",
                        name="Charges de personnel",
                        line_type=BudgetLineType.EXPENSE
                    )
                    result = service.create_category(data)

                    assert result.code == "EXP001"
                    assert result.name == "Charges de personnel"

    def test_create_category_duplicate_code(self, service, sample_category):
        """Test erreur sur code duplique."""
        with patch.object(service.repo, 'get_category_by_code', return_value=sample_category):
            data = BudgetCategoryCreate(
                code="EXP001",
                name="Autre categorie",
                line_type=BudgetLineType.EXPENSE
            )

            with pytest.raises(BudgetAlreadyExistsError):
                service.create_category(data)

    def test_get_category_not_found(self, service):
        """Test erreur categorie non trouvee."""
        with patch.object(service.repo, 'get_category', return_value=None):
            with pytest.raises(BudgetCategoryNotFoundError):
                service.get_category(uuid4())

    # =========================================================================
    # Tests Budgets
    # =========================================================================

    def test_create_budget_success(self, service, sample_budget):
        """Test creation budget reussie."""
        with patch.object(service.repo, 'get_budget_by_code', return_value=None):
            with patch.object(service.repo, 'create_budget', return_value=sample_budget):
                with patch.object(service.repo, 'create_budget_periods', return_value=[]):
                    with patch.object(service.repo, 'commit'):
                        data = BudgetCreate(
                            code="BUD-2026-01",
                            name="Budget exploitation 2026",
                            budget_type=BudgetType.OPERATING,
                            fiscal_year=2026,
                            start_date=date(2026, 1, 1),
                            end_date=date(2026, 12, 31)
                        )
                        result = service.create_budget(data)

                        assert result.code == "BUD-2026-01"
                        assert result.fiscal_year == 2026

    def test_create_budget_duplicate_code(self, service, sample_budget):
        """Test erreur sur code budget duplique."""
        with patch.object(service.repo, 'get_budget_by_code', return_value=sample_budget):
            data = BudgetCreate(
                code="BUD-2026-01",
                name="Autre budget",
                budget_type=BudgetType.OPERATING,
                fiscal_year=2026,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31)
            )

            with pytest.raises(BudgetAlreadyExistsError):
                service.create_budget(data)

    def test_get_budget_not_found(self, service):
        """Test erreur budget non trouve."""
        with patch.object(service.repo, 'get_budget', return_value=None):
            with pytest.raises(BudgetNotFoundError):
                service.get_budget(uuid4())

    def test_update_budget_not_modifiable(self, service, sample_budget):
        """Test erreur modification budget actif."""
        sample_budget.status = BudgetStatus.ACTIVE

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            data = BudgetUpdate(name="Nouveau nom")

            with pytest.raises(BudgetNotModifiableError):
                service.update_budget(sample_budget.id, data)

    def test_delete_budget_active_error(self, service, sample_budget):
        """Test erreur suppression budget actif."""
        sample_budget.status = BudgetStatus.ACTIVE

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with pytest.raises(BudgetStatusError):
                service.delete_budget(sample_budget.id)

    # =========================================================================
    # Tests Workflow
    # =========================================================================

    def test_submit_budget_success(self, service, sample_budget):
        """Test soumission budget reussie."""
        sample_budget.status = BudgetStatus.DRAFT
        sample_budget.approval_history = []

        mock_line = BudgetLine(
            id=uuid4(),
            budget_id=sample_budget.id,
            tenant_id=service.tenant_id,
            category_id=uuid4(),
            name="Ligne test",
            line_type=BudgetLineType.EXPENSE,
            annual_amount=Decimal("10000")
        )

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with patch.object(service.repo, 'get_budget_lines', return_value=[mock_line]):
                with patch.object(service.repo, 'commit'):
                    result = service.submit_budget(sample_budget.id, uuid4())

                    assert result.status == BudgetStatus.SUBMITTED

    def test_submit_budget_no_lines_error(self, service, sample_budget):
        """Test erreur soumission budget sans lignes."""
        sample_budget.status = BudgetStatus.DRAFT

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with patch.object(service.repo, 'get_budget_lines', return_value=[]):
                from ..exceptions import BudgetValidationError
                with pytest.raises(BudgetValidationError):
                    service.submit_budget(sample_budget.id, uuid4())

    def test_approve_budget_wrong_status(self, service, sample_budget):
        """Test erreur approbation budget non soumis."""
        sample_budget.status = BudgetStatus.DRAFT

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with pytest.raises(BudgetStatusError):
                service.approve_budget(sample_budget.id, uuid4())

    def test_activate_budget_success(self, service, sample_budget):
        """Test activation budget reussie."""
        sample_budget.status = BudgetStatus.APPROVED
        sample_budget.approval_history = []

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with patch.object(service.repo, 'commit'):
                result = service.activate_budget(sample_budget.id, uuid4())

                assert result.status == BudgetStatus.ACTIVE

    # =========================================================================
    # Tests Distribution
    # =========================================================================

    def test_distribute_annual_amount_equal(self, service):
        """Test distribution egale."""
        result = service._distribute_annual_amount(
            Decimal("12000"),
            AllocationMethod.EQUAL
        )

        assert len(result) == 12
        assert sum(result.values()) == Decimal("12000")
        # Chaque mois devrait avoir environ 1000
        for month in range(1, 12):
            assert result[month] == Decimal("1000.00")

    def test_distribute_annual_amount_seasonal(self, service):
        """Test distribution saisonniere."""
        result = service._distribute_annual_amount(
            Decimal("12000"),
            AllocationMethod.SEASONAL,
            "retail"
        )

        assert len(result) == 12
        assert sum(result.values()) == Decimal("12000")
        # Les mois d'ete devraient avoir moins (profil retail)

    # =========================================================================
    # Tests Controle Budgetaire
    # =========================================================================

    def test_check_budget_control_allowed(self, service, sample_budget):
        """Test controle budgetaire autorise."""
        sample_budget.control_mode = ControlMode.WARNING_ONLY
        sample_budget.warning_threshold = Decimal("80")
        sample_budget.critical_threshold = Decimal("95")
        sample_budget.block_threshold = Decimal("100")

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with patch.object(service.repo, 'get_actuals_sum_by_line', return_value={}):
                from ..schemas import BudgetControlCheck
                data = BudgetControlCheck(
                    budget_id=sample_budget.id,
                    amount=Decimal("5000")
                )

                result = service.check_budget_control(data)

                assert result.allowed is True

    def test_check_budget_control_no_control(self, service, sample_budget):
        """Test pas de controle budgetaire."""
        sample_budget.control_mode = ControlMode.NONE

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            from ..schemas import BudgetControlCheck
            data = BudgetControlCheck(
                budget_id=sample_budget.id,
                amount=Decimal("999999")
            )

            result = service.check_budget_control(data)

            assert result.allowed is True
            assert result.control_mode == ControlMode.NONE


class TestBudgetLineOperations:
    """Tests pour les operations sur les lignes."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BudgetService(mock_db, "test-tenant")

    @pytest.fixture
    def sample_budget(self):
        return Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test Budget",
            budget_type=BudgetType.OPERATING,
            period_type=BudgetPeriodType.MONTHLY,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=BudgetStatus.DRAFT
        )

    @pytest.fixture
    def sample_category(self):
        return BudgetCategory(
            id=uuid4(),
            tenant_id="test-tenant",
            code="CAT001",
            name="Test Category",
            line_type=BudgetLineType.EXPENSE
        )

    def test_add_line_to_draft_budget(self, service, sample_budget, sample_category):
        """Test ajout ligne a un budget brouillon."""
        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            with patch.object(service.repo, 'get_category', return_value=sample_category):
                with patch.object(service.repo, 'create_budget_line') as mock_create:
                    with patch.object(service.repo, 'get_budget_periods', return_value=[]):
                        with patch.object(service.repo, 'create_period_amounts', return_value=[]):
                            with patch.object(service.repo, 'get_budget_lines', return_value=[]):
                                with patch.object(service.repo, 'commit'):
                                    mock_line = BudgetLine(
                                        id=uuid4(),
                                        budget_id=sample_budget.id,
                                        tenant_id="test-tenant",
                                        category_id=sample_category.id,
                                        name="Nouvelle ligne",
                                        line_type=BudgetLineType.EXPENSE,
                                        annual_amount=Decimal("10000")
                                    )
                                    mock_create.return_value = mock_line

                                    data = BudgetLineCreate(
                                        category_id=sample_category.id,
                                        name="Nouvelle ligne",
                                        annual_amount=Decimal("10000")
                                    )

                                    result = service.add_budget_line(
                                        sample_budget.id, data
                                    )

                                    assert result.name == "Nouvelle ligne"
                                    assert result.annual_amount == Decimal("10000")

    def test_add_line_to_active_budget_error(self, service, sample_budget):
        """Test erreur ajout ligne a budget actif."""
        sample_budget.status = BudgetStatus.ACTIVE

        with patch.object(service.repo, 'get_budget', return_value=sample_budget):
            data = BudgetLineCreate(
                category_id=uuid4(),
                name="Test",
                annual_amount=Decimal("1000")
            )

            with pytest.raises(BudgetNotModifiableError):
                service.add_budget_line(sample_budget.id, data)


class TestVarianceCalculation:
    """Tests pour le calcul des ecarts."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return BudgetService(mock_db, "test-tenant")

    def test_calculate_variances_empty(self, service):
        """Test calcul ecarts budget sans lignes."""
        budget = Budget(
            id=uuid4(),
            tenant_id="test-tenant",
            code="BUD-001",
            name="Test",
            budget_type=BudgetType.OPERATING,
            period_type=BudgetPeriodType.MONTHLY,
            fiscal_year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=BudgetStatus.ACTIVE
        )

        with patch.object(service.repo, 'get_budget', return_value=budget):
            with patch.object(service.repo, 'get_budget_lines', return_value=[]):
                with patch.object(service.repo, 'get_actuals_sum_by_line', return_value={}):
                    result = service.calculate_variances(budget.id, "2026-06")

                    assert len(result) == 0
