"""
AZALS MODULE 13 - POS (Point de Vente)
=======================================
Système de caisse enterprise intégré à l'ERP.

Fonctionnalités:
- Gestion des magasins multi-sites
- Terminaux de caisse avec heartbeat
- Sessions caissier (ouverture/fermeture)
- Transactions avec lignes et paiements
- Modes de paiement multiples (espèces, CB, chèque, voucher)
- Remises ligne et globales
- Mouvements de caisse (entrées/sorties)
- Annulations et remboursements
- Transactions en attente (hold)
- Raccourcis produits (quick keys)
- Rapports journaliers (Z-Report)
- Dashboard temps réel
- Mode offline avec synchronisation

Intégrations AZALS:
- M1 Commercial (clients CRM)
- M2 Finance (comptabilité)
- M5 Inventory (stocks temps réel)
- M12 E-Commerce (unification omnicanale)
"""

from .models import (
    POSStore,
    POSTerminal,
    POSUser,
    POSSession,
    CashMovement,
    POSTransaction,
    POSTransactionLine,
    POSPayment,
    POSDailyReport,
    POSProductQuickKey,
    POSHoldTransaction,
    POSOfflineQueue,
    POSTerminalStatus,
    POSSessionStatus,
    POSTransactionStatus,
    PaymentMethodType,
    DiscountType
)

from .service import POSService
from .router import router

__all__ = [
    # Models
    "POSStore",
    "POSTerminal",
    "POSUser",
    "POSSession",
    "CashMovement",
    "POSTransaction",
    "POSTransactionLine",
    "POSPayment",
    "POSDailyReport",
    "POSProductQuickKey",
    "POSHoldTransaction",
    "POSOfflineQueue",
    # Enums
    "POSTerminalStatus",
    "POSSessionStatus",
    "POSTransactionStatus",
    "PaymentMethodType",
    "DiscountType",
    # Service & Router
    "POSService",
    "router"
]
