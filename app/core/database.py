"""
AZALS - Connexion PostgreSQL
Gestion securisee de la connexion base de donnees avec SQLAlchemy

IMPORTANT: Ce module exporte la Base depuis app.db pour garantir
l'unicite du registre de metadonnees ORM. NE JAMAIS utiliser
declarative_base() ici.
"""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

# Configuration du logger
logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
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
