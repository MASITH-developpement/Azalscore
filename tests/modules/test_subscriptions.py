"""
AZALS MODULE 14 - Tests Subscriptions
======================================
Tests bloquants pour la gestion des abonnements.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.subscriptions.models import (
    SubscriptionPlan, PlanAddOn, Subscription, SubscriptionItem,
    SubscriptionInvoice, InvoiceLine, SubscriptionPayment,
    UsageRecord, SubscriptionCoupon, SubscriptionMetrics,
    PlanInterval, SubscriptionStatus, InvoiceStatus,
    PaymentStatus, UsageType
)
from app.modules.subscriptions.schemas import (
    PlanCreate, PlanUpdate, AddOnCreate,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionItemCreate,
    SubscriptionChangePlanRequest, SubscriptionCancelRequest,
    InvoiceCreate, InvoiceLineCreate, PaymentCreate,
    UsageRecordCreate, CouponCreate, CouponValidateRequest
)
from app.modules.subscriptions.service import SubscriptionService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    return db


@pytest.fixture
def sub_service(mock_db):
    """Subscription service instance."""
    return SubscriptionService(mock_db, "test-tenant")


@pytest.fixture
def sample_plan():
    """Sample plan data."""
    return PlanCreate(
        code="PRO",
        name="Plan Pro",
        description="Plan professionnel",
        base_price=Decimal("99.00"),
        currency="EUR",
        interval=PlanInterval.MONTHLY,
        interval_count=1,
        trial_days=14,
        max_users=10,
        features={"api": True, "support": "priority"}
    )


@pytest.fixture
def sample_subscription():
    """Sample subscription data."""
    return SubscriptionCreate(
        plan_id=1,
        customer_id=100,
        customer_name="Entreprise Test",
        customer_email="contact@test.com",
        quantity=5
    )


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestSubscriptionModels:
    """Tests des modèles Subscriptions."""

    def test_plan_model_creation(self):
        """Test création modèle plan."""
        plan = SubscriptionPlan(
            tenant_id="test",
            code="STARTER",
            name="Plan Starter",
            base_price=Decimal("29.00"),
            interval=PlanInterval.MONTHLY
        )
        assert plan.code == "STARTER"
        assert plan.interval == PlanInterval.MONTHLY

    def test_subscription_model_creation(self):
        """Test création modèle abonnement."""
        sub = Subscription(
            tenant_id="test",
            subscription_number="SUB202401-00001",
            plan_id=1,
            customer_id=100,
            status=SubscriptionStatus.ACTIVE,
            quantity=3,
            current_period_start=date.today(),
            current_period_end=date.today() + timedelta(days=30),
            started_at=date.today(),
            mrr=Decimal("99.00")
        )
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.quantity == 3

    def test_invoice_model_creation(self):
        """Test création modèle facture."""
        invoice = SubscriptionInvoice(
            tenant_id="test",
            subscription_id=1,
            invoice_number="INV202401-00001",
            customer_id=100,
            status=InvoiceStatus.OPEN,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            subtotal=Decimal("99.00"),
            total=Decimal("118.80"),
            amount_remaining=Decimal("118.80")
        )
        assert invoice.status == InvoiceStatus.OPEN

    def test_coupon_model_creation(self):
        """Test création modèle coupon."""
        coupon = SubscriptionCoupon(
            tenant_id="test",
            code="SUMMER20",
            name="Promo été",
            discount_type="percent",
            discount_value=Decimal("20"),
            duration="once"
        )
        assert coupon.code == "SUMMER20"
        assert coupon.discount_value == Decimal("20")


# ============================================================================
# SCHEMA TESTS
# ============================================================================

class TestSubscriptionSchemas:
    """Tests des schémas Subscriptions."""

    def test_plan_create_schema(self, sample_plan):
        """Test schéma création plan."""
        assert sample_plan.code == "PRO"
        assert sample_plan.base_price == Decimal("99.00")
        assert sample_plan.trial_days == 14

    def test_subscription_create_schema(self, sample_subscription):
        """Test schéma création abonnement."""
        assert sample_subscription.plan_id == 1
        assert sample_subscription.customer_id == 100
        assert sample_subscription.quantity == 5

    def test_invoice_line_create_schema(self):
        """Test schéma création ligne facture."""
        line = InvoiceLineCreate(
            description="Abonnement Pro - Janvier 2024",
            item_type="subscription",
            quantity=Decimal("1"),
            unit_price=Decimal("99.00"),
            tax_rate=Decimal("20.00")
        )
        assert line.description == "Abonnement Pro - Janvier 2024"
        assert line.unit_price == Decimal("99.00")

    def test_coupon_create_schema(self):
        """Test schéma création coupon."""
        coupon = CouponCreate(
            code="NEWYEAR",
            name="Nouvel An",
            discount_type="percent",
            discount_value=Decimal("25"),
            duration="repeating",
            duration_months=3
        )
        assert coupon.code == "NEWYEAR"
        assert coupon.duration_months == 3

    def test_usage_record_create_schema(self):
        """Test schéma création usage."""
        usage = UsageRecordCreate(
            subscription_item_id=1,
            quantity=Decimal("1000"),
            unit="api_calls",
            action="increment"
        )
        assert usage.quantity == Decimal("1000")
        assert usage.action == "increment"


# ============================================================================
# SERVICE TESTS - PLANS
# ============================================================================

class TestPlanService:
    """Tests service plans."""

    def test_create_plan_success(self, sub_service, sample_plan, mock_db):
        """Test création plan réussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        plan = sub_service.create_plan(sample_plan)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_plan_duplicate_code(self, sub_service, sample_plan, mock_db):
        """Test création plan code dupliqué."""
        existing = SubscriptionPlan(id=1, code="PRO", tenant_id="test")
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValueError, match="déjà utilisé"):
            sub_service.create_plan(sample_plan)

    def test_list_plans(self, sub_service, mock_db):
        """Test liste plans."""
        plans = [
            SubscriptionPlan(id=1, code="STARTER", tenant_id="test"),
            SubscriptionPlan(id=2, code="PRO", tenant_id="test")
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = plans

        items, total = sub_service.list_plans()
        assert total == 2


# ============================================================================
# SERVICE TESTS - SUBSCRIPTIONS
# ============================================================================

class TestSubscriptionService:
    """Tests service abonnements."""

    def test_create_subscription_success(self, sub_service, sample_subscription, mock_db):
        """Test création abonnement réussie."""
        plan = SubscriptionPlan(
            id=1, code="PRO", name="Pro",
            tenant_id="test", base_price=Decimal("99.00"),
            interval=PlanInterval.MONTHLY, interval_count=1,
            trial_days=0, is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            plan,  # get_plan
            None   # _generate_subscription_number
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        sub = sub_service.create_subscription(sample_subscription)
        mock_db.add.assert_called()

    def test_create_subscription_plan_not_found(self, sub_service, sample_subscription, mock_db):
        """Test création abonnement plan inexistant."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Plan introuvable"):
            sub_service.create_subscription(sample_subscription)

    def test_create_subscription_with_trial(self, sub_service, mock_db):
        """Test création abonnement avec essai."""
        plan = SubscriptionPlan(
            id=1, code="PRO", name="Pro",
            tenant_id="test", base_price=Decimal("99.00"),
            interval=PlanInterval.MONTHLY, interval_count=1,
            trial_days=14, trial_once=True, is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            plan,  # get_plan
            None,  # check existing trial
            None   # _generate_subscription_number
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = SubscriptionCreate(
            plan_id=1,
            customer_id=100,
            customer_name="Test"
        )

        sub = sub_service.create_subscription(data)
        # Vérifie que l'abonnement est créé
        mock_db.add.assert_called()

    def test_cancel_subscription_success(self, sub_service, mock_db):
        """Test annulation abonnement réussie."""
        sub = Subscription(
            id=1, tenant_id="test", subscription_number="SUB001",
            plan_id=1, customer_id=100, status=SubscriptionStatus.ACTIVE,
            current_period_start=date.today(),
            current_period_end=date.today() + timedelta(days=30),
            mrr=Decimal("99.00")
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sub

        data = SubscriptionCancelRequest(
            cancel_at_period_end=True,
            reason="Plus besoin"
        )

        result = sub_service.cancel_subscription(1, data)
        assert sub.cancel_at_period_end is True
        assert sub.canceled_at is not None

    def test_pause_subscription_success(self, sub_service, mock_db):
        """Test mise en pause abonnement."""
        sub = Subscription(
            id=1, tenant_id="test", subscription_number="SUB001",
            plan_id=1, customer_id=100, status=SubscriptionStatus.ACTIVE,
            mrr=Decimal("99.00")
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sub

        from app.modules.subscriptions.schemas import SubscriptionPauseRequest
        data = SubscriptionPauseRequest(
            resume_at=date.today() + timedelta(days=30),
            reason="Vacances"
        )

        result = sub_service.pause_subscription(1, data)
        assert sub.status == SubscriptionStatus.PAUSED


# ============================================================================
# SERVICE TESTS - INVOICES
# ============================================================================

class TestInvoiceService:
    """Tests service factures."""

    def test_create_invoice_success(self, sub_service, mock_db):
        """Test création facture réussie."""
        sub = Subscription(
            id=1, tenant_id="test", subscription_number="SUB001",
            plan_id=1, customer_id=100, status=SubscriptionStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sub, None
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = InvoiceCreate(
            subscription_id=1,
            customer_id=100,
            customer_name="Test",
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            lines=[
                InvoiceLineCreate(
                    description="Abonnement Pro",
                    quantity=Decimal("1"),
                    unit_price=Decimal("99.00"),
                    tax_rate=Decimal("20.00")
                )
            ]
        )

        invoice = sub_service.create_invoice(data)
        mock_db.add.assert_called()

    def test_finalize_invoice_success(self, sub_service, mock_db):
        """Test finalisation facture."""
        invoice = SubscriptionInvoice(
            id=1, tenant_id="test", invoice_number="INV001",
            subscription_id=1, customer_id=100,
            status=InvoiceStatus.DRAFT,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            total=Decimal("99.00"),
            amount_remaining=Decimal("99.00")
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice

        result = sub_service.finalize_invoice(1)
        assert invoice.status == InvoiceStatus.OPEN
        assert invoice.finalized_at is not None

    def test_void_invoice_success(self, sub_service, mock_db):
        """Test annulation facture."""
        invoice = SubscriptionInvoice(
            id=1, tenant_id="test", invoice_number="INV001",
            status=InvoiceStatus.OPEN,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice

        result = sub_service.void_invoice(1)
        assert invoice.status == InvoiceStatus.VOID

    def test_void_paid_invoice_fails(self, sub_service, mock_db):
        """Test annulation facture payée échoue."""
        invoice = SubscriptionInvoice(
            id=1, tenant_id="test", invoice_number="INV001",
            status=InvoiceStatus.PAID,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = invoice

        with pytest.raises(ValueError, match="payée"):
            sub_service.void_invoice(1)


# ============================================================================
# SERVICE TESTS - COUPONS
# ============================================================================

class TestCouponService:
    """Tests service coupons."""

    def test_create_coupon_success(self, sub_service, mock_db):
        """Test création coupon réussie."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = CouponCreate(
            code="SAVE20",
            name="Économisez 20%",
            discount_type="percent",
            discount_value=Decimal("20"),
            duration="once"
        )

        coupon = sub_service.create_coupon(data)
        mock_db.add.assert_called_once()

    def test_validate_coupon_valid(self, sub_service, mock_db):
        """Test validation coupon valide."""
        coupon = SubscriptionCoupon(
            id=1, tenant_id="test",
            code="SAVE20", name="Save 20%",
            discount_type="percent",
            discount_value=Decimal("20"),
            duration="once",
            is_active=True,
            times_redeemed=0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = coupon

        data = CouponValidateRequest(
            code="SAVE20",
            amount=Decimal("100.00")
        )

        result = sub_service.validate_coupon(data)
        assert result["valid"] is True
        assert result["discount_amount"] == Decimal("20.00")

    def test_validate_coupon_expired(self, sub_service, mock_db):
        """Test validation coupon expiré."""
        coupon = SubscriptionCoupon(
            id=1, tenant_id="test",
            code="EXPIRED", name="Expired",
            discount_type="percent",
            discount_value=Decimal("20"),
            is_active=True,
            valid_until=datetime.utcnow() - timedelta(days=1)
        )
        mock_db.query.return_value.filter.return_value.first.return_value = coupon

        data = CouponValidateRequest(code="EXPIRED")

        result = sub_service.validate_coupon(data)
        assert result["valid"] is False
        assert "expiré" in result["error_message"]

    def test_validate_coupon_max_redemptions(self, sub_service, mock_db):
        """Test validation coupon limite atteinte."""
        coupon = SubscriptionCoupon(
            id=1, tenant_id="test",
            code="LIMITED", name="Limited",
            discount_type="percent",
            discount_value=Decimal("20"),
            is_active=True,
            max_redemptions=100,
            times_redeemed=100
        )
        mock_db.query.return_value.filter.return_value.first.return_value = coupon

        data = CouponValidateRequest(code="LIMITED")

        result = sub_service.validate_coupon(data)
        assert result["valid"] is False
        assert "Limite" in result["error_message"]


# ============================================================================
# SERVICE TESTS - USAGE
# ============================================================================

class TestUsageService:
    """Tests service usage."""

    def test_create_usage_record_success(self, sub_service, mock_db):
        """Test création enregistrement usage."""
        item = SubscriptionItem(
            id=1, tenant_id="test", subscription_id=1,
            name="API Calls", usage_type=UsageType.METERED,
            metered_usage=Decimal("0")
        )
        sub = Subscription(
            id=1, tenant_id="test", subscription_number="SUB001",
            current_period_start=date.today(),
            current_period_end=date.today() + timedelta(days=30)
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # idempotency check
            item,  # get item
            sub    # get subscription
        ]

        data = UsageRecordCreate(
            subscription_item_id=1,
            quantity=Decimal("100"),
            unit="api_calls",
            action="increment"
        )

        record = sub_service.create_usage_record(data)
        mock_db.add.assert_called()
        assert item.metered_usage == Decimal("100")

    def test_create_usage_record_not_metered(self, sub_service, mock_db):
        """Test usage sur item non metered échoue."""
        item = SubscriptionItem(
            id=1, tenant_id="test", subscription_id=1,
            name="Seats", usage_type=UsageType.LICENSED
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None, item
        ]

        data = UsageRecordCreate(
            subscription_item_id=1,
            quantity=Decimal("100"),
            action="increment"
        )

        with pytest.raises(ValueError, match="metered"):
            sub_service.create_usage_record(data)


# ============================================================================
# SERVICE TESTS - PAYMENTS
# ============================================================================

class TestPaymentService:
    """Tests service paiements."""

    def test_create_payment_success(self, sub_service, mock_db):
        """Test création paiement réussie."""
        invoice = SubscriptionInvoice(
            id=1, tenant_id="test", invoice_number="INV001",
            subscription_id=1, customer_id=100,
            status=InvoiceStatus.OPEN, total=Decimal("99.00"),
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30)
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            invoice, None
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        data = PaymentCreate(
            invoice_id=1,
            amount=Decimal("99.00"),
            payment_method_type="card"
        )

        payment = sub_service.create_payment(data)
        mock_db.add.assert_called()

    def test_refund_payment_success(self, sub_service, mock_db):
        """Test remboursement paiement."""
        payment = SubscriptionPayment(
            id=1, tenant_id="test", payment_number="PAY001",
            customer_id=100, amount=Decimal("99.00"),
            status=PaymentStatus.SUCCEEDED,
            refunded_amount=Decimal("0")
        )
        mock_db.query.return_value.filter.return_value.first.return_value = payment

        result = sub_service.refund_payment(1, Decimal("50.00"), "Partial refund")
        assert payment.refunded_amount == Decimal("50.00")
        assert payment.status == PaymentStatus.PARTIALLY_REFUNDED


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestSubscriptionEnums:
    """Tests des énumérations."""

    def test_plan_interval_values(self):
        """Test valeurs intervalles plan."""
        assert PlanInterval.DAILY.value == "daily"
        assert PlanInterval.WEEKLY.value == "weekly"
        assert PlanInterval.MONTHLY.value == "monthly"
        assert PlanInterval.QUARTERLY.value == "quarterly"
        assert PlanInterval.ANNUAL.value == "annual"
        assert PlanInterval.LIFETIME.value == "lifetime"

    def test_subscription_status_values(self):
        """Test valeurs statut abonnement."""
        assert SubscriptionStatus.TRIALING.value == "trialing"
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.PAUSED.value == "paused"
        assert SubscriptionStatus.CANCELED.value == "canceled"

    def test_invoice_status_values(self):
        """Test valeurs statut facture."""
        assert InvoiceStatus.DRAFT.value == "draft"
        assert InvoiceStatus.OPEN.value == "open"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.VOID.value == "void"

    def test_payment_status_values(self):
        """Test valeurs statut paiement."""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.REFUNDED.value == "refunded"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSubscriptionIntegration:
    """Tests d'intégration."""

    def test_mrr_calculation_monthly(self, sub_service):
        """Test calcul MRR mensuel."""
        plan = SubscriptionPlan(
            id=1, code="PRO", base_price=Decimal("99.00"),
            interval=PlanInterval.MONTHLY
        )
        sub = Subscription(
            id=1, tenant_id="test", plan_id=1,
            quantity=3, discount_percent=Decimal("0")
        )
        sub.plan = plan
        sub.items = []

        mrr = sub_service._calculate_mrr(sub)
        assert mrr == Decimal("297.00")  # 99 * 3

    def test_mrr_calculation_annual(self, sub_service):
        """Test calcul MRR annuel."""
        plan = SubscriptionPlan(
            id=1, code="PRO", base_price=Decimal("1188.00"),
            interval=PlanInterval.ANNUAL
        )
        sub = Subscription(
            id=1, tenant_id="test", plan_id=1,
            quantity=1, discount_percent=Decimal("0")
        )
        sub.plan = plan
        sub.items = []

        mrr = sub_service._calculate_mrr(sub)
        assert mrr == Decimal("99.00")  # 1188 / 12

    def test_mrr_calculation_with_discount(self, sub_service):
        """Test calcul MRR avec remise."""
        plan = SubscriptionPlan(
            id=1, code="PRO", base_price=Decimal("100.00"),
            interval=PlanInterval.MONTHLY
        )
        sub = Subscription(
            id=1, tenant_id="test", plan_id=1,
            quantity=1, discount_percent=Decimal("20"),
            discount_end_date=date.today() + timedelta(days=30)
        )
        sub.plan = plan
        sub.items = []

        mrr = sub_service._calculate_mrr(sub)
        assert mrr == Decimal("80.00")  # 100 - 20%

    def test_period_end_calculation(self, sub_service):
        """Test calcul fin de période."""
        start = date(2024, 1, 15)

        # Mensuel
        end = sub_service._calculate_period_end(start, PlanInterval.MONTHLY, 1)
        assert end == date(2024, 2, 15)

        # Trimestriel
        end = sub_service._calculate_period_end(start, PlanInterval.QUARTERLY, 1)
        assert end == date(2024, 4, 15)

        # Annuel
        end = sub_service._calculate_period_end(start, PlanInterval.ANNUAL, 1)
        assert end == date(2025, 1, 15)


# ============================================================================
# EDGE CASES
# ============================================================================

class TestSubscriptionEdgeCases:
    """Tests cas limites."""

    def test_subscription_lifecycle(self, sub_service):
        """Test cycle de vie complet abonnement."""
        # Vérifie que les méthodes existent
        assert hasattr(sub_service, 'create_subscription')
        assert hasattr(sub_service, 'change_plan')
        assert hasattr(sub_service, 'pause_subscription')
        assert hasattr(sub_service, 'resume_subscription')
        assert hasattr(sub_service, 'cancel_subscription')

    def test_coupon_fixed_amount(self, sub_service, mock_db):
        """Test coupon montant fixe."""
        coupon = SubscriptionCoupon(
            id=1, tenant_id="test",
            code="FLAT10", name="10€ off",
            discount_type="fixed_amount",
            discount_value=Decimal("10"),
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = coupon

        # Test avec montant supérieur
        result = sub_service.validate_coupon(
            CouponValidateRequest(code="FLAT10", amount=Decimal("100.00"))
        )
        assert result["valid"] is True
        assert result["discount_amount"] == Decimal("10.00")

        # Test avec montant inférieur
        result = sub_service.validate_coupon(
            CouponValidateRequest(code="FLAT10", amount=Decimal("5.00"))
        )
        assert result["valid"] is True
        assert result["discount_amount"] == Decimal("5.00")  # Max = montant
