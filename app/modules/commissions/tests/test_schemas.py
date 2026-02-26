"""
Tests des schemas - Module Commissions (GAP-041)
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from pydantic import ValidationError

from app.modules.commissions.schemas import (
    CommissionPlanCreate, CommissionPlanUpdate, CommissionPlanResponse,
    CommissionTierCreate, CommissionTierUpdate,
    AcceleratorCreate, AcceleratorUpdate,
    AssignmentCreate, AssignmentUpdate,
    TeamMemberCreate,
    TransactionCreate, TransactionUpdate,
    CalculationRequest, BulkCalculationRequest,
    PeriodCreate, PeriodUpdate,
    AdjustmentCreate,
    ClawbackCreate,
    CommissionBasis, TierType, PlanStatus, PaymentFrequency, PeriodType, AdjustmentType
)


class TestCommissionTierSchemas:
    """Tests des schemas de paliers."""

    def test_tier_create_valid(self):
        tier = CommissionTierCreate(
            tier_number=1,
            name="Palier Bronze",
            min_value=Decimal("0"),
            max_value=Decimal("10000"),
            rate=Decimal("5.00")
        )

        assert tier.tier_number == 1
        assert tier.rate == Decimal("5.00")

    def test_tier_create_invalid_range(self):
        with pytest.raises(ValidationError):
            CommissionTierCreate(
                tier_number=1,
                min_value=Decimal("10000"),
                max_value=Decimal("5000"),  # max < min
                rate=Decimal("5.00")
            )

    def test_tier_create_invalid_rate(self):
        with pytest.raises(ValidationError):
            CommissionTierCreate(
                tier_number=1,
                min_value=Decimal("0"),
                rate=Decimal("150")  # > 100
            )

    def test_tier_unlimited(self):
        tier = CommissionTierCreate(
            tier_number=3,
            min_value=Decimal("50000"),
            max_value=None,  # Illimite
            rate=Decimal("10.00")
        )

        assert tier.max_value is None


class TestAcceleratorSchemas:
    """Tests des schemas d'accelerateurs."""

    def test_accelerator_create_valid(self):
        acc = AcceleratorCreate(
            name="Super Performer",
            description="Bonus 150% objectif",
            threshold_type="quota_percent",
            threshold_value=Decimal("150"),
            multiplier=Decimal("1.5")
        )

        assert acc.threshold_type == "quota_percent"
        assert acc.multiplier == Decimal("1.5")

    def test_accelerator_create_with_bonus(self):
        acc = AcceleratorCreate(
            name="Q4 Boost",
            threshold_type="absolute_amount",
            threshold_value=Decimal("100000"),
            bonus_amount=Decimal("5000"),
            valid_from=date(2024, 10, 1),
            valid_to=date(2024, 12, 31)
        )

        assert acc.bonus_amount == Decimal("5000")

    def test_accelerator_invalid_threshold_type(self):
        with pytest.raises(ValidationError):
            AcceleratorCreate(
                name="Invalid",
                threshold_type="invalid_type",
                threshold_value=Decimal("100")
            )


class TestCommissionPlanSchemas:
    """Tests des schemas de plans."""

    def test_plan_create_minimal(self):
        plan = CommissionPlanCreate(
            name="Plan Simple",
            effective_from=date(2024, 1, 1)
        )

        assert plan.name == "Plan Simple"
        assert plan.basis == CommissionBasis.REVENUE
        assert plan.tier_type == TierType.FLAT
        assert plan.clawback_enabled is True

    def test_plan_create_full(self):
        plan = CommissionPlanCreate(
            code="PLAN-001",
            name="Plan Complet",
            description="Plan de commission complet",
            basis=CommissionBasis.MARGIN,
            tier_type=TierType.PROGRESSIVE,
            payment_frequency=PaymentFrequency.MONTHLY,
            quota_period=PeriodType.QUARTERLY,
            quota_amount=Decimal("100000"),
            cap_enabled=True,
            cap_amount=Decimal("50000"),
            minimum_guaranteed=Decimal("1000"),
            clawback_enabled=True,
            clawback_period_days=90,
            trigger_on_invoice=False,
            trigger_on_payment=True,
            effective_from=date(2024, 1, 1),
            effective_to=date(2024, 12, 31),
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
            ],
            accelerators=[
                AcceleratorCreate(
                    name="Over 150%",
                    threshold_type="quota_percent",
                    threshold_value=Decimal("150"),
                    multiplier=Decimal("1.5")
                )
            ]
        )

        assert plan.code == "PLAN-001"
        assert len(plan.tiers) == 2
        assert len(plan.accelerators) == 1
        assert plan.trigger_on_payment is True

    def test_plan_create_invalid_dates(self):
        with pytest.raises(ValidationError):
            CommissionPlanCreate(
                name="Plan Invalid",
                effective_from=date(2024, 12, 31),
                effective_to=date(2024, 1, 1)  # to < from
            )

    def test_plan_code_uppercase(self):
        plan = CommissionPlanCreate(
            code="plan-lower",
            name="Test",
            effective_from=date(2024, 1, 1)
        )
        assert plan.code == "PLAN-LOWER"

    def test_plan_update_partial(self):
        update = CommissionPlanUpdate(
            name="Nouveau Nom",
            quota_amount=Decimal("150000")
        )

        assert update.name == "Nouveau Nom"
        assert update.basis is None  # Non specifie


class TestAssignmentSchemas:
    """Tests des schemas d'attribution."""

    def test_assignment_create_employee(self):
        assignment = AssignmentCreate(
            plan_id=uuid4(),
            assignee_type="employee",
            assignee_id=uuid4(),
            assignee_name="Jean Dupont",
            effective_from=date(2024, 1, 1)
        )

        assert assignment.assignee_type == "employee"

    def test_assignment_create_team(self):
        assignment = AssignmentCreate(
            plan_id=uuid4(),
            assignee_type="team",
            assignee_id=uuid4(),
            assignee_name="Equipe Paris",
            effective_from=date(2024, 1, 1),
            quota_override=Decimal("500000")
        )

        assert assignment.assignee_type == "team"
        assert assignment.quota_override == Decimal("500000")

    def test_assignment_invalid_type(self):
        with pytest.raises(ValidationError):
            AssignmentCreate(
                plan_id=uuid4(),
                assignee_type="invalid",
                assignee_id=uuid4(),
                effective_from=date(2024, 1, 1)
            )


class TestTeamMemberSchemas:
    """Tests des schemas d'equipe."""

    def test_member_create_sales_rep(self):
        member = TeamMemberCreate(
            employee_id=uuid4(),
            employee_name="Marie Martin",
            employee_email="marie@example.com",
            role="sales_rep",
            start_date=date(2024, 1, 1)
        )

        assert member.role == "sales_rep"
        assert member.override_enabled is False

    def test_member_create_manager(self):
        member = TeamMemberCreate(
            employee_id=uuid4(),
            employee_name="Paul Manager",
            role="sales_manager",
            start_date=date(2024, 1, 1),
            override_enabled=True,
            override_rate=Decimal("3.0"),
            override_levels=2
        )

        assert member.override_enabled is True
        assert member.override_rate == Decimal("3.0")

    def test_member_invalid_role(self):
        with pytest.raises(ValidationError):
            TeamMemberCreate(
                employee_id=uuid4(),
                role="invalid_role",
                start_date=date(2024, 1, 1)
            )


class TestTransactionSchemas:
    """Tests des schemas de transactions."""

    def test_transaction_create_minimal(self):
        txn = TransactionCreate(
            source_type="invoice",
            source_id=uuid4(),
            source_number="FAC-2024-0001",
            source_date=date(2024, 1, 15),
            sales_rep_id=uuid4(),
            customer_id=uuid4(),
            revenue=Decimal("10000")
        )

        assert txn.source_type == "invoice"
        assert txn.revenue == Decimal("10000")
        assert txn.currency == "EUR"

    def test_transaction_create_with_split(self):
        txn = TransactionCreate(
            source_type="order",
            source_id=uuid4(),
            source_date=date(2024, 1, 20),
            sales_rep_id=uuid4(),
            customer_id=uuid4(),
            revenue=Decimal("50000"),
            split_config=[
                {"participant_id": str(uuid4()), "role": "secondary", "percent": 30}
            ]
        )

        assert len(txn.split_config) == 1

    def test_transaction_invalid_source_type(self):
        with pytest.raises(ValidationError):
            TransactionCreate(
                source_type="invalid",
                source_id=uuid4(),
                source_date=date.today(),
                sales_rep_id=uuid4(),
                customer_id=uuid4(),
                revenue=Decimal("1000")
            )


class TestCalculationRequestSchemas:
    """Tests des schemas de calcul."""

    def test_calculation_request(self):
        req = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=uuid4(),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )

        assert req.recalculate is False

    def test_calculation_request_recalculate(self):
        req = CalculationRequest(
            sales_rep_id=uuid4(),
            plan_id=uuid4(),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            recalculate=True
        )

        assert req.recalculate is True

    def test_bulk_calculation_request(self):
        req = BulkCalculationRequest(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            plan_ids=[uuid4(), uuid4()],
            recalculate=False
        )

        assert len(req.plan_ids) == 2


class TestPeriodSchemas:
    """Tests des schemas de periodes."""

    def test_period_create(self):
        period = PeriodCreate(
            code="2024-M01",
            name="Janvier 2024",
            period_type=PeriodType.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            payment_date=date(2024, 2, 10)
        )

        assert period.code == "2024-M01"
        assert period.period_type == PeriodType.MONTHLY


class TestAdjustmentSchemas:
    """Tests des schemas d'ajustements."""

    def test_adjustment_create_bonus(self):
        adj = AdjustmentCreate(
            adjustment_type=AdjustmentType.BONUS,
            sales_rep_id=uuid4(),
            effective_date=date(2024, 1, 31),
            amount=Decimal("1000"),
            reason="Prime exceptionnelle"
        )

        assert adj.adjustment_type == AdjustmentType.BONUS
        assert adj.amount == Decimal("1000")

    def test_adjustment_create_penalty(self):
        adj = AdjustmentCreate(
            adjustment_type=AdjustmentType.PENALTY,
            sales_rep_id=uuid4(),
            effective_date=date(2024, 1, 31),
            amount=Decimal("-500"),
            reason="Penalite"
        )

        assert adj.amount == Decimal("-500")


class TestClawbackSchemas:
    """Tests des schemas de clawbacks."""

    def test_clawback_create(self):
        clawback = ClawbackCreate(
            original_calculation_id=uuid4(),
            original_transaction_id=uuid4(),
            sales_rep_id=uuid4(),
            clawback_amount=Decimal("500"),
            reason="cancellation",
            reason_details="Annulation commande",
            cancellation_date=date(2024, 2, 15)
        )

        assert clawback.reason == "cancellation"
        assert clawback.clawback_percent == Decimal("100")

    def test_clawback_invalid_reason(self):
        with pytest.raises(ValidationError):
            ClawbackCreate(
                original_calculation_id=uuid4(),
                original_transaction_id=uuid4(),
                sales_rep_id=uuid4(),
                clawback_amount=Decimal("500"),
                reason="invalid_reason",
                cancellation_date=date(2024, 2, 15)
            )
