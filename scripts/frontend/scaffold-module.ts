#!/usr/bin/env tsx
/**
 * AZALSCORE - Scaffold Module Structure
 * ======================================
 * Génère structure minimale conforme AZA-FE pour un module
 *
 * Usage: tsx scaffold-module.ts <module-name>
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// CONFIGURATION
// ============================================================

const MODULES_DIR = path.join(__dirname, '../../frontend/src/modules');

// ============================================================
// TEMPLATES
// ============================================================

function generateIndexTemplate(moduleName: string): string {
  const displayName = moduleName
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return `/**
 * AZALSCORE - Module ${displayName}
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ${moduleName.replace(/-/g, '_').replace(/^(.)/, (m) => m.toUpperCase())}Module: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="${displayName}"
      subtitle="Module ${moduleName}"
    >
      <div className="azals-module-content">
        <p>Module ${displayName} - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('${moduleName.replace(/-/g, '_')}')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ${moduleName.replace(/-/g, '_').replace(/^(.)/, (m) => m.toUpperCase())}Routes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<${moduleName.replace(/-/g, '_').replace(/^(.)/, (m) => m.toUpperCase())}Module />} />
    </Routes>
  );
};

export default ${moduleName.replace(/-/g, '_').replace(/^(.)/, (m) => m.toUpperCase())}Routes;
`;
}

function generateTypesTemplate(moduleName: string): string {
  const displayName = moduleName
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return `/**
 * AZALSCORE - Types Module ${displayName}
 * Conformité AZA-FE-META
 */

// ============================================================
// STATUS & ENUMS
// ============================================================

export type ItemStatus = 'draft' | 'active' | 'archived';

export const STATUS_CONFIG: Record<ItemStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  active: { label: 'Actif', color: 'green' },
  archived: { label: 'Archivé', color: 'gray' },
};

// ============================================================
// MAIN TYPES
// ============================================================

export interface Item {
  id: string;
  name: string;
  status: ItemStatus;
  created_at: string;
  updated_at: string;
}

// ============================================================
// API TYPES
// ============================================================

export interface ItemsResponse {
  items: Item[];
  total: number;
}

export interface ItemCreateInput {
  name: string;
}

export interface ItemUpdateInput {
  name?: string;
  status?: ItemStatus;
}

// ============================================================
// UTILITIES
// ============================================================

export function getStatusLabel(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.label || status;
}

export function getStatusColor(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.color || 'gray';
}
`;
}

function generateComponentsReadme(moduleName: string): string {
  return `# ${moduleName} Components

Ce dossier contient les composants réutilisables du module ${moduleName}.

## Structure recommandée

- **Tabs**: Composants onglets pour BaseViewStandard
- **Forms**: Formulaires de création/édition
- **Tables**: Composants tableaux spécifiques
- **Modals**: Modales du module

## Conventions

- Un composant = un fichier
- Export nommé preferred
- Props typées avec TypeScript
- Documentation JSDoc si complexe
`;
}

function generateTestsReadme(moduleName: string): string {
  return `# ${moduleName} Tests

Tests du module ${moduleName}.

## Structure

- **${moduleName}.test.tsx**: Tests unitaires composants
- **${moduleName}.api.test.ts**: Tests API/queries
- **${moduleName}.e2e.spec.ts**: Tests E2E Playwright

## Commandes

\`\`\`bash
npm run test -- ${moduleName}
npm run test:coverage -- ${moduleName}
npm run test:e2e -- ${moduleName}
\`\`\`
`;
}

// ============================================================
// SCAFFOLD FUNCTION
// ============================================================

function scaffoldModule(moduleName: string): void {
  const modulePath = path.join(MODULES_DIR, moduleName);

  // Vérifier si existe déjà
  if (fs.existsSync(modulePath)) {
    console.log(`⚠️  Module ${moduleName} existe déjà`);
    return;
  }

  console.log(`🔧 Création structure pour module: ${moduleName}`);

  // Créer répertoire principal
  fs.mkdirSync(modulePath, { recursive: true });

  // Créer index.tsx
  fs.writeFileSync(
    path.join(modulePath, 'index.tsx'),
    generateIndexTemplate(moduleName)
  );
  console.log(`   ✅ index.tsx créé`);

  // Créer types.ts
  fs.writeFileSync(
    path.join(modulePath, 'types.ts'),
    generateTypesTemplate(moduleName)
  );
  console.log(`   ✅ types.ts créé`);

  // Créer components/
  const componentsPath = path.join(modulePath, 'components');
  fs.mkdirSync(componentsPath, { recursive: true });
  fs.writeFileSync(
    path.join(componentsPath, 'README.md'),
    generateComponentsReadme(moduleName)
  );
  console.log(`   ✅ components/ créé`);

  // Créer tests/
  const testsPath = path.join(modulePath, 'tests');
  fs.mkdirSync(testsPath, { recursive: true });
  fs.writeFileSync(
    path.join(testsPath, 'README.md'),
    generateTestsReadme(moduleName)
  );
  console.log(`   ✅ tests/ créé`);

  console.log(`\n✅ Module ${moduleName} scaffoldé avec succès!`);
  console.log(`\n📖 Prochaines étapes:`);
  console.log(`   1. Adapter index.tsx selon besoins métier`);
  console.log(`   2. Enrichir types.ts`);
  console.log(`   3. Créer composants dans components/`);
  console.log(`   4. Ajouter tests dans tests/`);
  console.log(`   5. Générer meta.ts: npm run generate:meta`);
}

// ============================================================
// MAIN
// ============================================================

function main() {
  const moduleName = process.argv[2];

  if (!moduleName) {
    console.error('❌ Usage: tsx scaffold-module.ts <module-name>');
    console.error('   Exemple: tsx scaffold-module.ts gestion-stock');
    process.exit(1);
  }

  // Valider nom module
  if (!/^[a-z0-9-]+$/.test(moduleName)) {
    console.error('❌ Nom module invalide. Utiliser: minuscules, chiffres, tirets');
    process.exit(1);
  }

  scaffoldModule(moduleName);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { scaffoldModule };
