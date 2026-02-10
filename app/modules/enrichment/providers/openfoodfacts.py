"""
AZALS MODULE - Auto-Enrichment - Open Food/Beauty/Pet Facts Providers
======================================================================

Providers pour les APIs Open Facts (code-barres produits).

- Open Food Facts: Produits alimentaires
- Open Beauty Facts: Produits cosmetiques
- Open Pet Food Facts: Produits animaliers

API Documentation: https://world.openfoodfacts.org/data
"""

import logging
import re
import time
from typing import Any

import httpx

from app.core.cache import CacheTTL

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class OpenFactsBaseProvider(BaseProvider):
    """
    Classe de base pour tous les providers Open Facts.
    Partage la logique commune de lookup par code-barres.
    """

    PROVIDER_NAME = "openfacts"
    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    CACHE_TTL = 604800  # 7 jours - produits tres stables
    DEFAULT_TIMEOUT = 10.0

    # Champs a demander a l'API
    PRODUCT_FIELDS = [
        "code",
        "product_name",
        "product_name_fr",
        "brands",
        "generic_name",
        "generic_name_fr",
        "quantity",
        "image_url",
        "image_front_url",
        "image_front_small_url",
        "categories",
        "categories_tags",
        "nutriscore_grade",
        "ecoscore_grade",
        "nova_group",
        "packaging",
        "origins",
        "manufacturing_places",
        "ingredients_text",
        "ingredients_text_fr",
        "allergens",
        "labels",
    ]

    def _validate_barcode(self, barcode: str) -> tuple[bool, str]:
        """
        Valide le format du code-barres.
        Accepte EAN-8, EAN-13, UPC-A, UPC-E.

        Returns:
            (is_valid, cleaned_value)
        """
        cleaned = re.sub(r'[^0-9]', '', barcode)

        # EAN-8, EAN-13, UPC-A (12), UPC-E (8)
        if len(cleaned) not in (8, 12, 13):
            return False, cleaned

        return True, cleaned

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Recherche produit par code-barres.

        Args:
            lookup_type: Doit etre 'barcode'
            lookup_value: Code-barres du produit

        Returns:
            EnrichmentResult avec donnees produit
        """
        start_time = time.time()

        if lookup_type != "barcode":
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Type de recherche non supporte: {lookup_type}",
                response_time_ms=self._measure_time(start_time),
            )

        is_valid, cleaned = self._validate_barcode(lookup_value)
        if not is_valid:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Format code-barres invalide (8, 12 ou 13 chiffres)",
                response_time_ms=self._measure_time(start_time),
            )

        try:
            client = await self.get_client()

            # Construire l'URL avec les champs demandes
            fields_param = ",".join(self.PRODUCT_FIELDS)
            response = await client.get(
                f"/product/{cleaned}.json",
                params={"fields": fields_param}
            )

            response_time = self._measure_time(start_time)

            data = response.json()

            # Verifier si le produit existe
            if data.get("status") == 0 or not data.get("product"):
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Produit non trouve",
                    response_time_ms=response_time,
                )

            product = data.get("product", {})

            # Calculer la confiance basee sur la completude des donnees
            confidence = self._calculate_confidence(product)

            logger.info(f"[{self.PROVIDER_NAME.upper()}] Lookup barcode={cleaned} -> OK ({response_time}ms)")

            return EnrichmentResult(
                success=True,
                data=product,
                confidence=confidence,
                source=self.PROVIDER_NAME,
                response_time_ms=response_time,
            )

        except httpx.TimeoutException:
            logger.warning(f"[{self.PROVIDER_NAME.upper()}] Timeout pour barcode={lookup_value}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Timeout API",
                response_time_ms=self._measure_time(start_time),
            )

        except httpx.HTTPError as e:
            logger.error(f"[{self.PROVIDER_NAME.upper()}] Erreur HTTP: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur HTTP: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

        except Exception as e:
            logger.exception(f"[{self.PROVIDER_NAME.upper()}] Erreur inattendue: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def _calculate_confidence(self, product: dict) -> float:
        """
        Calcule le score de confiance base sur la completude.

        Args:
            product: Donnees produit

        Returns:
            Score entre 0.0 et 1.0
        """
        required_fields = ["product_name", "brands"]
        optional_fields = ["generic_name", "quantity", "image_url", "categories"]

        score = 0.0

        # Champs requis = 0.3 chacun
        for field in required_fields:
            # Verifier aussi les variantes _fr
            if product.get(field) or product.get(f"{field}_fr"):
                score += 0.3

        # Champs optionnels = 0.1 chacun
        for field in optional_fields:
            if product.get(field) or product.get(f"{field}_fr"):
                score += 0.1

        return min(score, 1.0)

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse Open Facts aux champs Product.

        Args:
            entity_type: Doit etre 'product'
            api_data: Donnees produit brutes

        Returns:
            Dict des champs mappes
        """
        if entity_type != "product":
            return {}

        # Privilegier les champs en francais
        name = api_data.get("product_name_fr") or api_data.get("product_name", "")
        description = api_data.get("generic_name_fr") or api_data.get("generic_name", "")
        brand = api_data.get("brands", "")

        # Construire le nom complet
        full_name = f"{brand} - {name}".strip(" -") if brand else name

        # Meilleure image disponible
        image_url = (
            api_data.get("image_front_url") or
            api_data.get("image_url") or
            ""
        )

        # Categories
        categories = api_data.get("categories", "")
        if isinstance(categories, list):
            categories = ", ".join(categories)

        return {
            # Champs principaux Product
            "name": full_name,
            "description": description,
            "barcode": api_data.get("code", ""),
            "ean13": api_data.get("code", ""),
            "image_url": image_url,

            # Quantite et conditionnement
            "quantity": api_data.get("quantity", ""),
            "packaging": api_data.get("packaging", ""),

            # Metadonnees Open Facts (prefixees _)
            "_off_brand": brand,
            "_off_categories": categories,
            "_off_nutriscore": api_data.get("nutriscore_grade"),
            "_off_ecoscore": api_data.get("ecoscore_grade"),
            "_off_nova_group": api_data.get("nova_group"),
            "_off_origins": api_data.get("origins", ""),
            "_off_labels": api_data.get("labels", ""),
            "_off_allergens": api_data.get("allergens", ""),
            "_off_ingredients": api_data.get("ingredients_text_fr") or api_data.get("ingredients_text", ""),
        }


class OpenFoodFactsProvider(OpenFactsBaseProvider):
    """Provider pour Open Food Facts (produits alimentaires)."""

    PROVIDER_NAME = "openfoodfacts"
    BASE_URL = "https://world.openfoodfacts.org/api/v2"


class OpenBeautyFactsProvider(OpenFactsBaseProvider):
    """Provider pour Open Beauty Facts (produits cosmetiques)."""

    PROVIDER_NAME = "openbeautyfacts"
    BASE_URL = "https://world.openbeautyfacts.org/api/v2"

    # Champs specifiques aux cosmetiques
    PRODUCT_FIELDS = OpenFactsBaseProvider.PRODUCT_FIELDS + [
        "ingredients_analysis",
        "ingredients_analysis_tags",
    ]


class OpenPetFoodFactsProvider(OpenFactsBaseProvider):
    """Provider pour Open Pet Food Facts (produits animaliers)."""

    PROVIDER_NAME = "openpetfoodfacts"
    BASE_URL = "https://world.openpetfoodfacts.org/api/v2"

    # Champs specifiques aux produits animaliers
    PRODUCT_FIELDS = OpenFactsBaseProvider.PRODUCT_FIELDS + [
        "species",  # Espece cible (chien, chat, etc.)
    ]

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """Mappe avec champs specifiques animaliers."""
        base_mapping = super().map_to_entity(entity_type, api_data)

        if entity_type == "product":
            base_mapping["_off_species"] = api_data.get("species", "")

        return base_mapping
