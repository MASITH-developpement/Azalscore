# Module Template

Template pour créer un nouveau module AZALSCORE conforme aux normes AZA-FE.

## Structure

```
_TEMPLATE/
├── index.tsx           # Point d'entrée avec BaseViewStandard
├── types.ts            # Types TypeScript
├── meta.ts             # Métadonnées AZA-FE-META
├── components/         # Composants locaux
│   ├── Tab1View.tsx
│   └── Tab2View.tsx
├── tests/              # Tests unitaires
│   └── index.test.tsx
└── README.md           # Cette documentation
```

## Utilisation

### 1. Copier le template

```bash
npm run scaffold:module -- mon-nouveau-module
```

Ou manuellement :

```bash
cp -r src/modules/_TEMPLATE src/modules/mon-nouveau-module
```

### 2. Personnaliser

- **index.tsx** : Modifier le titre, l'icône et les tabs
- **types.ts** : Définir les interfaces spécifiques
- **meta.ts** : Mettre à jour les métadonnées
- **components/** : Créer les vues nécessaires
- **tests/** : Ajouter les tests

### 3. Enregistrer

```bash
# Générer/mettre à jour meta.ts et registry
npm run generate:meta
```

### 4. Valider

```bash
# Vérifier conformité AZA-FE
npm run azalscore:lint
npm run validate:meta
```

## Conformité AZA-FE

Ce template garantit :

- ✅ Utilisation de BaseViewStandard (AZA-FE-ENF)
- ✅ Structure complète (index.tsx + types.ts + meta.ts + components/ + tests/)
- ✅ Métadonnées conformes AZA-FE-META
- ✅ Tests inclus
- ✅ Aucun composant vide

## Routes

Pour ajouter une route :

```tsx
// src/routing/index.tsx
import MonNouveauModule from '@/modules/mon-nouveau-module';

<Route
  path="/mon-nouveau-module/*"
  element={
    <RouteGuard moduleCode="mon-nouveau-module">
      <MonNouveauModule />
    </RouteGuard>
  }
/>
```

## Menu

Pour ajouter au menu :

```tsx
// src/ui-engine/top-menu/index.tsx ou menu-dynamic/index.tsx
{
  label: 'Mon Nouveau Module',
  path: '/mon-nouveau-module',
  icon: '🔧',
}
```

## Documentation

Voir `/frontend/AZA-FE-NORMS.md` pour les normes complètes.
