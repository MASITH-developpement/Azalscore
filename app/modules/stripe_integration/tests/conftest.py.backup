"""Configuration pytest et fixtures pour les tests Stripe Integration."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.stripe_integration.models import PaymentIntentStatus, RefundStatus


@pytest.fixture
def mock_stripe_service(monkeypatch):
    """Mock du service Stripe."""

    class MockStripeService:
        def __init__(self, db, tenant_id, user_id=None):
            self.db = db
            self.tenant_id = tenant_id
            self.user_id = user_id

        # Config
        def create_config(self, data):
            class MockConfig:
                id = 1
                tenant_id = self.tenant_id
                api_key_test = data.api_key_test
                api_key_live = data.api_key_live
                is_live_mode = data.is_live_mode
                webhook_secret = data.webhook_secret
                created_at = datetime.utcnow()
                updated_at = datetime.utcnow()
            return MockConfig()

        def get_config(self):
            class MockConfig:
                id = 1
                tenant_id = self.tenant_id
                api_key_test = "sk_test_xxx"
                is_live_mode = False
            return MockConfig()

        def update_config(self, data):
            class MockConfig:
                id = 1
                tenant_id = self.tenant_id
                is_live_mode = data.is_live_mode if hasattr(data, 'is_live_mode') else False
                updated_at = datetime.utcnow()
            return MockConfig()

        # Customers
        def create_customer(self, data):
            class MockCustomer:
                id = 1
                tenant_id = self.tenant_id
                stripe_customer_id = "cus_test123"
                email = data.email
                name = data.name
                crm_customer_id = data.crm_customer_id if hasattr(data, 'crm_customer_id') else None
                created_at = datetime.utcnow()
            return MockCustomer()

        def list_customers(self, skip, limit):
            class MockCustomer:
                id = 1
                tenant_id = self.tenant_id
                stripe_customer_id = "cus_test123"
                email = "test@example.com"
                name = "Test Customer"
            return [MockCustomer()]

        def get_customer(self, customer_id):
            if customer_id == 999:
                return None
            class MockCustomer:
                id = customer_id
                tenant_id = self.tenant_id
                stripe_customer_id = "cus_test123"
                email = "test@example.com"
            return MockCustomer()

        def get_customer_by_crm_id(self, crm_customer_id):
            if crm_customer_id == 999:
                return None
            class MockCustomer:
                id = 1
                tenant_id = self.tenant_id
                stripe_customer_id = "cus_test123"
                crm_customer_id = crm_customer_id
            return MockCustomer()

        def update_customer(self, customer_id, data):
            if customer_id == 999:
                raise ValueError("Customer not found")
            class MockCustomer:
                id = customer_id
                email = data.email if hasattr(data, 'email') else "test@example.com"
                name = data.name if hasattr(data, 'name') else "Test Customer"
            return MockCustomer()

        def sync_customer(self, customer_id):
            if customer_id == 999:
                raise ValueError("Customer not found")
            class MockCustomer:
                id = customer_id
                stripe_customer_id = "cus_test123"
                updated_at = datetime.utcnow()
            return MockCustomer()

        # Payment Methods
        def add_payment_method(self, data):
            class MockPaymentMethod:
                id = 1
                tenant_id = self.tenant_id
                stripe_payment_method_id = "pm_test123"
                customer_id = data.customer_id
                type = "card"
                card_brand = "visa"
                card_last4 = "4242"
                is_default = data.is_default if hasattr(data, 'is_default') else False
            return MockPaymentMethod()

        def list_payment_methods(self, customer_id):
            class MockPaymentMethod:
                id = 1
                stripe_payment_method_id = "pm_test123"
                type = "card"
                card_brand = "visa"
                card_last4 = "4242"
            return [MockPaymentMethod()]

        def delete_payment_method(self, payment_method_id):
            return payment_method_id != 999

        # Setup Intent
        def create_setup_intent(self, data):
            return {
                "id": "seti_test123",
                "client_secret": "seti_test123_secret_xyz",
                "status": "requires_payment_method"
            }

        # Payment Intents
        def create_payment_intent(self, data):
            class MockPaymentIntent:
                id = 1
                tenant_id = self.tenant_id
                stripe_payment_intent_id = "pi_test123"
                amount = data.amount
                currency = data.currency
                customer_id = data.customer_id if hasattr(data, 'customer_id') else None
                status = PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
                client_secret = "pi_test123_secret_xyz"
                created_at = datetime.utcnow()
            return MockPaymentIntent()

        def list_payment_intents(self, customer_id, status, skip, limit):
            class MockPaymentIntent:
                id = 1
                stripe_payment_intent_id = "pi_test123"
                amount = 1000
                currency = "eur"
                status = PaymentIntentStatus.SUCCEEDED
            return [MockPaymentIntent()]

        def get_payment_intent(self, payment_intent_id):
            if payment_intent_id == 999:
                return None
            class MockPaymentIntent:
                id = payment_intent_id
                stripe_payment_intent_id = "pi_test123"
                amount = 1000
                status = PaymentIntentStatus.SUCCEEDED
            return MockPaymentIntent()

        def confirm_payment_intent(self, payment_intent_id, data):
            if payment_intent_id == 999:
                raise ValueError("Payment Intent not found")
            class MockPaymentIntent:
                id = payment_intent_id
                status = PaymentIntentStatus.SUCCEEDED
            return MockPaymentIntent()

        def capture_payment_intent(self, payment_intent_id, amount):
            if payment_intent_id == 999:
                raise ValueError("Payment Intent not found")
            class MockPaymentIntent:
                id = payment_intent_id
                status = PaymentIntentStatus.SUCCEEDED
            return MockPaymentIntent()

        def cancel_payment_intent(self, payment_intent_id):
            if payment_intent_id == 999:
                raise ValueError("Payment Intent not found")
            class MockPaymentIntent:
                id = payment_intent_id
                status = PaymentIntentStatus.CANCELED
            return MockPaymentIntent()

        # Checkout Sessions
        def create_checkout_session(self, data):
            class MockSession:
                id = 1
                tenant_id = self.tenant_id
                stripe_session_id = "cs_test123"
                customer_id = data.customer_id if hasattr(data, 'customer_id') else None
                success_url = data.success_url
                cancel_url = data.cancel_url
                payment_status = "unpaid"
                url = "https://checkout.stripe.com/pay/cs_test123"
                created_at = datetime.utcnow()
            return MockSession()

        def get_checkout_session(self, session_id):
            class MockSession:
                id = 1
                stripe_session_id = session_id
                payment_status = "paid"
            return MockSession()

        # Refunds
        def create_refund(self, data):
            class MockRefund:
                id = 1
                tenant_id = self.tenant_id
                stripe_refund_id = "re_test123"
                payment_intent_id = data.payment_intent_id
                amount = data.amount if hasattr(data, 'amount') else None
                reason = data.reason if hasattr(data, 'reason') else None
                status = RefundStatus.SUCCEEDED
                created_at = datetime.utcnow()
            return MockRefund()

        def list_refunds(self, payment_intent_id, skip, limit):
            class MockRefund:
                id = 1
                stripe_refund_id = "re_test123"
                amount = 1000
                status = RefundStatus.SUCCEEDED
            return [MockRefund()]

        # Products & Prices
        def create_product(self, data):
            class MockProduct:
                id = 1
                tenant_id = self.tenant_id
                stripe_product_id = "prod_test123"
                name = data.name
                description = data.description
                active = data.active if hasattr(data, 'active') else True
                created_at = datetime.utcnow()
            return MockProduct()

        def create_price(self, data):
            class MockPrice:
                id = 1
                tenant_id = self.tenant_id
                stripe_price_id = "price_test123"
                product_id = data.product_id
                unit_amount = data.unit_amount
                currency = data.currency
                recurring_interval = data.recurring_interval if hasattr(data, 'recurring_interval') else None
                active = True
                created_at = datetime.utcnow()
            return MockPrice()

        # Connect
        def create_connect_account(self, data):
            class MockAccount:
                id = 1
                tenant_id = self.tenant_id
                stripe_account_id = "acct_test123"
                email = data.email
                country = data.country
                type = data.account_type if hasattr(data, 'account_type') else "standard"
                charges_enabled = False
                payouts_enabled = False
                created_at = datetime.utcnow()
            return MockAccount()

        def get_connect_account(self, account_id):
            class MockAccount:
                id = 1
                stripe_account_id = account_id
                charges_enabled = True
                payouts_enabled = True
            return MockAccount()

        # Webhooks
        def process_webhook(self, event_id, event_type, event, signature):
            class MockWebhook:
                id = 1
                stripe_event_id = event_id
                event_type = event_type
            return MockWebhook()

    from app.modules.stripe_integration import router_v2

    def mock_get_service(db, tenant_id, user_id):
        return MockStripeService(db, tenant_id, user_id)

    monkeypatch.setattr(router_v2, "get_stripe_service", mock_get_service)
    # Also patch StripeService for webhook endpoint (which doesn't use factory)
    monkeypatch.setattr("app.modules.stripe_integration.router_v2.StripeService", MockStripeService)
    return MockStripeService(None, "test-tenant", "1")


@pytest.fixture
def sample_config_data():
    return {
        "api_key_test": "sk_test_xxx",
        "api_key_live": "sk_live_xxx",
        "webhook_secret": "whsec_test_xxx",
        "is_live_mode": False
    }


@pytest.fixture
def sample_customer_data():
    return {
        "email": "customer@example.com",
        "name": "John Doe",
        "phone": "+33612345678"
    }


@pytest.fixture
def sample_payment_intent_data():
    return {
        "amount": 1000,
        "currency": "eur",
        "description": "Test payment"
    }
