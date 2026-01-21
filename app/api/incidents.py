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

# Dossier pour stocker les captures d'écran
SCREENSHOT_DIR = os.environ.get("GUARDIAN_SCREENSHOT_DIR", "/tmp/guardian_screenshots")

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
                os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                screenshot_filename = f"{tenant_id}_{uuid_module.uuid4()}.jpg"
                screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_filename)

                if "," in data.screenshot_data:
                    _, base64_data = data.screenshot_data.split(",", 1)
                else:
                    base64_data = data.screenshot_data

                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(base64_data))

                has_screenshot = True
                logger.info(f"[GUARDIAN] Screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logger.warning(f"[GUARDIAN] Screenshot save failed: {screenshot_error}")
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
            frontend_timestamp=data.timestamp,
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.info(
            f"[GUARDIAN] Incident created: {incident.incident_uid}",
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
            f"[GUARDIAN] Incident creation failed: {e}",
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

    if not os.path.exists(incident.screenshot_path):
        raise HTTPException(status_code=404, detail="Fichier de capture non trouvé")

    return FileResponse(
        incident.screenshot_path,
        media_type="image/jpeg",
        filename=f"incident_{incident_id}.jpg"
    )
