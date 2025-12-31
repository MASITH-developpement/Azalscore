"""
AZALS - Point d'entrée principal
ERP décisionnel critique - Sécurité by design
"""

from fastapi import FastAPI
from app.core.database import check_database_connection

app = FastAPI(
    title="AZALS",
    description="ERP décisionnel critique",
    version="0.1.0",
    docs_url=None,
    redoc_url=None
)


@app.get("/health")
async def health_check():
    """
    Endpoint de santé.
    Vérifie que l'API et la base de données fonctionnent.
    """
    db_ok = check_database_connection()
    
    return {
        "status": "ok" if db_ok else "degraded",
        "api": True,
        "database": db_ok
    }
