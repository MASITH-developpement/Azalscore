/**
 * AZALSCORE Module - HR Vault - Documents List View
 * Liste des documents avec filtres et actions
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Download, Trash2, Eye, Upload, RefreshCw
} from 'lucide-react';
import { Button, ConfirmDialog } from '@ui/actions';
import { Input, Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { hrVaultApi } from '../api';
import { useDocuments, useCategories, hrVaultKeys } from '../hooks';
import {
  DOCUMENT_TYPE_CONFIG,
  DOCUMENT_STATUS_CONFIG,
  SIGNATURE_STATUS_CONFIG,
  formatFileSize,
} from '../types';
import type {
  VaultDocument,
  VaultDocumentType,
  VaultDocumentStatus,
  VaultDocumentFilters,
} from '../types';
import { Badge } from './LocalComponents';
import { UploadDocumentModal } from './UploadDocumentModal';

export const DocumentsListView: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<VaultDocumentFilters>({});
  const [page, setPage] = useState(1);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<VaultDocument | null>(null);

  const { data, isLoading, error, refetch } = useDocuments(filters, page, 50);
  const { data: categories = [] } = useCategories();

  const deleteDocumentMutation = useMutation({
    mutationFn: async (documentId: string) => {
      await hrVaultApi.deleteDocument(documentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: hrVaultKeys.all });
    },
  });

  const handleDownload = async (doc: VaultDocument) => {
    try {
      const response = await hrVaultApi.downloadDocument(doc.id);
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Erreur telechargement:', err);
    }
  };

  const columns: TableColumn<VaultDocument>[] = [
    {
      id: 'title',
      header: 'Document',
      accessor: 'title',
      render: (_, doc) => (
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-gray-400" />
          <div>
            <div className="font-medium">{doc.title}</div>
            <div className="text-sm text-gray-500">{doc.file_name}</div>
          </div>
        </div>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'document_type',
      render: (type) => {
        const config = DOCUMENT_TYPE_CONFIG[type as VaultDocumentType];
        return <Badge color={config?.color || 'gray'}>{config?.label || String(type)}</Badge>;
      },
    },
    {
      id: 'employee',
      header: 'Employe',
      accessor: 'employee_name',
      render: (name) => String(name || '-'),
    },
    {
      id: 'date',
      header: 'Date document',
      accessor: 'document_date',
      render: (date) => date ? formatDate(date as string) : '-',
    },
    {
      id: 'size',
      header: 'Taille',
      accessor: 'file_size',
      render: (size) => formatFileSize(size as number),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (status) => {
        const config = DOCUMENT_STATUS_CONFIG[status as VaultDocumentStatus];
        return <Badge color={config?.color || 'gray'}>{config?.label || String(status)}</Badge>;
      },
    },
    {
      id: 'signature',
      header: 'Signature',
      accessor: 'signature_status',
      render: (status, doc) => {
        if (status === 'NOT_REQUIRED') return <span className="text-gray-400">-</span>;
        const config = SIGNATURE_STATUS_CONFIG[doc.signature_status];
        return <Badge color={config?.color || 'gray'}>{config?.label}</Badge>;
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, doc) => (
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => navigate(`/hr-vault/documents/${doc.id}`)}
            aria-label="Voir"
          >
            <Eye size={14} />
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleDownload(doc)}
            aria-label="Telecharger"
          >
            <Download size={14} />
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => setSelectedDocument(doc)}
            aria-label="Supprimer"
          >
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ];

  const documentTypeOptions = [
    { value: '', label: 'Tous les types' },
    ...Object.entries(DOCUMENT_TYPE_CONFIG).map(([value, config]) => ({
      value,
      label: config.label,
    })),
  ];

  const statusOptions = [
    { value: '', label: 'Tous les statuts' },
    ...Object.entries(DOCUMENT_STATUS_CONFIG).map(([value, config]) => ({
      value,
      label: config.label,
    })),
  ];

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <Card>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Rechercher..."
              value={filters.search || ''}
              onChange={(v) => setFilters({ ...filters, search: v })}
            />
          </div>
          <div className="w-48">
            <Select
              value={filters.document_type || ''}
              onChange={(v) => setFilters({ ...filters, document_type: v as VaultDocumentType })}
              options={documentTypeOptions}
            />
          </div>
          <div className="w-40">
            <Select
              value={filters.status || ''}
              onChange={(v) => setFilters({ ...filters, status: v as VaultDocumentStatus })}
              options={statusOptions}
            />
          </div>
          <Button variant="secondary" onClick={() => { void refetch(); }}>
            <RefreshCw size={16} />
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload size={16} className="mr-2" />
            Deposer un document
          </Button>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <DataTable
          columns={columns}
          data={data?.items || []}
          isLoading={isLoading}
          keyField="id"
          filterable
          error={error as Error | null}
          onRetry={() => refetch()}
        />

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex justify-center gap-2 mt-4">
            <Button
              variant="secondary"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              Precedent
            </Button>
            <span className="px-4 py-2">
              Page {page} / {data.pages}
            </span>
            <Button
              variant="secondary"
              disabled={page === data.pages}
              onClick={() => setPage(p => p + 1)}
            >
              Suivant
            </Button>
          </div>
        )}
      </Card>

      {/* Modal confirmation suppression */}
      {selectedDocument && (
        <ConfirmDialog
          title="Supprimer le document"
          message={`Etes-vous sur de vouloir supprimer "${selectedDocument.title}" ?`}
          confirmLabel="Supprimer"
          cancelLabel="Annuler"
          variant="danger"
          onConfirm={() => {
            deleteDocumentMutation.mutate(selectedDocument.id);
            setSelectedDocument(null);
          }}
          onCancel={() => setSelectedDocument(null)}
        />
      )}

      {/* Modal upload */}
      {showUploadModal && (
        <UploadDocumentModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            queryClient.invalidateQueries({ queryKey: hrVaultKeys.all });
          }}
        />
      )}
    </div>
  );
};

export default DocumentsListView;
