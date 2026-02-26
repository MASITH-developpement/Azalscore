"""
AZALS MODULE - Auto-Enrichment - INSEE Provider
================================================

Provider pour l'API Recherche Entreprises (data.gouv.fr).
Lookup entreprises francaises par SIRET/SIREN.

API Documentation: https://recherche-entreprises.api.gouv.fr/docs/
Note: Ancienne API api.insee.fr deprecee en 2025, migre vers recherche-entreprises.api.gouv.fr
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


class INSEEProvider(BaseProvider):
    """
    Provider pour l'API Recherche Entreprises (data.gouv.fr).

    Recherche par:
    - SIRET (14 chiffres): Info etablissement complet
    - SIREN (9 chiffres): Info entreprise (tous etablissements)

    API gratuite, sans authentification requise.
    """

    PROVIDER_NAME = "insee"
    BASE_URL = "https://recherche-entreprises.api.gouv.fr"
    CACHE_TTL = CacheTTL.DAY  # 24h - donnees entreprise stables
    DEFAULT_TIMEOUT = 15.0

    def __init__(self, tenant_id: str, api_token: str | None = None):
        """
        Initialise le provider INSEE.

        Args:
            tenant_id: ID du tenant
            api_token: Non utilise (API gratuite sans auth)
        """
        super().__init__(tenant_id)
        self.api_token = api_token  # Garde pour compatibilite

    def _get_headers(self) -> dict[str, str]:
        """Headers standards (pas d'auth requise)."""
        return super()._get_headers()

    def _validate_siret(self, siret: str) -> tuple[bool, str]:
        """
        Valide le format SIRET (14 chiffres).

        Returns:
            (is_valid, cleaned_value)
        """
        cleaned = re.sub(r'\s+', '', siret)
        if not re.match(r'^\d{14}$', cleaned):
            return False, cleaned
        return True, cleaned

    def _validate_siren(self, siren: str) -> tuple[bool, str]:
        """
        Valide le format SIREN (9 chiffres).

        Returns:
            (is_valid, cleaned_value)
        """
        cleaned = re.sub(r'\s+', '', siren)
        if not re.match(r'^\d{9}$', cleaned):
            return False, cleaned
        return True, cleaned

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Recherche entreprise par SIRET, SIREN ou nom.

        Args:
            lookup_type: 'siret', 'siren' ou 'name'
            lookup_value: Numero SIRET/SIREN ou nom d'entreprise

        Returns:
            EnrichmentResult avec donnees entreprise
        """
        start_time = time.time()

        # Validation selon le type
        if lookup_type == "siret":
            is_valid, cleaned = self._validate_siret(lookup_value)
            if not is_valid:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Format SIRET invalide (14 chiffres requis)",
                    response_time_ms=self._measure_time(start_time),
                )

        elif lookup_type == "siren":
            is_valid, cleaned = self._validate_siren(lookup_value)
            if not is_valid:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Format SIREN invalide (9 chiffres requis)",
                    response_time_ms=self._measure_time(start_time),
                )

        elif lookup_type == "name":
            # Recherche par nom - minimum 2 caracteres
            cleaned = lookup_value.strip()
            if len(cleaned) < 2:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Minimum 2 caracteres requis pour la recherche",
                    response_time_ms=self._measure_time(start_time),
                )

        else:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Type de recherche non supporte: {lookup_type}",
                response_time_ms=self._measure_time(start_time),
            )

        try:
            client = await self.get_client()

            # Parametres de recherche
            params = {"q": cleaned}
            if lookup_type == "name":
                params["per_page"] = 10  # Plus de resultats pour recherche par nom

            response = await client.get("/search", params=params)
            response_time = self._measure_time(start_time)

            if response.status_code == 429:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Limite de requetes atteinte (reessayez plus tard)",
                    response_time_ms=response_time,
                )

            response.raise_for_status()
            data = response.json()

            # Verifier qu'on a des resultats
            results = data.get("results", [])
            if not results:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Entreprise non trouvee",
                    response_time_ms=response_time,
                )

            # Pour recherche par nom: retourner tous les resultats comme suggestions
            if lookup_type == "name":
                suggestions = self._build_company_suggestions(results)
                logger.info(f"[INSEE] Search name='{cleaned}' -> {len(results)} resultats ({response_time}ms)")

                return EnrichmentResult(
                    success=True,
                    data={"results": results, "suggestions": suggestions},
                    confidence=0.8,  # Recherche textuelle = confiance moderee
                    source=self.PROVIDER_NAME,
                    response_time_ms=response_time,
                )

            # Pour SIRET/SIREN: prendre le premier resultat exact
            entreprise = results[0]

            # Verifier correspondance exacte SIRET/SIREN
            if lookup_type == "siret":
                siege = entreprise.get("siege", {})
                if siege.get("siret") != cleaned:
                    # Chercher dans les etablissements
                    matching = entreprise.get("matching_etablissements", [])
                    found = False
                    for etab in matching:
                        if etab.get("siret") == cleaned:
                            found = True
                            break
                    if not found and siege.get("siret") != cleaned:
                        return EnrichmentResult(
                            success=False,
                            source=self.PROVIDER_NAME,
                            error="Entreprise non trouvee",
                            response_time_ms=response_time,
                        )

            logger.info(f"[INSEE] Lookup {lookup_type}={cleaned} -> {entreprise.get('nom_complet', 'N/A')} ({response_time}ms)")

            return EnrichmentResult(
                success=True,
                data=entreprise,
                confidence=1.0,  # Registre officiel = confiance maximale
                source=self.PROVIDER_NAME,
                response_time_ms=response_time,
            )

        except httpx.TimeoutException:
            logger.warning(f"[INSEE] Timeout pour {lookup_type}={lookup_value}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Timeout API INSEE",
                response_time_ms=self._measure_time(start_time),
            )

        except httpx.HTTPError as e:
            logger.error(f"[INSEE] Erreur HTTP: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur HTTP: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

        except Exception as e:
            logger.exception(f"[INSEE] Erreur inattendue: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse API Recherche Entreprises aux champs Contact.

        Args:
            entity_type: Doit etre 'contact'
            api_data: Reponse de recherche-entreprises.api.gouv.fr

        Returns:
            Dict des champs mappes pour Contact
        """
        if entity_type != "contact":
            return {}

        # Format nouveau API: donnees directement dans l'objet entreprise
        siege = api_data.get("siege", {})

        # Nom de l'entreprise
        denomination = api_data.get("nom_complet", "")
        if not denomination:
            denomination = api_data.get("nom_raison_sociale", "")

        # Adresse du siege
        address_line = siege.get("adresse", "") or siege.get("geo_adresse", "")

        # Si adresse complete, on l'utilise directement
        # Sinon on construit depuis les composants
        if not address_line:
            address_parts = [
                siege.get("numero_voie", ""),
                siege.get("indice_repetition", ""),
                siege.get("type_voie", ""),
                siege.get("libelle_voie", ""),
            ]
            address_line = " ".join(filter(None, address_parts)).strip()

        # Complement d'adresse
        complement = siege.get("complement_adresse", "")

        # Nature juridique
        nature_juridique = api_data.get("nature_juridique", "")
        legal_form = self._map_legal_form(nature_juridique)

        # Code NAF/APE
        naf_code = siege.get("activite_principale", "") or api_data.get("activite_principale", "")

        # Determiner le type d'entite
        entity_type_value = "COMPANY"
        if nature_juridique and nature_juridique.startswith("1"):
            entity_type_value = "INDIVIDUAL"

        return {
            # Champs principaux Contact
            "name": denomination,
            "company_name": denomination,
            "legal_name": denomination,
            "registration_number": siege.get("siret", ""),
            "siret": siege.get("siret", ""),
            "siren": api_data.get("siren", ""),
            "entity_type": entity_type_value,

            # Adresse
            "address_line1": address_line,
            "address_line2": complement,
            "postal_code": siege.get("code_postal", ""),
            "city": siege.get("libelle_commune", ""),
            "country": "France",
            "country_code": "FR",

            # Coordonnees GPS
            "latitude": siege.get("latitude"),
            "longitude": siege.get("longitude"),

            # Donnees supplementaires
            "legal_form": legal_form,
            "industry_code": naf_code,

            # Metadonnees INSEE (prefixees _)
            "_insee_siren": api_data.get("siren", ""),
            "_insee_siret": siege.get("siret", ""),
            "_insee_creation_date": api_data.get("date_creation"),
            "_insee_naf_code": naf_code,
            "_insee_legal_form_code": nature_juridique,
            "_insee_tranche_effectifs": siege.get("tranche_effectif_salarie"),
            "_insee_etat_administratif": siege.get("etat_administratif"),
        }

    def _build_company_suggestions(self, results: list[dict]) -> list[dict]:
        """
        Construit une liste de suggestions a partir des resultats de recherche.

        Args:
            results: Liste des entreprises retournees par l'API

        Returns:
            Liste de suggestions formatees pour l'autocomplete
        """
        suggestions = []
        for ent in results:
            siege = ent.get("siege", {}) or {}
            # S'assurer que les valeurs sont des strings (jamais None)
            ville = siege.get("libelle_commune") or ""
            code_postal = siege.get("code_postal") or ""
            adresse = siege.get("adresse") or siege.get("geo_adresse") or ""
            siret = siege.get("siret") or ""
            siren = ent.get("siren") or ""
            nom = ent.get("nom_complet") or ""

            # Construire le label affiche
            location = f"{code_postal} {ville}".strip() if code_postal or ville else ""
            label = nom
            if location:
                label = f"{label} - {location}"

            suggestions.append({
                "label": label or "Inconnu",
                "value": siret or siren,
                "siren": siren,
                "siret": siret,
                "name": nom,
                "address": adresse,
                "city": ville,
                "postal_code": code_postal,
                "data": ent,  # Donnees completes pour enrichissement
            })

        return suggestions

    def get_suggestions(self, api_data: dict) -> list[dict]:
        """
        Retourne les suggestions pour l'autocomplete (recherche par nom).

        Args:
            api_data: Reponse de l'API avec results et suggestions

        Returns:
            Liste de suggestions formatees
        """
        return api_data.get("suggestions", [])

    def _map_legal_form(self, code: str) -> str:
        """
        Mappe le code forme juridique INSEE vers un libelle lisible.

        Reference: https://www.insee.fr/fr/information/2028129
        """
        legal_forms = {
            # Personnes physiques
            "1000": "Entrepreneur individuel",
            # Societes commerciales
            "5499": "SARL",
            "5498": "EURL",
            "5710": "SAS",
            "5720": "SASU",
            "5599": "SA a conseil d'administration",
            "5585": "SA a directoire",
            # Societes civiles
            "6540": "SCI",
            "6533": "GAEC",
            # Autres
            "5308": "SCOP",
            "9220": "Association declaree",
            "9221": "Association declaree reconnue d'utilite publique",
            "7112": "Autorite administrative centrale",
            "7210": "Commune",
        }

        # Retourner le libelle ou le code si non trouve
        return legal_forms.get(code, f"Code {code}" if code else "")

    def get_siren_from_siret(self, siret: str) -> str:
        """Extrait le SIREN (9 premiers chiffres) d'un SIRET."""
        cleaned = re.sub(r'\s+', '', siret)
        return cleaned[:9] if len(cleaned) >= 9 else ""
