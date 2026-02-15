/**
 * AZALSCORE Module - Facturation (VENTES T0)
 * ===========================================
 *
 * Module complet de gestion des devis et factures.
 *
 * Fonctionnalités:
 * - Création/modification de devis et factures
 * - Gestion des lignes de document
 * - Calculs automatiques HT/TVA/TTC
 * - Validation des documents (DRAFT -> VALIDATED)
 * - Conversion devis -> facture
 * - Export CSV
 * - Filtres et recherche
 *
 * Statuts T0: DRAFT (Brouillon), VALIDATED (Validé)
 * Types T0: QUOTE (Devis), INVOICE (Facture)
 */

import React, { useState, useMemo, useCallback } from 'react';
import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, FileText, Check, Download, Eye, Edit, Trash2,
  ArrowRight, Filter, Search, X, FileSpreadsheet,
  AlertCircle, CheckCircle2, Clock, UserPlus, Copy, ShoppingCart,
  DollarSign, Link2, Sparkles, Shield
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import { api } from '@core/api-client';
import { SmartSelector, FieldConfig } from '@/components/SmartSelector';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn, TableAction } from '@/types';
import type { Document as InvoicingDocument } from './types';
import {
  DOCUMENT_STATUS_CONFIG, DOCUMENT_TYPE_CONFIG,
  TRANSFORM_WORKFLOW as TRANSFORM_WORKFLOW_TYPES,
  getDaysUntilDue, isDocumentOverdue, canTransformDocument
} from './types';
import { formatCurrency as formatCurrencyUtil, formatDate as formatDateUtil } from '@/utils/formatters';
import {
  InvoicingInfoTab,
  InvoicingLinesTab,
  InvoicingFinancialTab,
  InvoicingDocumentsTab,
  InvoicingHistoryTab,
  InvoicingIATab,
  InvoicingRiskTab,
  LineEditor as LineEditorModal
} from './components';
import type { LineFormData } from './types';

// ============================================================
// TYPES - Alignés avec le backend
// ============================================================

type DocumentType = 'QUOTE' | 'INVOICE' | 'ORDER';
type DocumentStatus = 'DRAFT' | 'VALIDATED';

interface DocumentLine {
  id: string;
  document_id: string;
  line_number: number;
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
  discount_amount: number;
  subtotal: number;
  tax_amount: number;
  total: number;
  notes?: string;
  created_at: string;
}

interface Document {
  id: string;
  number: string;
  type: DocumentType;
  status: DocumentStatus;
  customer_id: string;
  date: string;
  due_date?: string;
  validity_date?: string;
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  parent_id?: string;
  validated_by?: string;
  validated_at?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  lines: DocumentLine[];
  // Customer info for display
  customer_name?: string;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  email?: string;
}

// LineFormData est importe depuis ./types

// ============================================================
// CONSTANTES
// ============================================================

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    icon: <Clock size={14} />
  },
  VALIDATED: {
    label: 'Validé',
    color: 'green',
    icon: <CheckCircle2 size={14} />
  },
};

const TYPE_CONFIG: Record<DocumentType, { label: string; labelPlural: string; prefix: string }> = {
  QUOTE: { label: 'Devis', labelPlural: 'Devis', prefix: 'DEV' },
  ORDER: { label: 'Commande', labelPlural: 'Commandes', prefix: 'CMD' },
  INVOICE: { label: 'Facture', labelPlural: 'Factures', prefix: 'FAC' },
};

// Workflow de transformation: type source → type cible
const TRANSFORM_WORKFLOW: Partial<Record<DocumentType, { target: DocumentType; label: string; icon: React.ReactNode }>> = {
  QUOTE: { target: 'ORDER', label: 'Transformer en commande', icon: <ShoppingCart size={14} /> },
  ORDER: { target: 'INVOICE', label: 'Transformer en facture', icon: <FileText size={14} /> },
};

const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency
  }).format(amount);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

// Configuration pour la création de client inline
const CUSTOMER_CREATE_FIELDS: FieldConfig[] = [
  { key: 'name', label: 'Nom', type: 'text', required: true },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Téléphone', type: 'tel' },
];

// ============================================================
// API HOOKS
// ============================================================

interface DocumentFilters {
  status?: DocumentStatus;
  search?: string;
  date_from?: string;
  date_to?: string;
}

const useDocuments = (
  type: DocumentType,
  page = 1,
  pageSize = 25,
  filters: DocumentFilters = {}
) => {
  const queryParams = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    type: type,
    ...(filters.status && { status: filters.status }),
    ...(filters.search && { search: filters.search }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
  });

  return useQuery({
    queryKey: ['documents', type, page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Document>>(
        `/v3/commercial/documents?${queryParams}`
      );
      // api.get retourne déjà response.data
      return response as unknown as PaginatedResponse<Document>;
    },
  });
};

const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const response = await api.get<Document>(`/v3/commercial/documents/${id}`);
      // api.get retourne déjà response.data
      return response as unknown as Document;
    },
    enabled: !!id && id !== 'new',
  });
};

const useCustomers = () => {
  return useQuery({
    queryKey: ['customers', 'list'],
    queryFn: async () => {
      // Utiliser /v3/partners/clients au lieu de /v3/commercial/customers
      const response = await api.get<PaginatedResponse<Customer>>(
        '/v3/partners/clients?page_size=500&is_active=true'
      );
      // api.get retourne déjà response.data
      return (response as unknown as PaginatedResponse<Customer>).items;
    },
  });
};

const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      type: DocumentType;
      customer_id: string;
      date: string;
      due_date?: string;
      validity_date?: string;
      notes?: string;
      lines: Omit<LineFormData, 'id'>[];
    }) => {
      const response = await api.post<Document>('/v3/commercial/documents', data);
      // api.post retourne déjà response.data
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

const useUpdateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data: Omit<Partial<Document>, 'lines'> & { lines?: LineFormData[] };
    }) => {
      const response = await api.put<Document>(`/v3/commercial/documents/${id}`, data);
      // api.put retourne déjà response.data
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.id] });
    },
  });
};

const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, type }: { id: string; type: DocumentType }) => {
      await api.delete(`/v3/commercial/documents/${id}`);
      return { id, type };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.type] });
    },
  });
};

const useValidateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }: { id: string }) => {
      const response = await api.post<Document>(`/v3/commercial/documents/${id}/validate`);
      // api.post retourne déjà response.data
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.id] });
    },
  });
};

const useConvertQuoteToInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ quoteId }: { quoteId: string }) => {
      const response = await api.post<Document>(`/v3/commercial/quotes/${quoteId}/convert`);
      // api.post retourne déjà response.data
      return response as unknown as Document;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'INVOICE'] });
    },
  });
};

// Hook pour dupliquer un document
const useDuplicateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ document }: { document: Document }) => {
      // Créer un nouveau document avec les mêmes données mais nouvelle date
      const payload = {
        type: document.type,
        customer_id: document.customer_id,
        date: new Date().toISOString().split('T')[0],
        due_date: document.due_date,
        validity_date: document.validity_date,
        notes: document.notes ? `(Copie) ${document.notes}` : '(Copie)',
        lines: document.lines.map(l => ({
          description: l.description,
          quantity: l.quantity,
          unit: l.unit,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate: l.tax_rate,
        })),
      };
      const response = await api.post<Document>('/v3/commercial/documents', payload);
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

// Hook pour transformer un document (Devis → Commande ou Commande → Facture)
const useTransformDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ document, targetType }: { document: Document; targetType: DocumentType }) => {
      const payload = {
        type: targetType,
        customer_id: document.customer_id,
        date: new Date().toISOString().split('T')[0],
        parent_id: document.id,
        notes: document.notes,
        lines: document.lines.map(l => ({
          description: l.description,
          quantity: l.quantity,
          unit: l.unit,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate: l.tax_rate,
        })),
      };
      const response = await api.post<Document>('/v3/commercial/documents', payload);
      return response as unknown as Document;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.document.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

const useExportDocuments = () => {
  return useMutation({
    mutationFn: async ({ type, filters }: { type: DocumentType; filters: DocumentFilters }) => {
      const queryParams = new URLSearchParams({
        type: type,
        format: 'csv',
        ...(filters.status && { status: filters.status }),
        ...(filters.search && { search: filters.search }),
      });

      const response = await api.get<Blob>(
        `/v3/commercial/documents/export?${queryParams}`,
        { responseType: 'blob' }
      );
      // api.get retourne déjà response.data
      return response as unknown as Blob;
    },
  });
};

// ============================================================
// COMPONENTS - Status Badge
// ============================================================

interface StatusBadgeProps {
  status: DocumentStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'gray', icon: null };

  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

// ============================================================
// COMPONENTS - Lines Editor (avec modal ProductAutocomplete)
// ============================================================

interface LinesEditorProps {
  lines: LineFormData[];
  onChange: (lines: LineFormData[]) => void;
  readOnly?: boolean;
  currency?: string;
}

const calculateLineTotal = (line: LineFormData): { subtotal: number; taxAmount: number; total: number } => {
  const baseAmount = line.quantity * line.unit_price;
  const discountAmount = baseAmount * (line.discount_percent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (line.tax_rate / 100);
  const total = subtotal + taxAmount;

  return { subtotal, taxAmount, total };
};

const LinesEditor: React.FC<LinesEditorProps> = ({ lines, onChange, readOnly = false, currency = 'EUR' }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  // Ouvrir modal pour nouvelle ligne
  const openAddModal = () => {
    setEditingIndex(null);
    setShowModal(true);
  };

  // Ouvrir modal pour editer une ligne existante
  const openEditModal = (index: number) => {
    setEditingIndex(index);
    setShowModal(true);
  };

  // Sauvegarder depuis le modal
  const handleSaveLine = (lineData: LineFormData) => {
    if (editingIndex !== null) {
      // Edition d'une ligne existante
      const newLines = [...lines];
      newLines[editingIndex] = { ...newLines[editingIndex], ...lineData };
      onChange(newLines);
    } else {
      // Nouvelle ligne
      const newLine: LineFormData = {
        ...lineData,
        id: lineData.id || `temp-${Date.now()}`,
      };
      onChange([...lines, newLine]);
    }
    setShowModal(false);
    setEditingIndex(null);
  };

  const removeLine = (index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
  };

  const totals = useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        const calc = calculateLineTotal(line);
        return {
          subtotal: acc.subtotal + calc.subtotal,
          taxAmount: acc.taxAmount + calc.taxAmount,
          total: acc.total + calc.total,
        };
      },
      { subtotal: 0, taxAmount: 0, total: 0 }
    );
  }, [lines]);

  // Donnees initiales pour le modal
  const editingLineData = editingIndex !== null ? lines[editingIndex] : undefined;

  return (
    <div className="azals-line-editor">
      <div className="azals-line-editor__header">
        <h3>Lignes du document</h3>
        {!readOnly && (
          <Button
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={openAddModal}
          >
            Ajouter une ligne
          </Button>
        )}
      </div>

      {lines.length === 0 ? (
        <div className="azals-line-editor__empty">
          <AlertCircle size={24} />
          <p>Aucune ligne. {!readOnly && 'Cliquez sur "Ajouter une ligne" pour commencer.'}</p>
        </div>
      ) : (
        <table className="azals-line-editor__table">
          <thead>
            <tr>
              <th style={{ width: '35%' }}>Description</th>
              <th style={{ width: '10%' }}>Qté</th>
              <th style={{ width: '12%' }}>Prix unit. HT</th>
              <th style={{ width: '10%' }}>Remise</th>
              <th style={{ width: '8%' }}>TVA</th>
              <th style={{ width: '15%' }}>Total HT</th>
              {!readOnly && <th style={{ width: '10%' }}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line);

              return (
                <tr key={line.id || index}>
                  <td>
                    <div className="font-medium">{line.description || <em className="text-muted">Sans description</em>}</div>
                    {line.unit && <div className="text-xs text-muted">Unité: {line.unit}</div>}
                  </td>
                  <td className="text-right">{line.quantity}</td>
                  <td className="text-right">{formatCurrency(line.unit_price, currency)}</td>
                  <td className="text-right">
                    {line.discount_percent > 0 ? (
                      <span className="text-orange">{line.discount_percent}%</span>
                    ) : '-'}
                  </td>
                  <td className="text-right">{line.tax_rate}%</td>
                  <td className="text-right font-medium">{formatCurrency(calc.subtotal, currency)}</td>
                  {!readOnly && (
                    <td>
                      <div className="flex gap-1">
                        <button
                          type="button"
                          className="azals-btn-icon"
                          onClick={() => openEditModal(index)}
                          title="Modifier"
                        >
                          <Edit size={14} />
                        </button>
                        <button
                          type="button"
                          className="azals-btn-icon azals-btn-icon--danger"
                          onClick={() => removeLine(index)}
                          title="Supprimer"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <div className="azals-line-editor__totals">
        <div className="azals-line-editor__total-row">
          <span>Total HT</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row">
          <span>Total TVA</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row azals-line-editor__total-row--main">
          <span>Total TTC</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>

      {/* Modal d'edition de ligne avec ProductAutocomplete */}
      {showModal && (
        <LineEditorModal
          initialData={editingLineData}
          currency={currency}
          onSave={handleSaveLine}
          onCancel={() => {
            setShowModal(false);
            setEditingIndex(null);
          }}
          isModal={true}
        />
      )}
    </div>
  );
};

// Alias pour compatibilite avec le code existant
const LineEditor = LinesEditor;

// ============================================================
// COMPONENTS - Filter Bar
// ============================================================

interface FilterBarProps {
  filters: DocumentFilters;
  onChange: (filters: DocumentFilters) => void;
  onExport: () => void;
  isExporting?: boolean;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange, onExport, isExporting }) => {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="azals-filter-bar">
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Rechercher par numéro ou client..."
          value={filters.search || ''}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="azals-input"
        />
        {filters.search && (
          <button
            className="azals-filter-bar__clear"
            onClick={() => onChange({ ...filters, search: '' })}
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="azals-filter-bar__actions">
        <Button
          variant="ghost"
          leftIcon={<Filter size={16} />}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filtres
          {(filters.status || filters.date_from) && (
            <span className="azals-filter-bar__badge">!</span>
          )}
        </Button>

        <CapabilityGuard capability="invoicing.export">
          <Button
            variant="ghost"
            leftIcon={<FileSpreadsheet size={16} />}
            onClick={onExport}
            isLoading={isExporting}
          >
            Export CSV
          </Button>
        </CapabilityGuard>
      </div>

      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__field">
            <label>Statut</label>
            <select
              value={filters.status || ''}
              onChange={(e) => onChange({
                ...filters,
                status: e.target.value as DocumentStatus || undefined
              })}
              className="azals-select"
            >
              <option value="">Tous</option>
              <option value="DRAFT">Brouillon</option>
              <option value="VALIDATED">Validé</option>
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Date début</label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
              className="azals-input"
            />
          </div>

          <div className="azals-filter-bar__field">
            <label>Date fin</label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
              className="azals-input"
            />
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange({})}
          >
            Réinitialiser
          </Button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// PAGES - Document List
// ============================================================

interface DocumentListPageProps {
  type: DocumentType;
}

const DocumentListPage: React.FC<DocumentListPageProps> = ({ type }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<DocumentFilters>({});
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [validateTarget, setValidateTarget] = useState<Document | null>(null);
  const [convertTarget, setConvertTarget] = useState<Document | null>(null);
  const [duplicateTarget, setDuplicateTarget] = useState<Document | null>(null);
  const [transformTarget, setTransformTarget] = useState<Document | null>(null);

  const { data, isLoading, error, refetch } = useDocuments(type, page, pageSize, filters);
  const deleteDocument = useDeleteDocument();
  const validateDocument = useValidateDocument();
  const convertQuote = useConvertQuoteToInvoice();
  const duplicateDocument = useDuplicateDocument();
  const transformDocument = useTransformDocument();
  const exportDocuments = useExportDocuments();

  const typeConfig = TYPE_CONFIG[type] || { label: type, color: 'gray', prefix: 'DOC' };
  // Utiliser les capabilities générales (invoicing.create) plutôt que granulaires (invoicing.quotes.create)
  const canCreate = useHasCapability('invoicing.create');
  const canEdit = useHasCapability('invoicing.edit');
  const canDelete = useHasCapability('invoicing.delete');
  const canValidate = useHasCapability('invoicing.edit'); // validate = edit permission

  const handleExport = async () => {
    try {
      const blob = await exportDocuments.mutateAsync({ type, filters });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type.toLowerCase()}s_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const columns: TableColumn<Document>[] = [
    {
      id: 'number',
      header: 'Numéro',
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <Link to={`/invoicing/${type.toLowerCase()}s/${row.id}`} className="azals-link">
          {value as string}
        </Link>
      ),
    },
    {
      id: 'customer_name',
      header: 'Client',
      accessor: 'customer_name',
      sortable: true,
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <StatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'total',
      header: 'Total TTC',
      accessor: 'total',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  // Configuration de transformation pour ce type
  const transformConfig = TRANSFORM_WORKFLOW[type];

  const actions: TableAction<Document>[] = [
    {
      id: 'view',
      label: 'Voir',
      icon: 'eye',
      onClick: (row) => navigate(`/invoicing/${type.toLowerCase()}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: 'edit',
      onClick: (row) => navigate(`/invoicing/${type.toLowerCase()}s/${row.id}/edit`),
      isHidden: (row) => row.status !== 'DRAFT' || !canEdit,
    },
    {
      id: 'duplicate',
      label: 'Dupliquer',
      icon: 'copy',
      onClick: (row) => setDuplicateTarget(row),
      isHidden: () => !canCreate,
    },
    {
      id: 'validate',
      label: 'Valider',
      icon: 'check',
      onClick: (row) => setValidateTarget(row),
      isHidden: (row) => row.status !== 'DRAFT' || !canValidate,
    },
    // Action de transformation (Devis → Commande ou Commande → Facture)
    ...(transformConfig ? [{
      id: 'transform',
      label: transformConfig.label,
      icon: 'arrow-right',
      onClick: (row: Document) => setTransformTarget(row),
      isHidden: (row: Document) => row.status !== 'VALIDATED',
    }] : []),
    // Legacy: Convertir devis en facture (directement)
    ...(type === 'QUOTE' ? [{
      id: 'convert',
      label: 'Convertir en facture',
      icon: 'arrow-right',
      onClick: (row: Document) => setConvertTarget(row),
      isHidden: (row: Document) => row.status !== 'VALIDATED',
    }] : []),
    {
      id: 'delete',
      label: 'Supprimer',
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: (row) => row.status !== 'DRAFT' || !canDelete,
    },
  ];

  return (
    <PageWrapper
      title={typeConfig.labelPlural}
      actions={
        canCreate && (
          <Button
            leftIcon={<Plus size={16} />}
            onClick={() => navigate(`/invoicing/${type.toLowerCase()}s/new`)}
          >
            Nouveau {typeConfig.label.toLowerCase()}
          </Button>
        )
      }
    >
      <Card>
        <FilterBar
          filters={filters}
          onChange={setFilters}
          onExport={handleExport}
          isExporting={exportDocuments.isPending}
        />

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage={`Aucun ${typeConfig.label.toLowerCase()}`}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          title="Confirmer la suppression"
          message={`Êtes-vous sûr de vouloir supprimer le ${typeConfig.label.toLowerCase()} ${deleteTarget.number} ?`}
          variant="danger"
          onConfirm={async () => {
            await deleteDocument.mutateAsync({ id: deleteTarget.id, type });
            setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteDocument.isPending}
        />
      )}

      {/* Validate Confirmation */}
      {validateTarget && (
        <ConfirmDialog
          title="Confirmer la validation"
          message={
            <>
              <p>Voulez-vous valider le {typeConfig.label.toLowerCase()} <strong>{validateTarget.number}</strong> ?</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                Attention : Un document validé ne peut plus être modifié.
              </p>
            </>
          }
          variant="warning"
          confirmLabel="Valider"
          onConfirm={async () => {
            await validateDocument.mutateAsync({ id: validateTarget.id });
            setValidateTarget(null);
          }}
          onCancel={() => setValidateTarget(null)}
          isLoading={validateDocument.isPending}
        />
      )}

      {/* Convert Confirmation */}
      {convertTarget && (
        <ConfirmDialog
          title="Convertir en facture"
          message={
            <>
              <p>Voulez-vous créer une facture à partir du devis <strong>{convertTarget.number}</strong> ?</p>
              <p className="text-muted mt-2">
                Une nouvelle facture sera créée avec les mêmes lignes.
              </p>
            </>
          }
          confirmLabel="Créer la facture"
          onConfirm={async () => {
            const invoice = await convertQuote.mutateAsync({ quoteId: convertTarget.id });
            setConvertTarget(null);
            navigate(`/invoicing/invoices/${invoice.id}`);
          }}
          onCancel={() => setConvertTarget(null)}
          isLoading={convertQuote.isPending}
        />
      )}

      {/* Duplicate Confirmation */}
      {duplicateTarget && (
        <ConfirmDialog
          title="Dupliquer le document"
          message={
            <>
              <p>Voulez-vous dupliquer le {typeConfig.label.toLowerCase()} <strong>{duplicateTarget.number}</strong> ?</p>
              <p className="text-muted mt-2">
                <Copy size={14} className="inline mr-1" />
                Un nouveau {typeConfig.label.toLowerCase()} brouillon sera créé avec les mêmes lignes et la date du jour.
              </p>
            </>
          }
          confirmLabel="Dupliquer"
          onConfirm={async () => {
            const newDoc = await duplicateDocument.mutateAsync({ document: duplicateTarget });
            setDuplicateTarget(null);
            navigate(`/invoicing/${type.toLowerCase()}s/${newDoc.id}`);
          }}
          onCancel={() => setDuplicateTarget(null)}
          isLoading={duplicateDocument.isPending}
        />
      )}

      {/* Transform Confirmation */}
      {transformTarget && transformConfig && (
        <ConfirmDialog
          title={transformConfig.label}
          message={
            <>
              <p>Voulez-vous transformer le {typeConfig.label.toLowerCase()} <strong>{transformTarget.number}</strong> ?</p>
              <p className="text-muted mt-2">
                {transformConfig.icon}
                <span className="ml-1">
                  Un nouveau document de type {TYPE_CONFIG[transformConfig.target].label.toLowerCase()} sera créé.
                </span>
              </p>
              <div className="azals-transform-workflow mt-3">
                <span className="azals-transform-workflow__step azals-transform-workflow__step--active">
                  {typeConfig.label}
                </span>
                <ArrowRight size={16} className="azals-transform-workflow__arrow" />
                <span className="azals-transform-workflow__step azals-transform-workflow__step--target">
                  {TYPE_CONFIG[transformConfig.target].label}
                </span>
              </div>
            </>
          }
          confirmLabel={`Créer ${TYPE_CONFIG[transformConfig.target].label.toLowerCase()}`}
          onConfirm={async () => {
            const newDoc = await transformDocument.mutateAsync({
              document: transformTarget,
              targetType: transformConfig.target
            });
            setTransformTarget(null);
            navigate(`/invoicing/${transformConfig.target.toLowerCase()}s/${newDoc.id}`);
          }}
          onCancel={() => setTransformTarget(null)}
          isLoading={transformDocument.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Document Form
// ============================================================

interface DocumentFormPageProps {
  type: DocumentType;
}

const DocumentFormPage: React.FC<DocumentFormPageProps> = ({ type }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== 'new';

  const { data: document, isLoading: loadingDocument } = useDocument(id || '');
  const { data: customers, isLoading: loadingCustomers } = useCustomers();
  const createDocument = useCreateDocument();
  const updateDocument = useUpdateDocument();

  const typeConfig = TYPE_CONFIG[type] || { label: type, color: 'gray', prefix: 'DOC' };

  // Form state
  const [customerId, setCustomerId] = useState('');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [validityDate, setValidityDate] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load existing document data
  React.useEffect(() => {
    if (document) {
      setCustomerId(document.customer_id);
      setDocDate(document.date);
      setDueDate(document.due_date || '');
      setValidityDate(document.validity_date || '');
      setNotes(document.notes || '');
      setLines(document.lines.map((l) => ({
        id: l.id,
        description: l.description,
        quantity: l.quantity,
        unit: l.unit,
        unit_price: l.unit_price,
        discount_percent: l.discount_percent,
        tax_rate: l.tax_rate,
      })));
    }
  }, [document]);

  // Redirect if document is validated (not editable)
  React.useEffect(() => {
    if (isEdit && document && document.status !== 'DRAFT') {
      navigate(`/invoicing/${type.toLowerCase()}s/${id}`);
    }
  }, [document, isEdit, type, id, navigate]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!customerId) {
      newErrors.customer = 'Veuillez sélectionner un client';
    }
    if (!docDate) {
      newErrors.date = 'La date est requise';
    }
    if (lines.length === 0) {
      newErrors.lines = 'Ajoutez au moins une ligne';
    }
    if (lines.some((l) => !l.description.trim())) {
      newErrors.lines = 'Toutes les lignes doivent avoir une description';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      if (isEdit) {
        await updateDocument.mutateAsync({
          id: id!,
          data: {
            date: docDate,
            due_date: dueDate || undefined,
            validity_date: validityDate || undefined,
            notes: notes || undefined,
            lines,
          },
        });
      } else {
        await createDocument.mutateAsync({
          type,
          customer_id: customerId,
          date: docDate,
          due_date: dueDate || undefined,
          validity_date: validityDate || undefined,
          notes: notes || undefined,
          lines: lines.map(({ id: _, ...line }) => line),
        });
      }
      navigate(`/invoicing/${type.toLowerCase()}s`);
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  if ((isEdit && loadingDocument) || loadingCustomers) {
    return (
      <PageWrapper title={`${isEdit ? 'Modifier' : 'Nouveau'} ${typeConfig.label}`}>
        <LoadingState message="Chargement du formulaire..." />
      </PageWrapper>
    );
  }

  const isSubmitting = createDocument.isPending || updateDocument.isPending;

  return (
    <PageWrapper
      title={`${isEdit ? 'Modifier' : 'Nouveau'} ${typeConfig.label}`}
      actions={
        <Button variant="ghost" onClick={() => navigate(`/invoicing/${type.toLowerCase()}s`)}>
          Annuler
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card className="mb-4">
          <h3 className="mb-4">Informations générales</h3>

          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <SmartSelector
                items={(customers || []).map(c => ({ ...c, id: c.id, name: c.name }))}
                value={customerId}
                onChange={(value) => setCustomerId(value)}
                label="Client *"
                placeholder="Sélectionner un client..."
                displayField="name"
                secondaryField="code"
                entityName="client"
                entityIcon={<UserPlus size={16} />}
                createEndpoint="/v3/partners/clients"
                createFields={CUSTOMER_CREATE_FIELDS}
                createUrl="/partners/clients/new"
                queryKeys={['customers', 'clients']}
                disabled={isEdit}
                error={errors.customer}
                allowCreate={!isEdit}
              />
            </div>

            <div className="azals-form-field">
              <label htmlFor="date">Date *</label>
              <input
                type="date"
                id="date"
                value={docDate}
                onChange={(e) => setDocDate(e.target.value)}
                className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
              />
              {errors.date && <span className="azals-form-error">{errors.date}</span>}
            </div>

            {type === 'QUOTE' && (
              <div className="azals-form-field">
                <label htmlFor="validity">Date de validité</label>
                <input
                  type="date"
                  id="validity"
                  value={validityDate}
                  onChange={(e) => setValidityDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}

            {type === 'INVOICE' && (
              <div className="azals-form-field">
                <label htmlFor="due">Date d'échéance</label>
                <input
                  type="date"
                  id="due"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="azals-input"
                />
              </div>
            )}
          </Grid>

          <div className="azals-form-field mt-4">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="azals-textarea"
              rows={3}
              placeholder="Notes visibles sur le document..."
            />
          </div>
        </Card>

        <Card className="mb-4">
          {errors.lines && (
            <div className="azals-alert azals-alert--error mb-4">
              <AlertCircle size={16} />
              <span>{errors.lines}</span>
            </div>
          )}
          <LineEditor
            lines={lines}
            onChange={setLines}
          />
        </Card>

        <div className="azals-form-actions">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/invoicing/${type.toLowerCase()}s`)}
          >
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            leftIcon={<Check size={16} />}
          >
            {isEdit ? 'Enregistrer' : `Créer le ${typeConfig.label.toLowerCase()}`}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Document Detail
// ============================================================

interface DocumentDetailPageProps {
  type: DocumentType;
}

const DocumentDetailPage: React.FC<DocumentDetailPageProps> = ({ type }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [validateModal, setValidateModal] = useState(false);
  const [convertModal, setConvertModal] = useState(false);

  const { data: document, isLoading, refetch } = useDocument(id || '');
  const validateDocument = useValidateDocument();
  const convertQuote = useConvertQuoteToInvoice();

  const typeConfig = TYPE_CONFIG[type] || { label: type, color: 'gray', prefix: 'DOC' };
  const canEdit = useHasCapability('invoicing.edit');
  const canValidate = useHasCapability('invoicing.edit');

  if (isLoading) {
    return (
      <PageWrapper title={typeConfig.label}>
        <LoadingState onRetry={() => refetch()} message="Chargement du document..." />
      </PageWrapper>
    );
  }

  if (!document) {
    return (
      <PageWrapper title={typeConfig.label}>
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <h3>Document non trouvé</h3>
            <p>Le document demandé n'existe pas ou a été supprimé.</p>
            <Button onClick={() => navigate(`/invoicing/${type.toLowerCase()}s`)}>
              Retour à la liste
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const isDraft = document.status === 'DRAFT';
  const isValidated = document.status === 'VALIDATED';

  return (
    <PageWrapper
      title={`${typeConfig.label} ${document.number}`}
      actions={
        <ButtonGroup>
          {isDraft && canEdit && (
            <Button
              variant="ghost"
              leftIcon={<Edit size={16} />}
              onClick={() => navigate(`/invoicing/${type.toLowerCase()}s/${id}/edit`)}
            >
              Modifier
            </Button>
          )}
          {isDraft && canValidate && (
            <Button
              leftIcon={<Check size={16} />}
              onClick={() => setValidateModal(true)}
            >
              Valider
            </Button>
          )}
          {type === 'QUOTE' && isValidated && (
            <Button
              leftIcon={<ArrowRight size={16} />}
              onClick={() => setConvertModal(true)}
            >
              Convertir en facture
            </Button>
          )}
        </ButtonGroup>
      }
    >
      <Grid cols={3} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <StatusBadge status={document.status} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Total HT</span>
            <span className="azals-stat__value">
              {formatCurrency(document.subtotal, document.currency)}
            </span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Total TTC</span>
            <span className="azals-stat__value azals-stat__value--primary">
              {formatCurrency(document.total, document.currency)}
            </span>
          </div>
        </Card>
      </Grid>

      <Card className="mb-4">
        <div className="azals-document-header">
          <div>
            <h2>{document.customer_name}</h2>
            <p className="text-muted">Numéro: {document.number}</p>
          </div>
          <div className="text-right">
            <p><strong>Date:</strong> {formatDate(document.date)}</p>
            {document.due_date && (
              <p><strong>Échéance:</strong> {formatDate(document.due_date)}</p>
            )}
            {document.validity_date && (
              <p><strong>Validité:</strong> {formatDate(document.validity_date)}</p>
            )}
          </div>
        </div>

        {document.validated_at && (
          <div className="azals-document-validation mt-4">
            <CheckCircle2 size={16} className="text-success" />
            <span>
              Validé le {formatDate(document.validated_at)}
            </span>
          </div>
        )}

        {document.parent_id && (
          <div className="azals-document-link mt-2">
            <FileText size={14} />
            <span>Créé à partir du devis </span>
            <Link to={`/invoicing/quotes/${document.parent_id}`}>
              voir le devis original
            </Link>
          </div>
        )}
      </Card>

      <Card className="mb-4">
        <LineEditor
          lines={document.lines.map((l) => ({
            id: l.id,
            description: l.description,
            quantity: l.quantity,
            unit: l.unit,
            unit_price: l.unit_price,
            discount_percent: l.discount_percent,
            tax_rate: l.tax_rate,
          }))}
          onChange={() => {}}
          readOnly
          currency={document.currency}
        />
      </Card>

      {document.notes && (
        <Card>
          <h4>Notes</h4>
          <p className="text-muted">{document.notes}</p>
        </Card>
      )}

      {/* Validate Modal */}
      {validateModal && (
        <ConfirmDialog
          title="Confirmer la validation"
          message={
            <>
              <p>Voulez-vous valider ce {typeConfig.label.toLowerCase()} ?</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                Un document validé ne peut plus être modifié.
              </p>
            </>
          }
          variant="warning"
          confirmLabel="Valider"
          onConfirm={async () => {
            await validateDocument.mutateAsync({ id: document.id });
            setValidateModal(false);
          }}
          onCancel={() => setValidateModal(false)}
          isLoading={validateDocument.isPending}
        />
      )}

      {/* Convert Modal */}
      {convertModal && (
        <ConfirmDialog
          title="Convertir en facture"
          message={
            <>
              <p>Créer une facture à partir de ce devis ?</p>
              <p className="text-muted mt-2">
                Une nouvelle facture sera créée avec les mêmes lignes.
              </p>
            </>
          }
          confirmLabel="Créer la facture"
          onConfirm={async () => {
            const invoice = await convertQuote.mutateAsync({ quoteId: document.id });
            setConvertModal(false);
            navigate(`/invoicing/invoices/${invoice.id}`);
          }}
          onCancel={() => setConvertModal(false)}
          isLoading={convertQuote.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Dashboard
// ============================================================

const InvoicingDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: quotes } = useDocuments('QUOTE', 1, 5, { status: 'DRAFT' });
  const { data: invoices } = useDocuments('INVOICE', 1, 5, { status: 'DRAFT' });

  return (
    <PageWrapper title="Facturation">
      <Grid cols={2} gap="lg">
        <Card className="azals-dashboard-card" onClick={() => navigate('/invoicing/quotes')}>
          <div className="azals-dashboard-card__icon azals-dashboard-card__icon--blue">
            <FileText size={32} />
          </div>
          <div className="azals-dashboard-card__content">
            <h3>Devis</h3>
            <p className="text-muted">
              {quotes?.total || 0} devis en brouillon
            </p>
          </div>
          <ArrowRight size={20} className="azals-dashboard-card__arrow" />
        </Card>

        <Card className="azals-dashboard-card" onClick={() => navigate('/invoicing/invoices')}>
          <div className="azals-dashboard-card__icon azals-dashboard-card__icon--green">
            <FileText size={32} />
          </div>
          <div className="azals-dashboard-card__content">
            <h3>Factures</h3>
            <p className="text-muted">
              {invoices?.total || 0} factures en brouillon
            </p>
          </div>
          <ArrowRight size={20} className="azals-dashboard-card__arrow" />
        </Card>
      </Grid>

      <Grid cols={2} gap="lg" className="mt-6">
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3>Derniers devis brouillons</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/invoicing/quotes')}
            >
              Voir tout
            </Button>
          </div>
          {quotes?.items && quotes.items.length > 0 ? (
            <ul className="azals-simple-list">
              {quotes.items.slice(0, 5).map((doc) => (
                <li key={doc.id}>
                  <Link to={`/invoicing/quotes/${doc.id}`}>
                    <span>{doc.number}</span>
                    <span className="text-muted">{doc.customer_name}</span>
                    <span>{formatCurrency(doc.total, doc.currency)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucun devis en brouillon</p>
          )}
        </Card>

        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3>Dernières factures brouillons</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/invoicing/invoices')}
            >
              Voir tout
            </Button>
          </div>
          {invoices?.items && invoices.items.length > 0 ? (
            <ul className="azals-simple-list">
              {invoices.items.slice(0, 5).map((doc) => (
                <li key={doc.id}>
                  <Link to={`/invoicing/invoices/${doc.id}`}>
                    <span>{doc.number}</span>
                    <span className="text-muted">{doc.customer_name}</span>
                    <span>{formatCurrency(doc.total, doc.currency)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucune facture en brouillon</p>
          )}
        </Card>
      </Grid>
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Detail View (BaseViewStandard)
// ============================================================

interface InvoicingDetailViewProps {
  type: DocumentType;
}

const InvoicingDetailView: React.FC<InvoicingDetailViewProps> = ({ type }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: document, isLoading, error, refetch } = useDocument(id || '');

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <LoadingState onRetry={() => refetch()} message="Chargement du document..." />
      </PageWrapper>
    );
  }

  if (error || !document) {
    return (
      <PageWrapper title="Erreur">
        <ErrorState
          message="Document introuvable"
          onRetry={() => refetch()}
          onBack={() => navigate(-1)}
        />
      </PageWrapper>
    );
  }

  const typeConfig = DOCUMENT_TYPE_CONFIG[document.type] || { label: document.type, color: 'gray' };
  const statusConfig = DOCUMENT_STATUS_CONFIG[document.status] || { label: document.status, color: 'gray' };

  // Configuration des onglets
  const tabs: TabDefinition<InvoicingDocument>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <FileText size={16} />,
      component: InvoicingInfoTab
    },
    {
      id: 'lines',
      label: 'Lignes',
      icon: <ShoppingCart size={16} />,
      badge: document.lines?.length,
      component: InvoicingLinesTab
    },
    {
      id: 'financial',
      label: 'Financier',
      icon: <DollarSign size={16} />,
      component: InvoicingFinancialTab
    },
    {
      id: 'risk',
      label: 'Risque Client',
      icon: <Shield size={16} />,
      component: InvoicingRiskTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <Link2 size={16} />,
      component: InvoicingDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: InvoicingHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: InvoicingIATab
    }
  ];

  // Barre d'info KPIs
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'type',
      label: 'Type',
      value: typeConfig.label,
      valueColor: typeConfig.color as SemanticColor
    },
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color as SemanticColor
    },
    {
      id: 'lines',
      label: 'Lignes',
      value: String(document.lines?.length || 0),
      valueColor: 'blue'
    },
    {
      id: 'total',
      label: 'Total TTC',
      value: formatCurrencyUtil(document.total, document.currency),
      valueColor: 'green'
    }
  ];

  // Ajouter alerte retard si applicable
  if (isDocumentOverdue(document)) {
    const days = Math.abs(getDaysUntilDue(document) || 0);
    infoBarItems.push({
      id: 'overdue',
      label: 'Retard',
      value: `${days}j`,
      valueColor: 'red'
    });
  }

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'number', label: 'Numero', value: document.number },
        { id: 'date', label: 'Date', value: formatDateUtil(document.date) },
        { id: 'customer', label: 'Client', value: document.customer_name || '-' },
        { id: 'currency', label: 'Devise', value: document.currency }
      ]
    },
    {
      id: 'totals',
      title: 'Montants',
      items: [
        { id: 'subtotal', label: 'Total HT', value: formatCurrencyUtil(document.subtotal, document.currency) },
        { id: 'tax', label: 'TVA', value: formatCurrencyUtil(document.tax_amount, document.currency) },
        { id: 'total', label: 'Total TTC', value: formatCurrencyUtil(document.total, document.currency), highlight: true }
      ]
    }
  ];

  // Ajouter section echeance si applicable
  if (document.due_date) {
    const daysUntil = getDaysUntilDue(document);
    sidebarSections.push({
      id: 'payment',
      title: 'Echeance',
      items: [
        { id: 'due_date', label: 'Date', value: formatDateUtil(document.due_date) },
        {
          id: 'days',
          label: 'Statut',
          value: daysUntil !== null
            ? (daysUntil < 0 ? `En retard (${Math.abs(daysUntil)}j)` : `${daysUntil}j restants`)
            : '-',
          highlight: daysUntil !== null && daysUntil < 0
        }
      ]
    });
  }

  // Actions header
  const headerActions: ActionDefinition[] = [];

  if (document.status === 'DRAFT') {
    headerActions.push({
      id: 'edit',
      label: 'Modifier',
      variant: 'secondary',
      capability: 'invoicing.edit',
      onClick: () => navigate(`/invoicing/${type.toLowerCase()}s/${id}/edit`)
    });
  }

  if (canTransformDocument(document)) {
    const transformConfig = TRANSFORM_WORKFLOW_TYPES[document.type];
    if (transformConfig) {
      headerActions.push({
        id: 'transform',
        label: transformConfig.label,
        variant: 'primary',
        onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'transformDocument', documentId: document.id, targetType: transformConfig.target } })); },
      });
    }
  }

  // Statut du document
  const status = {
    label: statusConfig.label,
    color: statusConfig.color as SemanticColor
  };

  return (
    <BaseViewStandard<InvoicingDocument>
      title={`${typeConfig.label} ${document.number}`}
      subtitle={document.customer_name || undefined}
      status={status}
      data={document}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================
// EXPORTS - Page Components
// ============================================================

export const QuotesPage: React.FC = () => <DocumentListPage type="QUOTE" />;
export const OrdersPage: React.FC = () => <DocumentListPage type="ORDER" />;
export const InvoicesPage: React.FC = () => <DocumentListPage type="INVOICE" />;

export const QuoteFormPage: React.FC = () => <DocumentFormPage type="QUOTE" />;
export const OrderFormPage: React.FC = () => <DocumentFormPage type="ORDER" />;
export const InvoiceFormPage: React.FC = () => <DocumentFormPage type="INVOICE" />;

// Legacy detail pages (keeping for backward compatibility)
export const QuoteDetailPage: React.FC = () => <DocumentDetailPage type="QUOTE" />;
export const OrderDetailPage: React.FC = () => <DocumentDetailPage type="ORDER" />;
export const InvoiceDetailPageComponent: React.FC = () => <DocumentDetailPage type="INVOICE" />;

// New BaseViewStandard detail views
export const QuoteDetailViewStandard: React.FC = () => <InvoicingDetailView type="QUOTE" />;
export const OrderDetailViewStandard: React.FC = () => <InvoicingDetailView type="ORDER" />;
export const InvoiceDetailViewStandard: React.FC = () => <InvoicingDetailView type="INVOICE" />;

// ============================================================
// EXPORTS - Router
// ============================================================

export const InvoicingRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InvoicingDashboard />} />

    <Route path="quotes" element={<QuotesPage />} />
    <Route path="quotes/new" element={<QuoteFormPage />} />
    <Route path="quotes/:id" element={<QuoteDetailViewStandard />} />
    <Route path="quotes/:id/edit" element={<QuoteFormPage />} />

    <Route path="orders" element={<OrdersPage />} />
    <Route path="orders/new" element={<OrderFormPage />} />
    <Route path="orders/:id" element={<OrderDetailViewStandard />} />
    <Route path="orders/:id/edit" element={<OrderFormPage />} />

    <Route path="invoices" element={<InvoicesPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailViewStandard />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
  </Routes>
);

export default InvoicingRoutes;
