/**
 * Vue Assistante - Dashboard Comptabilité Automatisée
 *
 * Objectif: Centraliser & organiser, JAMAIS comptabiliser
 *
 * INCLUT:
 * - Vue documentaire (factures, notes de frais, devis)
 * - Statuts des documents
 * - Alertes "pièce illisible / info manquante"
 * - Ajout de contexte simple (commentaire, projet)
 *
 * INTERDICTIONS:
 * - Aucun accès bancaire
 * - Aucune validation comptable
 * - Aucun export
 * - Aucune modification d'écriture
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Upload,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Eye,
  Plus,
  Inbox,
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { StatusBadge } from '@ui/dashboards';
import { Modal, Input, TextArea, Select } from '@ui/forms';
import type { TableColumn, PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface DocumentCountsByStatus {
  received: number;
  processing: number;
  analyzed: number;
  pending_validation: number;
  validated: number;
  accounted: number;
  rejected: number;
  error: number;
}

interface DocumentCountsByType {
  invoice_received: number;
  invoice_sent: number;
  expense_note: number;
  credit_note_received: number;
  credit_note_sent: number;
  quote: number;
  purchase_order: number;
  other: number;
}

interface Alert {
  id: string;
  alert_type: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  title: string;
  message: string;
  document_id?: string;
  is_resolved: boolean;
  created_at: string;
}

interface Document {
  id: string;
  document_type: string;
  status: string;
  reference: string | null;
  partner_name: string | null;
  amount_total: number | null;
  document_date: string | null;
  due_date: string | null;
  original_filename: string | null;
  ai_confidence: string | null;
  ai_confidence_score: number | null;
  received_at: string;
}

interface AssistanteDashboardData {
  total_documents: number;
  documents_by_status: DocumentCountsByStatus;
  documents_by_type: DocumentCountsByType;
  recent_documents: Document[];
  alerts: Alert[];
  last_updated: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useAssistanteDashboard = () => {
  return useQuery({
    queryKey: ['accounting', 'assistante', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<AssistanteDashboardData>(
        '/accounting/assistante/dashboard'
      );
      return response.data;
    },
    staleTime: 30000,
  });
};

const useDocuments = (page = 1, pageSize = 20, filters: Record<string, string> = {}) => {
  return useQuery({
    queryKey: ['accounting', 'documents', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...filters,
      });
      const response = await api.get<PaginatedResponse<Document>>(
        `/accounting/assistante/documents?${params}`
      );
      return response.data;
    },
  });
};

const useUploadDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, documentType }: { file: File; documentType: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', documentType);

      const response = await api.post('/accounting/assistante/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

const formatCurrency = (value: number | null) =>
  value !== null
    ? new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
      }).format(value)
    : '-';

const formatDate = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleDateString('fr-FR') : '-';

const getStatusVariant = (
  status: string
): 'success' | 'warning' | 'danger' | 'info' | 'default' => {
  switch (status) {
    case 'ACCOUNTED':
    case 'VALIDATED':
      return 'success';
    case 'PENDING_VALIDATION':
    case 'ANALYZED':
      return 'warning';
    case 'ERROR':
    case 'REJECTED':
      return 'danger';
    case 'PROCESSING':
      return 'info';
    default:
      return 'default';
  }
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    RECEIVED: 'Reçu',
    PROCESSING: 'En traitement',
    ANALYZED: 'Analysé',
    PENDING_VALIDATION: 'À valider',
    VALIDATED: 'Validé',
    ACCOUNTED: 'Comptabilisé',
    REJECTED: 'Rejeté',
    ERROR: 'Erreur',
  };
  return labels[status] || status;
};

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    INVOICE_RECEIVED: 'Facture fournisseur',
    INVOICE_SENT: 'Facture client',
    EXPENSE_NOTE: 'Note de frais',
    CREDIT_NOTE_RECEIVED: 'Avoir reçu',
    CREDIT_NOTE_SENT: 'Avoir émis',
    QUOTE: 'Devis',
    PURCHASE_ORDER: 'Bon de commande',
    OTHER: 'Autre',
  };
  return labels[type] || type;
};

// ============================================================
// WIDGETS
// ============================================================

const StatusSummaryWidget: React.FC<{
  counts: DocumentCountsByStatus;
  onFilter: (status: string) => void;
}> = ({ counts, onFilter }) => {
  const items = [
    {
      status: 'RECEIVED',
      label: 'Reçus',
      count: counts.received,
      icon: Inbox,
      color: 'default',
    },
    {
      status: 'PROCESSING',
      label: 'En traitement',
      count: counts.processing,
      icon: Clock,
      color: 'info',
    },
    {
      status: 'PENDING_VALIDATION',
      label: 'À valider',
      count: counts.pending_validation,
      icon: AlertTriangle,
      color: 'warning',
    },
    {
      status: 'ACCOUNTED',
      label: 'Comptabilisés',
      count: counts.accounted,
      icon: CheckCircle,
      color: 'success',
    },
    {
      status: 'ERROR',
      label: 'En erreur',
      count: counts.error,
      icon: XCircle,
      color: 'danger',
    },
  ];

  return (
    <div className="azals-auto-accounting__status-summary">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.status}
            className={`azals-auto-accounting__status-card azals-auto-accounting__status-card--${item.color}`}
            onClick={() => onFilter(item.status)}
          >
            <Icon size={20} />
            <span className="azals-auto-accounting__status-count">
              {item.count}
            </span>
            <span className="azals-auto-accounting__status-label">
              {item.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

const AlertsWidget: React.FC<{ alerts: Alert[] }> = ({ alerts }) => {
  const navigate = useNavigate();

  if (alerts.length === 0) {
    return null;
  }

  return (
    <Card title="Documents nécessitant attention">
      <div className="azals-auto-accounting__doc-alerts">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="azals-auto-accounting__doc-alert"
            onClick={() =>
              alert.document_id &&
              navigate(`/auto-accounting/documents/${alert.document_id}`)
            }
          >
            <AlertTriangle
              size={18}
              className={
                alert.alert_type === 'DOCUMENT_UNREADABLE'
                  ? 'azals-text--danger'
                  : 'azals-text--warning'
              }
            />
            <div className="azals-auto-accounting__doc-alert-content">
              <span className="azals-auto-accounting__doc-alert-title">
                {alert.title}
              </span>
              <span className="azals-auto-accounting__doc-alert-message">
                {alert.message}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============================================================
// UPLOAD MODAL
// ============================================================

const UploadModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
}> = ({ isOpen, onClose }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState('INVOICE_RECEIVED');
  const uploadDocument = useUploadDocument();

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      await uploadDocument.mutateAsync({ file: selectedFile, documentType });
      onClose();
      setSelectedFile(null);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const documentTypes = [
    { value: 'INVOICE_RECEIVED', label: 'Facture fournisseur' },
    { value: 'EXPENSE_NOTE', label: 'Note de frais' },
    { value: 'INVOICE_SENT', label: 'Facture client' },
    { value: 'CREDIT_NOTE_RECEIVED', label: 'Avoir reçu' },
    { value: 'QUOTE', label: 'Devis' },
    { value: 'PURCHASE_ORDER', label: 'Bon de commande' },
    { value: 'OTHER', label: 'Autre document' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Ajouter un document">
      <div className="azals-auto-accounting__upload-form">
        <div className="azals-form-group">
          <label className="azals-form-label">Type de document</label>
          <Select
            value={documentType}
            onChange={(value) => setDocumentType(value)}
            options={documentTypes}
          />
        </div>

        <div className="azals-form-group">
          <label className="azals-form-label">Fichier</label>
          <div
            className={`azals-auto-accounting__dropzone ${
              selectedFile ? 'azals-auto-accounting__dropzone--has-file' : ''
            }`}
          >
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="azals-auto-accounting__file-input"
            />
            {selectedFile ? (
              <div className="azals-auto-accounting__file-info">
                <FileText size={24} />
                <span>{selectedFile.name}</span>
              </div>
            ) : (
              <div className="azals-auto-accounting__dropzone-content">
                <Upload size={32} />
                <p>Glissez un fichier ou cliquez pour sélectionner</p>
                <span>PDF, JPG ou PNG</span>
              </div>
            )}
          </div>
        </div>

        <div className="azals-form-group azals-form-group--info">
          <p>
            Le document sera automatiquement analysé et comptabilisé.
            Vous n'avez rien d'autre à faire !
          </p>
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploadDocument.isPending}
          >
            {uploadDocument.isPending ? 'Envoi en cours...' : 'Ajouter'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const AssistanteDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: dashboard, isLoading: dashboardLoading } = useAssistanteDashboard();
  const { data: documents, isLoading: documentsLoading } = useDocuments(
    page,
    20,
    statusFilter ? { status: statusFilter } : {}
  );

  const columns: TableColumn<Document>[] = [
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      width: '120px',
      render: (value) => (
        <StatusBadge variant={getStatusVariant(value as string)} size="sm" status={getStatusLabel(value as string)} />
      ),
    },
    {
      id: 'document_type',
      header: 'Type',
      accessor: 'document_type',
      render: (value) => getTypeLabel(value as string),
    },
    {
      id: 'reference',
      header: 'Référence',
      accessor: 'reference',
      render: (value, row) => (value as string) || row.original_filename || '-',
    },
    {
      id: 'partner_name',
      header: 'Partenaire',
      accessor: 'partner_name',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'amount_total',
      header: 'Montant',
      accessor: 'amount_total',
      align: 'right',
      render: (value) => formatCurrency(value as number | null),
    },
    {
      id: 'document_date',
      header: 'Date',
      accessor: 'document_date',
      render: (value) => formatDate(value as string | null),
    },
    {
      id: 'received_at',
      header: 'Reçu le',
      accessor: 'received_at',
      render: (value) => formatDate(value as string),
    },
  ];

  const rowActions = [
    {
      id: 'view',
      label: 'Voir',
      icon: <Eye size={16} />,
      onClick: (row: Document) => navigate(`/auto-accounting/documents/${row.id}`),
    },
  ];

  if (dashboardLoading) {
    return (
      <PageWrapper title="Mes documents">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Mes documents"
      subtitle="Centralisez et organisez vos pièces comptables"
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={() => setIsUploadOpen(true)}>
          Ajouter un document
        </Button>
      }
    >
      {/* Résumé par statut */}
      {dashboard && (
        <section className="azals-section">
          <StatusSummaryWidget
            counts={dashboard.documents_by_status}
            onFilter={(status) => {
              setStatusFilter(status === statusFilter ? null : status);
              setPage(1);
            }}
          />
        </section>
      )}

      {/* Alertes documentaires */}
      {dashboard && dashboard.alerts.length > 0 && (
        <section className="azals-section">
          <AlertsWidget alerts={dashboard.alerts} />
        </section>
      )}

      {/* Liste des documents */}
      <section className="azals-section">
        <Card
          title="Documents"
          noPadding
          actions={
            <ButtonGroup>
              {statusFilter && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStatusFilter(null)}
                >
                  Effacer filtre
                </Button>
              )}
              <div className="azals-search-input">
                <Search size={16} />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </ButtonGroup>
          }
        >
          <DataTable
            columns={columns}
            data={documents?.items || []}
            keyField="id"
            isLoading={documentsLoading}
            actions={rowActions}
            pagination={{
              page,
              pageSize: 20,
              total: documents?.total || 0,
              onPageChange: setPage,
              onPageSizeChange: () => {},
            }}
            emptyMessage="Aucun document"
          />
        </Card>
      </section>

      {/* Modal d'upload */}
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
    </PageWrapper>
  );
};

export default AssistanteDashboard;
