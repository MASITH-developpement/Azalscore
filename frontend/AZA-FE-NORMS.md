# AZALSCORE Frontend Norms - AZA-FE
**Version:** 1.0.0
**Date:** 2026-01-23
**Status:** MANDATORY

---

## Table des Matières

1. [Introduction](#introduction)
2. [AZA-FE-ENF: Frontend Technical Enforcement](#aza-fe-enf-frontend-technical-enforcement)
3. [AZA-FE-DASH: Frontend Health Dashboard](#aza-fe-dash-frontend-health-dashboard)
4. [AZA-FE-META: Frontend Module Metadata](#aza-fe-meta-frontend-module-metadata)
5. [Standards de Développement](#standards-de-développement)
6. [Conformité et Validation](#conformité-et-validation)
7. [FAQ](#faq)

---

## Introduction

Les normes AZALSCORE Frontend (AZA-FE) définissent les exigences techniques **OBLIGATOIRES** pour le développement frontend de la plateforme AZALSCORE. Ces normes garantissent:

- ✅ **Zéro page vide** - Toute route doit afficher du contenu
- ✅ **Zéro lien mort** - Tous les liens menu doivent pointer vers des routes valides
- ✅ **UX cohérente à 100%** - Utilisation systématique des layouts normés
- ✅ **Gouvernance traçable** - Métadonnées complètes pour tous les modules
- ✅ **Qualité mesurable** - Dashboard de santé accessible aux dirigeants

### Principes Fondamentaux

1. **Enforcement Automatique**: Toute violation DOIT être détectée automatiquement
2. **Blocage CI/CD**: Les violations critiques DOIVENT empêcher le déploiement
3. **Gouvernance**: Les métriques de qualité DOIVENT être visibles des décideurs
4. **Traçabilité**: Toute violation DOIT être journalisée

---

## AZA-FE-ENF: Frontend Technical Enforcement

### Principe

**Toute violation technique DOIT être détectée automatiquement, être bloquante, et empêcher le déploiement.**

### 1. Linter Normatif AZALSCORE

#### Objectif
Vérifier automatiquement la conformité technique de tous les modules.

#### Localisation
- **Script**: `/scripts/frontend/azalscore-linter.ts`
- **Commande**: `npm run azalscore:lint`
- **CI/CD**: Job obligatoire dans le pipeline

#### Vérifications Obligatoires

##### 1.1 Existence page.tsx pour chaque route

**Règle**: Toute route déclarée dans `src/routing/index.tsx` DOIT avoir un fichier `index.tsx` correspondant.

**Exemple de violation**:
```tsx
// src/routing/index.tsx
<Route path="/inventory/*" element={<InventoryModule />} />

// ❌ VIOLATION: src/modules/inventory/index.tsx n'existe pas
```

**Correction**:
```bash
# Créer le module manquant
npm run scaffold:module -- inventory
```

##### 1.2 Utilisation obligatoire UnifiedLayout

**Règle**: Tout module DOIT utiliser un des layouts AZALSCORE approuvés:
- `UnifiedLayout`
- `MainLayout`
- `BaseViewStandard`
- `PageWrapper`

**Exemple de violation**:
```tsx
// ❌ VIOLATION: Module sans layout
export default function InventoryModule() {
  return (
    <div>
      <h1>Inventory</h1>
      {/* ... */}
    </div>
  );
}
```

**Correction**:
```tsx
// ✅ CONFORME: Utilisation de BaseViewStandard
import { BaseViewStandard } from '@/ui-engine/layouts';

export default function InventoryModule() {
  return (
    <BaseViewStandard
      title="Gestion de Stock"
      icon="📦"
    >
      {/* ... */}
    </BaseViewStandard>
  );
}
```

##### 1.3 Absence composant vide

**Règle**: Aucun module ne DOIT contenir de composant vide ou placeholder.

**Patterns interdits**:
- `return null`
- `return <></>`
- `return <div></div>`
- `TODO: Implement`
- `PLACEHOLDER`
- `COMING SOON`

**Exemple de violation**:
```tsx
// ❌ VIOLATION: Composant vide
export default function MyModule() {
  return null; // ❌
}

// ❌ VIOLATION: Placeholder
export default function MyModule() {
  return <div>TODO: Implement this module</div>; // ❌
}
```

**Correction**:
```tsx
// ✅ CONFORME: Module avec contenu minimal
export default function MyModule() {
  return (
    <BaseViewStandard title="Mon Module">
      <p>Bienvenue dans le module.</p>
    </BaseViewStandard>
  );
}
```

##### 1.4 Absence route orpheline

**Règle**: Toute route DOIT pointer vers un module existant.

**Exemple de violation**:
```tsx
// src/routing/index.tsx
<Route path="/inventory/*" element={<InventoryModule />} />

// ❌ VIOLATION: src/modules/inventory/ n'existe pas
```

---

### 2. Route Guards

#### Objectif
Vérifier à l'exécution que le module est valide, actif, et possède un contrat UI.

#### Localisation
- **Composant**: `/src/routing/RouteGuard.tsx`
- **Usage**: Entourer tout élément de route

#### Vérifications Obligatoires

##### 2.1 Module existant
```typescript
if (!meta) {
  logViolation('MODULE_NOT_FOUND', moduleCode);
  navigate('/error/module-not-found');
}
```

##### 2.2 Module actif
```typescript
if (meta.status === 'inactive') {
  logViolation('MODULE_INACTIVE', moduleCode);
  navigate('/error/module-inactive');
}
```

##### 2.3 UI contract présent
```typescript
if (!meta.frontend.hasUI) {
  logViolation('NO_UI_CONTRACT', moduleCode);
  navigate('/error/no-ui');
}
```

##### 2.4 Conformité AZA-FE (warning)
```typescript
if (!meta.frontend.compliance) {
  logViolation('NON_COMPLIANT', moduleCode);
  // Afficher banner d'avertissement mais laisser passer
}
```

#### Journalisation Obligatoire

Toute violation DOIT être journalisée:
1. **Console** (développement)
2. **Backend API** `/api/v1/frontend-violations` (production)
3. **LocalStorage** (analytics, 100 dernières violations)

**Format violation**:
```typescript
{
  type: 'MODULE_NOT_FOUND' | 'MODULE_INACTIVE' | 'NO_UI_CONTRACT' | 'NON_COMPLIANT',
  moduleCode: string,
  timestamp: ISO8601,
  userAgent: string,
  url: string,
}
```

#### Utilisation

```tsx
// src/routing/index.tsx
import { RouteGuard } from './RouteGuard';

<Route
  path="/inventory/*"
  element={
    <RouteGuard moduleCode="inventory">
      <InventoryModule />
    </RouteGuard>
  }
/>
```

---

### 3. Vérification Menu ↔ Route

#### Objectif
Garantir la synchronisation entre les liens de menu et les routes existantes.

#### Localisation
- **Script**: `/scripts/frontend/validate-menu-route-sync.ts`
- **Commande**: `npm run validate:menu-route-sync`
- **Hook**: Pre-push

#### Vérifications Obligatoires

##### 3.1 Chaque entrée menu = route valide

**Règle**: Tout lien dans le menu DOIT correspondre à une route déclarée.

**Fichiers scannés**:
- `src/ui-engine/top-menu/index.tsx`
- `src/ui-engine/menu-dynamic/index.tsx`

**Exemple de violation**:
```tsx
// src/ui-engine/top-menu/index.tsx
const menuItems = [
  { label: 'Inventory', path: '/inventory' }, // ❌ Route inexistante
];
```

##### 3.2 Chaque route affichée = page rendue

**Règle**: Toute route DOIT pointer vers une page non vide.

**Exemple de violation**:
```tsx
// Route déclarée
<Route path="/inventory/*" element={<InventoryModule />} />

// Mais module vide:
// src/modules/inventory/index.tsx
export default function InventoryModule() {
  return null; // ❌ VIOLATION: Page vide
}
```

---

### 4. Blocage CI/CD

#### Principe
Le pipeline CI/CD DOIT échouer si des violations AZA-FE-ENF sont détectées.

#### Jobs Obligatoires

```yaml
# .github/workflows/frontend-ci.yml

jobs:
  validate-azalscore-norms:
    name: Validate AZALSCORE Norms (AZA-FE-ENF)
    runs-on: ubuntu-latest
    steps:
      - name: Run AZALSCORE Linter
        run: npm run azalscore:lint # EXIT 1 si violation

      - name: Validate module structure
        run: npm run validate:modules

      - name: Validate meta.ts
        run: npm run validate:meta

      - name: Validate menu/route sync
        run: npm run validate:menu-route-sync

  # Autres jobs dépendent de validate-azalscore-norms
  build:
    needs: [validate-azalscore-norms]
    # ...
```

#### Branch Protection

**Configuration GitHub requise**:
- ✅ Require status checks to pass: `validate-azalscore-norms`
- ✅ Require branches to be up to date

---

## AZA-FE-DASH: Frontend Health Dashboard

### Principe

**Surface de gouvernance accessible dirigeants, product owners, et auditeurs.**

### Localisation
- **Page**: `/src/pages/FrontendHealthDashboard.tsx`
- **Route**: `/admin/frontend-health`
- **Accès**: Capability `admin.view` (restreint)

### Indicateurs Obligatoires

#### 1. Indicateurs Globaux

Affichés en cartes métriques:

| Indicateur | Description | Calcul |
|-----------|-------------|---------|
| **Total Modules** | Nombre total de modules | `Object.keys(moduleRegistry).length` |
| **Exposés Frontend** | Modules avec UI | `filter(m => m.frontend.hasUI)` |
| **Conformes AZA-FE** | Modules conformes | `filter(m => m.frontend.compliance && m.status === 'active')` |
| **Dégradés** | Modules partiels | `filter(m => m.status === 'degraded')` |
| **Bloqués** | Modules non conformes | `filter(m => !m.frontend.compliance || m.status === 'inactive')` |

#### 2. Indicateurs par Module

Affichés en tableau:

| Colonne | Description |
|---------|-------------|
| **Module** | Nom + code |
| **Backend** | API disponible (✓/✗) |
| **Frontend** | UI présente (✓/✗) |
| **Pages** | Nombre de pages |
| **Routes** | Nombre de routes |
| **Erreurs** | Nombre d'erreurs détectées |
| **Conformité AZA-FE** | Conforme (✓/✗) |
| **État** | Badge 🟢🟠🔴 |
| **Propriétaire** | Équipe responsable |
| **Dernier Audit** | Date (YYYY-MM-DD) |

#### 3. États Normatifs

| État | Icône | Condition |
|------|-------|-----------|
| **Conforme** | 🟢 | `compliance === true && status === 'active'` |
| **Dégradé** | 🟠 | `status === 'degraded'` |
| **Non conforme** | 🔴 | `compliance === false || status === 'inactive'` |

### Mise à Jour

- **Fréquence**: Temps réel (React state)
- **Source**: `moduleRegistry` importé directement
- **Rafraîchissement**: Automatique au chargement de la page

### Accès

```tsx
// src/routing/index.tsx
import { CapabilityRoute } from '@/routing/CapabilityRoute';
import { FrontendHealthDashboard } from '@/pages/FrontendHealthDashboard';

<Route
  path="/admin/frontend-health"
  element={
    <CapabilityRoute capability="admin.view">
      <FrontendHealthDashboard />
    </CapabilityRoute>
  }
/>
```

---

## AZA-FE-META: Frontend Module Metadata

### Principe

**Fichier `meta.ts` obligatoire dans chaque module.**

### Structure Obligatoire

```typescript
// src/modules/[module-name]/meta.ts

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Nom Lisible du Module',
  code: 'module-code',
  version: '1.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,                  // Module a une interface
    pagesCount: 3,                // Nombre de pages
    routesCount: 5,               // Nombre de routes
    errorsCount: 0,               // Erreurs détectées
    lastAudit: '2026-01-23',      // Date dernier audit
    compliance: true,             // Conformité AZA-FE
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,           // API disponible
    lastCheck: '2026-01-23',      // Date dernière vérification
    endpoints: [                  // Liste endpoints
      '/api/v1/resource',
      '/api/v1/resource/:id',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Équipe Backend',        // Responsable
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-01',
  updatedAt: '2026-01-23',
} as const;

export type ModuleMeta = typeof moduleMeta;
```

### Champs Obligatoires

#### Identification
- **name**: Nom affiché dans l'UI
- **code**: Identifiant unique (snake_case ou kebab-case)
- **version**: Version sémantique (semver)

#### État
- **status**: `active` | `degraded` | `inactive`
  - `active`: Module fonctionnel et complet
  - `degraded`: Module partiel ou avec limitations
  - `inactive`: Module désactivé

#### Frontend
- **hasUI**: Booléen indiquant si le module a une interface
- **pagesCount**: Nombre de pages dans le module
- **routesCount**: Nombre de routes définies
- **errorsCount**: Nombre d'erreurs détectées (0 si aucune)
- **lastAudit**: Date du dernier audit (YYYY-MM-DD)
- **compliance**: Conformité aux normes AZA-FE

#### Backend
- **apiAvailable**: API backend disponible
- **lastCheck**: Date de dernière vérification API
- **endpoints**: Liste des endpoints utilisés

#### Gouvernance
- **owner**: Équipe ou personne responsable
- **criticality**: Criticité du module (high/medium/low)

#### Audit
- **createdAt**: Date de création du module
- **updatedAt**: Date de dernière modification

### Génération Automatique

```bash
# Générer meta.ts pour tous les modules
npm run generate:meta

# Forcer la régénération (écrase existants)
npm run generate:meta -- --force
```

### Validation

```bash
# Valider tous les meta.ts
npm run validate:meta
```

**Vérifications**:
- ✅ Présence de `meta.ts` dans chaque module
- ✅ Présence de tous les champs obligatoires
- ✅ Format des dates (YYYY-MM-DD)
- ✅ Valeurs enum valides (status, criticality)

### Registre Global

**Fichier**: `/src/modules/registry.ts`

**Généré automatiquement** par `generate:meta`.

```typescript
// src/modules/registry.ts
import { moduleMeta as inventory } from './inventory/meta';
import { moduleMeta as invoicing } from './invoicing/meta';
// ... imports pour tous les modules

export const moduleRegistry: Record<string, ModuleMeta> = {
  'inventory': inventory,
  'invoicing': invoicing,
  // ... tous les modules
};

export type ModuleCode = keyof typeof moduleRegistry;
```

**Usage**:
```typescript
import { moduleRegistry } from '@/modules/registry';

// Accéder aux métadonnées d'un module
const inventoryMeta = moduleRegistry['inventory'];

// Vérifier si module existe
if (moduleRegistry['my-module']) {
  // ...
}

// Lister tous les modules actifs
const activeModules = Object.values(moduleRegistry)
  .filter(m => m.status === 'active');
```

---

## Standards de Développement

### Structure de Module Obligatoire

```
src/modules/[module-name]/
├── index.tsx           # ✅ OBLIGATOIRE - Point d'entrée avec layout
├── meta.ts             # ✅ OBLIGATOIRE - Métadonnées AZA-FE-META
├── types.ts            # ✅ OBLIGATOIRE - Types TypeScript
├── components/         # ✅ OBLIGATOIRE - Composants locaux
│   ├── TabView1.tsx
│   ├── TabView2.tsx
│   └── ...
├── tests/              # ✅ OBLIGATOIRE - Tests unitaires
│   ├── index.test.tsx
│   └── ...
└── README.md           # Recommandé - Documentation module
```

### Template Module

Utiliser le script de scaffolding:

```bash
npm run scaffold:module -- my-new-module
```

Ou créer manuellement avec le template:

```tsx
// src/modules/my-new-module/index.tsx
import { BaseViewStandard } from '@/ui-engine/layouts';

export default function MyNewModule() {
  return (
    <BaseViewStandard
      title="Mon Nouveau Module"
      icon="🔧"
    >
      <p>Contenu du module...</p>
    </BaseViewStandard>
  );
}
```

### Layouts Approuvés

#### 1. BaseViewStandard
**Usage**: Module avec tabs

```tsx
import { BaseViewStandard } from '@/ui-engine/layouts';

<BaseViewStandard
  title="Titre du Module"
  icon="📦"
  tabs={[
    { id: 'tab1', label: 'Onglet 1', content: <Tab1 /> },
    { id: 'tab2', label: 'Onglet 2', content: <Tab2 /> },
  ]}
/>
```

#### 2. UnifiedLayout
**Usage**: Layout global avec menu

```tsx
import { UnifiedLayout } from '@/ui-engine/layouts';

<UnifiedLayout>
  <YourContent />
</UnifiedLayout>
```

#### 3. MainLayout
**Usage**: Layout simple

```tsx
import { MainLayout } from '@/ui-engine/layouts';

<MainLayout title="Page Title">
  <YourContent />
</MainLayout>
```

---

## Conformité et Validation

### Checklist Pré-Commit

```bash
# 1. Linter
npm run lint

# 2. Type check
npm run type-check

# 3. AZALSCORE Linter (AZA-FE-ENF)
npm run azalscore:lint

# 4. Validation structure modules
npm run validate:modules

# 5. Validation meta.ts (AZA-FE-META)
npm run validate:meta
```

### Checklist Pré-Push

```bash
# 1. Tous les checks pré-commit
npm run validate:all

# 2. Menu/Route sync (AZA-FE-ENF)
npm run validate:menu-route-sync

# 3. Tests
npm run test -- --run
```

### Hooks Git

#### Pre-commit
```bash
# .husky/pre-commit
npx lint-staged
npm run azalscore:lint
npm run validate:modules
npm run validate:meta
```

#### Pre-push
```bash
# .husky/pre-push
npm run type-check
npm run validate:menu-route-sync
npm run test -- --run --passWithNoTests
```

### Validation CI/CD

Le pipeline DOIT inclure:

1. ✅ ESLint
2. ✅ TypeScript type-check
3. ✅ **AZALSCORE Linter (AZA-FE-ENF)** - BLOQUANT
4. ✅ **Validation meta.ts (AZA-FE-META)** - BLOQUANT
5. ✅ **Menu/Route sync (AZA-FE-ENF)** - BLOQUANT
6. ✅ Tests unitaires
7. ✅ Tests E2E (smoke tests)
8. ✅ Build production

### Critères GO/NO-GO Production

Avant tout déploiement en production:

- ✅ `npm run azalscore:lint` PASSE (0 violation)
- ✅ `npm run validate:meta` PASSE (100% modules)
- ✅ `npm run validate:menu-route-sync` PASSE (100% sync)
- ✅ Coverage tests ≥ 70% global
- ✅ Dashboard `/admin/frontend-health` accessible
- ✅ Tous modules avec `meta.ts` conforme
- ✅ 0 page vide détectée
- ✅ 0 lien mort détecté
- ✅ Performance Lighthouse ≥ 90

---

## FAQ

### Q1: Que faire si mon module n'a pas encore d'UI fonctionnelle?

**R**: Marquer le module avec `status: 'degraded'` dans `meta.ts` et fournir au minimum un contenu textuel (pas de `return null`).

```tsx
// ✅ ACCEPTABLE (status: degraded)
export default function MyModule() {
  return (
    <BaseViewStandard title="Mon Module" icon="🔧">
      <p>Module en cours de développement.</p>
      <p>Fonctionnalités prévues:</p>
      <ul>
        <li>Feature 1</li>
        <li>Feature 2</li>
      </ul>
    </BaseViewStandard>
  );
}
```

### Q2: Comment désactiver temporairement un module?

**R**: Mettre `status: 'inactive'` dans `meta.ts`. Le RouteGuard empêchera l'accès.

```typescript
// src/modules/my-module/meta.ts
export const moduleMeta = {
  // ...
  status: 'inactive' as const,
  // ...
};
```

### Q3: Mon module backend-only doit-il avoir un meta.ts?

**R**: OUI. Tous les modules dans `/src/modules` doivent avoir un `meta.ts`, même sans UI.

```typescript
export const moduleMeta = {
  name: 'Backend Module',
  code: 'backend-module',
  version: '1.0.0',
  status: 'active',

  frontend: {
    hasUI: false, // ⬅ Indiquer l'absence d'UI
    compliance: true,
    lastAudit: '2026-01-23',
  },

  backend: {
    apiAvailable: true,
    lastCheck: '2026-01-23',
    endpoints: ['/api/v1/resource'],
  },

  // ...
};
```

### Q4: Puis-je ignorer les violations AZA-FE-ENF temporairement?

**R**: **NON**. Les violations AZA-FE-ENF sont BLOQUANTES par design. Si nécessaire:
1. Marquer module `status: 'degraded'`
2. Créer une issue GitHub pour tracer la dette technique
3. Planifier correction dans sprint suivant

### Q5: Comment tester les Route Guards localement?

**R**: Modifier temporairement un `meta.ts` pour simuler violations:

```typescript
// Tester MODULE_INACTIVE
status: 'inactive',

// Tester NO_UI_CONTRACT
frontend: { hasUI: false, ... }

// Tester NON_COMPLIANT
frontend: { compliance: false, ... }
```

Naviguer vers le module et vérifier la redirection + journalisation.

### Q6: Le Dashboard est-il accessible en développement?

**R**: OUI, naviguer vers `/admin/frontend-health`. En production, l'accès est restreint à la capability `admin.view`.

### Q7: Que faire si le linter détecte un faux positif?

**R**:
1. Vérifier si la violation est légitime
2. Si faux positif avéré, ouvrir une issue sur le linter
3. En attendant correction, ajuster le pattern de détection dans `azalscore-linter.ts`

### Q8: Comment ajouter un nouveau layout approuvé?

**R**:
1. Créer le layout dans `/src/ui-engine/layouts`
2. Ajouter à la liste `acceptedLayouts` dans `azalscore-linter.ts`
3. Documenter dans cette norme (AZA-FE-NORMS.md)
4. Obtenir validation tech lead

---

## Contacts et Support

- **Tech Lead**: [À définir]
- **Product Owner**: [À définir]
- **Questions**: Ouvrir une issue GitHub avec tag `[AZA-FE]`
- **Documentation**: `/frontend/AZA-FE-NORMS.md`

---

## Historique des Versions

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2026-01-23 | Version initiale - Normes AZA-FE-ENF, AZA-FE-DASH, AZA-FE-META |

---

**🔒 Ce document définit des normes OBLIGATOIRES. Toute dérogation DOIT être approuvée par le Tech Lead et tracée.**
