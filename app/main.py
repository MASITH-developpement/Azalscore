"""
AZALS - Point d'entrée principal SÉCURISÉ ÉLITE
=================================================
ERP décisionnel critique - Sécurité by design - Multi-tenant strict
ÉLITE: Docs API désactivées en production, Observabilité complète
"""

import asyncio
from fastapi import FastAPI, APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from contextlib import asynccontextmanager
from app.core.database import check_database_connection, engine, Base
from app.core.middleware import TenantMiddleware
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User
from app.core.compression import CompressionMiddleware
from app.core.security_middleware import setup_cors
from app.core.metrics import MetricsMiddleware, router as metrics_router, init_metrics
from app.core.health import router as health_router
from app.core.logging_config import setup_logging, get_logger
from app.services.scheduler import scheduler_service
from app.core.config import get_settings
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
from app.api.partners import router as partners_router
from app.api.invoicing import router as invoicing_router

# Module T0 - IAM (Gestion Utilisateurs & Rôles)
from app.modules.iam.router import router as iam_router
from app.modules.iam.rbac_middleware import RBACMiddleware

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
from app.modules.country_packs.france.router import router as france_pack_router

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

# Module M12 - E-Commerce
from app.modules.ecommerce.router import router as ecommerce_router

# Module M13 - POS (Point de Vente)
from app.modules.pos.router import router as pos_router

# Module M14 - Subscriptions (Abonnements)
from app.modules.subscriptions.router import router as subscriptions_router

# Module M15 - Stripe Integration
from app.modules.stripe_integration.router import router as stripe_router

# Module M16 - Helpdesk (Support Client)
from app.modules.helpdesk.router import router as helpdesk_router

# Module M17 - Field Service (Interventions Terrain)
from app.modules.field_service.router import router as field_service_router

# Module M18 - Mobile App Backend
from app.modules.mobile.router import router as mobile_router

# Module IA - Assistant IA Transverse Opérationnelle
from app.modules.ai_assistant.router import router as ai_router

# Module GUARDIAN - Correction Automatique Gouvernée & Auditable
from app.modules.guardian.router import router as guardian_router
from app.modules.guardian.middleware import setup_guardian_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: création des tables au démarrage avec retry + observabilité"""
    from sqlalchemy import text

    # Initialiser le logging structuré
    _settings = get_settings()
    setup_logging(
        level="DEBUG" if _settings.debug else "INFO",
        json_format=_settings.is_production
    )
    logger = get_logger(__name__)
    logger.info("AZALS démarrage", extra={"environment": _settings.environment})

    # Initialiser les métriques Prometheus
    init_metrics()

    max_retries = 5

    for attempt in range(max_retries):
        try:
            # Test connection first
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # Create tables one by one to handle existing indexes gracefully
            # Two passes: first creates parent tables, second creates dependent tables
            tables_created = 0
            tables_existed = 0
            failed_tables = []

            # First pass
            for table in Base.metadata.sorted_tables:
                try:
                    table.create(bind=engine, checkfirst=True)
                    tables_created += 1
                except Exception as table_error:
                    error_str = str(table_error).lower()
                    if "already exists" in error_str or "duplicate" in error_str:
                        tables_existed += 1
                    else:
                        failed_tables.append((table, table_error))

            # Second pass for tables with FK dependencies
            for table, _ in failed_tables:
                try:
                    table.create(bind=engine, checkfirst=True)
                    tables_created += 1
                except Exception as table_error:
                    error_str = str(table_error).lower()
                    if "already exists" in error_str or "duplicate" in error_str:
                        tables_existed += 1
                    else:
                        print(f"[WARN] Erreur table {table.name}: {table_error}")

            print(f"[OK] Base de donnees connectee (creees: {tables_created}, existantes: {tables_existed})")
            break

        except Exception as e:
            print(f"[...] Connexion DB tentative {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                print("[WARN] DB non disponible, l'app demarre quand meme")

    # Démarrer le scheduler
    scheduler_service.start()

    yield

    # Arrêter le scheduler à l'arrêt
    scheduler_service.shutdown()

# SÉCURITÉ: Configuration dynamique selon environnement
_settings = get_settings()

# Désactiver docs API en production (CRITIQUE)
_docs_url = "/docs" if _settings.is_development else None
_redoc_url = "/redoc" if _settings.is_development else None
_openapi_url = "/openapi.json" if _settings.is_development else None

if _settings.is_production:
    print("[SECURE] PRODUCTION MODE: API docs desactivees")

app = FastAPI(
    title="AZALS",
    description="ERP decisionnel critique - Multi-tenant + Authentification JWT",
    version="0.3.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan
)

# Middleware stack (ordre important: dernier ajouté = premier exécuté)
# En Starlette, les middlewares s'exécutent dans l'ordre INVERSE d'ajout
# Donc on ajoute dans l'ordre: compression -> metrics -> rbac -> tenant -> CORS
# Pour que l'exécution soit: CORS -> tenant -> rbac -> metrics -> compression

# 1. Compression (s'exécute en dernier)
app.add_middleware(CompressionMiddleware, minimum_size=1024, compress_level=6)

# 2. Metrics
app.add_middleware(MetricsMiddleware)

# 3. RBAC Middleware - Contrôle d'accès basé sur les rôles (BETA)
# Note: Le middleware RBAC vérifie les permissions après authentification
# Pour la bêta, les routes non configurées génèrent un warning mais passent
# En production, activer deny-by-default dans rbac_middleware.py
app.add_middleware(RBACMiddleware)

# 4. TenantMiddleware - Validation X-Tenant-ID
app.add_middleware(TenantMiddleware)

# 5. GUARDIAN Middleware - Interception automatique des erreurs
# S'exécute après Tenant pour avoir accès au tenant_id
setup_guardian_middleware(app, environment=_settings.environment)

# 6. CORS en dernier (s'exécute en premier pour gérer OPTIONS preflight)
setup_cors(app)

# Routes observabilite (PUBLIQUES - pas de tenant required)
app.include_router(health_router)
app.include_router(metrics_router)

# ==================== API v1 ====================
# Toutes les routes metier sous le prefixe /v1
api_v1 = APIRouter(prefix="/v1")

# Routes authentification (necessitent X-Tenant-ID mais pas JWT)
api_v1.include_router(auth_router)

# Routes protegees par JWT + tenant
api_v1.include_router(protected_router)
api_v1.include_router(journal_router)
api_v1.include_router(decision_router)
api_v1.include_router(red_workflow_router)
api_v1.include_router(accounting_router)
api_v1.include_router(treasury_router)
api_v1.include_router(tax_router)
api_v1.include_router(hr_router)
api_v1.include_router(legal_router)
api_v1.include_router(admin_migration_router)  # TEMPORAIRE pour migration
api_v1.include_router(partners_router)  # Alias vers module commercial (clients, fournisseurs, contacts)
api_v1.include_router(invoicing_router)  # Alias vers module commercial (devis, factures, avoirs)

# Module T0 - IAM (Gestion Utilisateurs & Roles)
api_v1.include_router(iam_router)

# Module T1 - Configuration Automatique par Fonction
api_v1.include_router(autoconfig_router)

# Module T2 - Systeme de Declencheurs & Diffusion
api_v1.include_router(triggers_router)

# Module T3 - Audit & Benchmark Evolutif
api_v1.include_router(audit_router)

# Module T4 - Controle Qualite Central
api_v1.include_router(qc_router)

# Module T5 - Packs Pays (Localisation)
api_v1.include_router(country_packs_router)
api_v1.include_router(france_pack_router)

# Module T6 - Diffusion d'Information Periodique
api_v1.include_router(broadcast_router)

# Module T7 - Module Web Transverse
api_v1.include_router(web_router)

# Module T8 - Site Web Officiel AZALS
api_v1.include_router(website_router)

# Module T9 - Gestion des Tenants (Multi-Tenancy)
api_v1.include_router(tenants_router)

# Module M1 - Commercial (CRM & Ventes)
api_v1.include_router(commercial_router)

# Module M2 - Finance (Comptabilite & Tresorerie)
api_v1.include_router(finance_router)

# Module M3 - RH (Ressources Humaines)
api_v1.include_router(hr_module_router)

# Module M4 - Achats (Procurement)
api_v1.include_router(procurement_router)

# Module M5 - Stock (Inventaire + Logistique)
api_v1.include_router(inventory_router)

# Module M6 - Production (Manufacturing)
api_v1.include_router(production_router)

# Module M7 - Qualite (Quality Management)
api_v1.include_router(quality_router)

# Module M8 - Maintenance (Asset Management / GMAO)
api_v1.include_router(maintenance_router)

# Module M9 - Projets (Project Management)
api_v1.include_router(projects_router)

# Module M10 - BI & Reporting (Business Intelligence)
api_v1.include_router(bi_router)

# Module M11 - Compliance (Conformite Reglementaire)
api_v1.include_router(compliance_router)

# Module M12 - E-Commerce
api_v1.include_router(ecommerce_router)

# Module M13 - POS (Point de Vente)
api_v1.include_router(pos_router)

# Module M14 - Subscriptions (Abonnements)
api_v1.include_router(subscriptions_router)

# Module M15 - Stripe Integration
api_v1.include_router(stripe_router)

# Module M16 - Helpdesk (Support Client)
api_v1.include_router(helpdesk_router)

# Module M17 - Field Service (Interventions Terrain)
api_v1.include_router(field_service_router)

# Module M18 - Mobile App Backend
api_v1.include_router(mobile_router)

# Module IA - Assistant IA Transverse Operationnelle
api_v1.include_router(ai_router)

# Module GUARDIAN - Correction Automatique Gouvernee & Auditable
api_v1.include_router(guardian_router)

# Routes protegees par tenant uniquement (pas JWT pour compatibilite)
api_v1.include_router(items_router)


# ==================== UTILITY ENDPOINTS ====================
# Endpoints utilitaires pour le cockpit frontend
# NOTE: Doivent être définis AVANT app.include_router(api_v1)

@api_v1.get("/modules")
def get_active_modules(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne la liste des modules actifs pour le tenant courant.
    Utilise par le frontend pour afficher le menu de navigation.
    """
    base_modules = [
        {"code": "cockpit", "name": "Cockpit", "icon": "dashboard", "active": True},
        {"code": "partners", "name": "Partenaires", "icon": "people", "active": True},
        {"code": "invoicing", "name": "Facturation", "icon": "receipt", "active": True},
        {"code": "treasury", "name": "Trésorerie", "icon": "account_balance", "active": True},
        {"code": "accounting", "name": "Comptabilité", "icon": "calculate", "active": True},
        {"code": "projects", "name": "Projets", "icon": "folder", "active": True},
        {"code": "interventions", "name": "Interventions", "icon": "build", "active": True},
        {"code": "purchases", "name": "Achats", "icon": "shopping_cart", "active": True},
        {"code": "payments", "name": "Paiements", "icon": "payment", "active": True},
    ]
    role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role in ["DIRIGEANT", "ADMIN"]:
        base_modules.append({"code": "admin", "name": "Administration", "icon": "settings", "active": True})
    return {"modules": base_modules}


@api_v1.get("/notifications")
def get_user_notifications(
    current_user: User = Depends(get_current_user)
):
    """Retourne les notifications non lues pour l'utilisateur courant."""
    return {"notifications": [], "unread_count": 0}


@api_v1.get("/tenant/current")
def get_current_tenant_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les informations du tenant courant."""
    return {
        "tenant_id": current_user.tenant_id,
        "name": "SAS MASITH",
        "plan": "professional",
        "status": "active"
    }


@api_v1.get("/cockpit/dashboard")
def get_cockpit_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les données du dashboard cockpit."""
    return {"data": {
        "kpis": [
            {"id": "revenue", "label": "CA du mois", "value": 0, "unit": "€", "trend": 0, "status": "green"},
            {"id": "invoices", "label": "Factures en attente", "value": 0, "trend": 0, "status": "green"},
            {"id": "treasury", "label": "Trésorerie", "value": 0, "unit": "€", "trend": 0, "status": "green"},
            {"id": "overdue", "label": "Impayés", "value": 0, "unit": "€", "trend": 0, "status": "green"},
        ],
        "alerts": [],
        "treasury_summary": {
            "balance": 0,
            "forecast_30d": 0,
            "pending_payments": 0
        },
        "sales_summary": {
            "month_revenue": 0,
            "prev_month_revenue": 0,
            "pending_invoices": 0,
            "overdue_invoices": 0
        },
        "activity_summary": {
            "open_quotes": 0,
            "pending_orders": 0,
            "scheduled_interventions": 0
        }
    }}


@api_v1.get("/cockpit/decisions")
def get_cockpit_decisions(
    current_user: User = Depends(get_current_user)
):
    """Retourne les décisions en attente."""
    return {"data": {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 25
    }}


# ==================== ADMIN ENDPOINTS ====================
# Endpoints pour le module Administration

from app.core.models import UserRole

def require_admin_role(current_user: User) -> None:
    """Vérifie que l'utilisateur a un rôle admin (DIRIGEANT ou ADMIN)."""
    role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_value not in ["DIRIGEANT", "ADMIN"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="Accès refusé. Rôle ADMIN ou DIRIGEANT requis."
        )


@api_v1.get("/admin/roles")
def get_admin_roles(
    current_user: User = Depends(get_current_user)
):
    """Retourne la liste des rôles disponibles pour les utilisateurs."""
    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    roles = [
        {
            "id": role.value,
            "name": role.value,
            "description": {
                "DIRIGEANT": "Accès complet à toutes les fonctionnalités",
                "ADMIN": "Administration du système",
                "DAF": "Directeur Administratif et Financier",
                "COMPTABLE": "Accès comptabilité et facturation",
                "COMMERCIAL": "Accès ventes et clients",
                "EMPLOYE": "Accès limité aux fonctionnalités de base",
            }.get(role.value, ""),
            "capabilities": [],
            "user_count": 0,
            "is_system": True,
        }
        for role in UserRole
    ]
    return {"items": roles, "total": len(roles)}


@api_v1.get("/admin/stats")
def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les statistiques pour le dashboard admin."""
    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    total_users = db.query(User).filter(User.tenant_id == current_user.tenant_id).count()
    active_users = db.query(User).filter(
        User.tenant_id == current_user.tenant_id,
        User.is_active == 1
    ).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_roles": len(UserRole),
        "total_tenants": 1,
        "active_modules": 9,
    }


@api_v1.get("/admin/users")
def get_admin_users(
    page: int = 1,
    page_size: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne la liste des utilisateurs du tenant."""
    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    query = db.query(User).filter(User.tenant_id == current_user.tenant_id)
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": getattr(u, 'full_name', u.email),
                "roles": [u.role.value if hasattr(u.role, 'value') else str(u.role)],
                "is_active": u.is_active == 1,
                "created_at": str(u.created_at) if u.created_at else None,
                "last_login": None,
                "login_count": 0,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@api_v1.post("/admin/users")
def create_admin_user(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée un nouvel utilisateur."""
    from app.core.security import get_password_hash
    from fastapi import HTTPException

    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    # Vérifier si l'email existe déjà
    existing = db.query(User).filter(User.email == data.get("email")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # SÉCURITÉ: Validation et restriction des rôles assignables
    role_value = data.get("roles", ["EMPLOYE"])[0] if isinstance(data.get("roles"), list) else data.get("roles", "EMPLOYE")

    # Seul un DIRIGEANT peut créer un autre DIRIGEANT
    current_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_value == "DIRIGEANT" and current_role != "DIRIGEANT":
        raise HTTPException(
            status_code=403,
            detail="Seul un DIRIGEANT peut créer un autre DIRIGEANT"
        )

    # Validation du rôle
    valid_roles = [r.value for r in UserRole]
    if role_value not in valid_roles:
        role_value = "EMPLOYE"

    new_user = User(
        email=data.get("email"),
        password_hash=get_password_hash("TempPassword123!"),  # Mot de passe temporaire
        tenant_id=current_user.tenant_id,
        role=UserRole(role_value),
        is_active=1,
        full_name=data.get("name", ""),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "name": getattr(new_user, 'full_name', new_user.email),
        "roles": [new_user.role.value],
        "is_active": True,
    }


# Monter l'API v1 sur l'app principale
app.include_router(api_v1)


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
