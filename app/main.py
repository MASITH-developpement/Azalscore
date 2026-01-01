"""
AZALS - Point d'entrée principal
ERP décisionnel critique - Sécurité by design - Multi-tenant strict
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.database import check_database_connection, engine, Base
from app.core.middleware import TenantMiddleware
from app.api.items import router as items_router
from app.api.auth import router as auth_router
from app.api.protected import router as protected_router
from app.api.journal import router as journal_router
from app.api.decision import router as decision_router
from app.api.red_workflow import router as red_workflow_router
from app.api.treasury import router as treasury_router

# Création des tables (en production : utiliser Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AZALS",
    description="ERP décisionnel critique - Multi-tenant + Authentification JWT",
    version="0.3.0",
    docs_url=None,
    redoc_url=None
)

# Middleware multi-tenant : validation X-Tenant-ID pour TOUTES les requêtes
app.add_middleware(TenantMiddleware)

# Routes authentification (nécessitent X-Tenant-ID mais pas JWT)
app.include_router(auth_router)

# Routes protégées par JWT + tenant
app.include_router(protected_router)
app.include_router(journal_router)
app.include_router(decision_router)
app.include_router(red_workflow_router)
app.include_router(treasury_router)

# Routes protégées par tenant uniquement (pas JWT pour compatibilité)
app.include_router(items_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de santé.
    Vérifie que l'API et la base de données fonctionnent.
    Endpoint PUBLIC : pas de validation tenant.
    """
    db_ok = check_database_connection()
    
    return {
        "status": "ok" if db_ok else "degraded",
        "api": True,
        "database": db_ok
    }


# ==================== FRONTEND STATIQUE ====================

# Chemin vers le dossier UI
UI_DIR = Path(__file__).parent.parent / "ui"

# Servir les fichiers statiques (CSS, JS) depuis /ui
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")
    
    @app.get("/")
    async def serve_index():
        """Servir la page d'accueil"""
        index_path = UI_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Interface frontend non disponible"}
    
    @app.get("/dashboard")
    async def serve_dashboard():
        """Servir le dashboard"""
        dashboard_path = UI_DIR / "dashboard.html"
        if dashboard_path.exists():
            return FileResponse(dashboard_path)
        return {"message": "Dashboard non disponible"}
