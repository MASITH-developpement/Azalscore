"""
AZALS - Endpoint temporaire pour migration manuelle
À supprimer après migration réussie
SÉCURISÉ: Authentification ADMIN requise
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.core.database import engine
from app.core.dependencies import get_current_user
from app.core.models import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/migrate-treasury")
def apply_treasury_migration(current_user: User = Depends(get_current_user)):
    """
    TEMPORAIRE: Applique la migration 005 directement.
    SÉCURISÉ: Requiert authentification DIRIGEANT.
    """
    # SECURITY FIX: Vérification du rôle DIRIGEANT
    if current_user.role != UserRole.DIRIGEANT:
        raise HTTPException(status_code=403, detail="Accès réservé aux DIRIGEANTS")
    try:
        with engine.connect() as conn:
            # Vérifier si colonnes existent déjà
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'treasury_forecasts'
            """))
            existing_columns = {row[0] for row in result.fetchall()}

            changes = []

            # Ajouter user_id si nécessaire
            if 'user_id' not in existing_columns:
                conn.execute(text("ALTER TABLE treasury_forecasts ADD COLUMN user_id INTEGER"))
                changes.append("user_id ajouté")
            else:
                changes.append("user_id déjà présent")

            # Ajouter red_triggered si nécessaire
            if 'red_triggered' not in existing_columns:
                conn.execute(text("ALTER TABLE treasury_forecasts ADD COLUMN red_triggered INTEGER DEFAULT 0"))
                changes.append("red_triggered ajouté")
            else:
                changes.append("red_triggered déjà présent")

            # Créer index
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_treasury_red
                ON treasury_forecasts(tenant_id, red_triggered)
            """))
            changes.append("index créé")

            conn.commit()

            return {
                "status": "success",
                "changes": changes,
                "message": "Migration 005 appliquée avec succès"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
