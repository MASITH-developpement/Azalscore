"""
AZALS MODULE - Réseaux Sociaux - Meta Business Client
=====================================================
Client API pour Meta Business Suite (Facebook, Instagram)
"""

import logging
import os
from datetime import date
from typing import Any, Optional

from .base import BaseAPIClient, APIClientError, OAuthConfig, MetricsData

logger = logging.getLogger(__name__)


class MetaBusinessClient(BaseAPIClient):
    """Client pour l'API Meta Business (Facebook/Instagram)."""

    PLATFORM_NAME = "meta_business"
    OAUTH_REQUIRED = True

    API_URL = "https://graph.facebook.com/v18.0"

    @classmethod
    def get_oauth_config(cls) -> Optional[OAuthConfig]:
        """Configuration OAuth Meta."""
        client_id = os.getenv("META_APP_ID")
        client_secret = os.getenv("META_APP_SECRET")
        redirect_uri = os.getenv("META_REDIRECT_URI", "https://azalscore.com/oauth/callback/meta")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=[
                "pages_show_list",
                "pages_read_engagement",
                "pages_read_user_content",
                "instagram_basic",
                "instagram_manage_insights",
                "ads_read",
            ],
            auth_url="https://www.facebook.com/v18.0/dialog/oauth",
            token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        )

    async def test_connection(self) -> bool:
        """Teste la connexion à Meta Business."""
        try:
            url = f"{self.API_URL}/me"
            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers()
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"[Meta] Exception: {e}")
            return False

    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte."""
        # Info utilisateur
        url = f"{self.API_URL}/me"
        params = {"fields": "id,name,email"}

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return {
            "user_id": data.get("id", ""),
            "user_name": data.get("name", ""),
            "email": data.get("email", ""),
        }

    async def list_pages(self) -> list[dict[str, str]]:
        """Liste les pages Facebook accessibles."""
        url = f"{self.API_URL}/me/accounts"
        params = {"fields": "id,name,access_token,category"}

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            raise APIClientError(f"Erreur listing pages: {response.text}", self.PLATFORM_NAME, response.status_code)

        data = response.json()
        return [
            {
                "page_id": page.get("id", ""),
                "page_name": page.get("name", ""),
                "category": page.get("category", ""),
            }
            for page in data.get("data", [])
        ]

    async def list_instagram_accounts(self) -> list[dict[str, str]]:
        """Liste les comptes Instagram Business liés."""
        pages = await self.list_pages()
        instagram_accounts = []

        for page in pages:
            page_id = page.get("page_id")
            if not page_id:
                continue

            url = f"{self.API_URL}/{page_id}"
            params = {"fields": "instagram_business_account{id,username,name}"}

            response = await self.http_client.get(
                url,
                headers=self._make_auth_headers(),
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                ig_account = data.get("instagram_business_account", {})
                if ig_account:
                    instagram_accounts.append({
                        "instagram_id": ig_account.get("id", ""),
                        "username": ig_account.get("username", ""),
                        "name": ig_account.get("name", ""),
                        "linked_page": page.get("page_name", ""),
                    })

        return instagram_accounts

    async def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques Facebook/Instagram."""
        if not self.account_id:
            raise APIClientError("Pas de account_id (page_id)", self.PLATFORM_NAME)

        results = []

        # Métriques de la page Facebook
        fb_metrics = await self._fetch_page_insights(date_from, date_to)
        results.extend(fb_metrics)

        return results

    async def _fetch_page_insights(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les insights de page Facebook."""
        url = f"{self.API_URL}/{self.account_id}/insights"

        # Métriques à récupérer
        metrics = [
            "page_impressions",
            "page_impressions_unique",
            "page_engaged_users",
            "page_post_engagements",
            "page_fans",
        ]

        params = {
            "metric": ",".join(metrics),
            "period": "day",
            "since": date_from.isoformat(),
            "until": date_to.isoformat(),
        }

        response = await self.http_client.get(
            url,
            headers=self._make_auth_headers(),
            params=params
        )

        if response.status_code != 200:
            logger.error(f"[Meta] Erreur insights: {response.text}")
            return []

        data = response.json()

        # Agréger par date
        metrics_by_date: dict[date, MetricsData] = {}

        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name", "")

            for value_data in metric_data.get("values", []):
                end_time = value_data.get("end_time", "")
                try:
                    metrics_date = date.fromisoformat(end_time[:10])
                except ValueError:
                    continue

                if metrics_date not in metrics_by_date:
                    metrics_by_date[metrics_date] = MetricsData(
                        platform=self.PLATFORM_NAME,
                        metrics_date=metrics_date,
                    )

                value = value_data.get("value", 0)

                if metric_name == "page_impressions":
                    metrics_by_date[metrics_date].impressions = value
                elif metric_name == "page_impressions_unique":
                    metrics_by_date[metrics_date].reach = value
                elif metric_name == "page_engaged_users":
                    metrics_by_date[metrics_date].engagement = value
                elif metric_name == "page_fans":
                    metrics_by_date[metrics_date].followers = value

        return list(metrics_by_date.values())

    async def fetch_ads_metrics(self, date_from: date, date_to: date) -> list[MetricsData]:
        """Récupère les métriques publicitaires Meta Ads."""
        if not self.account_id:
            raise APIClientError("Pas de account_id", self.PLATFORM_NAME)

        # Récupérer l'ad account associé
        url = f"{self.API_URL}/me/adaccounts"
        response = await self.http_client.get(url, headers=self._make_auth_headers())

        if response.status_code != 200 or not response.json().get("data"):
            return []

        ad_accounts = response.json().get("data", [])
        results = []

        for ad_account in ad_accounts:
            ad_account_id = ad_account.get("id", "")

            insights_url = f"{self.API_URL}/{ad_account_id}/insights"
            params = {
                "fields": "impressions,clicks,spend,ctr,cpc,reach,conversions",
                "time_range": f'{{"since":"{date_from.isoformat()}","until":"{date_to.isoformat()}"}}',
                "time_increment": 1,  # Quotidien
            }

            insights_response = await self.http_client.get(
                insights_url,
                headers=self._make_auth_headers(),
                params=params
            )

            if insights_response.status_code != 200:
                continue

            for row in insights_response.json().get("data", []):
                date_str = row.get("date_start", "")
                try:
                    metrics_date = date.fromisoformat(date_str)
                except ValueError:
                    continue

                results.append(MetricsData(
                    platform=f"{self.PLATFORM_NAME}_ads",
                    metrics_date=metrics_date,
                    impressions=int(row.get("impressions", 0)),
                    clicks=int(row.get("clicks", 0)),
                    reach=int(row.get("reach", 0)),
                    cost=float(row.get("spend", 0)),
                    ctr=float(row.get("ctr", 0)),
                    cpc=float(row.get("cpc", 0)),
                    conversions=int(row.get("conversions", 0)) if row.get("conversions") else 0,
                ))

        return results
