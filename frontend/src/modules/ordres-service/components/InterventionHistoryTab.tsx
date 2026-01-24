/**
 * AZALSCORE Module - Ordres de Service - Intervention History Tab
 * Onglet historique de l'intervention
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  CheckCircle, Play, Calendar, Camera, X
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention, InterventionHistoryEntry } from '../types';
import { formatDateTime, STATUT_CONFIG } from '../types';

/**
 * InterventionHistoryTab - Historique
 */
export const InterventionHistoryTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  // Generer l'historique combine
  const history = generateHistoryFromIntervention(intervention);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des evenements" icon={<Clock size={18} />}>
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

      {/* Journal d'audit detaille (ERP only) */}
      <Card
        title="Journal d'audit detaille"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
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
 * Composant entree de timeline
 */
interface HistoryEntryProps {
  entry: InterventionHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('planifi')) {
      return <Calendar size={16} className="text-blue-500" />;
    }
    if (action.includes('demar') || action.includes('debut')) {
      return <Play size={16} className="text-yellow-500" />;
    }
    if (action.includes('termin') || action.includes('clotur')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <X size={16} className="text-red-500" />;
    }
    if (action.includes('photo')) {
      return <Camera size={16} className="text-purple-500" />;
    }
    if (action.includes('modif')) {
      return <Edit size={16} className="text-warning" />;
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
 * Generer l'historique a partir des donnees de l'intervention
 */
function generateHistoryFromIntervention(intervention: Intervention): InterventionHistoryEntry[] {
  const history: InterventionHistoryEntry[] = [];

  // Creation de l'intervention
  history.push({
    id: 'created',
    timestamp: intervention.created_at,
    action: 'Intervention creee',
    user_name: intervention.created_by,
    details: `Titre: ${intervention.titre}`,
  });

  // Planification
  if (intervention.date_prevue) {
    history.push({
      id: 'planned',
      timestamp: intervention.updated_at || intervention.created_at,
      action: 'Intervention planifiee',
      details: `Prevue le ${new Date(intervention.date_prevue).toLocaleDateString('fr-FR')}${intervention.intervenant_nom ? ` - ${intervention.intervenant_nom}` : ''}`,
    });
  }

  // Arrivee sur site
  if (intervention.date_arrivee) {
    history.push({
      id: 'arrival',
      timestamp: intervention.date_arrivee,
      action: 'Arrivee sur site',
      user_name: intervention.intervenant_nom,
    });
  }

  // Debut intervention
  if (intervention.date_debut_intervention) {
    history.push({
      id: 'started',
      timestamp: intervention.date_debut_intervention,
      action: 'Intervention demarree',
      user_name: intervention.intervenant_nom,
    });
  }

  // Photos ajoutees
  if (intervention.photos && intervention.photos.length > 0) {
    history.push({
      id: 'photos',
      timestamp: intervention.date_fin_intervention || intervention.updated_at || intervention.created_at,
      action: 'Photos ajoutees',
      details: `${intervention.photos.length} photo(s) ajoutee(s)`,
    });
  }

  // Fin intervention
  if (intervention.date_fin_intervention) {
    history.push({
      id: 'completed',
      timestamp: intervention.date_fin_intervention,
      action: 'Intervention terminee',
      user_name: intervention.intervenant_nom,
      details: intervention.commentaire_cloture?.substring(0, 100),
    });
  }

  // Historique fourni par l'API
  if (intervention.history && intervention.history.length > 0) {
    history.push(...intervention.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default InterventionHistoryTab;
