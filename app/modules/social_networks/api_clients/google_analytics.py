"""
AZALS MODULE - Réseaux Sociaux - Google Analytics Client
========================================================
Client API pour Google Analytics 4 (GA4)
"""
from __future__ import annotations


import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class GoogleAnalyticsClient(BaseAPIClient):
    """Client pour l'API Google Analytics 4."""

    PLATFORM_NAME = "google_analytics"
    OAUTH_REQUIRED = True

    # URLs API
    GA4_API_URL = "https://analyticsdata.googleapis.com/v1beta"

    @classmethod
    def get_oauth_config(cls) -> Optional[OAuthConfig]:
        """Configuration OAuth Google."""
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://azalscore.com/oauth/callback/google")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=[
                "https://www.googleapis.com/auth/analytics.readonly",
            ],
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )

    async def test_connection(self) -> bool:
        """Teste la connexion à Google Analytics."""
        try:
            if not self.property_id:
                logger.error("[GA4] Pas de property_id configuré")
                return False

            # Test avec une requête simple
            url = f"{self.GA4_API_URL}/properties/{self.property_id}:runReport"
            response = await self.http_client.post(
                url,
                headers=self._make_auth_headers(),
                json={
                    "dateRanges": [{"startDate": "yesterday", "endDate": "yesterday"}],
                    "metrics": [{"name": "sessions"}],
                    "limit": 1
                }
            )

            if response.status_code == 200:
                logger.info("[GA4] Connexion réussie")
                return True
            else:
                logger.error(f"[GA4] Erreur connexion: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"[GA4] Exception test connexion: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte GA4."""
        if not self.property_id:
            raise APIClientError("Pas de property_id configuré", self.PLATFORM_NAME)

        # Utiliser l'API Admin pour obtenir les infos de propriété
        url = f"https://analyticsadmin.googleapis.com/v1beta/properties/{self.property_id}"

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers()
        )

        if response.status_code != 200:
            raise APIClientError(
                f"Erreur récupération compte: {response.text}",
                self.PLATFORM_NAME,
                response.status_code
            )

        data = response.json()
        return {
            "account_id": self.property_id,
            "account_name": data.get("displayName", ""),
            "property_id": self.property_id,
            "industry": data.get("industryCategory", ""),
            "timezone": data.get("timeZone", ""),
        }

    async def fetch_metrics(
        self,
        date_from: date,
        date_to: date
    ) -> list[MetricsData]:
        """Récupère les métriques GA4 pour une période."""
        if not self.property_id:
            raise APIClientError("Pas de property_id configuré", self.PLATFORM_NAME)

        url = f"{self.GA4_API_URL}/properties/{self.property_id}:runReport"

        # Requête pour les métriques principales
        payload = {
            "dateRanges": [{
                "startDate": date_from.isoformat(),
                "endDate": date_to.isoformat()
            }],
            "dimensions": [{"name": "date"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "screenPageViews"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
                {"name": "conversions"},
            ],
            "orderBys": [{"dimension": {"dimensionName": "date"}}]
        }

        response = await self.http_client.post(
            url,
            headers=self._make_auth_headers(),
            json=payload
        )

        if response.status_code != 200:
            raise APIClientError(
                f"Erreur fetch métriques: {response.text}",
                self.PLATFORM_NAME,
                response.status_code
            )

        data = response.json()
        results = []

        for row in data.get("rows", []):
            dimensions = row.get("dimensionValues", [])
            metrics_values = row.get("metricValues", [])

            if not dimensions or not metrics_values:
                continue

            # Parse la date (format YYYYMMDD)
            date_str = dimensions[0].get("value", "")
            try:
                metrics_date = date(
                    int(date_str[:4]),
                    int(date_str[4:6]),
                    int(date_str[6:8])
                )
            except (ValueError, IndexError):
                continue

            # Extraire les métriques
            def safe_int(idx: int) -> int:
                try:
                    return int(float(metrics_values[idx].get("value", 0)))
                except (IndexError, ValueError):
                    return 0

            def safe_float(idx: int) -> float:
                try:
                    return float(metrics_values[idx].get("value", 0))
                except (IndexError, ValueError):
                    return 0.0

            results.append(MetricsData(
                platform=self.PLATFORM_NAME,
                metrics_date=metrics_date,
                sessions=safe_int(0),
                users=safe_int(1),
                pageviews=safe_int(2),
                bounce_rate=safe_float(3) * 100,  # Convertir en pourcentage
                avg_session_duration=safe_float(4),
                conversions=safe_int(5),
            ))

        logger.info(f"[GA4] {len(results)} jours de métriques récupérés")
        return results

    async def list_properties(self) -> list[dict[str, str]]:
        """Liste les propriétés GA4 accessibles."""
        url = "https://analyticsadmin.googleapis.com/v1beta/accountSummaries"

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers()
        )

        if response.status_code != 200:
            raise APIClientError(
                f"Erreur listing propriétés: {response.text}",
                self.PLATFORM_NAME,
                response.status_code
            )

        data = response.json()
        properties = []

        for account in data.get("accountSummaries", []):
            for prop in account.get("propertySummaries", []):
                # Extraire l'ID numérique de la propriété
                prop_name = prop.get("property", "")
                prop_id = prop_name.replace("properties/", "") if prop_name else ""

                properties.append({
                    "property_id": prop_id,
                    "property_name": prop.get("displayName", ""),
                    "account_name": account.get("displayName", ""),
                })

        return properties
