# AZALSCORE - RAPPORT DE NON-CONFORMITÉ
## MODULE: SOCLE TECHNIQUE (T0-CORE)

**Date d'évaluation**: 2026-01-08
**Version analysée**: 1.0-BETA
**Statut**: ❌ FAIL
**Phase**: 1 - Socle Technique Industriel

---

## 1. RÉSUMÉ EXÉCUTIF

### Pourquoi le module échoue

Le module SOCLE TECHNIQUE **ne peut pas être validé PASS** en raison de **3 manquements critiques de sécurité** :

1. **Chiffrement AES-256 au repos NON IMPLÉMENTÉ** - Les données sensibles sont stockées en clair
2. **Hash chaîné du journal d'audit NON IMPLÉMENTÉ** - L'intégrité n'est pas prouvable cryptographiquement
3. **Tests d'isolation inter-tenant INSUFFISANTS** - Pas de preuve d'absence de fuite de données

### Impact

| Critère | Impact |
|---------|--------|
| **Sécurité** | CRITIQUE - Données sensibles exposées en cas de compromission DB |
| **Conformité** | BLOQUANT - Non conforme RGPD/CNIL pour données sensibles |
| **Exploitation** | MAJEUR - Pas de garantie d'intégrité des logs d'audit |
| **Commercial** | BLOQUANT - ERP non vendable légalement en l'état |

---

## 2. LISTE PRÉCISE DES CRITÈRES EN FAIL

| # | Critère | Statut | Gravité | Détail |
|---|---------|--------|---------|--------|
| 1 | Chiffrement AES-256 au repos | ❌ FAIL | **BLOQUANT** | Aucun chiffrement des données sensibles |
| 2 | TLS en transit | ⚠️ PARTIEL | Majeur | Dépend du déploiement, pas forcé par l'app |
| 3 | Clés hors code | ✅ PASS | - | Variables d'environnement utilisées |
| 4 | Rotation de clés | ❌ FAIL | Majeur | Non implémenté |
| 5 | Hash chaîné journal audit | ❌ FAIL | **BLOQUANT** | Pas de chaînage cryptographique |
| 6 | Tests injection SQL | ⚠️ PARTIEL | Majeur | Tests présents mais couverture incomplète |
| 7 | Tests élévation privilèges | ⚠️ PARTIEL | Majeur | RBAC testé mais pas tous les scénarios |
| 8 | Tests accès inter-tenant | ❌ FAIL | **BLOQUANT** | Pas de tests de fuite cross-tenant |
| 9 | CORS production | ⚠️ PARTIEL | Majeur | Défaut allow_origins=["*"] |
| 10 | Session révocation | ❌ FAIL | Majeur | JWT stateless, pas de blacklist |

---

## 3. CAUSES TECHNIQUES IDENTIFIÉES

### 3.1 Chiffrement AES-256 (BLOQUANT)

**Fichiers concernés** :
- `app/core/security.py` - Ne contient que le hash bcrypt
- `app/core/database.py` - Pas de chiffrement transparent

**Analyse** :
```python
# ACTUEL dans app/core/security.py
def get_password_hash(password: str) -> str:
    # Hash bcrypt uniquement pour mots de passe
    return bcrypt.hashpw(...)

# MANQUANT : Chiffrement des colonnes sensibles
# - Emails personnels
# - Numéros de téléphone
# - Données bancaires
# - Secrets TOTP
```

**Preuve** :
```bash
grep -r "AES\|encrypt\|Fernet\|cryptography" app/core/
# Résultat: Aucune correspondance dans le core
```

### 3.2 Hash Chaîné Journal Audit (BLOQUANT)

**Fichier concerné** : `migrations/003_journal.sql`

**Analyse** :
Le journal a des triggers empêchant UPDATE/DELETE (bien), mais **aucun hash chaîné** ne garantit l'intégrité :

```sql
-- ACTUEL
CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MANQUANT
-- previous_hash VARCHAR(64) NOT NULL,
-- entry_hash VARCHAR(64) NOT NULL,
```

**Impact** : Un accès admin à la DB peut insérer des entrées falsifiées sans détection.

### 3.3 Tests Inter-Tenant (BLOQUANT)

**Fichier concerné** : `tests/test_multi_tenant.py`

**Analyse** :
Les tests vérifient le fonctionnement nominal mais **pas les tentatives de fuite** :

```python
# MANQUANT : Tests de tentative d'accès cross-tenant
def test_tenant_a_cannot_access_tenant_b_data():
    """Un utilisateur tenant A ne peut PAS voir les données tenant B."""
    # Créer données tenant B
    # Se connecter en tant que tenant A
    # Tenter d'accéder aux données tenant B
    # Vérifier 403 ou liste vide
```

### 3.4 CORS Non Restrictif (MAJEUR)

**Fichier concerné** : `app/core/security_middleware.py:23-35`

```python
# ACTUEL
def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # DANGEREUX en production
        ...
    )
```

**Impact** : Vulnérable aux attaques CSRF depuis n'importe quel domaine.

### 3.5 Révocation de Session (MAJEUR)

**Analyse** :
JWT stateless sans mécanisme de blacklist. Si un token est compromis, il reste valide jusqu'à expiration (30 min).

**Fichiers** : `app/core/security.py`, `app/api/auth.py`

---

## 4. CORRECTIONS NÉCESSAIRES

### 4.1 Implémenter Chiffrement AES-256 (BLOQUANT)

**Priorité** : CRITIQUE - À faire IMMÉDIATEMENT

**Actions** :
1. Créer `app/core/encryption.py` avec classe `FieldEncryption`
2. Utiliser `cryptography.fernet` ou `pycryptodome`
3. Clé de chiffrement dans variable d'environnement `ENCRYPTION_KEY`
4. Types SQLAlchemy personnalisés pour colonnes chiffrées

**Fichiers à créer** :
- `app/core/encryption.py`

**Fichiers à modifier** :
- `app/core/config.py` - Ajouter `encryption_key`
- `app/core/models.py` - Utiliser types chiffrés
- `migrations/030_add_encryption.sql` - Migration données

**Code suggéré** :
```python
# app/core/encryption.py
from cryptography.fernet import Fernet
from app.core.config import get_settings

class FieldEncryption:
    def __init__(self):
        settings = get_settings()
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY required")
        self.cipher = Fernet(settings.encryption_key.encode())

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### 4.2 Implémenter Hash Chaîné Audit (BLOQUANT)

**Priorité** : CRITIQUE

**Actions** :
1. Ajouter colonnes `previous_hash` et `entry_hash` au journal
2. Calculer hash SHA-256 de chaque entrée
3. Inclure le hash précédent dans le calcul
4. Créer endpoint de vérification d'intégrité

**Fichiers à modifier** :
- `migrations/003_journal.sql` → Nouvelle migration
- `app/core/models.py` - Ajouter colonnes
- `app/api/audit.py` - Endpoint vérification

**Migration SQL** :
```sql
-- migrations/031_audit_hash_chain.sql
ALTER TABLE journal_entries ADD COLUMN previous_hash VARCHAR(64);
ALTER TABLE journal_entries ADD COLUMN entry_hash VARCHAR(64) NOT NULL;

-- Trigger pour calculer le hash automatiquement
CREATE OR REPLACE FUNCTION calculate_journal_hash()
RETURNS TRIGGER AS $$
DECLARE
    prev_hash VARCHAR(64);
    hash_input TEXT;
BEGIN
    SELECT entry_hash INTO prev_hash
    FROM journal_entries
    WHERE tenant_id = NEW.tenant_id
    ORDER BY id DESC LIMIT 1;

    IF prev_hash IS NULL THEN
        prev_hash := 'GENESIS';
    END IF;

    NEW.previous_hash := prev_hash;
    hash_input := CONCAT(NEW.tenant_id, NEW.user_id, NEW.action,
                         NEW.details, NEW.created_at, prev_hash);
    NEW.entry_hash := encode(sha256(hash_input::bytea), 'hex');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_hash
BEFORE INSERT ON journal_entries
FOR EACH ROW EXECUTE FUNCTION calculate_journal_hash();
```

### 4.3 Ajouter Tests Inter-Tenant (BLOQUANT)

**Priorité** : CRITIQUE

**Fichier à modifier** : `tests/test_multi_tenant.py`

**Tests à ajouter** :
```python
def test_tenant_isolation_api_level():
    """Test: API refuse accès cross-tenant."""
    # 1. Créer user et item dans tenant-A
    # 2. Créer user dans tenant-B
    # 3. Se connecter tenant-B
    # 4. Tenter GET /items avec X-Tenant-ID: tenant-B
    # 5. Vérifier: liste vide ou 403

def test_tenant_isolation_jwt_mismatch():
    """Test: JWT tenant-A + header tenant-B = 403."""
    # 1. Login tenant-A → JWT
    # 2. Requête avec JWT + header X-Tenant-ID: tenant-B
    # 3. Vérifier 403 "Tenant ID mismatch"

def test_tenant_isolation_db_query():
    """Test: Requête DB ne retourne jamais données autre tenant."""
    # 1. Insérer données tenant-A et tenant-B
    # 2. Requête filtrée tenant-A
    # 3. Vérifier AUCUNE donnée tenant-B
```

### 4.4 Configurer CORS Production (MAJEUR)

**Fichier à modifier** : `app/core/security_middleware.py`

**Correction** :
```python
def setup_cors(app: FastAPI) -> None:
    settings = get_settings()

    if settings.is_production:
        if not settings.cors_origins:
            raise ValueError("CORS_ORIGINS required in production")
        origins = [o.strip() for o in settings.cors_origins.split(",")]
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.is_production,  # True en prod
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        max_age=3600,
    )
```

### 4.5 Implémenter Token Blacklist (MAJEUR)

**Actions** :
1. Créer table `token_blacklist`
2. Ajouter middleware de vérification
3. Endpoint `/auth/logout` qui blacklist le token

**Fichiers** :
- `migrations/032_token_blacklist.sql`
- `app/core/token_blacklist.py`
- Modifier `app/core/dependencies.py`

---

## 5. CONDITIONS DE REVALIDATION

### 5.1 Critères PASS Obligatoires

Pour que le module SOCLE TECHNIQUE passe en PASS, **TOUS** ces critères doivent être validés :

| # | Critère | Test de validation |
|---|---------|-------------------|
| 1 | Chiffrement AES-256 | Lire une colonne chiffrée en DB → illisible |
| 2 | Hash chaîné audit | Modifier une entrée manuellement → hash invalide détecté |
| 3 | Tests inter-tenant | 100% des tests cross-tenant passent |
| 4 | CORS production | Requête origin non autorisé → bloquée |
| 5 | Token blacklist | Token logout → requête suivante 401 |

### 5.2 Tests à Exécuter

```bash
# Après corrections, exécuter :
pytest tests/test_security_elite.py -v
pytest tests/test_multi_tenant.py -v
pytest tests/test_rbac_matrix.py -v
pytest tests/test_auth.py -v

# Nouveau test intégration chiffrement
pytest tests/test_encryption.py -v

# Nouveau test hash chaîné
pytest tests/test_audit_integrity.py -v
```

### 5.3 Vérifications Manuelles

1. **Chiffrement** : Exécuter `SELECT email FROM users` en DB → doit être chiffré
2. **Audit** : Insérer fausse entrée → endpoint `/audit/verify` doit détecter
3. **Inter-tenant** : Curl avec JWT tenant-A vers données tenant-B → 403
4. **CORS** : Curl avec Origin: evil.com → pas de header Access-Control-Allow-Origin

---

## 6. PLAN D'ACTION RECOMMANDÉ

### Sprint 1 (Immédiat - 1-2 jours)

| Priorité | Tâche | Assigné | Statut |
|----------|-------|---------|--------|
| P0 | Implémenter `app/core/encryption.py` | - | À faire |
| P0 | Migration chiffrement colonnes sensibles | - | À faire |
| P0 | Tests chiffrement | - | À faire |

### Sprint 2 (Suivant - 2-3 jours)

| Priorité | Tâche | Assigné | Statut |
|----------|-------|---------|--------|
| P0 | Hash chaîné journal audit | - | À faire |
| P0 | Tests intégrité audit | - | À faire |
| P1 | Tests isolation inter-tenant complets | - | À faire |

### Sprint 3 (Production - 1-2 jours)

| Priorité | Tâche | Assigné | Statut |
|----------|-------|---------|--------|
| P1 | CORS restrictif production | - | À faire |
| P1 | Token blacklist | - | À faire |
| P2 | Documentation sécurité | - | À faire |

---

## 7. SIGNATURES

| Rôle | Date | Signature |
|------|------|-----------|
| Évaluateur | 2026-01-08 | [SYSTÈME] |
| Responsable Sécurité | - | __________ |
| Responsable Technique | - | __________ |

---

## 8. HISTORIQUE

| Date | Action | Auteur |
|------|--------|--------|
| 2026-01-08 | Création rapport FAIL | Système |

---

**⚠️ AVERTISSEMENT** : Ce module NE PEUT PAS être utilisé en production tant que les critères BLOQUANTS ne sont pas corrigés. L'utilisation en l'état expose les données clients et engage la responsabilité légale de l'entreprise.
