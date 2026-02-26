# AZALSCORE - Configuration des Environnements

## Vue d'ensemble

| Environnement | Branch | URL | Deploiement |
|---------------|--------|-----|-------------|
| **Production** | `main` | `$PRODUCTION_URL` | Auto (apres review) |
| **Staging** | `develop` | `$STAGING_URL` | Auto |
| **Preview** | PR | `pr-<id>.azals.dev` | Auto |
| **Local** | - | `localhost:8000` | Manuel |

## Configuration GitHub Environments

### 1. Creer les environnements

Dans GitHub > Settings > Environments:

#### Environment: `staging`

```yaml
# Variables
STAGING_URL: https://staging.azalscore.com

# Secrets
STAGING_DATABASE_URL: postgresql://user:pass@host:5432/azals_staging
RENDER_STAGING_SERVICE_ID: srv-xxxxx
```

#### Environment: `production`

```yaml
# Protection rules
- Required reviewers: 2
- Wait timer: 15 minutes (optionnel)
- Restrict to branches: main

# Variables
PRODUCTION_URL: https://azalscore.com

# Secrets
PRODUCTION_DATABASE_URL: postgresql://user:pass@host:5432/azals_prod
RENDER_PRODUCTION_SERVICE_ID: srv-yyyyy
```

### 2. Secrets globaux requis

```yaml
# Render deployment
RENDER_API_KEY: rnd_xxxxx

# SonarCloud
SONAR_TOKEN: sqp_xxxxx

# Notifications
SLACK_WEBHOOK: https://hooks.slack.com/services/xxx

# Container registry (auto avec GITHUB_TOKEN)
# Pas de configuration supplementaire
```

## Infrastructure Staging

### Architecture

```
                    ┌─────────────────────────────────────┐
                    │           STAGING ENV               │
                    ├─────────────────────────────────────┤
                    │                                     │
  develop ─────────>│   Render Web Service                │
  (auto deploy)     │   ├── API Backend (Python 3.11)    │
                    │   └── Port 80                      │
                    │                                     │
                    │   PostgreSQL 15                     │
                    │   ├── Database: azals_staging      │
                    │   └── SSL required                 │
                    │                                     │
                    │   Redis 7                          │
                    │   └── Cache & sessions             │
                    │                                     │
                    └─────────────────────────────────────┘
```

### Base de donnees staging

```sql
-- Creation (une seule fois)
CREATE DATABASE azals_staging;
CREATE USER azals_staging WITH PASSWORD 'xxx';
GRANT ALL PRIVILEGES ON DATABASE azals_staging TO azals_staging;

-- Extensions requises
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Variables d'environnement staging

```bash
# Application
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@host:5432/azals_staging
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0

# Security
SECRET_KEY=<32-char-key>
ENCRYPTION_KEY=<32-char-key>
CORS_ORIGINS=https://staging.azalscore.com,https://staging-app.azalscore.com

# External services (mode test/sandbox)
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_test_xxx
RESEND_API_KEY=re_test_xxx

# Features
FEATURE_FLAG_NEW_UI=true
FEATURE_FLAG_AI_ASSISTANT=true
```

## Deploiement local

### Prerequisites

```bash
# Python 3.11+
python --version  # 3.11.x

# Docker & Docker Compose
docker --version
docker-compose --version

# PostgreSQL client (optionnel)
psql --version
```

### Setup

```bash
# 1. Clone
git clone https://github.com/azals/azalscore.git
cd azalscore

# 2. Environment
cp .env.example .env
# Editer .env avec vos valeurs

# 3. Dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Database
docker-compose up -d postgres redis

# 5. Migrations
alembic upgrade head

# 6. Run
uvicorn app.main:app --reload --port 8000
```

### Docker Compose local

```bash
# Full stack
docker-compose up -d

# Logs
docker-compose logs -f api

# Reset database
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

## Monitoring

### Health checks

```bash
# Staging
curl https://staging.azalscore.com/health
curl https://staging.azalscore.com/health/ready
curl https://staging.azalscore.com/health/live

# Production
curl https://azalscore.com/health
```

### Endpoints de monitoring

| Endpoint | Description |
|----------|-------------|
| `/health` | Health check complet |
| `/health/live` | Liveness probe (Kubernetes) |
| `/health/ready` | Readiness probe |
| `/metrics` | Prometheus metrics |
| `/api/status` | Status API v3 |

### Alertes

- **Slack**: #alerts-staging, #alerts-production
- **PagerDuty**: Production only
- **Email**: ops@azals.io

## Rollback

### Procedure de rollback

```bash
# 1. Identifier la derniere version stable
git log --oneline main

# 2. Revert ou deploy version specifique
# Via Render UI: Deploy > Select commit

# 3. Rollback database (si necessaire)
alembic downgrade -1

# 4. Verifier
curl https://azalscore.com/health
```

### Points de controle post-deploy

1. Health check OK
2. API docs accessible (`/docs`)
3. Login fonctionnel
4. Requetes DB OK (pas d'erreurs dans logs)
5. Redis connecte
6. Metrics endpoint OK
