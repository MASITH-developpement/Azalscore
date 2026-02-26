"""
AZALSCORE API - Incidents Endpoint
===================================

Endpoint direct /v1/incidents pour le frontend Guardian.
Délègue au module guardian mais avec un chemin simplifié.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User
from app.modules.guardian.schemas import IncidentCreate, IncidentResponse
from app.modules.guardian.models import Incident
from app.core.logging_config import get_logger

import base64
import os
import uuid as uuid_module

router = APIRouter(prefix="/incidents", tags=["Incidents"])

# SÉCURITÉ: Dossier pour stocker les captures d'écran
# IMPORTANT: Ne PAS utiliser /tmp en production (accessible par tous les utilisateurs)
# Utiliser un dossier dédié avec permissions restrictives
_default_screenshot_dir = os.path.join(
    os.environ.get("AZALS_DATA_DIR", "/var/lib/azalscore"),
    "guardian_screenshots"
)
SCREENSHOT_DIR = os.environ.get("GUARDIAN_SCREENSHOT_DIR", _default_screenshot_dir)

# SÉCURITÉ: Limite de taille des screenshots (5MB max)
MAX_SCREENSHOT_SIZE_BYTES = 5 * 1024 * 1024

logger = get_logger(__name__)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Crée un incident depuis le frontend.

    GUARDIAN: Cet endpoint ne doit JAMAIS retourner 500.
    Toute erreur est gérée silencieusement pour ne pas bloquer le frontend.
    """
    try:
        # Sauvegarder la capture d'écran si présente
        screenshot_path = None
        has_screenshot = False

        if data.screenshot_data:
            try:
                # SÉCURITÉ: Créer le dossier avec permissions restrictives (700)
                os.makedirs(SCREENSHOT_DIR, mode=0o700, exist_ok=True)

                # SÉCURITÉ: Valider le tenant_id pour éviter path traversal
                import re
                if not re.match(r'^[a-zA-Z0-9_-]+$', tenant_id):
                    raise ValueError("Invalid tenant_id format")

                screenshot_filename = f"{tenant_id}_{uuid_module.uuid4()}.jpg"
                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)

                # SÉCURITÉ: Vérifier que le path résolu est dans SCREENSHOT_DIR
                resolved_path = os.path.realpath(screenshot_path)
                resolved_dir = os.path.realpath(SCREENSHOT_DIR)
                if not resolved_path.startswith(resolved_dir + os.sep):
                    raise ValueError("Path traversal detected")

                if "," in data.screenshot_data:
                    _, base64_data = data.screenshot_data.split(",", 1)
                else:
                    base64_data = data.screenshot_data

                # SÉCURITÉ: Valider la taille avant décodage
                # Base64 encode ~33% plus grand que les données originales
                estimated_size = len(base64_data) * 3 // 4
                if estimated_size > MAX_SCREENSHOT_SIZE_BYTES:
                    logger.warning(
                        "[GUARDIAN] Screenshot too large: %s bytes (max %s)",
                        estimated_size, MAX_SCREENSHOT_SIZE_BYTES
                    )
                    raise ValueError(f"Screenshot too large (max {MAX_SCREENSHOT_SIZE_BYTES // 1024 // 1024}MB)")

                decoded_data = base64.b64decode(base64_data)

                # SÉCURITÉ: Double vérification de la taille après décodage
                if len(decoded_data) > MAX_SCREENSHOT_SIZE_BYTES:
                    raise ValueError("Screenshot exceeds maximum size")

                with open(screenshot_path, "wb") as f:
                    f.write(decoded_data)

                # SÉCURITÉ: Restreindre les permissions du fichier (600)
                os.chmod(screenshot_path, 0o600)

                has_screenshot = True
                logger.info("[GUARDIAN] Screenshot saved: %s", screenshot_path)
            except Exception as screenshot_error:
                logger.warning("[GUARDIAN] Screenshot save failed: %s", screenshot_error)
                screenshot_path = None
                has_screenshot = False

        # Créer l'incident
        incident = Incident(
            tenant_id=tenant_id,
            type=data.type,
            severity=data.severity,
            user_id=current_user.id,
            user_role=current_user.role.value if hasattr(current_user, 'role') else None,
            page=data.page,
            route=data.route,
            endpoint=data.endpoint,
            method=data.method,
            http_status=data.http_status,
            message=data.message,
            details=data.details,
            stack_trace=data.stack_trace,
            screenshot_path=screenshot_path,
            has_screenshot=has_screenshot,
            frontend_timestamp=data.frontend_timestamp,
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.info(
            "[GUARDIAN] Incident created: %s", incident.incident_uid,
            extra={
                "tenant_id": tenant_id,
                "incident_type": data.type,
                "severity": data.severity,
                "page": data.page,
            }
        )

        return IncidentResponse(
            id=str(incident.id),
            incident_uid=str(incident.incident_uid),
            tenant_id=tenant_id,
            type=incident.type,
            severity=incident.severity,
            page=incident.page,
            route=incident.route,
            endpoint=incident.endpoint,
            method=incident.method,
            http_status=incident.http_status,
            message=incident.message,
            details=incident.details,
            frontend_timestamp=incident.frontend_timestamp,
            created_at=incident.created_at,
            has_screenshot=has_screenshot,
            is_processed=incident.is_processed if hasattr(incident, 'is_processed') else False,
            is_resolved=incident.is_resolved if hasattr(incident, 'is_resolved') else False,
        )

    except Exception as e:
        # GUARDIAN: JAMAIS de 500 sur cet endpoint
        logger.error(
            "[GUARDIAN] Incident creation failed: %s", e,
            extra={"tenant_id": tenant_id, "error_type": type(e).__name__},
            exc_info=True
        )

        fallback_id = str(uuid_module.uuid4())
        return IncidentResponse(
            id=fallback_id,
            incident_uid=fallback_id,
            tenant_id=tenant_id,
            type=data.type,
            severity=data.severity,
            page=data.page,
            route=data.route,
            endpoint=data.endpoint,
            method=data.method,
            http_status=data.http_status,
            message=data.message,
            details=data.details,
            frontend_timestamp=data.frontend_timestamp,
            created_at=datetime.utcnow(),
            has_screenshot=False,
            is_processed=False,
            is_resolved=False,
        )


@router.get("")
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    incident_type: Optional[str] = Query(None, alias="type"),
    is_resolved: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Liste les incidents avec filtres et pagination."""
    query = db.query(Incident).filter(Incident.tenant_id == tenant_id)

    if severity:
        query = query.filter(Incident.severity == severity)
    if incident_type:
        query = query.filter(Incident.type == incident_type)
    if is_resolved is not None:
        query = query.filter(Incident.is_resolved == is_resolved)
    if date_from:
        query = query.filter(Incident.created_at >= date_from)
    if date_to:
        query = query.filter(Incident.created_at <= date_to)

    total = query.count()
    items = query.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": str(i.incident_uid),
                "type": i.type,
                "severity": i.severity,
                "page": i.page,
                "route": i.route,
                "endpoint": i.endpoint,
                "method": i.method,
                "http_status": i.http_status,
                "message": i.message,
                "details": i.details,
                "has_screenshot": i.has_screenshot,
                "is_resolved": i.is_resolved,
                "created_at": i.created_at.isoformat(),
                "frontend_timestamp": i.frontend_timestamp.isoformat(),
            }
            for i in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{incident_id}/screenshot")
async def get_incident_screenshot(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Récupère la capture d'écran d'un incident."""
    from fastapi.responses import FileResponse

    incident = db.query(Incident).filter(
        Incident.incident_uid == incident_id,
        Incident.tenant_id == tenant_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    if not incident.has_screenshot or not incident.screenshot_path:
        raise HTTPException(status_code=404, detail="Pas de capture d'écran pour cet incident")

    # SÉCURITÉ: Valider que le chemin est bien dans SCREENSHOT_DIR
    # Prévient les attaques de path traversal si screenshot_path a été manipulé
    try:
        resolved_path = os.path.realpath(incident.screenshot_path)
        resolved_dir = os.path.realpath(SCREENSHOT_DIR)
        if not resolved_path.startswith(resolved_dir + os.sep):
            logger.warning(
                "[GUARDIAN] Path traversal attempt detected",
                extra={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                    "screenshot_path": incident.screenshot_path[:100]
                }
            )
            raise HTTPException(status_code=404, detail="Fichier de capture non trouvé")
    except Exception as e:
        logger.warning("[GUARDIAN] Path validation failed: %s", e)
        raise HTTPException(status_code=404, detail="Fichier de capture non trouvé")

    if not os.path.exists(incident.screenshot_path):
        raise HTTPException(status_code=404, detail="Fichier de capture non trouvé")

    return FileResponse(
        incident.screenshot_path,
        media_type="image/jpeg",
        filename=f"incident_{incident_id}.jpg"
    )
