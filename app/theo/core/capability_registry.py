"""
THÉO — Registre de Capacités Dynamique
======================================

Principe anti-obsolescence:
- Les capacités sont abstraites (ex: "raisonnement", "navigation")
- Les implémentations sont interchangeables (GPT, Claude, Maps...)
- Le pipeline ne change jamais, seuls les providers évoluent

Aucune IA n'est figée. Toute dépendance est remplaçable.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Protocol, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================
# CAPACITÉS ABSTRAITES
# ============================================================

class CapabilityType(str, Enum):
    """Capacités abstraites supportées par Théo."""

    # Information & Recherche
    INFORMATION = "information"      # Répondre à une question factuelle
    RECHERCHE = "recherche"          # Rechercher sur le web
    SYNTHESE = "synthese"            # Résumer un contenu
    RAISONNEMENT = "raisonnement"    # Analyser, déduire

    # Navigation & Mobilité
    NAVIGATION = "navigation"        # Itinéraire, directions
    TRAFIC = "trafic"               # État du trafic

    # Environnement
    METEO = "meteo"                  # Prévisions météo

    # Actions Métier AZALSCORE
    DEVIS = "devis"                  # Créer un devis
    FACTURE = "facture"              # Créer une facture
    TICKET = "ticket"                # Créer un ticket
    NOTE = "note"                    # Enregistrer une note
    CRM = "crm"                      # Actions client
    PLANNING = "planning"            # Agenda, rendez-vous
    AUTOMATISATION = "automatisation" # Actions programmées

    # Conversation
    CONVERSATION = "conversation"    # Discussion générale
    CLARIFICATION = "clarification"  # Demander des précisions


# ============================================================
# PROTOCOLE PROVIDER
# ============================================================

@runtime_checkable
class CapabilityProvider(Protocol):
    """Interface que tout provider de capacité doit implémenter."""

    @property
    def name(self) -> str:
        """Nom du provider (ex: 'openai', 'azalscore.invoicing')."""
        ...

    @property
    def capabilities(self) -> List[CapabilityType]:
        """Liste des capacités fournies."""
        ...

    async def execute(
        self,
        capability: CapabilityType,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute une capacité.

        Args:
            capability: Type de capacité demandée
            params: Paramètres extraits de l'intention
            context: Contexte (session, user, tenant, etc.)

        Returns:
            Résultat de l'exécution avec au minimum:
            - success: bool
            - result: Any
            - message: str (pour synthèse vocale)
        """
        ...

    async def health_check(self) -> bool:
        """Vérifie si le provider est disponible."""
        ...


# ============================================================
# CONFIGURATION PROVIDER
# ============================================================

@dataclass
class ProviderConfig:
    """Configuration d'un provider enregistré."""

    provider: CapabilityProvider
    priority: int = 0                    # Plus élevé = prioritaire
    enabled: bool = True
    rate_limit: Optional[int] = None     # Appels par minute
    timeout_ms: int = 30000
    fallback_provider: Optional[str] = None
    last_health_check: Optional[datetime] = None
    is_healthy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# CAPACITÉ RÉSOLUE
# ============================================================

@dataclass
class Capability:
    """Capacité résolue avec son provider sélectionné."""

    type: CapabilityType
    provider_name: str
    provider: CapabilityProvider
    priority: int
    is_available: bool
    fallback: Optional[str] = None


# ============================================================
# REGISTRE DE CAPACITÉS
# ============================================================

class CapabilityRegistry:
    """
    Registre central des capacités et providers.

    Permet l'enregistrement dynamique de providers et la résolution
    de capacités vers le meilleur provider disponible.
    """

    def __init__(self):
        self._providers: Dict[str, ProviderConfig] = {}
        self._capability_index: Dict[CapabilityType, List[str]] = {
            cap: [] for cap in CapabilityType
        }
        self._default_providers: Dict[CapabilityType, str] = {}

    def register(
        self,
        provider: CapabilityProvider,
        priority: int = 0,
        enabled: bool = True,
        rate_limit: Optional[int] = None,
        timeout_ms: int = 30000,
        fallback_provider: Optional[str] = None,
        as_default_for: Optional[List[CapabilityType]] = None
    ) -> None:
        """
        Enregistre un provider de capacités.

        Args:
            provider: Instance du provider
            priority: Priorité (plus élevé = prioritaire)
            enabled: Activer immédiatement
            rate_limit: Limite d'appels par minute
            timeout_ms: Timeout en millisecondes
            fallback_provider: Nom du provider de fallback
            as_default_for: Définir comme défaut pour ces capacités
        """
        name = provider.name

        if name in self._providers:
            logger.warning(f"Provider '{name}' already registered, updating")

        config = ProviderConfig(
            provider=provider,
            priority=priority,
            enabled=enabled,
            rate_limit=rate_limit,
            timeout_ms=timeout_ms,
            fallback_provider=fallback_provider
        )

        self._providers[name] = config

        # Indexer par capacité
        for capability in provider.capabilities:
            if name not in self._capability_index[capability]:
                self._capability_index[capability].append(name)
                # Trier par priorité (descendant)
                self._capability_index[capability].sort(
                    key=lambda n: self._providers[n].priority,
                    reverse=True
                )

        # Définir comme défaut si demandé
        if as_default_for:
            for cap in as_default_for:
                self._default_providers[cap] = name

        logger.info(
            f"Registered provider '{name}' with capabilities: "
            f"{[c.value for c in provider.capabilities]}"
        )

    def unregister(self, provider_name: str) -> bool:
        """Désenregistre un provider."""
        if provider_name not in self._providers:
            return False

        # Retirer de l'index
        config = self._providers[provider_name]
        for capability in config.provider.capabilities:
            if provider_name in self._capability_index[capability]:
                self._capability_index[capability].remove(provider_name)

        # Retirer des défauts
        for cap, name in list(self._default_providers.items()):
            if name == provider_name:
                del self._default_providers[cap]

        del self._providers[provider_name]
        logger.info(f"Unregistered provider '{provider_name}'")
        return True

    def resolve(
        self,
        capability: CapabilityType,
        prefer_provider: Optional[str] = None
    ) -> Optional[Capability]:
        """
        Résout une capacité vers le meilleur provider disponible.

        Args:
            capability: Type de capacité demandée
            prefer_provider: Nom du provider préféré (optionnel)

        Returns:
            Capability résolue ou None si indisponible
        """
        # 1. Provider préféré explicite
        if prefer_provider and prefer_provider in self._providers:
            config = self._providers[prefer_provider]
            if config.enabled and config.is_healthy:
                if capability in config.provider.capabilities:
                    return Capability(
                        type=capability,
                        provider_name=prefer_provider,
                        provider=config.provider,
                        priority=config.priority,
                        is_available=True,
                        fallback=config.fallback_provider
                    )

        # 2. Provider par défaut pour cette capacité
        if capability in self._default_providers:
            default_name = self._default_providers[capability]
            if default_name in self._providers:
                config = self._providers[default_name]
                if config.enabled and config.is_healthy:
                    return Capability(
                        type=capability,
                        provider_name=default_name,
                        provider=config.provider,
                        priority=config.priority,
                        is_available=True,
                        fallback=config.fallback_provider
                    )

        # 3. Premier provider disponible par priorité
        for provider_name in self._capability_index[capability]:
            config = self._providers[provider_name]
            if config.enabled and config.is_healthy:
                return Capability(
                    type=capability,
                    provider_name=provider_name,
                    provider=config.provider,
                    priority=config.priority,
                    is_available=True,
                    fallback=config.fallback_provider
                )

        # 4. Aucun provider disponible
        logger.warning(f"No available provider for capability '{capability.value}'")
        return None

    def get_all_capabilities(self) -> Dict[CapabilityType, List[str]]:
        """Retourne toutes les capacités et leurs providers."""
        return {
            cap: [
                name for name in providers
                if self._providers[name].enabled
            ]
            for cap, providers in self._capability_index.items()
            if providers
        }

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Retourne la configuration d'un provider."""
        return self._providers.get(name)

    def set_enabled(self, provider_name: str, enabled: bool) -> bool:
        """Active ou désactive un provider."""
        if provider_name not in self._providers:
            return False
        self._providers[provider_name].enabled = enabled
        logger.info(f"Provider '{provider_name}' {'enabled' if enabled else 'disabled'}")
        return True

    def set_healthy(self, provider_name: str, healthy: bool) -> bool:
        """Marque un provider comme sain ou non."""
        if provider_name not in self._providers:
            return False
        self._providers[provider_name].is_healthy = healthy
        self._providers[provider_name].last_health_check = datetime.utcnow()
        return True

    async def health_check_all(self) -> Dict[str, bool]:
        """Vérifie la santé de tous les providers."""
        results = {}
        for name, config in self._providers.items():
            try:
                healthy = await config.provider.health_check()
                self.set_healthy(name, healthy)
                results[name] = healthy
            except Exception as e:
                logger.error(f"Health check failed for '{name}': {e}")
                self.set_healthy(name, False)
                results[name] = False
        return results

    def status(self) -> Dict[str, Any]:
        """Retourne le statut complet du registre."""
        return {
            "providers": {
                name: {
                    "enabled": config.enabled,
                    "healthy": config.is_healthy,
                    "priority": config.priority,
                    "capabilities": [c.value for c in config.provider.capabilities],
                    "last_health_check": config.last_health_check.isoformat() if config.last_health_check else None
                }
                for name, config in self._providers.items()
            },
            "capabilities": {
                cap.value: providers
                for cap, providers in self.get_all_capabilities().items()
            },
            "defaults": {
                cap.value: name
                for cap, name in self._default_providers.items()
            }
        }


# ============================================================
# SINGLETON
# ============================================================

_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """Retourne l'instance singleton du registre."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry
