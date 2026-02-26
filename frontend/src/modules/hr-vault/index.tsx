/**
 * AZALSCORE Module - HR Vault (Coffre-fort RH)
 * ==============================================
 * Module de gestion securisee des documents employes
 *
 * Fonctionnalites:
 * - Stockage chiffre des documents
 * - Categories personnalisables
 * - Signature electronique
 * - Conformite RGPD
 * - Historique des acces
 * - Dashboard RH
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import {
  FileText, Download, Upload, Trash2, Eye, PenTool, Shield,
  Clock, AlertTriangle, Search, Filter, FolderOpen, Users,
  Lock, Archive, FileCheck, ArrowLeft, MoreVertical, RefreshCw,
  Calendar, HardDrive, Bell, CheckCircle, XCircle
} from 'lucide-react';
import { Button, Modal, ConfirmDialog } from '@ui/actions';
import { StatCard, ProgressBar } from '@ui/dashboards';
import { Input, Select, TextArea } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { formatDate, formatDateTime } from '@/utils/formatters';
import { hrVaultApi } from './api';
import {
  DOCUMENT_TYPE_CONFIG,
  DOCUMENT_STATUS_CONFIG,
  SIGNATURE_STATUS_CONFIG,
  GDPR_TYPE_CONFIG,
  GDPR_STATUS_CONFIG,
  formatFileSize,
  getDocumentTypeLabel,
  isDocumentExpiring,
  needsSignature,
} from './types';
import type {
  VaultDocument,
  VaultDocumentType,
  VaultDocumentStatus,
  VaultCategory,
  VaultDashboardStats,
  VaultGDPRRequest,
  VaultAccessLog,
  VaultAlert,
  VaultDocumentFilters,
} from './types';
import type { TableColumn } from '@/types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string; icon?: React.ReactNode; badge?: number }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.icon && <span className="mr-2">{tab.icon}</span>}
        {tab.label}
        {tab.badge !== undefined && tab.badge > 0 && (
          <span className="ml-2 azals-badge azals-badge--red azals-badge--sm">{tab.badge}</span>
        )}
      </button>
    ))}
  </nav>
);

// ============================================================================
// API HOOKS
// ============================================================================

const useDashboardStats = () => {
  return useQuery({
    queryKey: ['hr-vault', 'dashboard', 'stats'],
    queryFn: async () => {
      const response = await hrVaultApi.getDashboardStats();
      return response.data;
    },
  });
};

const useDocuments = (filters: VaultDocumentFilters, page: number, pageSize: number) => {
  return useQuery({
    queryKey: ['hr-vault', 'documents', filters, page, pageSize],
    queryFn: async () => {
      const response = await hrVaultApi.listDocuments(filters, page, pageSize);
      return response.data;
    },
  });
};

const useCategories = () => {
  return useQuery({
    queryKey: ['hr-vault', 'categories'],
    queryFn: async () => {
      const response = await hrVaultApi.listCategories();
      return response.data;
    },
  });
};

const useGDPRRequests = (status?: string) => {
  return useQuery({
    queryKey: ['hr-vault', 'gdpr', status],
    queryFn: async () => {
      const response = await hrVaultApi.listGDPRRequests(undefined, undefined, status);
      return response.data;
    },
  });
};

const useAlerts = (unreadOnly = false) => {
  return useQuery({
    queryKey: ['hr-vault', 'alerts', unreadOnly],
    queryFn: async () => {
      const response = await hrVaultApi.listAlerts(unreadOnly);
      return response.data;
    },
  });
};

const useExpiringDocuments = () => {
  return useQuery({
    queryKey: ['hr-vault', 'expiring'],
    queryFn: async () => {
      const response = await hrVaultApi.getExpiringDocuments(30);
      return response.data;
    },
  });
};

const usePendingSignatures = () => {
  return useQuery({
    queryKey: ['hr-vault', 'pending-signatures'],
    queryFn: async () => {
      const response = await hrVaultApi.getPendingSignatures();
      return response.data;
    },
  });
};

const useAccessLogs = (documentId?: string) => {
  return useQuery({
    queryKey: ['hr-vault', 'access-logs', documentId],
    queryFn: async () => {
      const response = await hrVaultApi.listAccessLogs(documentId);
      return response.data;
    },
    enabled: !!documentId,
  });
};

// ============================================================================
// DASHBOARD VIEW
// ============================================================================

const DashboardView: React.FC = () => {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: expiringDocs = [] } = useExpiringDocuments();
  const { data: pendingSignatures = [] } = usePendingSignatures();
  const { data: alerts = [] } = useAlerts(true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="azals-spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <Grid cols={4}>
        <StatCard
          title="Documents totaux"
          value={String(stats?.total_documents || 0)}
          icon={<FileText size={24} />}
          variant="default"
        />
        <StatCard
          title="Stockage utilise"
          value={formatFileSize(stats?.total_storage_bytes || 0)}
          icon={<HardDrive size={24} />}
          variant="default"
        />
        <StatCard
          title="Signatures en attente"
          value={String(stats?.pending_signatures || 0)}
          icon={<PenTool size={24} />}
          variant={stats?.pending_signatures ? 'warning' : 'success'}
        />
        <StatCard
          title="Demandes RGPD"
          value={String(stats?.gdpr_requests_pending || 0)}
          icon={<Shield size={24} />}
          variant={stats?.gdpr_requests_pending ? 'warning' : 'success'}
        />
      </Grid>

      <Grid cols={2}>
        {/* Documents expirant */}
        <Card title="Documents expirant prochainement" icon={<Clock size={18} />}>
          {expiringDocs.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Aucun document expirant dans les 30 jours</p>
          ) : (
            <div className="space-y-2">
              {expiringDocs.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={16} className="text-orange-500" />
                    <span className="font-medium">{doc.title}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    Expire le {formatDate(doc.expiry_date || '')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Signatures en attente */}
        <Card title="Signatures en attente" icon={<PenTool size={18} />}>
          {pendingSignatures.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Aucune signature en attente</p>
          ) : (
            <div className="space-y-2">
              {pendingSignatures.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                  <div className="flex items-center gap-2">
                    <FileCheck size={16} className="text-blue-500" />
                    <span className="font-medium">{doc.title}</span>
                  </div>
                  <Badge color={SIGNATURE_STATUS_CONFIG[doc.signature_status].color}>
                    {SIGNATURE_STATUS_CONFIG[doc.signature_status].label}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </Grid>

      {/* Alertes */}
      {alerts.length > 0 && (
        <Card title="Alertes non lues" icon={<Bell size={18} />}>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`flex items-center justify-between p-3 rounded ${
                  alert.severity === 'CRITICAL' ? 'bg-red-50' :
                  alert.severity === 'WARNING' ? 'bg-orange-50' : 'bg-blue-50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle
                    size={16}
                    className={
                      alert.severity === 'CRITICAL' ? 'text-red-500' :
                      alert.severity === 'WARNING' ? 'text-orange-500' : 'text-blue-500'
                    }
                  />
                  <div>
                    <div className="font-medium">{alert.title}</div>
                    {alert.description && (
                      <div className="text-sm text-gray-500">{alert.description}</div>
                    )}
                  </div>
                </div>
                <span className="text-sm text-gray-500">{formatDate(alert.created_at)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Repartition par type */}
      {stats?.documents_by_type && Object.keys(stats.documents_by_type).length > 0 && (
        <Card title="Repartition par type de document" icon={<FolderOpen size={18} />}>
          <div className="grid grid-cols-4 gap-4">
            {Object.entries(stats.documents_by_type).map(([type, count]) => (
              <div key={type} className="p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">
                  {getDocumentTypeLabel(type as VaultDocumentType)}
                </div>
                <div className="text-2xl font-bold">{count}</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

// ============================================================================
// DOCUMENTS LIST VIEW
// ============================================================================

const DocumentsListView: React.FC = () => {
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
      queryClient.invalidateQueries({ queryKey: ['hr-vault', 'documents'] });
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
            queryClient.invalidateQueries({ queryKey: ['hr-vault', 'documents'] });
          }}
        />
      )}
    </div>
  );
};

// ============================================================================
// UPLOAD DOCUMENT MODAL
// ============================================================================

interface UploadDocumentModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const UploadDocumentModal: React.FC<UploadDocumentModalProps> = ({ onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState<VaultDocumentType>('OTHER');
  const [employeeId, setEmployeeId] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !employeeId) {
      setError('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('document_type', documentType);
      formData.append('employee_id', employeeId);
      if (description) formData.append('description', description);

      await hrVaultApi.uploadDocument(formData);
      onSuccess();
    } catch (err) {
      setError('Erreur lors du depot du document');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const documentTypeOptions = Object.entries(DOCUMENT_TYPE_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <Modal title="Deposer un document" isOpen onClose={onClose} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Fichier *</label>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full border rounded p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Titre *</label>
          <Input
            value={title}
            onChange={setTitle}
            placeholder="Titre du document"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Type de document *</label>
          <Select
            value={documentType}
            onChange={(v) => setDocumentType(v as VaultDocumentType)}
            options={documentTypeOptions}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">ID Employe *</label>
          <Input
            value={employeeId}
            onChange={setEmployeeId}
            placeholder="UUID de l'employe"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <TextArea
            value={description}
            onChange={setDescription}
            placeholder="Description optionnelle"
            rows={3}
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Depot en cours...' : 'Deposer'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================================
// GDPR VIEW
// ============================================================================

const GDPRView: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const { data: requests = [], isLoading, refetch } = useGDPRRequests(statusFilter || undefined);
  const queryClient = useQueryClient();

  const processRequestMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      await hrVaultApi.processGDPRRequest(id, status);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-vault', 'gdpr'] });
    },
  });

  const columns: TableColumn<VaultGDPRRequest>[] = [
    {
      id: 'code',
      header: 'Reference',
      accessor: 'request_code',
      render: (v) => <code className="font-mono">{v as string}</code>,
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'request_type',
      render: (type) => {
        const config = GDPR_TYPE_CONFIG[type as keyof typeof GDPR_TYPE_CONFIG];
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
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (status) => {
        const config = GDPR_STATUS_CONFIG[status as keyof typeof GDPR_STATUS_CONFIG];
        return <Badge color={config?.color || 'gray'}>{config?.label || String(status)}</Badge>;
      },
    },
    {
      id: 'requested_at',
      header: 'Date demande',
      accessor: 'requested_at',
      render: (date) => formatDate(date as string),
    },
    {
      id: 'due_date',
      header: 'Echeance',
      accessor: 'due_date',
      render: (date, row) => {
        const isOverdue = new Date(date as string) < new Date() && row.status === 'PENDING';
        return (
          <span className={isOverdue ? 'text-red-600 font-bold' : ''}>
            {formatDate(date as string)}
          </span>
        );
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'PENDING' && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => processRequestMutation.mutate({ id: row.id, status: 'PROCESSING' })}
            >
              Traiter
            </Button>
          )}
          {row.status === 'PROCESSING' && (
            <Button
              size="sm"
              variant="success"
              onClick={() => processRequestMutation.mutate({ id: row.id, status: 'COMPLETED' })}
            >
              Terminer
            </Button>
          )}
        </div>
      ),
    },
  ];

  const statusOptions = [
    { value: '', label: 'Tous les statuts' },
    ...Object.entries(GDPR_STATUS_CONFIG).map(([value, config]) => ({
      value,
      label: config.label,
    })),
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Shield size={20} />
          Demandes RGPD
        </h3>
        <div className="flex gap-2">
          <Select
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
            options={statusOptions}
            className="w-40"
          />
          <Button variant="secondary" onClick={() => { void refetch(); }}>
            <RefreshCw size={16} />
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={requests}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// ACCESS LOGS VIEW
// ============================================================================

const AccessLogsView: React.FC = () => {
  const [documentId, setDocumentId] = useState<string>('');
  const { data, isLoading } = useAccessLogs(documentId || undefined);

  const columns: TableColumn<VaultAccessLog>[] = [
    {
      id: 'date',
      header: 'Date',
      accessor: 'access_date',
      render: (date) => formatDateTime(date as string),
    },
    {
      id: 'document',
      header: 'Document',
      accessor: 'document_title',
      render: (title) => String(title || '-'),
    },
    {
      id: 'user',
      header: 'Utilisateur',
      accessor: 'accessed_by_name',
      render: (name) => String(name || '-'),
    },
    {
      id: 'role',
      header: 'Role',
      accessor: 'access_role',
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'access_type',
    },
    {
      id: 'ip',
      header: 'IP',
      accessor: 'ip_address',
      render: (ip) => String(ip || '-'),
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (success) =>
        success ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <XCircle size={16} className="text-red-500" />
        ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Eye size={20} />
          Historique des acces
        </h3>
        <div className="w-64">
          <Input
            placeholder="Filtrer par ID document"
            value={documentId}
            onChange={setDocumentId}
          />
        </div>
      </div>
      <DataTable
        columns={columns}
        data={data?.items || []}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// CATEGORIES VIEW
// ============================================================================

const CategoriesView: React.FC = () => {
  const { data: categories = [], isLoading, refetch } = useCategories();
  const queryClient = useQueryClient();

  const deleteCategoryMutation = useMutation({
    mutationFn: async (categoryId: string) => {
      await hrVaultApi.deleteCategory(categoryId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-vault', 'categories'] });
    },
  });

  const columns: TableColumn<VaultCategory>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (v) => <code className="font-mono">{v as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      render: (v) => String(v || '-'),
    },
    {
      id: 'documents',
      header: 'Documents',
      accessor: 'documents_count',
    },
    {
      id: 'retention',
      header: 'Conservation',
      accessor: 'default_retention',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, cat) => (
        <Button
          size="sm"
          variant="danger"
          disabled={cat.documents_count > 0}
          onClick={() => deleteCategoryMutation.mutate(cat.id)}
        >
          <Trash2 size={14} />
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FolderOpen size={20} />
          Categories de documents
        </h3>
        <Button variant="secondary" onClick={() => { void refetch(); }}>
          <RefreshCw size={16} />
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={categories}
        isLoading={isLoading}
        keyField="id"
      />
    </Card>
  );
};

// ============================================================================
// MAIN MODULE
// ============================================================================

type View = 'dashboard' | 'documents' | 'gdpr' | 'access-logs' | 'categories';

const HRVaultModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useDashboardStats();

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <FileText size={16} /> },
    { id: 'documents', label: 'Documents', icon: <FolderOpen size={16} /> },
    { id: 'gdpr', label: 'RGPD', icon: <Shield size={16} />, badge: stats?.gdpr_requests_pending },
    { id: 'access-logs', label: 'Historique', icon: <Eye size={16} /> },
    { id: 'categories', label: 'Categories', icon: <Archive size={16} /> },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'documents':
        return <DocumentsListView />;
      case 'gdpr':
        return <GDPRView />;
      case 'access-logs':
        return <AccessLogsView />;
      case 'categories':
        return <CategoriesView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <PageWrapper
      title="Coffre-fort RH"
      subtitle="Gestion securisee des documents employes"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

// ============================================================================
// DOCUMENT DETAIL VIEW
// ============================================================================

const DocumentDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['hr-vault', 'documents', id],
    queryFn: async () => {
      const response = await hrVaultApi.getDocument(id || '');
      return response.data;
    },
    enabled: !!id,
  });

  const { data: versions = [] } = useQuery({
    queryKey: ['hr-vault', 'documents', id, 'versions'],
    queryFn: async () => {
      const response = await hrVaultApi.getDocumentVersions(id || '');
      return response.data;
    },
    enabled: !!id,
  });

  const { data: accessLogs } = useAccessLogs(id);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="flex items-center justify-center h-64">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (error || !document) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600">Document non trouve</p>
            <Button variant="secondary" onClick={() => navigate('/hr-vault')} className="mt-4">
              <ArrowLeft size={16} className="mr-2" />
              Retour
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const handleDownload = async () => {
    try {
      const response = await hrVaultApi.downloadDocument(document.id);
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.file_name;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (err) {
      console.error('Erreur telechargement:', err);
    }
  };

  return (
    <PageWrapper
      title={document.title}
      subtitle={document.file_name}
    >
      <div className="mb-4 flex gap-2">
        <Button variant="secondary" onClick={() => navigate('/hr-vault')}>
          <ArrowLeft size={16} className="mr-2" />
          Retour
        </Button>
        <Button onClick={handleDownload}>
          <Download size={16} className="mr-2" />
          Telecharger
        </Button>
      </div>

      <Grid cols={3}>
        {/* Informations */}
        <Card title="Informations" className="col-span-2">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <span className="azals-field__label">Type</span>
              <div className="azals-field__value">
                <Badge color={DOCUMENT_TYPE_CONFIG[document.document_type]?.color || 'gray'}>
                  {DOCUMENT_TYPE_CONFIG[document.document_type]?.label || document.document_type}
                </Badge>
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Statut</span>
              <div className="azals-field__value">
                <Badge color={DOCUMENT_STATUS_CONFIG[document.status]?.color || 'gray'}>
                  {DOCUMENT_STATUS_CONFIG[document.status]?.label || document.status}
                </Badge>
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Taille</span>
              <div className="azals-field__value">{formatFileSize(document.file_size)}</div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Chiffrement</span>
              <div className="azals-field__value">
                {document.is_encrypted ? (
                  <span className="text-green-600 flex items-center gap-1">
                    <Lock size={14} /> Chiffre
                  </span>
                ) : (
                  <span className="text-red-600">Non chiffre</span>
                )}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Date du document</span>
              <div className="azals-field__value">
                {document.document_date ? formatDate(document.document_date) : '-'}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Conservation jusqu au</span>
              <div className="azals-field__value">
                {document.retention_end_date ? formatDate(document.retention_end_date) : '-'}
              </div>
            </div>
            {document.description && (
              <div className="azals-field col-span-2">
                <span className="azals-field__label">Description</span>
                <div className="azals-field__value">{document.description}</div>
              </div>
            )}
          </Grid>
        </Card>

        {/* Signature */}
        <Card title="Signature">
          <div className="space-y-4">
            <div className="azals-field">
              <span className="azals-field__label">Statut</span>
              <div className="azals-field__value">
                <Badge color={SIGNATURE_STATUS_CONFIG[document.signature_status]?.color || 'gray'}>
                  {SIGNATURE_STATUS_CONFIG[document.signature_status]?.label}
                </Badge>
              </div>
            </div>
            {document.signed_at && (
              <div className="azals-field">
                <span className="azals-field__label">Signe le</span>
                <div className="azals-field__value">{formatDateTime(document.signed_at)}</div>
              </div>
            )}
            {needsSignature(document) && (
              <Button className="w-full">
                <PenTool size={16} className="mr-2" />
                Demander signature
              </Button>
            )}
          </div>
        </Card>
      </Grid>

      {/* Versions */}
      <Card title="Versions" className="mt-4">
        {versions.length === 0 ? (
          <p className="text-gray-500">Aucune version</p>
        ) : (
          <div className="space-y-2">
            {versions.map((version) => (
              <div key={version.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-4">
                  <span className="font-medium">v{version.version_number}</span>
                  <span>{version.file_name}</span>
                  <span className="text-sm text-gray-500">{formatFileSize(version.file_size)}</span>
                </div>
                <span className="text-sm text-gray-500">{formatDateTime(version.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Historique des acces */}
      <Card title="Historique des acces" className="mt-4">
        {!accessLogs?.items?.length ? (
          <p className="text-gray-500">Aucun acces enregistre</p>
        ) : (
          <div className="space-y-2">
            {accessLogs.items.slice(0, 10).map((log) => (
              <div key={log.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center gap-2">
                  {log.success ? (
                    <CheckCircle size={14} className="text-green-500" />
                  ) : (
                    <XCircle size={14} className="text-red-500" />
                  )}
                  <span>{log.access_type}</span>
                  <span className="text-sm text-gray-500">par {log.accessed_by_name || log.accessed_by}</span>
                </div>
                <span className="text-sm text-gray-500">{formatDateTime(log.access_date)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

const HRVaultRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<HRVaultModule />} />
      <Route path="documents/:id" element={<DocumentDetailView />} />
    </Routes>
  );
};

export default HRVaultRoutes;
