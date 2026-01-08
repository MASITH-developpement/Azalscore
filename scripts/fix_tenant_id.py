"""
Script de réparation - Restaure tenant_id dans la table users
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "azals.db")

def fix_tenant_id():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Base non trouvée: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Restaurer tenant_id à 'tenant-demo' pour tous les users qui ont NULL
    cursor.execute("UPDATE users SET tenant_id = 'tenant-demo' WHERE tenant_id IS NULL")
    affected = cursor.rowcount

    # Aussi vérifier les autres tables
    tables_with_tenant = [
        "customers", "customer_contacts", "opportunities",
        "commercial_documents", "document_lines", "payments",
        "customer_activities", "pipeline_stages", "catalog_products"
    ]

    for table in tables_with_tenant:
        try:
            cursor.execute(f"UPDATE {table} SET tenant_id = 'tenant-demo' WHERE tenant_id IS NULL")
            if cursor.rowcount > 0:
                print(f"[FIX] {cursor.rowcount} enregistrements restaurés dans {table}")
                affected += cursor.rowcount
        except sqlite3.Error:
            pass

    conn.commit()
    conn.close()

    if affected > 0:
        print(f"\n[OK] {affected} enregistrement(s) restauré(s) avec tenant_id='tenant-demo'")
    else:
        print("[OK] Aucune restauration nécessaire")

if __name__ == "__main__":
    print("Restauration de tenant_id...")
    fix_tenant_id()
