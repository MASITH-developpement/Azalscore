#!/usr/bin/env tsx
/**
 * AZALSCORE - Validation Structure Module
 * =========================================
 * Vérifie que chaque module a la structure complète obligatoire:
 * - index.tsx (point d'entrée)
 * - types.ts (types TypeScript)
 * - meta.ts (métadonnées AZA-FE-META)
 * - components/ (composants locaux)
 * - tests/ (tests unitaires)
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// TYPES
// ============================================================

interface ModuleValidation {
  module: string;
  hasIndex: boolean;
  hasTypes: boolean;
  hasMeta: boolean;
  hasComponents: boolean;
  hasTests: boolean;
  isComplete: boolean;
  missingFiles: string[];
}

interface ValidationSummary {
  total: number;
  complete: number;
  partial: number;
  incomplete: number;
  violations: ModuleValidation[];
}

// ============================================================
// CONFIGURATION
// ============================================================

const MODULES_DIR = path.join(__dirname, '../../frontend/src/modules');

const REQUIRED_FILES = [
  { file: 'index.tsx', required: true },
  { file: 'types.ts', required: true },
  { file: 'meta.ts', required: true },
  { file: 'components', required: true, isDirectory: true },
  { file: 'tests', required: true, isDirectory: true },
];

// ============================================================
// VALIDATION FUNCTIONS
// ============================================================

function validateModuleStructure(moduleName: string): ModuleValidation {
  const modulePath = path.join(MODULES_DIR, moduleName);
  const missing: string[] = [];

  const hasIndex = fs.existsSync(path.join(modulePath, 'index.tsx'));
  const hasTypes = fs.existsSync(path.join(modulePath, 'types.ts'));
  const hasMeta = fs.existsSync(path.join(modulePath, 'meta.ts'));
  const hasComponents = fs.existsSync(path.join(modulePath, 'components'));
  const hasTests = fs.existsSync(path.join(modulePath, 'tests'));

  if (!hasIndex) missing.push('index.tsx');
  if (!hasTypes) missing.push('types.ts');
  if (!hasMeta) missing.push('meta.ts');
  if (!hasComponents) missing.push('components/');
  if (!hasTests) missing.push('tests/');

  const isComplete = missing.length === 0;

  return {
    module: moduleName,
    hasIndex,
    hasTypes,
    hasMeta,
    hasComponents,
    hasTests,
    isComplete,
    missingFiles: missing,
  };
}

function validateAllModules(): ValidationSummary {
  // Récupérer tous les modules
  const modules = fs
    .readdirSync(MODULES_DIR, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .filter((dirent) => !dirent.name.startsWith('_') && !dirent.name.startsWith('.'))
    .map((dirent) => dirent.name);

  console.log(`📋 Validation de ${modules.length} module(s)...\n`);

  // Valider chaque module
  const validations: ModuleValidation[] = modules.map(validateModuleStructure);

  // Catégoriser
  const complete = validations.filter((v) => v.isComplete);
  const partial = validations.filter(
    (v) => !v.isComplete && v.missingFiles.length < REQUIRED_FILES.length
  );
  const incomplete = validations.filter(
    (v) => v.missingFiles.length === REQUIRED_FILES.length
  );

  const violations = validations.filter((v) => !v.isComplete);

  return {
    total: modules.length,
    complete: complete.length,
    partial: partial.length,
    incomplete: incomplete.length,
    violations,
  };
}

// ============================================================
// DISPLAY FUNCTIONS
// ============================================================

function displaySummary(summary: ValidationSummary): void {
  console.log('📊 Résumé:');
  console.log('─'.repeat(60));
  console.log(`  Total modules:     ${summary.total}`);
  console.log(`  ✅ Complets:       ${summary.complete} (${Math.round(summary.complete / summary.total * 100)}%)`);
  console.log(`  ⚠️  Partiels:       ${summary.partial} (${Math.round(summary.partial / summary.total * 100)}%)`);
  console.log(`  ❌ Incomplets:     ${summary.incomplete} (${Math.round(summary.incomplete / summary.total * 100)}%)`);
  console.log();
}

function displayViolations(violations: ModuleValidation[]): void {
  if (violations.length === 0) {
    return;
  }

  console.log('⚠️  MODULES NON CONFORMES:');
  console.log('─'.repeat(60));

  violations.forEach((v, i) => {
    const icon = v.missingFiles.length < 3 ? '⚠️ ' : '❌';
    console.log(`  ${i + 1}. ${icon} ${v.module}`);
    console.log(`     Fichiers manquants: ${v.missingFiles.join(', ')}`);
  });

  console.log();
}

function displayCompleteness(): void {
  console.log('📋 Structure requise pour chaque module:');
  console.log('─'.repeat(60));
  REQUIRED_FILES.forEach((f) => {
    const type = f.isDirectory ? '📁' : '📄';
    console.log(`  ${type} ${f.file}`);
  });
  console.log();
}

// ============================================================
// MAIN EXECUTION
// ============================================================

function main() {
  console.log('🔍 Validation Structure Modules\n');
  console.log(`📁 Modules: ${MODULES_DIR}\n`);

  displayCompleteness();

  const summary = validateAllModules();

  displaySummary(summary);

  if (summary.violations.length > 0) {
    displayViolations(summary.violations);

    console.log('💡 Actions recommandées:');
    console.log('─'.repeat(60));
    console.log('  1. Utiliser le template: npm run scaffold:module -- <nom>');
    console.log('  2. Créer les fichiers manquants manuellement');
    console.log('  3. Générer meta.ts: npm run generate:meta');
    console.log();

    // Sortie avec code d'erreur si modules incomplets
    if (summary.incomplete > 0) {
      console.log('❌ Modules incomplets détectés. Correction obligatoire.\n');
      process.exit(1);
    } else if (summary.partial > 0) {
      console.log('⚠️  Modules partiels détectés. Complétion recommandée.\n');
      // Ne pas bloquer pour modules partiels
      process.exit(0);
    }
  } else {
    console.log('✅ Tous les modules ont la structure complète!\n');
    process.exit(0);
  }
}

// Run main if script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { validateModuleStructure, validateAllModules };
