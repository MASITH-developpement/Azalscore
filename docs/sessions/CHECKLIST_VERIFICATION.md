# AZALS - Checklist de Vérification Systématique

## Avant chaque commit / déploiement

### 1. Variables et Configuration

#### Variables CSS
```bash
grep -r "style=" ui/*.html
# Résultat attendu: Aucun inline style
```

#### Variables JavaScript
- [ ] `API_BASE` défini dans app.js
- [ ] Toutes les fonctions `load*Data()` présentes
- [ ] Toutes les fonctions `build*Module()` présentes
- [ ] Toutes les fonctions `create*Card()` présentes

#### Variables Backend
- [ ] `SECRET_KEY` >= 32 caractères
- [ ] `DATABASE_URL` valide (postgresql:// ou sqlite:///)
- [ ] Pas de "CHANGEME" dans .env

#### Variables d'environnement (.env)
```bash
# Vérifier que .env existe et contient:
- DATABASE_URL
- SECRET_KEY
- APP_NAME
- DEBUG
```

### 2. Navigation et Routes

#### Menu latéral (sidebar)
- [ ] Tous les menus identiques sur toutes les pages
- [ ] Classe `active` correcte selon la page
- [ ] Liens cohérents (pas de mix #, /dashboard, etc.)

```bash
# Vérifier la cohérence des menus
diff <(grep -A 50 "<nav class=\"sidebar-nav\">" ui/dashboard.html) \
     <(grep -A 50 "<nav class=\"sidebar-nav\">" ui/treasury.html)
```

#### Routes backend (middleware)
```bash
# Vérifier PUBLIC_PATHS dans app/core/middleware.py
grep "PUBLIC_PATHS" app/core/middleware.py
```

Routes publiques requises:
- [ ] `/health`
- [ ] `/`
- [ ] `/dashboard`
- [ ] `/treasury`
- [ ] `/static`
- [ ] `/favicon.ico`

#### Routes serveur (main.py)
```bash
# Vérifier que toutes les pages HTML ont une route
ls ui/*.html | while read f; do 
  name=$(basename $f .html)
  [[ "$name" == "index" ]] && name="/"
  grep -q "\"/$name\"" app/main.py || echo "Route manquante: $name"
done
```

### 3. Syntaxe et Erreurs

#### Python
```bash
python3 -m py_compile app/main.py app/api/*.py app/core/*.py app/services/*.py
echo "✓ Python OK" || echo "✗ Erreurs Python"
```

#### JavaScript
```bash
node -c ui/app.js && echo "✓ JavaScript OK" || echo "✗ Erreurs JavaScript"
```

#### HTML - Inline Styles
```bash
grep -r 'style=' ui/*.html
# Résultat attendu: Aucun résultat (0 inline styles)
```

### 4. Cohérence des données

#### Modules dans le cockpit
Vérifier dans `ui/app.js` fonction `initDashboard()`:
- [ ] `loadTreasuryData()` appelé
- [ ] `buildTreasuryModule()` dans la liste des modules
- [ ] `buildAccountingModule()` dans la liste
- [ ] Tous les modules ont `domain` et `domainPriority`

#### Templates HTML
```bash
# Vérifier que chaque page a son template
grep -l "data-page=" ui/*.html
```

Pour chaque `data-page="X"`, vérifier dans app.js:
- [ ] `case 'X':` existe dans le switch
- [ ] Fonction `initX()` ou équivalent existe

### 5. Authentification

#### Pages protégées
Toutes les pages sauf index.html doivent avoir:
- [ ] `data-require-auth="true"`
- [ ] Appel à `checkAuth()` dans la fonction d'initialisation

```bash
# Vérifier
grep -l "data-require-auth" ui/*.html
```

#### Session Storage
Vérifier que ces clés sont utilisées:
- [ ] `token`
- [ ] `tenant_id`
- [ ] `user_email`

### 6. API Endpoints

#### Vérifier que les endpoints appelés existent
```bash
# Extraire les appels API du frontend
grep -oE "API_BASE[^'\"]*['\"][^'\"]+['\"]" ui/app.js | sort -u

# Vérifier contre les routes backend
grep -oE "@router\.(get|post|put|delete)\(['\"][^'\"]+['\"]" app/api/*.py
```

Endpoints critiques:
- [ ] POST `/auth/login`
- [ ] GET `/treasury/latest`
- [ ] GET `/journal`
- [ ] GET `/decision/red/status/{id}`
- [ ] POST `/decision/red/acknowledge/{id}`
- [ ] POST `/decision/red/confirm-completeness/{id}`
- [ ] POST `/decision/red/confirm-final/{id}`

### 7. Design et UX

#### Charte graphique
- [ ] Aucun inline style (vérifié ci-dessus)
- [ ] Toutes les classes CSS référencées existent dans styles.css
- [ ] Variables CSS utilisées (pas de couleurs en dur)

```bash
# Vérifier les classes non définies
grep -oE 'class="[^"]*"' ui/*.html | \
  sed 's/class="//;s/"//;s/ /\n/g' | sort -u | \
  while read class; do
    grep -q "\.$class\b" ui/styles.css || echo "Classe manquante: $class"
  done
```

#### Responsive
- [ ] Viewport meta tag présent sur toutes les pages
- [ ] Aucun width/height en pixels en dur (sauf SVG)

### 8. Sécurité

#### Headers sensibles
```bash
# Vérifier X-Tenant-ID dans les requêtes
grep -r "X-Tenant-ID" ui/app.js app/
```

- [ ] X-Tenant-ID envoyé dans `authenticatedFetch()`
- [ ] X-Tenant-ID validé par le middleware

#### Mots de passe
- [ ] Hachage bcrypt utilisé (pas de plaintext)
- [ ] SECRET_KEY >= 32 caractères
- [ ] Pas de credentials en dur dans le code

### 9. Base de données

#### Migrations
```bash
ls migrations/*.sql
```

- [ ] Toutes les migrations exécutées
- [ ] Pas de migration en conflit

#### Modèles
Vérifier cohérence entre:
- [ ] `app/core/models.py` (SQLAlchemy)
- [ ] Schémas Pydantic dans `app/api/*.py`
- [ ] Migrations SQL dans `migrations/`

### 10. Tests

#### Santé du service
```bash
curl -s https://azalscore.onrender.com/health | jq .
# Attendu: {"status":"ok","api":true,"database":true}
```

#### Pages accessibles
```bash
for page in "" dashboard treasury; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://azalscore.onrender.com/$page")
  echo "$page: $status"
done
```

Codes attendus:
- [ ] `/` → 200
- [ ] `/dashboard` → 200 ou 401 (si auth requis)
- [ ] `/treasury` → 200 ou 401

## Checklist rapide avant push

```bash
# 1. Pas d'inline styles
! grep -r 'style=' ui/*.html

# 2. Syntaxe Python OK
python3 -m py_compile app/**/*.py

# 3. Syntaxe JavaScript OK
node -c ui/app.js

# 4. Git clean
git status

# 5. Santé API
curl -s https://azalscore.onrender.com/health | grep -q '"status":"ok"'
```

## Variables à vérifier systématiquement

### Frontend (app.js)
- API_BASE
- checkAuth()
- authenticatedFetch()
- sessionStorage: token, tenant_id, user_email

### Backend (config.py)
- SECRET_KEY
- DATABASE_URL
- APP_NAME
- DEBUG
- DB_POOL_SIZE

### CSS (styles.css)
- --color-* (couleurs)
- --spacing-* (espacements)
- --border-radius-* (bordures)
- --shadow-* (ombres)
- --transition-* (transitions)

### Environnement (.env)
- DATABASE_URL
- SECRET_KEY
- POSTGRES_*
- CORS_ORIGINS
