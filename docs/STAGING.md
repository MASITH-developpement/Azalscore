# AZALS - Environnement Staging

Guide de déploiement et utilisation de l'environnement de pré-production.

## Vue d'ensemble

L'environnement staging est une réplique allégée de la production, utilisée pour:
- Tests d'intégration avant mise en production
- Validation par le QA et les stakeholders
- Tests de performance (charge modérée)
- Démonstrations clients

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STAGING                               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐               │
│  │  Nginx  │───│   API   │───│ Frontend│               │
│  │ :8081   │   │  :80    │   │  :80    │               │
│  └────┬────┘   └────┬────┘   └─────────┘               │
│       │             │                                    │
│  ┌────┴────┐   ┌────┴────┐                              │
│  │Postgres │   │  Redis  │                              │
│  │ :5433   │   │ :6380   │                              │
│  └─────────┘   └─────────┘                              │
│                                                          │
│  ┌──────────────────────────────────────┐               │
│  │         Monitoring (optionnel)        │               │
│  │  Prometheus :9091  │  Grafana :3001   │               │
│  └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## Prérequis

- Docker >= 24.0
- Docker Compose >= 2.20
- 4 Go RAM minimum (8 Go recommandé)
- 20 Go d'espace disque

## Installation

### 1. Configuration

```bash
# Copier le template d'environnement
cp .env.staging.example .env.staging

# Éditer et configurer les variables
nano .env.staging
```

**Variables obligatoires à modifier:**
- `POSTGRES_PASSWORD` - Mot de passe BDD
- `SECRET_KEY` - Clé JWT (générer avec `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `STRIPE_SECRET_KEY` - Clé Stripe TEST (sk_test_...)

### 2. Démarrage

```bash
# Démarrer tous les services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Vérifier le statut
docker compose -f docker-compose.staging.yml ps

# Voir les logs
docker compose -f docker-compose.staging.yml logs -f api
```

### 3. Initialisation de la base

```bash
# Exécuter les migrations
docker compose -f docker-compose.staging.yml exec api alembic upgrade head

# Créer le tenant de test
docker compose -f docker-compose.staging.yml exec api python scripts/provision_test_tenant.py
```

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8081 | Application web |
| API | http://localhost:8081/api | Endpoints API |
| API Docs | http://localhost:8081/docs | Swagger UI |
| Grafana | http://localhost:3001 | Monitoring |
| Prometheus | http://localhost:9091 | Métriques |

## Différences avec Production

| Aspect | Staging | Production |
|--------|---------|------------|
| Ressources | Réduites (50%) | Pleines |
| Rate limiting | Permissif (500r/m) | Strict (100r/m) |
| Debug | Activé | Désactivé |
| Logs | Verbeux (DEBUG) | Standard (INFO) |
| Email | Mailtrap/local | SMTP réel |
| Stripe | Clés TEST | Clés LIVE |
| SSL | Optionnel | Obligatoire |
| Rétention Prometheus | 7 jours | 30 jours |

## CI/CD

Le déploiement staging est automatique via GitHub Actions:

```yaml
# Déclenché sur push vers develop
on:
  push:
    branches: [develop]
```

### Pipeline

1. **Tests** - Unit tests, integration tests
2. **Build** - Docker image avec tag `staging`
3. **Security Scan** - Trivy, Bandit
4. **Deploy** - Push vers serveur staging
5. **Smoke Tests** - Vérification post-déploiement

## Tests

### Lancer les tests contre staging

```bash
# Tests API
pytest tests/integration/ --base-url=http://localhost:8081

# Tests E2E (Playwright)
cd frontend && npx playwright test --config=playwright.staging.config.ts
```

### Tests de charge

```bash
# k6 load test
k6 run tests/load/staging-load-test.js
```

## Maintenance

### Reset complet

```bash
# Arrêter et supprimer tous les conteneurs/volumes
docker compose -f docker-compose.staging.yml down -v

# Redémarrer proprement
docker compose -f docker-compose.staging.yml up -d
```

### Backup de la BDD staging

```bash
docker compose -f docker-compose.staging.yml exec postgres \
  pg_dump -U azals_staging_user azals_staging > staging_backup.sql
```

### Restauration depuis production (données anonymisées)

```bash
# 1. Exporter depuis prod avec anonymisation
./scripts/export_anonymized.sh production

# 2. Importer en staging
docker compose -f docker-compose.staging.yml exec -T postgres \
  psql -U azals_staging_user azals_staging < anonymized_dump.sql
```

## Troubleshooting

### L'API ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker-compose.staging.yml logs api

# Vérifier la connexion BDD
docker compose -f docker-compose.staging.yml exec api \
  python -c "from app.core.database import engine; engine.connect()"
```

### Problèmes de performance

```bash
# Vérifier les ressources
docker stats

# Augmenter les limites si nécessaire
# Modifier dans docker-compose.staging.yml
```

### Erreurs CORS

Vérifier que `CORS_ORIGINS` dans `.env.staging` inclut votre URL de test.

## Contacts

- **DevOps**: devops@azals.io
- **Backend**: backend@azals.io
- **Incidents staging**: #staging-alerts (Slack)
