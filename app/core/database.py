"""
AZALS - Connexion PostgreSQL
Gestion securisee de la connexion base de donnees avec SQLAlchemy

IMPORTANT: Ce module exporte la Base depuis app.db pour garantir
l'unicite du registre de metadonnees ORM. NE JAMAIS utiliser
declarative_base() ici.

EXPORTS:
- Base: Classe de base ORM (re-exportée depuis app.db)
- get_db: Générateur de session FastAPI
- get_db_with_rls: Session avec contexte RLS
- set_rls_context: Définir le contexte RLS
- check_database_connection: Vérification connexion
- engine: Engine SQLAlchemy
- SessionLocal: Session factory
"""

import logging
import time

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

# IMPORTANT: Re-export Base depuis app.db pour compatibilité
# avec les imports existants (from app.core.database import Base)
from app.db import Base

# Configuration du logger
logger = logging.getLogger(__name__)

settings = get_settings()

# Configuration engine avec paramètres adaptés au type de base
# SQLite ne supporte pas pool_size/max_overflow
if settings.database_url.startswith('sqlite://'):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # P0 SÉCURITÉ: Protection contre DoS par épuisement du pool
    # - pool_timeout: délai max d'attente d'une connexion (évite blocage infini)
    # - pool_recycle: recycle les connexions anciennes (évite connexions zombies)
    # - connect_args timeout: limite le temps de connexion initial
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=30,  # P0: Max 30s d'attente pour une connexion
        pool_recycle=3600,  # P0: Recycle connexions après 1h
        connect_args={
            "connect_timeout": 10,  # P0: Max 10s pour établir connexion
            "options": "-c statement_timeout=30000"  # P0: Max 30s par requête
        },
        echo=False  # PRODUCTION: pas de log SQL verbeux
    )

logger.info(
    "[DB] Engine SQLAlchemy créé",
    extra={
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": True,
        "echo": False
    }
)

# ============================================================================
# MÉTRIQUES POOL DE CONNEXIONS
# ============================================================================

def _get_db_metrics():
    """Import lazy des métriques pour éviter les imports circulaires."""
    from app.core.metrics import DB_CONNECTIONS_ACTIVE, DB_QUERY_DURATION
    return DB_CONNECTIONS_ACTIVE, DB_QUERY_DURATION


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Appelé quand une connexion est empruntée du pool."""
    try:
        DB_CONNECTIONS_ACTIVE, _ = _get_db_metrics()
        DB_CONNECTIONS_ACTIVE.inc()
    except Exception:
        pass  # Silencieux si les métriques ne sont pas disponibles


@event.listens_for(engine, "checkin")
def on_checkin(dbapi_conn, connection_record):
    """Appelé quand une connexion est retournée au pool."""
    try:
        DB_CONNECTIONS_ACTIVE, _ = _get_db_metrics()
        DB_CONNECTIONS_ACTIVE.dec()
    except Exception:
        pass


def get_pool_status() -> dict:
    """Retourne les statistiques du pool de connexions."""
    pool = engine.pool
    return {
        "size": pool.size(),
        "checkedin": pool.checkedin(),
        "checkedout": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalidated": pool.invalidated()
    }


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# IMPORTANT: Reutiliser la Base unifiee depuis app.db
# Cette Base inclut UUIDMixin et garantit que TOUS les modeles
# sont enregistres dans le MEME registre de metadonnees.
# NE PAS utiliser declarative_base() ici - cela creerait un registre separe.


def get_db():
    """
    Générateur de session base de données.
    Utilisé comme dépendance FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_with_rls(tenant_id: str):
    """
    Générateur de session avec contexte RLS activé.

    SÉCURITÉ P1: Définit le tenant_id dans la session PostgreSQL
    pour que les politiques RLS filtrent automatiquement les données.

    Usage:
        db = next(get_db_with_rls(tenant_id))
        # Toutes les requêtes sont maintenant filtrées par RLS

    Args:
        tenant_id: ID du tenant pour le contexte RLS
    """
    db = SessionLocal()
    try:
        # SÉCURITÉ P1: Définir le contexte tenant pour RLS
        # Cette variable est lue par les politiques RLS PostgreSQL
        if tenant_id:
            db.execute(
                text("SET LOCAL app.current_tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            logger.debug("[RLS] Tenant context set: %s", tenant_id)
        yield db
    finally:
        db.close()


def set_rls_context(db, tenant_id: str) -> None:
    """
    Définit le contexte RLS sur une session existante.

    SÉCURITÉ P1: À appeler au début de chaque transaction
    pour activer le filtrage RLS.

    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant
    """
    if tenant_id:
        db.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        logger.debug("[RLS] Tenant context set on existing session: %s", tenant_id)


def get_db_for_scheduler(tenant_id: str):
    """
    P0 SÉCURITÉ: Crée une session DB pour les tâches planifiées avec contexte RLS.

    IMPORTANT: Les schedulers/background tasks DOIVENT utiliser cette fonction
    au lieu de SessionLocal() directement pour garantir l'isolation multi-tenant.

    P0 CRITIQUE: tenant_id est OBLIGATOIRE pour éviter tout accès cross-tenant.
    Pour les opérations plateforme (lister tous les tenants), utiliser
    get_db_for_platform_operation() à la place.

    Usage:
        db = get_db_for_scheduler(tenant_id)
        try:
            # ... opérations DB isolées par tenant
        finally:
            db.close()

    Args:
        tenant_id: ID du tenant pour le contexte RLS (OBLIGATOIRE)

    Returns:
        Session SQLAlchemy avec contexte RLS

    Raises:
        ValueError: Si tenant_id est None ou vide
    """
    # P0 SÉCURITÉ: tenant_id OBLIGATOIRE - jamais de session sans contexte RLS
    if not tenant_id or not tenant_id.strip():
        raise ValueError(
            "[RLS_CRITICAL] tenant_id est OBLIGATOIRE pour get_db_for_scheduler(). "
            "Pour les opérations plateforme, utiliser get_db_for_platform_operation()."
        )

    db = SessionLocal()
    set_rls_context(db, tenant_id)
    logger.debug("[RLS] Scheduler session with RLS context: %s", tenant_id)
    return db


def get_db_for_platform_operation(caller: str = "unknown"):
    """
    P0 SÉCURITÉ: Session DB pour opérations plateforme UNIQUEMENT.

    ATTENTION: Cette fonction crée une session SANS contexte RLS.
    À utiliser UNIQUEMENT pour:
    - Lister tous les tenants (opération plateforme)
    - Migrations/maintenance système
    - Opérations SUPERADMIN explicites
    - Schedulers pour requêtes cross-tenant initiales

    JAMAIS pour des opérations sur des données tenant-specific.

    P1 SÉCURITÉ: Le paramètre caller permet de tracer l'origine des appels.

    Usage:
        db = get_db_for_platform_operation(caller="scheduler.reset_red_alerts")
        try:
            tenants = db.query(Tenant).all()  # OK - opération plateforme
        finally:
            db.close()

    Args:
        caller: Identifiant du code appelant pour audit

    Returns:
        Session SQLAlchemy SANS contexte RLS
    """
    import inspect
    # P1 SÉCURITÉ: Détecter automatiquement l'appelant si non fourni
    if caller == "unknown":
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller = f"{frame.f_back.f_code.co_filename}:{frame.f_back.f_lineno}"

    logger.warning(
        "[RLS_PLATFORM] Session sans RLS créée - opération plateforme uniquement",
        extra={
            "caller": caller,
            "consequence": "no_tenant_isolation",
            "action_required": "verify_platform_scope_only"
        }
    )
    return SessionLocal()


def check_database_connection() -> bool:
    """
    Vérifie que la connexion à PostgreSQL fonctionne.
    Retourne True si OK, False sinon.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("[DB] Vérification connexion base de données — OK")
        return True
    except OperationalError as e:
        logger.error(
            "[DB] Échec connexion base de données — erreur opérationnelle",
            extra={"error": str(e)[:500], "consequence": "db_unavailable"}
        )
        return False
    except SQLAlchemyError as e:
        logger.error(
            "[DB] Échec connexion base de données — erreur SQLAlchemy",
            extra={"error": str(e)[:500], "consequence": "db_unavailable"}
        )
        return False
    except Exception as e:
        logger.exception(
            "[DB] Échec connexion base de données — erreur inattendue",
            extra={"error": str(e)[:500], "consequence": "db_unavailable"}
        )
        return False
