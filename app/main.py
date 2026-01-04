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
from app.api.tax import router as tax_router
from app.api.hr import router as hr_router
from app.api.legal import router as legal_router
from app.api.admin_migration import router as admin_migration_router

# Module T0 - IAM (Gestion Utilisateurs & Rôles)
from app.modules.iam.router import router as iam_router

# Module T1 - Configuration Automatique par Fonction
from app.modules.autoconfig.router import router as autoconfig_router

# Module T2 - Système de Déclencheurs & Diffusion
from app.modules.triggers.router import router as triggers_router

# Module T3 - Audit & Benchmark Évolutif
from app.modules.audit.router import router as audit_router

# Module T4 - Contrôle Qualité Central
from app.modules.qc.router import router as qc_router

# Module T5 - Packs Pays (Localisation)
from app.modules.country_packs.router import router as country_packs_router

# Module T6 - Diffusion d'Information Périodique
from app.modules.broadcast.router import router as broadcast_router

# Module T7 - Module Web Transverse
from app.modules.web.router import router as web_router

# Module T8 - Site Web Officiel AZALS
from app.modules.website.router import router as website_router

# Module T9 - Gestion des Tenants (Multi-Tenancy)
from app.modules.tenants.router import router as tenants_router

# Module M1 - Commercial (CRM & Ventes)
from app.modules.commercial.router import router as commercial_router

# Module M2 - Finance (Comptabilité & Trésorerie)
from app.modules.finance.router import router as finance_router

# Module M3 - RH (Ressources Humaines)
from app.modules.hr.router import router as hr_module_router

# Module M4 - Achats (Procurement)
from app.modules.procurement.router import router as procurement_router

# Module M5 - Stock (Inventaire + Logistique)
from app.modules.inventory.router import router as inventory_router

# Module M6 - Production (Manufacturing)
from app.modules.production.router import router as production_router

# Module M7 - Qualité (Quality Management)
from app.modules.quality.router import router as quality_router

# Module M8 - Maintenance (Asset Management / GMAO)
from app.modules.maintenance.router import router as maintenance_router

# Module M9 - Projets (Project Management)
from app.modules.projects.router import router as projects_router

# Module M10 - BI & Reporting (Business Intelligence)
from app.modules.bi.router import router as bi_router

# Module M11 - Compliance (Conformité Réglementaire)
from app.modules.compliance.router import router as compliance_router


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
app.include_router(accounting_router)
app.include_router(treasury_router)
app.include_router(tax_router)
app.include_router(hr_router)
app.include_router(legal_router)
app.include_router(admin_migration_router)  # TEMPORAIRE pour migration

# Module T0 - IAM (Gestion Utilisateurs & Rôles)
app.include_router(iam_router)

# Module T1 - Configuration Automatique par Fonction
app.include_router(autoconfig_router)

# Module T2 - Système de Déclencheurs & Diffusion
app.include_router(triggers_router)

# Module T3 - Audit & Benchmark Évolutif
app.include_router(audit_router)

# Module T4 - Contrôle Qualité Central
app.include_router(qc_router)

# Module T5 - Packs Pays (Localisation)
app.include_router(country_packs_router)

# Module T6 - Diffusion d'Information Périodique
app.include_router(broadcast_router)

# Module T7 - Module Web Transverse
app.include_router(web_router)

# Module T8 - Site Web Officiel AZALS
app.include_router(website_router)

# Module T9 - Gestion des Tenants (Multi-Tenancy)
app.include_router(tenants_router)

# Module M1 - Commercial (CRM & Ventes)
app.include_router(commercial_router)

# Module M2 - Finance (Comptabilité & Trésorerie)
app.include_router(finance_router)

# Module M3 - RH (Ressources Humaines)
app.include_router(hr_module_router)

# Module M4 - Achats (Procurement)
app.include_router(procurement_router)

# Module M5 - Stock (Inventaire + Logistique)
app.include_router(inventory_router)

# Module M6 - Production (Manufacturing)
app.include_router(production_router)

# Module M7 - Qualité (Quality Management)
app.include_router(quality_router)

# Module M8 - Maintenance (Asset Management / GMAO)
app.include_router(maintenance_router)

# Module M9 - Projets (Project Management)
app.include_router(projects_router)

# Module M10 - BI & Reporting (Business Intelligence)
app.include_router(bi_router)

# Module M11 - Compliance (Conformité Réglementaire)
app.include_router(compliance_router)

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
