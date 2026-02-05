# AZALSCORE - Reference des Variables d'Environnement

Ce document liste toutes les variables d'environnement configurables pour le systeme AZALSCORE.

## Table des Matieres

1. [Application](#application)
2. [Base de Donnees PostgreSQL](#base-de-donnees-postgresql)
3. [Redis](#redis)
4. [Securite](#securite)
5. [Rate Limiting](#rate-limiting)
6. [Timeouts](#timeouts)
7. [URLs Application](#urls-application)
8. [Nginx](#nginx)
9. [Prometheus](#prometheus)
10. [Grafana](#grafana)
11. [Loki & Promtail](#loki--promtail)
12. [Stripe (Paiement)](#stripe-paiement)
13. [SMTP (Email)](#smtp-email)
14. [Backup](#backup)
15. [Tenant Initial](#tenant-initial)
16. [Gunicorn](#gunicorn)
17. [Docker Resources](#docker-resources)
18. [Logging](#logging)

---

## Application

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `VERSION` | Version de l'application | - | Non |
| `ENVIRONMENT` | Environnement (development, staging, production) | development | Oui |
| `AZALS_ENV` | Alias pour ENVIRONMENT | development | Non |
| `DEBUG` | Mode debug (true/false) | false | Non |
| `LOG_LEVEL` | Niveau de log (DEBUG, INFO, WARNING, ERROR) | INFO | Non |
| `LOG_JSON` | Format JSON pour les logs (true/false) | true | Non |

---

## Base de Donnees PostgreSQL

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `POSTGRES_VERSION` | Version image Docker PostgreSQL | 15-alpine | Non |
| `POSTGRES_DB` | Nom de la base de donnees | azals | Oui |
| `POSTGRES_USER` | Utilisateur PostgreSQL | - | Oui |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | - | Oui |
| `POSTGRES_BIND` | Adresse IP de binding | 127.0.0.1 | Non |
| `POSTGRES_PORT` | Port PostgreSQL | 5432 | Non |
| `DATABASE_URL` | URL complete de connexion | - | Oui |
| `DB_POOL_SIZE` | Taille du pool de connexions | 10 | Non |
| `DB_MAX_OVERFLOW` | Connexions supplementaires max | 20 | Non |

**Format DATABASE_URL:**
```
postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{host}:{POSTGRES_PORT}/{POSTGRES_DB}
```

---

## Redis

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `REDIS_VERSION` | Version image Docker Redis | 7-alpine | Non |
| `REDIS_BIND` | Adresse IP de binding | 127.0.0.1 | Non |
| `REDIS_PORT` | Port Redis | 6379 | Non |
| `REDIS_URL` | URL complete de connexion | - | Oui (prod) |
| `REDIS_MAXMEMORY` | Memoire maximum Redis | 256mb | Non |
| `REDIS_TIMEOUT` | Timeout connexion en secondes | 5 | Non |
| `REDIS_HEALTH_TIMEOUT` | Timeout health check en secondes | 2 | Non |

**Format REDIS_URL:**
```
redis://{host}:{REDIS_PORT}/0
```

---

## Securite

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `SECRET_KEY` | Cle secrete JWT (min 32 caracteres) | - | **Oui** |
| `BOOTSTRAP_SECRET` | Secret pour bootstrap initial | - | **Oui (prod)** |
| `ENCRYPTION_KEY` | Cle Fernet pour chiffrement AES-256 | - | **Oui (prod)** |
| `CORS_ORIGINS` | Origins CORS autorisees (separees par virgule) | - | Non |
| `CORS_MAX_AGE` | Duree cache CORS en secondes | 3600 | Non |

**Generation des cles:**
```bash
# SECRET_KEY ou BOOTSTRAP_SECRET
python -c "import secrets; print(secrets.token_urlsafe(64))"

# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Rate Limiting

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `RATE_LIMIT_PER_MINUTE` | Limite globale requetes/minute | 100 | Non |
| `AUTH_RATE_LIMIT_PER_MINUTE` | Limite auth requetes/minute | 5 | Non |

---

## Timeouts

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `API_TIMEOUT_MS` | Timeout API par defaut en millisecondes | 30000 | Non |

---

## URLs Application

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `APP_URL` | URL publique complete de l'application | https://localhost | Non |
| `APP_DOMAIN` | Domaine principal | localhost | Non |

**Exemple:**
```
APP_URL=https://azalscore.com
APP_DOMAIN=azalscore.com
```

---

## Nginx

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `NGINX_VERSION` | Version image Docker Nginx | alpine | Non |
| `NGINX_BIND` | Adresse IP de binding | 127.0.0.1 | Non |
| `NGINX_HTTP_PORT` | Port HTTP interne | 8080 | Non |
| `NGINX_HTTPS_PORT` | Port HTTPS interne | 8443 | Non |

---

## Prometheus

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `PROMETHEUS_VERSION` | Version image Docker Prometheus | v2.45.0 | Non |
| `PROMETHEUS_BIND` | Adresse IP de binding | 0.0.0.0 | Non |
| `PROMETHEUS_PORT` | Port Prometheus | 9090 | Non |
| `PROMETHEUS_RETENTION` | Duree retention donnees | 30d | Non |

---

## Grafana

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `GRAFANA_VERSION` | Version image Docker Grafana | 10.0.0 | Non |
| `GRAFANA_BIND` | Adresse IP de binding | 0.0.0.0 | Non |
| `GRAFANA_PORT` | Port Grafana | 3000 | Non |
| `GRAFANA_USER` | Utilisateur admin | admin | Non |
| `GRAFANA_PASSWORD` | Mot de passe admin | - | **Oui (prod)** |
| `GF_SECURITY_ADMIN_USER` | Utilisateur admin (env Grafana) | admin | Non |
| `GF_SECURITY_ADMIN_PASSWORD` | Mot de passe admin (env Grafana) | - | **Oui (prod)** |
| `GF_USERS_ALLOW_SIGN_UP` | Autoriser inscription | false | Non |
| `GF_SERVER_ROOT_URL` | URL racine Grafana | - | Non |
| `GF_SERVER_SERVE_FROM_SUB_PATH` | Servir depuis sous-chemin | true | Non |

---

## Loki & Promtail

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `LOKI_VERSION` | Version image Docker Loki | 2.8.0 | Non |
| `LOKI_BIND` | Adresse IP de binding | 127.0.0.1 | Non |
| `LOKI_PORT` | Port Loki | 3100 | Non |
| `PROMTAIL_VERSION` | Version image Docker Promtail | 2.8.0 | Non |

---

## Stripe (Paiement)

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `STRIPE_SECRET_KEY` | Cle secrete Stripe | - | Oui (si paiement) |
| `STRIPE_PUBLISHABLE_KEY` | Cle publique Stripe | - | Oui (si paiement) |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe | - | Oui (si paiement) |

---

## SMTP (Email)

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `SMTP_HOST` | Serveur SMTP | localhost | Non |
| `SMTP_PORT` | Port SMTP | 1025 | Non |
| `SMTP_USER` | Utilisateur SMTP | - | Non |
| `SMTP_PASSWORD` | Mot de passe SMTP | - | Non |
| `SMTP_FROM` | Adresse expediteur | - | Non |
| `SMTP_USE_TLS` | Utiliser TLS | false | Non |

---

## Backup

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `BACKUP_STORAGE_PATH` | Chemin stockage backups | /app/backups | Non |

---

## Tenant Initial

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `MASITH_TENANT_ID` | ID du tenant initial | masith | Non |
| `MASITH_ADMIN_EMAIL` | Email admin initial | - | **Oui (bootstrap)** |
| `MASITH_ADMIN_PASSWORD` | Mot de passe admin initial (min 12 car.) | - | **Oui (bootstrap)** |

---

## Gunicorn

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `GUNICORN_WORKERS` | Nombre de workers | 1 | Non |
| `GUNICORN_THREADS` | Threads par worker | 2 | Non |

**Recommandation production:**
```
GUNICORN_WORKERS = (2 * CPU_CORES) + 1
GUNICORN_THREADS = 2-4
```

---

## Docker Resources

### Limites Memoire

| Variable | Description | Defaut |
|----------|-------------|--------|
| `API_MEMORY_LIMIT` | Limite memoire API | 2G |
| `API_MEMORY_RESERVATION` | Reservation memoire API | 512M |
| `POSTGRES_MEMORY_LIMIT` | Limite memoire PostgreSQL | 2G |
| `POSTGRES_MEMORY_RESERVATION` | Reservation memoire PostgreSQL | 512M |
| `REDIS_MEMORY_LIMIT` | Limite memoire Redis | 512M |
| `REDIS_MEMORY_RESERVATION` | Reservation memoire Redis | 64M |
| `FRONTEND_MEMORY_LIMIT` | Limite memoire Frontend | 128M |
| `FRONTEND_MEMORY_RESERVATION` | Reservation memoire Frontend | 32M |
| `NGINX_MEMORY_LIMIT` | Limite memoire Nginx | 256M |
| `NGINX_MEMORY_RESERVATION` | Reservation memoire Nginx | 64M |
| `PROMETHEUS_MEMORY_LIMIT` | Limite memoire Prometheus | 512M |
| `PROMETHEUS_MEMORY_RESERVATION` | Reservation memoire Prometheus | 128M |
| `GRAFANA_MEMORY_LIMIT` | Limite memoire Grafana | 256M |
| `GRAFANA_MEMORY_RESERVATION` | Reservation memoire Grafana | 64M |
| `LOKI_MEMORY_LIMIT` | Limite memoire Loki | 256M |
| `LOKI_MEMORY_RESERVATION` | Reservation memoire Loki | 64M |
| `PROMTAIL_MEMORY_LIMIT` | Limite memoire Promtail | 128M |
| `PROMTAIL_MEMORY_RESERVATION` | Reservation memoire Promtail | 32M |

---

## Logging

| Variable | Description | Defaut | Obligatoire |
|----------|-------------|--------|-------------|
| `LOG_MAX_SIZE` | Taille max fichier log | 100m | Non |
| `LOG_MAX_FILES` | Nombre max fichiers log | 5 | Non |
| `LOG_VERBOSE` | Mode verbose (log tout en DEBUG) | false | Non |
| `LOG_REQUESTS` | Log toutes les requetes HTTP | false | Non |

**Mode Verbose:**
Quand `LOG_VERBOSE=true`:
- Tous les loggers passent en niveau DEBUG
- Les requetes/reponses HTTP sont loguees avec details
- Les requetes SQL sont visibles
- Ideal pour debug en production

**Activation temporaire:**
```bash
# Activer le mode verbose
docker exec api sh -c 'export LOG_VERBOSE=true && kill -HUP 1'
```

---

## Variables Internes (Non Modifiables)

Ces variables sont gerees automatiquement par le systeme:

| Variable | Description |
|----------|-------------|
| `DB_RESET_UUID` | Mode reset UUID (dev only) |
| `DB_STRICT_UUID` | Mode strict UUID |
| `DB_AUTO_RESET_ON_VIOLATION` | Reset auto sur violation UUID |

---

## Exemple .env.production Minimal

```bash
# OBLIGATOIRES
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg2://user:password@postgres:5432/azals
SECRET_KEY=your-secret-key-min-32-chars
BOOTSTRAP_SECRET=your-bootstrap-secret
ENCRYPTION_KEY=your-fernet-key

# TENANT INITIAL
MASITH_ADMIN_EMAIL=admin@example.com
MASITH_ADMIN_PASSWORD=your-secure-password-12-chars

# RECOMMANDES
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=https://yourdomain.com
APP_URL=https://yourdomain.com
GRAFANA_PASSWORD=secure-grafana-password
GF_SECURITY_ADMIN_PASSWORD=secure-grafana-password
```

---

## Bonnes Pratiques

1. **Ne jamais commiter `.env.production`** - Utilisez `.env.production.example` comme template
2. **Utilisez des secrets forts** - Minimum 32 caracteres pour les cles
3. **Changez les mots de passe par defaut** - Notamment Grafana et admin
4. **Configurez CORS strictement** - Listez uniquement les domaines autorises
5. **Ajustez les ressources Docker** - Selon la charge prevue

---

*Document genere le 2026-01-21 - AZALSCORE v0.3.0*
