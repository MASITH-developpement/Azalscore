#!/usr/bin/env tsx
/**
 * AZALSCORE - Générateur meta.ts (AZA-FE-META)
 * =============================================
 * Génère fichiers meta.ts pour modules existants
 * Analyse automatique pour pré-remplir les métadonnées
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// TYPES
// ============================================================

interface ModuleAnalysis {
  name: string;
  code: string;
  hasIndex: boolean;
  hasTypes: boolean;
  hasComponents: boolean;
  hasTests: boolean;
  isEmpty: boolean;
  hasPlaceholder: boolean;
  status: 'active' | 'degraded' | 'inactive';
  compliance: boolean;
}

// ============================================================
// CONFIGURATION
// ============================================================

const MODULES_DIR = path.join(__dirname, '../../frontend/src/modules');
const TEMPLATE_PATH = path.join(MODULES_DIR, '_TEMPLATE/meta.ts');

// ============================================================
// MODULE ANALYSIS
// ============================================================

function analyzeModule(moduleName: string): ModuleAnalysis {
  const modulePath = path.join(MODULES_DIR, moduleName);

  // Vérifier fichiers
  const hasIndex = fs.existsSync(path.join(modulePath, 'index.tsx'));
  const hasTypes = fs.existsSync(path.join(modulePath, 'types.ts'));
  const hasComponents = fs.existsSync(path.join(modulePath, 'components'));
  const hasTests = fs.existsSync(path.join(modulePath, 'tests'));

  // Analyser le contenu si index.tsx existe
  let isEmpty = false;
  let hasPlaceholder = false;

  if (hasIndex) {
    const indexContent = fs.readFileSync(path.join(modulePath, 'index.tsx'), 'utf-8');

    // Patterns composants vides
    const emptyPatterns = [
      /return\s+null/,
      /return\s+<>\s*<\/>/,
      /return\s+<div>\s*<\/div>/,
    ];

    // Patterns placeholders
    const placeholderPatterns = [
      /TODO:?\s+Implement/i,
      /PLACEHOLDER/i,
      /COMING\s+SOON/i,
      /À\s+IMPLÉMENTER/i,
    ];

    isEmpty = emptyPatterns.some((pattern) => pattern.test(indexContent));
    hasPlaceholder = placeholderPatterns.some((pattern) =>
      pattern.test(indexContent)
    );
  }

  // Déterminer statut
  let status: 'active' | 'degraded' | 'inactive' = 'active';

  if (!hasIndex || isEmpty) {
    status = 'inactive';
  } else if (hasPlaceholder || !hasTypes) {
    status = 'degraded';
  }

  // Déterminer conformité AZA-FE
  const compliance = hasIndex && hasTypes && hasComponents && hasTests && !isEmpty;

  // Formatter le nom (capitaliser première lettre)
  const name = moduleName
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return {
    name,
    code: moduleName,
    hasIndex,
    hasTypes,
    hasComponents,
    hasTests,
    isEmpty,
    hasPlaceholder,
    status,
    compliance,
  };
}

// ============================================================
// META.TS GENERATION
// ============================================================

function generateMetaContent(analysis: ModuleAnalysis): string {
  const today = new Date().toISOString().split('T')[0];

  return `/**
 * AZALSCORE - Métadonnées Module ${analysis.name} (AZA-FE-META)
 * =============================================
 * Fichier généré automatiquement - Mettre à jour si nécessaire
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: '${analysis.name}',
  code: '${analysis.code}',
  version: '1.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: '${analysis.status}' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: ${analysis.hasIndex},
    pagesCount: 1,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '${today}',
    compliance: ${analysis.compliance},
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: false, // À vérifier manuellement
    lastCheck: '${today}',
    endpoints: [],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'À définir',
  criticality: 'medium' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '${today}',
  updatedAt: '${today}',
} as const;

export type ModuleMeta = typeof moduleMeta;
`;
}

function generateMetaFile(moduleName: string, force: boolean = false): boolean {
  const metaPath = path.join(MODULES_DIR, moduleName, 'meta.ts');

  // Vérifier si existe déjà
  if (fs.existsSync(metaPath) && !force) {
    console.log(`   ⚠️  Ignoré: ${moduleName} (meta.ts existe déjà)`);
    return false;
  }

  // Analyser le module
  const analysis = analyzeModule(moduleName);

  // Générer le contenu
  const content = generateMetaContent(analysis);

  // Écrire le fichier
  fs.writeFileSync(metaPath, content, 'utf-8');

  // Status icon
  const statusIcon =
    analysis.status === 'active'
      ? '🟢'
      : analysis.status === 'degraded'
      ? '🟠'
      : '🔴';

  console.log(
    `   ${statusIcon} Créé: ${moduleName} (${analysis.status}${
      analysis.compliance ? ', conforme' : ', non conforme'
    })`
  );

  return true;
}

// ============================================================
// REGISTRY GENERATION
// ============================================================

function generateRegistry(moduleNames: string[]): void {
  const registryPath = path.join(MODULES_DIR, 'registry.ts');

  // Générer les imports
  const imports = moduleNames
    .filter((name) => fs.existsSync(path.join(MODULES_DIR, name, 'meta.ts')))
    .map((name) => {
      const varName = name.replace(/-/g, '_'); // converter-case -> converter_case
      return `import { moduleMeta as ${varName} } from './${name}/meta';`;
    })
    .join('\n');

  // Générer le registre
  const registryEntries = moduleNames
    .filter((name) => fs.existsSync(path.join(MODULES_DIR, name, 'meta.ts')))
    .map((name) => {
      const varName = name.replace(/-/g, '_');
      return `  '${name}': ${varName},`;
    })
    .join('\n');

  const content = `/**
 * AZALSCORE - Registre Global des Modules (AZA-FE-META)
 * ======================================================
 * Import centralisé de toutes métadonnées
 *
 * Ce fichier est généré automatiquement par generate-module-meta.ts
 * NE PAS MODIFIER MANUELLEMENT
 */

${imports}

export interface ModuleMeta {
  name: string;
  code: string;
  version: string;
  status: 'active' | 'degraded' | 'inactive';
  frontend: {
    hasUI: boolean;
    pagesCount?: number;
    routesCount?: number;
    errorsCount?: number;
    lastAudit: string;
    compliance: boolean;
  };
  backend: {
    apiAvailable: boolean;
    lastCheck: string;
    endpoints?: string[];
  };
  owner: string;
  criticality: 'high' | 'medium' | 'low';
  createdAt: string;
  updatedAt: string;
}

export const moduleRegistry: Record<string, ModuleMeta> = {
${registryEntries}
};

export type ModuleCode = keyof typeof moduleRegistry;
`;

  fs.writeFileSync(registryPath, content, 'utf-8');
  console.log(`\n✅ Registre mis à jour: ${registryPath}`);
}

// ============================================================
// MAIN EXECUTION
// ============================================================

function main() {
  console.log('🔧 Génération meta.ts pour tous les modules (AZA-FE-META)\n');
  console.log(`📁 Modules: ${MODULES_DIR}\n`);

  // Récupérer tous les modules
  const modules = fs
    .readdirSync(MODULES_DIR, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .filter((dirent) => !dirent.name.startsWith('_') && !dirent.name.startsWith('.'))
    .map((dirent) => dirent.name);

  console.log(`📋 Trouvé: ${modules.length} module(s)\n`);

  // Vérifier si --force flag
  const force = process.argv.includes('--force');

  if (force) {
    console.log('⚠️  Mode --force: remplacement des meta.ts existants\n');
  }

  // Générer meta.ts pour chaque module
  let created = 0;
  let skipped = 0;

  modules.forEach((moduleName) => {
    const wasCreated = generateMetaFile(moduleName, force);
    if (wasCreated) {
      created++;
    } else {
      skipped++;
    }
  });

  console.log(`\n📊 Résumé:`);
  console.log(`   Créés: ${created}`);
  console.log(`   Ignorés: ${skipped}`);
  console.log(`   Total: ${modules.length}\n`);

  // Générer le registre global
  console.log('🔧 Génération du registre global...');
  generateRegistry(modules);

  console.log('\n✅ Génération terminée!\n');
  console.log('📖 Prochaines étapes:');
  console.log('   1. Vérifier meta.ts générés: npm run validate:meta');
  console.log('   2. Mettre à jour propriétaires et criticité manuellement');
  console.log('   3. Vérifier conformité AZA-FE: npm run azalscore:lint\n');
}

// Run main if script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { analyzeModule, generateMetaFile, generateRegistry };
