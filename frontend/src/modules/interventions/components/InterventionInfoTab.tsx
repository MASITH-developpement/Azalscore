/**
 * AZALSCORE Module - INTERVENTIONS - Info Tab
 * Onglet informations générales de l'intervention
 */

import React from 'react';
import {
  Building2, User, Calendar, Clock, MapPin, FileText,
  Phone, Mail, AlertTriangle, Wrench, Package, Lock, ShieldAlert
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatDuration } from '@/utils/formatters';
import {
  formatAddress,
  PRIORITE_CONFIG, TYPE_CONFIG, STATUT_CONFIG,
  isLate, getDaysUntilIntervention
} from '../types';
import type { Intervention } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * InterventionInfoTab - Informations générales de l'intervention
 */
export const InterventionInfoTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const isInterventionLate = isLate(intervention);
  const daysUntil = getDaysUntilIntervention(intervention);

  const risqueColor: Record<string, string> = {
    MOYEN: 'warning',
    ELEVE: 'danger',
    CRITIQUE: 'danger',
  };

  return (
    <div className="azals-std-tab-content">
      {/* Alerte BLOQUEE */}
      {intervention.statut === 'BLOQUEE' && (
        <div className="azals-alert azals-alert--danger mb-4">
          <Lock size={20} />
          <div>
            <strong>Intervention bloquée</strong>
            <p>{intervention.motif_blocage || 'Motif non renseigné'}</p>
            {intervention.date_blocage && (
              <p className="text-sm text-muted mt-1">Bloquée le {formatDate(intervention.date_blocage)}</p>
            )}
          </div>
        </div>
      )}

      {/* Alerte risque métier */}
      {intervention.indicateurs && intervention.indicateurs.indicateur_risque !== 'FAIBLE' && (
        <div className={`azals-alert azals-alert--${risqueColor[intervention.indicateurs.indicateur_risque] || 'warning'} mb-4`}>
          <ShieldAlert size={20} />
          <div>
            <strong>Risque {intervention.indicateurs.indicateur_risque.toLowerCase()}</strong>
            <p>{intervention.indicateurs.risque_justification}</p>
          </div>
        </div>
      )}

      {/* Alerte retard */}
      {isInterventionLate && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Intervention en retard</strong>
            <p>
              La date prévue ({formatDate(intervention.date_prevue)}) est dépassée.
            </p>
          </div>
        </div>
      )}

      {/* Alerte urgente */}
      {intervention.priorite === 'URGENT' && intervention.statut !== 'TERMINEE' && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Intervention urgente</strong>
            <p>Cette intervention est marquée comme urgente.</p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations client */}
        <Card title="Client" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Nom</dt>
              <dd className="font-medium">{intervention.client_name || '-'}</dd>
            </div>
            <div className="azals-dl__row azals-std-field--secondary">
              <dt>Code client</dt>
              <dd>{intervention.client_code || '-'}</dd>
            </div>
            {intervention.donneur_ordre_name && (
              <div className="azals-dl__row">
                <dt>Donneur d'ordre</dt>
                <dd>{intervention.donneur_ordre_name}</dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Intervenant */}
        <Card title="Intervenant" icon={<User size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Technicien</dt>
              <dd className="font-medium">{intervention.intervenant_name || 'Non assigné'}</dd>
            </div>
            {intervention.equipe && intervention.equipe.length > 0 && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt>Équipe</dt>
                <dd>{intervention.equipe.length} membre(s)</dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Planification */}
        <Card title="Planification" icon={<Calendar size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Date prévue</dt>
              <dd className={isInterventionLate ? 'text-danger' : ''}>
                {formatDate(intervention.date_prevue)}
                {daysUntil !== null && daysUntil > 0 && (
                  <span className="text-muted ml-2">(dans {daysUntil} j)</span>
                )}
                {daysUntil !== null && daysUntil < 0 && (
                  <span className="text-danger ml-2">({Math.abs(daysUntil)} j de retard)</span>
                )}
              </dd>
            </div>
            {intervention.heure_prevue && (
              <div className="azals-dl__row">
                <dt>Heure prévue</dt>
                <dd>{intervention.heure_prevue}</dd>
              </div>
            )}
            <div className="azals-dl__row">
              <dt>Durée prévue</dt>
              <dd>{formatDuration(intervention.duree_prevue_minutes)}</dd>
            </div>
          </dl>
        </Card>

        {/* Type et priorité */}
        <Card title="Classification" icon={<Wrench size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Type</dt>
              <dd>
                <span className={`azals-badge azals-badge--${TYPE_CONFIG[intervention.type_intervention].color}`}>
                  {TYPE_CONFIG[intervention.type_intervention].label}
                </span>
              </dd>
            </div>
            <div className="azals-dl__row">
              <dt>Priorité</dt>
              <dd>
                <span className={`azals-badge azals-badge--${PRIORITE_CONFIG[intervention.priorite].color} azals-badge--outline`}>
                  {PRIORITE_CONFIG[intervention.priorite].label}
                </span>
              </dd>
            </div>
            <div className="azals-dl__row">
              <dt>Statut</dt>
              <dd>
                <span className={`azals-badge azals-badge--${STATUT_CONFIG[intervention.statut].color}`}>
                  {STATUT_CONFIG[intervention.statut].icon}
                  <span className="ml-1">{STATUT_CONFIG[intervention.statut].label}</span>
                </span>
              </dd>
            </div>
          </dl>
        </Card>
      </Grid>

      {/* Adresse d'intervention */}
      <Card title="Lieu d'intervention" icon={<MapPin size={18} />} className="mt-4">
        <div className="azals-address-block">
          <p className="font-medium">{formatAddress(intervention)}</p>
          {intervention.contact_sur_place && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-sm text-muted mb-1">Contact sur place</p>
              <div className="flex items-center gap-4">
                <span className="font-medium">{intervention.contact_sur_place}</span>
                {intervention.telephone_contact && (
                  <span className="flex items-center gap-1 text-sm">
                    <Phone size={14} />
                    {intervention.telephone_contact}
                  </span>
                )}
                {intervention.email_contact && (
                  <span className="flex items-center gap-1 text-sm">
                    <Mail size={14} />
                    {intervention.email_contact}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Description */}
      {intervention.description && (
        <Card title="Description" icon={<FileText size={18} />} className="mt-4">
          <p className="text-gray-700 whitespace-pre-wrap">{intervention.description}</p>
        </Card>
      )}

      {/* Matériel nécessaire */}
      {intervention.materiel_necessaire && (
        <Card title="Matériel nécessaire" icon={<Package size={18} />} className="mt-4">
          <div className="azals-alert azals-alert--warning">
            <Package size={18} />
            <p className="whitespace-pre-wrap">{intervention.materiel_necessaire}</p>
          </div>
        </Card>
      )}

      {/* Notes client */}
      {intervention.notes_client && (
        <Card title="Notes client" className="mt-4">
          <p className="text-gray-600 whitespace-pre-wrap">{intervention.notes_client}</p>
        </Card>
      )}

      {/* Notes internes (ERP only) */}
      {intervention.notes_internes && (
        <Card title="Notes internes" className="mt-4 azals-std-field--secondary">
          <p className="text-gray-600 whitespace-pre-wrap">{intervention.notes_internes}</p>
        </Card>
      )}

      {/* Affaire liée */}
      {intervention.affaire_reference && (
        <Card title="Document lié" icon={<FileText size={18} />} className="mt-4">
          <button
            className="azals-linked-doc azals-linked-doc--affaire"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'affaires', params: { id: intervention.affaire_id } }
              }));
            }}
          >
            <FileText size={16} />
            <span>Affaire: {intervention.affaire_reference}</span>
          </button>
        </Card>
      )}

      {/* Métadonnées (ERP only) */}
      <Card title="Métadonnées" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
        <dl className="azals-dl azals-dl--inline">
          <div className="azals-dl__row">
            <dt>Référence</dt>
            <dd className="font-mono">{intervention.reference}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Créé le</dt>
            <dd>{formatDate(intervention.created_at)}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Créé par</dt>
            <dd>{intervention.created_by || 'Système'}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Modifié le</dt>
            <dd>{formatDate(intervention.updated_at)}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
};

export default InterventionInfoTab;
