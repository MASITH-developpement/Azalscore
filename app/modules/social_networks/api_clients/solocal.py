"""
AZALS MODULE - Réseaux Sociaux - Solocal Client
===============================================
Client API pour Solocal (PagesJaunes)
"""
from __future__ import annotations


import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class SolocalClient(BaseAPIClient):
    """Client pour l'API Solocal / PagesJaunes."""

    PLATFORM_NAME = "solocal"
    OAUTH_REQUIRED = False  # Solocal utilise une clé API simple

    API_URL = "https://api.solocal.com/v1"

    @classmethod
    def get_oauth_config(cls) -> Optional[OAuthConfig]:
        """Solocal n'utilise pas OAuth."""
        return None

    def _make_auth_headers(self) -> dict[str, str]:
        """Headers d'authentification Solocal."""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.api_secret:
            headers["X-API-Secret"] = self.api_secret
        return headers

    async def test_connection(self) -> bool:
        """Teste la connexion à Solocal."""
        try:
            if not self.api_key:
                logger.error("[Solocal] Pas de clé API configurée")
                return False

            url = f"{self.API_URL}/establishments"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[Solocal] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (establishment_id)", self.PLATFORM_NAME)

        url = f"{self.API_URL}/establishments/{self.account_id}"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "establishment_id": self.account_id,
            "establishment_name": data.get("name", ""),
            "address": data.get("address", {}),
            "phone": data.get("phone", ""),
        }

    async def list_establishments(self) -> list[dict[str, str]]:
        """Liste les établissements du compte."""
        url = f"{self.API_URL}/establishments"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            raise APIClientError(f"Erreur listing: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return [
            {
                "establishment_id": est.get("id", ""),
                "establishment_name": est.get("name", ""),
                "city": est.get("address", {}).get("city", ""),
            }
            for est in data.get("establishments", [])
        ]

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques Solocal."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (establishment_id)", self.PLATFORM_NAME)

        url = f"{self.API_URL}/establishments/{self.account_id}/statistics"

        params = {
            "start_date": date_from.isoformat(),
            "end_date": date_to.isoformat(),
            "granularity": "day",
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        results = []

        for day_data in data.get("statistics", []):
            date_str = day_data.get("date", "")
            try:
                metrics_date = date.fromisoformat(date_str)
            except ValueError:
                continue

            results.append(MetricsData(
                platform=self.PLATFORM_NAME,
                metrics_date=metrics_date,
                impressions=day_data.get("impressions", 0),
                clicks=day_data.get("clicks", 0),
                calls=day_data.get("phone_clicks", 0),
                directions=day_data.get("itinerary_clicks", 0),
            ))

        return results

    async def get_reviews(self) -> dict[str, Any]:
        """Récupère les avis et la note moyenne."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (establishment_id)", self.PLATFORM_NAME)

        url = f"{self.API_URL}/establishments/{self.account_id}/reviews"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200:
            return {"reviews_count": 0, "average_rating": 0.0}

        data = response.json()
        reviews = data.get("reviews", [])

        avg_rating = data.get("average_rating", 0.0)
        if not avg_rating and reviews:
            total = sum(r.get("rating", 0) for r in reviews)
            avg_rating = total / len(reviews)

        return {
            "reviews_count": data.get("total_count", len(reviews)),
            "average_rating": avg_rating,
        }
