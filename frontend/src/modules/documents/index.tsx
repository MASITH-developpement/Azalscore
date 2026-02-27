/**
 * AZALSCORE Module - DOCUMENTS (GED)
 * ===================================
 * Interface de Gestion Electronique de Documents
 */

import React, { useState, useCallback } from 'react';
import {
  FileText, Folder, FolderPlus, Upload, Download, Trash2,
  Share2, Lock, Unlock, Eye, Search, Grid, List,
  ChevronRight, MoreVertical, Clock, HardDrive
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid as GridLayout } from '@ui/layout';
import { KPICard } from '@ui/dashboards';
import { DataTable } from '@ui/tables';
import { Badge } from '@ui/simple';
import { Input, Modal } from '@ui/forms';
import { formatDate, formatFileSize } from '@/utils/formatters';
import type { TableColumn, DashboardKPI } from '@/types';

import {
  useDocuments,
  useFolders,
  useDocumentStats,
  useUploadDocument,
  useDeleteDocument,
  useCreateFolder,
  useLockDocument,
  useUnlockDocument,
} from './hooks';
import type { Document, Folder as FolderType, DocumentStatus, FileCategory } from './types';
import { DOCUMENT_STATUS_CONFIG, FILE_CATEGORY_CONFIG } from './types';

// ============================================================================
// HELPERS
// ============================================================================

const formatFileSizeLocal = (bytes: number): string => {
  if (typeof formatFileSize === 'function') return formatFileSize(bytes);
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// ============================================================================
// COMPONENTS
// ============================================================================

const StatusBadge: React.FC<{ status: DocumentStatus }> = ({ status }) => {
  const config = DOCUMENT_STATUS_CONFIG[status];
  const variant = config?.color === 'green' ? 'success' : config?.color === 'red' ? 'destructive' : 'default';
  return <Badge variant={variant}>{config?.label || status}</Badge>;
};

const CategoryIcon: React.FC<{ category: FileCategory }> = ({ category }) => {
  const config = FILE_CATEGORY_CONFIG[category];
  return (
    <span className={`text-${config?.color || 'gray'}-500`}>
      <FileText size={16} />
    </span>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const DocumentsModule: React.FC = () => {
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  const { data: stats } = useDocumentStats();
  const { data: folders } = useFolders({ parent_id: currentFolderId });
  const { data: documents, isLoading, refetch } = useDocuments({
    folder_id: currentFolderId,
    search: searchQuery || undefined,
    page,
    page_size: pageSize,
  });

  const uploadDocument = useUploadDocument();
  const deleteDocument = useDeleteDocument();
  const createFolder = useCreateFolder();
  const lockDocument = useLockDocument();
  const unlockDocument = useUnlockDocument();

  const [folderName, setFolderName] = useState('');

  const handleUpload = useCallback(async (files: FileList) => {
    for (const file of Array.from(files)) {
      await uploadDocument.mutateAsync({ file, data: { folder_id: currentFolderId } });
    }
    setShowUploadModal(false);
  }, [uploadDocument, currentFolderId]);

  const handleCreateFolder = useCallback(() => {
    if (folderName.trim()) {
      createFolder.mutate({ name: folderName, parent_id: currentFolderId });
      setFolderName('');
      setShowFolderModal(false);
    }
  }, [createFolder, folderName, currentFolderId]);

  const kpis: DashboardKPI[] = [
    {
      id: 'total',
      label: 'Documents',
      value: stats?.total_documents || 0,
      icon: <FileText size={20} />,
      variant: 'info',
    },
    {
      id: 'folders',
      label: 'Dossiers',
      value: stats?.total_folders || 0,
      icon: <Folder size={20} />,
      variant: 'default',
    },
    {
      id: 'size',
      label: 'Espace utilise',
      value: formatFileSizeLocal(stats?.total_size || 0),
      icon: <HardDrive size={20} />,
      variant: 'warning',
    },
    {
      id: 'shared',
      label: 'Partages',
      value: stats?.shared_documents || 0,
      icon: <Share2 size={20} />,
      variant: 'success',
    },
  ];

  const columns: TableColumn<Document>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      render: (_, row): React.ReactNode => (
        <div className="flex items-center gap-2">
          <CategoryIcon category={row.file_category} />
          <div>
            <div className="font-medium">{row.name}</div>
            <div className="text-xs text-gray-500">{row.file_name}</div>
          </div>
          {row.is_locked && <Lock size={14} className="text-orange-500" />}
        </div>
      ),
    },
    {
      id: 'size',
      header: 'Taille',
      accessor: 'file_size',
      render: (v): React.ReactNode => formatFileSizeLocal(v as number),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => <StatusBadge status={v as DocumentStatus} />,
    },
    {
      id: 'updated_at',
      header: 'Modifie',
      accessor: 'updated_at',
      render: (v): React.ReactNode => formatDate(v as string),
    },
    {
      id: 'actions',
      header: '',
      accessor: 'id',
      width: 120,
      render: (_, row): React.ReactNode => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => setSelectedDocument(row)}>
            <Eye size={14} />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { window.open(row.download_url); }}>
            <Download size={14} />
          </Button>
          {row.is_locked ? (
            <Button size="sm" variant="ghost" onClick={() => unlockDocument.mutate(row.id)}>
              <Unlock size={14} />
            </Button>
          ) : (
            <Button size="sm" variant="ghost" onClick={() => lockDocument.mutate(row.id)}>
              <Lock size={14} />
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={() => deleteDocument.mutate(row.id)}>
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ];

  const folderColumns: TableColumn<FolderType>[] = [
    {
      id: 'name',
      header: 'Dossier',
      accessor: 'name',
      render: (_, row): React.ReactNode => (
        <button
          className="flex items-center gap-2 text-left hover:text-primary"
          onClick={() => setCurrentFolderId(row.id)}
        >
          <Folder size={18} className="text-yellow-500" />
          <span className="font-medium">{row.name}</span>
          <ChevronRight size={14} className="text-gray-400" />
        </button>
      ),
    },
    {
      id: 'items',
      header: 'Contenu',
      accessor: 'document_count',
      render: (_, row): React.ReactNode => (
        <span className="text-sm text-gray-500">
          {row.subfolder_count} dossiers, {row.document_count} fichiers
        </span>
      ),
    },
    {
      id: 'size',
      header: 'Taille',
      accessor: 'total_size',
      render: (v): React.ReactNode => formatFileSizeLocal(v as number),
    },
    {
      id: 'updated_at',
      header: 'Modifie',
      accessor: 'updated_at',
      render: (v): React.ReactNode => formatDate(v as string),
    },
  ];

  return (
    <PageWrapper
      title="Documents"
      subtitle="Gestion Electronique de Documents"
      actions={
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowFolderModal(true)}>
            <FolderPlus size={16} className="mr-2" />
            Nouveau dossier
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload size={16} className="mr-2" />
            Importer
          </Button>
        </div>
      }
    >
      {/* KPIs */}
      <GridLayout cols={4} gap="md" className="mb-6">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </GridLayout>

      {/* Breadcrumb */}
      {currentFolderId && (
        <div className="flex items-center gap-2 mb-4 text-sm">
          <button className="text-primary hover:underline" onClick={() => setCurrentFolderId(undefined)}>
            Racine
          </button>
          <ChevronRight size={14} className="text-gray-400" />
          <span className="text-gray-600">Dossier actuel</span>
        </div>
      )}

      {/* Toolbar */}
      <Card className="mb-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher des documents..."
              className="azals-input pl-10 w-full"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex gap-1 border rounded p-1">
            <button
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-100' : ''}`}
              onClick={() => setViewMode('list')}
            >
              <List size={16} />
            </button>
            <button
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-100' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              <Grid size={16} />
            </button>
          </div>
        </div>
      </Card>

      {/* Folders */}
      {folders?.items && folders.items.length > 0 && (
        <Card title="Dossiers" className="mb-4" noPadding>
          <DataTable
            columns={folderColumns}
            data={folders.items}
            keyField="id"
            emptyMessage="Aucun dossier"
          />
        </Card>
      )}

      {/* Documents */}
      <Card title="Fichiers" noPadding>
        <DataTable
          columns={columns}
          data={documents?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: documents?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={() => { refetch(); }}
          emptyMessage="Aucun document"
        />
      </Card>

      {/* Upload Modal */}
      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Importer des documents">
        <div className="space-y-4">
          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <Upload size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-4">Glissez vos fichiers ici ou</p>
            <input
              type="file"
              multiple
              className="hidden"
              id="file-upload"
              onChange={(e) => e.target.files && handleUpload(e.target.files)}
            />
            <label htmlFor="file-upload" className="inline-block">
              <span className="azals-btn azals-btn--primary cursor-pointer">Parcourir</span>
            </label>
          </div>
        </div>
      </Modal>

      {/* Folder Modal */}
      <Modal isOpen={showFolderModal} onClose={() => setShowFolderModal(false)} title="Nouveau dossier">
        <div className="space-y-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium">Nom du dossier</label>
            <input
              type="text"
              className="azals-input w-full"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="Mon dossier"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowFolderModal(false)}>Annuler</Button>
            <Button onClick={handleCreateFolder}>Creer</Button>
          </div>
        </div>
      </Modal>

      {/* Document Preview Modal */}
      <Modal
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        title={selectedDocument?.name || 'Document'}
      >
        {selectedDocument && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Fichier:</span>
                <span className="ml-2">{selectedDocument.file_name}</span>
              </div>
              <div>
                <span className="text-gray-500">Taille:</span>
                <span className="ml-2">{formatFileSizeLocal(selectedDocument.file_size)}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-2">{selectedDocument.mime_type}</span>
              </div>
              <div>
                <span className="text-gray-500">Version:</span>
                <span className="ml-2">{selectedDocument.version}</span>
              </div>
              <div>
                <span className="text-gray-500">Cree le:</span>
                <span className="ml-2">{formatDate(selectedDocument.created_at)}</span>
              </div>
              <div>
                <span className="text-gray-500">Modifie le:</span>
                <span className="ml-2">{formatDate(selectedDocument.updated_at)}</span>
              </div>
            </div>

            {selectedDocument.tags && selectedDocument.tags.length > 0 && (
              <div>
                <span className="text-gray-500 text-sm">Tags:</span>
                <div className="flex gap-1 mt-1">
                  {selectedDocument.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" size="sm">{tag}</Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="secondary" onClick={() => { window.open(selectedDocument.download_url); }}>
                <Download size={16} className="mr-2" />
                Telecharger
              </Button>
              <Button variant="secondary" onClick={() => setSelectedDocument(null)}>
                Fermer
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </PageWrapper>
  );
};

export default DocumentsModule;
