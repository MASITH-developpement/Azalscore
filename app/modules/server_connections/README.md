# Module Server Connections - Azalscore

Module de gestion des connexions aux serveurs distants pour le déploiement et la gestion du code Azalscore.

## Fonctionnalités

- **Connexions SSH/SFTP sécurisées** : Authentification par mot de passe ou clé SSH
- **Gestion des identifiants chiffrés** : Stockage sécurisé avec chiffrement AES-256
- **Exécution de commandes à distance** : Shell, Git, Docker, commandes Azalscore
- **Transfert de fichiers** : Upload/Download via SFTP
- **Surveillance de l'état des serveurs** : Health checks automatiques
- **Déploiement et mise à jour** : Git pull, build, migrations, restart

## Configuration du serveur de production

### Adresse par défaut
- **Host**: 192.168.1.185
- **Port**: 22
- **Chemin Azalscore**: /opt/azalscore

### Via l'API REST

```bash
# 1. Obtenir un token JWT
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: masith" \
  -d '{"email": "admin@masith.fr", "password": "votre_mot_de_passe"}'

# 2. Créer le serveur
curl -X POST http://localhost:8000/v1/servers \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: masith" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "azals-production",
    "host": "192.168.1.185",
    "port": 22,
    "username": "azalscore",
    "password": "votre_mot_de_passe_ssh",
    "role": "PRODUCTION",
    "azalscore_path": "/opt/azalscore",
    "is_default": true
  }'
```

### Via le script de configuration

```bash
# Test de connexion
PROD_SERVER_PASSWORD=secret python -m app.modules.server_connections.setup_production_server test

# Créer via l'API
AZALS_API_TOKEN=xxx PROD_SERVER_PASSWORD=yyy python -m app.modules.server_connections.setup_production_server create
```

## Endpoints API

### Gestion des serveurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/servers` | Lister les serveurs |
| POST | `/v1/servers` | Créer un serveur |
| GET | `/v1/servers/{id}` | Détails d'un serveur |
| PUT | `/v1/servers/{id}` | Modifier un serveur |
| DELETE | `/v1/servers/{id}` | Supprimer un serveur |
| GET | `/v1/servers/default` | Serveur par défaut |

### Connexion et exécution

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/servers/{id}/connect` | Établir la connexion SSH |
| POST | `/v1/servers/{id}/disconnect` | Fermer la connexion |
| POST | `/v1/servers/{id}/execute` | Exécuter une commande |
| GET | `/v1/servers/{id}/commands` | Historique des commandes |
| POST | `/v1/servers/test-connection` | Tester une connexion |

### Commandes rapides

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/servers/{id}/quick-commands` | Liste des commandes |
| POST | `/v1/servers/{id}/quick-commands/{name}` | Exécuter une commande rapide |

**Commandes disponibles:**
- `status` - Statut d'Azalscore (docker-compose ps)
- `logs` - Logs récents
- `restart` - Redémarrer Azalscore
- `stop` / `start` - Arrêter / Démarrer
- `update` - Mettre à jour depuis Git
- `disk` / `memory` - Infos système
- `docker_ps` - Conteneurs Docker
- `git_status` / `git_log` - Infos Git
- `version` - Version Azalscore

### Santé et surveillance

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/servers/{id}/health-check` | Vérification de santé |
| GET | `/v1/servers/{id}/health-history` | Historique des checks |
| GET | `/v1/servers/{id}/dashboard` | Dashboard complet |

### Déploiements

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/servers/{id}/deploy` | Lancer un déploiement |
| GET | `/v1/servers/{id}/deployments` | Historique |
| GET | `/v1/servers/{id}/deployments/{id}` | Détails |

### Git et Docker

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/servers/{id}/git/status` | Statut Git |
| POST | `/v1/servers/{id}/git/pull` | Git pull |
| GET | `/v1/servers/{id}/docker/containers` | Liste conteneurs |
| POST | `/v1/servers/{id}/docker/compose` | Action Docker Compose |

### Fichiers

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/servers/{id}/files/transfer` | Transfert de fichier |
| POST | `/v1/servers/{id}/files/list` | Lister les fichiers |

## Exemples d'utilisation

### Exécuter une commande

```bash
curl -X POST http://localhost:8000/v1/servers/1/execute \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: masith" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "docker-compose ps",
    "timeout_ms": 30000
  }'
```

### Vérifier la santé

```bash
curl -X POST http://localhost:8000/v1/servers/1/health-check \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: masith"
```

### Déployer une mise à jour

```bash
curl -X POST http://localhost:8000/v1/servers/1/deploy \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: masith" \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_type": "update",
    "git_branch": "main",
    "run_migrations": true,
    "restart_services": true,
    "backup_first": true
  }'
```

### Redémarrer Azalscore (commande rapide)

```bash
curl -X POST http://localhost:8000/v1/servers/1/quick-commands/restart \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: masith"
```

## Sécurité

- Les identifiants (mot de passe, clés SSH) sont chiffrés avec AES-256
- Les connexions nécessitent un rôle ADMIN ou supérieur
- Toutes les actions sont journalisées dans les événements serveur
- Les commandes sont enregistrées avec l'utilisateur exécutant

## Structure des fichiers

```
app/modules/server_connections/
├── __init__.py          # Configuration par défaut
├── models.py            # Modèles SQLAlchemy
├── schemas.py           # Schémas Pydantic
├── service.py           # Logique métier
├── router.py            # Endpoints API
├── setup_production_server.py  # Script de configuration
├── README.md            # Cette documentation
└── clients/
    ├── __init__.py
    └── ssh.py           # Client SSH/SFTP
```
