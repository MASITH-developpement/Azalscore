#!/usr/bin/env python3
"""
AZALSCORE - Initialisation Securisee du Compte Createur
========================================================

Ce script crée le premier utilisateur créateur (super-admin) du système.

SÉCURITÉ:
- Aucun mot de passe en clair dans le code
- Utilisation de variables d'environnement ou prompt sécurisé
- Hash fort du mot de passe (bcrypt)
- Journalisation complète de l'opération
- Protection contre la création multiple

USAGE:
    # Via variables d'environnement
    export CREATOR_EMAIL="admin@example.com"
    export CREATOR_PASSWORD="VotreMotDePasseTresSecurise123!"
    export CREATOR_TENANT_ID="votre-tenant-id"
    python init_creator.py

    # Via prompt interactif (plus sécurisé)
    python init_creator.py --interactive

    # Vérifier l'état sans créer
    python init_creator.py --check-only

PRÉREQUIS:
    - DATABASE_URL configuré
    - SECRET_KEY configuré
    - Base de données initialisée (migrations exécutées)
"""

import os
import sys
import json
import hashlib
import getpass
import argparse
import re
from datetime import datetime
from typing import Optional, Tuple

# Configuration du path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports applicatifs (après configuration du path)
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.core.security import get_password_hash
    from app.modules.iam.models import (
        IAMUser, IAMRole, IAMPermission,
        user_roles, role_permissions,
        PermissionAction
    )
    from app.modules.iam.rbac_matrix import (
        STANDARD_ROLES_CONFIG,
        get_legacy_permissions_for_role,
        StandardRole
    )
    from app.core.database import Base
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("   Assurez-vous d'exécuter ce script depuis la racine du projet.")
    sys.exit(1)


# ============================================================================
# CONSTANTES DE SÉCURITÉ
# ============================================================================

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 72  # Limite bcrypt
REQUIRED_PASSWORD_PATTERNS = [
    (r'[A-Z]', "au moins une majuscule"),
    (r'[a-z]', "au moins une minuscule"),
    (r'[0-9]', "au moins un chiffre"),
    (r'[!@#$%^&*(),.?":{}|<>]', "au moins un caractère special")
]

SUPER_ADMIN_ROLE_CONFIG = {
    "code": "super_admin",
    "name": "Super Administrateur",
    "description": "Compte créateur avec accès total au système. Non modifiable via l'UI.",
    "level": 0,
    "is_system": True,
    "is_assignable": False,
    "is_protected": True,
    "is_deletable": False,
    "max_assignments": 1,  # Un seul super_admin par tenant
    "requires_approval": False,
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def print_banner():
    """Affiche la banniere du script."""
    print("\n" + "=" * 60)
    print("  AZALSCORE - Initialisation du Compte Createur")
    print("  Version: 1.0.0 | Securite: HAUTE")
    print("=" * 60 + "\n")


def print_status(message: str, status: str = "INFO"):
    """Affiche un message avec statut."""
    # Utiliser des caracteres ASCII pour compatibilité Windows
    icons = {
        "INFO": "[INFO]",
        "OK": "[OK]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]",
        "SECURE": "[SECURE]"
    }
    try:
        print(f"{icons.get(status, '')} {message}")
    except UnicodeEncodeError:
        # Fallback pour Windows avec encodage limité
        print(f"{icons.get(status, '')} {message.encode('ascii', 'replace').decode()}")


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Valide la robustesse du mot de passe.

    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Le mot de passe ne peut pas etre vide"

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caracteres"

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Le mot de passe ne peut pas depasser {MAX_PASSWORD_LENGTH} caracteres (limite bcrypt)"

    for pattern, description in REQUIRED_PASSWORD_PATTERNS:
        if not re.search(pattern, password):
            return False, f"Le mot de passe doit contenir {description}"

    # Vérifier les patterns dangereux
    weak_patterns = ['password', '123456', 'azerty', 'qwerty', 'admin', 'root']
    password_lower = password.lower()
    for weak in weak_patterns:
        if weak in password_lower:
            return False, f"Le mot de passe contient un pattern faible: '{weak}'"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Valide le format de l'email."""
    if not email:
        return False, "L email ne peut pas etre vide"

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Format d email invalide"

    return True, ""


def compute_checksum(data: dict) -> str:
    """Calcule un checksum SHA-256 pour l'integrite."""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


# ============================================================================
# CLASSE PRINCIPALE
# ============================================================================

class CreatorInitializer:
    """Gère l'initialisation securisee du compte créateur."""

    def __init__(self, interactive: bool = False):
        self.interactive = interactive
        self.settings = get_settings()
        self.engine = None
        self.Session = None

    def connect_database(self) -> bool:
        """Établit la connexion à la base de données."""
        try:
            db_url = self.settings.database_url
            # Conversion pour Render si nécessaire
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)

            self.engine = create_engine(db_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)

            # Test de connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            print_status("Connexion a la base de donnees etablie", "OK")
            return True

        except Exception as e:
            print_status(f"Impossible de se connecter a la base de donnees: {e}", "ERROR")
            return False

    def check_migrations(self) -> bool:
        """Verifie que les migrations necessaires ont ete executees."""
        try:
            db_url = self.settings.database_url
            is_sqlite = db_url.startswith("sqlite")

            with self.engine.connect() as conn:
                if is_sqlite:
                    # SQLite: verifier via sqlite_master
                    result = conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='iam_users'"
                    ))
                    if not result.fetchone():
                        print_status("Table iam_users non trouvee. Executez les migrations.", "ERROR")
                        return False

                    # Verifier la colonne is_protected via PRAGMA
                    result = conn.execute(text("PRAGMA table_info(iam_users)"))
                    columns = [row[1] for row in result.fetchall()]
                    if 'is_protected' not in columns:
                        print_status("Colonne is_protected manquante. Executez: python run_migrations.py", "WARN")
                        # Pour SQLite en dev, on continue quand meme
                        print_status("Mode SQLite detecte - continuation sans migration 028", "INFO")
                else:
                    # PostgreSQL: utiliser information_schema
                    result = conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'iam_users')"
                    ))
                    if not result.scalar():
                        print_status("Table iam_users non trouvee. Executez les migrations.", "ERROR")
                        return False

                    # Verifier la colonne is_protected
                    result = conn.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                        "WHERE table_name = 'iam_users' AND column_name = 'is_protected')"
                    ))
                    if not result.scalar():
                        print_status("Migration 028 non appliquee. Executez: python run_migrations.py", "ERROR")
                        return False

            print_status("Migrations verifiees", "OK")
            return True

        except Exception as e:
            print_status(f"Erreur lors de la verification des migrations: {e}", "ERROR")
            return False

    def get_credentials(self) -> Tuple[str, str, str]:
        """
        Récupère les credentials de manière securisee.

        Returns:
            (email, password, tenant_id)
        """
        if self.interactive:
            print_status("Mode interactif - Saisie securisee des credentials", "SECURE")
            print()

            # Email
            while True:
                email = input("Email du createur: ").strip()
                is_valid, error = validate_email(email)
                if is_valid:
                    break
                print_status(error, "ERROR")

            # Tenant ID
            tenant_id = input("Tenant ID: ").strip()
            if not tenant_id:
                tenant_id = "default-tenant"
                print_status(f"Tenant ID par defaut: {tenant_id}", "WARN")

            # Mot de passe (saisie masquée)
            while True:
                password = getpass.getpass("Mot de passe (min 12 chars, masque): ")
                is_valid, error = validate_password(password)
                if not is_valid:
                    print_status(error, "ERROR")
                    continue

                # Confirmation
                password_confirm = getpass.getpass("Confirmer le mot de passe: ")
                if password != password_confirm:
                    print_status("Les mots de passe ne correspondent pas", "ERROR")
                    continue

                break

            return email, password, tenant_id

        else:
            # Mode non-interactif via variables d'environnement
            email = os.environ.get("CREATOR_EMAIL", "").strip()
            password = os.environ.get("CREATOR_PASSWORD", "").strip()
            tenant_id = os.environ.get("CREATOR_TENANT_ID", "default-tenant").strip()

            if not email:
                print_status("Variable CREATOR_EMAIL non definie", "ERROR")
                sys.exit(1)

            if not password:
                print_status("Variable CREATOR_PASSWORD non definie", "ERROR")
                sys.exit(1)

            # Validation
            is_valid, error = validate_email(email)
            if not is_valid:
                print_status(f"Email invalide: {error}", "ERROR")
                sys.exit(1)

            is_valid, error = validate_password(password)
            if not is_valid:
                print_status(f"Mot de passe invalide: {error}", "ERROR")
                sys.exit(1)

            print_status("Credentials lus depuis les variables d environnement", "OK")
            return email, password, tenant_id

    def check_existing_creator(self, tenant_id: str) -> bool:
        """Vérifie si un créateur existe déjà."""
        session = self.Session()
        try:
            # Vérifier s'il existe un utilisateur avec le rôle super_admin
            result = session.execute(text("""
                SELECT u.email FROM iam_users u
                JOIN iam_user_roles ur ON u.id = ur.user_id
                JOIN iam_roles r ON ur.role_id = r.id
                WHERE u.tenant_id = :tenant_id
                  AND r.code = 'super_admin'
                  AND ur.is_active = TRUE
                  AND u.is_active = TRUE
            """), {"tenant_id": tenant_id})

            existing = result.fetchone()
            if existing:
                print_status(f"Un compte createur existe deja: {existing[0]}", "WARN")
                return True

            return False

        finally:
            session.close()

    def create_super_admin_role(self, session, tenant_id: str) -> int:
        """Cree le role super_admin s'il n'existe pas."""
        # Verifier si le role existe
        result = session.execute(text(
            "SELECT id FROM iam_roles WHERE tenant_id = :tenant_id AND code = 'super_admin'"
        ), {"tenant_id": tenant_id})
        existing = result.fetchone()

        if existing:
            print_status("Role super_admin existant", "INFO")
            return existing[0]

        # Detecter SQLite vs PostgreSQL
        is_sqlite = self.settings.database_url.startswith("sqlite")

        # Creer le role (syntaxe compatible SQLite et PostgreSQL)
        # Pour SQLite, on n'utilise pas les colonnes qui n'existent pas
        if is_sqlite:
            session.execute(text("""
                INSERT INTO iam_roles (
                    tenant_id, code, name, description, level,
                    is_system, is_active, is_assignable, requires_approval, created_at
                ) VALUES (
                    :tenant_id, :code, :name, :description, :level,
                    :is_system, 1, :is_assignable, :requires_approval, CURRENT_TIMESTAMP
                )
            """), {
                "tenant_id": tenant_id,
                "code": SUPER_ADMIN_ROLE_CONFIG["code"],
                "name": SUPER_ADMIN_ROLE_CONFIG["name"],
                "description": SUPER_ADMIN_ROLE_CONFIG["description"],
                "level": SUPER_ADMIN_ROLE_CONFIG["level"],
                "is_system": 1,
                "is_assignable": 0,
                "requires_approval": 0,
            })
            # Recuperer l'ID insere
            result = session.execute(text(
                "SELECT id FROM iam_roles WHERE tenant_id = :tenant_id AND code = 'super_admin'"
            ), {"tenant_id": tenant_id})
            role_id = result.fetchone()[0]
        else:
            result = session.execute(text("""
                INSERT INTO iam_roles (
                    tenant_id, code, name, description, level,
                    is_system, is_active, is_assignable, is_protected, is_deletable,
                    max_assignments, requires_approval, created_at
                ) VALUES (
                    :tenant_id, :code, :name, :description, :level,
                    :is_system, TRUE, :is_assignable, :is_protected, :is_deletable,
                    :max_assignments, :requires_approval, CURRENT_TIMESTAMP
                ) RETURNING id
            """), {
                "tenant_id": tenant_id,
                **SUPER_ADMIN_ROLE_CONFIG
            })
            role_id = result.fetchone()[0]

        print_status(f"Role super_admin cree (ID: {role_id})", "OK")

        # Créer les permissions universelles pour super_admin
        self._create_super_admin_permissions(session, tenant_id, role_id)

        return role_id

    def _create_super_admin_permissions(self, session, tenant_id: str, role_id: int):
        """Cree les permissions universelles pour super_admin."""
        is_sqlite = self.settings.database_url.startswith("sqlite")

        # Permission wildcard (*) pour tout acces
        modules = ['iam', 'admin', 'commercial', 'sales', 'treasury', 'hr',
                   'procurement', 'inventory', 'production', 'quality',
                   'projects', 'bi', 'audit', 'system']

        actions = ['create', 'read', 'update', 'delete', 'validate', 'export', 'admin', '*']

        permission_count = 0
        for module in modules:
            for action in actions:
                code = f"{module}.*.{action}"

                # Verifier si la permission existe
                result = session.execute(text(
                    "SELECT id FROM iam_permissions WHERE tenant_id = :tenant_id AND code = :code"
                ), {"tenant_id": tenant_id, "code": code})

                perm = result.fetchone()
                if perm:
                    perm_id = perm[0]
                else:
                    # Creer la permission
                    if is_sqlite:
                        session.execute(text("""
                            INSERT INTO iam_permissions (
                                tenant_id, code, module, resource, action,
                                name, description, is_system, is_active, is_dangerous, created_at
                            ) VALUES (
                                :tenant_id, :code, :module, '*', :action,
                                :name, :description, 1, 1, :is_dangerous, CURRENT_TIMESTAMP
                            )
                        """), {
                            "tenant_id": tenant_id,
                            "code": code,
                            "module": module,
                            "action": action,
                            "name": f"Acces {action} sur {module}",
                            "description": f"Permission systeme super_admin: {code}",
                            "is_dangerous": 1 if action in ['delete', 'admin', '*'] else 0
                        })
                        result = session.execute(text(
                            "SELECT id FROM iam_permissions WHERE tenant_id = :tenant_id AND code = :code"
                        ), {"tenant_id": tenant_id, "code": code})
                        perm_id = result.fetchone()[0]
                    else:
                        result = session.execute(text("""
                            INSERT INTO iam_permissions (
                                tenant_id, code, module, resource, action,
                                name, description, is_system, is_active, is_dangerous, created_at
                            ) VALUES (
                                :tenant_id, :code, :module, '*', :action,
                                :name, :description, TRUE, TRUE, :is_dangerous, CURRENT_TIMESTAMP
                            ) RETURNING id
                        """), {
                            "tenant_id": tenant_id,
                            "code": code,
                            "module": module,
                            "action": action,
                            "name": f"Acces {action} sur {module}",
                            "description": f"Permission systeme super_admin: {code}",
                            "is_dangerous": action in ['delete', 'admin', '*']
                        })
                        perm_id = result.fetchone()[0]

                # Associer au role (verifier d'abord si existe pour SQLite)
                existing = session.execute(text(
                    "SELECT id FROM iam_role_permissions WHERE tenant_id = :tenant_id AND role_id = :role_id AND permission_id = :permission_id"
                ), {"tenant_id": tenant_id, "role_id": role_id, "permission_id": perm_id}).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO iam_role_permissions (tenant_id, role_id, permission_id, granted_at)
                        VALUES (:tenant_id, :role_id, :permission_id, CURRENT_TIMESTAMP)
                    """), {
                        "tenant_id": tenant_id,
                        "role_id": role_id,
                        "permission_id": perm_id
                    })
                permission_count += 1

        print_status(f"{permission_count} permissions associees au role super_admin", "OK")

    def create_creator_user(
        self,
        session,
        tenant_id: str,
        email: str,
        password_hash: str,
        role_id: int
    ) -> int:
        """Cree l'utilisateur createur."""
        is_sqlite = self.settings.database_url.startswith("sqlite")

        # Creer l'utilisateur
        if is_sqlite:
            # SQLite: colonnes de base seulement (sans is_system_account, is_protected, created_via)
            session.execute(text("""
                INSERT INTO iam_users (
                    tenant_id, email, password_hash,
                    first_name, last_name, display_name,
                    is_active, is_verified, is_locked,
                    locale, timezone,
                    password_changed_at, created_at, updated_at
                ) VALUES (
                    :tenant_id, :email, :password_hash,
                    'Createur', 'Systeme', 'Createur Systeme',
                    1, 1, 0,
                    'fr', 'Europe/Paris',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "tenant_id": tenant_id,
                "email": email,
                "password_hash": password_hash
            })
            result = session.execute(text(
                "SELECT id FROM iam_users WHERE tenant_id = :tenant_id AND email = :email"
            ), {"tenant_id": tenant_id, "email": email})
            user_id = result.fetchone()[0]
        else:
            result = session.execute(text("""
                INSERT INTO iam_users (
                    tenant_id, email, password_hash,
                    first_name, last_name, display_name,
                    is_active, is_verified, is_locked,
                    is_system_account, is_protected, created_via,
                    locale, timezone,
                    password_changed_at, created_at, updated_at
                ) VALUES (
                    :tenant_id, :email, :password_hash,
                    'Createur', 'Systeme', 'Createur Systeme',
                    TRUE, TRUE, FALSE,
                    TRUE, TRUE, 'cli',
                    'fr', 'Europe/Paris',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING id
            """), {
                "tenant_id": tenant_id,
                "email": email,
                "password_hash": password_hash
            })
            user_id = result.fetchone()[0]

        print_status(f"Utilisateur createur cree (ID: {user_id})", "OK")

        # Associer le role
        is_sqlite = self.settings.database_url.startswith("sqlite")
        session.execute(text("""
            INSERT INTO iam_user_roles (tenant_id, user_id, role_id, granted_at, is_active)
            VALUES (:tenant_id, :user_id, :role_id, CURRENT_TIMESTAMP, :is_active)
        """), {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role_id": role_id,
            "is_active": 1 if is_sqlite else True
        })

        print_status("Role super_admin attribue au createur", "OK")
        return user_id

    def log_initialization(
        self,
        session,
        tenant_id: str,
        user_id: int,
        role_id: int,
        email: str
    ):
        """Journalise l'operation d'initialisation."""
        is_sqlite = self.settings.database_url.startswith("sqlite")

        details = {
            "email": email,
            "role_id": role_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": sys.version,
        }

        checksum = compute_checksum(details)

        # Pour SQLite, on skip les tables qui n'existent peut-etre pas
        if is_sqlite:
            print_status("Mode SQLite - journalisation simplifiee", "INFO")
            # Log dans iam_audit_logs seulement si la table existe
            try:
                session.execute(text("""
                    INSERT INTO iam_audit_logs (
                        tenant_id, action, entity_type, entity_id,
                        actor_id, details, success, created_at
                    ) VALUES (
                        :tenant_id, 'SYSTEM_INIT', 'USER', :user_id,
                        NULL, :details, 1, CURRENT_TIMESTAMP
                    )
                """), {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "details": json.dumps({
                        "operation": "CREATOR_INIT",
                        "email": email,
                        "role": "super_admin"
                    })
                })
            except Exception:
                print_status("Table iam_audit_logs non disponible - skip", "WARN")
        else:
            # PostgreSQL: log complet
            session.execute(text("""
                INSERT INTO iam_system_init_log (
                    tenant_id, operation, entity_type, entity_id, entity_code,
                    executed_by, execution_mode, details, justification, checksum, created_at
                ) VALUES (
                    :tenant_id, 'CREATOR_INIT', 'USER', :user_id, :email,
                    'bootstrap', 'cli', :details, :justification, :checksum, CURRENT_TIMESTAMP
                )
            """), {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "email": email,
                "details": json.dumps(details),
                "justification": "Creation du compte fondateur lors de l initialisation systeme",
                "checksum": checksum
            })

            # Log dans iam_audit_logs aussi
            session.execute(text("""
                INSERT INTO iam_audit_logs (
                    tenant_id, action, entity_type, entity_id,
                    actor_id, details, success, created_at
                ) VALUES (
                    :tenant_id, 'SYSTEM_INIT', 'USER', :user_id,
                    NULL, :details, TRUE, CURRENT_TIMESTAMP
                )
            """), {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "details": json.dumps({
                    "operation": "CREATOR_INIT",
                    "email": email,
                    "role": "super_admin"
                })
            })

        print_status("Operation journalisee dans le registre de securite", "SECURE")

    def run(self, check_only: bool = False) -> bool:
        """Exécute l'initialisation."""
        print_banner()

        # 1. Connexion à la base de données
        if not self.connect_database():
            return False

        # 2. Vérifier les migrations
        if not self.check_migrations():
            return False

        # 3. Récupérer les credentials
        email, password, tenant_id = self.get_credentials()

        print()
        print_status(f"Tenant: {tenant_id}", "INFO")
        print_status(f"Email: {email}", "INFO")
        print()

        # 4. Vérifier si un créateur existe déjà
        if self.check_existing_creator(tenant_id):
            if not check_only:
                print_status("Initialisation annulee - un createur existe deja", "WARN")
            return False

        if check_only:
            print_status("Verification terminee - aucun createur existant", "OK")
            print_status("Vous pouvez exécuter le script sans --check-only pour créer le compte", "INFO")
            return True

        # 5. Confirmation finale
        if self.interactive:
            confirm = input("\n[CONFIRM] Confirmer la creation du compte createur? (oui/non): ").strip().lower()
            if confirm != "oui":
                print_status("Operation annulee par l utilisateur", "WARN")
                return False

        # 6. Creation
        session = self.Session()
        try:
            print()
            print_status("Debut de l initialisation...", "INFO")

            # Hash du mot de passe
            print_status("Hashage du mot de passe (bcrypt)...", "SECURE")
            password_hash = get_password_hash(password)

            # Creer le role
            role_id = self.create_super_admin_role(session, tenant_id)

            # Creer l'utilisateur
            user_id = self.create_creator_user(
                session, tenant_id, email, password_hash, role_id
            )

            # Journaliser
            self.log_initialization(session, tenant_id, user_id, role_id, email)

            # Commit
            session.commit()

            print()
            print("=" * 60)
            print_status("INITIALISATION REUSSIE", "OK")
            print("=" * 60)
            print()
            print(f"   Email: {email}")
            print(f"   Tenant: {tenant_id}")
            print(f"   User ID: {user_id}")
            print(f"   Role: super_admin")
            print(f"   MFA: Activable par la suite")
            print()
            print_status("Vous pouvez maintenant vous connecter via l API", "INFO")
            print_status("POST /v1/iam/auth/login", "INFO")
            print()

            # Nettoyage securise
            del password
            del password_hash

            return True

        except Exception as e:
            session.rollback()
            print_status(f"Erreur lors de l initialisation: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

        finally:
            session.close()


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Initialisation securisee du compte créateur AZALSCORE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Mode interactif avec saisie securisee des credentials"
    )

    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="Vérifier l'état sans créer le compte"
    )

    args = parser.parse_args()

    initializer = CreatorInitializer(interactive=args.interactive)
    success = initializer.run(check_only=args.check_only)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
