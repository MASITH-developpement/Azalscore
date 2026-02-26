"""
AZALS MODULE - Réseaux Sociaux - Base API Client
================================================
Classe de base pour tous les clients API marketing
"""
from __future__ import annotations


import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Erreur générique des clients API."""
    def __init__(self, message: str, platform: str, status_code: Optional[int] = None):
        self.message = message
        self.platform = platform
        self.status_code = status_code
        super().__init__(f"[{platform}] {message}")


@dataclass
class OAuthConfig:
    """Configuration OAuth pour une plateforme."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    auth_url: str
    token_url: str


@dataclass
class OAuthTokens:
    """Tokens OAuth."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"


@dataclass
class MetricsData:
    """Données de métriques récupérées."""
    platform: str
    metrics_date: date

    # Métriques communes
    impressions: int = 0
    clicks: int = 0
    reach: int = 0
    engagement: int = 0
    followers: int = 0

    # Taux
    ctr: float = 0.0
    engagement_rate: float = 0.0
    bounce_rate: float = 0.0
    conversion_rate: float = 0.0

    # Analytics
    sessions: int = 0
    users: int = 0
    pageviews: int = 0
    avg_session_duration: float = 0.0
    conversions: int = 0

    # Publicité
    cost: float = 0.0
    cpc: float = 0.0
    cpm: float = 0.0
    roas: float = 0.0

    # SEO
    avg_position: float = 0.0

    # Local
    calls: int = 0
    directions: int = 0
    reviews_count: int = 0
    rating: float = 0.0

    # Vidéo
    views: int = 0
    watch_time: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    subscribers: int = 0


class BaseAPIClient(ABC):
    """Classe de base pour les clients API marketing."""

    PLATFORM_NAME: str = "base"
    OAUTH_REQUIRED: bool = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        account_id: Optional[str] = None,
        property_id: Optional[str] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.account_id = account_id
        self.property_id = property_id
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    @property
    def http_client(self) -> httpx.AsyncClient:
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    @classmethod
    @abstractmethod
    def get_oauth_config(cls) -> Optional[OAuthConfig]:
        """Retourne la configuration OAuth pour cette plateforme."""
        pass

    @classmethod
    def get_auth_url(cls, state: str, redirect_uri: Optional[str] = None) -> Optional[str]:
        """Génère l'URL d'autorisation OAuth."""
        oauth_config = cls.get_oauth_config()
        if not oauth_config:
            return None

        redirect = redirect_uri or oauth_config.redirect_uri
        scopes = " ".join(oauth_config.scopes)

        return (
            f"{oauth_config.auth_url}"
            f"?client_id={oauth_config.client_id}"
            f"&redirect_uri={redirect}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&state={state}"
            f"&access_type=offline"
            f"&prompt=consent"
        )

    @classmethod
    async def exchange_code_for_tokens(
        cls,
        code: str,
        redirect_uri: Optional[str] = None
    ) -> OAuthTokens:
        """Échange le code d'autorisation contre des tokens."""
        oauth_config = cls.get_oauth_config()
        if not oauth_config:
            raise APIClientError("OAuth non configuré", cls.PLATFORM_NAME)

        redirect = redirect_uri or oauth_config.redirect_uri

        async with httpx.AsyncClient() as client:
            response = await client.post(
                oauth_config.token_url,
                data={
                    "client_id": oauth_config.client_id,
                    "client_secret": oauth_config.client_secret,
                    "code": code,
                    "redirect_uri": redirect,
                    "grant_type": "authorization_code",
                }
            )

            if response.status_code != 200:
                raise APIClientError(
                    f"Échec échange token: {response.text}",
                    cls.PLATFORM_NAME,
                    response.status_code
                )

            data = response.json()

            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.utcnow().replace(
                    microsecond=0
                ) + __import__("datetime").timedelta(seconds=data["expires_in"])

            return OAuthTokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_at=expires_at,
                token_type=data.get("token_type", "Bearer"),
            )

    async def refresh_access_token(self) -> OAuthTokens:
        """Rafraîchit le token d'accès."""
        if not self.refresh_token:
            raise APIClientError("Pas de refresh token", self.PLATFORM_NAME)

        oauth_config = self.get_oauth_config()
        if not oauth_config:
            raise APIClientError("OAuth non configuré", self.PLATFORM_NAME)

        response = await self.http_client.post(
            oauth_config.token_url,
            data={
                "client_id": oauth_config.client_id,
                "client_secret": oauth_config.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        )

        if response.status_code != 200:
            raise APIClientError(
                f"Échec refresh token: {response.text}",
                self.PLATFORM_NAME,
                response.status_code
            )

        data = response.json()

        self.access_token = data["access_token"]
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]

        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow().replace(
                microsecond=0
            ) + __import__("datetime").timedelta(seconds=data["expires_in"])

        return OAuthTokens(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_at=expires_at,
        )

    @abstractmethod
    async def test_connection(self) -> bool:
        """Teste la connexion à l'API."""
        pass

    @abstractmethod
    async def get_account_info(self) -> dict[str, Any]:
        """Récupère les informations du compte."""
        pass

    @abstractmethod
    async def fetch_metrics(
        self,
        date_from: date,
        date_to: date
    ) -> list[MetricsData]:
        """Récupère les métriques pour une période."""
        pass

    def _make_auth_headers(self) -> dict[str, str]:
        """Crée les headers d'authentification."""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
