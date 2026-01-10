# AZALSCORE - Déploiement sur Fly.io

## Vue d'ensemble

Fly.io permet de déployer des applications au plus près des utilisateurs grâce à son réseau edge mondial.

## Prérequis

- Compte Fly.io (https://fly.io)
- Fly CLI installé

```bash
# Installer flyctl
curl -L https://fly.io/install.sh | sh

# Ou sur macOS
brew install flyctl

# Se connecter
fly auth login
```

## Configuration

### 1. Fichier fly.toml

Créez `fly.toml` à la racine du projet:

```toml
# AZALSCORE - Configuration Fly.io

app = "azalscore"
primary_region = "cdg"  # Paris

[build]
  dockerfile = "Dockerfile.prod"

[env]
  ENVIRONMENT = "production"
  DEBUG = "false"
  LOG_LEVEL = "INFO"
  DB_STRICT_UUID = "true"
  DB_RESET_UUID = "false"
  DB_AUTO_RESET_ON_VIOLATION = "false"
  DB_POOL_SIZE = "10"
  DB_MAX_OVERFLOW = "20"
  RATE_LIMIT_PER_MINUTE = "60"
  AUTH_RATE_LIMIT_PER_MINUTE = "5"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [http_service.concurrency]
    type = "connections"
    hard_limit = 100
    soft_limit = 80

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512

[deploy]
  release_command = "alembic upgrade head"

[processes]
  app = "gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:8000 --timeout 120"
```

### 2. Créer l'application

```bash
# Créer l'application
fly launch --no-deploy

# Choisir une région proche des utilisateurs
# cdg = Paris, fra = Frankfurt, lhr = Londres
```

### 3. Créer la base de données PostgreSQL

```bash
# Créer un cluster PostgreSQL
fly postgres create --name azalscore-db --region cdg

# Attacher à l'application
fly postgres attach azalscore-db --app azalscore
```

Cela crée automatiquement la variable `DATABASE_URL`.

### 4. Configurer les secrets

```bash
# Générer et définir les secrets
fly secrets set SECRET_KEY=$(openssl rand -hex 32)
fly secrets set BOOTSTRAP_SECRET=$(openssl rand -hex 32)
fly secrets set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# CORS (remplacer par votre domaine)
fly secrets set CORS_ORIGINS=https://azalscore.fly.dev
```

### 5. Déployer

```bash
# Premier déploiement
fly deploy

# Vérifier le statut
fly status

# Voir les logs
fly logs
```

## Configuration avancée

### Scaling automatique

```toml
# Dans fly.toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

# Ou scaling manuel
# fly scale count 3
```

### Scaling des ressources

```bash
# Augmenter la mémoire
fly scale memory 1024

# Augmenter les CPUs
fly scale vm shared-cpu-2x
```

### Multi-région

```bash
# Ajouter une région
fly regions add ams  # Amsterdam

# Lister les régions
fly regions list

# Déployer dans toutes les régions
fly deploy
```

### Redis (optionnel)

```bash
# Créer un Redis
fly redis create --name azalscore-redis --region cdg

# Le connecter
fly redis connect azalscore-redis
```

Ajoutez dans `fly.toml`:

```toml
[env]
  REDIS_URL = "redis://default:password@azalscore-redis.internal:6379"
```

## Volumes persistants

Pour les fichiers uploadés:

```bash
# Créer un volume
fly volumes create azalscore_data --size 10 --region cdg

# Configurer dans fly.toml
[mounts]
  source = "azalscore_data"
  destination = "/app/data"
```

## Secrets management

```bash
# Lister les secrets
fly secrets list

# Ajouter un secret
fly secrets set KEY=value

# Supprimer un secret
fly secrets unset KEY

# Importer depuis un fichier
fly secrets import < .env.prod
```

## Domaine personnalisé

```bash
# Ajouter un domaine
fly certs create votre-domaine.com

# Vérifier le certificat
fly certs show votre-domaine.com

# Mettre à jour CORS
fly secrets set CORS_ORIGINS=https://votre-domaine.com
```

Configurez le DNS:
- Type A: `@` → IP fournie par Fly
- Type AAAA: `@` → IPv6 fournie par Fly

## Déploiement continu

### GitHub Actions

Créez `.github/workflows/fly-deploy.yml`:

```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: superfly/flyctl-actions/setup-flyctl@master

      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Générez un token:

```bash
fly tokens create deploy -x 999999h
```

Ajoutez-le comme secret GitHub: `FLY_API_TOKEN`

## Surveillance

### Métriques

```bash
# Voir les métriques
fly dashboard

# Ou via CLI
fly status
fly vm status
```

### Logs

```bash
# Logs en temps réel
fly logs

# Logs d'une machine spécifique
fly logs --instance <instance-id>
```

### Monitoring externe

Intégrez avec:
- Prometheus: endpoint `/metrics`
- Sentry: tracking d'erreurs
- Uptime monitoring

## Base de données

### Connexion

```bash
# Connexion interactive
fly postgres connect -a azalscore-db

# Proxy local
fly proxy 5432 -a azalscore-db
# Puis: psql postgresql://postgres:password@localhost:5432/azals
```

### Sauvegardes

```bash
# Lister les sauvegardes
fly postgres list -a azalscore-db

# Créer une sauvegarde manuelle
fly postgres backup create -a azalscore-db

# Restaurer
fly postgres backup restore <backup-id> -a azalscore-db
```

### Migrations

```bash
# Exécuter les migrations
fly ssh console -C "alembic upgrade head"

# Ou via release_command dans fly.toml
[deploy]
  release_command = "alembic upgrade head"
```

## Checklist de sécurité

- [ ] `DEBUG=false`
- [ ] Tous les secrets définis via `fly secrets set`
- [ ] `CORS_ORIGINS` configuré (pas de localhost)
- [ ] `DB_STRICT_UUID=true`
- [ ] `DB_RESET_UUID=false`
- [ ] `DB_AUTO_RESET_ON_VIOLATION=false`
- [ ] `force_https = true` dans fly.toml
- [ ] Domaine personnalisé avec certificat SSL
- [ ] Sauvegardes PostgreSQL activées
- [ ] Health checks configurés

## Dépannage

### L'application ne démarre pas

```bash
# Voir les logs de déploiement
fly logs --app azalscore

# Se connecter en SSH
fly ssh console

# Tester l'application
python -c "from app.main import app"
```

### Problèmes de connexion DB

```bash
# Vérifier la connexion
fly postgres connect -a azalscore-db

# Vérifier DATABASE_URL
fly secrets list
```

### Migrations échouées

```bash
# Exécuter manuellement
fly ssh console
alembic upgrade head

# Voir l'historique
alembic history
```

### Machine qui ne répond pas

```bash
# Lister les machines
fly machines list

# Redémarrer une machine
fly machines restart <machine-id>

# Détruire et recréer
fly machines destroy <machine-id>
fly deploy
```

## Coûts estimés

| Ressource | Specs | Prix/mois |
|-----------|-------|-----------|
| VM shared-cpu-1x | 256MB RAM | ~$2 |
| VM shared-cpu-2x | 512MB RAM | ~$4 |
| PostgreSQL | 1GB | ~$7 |
| Volume 10GB | SSD | ~$1.5 |
| Certificat SSL | Inclus | $0 |
| Bandwidth | 100GB | Inclus |

Pour AZALSCORE: ~$15-30/mois en production légère.

## Liens utiles

- Documentation: https://fly.io/docs
- Status: https://status.fly.io
- Community: https://community.fly.io
- Pricing: https://fly.io/docs/about/pricing/
