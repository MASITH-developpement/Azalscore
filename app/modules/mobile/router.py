"""
AZALS MODULE 18 - Mobile App Router
====================================
Endpoints API pour le backend mobile.
"""


from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User

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
    SessionCreate,
    SessionRefresh,
    SessionResponse,
    SyncBatch,
    SyncRequest,
    SyncResponse,
)
from .service import MobileService

router = APIRouter(prefix="/mobile", tags=["Mobile"])


def get_mobile_service(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
) -> MobileService:
    """Injection du service Mobile."""
    return MobileService(db, tenant_id)


def get_validated_user_id(
    current_user: User = Depends(get_current_user),
    x_user_id: str | None = Header(None)
) -> int:
    """
    SECURITY FIX: Valider user_id depuis header contre l'utilisateur authentifié.
    Empêche le spoofing d'identité via header X-User-ID.
    """
    # Si X-User-ID fourni, vérifier qu'il correspond à current_user
    if x_user_id:
        try:
            requested_user_id = int(x_user_id)
            if requested_user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="User ID header ne correspond pas à l'utilisateur authentifié"
                )
        except ValueError:
            raise HTTPException(status_code=400, detail="User ID invalide")

    # Toujours retourner l'ID de l'utilisateur authentifié (source de vérité)
    return current_user.id


def require_mobile_admin(current_user: User) -> None:
    """Vérifie que l'utilisateur a des droits admin pour les opérations mobile."""
    role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_value not in ["DIRIGEANT", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Droits admin requis pour cette opération."
        )


# ============================================================================
# DEVICES
# ============================================================================

@router.post("/devices/register", response_model=DeviceResponse)
def register_device(
    data: DeviceRegister,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Enregistrer un appareil mobile."""
    device = service.register_device(user_id, data)
    return device


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Lister les appareils de l'utilisateur."""
    return service.list_user_devices(user_id)


@router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    service: MobileService = Depends(get_mobile_service)
):
    """Récupérer un appareil."""
    device = service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    return device


@router.put("/devices/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    service: MobileService = Depends(get_mobile_service)
):
    """Mettre à jour un appareil."""
    device = service.update_device(device_id, data)
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    return device


@router.delete("/devices/{device_id}")
def deactivate_device(
    device_id: int,
    service: MobileService = Depends(get_mobile_service)
):
    """Désactiver un appareil."""
    success = service.deactivate_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    return {"message": "Appareil désactivé"}


# ============================================================================
# SESSIONS
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
def create_session(
    data: SessionCreate,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Créer une session mobile."""
    device = service.get_device_by_uuid(data.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable")

    session = service.create_session(user_id, device.id)
    return SessionResponse(
        session_token=session.session_token,
        refresh_token=session.refresh_token,
        expires_at=session.expires_at,
        device_id=session.device_id
    )


@router.post("/sessions/refresh", response_model=SessionResponse)
def refresh_session(
    data: SessionRefresh,
    service: MobileService = Depends(get_mobile_service)
):
    """Renouveler une session."""
    session = service.refresh_session(data.refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return SessionResponse(
        session_token=session.session_token,
        refresh_token=session.refresh_token,
        expires_at=session.expires_at,
        device_id=session.device_id
    )


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    service: MobileService = Depends(get_mobile_service)
):
    """Révoquer une session."""
    success = service.revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"message": "Session révoquée"}


@router.delete("/sessions")
def revoke_all_sessions(
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Révoquer toutes les sessions de l'utilisateur."""
    count = service.revoke_user_sessions(user_id)
    return {"message": f"{count} sessions révoquées"}


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@router.post("/notifications", response_model=NotificationResponse)
def send_notification(
    data: NotificationCreate,
    service: MobileService = Depends(get_mobile_service)
):
    """Envoyer une notification push."""
    notification = service.send_notification(data)
    return notification


@router.post("/notifications/bulk")
def send_bulk_notifications(
    data: NotificationBulk,
    service: MobileService = Depends(get_mobile_service)
):
    """Envoyer notifications en masse."""
    notifications = service.send_bulk_notifications(data)
    return {"sent": len(notifications)}


@router.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Récupérer les notifications de l'utilisateur."""
    return service.get_user_notifications(user_id, unread_only, skip, limit)


@router.get("/notifications/unread-count")
def get_unread_count(
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Compter les notifications non lues."""
    count = service.get_unread_count(user_id)
    return {"count": count}


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Marquer une notification comme lue."""
    success = service.mark_notification_read(notification_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return {"message": "Notification marquée comme lue"}


@router.put("/notifications/read-all")
def mark_all_read(
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Marquer toutes les notifications comme lues."""
    count = service.mark_all_notifications_read(user_id)
    return {"marked": count}


# ============================================================================
# SYNC
# ============================================================================

@router.post("/sync/pull", response_model=SyncResponse)
def sync_pull(
    data: SyncRequest,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Récupérer données à synchroniser (serveur -> client)."""
    items, version, has_more = service.get_sync_data(
        user_id, data.entity_type, data.since_version, data.limit
    )

    # Mettre à jour checkpoint
    service.update_sync_checkpoint(user_id, data.entity_type, version, len(items))

    return SyncResponse(
        entity_type=data.entity_type,
        items=items,
        version=version,
        has_more=has_more
    )


@router.post("/sync/push")
def sync_push(
    data: SyncBatch,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Envoyer données à synchroniser (client -> serveur)."""
    success, errors, conflicts = service.process_sync_batch(user_id, data)
    return {
        "success": success,
        "errors": errors,
        "conflicts": [c.model_dump() for c in conflicts] if conflicts else []
    }


# ============================================================================
# PREFERENCES
# ============================================================================

@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Récupérer préférences utilisateur."""
    return service.get_preferences(user_id)


@router.put("/preferences", response_model=PreferencesResponse)
def update_preferences(
    data: PreferencesUpdate,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Mettre à jour préférences."""
    return service.update_preferences(user_id, data)


# ============================================================================
# ACTIVITY
# ============================================================================

@router.post("/activity")
def log_activity(
    data: ActivityLog,
    request: Request,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Enregistrer une activité."""
    ip = request.client.host if request.client else None
    service.log_activity(user_id, data, ip=ip)
    return {"message": "Activité enregistrée"}


@router.post("/activity/batch")
def log_activity_batch(
    data: ActivityBatch,
    user_id: int = Depends(get_validated_user_id),
    service: MobileService = Depends(get_mobile_service)
):
    """Enregistrer batch d'activités."""
    count = service.log_activity_batch(user_id, data)
    return {"logged": count}


# ============================================================================
# CONFIG
# ============================================================================

@router.get("/config", response_model=AppConfigResponse)
def get_config(
    service: MobileService = Depends(get_mobile_service)
):
    """Récupérer configuration app."""
    config = service.get_app_config()
    if not config:
        return AppConfigResponse(
            min_version="1.0.0",
            current_version="1.0.0",
            force_update=False,
            update_message=None,
            maintenance_mode=False,
            maintenance_message=None,
            features_enabled={},
            sync_interval_minutes=15,
            session_timeout_hours=24,
            branding=None
        )

    return AppConfigResponse(
        min_version=config.min_ios_version or "1.0.0",
        current_version=config.current_version or "1.0.0",
        force_update=config.force_update,
        update_message=config.update_message,
        maintenance_mode=config.maintenance_mode,
        maintenance_message=config.maintenance_message,
        features_enabled=config.features_enabled or {},
        sync_interval_minutes=config.sync_interval_minutes,
        session_timeout_hours=config.session_timeout_hours,
        branding=config.branding
    )


@router.get("/config/check-version")
def check_version(
    platform: str,
    version: str,
    service: MobileService = Depends(get_mobile_service)
):
    """Vérifier si mise à jour requise."""
    return service.check_app_version(platform, version)


# ============================================================================
# CRASH REPORTS
# ============================================================================

@router.post("/crashes")
def report_crash(
    data: CrashReport,
    user_id: int = Depends(get_validated_user_id),
    device_id: int | None = None,
    service: MobileService = Depends(get_mobile_service)
):
    """Rapporter un crash."""
    # SÉCURITÉ: user_id vient de l'utilisateur authentifié
    crash = service.report_crash(user_id, device_id, data)
    return {"crash_id": crash.crash_id}


@router.get("/crashes")
def list_crashes(
    app_version: str | None = None,
    error_type: str | None = None,
    resolved: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: MobileService = Depends(get_mobile_service)
):
    """Lister les crashes."""
    # SÉCURITÉ: Seuls les admins peuvent voir les crash reports
    require_mobile_admin(current_user)
    return service.list_crashes(app_version, error_type, resolved, skip, limit)


# ============================================================================
# STATS
# ============================================================================

@router.get("/stats", response_model=MobileStats)
def get_mobile_stats(
    current_user: User = Depends(get_current_user),
    service: MobileService = Depends(get_mobile_service)
):
    """Statistiques mobile."""
    # SÉCURITÉ: Seuls les admins peuvent voir les statistiques
    require_mobile_admin(current_user)
    stats = service.get_mobile_stats()
    return MobileStats(**stats)
