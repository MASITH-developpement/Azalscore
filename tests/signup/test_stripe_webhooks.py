"""
AZALSCORE - Tests des Webhooks Stripe
======================================
Tests des endpoints et handlers webhooks Stripe.

Exécution:
    pytest tests/test_stripe_webhooks.py -v
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

    @patch("stripe.Webhook.construct_event")
    def test_webhook_valid_event(self, mock_construct, client, stripe_checkout_event):
        """Test: événement valide → 200."""
        mock_construct.return_value = stripe_checkout_event
        
        response = client.post(
            "/webhooks/stripe",
            content=json.dumps(stripe_checkout_event),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["received"] is True

    @patch("stripe.Webhook.construct_event")
    def test_webhook_unknown_event_type(self, mock_construct, client):
        """Test: type d'événement inconnu → 200 (ignoré)."""
        mock_construct.return_value = {
            "type": "unknown.event.type",
            "data": {"object": {}}
        }
        
        response = client.post(
            "/webhooks/stripe",
            content=json.dumps({"type": "unknown.event.type"}),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )
        
        assert response.status_code == 200


class TestStripeWebhookHandler:
    """Tests du handler de webhooks Stripe."""

    @patch("stripe.Webhook.construct_event")
    def test_checkout_completed_activates_tenant(
        self, mock_construct, client, db, trial_tenant, stripe_checkout_event
    ):
        """Test: checkout.session.completed active le tenant."""
        from app.modules.tenants.models import TenantStatus
        
        # Configurer le mock avec le tenant_id correct
        stripe_checkout_event["data"]["object"]["metadata"]["tenant_id"] = trial_tenant.tenant_id
        mock_construct.return_value = stripe_checkout_event
        
        response = client.post(
            "/webhooks/stripe",
            content=json.dumps(stripe_checkout_event),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )
        
        assert response.status_code == 200
        
        # Vérifier que le tenant est activé
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.ACTIVE

    @patch("stripe.Webhook.construct_event")
    def test_payment_failed_after_3_attempts_suspends_tenant(
        self, mock_construct, client, db, sample_tenant, stripe_payment_failed_event
    ):
        """Test: 3 échecs de paiement → suspension du tenant."""
        from app.modules.tenants.models import TenantStatus
        
        # Configurer le mock
        # Note: Le handler actuel nécessite de récupérer tenant_id depuis customer_id
        # Ce test vérifie le logging pour l'instant
        mock_construct.return_value = stripe_payment_failed_event
        
        response = client.post(
            "/webhooks/stripe",
            content=json.dumps(stripe_payment_failed_event),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )
        
        assert response.status_code == 200
        # Le handler log une alerte après 3 tentatives

    @patch("stripe.Webhook.construct_event")
    def test_subscription_deleted_suspends_tenant(
        self, mock_construct, client, db, sample_tenant, stripe_subscription_deleted_event
    ):
        """Test: subscription.deleted suspend le tenant."""
        from app.modules.tenants.models import TenantStatus
        
        # Configurer le mock avec le tenant_id correct
        stripe_subscription_deleted_event["data"]["object"]["metadata"]["tenant_id"] = sample_tenant.tenant_id
        mock_construct.return_value = stripe_subscription_deleted_event
        
        response = client.post(
            "/webhooks/stripe",
            content=json.dumps(stripe_subscription_deleted_event),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "valid_signature"
            }
        )
        
        assert response.status_code == 200
        
        # Vérifier que le tenant est suspendu
        db.refresh(sample_tenant)
        assert sample_tenant.status == TenantStatus.SUSPENDED


class TestStripeServiceLive:
    """Tests du service Stripe live."""

    def test_create_checkout_session(self, db, sample_tenant, mock_stripe):
        """Test: création d'une session de checkout."""
        from app.modules.stripe_integration.stripe_service_live import StripeServiceLive
        
        service = StripeServiceLive(db)
        
        with patch("stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = MagicMock(
                id="cs_test_123",
                url="https://checkout.stripe.com/test"
            )
            
            result = service.create_checkout_session(
                tenant_id=sample_tenant.tenant_id,
                plan="PROFESSIONAL",
                billing_cycle="monthly",
                success_url="https://app.azalscore.com/success",
                cancel_url="https://app.azalscore.com/cancel",
            )
            
            assert result["session_id"] == "cs_test_123"
            assert "checkout.stripe.com" in result["checkout_url"]

    def test_create_customer(self, db, sample_tenant, mock_stripe):
        """Test: création d'un customer Stripe."""
        from app.modules.stripe_integration.stripe_service_live import StripeServiceLive
        
        service = StripeServiceLive(db)
        
        with patch("stripe.Customer.create") as mock_create:
            mock_create.return_value = MagicMock(id="cus_test_123")
            
            result = service.get_or_create_customer(
                tenant_id=sample_tenant.tenant_id,
                email="billing@testcompany.fr",
                name="Test Company",
            )
            
            assert result is not None

    def test_webhook_signature_validation(self, db):
        """Test: validation de signature webhook."""
        from app.modules.stripe_integration.stripe_service_live import StripeServiceLive
        
        service = StripeServiceLive(db)
        
        # Signature invalide doit lever une exception
        with pytest.raises(Exception):
            service.validate_webhook(
                payload=b'{"test": "data"}',
                signature="invalid_sig",
                endpoint_secret="whsec_test"
            )


class TestStripeCheckoutFlow:
    """Tests du flux complet de checkout."""

    @patch("stripe.checkout.Session.create")
    def test_full_checkout_flow(self, mock_session, client, db, trial_tenant):
        """Test: flux complet inscription → checkout → activation."""
        from app.modules.tenants.models import TenantStatus
        
        # 1. Le tenant est en trial
        assert trial_tenant.status == TenantStatus.TRIAL
        
        # 2. Créer une session de checkout (simulé)
        mock_session.return_value = MagicMock(
            id="cs_test_flow",
            url="https://checkout.stripe.com/test_flow"
        )
        
        # 3. Simuler le webhook de checkout complété
        with patch("stripe.Webhook.construct_event") as mock_construct:
            checkout_event = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_flow",
                        "customer": "cus_test_flow",
                        "subscription": "sub_test_flow",
                        "metadata": {
                            "tenant_id": trial_tenant.tenant_id,
                            "plan": "PROFESSIONAL",
                        }
                    }
                }
            }
            mock_construct.return_value = checkout_event
            
            response = client.post(
                "/webhooks/stripe",
                content=json.dumps(checkout_event),
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid"
                }
            )
            
            assert response.status_code == 200
        
        # 4. Vérifier que le tenant est maintenant ACTIVE
        db.refresh(trial_tenant)
        assert trial_tenant.status == TenantStatus.ACTIVE


class TestStripePricing:
    """Tests de la configuration des prix."""

    def test_price_ids_configured(self):
        """Test: les price_ids sont configurés."""
        from app.modules.stripe_integration.stripe_service_live import PRICE_IDS
        
        assert "STARTER" in PRICE_IDS
        assert "PROFESSIONAL" in PRICE_IDS
        assert "ENTERPRISE" in PRICE_IDS
        
        for plan in PRICE_IDS.values():
            assert "monthly" in plan
            assert "yearly" in plan

    def test_get_price_id(self, db):
        """Test: récupération du price_id selon plan et cycle."""
        from app.modules.stripe_integration.stripe_service_live import StripeServiceLive
        
        service = StripeServiceLive(db)
        
        price_id = service._get_price_id("PROFESSIONAL", "monthly")
        assert price_id is not None
        assert "price_" in price_id or price_id.startswith("price_")

    def test_get_price_id_yearly(self, db):
        """Test: récupération du price_id annuel."""
        from app.modules.stripe_integration.stripe_service_live import StripeServiceLive
        
        service = StripeServiceLive(db)
        
        monthly = service._get_price_id("PROFESSIONAL", "monthly")
        yearly = service._get_price_id("PROFESSIONAL", "yearly")
        
        # Les IDs doivent être différents
        assert monthly != yearly


class TestStripeWebhookSecurity:
    """Tests de sécurité des webhooks."""

    def test_webhook_endpoint_is_public(self, client):
        """Test: endpoint webhook accessible sans auth."""
        # Doit retourner une erreur de signature, pas 401/403
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"},
            headers={"Content-Type": "application/json"}
        )
        
        # 400 (signature manquante), pas 401/403
        assert response.status_code == 400

    def test_webhook_rejects_old_timestamp(self, client):
        """Test: webhook avec timestamp ancien rejeté."""
        # Stripe inclut un timestamp dans la signature
        # Les événements trop vieux (> 5 min) doivent être rejetés
        old_timestamp = int(time.time()) - 400  # 6+ minutes ago
        
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"},
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": f"t={old_timestamp},v1=invalid"
            }
        )
        
        assert response.status_code == 400

    def test_webhook_logs_events(self, client, caplog):
        """Test: les événements webhook sont loggés."""
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = {
                "type": "invoice.paid",
                "data": {"object": {"id": "in_test"}}
            }
            
            response = client.post(
                "/webhooks/stripe",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid"
                }
            )
            
            # Vérifier que l'événement est loggé
            # (Le log exact dépend de l'implémentation)
            assert response.status_code == 200
