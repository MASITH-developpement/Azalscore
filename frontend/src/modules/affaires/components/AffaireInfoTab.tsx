/**
 * AZALSCORE Module - AFFAIRES - Info Tab
 * Onglet informations générales de l'affaire
 */

import React from 'react';
import {
  Building2, User, Calendar, Clock, FileText,
  Package, Wrench, AlertTriangle, Target
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatPercent } from '@/utils/formatters';
import {
  PRIORITY_CONFIG, STATUS_CONFIG,
  isLate, getDaysRemaining
} from '../types';
import type { Affaire } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AffaireInfoTab - Informations générales de l'affaire
 */
export const AffaireInfoTab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const isAffaireLate = isLate(affaire);
  const daysRemaining = getDaysRemaining(affaire.end_date);

  return (
    <div className="azals-std-tab-content">
      {/* Alerte retard */}
      {isAffaireLate && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Affaire en retard</strong>
            <p>
              La date de fin prévue ({formatDate(affaire.end_date)}) est dépassée.
              {affaire.progress < 100 && ` Avancement actuel: ${formatPercent(affaire.progress)}`}
            </p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations client */}
        <Card title="Client" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Nom</dt>
              <dd className="font-medium">{affaire.customer_name || '-'}</dd>
            </div>
            <div className="azals-dl__row azals-std-field--secondary">
              <dt>Code client</dt>
              <dd>{affaire.customer_code || '-'}</dd>
            </div>
          </dl>
        </Card>

        {/* Responsable */}
        <Card title="Responsable" icon={<User size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Chef de projet</dt>
              <dd className="font-medium">{affaire.project_manager_name || '-'}</dd>
            </div>
            {affaire.team_members && affaire.team_members.length > 0 && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt>Équipe</dt>
                <dd>{affaire.team_members.length} membre(s)</dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Planification */}
        <Card title="Planification" icon={<Calendar size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt>Date de début</dt>
              <dd>{formatDate(affaire.start_date)}</dd>
            </div>
            <div className="azals-dl__row">
              <dt>Date de fin prévue</dt>
              <dd className={isAffaireLate ? 'text-danger' : ''}>
                {formatDate(affaire.end_date)}
                {daysRemaining !== null && daysRemaining > 0 && (
                  <span className="text-muted ml-2">({daysRemaining} j restants)</span>
                )}
                {daysRemaining !== null && daysRemaining < 0 && (
                  <span className="text-danger ml-2">({Math.abs(daysRemaining)} j de retard)</span>
                )}
              </dd>
            </div>
            {affaire.actual_start_date && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt>Début réel</dt>
                <dd>{formatDate(affaire.actual_start_date)}</dd>
              </div>
            )}
            {affaire.actual_end_date && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt>Fin réelle</dt>
                <dd>{formatDate(affaire.actual_end_date)}</dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Avancement */}
        <Card title="Avancement" icon={<Target size={18} />}>
          <div className="azals-progress-display">
            <div className="azals-progress-display__bar">
              <div
                className="azals-progress-display__fill"
                style={{
                  width: `${Math.min(affaire.progress || 0, 100)}%`,
                  backgroundColor: affaire.progress >= 100 ? 'var(--azals-success-500)' : 'var(--azals-primary-500)',
                }}
              />
            </div>
            <span className="azals-progress-display__value">{formatPercent(affaire.progress)}</span>
          </div>
          <dl className="azals-dl mt-3">
            <div className="azals-dl__row">
              <dt>Statut</dt>
              <dd>
                <span className={`azals-badge azals-badge--${STATUS_CONFIG[affaire.status].color}`}>
                  {STATUS_CONFIG[affaire.status].icon}
                  <span className="ml-1">{STATUS_CONFIG[affaire.status].label}</span>
                </span>
              </dd>
            </div>
            <div className="azals-dl__row">
              <dt>Priorité</dt>
              <dd>
                <span className={`azals-badge azals-badge--${PRIORITY_CONFIG[affaire.priority].color} azals-badge--outline`}>
                  {PRIORITY_CONFIG[affaire.priority].label}
                </span>
              </dd>
            </div>
          </dl>
        </Card>
      </Grid>

      {/* Origine / Documents liés */}
      {(affaire.commande_reference || affaire.ods_reference || affaire.devis_reference) && (
        <Card title="Documents d'origine" icon={<FileText size={18} />} className="mt-4">
          <div className="azals-linked-docs">
            {affaire.devis_reference && (
              <button
                className="azals-linked-doc azals-linked-doc--devis"
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'devis', params: { id: affaire.devis_id } }
                }))}
              >
                <FileText size={16} />
                <span>Devis: {affaire.devis_reference}</span>
              </button>
            )}
            {affaire.commande_reference && (
              <button
                className="azals-linked-doc azals-linked-doc--commande"
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'commandes', params: { id: affaire.commande_id } }
                }))}
              >
                <Package size={16} />
                <span>Commande: {affaire.commande_reference}</span>
              </button>
            )}
            {affaire.ods_reference && (
              <button
                className="azals-linked-doc azals-linked-doc--ods"
                onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'ordres-service', params: { id: affaire.ods_id } }
                }))}
              >
                <Wrench size={16} />
                <span>OS: {affaire.ods_reference}</span>
              </button>
            )}
          </div>
        </Card>
      )}

      {/* Description */}
      {affaire.description && (
        <Card title="Description" icon={<FileText size={18} />} className="mt-4">
          <p className="text-gray-700 whitespace-pre-wrap">{affaire.description}</p>
        </Card>
      )}

      {/* Notes */}
      {affaire.notes && (
        <Card title="Notes" className="mt-4">
          <p className="text-gray-600 whitespace-pre-wrap">{affaire.notes}</p>
        </Card>
      )}

      {/* Notes internes (ERP only) */}
      {affaire.internal_notes && (
        <Card title="Notes internes" className="mt-4 azals-std-field--secondary">
          <p className="text-gray-600 whitespace-pre-wrap">{affaire.internal_notes}</p>
        </Card>
      )}

      {/* Métadonnées (ERP only) */}
      <Card title="Métadonnées" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
        <dl className="azals-dl azals-dl--inline">
          <div className="azals-dl__row">
            <dt>Référence</dt>
            <dd className="font-mono">{affaire.reference}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Code</dt>
            <dd className="font-mono">{affaire.code}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Créé le</dt>
            <dd>{formatDate(affaire.created_at)}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Créé par</dt>
            <dd>{affaire.created_by || 'Système'}</dd>
          </div>
          <div className="azals-dl__row">
            <dt>Modifié le</dt>
            <dd>{formatDate(affaire.updated_at)}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
};

export default AffaireInfoTab;
