/**
 * AZALSCORE - Registre Global des Modules (AZA-FE-META)
 * ======================================================
 * Import centralisé de toutes métadonnées
 *
 * Ce fichier est généré automatiquement par generate-module-meta.ts
 * NE PAS MODIFIER MANUELLEMENT
 */

import { moduleMeta as accounting } from './accounting/meta';
import { moduleMeta as admin } from './admin/meta';
import { moduleMeta as affaires } from './affaires/meta';
import { moduleMeta as automated_accounting } from './automated-accounting/meta';
import { moduleMeta as bi } from './bi/meta';
import { moduleMeta as break_glass } from './break-glass/meta';
import { moduleMeta as cockpit } from './cockpit/meta';
import { moduleMeta as commandes } from './commandes/meta';
import { moduleMeta as compliance } from './compliance/meta';
import { moduleMeta as comptabilite } from './comptabilite/meta';
import { moduleMeta as country_packs_france } from './country-packs-france/meta';
import { moduleMeta as crm } from './crm/meta';
import { moduleMeta as devis } from './devis/meta';
import { moduleMeta as ecommerce } from './ecommerce/meta';
import { moduleMeta as factures } from './factures/meta';
import { moduleMeta as helpdesk } from './helpdesk/meta';
import { moduleMeta as hr } from './hr/meta';
import { moduleMeta as i18n } from './i18n/meta';
import { moduleMeta as interventions } from './interventions/meta';
import { moduleMeta as inventory } from './inventory/meta';
import { moduleMeta as invoicing } from './invoicing/meta';
import { moduleMeta as maintenance } from './maintenance/meta';
import { moduleMeta as marketplace } from './marketplace/meta';
import { moduleMeta as mobile } from './mobile/meta';
import { moduleMeta as not_found } from './not-found/meta';
import { moduleMeta as ordres_service } from './ordres-service/meta';
import { moduleMeta as partners } from './partners/meta';
import { moduleMeta as payments } from './payments/meta';
import { moduleMeta as pos } from './pos/meta';
import { moduleMeta as production } from './production/meta';
import { moduleMeta as profile } from './profile/meta';
import { moduleMeta as projects } from './projects/meta';
import { moduleMeta as purchases } from './purchases/meta';
import { moduleMeta as qualite } from './qualite/meta';
import { moduleMeta as settings } from './settings/meta';
import { moduleMeta as subscriptions } from './subscriptions/meta';
import { moduleMeta as treasury } from './treasury/meta';
import { moduleMeta as vehicles } from './vehicles/meta';
import { moduleMeta as web } from './web/meta';
import { moduleMeta as worksheet } from './worksheet/meta';

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
    endpoints?: readonly string[];
  };
  owner: string;
  criticality: 'high' | 'medium' | 'low';
  createdAt: string;
  updatedAt: string;
}

export const moduleRegistry: Record<string, ModuleMeta> = {
  'accounting': accounting,
  'admin': admin,
  'affaires': affaires,
  'automated-accounting': automated_accounting,
  'bi': bi,
  'break-glass': break_glass,
  'cockpit': cockpit,
  'commandes': commandes,
  'compliance': compliance,
  'comptabilite': comptabilite,
  'country-packs-france': country_packs_france,
  'crm': crm,
  'devis': devis,
  'ecommerce': ecommerce,
  'factures': factures,
  'helpdesk': helpdesk,
  'hr': hr,
  'i18n': i18n,
  'interventions': interventions,
  'inventory': inventory,
  'invoicing': invoicing,
  'maintenance': maintenance,
  'marketplace': marketplace,
  'mobile': mobile,
  'not-found': not_found,
  'ordres-service': ordres_service,
  'partners': partners,
  'payments': payments,
  'pos': pos,
  'production': production,
  'profile': profile,
  'projects': projects,
  'purchases': purchases,
  'qualite': qualite,
  'settings': settings,
  'subscriptions': subscriptions,
  'treasury': treasury,
  'vehicles': vehicles,
  'web': web,
  'worksheet': worksheet,
};

export type ModuleCode = keyof typeof moduleRegistry;
