/**
 * AZALSCORE Module - Qualite - NC History Tab
 * Onglet historique de la non-conformite
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  CheckCircle, AlertTriangle, Search, X
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance, NCHistoryEntry } from '../types';
import { formatDateTime, NC_STATUS_CONFIG } from '../types';

/**
 * NCHistoryTab - Historique
 */
export const NCHistoryTab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  // Generer l'historique combine
  const history = generateHistoryFromNC(nc);

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
  entry: NCHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('ouvert')) {
      return <AlertTriangle size={16} className="text-red-500" />;
    }
    if (action.includes('analyse')) {
      return <Search size={16} className="text-orange-500" />;
    }
    if (action.includes('action') || action.includes('planifi')) {
      return <CheckCircle size={16} className="text-blue-500" />;
    }
    if (action.includes('clotur') || action.includes('ferme')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <X size={16} className="text-gray-500" />;
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
 * Generer l'historique a partir des donnees de la NC
 */
function generateHistoryFromNC(nc: NonConformance): NCHistoryEntry[] {
  const history: NCHistoryEntry[] = [];

  // Creation de la NC
  history.push({
    id: 'created',
    timestamp: nc.created_at,
    action: 'NC ouverte',
    user_name: nc.detected_by_name || nc.created_by,
    details: `Gravite: ${nc.severity} - Type: ${nc.type}`,
  });

  // Passage en analyse (si applicable)
  if (nc.root_cause && nc.status !== 'OPEN') {
    history.push({
      id: 'analysis',
      timestamp: nc.updated_at || nc.created_at,
      action: 'Analyse effectuee',
      details: 'Cause racine identifiee',
    });
  }

  // Action planifiee (si applicable)
  if (nc.corrective_action) {
    history.push({
      id: 'action-planned',
      timestamp: nc.updated_at || nc.created_at,
      action: 'Action corrective definie',
      details: nc.corrective_action.substring(0, 100) + (nc.corrective_action.length > 100 ? '...' : ''),
    });
  }

  // Cloture
  if (nc.closed_date) {
    history.push({
      id: 'closed',
      timestamp: nc.closed_date,
      action: 'NC cloturee',
      details: 'Non-conformite resolue',
    });
  }

  // Historique fourni par l'API
  if (nc.history && nc.history.length > 0) {
    history.push(...nc.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default NCHistoryTab;
