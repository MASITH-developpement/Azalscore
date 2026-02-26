"""
AZALS - Module Backup - Router
==============================
Endpoints API pour les sauvegardes chiffrées.
"""
from __future__ import annotations



from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User

from .models import BackupStatus
from .schemas import (
    BackupConfigCreate,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupCreate,
    BackupDashboard,
    BackupDetail,
    BackupResponse,
    RestoreRequest,
    RestoreResponse,
)
from .service import get_backup_service

router = APIRouter(prefix="/backup", tags=["Sauvegardes Chiffrées"])


def get_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    return get_backup_service(db, tenant_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=BackupConfigResponse, status_code=201)
def create_config(
    data: BackupConfigCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Créer configuration backup avec génération de clé AES-256."""
    existing = service.get_config()
    if existing:
        raise HTTPException(status_code=409, detail="Configuration déjà existante")
    return service.create_config(data)


@router.get("/config", response_model=BackupConfigResponse)
def get_config(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupérer configuration backup."""
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.patch("/config", response_model=BackupConfigResponse)
def update_config(
    data: BackupConfigUpdate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour configuration backup."""
    config = service.update_config(data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


# ============================================================================
# BACKUPS
# ============================================================================

@router.post("", response_model=BackupResponse, status_code=201)
def create_backup(
    data: BackupCreate,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Créer une sauvegarde manuelle."""
    try:
        return service.create_backup(data, triggered_by=current_user.email or "api")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[BackupResponse])
def list_backups(
    status: BackupStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Lister les sauvegardes."""
    items, _ = service.list_backups(status, skip, limit)
    return items


@router.get("/{backup_id}", response_model=BackupDetail)
def get_backup(
    backup_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une sauvegarde."""
    backup = service.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde non trouvée")
    return backup


@router.delete("/{backup_id}", status_code=204)
def delete_backup(
    backup_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une sauvegarde."""
    backup = service.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde non trouvée")
    # Marquer comme supprimée
    backup.status = BackupStatus.DELETED
    service.db.commit()


@router.post("/{backup_id}/run", response_model=BackupResponse, status_code=201)
def run_backup(
    backup_id: str,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    Lancer une nouvelle sauvegarde basée sur une sauvegarde existante.

    Crée une nouvelle sauvegarde en réutilisant les paramètres d'une sauvegarde
    précédente (type, attachments, etc.). Utile pour re-exécuter manuellement
    une sauvegarde sans reconfigurer tous les paramètres.
    """
    # Récupérer le backup existant comme référence
    existing_backup = service.get_backup(backup_id)
    if not existing_backup:
        raise HTTPException(status_code=404, detail="Sauvegarde de référence non trouvée")

    # Créer une nouvelle sauvegarde basée sur les paramètres du backup existant
    new_backup_data = BackupCreate(
        backup_type=existing_backup.backup_type,
        include_attachments=existing_backup.include_attachments,
        notes=f"Re-exécution de {existing_backup.reference}"
    )

    try:
        new_backup = service.create_backup(
            new_backup_data,
            triggered_by=current_user.email or "api"
        )
        return new_backup
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la sauvegarde: {str(e)}")


# ============================================================================
# RESTAURATION
# ============================================================================

@router.post("/restore", response_model=RestoreResponse, status_code=201)
def restore_backup(
    data: RestoreRequest,
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Restaurer une sauvegarde."""
    try:
        return service.restore_backup(data, restored_by=current_user.email or "api")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard/stats", response_model=BackupDashboard)
def get_dashboard(
    service = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Dashboard backup."""
    return service.get_dashboard()
