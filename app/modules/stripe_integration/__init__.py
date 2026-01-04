"""
AZALS MODULE 15 - Stripe Integration
=====================================
Intégration complète avec Stripe pour les paiements.

Fonctionnalités:
- Gestion clients Stripe synchronisés
- Méthodes de paiement (carte, SEPA, etc.)
- PaymentIntents pour paiements
- Sessions Checkout
- Remboursements
- Litiges
- Produits et prix synchronisés
- Stripe Connect pour marketplaces
- Virements automatiques
- Webhooks pour événements temps réel
- Dashboard analytics

Intégrations AZALS:
- M1 Commercial (clients CRM)
- M2 Finance (comptabilité)
- M12 E-Commerce (checkout)
- M14 Subscriptions (abonnements)
"""

from .models import (
    StripeCustomer,
    StripePaymentMethod,
    StripePaymentIntent,
    StripeCheckoutSession,
    StripeRefund,
    StripeDispute,
    StripeWebhook,
    StripeProduct,
    StripePrice,
    StripeConnectAccount,
    StripePayout,
    StripeConfig,
    StripeAccountStatus,
    PaymentIntentStatus,
    RefundStatus,
    DisputeStatus,
    WebhookStatus
)

from .service import StripeService
from .router import router

__all__ = [
    # Models
    "StripeCustomer",
    "StripePaymentMethod",
    "StripePaymentIntent",
    "StripeCheckoutSession",
    "StripeRefund",
    "StripeDispute",
    "StripeWebhook",
    "StripeProduct",
    "StripePrice",
    "StripeConnectAccount",
    "StripePayout",
    "StripeConfig",
    # Enums
    "StripeAccountStatus",
    "PaymentIntentStatus",
    "RefundStatus",
    "DisputeStatus",
    "WebhookStatus",
    # Service & Router
    "StripeService",
    "router"
]
