"""
AZALS MODULE - Auto-Enrichment - Adresse Gouv Provider
=======================================================

Provider pour l'API Adresse du gouvernement francais.
Autocomplete et geocodage d'adresses francaises.

API Documentation: https://adresse.data.gouv.fr/api-doc/adresse
"""

import logging
import time
from typing import Any

import httpx

from app.core.cache import CacheTTL

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class AdresseGouvProvider(BaseProvider):
    """
    Provider pour l'API Adresse du gouvernement francais.

    Fonctionnalites:
    - Autocomplete d'adresses (search)
    - Geocodage inverse (coordinates -> adresse)

    API gratuite, sans limite stricte (usage raisonnable).
    """

    PROVIDER_NAME = "adresse_gouv"
    BASE_URL = "https://api-adresse.data.gouv.fr"
    CACHE_TTL = CacheTTL.DAY  # 24h
    DEFAULT_TIMEOUT = 5.0  # API rapide

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Recherche d'adresse.

        Args:
            lookup_type: 'address' pour autocomplete, 'reverse' pour geocodage inverse
            lookup_value: Texte d'adresse ou "lat,lon"

        Returns:
            EnrichmentResult avec suggestions d'adresses
        """
        start_time = time.time()

        try:
            client = await self.get_client()

            if lookup_type == "address":
                # Autocomplete
                if len(lookup_value.strip()) < 3:
                    return EnrichmentResult(
                        success=False,
                        source=self.PROVIDER_NAME,
                        error="Minimum 3 caracteres requis",
                        response_time_ms=self._measure_time(start_time),
                    )

                response = await client.get(
                    "/search/",
                    params={
                        "q": lookup_value,
                        "limit": 5,
                        "autocomplete": 1,
                    }
                )

            elif lookup_type == "reverse":
                # Geocodage inverse - format: "lat,lon"
                try:
                    lat, lon = lookup_value.split(",")
                    lat = float(lat.strip())
                    lon = float(lon.strip())
                except (ValueError, AttributeError):
                    return EnrichmentResult(
                        success=False,
                        source=self.PROVIDER_NAME,
                        error="Format coordonnees invalide (attendu: 'lat,lon')",
                        response_time_ms=self._measure_time(start_time),
                    )

                response = await client.get(
                    "/reverse/",
                    params={"lat": lat, "lon": lon}
                )

            else:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error=f"Type de recherche non supporte: {lookup_type}",
                    response_time_ms=self._measure_time(start_time),
                )

            response_time = self._measure_time(start_time)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Aucune adresse trouvee",
                    response_time_ms=response_time,
                )

            # Extraire le score de confiance du premier resultat
            confidence = features[0].get("properties", {}).get("score", 0.5)

            # Construire la liste de suggestions
            suggestions = self._build_suggestions(features)

            logger.info(f"[ADRESSE] Lookup '{lookup_value[:30]}...' -> {len(features)} resultats ({response_time}ms)")

            return EnrichmentResult(
                success=True,
                data=data,
                confidence=confidence,
                source=self.PROVIDER_NAME,
                response_time_ms=response_time,
                suggestions=suggestions,
            )

        except httpx.TimeoutException:
            logger.warning(f"[ADRESSE] Timeout pour '{lookup_value[:30]}...'")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Timeout API Adresse",
                response_time_ms=self._measure_time(start_time),
            )

        except httpx.HTTPError as e:
            logger.error(f"[ADRESSE] Erreur HTTP: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur HTTP: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

        except Exception as e:
            logger.exception(f"[ADRESSE] Erreur inattendue: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def _build_suggestions(self, features: list) -> list[dict[str, Any]]:
        """
        Construit la liste de suggestions d'adresses.

        Args:
            features: Liste de features GeoJSON

        Returns:
            Liste de suggestions formatees
        """
        suggestions = []

        for feature in features:
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            suggestions.append({
                "label": props.get("label", ""),
                "address_line1": props.get("name", ""),
                "house_number": props.get("housenumber", ""),
                "street": props.get("street", ""),
                "postal_code": props.get("postcode", ""),
                "city": props.get("city", ""),
                "context": props.get("context", ""),  # Departement, region
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if coords else None,
                "score": props.get("score", 0),
                "type": props.get("type"),  # housenumber, street, municipality
                "importance": props.get("importance", 0),
            })

        return suggestions

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse API Adresse aux champs Contact.
        Utilise le premier (meilleur) resultat.

        Args:
            entity_type: Type d'entite (contact, product)
            api_data: Reponse brute de l'API

        Returns:
            Dict des champs mappes
        """
        features = api_data.get("features", [])
        if not features:
            return {}

        props = features[0].get("properties", {})
        coords = features[0].get("geometry", {}).get("coordinates", [])

        # Construire l'adresse complete
        address_line1 = props.get("name", "")

        # Extraire departement et region du contexte
        context = props.get("context", "")
        context_parts = [p.strip() for p in context.split(",")]
        department = context_parts[0] if context_parts else ""
        region = context_parts[-1] if len(context_parts) > 1 else ""

        return {
            # Champs adresse standard
            "address_line1": address_line1,
            "postal_code": props.get("postcode", ""),
            "city": props.get("city", ""),
            "country": "France",
            "country_code": "FR",

            # Coordonnees GPS
            "latitude": coords[1] if len(coords) > 1 else None,
            "longitude": coords[0] if coords else None,

            # Metadonnees (prefixees _)
            "_address_score": props.get("score"),
            "_address_type": props.get("type"),
            "_address_department": department,
            "_address_region": region,
            "_address_city_code": props.get("citycode", ""),
        }

    def get_suggestions(self, api_data: dict) -> list[dict[str, Any]]:
        """
        Retourne toutes les suggestions pour l'autocomplete.

        Args:
            api_data: Reponse brute de l'API

        Returns:
            Liste de suggestions formatees
        """
        features = api_data.get("features", [])
        return self._build_suggestions(features)
