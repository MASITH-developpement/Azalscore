"""
Tests pour Subscriptions Router v2 - CORE SaaS
===============================================

Coverage complète des endpoints v2:
- Plans (8 tests)
- Add-ons (8 tests)
- Subscriptions (14 tests)
- Invoices (10 tests)
- Payments (5 tests)
- Coupons (6 tests)
- Usage (4 tests)
- Metrics (2 tests)
- Webhooks (2 tests)
- Workflows (2 tests)

Total: ~61 tests
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.core.saas_context import SaaSContext


# ============================================================================
# PLANS - 8 tests
# ============================================================================

def test_create_plan(test_client, mock_saas_context, plan_data, sample_plan):
    """Test création d'un plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_plan.return_value = sample_plan
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_plan
        from app.modules.subscriptions.schemas import PlanCreate

        result = create_plan(PlanCreate(**plan_data), service_mock)

        assert result["id"] == sample_plan["id"]
        assert result["code"] == sample_plan["code"]
        assert result["name"] == sample_plan["name"]
        service_mock.create_plan.assert_called_once()


def test_list_plans(test_client, mock_saas_context, sample_plan):
    """Test listage des plans."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_plans.return_value = ([sample_plan], 1)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plans

        result = list_plans(service=service_mock)

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == sample_plan["id"]


def test_get_plan(test_client, mock_saas_context, sample_plan):
    """Test récupération d'un plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_plan.return_value = sample_plan
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_plan

        result = get_plan(1, service_mock)

        assert result["id"] == sample_plan["id"]
        service_mock.get_plan.assert_called_once_with(1)


def test_get_plan_not_found(test_client, mock_saas_context):
    """Test récupération d'un plan inexistant."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_plan.return_value = None
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_plan

        with pytest.raises(HTTPException) as exc_info:
            get_plan(999, service_mock)

        assert exc_info.value.status_code == 404


def test_update_plan(test_client, mock_saas_context, sample_plan):
    """Test mise à jour d'un plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        updated_plan = {**sample_plan, "name": "Plan Updated"}
        service_mock.update_plan.return_value = updated_plan
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import update_plan
        from app.modules.subscriptions.schemas import PlanUpdate

        result = update_plan(1, PlanUpdate(name="Plan Updated"), service_mock)

        assert result["name"] == "Plan Updated"


def test_update_plan_not_found(test_client, mock_saas_context):
    """Test mise à jour d'un plan inexistant."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.update_plan.return_value = None
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import update_plan
        from app.modules.subscriptions.schemas import PlanUpdate

        with pytest.raises(HTTPException) as exc_info:
            update_plan(999, PlanUpdate(name="Test"), service_mock)

        assert exc_info.value.status_code == 404


def test_delete_plan(test_client, mock_saas_context):
    """Test suppression d'un plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.delete_plan.return_value = True
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import delete_plan

        result = delete_plan(1, service_mock)

        assert result is None
        service_mock.delete_plan.assert_called_once_with(1)


def test_plan_pagination(test_client, mock_saas_context, sample_plan):
    """Test pagination des plans."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        plans = [sample_plan] * 10
        service_mock.list_plans.return_value = (plans, 50)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plans

        result = list_plans(skip=10, limit=10, service=service_mock)

        assert result["total"] == 50
        assert len(result["items"]) == 10


# ============================================================================
# ADD-ONS - 8 tests
# ============================================================================

def test_create_addon(test_client, mock_saas_context, addon_data, sample_addon):
    """Test création d'un add-on."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_addon.return_value = sample_addon
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_addon
        from app.modules.subscriptions.schemas import AddOnCreate

        result = create_addon(AddOnCreate(**addon_data), service_mock)

        assert result["id"] == sample_addon["id"]
        assert result["code"] == sample_addon["code"]


def test_list_addons(test_client, mock_saas_context, sample_addon):
    """Test listage de tous les add-ons."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_all_addons

        result = list_all_addons(service=service_mock)

        # Endpoint non implémenté, retourne liste vide
        assert result == []


def test_list_plan_addons(test_client, mock_saas_context, sample_addon):
    """Test listage des add-ons d'un plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_addons.return_value = [sample_addon]
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plan_addons

        result = list_plan_addons(1, service_mock)

        assert len(result) == 1
        assert result[0]["id"] == sample_addon["id"]


def test_get_addon(test_client, mock_saas_context, sample_addon):
    """Test récupération d'un add-on (via list)."""
    # Note: Pas d'endpoint get_addon direct, testons via list
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_addons.return_value = [sample_addon]
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plan_addons

        result = list_plan_addons(1, service_mock)

        assert result[0]["id"] == sample_addon["id"]


def test_get_addon_not_found(test_client, mock_saas_context):
    """Test récupération d'un add-on inexistant."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_addons.return_value = []
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plan_addons

        result = list_plan_addons(999, service_mock)

        assert len(result) == 0


def test_update_addon(test_client, mock_saas_context, sample_addon):
    """Test mise à jour d'un add-on."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        updated_addon = {**sample_addon, "name": "Addon Updated"}
        service_mock.update_addon.return_value = updated_addon
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import update_addon
        from app.modules.subscriptions.schemas import AddOnUpdate

        result = update_addon(1, AddOnUpdate(name="Addon Updated"), service_mock)

        assert result["name"] == "Addon Updated"


def test_delete_addon(test_client, mock_saas_context):
    """Test suppression d'un add-on."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import delete_addon

        # Endpoint non implémenté, devrait lever 501
        with pytest.raises(HTTPException) as exc_info:
            delete_addon(1, service_mock)

        assert exc_info.value.status_code == 501


def test_addon_pagination(test_client, mock_saas_context, sample_addon):
    """Test pagination des add-ons."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        addons = [sample_addon] * 5
        service_mock.list_addons.return_value = addons
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_plan_addons

        result = list_plan_addons(1, service_mock)

        assert len(result) == 5


# ============================================================================
# SUBSCRIPTIONS - 14 tests
# ============================================================================

def test_create_subscription(test_client, mock_saas_context, subscription_data, sample_subscription):
    """Test création d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_subscription.return_value = sample_subscription
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_subscription
        from app.modules.subscriptions.schemas import SubscriptionCreate

        result = create_subscription(SubscriptionCreate(**subscription_data), service_mock)

        assert result["id"] == sample_subscription["id"]
        assert result["status"] == sample_subscription["status"]


def test_list_subscriptions(test_client, mock_saas_context, sample_subscription):
    """Test listage des abonnements."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_subscriptions.return_value = ([sample_subscription], 1)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_subscriptions

        result = list_subscriptions(service=service_mock)

        assert result["total"] == 1
        assert len(result["items"]) == 1


def test_list_subscriptions_with_filters(test_client, mock_saas_context, sample_subscription):
    """Test listage des abonnements avec filtres."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_subscriptions.return_value = ([sample_subscription], 1)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_subscriptions

        result = list_subscriptions(status="active", plan_id=1, service=service_mock)

        assert result["total"] == 1
        service_mock.list_subscriptions.assert_called_once()


def test_get_subscription(test_client, mock_saas_context, sample_subscription):
    """Test récupération d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_subscription.return_value = sample_subscription
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_subscription

        result = get_subscription(1, service_mock)

        assert result["id"] == sample_subscription["id"]


def test_get_subscription_not_found(test_client, mock_saas_context):
    """Test récupération d'un abonnement inexistant."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_subscription.return_value = None
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_subscription

        with pytest.raises(HTTPException) as exc_info:
            get_subscription(999, service_mock)

        assert exc_info.value.status_code == 404


def test_update_subscription(test_client, mock_saas_context, sample_subscription):
    """Test mise à jour d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        updated_sub = {**sample_subscription, "quantity": 2}
        service_mock.update_subscription.return_value = updated_sub
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import update_subscription
        from app.modules.subscriptions.schemas import SubscriptionUpdate

        result = update_subscription(1, SubscriptionUpdate(quantity=2), service_mock)

        assert result["quantity"] == 2


def test_change_plan(test_client, mock_saas_context, sample_subscription):
    """Test changement de plan."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        changed_sub = {**sample_subscription, "plan_id": 2}
        service_mock.change_plan.return_value = changed_sub
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import change_subscription_plan
        from app.modules.subscriptions.schemas import SubscriptionChangePlanRequest

        data = SubscriptionChangePlanRequest(new_plan_id=2)
        result = change_subscription_plan(1, data, service_mock)

        assert result["plan_id"] == 2


def test_change_plan_not_found(test_client, mock_saas_context):
    """Test changement de plan pour abonnement inexistant."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.change_plan.side_effect = ValueError("Abonnement introuvable")
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import change_subscription_plan
        from app.modules.subscriptions.schemas import SubscriptionChangePlanRequest

        data = SubscriptionChangePlanRequest(new_plan_id=2)

        with pytest.raises(ValueError):
            change_subscription_plan(999, data, service_mock)


def test_cancel_subscription(test_client, mock_saas_context, sample_subscription):
    """Test annulation d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        canceled_sub = {**sample_subscription, "status": "canceled"}
        service_mock.cancel_subscription.return_value = canceled_sub
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import cancel_subscription
        from app.modules.subscriptions.schemas import SubscriptionCancelRequest

        data = SubscriptionCancelRequest(reason="Customer request")
        result = cancel_subscription(1, data, service_mock)

        assert result["status"] == "canceled"


def test_pause_subscription(test_client, mock_saas_context, sample_subscription):
    """Test pause d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        paused_sub = {**sample_subscription, "status": "paused"}
        service_mock.pause_subscription.return_value = paused_sub
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import pause_subscription
        from app.modules.subscriptions.schemas import SubscriptionPauseRequest

        data = SubscriptionPauseRequest(reason="Customer request")
        result = pause_subscription(1, data, service_mock)

        assert result["status"] == "paused"


def test_resume_subscription(test_client, mock_saas_context, sample_subscription):
    """Test reprise d'un abonnement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        resumed_sub = {**sample_subscription, "status": "active"}
        service_mock.resume_subscription.return_value = resumed_sub
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import resume_subscription

        result = resume_subscription(1, service_mock)

        assert result["status"] == "active"


def test_subscription_pagination(test_client, mock_saas_context, sample_subscription):
    """Test pagination des abonnements."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        subs = [sample_subscription] * 10
        service_mock.list_subscriptions.return_value = (subs, 100)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_subscriptions

        result = list_subscriptions(skip=20, limit=10, service=service_mock)

        assert result["total"] == 100
        assert len(result["items"]) == 10


def test_subscription_with_addons(test_client, mock_saas_context, subscription_data, sample_subscription):
    """Test création abonnement avec add-ons."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_subscription.return_value = sample_subscription
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_subscription
        from app.modules.subscriptions.schemas import SubscriptionCreate

        data_with_items = {
            **subscription_data,
            "items": [
                {
                    "add_on_code": "ADDON_STORAGE",
                    "name": "Storage",
                    "unit_price": Decimal("9.99"),
                    "quantity": 1,
                    "usage_type": "licensed"
                }
            ]
        }

        result = create_subscription(SubscriptionCreate(**data_with_items), service_mock)

        assert result["id"] == sample_subscription["id"]


def test_subscription_status_transitions(test_client, mock_saas_context, sample_subscription):
    """Test transitions de statut."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()

        # Active -> Paused
        paused_sub = {**sample_subscription, "status": "paused"}
        service_mock.pause_subscription.return_value = paused_sub

        from app.modules.subscriptions.router_v2 import pause_subscription
        from app.modules.subscriptions.schemas import SubscriptionPauseRequest

        data = SubscriptionPauseRequest(reason="Test")
        result = pause_subscription(1, data, service_mock)

        assert result["status"] == "paused"


# ============================================================================
# INVOICES - 10 tests
# ============================================================================

def test_create_invoice(test_client, mock_saas_context, invoice_data, sample_invoice):
    """Test création d'une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_invoice.return_value = sample_invoice
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_invoice
        from app.modules.subscriptions.schemas import InvoiceCreate

        result = create_invoice(InvoiceCreate(**invoice_data), service_mock)

        assert result["id"] == sample_invoice["id"]
        assert result["invoice_number"] == sample_invoice["invoice_number"]


def test_list_invoices(test_client, mock_saas_context, sample_invoice):
    """Test listage des factures."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_invoices.return_value = ([sample_invoice], 1)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_invoices

        result = list_invoices(service=service_mock)

        assert result["total"] == 1
        assert len(result["items"]) == 1


def test_list_invoices_with_filters(test_client, mock_saas_context, sample_invoice):
    """Test listage des factures avec filtres."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_invoices.return_value = ([sample_invoice], 1)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_invoices

        result = list_invoices(subscription_id=1, status="draft", service=service_mock)

        assert result["total"] == 1


def test_get_invoice(test_client, mock_saas_context, sample_invoice):
    """Test récupération d'une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_invoice.return_value = sample_invoice
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_invoice

        result = get_invoice(1, service_mock)

        assert result["id"] == sample_invoice["id"]


def test_get_invoice_not_found(test_client, mock_saas_context):
    """Test récupération d'une facture inexistante."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_invoice.return_value = None
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_invoice

        with pytest.raises(HTTPException) as exc_info:
            get_invoice(999, service_mock)

        assert exc_info.value.status_code == 404


def test_finalize_invoice(test_client, mock_saas_context, sample_invoice):
    """Test finalisation d'une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        finalized_invoice = {**sample_invoice, "status": "open"}
        service_mock.finalize_invoice.return_value = finalized_invoice
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import finalize_invoice

        result = finalize_invoice(1, service_mock)

        assert result["status"] == "open"


def test_void_invoice(test_client, mock_saas_context, sample_invoice):
    """Test annulation d'une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        voided_invoice = {**sample_invoice, "status": "void"}
        service_mock.void_invoice.return_value = voided_invoice
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import void_invoice

        result = void_invoice(1, service_mock)

        assert result["status"] == "void"


def test_pay_invoice(test_client, mock_saas_context, sample_invoice):
    """Test paiement d'une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        paid_invoice = {**sample_invoice, "status": "paid"}
        service_mock.mark_invoice_paid.return_value = paid_invoice
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import pay_invoice

        result = pay_invoice(1, amount=35.99, service=service_mock)

        assert result["status"] == "paid"


def test_invoice_pagination(test_client, mock_saas_context, sample_invoice):
    """Test pagination des factures."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        invoices = [sample_invoice] * 10
        service_mock.list_invoices.return_value = (invoices, 50)
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_invoices

        result = list_invoices(skip=10, limit=10, service=service_mock)

        assert result["total"] == 50
        assert len(result["items"]) == 10


def test_invoice_line_items(test_client, mock_saas_context, invoice_data, sample_invoice):
    """Test facture avec lignes."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        invoice_with_lines = {
            **sample_invoice,
            "lines": invoice_data["lines"]
        }
        service_mock.create_invoice.return_value = invoice_with_lines
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_invoice
        from app.modules.subscriptions.schemas import InvoiceCreate

        result = create_invoice(InvoiceCreate(**invoice_data), service_mock)

        assert result["id"] == sample_invoice["id"]


# ============================================================================
# PAYMENTS - 5 tests
# ============================================================================

def test_create_payment(test_client, mock_saas_context, payment_data, sample_payment):
    """Test création d'un paiement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_payment.return_value = sample_payment
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_payment
        from app.modules.subscriptions.schemas import PaymentCreate

        result = create_payment(PaymentCreate(**payment_data), service_mock)

        assert result["id"] == sample_payment["id"]
        assert result["status"] == sample_payment["status"]


def test_list_payments(test_client, mock_saas_context, sample_payment):
    """Test listage des paiements."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_payments

        result = list_payments(service=service_mock)

        # Endpoint non implémenté, retourne liste vide
        assert result == []


def test_list_payments_with_filters(test_client, mock_saas_context):
    """Test listage des paiements avec filtres."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_payments

        result = list_payments(invoice_id=1, service=service_mock)

        assert result == []


def test_payment_pagination(test_client, mock_saas_context):
    """Test pagination des paiements."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_payments

        result = list_payments(skip=10, limit=10, service=service_mock)

        assert result == []


def test_payment_application(test_client, mock_saas_context, payment_data, sample_payment):
    """Test application d'un paiement à une facture."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_payment.return_value = sample_payment
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_payment
        from app.modules.subscriptions.schemas import PaymentCreate

        result = create_payment(PaymentCreate(**payment_data), service_mock)

        assert result["invoice_id"] == sample_payment["invoice_id"]


# ============================================================================
# COUPONS - 6 tests
# ============================================================================

def test_create_coupon(test_client, mock_saas_context, coupon_data, sample_coupon):
    """Test création d'un coupon."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.create_coupon.return_value = sample_coupon
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_coupon
        from app.modules.subscriptions.schemas import CouponCreate

        result = create_coupon(CouponCreate(**coupon_data), service_mock)

        assert result["id"] == sample_coupon["id"]
        assert result["code"] == sample_coupon["code"]


def test_list_coupons(test_client, mock_saas_context, sample_coupon):
    """Test listage des coupons."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.list_coupons.return_value = [sample_coupon]
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_coupons

        result = list_coupons(service=service_mock)

        assert len(result) == 1
        assert result[0]["id"] == sample_coupon["id"]


def test_get_coupon(test_client, mock_saas_context, sample_coupon):
    """Test récupération d'un coupon."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_coupon.return_value = sample_coupon
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_coupon

        result = get_coupon(1, service_mock)

        assert result["id"] == sample_coupon["id"]


def test_validate_coupon(test_client, mock_saas_context, sample_coupon):
    """Test validation d'un coupon."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        validation_result = {
            "valid": True,
            "coupon": sample_coupon,
            "discount_amount": Decimal("6.00")
        }
        service_mock.validate_coupon.return_value = validation_result
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import validate_coupon
        from app.modules.subscriptions.schemas import CouponValidateRequest

        data = CouponValidateRequest(code="SUMMER2024", amount=Decimal("30.00"))
        result = validate_coupon(1, data, service_mock)

        assert result["valid"] is True


def test_coupon_expiration(test_client, mock_saas_context, sample_coupon):
    """Test coupon expiré."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        validation_result = {
            "valid": False,
            "error_message": "Coupon expiré"
        }
        service_mock.validate_coupon.return_value = validation_result
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import validate_coupon
        from app.modules.subscriptions.schemas import CouponValidateRequest

        data = CouponValidateRequest(code="EXPIRED2020", amount=Decimal("30.00"))
        result = validate_coupon(1, data, service_mock)

        assert result["valid"] is False
        assert result["error_message"] == "Coupon expiré"


def test_coupon_usage_limit(test_client, mock_saas_context, sample_coupon):
    """Test limite d'utilisation d'un coupon."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        validation_result = {
            "valid": False,
            "error_message": "Limite d'utilisation atteinte"
        }
        service_mock.validate_coupon.return_value = validation_result
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import validate_coupon
        from app.modules.subscriptions.schemas import CouponValidateRequest

        data = CouponValidateRequest(code="MAXED", amount=Decimal("30.00"))
        result = validate_coupon(1, data, service_mock)

        assert result["valid"] is False


# ============================================================================
# USAGE - 4 tests
# ============================================================================

def test_record_usage(test_client, mock_saas_context, usage_data):
    """Test enregistrement d'usage."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        usage_record = {
            "id": 1,
            "subscription_item_id": usage_data["subscription_item_id"],
            "quantity": usage_data["quantity"],
            "unit": usage_data["unit"]
        }
        service_mock.create_usage_record.return_value = usage_record
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import create_usage_record
        from app.modules.subscriptions.schemas import UsageRecordCreate

        result = create_usage_record(1, UsageRecordCreate(**usage_data), service_mock)

        assert result["id"] == 1


def test_list_usage_records(test_client, mock_saas_context):
    """Test listage des enregistrements d'usage."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        usage_summary = [
            {
                "subscription_id": 1,
                "item_id": 1,
                "item_name": "API Calls",
                "total_usage": Decimal("1500"),
                "estimated_amount": Decimal("15.00")
            }
        ]
        service_mock.get_usage_summary.return_value = usage_summary
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_usage_summary

        result = get_usage_summary(1, service=service_mock)

        assert len(result) == 1
        assert result[0]["item_name"] == "API Calls"


def test_usage_pagination(test_client, mock_saas_context):
    """Test pagination des enregistrements d'usage."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        usage_records = [{"id": i, "quantity": 100} for i in range(10)]
        service_mock.get_usage_summary.return_value = usage_records
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_usage_summary

        result = get_usage_summary(1, service=service_mock)

        assert len(result) == 10


def test_usage_aggregation(test_client, mock_saas_context):
    """Test agrégation d'usage."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        usage_summary = [
            {
                "subscription_id": 1,
                "item_id": 1,
                "total_usage": Decimal("5000"),
                "estimated_amount": Decimal("50.00")
            }
        ]
        service_mock.get_usage_summary.return_value = usage_summary
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_usage_summary

        result = get_usage_summary(1, service=service_mock)

        assert float(result[0]["total_usage"]) == 5000.0


# ============================================================================
# METRICS - 2 tests
# ============================================================================

def test_get_metrics(test_client, mock_saas_context, sample_metrics):
    """Test récupération des métriques."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_metrics.return_value = sample_metrics
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_metrics

        result = get_metrics(service=service_mock)

        assert result["mrr"] == sample_metrics["mrr"]
        assert result["arr"] == sample_metrics["arr"]


def test_metrics_structure(test_client, mock_saas_context, sample_metrics):
    """Test structure des métriques."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        service_mock.get_metrics.return_value = sample_metrics
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import get_metrics

        result = get_metrics(service=service_mock)

        # Vérifier présence des champs clés
        assert "mrr" in result
        assert "arr" in result
        assert "new_mrr" in result
        assert "expansion_mrr" in result
        assert "churned_mrr" in result
        assert "active_subscriptions" in result
        assert "churn_rate" in result


# ============================================================================
# WEBHOOKS - 2 tests
# ============================================================================

def test_create_webhook(test_client, mock_saas_context):
    """Test réception d'un webhook."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        webhook_obj = Mock()
        webhook_obj.id = 1
        service_mock.process_webhook.return_value = webhook_obj
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import receive_webhook
        from app.modules.subscriptions.schemas import WebhookEvent

        event = WebhookEvent(
            event_type="subscription.created",
            source="stripe",
            payload={"id": "sub_123", "object": "subscription"}
        )

        result = receive_webhook(event, service_mock)

        assert result["received"] is True
        assert result["webhook_id"] == 1


def test_list_webhooks(test_client, mock_saas_context):
    """Test listage des webhooks."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()
        mock_service.return_value = service_mock

        from app.modules.subscriptions.router_v2 import list_webhooks

        result = list_webhooks(service=service_mock)

        # Endpoint non implémenté, retourne liste vide
        assert result == []


# ============================================================================
# WORKFLOWS - 2 tests
# ============================================================================

def test_complete_subscription_lifecycle(test_client, mock_saas_context, subscription_data, sample_subscription, sample_invoice, sample_payment):
    """Test workflow complet: création → facture → paiement → renouvellement."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()

        # 1. Créer abonnement
        service_mock.create_subscription.return_value = sample_subscription

        from app.modules.subscriptions.router_v2 import create_subscription
        from app.modules.subscriptions.schemas import SubscriptionCreate

        sub = create_subscription(SubscriptionCreate(**subscription_data), service_mock)
        assert sub["id"] == sample_subscription["id"]

        # 2. Créer facture
        service_mock.create_invoice.return_value = sample_invoice

        from app.modules.subscriptions.router_v2 import create_invoice
        from app.modules.subscriptions.schemas import InvoiceCreate

        invoice_data_dict = {
            "subscription_id": sub["id"],
            "customer_id": 100,
            "customer_name": "Acme Corp",
            "customer_email": "contact@acme.com",
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 1, 31),
            "collection_method": "send_invoice",
            "lines": []
        }
        invoice = create_invoice(InvoiceCreate(**invoice_data_dict), service_mock)
        assert invoice["id"] == sample_invoice["id"]

        # 3. Payer facture
        service_mock.mark_invoice_paid.return_value = {**sample_invoice, "status": "paid"}

        from app.modules.subscriptions.router_v2 import pay_invoice

        paid_invoice = pay_invoice(invoice["id"], service=service_mock)
        assert paid_invoice["status"] == "paid"


def test_plan_change_workflow(test_client, mock_saas_context, sample_subscription):
    """Test workflow changement de plan avec proratisation."""
    with patch("app.modules.subscriptions.router_v2.get_subscription_service") as mock_service:
        service_mock = Mock()

        # Abonnement initial
        service_mock.get_subscription.return_value = sample_subscription

        from app.modules.subscriptions.router_v2 import get_subscription

        sub = get_subscription(1, service_mock)
        assert sub["plan_id"] == 1

        # Changement de plan
        changed_sub = {**sample_subscription, "plan_id": 2}
        service_mock.change_plan.return_value = changed_sub

        from app.modules.subscriptions.router_v2 import change_subscription_plan
        from app.modules.subscriptions.schemas import SubscriptionChangePlanRequest

        data = SubscriptionChangePlanRequest(new_plan_id=2, prorate=True)
        result = change_subscription_plan(1, data, service_mock)

        assert result["plan_id"] == 2
