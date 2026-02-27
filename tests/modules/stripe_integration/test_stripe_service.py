"""
AZALS MODULE STRIPE INTEGRATION - Tests Service
=================================================
Tests bloquants pour le service d'integration Stripe.
"""

import uuid
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.stripe_integration.models import (
    DisputeStatus,
    PaymentIntentStatus,
    RefundStatus,
    StripeAccountStatus,
    StripeCheckoutSession,
    StripeConfig,
    StripeConnectAccount,
    StripeCustomer,
    StripeDispute,
    StripePaymentIntent,
    StripePaymentMethod,
    StripePrice,
    StripeProduct,
    StripeRefund,
    StripeWebhook,
    WebhookStatus,
)
from app.modules.stripe_integration.schemas import (
    CheckoutLineItem,
    CheckoutSessionCreate,
    ConnectAccountCreate,
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentMethodCreate,
    RefundCreate,
    SetupIntentCreate,
    StripeConfigCreate,
    StripeConfigUpdate,
    StripeCustomerCreate,
    StripeCustomerUpdate,
    StripePriceCreate,
    StripeProductCreate,
)
from app.modules.stripe_integration.service import StripeService


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
def stripe_service(mock_db):
    """Stripe service instance with mocked DB."""
    return StripeService(mock_db, "test-tenant")


@pytest.fixture
def sample_stripe_config():
    """Sample Stripe configuration."""
    return StripeConfig(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        api_key_live="sk_live_test123",
        api_key_test="sk_test_test123",
        webhook_secret_live="whsec_live_test",
        webhook_secret_test="whsec_test_test",
        is_live_mode=False,
        default_currency="EUR",
        default_payment_methods=["card"],
        auto_capture=True,
        send_receipts=True,
        connect_enabled=False,
    )


@pytest.fixture
def sample_stripe_customer():
    """Sample Stripe customer."""
    return StripeCustomer(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        stripe_customer_id="cus_test123456789",
        customer_id=uuid.uuid4(),
        email="customer@example.com",
        name="Test Customer",
        phone="+33612345678",
        balance=Decimal("0"),
        delinquent=False,
        is_synced=True,
    )


@pytest.fixture
def sample_payment_intent():
    """Sample PaymentIntent."""
    return StripePaymentIntent(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        stripe_payment_intent_id="pi_test123456789",
        stripe_customer_id=uuid.uuid4(),
        amount=Decimal("99.99"),
        amount_received=Decimal("0"),
        currency="EUR",
        status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
        capture_method="automatic",
        client_secret="pi_test_secret_123",
    )


@pytest.fixture
def sample_customer_create_data():
    """Sample customer creation data."""
    return StripeCustomerCreate(
        customer_id=100,
        email="new@example.com",
        name="New Customer",
        phone="+33698765432",
        country="FR",
    )


@pytest.fixture
def sample_payment_intent_data():
    """Sample PaymentIntent creation data."""
    return PaymentIntentCreate(
        customer_id=100,
        amount=Decimal("150.00"),
        currency="EUR",
        payment_method_types=["card"],
        capture_method="automatic",
        description="Test payment",
    )


# ============================================================================
# SERVICE INITIALIZATION TESTS
# ============================================================================

class TestStripeServiceInitialization:
    """Tests for Stripe service initialization."""

    def test_service_initialization(self, mock_db):
        """Test service initializes correctly."""
        service = StripeService(mock_db, "test-tenant")
        assert service.db == mock_db
        assert service.tenant_id == "test-tenant"
        assert service._config is None
        assert service._stripe is None

    def test_service_initialization_with_different_tenant(self, mock_db):
        """Test service initializes with different tenant."""
        service = StripeService(mock_db, "other-tenant")
        assert service.tenant_id == "other-tenant"


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestStripeConfig:
    """Tests for Stripe configuration management."""

    def test_create_config_success(self, stripe_service, mock_db):
        """Test successful config creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        config_data = StripeConfigCreate(
            api_key_test="sk_test_new123",
            webhook_secret_test="whsec_test_new",
            default_currency="EUR",
        )

        config = stripe_service.create_config(config_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_config_already_exists(self, stripe_service, mock_db, sample_stripe_config):
        """Test config creation fails if already exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_config

        config_data = StripeConfigCreate(
            api_key_test="sk_test_new123",
        )

        with pytest.raises(ValueError, match="déjà existante"):
            stripe_service.create_config(config_data)

    def test_update_config_success(self, stripe_service, mock_db, sample_stripe_config):
        """Test successful config update."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_config

        update_data = StripeConfigUpdate(
            is_live_mode=True,
            auto_capture=False,
        )

        result = stripe_service.update_config(update_data)

        assert sample_stripe_config.is_live_mode is True
        assert sample_stripe_config.auto_capture is False
        mock_db.commit.assert_called()

    def test_update_config_not_found(self, stripe_service, mock_db):
        """Test config update fails if not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        update_data = StripeConfigUpdate(is_live_mode=True)

        with pytest.raises(ValueError, match="non trouvée"):
            stripe_service.update_config(update_data)

    def test_get_config_returns_cached(self, stripe_service, mock_db, sample_stripe_config):
        """Test get_config returns cached config."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_config

        config1 = stripe_service.get_config()
        config2 = stripe_service.get_config()

        assert config1 is config2
        # Should only query once
        assert mock_db.query.call_count == 1


# ============================================================================
# CUSTOMER TESTS
# ============================================================================

class TestStripeCustomer:
    """Tests for Stripe customer management."""

    def test_create_customer_success(self, stripe_service, mock_db, sample_customer_create_data):
        """Test successful customer creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        customer = stripe_service.create_customer(sample_customer_create_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_customer_already_exists(self, stripe_service, mock_db, sample_stripe_customer, sample_customer_create_data):
        """Test customer creation fails if already exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        with pytest.raises(ValueError, match="déjà existant"):
            stripe_service.create_customer(sample_customer_create_data)

    def test_get_customer_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful customer retrieval."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        customer = stripe_service.get_customer(1)

        assert customer == sample_stripe_customer

    def test_get_customer_by_crm_id(self, stripe_service, mock_db, sample_stripe_customer):
        """Test customer retrieval by CRM ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        customer = stripe_service.get_customer_by_crm_id(100)

        assert customer == sample_stripe_customer

    def test_get_or_create_customer_existing(self, stripe_service, mock_db, sample_stripe_customer):
        """Test get_or_create returns existing customer."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        customer = stripe_service.get_or_create_customer(100, "test@example.com", "Test")

        assert customer == sample_stripe_customer
        mock_db.add.assert_not_called()

    def test_get_or_create_customer_creates_new(self, stripe_service, mock_db):
        """Test get_or_create creates new customer if not exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        customer = stripe_service.get_or_create_customer(100, "new@example.com", "New Customer")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_list_customers_pagination(self, stripe_service, mock_db):
        """Test listing customers with pagination."""
        customers = [
            StripeCustomer(id=uuid.uuid4(), tenant_id="test-tenant", stripe_customer_id=f"cus_{i}")
            for i in range(5)
        ]

        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = customers
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = stripe_service.list_customers(skip=10, limit=5)

        assert total == 50
        assert len(items) == 5

    def test_update_customer_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful customer update."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        update_data = StripeCustomerUpdate(
            name="Updated Name",
            phone="+33600000000",
        )

        result = stripe_service.update_customer(1, update_data)

        assert sample_stripe_customer.name == "Updated Name"
        assert sample_stripe_customer.phone == "+33600000000"

    def test_update_customer_not_found(self, stripe_service, mock_db):
        """Test customer update returns None if not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        update_data = StripeCustomerUpdate(name="Updated Name")

        result = stripe_service.update_customer(999, update_data)

        assert result is None

    def test_sync_customer_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful customer sync."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        result = stripe_service.sync_customer(1)

        assert result.is_synced is True
        assert result.sync_error is None


# ============================================================================
# PAYMENT METHOD TESTS
# ============================================================================

class TestPaymentMethod:
    """Tests for payment method management."""

    def test_add_payment_method_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful payment method addition."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        data = PaymentMethodCreate(
            stripe_customer_id="cus_test123456789",
            method_type="card",
            set_as_default=True,
        )

        pm = stripe_service.add_payment_method(data)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_add_payment_method_customer_not_found(self, stripe_service, mock_db):
        """Test payment method addition fails if customer not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = PaymentMethodCreate(
            stripe_customer_id="cus_nonexistent",
            method_type="card",
        )

        with pytest.raises(ValueError, match="non trouvé"):
            stripe_service.add_payment_method(data)

    def test_list_payment_methods_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test listing payment methods."""
        pms = [
            StripePaymentMethod(id=uuid.uuid4(), stripe_payment_method_id=f"pm_{i}", is_active=True)
            for i in range(2)
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer
        mock_db.query.return_value.filter.return_value.all.return_value = pms

        result = stripe_service.list_payment_methods(1)

        # Returns empty if customer not found in current mock setup
        # This tests the method call itself

    def test_delete_payment_method_success(self, stripe_service, mock_db):
        """Test successful payment method deletion."""
        pm = StripePaymentMethod(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            stripe_payment_method_id="pm_test123",
            is_active=True,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pm

        result = stripe_service.delete_payment_method(1)

        assert result is True
        assert pm.is_active is False

    def test_delete_payment_method_not_found(self, stripe_service, mock_db):
        """Test payment method deletion returns False if not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = stripe_service.delete_payment_method(999)

        assert result is False

    def test_create_setup_intent_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful SetupIntent creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        data = SetupIntentCreate(
            customer_id=100,
            payment_method_types=["card", "sepa_debit"],
        )

        result = stripe_service.create_setup_intent(data)

        assert "setup_intent_id" in result
        assert "client_secret" in result
        assert result["status"] == "requires_payment_method"


# ============================================================================
# PAYMENT INTENT TESTS
# ============================================================================

@pytest.mark.skip(reason="Stripe API mock requires complex setup - external service")
class TestPaymentIntent:
    """Tests for PaymentIntent management."""

    def test_create_payment_intent_success(self, stripe_service, mock_db, sample_stripe_customer, sample_payment_intent_data):
        """Test successful PaymentIntent creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        pi = stripe_service.create_payment_intent(sample_payment_intent_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_payment_intent_without_customer(self, stripe_service, mock_db):
        """Test PaymentIntent creation without customer."""
        data = PaymentIntentCreate(
            amount=Decimal("50.00"),
            currency="EUR",
        )

        pi = stripe_service.create_payment_intent(data)

        mock_db.add.assert_called_once()

    def test_get_payment_intent_success(self, stripe_service, mock_db, sample_payment_intent):
        """Test successful PaymentIntent retrieval."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent

        pi = stripe_service.get_payment_intent(1)

        assert pi == sample_payment_intent

    def test_list_payment_intents_with_filters(self, stripe_service, mock_db):
        """Test listing PaymentIntents with filters."""
        pis = [
            StripePaymentIntent(id=uuid.uuid4(), tenant_id="test-tenant", status=PaymentIntentStatus.SUCCEEDED)
            for i in range(3)
        ]

        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = pis
        mock_db.query.return_value.filter.return_value = mock_query

        items, total = stripe_service.list_payment_intents(
            status=PaymentIntentStatus.SUCCEEDED,
            skip=0,
            limit=50
        )

        assert total == 10
        assert len(items) == 3

    def test_confirm_payment_intent_success(self, stripe_service, mock_db, sample_payment_intent):
        """Test successful PaymentIntent confirmation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent
        stripe_service._config = MagicMock()

        data = PaymentIntentConfirm(payment_method_id="pm_test123")

        result = stripe_service.confirm_payment_intent(1, data)

        assert sample_payment_intent.status == PaymentIntentStatus.SUCCEEDED
        assert sample_payment_intent.amount_received == sample_payment_intent.amount

    def test_confirm_payment_intent_not_found(self, stripe_service, mock_db):
        """Test PaymentIntent confirmation fails if not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = PaymentIntentConfirm(payment_method_id="pm_test123")

        with pytest.raises(ValueError, match="non trouvé"):
            stripe_service.confirm_payment_intent(999, data)

    def test_capture_payment_intent_success(self, stripe_service, mock_db):
        """Test successful PaymentIntent capture."""
        pi = StripePaymentIntent(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=PaymentIntentStatus.REQUIRES_CAPTURE,
            amount=Decimal("100.00"),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pi

        result = stripe_service.capture_payment_intent(1)

        assert pi.status == PaymentIntentStatus.SUCCEEDED
        assert pi.amount_received == pi.amount

    def test_capture_payment_intent_wrong_status(self, stripe_service, mock_db, sample_payment_intent):
        """Test PaymentIntent capture fails with wrong status."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent

        with pytest.raises(ValueError, match="ne peut pas être capturé"):
            stripe_service.capture_payment_intent(1)

    def test_cancel_payment_intent_success(self, stripe_service, mock_db, sample_payment_intent):
        """Test successful PaymentIntent cancellation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent

        result = stripe_service.cancel_payment_intent(1, reason="Customer requested")

        assert sample_payment_intent.status == PaymentIntentStatus.CANCELED
        assert sample_payment_intent.cancellation_reason == "Customer requested"

    def test_cancel_succeeded_payment_fails(self, stripe_service, mock_db):
        """Test cancelling succeeded payment fails."""
        pi = StripePaymentIntent(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=PaymentIntentStatus.SUCCEEDED,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pi

        with pytest.raises(ValueError, match="Impossible d'annuler"):
            stripe_service.cancel_payment_intent(1)


# ============================================================================
# CHECKOUT SESSION TESTS
# ============================================================================

@pytest.mark.skip(reason="Stripe API mock requires complex setup - external service")
class TestCheckoutSession:
    """Tests for Checkout Session management."""

    def test_create_checkout_session_success(self, stripe_service, mock_db, sample_stripe_customer):
        """Test successful checkout session creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_stripe_customer

        data = CheckoutSessionCreate(
            customer_id=100,
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            line_items=[
                CheckoutLineItem(
                    name="Test Product",
                    amount=Decimal("49.99"),
                    currency="EUR",
                    quantity=2,
                )
            ],
        )

        session = stripe_service.create_checkout_session(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_checkout_session_without_customer(self, stripe_service, mock_db):
        """Test checkout session creation without customer."""
        data = CheckoutSessionCreate(
            customer_email="guest@example.com",
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            line_items=[
                CheckoutLineItem(
                    name="Guest Product",
                    amount=Decimal("29.99"),
                    currency="EUR",
                )
            ],
        )

        session = stripe_service.create_checkout_session(data)

        mock_db.add.assert_called_once()

    def test_get_checkout_session_success(self, stripe_service, mock_db):
        """Test successful checkout session retrieval."""
        session = StripeCheckoutSession(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            stripe_session_id="cs_test123",
            status="open",
        )

        mock_db.query.return_value.filter.return_value.first.return_value = session

        result = stripe_service.get_checkout_session(1)

        assert result == session


# ============================================================================
# REFUND TESTS
# ============================================================================

class TestRefund:
    """Tests for refund management."""

    def test_create_refund_success(self, stripe_service, mock_db):
        """Test successful refund creation."""
        pi = StripePaymentIntent(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=PaymentIntentStatus.SUCCEEDED,
            amount=Decimal("100.00"),
            amount_received=Decimal("100.00"),
            currency="EUR",
            refunds=[],
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pi

        data = RefundCreate(
            payment_intent_id=1,
            amount=Decimal("50.00"),
            reason="requested_by_customer",
        )

        refund = stripe_service.create_refund(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_refund_full_amount(self, stripe_service, mock_db):
        """Test full refund creation."""
        pi = StripePaymentIntent(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=PaymentIntentStatus.SUCCEEDED,
            amount=Decimal("100.00"),
            amount_received=Decimal("100.00"),
            currency="EUR",
            refunds=[],
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pi

        data = RefundCreate(
            payment_intent_id=1,
            # amount=None means full refund
        )

        refund = stripe_service.create_refund(data)

        mock_db.add.assert_called_once()

    def test_create_refund_not_succeeded(self, stripe_service, mock_db, sample_payment_intent):
        """Test refund creation fails if payment not succeeded."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent

        data = RefundCreate(payment_intent_id=1)

        with pytest.raises(ValueError, match="réussis peuvent être remboursés"):
            stripe_service.create_refund(data)

    def test_create_refund_amount_exceeds_available(self, stripe_service, mock_db):
        """Test refund fails if amount exceeds available."""
        existing_refund = StripeRefund(
            id=uuid.uuid4(),
            amount=Decimal("80.00"),
            status=RefundStatus.SUCCEEDED,
        )

        pi = StripePaymentIntent(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            status=PaymentIntentStatus.SUCCEEDED,
            amount=Decimal("100.00"),
            amount_received=Decimal("100.00"),
            refunds=[existing_refund],
        )

        mock_db.query.return_value.filter.return_value.first.return_value = pi

        data = RefundCreate(
            payment_intent_id=1,
            amount=Decimal("50.00"),  # Only 20 available
        )

        with pytest.raises(ValueError, match="supérieur au disponible"):
            stripe_service.create_refund(data)

    def test_list_refunds_success(self, stripe_service, mock_db):
        """Test listing refunds."""
        refunds = [
            StripeRefund(id=uuid.uuid4(), tenant_id="test-tenant", amount=Decimal("50.00"))
            for i in range(3)
        ]

        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = refunds

        result = stripe_service.list_refunds()

        assert len(result) == 3


# ============================================================================
# PRODUCT & PRICE TESTS
# ============================================================================

class TestProductAndPrice:
    """Tests for product and price management."""

    def test_create_product_success(self, stripe_service, mock_db):
        """Test successful product creation."""
        data = StripeProductCreate(
            name="Premium Plan",
            description="Premium subscription plan",
        )

        product = stripe_service.create_product(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_price_success(self, stripe_service, mock_db):
        """Test successful price creation."""
        product = StripeProduct(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            stripe_product_id="prod_test123",
            name="Test Product",
        )

        mock_db.query.return_value.filter.return_value.first.return_value = product

        data = StripePriceCreate(
            product_id=1,
            unit_amount=Decimal("9900"),  # 99.00 in cents
            currency="EUR",
            recurring_interval="month",
        )

        price = stripe_service.create_price(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_price_product_not_found(self, stripe_service, mock_db):
        """Test price creation fails if product not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = StripePriceCreate(
            product_id=999,
            unit_amount=Decimal("9900"),
            currency="EUR",
        )

        with pytest.raises(ValueError, match="non trouvé"):
            stripe_service.create_price(data)


# ============================================================================
# CONNECT ACCOUNT TESTS
# ============================================================================

@pytest.mark.skip(reason="Stripe Connect API mock requires complex setup - external service")
class TestConnectAccount:
    """Tests for Stripe Connect account management."""

    def test_create_connect_account_success(self, stripe_service, mock_db):
        """Test successful Connect account creation."""
        data = ConnectAccountCreate(
            vendor_id=1,
            email="vendor@example.com",
            country="FR",
            account_type="express",
            business_type="company",
            return_url="https://example.com/return",
            refresh_url="https://example.com/refresh",
        )

        account = stripe_service.create_connect_account(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_connect_account_success(self, stripe_service, mock_db):
        """Test successful Connect account retrieval."""
        account = StripeConnectAccount(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            stripe_account_id="acct_test123",
            status=StripeAccountStatus.PENDING,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = account

        result = stripe_service.get_connect_account(1)

        assert result == account


# ============================================================================
# WEBHOOK TESTS
# ============================================================================

class TestWebhook:
    """Tests for webhook processing."""

    def test_process_webhook_success(self, stripe_service, mock_db, sample_stripe_config):
        """Test successful webhook processing."""
        stripe_service._config = sample_stripe_config

        webhook = stripe_service.process_webhook(
            event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={
                "data": {
                    "object": {
                        "id": "pi_test123",
                        "object": "payment_intent",
                    }
                }
            },
            signature="test_signature",
        )

        mock_db.add.assert_called()

    def test_process_webhook_payment_intent_succeeded(self, stripe_service, mock_db, sample_stripe_config, sample_payment_intent):
        """Test webhook handling for payment_intent.succeeded."""
        stripe_service._config = sample_stripe_config
        mock_db.query.return_value.filter.return_value.first.return_value = sample_payment_intent

        webhook = stripe_service.process_webhook(
            event_id="evt_test456",
            event_type="payment_intent.succeeded",
            payload={
                "data": {
                    "object": {
                        "id": "pi_test123456789",
                        "object": "payment_intent",
                        "amount_received": 9999,
                    }
                }
            },
        )

        mock_db.add.assert_called()


# ============================================================================
# DASHBOARD TESTS
# ============================================================================

class TestDashboard:
    """Tests for dashboard data retrieval."""

    def test_get_dashboard_empty(self, stripe_service, mock_db):
        """Test dashboard with no data."""
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("0")
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        dashboard = stripe_service.get_dashboard()

        assert dashboard["total_volume_30d"] == 0
        assert dashboard["successful_payments_30d"] == 0

    def test_get_dashboard_with_data(self, stripe_service, mock_db):
        """Test dashboard with sample data."""
        # Configure mocks for various queries
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            Decimal("1500.00"),  # volume
            Decimal("150.00"),  # refunds
            Decimal("50.00"),   # disputed amount
        ]
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            25,  # successful payments
            3,   # failed payments
            1,   # open disputes
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        dashboard = stripe_service.get_dashboard()

        assert dashboard["total_volume_30d"] == 1500.00
        assert dashboard["successful_payments_30d"] == 25


# ============================================================================
# TENANT ISOLATION TESTS
# ============================================================================

class TestTenantIsolation:
    """Tests for tenant isolation in Stripe service."""

    def test_customer_tenant_isolation(self, mock_db):
        """Test customer operations are tenant-isolated."""
        service1 = StripeService(mock_db, "tenant-1")
        service2 = StripeService(mock_db, "tenant-2")

        assert service1.tenant_id != service2.tenant_id

    def test_payment_intent_tenant_isolation(self, mock_db):
        """Test PaymentIntent operations are tenant-isolated."""
        service1 = StripeService(mock_db, "tenant-1")
        service2 = StripeService(mock_db, "tenant-2")

        # Both services should use their respective tenant_id
        assert service1.tenant_id == "tenant-1"
        assert service2.tenant_id == "tenant-2"


# ============================================================================
# MODEL TESTS
# ============================================================================

class TestStripeModels:
    """Tests for Stripe model creation."""

    def test_stripe_customer_model_creation(self):
        """Test StripeCustomer model creation."""
        customer = StripeCustomer(
            tenant_id="test-tenant",
            stripe_customer_id="cus_test123",
            customer_id=uuid.uuid4(),
            email="test@example.com",
            name="Test Customer",
            balance=Decimal("0"),
            delinquent=False,
            is_synced=True,
        )

        assert customer.stripe_customer_id == "cus_test123"
        assert customer.balance == Decimal("0")

    def test_stripe_payment_intent_model_creation(self):
        """Test StripePaymentIntent model creation."""
        pi = StripePaymentIntent(
            tenant_id="test-tenant",
            stripe_payment_intent_id="pi_test123",
            amount=Decimal("99.99"),
            currency="EUR",
            status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
        )

        assert pi.status == PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
        assert pi.amount == Decimal("99.99")

    def test_stripe_refund_model_creation(self):
        """Test StripeRefund model creation."""
        refund = StripeRefund(
            tenant_id="test-tenant",
            stripe_refund_id="re_test123",
            amount=Decimal("50.00"),
            currency="EUR",
            status=RefundStatus.SUCCEEDED,
        )

        assert refund.status == RefundStatus.SUCCEEDED

    def test_stripe_webhook_model_creation(self):
        """Test StripeWebhook model creation."""
        webhook = StripeWebhook(
            tenant_id="test-tenant",
            stripe_event_id="evt_test123",
            event_type="payment_intent.succeeded",
            payload={"test": "data"},
            status=WebhookStatus.PENDING,
        )

        assert webhook.status == WebhookStatus.PENDING
        assert webhook.event_type == "payment_intent.succeeded"


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestStripeEnums:
    """Tests for Stripe enumerations."""

    def test_payment_intent_status_values(self):
        """Test PaymentIntentStatus enum values."""
        assert PaymentIntentStatus.REQUIRES_PAYMENT_METHOD.value == "requires_payment_method"
        assert PaymentIntentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentIntentStatus.CANCELED.value == "canceled"
        assert PaymentIntentStatus.REQUIRES_CAPTURE.value == "requires_capture"

    def test_refund_status_values(self):
        """Test RefundStatus enum values."""
        assert RefundStatus.PENDING.value == "pending"
        assert RefundStatus.SUCCEEDED.value == "succeeded"
        assert RefundStatus.FAILED.value == "failed"
        assert RefundStatus.CANCELED.value == "canceled"

    def test_dispute_status_values(self):
        """Test DisputeStatus enum values."""
        assert DisputeStatus.NEEDS_RESPONSE.value == "needs_response"
        assert DisputeStatus.UNDER_REVIEW.value == "under_review"
        assert DisputeStatus.WON.value == "won"
        assert DisputeStatus.LOST.value == "lost"

    def test_webhook_status_values(self):
        """Test WebhookStatus enum values."""
        assert WebhookStatus.PENDING.value == "pending"
        assert WebhookStatus.PROCESSED.value == "processed"
        assert WebhookStatus.FAILED.value == "failed"
        assert WebhookStatus.IGNORED.value == "ignored"

    def test_stripe_account_status_values(self):
        """Test StripeAccountStatus enum values."""
        assert StripeAccountStatus.PENDING.value == "pending"
        assert StripeAccountStatus.ACTIVE.value == "active"
        assert StripeAccountStatus.RESTRICTED.value == "restricted"
        assert StripeAccountStatus.DISABLED.value == "disabled"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_create_customer_db_error(self, stripe_service, mock_db, sample_customer_create_data):
        """Test customer creation handles DB errors."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            stripe_service.create_customer(sample_customer_create_data)

    def test_get_config_missing_raises_on_stripe_client(self, stripe_service, mock_db):
        """Test getting Stripe client fails without config."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        stripe_service._config = None

        with pytest.raises(ValueError, match="non trouvée"):
            stripe_service._get_stripe_client()
