"""
AZALSCORE Module I18N - Routes API
===================================

API REST complete pour l'internationalisation.
CRUD, Autocomplete, Permissions verifiees.
"""
from __future__ import annotations


from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.dependencies_v2 import require_permission

from .models import (
    LanguageStatus, TranslationStatus, TranslationScope,
    DateFormatType, NumberFormatType, ImportExportFormat
)
from .schemas import (
    # Language
    LanguageCreate, LanguageUpdate, LanguageResponse, LanguageList, LanguageFilters,
    # Namespace
    NamespaceCreate, NamespaceUpdate, NamespaceResponse, NamespaceList,
    # Translation Key
    TranslationKeyCreate, TranslationKeyUpdate, TranslationKeyResponse,
    TranslationKeyWithTranslations, TranslationKeyList, TranslationKeyFilters,
    # Translation
    TranslationCreate, TranslationUpdate, TranslationResponse, TranslationList,
    TranslationBulkUpdate, TranslationFilters,
    # Bundle
    TranslationBundle, TranslationBundleRequest,
    # Inline
    InlineTranslationRequest, InlineTranslationResponse,
    # Auto-translate
    AutoTranslateRequest, TranslationJobResponse, TranslationJobList,
    # Import/Export
    ImportRequest, ExportRequest, ImportExportResponse,
    # Glossary
    GlossaryCreate, GlossaryUpdate, GlossaryResponse, GlossaryList,
    # Dashboard
    TranslationDashboard, CoverageReport, LanguageStats,
    # Common
    AutocompleteResponse, BulkDeleteRequest, BulkResult,
    FormatRequest, FormatResponse,
)
from .service import I18NService
from .exceptions import (
    LanguageNotFoundError, LanguageDuplicateError, LanguageDeleteError,
    NamespaceNotFoundError, NamespaceDuplicateError, NamespaceNotEditableError,
    TranslationKeyNotFoundError, TranslationKeyDuplicateError,
    TranslationNotFoundError, TranslationLengthError,
    GlossaryTermNotFoundError, GlossaryTermDuplicateError,
    AutoTranslationError, AutoTranslationProviderError,
)

router = APIRouter(prefix="/i18n", tags=["Internationalization"])


# ============================================================================
# HELPERS
# ============================================================================

def get_i18n_service(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> I18NService:
    """Dependency pour obtenir le service I18N."""
    return I18NService(db, user.tenant_id)


def handle_i18n_exception(e: Exception):
    """Convertit les exceptions metier en HTTPException."""
    if isinstance(e, (LanguageNotFoundError, NamespaceNotFoundError,
                      TranslationKeyNotFoundError, TranslationNotFoundError,
                      GlossaryTermNotFoundError)):
        raise HTTPException(status_code=404, detail=str(e))
    elif isinstance(e, (LanguageDuplicateError, NamespaceDuplicateError,
                        TranslationKeyDuplicateError, GlossaryTermDuplicateError)):
        raise HTTPException(status_code=409, detail=str(e))
    elif isinstance(e, (LanguageDeleteError, NamespaceNotEditableError,
                        TranslationLengthError)):
        raise HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, (AutoTranslationError, AutoTranslationProviderError)):
        raise HTTPException(status_code=503, detail=str(e))
    else:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LANGUAGE ROUTES
# ============================================================================

@router.get("/languages", response_model=LanguageList)
async def list_languages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1),
    status: Optional[List[LanguageStatus]] = Query(None),
    is_default: Optional[bool] = Query(None),
    rtl: Optional[bool] = Query(None),
    sort_by: str = Query("sort_order"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste paginee des langues."""
    items, total = service.list_languages(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        is_default=is_default,
        rtl=rtl
    )
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/languages/active", response_model=List[LanguageResponse])
async def list_active_languages(
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste des langues actives."""
    return service.get_active_languages()


@router.get("/languages/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_languages(
    prefix: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Autocomplete pour les langues."""
    items = service.language_repo.autocomplete(prefix, limit)
    return {"items": items}


@router.get("/languages/default", response_model=LanguageResponse)
async def get_default_language(
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere la langue par defaut."""
    lang = service.get_default_language()
    if not lang:
        raise HTTPException(status_code=404, detail="No default language configured")
    return lang


@router.get("/languages/{id}", response_model=LanguageResponse)
async def get_language(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere une langue par ID."""
    try:
        return service.get_language(id)
    except LanguageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/languages", response_model=LanguageResponse, status_code=201)
async def create_language(
    data: LanguageCreate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.create"))
):
    """Cree une nouvelle langue."""
    try:
        return service.create_language(data, user.id)
    except LanguageDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/languages/{id}", response_model=LanguageResponse)
async def update_language(
    id: UUID,
    data: LanguageUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Met a jour une langue."""
    try:
        return service.update_language(id, data, user.id)
    except LanguageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/languages/{id}", status_code=204)
async def delete_language(
    id: UUID,
    hard: bool = Query(False),
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.delete"))
):
    """Supprime une langue."""
    try:
        service.delete_language(id, user.id, hard)
    except (LanguageNotFoundError, LanguageDeleteError) as e:
        handle_i18n_exception(e)


@router.post("/languages/{id}/set-default", response_model=LanguageResponse)
async def set_default_language(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Definit une langue comme langue par defaut."""
    try:
        return service.set_default_language(id, user.id)
    except LanguageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# NAMESPACE ROUTES
# ============================================================================

@router.get("/namespaces", response_model=NamespaceList)
async def list_namespaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, min_length=1),
    module_code: Optional[str] = Query(None),
    sort_by: str = Query("code"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste paginee des namespaces."""
    items, total = service.list_namespaces(
        page=page,
        page_size=page_size,
        search=search,
        module_code=module_code
    )
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/namespaces/{id}", response_model=NamespaceResponse)
async def get_namespace(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere un namespace par ID."""
    try:
        return service.get_namespace(id)
    except NamespaceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/namespaces", response_model=NamespaceResponse, status_code=201)
async def create_namespace(
    data: NamespaceCreate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.create"))
):
    """Cree un nouveau namespace."""
    try:
        return service.create_namespace(data, user.id)
    except NamespaceDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/namespaces/{id}", response_model=NamespaceResponse)
async def update_namespace(
    id: UUID,
    data: NamespaceUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Met a jour un namespace."""
    try:
        return service.update_namespace(id, data, user.id)
    except (NamespaceNotFoundError, NamespaceNotEditableError) as e:
        handle_i18n_exception(e)


@router.delete("/namespaces/{id}", status_code=204)
async def delete_namespace(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.delete"))
):
    """Supprime un namespace."""
    try:
        service.delete_namespace(id, user.id)
    except (NamespaceNotFoundError, NamespaceNotEditableError) as e:
        handle_i18n_exception(e)


# ============================================================================
# TRANSLATION KEY ROUTES
# ============================================================================

@router.get("/keys", response_model=TranslationKeyList)
async def list_translation_keys(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, min_length=1),
    namespace_id: Optional[UUID] = Query(None),
    namespace_code: Optional[str] = Query(None),
    scope: Optional[TranslationScope] = Query(None),
    entity_type: Optional[str] = Query(None),
    sort_by: str = Query("key"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste paginee des cles de traduction."""
    items, total = service.list_translation_keys(
        page=page,
        page_size=page_size,
        search=search,
        namespace_id=namespace_id,
        namespace_code=namespace_code,
        scope=scope,
        entity_type=entity_type
    )
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/keys/missing/{language_code}")
async def get_missing_keys(
    language_code: str,
    namespace_code: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere les cles sans traduction pour une langue."""
    try:
        keys = service.get_missing_keys_for_language(language_code, namespace_code, limit)
        return {"items": keys, "count": len(keys)}
    except LanguageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/keys/{id}", response_model=TranslationKeyWithTranslations)
async def get_translation_key(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere une cle avec ses traductions."""
    try:
        key = service.get_translation_key(id)
        # Recuperer les traductions
        translations = {}
        for lang in service.get_active_languages():
            trans = service.get_translation(key.id, lang.id)
            if trans:
                translations[lang.code] = trans

        return {**key.__dict__, "translations": translations}
    except TranslationKeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/keys", response_model=TranslationKeyResponse, status_code=201)
async def create_translation_key(
    data: TranslationKeyCreate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.create"))
):
    """Cree une nouvelle cle de traduction."""
    try:
        return service.create_translation_key(data, user.id)
    except (NamespaceNotFoundError, TranslationKeyDuplicateError) as e:
        handle_i18n_exception(e)


@router.put("/keys/{id}", response_model=TranslationKeyResponse)
async def update_translation_key(
    id: UUID,
    data: TranslationKeyUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Met a jour une cle de traduction."""
    try:
        return service.update_translation_key(id, data, user.id)
    except TranslationKeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/keys/{id}", status_code=204)
async def delete_translation_key(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.delete"))
):
    """Supprime une cle de traduction."""
    try:
        service.delete_translation_key(id, user.id)
    except TranslationKeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# TRANSLATION ROUTES
# ============================================================================

@router.get("/translations", response_model=TranslationList)
async def list_translations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, min_length=1),
    language_code: Optional[str] = Query(None),
    namespace_code: Optional[str] = Query(None),
    status: Optional[List[TranslationStatus]] = Query(None),
    is_machine_translated: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste paginee des traductions."""
    filters = TranslationFilters(
        search=search,
        language_code=language_code,
        namespace_code=namespace_code,
        status=status,
        is_machine_translated=is_machine_translated
    )
    items, total = service.translation_repo.list(filters, page, page_size, sort_by, sort_dir)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.put("/translations/{key_id}/{language_id}", response_model=TranslationResponse)
async def set_translation(
    key_id: UUID,
    language_id: UUID,
    data: TranslationUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Definit ou met a jour une traduction."""
    try:
        return service.set_translation(
            key_id,
            language_id,
            data.value,
            data.plural_values,
            data.status or TranslationStatus.DRAFT,
            user.id
        )
    except (TranslationKeyNotFoundError, LanguageNotFoundError, TranslationLengthError) as e:
        handle_i18n_exception(e)


@router.post("/translations/{id}/validate", response_model=TranslationResponse)
async def validate_translation(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.validate"))
):
    """Valide une traduction."""
    try:
        return service.validate_translation(id, user.id)
    except TranslationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/translations/bulk", response_model=BulkResult)
async def bulk_update_translations(
    data: TranslationBulkUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Mise a jour en masse des traductions."""
    try:
        created, updated = service.bulk_update_translations(data, user.id)
        return {"success": created + updated, "errors": []}
    except Exception as e:
        return {"success": 0, "errors": [{"error": str(e)}]}


@router.post("/translations/inline", response_model=InlineTranslationResponse)
async def inline_translate(
    data: InlineTranslationRequest,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Traduction inline depuis le frontend."""
    try:
        return service.inline_translate(data, user.id)
    except (LanguageNotFoundError, TranslationKeyNotFoundError) as e:
        handle_i18n_exception(e)


# ============================================================================
# BUNDLE ROUTES (pour le frontend)
# ============================================================================

@router.get("/bundle/{language_code}/{namespace_code}", response_model=TranslationBundle)
async def get_translation_bundle(
    language_code: str,
    namespace_code: str,
    no_cache: bool = Query(False),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere un bundle de traductions pour le frontend."""
    try:
        return service.get_bundle(language_code, namespace_code, use_cache=not no_cache)
    except (LanguageNotFoundError, NamespaceNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bundles", response_model=dict)
async def get_translation_bundles(
    request: TranslationBundleRequest,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere plusieurs bundles de traductions."""
    bundles = service.get_bundles(request.language, request.namespaces)
    return {ns: bundle.translations for ns, bundle in bundles.items()}


@router.post("/cache/invalidate")
async def invalidate_cache(
    namespace_code: Optional[str] = Query(None),
    language_code: Optional[str] = Query(None),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.admin"))
):
    """Invalide le cache de traductions."""
    count = service.invalidate_cache(namespace_code, language_code)
    return {"invalidated": count}


# ============================================================================
# TRANSLATE FUNCTION (simple API)
# ============================================================================

@router.get("/t/{namespace}/{key}")
async def translate(
    namespace: str,
    key: str,
    lang: str = Query("fr"),
    service: I18NService = Depends(get_i18n_service)
):
    """Traduit une cle (API simple)."""
    value = service.t(key, lang, namespace)
    return {"key": f"{namespace}.{key}", "language": lang, "value": value}


# ============================================================================
# AUTO-TRANSLATE ROUTES
# ============================================================================

@router.post("/auto-translate", response_model=TranslationJobResponse)
async def start_auto_translation(
    data: AutoTranslateRequest,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.admin"))
):
    """Lance un job de traduction automatique."""
    try:
        import asyncio
        job = asyncio.get_event_loop().run_until_complete(
            service.auto_translate(data, user.id)
        )
        return job
    except (AutoTranslationError, AutoTranslationProviderError) as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/jobs", response_model=TranslationJobList)
async def list_translation_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste les jobs de traduction."""
    items, total = service.job_repo.list(page, page_size)
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/jobs/{id}", response_model=TranslationJobResponse)
async def get_translation_job(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere un job de traduction."""
    job = service.job_repo.get_by_id(id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job


# ============================================================================
# IMPORT/EXPORT ROUTES
# ============================================================================

@router.post("/export")
async def export_translations(
    request: ExportRequest,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.export"))
):
    """Exporte les traductions."""
    data = service.export_translations(request, user.id)
    return JSONResponse(content=data)


@router.post("/import", response_model=ImportExportResponse)
async def import_translations(
    request: ImportRequest,
    file: UploadFile = File(...),
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.import"))
):
    """Importe des traductions depuis un fichier."""
    import json

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    created, updated, skipped, errors = service.import_translations(
        data, request, user.id
    )

    return {
        "id": str(uuid_module.uuid4()),
        "tenant_id": service.tenant_id,
        "operation": "import",
        "format": request.format,
        "file_name": file.filename,
        "file_url": None,
        "file_size": len(content),
        "language_codes": request.language_codes or [],
        "namespace_codes": request.namespace_codes or [],
        "status": "completed",
        "total_keys": created + updated + skipped,
        "processed_keys": created + updated,
        "new_keys": created,
        "updated_keys": updated,
        "skipped_keys": skipped,
        "error_keys": len(errors),
        "errors": errors,
        "created_by": user.id,
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow()
    }


# ============================================================================
# FORMAT ROUTES
# ============================================================================

@router.post("/format/date")
async def format_date(
    date_str: str = Query(..., description="Date ISO format"),
    language_code: str = Query("fr"),
    format_type: Optional[DateFormatType] = Query(None),
    service: I18NService = Depends(get_i18n_service)
):
    """Formate une date."""
    from datetime import date
    try:
        dt = date.fromisoformat(date_str)
        formatted = service.format_date(dt, language_code, format_type)
        return {"original": date_str, "formatted": formatted, "language": language_code}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/format/number")
async def format_number(
    value: float = Query(...),
    language_code: str = Query("fr"),
    decimals: int = Query(2, ge=0, le=10),
    service: I18NService = Depends(get_i18n_service)
):
    """Formate un nombre."""
    from decimal import Decimal
    formatted = service.format_number(Decimal(str(value)), language_code, decimals)
    return {"original": value, "formatted": formatted, "language": language_code}


@router.post("/format/currency")
async def format_currency(
    amount: float = Query(...),
    currency: str = Query("EUR"),
    language_code: str = Query("fr"),
    decimals: int = Query(2, ge=0, le=10),
    service: I18NService = Depends(get_i18n_service)
):
    """Formate un montant."""
    from decimal import Decimal
    formatted = service.format_currency(
        Decimal(str(amount)), currency, language_code, decimals
    )
    return {"original": amount, "formatted": formatted, "currency": currency, "language": language_code}


# ============================================================================
# GLOSSARY ROUTES
# ============================================================================

@router.get("/glossary", response_model=GlossaryList)
async def list_glossary_terms(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, min_length=1),
    term_type: Optional[str] = Query(None),
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Liste les termes du glossaire."""
    items, total = service.list_glossary_terms(
        page=page,
        page_size=page_size,
        search=search,
        term_type=term_type
    )
    pages = (total + page_size - 1) // page_size
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.post("/glossary", response_model=GlossaryResponse, status_code=201)
async def create_glossary_term(
    data: GlossaryCreate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.create"))
):
    """Cree un terme de glossaire."""
    try:
        return service.create_glossary_term(data, user.id)
    except GlossaryTermDuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/glossary/{id}", response_model=GlossaryResponse)
async def update_glossary_term(
    id: UUID,
    data: GlossaryUpdate,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.edit"))
):
    """Met a jour un terme de glossaire."""
    try:
        return service.update_glossary_term(id, data, user.id)
    except GlossaryTermNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/glossary/{id}", status_code=204)
async def delete_glossary_term(
    id: UUID,
    service: I18NService = Depends(get_i18n_service),
    user=Depends(get_current_user),
    _: None = Depends(require_permission("i18n.delete"))
):
    """Supprime un terme de glossaire."""
    try:
        service.delete_glossary_term(id, user.id)
    except GlossaryTermNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@router.get("/dashboard", response_model=TranslationDashboard)
async def get_dashboard(
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Recupere le dashboard de couverture."""
    return service.get_dashboard()


@router.get("/coverage/{language_code}", response_model=CoverageReport)
async def get_coverage_report(
    language_code: str,
    service: I18NService = Depends(get_i18n_service),
    _: None = Depends(require_permission("i18n.view"))
):
    """Rapport de couverture pour une langue."""
    try:
        return service.get_coverage_report(language_code)
    except LanguageNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Import manquant
import uuid as uuid_module
from datetime import datetime
