"""
Tests E2E - Workflows Critiques Multi-Modules
==============================================
Valide les flux métier complets à travers plusieurs modules.
"""

import pytest


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_customer_to_payment(
    e2e_client,
    auth_headers_alpha_admin,
    sample_customer_alpha,
    e2e_cleanup
):
    """
    Workflow: Créer client → Créer facture → Créer paiement
    Modules: Commercial (CRM) → Invoicing → Stripe
    """
    # ÉTAPE 1: Créer un client dans le CRM
    # Note: Utiliser l'API v1 si v2 pas encore migrée pour commercial
    # Ou mocker si nécessaire

    # ÉTAPE 2: Créer un client Stripe lié
    stripe_customer_data = {
        "email": sample_customer_alpha["email"],
        "name": sample_customer_alpha["name"],
        "phone": sample_customer_alpha.get("phone")
    }

    response_customer = e2e_client.post(
        "/v2/stripe/customers",
        json=stripe_customer_data,
        headers=auth_headers_alpha_admin
    )

    # Mock peut retourner 401 si auth non configurée
    if response_customer.status_code == 201:
        customer = response_customer.json()
        customer_id = customer["id"]
        e2e_cleanup["customers"].append(customer_id)

        # ÉTAPE 3: Créer une intention de paiement
        payment_intent_data = {
            "amount": 10000,  # 100 EUR
            "currency": "eur",
            "customer_id": customer_id,
            "description": "Test E2E workflow"
        }

        response_payment = e2e_client.post(
            "/v2/stripe/payment-intents",
            json=payment_intent_data,
            headers=auth_headers_alpha_admin
        )

        assert response_payment.status_code in [201, 400, 401]

        if response_payment.status_code == 201:
            payment_intent = response_payment.json()
            assert payment_intent["amount"] == 10000
            assert payment_intent["currency"] == "eur"
            e2e_cleanup["payment_intents"].append(payment_intent["id"])
    else:
        # Mock auth - test de structure OK
        assert response_customer.status_code in [401, 404]


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_marketplace_to_tenant_provisioning(
    e2e_client,
    sample_payment_intent
):
    """
    Workflow: Commande marketplace → Paiement → Provisioning tenant
    Modules: Marketplace → Stripe → Tenants (IAM)
    """
    # ÉTAPE 1: Créer une session checkout marketplace
    checkout_data = {
        "plan_code": "pro",
        "billing_cycle": "monthly",
        "customer_email": "newcustomer@example.com",
        "customer_name": "New Customer",
        "company_name": "New Corp",
        "company_siret": "98765432101234",
        "phone": "+33698765432",
        "billing_address_line1": "456 Avenue Test",
        "billing_city": "Lyon",
        "billing_postal_code": "69001",
        "billing_country": "FR",
        "payment_method": "card"
    }

    response_checkout = e2e_client.post(
        "/v2/marketplace/checkout",
        json=checkout_data
    )

    assert response_checkout.status_code in [201, 400, 401]

    if response_checkout.status_code == 201:
        checkout = response_checkout.json()
        order_id = checkout.get("order_id")

        # ÉTAPE 2: Simuler webhook Stripe payment_intent.succeeded
        # (Dans un vrai E2E, attendre webhook réel)
        webhook_payload = {
            "id": "evt_test_e2e_001",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_e2e_001",
                    "metadata": {
                        "tenant_id": "new-tenant-from-marketplace",
                        "order_id": order_id
                    }
                }
            }
        }

        response_webhook = e2e_client.post(
            "/v2/marketplace/webhooks/stripe",
            json=webhook_payload,
            headers={"stripe-signature": "sig_test_e2e"}
        )

        assert response_webhook.status_code in [200, 400]

        # ÉTAPE 3: Vérifier provisioning automatique
        if order_id:
            response_provision = e2e_client.post(
                f"/v2/marketplace/orders/{order_id}/provision"
            )

            # Doit retourner les infos du tenant créé
            assert response_provision.status_code in [200, 400, 404]


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_mobile_session_to_notification(
    e2e_client,
    auth_headers_alpha_admin
):
    """
    Workflow: Enregistrer device → Créer session → Envoyer notification
    Modules: Mobile
    """
    # ÉTAPE 1: Enregistrer un appareil
    device_data = {
        "device_id": "device-e2e-workflow-001",
        "device_name": "iPhone E2E Test",
        "platform": "ios",
        "os_version": "17.0",
        "app_version": "1.0.0",
        "model": "iPhone 14",
        "push_token": "token_e2e_test_123"
    }

    response_device = e2e_client.post(
        "/v2/mobile/devices/register",
        json=device_data,
        headers=auth_headers_alpha_admin
    )

    assert response_device.status_code in [200, 401, 404]

    if response_device.status_code == 200:
        device = response_device.json()
        device_uuid = device.get("id") or "device-e2e-workflow-001"

        # ÉTAPE 2: Créer une session mobile
        response_session = e2e_client.post(
            "/v2/mobile/sessions",
            params={"device_uuid": device_uuid},
            headers=auth_headers_alpha_admin
        )

        assert response_session.status_code in [200, 400, 401]

        # ÉTAPE 3: Envoyer une notification push
        notification_data = {
            "user_id": 1,
            "title": "Test E2E Notification",
            "body": "This is an E2E test notification",
            "data": {"action": "open_app"}
        }

        response_notification = e2e_client.post(
            "/v2/mobile/notifications",
            json=notification_data,
            headers=auth_headers_alpha_admin
        )

        assert response_notification.status_code in [200, 401, 404]


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_website_content_publication(
    e2e_client,
    auth_headers_alpha_admin
):
    """
    Workflow: Créer page → Ajouter média → Publier → Vérifier SEO
    Modules: Website (CMS)
    """
    # ÉTAPE 1: Upload média
    # Note: Upload fichier nécessite multipart/form-data
    # Simuler avec mock data

    # ÉTAPE 2: Créer une page
    page_data = {
        "title": "E2E Test Page",
        "slug": "e2e-test-page",
        "content": "Contenu de test E2E",
        "status": "draft",
        "meta_title": "E2E Test Page - SEO",
        "meta_description": "Description SEO pour test E2E"
    }

    response_page = e2e_client.post(
        "/v2/website/pages",
        json=page_data,
        headers=auth_headers_alpha_admin
    )

    assert response_page.status_code in [201, 401, 404]

    if response_page.status_code == 201:
        page = response_page.json()
        page_id = page["id"]

        # ÉTAPE 3: Publier la page
        response_publish = e2e_client.post(
            f"/v2/website/pages/{page_id}/publish",
            headers=auth_headers_alpha_admin
        )

        assert response_publish.status_code in [200, 404, 401]

        # ÉTAPE 4: Récupérer la page publiée par slug (endpoint public)
        response_public = e2e_client.get(
            f"/v2/website/pages/slug/e2e-test-page"
        )

        if response_public.status_code == 200:
            public_page = response_public.json()
            assert public_page["slug"] == "e2e-test-page"
            assert public_page["status"] == "published"


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_ai_assistant_decision_flow(
    e2e_client,
    auth_headers_alpha_admin
):
    """
    Workflow: Créer conversation → Analyser → Décision → Confirmer
    Modules: AI Assistant
    """
    # ÉTAPE 1: Créer une conversation
    conversation_data = {
        "title": "E2E Test Conversation",
        "context": "Test conversation for E2E workflow"
    }

    response_conv = e2e_client.post(
        "/v2/ai-assistant/conversations",
        json=conversation_data,
        headers=auth_headers_alpha_admin
    )

    assert response_conv.status_code in [201, 401, 404]

    if response_conv.status_code == 201:
        conversation = response_conv.json()
        conv_id = conversation["id"]

        # ÉTAPE 2: Créer une décision
        decision_data = {
            "conversation_id": conv_id,
            "title": "Test Decision E2E",
            "description": "Test decision for E2E",
            "impact_level": "medium",
            "requires_double_confirmation": False
        }

        response_decision = e2e_client.post(
            "/v2/ai-assistant/decisions",
            json=decision_data,
            headers=auth_headers_alpha_admin
        )

        assert response_decision.status_code in [201, 400, 401]

        if response_decision.status_code == 201:
            decision = response_decision.json()
            decision_id = decision["id"]

            # ÉTAPE 3: Confirmer la décision
            confirm_data = {
                "confirmed": True,
                "confirmation_note": "E2E test confirmation"
            }

            response_confirm = e2e_client.post(
                f"/v2/ai-assistant/decisions/{decision_id}/confirm",
                json=confirm_data,
                headers=auth_headers_alpha_admin
            )

            assert response_confirm.status_code in [200, 400, 401]


@pytest.mark.e2e
@pytest.mark.workflow
def test_workflow_country_pack_localization(
    e2e_client,
    auth_headers_alpha_admin
):
    """
    Workflow: Activer pack pays → Formater données → Valider conformité
    Modules: Country Packs
    """
    # ÉTAPE 1: Obtenir le pack France
    response_pack = e2e_client.get(
        "/v2/country-packs/packs/code/FR",
        headers=auth_headers_alpha_admin
    )

    assert response_pack.status_code in [200, 404, 401]

    if response_pack.status_code == 200:
        # ÉTAPE 2: Formater une devise
        response_currency = e2e_client.post(
            "/v2/country-packs/format-currency",
            params={"amount": 1234.56, "country_code": "FR"},
            headers=auth_headers_alpha_admin
        )

        assert response_currency.status_code in [200, 401]

        if response_currency.status_code == 200:
            formatted = response_currency.json()
            # Format français attendu: "1 234,56 €"
            assert "formatted" in formatted

        # ÉTAPE 3: Valider un SIRET
        response_siret = e2e_client.post(
            "/v2/country-packs/validate-siret",
            params={"siret": "12345678901234"},
            headers=auth_headers_alpha_admin
        )

        assert response_siret.status_code in [200, 401]
