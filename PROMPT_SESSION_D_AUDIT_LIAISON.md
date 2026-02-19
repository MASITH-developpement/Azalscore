# SESSION D — AUDIT LIAISON BACKEND ↔ FRONTEND

## ⚠️ RÈGLES ABSOLUES — VÉRITÉ UNIQUEMENT

**Attention, cette mission exige une HONNÊTETÉ TOTALE.**

- **JAMAIS de mensonge** — Je préfère une mauvaise note à une note truquée ou fausse
- **JAMAIS de bullshit** — Que la vérité, même si elle est catastrophique
- **JAMAIS de faux semblant** — Si ça ne marche pas, dis-le clairement
- **JAMAIS de "ça devrait marcher"** — Teste et prouve que ça marche
- **JAMAIS de diminution de sécurité** — Le multi-tenant est SACRÉ
- **Rapport HONNÊTE** — Chaque endpoint testé = résultat réel documenté

### Format de rapport attendu :

```
✅ FONCTIONNE — Testé et validé
⚠️ PARTIEL — Fonctionne avec limitations (détailler)
❌ ÉCHOUE — Ne fonctionne pas (détailler l'erreur exacte)
🔴 ABSENT — Endpoint backend existe, pas de frontend
⚪ NON TESTÉ — Impossible à tester (expliquer pourquoi)
```

---

## 🎯 MISSION

**Auditer et corriger TOUTES les liaisons Backend ↔ Frontend pour garantir que :**

1. **Chaque endpoint backend** a un appel frontend fonctionnel
2. **Chaque module frontend** appelle les bons endpoints
3. **L'autocomplétion fonctionne** partout (installer des API si nécessaire)
4. **Aucune erreur** en console navigateur
5. **La sécurité multi-tenant** est préservée (JAMAIS de fuite cross-tenant)
6. **Les types sont synchronisés** Backend (Pydantic) ↔ Frontend (TypeScript)

---

## 📂 CONTEXTE

- **Backend:** `/home/ubuntu/azalscore/app/` — FastAPI + SQLAlchemy + Pydantic
- **Frontend:** `/home/ubuntu/azalscore/frontend/` — React + TypeScript + TailwindCSS
- **Documentation:** `/home/ubuntu/azalscore/memoire.md`
- **API Base:** `http://localhost:8000` (ou selon configuration)

---

## 🔍 PHASE 1 — INVENTAIRE COMPLET (Ne rien supposer)

### 1.1 Lister TOUS les endpoints backend

```bash
# Exécuter cette commande pour extraire tous les endpoints
cd /home/ubuntu/azalscore

# Méthode 1: Via OpenAPI
curl http://localhost:8000/openapi.json | jq '.paths | keys[]' > reports/all_endpoints.txt

# Méthode 2: Via grep dans le code
grep -r "@router\." app/modules/ --include="*.py" | grep -E "(get|post|put|patch|delete)" > reports/endpoints_code.txt

# Méthode 3: Via le registre v3
python -c "
from app.api.v3 import api_v3_router
for route in api_v3_router.routes:
    if hasattr(route, 'path'):
        print(f'{route.methods} {route.path}')
" > reports/endpoints_v3.txt
```

### 1.2 Lister TOUS les appels frontend

```bash
cd /home/ubuntu/azalscore/frontend

# Trouver tous les appels API
grep -r "apiClient\|api\.\|fetch\|axios" src/ --include="*.ts" --include="*.tsx" | \
  grep -E "(get|post|put|patch|delete|GET|POST|PUT|PATCH|DELETE)" > ../reports/frontend_calls.txt

# Trouver tous les fichiers api.ts
find src/modules -name "api.ts" -o -name "api.tsx" > ../reports/frontend_api_files.txt

# Compter les modules avec/sans api.ts
echo "Modules avec api.ts:" && find src/modules -name "api.ts" | wc -l
echo "Total modules:" && ls -d src/modules/*/ | wc -l
```

### 1.3 Générer le rapport de couverture

Créer un fichier `/home/ubuntu/azalscore/reports/AUDIT_LIAISON.md` avec ce format :

```markdown
# AUDIT LIAISON BACKEND ↔ FRONTEND
**Date:** YYYY-MM-DD
**Auditeur:** Claude Code Session D

## RÉSUMÉ EXÉCUTIF

| Métrique | Valeur | % |
|----------|--------|---|
| Endpoints backend total | XXX | 100% |
| Endpoints avec frontend | XXX | XX% |
| Endpoints sans frontend | XXX | XX% |
| Endpoints testés OK | XXX | XX% |
| Endpoints en erreur | XXX | XX% |
| Modules frontend total | XXX | 100% |
| Modules avec api.ts | XXX | XX% |
| Modules sans api.ts | XXX | XX% |

## SCORE GLOBAL: XX/100

> ⚠️ Ce score est HONNÊTE. Pas de trucage.
```

---

## 🔍 PHASE 2 — TEST DE CHAQUE MODULE

### Pour CHAQUE module, exécuter ce protocole :

```markdown
### Module: [NOM_MODULE]

**Backend:** `app/modules/[module]/`
**Frontend:** `frontend/src/modules/[module]/`

#### Endpoints backend

| Méthode | Endpoint | Frontend | Test | Résultat |
|---------|----------|----------|------|----------|
| GET | /module/items | ✅ api.ts:15 | ✅ | 200 OK |
| POST | /module/items | ✅ api.ts:22 | ✅ | 201 Created |
| GET | /module/items/{id} | ❌ ABSENT | - | Non testé |
| PUT | /module/items/{id} | ⚠️ Partiel | ❌ | 422 Validation |
| DELETE | /module/items/{id} | ✅ api.ts:35 | ✅ | 204 No Content |

#### Fichier api.ts

- [ ] Existe
- [ ] Types importés depuis @/types/api
- [ ] Pas de `any`
- [ ] Gestion erreurs
- [ ] Autocomplétion fonctionne

#### Tests effectués

1. **CRUD basique:** [Résultat]
2. **Isolation tenant:** [Résultat]
3. **Validation données:** [Résultat]
4. **Autocomplétion:** [Résultat]

#### Erreurs trouvées

```
[Copier les erreurs exactes de la console]
```

#### Corrections appliquées

```
[Détailler les corrections]
```
```

---

## 🔍 PHASE 3 — SYNCHRONISATION DES TYPES

### 3.1 Générer les types TypeScript depuis OpenAPI

```bash
cd /home/ubuntu/azalscore/frontend

# Installer openapi-typescript si nécessaire
npm install -D openapi-typescript

# Générer les types
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api-generated.ts

# Vérifier la génération
wc -l src/types/api-generated.ts
```

### 3.2 Vérifier la synchronisation

```typescript
// frontend/src/types/api.ts — TEMPLATE À SUIVRE

// Importer les types générés
export * from './api-generated';

// OU créer des alias si nécessaire
import type {
  Invoice as APIInvoice,
  InvoiceCreate as APIInvoiceCreate,
} from './api-generated';

// Exporter avec noms cohérents
export type Invoice = APIInvoice;
export type InvoiceCreate = APIInvoiceCreate;
```

### 3.3 Audit des types

Pour chaque module, vérifier :

```markdown
#### Types Module [NOM]

| Type Backend (Pydantic) | Type Frontend (TS) | Synchronisé |
|-------------------------|--------------------| ------------|
| InvoiceSchema | Invoice | ✅ |
| InvoiceCreateSchema | InvoiceCreate | ✅ |
| InvoiceUpdateSchema | InvoiceUpdate | ❌ Manquant |
| InvoiceListResponse | PaginatedResponse<Invoice> | ⚠️ Différent |
```

---

## 🔍 PHASE 4 — AUTOCOMPLÉTION MAXIMALE

### 4.1 Vérifier l'autocomplétion existante

Pour chaque champ de recherche/sélection :

```markdown
#### Autocomplétion Module [NOM]

| Champ | Type | Backend endpoint | Autocomplétion | Statut |
|-------|------|------------------|----------------|--------|
| client_id | Select | GET /contacts?search= | ✅ Fonctionne | OK |
| product_id | Combobox | GET /products?q= | ❌ Absent | À créer |
| account_code | Input | GET /accounts/search | ⚠️ Lent (>500ms) | Optimiser |
```

### 4.2 Implémenter l'autocomplétion manquante

```typescript
// TEMPLATE — Composant Autocomplete réutilisable
// frontend/src/components/ui/Autocomplete.tsx

import { useState, useEffect, useCallback } from 'react';
import { useDebounce } from '@/hooks/useDebounce';

interface AutocompleteProps<T> {
  // Endpoint de recherche
  searchEndpoint: string;
  // Fonction pour extraire le label
  getLabel: (item: T) => string;
  // Fonction pour extraire la valeur
  getValue: (item: T) => string;
  // Valeur sélectionnée
  value?: string;
  // Callback de sélection
  onSelect: (item: T) => void;
  // Placeholder
  placeholder?: string;
  // Délai debounce (ms)
  debounceMs?: number;
  // Minimum caractères avant recherche
  minChars?: number;
}

export function Autocomplete<T>({
  searchEndpoint,
  getLabel,
  getValue,
  value,
  onSelect,
  placeholder = 'Rechercher...',
  debounceMs = 300,
  minChars = 2,
}: AutocompleteProps<T>) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const debouncedQuery = useDebounce(query, debounceMs);

  useEffect(() => {
    if (debouncedQuery.length < minChars) {
      setResults([]);
      return;
    }

    const search = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `${searchEndpoint}?q=${encodeURIComponent(debouncedQuery)}`
        );
        const data = await response.json();
        setResults(data.items || data);
      } catch (error) {
        console.error('Autocomplete error:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    search();
  }, [debouncedQuery, searchEndpoint, minChars]);

  // ... reste du composant avec accessibilité ARIA
}
```

### 4.3 Endpoints de recherche requis

Vérifier que ces endpoints existent et fonctionnent :

```python
# Backend — Endpoints de recherche OBLIGATOIRES

# Contacts/Clients
GET /contacts/search?q={query}&limit=10
GET /contacts/autocomplete?q={query}  # Version légère

# Produits/Articles
GET /products/search?q={query}&limit=10
GET /products/autocomplete?q={query}

# Comptes comptables
GET /accounts/search?q={query}&type={type}
GET /accounts/autocomplete?q={query}

# Employés
GET /employees/search?q={query}&limit=10

# Projets
GET /projects/search?q={query}&status=active

# etc. pour chaque entité avec sélection
```

---

## 🔍 PHASE 5 — SÉCURITÉ MULTI-TENANT

### 5.1 Tests d'isolation tenant OBLIGATOIRES

```python
# Tests à exécuter pour CHAQUE endpoint

import pytest
from httpx import AsyncClient

async def test_tenant_isolation_list(client: AsyncClient):
    """
    Test: Un tenant ne peut PAS voir les données d'un autre tenant.
    """
    # Créer données tenant A
    tenant_a_token = await get_token(tenant_id="tenant-a")
    response_a = await client.post(
        "/items",
        json={"name": "Item Tenant A"},
        headers={"Authorization": f"Bearer {tenant_a_token}"}
    )
    item_a_id = response_a.json()["id"]

    # Essayer de lire depuis tenant B
    tenant_b_token = await get_token(tenant_id="tenant-b")
    response_b = await client.get(
        f"/items/{item_a_id}",
        headers={"Authorization": f"Bearer {tenant_b_token}"}
    )

    # DOIT échouer avec 404 (pas 403 pour ne pas révéler l'existence)
    assert response_b.status_code == 404, \
        f"FUITE CROSS-TENANT! Tenant B peut voir item de Tenant A"

async def test_tenant_isolation_update(client: AsyncClient):
    """
    Test: Un tenant ne peut PAS modifier les données d'un autre tenant.
    """
    # ... même logique
    assert response.status_code == 404

async def test_tenant_isolation_delete(client: AsyncClient):
    """
    Test: Un tenant ne peut PAS supprimer les données d'un autre tenant.
    """
    # ... même logique
    assert response.status_code == 404

async def test_tenant_isolation_search(client: AsyncClient):
    """
    Test: La recherche ne retourne que les données du tenant courant.
    """
    # Créer données dans les deux tenants
    # Rechercher depuis tenant A
    # Vérifier que seules les données tenant A sont retournées
    for item in response.json()["items"]:
        assert item["tenant_id"] == "tenant-a", \
            f"FUITE! Item d'un autre tenant dans les résultats"
```

### 5.2 Checklist sécurité frontend

```markdown
#### Sécurité Frontend Module [NOM]

- [ ] Token JWT envoyé dans Authorization header
- [ ] Pas de tenant_id dans les URLs (déduit du token)
- [ ] Pas de données sensibles dans localStorage (sauf token)
- [ ] Pas de console.log avec données sensibles
- [ ] XSS: Données échappées avant affichage
- [ ] CSRF: Token inclus si formulaires traditionnels
- [ ] Pas de credentials dans le code
```

---

## 🔍 PHASE 6 — QUALITÉ DU CODE

### 6.1 Lint et TypeScript strict

```bash
cd /home/ubuntu/azalscore/frontend

# TypeScript strict
npx tsc --noEmit

# ESLint
npx eslint src/ --ext .ts,.tsx

# Prettier
npx prettier --check "src/**/*.{ts,tsx}"
```

### 6.2 Checklist qualité par module

```markdown
#### Qualité Module [NOM]

**api.ts:**
- [ ] Pas de `any` (0 occurrences)
- [ ] Types importés depuis @/types/api
- [ ] Fonctions async/await propres
- [ ] Gestion erreurs (try/catch ou .catch)
- [ ] JSDoc sur fonctions publiques

**Composants:**
- [ ] Props typées (interface explicite)
- [ ] Pas de `any` dans les props
- [ ] Accessibilité (aria-*, role, labels)
- [ ] Loading states gérés
- [ ] Error states gérés
- [ ] Empty states gérés

**Tests:**
- [ ] Tests unitaires présents
- [ ] Couverture > 70%
- [ ] Tests d'intégration API mockés
```

---

## 📊 PHASE 7 — RAPPORT FINAL

### Template de rapport final

```markdown
# RAPPORT AUDIT LIAISON BACKEND ↔ FRONTEND

**Date:** YYYY-MM-DD HH:MM
**Durée audit:** X heures
**Auditeur:** Claude Code Session D

---

## RÉSUMÉ EXÉCUTIF

### Score Global: XX/100

| Catégorie | Score | Poids | Pondéré |
|-----------|-------|-------|---------|
| Couverture endpoints | XX/100 | 30% | XX |
| Types synchronisés | XX/100 | 20% | XX |
| Autocomplétion | XX/100 | 15% | XX |
| Sécurité multi-tenant | XX/100 | 25% | XX |
| Qualité code | XX/100 | 10% | XX |
| **TOTAL** | - | 100% | **XX/100** |

### Verdict

> [HONNÊTE] Ce score reflète l'état RÉEL du code.
> Points forts: ...
> Points critiques: ...

---

## STATISTIQUES

### Endpoints

| Statut | Nombre | % |
|--------|--------|---|
| ✅ Fonctionnels | XXX | XX% |
| ⚠️ Partiels | XXX | XX% |
| ❌ En erreur | XXX | XX% |
| 🔴 Sans frontend | XXX | XX% |
| **Total** | XXX | 100% |

### Modules

| Module | Endpoints | api.ts | Types | Autocomplétion | Sécurité | Score |
|--------|-----------|--------|-------|----------------|----------|-------|
| accounting | 45 | ✅ | ✅ | ⚠️ | ✅ | 85/100 |
| commercial | 32 | ✅ | ⚠️ | ✅ | ✅ | 80/100 |
| contacts | 18 | ❌ | ❌ | ❌ | ✅ | 40/100 |
| ... | ... | ... | ... | ... | ... | ... |

---

## ERREURS CRITIQUES (À corriger immédiatement)

### 1. [Titre erreur]

**Module:** XXX
**Endpoint:** XXX
**Erreur:**
```
[Message d'erreur exact]
```
**Impact:** [Décrire l'impact]
**Correction:** [Proposer ou appliquer la correction]

---

## CORRECTIONS APPLIQUÉES

### 1. [Titre correction]

**Fichier:** `path/to/file.ts`
**Avant:**
```typescript
// Code problématique
```
**Après:**
```typescript
// Code corrigé
```
**Test:** ✅ Vérifié

---

## RECOMMANDATIONS

### Priorité CRITIQUE (Cette semaine)

1. ...
2. ...

### Priorité HAUTE (Ce mois)

1. ...
2. ...

### Priorité MOYENNE (Ce trimestre)

1. ...

---

## ANNEXES

### A. Liste complète des endpoints

[Tableau complet]

### B. Erreurs console détaillées

[Logs complets]

### C. Commandes exécutées

[Historique des commandes]
```

---

## 🚀 COMMENCE PAR

1. **Démarrer les serveurs** (backend + frontend)
2. **Exécuter les commandes d'inventaire** (Phase 1)
3. **Créer le fichier de rapport** `/home/ubuntu/azalscore/reports/AUDIT_LIAISON.md`
4. **Tester module par module** — Ne RIEN supposer, tout vérifier
5. **Documenter CHAQUE erreur** avec le message exact
6. **Corriger au fur et à mesure** — Pas de report

---

## ⚠️ RAPPELS CRITIQUES

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚫 JAMAIS de score truqué                                      ║
║   🚫 JAMAIS de "ça devrait marcher"                              ║
║   🚫 JAMAIS de diminution sécurité multi-tenant                  ║
║   🚫 JAMAIS de suppression de code existant sans test            ║
║                                                                  ║
║   ✅ TOUJOURS tester avant de valider                            ║
║   ✅ TOUJOURS documenter les erreurs exactes                     ║
║   ✅ TOUJOURS préserver l'isolation tenant                       ║
║   ✅ TOUJOURS être HONNÊTE dans le rapport                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 📁 FICHIERS À CRÉER/METTRE À JOUR

```
/home/ubuntu/azalscore/
├── reports/
│   ├── AUDIT_LIAISON.md          # Rapport principal
│   ├── all_endpoints.txt         # Liste endpoints backend
│   ├── frontend_calls.txt        # Liste appels frontend
│   ├── errors_console.log        # Erreurs navigateur
│   └── tenant_isolation_tests.md # Résultats tests sécurité
├── frontend/
│   ├── src/types/api-generated.ts  # Types générés OpenAPI
│   ├── src/types/api.ts            # Types exportés
│   └── src/modules/*/api.ts        # API par module (créer si absent)
```

---

**GO ! Sois HONNÊTE. Sois RIGOUREUX. Sois COMPLET.**
