"""
AZALSCORE - Script de nettoyage de la base de données
======================================================

Ce script nettoie les données corrompues dans la base de données SQLite:
- UUID invalides
- Références orphelines
"""

import os
import sys
import sqlite3
import uuid
import re

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "azals.db")


def is_valid_uuid(value):
    """Vérifie si une valeur est un UUID valide."""
    if value is None:
        return True
    if isinstance(value, uuid.UUID):
        return True
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def cleanup_corrupted_uuids():
    """Nettoie les UUID corrompus dans toutes les tables."""
    if not os.path.exists(DB_PATH):
        print(f"[INFO] Base de données non trouvée: {DB_PATH}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_fixed = 0

    # Récupérer la liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        # Récupérer les colonnes de la table
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        # Identifier les colonnes qui pourraient contenir des UUID (id, *_id, etc.)
        # EXCLURE tenant_id qui est une chaîne de caractères, pas un UUID
        uuid_columns = []
        for col in columns:
            col_name = col[1]
            col_type = col[2].upper() if col[2] else ""
            # Les colonnes UUID sont généralement nommées 'id', '*_id', ou de type VARCHAR(36)
            # MAIS pas tenant_id qui est un identifiant string
            if col_name == 'tenant_id':
                continue  # Skip tenant_id - c'est une chaîne, pas un UUID
            if col_name == 'id' or col_name.endswith('_id') or 'uuid' in col_name.lower():
                uuid_columns.append(col_name)

        if not uuid_columns:
            continue

        # Vérifier chaque ligne pour des UUID invalides
        for col_name in uuid_columns:
            try:
                cursor.execute(f"SELECT rowid, {col_name} FROM {table} WHERE {col_name} IS NOT NULL")
                rows = cursor.fetchall()

                for rowid, value in rows:
                    if not is_valid_uuid(value):
                        # Générer un nouvel UUID pour les colonnes 'id', ou mettre NULL pour les FK
                        if col_name == 'id':
                            new_value = str(uuid.uuid4())
                            print(f"[FIX] {table}.{col_name}: '{value}' -> '{new_value}'")
                            cursor.execute(f"UPDATE {table} SET {col_name} = ? WHERE rowid = ?", (new_value, rowid))
                        else:
                            # Pour les clés étrangères, on met NULL pour éviter les erreurs
                            print(f"[FIX] {table}.{col_name}: '{value}' -> NULL")
                            cursor.execute(f"UPDATE {table} SET {col_name} = NULL WHERE rowid = ?", (rowid,))
                        total_fixed += 1
            except sqlite3.Error as e:
                # Ignorer les erreurs de colonnes qui n'existent pas
                pass

    conn.commit()
    conn.close()

    return total_fixed


def cleanup_orphan_records():
    """Supprime les enregistrements orphelins."""
    if not os.path.exists(DB_PATH):
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_deleted = 0

    # Liste des relations à vérifier (table_enfant, colonne_fk, table_parent)
    relations = [
        ("customer_contacts", "customer_id", "customers"),
        ("opportunities", "customer_id", "customers"),
        ("commercial_documents", "customer_id", "customers"),
        ("document_lines", "document_id", "commercial_documents"),
        ("payments", "document_id", "commercial_documents"),
        ("customer_activities", "customer_id", "customers"),
    ]

    for child_table, fk_column, parent_table in relations:
        try:
            # Trouver les enregistrements orphelins
            query = f"""
                SELECT c.rowid FROM {child_table} c
                LEFT JOIN {parent_table} p ON c.{fk_column} = p.id
                WHERE c.{fk_column} IS NOT NULL AND p.id IS NULL
            """
            cursor.execute(query)
            orphans = cursor.fetchall()

            if orphans:
                print(f"[CLEAN] {len(orphans)} enregistrements orphelins dans {child_table}")
                for (rowid,) in orphans:
                    cursor.execute(f"DELETE FROM {child_table} WHERE rowid = ?", (rowid,))
                    total_deleted += 1
        except sqlite3.Error:
            # Table n'existe peut-être pas encore
            pass

    conn.commit()
    conn.close()

    return total_deleted


def main():
    print("=" * 60)
    print("AZALSCORE - Nettoyage de la base de données")
    print("=" * 60)

    # Nettoyage des UUID corrompus
    print("\n[1/2] Nettoyage des UUID corrompus...")
    fixed = cleanup_corrupted_uuids()
    if fixed > 0:
        print(f"   [OK] {fixed} UUID(s) corrigé(s)")
    else:
        print("   [OK] Aucun UUID corrompu trouvé")

    # Nettoyage des enregistrements orphelins
    print("\n[2/2] Nettoyage des enregistrements orphelins...")
    deleted = cleanup_orphan_records()
    if deleted > 0:
        print(f"   [OK] {deleted} enregistrement(s) orphelin(s) supprimé(s)")
    else:
        print("   [OK] Aucun enregistrement orphelin trouvé")

    print("\n" + "=" * 60)
    print("[OK] Nettoyage terminé")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
