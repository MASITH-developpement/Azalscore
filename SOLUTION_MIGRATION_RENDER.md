# 🚨 SOLUTION - Migration Manuelle Render

## Problème Actuel

Les colonnes `user_id` et `red_triggered` n'existent PAS dans la base PostgreSQL de Render, malgré :
- ✅ Modèle SQLAlchemy mis à jour
- ✅ Migration 005 créée
- ✅ Script run_migrations.py dans build.sh
- ✅ Déploiement réussi

**Cause**: `Base.metadata.create_all()` ne modifie PAS les tables existantes, seulement création initiale.

## Solution Immédiate (Shell Render)

### Option A: Shell Render Dashboard

1. Connectez-vous à https://render.com
2. Sélectionnez le service `azalscore`
3. Cliquez sur "Shell" dans le menu
4. Exécutez:

```bash
python3 run_migrations.py
```

**Sortie attendue**:
```
📦 5 migration(s) trouvée(s)
🔄 Exécution: 001_multi_tenant.sql
⚠️ 001_multi_tenant.sql - Erreur: ... (normal, déjà appliqué)
🔄 Exécution: 002_auth.sql
⚠️ 002_auth.sql - Erreur: ... (normal, déjà appliqué)
🔄 Exécution: 003_journal.sql
⚠️ 003_journal.sql - Erreur: ... (normal, déjà appliqué)
🔄 Exécution: 004_treasury.sql
⚠️ 004_treasury.sql - Erreur: ... (normal, déjà appliqué)
🔄 Exécution: 005_treasury_updates.sql
✅ 005_treasury_updates.sql - OK  ← CECI EST CRITIQUE
✅ Migrations terminées
```

### Option B: SQL Direct via psql

Si vous avez accès au shell Render:

```bash
# Connexion à la DB
psql $DATABASE_URL

-- Vérifier les colonnes actuelles
\d treasury_forecasts

-- Ajouter user_id
ALTER TABLE treasury_forecasts ADD COLUMN user_id INTEGER;

-- Ajouter red_triggered
ALTER TABLE treasury_forecasts ADD COLUMN red_triggered INTEGER DEFAULT 0;

-- Créer l'index
CREATE INDEX idx_treasury_red ON treasury_forecasts(tenant_id, red_triggered);

-- Vérifier
\d treasury_forecasts
```

### Option C: Migration Automatique (non recommandé production)

Modifier [app/main.py](app/main.py) pour forcer l'exécution:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle avec migrations forcées"""
    # ... code existant ...
    
    # TEMPORAIRE: Forcer migrations
    import subprocess
    subprocess.run(["python3", "run_migrations.py"])
    
    yield
```

## Vérification Post-Migration

Après avoir exécuté la migration, testez:

```bash
./test_red_manual.sh
```

**Sortie attendue**:
```
✅ Connecté - Token obtenu
✅ RED DÉCLENCHÉ !
   ID Forecast: 1
   Solde prévisionnel: -8 000€
   RED triggered: true
```

## Commandes de Diagnostic

### Vérifier colonnes en production

Via Shell Render:
```bash
python3 << 'EOF'
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'treasury_forecasts'"))
    columns = [row[0] for row in result.fetchall()]
    print("Colonnes:", columns)
    
    if 'user_id' in columns and 'red_triggered' in columns:
        print("✅ Colonnes présentes")
    else:
        print("❌ Colonnes manquantes")
EOF
```

### Tester l'endpoint après migration

```bash
curl -X POST https://azalscore.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -d '{"email":"admin@azals.fr","password":"azals2026"}' \
  | jq -r '.access_token' > /tmp/token.txt

curl -X POST https://azalscore.onrender.com/treasury/forecast \
  -H "Authorization: Bearer $(cat /tmp/token.txt)" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Content-Type: application/json" \
  -d '{"opening_balance":5000,"inflows":2000,"outflows":15000}' \
  | jq
```

**Attendu**:
```json
{
  "id": 1,
  "opening_balance": 5000,
  "inflows": 2000,
  "outflows": 15000,
  "forecast_balance": -8000,
  "red_triggered": true,
  "created_at": "2026-01-02T..."
}
```

## Migration Réussie - Checklist

- [ ] Shell Render ouvert
- [ ] `python3 run_migrations.py` exécuté
- [ ] Migration 005 affiche "✅ OK" (pas d'erreur)
- [ ] Test `./test_red_manual.sh` retourne status 200
- [ ] Cockpit affiche la zone critique avec trésorerie RED
- [ ] Autres zones sont inactives (opacity 0.4)
- [ ] Bouton "📊 Consulter le rapport RED" visible

## Prochaines Actions

### 1. Exécuter Migration (URGENT)
**Shell Render → `python3 run_migrations.py`**

### 2. Tester RED
```bash
EMAIL="admin@azals.fr" PASSWORD="azals2026" TENANT_ID="tenant-demo" ./test_red_manual.sh
```

### 3. Valider UI
- Accéder à https://azalscore.onrender.com/dashboard
- Vérifier affichage zone critique
- Vérifier zones inactives
- Tester workflow 3 étapes

### 4. Production (optionnel)
Migrer vers Alembic pour gestion automatique:
```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Treasury columns"
alembic upgrade head
```

## Notes Techniques

### Pourquoi Base.metadata.create_all() ne suffit pas?

- `create_all()` exécute uniquement `CREATE TABLE IF NOT EXISTS`
- Ne détecte PAS les différences de colonnes
- Ne modifie PAS les tables existantes
- Solution: Migrations SQL explicites (Alembic, Flyway, ou scripts manuels)

### Pourquoi le build.sh n'a pas fonctionné?

Le script `run_migrations.py` s'exécute MAIS:
- Les migrations 001-004 échouent (tables déjà créées via create_all)
- La migration 005 échoue aussi car elle utilise `ALTER TABLE ... ADD COLUMN`
- Sur PostgreSQL avec tables existantes, besoin de `ADD COLUMN IF NOT EXISTS` ou vérification préalable

### Solution Alternative: Migration Idempotente

Modifier [migrations/005_treasury_updates.sql](migrations/005_treasury_updates.sql):

```sql
-- Version idempotente pour PostgreSQL
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'treasury_forecasts' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE treasury_forecasts ADD COLUMN user_id INTEGER;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'treasury_forecasts' AND column_name = 'red_triggered'
    ) THEN
        ALTER TABLE treasury_forecasts ADD COLUMN red_triggered INTEGER DEFAULT 0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_treasury_red ON treasury_forecasts(tenant_id, red_triggered);
```

## Contacts Render

Si problème d'accès Shell:
- Dashboard: https://render.com
- Documentation Shell: https://render.com/docs/shell
- Support: support@render.com

---

**RÉSUMÉ**: Toute l'intégration est prête côté code. Seule la migration 005 doit être exécutée manuellement sur Render via Shell. 2 commandes suffisent: `python3 run_migrations.py` puis `./test_red_manual.sh`.
