#!/usr/bin/env python3
"""
AZALS - Script de correction du mot de passe admin
===================================================

Usage:
    python scripts/fix_admin_password.py

Ce script:
1. Vérifie la connexion à la base de données
2. Crée ou met à jour l'utilisateur admin avec un hash bcrypt valide
3. Affiche les informations de connexion
"""

import os
import sys
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import bcrypt

def get_password_hash(password: str) -> str:
    """Generate a valid bcrypt hash."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def main():
    print("=" * 60)
    print("AZALS - Correction du mot de passe admin")
    print("=" * 60)

    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("\n[ERREUR] DATABASE_URL non définie!")
        print("Assurez-vous que le fichier .env est configuré.")
        print("\nAlternative: définir manuellement:")
        print("  export DATABASE_URL=postgresql://azals_user:VOTRE_MOT_DE_PASSE@localhost:5432/azals")
        sys.exit(1)

    print(f"\nDATABASE_URL: {database_url[:50]}...")

    # Configuration admin
    admin_email = "admin@azals.local"
    admin_password = "admin123"
    tenant_id = "default"

    # Generate valid bcrypt hash
    password_hash = get_password_hash(admin_password)

    print(f"\nConfiguration:")
    print(f"  Email: {admin_email}")
    print(f"  Password: {admin_password}")
    print(f"  Tenant ID: {tenant_id}")
    print(f"  Hash: {password_hash}")

    # Verify the hash works
    verify_result = bcrypt.checkpw(
        admin_password.encode('utf-8'),
        password_hash.encode('utf-8')
    )
    print(f"  Hash verification: {verify_result}")

    if not verify_result:
        print("\n[ERREUR] Le hash généré est invalide!")
        sys.exit(1)

    # Connect to database
    try:
        import psycopg2
        from urllib.parse import urlparse

        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/') or "azals"
        )
        conn.autocommit = False
        cursor = conn.cursor()

        print("\n[OK] Connexion à PostgreSQL réussie")

        # Check if user exists
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (admin_email,)
        )
        existing = cursor.fetchone()

        if existing:
            print(f"\n[INFO] Utilisateur existant trouvé (ID: {existing[0]})")
            print(f"  Hash actuel: {existing[2][:30]}...")

            # Update the user
            cursor.execute("""
                UPDATE users SET
                    password_hash = %s,
                    is_active = 1,
                    totp_enabled = 0,
                    must_change_password = 0,
                    updated_at = %s
                WHERE email = %s
            """, (password_hash, datetime.utcnow(), admin_email))

            print("[OK] Mot de passe mis à jour!")

        else:
            print("\n[INFO] Aucun utilisateur trouvé, création...")

            # Generate UUID
            user_id = str(uuid.uuid4())

            # Insert new user
            cursor.execute("""
                INSERT INTO users (
                    id, tenant_id, email, password_hash, role,
                    is_active, totp_enabled, must_change_password,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
            """, (
                user_id, tenant_id, admin_email, password_hash, "DIRIGEANT",
                1, 0, 0,
                datetime.utcnow(), datetime.utcnow()
            ))

            print(f"[OK] Utilisateur créé avec ID: {user_id}")

        conn.commit()
        print("\n[OK] Transaction validée!")

        # Verify the update
        cursor.execute(
            "SELECT id, email, password_hash, is_active, role FROM users WHERE email = %s",
            (admin_email,)
        )
        user = cursor.fetchone()
        if user:
            print(f"\n[VÉRIFICATION] Utilisateur en base:")
            print(f"  ID: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Hash: {user[2][:30]}...")
            print(f"  Actif: {user[3]}")
            print(f"  Rôle: {user[4]}")

            # Final verification
            verify = bcrypt.checkpw(
                admin_password.encode('utf-8'),
                user[2].encode('utf-8')
            )
            print(f"  Vérification finale: {verify}")

            if verify:
                print("\n" + "=" * 60)
                print("SUCCÈS! Vous pouvez maintenant vous connecter avec:")
                print(f"  Email: {admin_email}")
                print(f"  Mot de passe: {admin_password}")
                print("=" * 60)
            else:
                print("\n[ERREUR] La vérification finale a échoué!")

        cursor.close()
        conn.close()

    except ImportError:
        print("\n[ERREUR] psycopg2 non installé!")
        print("Installer avec: pip install psycopg2-binary")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
