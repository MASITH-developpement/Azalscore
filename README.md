# AZALSCORE - ERP SaaS Multi-tenant

> Plateforme ERP nouvelle generation - Comptabilite automatique & Cockpit decisionnel

## Demarrage rapide

```bash
# Lancer l'application
docker-compose up --build

# Acces
# API:  http://localhost:8000
# UI:   http://localhost:5173
# Docs: http://localhost:8000/docs
```

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend   | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| Frontend  | React 18, TypeScript, Vite, TanStack Query |
| Database  | PostgreSQL 15, Redis |
| Tests     | pytest (backend), Playwright (frontend) |
| Infra     | Docker, Nginx, Prometheus, Grafana |

## Modules metier

### Finance
- **Comptabilite** - Plan comptable, ecritures, exercices fiscaux
- **Tresorerie** - Comptes bancaires, rapprochements, previsions
- **Achats** - Fournisseurs, commandes, factures fournisseurs
- **Facturation** - Devis, factures clients, avoirs

### CRM & Commercial
- **CRM** - Clients, prospects, opportunites
- **Helpdesk** - Tickets support, SLA, base connaissances

### Operations
- **Stock** - Produits, inventaire, mouvements
- **Production** - Ordres fabrication, nomenclatures
- **Field Service** - Interventions terrain, planning techniciens

### RH & Administration
- **RH** - Employes, contrats, conges
- **IAM** - Utilisateurs, roles, permissions RBAC
- **Audit** - Traces, conformite, logs

### Intelligence Artificielle
- **Theo** - Assistant IA conversationnel
- **Guardian** - Auto-healing et detection anomalies

## Architecture

```
azalscore/
├── app/                    # Backend FastAPI (39 modules)
│   ├── api/               # Routes API v1/v2
│   ├── core/              # CORE SaaS (auth, multi-tenant, middleware)
│   ├── modules/           # Modules metier
│   └── theo/              # Assistant IA
├── frontend/              # React TypeScript (41 modules)
│   ├── src/modules/       # Modules UI
│   └── src/ui-engine/     # Composants partages
├── infra/                 # Configuration infrastructure
└── docs/                  # Documentation
```

### Patterns cles
- **Multi-tenant strict** : Isolation complete par `tenant_id`
- **CORE SaaS v2** : `SaaSContext` injecte automatiquement
- **API versioning** : v1 (legacy) et v2 (migre) cohabitent
- **RBAC** : Permissions granulaires par module/action

## Documentation

| Section | Description |
|---------|-------------|
| [docs/guides/](docs/guides/) | Demarrage, conventions, routines |
| [docs/architecture/](docs/architecture/) | Decisions techniques, patterns |
| [docs/migration/](docs/migration/) | Etat migration v2, roadmap |
| [docs/audits/](docs/audits/) | Rapports, analyses, sessions |

## Tests

```bash
# Backend
cd app && pytest -v

# Frontend E2E
cd frontend && npm run test:e2e
```

## License

Proprietary - MASITH Developpement
