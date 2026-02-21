"""
AZALS MODULE - Réseaux Sociaux - LinkedIn Client
=================================================
Client API pour LinkedIn Marketing
"""

import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class LinkedInClient(BaseAPIClient):
    """Client pour l'API LinkedIn."""

    PLATFORM_NAME = "linkedin"
    OAUTH_REQUIRED = True

    API_URL = "https://api.linkedin.com/v2"
    MARKETING_API_URL = "https://api.linkedin.com/rest"

    @classmethod
    def get_oauth_config(cls) -> Optional[OAuthConfig]:
        """Configuration OAuth LinkedIn."""
        client_id = os.getenv("LINKEDIN_CLIENT_ID")
        client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "https://azalscore.com/oauth/callback/linkedin")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=[
                "r_liteprofile",
                "r_organization_social",
                "rw_organization_admin",
                "r_organization_analytics",
            ],
            auth_url="https://www.linkedin.com/oauth/v2/authorization",
            token_url="https://www.linkedin.com/oauth/v2/accessToken",
        )

    def _make_auth_headers(self) -> dict[str, str]:
        """Headers LinkedIn avec version API."""
        headers = super()._make_auth_headers()
        headers["LinkedIn-Version"] = "202401"
        headers["X-Restli-Protocol-Version"] = "2.0.0"
        return headers

    async def test_connection(self) -> bool:
        """Teste la connexion à LinkedIn."""
        try:
            url = f"{self.API_URL}/me"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[LinkedIn] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du profil."""
        url = f"{self.API_URL}/me"
        params = {"projection": "(id,localizedFirstName,localizedLastName)"}

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "profile_id": data.get("id", ""),
            "first_name": data.get("localizedFirstName", ""),
            "last_name": data.get("localizedLastName", ""),
        }

    async def list_organizations(self) -> list[dict[str, str]]:
        """Liste les organisations administrées."""
        url = f"{self.API_URL}/organizationalEntityAcls"
        params = {
            "q": "roleAssignee",
            "projection": "(elements*(organizationalTarget~(localizedName,id)))",
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur listing orgs: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        organizations = []

        for element in data.get("elements", []):
            org = element.get("organizationalTarget~", {})
            org_urn = element.get("organizationalTarget", "")
            org_id = org_urn.split(":")[-1] if org_urn else ""

            organizations.append({
                "organization_id": org_id,
                "organization_name": org.get("localizedName", ""),
            })

        return organizations

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques de page d'organisation."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (organization_id)", self.PLATFORM_NAME)

        org_urn = f"urn:li:organization:{self.account_id}"

        # Métriques de followers
        followers_metrics = await self._fetch_follower_statistics(org_urn, date_from, date_to)

        # Métriques de page
        page_metrics = await self._fetch_page_statistics(org_urn, date_from, date_to)

        # Fusionner les métriques par date
        metrics_by_date: dict[date, MetricsData] = {}

        for m in followers_metrics + page_metrics:
            if m.metrics_date not in metrics_by_date:
                metrics_by_date[m.metrics_date] = m
            else:
                # Fusionner
                existing = metrics_by_date[m.metrics_date]
                existing.followers = m.followers or existing.followers
                existing.impressions = m.impressions or existing.impressions
                existing.engagement = m.engagement or existing.engagement
                existing.clicks = m.clicks or existing.clicks

        return list(metrics_by_date.values())

    async def _fetch_follower_statistics(
        self,
        org_urn: str,
        date_from: date,
        date_to: date
    ) -> list[MetricsData]:
        """Récupère les statistiques de followers."""
        url = f"{self.API_URL}/organizationalEntityFollowerStatistics"
        params = {
            "q": "organizationalEntity",
            "organizationalEntity": org_urn,
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            logger.error(f"[LinkedIn] Erreur followers stats: {response.text}")
            return []

        data = response.json()
        results = []

        for element in data.get("elements", []):
            # Les stats sont agrégées, on crée une entrée pour aujourd'hui
            total_followers = element.get("followerCounts", {}).get("organicFollowerCount", 0)

            results.append(MetricsData(
                platform=self.PLATFORM_NAME,
                metrics_date=date.today(),
                followers=total_followers,
            ))

        return results

    async def _fetch_page_statistics(
        self,
        org_urn: str,
        date_from: date,
        date_to: date
    ) -> list[MetricsData]:
        """Récupère les statistiques de page."""
        url = f"{self.API_URL}/organizationPageStatistics"
        params = {
            "q": "organization",
            "organization": org_urn,
            "timeIntervals.timeGranularityType": "DAY",
            "timeIntervals.timeRange.start": int(date_from.strftime("%s")) * 1000,
            "timeIntervals.timeRange.end": int(date_to.strftime("%s")) * 1000,
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            logger.error(f"[LinkedIn] Erreur page stats: {response.text}")
            return []

        data = response.json()
        results = []

        for element in data.get("elements", []):
            time_range = element.get("timeRange", {})
            start_ts = time_range.get("start", 0) / 1000

            try:
                from datetime import datetime
                metrics_date = datetime.fromtimestamp(start_ts).date()
            except (ValueError, OSError):
                continue

            total_stats = element.get("totalPageStatistics", {})
            views = total_stats.get("views", {})
            clicks = total_stats.get("clicks", {})

            results.append(MetricsData(
                platform=self.PLATFORM_NAME,
                metrics_date=metrics_date,
                impressions=views.get("allPageViews", {}).get("pageViews", 0),
                clicks=clicks.get("careersPageClicks", {}).get("careersPageClicks", 0) +
                       clicks.get("mobileCustomButtonClickCounts", 0),
            ))

        return results
