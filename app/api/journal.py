"""
AZALS - Endpoints Journal APPEND-ONLY
API pour écriture et lecture du journal d'audit
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User
from app.services.journal import JournalService


router = APIRouter(prefix="/journal", tags=["journal"])


class JournalWriteRequest(BaseModel):
    """Requête d'écriture dans le journal"""
    action: str = Field(..., min_length=1, max_length=255)
    details: Optional[str] = Field(None, max_length=10000)


class JournalEntryResponse(BaseModel):
    """Réponse représentant une entrée de journal"""
    id: int
    tenant_id: str
    user_id: int
    action: str
    details: Optional[str]
    created_at: str
    
    model_config = {"from_attributes": True}


@router.post("/write", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def write_journal_entry(
    request: JournalWriteRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Écrit une entrée dans le journal APPEND-ONLY.
    Requiert JWT valide + X-Tenant-ID cohérent.
    
    Protections:
    - Écriture uniquement (INSERT)
    - UPDATE et DELETE impossibles (triggers DB)
    - Horodatage automatique
    """
    entry = JournalService.write(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action=request.action,
        details=request.details
    )
    
    return JournalEntryResponse(
        id=entry.id,
        tenant_id=entry.tenant_id,
        user_id=entry.user_id,
        action=entry.action,
        details=entry.details,
        created_at=entry.created_at.isoformat()
    )


@router.get("", response_model=list[JournalEntryResponse])
async def read_journal_entries(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Lit les entrées du journal pour le tenant de l'utilisateur.
    Filtrage strict par tenant_id.
    Pagination via limit/offset.
    """
    entries = JournalService.read_tenant_entries(
        db=db,
        tenant_id=tenant_id,
        limit=min(limit, 1000),
        offset=offset
    )
    
    return [
        JournalEntryResponse(
            id=entry.id,
            tenant_id=entry.tenant_id,
            user_id=entry.user_id,
            action=entry.action,
            details=entry.details,
            created_at=entry.created_at.isoformat()
        )
        for entry in entries
    ]
