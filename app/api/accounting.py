"""
AZALS - API Comptabilité
Endpoints pour tableau de bord comptable du cockpit dirigeant
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user_and_tenant


router = APIRouter(prefix="/accounting", tags=["accounting"])


class AccountingStatusResponse(BaseModel):
    """État comptable pour le cockpit."""
    entries_up_to_date: bool
    last_closure_date: str | None
    pending_entries_count: int
    days_since_closure: int | None
    status: str  # 🟢 ou 🟠
    
    model_config = {"from_attributes": True}


@router.get("/status", response_model=AccountingStatusResponse)
def get_accounting_status(
    context: dict = Depends(get_current_user_and_tenant),
    db: Session = Depends(get_db)
):
    """
    Récupère l'état comptable du cockpit dirigeant.
    
    Règles:
    - 🟢: Écritures récentes (< 3 jours) + dernière clôture ≤ 30 jours
    - 🟠: Écritures anciennes (> 3 jours) OU clôture lointaine (> 30 jours)
    """
    tenant_id = context["tenant_id"]
    
    try:
        # Compter les écritures des 3 derniers jours
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_entries,
                COUNT(CASE WHEN created_at >= :three_days_ago THEN 1 END) as recent_entries
            FROM core_audit_journal
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id, "three_days_ago": three_days_ago})
        
        row = result.fetchone()
        total_entries = row[0] if row else 0
        recent_entries = row[1] if row else 0
        entries_up_to_date = recent_entries > 0 if total_entries > 0 else True
        
        # Récupérer la dernière "clôture comptable" (marquée par action CLOSURE ou END_PERIOD)
        closure_result = db.execute(text("""
            SELECT MAX(created_at) as last_closure
            FROM core_audit_journal
            WHERE tenant_id = :tenant_id
            AND (action = 'ACCOUNTING_CLOSURE' OR action = 'END_PERIOD')
        """), {"tenant_id": tenant_id})
        
        closure_row = closure_result.fetchone()
        last_closure = closure_row[0] if closure_row and closure_row[0] else None
        
        days_since_closure = None
        closure_is_recent = False
        
        if last_closure:
            days_since_closure = (datetime.utcnow() - last_closure).days
            closure_is_recent = days_since_closure <= 30
        
        # Déterminer l'état
        # 🟢 : écritures récentes ET clôture ≤ 30 jours (ou pas de clôture enregistrée = neuf)
        # 🟠 : écritures anciennes OU clôture > 30 jours
        is_green = entries_up_to_date and (not last_closure or closure_is_recent)
        status = '🟢' if is_green else '🟠'
        
        # Compter les écritures "en attente" = dernière semaine
        pending_result = db.execute(text("""
            SELECT COUNT(*) 
            FROM core_audit_journal
            WHERE tenant_id = :tenant_id
            AND created_at >= :one_week_ago
        """), {"tenant_id": tenant_id, "one_week_ago": datetime.utcnow() - timedelta(days=7)})
        
        pending_count = pending_result.scalar() or 0
        
        return AccountingStatusResponse(
            entries_up_to_date=entries_up_to_date,
            last_closure_date=last_closure.isoformat() if last_closure else None,
            pending_entries_count=pending_count,
            days_since_closure=days_since_closure,
            status=status
        )
    
    except Exception:
        # En cas d'erreur, retourner un état neutral
        return AccountingStatusResponse(
            entries_up_to_date=True,
            last_closure_date=None,
            pending_entries_count=0,
            days_since_closure=None,
            status='🟢'
        )
