#!/usr/bin/env tsx
/**
 * AZALSCORE - Register Modules in Router & Menu
 * ==============================================
 * Enregistre automatiquement les modules frontend dans:
 * - routing/index.tsx (lazy imports + routes)
 * - menu-dynamic/index.tsx (entrées de menu)
 *
 * Usage: tsx register-modules.ts [--dry-run]
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// CONFIGURATION
// ============================================================

const FRONTEND_DIR = path.join(__dirname, '../../frontend/src');
const MODULES_DIR = path.join(FRONTEND_DIR, 'modules');
const ROUTING_FILE = path.join(FRONTEND_DIR, 'routing/index.tsx');
const MENU_FILE = path.join(FRONTEND_DIR, 'ui-engine/menu-dynamic/index.tsx');

// Modules à ignorer (utilitaires, templates, etc.)
const IGNORED_MODULES = [
  '_TEMPLATE',
  'not-found',
  'registry.ts',
  'enrichment',  // Module utilitaire (pas de page)
  'i18n',        // Module utilitaire (internationalisation)
];

// Mapping module -> section du menu
const MODULE_SECTION_MAP: Record<string, string> = {
  // Finance
  'accounting': 'finance',
  'treasury': 'finance',
  'finance': 'finance',
  'expenses': 'finance',
  'consolidation': 'finance',
  'comptabilite': 'finance',
  'automated-accounting': 'finance',

  // Gestion
  'partners': 'gestion',
  'contacts': 'gestion',
  'invoicing': 'gestion',
  'purchases': 'gestion',
  'hr': 'gestion',
  'hr-vault': 'gestion',
  'timesheet': 'gestion',
  'contracts': 'gestion',
  'affaires': 'gestion',
  'devis': 'gestion',
  'factures': 'gestion',
  'commandes': 'gestion',
  'ordres-service': 'gestion',

  // Logistique & Production
  'inventory': 'logistique',
  'production': 'logistique',
  'quality': 'logistique',
  'qualite': 'logistique',
  'qc': 'logistique',
  'maintenance': 'logistique',
  'assets': 'logistique',
  'warranty': 'logistique',
  'vehicles': 'logistique',
  'procurement': 'logistique',

  // Opérations
  'projects': 'operations',
  'interventions': 'operations',
  'helpdesk': 'operations',
  'field-service': 'operations',
  'complaints': 'operations',
  'worksheet': 'operations',
  'saisie': 'operations',

  // Ventes & Commerce
  'pos': 'ventes',
  'ecommerce': 'ventes',
  'marketplace': 'ventes',
  'subscriptions': 'ventes',
  'payments': 'ventes',
  'stripe-integration': 'ventes',
  'commercial': 'ventes',
  'rfq': 'ventes',
  'crm': 'ventes',
  'enrichment': 'ventes',
  'social-networks': 'ventes',

  // Digital & Reporting
  'web': 'digital',
  'website': 'digital',
  'mobile': 'digital',
  'bi': 'digital',
  'compliance': 'digital',
  'email': 'digital',
  'broadcast': 'digital',
  'esignature': 'digital',
  'i18n': 'digital',

  // Import
  'import': 'import',
  'import-gateways': 'import',
  'odoo-import': 'import',
  'country-packs': 'import',
  'country-packs-france': 'import',

  // Admin
  'admin': 'admin',
  'iam': 'admin',
  'tenants': 'admin',
  'audit': 'admin',
  'backup': 'admin',
  'autoconfig': 'admin',
  'triggers': 'admin',
  'guardian': 'admin',
  'settings': 'admin',
  'profile': 'admin',
  'break-glass': 'admin',

  // Principal
  'cockpit': 'main',
  'marceau': 'main',
  'ai-assistant': 'main',
};

// Labels français pour les modules
const MODULE_LABELS: Record<string, string> = {
  'ai-assistant': 'Assistant IA',
  'affaires': 'Affaires',
  'assets': 'Immobilisations',
  'audit': 'Audit',
  'autoconfig': 'Configuration Auto',
  'automated-accounting': 'Comptabilité Auto',
  'backup': 'Sauvegardes',
  'break-glass': 'Accès d\'Urgence',
  'broadcast': 'Diffusion',
  'commandes': 'Commandes',
  'commercial': 'Commercial',
  'complaints': 'Réclamations',
  'comptabilite': 'Comptabilité',
  'consolidation': 'Consolidation',
  'contracts': 'Contrats',
  'country-packs': 'Packs Pays',
  'country-packs-france': 'Pack France',
  'crm': 'CRM',
  'devis': 'Devis',
  'email': 'Email',
  'enrichment': 'Enrichissement',
  'esignature': 'Signature Électronique',
  'expenses': 'Notes de Frais',
  'factures': 'Factures',
  'field-service': 'Service Terrain',
  'finance': 'Finance',
  'guardian': 'Guardian (Sécurité)',
  'hr-vault': 'Coffre-fort RH',
  'i18n': 'Internationalisation',
  'iam': 'Gestion des Accès',
  'import': 'Import Données',
  'import-gateways': 'Passerelles Import',
  'odoo-import': 'Import Odoo',
  'ordres-service': 'Ordres de Service',
  'procurement': 'Approvisionnement',
  'profile': 'Profil',
  'qc': 'Contrôle Qualité',
  'qualite': 'Qualité',
  'rfq': 'Appels d\'Offres',
  'saisie': 'Saisie',
  'settings': 'Paramètres',
  'social-networks': 'Réseaux Sociaux',
  'stripe-integration': 'Intégration Stripe',
  'tenants': 'Multi-Tenants',
  'timesheet': 'Feuilles de Temps',
  'triggers': 'Déclencheurs',
  'vehicles': 'Véhicules',
  'warranty': 'Garanties',
  'website': 'Site Web Builder',
  'worksheet': 'Fiches de Travail',
};

// Icônes pour les modules
const MODULE_ICONS: Record<string, string> = {
  'ai-assistant': 'marceau',
  'affaires': 'projects',
  'assets': 'inventory',
  'audit': 'compliance',
  'autoconfig': 'settings',
  'automated-accounting': 'accounting',
  'backup': 'settings',
  'break-glass': 'admin',
  'broadcast': 'mobile',
  'commandes': 'purchases',
  'commercial': 'users',
  'complaints': 'helpdesk',
  'comptabilite': 'accounting',
  'consolidation': 'accounting',
  'contracts': 'invoicing',
  'country-packs': 'download',
  'country-packs-france': 'download',
  'crm': 'contacts',
  'devis': 'invoicing',
  'email': 'mobile',
  'enrichment': 'contacts',
  'esignature': 'invoicing',
  'expenses': 'treasury',
  'factures': 'invoicing',
  'field-service': 'interventions',
  'finance': 'treasury',
  'guardian': 'admin',
  'hr-vault': 'hr',
  'i18n': 'settings',
  'iam': 'admin',
  'import': 'download',
  'import-gateways': 'download',
  'odoo-import': 'download',
  'ordres-service': 'interventions',
  'procurement': 'purchases',
  'profile': 'users',
  'qc': 'quality',
  'qualite': 'quality',
  'rfq': 'purchases',
  'saisie': 'invoicing',
  'settings': 'settings',
  'social-networks': 'mobile',
  'stripe-integration': 'payments',
  'tenants': 'settings',
  'timesheet': 'projects',
  'triggers': 'settings',
  'vehicles': 'maintenance',
  'warranty': 'maintenance',
  'website': 'web',
  'worksheet': 'projects',
};

// ============================================================
// HELPERS
// ============================================================

function toPascalCase(str: string): string {
  return str
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
}

function toSnakeCase(str: string): string {
  return str.replace(/-/g, '_');
}

function getModuleLabel(moduleName: string): string {
  let label = MODULE_LABELS[moduleName];
  if (!label) {
    // Convertir kebab-case en Title Case
    label = moduleName
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  // Échapper les apostrophes pour éviter les erreurs de syntaxe
  return label.replace(/'/g, "\\'");
}

function getModuleIcon(moduleName: string): string {
  return MODULE_ICONS[moduleName] || 'settings';
}

function getModuleSection(moduleName: string): string {
  return MODULE_SECTION_MAP[moduleName] || 'admin';
}

function getCapability(moduleName: string): string {
  return `${toSnakeCase(moduleName)}.view`;
}

// ============================================================
// SCAN MODULES
// ============================================================

function getExistingModules(): string[] {
  const entries = fs.readdirSync(MODULES_DIR, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => !IGNORED_MODULES.includes(name))
    .sort();
}

function getRegisteredModulesInRouting(): Set<string> {
  const content = fs.readFileSync(ROUTING_FILE, 'utf-8');
  const registered = new Set<string>();

  // Chercher les imports lazy: import('@modules/xxx')
  const importRegex = /import\('@modules\/([^']+)'\)/g;
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    registered.add(match[1]);
  }

  return registered;
}

function getRegisteredModulesInMenu(): Set<string> {
  const content = fs.readFileSync(MENU_FILE, 'utf-8');
  const registered = new Set<string>();

  // Chercher les paths: path: '/xxx'
  const pathRegex = /path:\s*'\/([^/']+)'/g;
  let match;
  while ((match = pathRegex.exec(content)) !== null) {
    registered.add(match[1]);
  }

  return registered;
}

// ============================================================
// UPDATE ROUTING
// ============================================================

function updateRouting(missingModules: string[], dryRun: boolean): void {
  if (missingModules.length === 0) {
    console.log('   ✅ Toutes les routes sont déjà enregistrées');
    return;
  }

  let content = fs.readFileSync(ROUTING_FILE, 'utf-8');

  // Générer les imports lazy
  const lazyImports = missingModules.map((mod) => {
    const pascalName = toPascalCase(mod);
    return `const ${pascalName}Routes = lazy(() => import('@modules/${mod}'));`;
  }).join('\n');

  // Générer les routes
  const routes = missingModules.map((mod) => {
    const pascalName = toPascalCase(mod);
    const capability = getCapability(mod);
    return `
            {/* ${getModuleLabel(mod)} */}
            <Route path="/${mod}/*" element={
              <CapabilityRoute capability="${capability}">
                <${pascalName}Routes />
              </CapabilityRoute>
            } />`;
  }).join('\n');

  // Insérer les imports après le dernier import lazy existant
  const lastLazyImportMatch = content.match(/const \w+Routes = lazy\(\(\) => import\('@modules\/[^']+'\)\);/g);
  if (lastLazyImportMatch) {
    const lastImport = lastLazyImportMatch[lastLazyImportMatch.length - 1];
    const insertPos = content.indexOf(lastImport) + lastImport.length;
    content = content.slice(0, insertPos) + '\n' + lazyImports + content.slice(insertPos);
  }

  // Insérer les routes avant {/* Profil et Paramètres */}
  const profileRouteMarker = '{/* Profil et Paramètres */}';
  const profilePos = content.indexOf(profileRouteMarker);
  if (profilePos !== -1) {
    content = content.slice(0, profilePos) + routes + '\n\n            ' + content.slice(profilePos);
  }

  if (dryRun) {
    console.log('   [DRY-RUN] Routes à ajouter:');
    missingModules.forEach((mod) => console.log(`      - ${mod}`));
  } else {
    fs.writeFileSync(ROUTING_FILE, content);
    console.log(`   ✅ ${missingModules.length} route(s) ajoutée(s)`);
  }
}

// ============================================================
// UPDATE MENU
// ============================================================

function updateMenu(missingModules: string[], dryRun: boolean): void {
  if (missingModules.length === 0) {
    console.log('   ✅ Tous les menus sont déjà enregistrés');
    return;
  }

  let content = fs.readFileSync(MENU_FILE, 'utf-8');

  // Grouper les modules par section
  const modulesBySection: Record<string, string[]> = {};
  for (const mod of missingModules) {
    const section = getModuleSection(mod);
    if (!modulesBySection[section]) {
      modulesBySection[section] = [];
    }
    modulesBySection[section].push(mod);
  }

  // Section ID to title mapping
  const sectionTitles: Record<string, string> = {
    'main': 'Principal',
    'gestion': 'Gestion',
    'finance': 'Finance',
    'logistique': 'Logistique & Production',
    'operations': 'Opérations',
    'ventes': 'Ventes & Commerce',
    'digital': 'Digital & Reporting',
    'import': 'Import de Données',
    'admin': 'Administration',
  };

  // Pour chaque section, ajouter les modules manquants
  for (const [sectionId, modules] of Object.entries(modulesBySection)) {
    const sectionTitle = sectionTitles[sectionId];
    if (!sectionTitle) continue;

    // Trouver la section dans le fichier
    const sectionPattern = `title: '${sectionTitle}'`;
    const sectionPos = content.indexOf(sectionPattern);

    if (sectionPos === -1) continue;

    // Trouver la fin de la section (prochain "items: [" ou fin du tableau)
    const itemsStart = content.indexOf('items: [', sectionPos);
    if (itemsStart === -1) continue;

    // Trouver le premier item existant ou la fin du tableau
    const itemsEnd = content.indexOf('],', itemsStart);
    if (itemsEnd === -1) continue;

    // Générer les nouvelles entrées de menu
    const menuEntries = modules.map((mod) => {
      const label = getModuleLabel(mod);
      const icon = getModuleIcon(mod);
      const capability = getCapability(mod);
      return `      {
        id: '${mod}',
        label: '${label}',
        icon: '${icon}',
        path: '/${mod}',
        capability: '${capability}',
      },`;
    }).join('\n');

    // Insérer avant la fermeture du tableau items
    content = content.slice(0, itemsEnd) + '\n' + menuEntries + '\n    ' + content.slice(itemsEnd);
  }

  if (dryRun) {
    console.log('   [DRY-RUN] Menus à ajouter:');
    for (const [section, modules] of Object.entries(modulesBySection)) {
      console.log(`      Section ${section}:`);
      modules.forEach((mod) => console.log(`         - ${mod}`));
    }
  } else {
    fs.writeFileSync(MENU_FILE, content);
    console.log(`   ✅ ${missingModules.length} entrée(s) de menu ajoutée(s)`);
  }
}

// ============================================================
// MAIN
// ============================================================

function main() {
  const dryRun = process.argv.includes('--dry-run');

  console.log('🔧 Enregistrement automatique des modules frontend');
  console.log('');

  if (dryRun) {
    console.log('⚠️  Mode DRY-RUN: aucune modification ne sera effectuée');
    console.log('');
  }

  // 1. Scanner les modules existants
  const existingModules = getExistingModules();
  console.log(`📁 Modules trouvés: ${existingModules.length}`);

  // 2. Vérifier les routes
  console.log('');
  console.log('📍 Vérification des routes...');
  const registeredRoutes = getRegisteredModulesInRouting();
  const missingRoutes = existingModules.filter((mod) => !registeredRoutes.has(mod));
  console.log(`   Enregistrés: ${registeredRoutes.size}`);
  console.log(`   Manquants: ${missingRoutes.length}`);

  if (missingRoutes.length > 0) {
    console.log('   Modules sans route:', missingRoutes.join(', '));
  }

  // 3. Vérifier les menus
  console.log('');
  console.log('📋 Vérification des menus...');
  const registeredMenus = getRegisteredModulesInMenu();
  const missingMenus = existingModules.filter((mod) => !registeredMenus.has(mod));
  console.log(`   Enregistrés: ${registeredMenus.size}`);
  console.log(`   Manquants: ${missingMenus.length}`);

  if (missingMenus.length > 0) {
    console.log('   Modules sans menu:', missingMenus.join(', '));
  }

  // 4. Appliquer les modifications
  console.log('');
  console.log('🔧 Application des modifications...');
  console.log('');
  console.log('   Routes:');
  updateRouting(missingRoutes, dryRun);

  console.log('');
  console.log('   Menus:');
  updateMenu(missingMenus, dryRun);

  // 5. Résumé
  console.log('');
  console.log('════════════════════════════════════════════════════════════');
  console.log('📊 Résumé:');
  console.log(`   Routes ajoutées: ${dryRun ? '(dry-run) ' : ''}${missingRoutes.length}`);
  console.log(`   Menus ajoutés: ${dryRun ? '(dry-run) ' : ''}${missingMenus.length}`);
  console.log('');

  if (!dryRun && (missingRoutes.length > 0 || missingMenus.length > 0)) {
    console.log('✅ Enregistrement terminé!');
    console.log('');
    console.log('📖 Prochaines étapes:');
    console.log('   1. Vérifier les modifications: git diff');
    console.log('   2. Tester le build: npm run build');
    console.log('   3. Vérifier l\'application: npm run dev');
  } else if (dryRun) {
    console.log('💡 Exécuter sans --dry-run pour appliquer les modifications');
  } else {
    console.log('✅ Tous les modules sont déjà enregistrés!');
  }
}

main();
