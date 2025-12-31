"""
AZALS - Point d'entrée principal
ERP décisionnel critique - Sécurité by design
"""

from fastapi import FastAPI

app = FastAPI(
    title="AZALS",
    description="ERP décisionnel critique",
    version="0.1.0",
    docs_url=None,  # Désactivé en prod pour sécurité
    redoc_url=None  # Désactivé en prod pour sécurité
)


@app.get("/health")
async def health_check():
    """
    Endpoint de santé pour vérifier que l'API répond.
    Utilisé par Fly.io pour les health checks.
    """
    return {"status": "ok"}
