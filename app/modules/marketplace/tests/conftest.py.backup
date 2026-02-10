"""Configuration pytest et fixtures pour les tests Marketplace."""

import pytest
from decimal import Decimal
from datetime import datetime

from app.modules.marketplace.models import OrderStatus, BillingCycle, PaymentMethod, PlanType
from app.modules.marketplace.schemas import DiscountCodeResponse, TenantProvisionResponse, MarketplaceStats


@pytest.fixture
def mock_marketplace_service(monkeypatch):
    """Mock du service Marketplace."""

    class MockMarketplaceService:
        def __init__(self, db, user_id=None):
            self.db = db
            self.user_id = user_id

        # Plans
        def get_plans(self, active_only=True):
            return [
                {
                    "id": "1",
                    "code": "essentiel",
                    "name": "Essentiel",
                    "price_monthly": Decimal("49.00"),
                    "price_annual": Decimal("490.00"),
                    "is_active": True
                },
                {
                    "id": "2",
                    "code": "pro",
                    "name": "Pro",
                    "price_monthly": Decimal("149.00"),
                    "price_annual": Decimal("1490.00"),
                    "is_active": True,
                    "is_featured": True
                }
            ]

        def get_plan(self, plan_id):
            return {
                "id": plan_id,
                "code": "pro",
                "name": "Pro",
                "price_monthly": Decimal("149.00")
            }

        def get_plan_by_code(self, code):
            if code == "pro":
                return {
                    "id": "2",
                    "code": "pro",
                    "name": "Pro",
                    "price_monthly": Decimal("149.00"),
                    "price_annual": Decimal("1490.00")
                }
            return None

        def seed_default_plans(self):
            pass

        # Checkout
        def create_checkout(self, data):
            from app.modules.marketplace.schemas import CheckoutResponse
            return CheckoutResponse(
                order_id="order-123",
                order_number="CMD-20240101-ABCD",
                status=OrderStatus.PAYMENT_PENDING,
                subtotal=Decimal("149.00"),
                tax_amount=Decimal("29.80"),
                discount_amount=Decimal("0.00"),
                total=Decimal("178.80"),
                currency="EUR",
                payment_intent_client_secret="pi_secret_xyz" if data.payment_method == PaymentMethod.CARD else None,
                checkout_url=None,
                instructions=None
            )

        # Discount Codes
        def validate_discount_code(self, code, plan_code, order_amount):
            if code.upper() == "PROMO20":
                return DiscountCodeResponse(
                    code=code,
                    valid=True,
                    discount_type="percent",
                    discount_value=Decimal("20"),
                    final_discount=Decimal("29.80"),
                    message="Réduction de 29.80€ appliquée"
                )
            return DiscountCodeResponse(
                code=code,
                valid=False,
                message="Code promo invalide"
            )

        # Orders
        def list_orders(self, status=None, skip=0, limit=50):
            orders = [
                {
                    "id": "order-1",
                    "order_number": "CMD-20240101-AAAA",
                    "status": OrderStatus.COMPLETED
                },
                {
                    "id": "order-2",
                    "order_number": "CMD-20240102-BBBB",
                    "status": OrderStatus.PAYMENT_PENDING
                }
            ]
            return orders, len(orders)

        def get_order(self, order_id):
            return {
                "id": order_id,
                "order_number": "CMD-20240101-ABCD",
                "status": OrderStatus.PAID,
                "total": Decimal("178.80")
            }

        def get_order_by_number(self, order_number):
            if order_number == "CMD-20240101-ABCD":
                return {
                    "id": "order-123",
                    "order_number": order_number,
                    "status": OrderStatus.PAID
                }
            return None

        # Provisioning
        def provision_tenant_for_order(self, order_id):
            if order_id == "invalid":
                raise ValueError("Commande non trouvée")
            return TenantProvisionResponse(
                tenant_id="company-abc123",
                admin_email="admin@example.com",
                login_url="https://app.azalscore.com/login?tenant=company-abc123",
                temporary_password="TempPass123!",
                welcome_email_sent=True
            )

        # Webhooks
        def process_stripe_webhook(self, event_id, event_type, payload, signature):
            class WebhookResult:
                id = "webhook-123"
            return WebhookResult()

        # Statistics
        def get_stats(self):
            return MarketplaceStats(
                total_orders=150,
                total_revenue=Decimal("25000.00"),
                orders_today=5,
                revenue_today=Decimal("750.00"),
                orders_month=45,
                revenue_month=Decimal("8000.00"),
                conversion_rate=75.5,
                avg_order_value=Decimal("166.67"),
                by_plan={"essentiel": 50, "pro": 80, "entreprise": 20},
                by_billing_cycle={"monthly": 100, "annual": 50}
            )

    from app.modules.marketplace import router_v2

    def mock_get_service(db, user_id=None):
        return MockMarketplaceService(db, user_id)

    monkeypatch.setattr(router_v2, "get_marketplace_service", mock_get_service)
    return MockMarketplaceService(None)


@pytest.fixture
def sample_checkout_data():
    return {
        "plan_code": "pro",
        "billing_cycle": "monthly",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "company_name": "Acme Corp",
        "company_siret": "12345678901234",
        "phone": "+33612345678",
        "billing_address_line1": "123 Rue Example",
        "billing_city": "Paris",
        "billing_postal_code": "75001",
        "billing_country": "FR",
        "payment_method": "card"
    }
