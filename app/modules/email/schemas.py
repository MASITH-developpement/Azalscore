"""
AZALS - Module Email - Schémas
==============================
Schémas Pydantic pour les emails transactionnels.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from .models import EmailStatus, EmailType

# ============================================================================
# CONFIGURATION
# ============================================================================

class EmailConfigCreate(BaseModel):
    """Création configuration email."""
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    provider: str = "smtp"
    api_key: str | None = None
    api_endpoint: str | None = None
    from_email: EmailStr
    from_name: str
    reply_to_email: EmailStr | None = None
    max_emails_per_hour: int = 100
    max_emails_per_day: int = 1000
    track_opens: bool = True
    track_clicks: bool = True


class EmailConfigUpdate(BaseModel):
    """Mise à jour configuration email."""
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool | None = None
    smtp_use_ssl: bool | None = None
    provider: str | None = None
    api_key: str | None = None
    api_endpoint: str | None = None
    from_email: EmailStr | None = None
    from_name: str | None = None
    reply_to_email: EmailStr | None = None
    max_emails_per_hour: int | None = None
    max_emails_per_day: int | None = None
    track_opens: bool | None = None
    track_clicks: bool | None = None
    is_active: bool | None = None


class EmailConfigResponse(BaseModel):
    """Réponse configuration email."""
    id: str
    tenant_id: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_use_tls: bool
    smtp_use_ssl: bool
    provider: str
    from_email: str
    from_name: str
    reply_to_email: str | None
    max_emails_per_hour: int
    max_emails_per_day: int
    track_opens: bool
    track_clicks: bool
    is_active: bool
    is_verified: bool
    last_verified_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEMPLATES
# ============================================================================

class EmailTemplateCreate(BaseModel):
    """Création template email."""
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    email_type: EmailType
    subject: str = Field(..., min_length=1, max_length=500)
    body_html: str
    body_text: str | None = None
    variables: list[str] = []
    language: str = "fr"


class EmailTemplateUpdate(BaseModel):
    """Mise à jour template email."""
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: list[str] | None = None
    language: str | None = None
    is_active: bool | None = None


class EmailTemplateResponse(BaseModel):
    """Réponse template email."""
    id: str
    tenant_id: str | None
    code: str
    name: str
    email_type: EmailType
    subject: str
    body_html: str
    body_text: str | None
    variables: list[str]
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ENVOI D'EMAIL
# ============================================================================

class SendEmailRequest(BaseModel):
    """Requête d'envoi d'email."""
    to_email: EmailStr
    to_name: str | None = None
    cc_emails: list[EmailStr] = []
    bcc_emails: list[EmailStr] = []
    email_type: EmailType
    template_code: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: dict[str, Any] = {}
    attachments: list[dict[str, Any]] = []
    reference_type: str | None = None
    reference_id: str | None = None
    priority: int = Field(default=5, ge=1, le=10)
    schedule_at: datetime | None = None


class SendEmailResponse(BaseModel):
    """Réponse envoi email."""
    id: str
    status: EmailStatus
    to_email: str
    subject: str
    queued_at: datetime | None
    message: str


class BulkSendRequest(BaseModel):
    """Requête envoi en masse."""
    recipients: list[dict[str, Any]]  # Liste de {email, name, variables}
    email_type: EmailType
    template_code: str
    base_variables: dict[str, Any] = {}
    priority: int = 5


class BulkSendResponse(BaseModel):
    """Réponse envoi en masse."""
    total: int
    queued: int
    failed: int
    email_ids: list[str]


# ============================================================================
# LOGS
# ============================================================================

class EmailLogResponse(BaseModel):
    """Réponse log email."""
    id: str
    tenant_id: str
    email_type: EmailType
    status: EmailStatus
    to_email: str
    to_name: str | None
    subject: str
    reference_type: str | None
    reference_id: str | None
    priority: int
    retry_count: int
    provider: str | None
    provider_message_id: str | None
    created_at: datetime
    queued_at: datetime | None
    sent_at: datetime | None
    delivered_at: datetime | None
    opened_at: datetime | None
    clicked_at: datetime | None
    failed_at: datetime | None
    error_message: str | None

    class Config:
        from_attributes = True


class EmailLogDetail(EmailLogResponse):
    """Détail complet d'un log email."""
    body_html: str | None
    body_text: str | None
    variables_used: dict[str, Any]
    attachments: list[dict[str, Any]]
    cc_emails: list[str]
    bcc_emails: list[str]
    provider_response: dict[str, Any] | None
    created_by: str | None
    ip_address: str | None


# ============================================================================
# STATISTIQUES
# ============================================================================

class EmailStats(BaseModel):
    """Statistiques emails."""
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_failed: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float


class EmailStatsByType(BaseModel):
    """Statistiques par type d'email."""
    email_type: EmailType
    count: int
    delivered: int
    opened: int
    clicked: int
    bounced: int


class EmailDashboard(BaseModel):
    """Dashboard email."""
    config: EmailConfigResponse | None
    stats_today: EmailStats
    stats_month: EmailStats
    by_type: list[EmailStatsByType]
    recent_failures: list[EmailLogResponse]
    queue_size: int
