#!/usr/bin/env python3
"""
AZALS - Script d'initialisation Production
==========================================
Script d'initialisation automatique pour déploiement Railway/OVH/Docker.
Exécuté automatiquement au premier démarrage.

Usage:
    python scripts/deploy/init_production.py

Variables d'environnement requises:
    - DATABASE_URL
    - SECRET_KEY
    - BOOTSTRAP_SECRET
    - ENCRYPTION_KEY (production)
    - CORS_ORIGINS (production)
"""

import os
import sys
import time
import logging

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('init_production')

# Ajouter le chemin racine
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)


def wait_for_database(max_retries: int = 30, delay: int = 2) -> bool:
    """Attend que la base de données soit prête."""
    from sqlalchemy import create_engine, text

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL non définie")
        return False

    logger.info("Attente de la base de données...")

    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Base de données connectée")
            return True
        except Exception as e:
            logger.warning(f"Tentative {attempt + 1}/{max_retries}: {e}")
            time.sleep(delay)

    logger.error("Impossible de se connecter à la base de données")
    return False


def run_migrations():
    """Exécute les migrations Alembic."""
    logger.info("Exécution des migrations...")

    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.warning(f"Alembic: {result.stderr}")
            # Essayer de créer les tables directement
            create_tables_directly()
        else:
            logger.info("Migrations exécutées avec succès")
    except Exception as e:
        logger.warning(f"Erreur migrations: {e}")
        create_tables_directly()


def create_tables_directly():
    """Crée les tables directement si Alembic échoue."""
    logger.info("Création des tables directement...")

    try:
        from app.db import Base
        from app.core.database import engine
        from app.db.model_loader import load_all_models

        # Charger tous les modèles
        load_all_models()

        # Créer les tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except Exception as e:
        logger.error(f"Erreur création tables: {e}")
        raise


def seed_default_data():
    """Initialise les données par défaut."""
    logger.info("Initialisation des données par défaut...")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.environ.get("DATABASE_URL")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Créer les plans commerciaux
        seed_commercial_plans(session)

        # 2. Créer le tenant MASITH si configuré
        if os.environ.get("MASITH_TENANT_ID"):
            seed_masith_tenant(session)

        session.commit()
        logger.info("Données par défaut initialisées")
    except Exception as e:
        session.rollback()
        logger.error(f"Erreur initialisation données: {e}")
    finally:
        session.close()


def seed_commercial_plans(session):
    """Crée les plans commerciaux par défaut."""
    from sqlalchemy import text

    # Vérifier si les plans existent
    result = session.execute(text("SELECT COUNT(*) FROM commercial_plans"))
    if result.scalar() > 0:
        logger.info("Plans commerciaux déjà existants")
        return

    logger.info("Création des plans commerciaux...")

    from app.modules.marketplace.service import MarketplaceService
    service = MarketplaceService(session)
    service.seed_default_plans()
    logger.info("Plans commerciaux créés: Essentiel, Pro, Entreprise")


def seed_masith_tenant(session):
    """Crée le tenant MASITH."""
    from sqlalchemy import text
    import uuid
    import bcrypt

    tenant_id = os.environ.get("MASITH_TENANT_ID", "masith")
    admin_email = os.environ.get("MASITH_ADMIN_EMAIL", "contact@masith.fr")
    admin_password = os.environ.get("MASITH_ADMIN_PASSWORD", "Gobelet2026!")

    # Vérifier si le tenant existe
    result = session.execute(text(
        "SELECT tenant_id FROM tenants WHERE tenant_id = :tenant_id"
    ), {"tenant_id": tenant_id})

    if result.fetchone():
        logger.info(f"Tenant '{tenant_id}' existe déjà")
        return

    logger.info(f"Création du tenant '{tenant_id}'...")

    # Créer le tenant (colonnes selon app/modules/tenants/models.py)
    session.execute(text("""
        INSERT INTO tenants (
            id, tenant_id, name, legal_name, email, plan, status,
            country, timezone, language, currency,
            created_at, updated_at
        ) VALUES (
            gen_random_uuid(), :tenant_id, 'SAS MASITH', 'SAS MASITH', 'contact@masith.fr',
            'ENTREPRISE', 'ACTIVE',
            'FR', 'Europe/Paris', 'fr', 'EUR',
            NOW(), NOW()
        )
        ON CONFLICT (tenant_id) DO NOTHING
    """), {"tenant_id": tenant_id})

    # Créer l'administrateur
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt(rounds=12)).decode()

    session.execute(text("""
        INSERT INTO users (
            id, tenant_id, email, password_hash, name,
            role, is_active, email_verified, is_super_admin,
            created_at, updated_at
        ) VALUES (
            :id, :tenant_id, :email, :password_hash, 'Administrateur MASITH',
            'DIRIGEANT', TRUE, TRUE, TRUE,
            NOW(), NOW()
        )
        ON CONFLICT (tenant_id, email) DO NOTHING
    """), {
        "id": user_id,
        "tenant_id": tenant_id,
        "email": admin_email,
        "password_hash": password_hash
    })

    logger.info(f"Tenant MASITH créé avec admin {admin_email}")


def verify_configuration():
    """Vérifie la configuration production."""
    logger.info("Vérification de la configuration...")

    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    production_vars = ["BOOTSTRAP_SECRET", "ENCRYPTION_KEY", "CORS_ORIGINS"]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        logger.error(f"Variables manquantes: {', '.join(missing)}")
        return False

    # Vérifier les variables production si en mode production
    env = os.environ.get("AZALS_ENV", os.environ.get("ENVIRONMENT", "development"))
    if env == "production":
        for var in production_vars:
            if not os.environ.get(var):
                logger.warning(f"Variable production manquante: {var}")

    logger.info("Configuration vérifiée")
    return True


def main():
    """Point d'entrée principal."""
    logger.info("=" * 60)
    logger.info("AZALSCORE - Initialisation Production")
    logger.info("=" * 60)

    # 1. Vérifier la configuration
    if not verify_configuration():
        sys.exit(1)

    # 2. Attendre la base de données
    if not wait_for_database():
        sys.exit(1)

    # 3. Exécuter les migrations
    run_migrations()

    # 4. Initialiser les données par défaut
    seed_default_data()

    logger.info("=" * 60)
    logger.info("INITIALISATION TERMINÉE AVEC SUCCÈS")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
