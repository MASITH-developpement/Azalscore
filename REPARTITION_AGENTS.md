# RÉPARTITION DES MODULES - 2 AGENTS PARALLÈLES

**Date:** 2026-02-20
**Total modules:** 95
**Répartition:** ~48 modules par agent

---

## AGENT 1 - MODULES A-I (48 modules)

```
Copier ce prompt pour l'Agent 1:
```

```markdown
# Agent 1: Développement Complet Modules A-I

Tu dois développer/compléter les 48 modules suivants selon le template dans PROMPTS_MODULES_PARALLELES.md.

Pour CHAQUE module:
1. Vérifier si le code existe et est complet
2. Compléter ce qui manque (backend + frontend)
3. Assurer: multi-tenant, soft-delete, audit, autocomplete
4. Tester l'isolation tenant

## TES MODULES (48)

| # | Module | Priorité |
|---|--------|----------|
| 1 | accounting | Standard |
| 2 | ai_assistant | Standard |
| 3 | appointments | Standard |
| 4 | approval | **HAUTE** (GAP-083) |
| 5 | assets | Standard |
| 6 | audit | Standard |
| 7 | autoconfig | Standard |
| 8 | automated_accounting | Standard |
| 9 | backup | Standard |
| 10 | bi | Standard |
| 11 | broadcast | Standard |
| 12 | budget | Standard |
| 13 | cache | Standard |
| 14 | commercial | Standard |
| 15 | commissions | Standard |
| 16 | complaints | Standard |
| 17 | compliance | Standard |
| 18 | consolidation | Standard |
| 19 | contacts | Standard |
| 20 | contracts | Standard |
| 21 | country_packs | Standard |
| 22 | currency | Standard |
| 23 | dashboards | Standard |
| 24 | dataexchange | Standard |
| 25 | documents | Standard |
| 26 | ecommerce | Standard |
| 27 | email | Standard |
| 28 | enrichment | Standard |
| 29 | esignature | Standard |
| 30 | events | Standard |
| 31 | expense | **HAUTE** (GAP-084) |
| 32 | expenses | Standard |
| 33 | field_service | Standard |
| 34 | fieldservice | **HAUTE** (GAP-081) |
| 35 | finance | Standard |
| 36 | fleet | Standard |
| 37 | forecasting | **HAUTE** (GAP-076) |
| 38 | gamification | Standard |
| 39 | gateway | Standard |
| 40 | guardian | Standard |
| 41 | helpdesk | Standard |
| 42 | hr | Standard |
| 43 | hr_vault | Standard |
| 44 | i18n | Standard |
| 45 | iam | Standard |
| 46 | integration | **HAUTE** (GAP-086) |
| 47 | integrations | Standard |
| 48 | interventions | Standard |

## CHECKLIST PAR MODULE

Pour chaque module, assurer:

### Backend
- [ ] models.py - Entités avec tenant_id, soft-delete, audit, version
- [ ] schemas.py - Pydantic avec validation
- [ ] repository.py - _base_query() filtré par tenant
- [ ] service.py - Logique métier, transitions d'état
- [ ] router.py - CRUD + autocomplete + bulk
- [ ] tests/test_security.py - Isolation tenant

### Frontend
- [ ] types.ts - Types correspondant au backend
- [ ] api.ts - Client API complet
- [ ] hooks/ - React Query avec cache
- [ ] components/Autocomplete.tsx - Debounce, keyboard
- [ ] pages/ - Page principale intégrée

### Intégration
- [ ] main.py - Router inclus
- [ ] UnifiedApp.tsx - Route ajoutée
- [ ] UnifiedLayout.tsx - Menu ajouté

## RÈGLES

1. **Isolation** - Ne touche PAS aux modules J-Z (Agent 2)
2. **Ordre** - Commence par les modules **HAUTE** priorité
3. **Complet** - Chaque module doit être 100% fonctionnel avant de passer au suivant
4. **Tests** - Exécute les tests de sécurité pour chaque module
```

---

## AGENT 2 - MODULES I-Z (47 modules)

```
Copier ce prompt pour l'Agent 2:
```

```markdown
# Agent 2: Développement Complet Modules I-Z

Tu dois développer/compléter les 47 modules suivants selon le template dans PROMPTS_MODULES_PARALLELES.md.

Pour CHAQUE module:
1. Vérifier si le code existe et est complet
2. Compléter ce qui manque (backend + frontend)
3. Assurer: multi-tenant, soft-delete, audit, autocomplete
4. Tester l'isolation tenant

## TES MODULES (47)

| # | Module | Priorité |
|---|--------|----------|
| 1 | inventory | Standard |
| 2 | knowledge | Standard |
| 3 | loyalty | Standard |
| 4 | maintenance | Standard |
| 5 | manufacturing | **HAUTE** (GAP-077) |
| 6 | marceau | Standard |
| 7 | marketplace | Standard |
| 8 | mobile | Standard |
| 9 | notifications | Standard |
| 10 | odoo_import | Standard |
| 11 | pos | Standard |
| 12 | procurement | Standard |
| 13 | production | Standard |
| 14 | projects | Standard |
| 15 | purchases | Standard |
| 16 | qc | Standard |
| 17 | quality | Standard |
| 18 | referral | **HAUTE** (GAP-070) |
| 19 | rental | Standard |
| 20 | requisition | **HAUTE** (GAP-085) |
| 21 | resources | **HAUTE** (GAP-071) |
| 22 | rfq | Standard |
| 23 | risk | **HAUTE** (GAP-075) |
| 24 | scheduler | Standard |
| 25 | search | Standard |
| 26 | shipping | **HAUTE** (GAP-078) |
| 27 | signatures | Standard |
| 28 | sla | **HAUTE** (GAP-074) |
| 29 | social_networks | Standard |
| 30 | storage | Standard |
| 31 | stripe_integration | Standard |
| 32 | subscriptions | Standard |
| 33 | survey | **HAUTE** (GAP-082) |
| 34 | surveys | Standard |
| 35 | templates | Standard |
| 36 | tenants | Standard |
| 37 | timesheet | Standard |
| 38 | timetracking | **HAUTE** (GAP-080) |
| 39 | training | Standard |
| 40 | treasury | Standard |
| 41 | triggers | Standard |
| 42 | visitor | **HAUTE** (GAP-079) |
| 43 | warranty | Standard |
| 44 | web | Standard |
| 45 | webhooks | Standard |
| 46 | website | Standard |
| 47 | workflows | Standard |

## CHECKLIST PAR MODULE

Pour chaque module, assurer:

### Backend
- [ ] models.py - Entités avec tenant_id, soft-delete, audit, version
- [ ] schemas.py - Pydantic avec validation
- [ ] repository.py - _base_query() filtré par tenant
- [ ] service.py - Logique métier, transitions d'état
- [ ] router.py - CRUD + autocomplete + bulk
- [ ] tests/test_security.py - Isolation tenant

### Frontend
- [ ] types.ts - Types correspondant au backend
- [ ] api.ts - Client API complet
- [ ] hooks/ - React Query avec cache
- [ ] components/Autocomplete.tsx - Debounce, keyboard
- [ ] pages/ - Page principale intégrée

### Intégration
- [ ] main.py - Router inclus
- [ ] UnifiedApp.tsx - Route ajoutée
- [ ] UnifiedLayout.tsx - Menu ajouté

## RÈGLES

1. **Isolation** - Ne touche PAS aux modules A-I (Agent 1)
2. **Ordre** - Commence par les modules **HAUTE** priorité
3. **Complet** - Chaque module doit être 100% fonctionnel avant de passer au suivant
4. **Tests** - Exécute les tests de sécurité pour chaque module
```

---

## RÉSUMÉ RÉPARTITION

| Agent | Modules | GAPs Haute Priorité |
|-------|---------|---------------------|
| **Agent 1** | A-I (48) | approval, expense, fieldservice, forecasting, integration |
| **Agent 2** | I-Z (47) | manufacturing, referral, requisition, resources, risk, shipping, sla, survey, timetracking, visitor |

## FICHIERS PARTAGÉS (NE PAS TOUCHER EN PARALLÈLE)

Ces fichiers seront modifiés par les deux agents, mais sur des LIGNES DIFFÉRENTES:

| Fichier | Agent 1 ajoute | Agent 2 ajoute |
|---------|----------------|----------------|
| `main.py` | Routers A-I | Routers I-Z |
| `UnifiedApp.tsx` | Routes A-I | Routes I-Z |
| `UnifiedLayout.tsx` | Menus A-I | Menus I-Z |

**IMPORTANT:** Chaque agent ajoute ses lignes dans une SECTION MARQUÉE pour éviter les conflits git.

---

## LANCEMENT

```bash
# Terminal 1 - Agent 1
claude "Exécute le prompt Agent 1 dans REPARTITION_AGENTS.md"

# Terminal 2 - Agent 2
claude "Exécute le prompt Agent 2 dans REPARTITION_AGENTS.md"
```

---

*AZALSCORE - Répartition 2 Agents - 2026-02-20*
