"""
AZALS MODULE - Réseaux Sociaux - Google Ads Client
==================================================
Client API pour Google Ads
"""

import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class GoogleAdsClient(BaseAPIClient):
    """Client pour l'API Google Ads."""

    PLATFORM_NAME = "google_ads"
    OAUTH_REQUIRED = True

    API_URL = "https://googleads.googleapis.com/v14"

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
            scopes=["https://www.googleapis.com/auth/adwords"],
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )

    def _make_auth_headers(self) -> dict[str, str]:
        """Headers spécifiques Google Ads."""
        headers = super()._make_auth_headers()
        developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        if developer_token:
            headers["developer-token"] = developer_token
        if self.account_id:
            headers["login-customer-id"] = self.account_id
        return headers

    async def test_connection(self) -> bool:
        """Teste la connexion à Google Ads."""
        try:
            if not self.account_id:
                return False

            url = f"{self.API_URL}/customers/{self.account_id}"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[Google Ads] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte."""
        if not self.account_id:
            raise APIClientError("Pas de account_id", self.PLATFORM_NAME)

        url = f"{self.API_URL}/customers/{self.account_id}"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "account_id": self.account_id,
            "account_name": data.get("descriptiveName", ""),
            "currency": data.get("currencyCode", "EUR"),
        }

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques Google Ads."""
        if not self.account_id:
            raise APIClientError("Pas de account_id", self.PLATFORM_NAME)

        url = f"{self.API_URL}/customers/{self.account_id}/googleAds:searchStream"

        query = f"""
            SELECT
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date BETWEEN '{date_from.isoformat()}' AND '{date_to.isoformat()}'
        """

        response = await self.http_client.post(
            url,
            headers=self._make_auth_headers(),
            json={"query": query}
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        results = []
        for batch in response.json():
            for row in batch.get("results", []):
                segments = row.get("segments", {})
                metrics = row.get("metrics", {})

                date_str = segments.get("date", "")
                try:
                    metrics_date = date.fromisoformat(date_str)
                except ValueError:
                    continue

                cost_euros = metrics.get("costMicros", 0) / 1_000_000

                results.append(MetricsData(
                    platform=self.PLATFORM_NAME,
                    metrics_date=metrics_date,
                    impressions=metrics.get("impressions", 0),
                    clicks=metrics.get("clicks", 0),
                    cost=cost_euros,
                    conversions=int(metrics.get("conversions", 0)),
                    ctr=metrics.get("ctr", 0) * 100,
                    cpc=metrics.get("averageCpc", 0) / 1_000_000,
                ))

        return results
