"""
AZALS MODULE - Auto-Enrichment - Pappers Provider
==================================================

Provider pour l'API Pappers (donnees entreprises et analyse de risque).

API Documentation: https://www.pappers.fr/api/documentation
Version gratuite: 100 requetes/mois
"""
from __future__ import annotations


import logging
import re
import time
from datetime import datetime
from typing import Any

import httpx

from app.core.cache import CacheTTL

from .base import BaseProvider, EnrichmentResult
from .insee import INSEEProvider

logger = logging.getLogger(__name__)


class PappersProvider(BaseProvider):
    """
    Provider pour l'API Pappers.

    Recherche par SIREN/SIRET avec donnees enrichies:
    - Informations legales
    - Procedures collectives
    - Score de solvabilite (si disponible)
    - Donnees financieres basiques

    API gratuite: 100 req/mois (sans API key)
    API payante: avec API key pour plus de quota
    """

    PROVIDER_NAME = "pappers"
    BASE_URL = "https://api.pappers.fr/v2"
    CACHE_TTL = CacheTTL.DAY  # 24h - donnees entreprise stables
    DEFAULT_TIMEOUT = 15.0

    def __init__(self, tenant_id: str, api_key: str | None = None):
        """
        Initialise le provider Pappers.

        Args:
            tenant_id: ID du tenant
            api_key: Cle API Pappers (optionnelle pour tier gratuit)
        """
        super().__init__(tenant_id)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Headers avec API key si disponible."""
        headers = super()._get_headers()
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _validate_siren(self, siren: str) -> tuple[bool, str]:
        """Valide le format SIREN (9 chiffres)."""
        cleaned = re.sub(r'\s+', '', siren)
        if not re.match(r'^\d{9}$', cleaned):
            return False, cleaned
        return True, cleaned

    def _validate_siret(self, siret: str) -> tuple[bool, str]:
        """Valide le format SIRET (14 chiffres)."""
        cleaned = re.sub(r'\s+', '', siret)
        if not re.match(r'^\d{14}$', cleaned):
            return False, cleaned
        return True, cleaned

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str
    ) -> EnrichmentResult:
        """
        Recherche entreprise par SIREN ou SIRET.

        Si pas de cle API Pappers, utilise INSEE en fallback avec
        calcul de risque simplifie.

        Args:
            lookup_type: 'siret', 'siren' ou 'risk'
            lookup_value: Numero SIRET/SIREN

        Returns:
            EnrichmentResult avec donnees entreprise et analyse de risque
        """
        start_time = time.time()

        # Validation selon le type
        if lookup_type in ("siret", "risk"):
            is_valid, cleaned = self._validate_siret(lookup_value)
            if not is_valid:
                # Peut-etre un SIREN
                is_valid, cleaned = self._validate_siren(lookup_value)
                if not is_valid:
                    return EnrichmentResult(
                        success=False,
                        source=self.PROVIDER_NAME,
                        error="Format SIRET (14 chiffres) ou SIREN (9 chiffres) invalide",
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
        else:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Type de recherche non supporte: {lookup_type}",
                response_time_ms=self._measure_time(start_time),
            )

        # Si pas de cle API Pappers, utiliser INSEE en fallback
        if not self.api_key:
            return await self._fallback_to_insee(lookup_type, cleaned, start_time)

        try:
            client = await self.get_client()

            # Determiner le parametre selon la longueur
            param_name = "siret" if len(cleaned) == 14 else "siren"
            params = {param_name: cleaned}

            # Ajouter l'API key
            params["api_token"] = self.api_key

            response = await client.get("/entreprise", params=params)
            response_time = self._measure_time(start_time)

            if response.status_code == 404:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Entreprise non trouvee",
                    response_time_ms=response_time,
                )

            if response.status_code == 429:
                return EnrichmentResult(
                    success=False,
                    source=self.PROVIDER_NAME,
                    error="Quota API Pappers atteint (100 req/mois gratuit)",
                    response_time_ms=response_time,
                )

            if response.status_code == 401:
                # Fallback to INSEE si cle invalide
                logger.warning("[PAPPERS] Cle API invalide, fallback vers INSEE")
                return await self._fallback_to_insee(lookup_type, cleaned, start_time)

            response.raise_for_status()
            data = response.json()

            # Calculer le score de risque
            risk_data = self._calculate_risk_score(data)
            data["risk_analysis"] = risk_data

            logger.info(
                f"[PAPPERS] Lookup {lookup_type}={cleaned} -> "
                f"{data.get('nom_entreprise', 'N/A')} "
                f"(risque: {risk_data.get('score', 'N/A')}) ({response_time}ms)"
            )

            return EnrichmentResult(
                success=True,
                data=data,
                confidence=1.0,  # Registre officiel
                source=self.PROVIDER_NAME,
                response_time_ms=response_time,
            )

        except httpx.TimeoutException:
            logger.warning(f"[PAPPERS] Timeout, fallback vers INSEE")
            return await self._fallback_to_insee(lookup_type, cleaned, start_time)

        except httpx.HTTPError as e:
            logger.error(f"[PAPPERS] Erreur HTTP: {e}, fallback vers INSEE")
            return await self._fallback_to_insee(lookup_type, cleaned, start_time)

        except Exception as e:
            logger.exception(f"[PAPPERS] Erreur inattendue: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    async def _fallback_to_insee(
        self,
        lookup_type: str,
        cleaned_value: str,
        start_time: float
    ) -> EnrichmentResult:
        """
        Fallback vers l'API INSEE quand Pappers n'est pas disponible.
        Calcule un score de risque simplifie base sur les donnees INSEE.
        """
        try:
            insee_provider = INSEEProvider(self.tenant_id)
            insee_lookup_type = "siret" if len(cleaned_value) == 14 else "siren"
            result = await insee_provider.lookup(insee_lookup_type, cleaned_value)
            await insee_provider.close()

            if not result.success:
                return EnrichmentResult(
                    success=False,
                    source="pappers+insee",
                    error=result.error or "Entreprise non trouvee",
                    response_time_ms=self._measure_time(start_time),
                )

            # Convertir donnees INSEE vers format Pappers-like
            data = self._convert_insee_to_pappers(result.data)

            # Calculer le score de risque (simplifie sans procedures collectives)
            risk_data = self._calculate_risk_score_from_insee(result.data)
            data["risk_analysis"] = risk_data

            response_time = self._measure_time(start_time)
            logger.info(
                f"[PAPPERS+INSEE] Lookup {lookup_type}={cleaned_value} -> "
                f"{data.get('nom_entreprise', 'N/A')} "
                f"(risque: {risk_data.get('score', 'N/A')}) ({response_time}ms)"
            )

            return EnrichmentResult(
                success=True,
                data=data,
                confidence=0.8,  # Moins de confiance sans Pappers
                source="pappers+insee",
                response_time_ms=response_time,
            )

        except Exception as e:
            logger.exception(f"[PAPPERS+INSEE] Erreur fallback: {e}")
            return EnrichmentResult(
                success=False,
                source="pappers+insee",
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def _convert_insee_to_pappers(self, insee_data: dict) -> dict:
        """Convertit les donnees INSEE vers un format compatible Pappers."""
        siege = insee_data.get("siege", {})
        return {
            "siren": insee_data.get("siren", ""),
            "siret": siege.get("siret", ""),
            "nom_entreprise": insee_data.get("nom_complet", ""),
            "denomination": insee_data.get("nom_complet", ""),
            "date_creation": insee_data.get("date_creation"),
            "forme_juridique": insee_data.get("nature_juridique", ""),
            "code_naf": siege.get("activite_principale", ""),
            "tranche_effectif_salarie": insee_data.get("tranche_effectif_salarie"),
            "siege": {
                "siret": siege.get("siret", ""),
                "adresse_ligne_1": siege.get("adresse", siege.get("geo_adresse", "")),
                "code_postal": siege.get("code_postal", ""),
                "ville": siege.get("libelle_commune", ""),
                "etat_administratif": siege.get("etat_administratif", ""),
            },
            # Champs Pappers non disponibles via INSEE
            "procedures_collectives": [],
            "capital": None,
            "effectif": None,
            "cotation_banque_france": None,
            "_source": "insee_fallback",
        }

    def _calculate_risk_score_from_insee(self, insee_data: dict) -> dict[str, Any]:
        """
        Calcule un score de risque simplifie depuis les donnees INSEE.
        Sans Pappers, on n'a pas acces aux:
        - Procedures collectives
        - Cotation Banque de France
        - Donnees financieres detaillees
        """
        score = 100
        factors = []
        alerts = []

        siege = insee_data.get("siege", {})

        # 0. Statut de l'entreprise (niveau entreprise, pas seulement siege)
        # L'API INSEE renvoie etat_administratif au niveau entreprise aussi
        etat_entreprise = insee_data.get("etat_administratif", "").upper()
        statut_diffusion = insee_data.get("statut_diffusion", "").lower()

        # Verifier si entreprise dissoute/cessée (différent du siège fermé)
        if etat_entreprise == "C":  # Cessé = entreprise dissoute
            score -= 100  # Score minimum pour entreprise dissoute
            factors.append({
                "factor": "Entreprise dissoute/cessée",
                "impact": -100,
                "severity": "critical"
            })
            alerts.append("ENTREPRISE DISSOUTE")
        elif "partiel" in statut_diffusion:
            # Diffusion partielle = souvent signe de problemes
            score -= 10
            factors.append({
                "factor": "Diffusion partielle (données limitées)",
                "impact": -10,
                "severity": "low"
            })

        # 1. Statut administratif du siège
        etat = siege.get("etat_administratif", "").upper()
        if etat == "F":  # Ferme
            score -= 80
            factors.append({
                "factor": "Etablissement ferme",
                "impact": -80,
                "severity": "critical"
            })
            alerts.append("ETABLISSEMENT FERME")
        elif etat == "A" and etat_entreprise != "C":  # Actif (et entreprise non dissoute)
            factors.append({
                "factor": "Etablissement actif",
                "impact": 0,
                "severity": "positive"
            })

        # 2. Anciennete
        date_creation = insee_data.get("date_creation")
        if date_creation:
            try:
                creation = datetime.strptime(date_creation, "%Y-%m-%d")
                age_years = (datetime.now() - creation).days / 365.25

                if age_years < 1:
                    score -= 20
                    factors.append({
                        "factor": "Entreprise tres jeune (< 1 an)",
                        "impact": -20,
                        "severity": "medium"
                    })
                elif age_years < 2:
                    score -= 10
                    factors.append({
                        "factor": "Entreprise jeune (< 2 ans)",
                        "impact": -10,
                        "severity": "low"
                    })
                elif age_years < 5:
                    factors.append({
                        "factor": f"Entreprise recente ({int(age_years)} ans)",
                        "impact": 0,
                        "severity": "low"
                    })
                elif age_years > 10:
                    score += 5
                    factors.append({
                        "factor": f"Entreprise etablie ({int(age_years)} ans)",
                        "impact": 5,
                        "severity": "positive"
                    })
            except (ValueError, TypeError):
                pass

        # 3. Tranche effectif
        tranche = insee_data.get("tranche_effectif_salarie")
        if tranche:
            # Tranches INSEE: 00=0, 01=1-2, 02=3-5, 03=6-9, 11=10-19, etc.
            try:
                tranche_int = int(tranche)
                if tranche_int >= 21:  # 50+ salaries
                    score += 5
                    factors.append({
                        "factor": "Entreprise de taille significative",
                        "impact": 5,
                        "severity": "positive"
                    })
                elif tranche_int == 0:
                    score -= 5
                    factors.append({
                        "factor": "Pas de salaries declares",
                        "impact": -5,
                        "severity": "low"
                    })
            except ValueError:
                pass

        # Avertissement: donnees limitees
        factors.append({
            "factor": "Analyse basee sur donnees INSEE (limitees)",
            "impact": 0,
            "severity": "low",
            "source": "Avertissement"
        })

        # Borner le score
        score = max(0, min(100, score))

        # Determiner le niveau
        if score >= 80:
            level = "low"
            level_label = "Risque faible"
            color = "green"
        elif score >= 60:
            level = "medium"
            level_label = "Risque modere"
            color = "yellow"
        elif score >= 40:
            level = "elevated"
            level_label = "Risque eleve"
            color = "orange"
        else:
            level = "high"
            level_label = "Risque tres eleve"
            color = "red"

        return {
            "score": score,
            "level": level,
            "level_label": level_label,
            "color": color,
            "factors": factors,
            "alerts": alerts,
            "recommendation": self._get_recommendation(score, alerts),
            "cotation_bdf": None,
            "_limited_data": True,
            "_note": "Analyse simplifiee - Pappers non configure"
        }

    def _calculate_risk_score(self, data: dict) -> dict[str, Any]:
        """
        Calcule un score de risque basé sur les données disponibles.

        Facteurs de risque:
        - Cotation Banque de France (si disponible)
        - Entreprise radiee = risque maximum
        - Procedures collectives = risque eleve
        - Anciennete < 2 ans = risque modere
        - Pas de chiffre d'affaires = risque modere

        Score: 0-100 (0 = risque max, 100 = tres fiable)

        Returns:
            Dict avec score, niveau et details
        """
        score = 100
        factors = []
        alerts = []

        # 0. Cotation Banque de France (si disponible)
        cotation_bdf = data.get("cotation_banque_france")
        if cotation_bdf:
            bdf_score, bdf_factor = self._interpret_cotation_bdf(cotation_bdf)
            score += bdf_score
            factors.append(bdf_factor)
            if bdf_score < -20:
                alerts.append(f"COTATION BANQUE DE FRANCE: {cotation_bdf}")

        # 1. Statut de l'entreprise
        statut = data.get("statut_rcs", "").lower()
        date_radiation = data.get("date_radiation_rcs")
        date_dissolution = data.get("date_cessation") or data.get("date_dissolution")
        etat_administratif = data.get("etat_administratif", "").upper()

        # Entreprise dissoute = risque maximum
        if date_dissolution or "dissout" in statut or "dissol" in statut or etat_administratif == "C":
            score -= 100
            factors.append({
                "factor": "Entreprise dissoute",
                "impact": -100,
                "severity": "critical"
            })
            alerts.append("ENTREPRISE DISSOUTE")
        elif date_radiation or "radie" in statut:
            score -= 80
            factors.append({
                "factor": "Entreprise radiée",
                "impact": -80,
                "severity": "critical"
            })
            alerts.append("ENTREPRISE RADIEE DU RCS")
        elif "en sommeil" in statut or "cessation" in statut:
            score -= 40
            factors.append({
                "factor": "Entreprise en sommeil/cessation",
                "impact": -40,
                "severity": "high"
            })
            alerts.append("ACTIVITE EN SOMMEIL")

        # 2. Procedures collectives
        procedures = data.get("procedures_collectives", [])
        if procedures:
            # Verifier si procedure en cours
            for proc in procedures:
                proc_type = proc.get("type", "").lower()
                date_fin = proc.get("date_fin")

                if not date_fin:  # Procedure en cours
                    if "liquidation" in proc_type:
                        score -= 70
                        factors.append({
                            "factor": "Liquidation judiciaire en cours",
                            "impact": -70,
                            "severity": "critical"
                        })
                        alerts.append("LIQUIDATION JUDICIAIRE EN COURS")
                    elif "redressement" in proc_type:
                        score -= 50
                        factors.append({
                            "factor": "Redressement judiciaire en cours",
                            "impact": -50,
                            "severity": "high"
                        })
                        alerts.append("REDRESSEMENT JUDICIAIRE EN COURS")
                    elif "sauvegarde" in proc_type:
                        score -= 30
                        factors.append({
                            "factor": "Procedure de sauvegarde",
                            "impact": -30,
                            "severity": "medium"
                        })
                        alerts.append("PROCEDURE DE SAUVEGARDE")
                else:
                    # Procedure terminee - impact reduit
                    score -= 10
                    factors.append({
                        "factor": f"Antecedent: {proc_type}",
                        "impact": -10,
                        "severity": "low"
                    })

        # 3. Anciennete de l'entreprise
        date_creation = data.get("date_creation")
        if date_creation:
            try:
                creation = datetime.strptime(date_creation, "%Y-%m-%d")
                age_years = (datetime.now() - creation).days / 365.25

                if age_years < 1:
                    score -= 20
                    factors.append({
                        "factor": "Entreprise tres jeune (< 1 an)",
                        "impact": -20,
                        "severity": "medium"
                    })
                elif age_years < 2:
                    score -= 10
                    factors.append({
                        "factor": "Entreprise jeune (< 2 ans)",
                        "impact": -10,
                        "severity": "low"
                    })
                elif age_years > 10:
                    score += 5  # Bonus anciennete
                    factors.append({
                        "factor": f"Entreprise etablie ({int(age_years)} ans)",
                        "impact": 5,
                        "severity": "positive"
                    })
            except (ValueError, TypeError):
                pass

        # 4. Donnees financieres (si disponibles)
        finances = data.get("finances", [])
        derniers_comptes = data.get("derniers_comptes", {})

        if finances or derniers_comptes:
            # A des comptes publies = bon signe
            score += 5
            factors.append({
                "factor": "Comptes publies",
                "impact": 5,
                "severity": "positive"
            })

            # Verifier le resultat
            if derniers_comptes:
                resultat = derniers_comptes.get("resultat")
                if resultat is not None:
                    if resultat < 0:
                        score -= 15
                        factors.append({
                            "factor": "Resultat negatif",
                            "impact": -15,
                            "severity": "medium"
                        })
                    elif resultat > 0:
                        score += 5
                        factors.append({
                            "factor": "Resultat positif",
                            "impact": 5,
                            "severity": "positive"
                        })
        else:
            # Pas de comptes = risque modere
            score -= 5
            factors.append({
                "factor": "Aucun compte publie",
                "impact": -5,
                "severity": "low"
            })

        # 5. Capital social
        capital = data.get("capital")
        if capital:
            if capital < 1000:
                score -= 10
                factors.append({
                    "factor": f"Capital faible ({capital}€)",
                    "impact": -10,
                    "severity": "low"
                })
            elif capital >= 100000:
                score += 5
                factors.append({
                    "factor": f"Capital solide ({capital:,}€)",
                    "impact": 5,
                    "severity": "positive"
                })

        # 6. Effectif
        effectif = data.get("effectif")
        tranche = data.get("tranche_effectif")
        if effectif and effectif > 10:
            score += 5
            factors.append({
                "factor": f"Effectif: {effectif} salaries",
                "impact": 5,
                "severity": "positive"
            })

        # Borner le score entre 0 et 100
        score = max(0, min(100, score))

        # Determiner le niveau de risque
        if score >= 80:
            level = "low"
            level_label = "Risque faible"
            color = "green"
        elif score >= 60:
            level = "medium"
            level_label = "Risque modere"
            color = "yellow"
        elif score >= 40:
            level = "elevated"
            level_label = "Risque eleve"
            color = "orange"
        else:
            level = "high"
            level_label = "Risque tres eleve"
            color = "red"

        return {
            "score": score,
            "level": level,
            "level_label": level_label,
            "color": color,
            "factors": factors,
            "alerts": alerts,
            "recommendation": self._get_recommendation(score, alerts),
        }

    def _interpret_cotation_bdf(self, cotation: str) -> tuple[int, dict]:
        """
        Interprete la cotation Banque de France.

        Echelle BDF:
        - 3++ : Excellente capacite de remboursement
        - 3+  : Tres forte capacite
        - 3   : Forte capacite
        - 4+  : Assez forte capacite
        - 4   : Capacite acceptable
        - 5+  : Capacite assez faible
        - 5   : Capacite faible
        - 6   : Capacite tres faible
        - 7   : Capacite quasi nulle
        - 8   : Menace de defaillance
        - 9   : Situation tres compromise
        - P   : En procedure collective

        Returns:
            (score_impact, factor_dict)
        """
        cotation_map = {
            "3++": (15, "Excellente", "positive"),
            "3+": (10, "Tres forte", "positive"),
            "3": (5, "Forte", "positive"),
            "4+": (0, "Assez forte", "positive"),
            "4": (-5, "Acceptable", "low"),
            "5+": (-15, "Assez faible", "medium"),
            "5": (-25, "Faible", "medium"),
            "6": (-40, "Tres faible", "high"),
            "7": (-55, "Quasi nulle", "high"),
            "8": (-70, "Menace defaillance", "critical"),
            "9": (-80, "Compromise", "critical"),
            "P": (-80, "En procedure", "critical"),
        }

        # Normaliser la cotation
        cot = cotation.strip().upper()

        if cot in cotation_map:
            impact, label, severity = cotation_map[cot]
        else:
            # Cotation non reconnue
            return 0, {
                "factor": f"Cotation BDF: {cotation} (non interpretee)",
                "impact": 0,
                "severity": "low"
            }

        return impact, {
            "factor": f"Cotation Banque de France: {cotation} - {label}",
            "impact": impact,
            "severity": severity,
            "source": "Banque de France"
        }

    def _get_recommendation(self, score: int, alerts: list[str]) -> str:
        """Genere une recommandation basee sur le score et les alertes."""
        if any("RADIEE" in a or "LIQUIDATION" in a for a in alerts):
            return "NE PAS TRAVAILLER AVEC CETTE ENTREPRISE - Entreprise non viable"
        elif any("REDRESSEMENT" in a for a in alerts):
            return "PRUDENCE EXTREME - Demander des garanties de paiement"
        elif score >= 80:
            return "Partenaire fiable - Relations commerciales normales"
        elif score >= 60:
            return "Surveillance recommandee - Limiter les encours"
        elif score >= 40:
            return "Prudence - Paiement anticipe ou garanties"
        else:
            return "Risque eleve - Eviter ou exiger paiement comptant"

    def map_to_entity(
        self,
        entity_type: str,
        api_data: dict
    ) -> dict[str, Any]:
        """
        Mappe la reponse Pappers aux champs Contact.

        Args:
            entity_type: Doit etre 'contact'
            api_data: Reponse de l'API Pappers

        Returns:
            Dict des champs mappes pour Contact
        """
        if entity_type != "contact":
            return {}

        # Adresse siege
        siege = api_data.get("siege", {})

        # Construire l'adresse
        address_parts = []
        if siege.get("numero_voie"):
            address_parts.append(siege.get("numero_voie"))
        if siege.get("type_voie"):
            address_parts.append(siege.get("type_voie"))
        if siege.get("libelle_voie"):
            address_parts.append(siege.get("libelle_voie"))
        address_line = " ".join(address_parts) if address_parts else siege.get("adresse_ligne_1", "")

        # Risk analysis
        risk = api_data.get("risk_analysis", {})

        return {
            # Champs principaux
            "name": api_data.get("nom_entreprise", ""),
            "company_name": api_data.get("denomination", api_data.get("nom_entreprise", "")),
            "legal_name": api_data.get("denomination", ""),
            "siret": api_data.get("siret", siege.get("siret", "")),
            "siren": api_data.get("siren", ""),
            "registration_number": api_data.get("siret", siege.get("siret", "")),

            # Adresse
            "address_line1": address_line,
            "address_line2": siege.get("complement_adresse", ""),
            "postal_code": siege.get("code_postal", ""),
            "city": siege.get("ville", ""),
            "country": "France",
            "country_code": "FR",

            # Infos legales
            "legal_form": api_data.get("forme_juridique", ""),
            "industry_code": api_data.get("code_naf", ""),
            "industry_label": api_data.get("libelle_code_naf", ""),

            # Donnees financieres
            "capital": api_data.get("capital"),
            "effectif": api_data.get("effectif"),

            # Analyse de risque
            "risk_score": risk.get("score"),
            "risk_level": risk.get("level"),
            "risk_level_label": risk.get("level_label"),
            "risk_alerts": risk.get("alerts", []),
            "risk_recommendation": risk.get("recommendation"),

            # Metadonnees Pappers (prefixees _)
            "_pappers_siren": api_data.get("siren", ""),
            "_pappers_siret": api_data.get("siret", ""),
            "_pappers_date_creation": api_data.get("date_creation"),
            "_pappers_statut_rcs": api_data.get("statut_rcs"),
            "_pappers_procedures": api_data.get("procedures_collectives", []),
            "_pappers_risk_analysis": risk,
        }
