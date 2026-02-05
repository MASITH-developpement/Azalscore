/**
 * AZALSCORE - Shared Documents Component - DocumentList
 * ======================================================
 * Composant partagé pour afficher une liste de documents.
 * Réutilisable dans tous les onglets documents de l'application.
 */

import React, { useState, useMemo } from 'react';
import { FileText, Grid, List, Search, Upload, Filter } from 'lucide-react';
import { Button } from '@ui/actions';
import { DocumentCard, type DocumentData, type DocumentStatus } from './DocumentCard';

/**
 * Modes d'affichage
 */
export type ViewMode = 'grid' | 'list';

/**
 * Props du composant DocumentList
 */
export interface DocumentListProps {
  documents: DocumentData[];
  onView?: (doc: DocumentData) => void;
  onDownload?: (doc: DocumentData) => void;
  onDelete?: (doc: DocumentData) => void;
  onOpen?: (doc: DocumentData) => void;
  onUpload?: () => void;
  viewMode?: ViewMode;
  showViewToggle?: boolean;
  showSearch?: boolean;
  showUpload?: boolean;
  showFilters?: boolean;
  emptyMessage?: string;
  className?: string;
}

/**
 * DocumentList - Composant d'affichage d'une liste de documents
 */
export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onView,
  onDownload,
  onDelete,
  onOpen,
  onUpload,
  viewMode: initialViewMode = 'grid',
  showViewToggle = true,
  showSearch = true,
  showUpload = true,
  showFilters = false,
  emptyMessage = 'Aucun document',
  className = '',
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | ''>('');

  // Filtrer les documents
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      // Filtre de recherche
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesName = doc.name.toLowerCase().includes(query);
        const matchesDescription = doc.description?.toLowerCase().includes(query);
        if (!matchesName && !matchesDescription) return false;
      }

      // Filtre de statut
      if (statusFilter && doc.status !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [documents, searchQuery, statusFilter]);

  // Extraire les statuts uniques
  const uniqueStatuses = useMemo(() => {
    return [...new Set(documents.map(d => d.status).filter(Boolean))] as DocumentStatus[];
  }, [documents]);

  return (
    <div className={className}>
      {/* Barre d'outils */}
      <div className="flex justify-between items-center mb-4 gap-4">
        <div className="flex gap-2 flex-1">
          {showSearch && (
            <div className="relative flex-1 max-w-xs">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="azals-input azals-input--sm pl-9 w-full"
              />
            </div>
          )}
          {showFilters && uniqueStatuses.length > 1 && (
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-muted" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as DocumentStatus | '')}
                className="azals-select azals-select--sm"
              >
                <option value="">Tous les statuts</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex gap-2">
          {showViewToggle && (
            <div className="azals-btn-group">
              <Button
                size="sm"
                variant={viewMode === 'grid' ? 'primary' : 'secondary'}
                onClick={() => setViewMode('grid')}
              >
                <Grid size={14} />
              </Button>
              <Button
                size="sm"
                variant={viewMode === 'list' ? 'primary' : 'secondary'}
                onClick={() => setViewMode('list')}
              >
                <List size={14} />
              </Button>
            </div>
          )}
          {showUpload && onUpload && (
            <Button size="sm" leftIcon={<Upload size={14} />} onClick={onUpload}>
              Ajouter
            </Button>
          )}
        </div>
      </div>

      {/* Liste de documents */}
      {filteredDocuments.length === 0 ? (
        <div className="azals-empty azals-empty--md">
          <FileText size={48} className="text-muted" />
          <p className="text-muted">{emptyMessage}</p>
          {onUpload && (
            <Button
              variant="secondary"
              leftIcon={<Upload size={16} />}
              onClick={onUpload}
              className="mt-4"
            >
              Ajouter un document
            </Button>
          )}
        </div>
      ) : (
        <div className={viewMode === 'grid' ? 'azals-document-grid' : 'azals-document-list'}>
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onView={onView}
              onDownload={onDownload}
              onDelete={onDelete}
              onOpen={onOpen}
              compact={viewMode === 'list'}
            />
          ))}
        </div>
      )}

      {/* Compteur */}
      {filteredDocuments.length > 0 && (
        <div className="text-sm text-muted mt-4">
          {filteredDocuments.length} document(s)
          {searchQuery && ` trouvé(s) pour "${searchQuery}"`}
        </div>
      )}
    </div>
  );
};

export default DocumentList;
