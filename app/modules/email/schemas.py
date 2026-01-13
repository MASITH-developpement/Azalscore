"""
AZALS - Module Email - Schémas
==============================
Schémas Pydantic pour les emails transactionnels.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from .models import EmailStatus, EmailType


# ============================================================================
# CONFIGURATION
# ============================================================================

class EmailConfigCreate(BaseModel):
    """Création configuration email."""
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    provider: str = "smtp"
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    from_email: EmailStr
    from_name: str
    reply_to_email: Optional[EmailStr] = None
    max_emails_per_hour: int = 100
    max_emails_per_day: int = 1000
    track_opens: bool = True
    track_clicks: bool = True


class EmailConfigUpdate(BaseModel):
    """Mise à jour configuration email."""
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[EmailStr] = None
    max_emails_per_hour: Optional[int] = None
    max_emails_per_day: Optional[int] = None
    track_opens: Optional[bool] = None
    track_clicks: Optional[bool] = None
    is_active: Optional[bool] = None


class EmailConfigResponse(BaseModel):
    """Réponse configuration email."""
    id: str
    tenant_id: str
    smtp_host: Optional[str]
    smtp_port: int
    smtp_username: Optional[str]
    smtp_use_tls: bool
    smtp_use_ssl: bool
    provider: str
    from_email: str
    from_name: str
    reply_to_email: Optional[str]
    max_emails_per_hour: int
    max_emails_per_day: int
    track_opens: bool
    track_clicks: bool
    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime]
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
    body_text: Optional[str] = None
    variables: List[str] = []
    language: str = "fr"


class EmailTemplateUpdate(BaseModel):
    """Mise à jour template email."""
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """Réponse template email."""
    id: str
    tenant_id: Optional[str]
    code: str
    name: str
    email_type: EmailType
    subject: str
    body_html: str
    body_text: Optional[str]
    variables: List[str]
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
    to_name: Optional[str] = None
    cc_emails: List[EmailStr] = []
    bcc_emails: List[EmailStr] = []
    email_type: EmailType
    template_code: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Dict[str, Any] = {}
    attachments: List[Dict[str, Any]] = []
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    schedule_at: Optional[datetime] = None


class SendEmailResponse(BaseModel):
    """Réponse envoi email."""
    id: str
    status: EmailStatus
    to_email: str
    subject: str
    queued_at: Optional[datetime]
    message: str


class BulkSendRequest(BaseModel):
    """Requête envoi en masse."""
    recipients: List[Dict[str, Any]]  # Liste de {email, name, variables}
    email_type: EmailType
    template_code: str
    base_variables: Dict[str, Any] = {}
    priority: int = 5


class BulkSendResponse(BaseModel):
    """Réponse envoi en masse."""
    total: int
    queued: int
    failed: int
    email_ids: List[str]


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
    to_name: Optional[str]
    subject: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    priority: int
    retry_count: int
    provider: Optional[str]
    provider_message_id: Optional[str]
    created_at: datetime
    queued_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class EmailLogDetail(EmailLogResponse):
    """Détail complet d'un log email."""
    body_html: Optional[str]
    body_text: Optional[str]
    variables_used: Dict[str, Any]
    attachments: List[Dict[str, Any]]
    cc_emails: List[str]
    bcc_emails: List[str]
    provider_response: Optional[Dict[str, Any]]
    created_by: Optional[str]
    ip_address: Optional[str]


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
    config: Optional[EmailConfigResponse]
    stats_today: EmailStats
    stats_month: EmailStats
    by_type: List[EmailStatsByType]
    recent_failures: List[EmailLogResponse]
    queue_size: int
