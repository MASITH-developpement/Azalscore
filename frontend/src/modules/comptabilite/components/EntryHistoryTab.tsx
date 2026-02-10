/**
 * AZALSCORE Module - Comptabilite - Entry History Tab
 * Onglet historique de l'ecriture
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight, CheckCircle2,
  XCircle, Plus, BookOpen
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Entry, EntryHistoryEntry } from '../types';
import { ENTRY_STATUS_CONFIG } from '../types';
import { formatDateTime } from '@/utils/formatters';

/**
 * EntryHistoryTab - Historique
 */
export const EntryHistoryTab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const history = generateHistoryFromEntry(entry);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique de l'ecriture" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((item, index) => (
              <HistoryEntryComponent
                key={item.id}
                entry={item}
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

      {/* Journal d'audit (ERP only) */}
      <Card
        title="Journal d'audit"
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
            {history.map((item) => (
              <tr key={item.id}>
                <td className="text-muted text-sm">{formatDateTime(item.timestamp)}</td>
                <td>{item.action}</td>
                <td>{item.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {item.details || '-'}
                  {item.old_value && item.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{item.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{item.new_value}</span>
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
interface HistoryEntryComponentProps {
  entry: EntryHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <Plus size={16} className="text-green-500" />;
    }
    if (action.includes('valid')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('comptabilis') || action.includes('post')) {
      return <BookOpen size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('modif')) {
      return <Edit size={16} className="text-orange-500" />;
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
 * Generer l'historique a partir des donnees de l'ecriture
 */
function generateHistoryFromEntry(entry: Entry): EntryHistoryEntry[] {
  const history: EntryHistoryEntry[] = [];

  // Creation de l'ecriture
  history.push({
    id: 'created',
    timestamp: entry.created_at,
    action: 'Ecriture creee',
    user_name: entry.created_by_name,
    details: `Numero: ${entry.number}`,
  });

  // Validation
  if (entry.validated_at) {
    history.push({
      id: 'validated',
      timestamp: entry.validated_at,
      action: 'Ecriture validee',
      user_name: entry.validated_by_name,
      details: 'L\'ecriture a ete validee et verrouillee',
    });
  }

  // Comptabilisation
  if (entry.posted_at) {
    history.push({
      id: 'posted',
      timestamp: entry.posted_at,
      action: 'Ecriture comptabilisee',
      user_name: entry.posted_by_name,
      details: 'L\'ecriture est definitivement enregistree',
    });
  }

  // Annulation
  if (entry.cancelled_at) {
    history.push({
      id: 'cancelled',
      timestamp: entry.cancelled_at,
      action: 'Ecriture annulee',
      user_name: entry.cancelled_by,
      details: entry.cancelled_reason || 'Annulee par l\'utilisateur',
    });
  }

  // Derniere modification
  if (entry.updated_at && entry.updated_at !== entry.created_at && !entry.validated_at) {
    history.push({
      id: 'updated',
      timestamp: entry.updated_at,
      action: 'Ecriture modifiee',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (entry.history && entry.history.length > 0) {
    history.push(...entry.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default EntryHistoryTab;
