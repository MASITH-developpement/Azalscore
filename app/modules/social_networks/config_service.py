"""
AZALS MODULE - Réseaux Sociaux - Service de Configuration
=========================================================
Gestion des configurations de plateformes et synchronisation automatique
"""
from __future__ import annotations


import logging
import secrets
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .models import MarketingPlatform, SocialNetworkConfig, SocialNetworkMetrics
from .config_schemas import (
    PlatformConfigCreate, PlatformConfigUpdate, PlatformConfigResponse,
    PlatformStatus, AllPlatformsStatus, OAuthCallbackResponse
)
from .api_clients import (
    BaseAPIClient, APIClientError,
    GoogleAnalyticsClient, GoogleAdsClient, GoogleSearchConsoleClient,
    GoogleMyBusinessClient, MetaBusinessClient, LinkedInClient, SolocalClient
)

logger = logging.getLogger(__name__)

# Mapping plateforme -> client API
PLATFORM_CLIENTS: dict[MarketingPlatform, type[BaseAPIClient]] = {
    MarketingPlatform.GOOGLE_ANALYTICS: GoogleAnalyticsClient,
    MarketingPlatform.GOOGLE_ADS: GoogleAdsClient,
    MarketingPlatform.GOOGLE_SEARCH_CONSOLE: GoogleSearchConsoleClient,
    MarketingPlatform.GOOGLE_MY_BUSINESS: GoogleMyBusinessClient,
    MarketingPlatform.META_FACEBOOK: MetaBusinessClient,
    MarketingPlatform.META_INSTAGRAM: MetaBusinessClient,
    MarketingPlatform.LINKEDIN: LinkedInClient,
    MarketingPlatform.SOLOCAL: SolocalClient,
}

# Noms lisibles des plateformes
PLATFORM_NAMES: dict[MarketingPlatform, str] = {
    MarketingPlatform.GOOGLE_ANALYTICS: "Google Analytics 4",
    MarketingPlatform.GOOGLE_ADS: "Google Ads",
    MarketingPlatform.GOOGLE_SEARCH_CONSOLE: "Google Search Console",
    MarketingPlatform.GOOGLE_MY_BUSINESS: "Google Business Profile",
    MarketingPlatform.META_FACEBOOK: "Facebook",
    MarketingPlatform.META_INSTAGRAM: "Instagram",
    MarketingPlatform.LINKEDIN: "LinkedIn",
    MarketingPlatform.SOLOCAL: "Solocal / PagesJaunes",
    MarketingPlatform.TWITTER: "Twitter / X",
    MarketingPlatform.TIKTOK: "TikTok",
    MarketingPlatform.YOUTUBE: "YouTube",
}

# Cache d'états OAuth (en production, utiliser Redis)
_oauth_states: dict[str, dict[str, Any]] = {}


class ConfigService:
    """Service de gestion des configurations de plateformes."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # === CRUD Configuration ===

    def get_all_configs(self) -> list[SocialNetworkConfig]:
        """Récupère toutes les configurations du tenant."""
        return self.db.query(SocialNetworkConfig).filter(
            SocialNetworkConfig.tenant_id == self.tenant_id
        ).all()

    def get_config(self, platform: MarketingPlatform) -> Optional[SocialNetworkConfig]:
        """Récupère la configuration d'une plateforme."""
        return self.db.query(SocialNetworkConfig).filter(
            SocialNetworkConfig.tenant_id == self.tenant_id,
            SocialNetworkConfig.platform == platform
        ).first()

    def create_or_update_config(
        self,
        platform: MarketingPlatform,
        data: PlatformConfigCreate | PlatformConfigUpdate
    ) -> SocialNetworkConfig:
        """Crée ou met à jour la configuration d'une plateforme."""
        config = self.get_config(platform)

        if not config:
            config = SocialNetworkConfig(
                tenant_id=self.tenant_id,
                platform=platform
            )
            self.db.add(config)

        # Mise à jour des champs
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            if hasattr(config, key) and key != "platform":
                setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)

        return config

    def delete_config(self, platform: MarketingPlatform) -> bool:
        """Supprime la configuration d'une plateforme."""
        config = self.get_config(platform)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        return True

    # === OAuth ===

    def init_oauth(self, platform: MarketingPlatform, redirect_uri: Optional[str] = None) -> dict[str, str]:
        """Initialise le flux OAuth pour une plateforme."""
        client_class = PLATFORM_CLIENTS.get(platform)
        if not client_class:
            raise APIClientError(f"Plateforme non supportée: {platform}", str(platform))

        # Générer un state unique
        state = secrets.token_urlsafe(32)

        # Stocker le state (en production, utiliser Redis avec TTL)
        _oauth_states[state] = {
            "platform": platform,
            "tenant_id": self.tenant_id,
            "created_at": datetime.utcnow(),
        }

        # Générer l'URL d'autorisation
        auth_url = client_class.get_auth_url(state, redirect_uri)
        if not auth_url:
            raise APIClientError("OAuth non configuré pour cette plateforme", str(platform))

        return {
            "auth_url": auth_url,
            "state": state,
            "platform": platform.value,
        }

    async def handle_oauth_callback(
        self,
        platform: MarketingPlatform,
        code: str,
        state: str
    ) -> OAuthCallbackResponse:
        """Traite le callback OAuth."""
        # Vérifier le state
        state_data = _oauth_states.pop(state, None)
        if not state_data:
            return OAuthCallbackResponse(
                success=False,
                platform=platform,
                message="État OAuth invalide ou expiré"
            )

        if state_data["platform"] != platform:
            return OAuthCallbackResponse(
                success=False,
                platform=platform,
                message="Plateforme OAuth incohérente"
            )

        # Récupérer le client
        client_class = PLATFORM_CLIENTS.get(platform)
        if not client_class:
            return OAuthCallbackResponse(
                success=False,
                platform=platform,
                message="Plateforme non supportée"
            )

        try:
            # Échanger le code contre des tokens
            tokens = await client_class.exchange_code_for_tokens(code)

            # Sauvegarder les tokens
            config = self.get_config(platform) or SocialNetworkConfig(
                tenant_id=self.tenant_id,
                platform=platform
            )

            config.access_token = tokens.access_token
            config.refresh_token = tokens.refresh_token
            config.is_enabled = True
            config.last_error = None
            config.updated_at = datetime.utcnow()

            if not self.get_config(platform):
                self.db.add(config)

            self.db.commit()

            # Tester la connexion et récupérer les infos du compte
            async with client_class(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token
            ) as client:
                if await client.test_connection():
                    try:
                        account_info = await client.get_account_info()
                        return OAuthCallbackResponse(
                            success=True,
                            platform=platform,
                            message="Connexion établie avec succès",
                            account_id=account_info.get("account_id") or account_info.get("property_id"),
                            account_name=account_info.get("account_name") or account_info.get("property_name"),
                        )
                    except Exception:
                        pass

            return OAuthCallbackResponse(
                success=True,
                platform=platform,
                message="Tokens récupérés avec succès"
            )

        except Exception as e:
            logger.error(f"Erreur OAuth callback pour {platform}: {e}")
            return OAuthCallbackResponse(
                success=False,
                platform=platform,
                message=f"Erreur: {str(e)}"
            )

    # === Statut des plateformes ===

    def get_platform_status(self, platform: MarketingPlatform) -> PlatformStatus:
        """Récupère le statut d'une plateforme."""
        config = self.get_config(platform)

        status = PlatformStatus(
            platform=platform,
            name=PLATFORM_NAMES.get(platform, platform.value),
        )

        if config:
            status.is_configured = True
            status.is_enabled = config.is_enabled
            status.is_connected = bool(config.access_token or config.api_key)
            status.last_sync_at = config.last_sync_at
            status.error_message = config.last_error
            status.account_id = config.account_id or config.property_id

            if config.last_sync_at:
                if config.last_error:
                    status.sync_status = "error"
                else:
                    status.sync_status = "success"

        return status

    def get_all_platforms_status(self) -> AllPlatformsStatus:
        """Récupère le statut de toutes les plateformes."""
        platforms = []
        total_configured = 0
        total_connected = 0
        last_sync = None

        for platform in MarketingPlatform:
            status = self.get_platform_status(platform)
            platforms.append(status)

            if status.is_configured:
                total_configured += 1
            if status.is_connected:
                total_connected += 1
            if status.last_sync_at:
                if not last_sync or status.last_sync_at > last_sync:
                    last_sync = status.last_sync_at

        return AllPlatformsStatus(
            platforms=platforms,
            total_configured=total_configured,
            total_connected=total_connected,
            last_global_sync=last_sync,
        )

    # === Synchronisation ===

    async def sync_platform(
        self,
        platform: MarketingPlatform,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict[str, Any]:
        """Synchronise les métriques d'une plateforme."""
        config = self.get_config(platform)
        if not config:
            return {"success": False, "error": "Plateforme non configurée", "records": 0}

        if not config.is_enabled:
            return {"success": False, "error": "Plateforme désactivée", "records": 0}

        if not config.access_token and not config.api_key:
            return {"success": False, "error": "Pas de credentials", "records": 0}

        # Dates par défaut : hier
        if not date_to:
            date_to = date.today() - timedelta(days=1)
        if not date_from:
            date_from = date_to - timedelta(days=6)  # 7 jours

        client_class = PLATFORM_CLIENTS.get(platform)
        if not client_class:
            return {"success": False, "error": "Client API non disponible", "records": 0}

        try:
            async with client_class(
                access_token=config.access_token,
                refresh_token=config.refresh_token,
                api_key=config.api_key,
                api_secret=config.api_secret,
                account_id=config.account_id,
                property_id=config.property_id,
            ) as client:
                # Récupérer les métriques
                metrics_list = await client.fetch_metrics(date_from, date_to)

                records_saved = 0
                for metrics_data in metrics_list:
                    # Sauvegarder en base
                    self._save_metrics(platform, metrics_data)
                    records_saved += 1

                # Mettre à jour le statut de sync
                config.last_sync_at = datetime.utcnow()
                config.last_error = None
                self.db.commit()

                logger.info(f"[{platform.value}] {records_saved} enregistrements synchronisés")
                return {"success": True, "records": records_saved}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{platform.value}] Erreur sync: {error_msg}")

            config.last_error = error_msg
            self.db.commit()

            return {"success": False, "error": error_msg, "records": 0}

    def _save_metrics(self, platform: MarketingPlatform, metrics_data: Any) -> None:
        """Sauvegarde les métriques en base."""
        # Chercher une entrée existante
        existing = self.db.query(SocialNetworkMetrics).filter(
            SocialNetworkMetrics.tenant_id == self.tenant_id,
            SocialNetworkMetrics.platform == platform,
            SocialNetworkMetrics.metrics_date == metrics_data.metrics_date
        ).first()

        if existing:
            # Mise à jour
            for field in [
                "impressions", "clicks", "reach", "engagement", "followers",
                "ctr", "engagement_rate", "bounce_rate", "conversion_rate",
                "sessions", "users", "pageviews", "avg_session_duration", "conversions",
                "cost", "cpc", "cpm", "roas", "avg_position",
                "calls", "directions", "reviews_count", "rating",
                "views", "watch_time", "likes", "shares", "comments", "subscribers"
            ]:
                value = getattr(metrics_data, field, None)
                if value is not None and value != 0:
                    setattr(existing, field, value)
            existing.updated_at = datetime.utcnow()
        else:
            # Création
            new_metrics = SocialNetworkMetrics(
                tenant_id=self.tenant_id,
                platform=platform,
                metrics_date=metrics_data.metrics_date,
                impressions=getattr(metrics_data, "impressions", 0),
                clicks=getattr(metrics_data, "clicks", 0),
                reach=getattr(metrics_data, "reach", 0),
                engagement=getattr(metrics_data, "engagement", 0),
                followers=getattr(metrics_data, "followers", 0),
                ctr=getattr(metrics_data, "ctr", 0),
                sessions=getattr(metrics_data, "sessions", 0),
                users=getattr(metrics_data, "users", 0),
                pageviews=getattr(metrics_data, "pageviews", 0),
                avg_session_duration=getattr(metrics_data, "avg_session_duration", 0),
                conversions=getattr(metrics_data, "conversions", 0),
                cost=getattr(metrics_data, "cost", 0),
                cpc=getattr(metrics_data, "cpc", 0),
                avg_position=getattr(metrics_data, "avg_position", 0),
                calls=getattr(metrics_data, "calls", 0),
                directions=getattr(metrics_data, "directions", 0),
            )
            self.db.add(new_metrics)

        self.db.commit()

    async def sync_all_platforms(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> dict[str, Any]:
        """Synchronise toutes les plateformes configurées."""
        results = {
            "total_records": 0,
            "platforms_synced": 0,
            "platforms_failed": 0,
            "errors": [],
        }

        configs = self.get_all_configs()
        for config in configs:
            if not config.is_enabled:
                continue

            result = await self.sync_platform(config.platform, date_from, date_to)
            if result["success"]:
                results["total_records"] += result["records"]
                results["platforms_synced"] += 1
            else:
                results["platforms_failed"] += 1
                results["errors"].append(f"{config.platform.value}: {result['error']}")

        return results
