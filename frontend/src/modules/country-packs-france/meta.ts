/**
 * AZALSCORE Module Meta - Country Packs France
 */

import type { ModuleMeta } from '../registry';

export const moduleMeta: ModuleMeta = {
  name: 'Pack France',
  code: 'country-packs-france',
  version: '1.0.0',
  status: 'active',
  frontend: {
    hasUI: true,
    pagesCount: 6,
    routesCount: 6,
    errorsCount: 0,
    lastAudit: '2026-02-15',
    compliance: true
  },
  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-15',
    endpoints: [
      '/country-packs/france/stats',
      '/country-packs/france/pcg/accounts',
      '/country-packs/france/tva/rates',
      '/country-packs/france/tva/declarations',
      '/country-packs/france/fec/generate',
      '/country-packs/france/dsn',
      '/country-packs/france/rgpd/consents',
      '/country-packs/france/rgpd/requests',
      '/country-packs/france/rgpd/breaches'
    ] as const
  },
  owner: 'compliance-team',
  criticality: 'high',
  createdAt: '2026-02-15',
  updatedAt: '2026-02-15'
};

export default moduleMeta;
