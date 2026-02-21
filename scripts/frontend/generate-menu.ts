#!/usr/bin/env npx ts-node
/**
 * AZALSCORE - Générateur automatique de menu
 * ==========================================
 *
 * Génère automatiquement ViewKey et MENU_ITEMS dans UnifiedLayout.tsx
 * depuis les modules découverts dans le backend.
 *
 * Usage: npm run generate:menu
 */

import * as fs from 'fs';
import * as path from 'path';

// Configuration des groupes de menu par catégorie de module
const MODULE_GROUP_MAP: Record<string, string> = {
  // Gestion
  'invoicing': 'Gestion',
  'devis': 'Gestion',
  'commandes': 'Gestion',
  'factures': 'Gestion',
  'interventions': 'Gestion',
  'payments': 'Gestion',

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

  // IA
  'marceau': 'IA',
  'ai-assistant': 'IA',

  // Communication
  'email': 'Communication',
  'esignature': 'Communication',
  'notifications': 'Communication',

  // Import
  'odoo-import': 'Import',
  'import-odoo': 'Import',
  'import-axonaut': 'Import',
  'import-pennylane': 'Import',
  'import-sage': 'Import',
  'import-chorus': 'Import',

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
  'hr-vault': '_hidden',
};

// Labels personnalisés
const MODULE_LABELS: Record<string, string> = {
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
};

// Modules ignorés (déjà gérés autrement ou utilitaires)
const IGNORED_MODULES = new Set([
  'cache', 'currency', 'dataexchange', 'gateway', 'i18n',
  'integrations', 'scheduler', 'search', 'webhooks',
  'enrichment', 'mobile', 'hr-vault',
  // Import modules handled separately
  'IMP1', 'IMP2', 'IMP3', 'IMP4', 'IMP5',
]);

interface Module {
  code: string;
  name: string;
  category: string;
}

async function fetchModules(): Promise<Module[]> {
  // Simuler la lecture depuis modules_registry.py
  // En production, on pourrait appeler l'API ou parser le fichier Python
  const modulesFile = path.join(__dirname, '../../app/core/modules_registry.py');
  const content = fs.readFileSync(modulesFile, 'utf-8');

  const modules: Module[] = [];

  // Parser MODULE_METADATA_OVERRIDES
  const overridesMatch = content.match(/MODULE_METADATA_OVERRIDES[^{]*\{([\s\S]*?)\n\}/);
  if (overridesMatch) {
    const regex = /"([^"]+)":\s*\{[^}]*"name":\s*"([^"]+)"[^}]*"category":\s*"([^"]+)"/g;
    let match;
    while ((match = regex.exec(overridesMatch[1])) !== null) {
      modules.push({
        code: match[1].replace(/_/g, '-'),
        name: match[2],
        category: match[3],
      });
    }
  }

  return modules;
}

function generateViewKey(modules: Module[]): string {
  const groups: Record<string, string[]> = {};

  // Ajouter les modules statiques
  groups['Saisie'] = ["'saisie'"];
  groups['Gestion'] = ["'gestion-devis'", "'gestion-commandes'", "'gestion-interventions'", "'gestion-factures'", "'gestion-paiements'"];
  groups['Affaires'] = ["'affaires'"];

  for (const mod of modules) {
    if (IGNORED_MODULES.has(mod.code) || mod.code.startsWith('IMP')) continue;

    const group = MODULE_GROUP_MAP[mod.code] || mod.category;
    if (group === '_hidden') continue;

    if (!groups[group]) groups[group] = [];
    groups[group].push(`'${mod.code}'`);
  }

  // Ajouter les modules statiques finaux
  groups['Import'] = ["'import-odoo'", "'import-axonaut'", "'import-pennylane'", "'import-sage'", "'import-chorus'"];
  groups['Profile'] = ["'profile'", "'settings'"];

  const lines: string[] = ['export type ViewKey ='];
  for (const [group, keys] of Object.entries(groups)) {
    lines.push(`  // ${group}`);
    lines.push(`  | ${keys.join(' | ')}`);
  }
  lines[lines.length - 1] = lines[lines.length - 1].replace(/\|/, '') + ';';

  return lines.join('\n');
}

function generateMenuItems(modules: Module[]): string {
  const items: string[] = [];

  // Modules statiques
  items.push("  { key: 'saisie', label: 'Nouvelle saisie', group: 'Saisie' },");
  items.push("  { key: 'gestion-devis', label: 'Devis', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-commandes', label: 'Commandes', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-interventions', label: 'Interventions', group: 'Gestion', capability: 'interventions.view' },");
  items.push("  { key: 'gestion-factures', label: 'Factures', group: 'Gestion', capability: 'invoicing.view' },");
  items.push("  { key: 'gestion-paiements', label: 'Paiements', group: 'Gestion', capability: 'payments.view' },");
  items.push("  { key: 'affaires', label: 'Suivi Affaires', group: 'Affaires', capability: 'projects.view' },");

  // Modules dynamiques groupés
  const groupedModules: Record<string, Module[]> = {};
  for (const mod of modules) {
    if (IGNORED_MODULES.has(mod.code) || mod.code.startsWith('IMP')) continue;

    const group = MODULE_GROUP_MAP[mod.code] || mod.category;
    if (group === '_hidden') continue;

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

async function main() {
  console.log('Génération du menu depuis modules_registry.py...');

  const modules = await fetchModules();
  console.log(`${modules.length} modules trouvés`);

  const viewKey = generateViewKey(modules);
  const menuItems = generateMenuItems(modules);

  console.log('\n=== ViewKey ===');
  console.log(viewKey);

  console.log('\n=== MENU_ITEMS ===');
  console.log(menuItems);

  console.log('\n✓ Configuration générée. Copiez dans UnifiedLayout.tsx');
}

main().catch(console.error);
