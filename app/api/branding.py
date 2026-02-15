"""
AZALS API - Gestion du Branding
===============================

Endpoints pour gérer le favicon, logo et titre de l'application.
Accessible uniquement aux rôles ADMIN et DIRIGEANT.
"""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.models import User

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
    logo_url: str | None = None
    primary_color: str = "#1e40af"
    secondary_color: str = "#3b82f6"
    enable_tenant_branding: bool = False


class BrandingUpdateRequest(BaseModel):
    """Requête de mise à jour du branding."""
    title: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None


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


def validate_image_file(file: UploadFile, content: bytes) -> str:
    """
    Valide le fichier image uploadé.

    SÉCURITÉ:
    - Vérifie l'extension du fichier
    - Vérifie les magic bytes pour confirmer le type réel
    - Empêche l'upload de fichiers malveillants déguisés

    Returns:
        Extension normalisée du fichier
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non autorisée. Extensions valides: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # SÉCURITÉ: Vérifier les magic bytes pour confirmer le type réel
    magic_bytes = {
        ".png": [b'\x89PNG\r\n\x1a\n'],
        ".jpg": [b'\xff\xd8\xff'],
        ".jpeg": [b'\xff\xd8\xff'],
        ".ico": [b'\x00\x00\x01\x00', b'\x00\x00\x02\x00'],  # ICO et CUR
        ".svg": [b'<?xml', b'<svg', b'<!DOCTYPE svg'],  # SVG peut commencer de plusieurs façons
    }

    expected_magic = magic_bytes.get(ext, [])
    if expected_magic:
        content_start = content[:20]  # Premiers octets

        # Pour SVG, vérifier aussi après le BOM potentiel
        if ext == ".svg":
            # Retirer BOM UTF-8 si présent
            if content_start.startswith(b'\xef\xbb\xbf'):
                content_start = content[3:23]
            # SVG peut avoir des espaces au début
            content_str = content[:100].decode('utf-8', errors='ignore').strip().lower()
            if not any(content_str.startswith(m.decode('utf-8', errors='ignore').lower()) for m in expected_magic):
                raise HTTPException(
                    status_code=400,
                    detail=f"Le contenu du fichier ne correspond pas à un fichier {ext} valide"
                )
        else:
            if not any(content_start.startswith(m) for m in expected_magic):
                raise HTTPException(
                    status_code=400,
                    detail=f"Le contenu du fichier ne correspond pas à un fichier {ext} valide"
                )

    return ext


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

    # Lire le contenu du fichier d'abord pour la validation complète
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    # SÉCURITÉ: Valider extension ET contenu (magic bytes)
    ext = validate_image_file(file, content)

    # Convertir en PNG si nécessaire (garder l'original pour l'instant)
    favicon_path = UPLOAD_DIR / "favicon-custom.png" if ext in [".png", ".ico"] else UPLOAD_DIR / f"favicon-custom{ext}"

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

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    # SÉCURITÉ: Valider extension ET contenu (magic bytes)
    ext = validate_image_file(file, content)
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
