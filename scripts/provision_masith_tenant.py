#!/usr/bin/env python3
"""
AZALS - Provisioning Tenant MASITH
==================================
Script pour créer le tenant administrateur MASITH.

Tenant : MASITH
Email admin : contact@masith.fr
Mot de passe initial : Gobelet2026! (hashé avec bcrypt)
Rôle : SUPER_ADMIN global

Usage:
    python scripts/provision_masith_tenant.py

Ce script doit être exécuté une seule fois lors du déploiement initial.
"""

import os
import sys
import uuid
from datetime import datetime

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def get_database_url():
    """Récupère l'URL de la base de données."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback pour développement local
        url = "postgresql://azals_user:azals_password@localhost:5432/azals"
    return url


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def provision_masith_tenant():
    """Crée le tenant MASITH avec son administrateur."""

    print("=" * 60)
    print("AZALSCORE - Provisioning Tenant MASITH")
    print("=" * 60)

    # Configuration
    TENANT_ID = "masith"
    COMPANY_NAME = "SAS MASITH"
    ADMIN_EMAIL = "contact@masith.fr"
    ADMIN_PASSWORD = "Gobelet2026!"
    ADMIN_NAME = "Administrateur MASITH"

    # Connexion à la base
    database_url = get_database_url()
    print(f"\nConnexion à la base de données...")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Vérifier si le tenant existe déjà
        result = session.execute(text(
            "SELECT tenant_id FROM tenants WHERE tenant_id = :tenant_id"
        ), {"tenant_id": TENANT_ID})

        if result.fetchone():
            print(f"\n⚠️  Le tenant '{TENANT_ID}' existe déjà.")

            # Vérifier si l'admin existe
            result = session.execute(text(
                "SELECT email FROM users WHERE tenant_id = :tenant_id AND email = :email"
            ), {"tenant_id": TENANT_ID, "email": ADMIN_EMAIL})

            if result.fetchone():
                print(f"✓ L'administrateur '{ADMIN_EMAIL}' existe déjà.")
                print("\nAucune action nécessaire.")
                return

        # Créer le tenant
        print(f"\nCréation du tenant '{TENANT_ID}'...")

        session.execute(text("""
            INSERT INTO tenants (
                tenant_id,
                name,
                company_name,
                plan,
                status,
                country,
                timezone,
                language,
                currency,
                is_platform_admin,
                created_at,
                updated_at
            ) VALUES (
                :tenant_id,
                :name,
                :company_name,
                'entreprise',
                'active',
                'FR',
                'Europe/Paris',
                'fr',
                'EUR',
                TRUE,
                NOW(),
                NOW()
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
                is_platform_admin = TRUE,
                status = 'active',
                updated_at = NOW()
        """), {
            "tenant_id": TENANT_ID,
            "name": COMPANY_NAME,
            "company_name": COMPANY_NAME
        })

        print(f"✓ Tenant '{TENANT_ID}' créé/mis à jour")

        # Créer l'utilisateur administrateur
        print(f"\nCréation de l'administrateur '{ADMIN_EMAIL}'...")

        user_id = str(uuid.uuid4())
        password_hash = hash_password(ADMIN_PASSWORD)

        # Supprimer l'ancien utilisateur si existe pour le recréer
        session.execute(text("""
            DELETE FROM users WHERE tenant_id = :tenant_id AND email = :email
        """), {"tenant_id": TENANT_ID, "email": ADMIN_EMAIL})

        session.execute(text("""
            INSERT INTO users (
                id,
                tenant_id,
                email,
                password_hash,
                name,
                role,
                is_active,
                email_verified,
                is_super_admin,
                created_at,
                updated_at
            ) VALUES (
                :id,
                :tenant_id,
                :email,
                :password_hash,
                :name,
                'DIRIGEANT',
                TRUE,
                TRUE,
                TRUE,
                NOW(),
                NOW()
            )
        """), {
            "id": user_id,
            "tenant_id": TENANT_ID,
            "email": ADMIN_EMAIL,
            "password_hash": password_hash,
            "name": ADMIN_NAME
        })

        print(f"✓ Administrateur '{ADMIN_EMAIL}' créé")

        # Activer tous les modules pour MASITH
        print("\nActivation des modules...")

        modules = [
            "commercial", "finance", "accounting", "treasury",
            "hr", "projects", "inventory", "procurement",
            "helpdesk", "quality", "production", "maintenance",
            "field_service", "ecommerce", "subscriptions",
            "stripe_integration", "bi", "automation"
        ]

        for module in modules:
            session.execute(text("""
                INSERT INTO tenant_modules (
                    id, tenant_id, module_code, is_active, activated_at
                ) VALUES (
                    :id, :tenant_id, :module_code, TRUE, NOW()
                )
                ON CONFLICT (tenant_id, module_code) DO UPDATE SET
                    is_active = TRUE,
                    activated_at = NOW()
            """), {
                "id": str(uuid.uuid4()),
                "tenant_id": TENANT_ID,
                "module_code": module
            })

        print(f"✓ {len(modules)} modules activés")

        # Créer la configuration backup
        print("\nConfiguration des sauvegardes...")

        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()

        # Commit final
        session.commit()

        print("\n" + "=" * 60)
        print("✓ PROVISIONING MASITH TERMINÉ AVEC SUCCÈS")
        print("=" * 60)
        print(f"""
Tenant créé:
  - ID: {TENANT_ID}
  - Entreprise: {COMPANY_NAME}
  - Plan: Entreprise (tous les modules)

Administrateur:
  - Email: {ADMIN_EMAIL}
  - Mot de passe: {ADMIN_PASSWORD}
  - Rôle: SUPER_ADMIN (accès total plateforme)

⚠️  IMPORTANT:
  - Changez le mot de passe dès la première connexion
  - Configurez l'authentification 2FA
  - Ce compte a un accès total à tous les tenants

URL de connexion: https://app.azalscore.com/login
""")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERREUR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    provision_masith_tenant()
