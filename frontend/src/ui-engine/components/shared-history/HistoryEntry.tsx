/**
 * AZALSCORE - Shared History Component - HistoryEntry
 * ====================================================
 * Composant partagé pour afficher une entrée de timeline.
 * Réutilisable dans tous les onglets historique de l'application.
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  Plus, Trash2, Eye, Download, Upload, Check, X,
  RefreshCw, Settings, Send, UserPlus, UserMinus
} from 'lucide-react';
import { formatDateTime } from '@/utils/formatters';

/**
 * Types d'action pour le mapping automatique des icônes
 */
export type HistoryActionType =
  | 'create' | 'update' | 'delete'
  | 'view' | 'download' | 'upload'
  | 'validate' | 'reject' | 'convert'
  | 'send' | 'refresh' | 'settings'
  | 'user_add' | 'user_remove'
  | 'custom';

/**
 * Interface d'une entrée d'historique
 */
export interface HistoryEntryData {
  id: string;
  timestamp: string;
  action: string;
  action_type?: HistoryActionType;
  user_name?: string;
  user_id?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
  field_name?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Props du composant HistoryEntry
 */
export interface HistoryEntryProps {
  entry: HistoryEntryData;
  isFirst?: boolean;
  isLast?: boolean;
  showUser?: boolean;
  showChange?: boolean;
  onClick?: (entry: HistoryEntryData) => void;
  className?: string;
}

/**
 * Détermine l'icône en fonction du type d'action ou du texte
 */
function getActionIcon(entry: HistoryEntryData): React.ReactNode {
  // Si un type explicite est fourni
  if (entry.action_type) {
    const iconMap: Record<HistoryActionType, React.ReactNode> = {
      create: <Plus size={16} className="text-success" />,
      update: <Edit size={16} className="text-warning" />,
      delete: <Trash2 size={16} className="text-danger" />,
      view: <Eye size={16} className="text-blue" />,
      download: <Download size={16} className="text-primary" />,
      upload: <Upload size={16} className="text-primary" />,
      validate: <Check size={16} className="text-success" />,
      reject: <X size={16} className="text-danger" />,
      convert: <ArrowRight size={16} className="text-success" />,
      send: <Send size={16} className="text-blue" />,
      refresh: <RefreshCw size={16} className="text-muted" />,
      settings: <Settings size={16} className="text-muted" />,
      user_add: <UserPlus size={16} className="text-success" />,
      user_remove: <UserMinus size={16} className="text-danger" />,
      custom: <Clock size={16} className="text-muted" />,
    };
    return iconMap[entry.action_type] || <Clock size={16} className="text-muted" />;
  }

  // Sinon, détecter basé sur le texte de l'action
  const action = entry.action.toLowerCase();

  if (action.includes('créé') || action.includes('création') || action.includes('ajout')) {
    return <Plus size={16} className="text-success" />;
  }
  if (action.includes('converti') || action.includes('validation') || action.includes('validé')) {
    return <Check size={16} className="text-success" />;
  }
  if (action.includes('modifié') || action.includes('modification') || action.includes('mis à jour')) {
    return <Edit size={16} className="text-warning" />;
  }
  if (action.includes('supprim') || action.includes('annul')) {
    return <Trash2 size={16} className="text-danger" />;
  }
  if (action.includes('rejet') || action.includes('refus')) {
    return <X size={16} className="text-danger" />;
  }
  if (action.includes('envoy') || action.includes('email') || action.includes('notif')) {
    return <Send size={16} className="text-blue" />;
  }
  if (action.includes('télécharg') || action.includes('export')) {
    return <Download size={16} className="text-primary" />;
  }
  if (action.includes('import') || action.includes('upload')) {
    return <Upload size={16} className="text-primary" />;
  }
  if (action.includes('document') || action.includes('fichier') || action.includes('pièce')) {
    return <FileText size={16} className="text-primary" />;
  }

  return <Clock size={16} className="text-muted" />;
}

/**
 * HistoryEntry - Composant d'affichage d'une entrée de timeline
 */
export const HistoryEntry: React.FC<HistoryEntryProps> = ({
  entry,
  isFirst = false,
  isLast = false,
  showUser = true,
  showChange = true,
  onClick,
  className = '',
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(entry);
    }
  };

  return (
    <div
      className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={handleClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="azals-timeline__icon">
        {getActionIcon(entry)}
      </div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {showUser && entry.user_name && (
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
        {showChange && entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            {entry.field_name && (
              <span className="text-muted mr-2">{entry.field_name}:</span>
            )}
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2 inline" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Composant pour afficher une timeline complète
 */
export interface HistoryTimelineProps {
  entries: HistoryEntryData[];
  onEntryClick?: (entry: HistoryEntryData) => void;
  showUser?: boolean;
  showChange?: boolean;
  emptyMessage?: string;
  maxItems?: number;
  className?: string;
}

export const HistoryTimeline: React.FC<HistoryTimelineProps> = ({
  entries,
  onEntryClick,
  showUser = true,
  showChange = true,
  emptyMessage = 'Aucun historique disponible',
  maxItems,
  className = '',
}) => {
  if (entries.length === 0) {
    return (
      <div className={`azals-empty azals-empty--sm ${className}`}>
        <Clock size={32} className="text-muted" />
        <p className="text-muted">{emptyMessage}</p>
      </div>
    );
  }

  const displayedEntries = maxItems ? entries.slice(0, maxItems) : entries;

  return (
    <div className={`azals-timeline ${className}`}>
      {displayedEntries.map((entry, index) => (
        <HistoryEntry
          key={entry.id}
          entry={entry}
          isFirst={index === 0}
          isLast={index === displayedEntries.length - 1}
          showUser={showUser}
          showChange={showChange}
          onClick={onEntryClick}
        />
      ))}
    </div>
  );
};

/**
 * Hook utilitaire pour trier l'historique par date décroissante
 */
export function useSortedHistory(entries: HistoryEntryData[]): HistoryEntryData[] {
  return [...entries].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default HistoryEntry;
