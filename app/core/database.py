"""
AZALS - Connexion PostgreSQL
Gestion securisee de la connexion base de donnees avec SQLAlchemy

IMPORTANT: Ce module exporte la Base depuis app.db pour garantir
l'unicite du registre de metadonnees ORM. NE JAMAIS utiliser
declarative_base() ici.
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.core.config import get_settings

# Configuration du logger
logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug  # Log SQL en mode debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# IMPORTANT: Reutiliser la Base unifiee depuis app.db
# Cette Base inclut UUIDMixin et garantit que TOUS les modeles
# sont enregistres dans le MEME registre de metadonnees.
# NE PAS utiliser declarative_base() ici - cela creerait un registre separe.
from app.db import Base  # noqa: E402


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


def check_database_connection() -> bool:
    """
    Vérifie que la connexion à PostgreSQL fonctionne.
    Retourne True si OK, False sinon.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Connexion à la base de données : OK")
        return True
    except OperationalError as e:
        logger.error(f"Erreur de connexion à la base de données : {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"Erreur SQLAlchemy : {e}")
        return False
    except Exception as e:
        logger.exception(f"Erreur inattendue lors du check DB : {e}")
        return False
