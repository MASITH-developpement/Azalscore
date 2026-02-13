"""
AZALS API - Audit UI Events
============================

Endpoint pour enregistrer les événements UI du frontend.
Route: /v1/audit/ui-events

Ces données alimentent le module BI pour:
- Analyse comportement utilisateurs
- Optimisation UX décisionnel
- Tracking adoption modules
- Audit trail complet
"""

import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.models import User, UIEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])


class UIEventSchema(BaseModel):
    """Schema pour un événement UI."""
    event_type: str
    component: str | None = None
    action: str | None = None
    target: str | None = None
    metadata: dict | None = None
    timestamp: str | None = None


class UIEventsRequest(BaseModel):
    """Schema pour batch d'événements UI."""
    events: list[UIEventSchema]


def _store_ui_events_batch(
    events: list[UIEventSchema],
    tenant_id: str,
    user_id: uuid.UUID,
    db: Session
) -> dict:
    """
    Store batch UI events for decisional analytics.

    Args:
        events: Liste des événements UI à stocker
        tenant_id: ID du tenant
        user_id: ID de l'utilisateur
        db: Session SQLAlchemy

    Returns:
        Résumé du stockage
    """
    stored_count = 0
    errors = []

    for event in events:
        try:
            # Parser le timestamp si fourni
            if event.timestamp:
                try:
                    event_timestamp = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                except ValueError:
                    event_timestamp = datetime.utcnow()
            else:
                event_timestamp = datetime.utcnow()

            # Sérialiser metadata en JSON
            event_data_json = json.dumps(event.metadata) if event.metadata else None

            # Créer l'enregistrement
            db_event = UIEvent(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event.event_type,
                component=event.component,
                action=event.action,
                target=event.target,
                event_data=event_data_json,
                timestamp=event_timestamp
            )
            db.add(db_event)
            stored_count += 1

        except Exception as e:
            errors.append(str(e))
            logger.warning(
                "ui_event_storage_error",
                extra={
                    "event_type": event.event_type,
                    "error": str(e)[:200],
                    "tenant_id": tenant_id
                }
            )

    # Commit en batch pour performance
    try:
        db.commit()
        logger.info(
            "ui_events_stored",
            extra={
                "count": stored_count,
                "tenant_id": tenant_id,
                "user_id": str(user_id)
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "ui_events_commit_failed",
            extra={
                "error": str(e)[:200],
                "tenant_id": tenant_id,
                "attempted_count": stored_count
            }
        )
        return {
            "success": False,
            "stored": 0,
            "errors": [str(e)]
        }

    return {
        "success": True,
        "stored": stored_count,
        "errors": errors if errors else None,
        "analytics_ready": True  # Données prêtes pour module BI
    }


@router.post("/ui-events")
async def record_ui_events(
    data: UIEventsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre événements UI pour analytics décisionnel.

    Ces données alimentent le module BI pour:
    - Analyse comportement utilisateurs
    - Optimisation UX décisionnel
    - Tracking adoption modules

    Les événements sont stockés de manière asynchrone pour
    ne pas impacter la performance du frontend.

    Returns:
        Confirmation de réception avec nombre d'événements
    """
    event_count = len(data.events)

    if event_count == 0:
        return {
            "success": True,
            "message": "No events to process",
            "processed": 0
        }

    # Limite de sécurité : max 100 events par batch
    if event_count > 100:
        return {
            "success": False,
            "message": "Batch size exceeds limit (max 100 events)",
            "processed": 0
        }

    # Stockage en arrière-plan pour ne pas bloquer le frontend
    background_tasks.add_task(
        _store_ui_events_batch,
        data.events,
        current_user.tenant_id,
        current_user.id,
        db
    )

    return {
        "success": True,
        "message": f"Queued {event_count} UI events for analytics",
        "processed": event_count,
        "bi_integration": "enabled"
    }


@router.get("/ui-events/stats")
async def get_ui_events_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Statistiques des événements UI pour le tenant.

    Endpoint utile pour le module BI et dashboards décisionnels.
    """
    from sqlalchemy import func, text

    tenant_id = current_user.tenant_id

    # Total events
    total = db.query(func.count(UIEvent.id)).filter(
        UIEvent.tenant_id == tenant_id
    ).scalar() or 0

    # Events par type (top 10)
    events_by_type = db.execute(text("""
        SELECT event_type, COUNT(*) as count
        FROM ui_events
        WHERE tenant_id = :tenant_id
        GROUP BY event_type
        ORDER BY count DESC
        LIMIT 10
    """), {"tenant_id": tenant_id}).fetchall()

    # Events dernières 24h
    from datetime import timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    last_24h = db.query(func.count(UIEvent.id)).filter(
        UIEvent.tenant_id == tenant_id,
        UIEvent.timestamp >= yesterday
    ).scalar() or 0

    return {
        "total_events": total,
        "last_24h": last_24h,
        "by_type": [{"type": row[0], "count": row[1]} for row in events_by_type],
        "analytics_status": "operational"
    }
