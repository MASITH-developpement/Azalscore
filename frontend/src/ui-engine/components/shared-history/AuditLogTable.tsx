/**
 * AZALSCORE - Shared History Component - AuditLogTable
 * =====================================================
 * Composant partagé pour afficher un tableau d'audit détaillé.
 * Réutilisable dans tous les onglets historique de l'application.
 */

import React, { useState } from 'react';
import { ArrowRight, ChevronDown, ChevronUp, Filter, Download } from 'lucide-react';
import { Button } from '@ui/actions';
import { formatDateTime } from '@/utils/formatters';
import type { HistoryEntryData } from './HistoryEntry';

/**
 * Props du composant AuditLogTable
 */
export interface AuditLogTableProps {
  entries: HistoryEntryData[];
  showFilters?: boolean;
  showExport?: boolean;
  onExport?: (entries: HistoryEntryData[]) => void;
  pageSize?: number;
  className?: string;
}

/**
 * AuditLogTable - Tableau d'audit détaillé avec pagination et filtres
 */
export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  entries,
  showFilters = false,
  showExport = false,
  onExport,
  pageSize = 10,
  className = '',
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<'timestamp' | 'action' | 'user_name'>('timestamp');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [filterUser, setFilterUser] = useState<string>('');
  const [filterAction, setFilterAction] = useState<string>('');

  // Filtrer les entrées
  const filteredEntries = entries.filter(entry => {
    if (filterUser && entry.user_name && !entry.user_name.toLowerCase().includes(filterUser.toLowerCase())) {
      return false;
    }
    if (filterAction && !entry.action.toLowerCase().includes(filterAction.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Trier les entrées
  const sortedEntries = [...filteredEntries].sort((a, b) => {
    let comparison = 0;
    if (sortField === 'timestamp') {
      comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
    } else if (sortField === 'action') {
      comparison = a.action.localeCompare(b.action);
    } else if (sortField === 'user_name') {
      comparison = (a.user_name || '').localeCompare(b.user_name || '');
    }
    return sortDir === 'asc' ? comparison : -comparison;
  });

  // Paginer
  const totalPages = Math.ceil(sortedEntries.length / pageSize);
  const paginatedEntries = sortedEntries.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Extraire les utilisateurs uniques pour le filtre
  const uniqueUsers = [...new Set(entries.map(e => e.user_name).filter(Boolean))];

  const handleSort = (field: 'timestamp' | 'action' | 'user_name') => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortField !== field) return null;
    return sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  return (
    <div className={className}>
      {/* Filtres et actions */}
      {(showFilters || showExport) && (
        <div className="flex justify-between items-center mb-4">
          {showFilters && (
            <div className="flex gap-2">
              <div className="flex items-center gap-2">
                <Filter size={16} className="text-muted" />
                <input
                  type="text"
                  placeholder="Filtrer par action..."
                  value={filterAction}
                  onChange={(e) => setFilterAction(e.target.value)}
                  className="azals-input azals-input--sm w-48"
                />
              </div>
              {uniqueUsers.length > 0 && (
                <select
                  value={filterUser}
                  onChange={(e) => setFilterUser(e.target.value)}
                  className="azals-select azals-select--sm w-40"
                >
                  <option value="">Tous les utilisateurs</option>
                  {uniqueUsers.map(user => (
                    <option key={user} value={user}>{user}</option>
                  ))}
                </select>
              )}
            </div>
          )}
          {showExport && onExport && (
            <Button
              size="sm"
              variant="secondary"
              leftIcon={<Download size={14} />}
              onClick={() => onExport(filteredEntries)}
            >
              Exporter
            </Button>
          )}
        </div>
      )}

      {/* Tableau */}
      <table className="azals-table azals-table--simple azals-table--compact">
        <thead>
          <tr>
            <th
              onClick={() => handleSort('timestamp')}
              className="cursor-pointer"
            >
              <span className="flex items-center gap-1">
                Date/Heure
                <SortIcon field="timestamp" />
              </span>
            </th>
            <th
              onClick={() => handleSort('action')}
              className="cursor-pointer"
            >
              <span className="flex items-center gap-1">
                Action
                <SortIcon field="action" />
              </span>
            </th>
            <th
              onClick={() => handleSort('user_name')}
              className="cursor-pointer"
            >
              <span className="flex items-center gap-1">
                Utilisateur
                <SortIcon field="user_name" />
              </span>
            </th>
            <th>Détails</th>
          </tr>
        </thead>
        <tbody>
          {paginatedEntries.length === 0 ? (
            <tr>
              <td colSpan={4} className="text-center text-muted py-8">
                Aucune entrée d'audit
              </td>
            </tr>
          ) : (
            paginatedEntries.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm whitespace-nowrap">
                  {formatDateTime(entry.timestamp)}
                </td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Système'}</td>
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
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center mt-4">
          <span className="text-sm text-muted">
            {filteredEntries.length} entrée(s) - Page {currentPage}/{totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            >
              Précédent
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            >
              Suivant
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogTable;
