"""
AZALS MODULE BACKUP - Router API v2 (CORE SaaS)
================================================

✅ MIGRÉ CORE SaaS Phase 2.2
- Utilise get_saas_context() au lieu de get_current_user()
- Isolation tenant automatique via context.tenant_id
- Audit trail automatique via context.user_id

API REST pour les sauvegardes chiffrées AES-256.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

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
from .service import BackupService, get_backup_service

router = APIRouter(prefix="/v2/backup", tags=["Backups v2 - CORE SaaS"])


# ============================================================================
# SERVICE DEPENDENCY v2
# ============================================================================

def get_service_v2(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
) -> BackupService:
    """✅ MIGRÉ CORE SaaS: Utilise context.tenant_id et context.user_id"""
    return get_backup_service(db, context.tenant_id, context.user_id)


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.post("/config", response_model=BackupConfigResponse, status_code=201)
async def create_config(
    data: BackupConfigCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer configuration backup avec génération de clé AES-256"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    existing = service.get_config()
    if existing:
        raise HTTPException(status_code=409, detail="Configuration déjà existante")
    return service.create_config(data)


@router.get("/config", response_model=BackupConfigResponse)
async def get_config(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer configuration backup"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    config = service.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


@router.patch("/config", response_model=BackupConfigResponse)
async def update_config(
    data: BackupConfigUpdate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Mettre à jour configuration backup"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    config = service.update_config(data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config


# ============================================================================
# BACKUPS
# ============================================================================

@router.post("", response_model=BackupResponse, status_code=201)
async def create_backup(
    data: BackupCreate,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Créer une sauvegarde manuelle"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    try:
        return service.create_backup(data, triggered_by=context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[BackupResponse])
async def list_backups(
    status: BackupStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Lister les sauvegardes"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    items, _ = service.list_backups(status, skip, limit)
    return items


@router.get("/{backup_id}", response_model=BackupDetail)
async def get_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Récupérer une sauvegarde"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    backup = service.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde non trouvée")
    return backup


@router.delete("/{backup_id}", status_code=204)
async def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Supprimer une sauvegarde"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    backup = service.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Sauvegarde non trouvée")
    # Marquer comme supprimée
    backup.status = BackupStatus.DELETED
    service.db.commit()
    return None


@router.post("/{backup_id}/run", response_model=BackupResponse, status_code=201)
async def run_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """
    ✅ MIGRÉ CORE SaaS: Lancer une nouvelle sauvegarde basée sur une sauvegarde existante.

    Crée une nouvelle sauvegarde en réutilisant les paramètres d'une sauvegarde
    précédente (type, attachments, etc.). Utile pour re-exécuter manuellement
    une sauvegarde sans reconfigurer tous les paramètres.
    """
    service = get_backup_service(db, context.tenant_id, context.user_id)
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
            triggered_by=context.user_id
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
async def restore_backup(
    data: RestoreRequest,
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Restaurer une sauvegarde"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    try:
        return service.restore_backup(data, restored_by=context.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard/stats", response_model=BackupDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    context: SaaSContext = Depends(get_saas_context)
):
    """✅ MIGRÉ CORE SaaS: Dashboard backup"""
    service = get_backup_service(db, context.tenant_id, context.user_id)
    return service.get_dashboard()
