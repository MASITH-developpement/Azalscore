"""
AZALS MODULE - Auto-Enrichment - Service
=========================================

Service principal d'orchestration des enrichissements.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import get_cache, CacheTTL

from .models import (
    EnrichmentAction,
    EnrichmentHistory,
    EnrichmentProvider,
    EnrichmentProviderConfig,
    EnrichmentRateLimit,
    EnrichmentStatus,
    EntityType,
    LookupType,
    PROVIDER_RATE_LIMITS,
)
from .providers import (
    BaseProvider,
    INSEEProvider,
    AdresseGouvProvider,
    OpenFoodFactsProvider,
    OpenBeautyFactsProvider,
    OpenPetFoodFactsProvider,
    PappersProvider,
    VIESProvider,
    OpenCorporatesProvider,
)
from .providers.base import EnrichmentResult

logger = logging.getLogger(__name__)


# ============================================================================
# PROVIDER REGISTRY
# ============================================================================

# Mapping lookup_type -> providers (ordre de priorite)
# Note: L'ordre peut etre personnalise par tenant via EnrichmentProviderConfig
PROVIDER_REGISTRY: dict[LookupType, list[EnrichmentProvider]] = {
    LookupType.SIRET: [EnrichmentProvider.INSEE, EnrichmentProvider.OPENCORPORATES],
    LookupType.SIREN: [EnrichmentProvider.INSEE, EnrichmentProvider.OPENCORPORATES],
    LookupType.NAME: [EnrichmentProvider.INSEE, EnrichmentProvider.OPENCORPORATES],  # Recherche par nom
    LookupType.ADDRESS: [EnrichmentProvider.ADRESSE_GOUV],
    LookupType.BARCODE: [
        EnrichmentProvider.OPENFOODFACTS,
        EnrichmentProvider.OPENBEAUTYFACTS,
        EnrichmentProvider.OPENPETFOODFACTS,
    ],
    LookupType.VAT_NUMBER: [EnrichmentProvider.VIES],  # Validation TVA UE
    LookupType.RISK: [EnrichmentProvider.PAPPERS, EnrichmentProvider.OPENCORPORATES],  # Analyse de risque
}

# Mapping entity_type -> lookup_types valides
ENTITY_LOOKUP_MAPPING: dict[EntityType, list[LookupType]] = {
    EntityType.CONTACT: [LookupType.SIRET, LookupType.SIREN, LookupType.NAME, LookupType.ADDRESS, LookupType.VAT_NUMBER, LookupType.RISK],
    EntityType.PRODUCT: [LookupType.BARCODE],
}


# ============================================================================
# SERVICE
# ============================================================================

class EnrichmentService:
    """
    Service principal d'orchestration des enrichissements.

    Fonctionnalites:
    - Recherche multi-providers avec fallback (pour barcode)
    - Rate limiting par provider
    - Cache au niveau provider et service
    - Historique complet pour audit
    """

    def __init__(self, db: Session, tenant_id: str):
        """
        Initialise le service.

        Args:
            db: Session SQLAlchemy
            tenant_id: ID du tenant pour isolation
        """
        self.db = db
        self.tenant_id = tenant_id
        self._providers: dict[EnrichmentProvider, BaseProvider] = {}
        self._provider_configs: dict[EnrichmentProvider, EnrichmentProviderConfig] = {}

    def _load_provider_config(self, provider: EnrichmentProvider) -> Optional[EnrichmentProviderConfig]:
        """
        Charge la configuration du provider depuis la DB.

        Args:
            provider: Type de provider

        Returns:
            Config du provider ou None
        """
        if provider not in self._provider_configs:
            config = self.db.query(EnrichmentProviderConfig).filter(
                EnrichmentProviderConfig.tenant_id == self.tenant_id,
                EnrichmentProviderConfig.provider == provider,
            ).first()
            if config:
                self._provider_configs[provider] = config
        return self._provider_configs.get(provider)

    def _is_provider_enabled(self, provider: EnrichmentProvider) -> bool:
        """
        Verifie si un provider est active pour ce tenant.

        Args:
            provider: Type de provider

        Returns:
            True si active (ou pas de config = actif par defaut)
        """
        config = self._load_provider_config(provider)
        if config is None:
            return True  # Actif par defaut si pas de config
        return config.is_enabled

    def _get_provider_api_key(self, provider: EnrichmentProvider) -> Optional[str]:
        """
        Recupere la cle API du provider depuis la config.

        Args:
            provider: Type de provider

        Returns:
            Cle API ou None
        """
        config = self._load_provider_config(provider)
        if config:
            return config.api_key
        return None

    def _get_provider(self, provider: EnrichmentProvider) -> Optional[BaseProvider]:
        """
        Initialisation lazy des providers.

        Args:
            provider: Type de provider

        Returns:
            Instance du provider ou None
        """
        # Verifier si le provider est active
        if not self._is_provider_enabled(provider):
            logger.debug(f"[ENRICHMENT] Provider {provider.value} desactive pour tenant {self.tenant_id}")
            return None

        if provider not in self._providers:
            # Recuperer la cle API si configuree
            api_key = self._get_provider_api_key(provider)

            if provider == EnrichmentProvider.INSEE:
                self._providers[provider] = INSEEProvider(self.tenant_id)
            elif provider == EnrichmentProvider.ADRESSE_GOUV:
                self._providers[provider] = AdresseGouvProvider(self.tenant_id)
            elif provider == EnrichmentProvider.OPENFOODFACTS:
                self._providers[provider] = OpenFoodFactsProvider(self.tenant_id)
            elif provider == EnrichmentProvider.OPENBEAUTYFACTS:
                self._providers[provider] = OpenBeautyFactsProvider(self.tenant_id)
            elif provider == EnrichmentProvider.OPENPETFOODFACTS:
                self._providers[provider] = OpenPetFoodFactsProvider(self.tenant_id)
            elif provider == EnrichmentProvider.PAPPERS:
                self._providers[provider] = PappersProvider(self.tenant_id, api_key=api_key)
            elif provider == EnrichmentProvider.VIES:
                self._providers[provider] = VIESProvider(self.tenant_id)
            elif provider == EnrichmentProvider.OPENCORPORATES:
                self._providers[provider] = OpenCorporatesProvider(self.tenant_id, api_key=api_key)
            # Providers payants non implementes
            else:
                logger.warning(f"[ENRICHMENT] Provider {provider.value} non implemente")
                return None

        return self._providers.get(provider)

    async def enrich(
        self,
        lookup_type: LookupType,
        lookup_value: str,
        entity_type: EntityType = EntityType.CONTACT,
        entity_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> dict[str, Any]:
        """
        Point d'entree principal pour l'enrichissement.

        Args:
            lookup_type: Type de recherche (siret, barcode, address)
            lookup_value: Valeur a rechercher
            entity_type: Type d'entite cible (contact, product)
            entity_id: ID de l'entite existante (optionnel)
            user_id: ID de l'utilisateur effectuant la recherche

        Returns:
            Dict avec enriched_fields, confidence, source, suggestions, etc.
        """
        # Valider le lookup_type pour l'entity_type
        valid_lookups = ENTITY_LOOKUP_MAPPING.get(entity_type, [])
        if lookup_type not in valid_lookups:
            raise ValueError(
                f"Type de recherche '{lookup_type.value}' invalide pour '{entity_type.value}'. "
                f"Types valides: {[lt.value for lt in valid_lookups]}"
            )

        # Recuperer les providers pour ce type de recherche
        providers = PROVIDER_REGISTRY.get(lookup_type, [])
        if not providers:
            raise ValueError(f"Aucun provider pour le type: {lookup_type.value}")

        # Essayer les providers dans l'ordre (fallback pour barcode)
        last_error = None

        for provider_enum in providers:
            # Verifier le rate limit
            if not await self._check_rate_limit(provider_enum):
                logger.warning(f"[ENRICHMENT] Rate limit atteint pour {provider_enum.value}")
                last_error = "Limite de requetes atteinte"
                continue

            # Obtenir le provider
            provider = self._get_provider(provider_enum)
            if not provider:
                continue

            # Effectuer la recherche avec cache
            result = await provider.lookup_with_cache(
                lookup_type.value,
                lookup_value
            )

            # Enregistrer dans l'historique
            history = self._record_history(
                entity_type=entity_type,
                entity_id=entity_id,
                lookup_type=lookup_type,
                lookup_value=lookup_value,
                provider=provider_enum,
                result=result,
                user_id=user_id,
            )

            # Incrementer le compteur de rate limit
            await self._increment_rate_limit(provider_enum)

            if result.success:
                # Mapper les champs pour l'entite
                enriched_fields = provider.map_to_entity(entity_type.value, result.data)

                # Recuperer les suggestions pour address et name
                suggestions = []
                if lookup_type in (LookupType.ADDRESS, LookupType.NAME) and hasattr(provider, 'get_suggestions'):
                    suggestions = provider.get_suggestions(result.data)

                logger.info(
                    f"[ENRICHMENT] Succes: {lookup_type.value}='{lookup_value[:20]}...' "
                    f"via {provider_enum.value} ({result.response_time_ms}ms)"
                )

                return {
                    "success": True,
                    "enriched_fields": enriched_fields,
                    "confidence": result.confidence,
                    "source": result.source,
                    "cached": result.cached,
                    "history_id": str(history.id),
                    "suggestions": [s if isinstance(s, dict) else s.__dict__ for s in suggestions],
                    "error": None,
                }

            # Conserver la derniere erreur
            last_error = result.error

        # Tous les providers ont echoue
        logger.warning(
            f"[ENRICHMENT] Echec: {lookup_type.value}='{lookup_value[:20]}...' - {last_error}"
        )

        return {
            "success": False,
            "enriched_fields": {},
            "confidence": 0.0,
            "source": None,
            "cached": False,
            "history_id": None,
            "suggestions": [],
            "error": last_error or "Aucun resultat trouve",
        }

    async def _check_rate_limit(self, provider: EnrichmentProvider) -> bool:
        """
        Verifie si on est dans les limites de taux.

        Args:
            provider: Provider a verifier

        Returns:
            True si OK, False si limite atteinte
        """
        cache = get_cache()

        # Cles de cache pour les compteurs
        minute_key = f"ratelimit:{self.tenant_id}:{provider.value}:minute"
        day_key = f"ratelimit:{self.tenant_id}:{provider.value}:day"

        # Obtenir ou creer la config de limites
        limits = self._get_or_create_rate_limit(provider)

        if not limits.is_enabled:
            return False

        # Verifier limite par minute
        minute_count_str = cache.get(minute_key)
        minute_count = int(minute_count_str) if minute_count_str else 0
        if minute_count >= limits.requests_per_minute:
            return False

        # Verifier limite par jour
        day_count_str = cache.get(day_key)
        day_count = int(day_count_str) if day_count_str else 0
        if day_count >= limits.requests_per_day:
            return False

        return True

    async def _increment_rate_limit(self, provider: EnrichmentProvider):
        """Incremente les compteurs de rate limit."""
        cache = get_cache()

        minute_key = f"ratelimit:{self.tenant_id}:{provider.value}:minute"
        day_key = f"ratelimit:{self.tenant_id}:{provider.value}:day"

        # Incrementer avec TTL
        cache.incr(minute_key, CacheTTL.RATE_LIMIT)  # 60 secondes
        cache.incr(day_key, CacheTTL.DAY)  # 24 heures

    def _get_or_create_rate_limit(self, provider: EnrichmentProvider) -> EnrichmentRateLimit:
        """Obtient ou cree la config de rate limit pour un provider."""
        limits = self.db.query(EnrichmentRateLimit).filter(
            EnrichmentRateLimit.tenant_id == self.tenant_id,
            EnrichmentRateLimit.provider == provider,
        ).first()

        if not limits:
            # Utiliser les valeurs par defaut
            defaults = PROVIDER_RATE_LIMITS.get(provider, {
                "requests_per_minute": 60,
                "requests_per_day": 1000,
            })

            limits = EnrichmentRateLimit(
                tenant_id=self.tenant_id,
                provider=provider,
                requests_per_minute=defaults["requests_per_minute"],
                requests_per_day=defaults["requests_per_day"],
            )
            self.db.add(limits)
            self.db.commit()
            self.db.refresh(limits)

        return limits

    def _record_history(
        self,
        entity_type: EntityType,
        entity_id: Optional[UUID],
        lookup_type: LookupType,
        lookup_value: str,
        provider: EnrichmentProvider,
        result: EnrichmentResult,
        user_id: Optional[UUID],
    ) -> EnrichmentHistory:
        """Enregistre la tentative d'enrichissement dans l'historique."""
        # Determiner le statut
        if result.success:
            status = EnrichmentStatus.SUCCESS
        elif "not found" in (result.error or "").lower() or "non trouve" in (result.error or "").lower():
            status = EnrichmentStatus.NOT_FOUND
        elif "rate limit" in (result.error or "").lower() or "limite" in (result.error or "").lower():
            status = EnrichmentStatus.RATE_LIMITED
        elif result.error:
            status = EnrichmentStatus.ERROR
        else:
            status = EnrichmentStatus.PENDING

        history = EnrichmentHistory(
            tenant_id=self.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            lookup_type=lookup_type,
            lookup_value=lookup_value,
            provider=provider,
            status=status,
            response_data=result.data,
            confidence_score=Decimal(str(result.confidence)),
            api_response_time_ms=result.response_time_ms,
            cached=result.cached,
            error_message=result.error,
            created_by=user_id,
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def accept_enrichment(
        self,
        history_id: UUID,
        accepted_fields: list[str],
        rejected_fields: list[str],
        user_id: UUID,
    ) -> EnrichmentHistory:
        """
        Enregistre l'acceptation/rejet des donnees enrichies.

        Args:
            history_id: ID de l'historique
            accepted_fields: Champs acceptes
            rejected_fields: Champs rejetes
            user_id: ID de l'utilisateur

        Returns:
            Historique mis a jour
        """
        history = self.db.query(EnrichmentHistory).filter(
            EnrichmentHistory.id == history_id,
            EnrichmentHistory.tenant_id == self.tenant_id,
        ).first()

        if not history:
            raise ValueError("Historique d'enrichissement non trouve")

        # Determiner l'action
        if accepted_fields and rejected_fields:
            history.action = EnrichmentAction.PARTIAL
        elif accepted_fields:
            history.action = EnrichmentAction.ACCEPTED
        else:
            history.action = EnrichmentAction.REJECTED

        history.accepted_fields = accepted_fields
        history.rejected_fields = rejected_fields
        history.action_at = datetime.utcnow()
        history.action_by = user_id

        # Mapper les champs enrichis si pas encore fait
        if not history.enriched_fields and history.response_data:
            provider = self._get_provider(history.provider)
            if provider:
                history.enriched_fields = provider.map_to_entity(
                    history.entity_type.value,
                    history.response_data
                )

        self.db.commit()
        self.db.refresh(history)

        logger.info(
            f"[ENRICHMENT] Enrichissement {history_id} "
            f"{'accepte' if history.action == EnrichmentAction.ACCEPTED else 'rejete'} "
            f"par {user_id}"
        )

        return history

    def get_history(
        self,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[UUID] = None,
        provider: Optional[EnrichmentProvider] = None,
        status: Optional[EnrichmentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[EnrichmentHistory], int]:
        """
        Recupere l'historique des enrichissements.

        Args:
            entity_type: Filtrer par type d'entite
            entity_id: Filtrer par ID d'entite
            provider: Filtrer par provider
            status: Filtrer par statut
            limit: Nombre max de resultats
            offset: Offset pour pagination

        Returns:
            (liste, total)
        """
        query = self.db.query(EnrichmentHistory).filter(
            EnrichmentHistory.tenant_id == self.tenant_id
        )

        if entity_type:
            query = query.filter(EnrichmentHistory.entity_type == entity_type)
        if entity_id:
            query = query.filter(EnrichmentHistory.entity_id == entity_id)
        if provider:
            query = query.filter(EnrichmentHistory.provider == provider)
        if status:
            query = query.filter(EnrichmentHistory.status == status)

        total = query.count()

        history = query.order_by(
            EnrichmentHistory.created_at.desc()
        ).offset(offset).limit(limit).all()

        return history, total

    def get_stats(self, days: int = 30) -> dict[str, Any]:
        """
        Recupere les statistiques d'enrichissement.

        Args:
            days: Nombre de jours a analyser

        Returns:
            Dict de statistiques
        """
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        base_filter = [
            EnrichmentHistory.tenant_id == self.tenant_id,
            EnrichmentHistory.created_at >= start_date,
        ]

        # Total lookups
        total = self.db.query(func.count(EnrichmentHistory.id)).filter(
            *base_filter
        ).scalar() or 0

        # Successful
        successful = self.db.query(func.count(EnrichmentHistory.id)).filter(
            *base_filter,
            EnrichmentHistory.status == EnrichmentStatus.SUCCESS,
        ).scalar() or 0

        # Cached
        cached = self.db.query(func.count(EnrichmentHistory.id)).filter(
            *base_filter,
            EnrichmentHistory.cached == True,
        ).scalar() or 0

        # Accepted
        accepted = self.db.query(func.count(EnrichmentHistory.id)).filter(
            *base_filter,
            EnrichmentHistory.action == EnrichmentAction.ACCEPTED,
        ).scalar() or 0

        # Rejected
        rejected = self.db.query(func.count(EnrichmentHistory.id)).filter(
            *base_filter,
            EnrichmentHistory.action == EnrichmentAction.REJECTED,
        ).scalar() or 0

        # Avg confidence
        avg_confidence = self.db.query(
            func.avg(EnrichmentHistory.confidence_score)
        ).filter(
            *base_filter,
            EnrichmentHistory.status == EnrichmentStatus.SUCCESS,
        ).scalar()

        # Avg response time
        avg_response_time = self.db.query(
            func.avg(EnrichmentHistory.api_response_time_ms)
        ).filter(
            *base_filter,
            EnrichmentHistory.cached == False,
        ).scalar()

        # By provider
        by_provider = {}
        provider_counts = self.db.query(
            EnrichmentHistory.provider,
            func.count(EnrichmentHistory.id)
        ).filter(*base_filter).group_by(EnrichmentHistory.provider).all()
        for provider, count in provider_counts:
            by_provider[provider.value] = count

        # By lookup type
        by_lookup_type = {}
        lookup_counts = self.db.query(
            EnrichmentHistory.lookup_type,
            func.count(EnrichmentHistory.id)
        ).filter(*base_filter).group_by(EnrichmentHistory.lookup_type).all()
        for lt, count in lookup_counts:
            by_lookup_type[lt.value] = count

        return {
            "total_lookups": total,
            "successful_lookups": successful,
            "cached_lookups": cached,
            "accepted_enrichments": accepted,
            "rejected_enrichments": rejected,
            "avg_confidence": float(avg_confidence) if avg_confidence else 0.0,
            "avg_response_time_ms": float(avg_response_time) if avg_response_time else 0.0,
            "by_provider": by_provider,
            "by_lookup_type": by_lookup_type,
        }

    async def close(self):
        """Ferme tous les clients HTTP des providers."""
        for provider in self._providers.values():
            await provider.close()


def get_enrichment_service(db: Session, tenant_id: str) -> EnrichmentService:
    """Factory pour EnrichmentService."""
    return EnrichmentService(db, tenant_id)
