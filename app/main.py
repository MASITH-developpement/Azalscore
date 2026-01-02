"""
AZALS - Point d'entrée principal
ERP décisionnel critique - Sécurité by design - Multi-tenant strict
"""

import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
from app.core.database import check_database_connection, engine, Base
from app.core.middleware import TenantMiddleware
from app.services.scheduler import scheduler_service
from app.api.items import router as items_router
from app.api.auth import router as auth_router
from app.api.protected import router as protected_router
from app.api.journal import router as journal_router
from app.api.decision import router as decision_router
from app.api.red_workflow import router as red_workflow_router
from app.api.treasury import router as treasury_router
from app.api.accounting import router as accounting_router
from app.api.admin_migration import router as admin_migration_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: création des tables au démarrage avec retry"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print(f"✅ Base de données connectée (tentative {attempt + 1})")
            break
        except Exception as e:
            print(f"⏳ Connexion DB tentative {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                print("⚠️ DB non disponible, l'app démarre quand même")
    
    # Démarrer le scheduler
    scheduler_service.start()
    
    yield
    
    # Arrêter le scheduler à l'arrêt
    scheduler_service.shutdown()

app = FastAPI(
    title="AZALS",
    description="ERP décisionnel critique - Multi-tenant + Authentification JWT",
    version="0.3.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
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
app.include_router(tccounting_router)
app.include_router(areasury_router)
app.include_router(admin_migration_router)  # TEMPORAIRE pour migration

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
    
    @app.get("/treasury")
    async def serve_treasury():
        """Servir la page Trésorerie"""
        treasury_path = UI_DIR / "treasury.html"
        if treasury_path.exists():
            return FileResponse(treasury_path)
        return {"message": "Page Trésorerie non disponible"}
    
    @app.get("/favicon.ico")
    async def serve_favicon():
        """Servir le favicon"""
        favicon_path = UI_DIR / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return FileResponse(UI_DIR / "favicon.svg", status_code=404)
