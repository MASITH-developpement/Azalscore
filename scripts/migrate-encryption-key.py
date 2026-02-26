#!/usr/bin/env python3
"""
AZALS - Migration de clé de chiffrement
========================================

Ce script migre les données chiffrées de l'ancienne clé vers la nouvelle.

Usage:
    python scripts/migrate-encryption-key.py --old-key "ANCIENNE_CLE" --new-key "NOUVELLE_CLE" --dry-run
    python scripts/migrate-encryption-key.py --old-key "ANCIENNE_CLE" --new-key "NOUVELLE_CLE" --apply

IMPORTANT: Faire un backup de la base de données AVANT d'exécuter ce script!
"""

import argparse
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def migrate_encryption_key(old_key: str, new_key: str, dry_run: bool = True):
    """
    Migre les données chiffrées de l'ancienne clé vers la nouvelle.
    """
    from cryptography.fernet import Fernet, InvalidToken

    # Valider les clés
    try:
        old_fernet = Fernet(old_key.encode())
        new_fernet = Fernet(new_key.encode())
    except Exception as e:
        print(f"[ERREUR] Clés invalides: {e}")
        sys.exit(1)

    print("=" * 60)
    print("AZALS - Migration de clé de chiffrement")
    print("=" * 60)
    print(f"Mode: {'SIMULATION (dry-run)' if dry_run else 'APPLICATION RÉELLE'}")
    print()

    # Configurer l'environnement pour accéder à la DB
    os.environ["ENCRYPTION_KEY"] = old_key
    os.environ.setdefault("ENVIRONMENT", "production")

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    # Récupérer DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Lire depuis .env.production
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.production")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        database_url = line.split("=", 1)[1].strip()
                        break

    if not database_url:
        print("[ERREUR] DATABASE_URL non trouvée")
        sys.exit(1)

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Tables et colonnes contenant des données chiffrées
    # Format: (table, colonne)
    encrypted_columns = [
        ("users", "totp_secret"),           # Secret 2FA
        ("users", "backup_codes"),          # Codes de backup 2FA
        ("api_keys", "key_hash"),           # Clés API (si chiffrées)
        ("tenant_settings", "smtp_password"),  # Mots de passe SMTP tenant
        ("integrations", "credentials"),    # Credentials d'intégrations
    ]

    total_migrated = 0
    total_errors = 0

    for table, column in encrypted_columns:
        print(f"\n[TABLE] {table}.{column}")

        # Vérifier si la table/colonne existe
        try:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL"))
            count = result.scalar()
            print(f"  Enregistrements à migrer: {count}")
        except Exception as e:
            print(f"  [SKIP] Table/colonne n'existe pas: {e}")
            continue

        if count == 0:
            print("  [SKIP] Aucune donnée à migrer")
            continue

        # Récupérer les données
        try:
            result = session.execute(text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL"))
            rows = result.fetchall()
        except Exception as e:
            print(f"  [ERREUR] Lecture impossible: {e}")
            total_errors += 1
            continue

        for row in rows:
            record_id, encrypted_value = row

            if not encrypted_value:
                continue

            try:
                # Déchiffrer avec l'ancienne clé
                if isinstance(encrypted_value, str):
                    encrypted_bytes = encrypted_value.encode()
                else:
                    encrypted_bytes = encrypted_value

                decrypted = old_fernet.decrypt(encrypted_bytes)

                # Rechiffrer avec la nouvelle clé
                new_encrypted = new_fernet.encrypt(decrypted).decode()

                if dry_run:
                    print(f"  [DRY-RUN] ID {record_id}: serait migré")
                else:
                    # Mettre à jour en base
                    session.execute(
                        text(f"UPDATE {table} SET {column} = :new_value WHERE id = :id"),
                        {"new_value": new_encrypted, "id": record_id}
                    )
                    print(f"  [MIGRÉ] ID {record_id}")

                total_migrated += 1

            except InvalidToken:
                print(f"  [SKIP] ID {record_id}: données non chiffrées ou clé incorrecte")
            except Exception as e:
                print(f"  [ERREUR] ID {record_id}: {e}")
                total_errors += 1

    if not dry_run:
        session.commit()

    session.close()

    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Enregistrements migrés: {total_migrated}")
    print(f"Erreurs: {total_errors}")

    if dry_run:
        print()
        print("C'était une SIMULATION. Pour appliquer réellement:")
        print(f"  python {sys.argv[0]} --old-key '...' --new-key '...' --apply")
    else:
        print()
        print("Migration terminée!")
        print("N'oubliez pas de mettre à jour ENCRYPTION_KEY dans .env.production")


def main():
    parser = argparse.ArgumentParser(description="Migration de clé de chiffrement AZALS")
    parser.add_argument("--old-key", required=True, help="Ancienne clé de chiffrement")
    parser.add_argument("--new-key", required=True, help="Nouvelle clé de chiffrement")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans modification")
    parser.add_argument("--apply", action="store_true", help="Appliquer les modifications")

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Erreur: Spécifiez --dry-run ou --apply")
        sys.exit(1)

    if args.dry_run and args.apply:
        print("Erreur: --dry-run et --apply sont mutuellement exclusifs")
        sys.exit(1)

    migrate_encryption_key(args.old_key, args.new_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
