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
import { moduleMeta as ai_assistant } from './ai-assistant/meta';
import { moduleMeta as assets } from './assets/meta';
import { moduleMeta as audit } from './audit/meta';
import { moduleMeta as autoconfig } from './autoconfig/meta';
import { moduleMeta as automated_accounting } from './automated-accounting/meta';
import { moduleMeta as backup } from './backup/meta';
import { moduleMeta as bi } from './bi/meta';
import { moduleMeta as break_glass } from './break-glass/meta';
import { moduleMeta as broadcast } from './broadcast/meta';
import { moduleMeta as cockpit } from './cockpit/meta';
import { moduleMeta as commandes } from './commandes/meta';
import { moduleMeta as commercial } from './commercial/meta';
import { moduleMeta as complaints } from './complaints/meta';
import { moduleMeta as compliance } from './compliance/meta';
import { moduleMeta as comptabilite } from './comptabilite/meta';
import { moduleMeta as consolidation } from './consolidation/meta';
import { moduleMeta as contacts } from './contacts/meta';
import { moduleMeta as contracts } from './contracts/meta';
import { moduleMeta as country_packs } from './country-packs/meta';
import { moduleMeta as country_packs_france } from './country-packs-france/meta';
import { moduleMeta as crm } from './crm/meta';
import { moduleMeta as devis } from './devis/meta';
import { moduleMeta as ecommerce } from './ecommerce/meta';
import { moduleMeta as email } from './email/meta';
import { moduleMeta as enrichment } from './enrichment/meta';
import { moduleMeta as esignature } from './esignature/meta';
import { moduleMeta as expenses } from './expenses/meta';
import { moduleMeta as factures } from './factures/meta';
import { moduleMeta as field_service } from './field-service/meta';
import { moduleMeta as finance } from './finance/meta';
import { moduleMeta as guardian } from './guardian/meta';
import { moduleMeta as helpdesk } from './helpdesk/meta';
import { moduleMeta as hr } from './hr/meta';
import { moduleMeta as hr_vault } from './hr-vault/meta';
import { moduleMeta as i18n } from './i18n/meta';
import { moduleMeta as iam } from './iam/meta';
import { moduleMeta as import_module } from './import/meta';
import { moduleMeta as import_gateways } from './import-gateways/meta';
import { moduleMeta as interventions } from './interventions/meta';
import { moduleMeta as inventory } from './inventory/meta';
import { moduleMeta as invoicing } from './invoicing/meta';
import { moduleMeta as maintenance } from './maintenance/meta';
import { moduleMeta as marceau } from './marceau/meta';
import { moduleMeta as marketplace } from './marketplace/meta';
import { moduleMeta as mobile } from './mobile/meta';
import { moduleMeta as not_found } from './not-found/meta';
import { moduleMeta as odoo_import } from './odoo-import/meta';
import { moduleMeta as ordres_service } from './ordres-service/meta';
import { moduleMeta as partners } from './partners/meta';
import { moduleMeta as payments } from './payments/meta';
import { moduleMeta as pos } from './pos/meta';
import { moduleMeta as procurement } from './procurement/meta';
import { moduleMeta as production } from './production/meta';
import { moduleMeta as profile } from './profile/meta';
import { moduleMeta as projects } from './projects/meta';
import { moduleMeta as purchases } from './purchases/meta';
import { moduleMeta as qc } from './qc/meta';
import { moduleMeta as qualite } from './qualite/meta';
import { moduleMeta as quality } from './quality/meta';
import { moduleMeta as rfq } from './rfq/meta';
import { moduleMeta as saisie } from './saisie/meta';
import { moduleMeta as settings } from './settings/meta';
import { moduleMeta as social_networks } from './social-networks/meta';
import { moduleMeta as social_publications } from './social-publications/meta';
import { moduleMeta as stripe_integration } from './stripe-integration/meta';
import { moduleMeta as subscriptions } from './subscriptions/meta';
import { moduleMeta as tenants } from './tenants/meta';
import { moduleMeta as timesheet } from './timesheet/meta';
import { moduleMeta as treasury } from './treasury/meta';
import { moduleMeta as triggers } from './triggers/meta';
import { moduleMeta as vehicles } from './vehicles/meta';
import { moduleMeta as warranty } from './warranty/meta';
import { moduleMeta as web } from './web/meta';
import { moduleMeta as website } from './website/meta';
import { moduleMeta as worksheet } from './worksheet/meta';

export interface ModuleMeta {
  readonly name: string;
  readonly code: string;
  readonly version: string;
  readonly status: 'active' | 'degraded' | 'inactive';
  readonly frontend: {
    readonly hasUI: boolean;
    readonly pagesCount?: number;
    readonly routesCount?: number;
    readonly errorsCount?: number;
    readonly lastAudit: string;
    readonly compliance: boolean;
  };
  readonly backend: {
    readonly apiAvailable: boolean;
    readonly lastCheck: string;
    readonly endpoints?: readonly string[];
  };
  readonly owner: string;
  readonly criticality: 'high' | 'medium' | 'low';
  readonly createdAt: string;
  readonly updatedAt: string;
}

export const moduleRegistry: Record<string, ModuleMeta> = {
  'accounting': accounting,
  'admin': admin,
  'affaires': affaires,
  'ai-assistant': ai_assistant,
  'assets': assets,
  'audit': audit,
  'autoconfig': autoconfig,
  'automated-accounting': automated_accounting,
  'backup': backup,
  'bi': bi,
  'break-glass': break_glass,
  'broadcast': broadcast,
  'cockpit': cockpit,
  'commandes': commandes,
  'commercial': commercial,
  'complaints': complaints,
  'compliance': compliance,
  'comptabilite': comptabilite,
  'consolidation': consolidation,
  'contacts': contacts,
  'contracts': contracts,
  'country-packs': country_packs,
  'country-packs-france': country_packs_france,
  'crm': crm,
  'devis': devis,
  'ecommerce': ecommerce,
  'email': email,
  'enrichment': enrichment,
  'esignature': esignature,
  'expenses': expenses,
  'factures': factures,
  'field-service': field_service,
  'finance': finance,
  'guardian': guardian,
  'helpdesk': helpdesk,
  'hr': hr,
  'hr-vault': hr_vault,
  'i18n': i18n,
  'iam': iam,
  'import': import_module,
  'import-gateways': import_gateways,
  'interventions': interventions,
  'inventory': inventory,
  'invoicing': invoicing,
  'maintenance': maintenance,
  'marceau': marceau,
  'marketplace': marketplace,
  'mobile': mobile,
  'not-found': not_found,
  'odoo-import': odoo_import,
  'ordres-service': ordres_service,
  'partners': partners,
  'payments': payments,
  'pos': pos,
  'procurement': procurement,
  'production': production,
  'profile': profile,
  'projects': projects,
  'purchases': purchases,
  'qc': qc,
  'qualite': qualite,
  'quality': quality,
  'rfq': rfq,
  'saisie': saisie,
  'settings': settings,
  'social-networks': social_networks,
  'social-publications': social_publications,
  'stripe-integration': stripe_integration,
  'subscriptions': subscriptions,
  'tenants': tenants,
  'timesheet': timesheet,
  'treasury': treasury,
  'triggers': triggers,
  'vehicles': vehicles,
  'warranty': warranty,
  'web': web,
  'website': website,
  'worksheet': worksheet,
};

export type ModuleCode = keyof typeof moduleRegistry;
