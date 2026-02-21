#!/usr/bin/env node
/**
 * AZALSCORE - Générateur automatique de menu
 * ==========================================
 *
 * Génère automatiquement ViewKey et MENU_ITEMS dans UnifiedLayout.tsx
 * depuis les modules découverts dans le backend.
 *
 * Usage: node scripts/frontend/generate-menu.js
 */

const fs = require('fs');
const path = require('path');

// Configuration des groupes de menu par catégorie de module
const MODULE_GROUP_MAP = {
  // Gestion (modules de facturation/interventions déjà gérés manuellement)
  'invoicing': '_skip',
  'devis': '_skip',
  'commandes': '_skip',
  'factures': '_skip',
  'interventions': '_skip',
  'payments': '_skip',

  // Modules métier
  'partners': 'Modules',
  'crm': 'Modules',
  'contacts': 'Modules',
  'inventory': 'Modules',
  'purchases': 'Modules',
  'projects': 'Modules',
  'hr': 'Modules',
  'contracts': 'Modules',
  'timesheet': 'Modules',
  'field-service': 'Modules',
  'rfq': 'Modules',
  'complaints': 'Modules',
  'warranty': 'Modules',
  'procurement': 'Modules',

  // Logistique
  'production': 'Logistique',
  'maintenance': 'Logistique',
  'quality': 'Logistique',
  'qc': 'Logistique',

  // Commerce
  'pos': 'Commerce',
  'ecommerce': 'Commerce',
  'marketplace': 'Commerce',
  'subscriptions': 'Commerce',
  'commercial': 'Commerce',

  // Services
  'helpdesk': 'Services',

  // Digital
  'web': 'Digital',
  'website': 'Digital',
  'bi': 'Digital',
  'compliance': 'Digital',
  'social-networks': 'Digital',
  'broadcast': 'Digital',

  // Finance
  'accounting': 'Finance',
  'treasury': 'Finance',
  'finance': 'Finance',
  'assets': 'Finance',
  'consolidation': 'Finance',
  'expenses': 'Finance',
  'automated-accounting': 'Finance',

  // Direction
  'cockpit': 'Direction',
  'dashboards': 'Direction',
  'admin': 'Système',

  // IA
  'marceau': 'IA',
  'ai-assistant': 'IA',

  // Communication
  'email': 'Communication',
  'esignature': 'Communication',
  'notifications': 'Communication',

  // Système
  'admin': 'Système',
  'iam': 'Système',
  'tenants': 'Système',
  'audit': 'Système',
  'backup': 'Système',
  'guardian': 'Système',
  'autoconfig': 'Système',
  'triggers': 'Système',
  'workflows': 'Système',
  'country-packs': 'Système',
  'stripe-integration': 'Système',
  'hr-vault': 'Système',

  // Utilitaires (cachés)
  'cache': '_hidden',
  'currency': '_hidden',
  'dataexchange': '_hidden',
  'gateway': '_hidden',
  'i18n': '_hidden',
  'integrations': '_hidden',
  'scheduler': '_hidden',
  'search': '_hidden',
  'webhooks': '_hidden',
  'enrichment': '_hidden',
  'mobile': '_hidden',
};

// Labels personnalisés
const MODULE_LABELS = {
  'partners': 'CRM / Clients',
  'inventory': 'Stock',
  'purchases': 'Achats',
  'projects': 'Projets',
  'hr': 'Ressources Humaines',
  'accounting': 'Comptabilité',
  'treasury': 'Trésorerie',
  'pos': 'Point de Vente',
  'helpdesk': 'Support Client',
  'bi': 'Reporting & BI',
  'compliance': 'Conformité',
  'cockpit': 'Cockpit Dirigeant',
  'marceau': 'Marceau IA',
  'ai-assistant': 'Assistant IA',
  'admin': 'Administration',
  'iam': 'Gestion des Accès',
  'tenants': 'Multi-Tenants',
  'audit': 'Audit & Logs',
  'backup': 'Sauvegardes',
  'guardian': 'Sécurité',
  'triggers': 'Automatisations',
  'workflows': 'Workflows',
  'contracts': 'Contrats',
  'timesheet': 'Feuilles de Temps',
  'field-service': 'Service Terrain',
  'rfq': 'Appels d\'Offres',
  'complaints': 'Réclamations',
  'warranty': 'Garanties',
  'procurement': 'Approvisionnement',
  'qc': 'Contrôle Qualité',
  'commercial': 'Commercial',
  'website': 'Site Web Builder',
  'web': 'Site Web',
  'social-networks': 'Réseaux Sociaux',
  'broadcast': 'Diffusion',
  'assets': 'Immobilisations',
  'consolidation': 'Consolidation',
  'expenses': 'Notes de Frais',
  'automated-accounting': 'Comptabilité Auto',
  'email': 'Emails',
  'esignature': 'Signature Électronique',
  'notifications': 'Notifications',
  'autoconfig': 'Configuration Auto',
  'country-packs': 'Packs Pays',
  'stripe-integration': 'Intégration Stripe',
  'crm': 'CRM Avancé',
  'cockpit': 'Cockpit Dirigeant',
  'admin': 'Administration',
  'ecommerce': 'E-commerce',
  'marketplace': 'Marketplace',
  'subscriptions': 'Abonnements',
  'production': 'Production',
  'maintenance': 'Maintenance',
  'quality': 'Qualité',
  'finance': 'Finance',
  'hr-vault': 'Coffre-fort RH',
};

// Modules ignorés
const IGNORED_MODULES = new Set([
  'cache', 'currency', 'dataexchange', 'gateway', 'i18n',
  'integrations', 'scheduler', 'search', 'webhooks',
  'enrichment', 'mobile',
]);

function parseModulesRegistry() {
  const modulesFile = path.join(__dirname, '../../app/core/modules_registry.py');
  const content = fs.readFileSync(modulesFile, 'utf-8');

  const modules = [];

  // Parser MODULE_METADATA_OVERRIDES
  const overridesMatch = content.match(/MODULE_METADATA_OVERRIDES[^{]*\{([\s\S]*?)\n\}/);
  if (overridesMatch) {
    // Regex pour extraire chaque module
    const moduleRegex = /"([^"]+)":\s*\{[^}]*"name":\s*"([^"]+)"[^}]*"category":\s*"([^"]+)"/g;
    let match;
    while ((match = moduleRegex.exec(overridesMatch[1])) !== null) {
      const code = match[1].replace(/_/g, '-');
      modules.push({
        code: code,
        name: match[2],
        category: match[3],
      });
    }
  }

  return modules;
}

function generateViewKey(modules) {
  const viewKeys = new Set();

  // Modules statiques de base
  viewKeys.add("'saisie'");
  viewKeys.add("'gestion-devis'");
  viewKeys.add("'gestion-commandes'");
  viewKeys.add("'gestion-interventions'");
  viewKeys.add("'gestion-factures'");
  viewKeys.add("'gestion-paiements'");
  viewKeys.add("'affaires'");

  // Modules dynamiques
  for (const mod of modules) {
    if (IGNORED_MODULES.has(mod.code)) continue;
    const group = MODULE_GROUP_MAP[mod.code];
    if (group === '_hidden' || group === '_skip') continue;
    viewKeys.add(`'${mod.code}'`);
  }

  // Import modules
  viewKeys.add("'import-odoo'");
  viewKeys.add("'import-axonaut'");
  viewKeys.add("'import-pennylane'");
  viewKeys.add("'import-sage'");
  viewKeys.add("'import-chorus'");

  // Profile/Settings
  viewKeys.add("'profile'");
  viewKeys.add("'settings'");

  return `export type ViewKey =\n  | ${Array.from(viewKeys).join('\n  | ')};`;
}

function generateMenuItems(modules) {
  const items = [];

  // Modules statiques
  items.push("  { key: 'saisie', label: 'Nouvelle saisie', group: 'Saisie' },");
  items.push("  { key: 'gestion-devis', label: 'Devis', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-commandes', label: 'Commandes', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-interventions', label: 'Interventions', group: 'Gestion', capability: 'interventions.view' },");
  items.push("  { key: 'gestion-factures', label: 'Factures', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-paiements', label: 'Paiements', group: 'Gestion', capability: 'payments.view' },");
  items.push("  { key: 'affaires', label: 'Suivi Affaires', group: 'Affaires', capability: 'projects.view' },");

  // Grouper les modules par groupe
  const groupedModules = {};
  for (const mod of modules) {
    if (IGNORED_MODULES.has(mod.code)) continue;
    const group = MODULE_GROUP_MAP[mod.code];
    if (!group || group === '_hidden' || group === '_skip') continue;

    if (!groupedModules[group]) groupedModules[group] = [];
    groupedModules[group].push(mod);
  }

  // Ordre des groupes
  const groupOrder = ['Modules', 'Logistique', 'Commerce', 'Services', 'Digital', 'Communication', 'Finance', 'Direction', 'IA', 'Système'];

  for (const group of groupOrder) {
    const mods = groupedModules[group] || [];
    for (const mod of mods) {
      const label = MODULE_LABELS[mod.code] || mod.name;
      const capability = `${mod.code.replace(/-/g, '_')}.view`;
      items.push(`  { key: '${mod.code}', label: '${label}', group: '${group}', capability: '${capability}' },`);
    }
  }

  // Import modules
  items.push("  { key: 'import-odoo', label: 'Import Odoo', group: 'Import', capability: 'import_data.odoo' },");
  items.push("  { key: 'import-axonaut', label: 'Import Axonaut', group: 'Import', capability: 'import_data.axonaut' },");
  items.push("  { key: 'import-pennylane', label: 'Import Pennylane', group: 'Import', capability: 'import_data.pennylane' },");
  items.push("  { key: 'import-sage', label: 'Import Sage', group: 'Import', capability: 'import_data.sage' },");
  items.push("  { key: 'import-chorus', label: 'Import Chorus', group: 'Import', capability: 'import_data.chorus' },");

  return `const MENU_ITEMS: MenuItem[] = [\n${items.join('\n')}\n];`;
}

function main() {
  console.log('Génération du menu depuis modules_registry.py...\n');

  const modules = parseModulesRegistry();
  console.log(`${modules.length} modules trouvés dans le registre\n`);

  const viewKey = generateViewKey(modules);
  const menuItems = generateMenuItems(modules);

  console.log('='.repeat(60));
  console.log('ViewKey (copier dans UnifiedLayout.tsx)');
  console.log('='.repeat(60));
  console.log(viewKey);

  console.log('\n' + '='.repeat(60));
  console.log('MENU_ITEMS (copier dans UnifiedLayout.tsx)');
  console.log('='.repeat(60));
  console.log(menuItems);

  console.log('\n✓ Configuration générée. Copiez dans UnifiedLayout.tsx');
}

main();
