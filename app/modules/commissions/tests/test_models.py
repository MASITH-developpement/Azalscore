"""
Tests des modeles - Module Commissions (GAP-041)
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.modules.commissions.models import (
    CommissionPlan, CommissionTier, CommissionAccelerator,
    CommissionAssignment, SalesTeamMember,
    CommissionTransaction, CommissionCalculation,
    CommissionPeriod, CommissionStatement,
    CommissionAdjustment, CommissionClawback,
    CommissionBasis, TierType, PlanStatus, CommissionStatus,
    PaymentFrequency, PeriodType, AdjustmentType, WorkflowStatus
)


class TestEnums:
    """Tests des enumerations."""

    def test_commission_basis_values(self):
        assert CommissionBasis.REVENUE.value == "revenue"
        assert CommissionBasis.MARGIN.value == "margin"
        assert CommissionBasis.COLLECTED.value == "collected"
        assert CommissionBasis.NEW_BUSINESS.value == "new_business"

    def test_tier_type_values(self):
        assert TierType.FLAT.value == "flat"
        assert TierType.PROGRESSIVE.value == "progressive"
        assert TierType.RETROACTIVE.value == "retroactive"
        assert TierType.REGRESSIVE.value == "regressive"
        assert TierType.STEPPED.value == "stepped"

    def test_plan_status_values(self):
        assert PlanStatus.DRAFT.value == "draft"
        assert PlanStatus.ACTIVE.value == "active"
        assert PlanStatus.SUSPENDED.value == "suspended"
        assert PlanStatus.ARCHIVED.value == "archived"

    def test_commission_status_values(self):
        assert CommissionStatus.PENDING.value == "pending"
        assert CommissionStatus.CALCULATED.value == "calculated"
        assert CommissionStatus.APPROVED.value == "approved"
        assert CommissionStatus.PAID.value == "paid"

    def test_payment_frequency_values(self):
        assert PaymentFrequency.MONTHLY.value == "monthly"
        assert PaymentFrequency.QUARTERLY.value == "quarterly"
        assert PaymentFrequency.ON_PAYMENT.value == "on_payment"


class TestCommissionPlanModel:
    """Tests du modele CommissionPlan."""

    def test_plan_creation(self):
        plan = CommissionPlan(
            tenant_id="tenant-001",
            code="PLAN-001",
            name="Plan Standard",
            description="Plan de commission standard",
            basis=CommissionBasis.REVENUE.value,
            tier_type=TierType.PROGRESSIVE.value,
            payment_frequency=PaymentFrequency.MONTHLY.value,
            effective_from=date(2024, 1, 1)
        )

        assert plan.tenant_id == "tenant-001"
        assert plan.code == "PLAN-001"
        assert plan.name == "Plan Standard"
        assert plan.status == PlanStatus.DRAFT.value
        assert plan.quota_period == PeriodType.MONTHLY.value
        assert plan.clawback_enabled is True
        assert plan.clawback_period_days == 90

    def test_plan_defaults(self):
        plan = CommissionPlan(
            tenant_id="tenant-001",
            code="PLAN-002",
            name="Plan Test",
            effective_from=date.today()
        )

        assert plan.basis == CommissionBasis.REVENUE.value
        assert plan.tier_type == TierType.FLAT.value
        assert plan.payment_frequency == PaymentFrequency.MONTHLY.value
        assert plan.minimum_guaranteed == Decimal("0")
        assert plan.cap_enabled is False
        assert plan.apply_to_all_products is True
        assert plan.trigger_on_invoice is True
        assert plan.trigger_on_payment is False
        assert plan.version == 1
        assert plan.is_deleted is False


class TestCommissionTierModel:
    """Tests du modele CommissionTier."""

    def test_tier_creation(self):
        tier = CommissionTier(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            tier_number=1,
            name="Palier Bronze",
            min_value=Decimal("0"),
            max_value=Decimal("10000"),
            rate=Decimal("5.00"),
            fixed_amount=Decimal("0")
        )

        assert tier.tier_number == 1
        assert tier.min_value == Decimal("0")
        assert tier.max_value == Decimal("10000")
        assert tier.rate == Decimal("5.00")
        assert tier.is_active is True

    def test_tier_unlimited(self):
        tier = CommissionTier(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            tier_number=3,
            name="Palier Gold",
            min_value=Decimal("50000"),
            max_value=None,  # Illimite
            rate=Decimal("10.00")
        )

        assert tier.max_value is None


class TestCommissionAcceleratorModel:
    """Tests du modele CommissionAccelerator."""

    def test_accelerator_creation(self):
        accelerator = CommissionAccelerator(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            name="Super Performer",
            description="Bonus 150% objectif",
            threshold_type="quota_percent",
            threshold_value=Decimal("150"),
            multiplier=Decimal("1.5"),
            is_cumulative=False
        )

        assert accelerator.name == "Super Performer"
        assert accelerator.threshold_type == "quota_percent"
        assert accelerator.threshold_value == Decimal("150")
        assert accelerator.multiplier == Decimal("1.5")
        assert accelerator.is_active is True

    def test_accelerator_with_dates(self):
        accelerator = CommissionAccelerator(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            name="Q4 Boost",
            threshold_type="absolute_amount",
            threshold_value=Decimal("100000"),
            bonus_amount=Decimal("5000"),
            valid_from=date(2024, 10, 1),
            valid_to=date(2024, 12, 31)
        )

        assert accelerator.valid_from == date(2024, 10, 1)
        assert accelerator.valid_to == date(2024, 12, 31)


class TestCommissionAssignmentModel:
    """Tests du modele CommissionAssignment."""

    def test_assignment_creation(self):
        assignment = CommissionAssignment(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            assignee_type="employee",
            assignee_id=uuid4(),
            assignee_name="Jean Dupont",
            effective_from=date(2024, 1, 1)
        )

        assert assignment.assignee_type == "employee"
        assert assignment.is_active is True
        assert assignment.quota_override is None

    def test_assignment_with_override(self):
        assignment = CommissionAssignment(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            assignee_type="team",
            assignee_id=uuid4(),
            assignee_name="Equipe Paris",
            effective_from=date(2024, 1, 1),
            quota_override=Decimal("500000"),
            personal_rate_override=Decimal("7.5")
        )

        assert assignment.quota_override == Decimal("500000")
        assert assignment.personal_rate_override == Decimal("7.5")


class TestSalesTeamMemberModel:
    """Tests du modele SalesTeamMember."""

    def test_member_creation(self):
        member = SalesTeamMember(
            tenant_id="tenant-001",
            employee_id=uuid4(),
            employee_name="Marie Martin",
            employee_email="marie@example.com",
            role="sales_rep",
            start_date=date(2024, 1, 1)
        )

        assert member.role == "sales_rep"
        assert member.is_active is True
        assert member.override_enabled is False
        assert member.default_split_percent == Decimal("100")

    def test_member_manager_with_override(self):
        member = SalesTeamMember(
            tenant_id="tenant-001",
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
        assert member.override_levels == 2


class TestCommissionTransactionModel:
    """Tests du modele CommissionTransaction."""

    def test_transaction_creation(self):
        transaction = CommissionTransaction(
            tenant_id="tenant-001",
            source_type="invoice",
            source_id=uuid4(),
            source_number="FAC-2024-0001",
            source_date=date(2024, 1, 15),
            sales_rep_id=uuid4(),
            sales_rep_name="Jean Vendeur",
            customer_id=uuid4(),
            customer_name="Client SA",
            revenue=Decimal("10000"),
            cost=Decimal("7000"),
            margin=Decimal("3000"),
            margin_percent=Decimal("30.00")
        )

        assert transaction.source_type == "invoice"
        assert transaction.revenue == Decimal("10000")
        assert transaction.margin == Decimal("3000")
        assert transaction.commission_status == "pending"
        assert transaction.commission_locked is False
        assert transaction.has_split is False

    def test_transaction_with_split(self):
        transaction = CommissionTransaction(
            tenant_id="tenant-001",
            source_type="order",
            source_id=uuid4(),
            source_date=date(2024, 1, 20),
            sales_rep_id=uuid4(),
            customer_id=uuid4(),
            revenue=Decimal("50000"),
            cost=Decimal("35000"),
            has_split=True,
            split_config=[
                {"participant_id": str(uuid4()), "role": "secondary", "percent": 30}
            ]
        )

        assert transaction.has_split is True
        assert len(transaction.split_config) == 1


class TestCommissionCalculationModel:
    """Tests du modele CommissionCalculation."""

    def test_calculation_creation(self):
        calculation = CommissionCalculation(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            sales_rep_id=uuid4(),
            sales_rep_name="Jean Vendeur",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basis=CommissionBasis.REVENUE.value,
            base_amount=Decimal("100000"),
            rate_applied=Decimal("5.00"),
            commission_amount=Decimal("5000"),
            gross_commission=Decimal("5000"),
            net_commission=Decimal("5000")
        )

        assert calculation.base_amount == Decimal("100000")
        assert calculation.commission_amount == Decimal("5000")
        assert calculation.status == CommissionStatus.CALCULATED.value
        assert calculation.version == 1

    def test_calculation_with_accelerators(self):
        calculation = CommissionCalculation(
            tenant_id="tenant-001",
            plan_id=uuid4(),
            sales_rep_id=uuid4(),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            basis=CommissionBasis.REVENUE.value,
            base_amount=Decimal("150000"),
            commission_amount=Decimal("7500"),
            accelerator_bonus=Decimal("3750"),
            accelerators_applied=["acc-001"],
            gross_commission=Decimal("11250"),
            net_commission=Decimal("11250"),
            quota_target=Decimal("100000"),
            quota_achieved=Decimal("150000"),
            achievement_rate=Decimal("150.00")
        )

        assert calculation.accelerator_bonus == Decimal("3750")
        assert calculation.achievement_rate == Decimal("150.00")


class TestCommissionPeriodModel:
    """Tests du modele CommissionPeriod."""

    def test_period_creation(self):
        period = CommissionPeriod(
            tenant_id="tenant-001",
            code="2024-M01",
            name="Janvier 2024",
            period_type=PeriodType.MONTHLY.value,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            payment_date=date(2024, 2, 10)
        )

        assert period.code == "2024-M01"
        assert period.status == "open"
        assert period.is_locked is False
        assert period.total_commissions == Decimal("0")


class TestCommissionStatementModel:
    """Tests du modele CommissionStatement."""

    def test_statement_creation(self):
        statement = CommissionStatement(
            tenant_id="tenant-001",
            statement_number="REL-2024-M01-0001",
            period_id=uuid4(),
            sales_rep_id=uuid4(),
            sales_rep_name="Jean Vendeur",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            gross_commissions=Decimal("5000"),
            accelerator_bonuses=Decimal("500"),
            adjustments=Decimal("200"),
            clawbacks=Decimal("0"),
            net_commission=Decimal("5700")
        )

        assert statement.net_commission == Decimal("5700")
        assert statement.status == CommissionStatus.PENDING.value
        assert statement.payroll_exported is False


class TestCommissionAdjustmentModel:
    """Tests du modele CommissionAdjustment."""

    def test_adjustment_creation(self):
        adjustment = CommissionAdjustment(
            tenant_id="tenant-001",
            code="ADJ-BON-2024-0001",
            adjustment_type=AdjustmentType.BONUS.value,
            sales_rep_id=uuid4(),
            sales_rep_name="Jean Vendeur",
            effective_date=date(2024, 1, 31),
            amount=Decimal("1000"),
            reason="Prime exceptionnelle Q1",
            requested_by=uuid4()
        )

        assert adjustment.adjustment_type == AdjustmentType.BONUS.value
        assert adjustment.amount == Decimal("1000")
        assert adjustment.status == WorkflowStatus.PENDING.value

    def test_adjustment_negative(self):
        adjustment = CommissionAdjustment(
            tenant_id="tenant-001",
            code="ADJ-PEN-2024-0001",
            adjustment_type=AdjustmentType.PENALTY.value,
            sales_rep_id=uuid4(),
            effective_date=date(2024, 1, 31),
            amount=Decimal("-500"),
            reason="Penalite retard objectif",
            requested_by=uuid4()
        )

        assert adjustment.amount == Decimal("-500")


class TestCommissionClawbackModel:
    """Tests du modele CommissionClawback."""

    def test_clawback_creation(self):
        clawback = CommissionClawback(
            tenant_id="tenant-001",
            code="CLB-202401-0001",
            original_calculation_id=uuid4(),
            original_transaction_id=uuid4(),
            original_commission=Decimal("500"),
            sales_rep_id=uuid4(),
            sales_rep_name="Jean Vendeur",
            clawback_amount=Decimal("500"),
            clawback_percent=Decimal("100"),
            reason="cancellation",
            reason_details="Annulation commande client",
            cancellation_date=date(2024, 2, 15)
        )

        assert clawback.reason == "cancellation"
        assert clawback.clawback_amount == Decimal("500")
        assert clawback.status == "pending"

    def test_clawback_partial(self):
        clawback = CommissionClawback(
            tenant_id="tenant-001",
            code="CLB-202401-0002",
            original_calculation_id=uuid4(),
            original_transaction_id=uuid4(),
            original_commission=Decimal("1000"),
            sales_rep_id=uuid4(),
            clawback_amount=Decimal("500"),
            clawback_percent=Decimal("50"),
            reason="refund",
            cancellation_date=date(2024, 2, 20)
        )

        assert clawback.clawback_percent == Decimal("50")
        assert clawback.clawback_amount == Decimal("500")
