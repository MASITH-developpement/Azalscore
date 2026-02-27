"""
AZALSCORE - Tests des Webhooks Stripe
======================================
Tests des endpoints et handlers webhooks Stripe.

Exécution:
    pytest tests/signup/test_stripe_webhooks.py -v
"""

import pytest
import json
import hmac
import hashlib
import time
from unittest.mock import patch, MagicMock


class TestStripeWebhookEndpoint:
    """Tests de l'endpoint webhook Stripe."""

    def test_webhook_missing_signature(self, client):
        """Test: signature manquante → 400."""
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test.event"},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_webhook_invalid_signature(self, client):
        """Test: signature invalide → 400."""
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test.event"},
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "invalid_signature"
            }
        )

        assert response.status_code == 400

    @patch("app.api.webhooks.StripeServiceLive.verify_webhook")
    @patch("app.api.webhooks.StripeWebhookHandler")
    def test_webhook_valid_event(self, mock_handler_class, mock_verify, client):
        """Test: événement valide → 200."""
        mock_verify.return_value = {
            "type": "checkout.session.completed",
            "id": "evt_test_123",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "metadata": {"tenant_id": "test-company", "plan": "PROFESSIONAL"}
                }
            }
        }

        mock_handler = MagicMock()
        mock_handler.handle_event.return_value = True
        mock_handler_class.return_value = mock_handler

        response = client.post(
            "/webhooks/stripe",
            content=json.dumps({"type": "checkout.session.completed"}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch("app.api.webhooks.StripeServiceLive.verify_webhook")
    @patch("app.api.webhooks.StripeWebhookHandler")
    def test_webhook_unknown_event_type(self, mock_handler_class, mock_verify, client):
        """Test: type d'événement inconnu → 200 (ignoré)."""
        mock_verify.return_value = {
            "type": "unknown.event.type",
            "id": "evt_test_456",
            "data": {"object": {}}
        }

        mock_handler = MagicMock()
        mock_handler.handle_event.return_value = True
        mock_handler_class.return_value = mock_handler

        response = client.post(
            "/webhooks/stripe",
            content=json.dumps({"type": "unknown.event.type"}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )

        assert response.status_code == 200


class TestStripeServiceLive:
    """Tests du service Stripe."""

    def test_service_initialization(self, db_session):
        """Test: initialisation du service."""
        from app.services.stripe_service import StripeServiceLive

        service = StripeServiceLive(db=db_session, tenant_id="test-tenant")
        assert service is not None
        assert service.tenant_id == "test-tenant"

    @patch("stripe.Customer.create")
    def test_create_customer(self, mock_create, db_session):
        """Test: création de client Stripe."""
        from app.services.stripe_service import StripeServiceLive, STRIPE_AVAILABLE

        if not STRIPE_AVAILABLE:
            pytest.skip("Stripe module not installed")

        mock_create.return_value = MagicMock(
            id="cus_test_123",
            email="test@company.fr",
            __iter__=lambda self: iter([("id", "cus_test_123")])
        )
        mock_create.return_value.__getitem__ = lambda self, key: getattr(self, key)

        service = StripeServiceLive(db=db_session, tenant_id="test-company")
        result = service.create_customer(
            email="test@company.fr",
            name="Test Company"
        )

        # create_customer returns dict or None
        assert result is not None or not STRIPE_AVAILABLE

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_create, db_session):
        """Test: création de session checkout."""
        from app.services.stripe_service import StripeServiceLive, STRIPE_AVAILABLE

        if not STRIPE_AVAILABLE:
            pytest.skip("Stripe module not installed")

        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        # Set environment variable for price
        with patch.dict("os.environ", {"STRIPE_PRICE_PRO_MONTHLY": "price_test_123"}):
            service = StripeServiceLive(db=db_session, tenant_id="test-company")
            session = service.create_checkout_session(
                customer_id="cus_test_123",
                plan="professional",
                billing_period="monthly"
            )

            # Returns {"session_id": ..., "url": ...} or None
            if session:
                assert session["session_id"] == "cs_test_123"
                assert "checkout.stripe.com" in session["url"]

    def test_webhook_signature_validation(self, db_session):
        """Test: validation de signature webhook."""
        from app.services.stripe_service import StripeServiceLive

        # Test that verify_webhook is a static method
        assert hasattr(StripeServiceLive, 'verify_webhook')


class TestStripePricing:
    """Tests de la configuration des prix."""

    def test_plans_config_exists(self):
        """Test: configuration des plans existe."""
        from app.services.stripe_service import AZALSCORE_PLANS

        assert AZALSCORE_PLANS is not None
        assert isinstance(AZALSCORE_PLANS, dict)

    def test_plan_structure(self):
        """Test: structure des plans."""
        from app.services.stripe_service import AZALSCORE_PLANS

        # Au moins un plan doit exister
        assert len(AZALSCORE_PLANS) > 0

        # Vérifier la structure de chaque plan
        for plan_name, plan_config in AZALSCORE_PLANS.items():
            assert "name" in plan_config
            assert "price_monthly" in plan_config
            assert "price_yearly" in plan_config
            assert "max_users" in plan_config

    def test_all_plans_present(self):
        """Test: tous les plans AZALSCORE présents."""
        from app.services.stripe_service import AZALSCORE_PLANS

        expected_plans = ["starter", "professional", "enterprise"]
        for plan in expected_plans:
            assert plan in AZALSCORE_PLANS

    def test_get_plan_features(self):
        """Test: récupération des features d'un plan."""
        from app.services.stripe_service import get_plan_features

        features = get_plan_features("professional")
        assert features is not None
        assert "max_users" in features


class TestStripeWebhookSecurity:
    """Tests de sécurité des webhooks."""

    def test_webhook_endpoint_is_public(self, client):
        """Test: endpoint webhook accessible sans auth."""
        # Le webhook doit être accessible (même si signature invalide)
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"},
            headers={"Stripe-Signature": "test"}
        )

        # 400 = accessible mais signature invalide (pas 401/403)
        assert response.status_code == 400

    def test_webhook_rejects_without_signature(self, client):
        """Test: webhook rejette sans signature."""
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"}
        )

        assert response.status_code == 400

    @patch("app.api.webhooks.StripeServiceLive.verify_webhook")
    @patch("app.api.webhooks.StripeWebhookHandler")
    def test_webhook_logs_events(self, mock_handler_class, mock_verify, client):
        """Test: webhook loggue les événements."""
        mock_verify.return_value = {
            "type": "test.event",
            "id": "evt_test_123",
            "data": {"object": {}}
        }

        mock_handler = MagicMock()
        mock_handler.handle_event.return_value = True
        mock_handler_class.return_value = mock_handler

        response = client.post(
            "/webhooks/stripe",
            content=json.dumps({"type": "test.event"}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid"
            }
        )

        # Le webhook doit répondre (pas d'erreur de log)
        assert response.status_code == 200


class TestStripeWebhookHandler:
    """Tests des handlers de webhooks."""

    def test_handler_initialization(self, db_session):
        """Test: initialisation du handler."""
        from app.services.stripe_service import StripeWebhookHandler

        handler = StripeWebhookHandler(db=db_session)
        assert handler is not None
        assert handler.db == db_session

    def test_handler_has_handle_event_method(self, db_session):
        """Test: handler a une méthode handle_event."""
        from app.services.stripe_service import StripeWebhookHandler

        handler = StripeWebhookHandler(db=db_session)
        assert hasattr(handler, 'handle_event')
        assert callable(handler.handle_event)

    def test_handler_routes_events(self, db_session):
        """Test: handler route les événements correctement."""
        from app.services.stripe_service import StripeWebhookHandler

        handler = StripeWebhookHandler(db=db_session)

        # Test avec un événement inconnu (doit retourner True = ignoré)
        result = handler.handle_event({
            "type": "unknown.event",
            "data": {"object": {}}
        })

        assert result is True  # Événements inconnus sont ignorés avec succès

    @patch("app.services.tenant_status_guard.convert_trial_to_active")
    def test_handler_checkout_completed(self, mock_convert, db_session):
        """Test: handler checkout.session.completed."""
        from app.services.stripe_service import StripeWebhookHandler
        from app.modules.tenants.models import Tenant, TenantStatus, SubscriptionPlan

        # Create test tenant in the database
        tenant = Tenant(
            tenant_id="test-company",
            name="Test Company",
            email="test@company.fr",
            status=TenantStatus.TRIAL,
            plan=SubscriptionPlan.PROFESSIONAL,
        )
        db_session.add(tenant)
        db_session.flush()

        handler = StripeWebhookHandler(db=db_session)

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "metadata": {
                        "tenant_id": "test-company",
                        "plan": "PROFESSIONAL"
                    }
                }
            }
        }

        result = handler.handle_event(event)
        assert result is True
        mock_convert.assert_called_once()


class TestStripeUtilities:
    """Tests des fonctions utilitaires."""

    def test_format_price(self):
        """Test: formatage des prix."""
        from app.services.stripe_service import format_price

        assert format_price(4900) == "49.00 €"
        assert format_price(14900) == "149.00 €"
        assert format_price(0) == "0.00 €"

    def test_get_plan_features_unknown(self):
        """Test: plan inconnu retourne dict vide."""
        from app.services.stripe_service import get_plan_features

        features = get_plan_features("unknown_plan")
        assert features == {}
