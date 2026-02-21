"""
AZALS MODULE - Réseaux Sociaux - Google Search Console Client
=============================================================
Client API pour Google Search Console
"""

import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class GoogleSearchConsoleClient(BaseAPIClient):
    """Client pour l'API Google Search Console."""

    PLATFORM_NAME = "google_search_console"
    OAUTH_REQUIRED = True

    API_URL = "https://searchconsole.googleapis.com/webmasters/v3"

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
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )

    async def test_connection(self) -> bool:
        """Teste la connexion à Search Console."""
        try:
            url = f"{self.API_URL}/sites"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[Search Console] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du site."""
        if not self.property_id:
            raise APIClientError("Pas de property_id (URL du site)", self.PLATFORM_NAME)

        url = f"{self.API_URL}/sites/{self.property_id}"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "site_url": data.get("siteUrl", self.property_id),
            "permission_level": data.get("permissionLevel", ""),
        }

    async def list_sites(self) -> list[dict[str, str]]:
        """Liste les sites accessibles."""
        url = f"{self.API_URL}/sites"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return [
            {
                "site_url": site.get("siteUrl", ""),
                "permission_level": site.get("permissionLevel", ""),
            }
            for site in data.get("siteEntry", [])
        ]

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques Search Console."""
        if not self.property_id:
            raise APIClientError("Pas de property_id (URL du site)", self.PLATFORM_NAME)

        # L'URL doit être encodée
        import urllib.parse
        encoded_url = urllib.parse.quote(self.property_id, safe="")

        url = f"{self.API_URL}/sites/{encoded_url}/searchAnalytics/query"

        payload = {
            "startDate": date_from.isoformat(),
            "endDate": date_to.isoformat(),
            "dimensions": ["date"],
            "rowLimit": 1000,
        }

        response = await self.http_client.post(
            url,
            headers=self._make_auth_headers(),
            json=payload
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        results = []

        for row in data.get("rows", []):
            keys = row.get("keys", [])
            if not keys:
                continue

            try:
                metrics_date = date.fromisoformat(keys[0])
            except ValueError:
                continue

            results.append(MetricsData(
                platform=self.PLATFORM_NAME,
                metrics_date=metrics_date,
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=row.get("ctr", 0) * 100,  # Convertir en pourcentage
                avg_position=row.get("position", 0),
            ))

        return results
