# AZALSCORE - Déploiement sur Render

## Vue d'ensemble

Render est une plateforme cloud moderne avec support natif pour Python, PostgreSQL et Redis.

## Prérequis

- Compte Render (https://render.com)
- Dépôt GitHub avec le code AZALSCORE

## Configuration

### 1. Fichier render.yaml

Créez ou mettez à jour `render.yaml` à la racine du projet:

```yaml
services:
  # Service API
  - type: web
    name: azalscore-api
    runtime: python
    region: frankfurt  # EU pour RGPD
    plan: starter      # ou pro pour production
    buildCommand: |
      pip install -r requirements.txt
      python -c "from app.main import app"
    startCommand: >
      alembic upgrade head &&
      gunicorn app.main:app
      --worker-class uvicorn.workers.UvicornWorker
      --workers 2
      --threads 2
      --bind 0.0.0.0:$PORT
      --timeout 120
      --keep-alive 5
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: LOG_LEVEL
        value: INFO
      # Secrets (à définir manuellement dans le dashboard)
      - key: SECRET_KEY
        generateValue: true
      - key: BOOTSTRAP_SECRET
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: azalscore-db
          property: connectionString
      # UUID Security
      - key: DB_STRICT_UUID
        value: true
      - key: DB_RESET_UUID
        value: false
      - key: DB_AUTO_RESET_ON_VIOLATION
        value: false
      # Database Pool
      - key: DB_POOL_SIZE
        value: 10
      - key: DB_MAX_OVERFLOW
        value: 20
      # Rate Limiting
      - key: RATE_LIMIT_PER_MINUTE
        value: 60
      - key: AUTH_RATE_LIMIT_PER_MINUTE
        value: 5

databases:
  - name: azalscore-db
    plan: starter  # ou pro pour production
    region: frankfurt
    databaseName: azals
    user: azals_user
    ipAllowList: []  # Vide = accès limité aux services Render

# Redis (optionnel, pour rate limiting distribué)
# - type: redis
#   name: azalscore-redis
#   plan: starter
#   region: frankfurt
#   maxmemoryPolicy: allkeys-lru
```

### 2. Déploiement

#### Via l'interface web

1. Allez sur https://dashboard.render.com
2. Cliquez sur "New" → "Blueprint"
3. Connectez votre dépôt GitHub
4. Render détectera automatiquement `render.yaml`
5. Cliquez sur "Apply"

#### Via Render CLI (optionnel)

```bash
# Installer le CLI
npm install -g @render/cli

# Se connecter
render login

# Déployer
render blueprint apply
```

### 3. Variables d'environnement manuelles

Certaines variables sensibles doivent être définies manuellement:

1. Allez dans le dashboard du service
2. Cliquez sur "Environment"
3. Ajoutez:

```
ENCRYPTION_KEY=<générer avec: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
CORS_ORIGINS=https://azalscore-api.onrender.com
```

### 4. Générer les secrets localement

```bash
# SECRET_KEY (si non auto-généré)
openssl rand -hex 32

# BOOTSTRAP_SECRET
openssl rand -hex 32

# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Configuration avancée

### Scaling

```yaml
services:
  - type: web
    name: azalscore-api
    # ...
    scaling:
      minInstances: 1
      maxInstances: 5
      targetCPUPercent: 70
      targetMemoryPercent: 80
```

### Cron Jobs (tâches planifiées)

```yaml
services:
  # ... service principal ...

  - type: cron
    name: azalscore-cleanup
    runtime: python
    schedule: "0 2 * * *"  # Tous les jours à 2h
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.tasks.cleanup
    envVars:
      - fromGroup: azalscore-env
```

### Private Services

Pour les microservices internes:

```yaml
services:
  - type: pserv
    name: azalscore-worker
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.workers.main
```

## Domaine personnalisé

1. Dans le dashboard du service, allez dans "Settings"
2. Sous "Custom Domains", cliquez "Add Custom Domain"
3. Entrez votre domaine
4. Configurez le DNS CNAME vers `*.onrender.com`
5. Render génère automatiquement un certificat SSL

```bash
# Mettre à jour CORS
CORS_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
```

## Surveillance

### Health Checks

Le health check est configuré sur `/health`. Assurez-vous que cet endpoint existe:

```python
# Dans app/main.py ou app/api/health.py
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Logs

```bash
# Via le dashboard
# Service → Logs

# Ou via le CLI
render logs --service azalscore-api --tail
```

### Métriques

Render fournit des métriques de base. Pour des métriques avancées:

1. Intégrez Prometheus avec l'endpoint `/metrics`
2. Utilisez un service externe (DataDog, New Relic)

## Sauvegardes

### PostgreSQL

Render effectue des sauvegardes automatiques quotidiennes.

Pour une sauvegarde manuelle:

1. Allez dans le service PostgreSQL
2. Cliquez sur "Backups"
3. "Create Backup"

### Restauration

```bash
# Obtenir l'URL de connexion
# Dashboard → PostgreSQL → Connection → External URL

# Restaurer
pg_restore -h <host> -U azals_user -d azals backup.dump
```

## Migration depuis un autre hébergeur

### Depuis Heroku

```bash
# Exporter les variables d'environnement Heroku
heroku config --app your-app -s > .env.heroku

# Exporter la base de données
heroku pg:backups:capture --app your-app
heroku pg:backups:download --app your-app

# Importer dans Render
pg_restore -h <render-host> -U azals_user -d azals latest.dump
```

### Depuis Railway

```bash
# Exporter la DB Railway
railway run pg_dump > backup.sql

# Importer dans Render
psql <render-connection-string> < backup.sql
```

## Checklist de sécurité production

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` unique et fort (32+ bytes)
- [ ] `BOOTSTRAP_SECRET` unique et fort
- [ ] `ENCRYPTION_KEY` est une clé Fernet valide
- [ ] `CORS_ORIGINS` configuré avec les bons domaines (PAS localhost)
- [ ] `DB_STRICT_UUID=true`
- [ ] `DB_RESET_UUID=false`
- [ ] `DB_AUTO_RESET_ON_VIOLATION=false`
- [ ] PostgreSQL avec `ipAllowList` restreint
- [ ] Domaine personnalisé avec HTTPS
- [ ] Health check configuré
- [ ] Sauvegardes automatiques activées

## Coûts estimés

| Plan | RAM | CPU | PostgreSQL | Prix/mois |
|------|-----|-----|------------|-----------|
| Free | 512MB | Partagé | 1GB (90 jours) | $0 |
| Starter | 512MB | 0.5 | 1GB | ~$12 |
| Pro | 2GB | 1 | 10GB | ~$50 |

Pour AZALSCORE en production, le plan **Pro** est recommandé.

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs de build
# Dashboard → Service → Events

# Vérifier les logs runtime
# Dashboard → Service → Logs
```

### Connexion DB échouée

1. Vérifiez que `DATABASE_URL` est correctement lié
2. Vérifiez l'état du service PostgreSQL
3. Testez la connexion:

```bash
render shell --service azalscore-api
python -c "from app.core.database import engine; print(engine.url)"
```

### Migrations bloquées

```bash
# Se connecter au shell
render shell --service azalscore-api

# Vérifier l'état des migrations
alembic current

# Forcer une migration
alembic upgrade head --sql | psql $DATABASE_URL
```

## Liens utiles

- Documentation Render: https://render.com/docs
- Status: https://status.render.com
- Communauté: https://community.render.com
