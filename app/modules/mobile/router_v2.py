"""
AZALS - Module Mobile - Router v2 - CORE SaaS
==============================================
API backend pour applications mobiles iOS/Android.
"""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext

from .service import MobileService
from .schemas import (
    ActivityBatch,
    ActivityLog,
    AppConfigResponse,
    CrashReport,
    DeviceRegister,
    DeviceResponse,
    DeviceUpdate,
    MobileStats,
    NotificationBulk,
    NotificationCreate,
    NotificationResponse,
    PreferencesResponse,
    PreferencesUpdate,
    SessionResponse,
    SyncBatch,
    SyncResponse,
)

router = APIRouter(prefix="/v2/mobile", tags=["Mobile v2 - CORE SaaS"])


def get_mobile_service(db: Session, tenant_id: str, user_id: str) -> MobileService:
    """Factory pour créer le service Mobile avec contexte SaaS."""
    return MobileService(db, tenant_id, user_id)


# ============================================================================
# DEVICES - Gestion Appareils
# ============================================================================

@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(
    data: DeviceRegister,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Enregistrer un nouvel appareil mobile."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    device = service.register_device(user_id, data)
    return DeviceResponse.from_orm(device)


@router.get("/devices", response_model=list[DeviceResponse])
async def list_user_devices(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les appareils de l'utilisateur connecté."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    devices = service.list_user_devices(user_id)
    return [DeviceResponse.from_orm(d) for d in devices]


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer un appareil par ID."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    device = service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_orm(device)


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour un appareil."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    device = service.update_device(device_id, data)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_orm(device)


@router.delete("/devices/{device_id}")
async def deactivate_device(
    device_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Désactiver un appareil."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    success = service.deactivate_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deactivated successfully"}


# ============================================================================
# SESSIONS - Gestion Sessions Mobiles
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    device_uuid: str = Query(..., description="UUID de l'appareil"),
    ip_address: str | None = Query(None, description="Adresse IP"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Créer une session mobile."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    session = service.create_session(user_id, device_uuid, ip_address)
    if not session:
        raise HTTPException(status_code=400, detail="Failed to create session")
    return SessionResponse.from_orm(session)


@router.post("/sessions/refresh", response_model=SessionResponse)
async def refresh_session(
    refresh_token: str = Query(..., description="Refresh token"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Rafraîchir une session mobile."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    session = service.refresh_session(refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return SessionResponse.from_orm(session)


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Révoquer une session mobile."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    success = service.revoke_session(session_id, "Manual logout")
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session revoked successfully"}


@router.delete("/sessions")
async def revoke_all_sessions(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Révoquer toutes les sessions de l'utilisateur."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    count = service.revoke_user_sessions(user_id)
    return {"message": f"{count} session(s) revoked"}


# ============================================================================
# NOTIFICATIONS PUSH
# ============================================================================

@router.post("/notifications", response_model=NotificationResponse)
async def send_notification(
    data: NotificationCreate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Envoyer une notification push."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    notification = service.send_notification(data)
    return NotificationResponse.from_orm(notification)


@router.post("/notifications/bulk")
async def send_bulk_notifications(
    data: NotificationBulk,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Envoyer des notifications en masse."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    notifications = service.send_bulk_notifications(data)
    return {
        "message": f"{len(notifications)} notifications sent",
        "count": len(notifications)
    }


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer les notifications de l'utilisateur."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    notifications = service.get_user_notifications(user_id, skip, limit)
    return [NotificationResponse.from_orm(n) for n in notifications]


@router.get("/notifications/unread-count")
async def get_unread_count(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Nombre de notifications non lues."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    count = service.get_unread_count(user_id)
    return {"unread_count": count}


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Marquer une notification comme lue."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    success = service.mark_notification_read(notification_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Marquer toutes les notifications comme lues."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    count = service.mark_all_notifications_read(user_id)
    return {"message": f"{count} notification(s) marked as read"}


# ============================================================================
# SYNCHRONISATION OFFLINE
# ============================================================================

@router.post("/sync/pull", response_model=SyncResponse)
async def sync_pull(
    entity_type: str = Query(..., description="Type d'entité à synchroniser"),
    last_sync: str | None = Query(None, description="Timestamp dernière sync"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer les données modifiées depuis la dernière sync (pull)."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    data = service.get_sync_data(entity_type, user_id, last_sync)
    return SyncResponse(
        entity_type=entity_type,
        records=data.get("records", []),
        checkpoint=data.get("checkpoint"),
        has_more=data.get("has_more", False)
    )


@router.post("/sync/push")
async def sync_push(
    data: SyncBatch,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Envoyer les modifications locales au serveur (push)."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    result = service.process_sync_batch(user_id, data)
    return result


# ============================================================================
# PRÉFÉRENCES UTILISATEUR
# ============================================================================

@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer les préférences de l'utilisateur."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    prefs = service.get_preferences(user_id)
    return PreferencesResponse.from_orm(prefs)


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    data: PreferencesUpdate,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Mettre à jour les préférences de l'utilisateur."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    prefs = service.update_preferences(user_id, data)
    return PreferencesResponse.from_orm(prefs)


# ============================================================================
# ACTIVITY TRACKING
# ============================================================================

@router.post("/activity")
async def log_activity(
    data: ActivityLog,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Enregistrer une activité utilisateur."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    activity = service.log_activity(user_id, data)
    return {"message": "Activity logged", "activity_id": activity.id}


@router.post("/activity/batch")
async def log_activity_batch(
    data: ActivityBatch,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Enregistrer plusieurs activités en batch."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    count = service.log_activity_batch(user_id, data)
    return {"message": f"{count} activities logged"}


# ============================================================================
# CONFIGURATION APP
# ============================================================================

@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Récupérer la configuration de l'application mobile."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    config = service.get_app_config()
    if not config:
        # Retourner config par défaut
        return AppConfigResponse(
            min_version_ios="1.0.0",
            min_version_android="1.0.0",
            latest_version_ios="1.0.0",
            latest_version_android="1.0.0",
            force_update=False,
            maintenance_mode=False,
            api_base_url="https://api.azalscore.com",
            features_enabled={"offline_mode": True, "push_notifications": True}
        )
    return AppConfigResponse.from_orm(config)


@router.get("/config/check-version")
async def check_app_version(
    platform: str = Query(..., description="Platform (ios/android)"),
    version: str = Query(..., description="Version actuelle de l'app"),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Vérifier si la version de l'app est à jour."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    result = service.check_app_version(platform, version)
    return result


# ============================================================================
# CRASH REPORTS
# ============================================================================

@router.post("/crashes")
async def report_crash(
    data: CrashReport,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Enregistrer un rapport de crash."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    user_id = int(context.user_id) if context.user_id else None

    crash = service.report_crash(user_id, data)
    return {"message": "Crash reported", "crash_id": crash.id}


@router.get("/crashes")
async def list_crashes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Lister les rapports de crash (ADMIN)."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    crashes = service.list_crashes(skip, limit)
    return {"crashes": crashes, "total": len(crashes)}


# ============================================================================
# STATISTIQUES
# ============================================================================

@router.get("/stats", response_model=MobileStats)
async def get_mobile_stats(
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """Statistiques d'usage mobile (ADMIN)."""
    service = get_mobile_service(db, context.tenant_id, context.user_id)
    stats = service.get_stats()
    return MobileStats(**stats)
