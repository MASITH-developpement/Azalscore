"""
AZALS MODULE - Auto-Enrichment - VIES Provider
===============================================

Provider pour la validation des numeros de TVA europeens via l'API VIES.
API officielle de la Commission Europeenne.

API Documentation: https://ec.europa.eu/taxation_customs/vies/
REST API: https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number
"""
from __future__ import annotations


import logging
import re
import time
from typing import Any

import httpx

from app.core.cache import CacheTTL

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


# Codes pays UE valides pour TVA
EU_COUNTRY_CODES = frozenset({
    "AT",  # Autriche
    "BE",  # Belgique
    "BG",  # Bulgarie
    "CY",  # Chypre
    "CZ",  # Republique Tcheque
    "DE",  # Allemagne
    "DK",  # Danemark
    "EE",  # Estonie
    "EL",  # Grece (code VIES)
    "ES",  # Espagne
    "FI",  # Finlande
    "FR",  # France
    "HR",  # Croatie
    "HU",  # Hongrie
    "IE",  # Irlande
    "IT",  # Italie
    "LT",  # Lituanie
    "LU",  # Luxembourg
    "LV",  # Lettonie
    "MT",  # Malte
    "NL",  # Pays-Bas
    "PL",  # Pologne
    "PT",  # Portugal
    "RO",  # Roumanie
    "SE",  # Suede
    "SI",  # Slovenie
    "SK",  # Slovaquie
    "XI",  # Irlande du Nord (post-Brexit)
})

# Formats de TVA par pays (regex patterns)
# Reference: https://ec.europa.eu/taxation_customs/vies/faq.html
VAT_FORMATS = {
    "AT": r"U\d{8}",                          # Autriche: U + 8 chiffres
    "BE": r"[01]\d{9}",                       # Belgique: 0/1 + 9 chiffres
    "BG": r"\d{9,10}",                        # Bulgarie: 9-10 chiffres
    "CY": r"\d{8}[A-Z]",                      # Chypre: 8 chiffres + lettre
    "CZ": r"\d{8,10}",                        # Tcheque: 8-10 chiffres
    "DE": r"\d{9}",                           # Allemagne: 9 chiffres
    "DK": r"\d{8}",                           # Danemark: 8 chiffres
    "EE": r"\d{9}",                           # Estonie: 9 chiffres
    "EL": r"\d{9}",                           # Grece: 9 chiffres
    "ES": r"[A-Z0-9]\d{7}[A-Z0-9]",          # Espagne: lettre/chiffre + 7 chiffres + lettre/chiffre
    "FI": r"\d{8}",                           # Finlande: 8 chiffres
    "FR": r"[A-HJ-NP-Z0-9]{2}\d{9}",         # France: 2 caracteres + 9 chiffres
    "HR": r"\d{11}",                          # Croatie: 11 chiffres
    "HU": r"\d{8}",                           # Hongrie: 8 chiffres
    "IE": r"(\d{7}[A-W])|(\d[A-Z+*]\d{5}[A-W])|(\d{7}[A-W][A-I])",  # Irlande: formats multiples
    "IT": r"\d{11}",                          # Italie: 11 chiffres
    "LT": r"(\d{9}|\d{12})",                  # Lituanie: 9 ou 12 chiffres
    "LU": r"\d{8}",                           # Luxembourg: 8 chiffres
    "LV": r"\d{11}",                          # Lettonie: 11 chiffres
    "MT": r"\d{8}",                           # Malte: 8 chiffres
    "NL": r"\d{9}B\d{2}",                     # Pays-Bas: 9 chiffres + B + 2 chiffres
    "PL": r"\d{10}",                          # Pologne: 10 chiffres
    "PT": r"\d{9}",                           # Portugal: 9 chiffres
    "RO": r"\d{2,10}",                        # Roumanie: 2-10 chiffres
    "SE": r"\d{12}",                          # Suede: 12 chiffres
    "SI": r"\d{8}",                           # Slovenie: 8 chiffres
    "SK": r"\d{10}",                          # Slovaquie: 10 chiffres
    "XI": r"(\d{9}|\d{12}|GD\d{3}|HA\d{3})",  # Irlande du Nord: multiples formats
}


class VIESProvider(BaseProvider):
    """
    Provider pour la validation des numeros de TVA europeens via VIES.

    Validation par:
    - vat_number: Numero TVA complet (ex: FR12345678901)

    API gratuite de la Commission Europeenne, sans authentification.
    """

    PROVIDER_NAME = "vies"
    BASE_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api"
    CACHE_TTL = CacheTTL.DAY  # 24h - status TVA stable
    DEFAULT_TIMEOUT = 15.0

    def __init__(self, tenant_id: str):
        """
        Initialise le provider VIES.

        Args:
            tenant_id: ID du tenant
        """
        super().__init__(tenant_id)

    def _get_headers(self) -> dict[str, str]:
        """Headers standards pour l'API VIES."""
        headers = super()._get_headers()
        headers["Content-Type"] = "application/json"
        return headers

    def _parse_vat_number(self, vat_number: str) -> tuple[str | None, str | None, str | None]:
        """
        Parse et valide un numero de TVA.

        Args:
            vat_number: Numero TVA (ex: "FR12345678901" ou "FR 123 456 789 01")

        Returns:
            (country_code, vat_number_clean, error_message)
        """
        # Nettoyer: supprimer espaces, tirets, points
        cleaned = re.sub(r'[\s\-\.]', '', vat_number.upper())

        if len(cleaned) < 4:
            return None, None, "Numero TVA trop court (minimum 4 caracteres)"

        # Extraire le code pays (2 premieres lettres)
        country_code = cleaned[:2]
        vat_only = cleaned[2:]

        # Verifier que le code pays est dans l'UE
        if country_code not in EU_COUNTRY_CODES:
            # Cas special: GR -> EL pour la Grece
            if country_code == "GR":
                country_code = "EL"
            else:
                return None, None, f"Code pays '{country_code}' non valide pour TVA UE"

        # Validation du format specifique au pays
        pattern = VAT_FORMATS.get(country_code)
        if pattern and not re.match(f"^{pattern}$", vat_only):
            return None, None, f"Format TVA invalide pour {country_code}"

        return country_code, vat_only, None

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Valide un numero de TVA europeen via VIES.

        Args:
            lookup_type: 'vat_number'
            lookup_value: Numero TVA complet (ex: FR12345678901)

        Returns:
            EnrichmentResult avec donnees entreprise si valide
        """
        start_time = time.time()

        if lookup_type != "vat_number":
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Type de recherche non supporte: {lookup_type}",
                response_time_ms=self._measure_time(start_time),
            )

        # Parser et valider le format
        country_code, vat_only, parse_error = self._parse_vat_number(lookup_value)

        if parse_error:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=parse_error,
                response_time_ms=self._measure_time(start_time),
            )

        try:
            client = await self.get_client()

            # Appel API VIES REST
            response = await client.post(
                "/check-vat-number",
                json={
                    "countryCode": country_code,
                    "vatNumber": vat_only,
                }
            )

            response_time = self._measure_time(start_time)

            # VIES retourne 200 meme pour numero invalide
            if response.status_code == 200:
                data = response.json()

                # Verifier si le numero est valide
                is_valid = data.get("valid", False)

                if not is_valid:
                    return EnrichmentResult(
                        success=False,
                        source=self.PROVIDER_NAME,
                        data=data,
                        error="Numero TVA invalide ou non enregistre",
                        response_time_ms=response_time,
                    )

                # Numero valide - construire le resultat
                logger.info(
                    f"[VIES] Validation OK: {country_code}{vat_only} -> "
                    f"{data.get('name', 'N/A')} ({response_time}ms)"
                )

                return EnrichmentResult(
                    success=True,
                    data={
                        "valid": True,
                        "country_code": country_code,
                        "vat_number": vat_only,
                        "full_vat_number": f"{country_code}{vat_only}",
                        "name": data.get("name", ""),
                        "address": data.get("address", ""),
                        "request_date": data.get("requestDate", ""),
                    },
                    confidence=1.0,  # Registre officiel = confiance maximale
                    source=self.PROVIDER_NAME,
                    response_time_ms=response_time,
                )

            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("errorWrappers", [{}])[0].get("message", "Requete invalide")
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error=error_msg,
                    response_time_ms=response_time,
                )

            elif response.status_code == 503:
                # Service VIES temporairement indisponible
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Service VIES temporairement indisponible. Reessayez plus tard.",
                    response_time_ms=response_time,
                )

            else:
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.warning(f"[VIES] Timeout pour {lookup_value}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Timeout API VIES",
                response_time_ms=self._measure_time(start_time),
            )

        except httpx.HTTPError as e:
            logger.error(f"[VIES] Erreur HTTP: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur HTTP: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

        except Exception as e:
            logger.exception(f"[VIES] Erreur inattendue: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

        # Fallback (ne devrait pas etre atteint)
        return EnrichmentResult(
            success=False,
            source=self.PROVIDER_NAME,
            error="Erreur inconnue",
            response_time_ms=self._measure_time(start_time),
        )

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse VIES aux champs Contact.

        Args:
            entity_type: Doit etre 'contact'
            api_data: Reponse de l'API VIES

        Returns:
            Dict des champs mappes pour Contact
        """
        if entity_type != "contact":
            return {}

        # Extraire l'adresse parsee si possible
        address_raw = api_data.get("address", "")
        address_parts = self._parse_address(address_raw, api_data.get("country_code", ""))

        return {
            # Champs principaux Contact
            "name": api_data.get("name", ""),
            "company_name": api_data.get("name", ""),
            "vat_number": api_data.get("full_vat_number", ""),
            "vat_valid": True,

            # Adresse (parsee si possible)
            "address_line1": address_parts.get("line1", address_raw),
            "postal_code": address_parts.get("postal_code", ""),
            "city": address_parts.get("city", ""),
            "country_code": api_data.get("country_code", ""),
            "country": self._get_country_name(api_data.get("country_code", "")),

            # Metadonnees VIES (prefixees _)
            "_vies_valid": True,
            "_vies_country_code": api_data.get("country_code", ""),
            "_vies_vat_number": api_data.get("vat_number", ""),
            "_vies_request_date": api_data.get("request_date", ""),
            "_vies_raw_address": address_raw,
        }

    def _parse_address(self, address: str, country_code: str) -> dict[str, str]:
        """
        Tente de parser une adresse brute en composants.

        VIES retourne souvent l'adresse en bloc sans structure.
        Cette methode fait une tentative heuristique de parsing.

        Args:
            address: Adresse brute
            country_code: Code pays

        Returns:
            Dict avec line1, postal_code, city si detectes
        """
        if not address:
            return {}

        result = {}

        # Normaliser les retours a la ligne
        address = address.replace("\n", ", ").strip()

        # Patterns de code postal par pays
        postal_patterns = {
            "FR": r"\b(\d{5})\b",
            "DE": r"\b(\d{5})\b",
            "IT": r"\b(\d{5})\b",
            "ES": r"\b(\d{5})\b",
            "BE": r"\b(\d{4})\b",
            "NL": r"\b(\d{4}\s?[A-Z]{2})\b",
            "AT": r"\b(\d{4})\b",
            "PL": r"\b(\d{2}-\d{3})\b",
            # Defaut
            "DEFAULT": r"\b(\d{4,6})\b",
        }

        pattern = postal_patterns.get(country_code, postal_patterns["DEFAULT"])
        match = re.search(pattern, address)

        if match:
            result["postal_code"] = match.group(1).replace(" ", "")

            # Extraire la ville (generalement apres le code postal)
            after_postal = address[match.end():].strip()
            city_match = re.match(r"^[\s,]*([A-Za-zÀ-ÿ\s\-]+)", after_postal)
            if city_match:
                result["city"] = city_match.group(1).strip().rstrip(",")

            # Le reste est la ligne 1
            before_postal = address[:match.start()].strip().rstrip(",")
            if before_postal:
                result["line1"] = before_postal

        if not result.get("line1"):
            result["line1"] = address

        return result

    def _get_country_name(self, country_code: str) -> str:
        """Retourne le nom du pays depuis le code."""
        country_names = {
            "AT": "Autriche",
            "BE": "Belgique",
            "BG": "Bulgarie",
            "CY": "Chypre",
            "CZ": "Republique Tcheque",
            "DE": "Allemagne",
            "DK": "Danemark",
            "EE": "Estonie",
            "EL": "Grece",
            "ES": "Espagne",
            "FI": "Finlande",
            "FR": "France",
            "HR": "Croatie",
            "HU": "Hongrie",
            "IE": "Irlande",
            "IT": "Italie",
            "LT": "Lituanie",
            "LU": "Luxembourg",
            "LV": "Lettonie",
            "MT": "Malte",
            "NL": "Pays-Bas",
            "PL": "Pologne",
            "PT": "Portugal",
            "RO": "Roumanie",
            "SE": "Suede",
            "SI": "Slovenie",
            "SK": "Slovaquie",
            "XI": "Irlande du Nord",
        }
        return country_names.get(country_code, country_code)

    @staticmethod
    def is_eu_vat_number(vat_number: str) -> bool:
        """
        Verifie rapidement si un numero ressemble a un numero TVA UE.

        Args:
            vat_number: Numero a verifier

        Returns:
            True si le format correspond a un TVA UE potentiel
        """
        if not vat_number or len(vat_number) < 4:
            return False

        cleaned = re.sub(r'[\s\-\.]', '', vat_number.upper())
        country_code = cleaned[:2]

        # Cas special Grece
        if country_code == "GR":
            country_code = "EL"

        return country_code in EU_COUNTRY_CODES
