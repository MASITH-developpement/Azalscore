# AZALSCORE - API MAP

**Généré le:** 2026-02-26
**Version:** 1.1

## Vue d'ensemble

| Métrique | Valeur |
|----------|--------|
| **Modules Backend** | 96 |
| **Modules Frontend** | 82 |
| **Endpoints API** | ~2,100 |
| **Lignes Backend** | 672,000 |
| **Lignes Frontend** | 236,396 |
| **Fichiers api.ts** | 80 |
| **Lignes api.ts** | 42,124 |

---

## Modules Principaux - Correspondance Backend ↔ Frontend

| Module | Endpoints | api.ts | Lignes Backend | Statut |
|--------|-----------|--------|----------------|--------|
| **finance** | 287 | ✅ | 27,200 | Production |
| **commercial** | 136 | ✅ | - | Production |
| **hr** | 147 | ✅ | 5,964 | Production |
| **interventions** | 85 | ✅ | - | Production |
| **projects** | 153 | ✅ | - | Production |
| **inventory** | 127 | ✅ | 5,516 | Production |
| **accounting** | 61 | ✅ | - | Production |
| **treasury** | 42 | ✅ | - | Production |
| **audit** | 90 | ✅ | 5,445 | Production |
| **guardian** | 109 | ✅ | 9,117 | Production |
| **ai_assistant** | 83 | ✅ | 5,011 | Production |
| **compliance** | 190 | ✅ | 10,617 | Production |
| **helpdesk** | 184 | ✅ | - | Production |
| **maintenance** | 104 | ✅ | 5,278 | Production |
| **ecommerce** | 186 | ✅ | 9,832 | Production |
| **pos** | 130 | ✅ | 5,943 | Production |
| **expenses** | 45 | ✅ | 3,200 | Production |
| **assets** | 52 | ✅ | 4,100 | Production |
| **contracts** | 58 | ✅ | 4,800 | Production |
| **esignature** | 42 | ✅ | 3,900 | Production |
| **broadcast** | 35 | ✅ | 2,800 | Production |
| **email** | 38 | ✅ | 2,600 | Production |
| **timesheet** | 48 | ✅ | 1,260 | Production |
| **warranty** | 40 | ✅ | 1,333 | Production |
| **commissions** | 32 | ✅ | 1,886 | Production |
| **budget** | 30 | ✅ | 1,859 | Production |
| **gamification** | 28 | ✅ | 1,820 | Production |
| **subscriptions** | 35 | ✅ | 1,512 | Production |
| **loyalty** | 30 | ✅ | 1,528 | Production |
| **shipping** | 32 | ✅ | 1,646 | Production |
| **workflows** | 28 | ✅ | 1,410 | Production |

---

## Finance Suite - Sous-modules

| Sous-module | Endpoints | Description |
|-------------|-----------|-------------|
| **bank-accounts** | 15 | Comptes bancaires, soldes |
| **transactions** | 12 | Mouvements bancaires |
| **reconciliation** | 10 | Rapprochement bancaire IA |
| **cash-forecast** | 8 | Prévisions trésorerie |
| **virtual-cards** | 14 | Cartes virtuelles |
| **providers/swan** | 8 | Banking-as-a-Service |
| **providers/nmi** | 10 | Paiements |
| **providers/defacto** | 8 | Affacturage |
| **providers/solaris** | 8 | Crédit entreprise |
| **dunning** | 20 | Relances impayés |
| **invoice-ocr** | 8 | OCR factures |
| **currency** | 10 | Taux de change |
| **approval** | 18 | Workflows approbation |
| **webhooks** | 6 | Notifications providers |

---

## Conformité France

| Module | Endpoints | Statut | Deadline |
|--------|-----------|--------|----------|
| **einvoicing** | 67 | ✅ Production | 09/2026 |
| **fec** | 15 | ✅ Production | - |
| **liasses** | 12 | ✅ Production | - |
| **dsn** | 8 | ✅ Production | - |
| **pcg** | 10 | ✅ Production | - |
| **nf525** | 5 | ✅ Production | - |

---

## API Versioning

/v3/{module}/{resource}           # Standard CRUD
/v3/{module}/{resource}/{id}      # Single resource
/v3/{module}/{resource}/{id}/{action}  # Actions

### Exemples

# Finance
GET  /v3/finance/bank-accounts
POST /v3/finance/reconciliation/auto
GET  /v3/finance/cash-forecast?days=30

# Commercial
GET  /v3/commercial/customers?type=CLIENT
POST /v3/commercial/documents
POST /v3/commercial/documents/{id}/send

# Interventions
GET  /v3/interventions?statut=EN_COURS
POST /v3/interventions/{id}/transition

---

## Authentification

| Header | Description |
|--------|-------------|
| Authorization | Bearer {jwt_token} |
| X-Tenant-ID | ID du tenant (obligatoire) |
| X-CSRF-Token | Token CSRF (POST/PUT/DELETE) |

---

## Pagination Standard

{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}

### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| page | int | Page courante (défaut: 1) |
| per_page | int | Items par page (défaut: 20, max: 100) |
| sort | string | Champ de tri |
| order | string | asc ou desc |

---

## Codes HTTP

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Créé |
| 204 | Supprimé |
| 400 | Erreur validation |
| 401 | Non authentifié |
| 403 | Non autorisé (RBAC) |
| 404 | Non trouvé |
| 409 | Conflit (doublon) |
| 422 | Erreur Pydantic |
| 429 | Rate limit |
| 500 | Erreur serveur |

---

## Rate Limits

| Scope | Limite |
|-------|--------|
| Par IP | 1000 req/min |
| Par Tenant | 5000 req/min |
| Global | 50000 req/min |

---

## Modules Métier Additionnels

### Expenses (Notes de frais)
- Reports, lignes, justificatifs OCR
- Kilométrage barème fiscal
- Workflows approbation
- Politiques de dépenses

### Assets (Immobilisations)
- Catégories, amortissements
- Maintenance préventive
- Inventaire physique
- Assurances

### Contracts (Gestion contractuelle)
- Types: vente, achat, service, NDA...
- Parties, avenants, obligations
- Calendrier échéances
- Génération depuis templates

### E-Signature
- Providers: YouSign, DocuSign, HelloSign
- Niveaux: simple, avancé, qualifié
- Audit trail certifié
- Templates de signature

### Broadcast (Diffusion périodique)
- Templates contenu
- Listes destinataires dynamiques
- Planification CRON
- Tracking ouvertures/clics

### Email (Transactionnel)
- Config SMTP/API (Brevo, SendGrid)
- Templates multilingues
- Queue & retry
- Statistiques

### Timesheet (Temps & Activités)
- Saisie temps projet/tâche
- Chronomètre temps réel
- Feuilles hebdo/mensuelles
- Heures sup Code du travail

### Warranty (Garanties)
- Légale conformité (2 ans)
- Extensions commerciales
- Réclamations SAV
- Provisions comptables

---

## Modules Backend Complets (96 total)

### Tier 1 - Core Business (12)
accounting, commercial, crm, finance, hr, interventions, inventory, pos, procurement, projects, purchases, treasury

### Tier 2 - Operations (14)
assets, contracts, ecommerce, esignature, expenses, field_service, helpdesk, maintenance, manufacturing, production, shipping, subscriptions, timesheet, warranty

### Tier 3 - Support (18)
ai_assistant, audit, backup, bi, broadcast, budget, cache, commissions, compliance, consolidation, dashboards, email, gamification, guardian, loyalty, notifications, workflows, webhooks

### Tier 4 - Integration (10)
dataexchange, gateway, integration, integrations, marketplace, mobile, odoo_import, stripe_integration, web, website

### Tier 5 - Administration (12)
autoconfig, country_packs, currency, i18n, iam, resources, scheduler, search, storage, templates, tenants, triggers

### Tier 6 - Specialized (20)
appointments, approval, automated_accounting, complaints, contacts, documents, enrichment, events, fleet, forecasting, knowledge, quality, qc, referral, rental, requisition, rfq, risk, sla, social_networks, survey, surveys, training, visitor

