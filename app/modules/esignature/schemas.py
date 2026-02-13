"""
AZALS MODULE - Schémas Pydantic Signature Électronique
=======================================================

Schémas de validation pour l'API de signature électronique.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# ENUMS (reproduits pour Pydantic)
# ============================================================================

from .models import SignatureProvider, SignatureStatus, SignerStatus


# ============================================================================
# SCHEMAS SIGNATAIRE
# ============================================================================

class SignerBase(BaseModel):
    """Schéma de base pour un signataire."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    signing_order: int = Field(default=1, ge=1)


class SignerCreate(SignerBase):
    """Schéma de création d'un signataire."""
    pass


class SignerResponse(SignerBase):
    """Schéma de réponse pour un signataire."""
    id: UUID
    request_id: UUID
    tenant_id: UUID
    status: SignerStatus
    signature_url: Optional[str] = None
    provider_signer_id: Optional[str] = None
    notified_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS DEMANDE SIGNATURE
# ============================================================================

class SignatureRequestBase(BaseModel):
    """Schéma de base pour une demande de signature."""
    document_type: str = Field(..., max_length=50)
    document_id: UUID
    document_number: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    provider: SignatureProvider = SignatureProvider.YOUSIGN
    expires_at: Optional[datetime] = None
    send_reminders: bool = True
    metadata: dict = Field(default_factory=dict)


class SignatureRequestCreate(SignatureRequestBase):
    """Schéma de création d'une demande de signature."""
    document_url: Optional[str] = None  # URL ou sera généré
    signers: list[SignerCreate] = Field(..., min_length=1)
    webhook_url: Optional[str] = None

    @field_validator('signers')
    @classmethod
    def validate_signers(cls, v):
        """Valide que les signataires ont des ordres uniques."""
        if v:
            orders = [s.signing_order for s in v]
            if len(orders) != len(set(orders)):
                raise ValueError("Chaque signataire doit avoir un ordre de signature unique")
        return v


class SignatureRequestUpdate(BaseModel):
    """Schéma de mise à jour d'une demande de signature."""
    status: Optional[SignatureStatus] = None
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    send_reminders: Optional[bool] = None
    metadata: Optional[dict] = None


class SignatureRequestResponse(SignatureRequestBase):
    """Schéma de réponse pour une demande de signature."""
    id: UUID
    tenant_id: UUID
    provider_request_id: Optional[str] = None
    status: SignatureStatus
    document_url: Optional[str] = None
    signed_document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    signers: list[SignerResponse] = []

    class Config:
        from_attributes = True


class SignatureRequestListResponse(BaseModel):
    """Schéma de réponse pour une liste de demandes."""
    requests: list[SignatureRequestResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# SCHEMAS LOG SIGNATURE
# ============================================================================

class SignatureLogResponse(BaseModel):
    """Schéma de réponse pour un log de signature."""
    id: UUID
    request_id: UUID
    tenant_id: UUID
    event_type: str
    event_source: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    user_id: Optional[UUID] = None
    signer_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS ACTIONS
# ============================================================================

class SendSignatureRequest(BaseModel):
    """Schéma pour envoyer une demande de signature."""
    notify_signers: bool = True
    custom_message: Optional[str] = None


class DeclineSignatureRequest(BaseModel):
    """Schéma pour refuser une signature."""
    reason: str = Field(..., min_length=1, max_length=500)


class SignDocumentRequest(BaseModel):
    """Schéma pour déclencher l'envoi d'un document en signature."""
    document_type: str = Field(..., max_length=50)
    document_id: UUID
    signers: list[SignerCreate] = Field(..., min_length=1)
    title: Optional[str] = None
    message: Optional[str] = None
    expires_days: int = Field(default=30, ge=1, le=365)


# ============================================================================
# SCHEMAS WEBHOOK
# ============================================================================

class YousignWebhookEvent(BaseModel):
    """Schéma pour les événements webhook Yousign."""
    event_name: str
    signature_request_id: str
    data: dict = Field(default_factory=dict)


class DocuSignWebhookEvent(BaseModel):
    """Schéma pour les événements webhook DocuSign."""
    event: str
    envelope_id: str
    data: dict = Field(default_factory=dict)


# ============================================================================
# SCHEMAS PROVIDER CONFIGURATION
# ============================================================================

class ProviderConfigResponse(BaseModel):
    """Schéma de réponse pour la configuration des providers."""
    provider: SignatureProvider
    is_configured: bool
    is_active: bool
    supports_features: dict = Field(default_factory=dict)


class ProvidersListResponse(BaseModel):
    """Liste des providers disponibles."""
    providers: list[ProviderConfigResponse]
    default_provider: Optional[SignatureProvider] = None


# ============================================================================
# SCHEMAS STATISTIQUES
# ============================================================================

class SignatureStats(BaseModel):
    """Statistiques sur les signatures."""
    total_requests: int = 0
    pending_requests: int = 0
    signed_requests: int = 0
    declined_requests: int = 0
    expired_requests: int = 0
    average_signature_time_hours: Optional[float] = None
    total_signers: int = 0
    signed_signers: int = 0


class SignatureDashboard(BaseModel):
    """Dashboard des signatures."""
    stats: SignatureStats
    recent_requests: list[SignatureRequestResponse] = []
    pending_signatures: list[SignerResponse] = []
