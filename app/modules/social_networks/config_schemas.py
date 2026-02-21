"""
AZALS MODULE - Réseaux Sociaux - Schémas Configuration
=======================================================
Schémas Pydantic pour la configuration des connexions API
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import MarketingPlatform


class PlatformConfigBase(BaseModel):
    """Configuration de base pour une plateforme."""
    platform: MarketingPlatform
    is_enabled: bool = True

    # Identifiants de compte (varient selon la plateforme)
    account_id: Optional[str] = Field(None, description="ID du compte/propriété")
    property_id: Optional[str] = Field(None, description="ID de propriété (GA4, etc.)")

    # Credentials API (pour les APIs avec clé simple)
    api_key: Optional[str] = Field(None, description="Clé API")


class PlatformConfigCreate(PlatformConfigBase):
    """Création d'une configuration."""
    pass


class PlatformConfigUpdate(BaseModel):
    """Mise à jour d'une configuration (tous champs optionnels)."""
    is_enabled: Optional[bool] = None
    account_id: Optional[str] = None
    property_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class PlatformConfigResponse(PlatformConfigBase):
    """Réponse avec infos de configuration (sans secrets)."""
    id: UUID
    tenant_id: str

    # OAuth status
    is_connected: bool = False
    oauth_status: str = "not_connected"  # not_connected, connected, expired, error

    # Sync status
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None
    sync_status: str = "never"  # never, success, error, in_progress

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OAuthInitRequest(BaseModel):
    """Demande d'initialisation OAuth."""
    platform: MarketingPlatform
    redirect_uri: Optional[str] = None


class OAuthInitResponse(BaseModel):
    """Réponse avec URL d'autorisation OAuth."""
    auth_url: str
    state: str
    platform: MarketingPlatform


class OAuthCallbackRequest(BaseModel):
    """Callback OAuth après autorisation."""
    platform: MarketingPlatform
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Réponse après callback OAuth."""
    success: bool
    platform: MarketingPlatform
    message: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None


class SyncRequest(BaseModel):
    """Demande de synchronisation manuelle."""
    platform: Optional[MarketingPlatform] = None  # None = toutes les plateformes
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SyncResponse(BaseModel):
    """Réponse de synchronisation."""
    success: bool
    platform: Optional[MarketingPlatform] = None
    message: str
    records_synced: int = 0
    errors: list[str] = []


class PlatformStatus(BaseModel):
    """Statut d'une plateforme."""
    platform: MarketingPlatform
    name: str
    is_configured: bool = False
    is_connected: bool = False
    is_enabled: bool = False
    last_sync_at: Optional[datetime] = None
    sync_status: str = "never"
    error_message: Optional[str] = None

    # Infos de compte
    account_id: Optional[str] = None
    account_name: Optional[str] = None


class AllPlatformsStatus(BaseModel):
    """Statut de toutes les plateformes."""
    platforms: list[PlatformStatus]
    total_configured: int = 0
    total_connected: int = 0
    last_global_sync: Optional[datetime] = None
