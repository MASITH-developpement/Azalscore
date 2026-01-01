"""
AZALS - Connexion PostgreSQL
Gestion sécurisée de la connexion base de données avec SQLAlchemy
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.core.config import get_settings

# Configuration du logger
logger = logging.getLogger(__name__)

settings = get_settings()

# Création de l'engine avec connect_args pour PostgreSQL sur Fly.io
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,  # Log SQL en mode debug
    pool_timeout=30,
    pool_recycle=1800,
    connect_args={"connect_timeout": 10}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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
