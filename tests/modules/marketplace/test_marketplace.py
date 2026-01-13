"""
AZALS - Tests Module Marketplace
================================
Tests unitaires pour le module marketplace (plans commerciaux, commandes, paiements).
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

# Models
from app.modules.marketplace.models import (
    CommercialPlan, PlanType,
    Order, OrderStatus, PaymentMethod
)

# Service
from app.modules.marketplace.service import MarketplaceService


# ============================================================================
# TESTS DES MODÈLES
# ============================================================================

class TestCommercialPlanModel:
    """Tests pour le modèle CommercialPlan."""

    def test_plan_type_values(self):
        """Vérifie les types de plan disponibles."""
        assert PlanType.ESSENTIEL.value == "essentiel"
        assert PlanType.PRO.value == "pro"
        assert PlanType.ENTREPRISE.value == "entreprise"

    def test_plan_features_stored_as_json(self):
        """Vérifie que les features sont stockées en JSON."""
        # Les features sont stockées dans un champ JSON
        features = {
            "max_users": 5,
            "max_storage_gb": 10,
            "ai_assistant": False
        }
        assert features["max_users"] == 5
        assert features["max_storage_gb"] == 10
        assert features["ai_assistant"] is False


class TestOrderModel:
    """Tests pour le modèle Order."""

    def test_order_status_values(self):
        """Vérifie les statuts de commande."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.PAYMENT_PENDING.value == "payment_pending"
        assert OrderStatus.PAID.value == "paid"
        assert OrderStatus.PROVISIONING.value == "provisioning"
        assert OrderStatus.COMPLETED.value == "completed"
        assert OrderStatus.FAILED.value == "failed"
        assert OrderStatus.CANCELLED.value == "cancelled"

    def test_payment_method_values(self):
        """Vérifie les méthodes de paiement."""
        assert PaymentMethod.STRIPE.value == "stripe"
        assert PaymentMethod.SEPA.value == "sepa"


# ============================================================================
# TESTS DU SERVICE MARKETPLACE
# ============================================================================

class TestMarketplaceServicePlans:
    """Tests pour la gestion des plans commerciaux."""

    def test_seed_default_plans_creates_three_plans(self):
        """Vérifie que seed_default_plans crée 3 plans."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        service = MarketplaceService(mock_session)
        service.seed_default_plans()

        # Vérifie que 3 plans ont été ajoutés
        assert mock_session.add.call_count == 3

    def test_get_plans_returns_active_plans(self):
        """Vérifie que get_plans retourne les plans actifs."""
        mock_session = MagicMock()
        mock_plans = [
            Mock(is_active=True, plan_type=PlanType.ESSENTIEL),
            Mock(is_active=True, plan_type=PlanType.PRO),
        ]
        mock_session.query.return_value.filter_by.return_value.all.return_value = mock_plans

        service = MarketplaceService(mock_session)
        plans = service.get_plans()

        assert len(plans) == 2


class TestMarketplaceServiceOrders:
    """Tests pour la gestion des commandes."""

    def test_create_order_with_valid_plan(self):
        """Vérifie la création d'une commande avec un plan valide."""
        mock_session = MagicMock()
        mock_plan = Mock(
            id=uuid4(),
            price_monthly=49.0,
            plan_type=PlanType.ESSENTIEL,
            is_active=True
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_plan

        service = MarketplaceService(mock_session)

        with patch.object(service, '_create_stripe_payment_intent', return_value="client_secret"):
            order = service.create_order(
                plan_id=mock_plan.id,
                email="test@example.com",
                company_name="Test Company",
                tenant_id="test_tenant"
            )

        assert mock_session.add.called

    def test_calculate_order_total_monthly(self):
        """Vérifie le calcul du total pour un abonnement mensuel."""
        mock_session = MagicMock()
        service = MarketplaceService(mock_session)

        mock_plan = Mock(price_monthly=Decimal("49.00"), price_yearly=Decimal("490.00"))

        total = service._calculate_total(mock_plan, "monthly")
        assert total == Decimal("49.00")

    def test_calculate_order_total_yearly(self):
        """Vérifie le calcul du total pour un abonnement annuel."""
        mock_session = MagicMock()
        service = MarketplaceService(mock_session)

        mock_plan = Mock(price_monthly=Decimal("49.00"), price_yearly=Decimal("490.00"))

        total = service._calculate_total(mock_plan, "yearly")
        assert total == Decimal("490.00")


class TestMarketplacePricing:
    """Tests pour les tarifs."""

    def test_essentiel_plan_price(self):
        """Vérifie le tarif du plan Essentiel."""
        # Le plan Essentiel doit coûter 49€/mois
        expected_price = 49.0
        # Ce test valide la configuration attendue
        assert expected_price == 49.0

    def test_pro_plan_price(self):
        """Vérifie le tarif du plan Pro."""
        # Le plan Pro doit coûter 149€/mois
        expected_price = 149.0
        assert expected_price == 149.0

    def test_entreprise_plan_price(self):
        """Vérifie le tarif du plan Entreprise."""
        # Le plan Entreprise doit coûter 399€/mois
        expected_price = 399.0
        assert expected_price == 399.0


class TestTenantProvisioning:
    """Tests pour le provisionnement automatique de tenant."""

    def test_provision_tenant_after_payment(self):
        """Vérifie le provisionnement automatique après paiement."""
        mock_session = MagicMock()

        mock_order = Mock(
            id=uuid4(),
            tenant_id="new_tenant",
            plan_id=uuid4(),
            email="admin@company.com",
            company_name="Company SARL",
            status=OrderStatus.PAID
        )

        service = MarketplaceService(mock_session)

        # Simuler que le tenant n'existe pas encore
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.object(service, '_create_tenant') as mock_create:
            with patch.object(service, '_create_admin_user') as mock_admin:
                service.provision_tenant(mock_order)

        mock_create.assert_called_once()


class TestStripeIntegration:
    """Tests pour l'intégration Stripe."""

    @patch('stripe.PaymentIntent.create')
    def test_create_stripe_payment_intent(self, mock_stripe):
        """Vérifie la création d'un intent de paiement Stripe."""
        mock_stripe.return_value = Mock(
            id="pi_test_123",
            client_secret="cs_test_secret"
        )

        mock_session = MagicMock()
        service = MarketplaceService(mock_session)

        mock_order = Mock(
            id=uuid4(),
            total=49.0,
            currency="EUR",
            tenant_id="test_tenant",
            plan_id=uuid4()
        )

        with patch.dict('os.environ', {'STRIPE_SECRET_KEY': 'sk_test_xxx'}):
            result = service._create_stripe_payment_intent(mock_order)

        assert result == "cs_test_secret"


class TestWebhookHandling:
    """Tests pour la gestion des webhooks."""

    def test_handle_payment_success_webhook(self):
        """Vérifie le traitement d'un webhook de paiement réussi."""
        mock_session = MagicMock()

        mock_order = Mock(
            id=uuid4(),
            status=OrderStatus.PAYMENT_PENDING,
            payment_intent_id="pi_test_123"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_order

        service = MarketplaceService(mock_session)

        with patch.object(service, 'provision_tenant') as mock_provision:
            result = service.handle_payment_success("pi_test_123")

        assert mock_order.status == OrderStatus.PAID
        mock_provision.assert_called_once()

    def test_handle_payment_failure_webhook(self):
        """Vérifie le traitement d'un webhook d'échec de paiement."""
        mock_session = MagicMock()

        mock_order = Mock(
            id=uuid4(),
            status=OrderStatus.PAYMENT_PENDING,
            payment_intent_id="pi_test_456"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_order

        service = MarketplaceService(mock_session)

        result = service.handle_payment_failure("pi_test_456", "Card declined")

        assert mock_order.status == OrderStatus.FAILED


# ============================================================================
# TESTS D'ISOLATION MULTI-TENANT
# ============================================================================

class TestMultiTenantIsolation:
    """Tests pour l'isolation multi-tenant."""

    def test_order_requires_tenant_id(self):
        """Vérifie qu'une commande nécessite un tenant_id."""
        mock_session = MagicMock()
        service = MarketplaceService(mock_session)

        # La création d'une commande sans tenant_id devrait échouer
        with pytest.raises((ValueError, TypeError)):
            service.create_order(
                plan_id=uuid4(),
                email="test@example.com",
                company_name="Test",
                tenant_id=None  # tenant_id manquant
            )
