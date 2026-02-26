"""
AZALSCORE Finance Providers
===========================

Providers pour l'intégration avec les services financiers externes.

Providers disponibles:
- SwanProvider: Agrégation bancaire et open banking (Swan.io)
- NMIProvider: Paiements par carte (NMI Gateway)
- DefactoProvider: Affacturage et financement (Defacto)
- SolarisProvider: Crédit et services bancaires (Solaris Bank)

Usage:
    from app.modules.finance.providers import SwanProvider, FinanceProviderRegistry

    # Via Registry (recommandé)
    registry = FinanceProviderRegistry(tenant_id, db)
    swan = await registry.get_provider(FinanceProviderType.SWAN)
    result = await swan.get_accounts()

    # Direct (pour tests)
    provider = SwanProvider(tenant_id="tenant-001", api_key="sk_...")
    accounts = await provider.get_accounts()
"""

from .base import (
    BaseFinanceProvider,
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
    WebhookEvent,
    WebhookEventType,
)
from .swan import SwanProvider
from .nmi import NMIProvider
from .defacto import DefactoProvider
from .solaris import SolarisProvider
from .registry import FinanceProviderRegistry

__all__ = [
    # Base
    "BaseFinanceProvider",
    "FinanceProviderType",
    "FinanceResult",
    "FinanceError",
    "FinanceErrorCode",
    "WebhookEvent",
    "WebhookEventType",
    # Providers
    "SwanProvider",
    "NMIProvider",
    "DefactoProvider",
    "SolarisProvider",
    # Registry
    "FinanceProviderRegistry",
]
