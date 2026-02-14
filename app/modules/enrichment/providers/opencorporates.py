"""
AZALS MODULE - Auto-Enrichment - OpenCorporates Provider
=========================================================

Provider pour l'API OpenCorporates - registres d'entreprises mondiaux.
Documentation: https://api.opencorporates.com/documentation
"""

import logging
import re
import time
from typing import Any, Optional

from app.core.cache import CacheTTL

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class OpenCorporatesProvider(BaseProvider):
    """
    Provider OpenCorporates pour recherche entreprises mondiales.

    Fonctionnalites:
    - Recherche par nom d'entreprise dans 140+ pays
    - Recherche par numero d'identification (company_number)
    - Informations legales de base (statut, date creation, adresse)

    Limites API gratuite:
    - 500 requetes/mois
    - Pas d'acces aux documents
    - Donnees limitees

    Avec cle API:
    - Limites augmentees
    - Acces aux donnees completes
    - Acces aux documents (selon plan)
    """

    PROVIDER_NAME = "opencorporates"
    BASE_URL = "https://api.opencorporates.com/v0.4"
    DEFAULT_TIMEOUT = 15.0
    CACHE_TTL = CacheTTL.DAY  # Cache 24h (donnees entreprise stables)

    # Mapping codes pays OpenCorporates -> ISO
    JURISDICTION_MAP = {
        # Europe
        "fr": "FR", "de": "DE", "gb": "GB", "es": "ES", "it": "IT",
        "be": "BE", "nl": "NL", "at": "AT", "ch": "CH", "pt": "PT",
        "pl": "PL", "ie": "IE", "se": "SE", "dk": "DK", "fi": "FI",
        "no": "NO", "cz": "CZ", "hu": "HU", "ro": "RO", "bg": "BG",
        "lu": "LU", "sk": "SK", "si": "SI", "hr": "HR", "ee": "EE",
        "lv": "LV", "lt": "LT", "cy": "CY", "mt": "MT", "gr": "GR",
        # Ameriques
        "us": "US", "ca": "CA", "mx": "MX", "br": "BR", "ar": "AR",
        # Asie-Pacifique
        "au": "AU", "nz": "NZ", "sg": "SG", "hk": "HK", "jp": "JP",
        "cn": "CN", "in": "IN", "kr": "KR",
        # Autres
        "za": "ZA", "ae": "AE", "ru": "RU",
    }

    def __init__(self, tenant_id: str, api_key: Optional[str] = None):
        """
        Initialise le provider OpenCorporates.

        Args:
            tenant_id: ID du tenant
            api_key: Cle API OpenCorporates (optionnelle, version gratuite sinon)
        """
        super().__init__(tenant_id)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Headers avec API key si disponible."""
        headers = super()._get_headers()
        # OpenCorporates utilise le token dans l'URL, pas dans les headers
        return headers

    def _add_api_key(self, url: str) -> str:
        """Ajoute la cle API a l'URL si disponible."""
        if self.api_key:
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}api_token={self.api_key}"
        return url

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Effectue la recherche OpenCorporates.

        Args:
            lookup_type: Type de recherche ("name", "company_number")
            lookup_value: Valeur a rechercher

        Returns:
            EnrichmentResult avec donnees entreprise
        """
        start_time = time.time()

        try:
            client = await self.get_client()

            if lookup_type == "name":
                return await self._search_by_name(client, lookup_value, start_time)
            elif lookup_type in ("company_number", "siret", "siren"):
                return await self._search_by_number(client, lookup_value, start_time)
            else:
                return EnrichmentResult(
                    success=False,
                    error=f"Type de recherche non supporte: {lookup_type}",
                    response_time_ms=self._measure_time(start_time),
                )

        except Exception as e:
            logger.error(f"[OPENCORPORATES] Erreur: {e}")
            return EnrichmentResult(
                success=False,
                error=str(e),
                response_time_ms=self._measure_time(start_time),
            )

    async def _search_by_name(
        self,
        client,
        name: str,
        start_time: float
    ) -> EnrichmentResult:
        """Recherche entreprise par nom."""
        # Nettoyer le nom
        clean_name = name.strip()
        if len(clean_name) < 2:
            return EnrichmentResult(
                success=False,
                error="Nom trop court (min 2 caracteres)",
                response_time_ms=self._measure_time(start_time),
            )

        url = self._add_api_key(f"/companies/search?q={clean_name}&per_page=10")

        try:
            response = await client.get(url)

            if response.status_code == 401:
                return EnrichmentResult(
                    success=False,
                    error="Cle API invalide ou manquante",
                    response_time_ms=self._measure_time(start_time),
                )

            if response.status_code == 429:
                return EnrichmentResult(
                    success=False,
                    error="Limite de requetes atteinte",
                    response_time_ms=self._measure_time(start_time),
                )

            if response.status_code != 200:
                return EnrichmentResult(
                    success=False,
                    error=f"Erreur API: {response.status_code}",
                    response_time_ms=self._measure_time(start_time),
                )

            data = response.json()
            results = data.get("results", {})
            companies = results.get("companies", [])

            if not companies:
                return EnrichmentResult(
                    success=False,
                    error="Aucune entreprise trouvee",
                    response_time_ms=self._measure_time(start_time),
                )

            # Prendre le premier resultat comme principal
            best_match = companies[0].get("company", {})
            parsed = self._parse_company(best_match)

            # Preparer les suggestions (autres resultats)
            suggestions = []
            for company_wrapper in companies[1:6]:  # Max 5 suggestions
                company = company_wrapper.get("company", {})
                suggestions.append({
                    "name": company.get("name", ""),
                    "company_number": company.get("company_number", ""),
                    "jurisdiction_code": company.get("jurisdiction_code", ""),
                    "current_status": company.get("current_status", ""),
                    "opencorporates_url": company.get("opencorporates_url", ""),
                })

            return EnrichmentResult(
                success=True,
                data=parsed,
                confidence=0.8,  # Recherche par nom = confiance moderee
                source=self.PROVIDER_NAME,
                response_time_ms=self._measure_time(start_time),
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"[OPENCORPORATES] Search error: {e}")
            return EnrichmentResult(
                success=False,
                error=str(e),
                response_time_ms=self._measure_time(start_time),
            )

    async def _search_by_number(
        self,
        client,
        company_number: str,
        start_time: float
    ) -> EnrichmentResult:
        """Recherche entreprise par numero d'identification."""
        # Nettoyer le numero
        clean_number = re.sub(r'[^A-Za-z0-9]', '', company_number)

        # Detecter le pays si possible (SIRET/SIREN = France)
        jurisdiction = None
        if re.match(r'^\d{9}$', clean_number):  # SIREN
            jurisdiction = "fr"
        elif re.match(r'^\d{14}$', clean_number):  # SIRET
            jurisdiction = "fr"
            clean_number = clean_number[:9]  # Utiliser le SIREN

        # Recherche globale si pas de juridiction detectee
        if jurisdiction:
            url = self._add_api_key(
                f"/companies/{jurisdiction}/{clean_number}"
            )
        else:
            # Recherche par numero sans juridiction
            url = self._add_api_key(
                f"/companies/search?q={clean_number}&company_type=company"
            )

        try:
            response = await client.get(url)

            if response.status_code == 404:
                return EnrichmentResult(
                    success=False,
                    error="Entreprise non trouvee",
                    response_time_ms=self._measure_time(start_time),
                )

            if response.status_code == 401:
                return EnrichmentResult(
                    success=False,
                    error="Cle API invalide ou manquante",
                    response_time_ms=self._measure_time(start_time),
                )

            if response.status_code == 429:
                return EnrichmentResult(
                    success=False,
                    error="Limite de requetes atteinte",
                    response_time_ms=self._measure_time(start_time),
                )

            if response.status_code != 200:
                return EnrichmentResult(
                    success=False,
                    error=f"Erreur API: {response.status_code}",
                    response_time_ms=self._measure_time(start_time),
                )

            data = response.json()

            # Format different selon l'endpoint
            if "results" in data:
                # Recherche
                companies = data["results"].get("companies", [])
                if not companies:
                    return EnrichmentResult(
                        success=False,
                        error="Aucune entreprise trouvee",
                        response_time_ms=self._measure_time(start_time),
                    )
                company = companies[0].get("company", {})
            else:
                # Lookup direct
                company = data.get("results", {}).get("company", {})

            if not company:
                return EnrichmentResult(
                    success=False,
                    error="Aucune entreprise trouvee",
                    response_time_ms=self._measure_time(start_time),
                )

            parsed = self._parse_company(company)

            return EnrichmentResult(
                success=True,
                data=parsed,
                confidence=0.95,  # Lookup par numero = haute confiance
                source=self.PROVIDER_NAME,
                response_time_ms=self._measure_time(start_time),
            )

        except Exception as e:
            logger.error(f"[OPENCORPORATES] Lookup error: {e}")
            return EnrichmentResult(
                success=False,
                error=str(e),
                response_time_ms=self._measure_time(start_time),
            )

    def _parse_company(self, company: dict) -> dict[str, Any]:
        """
        Parse les donnees brutes OpenCorporates.

        Args:
            company: Donnees brutes de l'API

        Returns:
            Dict avec champs normalises
        """
        # Adresse
        address = company.get("registered_address", {}) or {}
        address_str = address.get("street_address", "")

        # Juridiction -> pays ISO
        jurisdiction = company.get("jurisdiction_code", "")
        country_code = self.JURISDICTION_MAP.get(
            jurisdiction.lower().split("_")[0],  # "us_de" -> "us"
            jurisdiction.upper()[:2] if jurisdiction else ""
        )

        # Statut
        status = company.get("current_status", "")
        is_active = status.lower() in ("active", "live", "registered", "good standing")

        # Date de creation
        incorporation_date = company.get("incorporation_date", "")

        return {
            # Identifiants
            "company_number": company.get("company_number", ""),
            "jurisdiction_code": jurisdiction,
            "opencorporates_url": company.get("opencorporates_url", ""),

            # Informations de base
            "name": company.get("name", ""),
            "company_name": company.get("name", ""),
            "company_type": company.get("company_type", ""),
            "current_status": status,
            "is_active": is_active,

            # Dates
            "incorporation_date": incorporation_date,
            "dissolution_date": company.get("dissolution_date", ""),

            # Adresse
            "address_line1": address_str,
            "address_line2": address.get("locality", ""),
            "postal_code": address.get("postal_code", ""),
            "city": address.get("locality", "") or address.get("region", ""),
            "region": address.get("region", ""),
            "country_code": country_code,

            # Metadata OpenCorporates
            "_opencorporates_url": company.get("opencorporates_url", ""),
            "_registry_url": company.get("registry_url", ""),
            "_source": company.get("source", {}),
            "_branch": company.get("branch", ""),
            "_branch_status": company.get("branch_status", ""),
            "_inactive": company.get("inactive", False),
            "_retrieved_at": company.get("retrieved_at", ""),
        }

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe les donnees OpenCorporates aux champs Contact.

        Args:
            entity_type: Type d'entite ("contact")
            api_data: Donnees parsees

        Returns:
            Dict de champs pour l'entite
        """
        if entity_type != "contact":
            return {}

        mapped = {}

        # Nom
        if api_data.get("name"):
            mapped["name"] = api_data["name"]
            mapped["company_name"] = api_data["name"]

        # Numero d'entreprise (pas SIRET, mais equivalent local)
        if api_data.get("company_number"):
            mapped["registration_number"] = api_data["company_number"]

        # Adresse
        if api_data.get("address_line1"):
            mapped["address_line1"] = api_data["address_line1"]
        if api_data.get("address_line2"):
            mapped["address_line2"] = api_data["address_line2"]
        if api_data.get("postal_code"):
            mapped["postal_code"] = api_data["postal_code"]
        if api_data.get("city"):
            mapped["city"] = api_data["city"]
        if api_data.get("country_code"):
            mapped["country_code"] = api_data["country_code"]

        # Forme juridique
        if api_data.get("company_type"):
            mapped["legal_form"] = api_data["company_type"]

        # Statut
        mapped["is_active"] = api_data.get("is_active", True)

        # Metadata (prefixees pour identification)
        for key in ["_opencorporates_url", "_registry_url", "_retrieved_at"]:
            if api_data.get(key):
                mapped[key] = api_data[key]

        return mapped
