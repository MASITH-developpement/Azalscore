# AZALS - ERP Décisionnel Critique

## Architecture Technique

### Stack
- **Python**: 3.11
- **Framework**: FastAPI
- **Base de données**: PostgreSQL 15
- **Orchestration**: Docker + docker-compose
- **Tests**: pytest

## Structure du Projet

```
azals/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   └── core/
│       ├── __init__.py
│       ├── config.py        # Configuration sécurisée
│       └── database.py      # Connexion PostgreSQL
├── tests/
│   ├── __init__.py
│   └── test_health.py       # Tests de l'endpoint /health
├── docker-compose.yml       # Orchestration des services
├── Dockerfile              # Image Docker de l'API
├── requirements.txt        # Dépendances Python
├── pytest.ini             # Configuration des tests
├── .env.example           # Template des variables d'environnement
└── README.md
```

## Démarrage Rapide

### 1. Lancer le projet

```bash
docker-compose up --build
```

### 2. Vérifier que tout fonctionne

Accéder à : http://localhost:8000/health

Réponse attendue :
```json
{
  "status": "ok",
  "api": true,
  "database": true
}
```

### 3. Exécuter les tests

```bash
# Dans un terminal séparé
docker-compose exec api pytest
```

ou depuis l'hôte (si pytest installé localement) :
```bash
pytest
```

## Arrêt du Projet

```bash
docker-compose down
```

Pour supprimer également les volumes (données PostgreSQL) :
```bash
docker-compose down -v
```

## Configuration

Les variables d'environnement sont définies dans `docker-compose.yml`.

Pour une configuration locale, copier `.env.example` vers `.env` :
```bash
cp .env.example .env
```

## Endpoints Disponibles

### GET /health
Point de santé de l'API et de la base de données.

**Réponse :**
```json
{
  "status": "ok|degraded",
  "api": true,
  "database": true|false
}
```

## Sécurité

- Pas de documentation Swagger exposée en production (`docs_url=None`)
- Validation stricte des variables d'environnement via Pydantic
- Connexion PostgreSQL avec pool de connexions configuré
- Architecture prête pour multi-tenant

## Développement

### Ajouter une dépendance

1. Ajouter dans `requirements.txt`
2. Rebuild l'image : `docker-compose up --build`

### Exécuter des commandes dans le container

```bash
docker-compose exec api bash
```

## Prochaines Étapes

- [ ] Authentification JWT
- [ ] Modèle multi-tenant
- [ ] Migrations Alembic
- [ ] Modules métier (finance, RH, juridique)
- [ ] CI/CD
