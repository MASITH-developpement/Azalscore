"""
AZALS MODULE 14 - Subscriptions
================================
Gestion des abonnements enterprise.

Fonctionnalités:
- Plans d'abonnement avec intervalles flexibles
- Add-ons et options
- Périodes d'essai
- Gestion du cycle de vie (création, upgrade, downgrade, pause, annulation)
- Facturation automatique et manuelle
- Paiements et remboursements
- Usage metered (basé sur l'usage)
- Coupons et réductions
- Métriques SaaS (MRR, ARR, churn, LTV)
- Dashboard analytics

Intégrations AZALS:
- M1 Commercial (clients CRM)
- M2 Finance (facturation comptable)
- M15 Stripe (paiements)
- T6 Broadcast (notifications)
"""

from .models import (
    InvoiceLine,
    InvoiceStatus,
    PaymentStatus,
    PlanAddOn,
    PlanInterval,
    Subscription,
    SubscriptionChange,
    SubscriptionCoupon,
    SubscriptionInvoice,
    SubscriptionItem,
    SubscriptionMetrics,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionStatus,
    SubscriptionWebhook,
    UsageRecord,
    UsageType,
)
from .router import router
from .service import SubscriptionService

__all__ = [
    # Models
    "SubscriptionPlan",
    "PlanAddOn",
    "Subscription",
    "SubscriptionItem",
    "SubscriptionChange",
    "SubscriptionInvoice",
    "InvoiceLine",
    "SubscriptionPayment",
    "UsageRecord",
    "SubscriptionCoupon",
    "SubscriptionMetrics",
    "SubscriptionWebhook",
    # Enums
    "PlanInterval",
    "SubscriptionStatus",
    "InvoiceStatus",
    "PaymentStatus",
    "UsageType",
    # Service & Router
    "SubscriptionService",
    "router"
]
