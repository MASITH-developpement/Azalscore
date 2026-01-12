"""
AZALS - Service Stripe Production
==================================
Intégration complète Stripe avec webhooks.
pip install stripe
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Configuration Stripe
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY_LIVE") or os.getenv("STRIPE_API_KEY_TEST")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_LIVE_MODE = os.getenv("STRIPE_LIVE_MODE", "false").lower() == "true"

if STRIPE_AVAILABLE and STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
    stripe.api_version = "2023-10-16"


# ============================================================
# PLANS AZALSCORE
# ============================================================

AZALSCORE_PLANS = {
    "starter": {
        "name": "Starter",
        "price_monthly": 4900,  # en centimes
        "price_yearly": 49000,
        "stripe_price_monthly": os.getenv("STRIPE_PRICE_STARTER_MONTHLY"),
        "stripe_price_yearly": os.getenv("STRIPE_PRICE_STARTER_YEARLY"),
        "max_users": 5,
        "max_storage_gb": 10,
        "modules": ["commercial", "finance", "hr"],
        "features": ["Multi-tenant", "Audit trail", "Support email"]
    },
    "professional": {
        "name": "Professional", 
        "price_monthly": 14900,
        "price_yearly": 149000,
        "stripe_price_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
        "stripe_price_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY"),
        "max_users": 25,
        "max_storage_gb": 50,
        "modules": [
            "commercial", "finance", "hr", "procurement",
            "inventory", "production", "quality", "maintenance"
        ],
        "features": [
            "Tous les modules métier",
            "API complète",
            "Support prioritaire",
            "Formations incluses"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 49900,
        "price_yearly": 499000,
        "stripe_price_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY"),
        "stripe_price_yearly": os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY"),
        "max_users": -1,  # Illimité
        "max_storage_gb": 500,
        "modules": "ALL",
        "features": [
            "Tous les modules + IA",
            "Support 24/7",
            "SLA 99.9%",
            "Personnalisation",
            "On-premise disponible"
        ]
    }
}


class StripeServiceLive:
    """Service Stripe pour production."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        if not STRIPE_AVAILABLE:
            logger.warning("[STRIPE] Module stripe non installé")
        elif not STRIPE_API_KEY:
            logger.warning("[STRIPE] STRIPE_API_KEY non configurée")

    # ========================================================================
    # CUSTOMERS
    # ========================================================================

    def create_customer(
        self,
        email: str,
        name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """Créer un client Stripe."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "tenant_id": self.tenant_id,
                    **(metadata or {})
                }
            )
            logger.info(f"[STRIPE] Customer créé: {customer.id}")
            return dict(customer)
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur création customer: {e}")
            return None

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Récupérer un client Stripe."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            return dict(stripe.Customer.retrieve(customer_id))
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur récupération customer: {e}")
            return None

    def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> Optional[Dict]:
        """Mettre à jour un client."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)
            return dict(customer)
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur update customer: {e}")
            return None

    # ========================================================================
    # CHECKOUT SESSIONS
    # ========================================================================

    def create_checkout_session(
        self,
        customer_id: str,
        plan: str,
        billing_period: str = "monthly",  # "monthly" | "yearly"
        success_url: str = None,
        cancel_url: str = None,
        trial_days: int = 14
    ) -> Optional[Dict[str, str]]:
        """
        Créer une session de checkout Stripe.
        
        Retourne:
            {"session_id": "...", "url": "..."}
        """
        if not STRIPE_AVAILABLE:
            return None

        plan_config = AZALSCORE_PLANS.get(plan)
        if not plan_config:
            logger.error(f"[STRIPE] Plan inconnu: {plan}")
            return None

        price_key = f"stripe_price_{billing_period}"
        price_id = plan_config.get(price_key)
        
        if not price_id:
            logger.error(f"[STRIPE] Prix non configuré pour {plan}/{billing_period}")
            return None

        app_url = os.getenv("APP_URL", "https://app.azalscore.com")
        
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=success_url or f"{app_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url or f"{app_url}/billing/cancel",
                subscription_data={
                    "trial_period_days": trial_days if trial_days > 0 else None,
                    "metadata": {
                        "tenant_id": self.tenant_id,
                        "plan": plan
                    }
                },
                metadata={
                    "tenant_id": self.tenant_id,
                    "plan": plan,
                    "billing_period": billing_period
                },
                allow_promotion_codes=True,
                billing_address_collection="auto",
                tax_id_collection={"enabled": True}
            )

            logger.info(f"[STRIPE] Checkout session créée: {session.id}")
            return {
                "session_id": session.id,
                "url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur création checkout: {e}")
            return None

    def get_checkout_session(self, session_id: str) -> Optional[Dict]:
        """Récupérer une session de checkout."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["subscription", "customer"]
            )
            return dict(session)
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur récupération session: {e}")
            return None

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Récupérer un abonnement."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            return dict(stripe.Subscription.retrieve(subscription_id))
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur récupération subscription: {e}")
            return None

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> bool:
        """
        Annuler un abonnement.
        
        Args:
            at_period_end: Si True, l'abonnement reste actif jusqu'à la fin de la période
        """
        if not STRIPE_AVAILABLE:
            return False

        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.cancel(subscription_id)

            logger.info(f"[STRIPE] Subscription annulée: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur annulation: {e}")
            return False

    def reactivate_subscription(self, subscription_id: str) -> bool:
        """Réactiver un abonnement annulé (avant la fin de période)."""
        if not STRIPE_AVAILABLE:
            return False

        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"[STRIPE] Subscription réactivée: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur réactivation: {e}")
            return False

    def change_plan(
        self,
        subscription_id: str,
        new_plan: str,
        billing_period: str = "monthly"
    ) -> Optional[Dict]:
        """
        Changer le plan d'un abonnement.
        Gère automatiquement le prorata.
        """
        if not STRIPE_AVAILABLE:
            return None

        plan_config = AZALSCORE_PLANS.get(new_plan)
        if not plan_config:
            logger.error(f"[STRIPE] Plan inconnu: {new_plan}")
            return None

        price_key = f"stripe_price_{billing_period}"
        new_price_id = plan_config.get(price_key)

        if not new_price_id:
            logger.error(f"[STRIPE] Prix non configuré pour {new_plan}/{billing_period}")
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations",
                metadata={
                    "tenant_id": self.tenant_id,
                    "plan": new_plan
                }
            )

            logger.info(f"[STRIPE] Plan changé: {subscription_id} → {new_plan}")
            return dict(updated)

        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur changement plan: {e}")
            return None

    # ========================================================================
    # BILLING PORTAL
    # ========================================================================

    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str = None
    ) -> Optional[str]:
        """
        Créer une session du portail de facturation Stripe.
        Permet au client de gérer son abonnement, factures, moyen de paiement.
        """
        if not STRIPE_AVAILABLE:
            return None

        app_url = os.getenv("APP_URL", "https://app.azalscore.com")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url or f"{app_url}/billing"
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur création portal: {e}")
            return None

    # ========================================================================
    # INVOICES
    # ========================================================================

    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Lister les factures d'un client."""
        if not STRIPE_AVAILABLE:
            return []

        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            return [dict(inv) for inv in invoices.data]
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur liste factures: {e}")
            return []

    def get_invoice_pdf(self, invoice_id: str) -> Optional[str]:
        """Récupérer l'URL du PDF d'une facture."""
        if not STRIPE_AVAILABLE:
            return None

        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return invoice.invoice_pdf
        except stripe.error.StripeError as e:
            logger.error(f"[STRIPE] Erreur récupération facture: {e}")
            return None

    # ========================================================================
    # WEBHOOKS
    # ========================================================================

    @staticmethod
    def verify_webhook(payload: bytes, signature: str) -> Optional[Dict]:
        """
        Vérifier et parser un webhook Stripe.
        
        Args:
            payload: Corps de la requête (bytes)
            signature: Header Stripe-Signature
            
        Returns:
            L'événement parsé ou None si invalide
        """
        if not STRIPE_AVAILABLE or not STRIPE_WEBHOOK_SECRET:
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            return dict(event)
        except stripe.error.SignatureVerificationError:
            logger.warning("[STRIPE] Signature webhook invalide")
            return None
        except Exception as e:
            logger.error(f"[STRIPE] Erreur parsing webhook: {e}")
            return None


# ============================================================
# WEBHOOK HANDLERS
# ============================================================

class StripeWebhookHandler:
    """Gestionnaire des webhooks Stripe."""

    def __init__(self, db: Session):
        self.db = db

    def handle_event(self, event: Dict) -> bool:
        """
        Router l'événement vers le bon handler.
        
        Returns:
            True si traité avec succès
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.updated": self._handle_customer_updated,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                handler(data)
                logger.info(f"[WEBHOOK] Traité: {event_type}")
                return True
            except Exception as e:
                logger.error(f"[WEBHOOK] Erreur {event_type}: {e}")
                return False
        else:
            logger.debug(f"[WEBHOOK] Ignoré: {event_type}")
            return True

    def _handle_checkout_completed(self, session: Dict):
        """Checkout terminé - Activer l'abonnement."""
        from app.core.tenant_status_guard import convert_trial_to_active
        
        metadata = session.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        plan = metadata.get("plan", "STARTER")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        logger.info(
            f"[WEBHOOK] Checkout complété: tenant={tenant_id}, "
            f"plan={plan}, subscription={subscription_id}"
        )

        # Convertir le trial en compte actif
        if tenant_id:
            convert_trial_to_active(self.db, tenant_id, plan)
            
            # TODO: Envoyer email de confirmation
            # from app.services.email_service import get_email_service
            # email_service = get_email_service()
            # email_service.send_payment_success(...)

    def _handle_subscription_created(self, subscription: Dict):
        """Nouvel abonnement créé."""
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        metadata = subscription.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        logger.info(
            f"[WEBHOOK] Subscription créée: {subscription_id}, "
            f"status={status}, tenant={tenant_id}"
        )

    def _handle_subscription_updated(self, subscription: Dict):
        """Abonnement mis à jour (changement de plan, etc.)."""
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        cancel_at_period_end = subscription.get("cancel_at_period_end")

        logger.info(
            f"[WEBHOOK] Subscription mise à jour: {subscription_id}, "
            f"status={status}, cancel_at_period_end={cancel_at_period_end}"
        )

        # TODO: Mettre à jour le tenant si changement de plan

    def _handle_subscription_deleted(self, subscription: Dict):
        """Abonnement annulé/expiré."""
        from app.core.tenant_status_guard import suspend_tenant
        
        subscription_id = subscription.get("id")
        metadata = subscription.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        logger.info(
            f"[WEBHOOK] Subscription supprimée: {subscription_id}, "
            f"tenant={tenant_id}"
        )

        # Suspendre le tenant
        if tenant_id:
            suspend_tenant(self.db, tenant_id, reason="subscription_cancelled")

    def _handle_invoice_paid(self, invoice: Dict):
        """Facture payée."""
        from app.core.tenant_status_guard import reactivate_tenant
        
        invoice_id = invoice.get("id")
        customer_id = invoice.get("customer")
        amount_paid = invoice.get("amount_paid", 0) / 100  # centimes → euros
        subscription_id = invoice.get("subscription")

        logger.info(
            f"[WEBHOOK] Facture payée: {invoice_id}, "
            f"customer={customer_id}, amount={amount_paid}€"
        )

        # Si c'était une facture de renouvellement, s'assurer que le tenant est actif
        # TODO: Récupérer tenant_id depuis customer_id ou subscription
        # if tenant_id:
        #     reactivate_tenant(self.db, tenant_id)
        
        # TODO: Envoyer email de confirmation + facture PDF

    def _handle_payment_failed(self, invoice: Dict):
        """Échec de paiement."""
        from app.core.tenant_status_guard import suspend_tenant
        
        invoice_id = invoice.get("id")
        customer_id = invoice.get("customer")
        attempt_count = invoice.get("attempt_count", 1)
        subscription_id = invoice.get("subscription")

        logger.warning(
            f"[WEBHOOK] Échec paiement: {invoice_id}, "
            f"customer={customer_id}, tentative={attempt_count}"
        )

        # Après 3 tentatives, suspendre le tenant
        if attempt_count >= 3:
            # TODO: Récupérer tenant_id depuis customer_id
            # suspend_tenant(self.db, tenant_id, reason="payment_failed")
            logger.error(f"[WEBHOOK] 3 échecs de paiement - Suspension requise pour customer={customer_id}")
        
        # TODO: Envoyer email de relance

    def _handle_customer_updated(self, customer: Dict):
        """Client mis à jour."""
        customer_id = customer.get("id")
        email = customer.get("email")
        
        logger.info(f"[WEBHOOK] Customer mis à jour: {customer_id}")
        
        # TODO: Synchroniser les infos si nécessaire


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def format_price(amount_cents: int) -> str:
    """Formater un prix en centimes vers une chaîne lisible."""
    return f"{amount_cents / 100:.2f} €"


def get_plan_features(plan: str) -> Dict:
    """Récupérer les caractéristiques d'un plan."""
    return AZALSCORE_PLANS.get(plan, {})
