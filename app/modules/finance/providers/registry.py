"""
AZALSCORE Finance Provider Registry
===================================

Registry centralisé pour la gestion des providers finance.
Gère la configuration multi-tenant, l'instanciation lazy, et le caching.

Usage:
    from app.modules.finance.providers import FinanceProviderRegistry

    registry = FinanceProviderRegistry(tenant_id, db)

    # Récupérer un provider configuré
    swan = await registry.get_provider(FinanceProviderType.SWAN)
    if swan:
        accounts = await swan.get_accounts()

    # Lister les providers disponibles
    available = await registry.list_available_providers()
"""
from __future__ import annotations


import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .base import (
    BaseFinanceProvider,
    FinanceProviderType,
    FinanceResult,
    FinanceError,
    FinanceErrorCode,
)
from .swan import SwanProvider
from .nmi import NMIProvider
from .defacto import DefactoProvider
from .solaris import SolarisProvider

logger = logging.getLogger(__name__)


class FinanceProviderRegistry:
    """
    Registry centralisé pour les providers finance.

    Fonctionnalités:
    - Configuration multi-tenant via DB
    - Instanciation lazy des providers
    - Caching des instances
    - Validation des credentials
    - Health check des providers
    """

    def __init__(self, tenant_id: str, db: Session):
        """
        Initialise le registry.

        Args:
            tenant_id: ID du tenant (OBLIGATOIRE)
            db: Session SQLAlchemy
        """
        if not tenant_id:
            raise ValueError("tenant_id est obligatoire")

        self.tenant_id = tenant_id
        self.db = db

        # Cache des instances de providers
        self._providers: dict[FinanceProviderType, BaseFinanceProvider] = {}

        # Logger avec contexte tenant
        self._logger = logging.LoggerAdapter(
            logger,
            extra={"tenant_id": tenant_id, "service": "FinanceProviderRegistry"}
        )

    async def get_provider(
        self,
        provider_type: FinanceProviderType,
        force_reload: bool = False,
    ) -> Optional[BaseFinanceProvider]:
        """
        Récupère une instance de provider configurée pour le tenant.

        Args:
            provider_type: Type de provider souhaité
            force_reload: Force la recréation de l'instance

        Returns:
            Instance du provider ou None si non configuré
        """
        # Vérifier le cache
        if not force_reload and provider_type in self._providers:
            return self._providers[provider_type]

        # Récupérer la configuration depuis la DB
        config = self._get_provider_config(provider_type)

        if not config:
            self._logger.debug(f"Provider {provider_type.value} non configuré pour le tenant")
            return None

        if not config.get("is_enabled", False):
            self._logger.debug(f"Provider {provider_type.value} désactivé pour le tenant")
            return None

        # Instancier le provider
        provider = self._create_provider(provider_type, config)

        if provider:
            self._providers[provider_type] = provider
            self._logger.info(f"Provider {provider_type.value} initialisé")

        return provider

    def _get_provider_config(self, provider_type: FinanceProviderType) -> Optional[dict]:
        """
        Récupère la configuration d'un provider depuis la DB.

        Args:
            provider_type: Type de provider

        Returns:
            Configuration ou None
        """
        try:
            # Chercher dans la table de configuration
            # Note: La table sera créée avec la migration
            from app.modules.finance.models import FinanceProviderConfig

            config = self.db.query(FinanceProviderConfig).filter(
                FinanceProviderConfig.tenant_id == self.tenant_id,
                FinanceProviderConfig.provider == provider_type.value,
            ).first()

            if config:
                return {
                    "is_enabled": config.is_enabled,
                    "api_key": config.api_key,
                    "api_secret": config.api_secret,
                    "project_id": config.config_data.get("project_id") if config.config_data else None,
                    "webhook_secret": config.config_data.get("webhook_secret") if config.config_data else None,
                    "sandbox": config.config_data.get("sandbox", False) if config.config_data else False,
                }

        except Exception as e:
            # Table pas encore créée ou autre erreur
            self._logger.debug(f"Config DB non disponible: {e}")

        # Fallback: configuration par défaut (pour développement)
        return self._get_default_config(provider_type)

    def _get_default_config(self, provider_type: FinanceProviderType) -> Optional[dict]:
        """
        Configuration par défaut pour développement.

        En production, la config doit venir de la DB.
        """
        import os

        if provider_type == FinanceProviderType.SWAN:
            api_key = os.environ.get("SWAN_API_KEY")
            if api_key:
                return {
                    "is_enabled": True,
                    "api_key": api_key,
                    "project_id": os.environ.get("SWAN_PROJECT_ID"),
                    "webhook_secret": os.environ.get("SWAN_WEBHOOK_SECRET"),
                    "sandbox": os.environ.get("SWAN_SANDBOX", "true").lower() == "true",
                }

        elif provider_type == FinanceProviderType.NMI:
            api_key = os.environ.get("NMI_API_KEY")
            if api_key:
                return {
                    "is_enabled": True,
                    "api_key": api_key,
                    "webhook_secret": os.environ.get("NMI_WEBHOOK_SECRET"),
                    "sandbox": os.environ.get("NMI_SANDBOX", "true").lower() == "true",
                }

        elif provider_type == FinanceProviderType.DEFACTO:
            api_key = os.environ.get("DEFACTO_API_KEY")
            if api_key:
                return {
                    "is_enabled": True,
                    "api_key": api_key,
                    "webhook_secret": os.environ.get("DEFACTO_WEBHOOK_SECRET"),
                    "sandbox": os.environ.get("DEFACTO_SANDBOX", "true").lower() == "true",
                }

        elif provider_type == FinanceProviderType.SOLARIS:
            client_id = os.environ.get("SOLARIS_CLIENT_ID")
            client_secret = os.environ.get("SOLARIS_CLIENT_SECRET")
            if client_id and client_secret:
                return {
                    "is_enabled": True,
                    "api_key": client_id,
                    "api_secret": client_secret,
                    "webhook_secret": os.environ.get("SOLARIS_WEBHOOK_SECRET"),
                    "sandbox": os.environ.get("SOLARIS_SANDBOX", "true").lower() == "true",
                }

        return None

    def _create_provider(
        self,
        provider_type: FinanceProviderType,
        config: dict,
    ) -> Optional[BaseFinanceProvider]:
        """
        Crée une instance de provider avec la configuration.

        Args:
            provider_type: Type de provider
            config: Configuration

        Returns:
            Instance du provider
        """
        try:
            if provider_type == FinanceProviderType.SWAN:
                return SwanProvider(
                    tenant_id=self.tenant_id,
                    api_key=config.get("api_key"),
                    project_id=config.get("project_id"),
                    webhook_secret=config.get("webhook_secret"),
                    sandbox=config.get("sandbox", True),
                )

            elif provider_type == FinanceProviderType.NMI:
                return NMIProvider(
                    tenant_id=self.tenant_id,
                    api_key=config.get("api_key"),
                    webhook_secret=config.get("webhook_secret"),
                    sandbox=config.get("sandbox", True),
                )

            elif provider_type == FinanceProviderType.DEFACTO:
                return DefactoProvider(
                    tenant_id=self.tenant_id,
                    api_key=config.get("api_key"),
                    webhook_secret=config.get("webhook_secret"),
                    sandbox=config.get("sandbox", True),
                )

            elif provider_type == FinanceProviderType.SOLARIS:
                return SolarisProvider(
                    tenant_id=self.tenant_id,
                    api_key=config.get("api_secret"),  # client_secret
                    client_id=config.get("api_key"),  # client_id
                    webhook_secret=config.get("webhook_secret"),
                    sandbox=config.get("sandbox", True),
                )

            self._logger.warning(f"Provider {provider_type.value} non implémenté")
            return None

        except Exception as e:
            self._logger.error(f"Erreur création provider {provider_type.value}: {e}")
            return None

    async def list_available_providers(self) -> list[dict]:
        """
        Liste les providers disponibles pour le tenant.

        Returns:
            Liste des providers avec leur statut
        """
        providers = []

        for provider_type in FinanceProviderType:
            config = self._get_provider_config(provider_type)

            providers.append({
                "type": provider_type.value,
                "name": self._get_provider_name(provider_type),
                "configured": config is not None,
                "enabled": config.get("is_enabled", False) if config else False,
                "sandbox": config.get("sandbox", True) if config else True,
            })

        return providers

    async def health_check_all(self) -> dict[str, FinanceResult]:
        """
        Vérifie la santé de tous les providers configurés.

        Returns:
            Dict avec les résultats par provider
        """
        results = {}

        for provider_type in FinanceProviderType:
            provider = await self.get_provider(provider_type)
            if provider:
                try:
                    results[provider_type.value] = await provider.health_check()
                except Exception as e:
                    results[provider_type.value] = FinanceResult.fail(
                        error=FinanceError(
                            code=FinanceErrorCode.INTERNAL_ERROR,
                            message=str(e),
                        ),
                        provider=provider_type.value,
                    )

        return results

    async def close_all(self) -> None:
        """Ferme tous les providers ouverts."""
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as e:
                self._logger.warning(f"Erreur fermeture provider: {e}")

        self._providers.clear()

    def _get_provider_name(self, provider_type: FinanceProviderType) -> str:
        """Retourne le nom lisible d'un provider."""
        names = {
            FinanceProviderType.SWAN: "Swan (Open Banking)",
            FinanceProviderType.NMI: "NMI (Paiements)",
            FinanceProviderType.DEFACTO: "Defacto (Affacturage)",
            FinanceProviderType.SOLARIS: "Solaris Bank (Crédit)",
        }
        return names.get(provider_type, provider_type.value)

    async def __aenter__(self) -> "FinanceProviderRegistry":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.close_all()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_finance_provider_registry(
    db: Session,
    tenant_id: str
) -> FinanceProviderRegistry:
    """
    Factory pour créer un registry de providers finance.

    Usage:
        registry = get_finance_provider_registry(db, context.tenant_id)
        swan = await registry.get_provider(FinanceProviderType.SWAN)

    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant

    Returns:
        Instance de FinanceProviderRegistry
    """
    return FinanceProviderRegistry(tenant_id=tenant_id, db=db)
