"""
AZALS MODULE - Auto-Enrichment - Base Provider
===============================================

Classe abstraite pour tous les fournisseurs d'enrichissement.
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from app.core.cache import get_cache, CacheTTL

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Resultat standardise d'une requete d'enrichissement."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0          # 0.0-1.0
    source: str = ""
    cached: bool = False
    error: Optional[str] = None
    response_time_ms: int = 0
    suggestions: list[dict[str, Any]] = field(default_factory=list)  # Pour autocomplete


class BaseProvider(ABC):
    """
    Classe abstraite pour tous les fournisseurs d'enrichissement.

    Chaque provider doit implementer:
    - lookup(): Effectuer la recherche API
    - map_to_entity(): Mapper la reponse aux champs de l'entite
    """

    PROVIDER_NAME: str = "base"
    BASE_URL: str = ""
    DEFAULT_TIMEOUT: float = 10.0
    CACHE_TTL: int = CacheTTL.HOUR  # 1 heure par defaut

    def __init__(self, tenant_id: str):
        """
        Initialise le provider.

        Args:
            tenant_id: ID du tenant pour isolation et cache
        """
        self.tenant_id = tenant_id
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """
        Initialisation lazy du client HTTP.
        Reutilise le meme client pour connection pooling.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.DEFAULT_TIMEOUT,
                headers=self._get_headers(),
                follow_redirects=True,
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """
        Headers HTTP par defaut.
        A surcharger pour ajouter des headers specifiques (API keys, etc).
        """
        return {
            "Accept": "application/json",
            "User-Agent": "AZALSCORE-ERP/1.0 (contact@azalscore.com)",
        }

    def _cache_key(self, lookup_type: str, lookup_value: str) -> str:
        """
        Genere une cle de cache unique pour cette recherche.

        Format: azals:enrichment:{tenant}:{provider}:{type}:{hash}
        """
        # Hash la valeur pour eviter les cles trop longues
        value_hash = hashlib.md5(lookup_value.encode()).hexdigest()[:12]
        return f"azals:enrichment:{self.tenant_id}:{self.PROVIDER_NAME}:{lookup_type}:{value_hash}"

    async def lookup_with_cache(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Recherche avec cache.
        Verifie le cache avant d'appeler l'API.

        Args:
            lookup_type: Type de recherche (siret, barcode, address)
            lookup_value: Valeur a rechercher

        Returns:
            EnrichmentResult avec les donnees ou erreur
        """
        cache = get_cache()
        cache_key = self._cache_key(lookup_type, lookup_value)

        # Verifier le cache
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"[ENRICHMENT] Cache hit: {cache_key}")
                return EnrichmentResult(
                    success=True,
                    data=data.get("data", {}),
                    confidence=data.get("confidence", 1.0),
                    source=self.PROVIDER_NAME,
                    cached=True,
                    suggestions=data.get("suggestions", []),
                )
        except Exception as e:
            logger.warning(f"[ENRICHMENT] Cache read error: {e}")

        # Appeler l'API
        result = await self.lookup(lookup_type, lookup_value)

        # Mettre en cache si succes
        if result.success and not result.error:
            try:
                cache_data = json.dumps({
                    "data": result.data,
                    "confidence": result.confidence,
                    "suggestions": result.suggestions,
                })
                cache.set(cache_key, cache_data, self.CACHE_TTL)
                logger.debug(f"[ENRICHMENT] Cached: {cache_key} (TTL: {self.CACHE_TTL}s)")
            except Exception as e:
                logger.warning(f"[ENRICHMENT] Cache write error: {e}")

        return result

    @abstractmethod
    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Effectue la recherche API.

        Args:
            lookup_type: Type de recherche
            lookup_value: Valeur a rechercher

        Returns:
            EnrichmentResult
        """
        pass

    @abstractmethod
    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse API aux champs de l'entite.

        Args:
            entity_type: Type d'entite (contact, product)
            api_data: Donnees brutes de l'API

        Returns:
            Dict de champs mappes {field_name: value}
        """
        pass

    def _measure_time(self, start_time: float) -> int:
        """Calcule le temps de reponse en ms."""
        return int((time.time() - start_time) * 1000)

    async def close(self):
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
