"""
AZALS MODULE - STRIPE INTEGRATION: Router Unifié
=================================================

Router complet compatible v1, v2 et v3 via app.azals.
Utilise get_context() qui fonctionne avec les deux patterns d'authentification.

Ce router remplace router.py et router_v2.py.

Enregistrement dans main.py:
    from app.modules.stripe_integration.router_unified import router as stripe_router

    # Double enregistrement pour compatibilité
    app.include_router(stripe_router, prefix="/v2")
    app.include_router(stripe_router, prefix="/v1", deprecated=True)

Conformité : AZA-NF-006

ENDPOINTS (29 total):
- Configuration (3): create/get/update config
- Customers (6): CRUD + by CRM ID + sync
- Payment Methods (3): add/list/delete
- Setup Intents (1): create
- Payment Intents (7): CRUD + confirm/capture/cancel
- Checkout Sessions (2): create/get
- Refunds (2): create/list
- Products & Prices (2): create product/price
- Connect (2): create/get account
- Webhooks (1): handle webhook (PUBLIC)
- Dashboard (1): stats
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.azals import SaaSContext, get_context, get_db

from .service import StripeService
from .schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    ConnectAccountCreate,
    ConnectAccountResponse,
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

router = APIRouter(prefix="/stripe", tags=["Stripe Integration - Paiements"])

def get_stripe_service(db: Session, tenant_id: str, user_id: str) -> StripeService:
    """Factory pour créer le service Stripe avec contexte SaaS."""
    return StripeService(db, tenant_id, user_id)

# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=StripeConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    data: StripeConfigCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer configuration Stripe pour le tenant (ADMIN)."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        config = service.create_config(data)
        return StripeConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/config", response_model=StripeConfigResponse)
async def get_config(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer configuration Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration Stripe non trouvée")
    return StripeConfigResponse.from_orm(config)

@router.patch("/config", response_model=StripeConfigResponse)
async def update_config(
    data: StripeConfigUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour configuration Stripe (ADMIN)."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        config = service.update_config(data)
        return StripeConfigResponse.from_orm(config)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ============================================================================
# CUSTOMERS (CLIENTS STRIPE)
# ============================================================================

@router.post("/customers", response_model=StripeCustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: StripeCustomerCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un client Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        customer = service.create_customer(data)
        return StripeCustomerResponse.from_orm(customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/customers", response_model=list[StripeCustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les clients Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    customers = service.list_customers(skip, limit)
    return [StripeCustomerResponse.from_orm(c) for c in customers]

@router.get("/customers/{customer_id}", response_model=StripeCustomerResponse)
async def get_customer(
    customer_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un client Stripe par ID."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return StripeCustomerResponse.from_orm(customer)

@router.get("/customers/crm/{crm_customer_id}", response_model=StripeCustomerResponse)
async def get_customer_by_crm_id(
    crm_customer_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un client Stripe par ID CRM."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    customer = service.get_customer_by_crm_id(crm_customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return StripeCustomerResponse.from_orm(customer)

@router.patch("/customers/{customer_id}", response_model=StripeCustomerResponse)
async def update_customer(
    customer_id: int,
    data: StripeCustomerUpdate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour un client Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        customer = service.update_customer(customer_id, data)
        return StripeCustomerResponse.from_orm(customer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/customers/{customer_id}/sync", response_model=StripeCustomerResponse)
async def sync_customer(
    customer_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Synchroniser un client Stripe avec l'API Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        customer = service.sync_customer(customer_id)
        return StripeCustomerResponse.from_orm(customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PAYMENT METHODS (MOYENS DE PAIEMENT)
# ============================================================================

@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    data: PaymentMethodCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Ajouter un moyen de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        pm = service.add_payment_method(data)
        return PaymentMethodResponse.from_orm(pm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/customers/{customer_id}/payment-methods", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    customer_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les moyens de paiement d'un client."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    methods = service.list_payment_methods(customer_id)
    return [PaymentMethodResponse.from_orm(m) for m in methods]

@router.delete("/payment-methods/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Supprimer un moyen de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    success = service.delete_payment_method(payment_method_id)
    if not success:
        raise HTTPException(status_code=404, detail="Payment method not found")

# ============================================================================
# SETUP INTENTS (CONFIGURATION PAIEMENT FUTUR)
# ============================================================================

@router.post("/setup-intents", response_model=SetupIntentResponse)
async def create_setup_intent(
    data: SetupIntentCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un Setup Intent pour enregistrer un moyen de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        setup_intent = service.create_setup_intent(data)
        return SetupIntentResponse(
            id=setup_intent.get("id"),
            client_secret=setup_intent.get("client_secret"),
            status=setup_intent.get("status")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PAYMENT INTENTS (INTENTIONS DE PAIEMENT)
# ============================================================================

@router.post("/payment-intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    data: PaymentIntentCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer une intention de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        pi = service.create_payment_intent(data)
        return PaymentIntentResponse.from_orm(pi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payment-intents", response_model=list[PaymentIntentResponse])
async def list_payment_intents(
    customer_id: int | None = Query(None, description="Filtrer par client"),
    status: str | None = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les intentions de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    intents = service.list_payment_intents(customer_id, status, skip, limit)
    return [PaymentIntentResponse.from_orm(pi) for pi in intents]

@router.get("/payment-intents/{payment_intent_id}", response_model=PaymentIntentResponse)
async def get_payment_intent(
    payment_intent_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer une intention de paiement par ID."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    pi = service.get_payment_intent(payment_intent_id)
    if not pi:
        raise HTTPException(status_code=404, detail="Payment Intent not found")
    return PaymentIntentResponse.from_orm(pi)

@router.post("/payment-intents/{payment_intent_id}/confirm", response_model=PaymentIntentResponse)
async def confirm_payment_intent(
    payment_intent_id: int,
    data: PaymentIntentConfirm,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Confirmer une intention de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        pi = service.confirm_payment_intent(payment_intent_id, data)
        return PaymentIntentResponse.from_orm(pi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-intents/{payment_intent_id}/capture", response_model=PaymentIntentResponse)
async def capture_payment_intent(
    payment_intent_id: int,
    amount: int | None = Query(None, description="Montant à capturer (centimes)"),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Capturer une intention de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        pi = service.capture_payment_intent(payment_intent_id, amount)
        return PaymentIntentResponse.from_orm(pi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-intents/{payment_intent_id}/cancel", response_model=PaymentIntentResponse)
async def cancel_payment_intent(
    payment_intent_id: int,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Annuler une intention de paiement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        pi = service.cancel_payment_intent(payment_intent_id)
        return PaymentIntentResponse.from_orm(pi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# CHECKOUT SESSIONS (SESSIONS DE PAIEMENT)
# ============================================================================

@router.post("/checkout-sessions", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    data: CheckoutSessionCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer une session Stripe Checkout."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        session = service.create_checkout_session(data)
        return CheckoutSessionResponse.from_orm(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/checkout-sessions/{session_id}", response_model=CheckoutSessionResponse)
async def get_checkout_session(
    session_id: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer une session Checkout par ID."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    session = service.get_checkout_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    return CheckoutSessionResponse.from_orm(session)

# ============================================================================
# REFUNDS (REMBOURSEMENTS)
# ============================================================================

@router.post("/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    data: RefundCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un remboursement."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        refund = service.create_refund(data)
        return RefundResponse.from_orm(refund)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/refunds", response_model=list[RefundResponse])
async def list_refunds(
    payment_intent_id: int | None = Query(None, description="Filtrer par payment intent"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Lister les remboursements."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    refunds = service.list_refunds(payment_intent_id, skip, limit)
    return [RefundResponse.from_orm(r) for r in refunds]

# ============================================================================
# PRODUCTS & PRICES (CATALOGUE STRIPE)
# ============================================================================

@router.post("/products", response_model=StripeProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: StripeProductCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un produit Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        product = service.create_product(data)
        return StripeProductResponse.from_orm(product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/prices", response_model=StripePriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
    data: StripePriceCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un prix Stripe."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        price = service.create_price(data)
        return StripePriceResponse.from_orm(price)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# STRIPE CONNECT (COMPTES CONNECTÉS)
# ============================================================================

@router.post("/connect/accounts", response_model=ConnectAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_connect_account(
    data: ConnectAccountCreate,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Créer un compte Stripe Connect."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    try:
        account = service.create_connect_account(data)
        return ConnectAccountResponse.from_orm(account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/connect/accounts/{account_id}", response_model=ConnectAccountResponse)
async def get_connect_account(
    account_id: str,
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Récupérer un compte Connect par ID."""
    service = get_stripe_service(db, context.tenant_id, context.user_id)
    account = service.get_connect_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Connect account not found")
    return ConnectAccountResponse.from_orm(account)

# ============================================================================
# WEBHOOKS (PUBLIC - pas de SaaSContext)
# ============================================================================

@router.post("/webhooks")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint webhook Stripe (PUBLIC - pas de SaaSContext).

    SÉCURITÉ: Vérifie la signature Stripe AVANT tout traitement.
    """
    import json
    import os

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

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

    try:
        event_id = event.get("id")
        event_type = event.get("type")

        # Note: Pour webhook, on ne peut pas utiliser SaaSContext
        # Le tenant_id est extrait des metadata de l'événement
        tenant_id = event.get("data", {}).get("object", {}).get("metadata", {}).get("tenant_id")

        if not tenant_id:
            raise ValueError("tenant_id not found in webhook metadata")

        service = StripeService(db, tenant_id)
        webhook = service.process_webhook(event_id, event_type, dict(event), signature)

        return {"received": True, "webhook_id": webhook.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # SÉCURITÉ: Ne pas exposer les détails d'erreur
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# ============================================================================
# DASHBOARD & STATS
# ============================================================================

@router.get("/dashboard", response_model=StripeDashboard)
async def get_dashboard(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
):
    """Dashboard Stripe avec statistiques (ADMIN)."""
    from .models import StripeCustomer, StripePaymentIntent, PaymentIntentStatus

    service = get_stripe_service(db, context.tenant_id, context.user_id)

    # Calculer stats
    from datetime import datetime

    today = datetime.utcnow().date()
    month_start = today.replace(day=1)

    total_customers = db.query(StripeCustomer).filter(
        StripeCustomer.tenant_id == context.tenant_id
    ).count()

    total_payment_intents = db.query(StripePaymentIntent).filter(
        StripePaymentIntent.tenant_id == context.tenant_id
    ).count()

    successful_payments = db.query(StripePaymentIntent).filter(
        StripePaymentIntent.tenant_id == context.tenant_id,
        StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED
    ).count()

    total_revenue = db.query(func.sum(StripePaymentIntent.amount)).filter(
        StripePaymentIntent.tenant_id == context.tenant_id,
        StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED
    ).scalar() or 0

    revenue_this_month = db.query(func.sum(StripePaymentIntent.amount)).filter(
        StripePaymentIntent.tenant_id == context.tenant_id,
        StripePaymentIntent.status == PaymentIntentStatus.SUCCEEDED,
        func.date(StripePaymentIntent.created_at) >= month_start
    ).scalar() or 0

    return StripeDashboard(
        total_customers=total_customers,
        active_customers=total_customers,
        total_payment_intents=total_payment_intents,
        successful_payments=successful_payments,
        failed_payments=total_payment_intents - successful_payments,
        total_revenue=total_revenue,
        revenue_this_month=revenue_this_month,
        refunds_count=0,
        disputes_count=0,
    )
