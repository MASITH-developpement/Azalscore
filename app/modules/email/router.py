"""
AZALS - Module Email - Router
=============================
Endpoints API pour les emails transactionnels.
"""
from __future__ import annotations


from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .models import EmailStatus, EmailType
from .schemas import (
    BulkSendRequest,
    BulkSendResponse,
    EmailConfigCreate,
    EmailConfigResponse,
    EmailConfigUpdate,
    EmailDashboard,
    EmailLogDetail,
    EmailLogResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    SendEmailRequest,
    SendEmailResponse,
)
from .service import get_email_service

router = APIRouter(prefix="/email", tags=["Email Transactionnel"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return get_email_service(db, tenant_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=EmailConfigResponse, status_code=201)
def create_config(
    data: EmailConfigCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Créer configuration email."""
    existing = service.get_config()
    if existing:
        raise HTTPException(status_code=409, detail="Configuration déjà existante")
    return service.create_config(data)


@router.get("/config", response_model=EmailConfigResponse)
def get_config(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupérer configuration email."""
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.patch("/config", response_model=EmailConfigResponse)
def update_config(
    data: EmailConfigUpdate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour configuration email."""
    config = service.update_config(data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.post("/config/verify")
def verify_config(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Vérifier configuration email."""
    success, message = service.verify_config()
    return {"success": success, "message": message}


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=EmailTemplateResponse, status_code=201)
def create_template(
    data: EmailTemplateCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Créer un template email."""
    return service.create_template(data)


@router.get("/templates", response_model=list[EmailTemplateResponse])
def list_templates(
    email_type: EmailType | None = None,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les templates email."""
    return service.list_templates(email_type)


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
def get_template(
    template_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un template."""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.patch("/templates/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: str,
    data: EmailTemplateUpdate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour un template."""
    template = service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


# ============================================================================
# ENVOI
# ============================================================================

@router.post("/send", response_model=SendEmailResponse)
def send_email(
    data: SendEmailRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Envoyer un email."""
    return service.send_email(data, created_by=current_user.email)


@router.post("/send/bulk", response_model=BulkSendResponse)
def send_bulk(
    data: BulkSendRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Envoyer des emails en masse."""
    return service.send_bulk(data)


@router.post("/queue/process")
def process_queue(
    batch_size: int = Query(10, ge=1, le=100),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Traiter la file d'attente (admin only)."""
    processed = service.process_queue(batch_size)
    return {"processed": processed}


# ============================================================================
# LOGS
# ============================================================================

@router.get("/logs", response_model=list[EmailLogResponse])
def list_logs(
    email_type: EmailType | None = None,
    status: EmailStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les logs emails."""
    items, _ = service.list_logs(email_type, status, start_date, end_date, skip, limit)
    return items


@router.get("/logs/{log_id}", response_model=EmailLogDetail)
def get_log(
    log_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un log email."""
    log = service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    return log


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=EmailDashboard)
def get_dashboard(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Dashboard email."""
    return service.get_dashboard()
