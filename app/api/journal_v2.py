"""
AZALS - Endpoints Journal APPEND-ONLY (MIGRÉ CORE SaaS)
========================================================
API pour écriture et lecture du journal d'audit

✅ MIGRÉ vers CORE SaaS (Phase 2.2):
- Utilise get_saas_context() au lieu de get_current_user() + get_tenant_id()
- SaaSContext fournit tenant_id + user_id directement
- Audit automatique via CoreAuthMiddleware
- Code plus concis et sécurisé
"""


from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies_v2 import get_saas_context
from app.core.saas_context import SaaSContext
from app.services.journal import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])


class JournalWriteRequest(BaseModel):
    """Requête d'écriture dans le journal"""
    action: str = Field(..., min_length=1, max_length=255)
    details: str | None = Field(None, max_length=10000)


class JournalEntryResponse(BaseModel):
    """Réponse représentant une entrée de journal"""
    id: int
    tenant_id: str
    user_id: int
    action: str
    details: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/write", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def write_journal_entry(
    request: JournalWriteRequest,
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Écrit une entrée dans le journal APPEND-ONLY.
    Requiert JWT valide + X-Tenant-ID cohérent.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id et context.user_id
    - Audit automatique de l'action write_journal_entry via CORE

    Protections:
    - Écriture uniquement (INSERT)
    - UPDATE et DELETE impossibles (triggers DB)
    - Horodatage automatique
    """
    entry = JournalService.write(
        db=db,
        tenant_id=context.tenant_id,  # Depuis SaaSContext
        user_id=context.user_id,       # Depuis SaaSContext
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
    context: SaaSContext = Depends(get_saas_context),
    db: Session = Depends(get_db)
):
    """
    Lit les entrées du journal pour le tenant de l'utilisateur.
    Filtrage strict par tenant_id.
    Pagination via limit/offset.

    ✅ MIGRÉ CORE SaaS:
    - Utilise context.tenant_id pour filtrage
    - Plus besoin de passer current_user ET tenant_id séparément
    """
    entries = JournalService.read_tenant_entries(
        db=db,
        tenant_id=context.tenant_id,  # Depuis SaaSContext
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
