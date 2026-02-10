# AZALS - Documentation des Variables

## Variables CSS (styles.css)

### Couleurs principales
```css
--color-primary: #1a2332          /* Bleu nuit principal */
--color-primary-light: #2a3647    /* Bleu nuit clair */
--color-primary-lighter: #3a4858  /* Bleu nuit plus clair */
--color-accent: #4a90e2           /* Bleu accent */
--color-accent-hover: #357abd     /* Bleu accent hover */
```

### Couleurs de fond
```css
--color-bg-main: #f8f9fb          /* Fond principal */
--color-bg-card: #ffffff          /* Fond carte */
--color-bg-sidebar: #1a2332       /* Fond sidebar */
--color-bg-hover: #f0f2f5         /* Fond hover */
```

### Couleurs de texte
```css
--color-text-primary: #1a1f2e     /* Texte principal */
--color-text-secondary: #6b7280   /* Texte secondaire */
--color-text-muted: #9ca3af       /* Texte atténué */
--color-text-inverse: #ffffff     /* Texte inversé */
```

### Couleurs de statut
```css
--color-success: #10b981          /* Vert succès (🟢) */
--color-warning: #f59e0b          /* Orange warning (🟠) */
--color-danger: #ef4444           /* Rouge danger (🔴) */
--color-info: #3b82f6             /* Bleu info */
```

### Ombres
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07)
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1)
```

### Espacements
```css
--spacing-xs: 0.25rem    /* 4px */
--spacing-sm: 0.5rem     /* 8px */
--spacing-md: 1rem       /* 16px */
--spacing-lg: 1.5rem     /* 24px */
--spacing-xl: 2rem       /* 32px */
--spacing-2xl: 3rem      /* 48px */
```

### Bordures
```css
--border-radius-sm: 0.375rem   /* 6px */
--border-radius-md: 0.5rem     /* 8px */
--border-radius-lg: 0.75rem    /* 12px */
```

### Transitions
```css
--transition-fast: 150ms ease
--transition-base: 250ms ease
```

## Variables JavaScript (app.js)

### Configuration
```javascript
const API_BASE = '';  // Préfixe API (vide = même origine)
```

### Fonctions de statut
- `checkAuth()` - Vérifie si l'utilisateur est authentifié
- `authenticatedFetch(url, options)` - Fetch avec JWT et tenant-id

### Modules principaux
- `buildTreasuryModule(data)` - Construction module trésorerie
- `buildAccountingModule(data)` - Construction module comptabilité
- `buildTaxModule()` - Construction module fiscal
- `buildHRModule()` - Construction module RH

### Fonctions de carte
- `createTreasuryCard(data, status, decisionId)` - Créer carte trésorerie
- `createAccountingCard(data, status, decisionId)` - Créer carte comptabilité

### Chargement données
- `loadTreasuryData()` - GET /treasury/latest
- `loadJournalData()` - GET /journal

## Variables Backend (Python)

### Configuration (app/core/config.py)
```python
database_url: str          # URL PostgreSQL ou SQLite
app_name: str = "AZALS"
debug: bool = False
secret_key: str            # Min 32 caractères (JWT)
db_pool_size: int = 5
db_max_overflow: int = 10
cors_origins: Optional[str]
```

### Sécurité (app/core/security.py)
```python
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

### Middleware (app/core/middleware.py)
```python
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/",
    "/dashboard",
    "/treasury",
    "/static",
    "/favicon.ico"
}
```

## Variables d'environnement (.env)

```bash
# Base de données
DATABASE_URL=postgresql://user:pass@host:5432/azals

# Configuration
APP_NAME=AZALS
DEBUG=false

# Sécurité JWT
SECRET_KEY=<min-32-caractères>

# PostgreSQL
POSTGRES_DB=azals
POSTGRES_USER=azals_user
POSTGRES_PASSWORD=<password>

# Pool de connexions
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# CORS (optionnel)
CORS_ORIGINS=http://localhost:3000,https://example.com
```

## Endpoints API

### Authentification
- `POST /auth/login` - Connexion (tenant-id + email + password)
- `POST /auth/register` - Inscription

### Trésorerie
- `GET /treasury/latest` - Dernière prévision (nécessite JWT)
- `POST /treasury/forecast` - Nouvelle prévision

### Journal comptable
- `GET /journal` - Écritures comptables (nécessite JWT)
- `POST /journal/entry` - Nouvelle écriture

### Workflow RED
- `POST /decision/red/acknowledge/{id}` - Étape 1: Accusé lecture
- `POST /decision/red/confirm-completeness/{id}` - Étape 2: Complétude
- `POST /decision/red/confirm-final/{id}` - Étape 3: Validation finale
- `GET /decision/red/status/{id}` - État du workflow
- `GET /decision/red/report/{id}` - Rapport immutable

## Statuts de Trésorerie

### Calcul du statut
```javascript
🔴 red_triggered = true  (forecast_balance < 0)
🟠 opening_balance < 10000 && !red_triggered
🟢 Sinon (situation normale)
⚪ Erreur ou données absentes
```

### Logique d'affichage
- **🔴 Pattern dominant** : Si trésorerie = 🔴 → masquer toutes les autres zones
- **🟠 Zone tension** : Afficher dans "Points d'attention"
- **🟢 Zone normale** : Afficher dans "Situation stable"

## Conventions de nommage

### Backend Python
- **snake_case** pour variables et fonctions
- **PascalCase** pour classes
- Suffixes: `_id`, `_at`, `_url`, `_key`

### Frontend JavaScript
- **camelCase** pour variables et fonctions
- **PascalCase** pour composants (non utilisé, vanilla JS)
- Préfixes: `build`, `create`, `load`, `init`, `handle`

### CSS
- **kebab-case** pour classes
- **--kebab-case** pour variables CSS
- Préfixes: `.btn-`, `.card-`, `.zone-`, `.modal-`
