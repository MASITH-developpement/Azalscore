# AZALS - UUID Migration Checklist

## Statut Final: CONFORME

**Date de vérification**: 2026-01-10
**Version**: 1.0.0

---

## Résumé de l'Audit

| Métrique | Valeur |
|----------|--------|
| Fichiers analysés | 234 |
| Classes ORM | 392 |
| Colonnes analysées | 7949 |
| Clés primaires | 392 |
| Clés étrangères | 361 |
| Classes conformes | 392 |
| Classes NON conformes | 0 |
| **ERREURS CRITIQUES** | **0** |

---

## Architecture UUID

### Type Universel: `UniversalUUID`

```python
# Localisation: app/core/types.py
from app.core.types import UniversalUUID

class UniversalUUID(TypeDecorator):
    """
    Type UUID universel compatible PostgreSQL et SQLite.
    - PostgreSQL: Utilise le type UUID natif
    - SQLite: Stocke comme String(36)
    """
    impl = String(36)
```

### Pattern Standard pour PK

```python
from app.core.types import UniversalUUID
import uuid

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(UniversalUUID(), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
```

### Pattern Standard pour FK

```python
parent_id = Column(UniversalUUID(), ForeignKey("parent_table.id"), nullable=False)
```

---

## Outils de Vérification

### 1. Script d'Audit ORM

```bash
# Audit complet
python scripts/audit_orm_ids.py

# Export rapport texte
python scripts/audit_orm_ids.py --output rapport.txt

# Export rapport JSON
python scripts/audit_orm_ids.py --json --output rapport.json
```

### 2. Script de Correction Automatique

```bash
# Simulation (dry-run)
python scripts/fix_orm_ids.py --dry-run

# Correction avec backup
python scripts/fix_orm_ids.py --backup

# Correction forcée
python scripts/fix_orm_ids.py --force
```

### 3. Validateur Anti-Régression

Le validateur est intégré au démarrage de l'application (`app/core/schema_validator.py`).

**Comportement**:
- Détecte les tables PostgreSQL avec PK/FK BIGINT
- Détecte les modèles ORM avec Integer/BigInteger
- **BLOQUE le démarrage** en mode strict si violation détectée

---

## Procédure de Déploiement

### Environnement DEV/TEST

```sql
-- 1. Réinitialisation complète
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- 2. Recréer les extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

```bash
# 3. Redémarrer l'application
python -m app.main
```

### Environnement PRODUCTION

1. **Backup** complet de la base
2. Exécuter le script de nettoyage:
   ```bash
   psql -d azalscore -f scripts/force_cleanup_bigint_tables.sql
   ```
3. Redémarrer l'application

---

## Logs Attendus au Démarrage

```
[STARTUP] Activation extensions pgcrypto, uuid-ossp
[CLEANUP] 0 table(s) BIGINT détectée(s)
[SCHEMA] Validation du schéma PostgreSQL...
[SCHEMA] ORM: 392 tables, 392 PK, 361 FK vérifiées
[SCHEMA] Validation réussie - Schéma conforme UUID
Application startup complete
```

---

## Points de Vigilance

### INTERDICTIONS ABSOLUES

1. **JAMAIS** utiliser `Integer` ou `BigInteger` pour:
   - Colonnes `id`
   - Colonnes `*_id` (foreign keys)
   - Colonnes de référence entre tables

2. **JAMAIS** utiliser:
   - `autoincrement=True` sur colonnes id
   - `Sequence(...)` pour les identifiants
   - `server_default` avec séquence PostgreSQL

### COLONNES AUTORISÉES EN INTEGER

Les colonnes suivantes peuvent légitimement utiliser `Integer`:

- Compteurs: `count`, `quantity`, `total_*`
- Dates partielles: `year`, `month`, `day`, `day_of_week`
- Durées: `estimated_minutes`, `duration_seconds`
- Métriques: `retry_count`, `version`, `priority`
- Indicateurs: `is_active`, `is_validated`, `level`

---

## Validation Finale

### Test de Conformité

```bash
# 1. Audit ORM
python scripts/audit_orm_ids.py

# Attendu: ERREURS CRITIQUES: 0

# 2. Test démarrage sur base vide
dropdb azalscore_test && createdb azalscore_test
DATABASE_URL=postgresql://user:pass@localhost/azalscore_test python -c "
from app.core.database import engine, Base
from app.core.schema_validator import validate_schema_on_startup

# Import all models
from app.core.models import *
from app.modules.inventory.models import *
# ... autres modules

Base.metadata.create_all(bind=engine)
validate_schema_on_startup(engine, Base, strict=True)
print('OK - Schéma conforme')
"
```

### Critères de Succès

- [ ] `scripts/audit_orm_ids.py` : 0 erreur
- [ ] Démarrage application : pas de SchemaValidationError
- [ ] Logs : "Schéma conforme UUID"
- [ ] PostgreSQL : aucune table avec PK int4/int8

---

## Historique des Corrections

| Date | Commit | Description |
|------|--------|-------------|
| 2026-01-10 | 48d28b9 | Cleanup automatique BIGINT au démarrage |
| 2026-01-10 | ff7d71d | Validateur anti-régression BIGINT |
| 2026-01-10 | 6f513b3 | Validation schéma UUID |
| 2026-01-10 | 89f9783 | Corrections APScheduler et modèles |

---

## Support

En cas de problème:

1. Vérifier les logs de démarrage
2. Exécuter `python scripts/audit_orm_ids.py`
3. Consulter le rapport généré
4. Appliquer les corrections avec `scripts/fix_orm_ids.py`
