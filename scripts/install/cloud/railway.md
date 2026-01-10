# AZALSCORE - Déploiement sur Railway

## Vue d'ensemble

Railway est une plateforme cloud qui permet de déployer des applications avec une base de données PostgreSQL managée.

## Prérequis

- Compte Railway (https://railway.app)
- Dépôt GitHub avec le code AZALSCORE
- Railway CLI (optionnel)

## Déploiement

### 1. Créer un nouveau projet

```bash
# Via CLI
railway login
railway init

# Ou via l'interface web
# 1. Allez sur https://railway.app/new
# 2. Sélectionnez "Deploy from GitHub repo"
# 3. Connectez votre dépôt AZALSCORE
```

### 2. Ajouter PostgreSQL

```bash
# Via CLI
railway add -p postgresql

# Ou via l'interface web
# 1. Cliquez sur "+ New"
# 2. Sélectionnez "Database" → "PostgreSQL"
```

### 3. Configurer les variables d'environnement

**IMPORTANT**: Toutes ces variables sont **obligatoires** pour la sécurité.

#### Variables requises

```bash
# Via CLI
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set BOOTSTRAP_SECRET=$(openssl rand -hex 32)
railway variables set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# UUID Security (OBLIGATOIRE)
railway variables set DB_STRICT_UUID=true
railway variables set DB_RESET_UUID=false
railway variables set DB_AUTO_RESET_ON_VIOLATION=false

# CORS (REMPLACEZ PAR VOTRE DOMAINE)
railway variables set CORS_ORIGINS=https://votre-app.railway.app

# Rate Limiting
railway variables set RATE_LIMIT_PER_MINUTE=60
railway variables set AUTH_RATE_LIMIT_PER_MINUTE=5

# Database Pool
railway variables set DB_POOL_SIZE=10
railway variables set DB_MAX_OVERFLOW=20

# Logging
railway variables set LOG_LEVEL=INFO
```

#### Variables fournies automatiquement par Railway

- `DATABASE_URL` - Fourni automatiquement par le service PostgreSQL
- `PORT` - Port d'écoute (Railway l'assigne automatiquement)

### 4. Configuration du service

Créez ou modifiez le fichier `railway.toml` à la racine du projet:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:$PORT --timeout 120"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[env]
PYTHON_VERSION = "3.12"
```

### 5. Déployer

```bash
# Via CLI
railway up

# Ou via GitHub
# Les déploiements automatiques sont activés par défaut
# Chaque push sur main déclenche un nouveau déploiement
```

### 6. Vérifier le déploiement

```bash
# Voir les logs
railway logs

# Obtenir l'URL du service
railway open
```

## Commandes de build et start

### Procfile (alternative à railway.toml)

```
web: gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:$PORT --timeout 120
release: alembic upgrade head
```

### nixpacks.toml (optionnel)

```toml
[phases.setup]
aptPkgs = ["libpq-dev"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["python -c 'from app.main import app'"]

[start]
cmd = "alembic upgrade head && gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:$PORT"
```

## Domaine personnalisé

1. Dans le dashboard Railway, allez dans les paramètres du service
2. Cliquez sur "Custom Domain"
3. Ajoutez votre domaine
4. Configurez le DNS CNAME chez votre registrar
5. Mettez à jour `CORS_ORIGINS`:

```bash
railway variables set CORS_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
```

## Scaling

Railway permet de configurer le scaling dans l'interface:

- **Horizontal**: Augmenter le nombre de replicas
- **Vertical**: Augmenter la RAM/CPU (plans payants)

Pour le scaling horizontal, assurez-vous d'utiliser Redis pour le rate limiting:

```bash
# Ajouter Redis
railway add -p redis

# La variable REDIS_URL sera automatiquement disponible
```

## Sauvegardes

Railway effectue des sauvegardes automatiques de PostgreSQL.
Pour les restaurer ou les exporter:

1. Allez dans le dashboard du service PostgreSQL
2. Cliquez sur "Backups"
3. Téléchargez ou restaurez une sauvegarde

## Surveillance

Railway fournit:
- Logs en temps réel
- Métriques CPU/RAM
- Alertes (plans payants)

Pour une surveillance avancée, intégrez:
- Sentry pour le tracking d'erreurs
- DataDog ou New Relic pour les métriques

## Checklist de sécurité

Avant de mettre en production, vérifiez:

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` généré avec au moins 32 bytes d'entropie
- [ ] `BOOTSTRAP_SECRET` unique et fort
- [ ] `ENCRYPTION_KEY` est une clé Fernet valide
- [ ] `CORS_ORIGINS` ne contient PAS localhost
- [ ] `DB_STRICT_UUID=true`
- [ ] `DB_RESET_UUID=false`
- [ ] `DB_AUTO_RESET_ON_VIOLATION=false`
- [ ] HTTPS activé (automatique sur Railway)
- [ ] Domaine personnalisé configuré (recommandé)

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
railway logs --tail 100

# Vérifier les variables
railway variables

# Tester localement avec les mêmes variables
railway run python -c "from app.main import app"
```

### Erreur de connexion à la base de données

```bash
# Vérifier que DATABASE_URL est disponible
railway run printenv DATABASE_URL

# Tester la connexion
railway run python -c "from app.core.database import engine; print(engine.url)"
```

### Migrations échouent

```bash
# Exécuter les migrations manuellement
railway run alembic upgrade head

# Voir l'historique des migrations
railway run alembic history
```

## Coûts estimés

- **Hobby Plan** (gratuit): 512MB RAM, 1 vCPU partagé, PostgreSQL 1GB
- **Pro Plan** ($20/mois): Ressources dédiées, plus de stockage
- **Enterprise**: Sur mesure

Pour AZALSCORE en production, le **Pro Plan** est recommandé.

## Liens utiles

- Documentation Railway: https://docs.railway.app
- Status Railway: https://status.railway.app
- Support: https://help.railway.app
