"""
AZALS - Point d'entrée principal SÉCURISÉ ÉLITE
=================================================
ERP décisionnel critique - Sécurité by design - Multi-tenant strict
ÉLITE: Docs API désactivées en production, Observabilité complète

SECURITE:
- Garde-fous de sécurité exécutés AVANT toute opération
- Version canonique depuis app/core/version.py
- Crash immédiat si violation de sécurité
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.admin import AdminUserCreate, AdminUserResponse, router as admin_dashboard_router
from app.api.admin_migration import router as admin_migration_router
from app.api.admin_sequences import router as admin_sequences_router
from app.api.auth import router as auth_router
from app.api.branding import router as branding_router
from app.api.signup import router as signup_router
from app.api.webhooks import router as webhooks_router

# Module COCKPIT - Tableau de bord dirigeant
from app.api.cockpit import router as cockpit_router

# Modules COMMERCIAL, PROJECTS, INTERVENTIONS -> v3 uniquement (voir app/api/v3.py)
from app.api.decision import router as decision_router
from app.api.hr import router as hr_router
from app.api.invoicing import router as invoicing_router
# V2 ROUTERS SUPPRIMÉS - Migration v3 complète
from app.api.items import router as items_router
from app.api.journal import router as journal_router
from app.api.legal import router as legal_router
from app.api.partners import router as partners_router
from app.api.protected import router as protected_router
from app.api.red_workflow import router as red_workflow_router
from app.api.tax import router as tax_router
from app.api.workflows import router as workflows_router
from app.core.compression import CompressionMiddleware
from app.core.config import get_settings
from app.core.database import engine, get_db
from app.core.dependencies import get_current_user
from app.core.guards import enforce_startup_security
from app.core.health import router as health_router
from app.api.health_business import router as health_business_router
from app.core.http_errors import register_error_handlers
from app.core.logging_config import get_logger, setup_logging
from app.core.metrics import MetricsMiddleware, init_metrics
from app.core.metrics import router as metrics_router
from app.core.middleware import TenantMiddleware
from app.core.core_auth_middleware import CoreAuthMiddleware
from app.core.models import User
from app.core.security_middleware import setup_cors
from app.core.error_middleware import ErrorHandlingMiddleware
from app.core.version import AZALS_VERSION

# IMPORTANT: Importer Base depuis app.db (avec UUIDMixin), PAS depuis app.core.database
from app.db import Base
from app.db.model_loader import load_all_models, verify_models_loaded

# ===========================================================================
# ROUTERS UNIFIÉS - Migration CORE SaaS v2 (Wave 8 Complete)
# ===========================================================================
# Tous les modules migrent vers router_unified.py qui supporte v1 et v2
# via double enregistrement avec préfixes différents.
# ===========================================================================

# Module IA - Orchestration IA AZALSCORE (Theo, Guardian, GPT, Claude)
from app.ai.api import router as ai_orchestration_router

# API Audit - UI Events endpoint
from app.api.audit import router as audit_api_router

# Guardian middleware and logging
from app.modules.guardian.middleware import setup_guardian_middleware
from app.core.request_logging import setup_request_logging

# Module GUARDIAN AI - Monitoring IA automatisé (Mode A/B/C)
from app.modules.guardian.ai_router import router as guardian_ai_router

# API Incidents - Endpoint simplifié pour Guardian
from app.api.incidents import router as incidents_router

# RBAC Middleware
from app.modules.iam.rbac_middleware import RBACMiddleware

# Trial Router
from app.modules.tenants.api_trial import router as trial_router

# France Country Pack (sous-module, reste en v1)
from app.modules.country_packs.france.router import router as france_pack_router

# ===========================================================================
# MODULES LEGACY (v1 seulement - pas de router_unified)
# ===========================================================================
# Module MARCEAU - Agent IA Polyvalent (9 modules metiers)
from app.modules.marceau.router import router as marceau_router

# Module ENRICHMENT - Auto-enrichissement via APIs externes (INSEE, Adresse gouv, Open Facts)
from app.modules.enrichment import enrichment_router

# Module ODOO IMPORT - Import de données depuis Odoo (versions 8-18)
from app.modules.odoo_import import odoo_import_router

# ===========================================================================
# MODULES V3 - CRUDRouter (Migration complète)
# ===========================================================================
# Tous les modules sont maintenant servis via /v3/ par app.api.v3
# Les router_unified.py ont été supprimés
# ===========================================================================

# ===========================================================================
# API V3 - CRUDROUTER EDITION (Minimal Code)
# ===========================================================================
# Routers CRUDRouter auto-generes avec ~60% moins de boilerplate
# Import conditionnel pour compatibilite si modules pas encore migres
# ===========================================================================
try:
    from app.api.v3 import router as api_v3_router, _metrics as api_v3_metrics
    API_V3_AVAILABLE = True
    _api_v3_error = None
except ImportError as e:
    API_V3_AVAILABLE = False
    _api_v3_error = str(e)
    api_v3_metrics = None

    # SÉCURITÉ: En production, l'API V3 est OBLIGATOIRE
    # Fail-fast pour éviter de démarrer avec seulement 6 modules au lieu de 43
    _settings_check = get_settings()
    if _settings_check.is_production:
        raise RuntimeError(
            f"[FATAL] API V3 import failed in PRODUCTION mode. "
            f"Cannot start without core modules. Error: {e}"
        ) from e

from app.services.scheduler import scheduler_service

# Logger module-level pour observabilité production
logger = get_logger(__name__)


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

    # =========================================================================
    # GARDE-FOUS DE SECURITE - EXECUTION AVANT TOUTE OPERATION
    # =========================================================================
    # CRITIQUE: Ces verifications s'executent AVANT toute connexion DB
    # Une violation provoque un CRASH IMMEDIAT (pas de demarrage)
    # =========================================================================
    try:
        security_status = enforce_startup_security(_settings)
        logger.info(
            "[SECURITY] Garde-fous valides",
            extra={
                "environment": security_status.environment,
                "version": security_status.version,
                "branch": security_status.branch,
                "locked": security_status.is_locked
            }
        )
    except Exception as security_error:
        logger.critical(
            "[SECURITY] VIOLATION FATALE — Arrêt immédiat du système",
            extra={"error": str(security_error), "consequence": "startup_aborted"}
        )
        raise  # Arret immediat - pas de demarrage sans validation securite

    # Initialiser les métriques Prometheus
    init_metrics()

    # =========================================================================
    # CHARGEMENT OBLIGATOIRE DES MODELES ORM
    # =========================================================================
    # CRITIQUE: Charger TOUS les modeles AVANT toute operation DB
    # Cela garantit que Base.metadata.tables contient toutes les tables
    # et que create_all() et le verrou UUID fonctionnent correctement.
    # =========================================================================
    try:
        modules_loaded = load_all_models()
        verify_models_loaded()
        table_count = len(Base.metadata.tables)
        logger.info(
            "[MODEL_LOADER] Modèles ORM chargés avec succès",
            extra={
                "modules_loaded": modules_loaded,
                "table_count": table_count,
                "consequence": "orm_ready"
            }
        )
    except (RuntimeError, AssertionError) as model_err:
        logger.critical(
            "[MODEL_LOADER] ECHEC CRITIQUE — Impossible de charger les modèles ORM",
            extra={"error": str(model_err), "consequence": "startup_aborted"}
        )
        raise  # Arret immediat - pas de demarrage sans modeles

    max_retries = 5
    # Variable pour tracker l'etat reel de la conformite UUID
    db_uuid_status = "UNKNOWN"
    db_violation_count = 0

    for attempt in range(max_retries):
        try:
            # Test connection first
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                # Enable pgcrypto extension for UUID generation (if PostgreSQL)
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
                    conn.commit()
                    logger.info("[DB] Extensions PostgreSQL activées (pgcrypto, uuid-ossp)")
                except Exception as e:
                    logger.info(
                        "[DB] Extensions PostgreSQL non créées — probablement déjà existantes",
                        extra={"error": str(e)}
                    )

            # =========================================================================
            # GESTION CONFORMITE UUID - DETECTION ET RESET AUTOMATIQUE
            # =========================================================================
            # Utilise UUIDComplianceManager pour:
            # - Detecter les violations (colonnes BIGINT/INT)
            # - Auto-reset en dev/test si configure
            # - Blocage strict en production
            # =========================================================================
            from app.db.uuid_reset import UUIDComplianceError, UUIDComplianceManager, UUIDResetBlockedError

            uuid_manager = UUIDComplianceManager(engine, _settings)

            # DETECTION INITIALE - OBLIGATOIRE AVANT TOUT
            initial_violations = uuid_manager.detect_violations()
            db_violation_count = len(initial_violations)

            if db_violation_count > 0:
                tables_affected = len({v[0] for v in initial_violations})
                logger.warning(
                    "[UUID] Base LEGACY détectée — colonnes INT/BIGINT non conformes",
                    extra={
                        "violation_count": db_violation_count,
                        "tables_affected": tables_affected,
                        "consequence": "uuid_compliance_required"
                    }
                )

            try:
                # Cette methode gere tout: detection, reset si autorise, erreur sinon
                uuid_compliant = uuid_manager.ensure_uuid_compliance()

                if uuid_manager.reset_performed:
                    # Reset effectue - les tables ont deja ete recreees par le manager
                    db_uuid_status = "UUID-native"
                    db_violation_count = 0
                    tables_created = len(uuid_manager.get_all_tables())
                    tables_existed = 0
                    logger.info(
                        "[UUID] Reset UUID effectué — base recréée en mode UUID-native",
                        extra={
                            "tables_created": tables_created,
                            "tables_existed": tables_existed,
                            "db_status": "UUID-native",
                            "consequence": "schema_validation_next"
                        }
                    )

                    # Skip la creation manuelle des tables - deja fait par le manager
                    # Aller directement a la validation schema
                    try:
                        from app.core.schema_validator import validate_schema_on_startup
                        schema_valid = validate_schema_on_startup(
                            engine, Base,
                            strict=_settings.is_production
                        )
                        if schema_valid:
                            logger.info("[UUID] Schéma validé — toutes les PK/FK utilisent UUID")
                        else:
                            logger.warning("[UUID] Schéma: avertissements détectés — consulter les logs détaillés")
                    except Exception as schema_err:
                        logger.warning(
                            "[UUID] Validation schéma ignorée",
                            extra={"error": str(schema_err), "consequence": "schema_not_validated"}
                        )

                    break  # Sortir de la boucle de retry

                elif uuid_compliant:
                    # Base deja conforme - verrou UUID silencieux
                    db_uuid_status = "UUID-native"
                    db_violation_count = 0
                    logger.info(
                        "[UUID] Base conforme UUID — verrou actif",
                        extra={"violations": 0, "lock": "active"}
                    )
                else:
                    # Mode non-strict avec violations - NE PAS mentir sur l'etat
                    db_uuid_status = "LEGACY (violations ignorees)"
                    db_violation_count = len(uuid_manager.violations)
                    logger.warning(
                        "[UUID] Violations UUID ignorées — mode non-strict actif",
                        extra={
                            "violation_count": db_violation_count,
                            "db_status": "INCOMPATIBLE",
                            "consequence": "legacy_mode_active"
                        }
                    )

            except UUIDComplianceError as uuid_err:
                # Violations detectees et mode strict - arreter le demarrage
                db_uuid_status = "INCOMPATIBLE (blocage strict)"
                logger.critical(
                    "[UUID] Violations détectées en mode strict — démarrage bloqué",
                    extra={"error": str(uuid_err), "consequence": "startup_aborted"}
                )
                raise RuntimeError(str(uuid_err))

            except UUIDResetBlockedError as reset_err:
                # Reset bloque (production ou non autorise)
                db_uuid_status = "INCOMPATIBLE (reset bloque)"
                logger.critical(
                    "[UUID_RESET] Reset bloqué — production ou non autorisé",
                    extra={"error": str(reset_err), "consequence": "startup_aborted"}
                )
                raise RuntimeError(str(reset_err))

            # Create tables with multi-pass retry for FK dependencies
            # sorted_tables respects FK order, but cross-module deps may need retries
            tables_created = 0
            tables_existed = 0
            pending_tables = list(Base.metadata.sorted_tables)
            max_passes = 10
            last_errors = {}

            for pass_num in range(1, max_passes + 1):
                if not pending_tables:
                    break

                still_pending = []
                pass_created = 0

                for table in pending_tables:
                    try:
                        table.create(bind=engine, checkfirst=True)
                        tables_created += 1
                        pass_created += 1
                        last_errors.pop(table.name, None)
                    except Exception as table_error:
                        error_str = str(table_error).lower()
                        if "already exists" in error_str or "duplicate" in error_str:
                            tables_existed += 1
                            pass_created += 1
                            last_errors.pop(table.name, None)
                        else:
                            # FK dependency or other error - retry in next pass
                            still_pending.append(table)
                            last_errors[table.name] = str(table_error)[:200]

                pending_tables = still_pending

                # Stop early if no progress (same tables failing repeatedly)
                if pass_created == 0 and pass_num >= 3:
                    break

            # Report final errors
            if pending_tables:
                failed_tables = {t.name: last_errors.get(t.name, "Unknown error") for t in pending_tables}
                logger.error(
                    "[DB] Tables non créées après retries",
                    extra={
                        "failed_count": len(pending_tables),
                        "failed_tables": failed_tables,
                        "consequence": "partial_schema"
                    }
                )

            logger.info(
                "[DB] Connexion base de données établie",
                extra={"tables_created": tables_created, "tables_existed": tables_existed}
            )

            # VERROU ANTI-RÉGRESSION: Valider le schéma UUID
            try:
                from app.core.schema_validator import validate_schema_on_startup
                # strict=False en dev, strict=True en prod pour bloquer les démarrages
                schema_valid = validate_schema_on_startup(
                    engine, Base,
                    strict=_settings.is_production
                )
                if schema_valid:
                    logger.info("[SCHEMA] Validé — toutes les PK/FK utilisent UUID")
                else:
                    logger.warning("[SCHEMA] Avertissements détectés — consulter les logs détaillés")
            except Exception as schema_err:
                logger.warning(
                    "[SCHEMA] Validation ignorée",
                    extra={"error": str(schema_err), "consequence": "schema_not_validated"}
                )

            break

        except Exception as e:
            logger.error(
                "[DB] Échec connexion base de données",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "error": str(e),
                    "consequence": "retry" if attempt < max_retries - 1 else "degraded_startup"
                }
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                logger.critical(
                    "[DB] Base de données non disponible après tous les retries — démarrage dégradé",
                    extra={"max_retries": max_retries, "consequence": "no_database"}
                )

    # Démarrer le scheduler
    scheduler_service.start()
    logger.info("[SCHEDULER] Service de planification démarré")

    # =========================================================================
    # DEMARRAGE TERMINE - AFFICHAGE ETAT REEL
    # =========================================================================
    # INTERDICTION d'afficher "Application startup complete" si violations > 0
    # Inclut maintenant la version et le statut de securite
    from app.core.guards import get_current_git_branch
    current_branch = get_current_git_branch() or "unknown"
    security_locked = "LOCKED" if _settings.is_production or current_branch == "main" else "UNLOCKED"

    startup_context = {
        "version": AZALS_VERSION,
        "environment": _settings.environment,
        "branch": current_branch,
        "security_status": security_locked,
        "uuid_lock": "active",
        "database": db_uuid_status,
        "violations": db_violation_count,
        "tables": len(Base.metadata.tables)
    }

    if db_violation_count == 0 and db_uuid_status == "UUID-native":
        # Base conforme - startup complet
        logger.info(
            "[STARTUP] APPLICATION STARTUP COMPLETE — Base UUID-native, système opérationnel",
            extra=startup_context
        )
    else:
        # Base non conforme - avertissement explicite
        logger.warning(
            "[STARTUP] DÉMARRAGE EN MODE DÉGRADÉ — Base non conforme UUID, reset requis",
            extra=startup_context
        )

    yield

    # Arrêter le scheduler à l'arrêt
    logger.info("[SHUTDOWN] Arrêt du scheduler en cours")
    scheduler_service.shutdown()
    logger.info("[SHUTDOWN] Application arrêtée proprement")

# SÉCURITÉ: Configuration dynamique selon environnement
_settings = get_settings()

# Désactiver docs API en production (CRITIQUE)
_docs_url = "/docs" if _settings.is_development else None
_redoc_url = "/redoc" if _settings.is_development else None
_openapi_url = "/openapi.json" if _settings.is_development else None

if _settings.is_production:
    logger.info("[SECURE] MODE PRODUCTION — docs API désactivées (/docs, /redoc, /openapi.json)")

app = FastAPI(
    title="AZALS",
    description="ERP decisionnel critique - Multi-tenant + Authentification JWT",
    version=AZALS_VERSION,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan
)


# ===========================================================================
# GESTION CENTRALISEE DES ERREURS HTTP
# ===========================================================================
# Enregistrement des handlers pour 401, 403, 404, 422, 500
# Format de reponse JSON standardise, logging structure
# ===========================================================================
register_error_handlers(app)


# Middleware stack (ordre important: dernier ajouté = premier exécuté)
# En Starlette, les middlewares s'exécutent dans l'ordre INVERSE d'ajout
# Donc on ajoute dans l'ordre: error_handling -> rate_limit -> csrf -> compression -> metrics -> rbac -> tenant -> CORS
# Pour que l'exécution soit: CORS -> tenant -> rbac -> metrics -> compression -> csrf -> rate_limit -> error_handling

# 1. Error Handling (s'exécute en tout dernier - capture toutes les erreurs)
app.add_middleware(ErrorHandlingMiddleware)
logger.info("[MIDDLEWARE] ErrorHandlingMiddleware activé")

# 2. Platform Rate Limiting - Protection DDoS et abuse API
# SÉCURITÉ P1: Limites globales par IP (1000/min), par tenant (5000/min), plateforme (50000/min)
from app.core.rate_limiter import setup_platform_rate_limiting
setup_platform_rate_limiting(app, ip_limit=1000, tenant_limit=5000, global_limit=50000)
logger.info(
    "[MIDDLEWARE] Rate Limiting activé — PRODUCTION",
    extra={"ip_limit": 1000, "tenant_limit": 5000, "global_limit": 50000}
)

# 3. CSRF Protection - Anti Cross-Site Request Forgery
# SÉCURITÉ: Vérifie les tokens CSRF pour POST/PUT/DELETE/PATCH
# Token obtenu via GET /auth/csrf-token, valide 1 heure
# Exempté: auth endpoints, webhooks (signature), health checks, Bearer API
from app.core.csrf_middleware import setup_csrf_middleware
setup_csrf_middleware(app, enforce=True)
logger.info(
    "[MIDDLEWARE] CSRF Protection activée — PRODUCTION",
    extra={"enforce": True, "token_endpoint": "/auth/csrf-token", "expiry": "1h"}
)

# 4. Compression
app.add_middleware(CompressionMiddleware, minimum_size=1024, compress_level=6)
logger.info("[MIDDLEWARE] Compression activée", extra={"min_size": 1024, "level": 6})

# 5. Metrics
app.add_middleware(MetricsMiddleware)
logger.info("[MIDDLEWARE] MetricsMiddleware activé")

# 6. RBAC Middleware - Contrôle d'accès basé sur les rôles (BETA)
# Note: Le middleware RBAC vérifie les permissions après authentification
# Pour la bêta, les routes non configurées génèrent un warning mais passent
# En production, activer deny-by-default dans rbac_middleware.py
app.add_middleware(RBACMiddleware)
logger.warning(
    "[MIDDLEWARE] RBAC en mode BETA — deny-by-default NON activé",
    extra={"mode": "beta", "consequence": "rbac_permissive", "action_required": "activer deny-by-default"}
)

# 7. CoreAuthMiddleware - Parse JWT et crée SaaSContext via CORE
# IMPORTANT: Doit s'exécuter AVANT RBAC pour que request.state.saas_context soit disponible
# NOUVEAU: Utilise CORE.authenticate() au lieu de logique dupliquée
app.add_middleware(CoreAuthMiddleware)
logger.info("[MIDDLEWARE] CoreAuthMiddleware activé (JWT + SaaSContext)")

# 8. TenantMiddleware - Validation X-Tenant-ID
app.add_middleware(TenantMiddleware)
logger.info("[MIDDLEWARE] TenantMiddleware activé (X-Tenant-ID)")

# 9. GUARDIAN Middleware - Interception automatique des erreurs
# S'exécute après Tenant pour avoir accès au tenant_id
setup_guardian_middleware(app, environment=_settings.environment)
logger.info("[MIDDLEWARE] Guardian activé", extra={"environment": _settings.environment})

# 10. CORS en dernier (s'exécute en premier pour gérer OPTIONS preflight)
setup_cors(app)
logger.info("[MIDDLEWARE] CORS configuré")

# 11. Request Logging (si LOG_VERBOSE=true ou LOG_REQUESTS=true)
setup_request_logging(app)
logger.info("[MIDDLEWARE] Request Logging configuré")

# NOTE: health_router and metrics_router sont inclus après api_v1 pour éviter
# les problèmes de "No response returned" lors du démarrage

# Routes signup et webhooks (PUBLIQUES - nouvelles inscriptions)
app.include_router(signup_router)
app.include_router(webhooks_router)

# ==================== AUTH LEGACY (sans prefix /v1) ====================
# Route /auth/login directement accessible pour compatibilité V0
# Ceci expose /auth/login, /auth/register, /auth/bootstrap, etc.
app.include_router(auth_router)

# ==================== API v1 - DEPRECATED ====================
# MIGRATION V3: Les routes v1 sont maintenant servies par v3
# Le frontend a ete migre vers /v3/
# Ces lignes sont commentees - a supprimer apres validation complete
#
# API sans version - URLs directes
api_v1 = APIRouter()  # Legacy routes (cockpit, auth, etc.) - sans prefixe de version

# Routes authentification (necessitent X-Tenant-ID mais pas JWT)
api_v1.include_router(auth_router)

# Routes protegees par JWT + tenant
api_v1.include_router(protected_router)
api_v1.include_router(journal_router)
api_v1.include_router(decision_router)
api_v1.include_router(red_workflow_router)
api_v1.include_router(tax_router)
api_v1.include_router(hr_router)
api_v1.include_router(legal_router)
api_v1.include_router(admin_migration_router)  # TEMPORAIRE pour migration
logger.warning(
    "[ROUTER] admin_migration_router monté — marqué TEMPORAIRE, à retirer après migration",
    extra={"router": "admin_migration", "status": "temporary", "action_required": "remove_after_migration"}
)
api_v1.include_router(admin_sequences_router)  # Administration des sequences de numerotation
api_v1.include_router(admin_dashboard_router)  # Administration dashboard (stats systeme)
api_v1.include_router(partners_router)  # Alias vers module commercial (clients, fournisseurs, contacts)
api_v1.include_router(invoicing_router)  # Alias vers module commercial (devis, factures, avoirs)
# commercial_router, projects_router, interventions_router -> v3 uniquement
api_v1.include_router(branding_router)  # Gestion favicon, logo, branding

# ===========================================================================
# ROUTES LEGACY SOUS /v1 (non migrées vers v3)
# ===========================================================================
api_v1.include_router(audit_api_router)        # Audit UI Events
api_v1.include_router(france_pack_router)      # France Country Pack
api_v1.include_router(ai_orchestration_router) # IA Orchestration
api_v1.include_router(guardian_ai_router)      # Guardian AI
api_v1.include_router(incidents_router)        # Incidents
api_v1.include_router(cockpit_router)          # Cockpit Dashboard

# API WORKFLOWS - Orchestration DAG déclarative (AZALSCORE)
api_v1.include_router(workflows_router)

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


@api_v1.get("/admin/users/{user_id}")
def get_admin_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les détails d'un utilisateur par son ID."""
    from uuid import UUID
    from fastapi import HTTPException

    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")

    user = db.query(User).filter(
        User.tenant_id == current_user.tenant_id,
        User.id == user_uuid
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return {
        "id": str(user.id),
        "email": user.email,
        "name": getattr(user, 'full_name', user.email),
        "first_name": getattr(user, 'first_name', None),
        "last_name": getattr(user, 'last_name', None),
        "roles": [user.role.value if hasattr(user.role, 'value') else str(user.role)],
        "is_active": user.is_active == 1,
        "is_locked": getattr(user, 'is_locked', 0) == 1,
        "created_at": str(user.created_at) if user.created_at else None,
        "last_login": str(getattr(user, 'last_login_at', None)) if getattr(user, 'last_login_at', None) else None,
        "login_count": getattr(user, 'login_count', 0) or 0,
        "totp_enabled": getattr(user, 'totp_enabled', 0) == 1,
        "must_change_password": getattr(user, 'must_change_password', 0) == 1,
        "tenant_id": user.tenant_id,
    }


@api_v1.post("/admin/users", response_model=AdminUserResponse)
def create_admin_user(
    data: AdminUserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel utilisateur.

    Conformité:
    - AZA-SEC-001: Validation Pydantic stricte
    - AZA-BE-003: Contrat backend obligatoire

    Args:
        data: Données validées par AdminUserCreate
        current_user: Utilisateur authentifié (admin requis)
        db: Session base de données

    Returns:
        AdminUserResponse avec les informations du nouvel utilisateur

    Raises:
        HTTPException 400: Email déjà utilisé
        HTTPException 403: Droits insuffisants pour créer un DIRIGEANT
    """
    from fastapi import HTTPException

    from app.core.security import get_password_hash

    # SÉCURITÉ: Vérification du rôle admin obligatoire
    require_admin_role(current_user)

    # Vérifier si l'email existe déjà
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # SÉCURITÉ: Extraction du rôle depuis la liste validée
    role_value = data.roles[0] if data.roles else "EMPLOYE"

    # Seul un DIRIGEANT peut créer un autre DIRIGEANT
    current_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_value == "DIRIGEANT" and current_role != "DIRIGEANT":
        raise HTTPException(
            status_code=403,
            detail="Seul un DIRIGEANT peut créer un autre DIRIGEANT"
        )

    # Création de l'utilisateur (données déjà validées par Pydantic)
    new_user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        tenant_id=current_user.tenant_id,
        role=UserRole(role_value),
        is_active=1,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AdminUserResponse(
        id=str(new_user.id),
        email=new_user.email,
        name=new_user.email,
        roles=[new_user.role.value],
        is_active=True,
    )


# Monter l'API v1 sur l'app principale
app.include_router(api_v1)

# Trial Registration (public endpoints - no auth required)
app.include_router(trial_router)

# ==================== V2 SUPPRIMÉ ====================
# Migration v3 complète - v2 supprimé le 2026-02-15

# ==================== API MODULES - CRUDROUTER ====================
# Routers CRUDRouter avec code minimal (~60% reduction boilerplate)
# URLs directes sans version: /commercial, /accounting, /projects, etc.
if API_V3_AVAILABLE:
    app.include_router(api_v3_router)
    logger.info(
        "[API] CRUDRouter activé — 41 modules disponibles (URLs sans version)",
        extra={"modules_count": 41, "reduction": "60%", "versioning": "none"}
    )
else:
    logger.warning(
        "[API] Modules CRUDRouter non disponibles — erreur d'import",
        extra={"error": _api_v3_error, "consequence": "modules_disabled"}
    )

# ==================== THEO VOICE API ====================
# WebSocket et REST endpoints pour Théo (assistant vocal)
try:
    from app.theo.api import theo_router, theo_rest_router
    app.include_router(theo_router)
    app.include_router(theo_rest_router, prefix="/v1")
    logger.info("[THEO] Voice API routes enregistrées (WebSocket + REST)")
except ImportError as e:
    logger.warning(
        "[THEO] Voice API non disponible — module non installé",
        extra={"error": str(e), "consequence": "theo_voice_disabled"}
    )


# ==================== ROUTES OBSERVABILITE ====================
# Routes publiques pour monitoring (pas de tenant/auth required)
# IMPORTANT: Inclure APRÈS api_v1 pour éviter les conflits de routes
app.include_router(health_router)
app.include_router(health_business_router)
app.include_router(metrics_router)


# Fallback routes for health/metrics if routers don't work
# These are simple inline routes to diagnose routing issues
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from app.core.database import engine
from sqlalchemy import text

logger.info("[ROUTES] Health/Metrics fallback routes enregistrées (/health, /health/ready, /health/live, /metrics)")


@app.get("/health")
async def health_check_fallback():
    """Fallback health check endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(
            "[HEALTH] Échec connexion DB lors du health check",
            extra={"error": str(e), "consequence": "status_degraded"}
        )
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "api": True,
        "database": db_ok
    }


@app.get("/health/ready")
async def health_ready_fallback():
    """Fallback readiness probe."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(
            "[HEALTH] Readiness probe échouée — base de données indisponible",
            extra={"error": str(e), "consequence": "not_ready"}
        )
        return {"status": "not_ready", "reason": "Database unavailable"}


@app.get("/health/live")
async def health_live_fallback():
    """Fallback liveness probe."""
    return {"status": "alive"}


@app.get("/metrics")
async def metrics_fallback():
    """Fallback metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

# ==================== FRONTEND STATIQUE (LEGACY) ====================
# En production Docker, le frontend est un conteneur séparé (React SPA via Nginx).
# Ce bloc ne s'active QUE si le dossier ui/ existe dans le conteneur API,
# ce qui ne devrait PAS être le cas en production standard.

# Chemin vers le dossier UI
UI_DIR = Path(__file__).parent.parent / "ui"

# Servir les fichiers statiques (CSS, JS) depuis /ui
if UI_DIR.exists():
    logger.warning(
        "[LEGACY] Dossier ui/ détecté — frontend statique legacy activé. "
        "En production Docker standard, le frontend est un conteneur séparé.",
        extra={"ui_dir": str(UI_DIR), "consequence": "legacy_static_routes_active"}
    )
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        """Servir la page d'accueil"""
        index_path = UI_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Interface frontend non disponible"}

    @app.get("/favicon.ico")
    async def serve_favicon_ico():
        """Servir le favicon (format .ico redirige vers PNG)"""
        # Priorité au favicon custom
        custom_path = UI_DIR / "favicon-custom.png"
        if custom_path.exists():
            return FileResponse(custom_path, media_type="image/png")
        favicon_path = UI_DIR / "favicon.png"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/png")
        return FileResponse(UI_DIR / "favicon.png", status_code=404)

    @app.get("/favicon.png")
    async def serve_favicon_png():
        """Servir le favicon PNG - Priorité au custom si existant"""
        # Priorité au favicon custom
        custom_path = UI_DIR / "favicon-custom.png"
        if custom_path.exists():
            return FileResponse(
                custom_path,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "X-Asset-Type": "custom",
                    "X-Content-Type-Options": "nosniff"
                }
            )
        # Fallback au favicon par défaut
        favicon_path = UI_DIR / "favicon.png"
        if favicon_path.exists():
            return FileResponse(
                favicon_path,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "X-Asset-Type": "system",
                    "X-Content-Type-Options": "nosniff"
                }
            )
        return FileResponse(UI_DIR / "favicon.png", status_code=404)
else:
    logger.info("[FRONTEND] Pas de dossier ui/ — frontend servi par conteneur séparé (mode production standard)")


# ===========================================================================
# PAGES D'ERREURS STATIQUES (THEME VAISSEAU SPATIAL)
# ===========================================================================
# Routes pour servir les pages d'erreurs avec theme visuel coherent
# Accessibles directement pour le frontend en cas de redirection
# ===========================================================================

ERRORS_DIR = Path(__file__).parent.parent / "frontend" / "errors"

if ERRORS_DIR.exists():
    # Monter les assets des pages d'erreurs (SVG illustrations)
    ERRORS_ASSETS_DIR = ERRORS_DIR / "assets"
    if ERRORS_ASSETS_DIR.exists():
        app.mount("/errors/assets", StaticFiles(directory=str(ERRORS_ASSETS_DIR)), name="error_assets")

    @app.get("/errors/401")
    async def serve_error_401():
        """Page d'erreur 401 - Cockpit verrouille"""
        error_path = ERRORS_DIR / "401.html"
        if error_path.exists():
            return FileResponse(error_path, media_type="text/html")
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "Authentication required", "code": 401}
        )

    @app.get("/errors/403")
    async def serve_error_403():
        """Page d'erreur 403 - Zone interdite"""
        error_path = ERRORS_DIR / "403.html"
        if error_path.exists():
            return FileResponse(error_path, media_type="text/html")
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": "Access denied", "code": 403}
        )

    @app.get("/errors/404")
    async def serve_error_404():
        """Page d'erreur 404 - Destination introuvable"""
        error_path = ERRORS_DIR / "404.html"
        if error_path.exists():
            return FileResponse(error_path, media_type="text/html")
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": "Resource not found", "code": 404}
        )

    @app.get("/errors/500")
    async def serve_error_500():
        """Page d'erreur 500 - Defaillance systeme"""
        error_path = ERRORS_DIR / "500.html"
        if error_path.exists():
            return FileResponse(error_path, media_type="text/html")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Unexpected server error", "code": 500}
        )


# ===========================================================================
# ROUTE DE TEST DES ERREURS — SUPPRIMÉES (PRODUCTION STRICTE)
# ===========================================================================
# Les routes /test-errors/* ont été supprimées conformément à la politique
# de production stricte. Aucun endpoint de test ne doit exister en prod.
# ===========================================================================
