#!/usr/bin/env python3
"""
Script d'exécution manuelle des migrations SQL
Applique les migrations dans l'ordre sur la base de données
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./azals.db")
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def run_migrations():
    """Exécute toutes les migrations SQL dans l'ordre"""
    engine = create_engine(DATABASE_URL)
    
    # Récupérer tous les fichiers .sql triés
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    
    if not migration_files:
        print("❌ Aucune migration trouvée")
        return
    
    print(f"📦 {len(migration_files)} migration(s) trouvée(s)")
    
    with engine.connect() as conn:
        for migration_file in migration_files:
            print(f"\n🔄 Exécution: {migration_file.name}")
            
            try:
                # Lire le contenu du fichier
                sql_content = migration_file.read_text()
                
                # Séparer les commandes SQL (PostgreSQL supporte les transactions)
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                
                for stmt in statements:
                    if stmt:
                        conn.execute(text(stmt))
                
                conn.commit()
                print(f"✅ {migration_file.name} - OK")
                
            except Exception as e:
                print(f"⚠️ {migration_file.name} - Erreur: {e}")
                # Continue avec les autres migrations
                conn.rollback()
    
    print("\n✅ Migrations terminées")

if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)
