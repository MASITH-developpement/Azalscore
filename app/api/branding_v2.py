"""
AZALS API - Branding v2 (CORE SaaS)
====================================

Gestion du favicon, logo et titre de l'application.
Version CORE SaaS avec isolation multi-tenant.

MIGRATION CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user()
- SaaSContext fournit tenant_id + user_id directement
- Support du branding par tenant
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/branding", tags=["Branding v2 - CORE SaaS"])

# Configuration
UPLOAD_DIR = Path(__file__).parent.parent.parent / "ui"
TENANT_BRANDING_DIR = Path(__file__).parent.parent.parent / "ui" / "tenants"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


# ============================================================================
# SCHEMAS
# ============================================================================

class BrandingConfig(BaseModel):
    """Configuration de branding actuelle."""
    title: str = "Azalscore"
    favicon_url: str = "/static/favicon.png"
    logo_url: str | None = None
    primary_color: str = "#1e40af"
    secondary_color: str = "#3b82f6"
    enable_tenant_branding: bool = False
    tenant_id: str | None = None


class BrandingUpdateRequest(BaseModel):
    """Requete de mise a jour du branding."""
    title: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None


class UploadResponse(BaseModel):
    """Reponse d'upload."""
    message: str
    url: str
    uploaded_at: str


class ResetResponse(BaseModel):
    """Reponse de reset."""
    message: str
    url: str | None = None


# ============================================================================
# HELPERS
# ============================================================================

def _require_admin_role(context: SaaSContext) -> None:
    """Verifie que l'utilisateur a un role admin."""
    admin_roles = {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DIRIGEANT}
    if context.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse. Role ADMIN ou DIRIGEANT requis."
        )


def _validate_image_file(file: UploadFile) -> None:
    """Valide le fichier image uploade."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier manquant"
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension non autorisee. Extensions valides: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def _get_tenant_dir(tenant_id: str) -> Path:
    """Retourne le repertoire de branding du tenant."""
    tenant_dir = TENANT_BRANDING_DIR / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=BrandingConfig)
async def get_branding_config(
    context: SaaSContext = Depends(get_saas_context)
) -> BrandingConfig:
    """
    Recupere la configuration de branding actuelle.

    CORE SaaS: Retourne le branding specifique au tenant si disponible.
    """
    tenant_id = context.tenant_id

    # Verifier le branding tenant-specific
    tenant_dir = TENANT_BRANDING_DIR / tenant_id
    if tenant_dir.exists():
        # Favicon tenant
        tenant_favicon = tenant_dir / "favicon-custom.png"
        favicon_url = f"/static/tenants/{tenant_id}/favicon-custom.png" if tenant_favicon.exists() else "/static/favicon.png"

        # Logo tenant
        tenant_logo = tenant_dir / "logo-custom.png"
        logo_url = f"/static/tenants/{tenant_id}/logo-custom.png" if tenant_logo.exists() else None

        return BrandingConfig(
            title="Azalscore",
            favicon_url=favicon_url,
            logo_url=logo_url,
            primary_color="#1e40af",
            secondary_color="#3b82f6",
            enable_tenant_branding=True,
            tenant_id=tenant_id
        )

    # Fallback vers branding global
    custom_favicon = UPLOAD_DIR / "favicon-custom.png"
    favicon_url = "/static/favicon-custom.png" if custom_favicon.exists() else "/static/favicon.png"

    custom_logo = UPLOAD_DIR / "logo-custom.png"
    logo_url = "/static/logo-custom.png" if custom_logo.exists() else None

    return BrandingConfig(
        title="Azalscore",
        favicon_url=favicon_url,
        logo_url=logo_url,
        primary_color="#1e40af",
        secondary_color="#3b82f6",
        enable_tenant_branding=False,
        tenant_id=tenant_id
    )


@router.post("/favicon", response_model=UploadResponse)
async def upload_favicon(
    file: UploadFile = File(...),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Upload un nouveau favicon pour le tenant.

    CORE SaaS: Le favicon est stocke dans le repertoire du tenant.

    Formats acceptes: PNG, JPG, ICO, SVG
    Taille max: 2 MB
    Taille recommandee: 32x32 ou 64x64 pixels
    """
    _require_admin_role(context)
    _validate_image_file(file)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    ext = Path(file.filename).suffix.lower()
    tenant_dir = _get_tenant_dir(context.tenant_id)

    favicon_path = tenant_dir / "favicon-custom.png" if ext in [".png", ".ico"] else tenant_dir / f"favicon-custom{ext}"

    # Backup
    if favicon_path.exists():
        backup_path = tenant_dir / f"favicon-custom.backup{ext}"
        shutil.copy(favicon_path, backup_path)

    with open(favicon_path, "wb") as f:
        f.write(content)

    logger.info(
        "[BRANDING_V2] Favicon mis a jour",
        extra={
            "tenant_id": context.tenant_id,
            "user_id": str(context.user_id),
            "file_size": len(content)
        }
    )

    return UploadResponse(
        message="Favicon mis a jour avec succes",
        url=f"/static/tenants/{context.tenant_id}/favicon-custom{ext if ext != '.png' else '.png'}",
        uploaded_at=datetime.utcnow().isoformat()
    )


@router.post("/logo", response_model=UploadResponse)
async def upload_logo(
    file: UploadFile = File(...),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Upload un nouveau logo pour le tenant.

    CORE SaaS: Le logo est stocke dans le repertoire du tenant.

    Formats acceptes: PNG, JPG, SVG
    Taille max: 2 MB
    Taille recommandee: 200x50 pixels (format horizontal)
    """
    _require_admin_role(context)
    _validate_image_file(file)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    ext = Path(file.filename).suffix.lower()
    tenant_dir = _get_tenant_dir(context.tenant_id)
    logo_path = tenant_dir / f"logo-custom{ext}"

    # Backup
    if logo_path.exists():
        backup_path = tenant_dir / f"logo-custom.backup{ext}"
        shutil.copy(logo_path, backup_path)

    with open(logo_path, "wb") as f:
        f.write(content)

    logger.info(
        "[BRANDING_V2] Logo mis a jour",
        extra={
            "tenant_id": context.tenant_id,
            "user_id": str(context.user_id),
            "file_size": len(content)
        }
    )

    return UploadResponse(
        message="Logo mis a jour avec succes",
        url=f"/static/tenants/{context.tenant_id}/logo-custom{ext}",
        uploaded_at=datetime.utcnow().isoformat()
    )


@router.delete("/favicon", response_model=ResetResponse)
async def reset_favicon(
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Reinitialise le favicon par defaut.

    CORE SaaS: Supprime le favicon custom du tenant.
    """
    _require_admin_role(context)

    tenant_dir = TENANT_BRANDING_DIR / context.tenant_id
    if tenant_dir.exists():
        for ext in ALLOWED_EXTENSIONS:
            custom_path = tenant_dir / f"favicon-custom{ext}"
            if custom_path.exists():
                custom_path.unlink()

    logger.info(
        "[BRANDING_V2] Favicon reinitialise",
        extra={
            "tenant_id": context.tenant_id,
            "user_id": str(context.user_id)
        }
    )

    return ResetResponse(
        message="Favicon reinitialise par defaut",
        url="/static/favicon.png"
    )


@router.delete("/logo", response_model=ResetResponse)
async def reset_logo(
    context: SaaSContext = Depends(get_saas_context)
):
    """
    Supprime le logo personnalise.

    CORE SaaS: Supprime le logo custom du tenant.
    """
    _require_admin_role(context)

    tenant_dir = TENANT_BRANDING_DIR / context.tenant_id
    if tenant_dir.exists():
        for ext in ALLOWED_EXTENSIONS:
            custom_path = tenant_dir / f"logo-custom{ext}"
            if custom_path.exists():
                custom_path.unlink()

    logger.info(
        "[BRANDING_V2] Logo supprime",
        extra={
            "tenant_id": context.tenant_id,
            "user_id": str(context.user_id)
        }
    )

    return ResetResponse(
        message="Logo supprime"
    )
