# AZALS - Politique de Securite

## Table des Matieres

1. [Regles Fondamentales](#regles-fondamentales)
2. [Gouvernance des Branches](#gouvernance-des-branches)
3. [Verrouillage des Environnements](#verrouillage-des-environnements)
4. [Gestion des Versions](#gestion-des-versions)
5. [Interdictions en Production](#interdictions-en-production)
6. [Secrets et Configuration](#secrets-et-configuration)
7. [Processus de Release](#processus-de-release)
8. [Verification et Audit](#verification-et-audit)

---

## Regles Fondamentales

### Principe de Separation Absolue

Le projet AZALS applique une separation **IRREVERSIBLE** entre les environnements de developpement (DEV) et de production (PROD).

| Regle | Description | Sanction |
|-------|-------------|----------|
| DEV -> PROD | Merge autorise (apres revue) | - |
| PROD -> DEV | **INTERDIT** | Rejet automatique |
| Version -dev en PROD | **INTERDIT** | Crash au demarrage |
| DEBUG en PROD | **INTERDIT** | Crash au demarrage |
| Reset UUID en PROD | **INTERDIT** | Crash au demarrage |

### Hierarchie de Confiance

```
main (PROD)     : VERROUILLE, IMMUTABLE, AUCUN DEV
   |
   v
develop (DEV)   : Developpement actif, tests, pre-prod possible
   |
   v
feature/*       : Branches de fonctionnalites
```

---

## Gouvernance des Branches

### Branche `main` (Production)

La branche `main` est la branche de **production irreversible**.

**INTERDICTIONS ABSOLUES sur `main` :**

- Execution de scripts DEV (`run_dev.sh`)
- Variables DEBUG=true
- Variables DB_AUTO_RESET_ON_VIOLATION=true
- Version contenant "-dev"
- Merge depuis une branche non validee
- Force push

**OBLIGATIONS sur `main` :**

- Version AZALS_VERSION = "X.Y.Z-prod"
- Tous les tests passes
- Revue de code obligatoire
- Secrets de production configures

### Branche `develop` (Developpement)

La branche `develop` est la branche de **developpement actif**.

**AUTORISATIONS sur `develop` :**

- Mode developpement (`run_dev.sh`)
- Mode pre-production (`run_prod.sh` pour tests)
- Auto-reset UUID (DB_AUTO_RESET_ON_VIOLATION=true)
- Debug active
- Version "-dev" ou "-prod" (pour release)

**INTERDICTIONS sur `develop` :**

- Merge direct depuis `main`

### Branches `feature/*`

Les branches de fonctionnalites suivent les memes regles que `develop`.

---

## Verrouillage des Environnements

### Script `run_dev.sh`

```bash
# Refuse de s'executer sur main
if [ "$BRANCH" = "main" ]; then
    exit 1  # FATAL
fi

export AZALS_ENV=dev
export DB_AUTO_RESET_ON_VIOLATION=true
```

### Script `run_prod.sh`

```bash
# Refuse les versions -dev
if [[ "$VERSION" == *"-dev"* ]]; then
    exit 1  # FATAL
fi

# Bloque les variables dangereuses
export AZALS_ENV=prod
export DB_AUTO_RESET_ON_VIOLATION=false
export DEBUG=false
```

### Garde-fou Python (`app/core/guards.py`)

```python
# PROD + "-dev" = CRASH IMMEDIAT
if is_prod and version.endswith("-dev"):
    raise EnvironmentVersionMismatchError()

# DEV + "-prod" = WARNING (pre-prod autorise)
if is_dev and version.endswith("-prod"):
    print("[WARN] Mode pre-production")
```

---

## Gestion des Versions

### Format de Version

```
AZALS_VERSION = "MAJOR.MINOR.PATCH-SUFFIX"

SUFFIX:
  -dev   : Developpement (branche develop)
  -prod  : Production (branche main)
```

### Fichier Source de Verite

```
app/core/version.py
```

**CE FICHIER EST LA SEULE SOURCE DE VERITE.**

La version ne doit JAMAIS etre calculee dynamiquement.

### Regles de Versionage

| Branche | Version Autorisee | Exemple |
|---------|-------------------|---------|
| develop | X.Y.Z-dev | 0.1.0-dev |
| main | X.Y.Z-prod | 0.1.0-prod |
| feature/* | X.Y.Z-dev | 0.1.0-dev |

---

## Interdictions en Production

### Liste Complete des Interdictions

| Variable/Configuration | Valeur Interdite | Consequence |
|------------------------|------------------|-------------|
| DEBUG | true | Crash au demarrage |
| DB_AUTO_RESET_ON_VIOLATION | true | Crash au demarrage |
| DB_RESET_UUID | true | Crash au demarrage |
| AZALS_DB_RESET_UUID | true | Crash au demarrage |
| AZALS_VERSION | *-dev | Crash au demarrage |
| docs_url | /docs | Desactive automatiquement |
| redoc_url | /redoc | Desactive automatiquement |
| openapi_url | /openapi.json | Desactive automatiquement |
| CORS_ORIGINS | localhost | Crash au demarrage |
| CORS_ORIGINS | * | Crash au demarrage |

### Verifications au Demarrage

L'application effectue ces verifications **AVANT toute connexion DB** :

1. Coherence environnement/version
2. Presence des secrets obligatoires
3. Absence de variables dangereuses
4. Configuration CORS stricte

---

## Secrets et Configuration

### Secrets Obligatoires en Production

| Secret | Description | Longueur Min |
|--------|-------------|--------------|
| SECRET_KEY | Cle JWT | 32 caracteres |
| BOOTSTRAP_SECRET | Secret admin initial | 32 caracteres |
| ENCRYPTION_KEY | Cle Fernet AES-256 | Cle Fernet valide |
| CORS_ORIGINS | Origines autorisees | URL(s) valide(s) |

### Generation des Secrets

```bash
# SECRET_KEY / BOOTSTRAP_SECRET
python -c "import secrets; print(secrets.token_urlsafe(64))"

# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Variables Interdites

Ces valeurs sont **REJETEES** pour les secrets :

- `dev-secret`
- `change-me`
- `changeme`
- `secret`
- `password`
- `123456`
- `azals`
- `default`

---

## Processus de Release

### 1. Preparation sur `develop`

```bash
# Verifier que tous les tests passent
pytest

# Verifier la version actuelle
cat app/core/version.py
# AZALS_VERSION = "0.1.0-dev"
```

### 2. Mise a jour de la version

```bash
# Modifier la version pour la release
# app/core/version.py
AZALS_VERSION = "0.1.0-prod"

# Commit
git add app/core/version.py
git commit -m "release: prepare v0.1.0-prod"
```

### 3. Merge vers `main`

```bash
# Creer une Pull Request develop -> main
# Revue de code obligatoire
# Merge apres validation
```

### 4. Post-release sur `develop`

```bash
# Revenir sur develop
git checkout develop

# Incrementer la version
# app/core/version.py
AZALS_VERSION = "0.2.0-dev"

# Commit
git add app/core/version.py
git commit -m "chore: bump version to 0.2.0-dev"
```

---

## Verification et Audit

### Log de Securite au Demarrage

L'application affiche un log de securite a chaque demarrage :

```
[SECURITY] ENV=prod | VERSION=0.1.0-prod | BRANCH=main | STATUS=LOCKED
```

### Statuts Possibles

| Status | Signification |
|--------|---------------|
| LOCKED | Production verrouillee, aucun risque |
| UNLOCKED | Developpement, operations dangereuses possibles |
| WARNING | Pre-production ou configuration atypique |

### Audit des Violations

Toute violation de securite est :

1. Loggee avec niveau CRITICAL
2. Affichee dans stderr
3. Provoque un arret immediat (exit code 1)

### Commandes de Verification

```bash
# Verifier la version actuelle
grep AZALS_VERSION app/core/version.py

# Verifier la branche
git rev-parse --abbrev-ref HEAD

# Verifier l'environnement
echo $AZALS_ENV

# Lancer les tests de securite
pytest tests/test_security_guards.py
```

---

## Contact Securite

Pour signaler une vulnerabilite ou une question de securite :

1. NE PAS ouvrir d'issue publique
2. Contacter l'equipe de securite directement
3. Fournir tous les details techniques

---

## Rotation des Secrets

### Frequence de Rotation

| Secret | Frequence | Procedure |
|--------|-----------|-----------|
| SECRET_KEY (JWT) | 90 jours | Voir 8.1 |
| ENCRYPTION_KEY | 180 jours | Voir 8.2 |
| Mots de passe DB | 90 jours | Voir 8.3 |
| Cles API externes | Selon provider | Regenerer dans console provider |

### 8.1 Rotation SECRET_KEY (JWT)

**Impact:** Invalidation de TOUS les tokens JWT actifs.

```bash
# 1. Generer nouvelle cle
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 2. Mettre a jour dans le gestionnaire de secrets
# 3. Deployer avec la nouvelle cle
# 4. Les utilisateurs devront se reconnecter
```

### 8.2 Rotation ENCRYPTION_KEY (Fernet)

**Impact:** Les donnees chiffrees doivent etre rechiffrees.

```bash
# 1. Generer nouvelle cle
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Executer le script de migration
python scripts/rotate_encryption_key.py --old-key <OLD> --new-key <NEW>

# 3. Mettre a jour et deployer
```

### 8.3 Rotation Mot de Passe PostgreSQL

```sql
-- 1. Generer nouveau mot de passe
-- 2. Mettre a jour dans PostgreSQL
ALTER USER azals_user WITH PASSWORD 'nouveau_mot_de_passe';

-- 3. Mettre a jour DATABASE_URL
-- 4. Redemarrer l'API
```

---

## Procedure d'Urgence

### Si un secret est compromis

1. **IMMEDIAT (< 5 min):**
   - Revoquer/regenerer le secret compromis
   - Si SECRET_KEY: invalider tous les tokens (redemarrage API)
   - Bloquer les IPs suspectes si identifiees

2. **COURT TERME (< 1h):**
   - Analyser les logs pour evaluer l'etendue
   - Notifier l'equipe securite
   - Documenter l'incident

3. **SUIVI:**
   - Audit complet des acces
   - Post-mortem avec actions correctives
   - Mise a jour des procedures si necessaire

---

**Document maintenu par l'equipe AZALS**
**Version: 1.1.0**
**Derniere mise a jour: 2026-02-10**
