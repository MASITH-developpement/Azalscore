/**
 * AZALSCORE Module - Ordres de Service - Intervention Info Tab
 * Onglet informations generales de l'intervention
 */

import React from 'react';
import {
  FileText, Building2, User, MapPin, Tag, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import {
  getFullAddress,
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_INTERVENTION_CONFIG
} from '../types';
import type { Intervention } from '../types';
import type { TabContentProps } from '@ui/standards';

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
            {intervention.client_name && (
              <>
                <dt><Building2 size={14} /> Client</dt>
                <dd>{intervention.client_name}</dd>
              </>
            )}
            {intervention.donneur_ordre_name && (
              <>
                <dt><User size={14} /> Donneur d'ordre</dt>
                <dd>{intervention.donneur_ordre_name}</dd>
              </>
            )}
            {intervention.projet_name && (
              <>
                <dt><Tag size={14} /> Projet</dt>
                <dd>{intervention.projet_name}</dd>
              </>
            )}
            {!intervention.client_name && !intervention.donneur_ordre_name && (
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
                <div>{intervention.adresse_ligne1}</div>
                {intervention.adresse_ligne2 && <div>{intervention.adresse_ligne2}</div>}
                {(intervention.code_postal || intervention.ville) && (
                  <div>{intervention.code_postal} {intervention.ville}</div>
                )}
              </dd>
              {intervention.contact_sur_place && (
                <>
                  <dt><User size={14} /> Contact</dt>
                  <dd>{intervention.contact_sur_place} {intervention.telephone_contact && `- ${intervention.telephone_contact}`}</dd>
                </>
              )}
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

      {/* Type et facturation */}
      <Card
        title="Facturation"
        icon={<Calendar size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="azals-stat">
            <span className="azals-stat__label">Type</span>
            <span className={`azals-badge azals-badge--${TYPE_INTERVENTION_CONFIG[intervention.type_intervention]?.color || 'gray'}`}>
              {TYPE_INTERVENTION_CONFIG[intervention.type_intervention]?.label || intervention.type_intervention}
            </span>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Montant HT</span>
            <span className="azals-stat__value">
              {intervention.montant_ht ? formatCurrency(intervention.montant_ht) : '-'}
            </span>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Facturable</span>
            <span className="azals-stat__value">{intervention.facturable !== false ? 'Oui' : 'Non'}</span>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default InterventionInfoTab;
