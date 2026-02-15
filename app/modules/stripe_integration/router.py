"""
AZALS MODULE 15 - Stripe Integration Router
=============================================
Endpoints API pour l'intégration Stripe.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id

from .models import PaymentIntentStatus
from .schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    ConnectAccountCreate,
    ConnectAccountResponse,
    PaymentIntentCapture,
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    RefundCreate,
    RefundResponse,
    SetupIntentCreate,
    SetupIntentResponse,
    StripeConfigCreate,
    StripeConfigResponse,
    StripeConfigUpdate,
    StripeCustomerCreate,
    StripeCustomerResponse,
    StripeCustomerUpdate,
    StripeDashboard,
    StripePriceCreate,
    StripePriceResponse,
    StripeProductCreate,
    StripeProductResponse,
)
from .service import StripeService

router = APIRouter(prefix="/stripe", tags=["Stripe - Paiements"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> StripeService:
    return StripeService(db, tenant_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=StripeConfigResponse, status_code=201)
def create_config(
    data: StripeConfigCreate,
    service: StripeService = Depends(get_service)
):
    """Créer configuration Stripe."""
    try:
        config = service.create_config(data)
        return StripeConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            is_live_mode=config.is_live_mode,
            default_currency=config.default_currency,
            default_payment_methods=config.default_payment_methods or ["card"],
            statement_descriptor=config.statement_descriptor,
            auto_capture=config.auto_capture,
            send_receipts=config.send_receipts,
            connect_enabled=config.connect_enabled,
            platform_fee_percent=config.platform_fee_percent,
            has_live_key=bool(config.api_key_live),
            has_test_key=bool(config.api_key_test),
            created_at=config.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config", response_model=StripeConfigResponse)
def get_config(
    service: StripeService = Depends(get_service)
):
    """Récupérer configuration Stripe."""
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return StripeConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        is_live_mode=config.is_live_mode,
        default_currency=config.default_currency,
        default_payment_methods=config.default_payment_methods or ["card"],
        statement_descriptor=config.statement_descriptor,
        auto_capture=config.auto_capture,
        send_receipts=config.send_receipts,
        connect_enabled=config.connect_enabled,
        platform_fee_percent=config.platform_fee_percent,
        has_live_key=bool(config.api_key_live),
        has_test_key=bool(config.api_key_test),
        created_at=config.created_at
    )


@router.patch("/config", response_model=StripeConfigResponse)
def update_config(
    data: StripeConfigUpdate,
    service: StripeService = Depends(get_service)
):
    """Mettre à jour configuration Stripe."""
    try:
        config = service.update_config(data)
        return StripeConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            is_live_mode=config.is_live_mode,
            default_currency=config.default_currency,
            default_payment_methods=config.default_payment_methods or ["card"],
            statement_descriptor=config.statement_descriptor,
            auto_capture=config.auto_capture,
            send_receipts=config.send_receipts,
            connect_enabled=config.connect_enabled,
            platform_fee_percent=config.platform_fee_percent,
            has_live_key=bool(config.api_key_live),
            has_test_key=bool(config.api_key_test),
            created_at=config.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CUSTOMERS
# ============================================================================

@router.post("/customers", response_model=StripeCustomerResponse, status_code=201)
def create_customer(
    data: StripeCustomerCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un client Stripe."""
    try:
        return service.create_customer(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers", response_model=list[StripeCustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: StripeService = Depends(get_service)
):
    """Lister les clients Stripe."""
    items, _ = service.list_customers(skip=skip, limit=limit)
    return items


@router.get("/customers/{customer_id}", response_model=StripeCustomerResponse)
def get_customer(
    customer_id: int,
    service: StripeService = Depends(get_service)
):
    """Récupérer un client Stripe."""
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.get("/customers/crm/{crm_customer_id}", response_model=StripeCustomerResponse)
def get_customer_by_crm_id(
    crm_customer_id: int,
    service: StripeService = Depends(get_service)
):
    """Récupérer client Stripe par ID CRM."""
    customer = service.get_customer_by_crm_id(crm_customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.patch("/customers/{customer_id}", response_model=StripeCustomerResponse)
def update_customer(
    customer_id: int,
    data: StripeCustomerUpdate,
    service: StripeService = Depends(get_service)
):
    """Mettre à jour un client Stripe."""
    customer = service.update_customer(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return customer


@router.post("/customers/{customer_id}/sync", response_model=StripeCustomerResponse)
def sync_customer(
    customer_id: int,
    service: StripeService = Depends(get_service)
):
    """Synchroniser client avec Stripe."""
    try:
        return service.sync_customer(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENT METHODS
# ============================================================================

@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=201)
def add_payment_method(
    data: PaymentMethodCreate,
    service: StripeService = Depends(get_service)
):
    """Ajouter une méthode de paiement."""
    try:
        return service.add_payment_method(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers/{customer_id}/payment-methods", response_model=list[PaymentMethodResponse])
def list_payment_methods(
    customer_id: int,
    service: StripeService = Depends(get_service)
):
    """Lister les méthodes de paiement d'un client."""
    return service.list_payment_methods(customer_id)


@router.delete("/payment-methods/{payment_method_id}", status_code=204)
def delete_payment_method(
    payment_method_id: int,
    service: StripeService = Depends(get_service)
):
    """Supprimer une méthode de paiement."""
    if not service.delete_payment_method(payment_method_id):
        raise HTTPException(status_code=404, detail="Méthode non trouvée")


@router.post("/setup-intents", response_model=SetupIntentResponse)
def create_setup_intent(
    data: SetupIntentCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un SetupIntent pour ajouter une méthode de paiement."""
    try:
        result = service.create_setup_intent(data)
        return SetupIntentResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PAYMENT INTENTS
# ============================================================================

@router.post("/payment-intents", response_model=PaymentIntentResponse, status_code=201)
def create_payment_intent(
    data: PaymentIntentCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un PaymentIntent."""
    try:
        return service.create_payment_intent(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-intents", response_model=list[PaymentIntentResponse])
def list_payment_intents(
    customer_id: int | None = None,
    status: PaymentIntentStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: StripeService = Depends(get_service)
):
    """Lister les PaymentIntents."""
    items, _ = service.list_payment_intents(
        customer_id=customer_id, status=status, skip=skip, limit=limit
    )
    return items


@router.get("/payment-intents/{payment_intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    payment_intent_id: int,
    service: StripeService = Depends(get_service)
):
    """Récupérer un PaymentIntent."""
    pi = service.get_payment_intent(payment_intent_id)
    if not pi:
        raise HTTPException(status_code=404, detail="PaymentIntent non trouvé")
    return pi


@router.post("/payment-intents/{payment_intent_id}/confirm", response_model=PaymentIntentResponse)
def confirm_payment_intent(
    payment_intent_id: int,
    data: PaymentIntentConfirm,
    service: StripeService = Depends(get_service)
):
    """Confirmer un PaymentIntent."""
    try:
        return service.confirm_payment_intent(payment_intent_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{payment_intent_id}/capture", response_model=PaymentIntentResponse)
def capture_payment_intent(
    payment_intent_id: int,
    data: PaymentIntentCapture = None,
    service: StripeService = Depends(get_service)
):
    """Capturer un PaymentIntent."""
    try:
        amount = data.amount_to_capture if data else None
        return service.capture_payment_intent(payment_intent_id, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-intents/{payment_intent_id}/cancel", response_model=PaymentIntentResponse)
def cancel_payment_intent(
    payment_intent_id: int,
    reason: str | None = None,
    service: StripeService = Depends(get_service)
):
    """Annuler un PaymentIntent."""
    try:
        return service.cancel_payment_intent(payment_intent_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CHECKOUT SESSIONS
# ============================================================================

@router.post("/checkout-sessions", response_model=CheckoutSessionResponse, status_code=201)
def create_checkout_session(
    data: CheckoutSessionCreate,
    service: StripeService = Depends(get_service)
):
    """Créer une session de checkout."""
    try:
        return service.create_checkout_session(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/checkout-sessions/{session_id}", response_model=CheckoutSessionResponse)
def get_checkout_session(
    session_id: int,
    service: StripeService = Depends(get_service)
):
    """Récupérer une session de checkout."""
    session = service.get_checkout_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return session


# ============================================================================
# REFUNDS
# ============================================================================

@router.post("/refunds", response_model=RefundResponse, status_code=201)
def create_refund(
    data: RefundCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un remboursement."""
    try:
        return service.create_refund(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/refunds", response_model=list[RefundResponse])
def list_refunds(
    payment_intent_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: StripeService = Depends(get_service)
):
    """Lister les remboursements."""
    return service.list_refunds(
        payment_intent_id=payment_intent_id, skip=skip, limit=limit
    )


# ============================================================================
# PRODUCTS & PRICES
# ============================================================================

@router.post("/products", response_model=StripeProductResponse, status_code=201)
def create_product(
    data: StripeProductCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un produit Stripe."""
    try:
        return service.create_product(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prices", response_model=StripePriceResponse, status_code=201)
def create_price(
    data: StripePriceCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un prix Stripe."""
    try:
        return service.create_price(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CONNECT
# ============================================================================

@router.post("/connect/accounts", response_model=ConnectAccountResponse, status_code=201)
def create_connect_account(
    data: ConnectAccountCreate,
    service: StripeService = Depends(get_service)
):
    """Créer un compte Stripe Connect."""
    try:
        return service.create_connect_account(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connect/accounts/{account_id}", response_model=ConnectAccountResponse)
def get_connect_account(
    account_id: int,
    service: StripeService = Depends(get_service)
):
    """Récupérer un compte Connect."""
    account = service.get_connect_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    return account


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    service: StripeService = Depends(get_service)
):
    """
    Recevoir un webhook Stripe.

    SÉCURITÉ: Vérifie la signature Stripe AVANT tout traitement.
    """
    import json
    import os

    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    # SÉCURITÉ: Signature obligatoire
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # SÉCURITÉ: Vérifier la signature Stripe
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if webhook_secret:
        try:
            import stripe
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception:
            raise HTTPException(status_code=400, detail="Webhook verification failed")
    else:
        # En développement sans secret, parser mais logger un warning
        import logging
        logging.getLogger(__name__).warning(
            "[WEBHOOK] STRIPE_WEBHOOK_SECRET not configured - signature not verified"
        )
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = event.get("id")
    event_type = event.get("type")

    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Payload invalide")

    webhook = service.process_webhook(event_id, event_type, dict(event), signature)
    return {"received": True, "webhook_id": webhook.id}


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=StripeDashboard)
def get_dashboard(
    service: StripeService = Depends(get_service)
):
    """Dashboard Stripe."""
    return service.get_dashboard()
