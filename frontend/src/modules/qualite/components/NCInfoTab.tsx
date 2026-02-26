/**
 * AZALSCORE Module - Qualite - NC Info Tab
 * Onglet informations generales de la non-conformite
 */

import React from 'react';
import {
  FileText, Package, Calendar, Tag, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import {
  getNCAge,
  NC_TYPE_CONFIG, NC_ORIGIN_CONFIG, SEVERITY_CONFIG, NC_STATUS_CONFIG
} from '../types';
import type { NonConformance } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * NCInfoTab - Informations generales
 */
export const NCInfoTab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const typeConfig = NC_TYPE_CONFIG[nc.type];
  const originConfig = NC_ORIGIN_CONFIG[nc.origin];
  const severityConfig = SEVERITY_CONFIG[nc.severity];
  const _statusConfig = NC_STATUS_CONFIG[nc.status];

  return (
    <div className="azals-std-tab-content">
      {/* Description */}
      <Card title="Description" icon={<FileText size={18} />} className="mb-4">
        <p className={nc.description ? '' : 'text-muted'}>
          {nc.description || 'Aucune description'}
        </p>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Classification */}
        <Card title="Classification" icon={<Tag size={18} />}>
          <dl className="azals-dl">
            <dt><Tag size={14} /> Type</dt>
            <dd>
              <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                {typeConfig.label}
              </span>
              <p className="text-sm text-muted mt-1">{typeConfig.description}</p>
            </dd>

            <dt><Tag size={14} /> Origine</dt>
            <dd>
              <span className={`azals-badge azals-badge--${originConfig.color}`}>
                {originConfig.label}
              </span>
              <p className="text-sm text-muted mt-1">{originConfig.description}</p>
            </dd>

            <dt><AlertTriangle size={14} /> Gravite</dt>
            <dd>
              <span className={`azals-badge azals-badge--${severityConfig.color}`}>
                {severityConfig.label}
              </span>
              <p className="text-sm text-muted mt-1">{severityConfig.description}</p>
            </dd>
          </dl>
        </Card>

        {/* Produit concerne */}
        <Card title="Produit concerne" icon={<Package size={18} />}>
          {nc.product_name ? (
            <dl className="azals-dl">
              <dt><Package size={14} /> Produit</dt>
              <dd>{nc.product_name}</dd>

              {nc.lot_number && (
                <>
                  <dt><Tag size={14} /> N° de lot</dt>
                  <dd><code className="font-mono">{nc.lot_number}</code></dd>
                </>
              )}
            </dl>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Package size={32} className="text-muted" />
              <p className="text-muted">Aucun produit associe</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Dates et responsables */}
      <Card title="Suivi" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-stat">
            <span className="azals-stat__label">Date de detection</span>
            <span className="azals-stat__value">{formatDate(nc.detected_date)}</span>
            <p className="text-sm text-muted">{getNCAge(nc)}</p>
          </div>

          <div className="azals-stat">
            <span className="azals-stat__label">Date objectif</span>
            <span className="azals-stat__value">{formatDate(nc.target_date)}</span>
          </div>

          <div className="azals-stat">
            <span className="azals-stat__label">Detecte par</span>
            <span className="azals-stat__value">{nc.detected_by_name || '-'}</span>
          </div>

          <div className="azals-stat">
            <span className="azals-stat__label">Responsable</span>
            <span className="azals-stat__value">{nc.responsible_name || 'Non assigne'}</span>
          </div>
        </Grid>
      </Card>

      {/* Estimation cout (ERP only) */}
      {nc.cost_estimate !== undefined && (
        <Card
          title="Estimation des couts"
          icon={<Tag size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <div className="azals-stat">
            <span className="azals-stat__label">Cout estime</span>
            <span className="azals-stat__value text-warning">
              {nc.cost_estimate.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
            </span>
          </div>
        </Card>
      )}
    </div>
  );
};

export default NCInfoTab;
