"""
AZALS MODULE EMAIL - Router API v2 (CORE SaaS)
===============================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

API REST pour les emails transactionnels avec file d'attente.
"""
from __future__ import annotations


from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

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

router = APIRouter(prefix="/v2/email", tags=["Email v2 - CORE SaaS"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id"""
    return get_email_service(db, context.tenant_id, context.user_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=EmailConfigResponse, status_code=201)
async def create_config(
    data: EmailConfigCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer configuration email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    existing = service.get_config()
    if existing:
        raise HTTPException(status_code=409, detail="Configuration déjà existante")
    return service.create_config(data)


@router.get("/config", response_model=EmailConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer configuration email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.patch("/config", response_model=EmailConfigResponse)
async def update_config(
    data: EmailConfigUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour configuration email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    config = service.update_config(data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.post("/config/verify")
async def verify_config(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Vérifier configuration email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    success, message = service.verify_config()
    return {"success": success, "message": message}


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post("/templates", response_model=EmailTemplateResponse, status_code=201)
async def create_template(
    data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer un template email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    return service.create_template(data)


@router.get("/templates", response_model=list[EmailTemplateResponse])
async def list_templates(
    email_type: EmailType | None = None,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les templates email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    return service.list_templates(email_type)


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un template"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


@router.patch("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: str,
    data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour un template"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    template = service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template


# ============================================================================
# ENVOI
# ============================================================================

@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    data: SendEmailRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Envoyer un email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    return service.send_email(data, created_by=context.user_id)


@router.post("/send/bulk", response_model=BulkSendResponse)
async def send_bulk(
    data: BulkSendRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Envoyer des emails en masse"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    return service.send_bulk(data)


@router.post("/queue/process")
async def process_queue(
    batch_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Traiter la file d'attente (admin only)"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    processed = service.process_queue(batch_size)
    return {"processed": processed}


# ============================================================================
# LOGS
# ============================================================================

@router.get("/logs", response_model=list[EmailLogResponse])
async def list_logs(
    email_type: EmailType | None = None,
    status: EmailStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les logs emails"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    items, _ = service.list_logs(email_type, status, start_date, end_date, skip, limit)
    return items


@router.get("/logs/{log_id}", response_model=EmailLogDetail)
async def get_log(
    log_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer un log email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    log = service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    return log


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=EmailDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Dashboard email"""
    service = get_email_service(db, context.tenant_id, context.user_id)
    return service.get_dashboard()
