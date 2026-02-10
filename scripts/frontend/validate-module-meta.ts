#!/usr/bin/env tsx
/**
 * AZALSCORE - Validation meta.ts (AZA-FE-META)
 * =============================================
 * Valide présence et conformité des fichiers meta.ts
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// TYPES
// ============================================================

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

interface ModuleValidation {
  module: string;
  hasMeta: boolean;
  hasAllFields: boolean;
  missingFields: string[];
}

// ============================================================
// CONFIGURATION
// ============================================================

const MODULES_DIR = path.join(__dirname, '../../frontend/src/modules');

const REQUIRED_FIELDS = [
  'name',
  'code',
  'version',
  'status',
  'frontend',
  'frontend.hasUI',
  'frontend.lastAudit',
  'frontend.compliance',
  'backend',
  'backend.apiAvailable',
  'backend.lastCheck',
  'owner',
  'criticality',
  'createdAt',
  'updatedAt',
];

// ============================================================
// VALIDATION FUNCTIONS
// ============================================================

function validateMetaFile(moduleName: string): ModuleValidation {
  const metaPath = path.join(MODULES_DIR, moduleName, 'meta.ts');

  // Vérifier existence
  if (!fs.existsSync(metaPath)) {
    return {
      module: moduleName,
      hasMeta: false,
      hasAllFields: false,
      missingFields: REQUIRED_FIELDS,
    };
  }

  // Lire le contenu
  const content = fs.readFileSync(metaPath, 'utf-8');

  // Vérifier champs obligatoires
  const missingFields = REQUIRED_FIELDS.filter((field) => {
    // Pour les champs imbriqués (ex: frontend.hasUI)
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      return !content.includes(`${parent}:`) || !content.includes(`${child}:`);
    }
    return !content.includes(`${field}:`);
  });

  return {
    module: moduleName,
    hasMeta: true,
    hasAllFields: missingFields.length === 0,
    missingFields,
  };
}

function validateAllModules(): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Récupérer tous les modules
  const modules = fs
    .readdirSync(MODULES_DIR, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .filter((dirent) => !dirent.name.startsWith('_') && !dirent.name.startsWith('.'))
    .map((dirent) => dirent.name);

  console.log(`📋 Validation de ${modules.length} module(s)...\n`);

  // Valider chaque module
  const validations: ModuleValidation[] = [];

  modules.forEach((moduleName) => {
    const validation = validateMetaFile(moduleName);
    validations.push(validation);

    if (!validation.hasMeta) {
      errors.push(`[AZA-FE-META] Module "${moduleName}" sans meta.ts`);
    } else if (!validation.hasAllFields) {
      warnings.push(
        `[AZA-FE-META] Module "${moduleName}": champs manquants: ${validation.missingFields.join(
          ', '
        )}`
      );
    }
  });

  // Statistiques
  const withMeta = validations.filter((v) => v.hasMeta).length;
  const compliant = validations.filter((v) => v.hasAllFields).length;

  console.log('📊 Statistiques:');
  console.log(`   Modules avec meta.ts: ${withMeta}/${modules.length}`);
  console.log(`   Conformes AZA-FE-META: ${compliant}/${modules.length}\n`);

  return {
    valid: errors.length === 0 && warnings.length === 0,
    errors,
    warnings,
  };
}

// ============================================================
// MAIN EXECUTION
// ============================================================

function main() {
  console.log('🔍 Validation meta.ts (AZA-FE-META)\n');
  console.log(`📁 Modules: ${MODULES_DIR}\n`);

  const result = validateAllModules();

  if (result.valid) {
    console.log('✅ Métadonnées conformes AZA-FE-META sur tous les modules\n');
    process.exit(0);
  } else {
    if (result.errors.length > 0) {
      console.log('❌ ERREURS:');
      console.log('─'.repeat(80));
      result.errors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
      console.log();
    }

    if (result.warnings.length > 0) {
      console.log('⚠️  WARNINGS:');
      console.log('─'.repeat(80));
      result.warnings.forEach((warning, i) => {
        console.log(`  ${i + 1}. ${warning}`);
      });
      console.log();
    }

    console.log('💡 Violations AZA-FE-META. Correction obligatoire.');
    console.log('📖 Exécutez: npm run generate:meta\n');

    process.exit(1);
  }
}

// Run main if script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { validateMetaFile, validateAllModules };
