"""
AZALS MODULE HR_VAULT - Router API
====================================

Endpoints REST pour le coffre-fort RH.
"""
from __future__ import annotations


import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.modules.iam.decorators import require_permission
from app.core.database import get_db
from app.core.config import get_settings

from .exceptions import (
    AccessDeniedException,
    CategoryNotFoundException,
    DocumentNotFoundException,
    EncryptionException,
    FileSizeLimitException,
    GDPRRequestNotFoundException,
    HRVaultException,
    InvalidFileTypeException,
    RetentionPeriodActiveException,
)
from .models import (
    GDPRRequestStatus,
    GDPRRequestType,
    SignatureStatus,
    VaultAccessRole,
    VaultDocumentStatus,
    VaultDocumentType,
)
from .schemas import (
    VaultAccessLogFilters,
    VaultAccessLogListResponse,
    VaultAccessLogResponse,
    VaultAccessPermissionCreate,
    VaultAccessPermissionResponse,
    VaultAlertResponse,
    VaultCategoryCreate,
    VaultCategoryResponse,
    VaultCategoryUpdate,
    VaultConsentCreate,
    VaultConsentResponse,
    VaultDashboardStats,
    VaultDocumentFilters,
    VaultDocumentListResponse,
    VaultDocumentResponse,
    VaultDocumentUpdate,
    VaultDocumentUpload,
    VaultDocumentVersionResponse,
    VaultEmployeeStats,
    VaultExportRequest,
    VaultExportResponse,
    VaultGDPRRequestCreate,
    VaultGDPRRequestProcess,
    VaultGDPRRequestResponse,
    VaultSignatureRequest,
    VaultSignatureStatus,
)
from .service import HRVaultService, create_hr_vault_service

router = APIRouter(prefix="/hr-vault", tags=["HR Vault - Coffre-fort RH"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_vault_service(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> HRVaultService:
    """Dependency pour obtenir le service HR Vault."""
    # Determiner le role
    role = VaultAccessRole.EMPLOYEE
    if hasattr(current_user, "roles"):
        if "hr_admin" in current_user.roles:
            role = VaultAccessRole.HR_ADMIN
        elif "hr_director" in current_user.roles:
            role = VaultAccessRole.HR_DIRECTOR
        elif "manager" in current_user.roles:
            role = VaultAccessRole.MANAGER

    # Recuperer la master key depuis les settings/secrets
    master_key = getattr(settings, "VAULT_MASTER_KEY", None)
    if master_key:
        master_key = bytes.fromhex(master_key)
    else:
        # En dev, utiliser une cle fixe (NE PAS FAIRE EN PRODUCTION)
        master_key = b"0" * 32

    return create_hr_vault_service(
        session=db,
        tenant_id=current_user.tenant_id,
        storage_path=getattr(settings, "VAULT_STORAGE_PATH", "/data/vault"),
        master_key=master_key,
        current_user_id=uuid.UUID(str(current_user.id)),
        current_user_role=role,
    )


def handle_vault_exception(e: HRVaultException):
    """Convertit les exceptions HR Vault en HTTPException."""
    status_map = {
        "DOCUMENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CATEGORY_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "GDPR_REQUEST_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "ACCESS_DENIED": status.HTTP_403_FORBIDDEN,
        "INSUFFICIENT_PERMISSIONS": status.HTTP_403_FORBIDDEN,
        "VAULT_NOT_ACTIVATED": status.HTTP_403_FORBIDDEN,
        "CONSENT_REQUIRED": status.HTTP_403_FORBIDDEN,
        "DOCUMENT_DELETED": status.HTTP_410_GONE,
        "RETENTION_PERIOD_ACTIVE": status.HTTP_409_CONFLICT,
        "FILE_SIZE_LIMIT_EXCEEDED": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "INVALID_FILE_TYPE": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    }
    http_status = status_map.get(e.code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(
        status_code=http_status,
        detail={"code": e.code, "message": e.message, "details": e.details},
    )


# ============================================================================
# CATEGORIES
# ============================================================================

@router.get("/categories", response_model=list[VaultCategoryResponse])
async def list_categories(
    include_inactive: bool = Query(False),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste toutes les categories de documents."""
    try:
        return await service.list_categories(include_inactive)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/categories/{category_id}", response_model=VaultCategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere une categorie par ID."""
    try:
        return await service.get_category(category_id)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/categories", response_model=VaultCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: VaultCategoryCreate,
    service: HRVaultService = Depends(get_vault_service),
):
    """Cree une nouvelle categorie."""
    try:
        return await service.create_category(data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.put("/categories/{category_id}", response_model=VaultCategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: VaultCategoryUpdate,
    service: HRVaultService = Depends(get_vault_service),
):
    """Met a jour une categorie."""
    try:
        return await service.update_category(category_id, data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Supprime une categorie."""
    try:
        await service.delete_category(category_id)
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# DOCUMENTS
# ============================================================================

@router.get("/documents", response_model=VaultDocumentListResponse)
async def list_documents(
    employee_id: Optional[uuid.UUID] = Query(None),
    document_type: Optional[VaultDocumentType] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[VaultDocumentStatus] = Query(None, alias="status"),
    signature_status: Optional[SignatureStatus] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    pay_period: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les documents avec filtres."""
    from datetime import date as date_type

    filters = VaultDocumentFilters(
        employee_id=employee_id,
        document_type=document_type,
        category_id=category_id,
        status=status_filter,
        signature_status=signature_status,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        pay_period=pay_period,
        search=search,
    )
    try:
        return await service.list_documents(filters, page, page_size)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/documents/{document_id}", response_model=VaultDocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere un document par ID."""
    try:
        return await service.get_document(document_id)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/documents", response_model=VaultDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    employee_id: uuid.UUID = Form(...),
    document_type: VaultDocumentType = Form(...),
    title: str = Form(...),
    category_id: Optional[uuid.UUID] = Form(None),
    description: Optional[str] = Form(None),
    reference: Optional[str] = Form(None),
    document_date: Optional[str] = Form(None),
    period_start: Optional[str] = Form(None),
    period_end: Optional[str] = Form(None),
    pay_period: Optional[str] = Form(None),
    gross_salary: Optional[float] = Form(None),
    net_salary: Optional[float] = Form(None),
    notify_employee: bool = Form(True),
    requires_signature: bool = Form(False),
    tags: Optional[str] = Form(None),
    service: HRVaultService = Depends(get_vault_service),
):
    """Upload un nouveau document."""
    from datetime import date as date_type
    from decimal import Decimal

    # Lire le contenu du fichier
    content = await file.read()

    # Parser les tags
    tag_list = tags.split(",") if tags else []

    data = VaultDocumentUpload(
        employee_id=employee_id,
        document_type=document_type,
        title=title,
        category_id=category_id,
        description=description,
        reference=reference,
        document_date=date_type.fromisoformat(document_date) if document_date else None,
        period_start=date_type.fromisoformat(period_start) if period_start else None,
        period_end=date_type.fromisoformat(period_end) if period_end else None,
        pay_period=pay_period,
        gross_salary=Decimal(str(gross_salary)) if gross_salary else None,
        net_salary=Decimal(str(net_salary)) if net_salary else None,
        notify_employee=notify_employee,
        requires_signature=requires_signature,
        tags=tag_list,
    )

    try:
        return await service.upload_document(
            data=data,
            file_content=content,
            file_name=file.filename or "document",
            mime_type=file.content_type or "application/octet-stream",
        )
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Telecharge un document."""
    try:
        content, filename, mime_type = await service.download_document(document_id)

        def iter_content():
            yield content

        return StreamingResponse(
            iter_content(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content)),
            },
        )
    except HRVaultException as e:
        handle_vault_exception(e)


@router.put("/documents/{document_id}", response_model=VaultDocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    data: VaultDocumentUpdate,
    service: HRVaultService = Depends(get_vault_service),
):
    """Met a jour les metadonnees d'un document."""
    try:
        return await service.update_document(document_id, data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    force: bool = Query(False),
    service: HRVaultService = Depends(get_vault_service),
):
    """Supprime un document."""
    try:
        await service.delete_document(document_id, reason, force)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/documents/{document_id}/versions", response_model=list[VaultDocumentVersionResponse])
async def list_document_versions(
    document_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les versions d'un document."""
    try:
        versions = await service.repository.list_document_versions(document_id)
        return [VaultDocumentVersionResponse.model_validate(v) for v in versions]
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# SIGNATURE ELECTRONIQUE
# ============================================================================

@router.post("/documents/{document_id}/signature", response_model=VaultSignatureStatus)
async def request_document_signature(
    document_id: uuid.UUID,
    data: VaultSignatureRequest,
    service: HRVaultService = Depends(get_vault_service),
):
    """Demande une signature electronique pour un document."""
    data.document_id = document_id
    try:
        return await service.request_signature(data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/webhooks/signature")
async def signature_webhook(
    payload: dict,
    service: HRVaultService = Depends(get_vault_service),
):
    """Webhook pour les notifications de signature."""
    # Extraire les informations du webhook
    event = payload.get("event", "")
    signature_request_id = payload.get("signature_request_id", "")

    if not event or not signature_request_id:
        raise HTTPException(
            status_code=400,
            detail="Payload invalide: event et signature_request_id requis"
        )

    # Traiter l'evenement via le service
    await service.process_signature_webhook(
        signature_request_id=signature_request_id,
        event=event,
        data=payload
    )

    return {"status": "ok", "event": event}


# ============================================================================
# RGPD
# ============================================================================

@router.get("/gdpr-requests", response_model=list[VaultGDPRRequestResponse])
async def list_gdpr_requests(
    employee_id: Optional[uuid.UUID] = Query(None),
    request_type: Optional[GDPRRequestType] = Query(None),
    status_filter: Optional[GDPRRequestStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les demandes RGPD."""
    try:
        requests, _ = await service.repository.list_gdpr_requests(
            employee_id=employee_id,
            request_type=request_type,
            status=status_filter,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        return [VaultGDPRRequestResponse.model_validate(r) for r in requests]
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/gdpr-requests", response_model=VaultGDPRRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_gdpr_request(
    data: VaultGDPRRequestCreate,
    service: HRVaultService = Depends(get_vault_service),
):
    """Cree une demande RGPD."""
    try:
        return await service.create_gdpr_request(data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/gdpr-requests/{request_id}", response_model=VaultGDPRRequestResponse)
async def get_gdpr_request(
    request_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere une demande RGPD."""
    try:
        request = await service.repository.get_gdpr_request(request_id)
        if not request:
            raise GDPRRequestNotFoundException(str(request_id))
        return VaultGDPRRequestResponse.model_validate(request)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/gdpr-requests/{request_id}/process", response_model=VaultGDPRRequestResponse)
async def process_gdpr_request(
    request_id: uuid.UUID,
    data: VaultGDPRRequestProcess,
    service: HRVaultService = Depends(get_vault_service),
):
    """Traite une demande RGPD."""
    try:
        return await service.process_gdpr_request(request_id, data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/gdpr-requests/{request_id}/download")
async def download_gdpr_export(
    request_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Telecharge l'export d'une demande RGPD."""
    try:
        content, filename = await service.download_gdpr_export(request_id)

        def iter_content():
            yield content

        return StreamingResponse(
            iter_content(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content)),
            },
        )
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# EXPORT DOSSIER SALARIE
# ============================================================================

@router.post("/employees/{employee_id}/export", response_model=VaultExportResponse)
async def export_employee_folder(
    employee_id: uuid.UUID,
    data: VaultExportRequest,
    service: HRVaultService = Depends(get_vault_service),
):
    """Exporte le dossier complet d'un employe."""
    data.employee_id = employee_id
    try:
        return await service.export_employee_folder(data)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/employees/{employee_id}/documents", response_model=VaultDocumentListResponse)
async def list_employee_documents(
    employee_id: uuid.UUID,
    document_type: Optional[VaultDocumentType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les documents d'un employe."""
    filters = VaultDocumentFilters(
        employee_id=employee_id,
        document_type=document_type,
    )
    try:
        return await service.list_documents(filters, page, page_size)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/employees/{employee_id}/stats", response_model=VaultEmployeeStats)
async def get_employee_stats(
    employee_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere les statistiques du coffre-fort d'un employe."""
    try:
        return await service.get_employee_stats(employee_id)
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# CONSENTEMENTS
# ============================================================================

@router.post("/consents", response_model=VaultConsentResponse, status_code=status.HTTP_201_CREATED)
async def create_consent(
    data: VaultConsentCreate,
    service: HRVaultService = Depends(get_vault_service),
):
    """Enregistre un consentement."""
    from .models import VaultConsent

    try:
        consent = VaultConsent(
            employee_id=data.employee_id,
            consent_type=data.consent_type,
            consent_version=data.consent_version,
            given=data.given,
        )
        consent = await service.repository.create_consent(consent)
        return VaultConsentResponse.model_validate(consent)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/consents/{employee_id}/{consent_type}", response_model=VaultConsentResponse)
async def get_consent(
    employee_id: uuid.UUID,
    consent_type: str,
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere le consentement d'un employe."""
    try:
        consent = await service.repository.get_consent(employee_id, consent_type)
        if not consent:
            raise HTTPException(status_code=404, detail="Consentement non trouve")
        return VaultConsentResponse.model_validate(consent)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.delete("/consents/{employee_id}/{consent_type}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_consent(
    employee_id: uuid.UUID,
    consent_type: str,
    service: HRVaultService = Depends(get_vault_service),
):
    """Revoque un consentement."""
    try:
        await service.repository.revoke_consent(employee_id, consent_type)
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# LOGS D'ACCES
# ============================================================================

@router.get("/access-logs", response_model=VaultAccessLogListResponse)
async def list_access_logs(
    document_id: Optional[uuid.UUID] = Query(None),
    employee_id: Optional[uuid.UUID] = Query(None),
    accessed_by: Optional[uuid.UUID] = Query(None),
    access_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les logs d'acces aux documents."""
    from datetime import datetime
    from .models import VaultAccessType as VAT

    try:
        logs, total = await service.repository.list_access_logs(
            document_id=document_id,
            employee_id=employee_id,
            accessed_by=accessed_by,
            access_type=VAT(access_type) if access_type else None,
            date_from=datetime.fromisoformat(date_from) if date_from else None,
            date_to=datetime.fromisoformat(date_to) if date_to else None,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        return VaultAccessLogListResponse(
            items=[VaultAccessLogResponse.model_validate(l) for l in logs],
            total=total,
            page=page,
            page_size=page_size,
        )
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# ALERTES
# ============================================================================

@router.get("/alerts", response_model=list[VaultAlertResponse])
async def list_alerts(
    unread_only: bool = Query(False),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les alertes de l'utilisateur."""
    try:
        alerts = await service.get_alerts(unread_only)
        return [VaultAlertResponse.model_validate(a) for a in alerts]
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/alerts/{alert_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_alert_read(
    alert_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Marque une alerte comme lue."""
    try:
        await service.mark_alert_read(alert_id)
    except HRVaultException as e:
        handle_vault_exception(e)


@router.post("/alerts/{alert_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_alert(
    alert_id: uuid.UUID,
    service: HRVaultService = Depends(get_vault_service),
):
    """Masque une alerte."""
    try:
        await service.dismiss_alert(alert_id)
    except HRVaultException as e:
        handle_vault_exception(e)


# ============================================================================
# STATISTIQUES ET DASHBOARD
# ============================================================================

@router.get("/dashboard/stats", response_model=VaultDashboardStats)
async def get_dashboard_stats(
    service: HRVaultService = Depends(get_vault_service),
):
    """Recupere les statistiques du dashboard."""
    try:
        return await service.get_dashboard_stats()
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/dashboard/expiring-documents", response_model=list[VaultDocumentResponse])
async def get_expiring_documents(
    days: int = Query(30, ge=1, le=365),
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les documents expirant prochainement."""
    try:
        documents = await service.repository.get_expiring_documents(days)
        return [VaultDocumentResponse.model_validate(d) for d in documents]
    except HRVaultException as e:
        handle_vault_exception(e)


@router.get("/dashboard/pending-signatures", response_model=list[VaultDocumentResponse])
async def get_pending_signatures(
    service: HRVaultService = Depends(get_vault_service),
):
    """Liste les documents en attente de signature."""
    try:
        documents = await service.repository.get_pending_signature_documents()
        return [VaultDocumentResponse.model_validate(d) for d in documents]
    except HRVaultException as e:
        handle_vault_exception(e)
