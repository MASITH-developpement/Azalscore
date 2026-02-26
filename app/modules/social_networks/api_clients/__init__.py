"""
AZALS MODULE - Réseaux Sociaux - API Clients
============================================
Clients API pour récupérer les métriques des plateformes marketing
"""

from .base import BaseAPIClient, APIClientError, OAuthConfig
from .google_analytics import GoogleAnalyticsClient
from .google_ads import GoogleAdsClient
from .google_search_console import GoogleSearchConsoleClient
from .google_my_business import GoogleMyBusinessClient
from .meta_business import MetaBusinessClient
from .linkedin import LinkedInClient
from .solocal import SolocalClient

__all__ = [
    "BaseAPIClient",
    "APIClientError",
    "OAuthConfig",
    "GoogleAnalyticsClient",
    "GoogleAdsClient",
    "GoogleSearchConsoleClient",
    "GoogleMyBusinessClient",
    "MetaBusinessClient",
    "LinkedInClient",
    "SolocalClient",
]
