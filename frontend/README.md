# AZALSCORE Frontend

Interface utilisateur de la plateforme ERP AZALSCORE.

## 🎯 État Actuel

**Phase actuelle:** Phase 1 - Normalisation Modules Critiques (En cours)
**Conformité normes AZA-FE:** 🟡 En progression (44% modules conformes)

### Métriques Clés

```
✅ Modules avec meta.ts:        41/41 (100%)
✅ Dashboard de santé:          Opérationnel
🟡 Violations AZA-FE-ENF:       23 (objectif: 0)
🟡 Modules conformes:           18/41 (44%)
```

### Évolution

```
Violations AZA-FE-ENF: 35 → 26 → 23 (-34% 🟢)
```

---

## 🚀 Démarrage Rapide

### Installation

```bash
cd frontend
npm install
```

### Développement

```bash
# Serveur de développement
npm run dev

# → http://localhost:5173
```

### Validation

```bash
# Validation complète (avant commit)
npm run validate:all

# Vérifications individuelles
npm run azalscore:lint              # Linter normatif AZALSCORE
npm run validate:meta               # Métadonnées modules
npm run validate:menu-route-sync    # Synchronisation menu/routes
npm run lint                        # ESLint
npm run type-check                  # TypeScript
npm run test                        # Tests unitaires
```

### Création de Module

```bash
# Créer un nouveau module conforme AZA-FE
npm run scaffold:module -- mon-nouveau-module

# Générer les métadonnées
npm run generate:meta

# Valider la structure
npm run validate:modules
```

---

## 📚 Documentation

### Essentiel

- **[AZA-FE-NORMS.md](./AZA-FE-NORMS.md)** - Normes AZALSCORE (15,000 mots)
  - AZA-FE-ENF : Enforcement technique
  - AZA-FE-DASH : Dashboard de santé
  - AZA-FE-META : Métadonnées modules

- **[PROGRESS_REPORT.md](./PROGRESS_REPORT.md)** - Suivi des progrès
  - Métriques actuelles
  - Violations détaillées
  - Prochaines étapes

- **[IMPLEMENTATION_REPORT.md](./IMPLEMENTATION_REPORT.md)** - Rapport détaillé Phase 0
  - Livrables complétés
  - Architecture implémentée
  - Décisions techniques

### Template & Guides

- **[src/modules/_TEMPLATE/](./src/modules/_TEMPLATE/)** - Template de module
  - Structure complète conforme AZA-FE
  - Exemples de composants
  - Tests inclus

---

## 🏗️ Architecture

### Structure Projet

```
frontend/
├── src/
│   ├── modules/              # Modules métiers (41 modules)
│   │   ├── _TEMPLATE/        # Template pour nouveaux modules
│   │   ├── login/            # Page connexion
│   │   ├── profile/          # Profil utilisateur
│   │   ├── comptabilite/     # Comptabilité
│   │   └── ...
│   ├── routing/              # Configuration routes
│   │   ├── index.tsx         # Routes principales
│   │   └── RouteGuard.tsx    # Guards de routes (AZA-FE-ENF)
│   ├── ui-engine/            # Composants UI
│   │   ├── layout/           # Layouts
│   │   ├── components/       # Composants réutilisables
│   │   └── ...
│   └── pages/                # Pages globales
│       └── FrontendHealthDashboard.tsx  # Dashboard AZA-FE-DASH
├── scripts/                  # Scripts de validation
│   └── frontend/
│       ├── azalscore-linter.ts           # Linter normatif
│       ├── generate-module-meta.ts       # Générateur meta.ts
│       ├── validate-module-meta.ts       # Validateur meta.ts
│       ├── validate-menu-route-sync.ts   # Validateur menu/routes
│       ├── validate-module-structure.ts  # Validateur structure
│       └── scaffold-module.ts            # Générateur modules
├── .husky/                   # Hooks Git
│   ├── pre-commit            # Validation pré-commit
│   └── pre-push              # Validation pré-push
├── .github/workflows/        # CI/CD
│   └── frontend-ci.yml       # Pipeline avec validations AZA-FE
└── docs/
    ├── AZA-FE-NORMS.md              # Normes complètes
    ├── PROGRESS_REPORT.md           # Suivi progrès
    └── IMPLEMENTATION_REPORT.md     # Rapport détaillé
```

### Normes AZALSCORE

#### AZA-FE-ENF (Enforcement Technique)

**Principe:** Toute violation DOIT être détectée automatiquement et empêcher le déploiement.

**Mécanismes:**
- ✅ Linter normatif AZALSCORE
- ✅ Route Guards avec journalisation
- ✅ Vérification menu ↔ route automatique
- ✅ Blocage CI/CD si violations

#### AZA-FE-DASH (Dashboard de Santé)

**Principe:** Surface de gouvernance pour dirigeants/product/auditeurs.

**Accès:** `/admin/frontend-health` (capability `admin.view`)

**Indicateurs:**
- Globaux : Total modules, conformes, dégradés, bloqués
- Par module : Backend/frontend, pages, routes, erreurs, conformité

#### AZA-FE-META (Métadonnées Modules)

**Principe:** Fichier `meta.ts` obligatoire dans chaque module.

**Structure:**
- Identification (name, code, version)
- État (status : active/degraded/inactive)
- Frontend (hasUI, compliance, pages, routes)
- Backend (apiAvailable, endpoints)
- Gouvernance (owner, criticality)

---

## 🛠️ Scripts NPM

### Développement

```bash
npm run dev              # Serveur développement (Vite)
npm run build            # Build production
npm run preview          # Preview build
```

### Tests

```bash
npm run test             # Tests unitaires (Vitest)
npm run test:coverage    # Tests avec coverage
npm run test:e2e         # Tests E2E (Playwright)
```

### Qualité Code

```bash
npm run lint             # ESLint
npm run lint:fix         # ESLint auto-fix
npm run format           # Prettier format
npm run format:check     # Prettier check
npm run type-check       # TypeScript check
```

### Normes AZALSCORE ⭐

```bash
npm run azalscore:lint              # Linter normatif (AZA-FE-ENF)
npm run scaffold:module             # Créer nouveau module
npm run generate:meta               # Générer meta.ts (AZA-FE-META)
npm run validate:modules            # Valider structure modules
npm run validate:meta               # Valider meta.ts (AZA-FE-META)
npm run validate:menu-route-sync    # Valider menu ↔ route (AZA-FE-ENF)
npm run validate:all                # Validation complète
```

---

## 🔍 Dashboard de Santé Frontend

Accédez au dashboard pour visualiser l'état de tous les modules :

```bash
npm run dev
# → http://localhost:5173/admin/frontend-health
```

**Indicateurs disponibles:**
- Nombre total de modules
- Modules conformes vs dégradés vs bloqués
- Détails par module (backend, frontend, conformité, erreurs)
- États normatifs 🟢🟠🔴

---

## ✅ Checklist Pré-Commit

Avant chaque commit, vérifiez :

```bash
# 1. Linter normatif AZALSCORE
npm run azalscore:lint

# 2. Structure modules
npm run validate:modules

# 3. Métadonnées
npm run validate:meta

# 4. Qualité code
npm run lint
npm run type-check

# OU tout en une commande:
npm run validate:all
```

**Note:** Les hooks Git exécutent automatiquement ces vérifications.

---

## 🚧 Travail en Cours (Phase 1)

### Priorités Immédiates

1. **Créer modules critiques manquants**
   - comptabilite (vide actuellement)
   - factures (vide actuellement)

2. **Mettre à jour routing**
   - Ajouter routes manquantes pour menu
   - Intégrer RouteGuard partout

3. **Réduire violations**
   - Objectif : 23 → <15 violations
   - Remplacer placeholders par contenu minimal

### Modules Nécessitant Attention

**Vides (priorité HAUTE):**
- admin, comptabilite, factures, invoicing, partners, purchases, inventory

**Partiels (priorité MOYENNE):**
- production, qualite, devis, commandes, crm, interventions

**Voir:** [PROGRESS_REPORT.md](./PROGRESS_REPORT.md) pour détails complets

---

## 📖 Guides de Contribution

### Créer un Nouveau Module

1. **Générer la structure**
   ```bash
   npm run scaffold:module -- mon-module
   ```

2. **Adapter le code**
   - Modifier `index.tsx` selon besoins métier
   - Enrichir `types.ts` avec vos interfaces
   - Créer composants dans `components/`
   - Ajouter tests dans `tests/`

3. **Générer les métadonnées**
   ```bash
   npm run generate:meta
   ```

4. **Valider**
   ```bash
   npm run validate:all
   ```

5. **Ajouter au routing**
   ```tsx
   // src/routing/index.tsx
   import MonModule from '@/modules/mon-module';

   <Route
     path="/mon-module/*"
     element={
       <RouteGuard moduleCode="mon-module">
         <MonModule />
       </RouteGuard>
     }
   />
   ```

### Layouts Approuvés

Utilisez **toujours** un des layouts suivants :

- `BaseViewStandard` - Recommandé (avec tabs)
- `MainLayout` - Simple
- `UnifiedLayout` - Avec menu global
- `PageWrapper` - Wrapper basique
- `Page` - Pour système UI custom

**Exemple:**

```tsx
import { BaseViewStandard } from '@/ui-engine/layouts/BaseViewStandard';

export default function MonModule() {
  return (
    <BaseViewStandard
      title="Mon Module"
      icon="📦"
      tabs={[
        { id: 'tab1', label: 'Vue 1', content: <Tab1 /> },
      ]}
    />
  );
}
```

---

## 🔒 Normes de Sécurité

- ✅ Route Guards vérifient permissions
- ✅ Capability-based access control
- ✅ Journalisation violations obligatoire
- ✅ Pas de composants vides en production
- ✅ TypeScript strict mode

---

## 🐛 Dépannage

### "Module non conforme" dans le dashboard

1. Vérifier que `meta.ts` existe :
   ```bash
   ls src/modules/mon-module/meta.ts
   ```

2. Régénérer si nécessaire :
   ```bash
   npm run generate:meta
   ```

3. Valider :
   ```bash
   npm run validate:meta
   ```

### Violations AZA-FE-ENF

```bash
# Voir détails
npm run azalscore:lint

# Vérifier structure
npm run validate:modules

# Vérifier menu/routes
npm run validate:menu-route-sync
```

### Hooks Git bloquent commit

Les hooks vérifient la conformité. Pour résoudre :

```bash
# Identifier le problème
npm run validate:all

# Corriger les violations
# ... faire les corrections ...

# Réessayer le commit
git commit -m "..."
```

---

## 📞 Support

**Documentation:**
- Normes complètes : [AZA-FE-NORMS.md](./AZA-FE-NORMS.md)
- FAQ : Voir section FAQ dans AZA-FE-NORMS.md
- Suivi progrès : [PROGRESS_REPORT.md](./PROGRESS_REPORT.md)

**Outils:**
- Dashboard : `/admin/frontend-health`
- Linter : `npm run azalscore:lint`
- Validation : `npm run validate:all`

**Issues:**
- Ouvrir issue GitHub avec tag `[AZA-FE]`

---

## 📊 Statistiques

- **Total modules:** 41
- **Modules conformes AZA-FE:** 18/41 (44%)
- **Coverage métadonnées:** 41/41 (100%)
- **Violations restantes:** 23
- **Réduction violations:** -34% depuis début

**Objectif final:** 0 violations, 100% conformité

---

## 🎉 Phase 0 Complétée ✅

Infrastructure de qualité et normes AZALSCORE opérationnelles :

- ✅ Linter normatif AZALSCORE
- ✅ Route Guards avec journalisation
- ✅ Dashboard de santé frontend
- ✅ Métadonnées 41 modules
- ✅ Hooks Git
- ✅ Pipeline CI/CD
- ✅ Documentation complète (15,000+ mots)

**Prêt pour Phase 1 !**

---

**Version:** 1.0.0
**Dernière mise à jour:** 2026-01-23
**Licence:** Propriétaire AZALSCORE
