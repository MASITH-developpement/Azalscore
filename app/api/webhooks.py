"""
AZALS - Webhook Stripe Router
==============================
Endpoint sécurisé pour recevoir les webhooks Stripe.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.services.stripe_service import (
    StripeServiceLive, StripeWebhookHandler
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = get_logger(__name__)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Endpoint webhook Stripe.
    
    Stripe envoie les événements ici après chaque action:
    - checkout.session.completed
    - customer.subscription.created/updated/deleted
    - invoice.paid/payment_failed
    
    IMPORTANT: Cet endpoint est PUBLIC (pas d'auth) mais vérifie la signature Stripe.
    """
    if not stripe_signature:
        logger.warning("[WEBHOOK] Missing Stripe-Signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Récupérer le body brut
    payload = await request.body()

    # Vérifier la signature et parser l'événement
    event = StripeServiceLive.verify_webhook(payload, stripe_signature)
    
    if not event:
        logger.warning("[WEBHOOK] Invalid signature or payload")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type", "unknown")
    event_id = event.get("id", "unknown")
    
    logger.info(f"[WEBHOOK] Received: {event_type} ({event_id})")

    # Traiter l'événement
    db = next(get_db())
    try:
        handler = StripeWebhookHandler(db)
        success = handler.handle_event(event)

        if success:
            return {"status": "success", "event_type": event_type}
        else:
            # On retourne 200 même en cas d'erreur de traitement
            # pour éviter que Stripe ne renvoie le webhook
            logger.warning(f"[WEBHOOK] Processing failed for {event_type}")
            return {"status": "processed_with_errors", "event_type": event_type}

    except Exception as e:
        logger.error(
            f"[WEBHOOK] Error processing {event_type}",
            extra={"error": str(e)[:200]},
            exc_info=True
        )
        # SÉCURITÉ: Ne pas exposer les détails d'erreur internes
        # Retourner 200 pour éviter les retries Stripe
        return {"status": "error", "event_type": event_type, "message": "Internal processing error"}
    
    finally:
        db.close()


@router.get("/stripe/health")
async def webhook_health():
    """Vérifier que l'endpoint webhook est opérationnel."""
    return {"status": "ok", "endpoint": "/webhooks/stripe"}
