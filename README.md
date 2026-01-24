# AZALSCORE - ERP Décisionnel Orienté Gestion

## Identité du produit

**AZALSCORE** est un ERP nouvelle génération conçu pour les TPE/PME qui combine :

### 🎯 Trois piliers fondamentaux

1. **Saisie métier ultra-simplifiée**
   - Interface épurée pour utilisateurs non-comptables
   - Langage naturel (pas de jargon ERP)
   - Prise en main seul en moins de 3 secondes
   - Zéro formation requise

2. **Comptabilité automatique**
   - Génération automatique des écritures comptables
   - Export comptable pour expert-comptable
   - Aucune connaissance comptable requise
   - Conforme aux normes françaises

3. **Cockpit décisionnel intelligent**
   - Détection automatique des risques critiques (🔴🟠🟢)
   - Priorisation stricte : Trésorerie > Juridique > Fiscal > RH > Compta
   - Vision en temps réel de la santé de l'entreprise
   - Alertes contextuelles pour le dirigeant

### 💡 Philosophie : "De la saisie à la décision"

```
Saisie métier simplifiée
         ↓
Comptabilité automatique
         ↓
Éléments de gestion
         ↓
Cockpit Dirigeant (décisions)
```

### 👥 Public cible : De la TPE à la Grande Entreprise

**AZALSCORE s'adapte à TOUTES les tailles d'entreprise** :

- **Mode AZALSCORE** → TPE/PME, dirigeants non-financiers, équipes sans formation ERP
- **Mode ERP** → Grandes entreprises, experts-comptables, DAF, contrôleurs de gestion

**Avantage unique** : Pas besoin de changer de logiciel en grandissant. L'entreprise évolue, l'interface s'adapte.

### 🎨 Dualité des modes

- **Mode AZALSCORE** (défaut) : Interface épurée, cockpit-first, prise en main 3 secondes
- **Mode ERP** (optionnel) : Interface complète avec navigation horizontale et fonctionnalités avancées

Un seul produit, deux interfaces, tous les besoins couverts.

---

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
