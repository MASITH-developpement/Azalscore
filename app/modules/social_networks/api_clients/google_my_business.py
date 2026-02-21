"""
AZALS MODULE - Réseaux Sociaux - Google My Business Client
==========================================================
Client API pour Google Business Profile (anciennement Google My Business)
"""

import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class GoogleMyBusinessClient(BaseAPIClient):
    """Client pour l'API Google Business Profile."""

    PLATFORM_NAME = "google_my_business"
    OAUTH_REQUIRED = True

    # APIs Google Business Profile
    BUSINESS_API_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"
    PERFORMANCE_API_URL = "https://businessprofileperformance.googleapis.com/v1"

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
            scopes=["https://www.googleapis.com/auth/business.manage"],
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )

    async def test_connection(self) -> bool:
        """Teste la connexion à Google Business Profile."""
        try:
            url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[GMB] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte."""
        if not self.account_id:
            raise APIClientError("Pas de account_id", self.PLATFORM_NAME)

        url = f"{self.BUSINESS_API_URL}/locations/{self.account_id}"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "location_id": self.account_id,
            "location_name": data.get("title", ""),
            "address": data.get("storefrontAddress", {}).get("addressLines", []),
        }

    async def list_locations(self) -> list[dict[str, str]]:
        """Liste les établissements accessibles."""
        # D'abord récupérer les comptes
        accounts_url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
        response = await self.http_client.get(accounts_url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur listing comptes: {response.text}", self.PLATFORM_NAME, response.status_code)

        accounts_data = response.json()
        locations = []

        for account in accounts_data.get("accounts", []):
            account_name = account.get("name", "")

            # Récupérer les locations de ce compte
            locations_url = f"{self.BUSINESS_API_URL}/{account_name}/locations"
            loc_response = await self.http_client.get(locations_url, headers=self._make_auth_headers())

            if loc_response.status_code == 200:
                loc_data = loc_response.json()
                for loc in loc_data.get("locations", []):
                    locations.append({
                        "location_id": loc.get("name", "").split("/")[-1],
                        "location_name": loc.get("title", ""),
                        "account_name": account.get("accountName", ""),
                    })

        return locations

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques Google Business Profile."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (location_id)", self.PLATFORM_NAME)

        url = f"{self.PERFORMANCE_API_URL}/locations/{self.account_id}:getDailyMetricsTimeSeries"

        # Les métriques disponibles
        daily_metrics = [
            "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
            "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
            "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
            "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
            "CALL_CLICKS",
            "WEBSITE_CLICKS",
            "BUSINESS_DIRECTION_REQUESTS",
        ]

        params = {
            "dailyRange.start_date.year": date_from.year,
            "dailyRange.start_date.month": date_from.month,
            "dailyRange.start_date.day": date_from.day,
            "dailyRange.end_date.year": date_to.year,
            "dailyRange.end_date.month": date_to.month,
            "dailyRange.end_date.day": date_to.day,
            "dailyMetrics": daily_metrics,
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()

        # Agréger les métriques par date
        metrics_by_date: dict[date, MetricsData] = {}

        for time_series in data.get("timeSeries", []):
            metric_name = time_series.get("dailyMetric", "")

            for point in time_series.get("dailySubEntityType", {}).get("timeSeriesValue", {}).get("values", []):
                date_info = point.get("date", {})
                try:
                    metrics_date = date(
                        date_info.get("year", 2000),
                        date_info.get("month", 1),
                        date_info.get("day", 1)
                    )
                except ValueError:
                    continue

                if metrics_date not in metrics_by_date:
                    metrics_by_date[metrics_date] = MetricsData(
                        platform=self.PLATFORM_NAME,
                        metrics_date=metrics_date,
                    )

                value = int(point.get("value", 0))

                if "IMPRESSIONS" in metric_name:
                    metrics_by_date[metrics_date].impressions += value
                elif metric_name == "CALL_CLICKS":
                    metrics_by_date[metrics_date].calls = value
                elif metric_name == "WEBSITE_CLICKS":
                    metrics_by_date[metrics_date].clicks = value
                elif metric_name == "BUSINESS_DIRECTION_REQUESTS":
                    metrics_by_date[metrics_date].directions = value

        return list(metrics_by_date.values())

    async def get_reviews(self) -> dict[str, Any]:
        """Récupère les avis et la note moyenne."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (location_id)", self.PLATFORM_NAME)

        url = f"https://mybusiness.googleapis.com/v4/accounts/{self.account_id}/locations/{self.account_id}/reviews"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            return {"reviews_count": 0, "average_rating": 0.0}

        data = response.json()
        reviews = data.get("reviews", [])

        total_rating = sum(r.get("starRating", 0) for r in reviews)
        avg_rating = total_rating / len(reviews) if reviews else 0.0

        return {
            "reviews_count": len(reviews),
            "average_rating": avg_rating,
        }
