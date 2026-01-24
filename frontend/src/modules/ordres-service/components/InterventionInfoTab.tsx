/**
 * AZALSCORE Module - Ordres de Service - Intervention Info Tab
 * Onglet informations generales de l'intervention
 */

import React from 'react';
import {
  FileText, Building2, User, MapPin, Tag, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import {
  formatDate, formatCurrency, getFullAddress,
  STATUT_CONFIG, PRIORITE_CONFIG
} from '../types';

/**
 * InterventionInfoTab - Informations generales
 */
export const InterventionInfoTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const fullAddress = getFullAddress(intervention);

  return (
    <div className="azals-std-tab-content">
      {/* Description */}
      <Card title="Description" icon={<FileText size={18} />} className="mb-4">
        <p className={intervention.description ? '' : 'text-muted'}>
          {intervention.description || 'Aucune description'}
        </p>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Client / Donneur d'ordre */}
        <Card title="Client / Donneur d'ordre" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            {intervention.client_nom && (
              <>
                <dt><Building2 size={14} /> Client</dt>
                <dd>{intervention.client_nom}</dd>
              </>
            )}
            {intervention.donneur_ordre_nom && (
              <>
                <dt><User size={14} /> Donneur d'ordre</dt>
                <dd>{intervention.donneur_ordre_nom}</dd>
              </>
            )}
            {intervention.projet_nom && (
              <>
                <dt><Tag size={14} /> Projet</dt>
                <dd>{intervention.projet_nom}</dd>
              </>
            )}
            {!intervention.client_nom && !intervention.donneur_ordre_nom && (
              <p className="text-muted">Aucun client associe</p>
            )}
          </dl>
        </Card>

        {/* Lieu d'intervention */}
        <Card title="Lieu d'intervention" icon={<MapPin size={18} />}>
          {fullAddress ? (
            <dl className="azals-dl">
              <dt><MapPin size={14} /> Adresse</dt>
              <dd>
                <div>{intervention.adresse_intervention}</div>
                {(intervention.code_postal || intervention.ville) && (
                  <div>{intervention.code_postal} {intervention.ville}</div>
                )}
              </dd>
            </dl>
          ) : (
            <p className="text-muted">Aucune adresse renseignee</p>
          )}
        </Card>
      </Grid>

      {/* Statut et Priorite */}
      <Card title="Classification" icon={<Tag size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <span className={`azals-badge azals-badge--${statutConfig.color}`}>
              {statutConfig.label}
            </span>
            <p className="text-sm text-muted mt-1">{statutConfig.description}</p>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Priorite</span>
            <span className={`azals-badge azals-badge--${prioriteConfig.color} azals-badge--outline`}>
              {prioriteConfig.label}
            </span>
            <p className="text-sm text-muted mt-1">{prioriteConfig.description}</p>
          </div>
        </Grid>
      </Card>

      {/* Estimation (ERP only) */}
      <Card
        title="Estimation"
        icon={<Calendar size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={2} gap="md">
          <div className="azals-stat">
            <span className="azals-stat__label">Montant estime</span>
            <span className="azals-stat__value">
              {intervention.montant_estime ? formatCurrency(intervention.montant_estime) : '-'}
            </span>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Cree le</span>
            <span className="azals-stat__value">{formatDate(intervention.created_at)}</span>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default InterventionInfoTab;
