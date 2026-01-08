"""
AZALS API - Audit UI Events
============================

Endpoint simple pour enregistrer les événements UI du frontend.
Route: /v1/audit/ui-events
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.models import User

router = APIRouter(prefix="/audit", tags=["Audit"])


class UIEventSchema(BaseModel):
    """Schema pour un événement UI."""
    event_type: str
    component: Optional[str] = None
    action: Optional[str] = None
    target: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: Optional[str] = None


class UIEventsRequest(BaseModel):
    """Schema pour batch d'événements UI."""
    events: List[UIEventSchema]


@router.post("/ui-events")
async def record_ui_events(
    data: UIEventsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre les événements UI du frontend.
    Les événements sont traités en arrière-plan pour ne pas bloquer le frontend.
    """
    # Pour l'instant, on accepte simplement les événements sans les stocker
    # TODO: Implémenter le stockage des événements UI dans le module audit
    event_count = len(data.events)

    return {
        "success": True,
        "message": f"Received {event_count} UI events",
        "processed": event_count
    }
