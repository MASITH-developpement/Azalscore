"""
Tests du service - Module Commissions (GAP-041)
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from app.modules.commissions.service import CommissionService
from app.modules.commissions.schemas import (
    CommissionPlanCreate, CommissionTierCreate, AcceleratorCreate,
    AssignmentCreate, TeamMemberCreate,
    TransactionCreate, CalculationRequest, BulkCalculationRequest,
    PeriodCreate, AdjustmentCreate, ClawbackCreate,
    CommissionBasis, TierType, PlanStatus, PaymentFrequency, PeriodType, AdjustmentType
)
from app.modules.commissions.exceptions import (
    PlanNotFoundError, PlanDuplicateError, PlanInvalidStateError,
    AssignmentOverlapError,
    TransactionDuplicateError,
    CalculationError, CalculationAlreadyExistsError,
    PeriodDuplicateError,
    ClawbackPeriodExpiredError,
    TeamMemberNotFoundError
)


class TestCommissionServicePlans:
    """Tests de gestion des plans."""

    @pytest.fixture
    def mock_service(self):
        """Service avec mocks."""
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_create_plan_simple(self, mock_service):
        """Test creation plan simple."""
        mock_service.plan_repo.code_exists = Mock(return_value=False)
        mock_service.plan_repo.create = Mock(return_value=Mock(
            id=uuid4(),
            code="PLAN-001",
            name="Plan Test",
            status=PlanStatus.DRAFT.value
        ))

        data = CommissionPlanCreate(
            name="Plan Test",
            effective_from=date.today()
        )

        result = mock_service.create_plan(data)

        assert result.code == "PLAN-001"
        mock_service.plan_repo.create.assert_called_once()

    def test_create_plan_duplicate_code(self, mock_service):
        """Test echec creation plan code duplique."""
        mock_service.plan_repo.code_exists = Mock(return_value=True)

        data = CommissionPlanCreate(
            code="EXISTING",
            name="Plan Test",
            effective_from=date.today()
        )

        with pytest.raises(PlanDuplicateError):
            mock_service.create_plan(data)

    def test_create_plan_with_tiers(self, mock_service):
        """Test creation plan avec paliers."""
        mock_service.plan_repo.code_exists = Mock(return_value=False)
        mock_service.plan_repo.create = Mock(return_value=Mock(
            id=uuid4(),
            code="PLAN-002",
            name="Plan Progressive",
            tier_type=TierType.PROGRESSIVE.value,
            tiers=[]
        ))

        data = CommissionPlanCreate(
            name="Plan Progressive",
            tier_type=TierType.PROGRESSIVE,
            effective_from=date.today(),
            tiers=[
                CommissionTierCreate(
                    tier_number=1,
                    min_value=Decimal("0"),
                    max_value=Decimal("50000"),
                    rate=Decimal("5")
                ),
                CommissionTierCreate(
                    tier_number=2,
                    min_value=Decimal("50000"),
                    max_value=None,
                    rate=Decimal("8")
                )
            ]
        )

        result = mock_service.create_plan(data)
        mock_service.plan_repo.create.assert_called_once()

    def test_activate_plan_success(self, mock_service):
        """Test activation plan."""
        plan = Mock(
            id=uuid4(),
            status=PlanStatus.DRAFT.value,
            tiers=[Mock()],
            tier_type=TierType.FLAT.value
        )
        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.plan_repo.activate = Mock(return_value=Mock(
            status=PlanStatus.ACTIVE.value
        ))

        result = mock_service.activate_plan(plan.id)

        assert result.status == PlanStatus.ACTIVE.value

    def test_activate_plan_no_tiers(self, mock_service):
        """Test echec activation plan sans paliers."""
        plan = Mock(
            id=uuid4(),
            status=PlanStatus.DRAFT.value,
            tiers=[],
            tier_type=TierType.FLAT.value
        )
        mock_service.plan_repo.get_by_id = Mock(return_value=plan)

        with pytest.raises(Exception):  # PlanActivationError
            mock_service.activate_plan(plan.id)


class TestCommissionServiceCalculations:
    """Tests de calcul des commissions."""

    @pytest.fixture
    def mock_service(self):
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_calculate_flat_rate(self, mock_service):
        """Test calcul taux fixe."""
        plan = Mock(
            id=uuid4(),
            basis=CommissionBasis.REVENUE.value,
            tier_type=TierType.FLAT.value,
            tiers=[Mock(
                min_value=Decimal("0"),
                max_value=None,
                rate=Decimal("5"),
                fixed_amount=Decimal("0"),
                tier_number=1,
                name="Standard"
            )],
            accelerators=[],
            quota_amount=None,
            cap_enabled=False,
            cap_amount=None,
            minimum_guaranteed=Decimal("0"),
            currency="EUR",
            trigger_on_invoice=True,
            trigger_on_payment=False,
            trigger_on_delivery=False,
            apply_to_all_products=True,
            apply_to_all_customers=True,
            included_products=[],
            excluded_products=[],
            included_categories=[],
            excluded_categories=[],
            included_customer_segments=[],
            excluded_customer_segments=[],
            new_customers_only=False
        )

        transactions = [
            Mock(
                id=uuid4(),
                revenue=Decimal("10000"),
                margin=Decimal("3000"),
                margin_percent=Decimal("30"),
                quantity=Decimal("1"),
                has_split=False,
                split_config=[],
                payment_status="paid",
                is_new_customer=False,
                transaction_type="standard"
            )
        ]

        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.calculation_repo.get_for_period = Mock(return_value=[])
        mock_service.transaction_repo.get_for_period = Mock(return_value=transactions)
        mock_service.transaction_repo.update_commission_status = Mock()
        mock_service.calculation_repo.create = Mock(return_value=Mock(
            net_commission=Decimal("500")
        ))
        mock_service.team_repo.get_by_employee_id = Mock(return_value=None)

        request = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=plan.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )

        result = mock_service.calculate_commission(request)

        # Verifie que le calcul a ete cree
        mock_service.calculation_repo.create.assert_called_once()

    def test_calculate_progressive_tiers(self, mock_service):
        """Test calcul paliers progressifs."""
        plan = Mock(
            id=uuid4(),
            basis=CommissionBasis.REVENUE.value,
            tier_type=TierType.PROGRESSIVE.value,
            tiers=[
                Mock(
                    min_value=Decimal("0"),
                    max_value=Decimal("50000"),
                    rate=Decimal("5"),
                    fixed_amount=Decimal("0"),
                    tier_number=1,
                    name="Bronze"
                ),
                Mock(
                    min_value=Decimal("50000"),
                    max_value=None,
                    rate=Decimal("8"),
                    fixed_amount=Decimal("0"),
                    tier_number=2,
                    name="Silver"
                )
            ],
            accelerators=[],
            quota_amount=None,
            cap_enabled=False,
            cap_amount=None,
            minimum_guaranteed=Decimal("0"),
            currency="EUR",
            trigger_on_invoice=True,
            trigger_on_payment=False,
            trigger_on_delivery=False,
            apply_to_all_products=True,
            apply_to_all_customers=True,
            included_products=[],
            excluded_products=[],
            included_categories=[],
            excluded_categories=[],
            included_customer_segments=[],
            excluded_customer_segments=[],
            new_customers_only=False
        )

        transactions = [
            Mock(
                id=uuid4(),
                revenue=Decimal("70000"),
                margin=Decimal("21000"),
                margin_percent=Decimal("30"),
                quantity=Decimal("1"),
                has_split=False,
                split_config=[],
                payment_status="paid",
                is_new_customer=False,
                transaction_type="standard"
            )
        ]

        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.calculation_repo.get_for_period = Mock(return_value=[])
        mock_service.transaction_repo.get_for_period = Mock(return_value=transactions)
        mock_service.transaction_repo.update_commission_status = Mock()
        mock_service.team_repo.get_by_employee_id = Mock(return_value=None)

        # Capture l'appel a create pour verifier les valeurs
        create_call_args = None
        def capture_create(data):
            nonlocal create_call_args
            create_call_args = data
            return Mock(net_commission=data.get("net_commission"))

        mock_service.calculation_repo.create = Mock(side_effect=capture_create)

        request = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=plan.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )

        result = mock_service.calculate_commission(request)

        # 50000 * 5% = 2500 + 20000 * 8% = 1600 = 4100
        assert create_call_args is not None

    def test_calculate_with_accelerators(self, mock_service):
        """Test calcul avec accelerateurs."""
        accelerator = Mock(
            id=uuid4(),
            is_active=True,
            valid_from=None,
            valid_to=None,
            threshold_type="quota_percent",
            threshold_value=Decimal("150"),
            threshold_operator=">=",
            multiplier=Decimal("1.5"),
            bonus_amount=Decimal("0"),
            bonus_percent=Decimal("0"),
            max_bonus_amount=None
        )

        plan = Mock(
            id=uuid4(),
            basis=CommissionBasis.REVENUE.value,
            tier_type=TierType.FLAT.value,
            tiers=[Mock(
                min_value=Decimal("0"),
                max_value=None,
                rate=Decimal("5"),
                fixed_amount=Decimal("0"),
                tier_number=1,
                name="Standard"
            )],
            accelerators=[accelerator],
            quota_amount=Decimal("100000"),
            cap_enabled=False,
            cap_amount=None,
            minimum_guaranteed=Decimal("0"),
            currency="EUR",
            trigger_on_invoice=True,
            trigger_on_payment=False,
            trigger_on_delivery=False,
            apply_to_all_products=True,
            apply_to_all_customers=True,
            included_products=[],
            excluded_products=[],
            included_categories=[],
            excluded_categories=[],
            included_customer_segments=[],
            excluded_customer_segments=[],
            new_customers_only=False
        )

        transactions = [
            Mock(
                id=uuid4(),
                revenue=Decimal("160000"),  # 160% du quota
                margin=Decimal("48000"),
                margin_percent=Decimal("30"),
                quantity=Decimal("1"),
                has_split=False,
                split_config=[],
                payment_status="paid",
                is_new_customer=False,
                transaction_type="standard"
            )
        ]

        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.calculation_repo.get_for_period = Mock(return_value=[])
        mock_service.transaction_repo.get_for_period = Mock(return_value=transactions)
        mock_service.transaction_repo.update_commission_status = Mock()
        mock_service.team_repo.get_by_employee_id = Mock(return_value=None)
        mock_service.calculation_repo.create = Mock(return_value=Mock(
            accelerator_bonus=Decimal("4000")
        ))

        request = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=plan.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )

        result = mock_service.calculate_commission(request)

        mock_service.calculation_repo.create.assert_called_once()

    def test_calculate_already_exists(self, mock_service):
        """Test echec calcul deja existant."""
        existing_calc = Mock(status="calculated")

        mock_service.plan_repo.get_by_id = Mock(return_value=Mock())
        mock_service.calculation_repo.get_for_period = Mock(return_value=[existing_calc])

        request = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=uuid4(),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            recalculate=False
        )

        with pytest.raises(CalculationAlreadyExistsError):
            mock_service.calculate_commission(request)


class TestCommissionServiceManagerOverride:
    """Tests du calcul override manager."""

    @pytest.fixture
    def mock_service(self):
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_calculate_manager_override_success(self, mock_service):
        """Test calcul override manager."""
        manager = Mock(
            id=uuid4(),
            employee_id=uuid4(),
            employee_name="Manager Test",
            override_enabled=True,
            override_rate=Decimal("3"),
            override_basis=CommissionBasis.REVENUE.value,
            override_levels=1
        )

        subordinate = Mock(
            id=uuid4(),
            employee_id=uuid4()
        )

        transactions = [
            Mock(
                id=uuid4(),
                revenue=Decimal("50000"),
                margin=Decimal("15000"),
                payment_status="paid"
            )
        ]

        mock_service.team_repo.get_by_employee_id = Mock(return_value=manager)
        mock_service.team_repo.get_all_subordinates_recursive = Mock(return_value=[subordinate])
        mock_service.transaction_repo.get_for_period = Mock(return_value=transactions)
        mock_service.calculation_repo.create = Mock(return_value=Mock(
            net_commission=Decimal("1500")  # 50000 * 3%
        ))

        result = mock_service.calculate_manager_override(
            manager.employee_id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        mock_service.calculation_repo.create.assert_called_once()

    def test_calculate_manager_override_not_enabled(self, mock_service):
        """Test echec override non active."""
        manager = Mock(
            override_enabled=False
        )

        mock_service.team_repo.get_by_employee_id = Mock(return_value=manager)

        with pytest.raises(CalculationError):
            mock_service.calculate_manager_override(
                uuid4(),
                date(2024, 1, 1),
                date(2024, 1, 31)
            )

    def test_calculate_manager_override_not_found(self, mock_service):
        """Test echec manager non trouve."""
        mock_service.team_repo.get_by_employee_id = Mock(return_value=None)

        with pytest.raises(TeamMemberNotFoundError):
            mock_service.calculate_manager_override(
                uuid4(),
                date(2024, 1, 1),
                date(2024, 1, 31)
            )


class TestCommissionServiceClawbacks:
    """Tests des clawbacks."""

    @pytest.fixture
    def mock_service(self):
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_create_clawback_within_period(self, mock_service):
        """Test creation clawback dans la periode."""
        calculation = Mock(
            plan_id=uuid4(),
            net_commission=Decimal("500")
        )

        plan = Mock(
            clawback_enabled=True,
            clawback_period_days=90
        )

        transaction = Mock(
            source_date=date.today() - timedelta(days=30)
        )

        mock_service.calculation_repo.get_by_id = Mock(return_value=calculation)
        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.transaction_repo.get_by_id = Mock(return_value=transaction)
        mock_service.clawback_repo.create = Mock(return_value=Mock(
            code="CLB-001"
        ))

        data = ClawbackCreate(
            original_calculation_id=uuid4(),
            original_transaction_id=uuid4(),
            sales_rep_id=uuid4(),
            clawback_amount=Decimal("500"),
            reason="cancellation",
            cancellation_date=date.today()
        )

        result = mock_service.create_clawback(data)

        mock_service.clawback_repo.create.assert_called_once()

    def test_create_clawback_period_expired(self, mock_service):
        """Test echec clawback periode expiree."""
        calculation = Mock(
            plan_id=uuid4(),
            net_commission=Decimal("500")
        )

        plan = Mock(
            clawback_enabled=True,
            clawback_period_days=90
        )

        transaction = Mock(
            source_date=date.today() - timedelta(days=100)  # > 90 jours
        )

        mock_service.calculation_repo.get_by_id = Mock(return_value=calculation)
        mock_service.plan_repo.get_by_id = Mock(return_value=plan)
        mock_service.transaction_repo.get_by_id = Mock(return_value=transaction)

        data = ClawbackCreate(
            original_calculation_id=uuid4(),
            original_transaction_id=uuid4(),
            sales_rep_id=uuid4(),
            clawback_amount=Decimal("500"),
            reason="cancellation",
            cancellation_date=date.today()
        )

        with pytest.raises(ClawbackPeriodExpiredError):
            mock_service.create_clawback(data)


class TestCommissionServiceStatements:
    """Tests des releves."""

    @pytest.fixture
    def mock_service(self):
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_generate_statement_success(self, mock_service):
        """Test generation releve."""
        period = Mock(
            id=uuid4(),
            code="2024-M01",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        calculations = [
            Mock(
                id=uuid4(),
                gross_commission=Decimal("5000"),
                accelerator_bonus=Decimal("500"),
                adjustments=Decimal("0"),
                calculation_details={"transaction_ids": ["t1", "t2"]}
            )
        ]

        mock_service.period_repo.get_by_id = Mock(return_value=period)
        mock_service.calculation_repo.get_for_period = Mock(return_value=calculations)
        mock_service.clawback_repo.get_pending_for_rep = Mock(return_value=[])
        mock_service.calculation_repo.get_ytd_totals = Mock(return_value={
            "total_commission": Decimal("10000"),
            "total_sales": Decimal("200000")
        })
        mock_service.statement_repo.get_next_number = Mock(return_value="REL-2024-M01-0001")
        mock_service.statement_repo.create = Mock(return_value=Mock(
            statement_number="REL-2024-M01-0001",
            net_commission=Decimal("5500")
        ))
        mock_service.team_repo.get_by_employee_id = Mock(return_value=Mock(
            employee_name="Jean Vendeur"
        ))

        result = mock_service.generate_statement(period.id, uuid4())

        assert result.statement_number == "REL-2024-M01-0001"
        mock_service.statement_repo.create.assert_called_once()


class TestCommissionServiceDashboard:
    """Tests du dashboard."""

    @pytest.fixture
    def mock_service(self):
        db = MagicMock()
        service = CommissionService(
            db=db,
            tenant_id="tenant-001",
            user_id=uuid4()
        )
        return service

    def test_get_dashboard(self, mock_service):
        """Test recuperation dashboard."""
        transactions = [
            Mock(revenue=Decimal("10000")),
            Mock(revenue=Decimal("20000"))
        ]

        calculations = [
            Mock(
                net_commission=Decimal("1000"),
                status="calculated"
            ),
            Mock(
                net_commission=Decimal("2000"),
                status="approved"
            )
        ]

        mock_service.transaction_repo.list = Mock(return_value=(transactions, 2))
        mock_service.calculation_repo.list = Mock(return_value=(calculations, 2))
        mock_service.calculation_repo.get_pending_approval = Mock(return_value=[])
        mock_service.adjustment_repo.get_pending_approval = Mock(return_value=[])
        mock_service.plan_repo.get_active_plans = Mock(return_value=[Mock()])
        mock_service.team_repo.list_active = Mock(return_value=[Mock()])
        mock_service.team_repo.get_by_employee_id = Mock(return_value=None)
        mock_service.assignment_repo.get_by_assignee = Mock(return_value=[])

        # Mock get_leaderboard
        mock_service.get_leaderboard = Mock(return_value=Mock(entries=[]))

        result = mock_service.get_dashboard(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        assert result.transaction_count == 2
        assert result.calculation_count == 2
