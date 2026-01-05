#!/usr/bin/env python3
"""
Script d'exécution manuelle des migrations SQL
Applique les migrations dans l'ordre sur la base de données
Avec gestion des dépendances de clés étrangères (2 passes)
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Configuration - Support DATABASE_URL pour PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./azals.db"
    print("⚠️  DATABASE_URL non définie, utilisation SQLite local")
else:
    # PostgreSQL sur Render utilise postgres:// qu'il faut convertir en postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print("✅ Conversion postgres:// → postgresql://")

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def is_dependency_error(error_msg: str) -> bool:
    """Vérifie si l'erreur est due à une dépendance de clé étrangère"""
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in [
        'foreign key',
        'does not exist',
        'relation',
        'references',
        'violates foreign key',
        'constraint'
    ])


def run_migrations():
    """Exécute toutes les migrations SQL dans l'ordre avec 2 passes pour les FK"""
    print(f"🔗 Database: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)

    # Récupérer tous les fichiers .sql triés
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        print("❌ Aucune migration trouvée")
        return

    print(f"📦 {len(migration_files)} migration(s) trouvée(s)")

    # Première passe
    failed_migrations = []
    succeeded = 0

    with engine.connect() as conn:
        for migration_file in migration_files:
            print(f"\n🔄 [Pass 1] {migration_file.name}")

            try:
                sql_content = migration_file.read_text()
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]

                for stmt in statements:
                    if stmt and not stmt.startswith('--'):
                        conn.execute(text(stmt))

                conn.commit()
                print(f"✅ {migration_file.name} - OK")
                succeeded += 1

            except Exception as e:
                error_str = str(e)
                conn.rollback()

                # Ignorer les erreurs "already exists"
                if 'already exists' in error_str.lower() or 'duplicate' in error_str.lower():
                    print(f"⏭️  {migration_file.name} - Déjà appliquée")
                    succeeded += 1
                elif is_dependency_error(error_str):
                    print(f"⏳ {migration_file.name} - Dépendance, retry en pass 2")
                    failed_migrations.append((migration_file, error_str))
                else:
                    print(f"⚠️  {migration_file.name} - Erreur: {e}")
                    failed_migrations.append((migration_file, error_str))

    # Deuxième passe pour les migrations avec dépendances
    if failed_migrations:
        print(f"\n🔄 Deuxième passe pour {len(failed_migrations)} migration(s)...")

        with engine.connect() as conn:
            for migration_file, prev_error in failed_migrations:
                print(f"\n🔄 [Pass 2] {migration_file.name}")

                try:
                    sql_content = migration_file.read_text()
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

                    for stmt in statements:
                        if stmt and not stmt.startswith('--'):
                            try:
                                conn.execute(text(stmt))
                            except Exception as stmt_error:
                                # Ignorer les erreurs "already exists" au niveau statement
                                if 'already exists' not in str(stmt_error).lower():
                                    raise

                    conn.commit()
                    print(f"✅ {migration_file.name} - OK (pass 2)")
                    succeeded += 1

                except Exception as e:
                    conn.rollback()
                    error_str = str(e).lower()

                    if 'already exists' in error_str or 'duplicate' in error_str:
                        print(f"⏭️  {migration_file.name} - Déjà appliquée")
                        succeeded += 1
                    else:
                        print(f"❌ {migration_file.name} - Échec final: {e}")

    print(f"\n✅ Migrations terminées ({succeeded}/{len(migration_files)} réussies)")


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)
