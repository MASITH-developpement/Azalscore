# AZALSCORE API MAP
**Version 3.1.0 | Derniere mise a jour: 2026-02-16**

---

## Vue d'ensemble

Ce document reference tous les modules API v3 et leurs endpoints.
Source unique de verite: `/app/api/v3/__init__.py`

---

## Architecture des Routes

```
/api/v1/       # Routes legacy (deprecated)
/api/v2/       # Routes v2 (transition)
/api/v3/       # Routes v3 unifiees (actif)
  ├─ /{module}/           # Prefix du module
  │   ├─ /status          # Statut du module
  │   ├─ /                # Liste (GET) / Creation (POST)
  │   ├─ /{id}            # Detail (GET) / Mise a jour (PUT) / Suppression (DELETE)
  │   └─ /{id}/{action}   # Actions sur une ressource
```

---

## Modules par Priorite

### CRITICAL (P0) - Requis pour le fonctionnement de base

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `commercial` | `app.modules.commercial.router_crud` | `/commercial` | Clients, documents, devis, factures |
| `contacts` | `app.modules.contacts.router_crud` | `/contacts` | Personnes, adresses, coordonnees |
| `hr` | `app.modules.hr.router_crud` | `/hr` | Employes, departements, conges |
| `interventions` | `app.modules.interventions.router_crud` | `/interventions` | Ordres de service, planification terrain |
| `inventory` | `app.modules.inventory.router_crud` | `/inventory` | Produits, stocks, mouvements |

### IMPORTANT (P1) - Fonctionnalites metier principales

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `accounting` | `app.modules.accounting.router_unified` | `/accounting` | Comptabilite, ecritures, rapprochement |
| `treasury` | `app.modules.treasury.router_crud` | `/treasury` | Tresorerie, comptes bancaires |
| `purchases` | `app.modules.purchases.router_crud` | `/purchases` | Achats, fournisseurs, commandes |
| `production` | `app.modules.production.router_crud` | `/production` | Ordres de fabrication, centres de travail |
| `projects` | `app.modules.projects.router_crud` | `/projects` | Projets, taches, temps |
| `maintenance` | `app.modules.maintenance.router_crud` | `/maintenance` | Equipements, ordres de maintenance |
| `finance` | `app.modules.finance.router_crud` | `/finance` | Journaux, ecritures comptables |
| `helpdesk` | `app.modules.helpdesk.router_crud` | `/helpdesk` | Tickets, categories, SLA |

### IMPORTANT (P1) - Securite & Administration

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `iam` | `app.modules.iam.router_crud` | `/iam` | Users, roles, permissions |
| `tenants` | `app.modules.tenants.router_crud` | `/tenants` | Multi-tenant management |
| `audit` | `app.modules.audit.router_crud` | `/audit` | Logs, tracabilite, conformite |
| `compliance` | `app.modules.compliance.router_crud` | `/compliance` | Conformite, RGPD |
| `subscriptions` | `app.modules.subscriptions.router_crud` | `/subscriptions` | Abonnements, plans, facturation |
| `backup` | `app.modules.backup.router_crud` | `/backup` | Sauvegardes, restauration |

### STANDARD (P2) - Interface & UX

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `cockpit` | `app.api.cockpit` | `/cockpit` | Dashboard principal |
| `pos` | `app.modules.pos.router_crud` | `/pos` | Point de vente |
| `mobile` | `app.modules.mobile.router_crud` | `/mobile` | App mobile, preferences |
| `web` | `app.modules.web.router_crud` | `/web` | Pages, themes, widgets |
| `website` | `app.modules.website.router_crud` | `/website` | Site web, CMS |

### STANDARD (P2) - IA & Enrichissement

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `enrichment` | `app.modules.enrichment.router` | `/enrichment` | Enrichissement donnees, APIs externes |
| `marceau` | `app.modules.marceau.router_crud` | `/marceau` | Assistant IA, memoire, knowledge |
| `ai_assistant` | `app.modules.ai_assistant.router_crud` | `/ai-assistant` | Assistant IA generique |
| `guardian` | `app.modules.guardian.router_crud` | `/guardian` | Monitoring, alertes, incidents |

### OPTIONAL (P3) - Qualite & Analytique

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `quality` | `app.modules.quality.router_crud` | `/quality` | Controle qualite, non-conformites |
| `qc` | `app.modules.qc.router_crud` | `/qc` | Quality Control |
| `bi` | `app.modules.bi.router_crud` | `/bi` | Business Intelligence, rapports |
| `field_service` | `app.modules.field_service.router_crud` | `/field-service` | Interventions terrain avancees |
| `procurement` | `app.modules.procurement.router_crud` | `/procurement` | Approvisionnement |

### OPTIONAL (P3) - Automatisation & Integration

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `triggers` | `app.modules.triggers.router_crud` | `/triggers` | Automatisations, workflows |
| `autoconfig` | `app.modules.autoconfig.router_crud` | `/autoconfig` | Configuration automatique |
| `broadcast` | `app.modules.broadcast.router_crud` | `/broadcast` | Diffusion, notifications |
| `email` | `app.modules.email.router_crud` | `/email` | Gestion emails |

### OPTIONAL (P3) - E-Commerce & Paiements

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `ecommerce` | `app.modules.ecommerce.router_crud` | `/ecommerce` | Boutique en ligne |
| `marketplace` | `app.modules.marketplace.router_crud` | `/marketplace` | Extensions, modules tiers |
| `stripe_integration` | `app.modules.stripe_integration.router_crud` | `/stripe` | Paiements Stripe |

### OPTIONAL (P3) - Localisation & Import

| Module | Import Path | Prefix | Description |
|--------|-------------|--------|-------------|
| `country_packs` | `app.modules.country_packs.router_crud` | `/country-packs` | Localisations fiscales |
| `odoo_import` | `app.modules.odoo_import.router_crud` | `/odoo-import` | Import depuis Odoo |
| `automated_accounting` | `app.modules.automated_accounting.router_crud` | `/automated-accounting` | Comptabilite automatisee |

---

## Patterns d'Endpoints Standards

### CRUD Operations

| Methode | Pattern | Description |
|---------|---------|-------------|
| `POST` | `/{module}` | Creer une ressource |
| `GET` | `/{module}` | Lister avec pagination |
| `GET` | `/{module}/{id}` | Recuperer par ID |
| `PUT` | `/{module}/{id}` | Mettre a jour |
| `DELETE` | `/{module}/{id}` | Supprimer |

### Actions sur Ressources

| Pattern | Exemples |
|---------|----------|
| `POST /{module}/{id}/{action}` | `/journal/{id}/post`, `/journal/{id}/validate` |
| `POST /{module}/{id}/close` | `/fiscal-years/{id}/close` |
| `POST /{module}/{id}/approve` | `/leave-requests/{id}/approve` |

### Ressources Imbriquees

| Pattern | Exemples |
|---------|----------|
| `GET /{parent}/{id}/{child}` | `/employees/{id}/contracts`, `/customers/{id}/contacts` |
| `POST /{parent}/{id}/{child}` | Creer un enfant lie au parent |

### Dashboard & Monitoring

| Endpoint | Description |
|----------|-------------|
| `GET /{module}/status` | Statut du module |
| `GET /{module}/summary` | Resume / Dashboard |
| `GET /{module}/monitoring` | Metriques de monitoring |

---

## Parametres de Pagination Standards

| Parametre | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Numero de page (1-based) |
| `page_size` | int | 20 | Nombre d'elements par page |
| `search` | string | null | Recherche textuelle |

Note: Certains modules utilisent `per_page` avec alias `page_size` pour compatibilite.

---

## Reponse Paginee Standard

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## Codes HTTP Standards

| Code | Signification |
|------|---------------|
| `200` | OK - Succes |
| `201` | Created - Ressource creee |
| `204` | No Content - Suppression reussie |
| `400` | Bad Request - Validation echouee |
| `401` | Unauthorized - Non authentifie |
| `403` | Forbidden - Non autorise |
| `404` | Not Found - Ressource inexistante |
| `409` | Conflict - Doublon (code unique) |
| `422` | Unprocessable Entity - Donnees invalides |
| `500` | Internal Server Error |

---

## Endpoint de Statut API

```
GET /api/v3/api/status
```

Retourne:
- Nombre total de modules
- Modules charges
- Modules en echec
- Temps de chargement
- Details par priorite

---

## Conformite Normative

Ce mapping respecte:
- **AZA-NF-003**: Modules subordonnes au noyau
- **AZA-BE-003**: Contrat backend obligatoire
- **AZA-API-003**: Versioning explicite
- **AZA-FE-007**: Auditabilite permanente

---

## Notes de Version

| Version | Date | Changements |
|---------|------|-------------|
| 3.1.0 | 2026-02-16 | 43 modules enregistres, registre declaratif |
| 3.0.0 | 2026-02-01 | Migration vers architecture unifiee |
