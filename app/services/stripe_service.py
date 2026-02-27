"""
AZALS - Service Stripe Production
==================================
Intégration complète Stripe avec webhooks.
pip install stripe
"""
from __future__ import annotations


import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from sqlalchemy.orm import Session

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Configuration Stripe
# Utilise STRIPE_SECRET_KEY (standard) avec fallback vers anciens noms pour compatibilité
STRIPE_API_KEY = (
    os.getenv("STRIPE_SECRET_KEY") or
    os.getenv("STRIPE_API_KEY_LIVE") or
    os.getenv("STRIPE_API_KEY_TEST")
)
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

    # Domaines autorisés pour les redirections (protection open redirect)
    ALLOWED_REDIRECT_DOMAINS = {
        "app.azalscore.com",
        "azalscore.com",
        "staging.azalscore.com",
        "localhost",  # Pour développement
    }

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

        if not STRIPE_AVAILABLE:
            logger.warning("[STRIPE] Module stripe non installé")
        elif not STRIPE_API_KEY:
            logger.warning("[STRIPE] STRIPE_API_KEY non configurée")

    def _validate_redirect_url(self, url: str) -> bool:
        """
        Valide qu'une URL de redirection est sûre (protection open redirect).

        SÉCURITÉ: Empêche les redirections vers des domaines malveillants.
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)

            # Doit être HTTPS en production (HTTP autorisé pour localhost)
            if parsed.scheme not in ("https", "http"):
                return False

            if parsed.scheme == "http" and parsed.hostname != "localhost":
                return False

            # Vérifier le domaine
            hostname = parsed.hostname or ""

            # Domaines autorisés ou sous-domaines
            for allowed_domain in self.ALLOWED_REDIRECT_DOMAINS:
                if hostname == allowed_domain or hostname.endswith(f".{allowed_domain}"):
                    return True

            return False

        except Exception:
            return False

    def _get_safe_redirect_url(self, url: Optional[str], default_path: str) -> str:
        """Retourne une URL de redirection sûre ou la valeur par défaut."""
        app_url = os.getenv("APP_URL", "https://app.azalscore.com")

        if url and self._validate_redirect_url(url):
            return url

        return f"{app_url}{default_path}"

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

        # Valider les URLs de redirection (protection open redirect)
        safe_success_url = self._get_safe_redirect_url(
            success_url,
            "/billing/success?session_id={CHECKOUT_SESSION_ID}"
        )
        safe_cancel_url = self._get_safe_redirect_url(
            cancel_url,
            "/billing/cancel"
        )

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=safe_success_url,
                cancel_url=safe_cancel_url,
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

        # Valider l'URL de retour (protection open redirect)
        safe_return_url = self._get_safe_redirect_url(return_url, "/billing")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=safe_return_url
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

    def _validate_tenant_id(self, tenant_id: Optional[str]) -> bool:
        """
        Valide que le tenant_id existe dans la base.

        SÉCURITÉ: Empêche le traitement de webhooks avec des tenant_id forgés.
        """
        if not tenant_id:
            return False

        try:
            from app.modules.tenants.models import Tenant, TenantStatus
            tenant = self.db.query(Tenant).filter(
                Tenant.tenant_id == tenant_id,
                Tenant.status.in_([TenantStatus.ACTIVE, TenantStatus.TRIAL])
            ).first()
            return tenant is not None
        except Exception as e:
            logger.error(f"[WEBHOOK] Erreur validation tenant_id: {e}")
            return False

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
        from app.services.tenant_status_guard import convert_trial_to_active

        metadata = session.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        plan = metadata.get("plan", "STARTER")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        logger.info(
            f"[WEBHOOK] Checkout complété: tenant={tenant_id}, "
            f"plan={plan}, subscription={subscription_id}"
        )

        # SÉCURITÉ: Valider que le tenant_id existe avant traitement
        if tenant_id:
            if not self._validate_tenant_id(tenant_id):
                logger.error(
                    f"[WEBHOOK] SÉCURITÉ: tenant_id invalide ou inexistant dans checkout: {tenant_id}"
                )
                raise ValueError(f"Invalid tenant_id in webhook metadata: {tenant_id}")
            convert_trial_to_active(self.db, tenant_id, plan)
            
            # NOTE: Phase 2 - Intégration email_service
            # from app.services.email_service import get_email_service
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

        # NOTE: Phase 2 - Mettre à jour le tenant si changement de plan

    def _handle_subscription_deleted(self, subscription: Dict):
        """Abonnement annulé/expiré."""
        from app.services.tenant_status_guard import suspend_tenant

        subscription_id = subscription.get("id")
        metadata = subscription.get("metadata", {})
        tenant_id = metadata.get("tenant_id")

        logger.info(
            f"[WEBHOOK] Subscription supprimée: {subscription_id}, "
            f"tenant={tenant_id}"
        )

        # SÉCURITÉ: Valider que le tenant_id existe avant suspension
        if tenant_id:
            if not self._validate_tenant_id(tenant_id):
                logger.error(
                    f"[WEBHOOK] SÉCURITÉ: tenant_id invalide dans subscription deleted: {tenant_id}"
                )
                raise ValueError(f"Invalid tenant_id in webhook metadata: {tenant_id}")
            suspend_tenant(self.db, tenant_id, reason="subscription_cancelled")

    def _handle_invoice_paid(self, invoice: Dict):
        """Facture payée."""
        from app.services.tenant_status_guard import reactivate_tenant
        
        invoice_id = invoice.get("id")
        customer_id = invoice.get("customer")
        amount_paid = invoice.get("amount_paid", 0) / 100  # centimes → euros
        subscription_id = invoice.get("subscription")

        logger.info(
            f"[WEBHOOK] Facture payée: {invoice_id}, "
            f"customer={customer_id}, amount={amount_paid}€"
        )

        # NOTE: Phase 2 - Récupérer tenant_id depuis customer_id ou subscription
        # pour réactiver le tenant et envoyer email de confirmation + facture PDF

    def _handle_payment_failed(self, invoice: Dict):
        """Échec de paiement."""
        from app.services.tenant_status_guard import suspend_tenant
        
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
            # NOTE: Phase 2 - Récupérer tenant_id depuis customer_id pour suspension
            # suspend_tenant(self.db, tenant_id, reason="payment_failed")
            logger.error(f"[WEBHOOK] 3 échecs de paiement - Suspension requise pour customer={customer_id}")

        # NOTE: Phase 2 - Envoyer email de relance via email_service

    def _handle_customer_updated(self, customer: Dict):
        """Client mis à jour."""
        customer_id = customer.get("id")
        email = customer.get("email")
        
        logger.info(f"[WEBHOOK] Customer mis à jour: {customer_id}")
        
        # NOTE: Phase 2 - Synchroniser les infos client si nécessaire


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def format_price(amount_cents: int) -> str:
    """Formater un prix en centimes vers une chaîne lisible."""
    return f"{amount_cents / 100:.2f} €"


def get_plan_features(plan: str) -> Dict:
    """Récupérer les caractéristiques d'un plan."""
    return AZALSCORE_PLANS.get(plan, {})
