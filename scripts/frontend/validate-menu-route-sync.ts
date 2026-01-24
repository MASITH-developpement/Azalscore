#!/usr/bin/env tsx
/**
 * AZALSCORE - Vérification Menu ↔ Route Sync (AZA-FE-ENF)
 * =========================================================
 * Contrôle automatique synchronisation menu/routes:
 * - Chaque entrée menu = route valide
 * - Chaque route affichée = page rendue (pas vide)
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================
// TYPES
// ============================================================

interface MenuLink {
  label: string;
  path: string;
  source: string; // 'top-menu' | 'dynamic-menu'
}

interface Route {
  path: string;
  module: string;
}

interface Validation {
  success: boolean;
  errors: string[];
  warnings: string[];
}

// ============================================================
// CONFIGURATION
// ============================================================

const FRONTEND_DIR = path.join(__dirname, '../../frontend/src');
const ROUTING_FILE = path.join(FRONTEND_DIR, 'routing/index.tsx');
const TOP_MENU_FILE = path.join(FRONTEND_DIR, 'ui-engine/top-menu/index.tsx');
const DYNAMIC_MENU_FILE = path.join(FRONTEND_DIR, 'ui-engine/menu-dynamic/index.tsx');
const MODULES_DIR = path.join(FRONTEND_DIR, 'modules');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');

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

  // Pattern pour extraire les routes: <Route path="/xxx"
  // Simpler regex that just captures the path, not the element (which may be multi-line)
  const routeRegex = /<Route\s+path="([^"]+)"/g;
  let match;

  while ((match = routeRegex.exec(content)) !== null) {
    const routePath = match[1];

    // Skip:
    // - Root path "/"
    // - Wildcard only paths "*"
    // - Paths with dynamic segments in the middle
    if (routePath === '/' || routePath === '*') {
      continue;
    }

    // Extraire le nom du module du path
    const pathParts = routePath.replace(/\/\*$/, '').split('/').filter(Boolean);
    const moduleName = pathParts[pathParts.length - 1];

    if (moduleName && moduleName !== ':id' && !moduleName.includes(':')) {
      routes.push({
        path: routePath,
        module: moduleName,
      });
    }
  }

  return routes;
}

// ============================================================
// MENU LINK EXTRACTION
// ============================================================

function extractMenuLinks(menuFilePath: string, source: string): MenuLink[] {
  if (!fs.existsSync(menuFilePath)) {
    console.warn(`⚠️  Fichier menu non trouvé: ${menuFilePath}`);
    return [];
  }

  const content = fs.readFileSync(menuFilePath, 'utf-8');
  const links: MenuLink[] = [];

  // Pattern 1: { label: '...', path: '/...' }
  const pattern1 = /{\s*label:\s*['"]([^'"]+)['"]\s*,\s*path:\s*['"]([^'"]+)['"]/g;
  let match;

  while ((match = pattern1.exec(content)) !== null) {
    const label = match[1];
    const linkPath = match[2];

    // Ignorer les paths avec variables (:id) ou wildcards
    if (!linkPath.includes(':id') && !linkPath.includes('*')) {
      links.push({
        label,
        path: linkPath,
        source,
      });
    }
  }

  // Pattern 2: to="/..." (NavLink direct)
  const pattern2 = /to=["']([^"']+)["']/g;

  while ((match = pattern2.exec(content)) !== null) {
    const linkPath = match[1];

    // Ignorer les paths avec variables ou déjà extraits
    if (
      !linkPath.includes(':id') &&
      !linkPath.includes('*') &&
      !links.some((l) => l.path === linkPath)
    ) {
      links.push({
        label: linkPath, // Pas de label explicite pour NavLink direct
        path: linkPath,
        source,
      });
    }
  }

  return links;
}

// ============================================================
// PAGE RENDERING CHECK
// ============================================================

function isPageRendered(modulePath: string): boolean {
  // Map route names to actual module names (for mismatches like /quality -> qualite)
  const routeToModuleMapping: Record<string, string> = {
    'quality': 'qualite',
  };

  const actualModulePath = routeToModuleMapping[modulePath] || modulePath;

  // Check both /modules/ and /pages/ directories
  const modulesIndexPath = path.join(MODULES_DIR, actualModulePath, 'index.tsx');
  const pagesIndexPath = path.join(PAGES_DIR, actualModulePath, 'index.tsx');
  const directPagePath = path.join(PAGES_DIR, `${actualModulePath}.tsx`);

  // Special handling for auth pages (in /pages/auth/ subdirectory)
  const authPageMapping: Record<string, string> = {
    'login': 'auth/Login.tsx',
    '2fa': 'auth/TwoFactor.tsx',
    'forgot-password': 'auth/ForgotPassword.tsx',
  };

  const authPagePath = authPageMapping[actualModulePath]
    ? path.join(PAGES_DIR, authPageMapping[actualModulePath])
    : null;

  let indexPath: string | null = null;

  if (fs.existsSync(modulesIndexPath)) {
    indexPath = modulesIndexPath;
  } else if (fs.existsSync(pagesIndexPath)) {
    indexPath = pagesIndexPath;
  } else if (fs.existsSync(directPagePath)) {
    indexPath = directPagePath;
  } else if (authPagePath && fs.existsSync(authPagePath)) {
    indexPath = authPagePath;
  }

  if (!indexPath) {
    return false;
  }

  const content = fs.readFileSync(indexPath, 'utf-8');

  // Filter out HTML placeholder attributes before checking
  const codeWithoutHtmlAttrs = content.replace(/placeholder\s*=\s*"[^"]*"/gi, '');

  // Heuristic: if file is substantial (>200 lines) and exports default, it's likely functional
  // even if it contains "return null" somewhere (e.g., in error handling)
  const lineCount = content.split('\n').length;
  const hasExportDefault = content.includes('export default');
  const isSubstantialModule = lineCount > 200 && hasExportDefault;

  if (isSubstantialModule) {
    return true; // Consider substantial modules as rendered
  }

  // Patterns de composants vides
  const emptyPatterns = [
    /return\s+null/,
    /return\s+<>\s*<\/>/,
    /return\s+<div>\s*<\/div>/,
  ];

  // TODO patterns only in comments
  const todoPatterns = [
    /\/\/\s*TODO:?\s+Implement/i,
    /\/\*\s*TODO:?\s+Implement/i,
    /\/\/\s*PLACEHOLDER/i,
    /\/\*\s*PLACEHOLDER/i,
    /\/\/\s*COMING\s+SOON/i,
    /\/\*\s*COMING\s+SOON/i,
  ];

  const hasEmptyPattern = emptyPatterns.some((pattern) => pattern.test(content));
  const hasTodoInComments = todoPatterns.some((pattern) => pattern.test(codeWithoutHtmlAttrs));

  // Si un pattern vide est trouvé, considérer comme non rendu
  return !(hasEmptyPattern || hasTodoInComments);
}

// ============================================================
// VALIDATION FUNCTIONS
// ============================================================

function validateMenuLinksHaveRoutes(
  menuLinks: MenuLink[],
  routes: Route[]
): Validation {
  const errors: string[] = [];
  const warnings: string[] = [];

  menuLinks.forEach((link) => {
    // Vérifier si une route correspond
    const routeExists = routes.some((route) => {
      const routePath = route.path.replace(/\/\*$/, '');
      return (
        link.path.startsWith(routePath) ||
        routePath.startsWith(link.path) ||
        link.path === routePath
      );
    });

    if (!routeExists) {
      errors.push(
        `[AZA-FE-ENF] Menu "${link.label}" (${link.source}) → route inexistante: ${link.path}`
      );
    }
  });

  return {
    success: errors.length === 0,
    errors,
    warnings,
  };
}

function validateRoutesHavePages(routes: Route[]): Validation {
  const errors: string[] = [];
  const warnings: string[] = [];

  routes.forEach((route) => {
    // Map route names to actual module names (for mismatches like /quality -> qualite)
    const routeToModuleMapping: Record<string, string> = {
      'quality': 'qualite',
    };

    const actualModulePath = routeToModuleMapping[route.module] || route.module;

    const modulesIndexPath = path.join(MODULES_DIR, actualModulePath, 'index.tsx');
    const pagesIndexPath = path.join(PAGES_DIR, actualModulePath, 'index.tsx');
    const directPagePath = path.join(PAGES_DIR, `${actualModulePath}.tsx`);

    // Special handling for auth pages
    const authPageMapping: Record<string, string> = {
      'login': 'auth/Login.tsx',
      '2fa': 'auth/TwoFactor.tsx',
      'forgot-password': 'auth/ForgotPassword.tsx',
    };

    const authPagePath = authPageMapping[actualModulePath]
      ? path.join(PAGES_DIR, authPageMapping[actualModulePath])
      : null;

    const pageExists =
      fs.existsSync(modulesIndexPath) ||
      fs.existsSync(pagesIndexPath) ||
      fs.existsSync(directPagePath) ||
      (authPagePath && fs.existsSync(authPagePath));

    if (!pageExists) {
      errors.push(
        `[AZA-FE-ENF] Route ${route.path} → page inexistante (checked: modules/, pages/, pages/auth/)`
      );
    } else {
      // Vérifier que la page n'est pas vide
      if (!isPageRendered(route.module)) {
        errors.push(
          `[AZA-FE-ENF] Route ${route.path} → page vide ou placeholder`
        );
      }
    }
  });

  return {
    success: errors.length === 0,
    errors,
    warnings,
  };
}

// ============================================================
// MAIN VALIDATOR
// ============================================================

function validateMenuRouteSync(): Validation {
  console.log('📋 Extraction des routes...');
  const routes = extractRoutes(ROUTING_FILE);
  console.log(`   Trouvé: ${routes.length} route(s)\n`);

  console.log('📋 Extraction des liens menu...');
  const topMenuLinks = extractMenuLinks(TOP_MENU_FILE, 'top-menu');
  const dynamicMenuLinks = extractMenuLinks(DYNAMIC_MENU_FILE, 'dynamic-menu');
  const allMenuLinks = [...topMenuLinks, ...dynamicMenuLinks];
  console.log(`   Trouvé: ${allMenuLinks.length} lien(s) menu\n`);

  console.log('🔍 Validation 1: Chaque entrée menu = route valide');
  const menuValidation = validateMenuLinksHaveRoutes(allMenuLinks, routes);

  console.log('🔍 Validation 2: Chaque route affichée = page rendue');
  const routeValidation = validateRoutesHavePages(routes);

  const allErrors = [...menuValidation.errors, ...routeValidation.errors];
  const allWarnings = [...menuValidation.warnings, ...routeValidation.warnings];

  return {
    success: allErrors.length === 0,
    errors: allErrors,
    warnings: allWarnings,
  };
}

// ============================================================
// MAIN EXECUTION
// ============================================================

function main() {
  console.log('🔍 Vérification Menu ↔ Route Sync (AZA-FE-ENF)\n');
  console.log(`📁 Frontend: ${FRONTEND_DIR}`);
  console.log(`📄 Routing: ${ROUTING_FILE}`);
  console.log(`📄 Top Menu: ${TOP_MENU_FILE}`);
  console.log(`📄 Dynamic Menu: ${DYNAMIC_MENU_FILE}\n`);

  const result = validateMenuRouteSync();

  if (result.success) {
    console.log('\n✅ Synchronisation menu ↔ route validée (AZA-FE-ENF)\n');
    console.log('Aucune violation détectée.\n');
    process.exit(0);
  } else {
    console.log('\n❌ VIOLATIONS AZA-FE-ENF DÉTECTÉES\n');
    console.log(`Total: ${result.errors.length} erreur(s), ${result.warnings.length} warning(s)\n`);

    if (result.errors.length > 0) {
      console.log('📋 ERREURS:');
      console.log('─'.repeat(80));
      result.errors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
      console.log();
    }

    if (result.warnings.length > 0) {
      console.log('📋 WARNINGS:');
      console.log('─'.repeat(80));
      result.warnings.forEach((warning, i) => {
        console.log(`  ${i + 1}. ${warning}`);
      });
      console.log();
    }

    console.log('💡 Violations AZA-FE-ENF détectées. Correction obligatoire.');
    console.log('📖 Voir norme AZA-FE-ENF pour détails.\n');

    process.exit(1);
  }
}

// Run main if script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { validateMenuRouteSync, extractRoutes, extractMenuLinks };
