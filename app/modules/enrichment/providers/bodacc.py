"""
AZALS - Provider BODACC (Bulletin Officiel des Annonces Civiles et Commerciales)
================================================================================

Vérifie les annonces légales pour détecter:
- Dissolutions
- Liquidations judiciaires
- Redressements judiciaires
- Radiations
- Procédures collectives

API: https://bodacc-datadila.opendatasoft.com/api/v2/
Documentation: https://bodacc-datadila.opendatasoft.com/explore/dataset/bodacc-a/api/

Gratuit et sans authentification.
"""
from __future__ import annotations


import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from .base import BaseProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class BODACCProvider(BaseProvider):
    """
    Provider pour l'API BODACC (annonces légales).

    Détecte les événements critiques:
    - Dissolution
    - Liquidation judiciaire
    - Redressement judiciaire
    - Radiation
    - Vente/cession
    """

    PROVIDER_NAME = "bodacc"
    BASE_URL = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1"
    DATASET_ID = "annonces-commerciales"

    # Types d'annonces critiques (risque élevé)
    CRITICAL_TYPES = {
        "dissolution": "Entreprise dissoute",
        "liquidation": "Liquidation judiciaire",
        "clôture pour insuffisance d'actif": "Clôture pour insuffisance d'actif",
        "radiation": "Radiation du RCS",
        "jugement d'ouverture de liquidation": "Liquidation judiciaire ouverte",
        "jugement de clôture pour extinction du passif": "Liquidation clôturée",
    }

    # Types d'annonces à risque modéré
    WARNING_TYPES = {
        "redressement": "Redressement judiciaire",
        "sauvegarde": "Procédure de sauvegarde",
        "plan de continuation": "Plan de continuation",
        "plan de cession": "Plan de cession",
        "jugement d'ouverture de redressement": "Redressement judiciaire ouvert",
    }

    def __init__(self, config: Optional[dict] = None):
        """Initialise le provider BODACC."""
        super().__init__(config)
        self.timeout = 10.0

    async def lookup(
        self,
        lookup_type: str,
        lookup_value: str,
        **kwargs
    ) -> EnrichmentResult:
        """
        Recherche les annonces BODACC pour un SIREN/SIRET.

        Args:
            lookup_type: 'siren' ou 'siret'
            lookup_value: Numéro SIREN (9 chiffres) ou SIRET (14 chiffres)

        Returns:
            EnrichmentResult avec les annonces trouvées et analyse de risque
        """
        start_time = datetime.now()

        # Extraire le SIREN (9 premiers chiffres)
        cleaned = "".join(c for c in lookup_value if c.isdigit())
        if len(cleaned) >= 9:
            siren = cleaned[:9]
        else:
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="SIREN/SIRET invalide",
                response_time_ms=self._measure_time(start_time),
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Rechercher les annonces pour ce SIREN
                # API v2.1 avec dataset annonces-commerciales
                url = f"{self.BASE_URL}/catalog/datasets/{self.DATASET_ID}/records"
                params = {
                    "where": f"registre like '%{siren}%'",
                    "order_by": "dateparution DESC",
                    "limit": 50,  # Dernières 50 annonces
                }

                response = await client.get(url, params=params)
                response_time = self._measure_time(start_time)

                if response.status_code == 200:
                    data = response.json()
                    # API v2.1 utilise "results" au lieu de "records"
                    records = data.get("results", [])

                    # Analyser les annonces
                    analysis = self._analyze_announcements(records, siren)

                    logger.info(
                        f"[BODACC] SIREN {siren}: {len(records)} annonces, "
                        f"risque={analysis['risk_level']} ({response_time}ms)"
                    )

                    return EnrichmentResult(
                        success=True,
                        data={
                            "siren": siren,
                            "announcements_count": len(records),
                            "announcements": analysis["announcements"],
                            "risk_analysis": analysis,
                        },
                        confidence=0.95,  # BODACC = source officielle
                        source=self.PROVIDER_NAME,
                        response_time_ms=response_time,
                    )
                else:
                    logger.warning(f"[BODACC] Erreur API: {response.status_code}")
                    return EnrichmentResult(
                        success=False,
                        source=self.PROVIDER_NAME,
                        error=f"Erreur API BODACC: {response.status_code}",
                        response_time_ms=response_time,
                    )

        except httpx.TimeoutException:
            logger.warning(f"[BODACC] Timeout pour SIREN {siren}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error="Timeout API BODACC",
                response_time_ms=self._measure_time(start_time),
            )
        except Exception as e:
            logger.exception(f"[BODACC] Erreur: {e}")
            return EnrichmentResult(
                success=False,
                source=self.PROVIDER_NAME,
                error=f"Erreur: {str(e)}",
                response_time_ms=self._measure_time(start_time),
            )

    def _analyze_announcements(self, records: list, siren: str) -> dict[str, Any]:
        """
        Analyse les annonces BODACC et calcule le risque.

        Args:
            records: Liste des annonces BODACC
            siren: Numéro SIREN recherché

        Returns:
            Dict avec analyse de risque et détails
        """
        critical_alerts = []
        warning_alerts = []
        announcements = []

        for record in records:
            # API v2.1: fields are directly on record, not nested
            fields = record

            # Extraire les informations de l'annonce (API v2.1 format)
            date_parution = fields.get("dateparution", "")
            type_annonce = (fields.get("typeavis_lib", "") or "").lower()
            famille = (fields.get("familleavis_lib", "") or "").lower()

            # Le champ jugement contient les détails de la procédure (JSON string)
            jugement_raw = fields.get("jugement", "") or ""
            jugement_text = jugement_raw.lower() if isinstance(jugement_raw, str) else ""

            # Commercant pour le nom
            commercant = (fields.get("commercant", "") or "").lower()

            # Combiner pour recherche
            full_text = f"{type_annonce} {famille} {jugement_text} {commercant}"

            announcement_info = {
                "date": date_parution,
                "type": fields.get("typeavis_lib", ""),
                "famille": fields.get("familleavis_lib", ""),
                "commercant": fields.get("commercant", ""),
                "tribunal": fields.get("tribunal", ""),
            }

            # Vérifier les types critiques
            is_critical = False
            is_warning = False

            for keyword, label in self.CRITICAL_TYPES.items():
                if keyword in full_text:
                    is_critical = True
                    critical_alerts.append({
                        "type": label,
                        "date": date_parution,
                        "details": fields.get("typeavis_lib", ""),
                        "severity": "critical"
                    })
                    announcement_info["risk_type"] = "critical"
                    announcement_info["risk_label"] = label
                    break

            if not is_critical:
                for keyword, label in self.WARNING_TYPES.items():
                    if keyword in full_text:
                        is_warning = True
                        warning_alerts.append({
                            "type": label,
                            "date": date_parution,
                            "details": fields.get("typeavis_lib", ""),
                            "severity": "warning"
                        })
                        announcement_info["risk_type"] = "warning"
                        announcement_info["risk_label"] = label
                        break

            announcements.append(announcement_info)

        # Déterminer le niveau de risque global
        if critical_alerts:
            # Annonce critique trouvée = risque maximum
            risk_score = 0
            risk_level = "critical"
            risk_label = "Risque critique - Entreprise en difficulté majeure"

            # Trouver l'alerte la plus récente
            most_recent = critical_alerts[0] if critical_alerts else None
            risk_reason = most_recent["type"] if most_recent else "Annonce critique détectée"

        elif warning_alerts:
            # Annonce à surveiller = risque élevé
            risk_score = 30
            risk_level = "high"
            risk_label = "Risque élevé - Procédure en cours"

            most_recent = warning_alerts[0] if warning_alerts else None
            risk_reason = most_recent["type"] if most_recent else "Procédure collective détectée"

        else:
            # Pas d'annonce critique = pas de risque BODACC
            risk_score = 100
            risk_level = "none"
            risk_label = "Aucune alerte BODACC"
            risk_reason = None

        return {
            "score": risk_score,
            "risk_level": risk_level,
            "risk_label": risk_label,
            "risk_reason": risk_reason,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "announcements": announcements[:10],  # Limiter aux 10 plus récentes
            "total_announcements": len(records),
            "has_critical": len(critical_alerts) > 0,
            "has_warning": len(warning_alerts) > 0,
        }

    def map_to_entity(self, entity_type: str, api_data: dict) -> dict[str, Any]:
        """
        BODACC ne mappe pas directement vers une entité.
        Retourne les données de risque pour enrichissement.
        """
        risk = api_data.get("risk_analysis", {})
        return {
            "_bodacc_risk_score": risk.get("score"),
            "_bodacc_risk_level": risk.get("risk_level"),
            "_bodacc_risk_reason": risk.get("risk_reason"),
            "_bodacc_critical_alerts": len(risk.get("critical_alerts", [])),
            "_bodacc_warning_alerts": len(risk.get("warning_alerts", [])),
            "_bodacc_checked_at": datetime.now().isoformat(),
        }

    def _measure_time(self, start: datetime) -> float:
        """Calcule le temps écoulé en millisecondes."""
        return (datetime.now() - start).total_seconds() * 1000


# Instance singleton
_bodacc_provider: Optional[BODACCProvider] = None


def get_bodacc_provider() -> BODACCProvider:
    """Retourne l'instance singleton du provider BODACC."""
    global _bodacc_provider
    if _bodacc_provider is None:
        _bodacc_provider = BODACCProvider()
    return _bodacc_provider
