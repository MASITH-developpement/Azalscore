/**
 * AZALSCORE Module - AFFAIRES - History Tab
 * Onglet historique et audit de l'affaire
 */

import React from 'react';
import {
  Clock, User, Edit, Check, X, Plus, Play, Pause,
  FileText, ArrowRight, Calendar, Target, AlertTriangle
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import { STATUS_CONFIG } from '../types';
import type { Affaire, AffaireHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AffaireHistoryTab - Historique et audit trail de l'affaire
 */
export const AffaireHistoryTab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  // Générer l'historique à partir des données de l'affaire
  const history = generateHistoryFromAffaire(affaire);

  return (
    <div className="azals-std-tab-content">
      <Card title="Historique des modifications" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((entry, index) => (
              <HistoryEntry
                key={entry.id}
                entry={entry}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      {/* Interventions liées */}
      {affaire.interventions && affaire.interventions.length > 0 && (
        <Card title="Historique des interventions" icon={<Calendar size={18} />} className="mt-4">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Référence</th>
                <th>Technicien</th>
                <th>Durée</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {affaire.interventions.map((intervention) => (
                <tr
                  key={intervention.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'interventions', params: { id: intervention.id } }
                  }))}
                >
                  <td>{formatDateTime(intervention.date)}</td>
                  <td className="font-medium text-primary">{intervention.reference}</td>
                  <td>{intervention.technician_name || '-'}</td>
                  <td>{intervention.duration_hours ? `${intervention.duration_hours}h` : '-'}</td>
                  <td>
                    <span className={`azals-badge azals-badge--${intervention.status === 'TERMINE' ? 'green' : 'blue'}`}>
                      {intervention.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Journal d'audit détaillé (ERP only) */}
      <Card
        title="Journal d'audit détaillé"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Détails</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Système'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1" />
                      <span className="text-success">{entry.new_value}</span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant entrée de timeline
 */
interface HistoryEntryProps {
  entry: AffaireHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <Plus size={16} className="text-success" />;
    }
    if (action.includes('démarr') || action.includes('lancé')) {
      return <Play size={16} className="text-primary" />;
    }
    if (action.includes('pause')) {
      return <Pause size={16} className="text-warning" />;
    }
    if (action.includes('terminé') || action.includes('clôtur')) {
      return <Check size={16} className="text-success" />;
    }
    if (action.includes('annulé')) {
      return <X size={16} className="text-danger" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('avancement') || action.includes('progress')) {
      return <Target size={16} className="text-primary" />;
    }
    if (action.includes('retard')) {
      return <AlertTriangle size={16} className="text-danger" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">
            {entry.details}
          </p>
        )}
        {entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Générer l'historique à partir des données de l'affaire
 */
function generateHistoryFromAffaire(affaire: Affaire): AffaireHistoryEntry[] {
  const history: AffaireHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: affaire.created_at,
    action: 'Affaire créée',
    user_name: affaire.created_by,
    details: `Référence: ${affaire.reference}`,
  });

  // Début réel
  if (affaire.actual_start_date) {
    history.push({
      id: 'started',
      timestamp: affaire.actual_start_date,
      action: 'Affaire démarrée',
      old_value: STATUS_CONFIG.PLANIFIE.label,
      new_value: STATUS_CONFIG.EN_COURS.label,
    });
  }

  // Statut en pause
  if (affaire.status === 'EN_PAUSE') {
    history.push({
      id: 'paused',
      timestamp: affaire.updated_at,
      action: 'Affaire mise en pause',
      new_value: STATUS_CONFIG.EN_PAUSE.label,
    });
  }

  // Terminé
  if (affaire.status === 'TERMINE' || affaire.actual_end_date) {
    history.push({
      id: 'completed',
      timestamp: affaire.actual_end_date || affaire.updated_at,
      action: 'Affaire terminée',
      details: `Avancement final: ${affaire.progress}%`,
      new_value: STATUS_CONFIG.TERMINE.label,
    });
  }

  // Annulé
  if (affaire.status === 'ANNULE') {
    history.push({
      id: 'cancelled',
      timestamp: affaire.updated_at,
      action: 'Affaire annulée',
      new_value: STATUS_CONFIG.ANNULE.label,
    });
  }

  // Historique fourni par l'API
  if (affaire.history && affaire.history.length > 0) {
    history.push(...affaire.history);
  }

  // Trier par date décroissante (plus récent en premier)
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default AffaireHistoryTab;
