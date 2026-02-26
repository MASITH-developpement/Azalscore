"""
AZALS MODULE ESIGNATURE - Router API
====================================

Endpoints REST pour la signature electronique.
"""
from __future__ import annotations


import math
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import EnvelopeStatus, SignerStatus, SignatureProvider, DocumentType, TemplateCategory
from .schemas import (
    # Config
    ESignatureConfigCreate,
    ESignatureConfigUpdate,
    ESignatureConfigResponse,
    # Provider Credentials
    ProviderCredentialCreate,
    ProviderCredentialUpdate,
    ProviderCredentialResponse,
    # Templates
    SignatureTemplateCreate,
    SignatureTemplateUpdate,
    SignatureTemplateResponse,
    SignatureTemplateList,
    SignatureTemplateListItem,
    TemplateFilters,
    # Envelopes
    EnvelopeCreate,
    EnvelopeCreateFromTemplate,
    EnvelopeUpdate,
    EnvelopeResponse,
    EnvelopeList,
    EnvelopeListItem,
    EnvelopeFilters,
    # Signers
    SignerCreate,
    SignerUpdate,
    SignerResponse,
    # Actions
    SendEnvelopeRequest,
    CancelEnvelopeRequest,
    VoidEnvelopeRequest,
    SendReminderRequest,
    DeclineRequest,
    DelegateRequest,
    ApproveEnvelopeRequest,
    RejectEnvelopeRequest,
    BulkActionRequest,
    BulkActionResponse,
    # Audit & Certificates
    AuditEventResponse,
    AuditTrailResponse,
    CertificateResponse,
    # Stats
    DashboardStatsResponse,
    SignatureStatsResponse,
    # Downloads
    DownloadResponse,
)
from .service import get_esignature_service
from .exceptions import (
    ESignatureError,
    ConfigNotFoundError,
    ConfigAlreadyExistsError,
    ProviderNotConfiguredError,
    ProviderCredentialNotFoundError,
    TemplateNotFoundError,
    TemplateDuplicateCodeError,
    TemplateLockedError,
    EnvelopeNotFoundError,
    EnvelopeStateError,
    EnvelopeNotDraftError,
    SignerNotFoundError,
    SignerAlreadySignedError,
    InvalidAccessTokenError,
)

router = APIRouter(prefix="/esignature", tags=["E-Signature"])


# =============================================================================
# ERROR HANDLERS
# =============================================================================

def handle_esignature_error(e: ESignatureError):
    """Convertit une exception metier en HTTPException."""
    status_map = {
        "CONFIG_NOT_FOUND": 404,
        "CONFIG_EXISTS": 409,
        "PROVIDER_NOT_CONFIGURED": 404,
        "CREDENTIALS_NOT_FOUND": 404,
        "TEMPLATE_NOT_FOUND": 404,
        "TEMPLATE_DUPLICATE_CODE": 409,
        "TEMPLATE_LOCKED": 403,
        "ENVELOPE_NOT_FOUND": 404,
        "ENVELOPE_STATE_ERROR": 400,
        "ENVELOPE_NOT_DRAFT": 400,
        "SIGNER_NOT_FOUND": 404,
        "SIGNER_ALREADY_SIGNED": 400,
        "INVALID_ACCESS_TOKEN": 401,
        "SIGNER_NOT_AUTHORIZED": 403,
    }
    status_code = status_map.get(e.code, 400)
    raise HTTPException(status_code=status_code, detail={"code": e.code, "message": e.message})


# =============================================================================
# CONFIGURATION
# =============================================================================

@router.get("/config", response_model=ESignatureConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.config.read")
):
    """Recupere la configuration signature electronique."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvee")
    return config


@router.post("/config", response_model=ESignatureConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    data: ESignatureConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.config.create")
):
    """Cree la configuration signature electronique."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.create_config(data)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.put("/config", response_model=ESignatureConfigResponse)
async def update_config(
    data: ESignatureConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.config.update")
):
    """Met a jour la configuration."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.update_config(data)
    except ESignatureError as e:
        handle_esignature_error(e)


# =============================================================================
# PROVIDER CREDENTIALS
# =============================================================================

@router.get("/providers", response_model=List[ProviderCredentialResponse])
async def list_provider_credentials(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.provider.read")
):
    """Liste les providers configures."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    return service.list_provider_credentials()


@router.post("/providers", response_model=ProviderCredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_provider_credential(
    data: ProviderCredentialCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.provider.create")
):
    """Configure un provider de signature."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    return service.create_provider_credential(data)


@router.put("/providers/{credential_id}", response_model=ProviderCredentialResponse)
async def update_provider_credential(
    credential_id: UUID,
    data: ProviderCredentialUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.provider.update")
):
    """Met a jour les credentials d'un provider."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.update_provider_credential(credential_id, data)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/providers/{provider}/verify")
async def verify_provider_credentials(
    provider: SignatureProvider,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.provider.update")
):
    """Verifie les credentials d'un provider."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    is_valid, message = await service.verify_provider_credentials(provider)
    return {"valid": is_valid, "message": message}


# =============================================================================
# TEMPLATES
# =============================================================================

@router.get("/templates", response_model=SignatureTemplateList)
async def list_templates(
    search: Optional[str] = Query(None, min_length=2),
    category: Optional[TemplateCategory] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.template.read")
):
    """Liste les templates de signature."""
    filters = TemplateFilters(
        search=search,
        category=category,
        document_type=document_type,
        is_active=is_active
    )
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    items, total = service.list_templates(filters, page, page_size, sort_by, sort_dir)

    return SignatureTemplateList(
        items=[SignatureTemplateListItem.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/templates/{template_id}", response_model=SignatureTemplateResponse)
async def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.template.read")
):
    """Recupere un template."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouve")
    return template


@router.post("/templates", response_model=SignatureTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: SignatureTemplateCreate,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.template.create")
):
    """Cree un template de signature."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)

        file_content = None
        file_name = None
        if file:
            file_content = await file.read()
            file_name = file.filename

        return service.create_template(data, file_content, file_name)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.put("/templates/{template_id}", response_model=SignatureTemplateResponse)
async def update_template(
    template_id: UUID,
    data: SignatureTemplateUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.template.update")
):
    """Met a jour un template."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.update_template(template_id, data)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.template.delete")
):
    """Supprime un template (soft delete)."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        service.delete_template(template_id)
    except ESignatureError as e:
        handle_esignature_error(e)


# =============================================================================
# ENVELOPES
# =============================================================================

@router.get("/envelopes", response_model=EnvelopeList)
async def list_envelopes(
    search: Optional[str] = Query(None, min_length=2),
    status: Optional[List[EnvelopeStatus]] = Query(None),
    provider: Optional[SignatureProvider] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    reference_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    include_archived: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.read")
):
    """Liste les enveloppes de signature."""
    filters = EnvelopeFilters(
        search=search,
        status=status,
        provider=provider,
        document_type=document_type,
        reference_type=reference_type,
        date_from=date_from,
        date_to=date_to,
        include_archived=include_archived
    )
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    items, total = service.list_envelopes(filters, page, page_size, sort_by, sort_dir)

    return EnvelopeList(
        items=[EnvelopeListItem.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/envelopes/{envelope_id}", response_model=EnvelopeResponse)
async def get_envelope(
    envelope_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.read")
):
    """Recupere une enveloppe."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    envelope = service.get_envelope(envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Enveloppe non trouvee")
    return envelope


@router.post("/envelopes", response_model=EnvelopeResponse, status_code=status.HTTP_201_CREATED)
async def create_envelope(
    data: EnvelopeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.create")
):
    """Cree une nouvelle enveloppe de signature."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.create_envelope(data)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/from-template", response_model=EnvelopeResponse, status_code=status.HTTP_201_CREATED)
async def create_envelope_from_template(
    data: EnvelopeCreateFromTemplate,
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.create")
):
    """Cree une enveloppe depuis un template."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)

        document_content = None
        if document:
            document_content = await document.read()

        return service.create_envelope_from_template(data, document_content)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/documents")
async def add_document_to_envelope(
    envelope_id: UUID,
    document: UploadFile = File(...),
    order: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.update")
):
    """Ajoute un document a une enveloppe."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    envelope = service.get_envelope(envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Enveloppe non trouvee")

    if envelope.status != EnvelopeStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Enveloppe non modifiable")

    content = await document.read()
    doc = service._add_document_to_envelope(envelope, content, document.filename, order)

    return {"id": str(doc.id), "name": doc.name, "filename": doc.original_file_name}


@router.put("/envelopes/{envelope_id}", response_model=EnvelopeResponse)
async def update_envelope(
    envelope_id: UUID,
    data: EnvelopeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.update")
):
    """Met a jour une enveloppe (brouillon uniquement)."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.update_envelope(envelope_id, data)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.delete("/envelopes/{envelope_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_envelope(
    envelope_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.delete")
):
    """Supprime une enveloppe (brouillon uniquement)."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    envelope = service.get_envelope(envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Enveloppe non trouvee")

    if envelope.status != EnvelopeStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Seuls les brouillons peuvent etre supprimes")

    service.envelope_repo.soft_delete(envelope, current_user.id)


# =============================================================================
# ENVELOPE ACTIONS
# =============================================================================

@router.post("/envelopes/{envelope_id}/send", response_model=EnvelopeResponse)
async def send_envelope(
    envelope_id: UUID,
    data: Optional[SendEnvelopeRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.send")
):
    """Envoie une enveloppe aux signataires."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        custom_message = data.custom_message if data else None
        return await service.send_envelope(envelope_id, custom_message)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/cancel", response_model=EnvelopeResponse)
async def cancel_envelope(
    envelope_id: UUID,
    data: CancelEnvelopeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.cancel")
):
    """Annule une enveloppe."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return await service.cancel_envelope(envelope_id, data.reason, data.notify_signers)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/void", response_model=EnvelopeResponse)
async def void_envelope(
    envelope_id: UUID,
    data: VoidEnvelopeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.void")
):
    """Invalide une enveloppe completee."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return await service.void_envelope(envelope_id, data.reason)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/remind")
async def send_reminder(
    envelope_id: UUID,
    data: Optional[SendReminderRequest] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.remind")
):
    """Envoie un rappel aux signataires."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        signer_ids = data.signer_ids if data else None
        custom_message = data.custom_message if data else None
        result = await service.send_reminder(envelope_id, signer_ids, custom_message)
        return {"success": result, "message": "Rappel(s) envoye(s)"}
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/approve", response_model=EnvelopeResponse)
async def approve_envelope(
    envelope_id: UUID,
    data: Optional[ApproveEnvelopeRequest] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.approve")
):
    """Approuve une enveloppe avant envoi."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        comments = data.comments if data else None
        return service.approve_envelope(envelope_id, comments)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/{envelope_id}/reject", response_model=EnvelopeResponse)
async def reject_envelope(
    envelope_id: UUID,
    data: RejectEnvelopeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.approve")
):
    """Rejette une enveloppe avant envoi."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        return service.reject_envelope(envelope_id, data.reason)
    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/envelopes/bulk", response_model=BulkActionResponse)
async def bulk_action(
    data: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.envelope.update")
):
    """Execute une action en masse sur des enveloppes."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)

    success = 0
    failed = 0
    errors = {}

    for envelope_id in data.envelope_ids:
        try:
            if data.action == "send":
                await service.send_envelope(envelope_id)
            elif data.action == "cancel":
                await service.cancel_envelope(envelope_id, data.reason or "Bulk cancel")
            elif data.action == "remind":
                await service.send_reminder(envelope_id)
            elif data.action == "archive":
                envelope = service.get_envelope(envelope_id)
                if envelope:
                    service.envelope_repo.archive(envelope)
            success += 1
        except Exception as e:
            failed += 1
            errors[str(envelope_id)] = str(e)

    return BulkActionResponse(
        total=len(data.envelope_ids),
        success=success,
        failed=failed,
        errors=errors
    )


# =============================================================================
# SIGNER PUBLIC ENDPOINTS (No auth required)
# =============================================================================

@router.get("/sign/{token}")
async def view_as_signer(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Page de signature pour un signataire (acces via token unique).

    Note: En production, cette route redirige vers l'UI de signature.
    """
    # Extraire tenant_id du token ou de la config
    # Pour simplifier, on cherche dans toutes les tenants (ou utiliser un prefix dans le token)

    try:
        # Recherche du signataire par token
        from .repository import EnvelopeSignerRepository
        from .models import EnvelopeSigner

        signer = db.query(EnvelopeSigner).filter(
            EnvelopeSigner.access_token == token
        ).first()

        if not signer:
            raise HTTPException(status_code=404, detail="Lien de signature invalide ou expire")

        service = get_esignature_service(db, signer.tenant_id)
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        envelope, signer = service.view_envelope_as_signer(token, ip, user_agent)

        return {
            "envelope": {
                "id": str(envelope.id),
                "name": envelope.name,
                "status": envelope.status.value,
                "documents": [
                    {
                        "id": str(d.id),
                        "name": d.name,
                        "page_count": d.page_count
                    }
                    for d in envelope.documents
                ]
            },
            "signer": {
                "id": str(signer.id),
                "email": signer.email,
                "name": f"{signer.first_name} {signer.last_name}",
                "status": signer.status.value
            }
        }

    except InvalidAccessTokenError:
        raise HTTPException(status_code=401, detail="Token invalide ou expire")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sign/{token}")
async def sign_as_signer(
    token: str,
    signatures: dict,  # {"field_id": "signature_base64", ...}
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Signe l'enveloppe avec les signatures fournies.
    """
    try:
        from .models import EnvelopeSigner
        signer = db.query(EnvelopeSigner).filter(
            EnvelopeSigner.access_token == token
        ).first()

        if not signer:
            raise HTTPException(status_code=404, detail="Lien invalide")

        service = get_esignature_service(db, signer.tenant_id)
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        envelope, signer = await service.sign_envelope(token, signatures, ip, user_agent)

        return {
            "success": True,
            "message": "Signature enregistree",
            "envelope_status": envelope.status.value,
            "signer_status": signer.status.value
        }

    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/sign/{token}/decline")
async def decline_as_signer(
    token: str,
    data: DeclineRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refuse de signer."""
    try:
        from .models import EnvelopeSigner
        signer = db.query(EnvelopeSigner).filter(
            EnvelopeSigner.access_token == token
        ).first()

        if not signer:
            raise HTTPException(status_code=404, detail="Lien invalide")

        service = get_esignature_service(db, signer.tenant_id)
        ip = request.client.host if request.client else None

        envelope, signer = service.decline_envelope(token, data.reason, ip)

        return {
            "success": True,
            "message": "Signature refusee",
            "envelope_status": envelope.status.value
        }

    except ESignatureError as e:
        handle_esignature_error(e)


@router.post("/sign/{token}/delegate")
async def delegate_signature(
    token: str,
    data: DelegateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delegue la signature a une autre personne."""
    try:
        from .models import EnvelopeSigner
        signer = db.query(EnvelopeSigner).filter(
            EnvelopeSigner.access_token == token
        ).first()

        if not signer:
            raise HTTPException(status_code=404, detail="Lien invalide")

        service = get_esignature_service(db, signer.tenant_id)
        ip = request.client.host if request.client else None

        new_signer = service.delegate_signature(
            token,
            data.delegate_email,
            data.delegate_first_name,
            data.delegate_last_name,
            data.reason,
            ip
        )

        return {
            "success": True,
            "message": f"Signature deleguee a {data.delegate_email}",
            "delegate_email": new_signer.email
        }

    except ESignatureError as e:
        handle_esignature_error(e)


# =============================================================================
# DOWNLOADS
# =============================================================================

@router.get("/envelopes/{envelope_id}/documents/{document_id}/download")
async def download_document(
    envelope_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.document.read")
):
    """Telecharge un document (original ou signe)."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        content, filename = service.get_signed_document(envelope_id, document_id)

        return StreamingResponse(
            BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ESignatureError as e:
        handle_esignature_error(e)


@router.get("/envelopes/{envelope_id}/certificate/download")
async def download_certificate(
    envelope_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.certificate.read")
):
    """Telecharge le certificat de signature."""
    try:
        service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
        content, filename = service.get_certificate(envelope_id)

        return StreamingResponse(
            BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ESignatureError as e:
        handle_esignature_error(e)


# =============================================================================
# AUDIT TRAIL
# =============================================================================

@router.get("/envelopes/{envelope_id}/audit", response_model=List[AuditEventResponse])
async def get_envelope_audit_trail(
    envelope_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.audit.read")
):
    """Recupere l'historique d'audit d'une enveloppe."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)

    envelope = service.get_envelope(envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Enveloppe non trouvee")

    events = service.get_audit_trail(envelope_id)
    return events


@router.get("/envelopes/{envelope_id}/certificates", response_model=List[CertificateResponse])
async def get_envelope_certificates(
    envelope_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.certificate.read")
):
    """Recupere les certificats d'une enveloppe."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    certificates = service.certificate_repo.get_by_envelope(envelope_id)
    return certificates


# =============================================================================
# WEBHOOKS
# =============================================================================

@router.post("/webhooks/{provider}")
async def receive_webhook(
    provider: SignatureProvider,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour recevoir les webhooks des providers.

    Note: Chaque provider utilise une signature differente pour la verification.
    """
    payload = await request.body()
    signature = request.headers.get("x-webhook-signature") or \
                request.headers.get("x-docusign-signature") or \
                request.headers.get("x-hellosign-signature")

    # Determiner le tenant_id depuis le payload
    import json
    data = json.loads(payload)

    # Extraire le tenant_id des metadonnees
    tenant_id = None
    if provider == SignatureProvider.YOUSIGN:
        tenant_id = data.get("data", {}).get("signature_request", {}).get("external_id", "").split("_")[0]
    elif provider == SignatureProvider.DOCUSIGN:
        tenant_id = data.get("envelopeStatus", {}).get("customFields", {}).get("tenant_id")

    if not tenant_id:
        # Fallback: chercher l'enveloppe par external_id
        from .models import SignatureEnvelope
        external_id = None
        if provider == SignatureProvider.YOUSIGN:
            external_id = data.get("data", {}).get("signature_request", {}).get("id")
        elif provider == SignatureProvider.DOCUSIGN:
            external_id = data.get("envelopeStatus", {}).get("envelopeId")

        if external_id:
            envelope = db.query(SignatureEnvelope).filter(
                SignatureEnvelope.external_id == external_id
            ).first()
            if envelope:
                tenant_id = envelope.tenant_id

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Impossible de determiner le tenant")

    try:
        service = get_esignature_service(db, tenant_id)
        envelope = await service.handle_webhook(provider, payload, signature)

        return {"success": True, "envelope_id": str(envelope.id) if envelope else None}

    except Exception as e:
        # Logger l'erreur mais retourner 200 pour eviter les retries
        import logging
        logging.exception(f"Erreur webhook {provider}: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.stats.read")
):
    """Recupere les statistiques pour le tableau de bord."""
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    return service.get_dashboard_stats()


@router.get("/stats/period", response_model=SignatureStatsResponse)
async def get_period_stats(
    period_type: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = require_permission("esignature.stats.read")
):
    """Recupere les statistiques pour une periode."""
    from datetime import datetime
    service = get_esignature_service(db, str(current_user.tenant_id), current_user.id)
    return service._calculate_stats(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
        period_type
    )
