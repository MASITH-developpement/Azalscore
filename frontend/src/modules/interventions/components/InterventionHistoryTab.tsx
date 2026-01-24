/**
 * AZALSCORE Module - INTERVENTIONS - History Tab
 * Onglet historique et audit de l'intervention
 */

import React from 'react';
import {
  Clock, User, Edit, Check, Play, Calendar,
  FileText, ArrowRight, MapPin, AlertTriangle, X
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention, InterventionHistoryEntry } from '../types';
import { formatDateTime, STATUT_CONFIG } from '../types';

/**
 * InterventionHistoryTab - Historique et audit trail de l'intervention
 */
export const InterventionHistoryTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  // Générer l'historique à partir des données de l'intervention
  const history = generateHistoryFromIntervention(intervention);

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
  entry: InterventionHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <FileText size={16} className="text-primary" />;
    }
    if (action.includes('planifié') || action.includes('planification')) {
      return <Calendar size={16} className="text-blue" />;
    }
    if (action.includes('démarr') || action.includes('en cours')) {
      return <Play size={16} className="text-warning" />;
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
    if (action.includes('assign') || action.includes('intervenant')) {
      return <User size={16} className="text-purple" />;
    }
    if (action.includes('adresse') || action.includes('lieu')) {
      return <MapPin size={16} className="text-primary" />;
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
 * Générer l'historique à partir des données de l'intervention
 */
function generateHistoryFromIntervention(intervention: Intervention): InterventionHistoryEntry[] {
  const history: InterventionHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: intervention.created_at,
    action: 'Intervention créée',
    user_name: intervention.created_by,
    details: `Référence: ${intervention.reference}`,
  });

  // Planification
  if (intervention.date_prevue && intervention.statut !== 'A_PLANIFIER') {
    history.push({
      id: 'planned',
      timestamp: intervention.updated_at, // Approximation
      action: 'Intervention planifiée',
      details: `Pour le ${formatDateTime(intervention.date_prevue)}`,
      old_value: STATUT_CONFIG.A_PLANIFIER.label,
      new_value: STATUT_CONFIG.PLANIFIEE.label,
    });
  }

  // Assignation intervenant
  if (intervention.intervenant_name) {
    history.push({
      id: 'assigned',
      timestamp: intervention.updated_at, // Approximation
      action: 'Intervenant assigné',
      details: intervention.intervenant_name,
    });
  }

  // Démarrage
  if (intervention.date_debut_reelle) {
    history.push({
      id: 'started',
      timestamp: intervention.date_debut_reelle,
      action: 'Intervention démarrée',
      old_value: STATUT_CONFIG.PLANIFIEE.label,
      new_value: STATUT_CONFIG.EN_COURS.label,
    });
  }

  // Fin
  if (intervention.date_fin_reelle) {
    history.push({
      id: 'completed',
      timestamp: intervention.date_fin_reelle,
      action: 'Intervention terminée',
      details: intervention.duree_reelle_minutes
        ? `Durée: ${Math.floor(intervention.duree_reelle_minutes / 60)}h${intervention.duree_reelle_minutes % 60}`
        : undefined,
      old_value: STATUT_CONFIG.EN_COURS.label,
      new_value: STATUT_CONFIG.TERMINEE.label,
    });
  }

  // Rapport
  if (intervention.rapport) {
    history.push({
      id: 'report-created',
      timestamp: intervention.rapport.created_at,
      action: 'Rapport créé',
      details: intervention.rapport.is_signed
        ? `Signé par ${intervention.rapport.nom_signataire || 'le client'}`
        : 'En attente de signature',
    });
  }

  // Annulation
  if (intervention.statut === 'ANNULEE') {
    history.push({
      id: 'cancelled',
      timestamp: intervention.updated_at,
      action: 'Intervention annulée',
      new_value: STATUT_CONFIG.ANNULEE.label,
    });
  }

  // Historique fourni par l'API
  if (intervention.history && intervention.history.length > 0) {
    history.push(...intervention.history);
  }

  // Trier par date décroissante (plus récent en premier)
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default InterventionHistoryTab;
