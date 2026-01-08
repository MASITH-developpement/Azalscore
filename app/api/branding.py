"""
AZALS API - Gestion du Branding
===============================

Endpoints pour gérer le favicon, logo et titre de l'application.
Accessible uniquement aux rôles ADMIN et DIRIGEANT.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.core.models import User, UserRole

router = APIRouter(prefix="/branding", tags=["Branding"])

# Configuration
UPLOAD_DIR = Path(__file__).parent.parent.parent / "ui"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


# ============================================================================
# SCHEMAS
# ============================================================================

class BrandingConfig(BaseModel):
    """Configuration de branding actuelle."""
    title: str = "Azalscore"
    favicon_url: str = "/static/favicon.png"
    logo_url: Optional[str] = None
    primary_color: str = "#1e40af"
    secondary_color: str = "#3b82f6"
    enable_tenant_branding: bool = False


class BrandingUpdateRequest(BaseModel):
    """Requête de mise à jour du branding."""
    title: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


# ============================================================================
# HELPERS
# ============================================================================

def require_admin_role(user: User) -> None:
    """Vérifie que l'utilisateur a un rôle admin."""
    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou DIRIGEANT requis."
        )


def validate_image_file(file: UploadFile) -> None:
    """Valide le fichier image uploadé."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non autorisée. Extensions valides: {', '.join(ALLOWED_EXTENSIONS)}"
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=BrandingConfig)
async def get_branding_config(
    current_user: User = Depends(get_current_user)
) -> BrandingConfig:
    """
    Récupère la configuration de branding actuelle.
    Accessible à tous les utilisateurs authentifiés.
    """
    # Vérifier si un favicon custom existe
    custom_favicon = UPLOAD_DIR / "favicon-custom.png"
    favicon_url = "/static/favicon-custom.png" if custom_favicon.exists() else "/static/favicon.png"

    # Vérifier si un logo custom existe
    custom_logo = UPLOAD_DIR / "logo-custom.png"
    logo_url = "/static/logo-custom.png" if custom_logo.exists() else None

    return BrandingConfig(
        title="Azalscore",
        favicon_url=favicon_url,
        logo_url=logo_url,
        primary_color="#1e40af",
        secondary_color="#3b82f6",
        enable_tenant_branding=False
    )


@router.post("/favicon")
async def upload_favicon(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload un nouveau favicon.
    Réservé aux rôles ADMIN et DIRIGEANT.

    Formats acceptés: PNG, JPG, ICO, SVG
    Taille max: 2 MB
    Taille recommandée: 32x32 ou 64x64 pixels
    """
    require_admin_role(current_user)
    validate_image_file(file)

    # Lire le contenu du fichier
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    # Sauvegarder le favicon
    ext = Path(file.filename).suffix.lower()

    # Convertir en PNG si nécessaire (garder l'original pour l'instant)
    if ext in [".png", ".ico"]:
        favicon_path = UPLOAD_DIR / "favicon-custom.png"
    else:
        favicon_path = UPLOAD_DIR / f"favicon-custom{ext}"

    # Backup de l'ancien favicon custom si existant
    if favicon_path.exists():
        backup_path = UPLOAD_DIR / f"favicon-custom.backup{ext}"
        shutil.copy(favicon_path, backup_path)

    # Sauvegarder le nouveau favicon
    with open(favicon_path, "wb") as f:
        f.write(content)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Favicon mis à jour avec succès",
            "favicon_url": f"/static/favicon-custom{ext if ext != '.png' else '.png'}",
            "uploaded_at": datetime.utcnow().isoformat()
        }
    )


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload un nouveau logo.
    Réservé aux rôles ADMIN et DIRIGEANT.

    Formats acceptés: PNG, JPG, SVG
    Taille max: 2 MB
    Taille recommandée: 200x50 pixels (format horizontal)
    """
    require_admin_role(current_user)
    validate_image_file(file)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    ext = Path(file.filename).suffix.lower()
    logo_path = UPLOAD_DIR / f"logo-custom{ext}"

    # Backup
    if logo_path.exists():
        backup_path = UPLOAD_DIR / f"logo-custom.backup{ext}"
        shutil.copy(logo_path, backup_path)

    with open(logo_path, "wb") as f:
        f.write(content)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Logo mis à jour avec succès",
            "logo_url": f"/static/logo-custom{ext}",
            "uploaded_at": datetime.utcnow().isoformat()
        }
    )


@router.delete("/favicon")
async def reset_favicon(
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Réinitialise le favicon par défaut (Azalscore).
    Réservé aux rôles ADMIN et DIRIGEANT.
    """
    require_admin_role(current_user)

    # Supprimer le favicon custom
    for ext in ALLOWED_EXTENSIONS:
        custom_path = UPLOAD_DIR / f"favicon-custom{ext}"
        if custom_path.exists():
            custom_path.unlink()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Favicon réinitialisé par défaut",
            "favicon_url": "/static/favicon.png"
        }
    )


@router.delete("/logo")
async def reset_logo(
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Supprime le logo personnalisé.
    Réservé aux rôles ADMIN et DIRIGEANT.
    """
    require_admin_role(current_user)

    for ext in ALLOWED_EXTENSIONS:
        custom_path = UPLOAD_DIR / f"logo-custom{ext}"
        if custom_path.exists():
            custom_path.unlink()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Logo supprimé",
            "logo_url": None
        }
    )
