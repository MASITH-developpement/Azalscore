# AZALSCORE - Documentation des Variables

> Guide de reference complet pour toutes les variables du projet

**Statut**: AUDIT COMPLETE - HARMONISATION REQUISE
**Date**: 2026-02-13
**Version**: 2.0

---

## Table des Matieres

1. [Variables d'Environnement](#1-variables-denvironnement)
2. [Constantes de Configuration](#2-constantes-de-configuration)
3. [Constantes de Test](#3-constantes-de-test)
4. [Constantes Globales](#4-constantes-globales)
5. [Variables Frontend](#5-variables-frontend)
6. [Inconsistances Detectees](#6-inconsistances-detectees)
7. [Plan d'Harmonisation](#7-plan-dharmonisation)

---

## 1. Variables d'Environnement

### 1.1 Fichiers de Configuration

| Fichier | Usage | Notes |
|---------|-------|-------|
| `.env` | Production (symlink) | Pointe vers .env.production |
| `.env.example` | Template | Documentation des variables |
| `.env.local` | Developpement local | Secrets de dev |
| `.env.production` | Production | Config serveur |
| `.env.production.example` | Template production | - |

### 1.2 Variables Obligatoires

```bash
# === BASE DE DONNEES (OBLIGATOIRE) ===
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/azals

# === SECURITE (OBLIGATOIRE) ===
SECRET_KEY=<minimum-32-caracteres>           # JWT signing
BOOTSTRAP_SECRET=<minimum-32-caracteres>     # Bootstrap admin (OBLIGATOIRE en prod)
ENCRYPTION_KEY=<base64-32-bytes>             # Chiffrement donnees sensibles

# === ENVIRONNEMENT ===
ENVIRONMENT=production                        # production|test|demo
# Note: AZALS_ENV est un alias (validation_alias dans config.py)
```

### 1.3 Variables Optionnelles

```bash
# === POOL DE CONNEXIONS ===
DB_POOL_SIZE=5                               # Dev: 5, Prod: 10
DB_MAX_OVERFLOW=10                           # Dev: 10, Prod: 20

# === CORS ===
CORS_ORIGINS=https://domain1.com,https://domain2.com

# === RATE LIMITING ===
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=5

# === REDIS (optionnel) ===
REDIS_URL=redis://redis:6379/0
REDIS_TIMEOUT=5
REDIS_HEALTH_TIMEOUT=2

# === EMAIL (SMTP) ===
SMTP_HOST=smtp.provider.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=secret
SMTP_FROM=noreply@azalscore.com

# === STRIPE ===
STRIPE_SECRET_KEY=sk_live_xxx               # ou sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_LIVE_MODE=true                       # ou false

# === API TIMEOUT ===
API_TIMEOUT_MS=30000                         # 30 secondes

# === VERSION ===
VERSION=0.5.0                                # Doit correspondre a app/core/version.py
```

### 1.4 Variables IA (Optionnelles)

```bash
# === OPENAI ===
OPENAI_API_KEY=sk-xxx
AZALSCORE_GPT_MODEL=gpt-4o
AZALSCORE_GPT_MAX_TOKENS=2000
AZALSCORE_GPT_TEMPERATURE=0.3
AZALSCORE_GPT_TIMEOUT_MS=30000
AZALSCORE_GPT_RATE_LIMIT=30

# === ANTHROPIC (Claude) ===
ANTHROPIC_API_KEY=sk-ant-xxx
AZALSCORE_CLAUDE_MODEL=claude-sonnet-4-20250514

# === LIMITES IA ===
AZALSCORE_AI_CALLS_PER_MINUTE=60
AZALSCORE_AI_CALLS_PER_HOUR=500
AZALSCORE_SENSITIVE_OPS_PER_DAY=10

# === AUTHENTIFICATION ===
AZALSCORE_SESSION_HOURS=2
AZALSCORE_MFA_VALIDITY_MINUTES=10
AZALSCORE_MAX_FAILED_ATTEMPTS=5
AZALSCORE_LOCKOUT_MINUTES=15

# === AUDIT ===
AZALSCORE_AUDIT_LOG_DIR=/app/logs/ai_audit
AZALSCORE_AUDIT_RETENTION_DAYS=365
```

### 1.5 Variables Services Externes

```bash
# === PAPPERS (Analyse risque France) ===
PAPPERS_API_KEY=xxx

# === RESEND (Email alternatif) ===
RESEND_API_KEY=re_xxx
EMAIL_FROM=noreply@azalscore.com

# === URLs ===
APP_URL=https://app.azalscore.com
APP_DOMAIN=azalscore.com
```

---

## 2. Constantes de Configuration

### 2.1 Configuration Principale (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # Obligatoires
    database_url: str
    secret_key: str                          # Min 32 caracteres
    bootstrap_secret: str | None             # Obligatoire en production

    # Avec valeurs par defaut
    environment: str = "production"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    cors_origins: str | None = None
    cors_max_age: int = 3600
    rate_limit_per_minute: int = 100
    auth_rate_limit_per_minute: int = 5
    redis_url: str | None = None
    redis_timeout: int = 5
    redis_health_timeout: int = 2
    api_timeout_ms: int = 30000
    app_url: str = "https://localhost"
    app_domain: str = "localhost"
    encryption_key: str | None = None

    # SMTP
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # Stripe
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
```

### 2.2 Configuration IA (`app/ai/config.py`)

```python
class AIConfig:
    gpt = AIModuleConfig(
        model="gpt-4o",
        max_tokens=2000,
        temperature=0.3,
        timeout_ms=30000,
        rate_limit_per_minute=30
    )

    claude = AIModuleConfig(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0.3,
        timeout_ms=30000,
        rate_limit_per_minute=30
    )

    guardian = GuardianConfig(
        ai_calls_per_minute=60,
        ai_calls_per_hour=500,
        sensitive_operations_per_day=10
    )

    auth = AuthConfig(
        session_duration_hours=2,
        mfa_code_validity_minutes=10,
        max_failed_attempts=5,
        lockout_duration_minutes=15
    )

    audit = AuditConfig(
        log_directory="/app/logs/ai_audit",
        retention_days=365
    )
```

### 2.3 Version (`app/core/version.py`)

```python
AZALS_VERSION = "0.5.0-prod"                 # VERSION CANONIQUE

VERSION_SUFFIX_DEV = "-dev"
VERSION_SUFFIX_PROD = "-prod"
BRANCH_DEVELOP = "develop"
BRANCH_MAIN = "main"
```

### 2.4 Securite (`app/core/security.py`)

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
```

### 2.5 CSRF (`app/core/csrf_middleware.py`)

```python
CSRF_TOKEN_EXPIRY = 3600                     # 1 heure

CSRF_EXEMPT_PATHS = {
    "/auth/login", "/auth/register", "/auth/logout", "/auth/refresh",
    "/auth/2fa/verify-login",
    "/v1/auth/login", "/v1/auth/register", "/v1/auth/logout",
    "/v1/auth/refresh", "/v1/auth/2fa/verify-login",
    "/health", "/health/live", "/health/ready",
    "/webhooks/", "/api/webhooks/",
}
```

### 2.6 Content Security (`app/core/security_middleware.py`)

```python
MAX_CONTENT_LENGTH = 10 * 1024 * 1024        # 10 MB max
```

### 2.7 Timeouts Providers (`app/modules/enrichment/providers/`)

| Provider | Fichier | Timeout |
|----------|---------|---------|
| Base | `base.py` | 10.0s |
| OpenFoodFacts | `openfoodfacts.py` | 10.0s |
| INSEE | `insee.py` | 15.0s |
| Adresse | `adresse.py` | 5.0s |
| Pappers | `pappers.py` | 15.0s |

---

## 3. Constantes de Test

### 3.1 Configuration Racine (`tests/conftest.py`)

```python
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-key-minimum-32-characters-long-for-tests")
os.environ.setdefault("BOOTSTRAP_SECRET", "test-bootstrap-minimum-32-characters-here")
os.environ.setdefault("ENVIRONMENT", "test")
```

### 3.2 Constantes Tests App (`app/conftest.py`)

```python
TEST_TENANT_ID = "tenant-test-001"
TEST_USER_ID = "12345678-1234-1234-1234-123456789001"
TEST_USER_UUID = UUID(TEST_USER_ID)

# Cle de chiffrement pour tests
os.environ.setdefault("ENCRYPTION_KEY", "J37-b0UuiaXxpvZmlu95ZmK0cNKYQK57SqplMtAmdn4=")
```

### 3.3 Fixtures Globales (Heritees par tous les modules)

| Fixture | Type | Valeur |
|---------|------|--------|
| `tenant_id` | str | `"tenant-test-001"` |
| `user_id` | str (UUID) | `"12345678-1234-1234-1234-123456789001"` |
| `user_uuid` | UUID | UUID object |
| `db_session` | Session | SQLite in-memory |
| `test_db_session` | Session | Alias db_session |
| `test_client` | TestClient | Headers auto-injectes |
| `mock_auth_global` | dict | autouse=True |
| `saas_context` | SaaSContext | Role ADMIN |
| `mock_user` | MockUser | Utilisateur mock |

---

## 4. Constantes Globales

### 4.1 URLs de Base API (Tests)

| Module | URL |
|--------|-----|
| ai_assistant | `/v2/ai` |
| autoconfig | `/v2/autoconfig` |
| commercial | `/v2/commercial` |
| compliance | `/v2/compliance` |
| hr | `/v2/hr` |
| inventory | `/v2/inventory` |
| projects | `/v2/projects` |
| purchases | `/v2/purchases` |

### 4.2 Plans Stripe (`app/services/stripe_service.py`)

```python
AZALSCORE_PLANS = {
    "starter": {
        "price_monthly": 4900,               # 49.00 EUR
        "price_yearly": 49000,               # 490.00 EUR
    },
    "professional": {
        "price_monthly": 14900,              # 149.00 EUR
        "price_yearly": 149000,              # 1490.00 EUR
    },
    "enterprise": {
        "price_monthly": 49900,              # 499.00 EUR
        "price_yearly": 499000,              # 4990.00 EUR
    }
}

stripe.api_version = "2023-10-16"
```

### 4.3 Configuration Marceau (`app/modules/marceau/config.py`)

```python
DEFAULT_ENABLED_MODULES = {
    "telephonie": True,
    "marketing": False,
    "seo": False,
    "commercial": False,
    "comptabilite": False,
    "juridique": False,
    "recrutement": False,
    "support": False,
    "orchestration": False,
}

DEFAULT_TELEPHONY_CONFIG = {
    "asterisk_ami_host": "localhost",
    "asterisk_ami_port": 5038,
    "working_hours": {"start": "09:00", "end": "18:00"},
    "overflow_threshold": 2,
    "appointment_duration_minutes": 60,
    "max_wait_days": 14,
    "travel_buffer_minutes": 15,
}
```

---

## 5. Variables Frontend

### 5.1 Variables CSS (styles.css)

```css
/* Couleurs principales */
--color-primary: #1a2332;
--color-primary-light: #2a3647;
--color-primary-lighter: #3a4858;
--color-accent: #4a90e2;
--color-accent-hover: #357abd;

/* Couleurs de fond */
--color-bg-main: #f8f9fb;
--color-bg-card: #ffffff;
--color-bg-sidebar: #1a2332;
--color-bg-hover: #f0f2f5;

/* Couleurs de texte */
--color-text-primary: #1a1f2e;
--color-text-secondary: #6b7280;
--color-text-muted: #9ca3af;
--color-text-inverse: #ffffff;

/* Couleurs de statut */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-danger: #ef4444;
--color-info: #3b82f6;

/* Ombres */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

/* Espacements */
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--spacing-2xl: 3rem;

/* Bordures */
--border-radius-sm: 0.375rem;
--border-radius-md: 0.5rem;
--border-radius-lg: 0.75rem;

/* Transitions */
--transition-fast: 150ms ease;
--transition-base: 250ms ease;
```

### 5.2 Configuration JavaScript

```javascript
const API_BASE = '';                         // Prefixe API (vide = meme origine)
```

---

## 6. Inconsistances Detectees

### 6.1 CRITIQUE - A Corriger Immediatement

| Probleme | Fichiers | Impact |
|----------|----------|--------|
| **Version mismatch** | `version.py`: 0.5.0 vs `.env.production`: 0.4.0 | Confusion sur version deployee |
| **ENCRYPTION_KEY manquant** | `.env.example` ne definit pas ENCRYPTION_KEY | Securite, erreurs potentielles |
| **Stripe keys inconsistantes** | Code attend `STRIPE_API_KEY_LIVE`, .env definit `STRIPE_SECRET_KEY` | Integration Stripe cassee |

### 6.2 HAUTE - A Planifier

| Probleme | Fichiers | Impact |
|----------|----------|--------|
| **Double nommage ENVIRONMENT** | Config utilise AZALS_ENV et ENVIRONMENT | Confusion |
| **Email service dual** | Resend vs SMTP dans differents fichiers | Configuration email confuse |
| **MASITH hard-coded** | `.env.production` contient identifiants en dur | Securite |
| **AI models mixtes** | Marceau hard-code `llama3-8b-instruct` | Non configurable |

### 6.3 MOYENNE - Amelioration

| Probleme | Fichiers | Impact |
|----------|----------|--------|
| **Timeouts multiples** | Config globale 30s vs providers 5-15s | Incoherence |
| **DB Pool sizes** | Pas de config staging | Manque environnement intermediaire |
| **Rate limits separes** | Global + AI non documentes ensemble | Documentation |
| **Test tenant IDs** | Certains tests utilisent "tenant_wf1" | Inconsistance mineure |

---

## 7. Plan d'Harmonisation

### Phase 1: Corrections Critiques (Immediat)

#### 1.1 Synchroniser les versions

```bash
# Fichier: .env.production
VERSION=0.5.0                                # Mettre a jour pour correspondre a version.py
```

#### 1.2 Ajouter ENCRYPTION_KEY a l'exemple

```bash
# Fichier: .env.example - AJOUTER
ENCRYPTION_KEY=<base64-encoded-32-bytes>     # OBLIGATOIRE - Generer avec: openssl rand -base64 32
```

#### 1.3 Standardiser les noms Stripe

```python
# Fichier: app/services/stripe_service.py - MODIFIER
# Avant:
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY_LIVE") or os.getenv("STRIPE_API_KEY_TEST")

# Apres:
STRIPE_API_KEY = os.getenv("STRIPE_SECRET_KEY")
```

### Phase 2: Nettoyage Configuration (1-2 jours)

#### 2.1 Standardiser nommage environnement

```python
# Fichier: app/core/config.py - Choisir UN seul nom
environment: str = Field(default="production")  # Supprimer validation_alias="AZALS_ENV"
```

#### 2.2 Unifier service email

```python
# Creer: app/services/email_service_unified.py
# Abstraire Resend et SMTP derriere une interface commune
class EmailProvider(ABC):
    @abstractmethod
    async def send(self, to, subject, body): ...

class ResendProvider(EmailProvider): ...
class SMTPProvider(EmailProvider): ...
```

#### 2.3 Externaliser credentials MASITH

```bash
# Fichier: .env.production - SUPPRIMER
# MASITH_TENANT_ID=masith
# MASITH_ADMIN_PASSWORD=Gobelet2026!

# Utiliser: secrets management externe (Vault, AWS Secrets Manager)
```

### Phase 3: Standardisation AI (2-3 jours)

#### 3.1 Centraliser configuration AI

```python
# Fichier: app/ai/config.py - UNIFIER
class AIConfig:
    # Tous les modeles configurables via env
    models = {
        "gpt": os.getenv("AI_MODEL_GPT", "gpt-4o"),
        "claude": os.getenv("AI_MODEL_CLAUDE", "claude-sonnet-4-20250514"),
        "local": os.getenv("AI_MODEL_LOCAL", "llama3-8b-instruct"),  # Marceau
    }

    # Timeouts unifies
    default_timeout_ms = int(os.getenv("AI_DEFAULT_TIMEOUT_MS", "30000"))
```

### Phase 4: Documentation (Continu)

#### 4.1 Creer fichier .env.staging

```bash
# Fichier: .env.staging - CREER
ENVIRONMENT=staging
DB_POOL_SIZE=7
DB_MAX_OVERFLOW=15
CORS_ORIGINS=https://staging.azalscore.com
```

#### 4.2 Documenter hierarchie de configuration

```
Configuration Priority (high to low):
1. Environment variables
2. .env.{environment} file
3. Settings class defaults
4. Hard-coded fallbacks (deprecated)
```

---

## Conventions de Nommage

### Variables d'Environnement

| Categorie | Prefixe | Exemple |
|-----------|---------|---------|
| Application | AZALSCORE_ | AZALSCORE_GPT_MODEL |
| Base de donnees | DB_ | DB_POOL_SIZE |
| Services externes | SERVICE_ | STRIPE_SECRET_KEY |
| Securite | (aucun) | SECRET_KEY, ENCRYPTION_KEY |

### Constantes Python

```python
# snake_case pour variables et fonctions
database_url = "..."

# SCREAMING_SNAKE_CASE pour constantes
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

# PascalCase pour classes
class Settings: ...
```

### Constantes Frontend

```javascript
// camelCase pour variables
const apiBase = '';

// SCREAMING_SNAKE_CASE pour constantes
const MAX_RETRIES = 3;
```

---

## Commandes Utiles

### Generer une cle de chiffrement

```bash
openssl rand -base64 32
```

### Generer un secret JWT

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Verifier les variables d'environnement en cours

```bash
docker exec azals_api env | grep -E "^(DATABASE|SECRET|STRIPE|ENVIRONMENT)" | sort
```

### Comparer .env files

```bash
diff <(grep -v '^#' .env.example | grep -v '^$' | sort) \
     <(grep -v '^#' .env.production | grep -v '^$' | sort)
```

---

**Derniere mise a jour**: 2026-02-13
