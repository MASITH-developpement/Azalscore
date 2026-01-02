"""
AZALS - Point d'entrée principal
ERP décisionnel critique - Sécurité by design
"""

import logging
from fastapi import FastAPI, HTTPException
from app.core.config import get_settings
from app.core.database import check_database_connection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Conditionner les docs selon l'environnement
app = FastAPI(
    title="AZALS",
    description="ERP décisionnel critique",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

logger.info(f"Démarrage de l'application AZALS - Mode debug: {settings.debug}")


@app.get("/health")
async def health_check():
    """
    Endpoint de santé.
    Vérifie que l'API et la base de données fonctionnent.
    """
    try:
        db_ok = check_database_connection()
        
        status = "ok" if db_ok else "degraded"
        
        if not db_ok:
            logger.warning("Health check : Base de données non accessible")
        
        return {
            "status": status,
            "api": True,
            "database": db_ok
        }
    except Exception as e:
        logger.exception(f"Erreur critique dans health_check : {e}")
        raise HTTPException(
            status_code=503,
            detail="Service temporairement indisponible"
        )
