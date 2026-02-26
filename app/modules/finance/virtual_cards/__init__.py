"""
AZALSCORE Finance Virtual Cards Management
==========================================

Service de gestion des cartes bancaires virtuelles.

Fonctionnalités:
- Création de cartes virtuelles
- Gestion des limites (montant, utilisation)
- Blocage/déblocage de cartes
- Historique des transactions
- Cartes à usage unique

Usage:
    from app.modules.finance.virtual_cards import VirtualCardService

    service = VirtualCardService(db, tenant_id)
    card = await service.create_card(holder_name="John Doe", limit=Decimal("500"))
    await service.block_card(card.id)
"""

from .service import (
    VirtualCardService,
    VirtualCard,
    CardTransaction,
    CardStatus,
    CardType,
    CardLimitType,
)
from .router import router as virtual_cards_router

__all__ = [
    "VirtualCardService",
    "VirtualCard",
    "CardTransaction",
    "CardStatus",
    "CardType",
    "CardLimitType",
    "virtual_cards_router",
]
