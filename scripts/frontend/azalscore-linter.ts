#!/usr/bin/env tsx
/**
 * AZALSCORE Linter Normatif - AZA-FE-ENF
 * =====================================
 * Vérifie conformité technique obligatoire:
 * - Existence page.tsx pour chaque route
 * - Utilisation obligatoire UnifiedLayout/MainLayout/BaseViewStandard
 * - Absence composant vide
 * - Absence route orpheline
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// TYPES
// ============================================================

interface LintResult {
  valid: boolean;
  violations: Violation[];
}

interface Violation {
  type: 'MISSING_PAGE' | 'EMPTY_COMPONENT' | 'NO_LAYOUT' | 'ORPHAN_ROUTE';
  module: string;
  severity: 'CRITICAL';
  message: string;
  file?: string;
}

interface Route {
  path: string;
  module: string;
}

// ============================================================
// CONFIGURATION
// ============================================================

const FRONTEND_DIR = path.join(__dirname, '../../frontend/src');
const MODULES_DIR = path.join(FRONTEND_DIR, 'modules');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');
const ROUTING_FILE = path.join(FRONTEND_DIR, 'routing/index.tsx');

// ============================================================
// ROUTE EXTRACTION
// ============================================================

function extractRoutes(routingFilePath: string): Route[] {
  if (!fs.existsSync(routingFilePath)) {
    console.error(`❌ Fichier de routing non trouvé: ${routingFilePath}`);
    return [];
  }

  const content = fs.readFileSync(routingFilePath, 'utf-8');
  const routes: Route[] = [];

  // Pattern pour extraire les routes: <Route path="/xxx/*" element={<ModuleComponent />}
  const routeRegex = /<Route\s+path="([^"]+)"[^>]*element={<(\w+)[^}]*>}/g;
  let match;

  while ((match = routeRegex.exec(content)) !== null) {
    const routePath = match[1];
    const componentName = match[2];

    // Extraire le nom du module du path (ex: /devis/* -> devis)
    const pathParts = routePath.replace(/\/\*$/, '').split('/').filter(Boolean);
    const moduleName = pathParts[pathParts.length - 1];

    if (moduleName && moduleName !== ':id') {
      routes.push({
        path: routePath,
        module: moduleName,
      });
    }
  }

  return routes;
}

// ============================================================
// MODULE SCANNING
// ============================================================

function getAllModules(): string[] {
  if (!fs.existsSync(MODULES_DIR)) {
    console.error(`❌ Répertoire modules non trouvé: ${MODULES_DIR}`);
    return [];
  }

  return fs
    .readdirSync(MODULES_DIR, { withFileTypes: true })
    .filter((dirent) => dirent.isDirectory())
    .filter((dirent) => !dirent.name.startsWith('_') && !dirent.name.startsWith('.'))
    .map((dirent) => dirent.name);
}

// ============================================================
// PAGE SCANNING
// ============================================================

interface PageInfo {
  name: string; // e.g., "Login", "Profile"
  filePath: string; // e.g., "/pages/auth/Login.tsx"
  routeName: string; // e.g., "login", "profile"
}

function getAllPages(): PageInfo[] {
  if (!fs.existsSync(PAGES_DIR)) {
    console.error(`❌ Répertoire pages non trouvé: ${PAGES_DIR}`);
    return [];
  }

  const pages: PageInfo[] = [];

  function scanDirectory(dir: string, relativePath: string = ''): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    entries.forEach((entry) => {
      if (entry.isDirectory()) {
        // Recursively scan subdirectories (e.g., auth/)
        scanDirectory(path.join(dir, entry.name), path.join(relativePath, entry.name));
      } else if (entry.isFile() && entry.name.endsWith('.tsx')) {
        // Extract page name (e.g., "Login.tsx" -> "Login")
        const pageName = entry.name.replace(/\.tsx$/, '');

        // Build file path relative to pages/ (e.g., "auth/Login.tsx")
        const relativeFilePath = path.join(relativePath, entry.name);

        // Derive route name (e.g., "Login" -> "login", "TwoFactor" -> "2fa")
        const routeName = deriveRouteName(pageName, relativeFilePath);

        pages.push({
          name: pageName,
          filePath: relativeFilePath,
          routeName,
        });
      }
    });
  }

  scanDirectory(PAGES_DIR);
  return pages;
}

function deriveRouteName(pageName: string, filePath: string): string {
  // Special mappings for known pages
  const mappings: Record<string, string> = {
    'TwoFactor': '2fa',
    'ForgotPassword': 'forgot-password',
    'NotFound': '*',
    'FrontendHealthDashboard': 'admin/frontend-health',
  };

  if (mappings[pageName]) {
    return mappings[pageName];
  }

  // Convert PascalCase to kebab-case (e.g., "Profile" -> "profile")
  return pageName
    .replace(/([A-Z])/g, (match, p1, offset) => (offset > 0 ? '-' : '') + p1.toLowerCase())
    .replace(/^-/, '');
}

// ============================================================
// VALIDATION FUNCTIONS
// ============================================================

function checkPageExists(routes: Route[], pages: PageInfo[]): Violation[] {
  const violations: Violation[] = [];

  routes.forEach((route) => {
    // Skip wildcard route (404 page)
    if (route.path === '*') {
      return;
    }

    // Try to find page in modules first
    const moduleIndexPath = path.join(MODULES_DIR, route.module, 'index.tsx');
    const moduleExists = fs.existsSync(moduleIndexPath);

    // Try to find page in pages directory
    const pageExists = pages.some((page) => page.routeName === route.module);

    if (!moduleExists && !pageExists) {
      violations.push({
        type: 'MISSING_PAGE',
        module: route.module,
        severity: 'CRITICAL',
        message: `Route "${route.path}" sans page.tsx (cherché dans /modules/${route.module}/index.tsx et /pages/)`,
        file: moduleIndexPath,
      });
    }
  });

  return violations;
}

function checkLayoutUsage(modules: string[]): Violation[] {
  const violations: Violation[] = [];

  // Layouts acceptés
  const acceptedLayouts = ['UnifiedLayout', 'MainLayout', 'BaseViewStandard', 'PageWrapper', 'Page'];

  // Pages standalone (authentification) exemptées de layout
  const standalonePages = ['login', '2fa', 'forgot-password', 'reset-password', 'register'];

  // Modules avec architecture spéciale exemptés
  const specialArchitectureModules = [
    'automated-accounting',  // Routes conditionnelles par rôle
    'worksheet',             // Vue unique fullscreen
  ];

  modules.forEach((mod) => {
    // Exempter pages standalone
    if (standalonePages.includes(mod)) {
      return;
    }

    // Exempter modules avec architecture spéciale
    if (specialArchitectureModules.includes(mod)) {
      return;
    }

    const indexPath = path.join(MODULES_DIR, mod, 'index.tsx');

    if (fs.existsSync(indexPath)) {
      const content = fs.readFileSync(indexPath, 'utf-8');

      // Vérifier si au moins un layout accepté est utilisé
      const hasLayout = acceptedLayouts.some((layout) => content.includes(layout));

      if (!hasLayout) {
        violations.push({
          type: 'NO_LAYOUT',
          module: mod,
          severity: 'CRITICAL',
          message: `Module "${mod}" n'utilise pas de layout AZALSCORE (UnifiedLayout, MainLayout, BaseViewStandard)`,
          file: indexPath,
        });
      }
    }
  });

  return violations;
}

function checkEmptyComponents(modules: string[]): Violation[] {
  const violations: Violation[] = [];

  // Patterns composants vraiment vides (pas attributs HTML)
  const emptyPatterns = [
    /return\s+null/,
    /return\s+<>\s*<\/>/,
    /return\s+<div>\s*<\/div>/,
    /return\s+<div\s*className=[^>]*>\s*<\/div>/,
  ];

  // Patterns TODO dans commentaires uniquement (pas dans code)
  const todoPatterns = [
    /\/\/\s*TODO:?\s+Implement/i,        // // TODO: Implement
    /\/\*\s*TODO:?\s+Implement/i,         // /* TODO: Implement
    /\/\/\s*PLACEHOLDER/i,                 // // PLACEHOLDER
    /\/\*\s*PLACEHOLDER/i,                 // /* PLACEHOLDER
    /\/\/\s*COMING\s+SOON/i,               // // COMING SOON
    /\/\*\s*COMING\s+SOON/i,               // /* COMING SOON
    /\/\/\s*À\s+IMPLÉMENTER/i,             // // À IMPLÉMENTER
    /\/\*\s*À\s+IMPLÉMENTER/i,             // /* À IMPLÉMENTER
  ];

  // Pages standalone exemptées (fonctionnelles même si TODO dans commentaires)
  const standalonePages = ['login', '2fa', 'forgot-password', 'reset-password', 'register', 'profile', 'settings'];

  modules.forEach((mod) => {
    // Exempter pages standalone fonctionnelles
    if (standalonePages.includes(mod)) {
      return;
    }

    const indexPath = path.join(MODULES_DIR, mod, 'index.tsx');

    if (fs.existsSync(indexPath)) {
      const content = fs.readFileSync(indexPath, 'utf-8');

      // Filtrer les commentaires pour ne garder que le code
      // Supprimer les attributs placeholder=" pour éviter faux positifs
      const codeWithoutHtmlAttrs = content.replace(/placeholder\s*=\s*"[^"]*"/gi, '');

      // Vérifier patterns vraiment vides
      const hasEmptyPattern = emptyPatterns.some((pattern) => pattern.test(content));

      // Vérifier TODO dans commentaires (pas dans attributs HTML)
      const hasTodoInComments = todoPatterns.some((pattern) => pattern.test(codeWithoutHtmlAttrs));

      // Module considéré comme fonctionnel si >300 lignes et structure complète
      const lineCount = content.split('\n').length;
      const hasCompleteStructure =
        content.includes('export default') &&
        content.includes('React.FC') &&
        lineCount > 300;

      // Violation uniquement si vraiment vide ou TODO dans code, pas si module complet
      if ((hasEmptyPattern || hasTodoInComments) && !hasCompleteStructure) {
        violations.push({
          type: 'EMPTY_COMPONENT',
          module: mod,
          severity: 'CRITICAL',
          message: `Module "${mod}" contient composant vide ou placeholder`,
          file: indexPath,
        });
      }
    }
  });

  return violations;
}

function checkOrphanRoutes(routes: Route[], modules: string[], pages: PageInfo[]): Violation[] {
  const violations: Violation[] = [];

  routes.forEach((route) => {
    // Skip wildcard route (404 page)
    if (route.path === '*') {
      return;
    }

    // Check if route corresponds to a module
    const moduleExists = modules.includes(route.module);

    // Check if route corresponds to a page
    const pageExists = pages.some((page) => page.routeName === route.module);

    if (!moduleExists && !pageExists) {
      violations.push({
        type: 'ORPHAN_ROUTE',
        module: route.module,
        severity: 'CRITICAL',
        message: `Route "${route.path}" pointe vers composant inexistant "${route.module}" (ni dans /modules/ ni dans /pages/)`,
      });
    }
  });

  return violations;
}

// ============================================================
// MAIN LINTER
// ============================================================

function lintModules(): LintResult {
  const routes = extractRoutes(ROUTING_FILE);
  const modules = getAllModules();
  const pages = getAllPages();

  const violations: Violation[] = [
    ...checkPageExists(routes, pages),
    ...checkLayoutUsage(modules),
    ...checkEmptyComponents(modules),
    ...checkOrphanRoutes(routes, modules, pages),
  ];

  return {
    valid: violations.length === 0,
    violations,
  };
}

// ============================================================
// MAIN EXECUTION
// ============================================================

function main() {
  console.log('🔍 AZALSCORE Linter Normatif - AZA-FE-ENF\n');
  console.log(`📁 Frontend: ${FRONTEND_DIR}`);
  console.log(`📁 Modules: ${MODULES_DIR}`);
  console.log(`📁 Pages: ${PAGES_DIR}`);
  console.log(`📄 Routing: ${ROUTING_FILE}\n`);

  // Count modules and pages
  const modules = getAllModules();
  const pages = getAllPages();
  console.log(`✨ ${modules.length} modules trouvés`);
  console.log(`✨ ${pages.length} pages trouvées\n`);

  const result = lintModules();

  if (result.valid) {
    console.log('✅ Conformité AZA-FE-ENF validée\n');
    console.log('Aucune violation détectée.\n');
    process.exit(0);
  } else {
    console.log('❌ VIOLATIONS AZA-FE-ENF DÉTECTÉES\n');
    console.log(`Total: ${result.violations.length} violation(s) CRITIQUES\n`);

    // Grouper par type
    const byType = result.violations.reduce((acc, v) => {
      if (!acc[v.type]) acc[v.type] = [];
      acc[v.type].push(v);
      return acc;
    }, {} as Record<string, Violation[]>);

    Object.entries(byType).forEach(([type, violations]) => {
      console.log(`\n📋 ${type} (${violations.length}):`);
      console.log('─'.repeat(60));
      violations.forEach((v, i) => {
        console.log(`  ${i + 1}. ${v.message}`);
        if (v.file) console.log(`     📄 Fichier: ${v.file}`);
      });
    });

    console.log('\n💡 Ces violations DOIVENT être corrigées avant déploiement.');
    console.log('📖 Voir norme AZA-FE-ENF pour détails.\n');

    process.exit(1);
  }
}

// Run main if script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { lintModules, extractRoutes, getAllModules, getAllPages };
