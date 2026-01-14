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
  ArrowRight, RefreshCw, Filter, Search, X, FileSpreadsheet,
  AlertCircle, CheckCircle2, Clock
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn, TableAction } from '@/types';

// ============================================================
// TYPES - Alignés avec le backend
// ============================================================

type DocumentType = 'QUOTE' | 'INVOICE';
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

interface LineFormData {
  id?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

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
  INVOICE: { label: 'Facture', labelPlural: 'Factures', prefix: 'FAC' },
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
        `/v1/commercial/documents?${queryParams}`
      );
      return response.data;
    },
  });
};

const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const response = await api.get<Document>(`/v1/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
};

const useCustomers = () => {
  return useQuery({
    queryKey: ['customers', 'list'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        '/v1/commercial/customers?page_size=500&is_active=true'
      );
      return response.data.items;
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
      const response = await api.post<Document>('/v1/commercial/documents', data);
      return response.data;
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
      const response = await api.put<Document>(`/v1/commercial/documents/${id}`, data);
      return response.data;
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
      await api.delete(`/v1/commercial/documents/${id}`);
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
      const response = await api.post<Document>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
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
      const response = await api.post<Document>(`/v1/commercial/quotes/${quoteId}/convert`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'INVOICE'] });
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
        `/v1/commercial/documents/export?${queryParams}`,
        { responseType: 'blob' } as any
      );
      return response.data;
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
  const config = STATUS_CONFIG[status];

  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

// ============================================================
// COMPONENTS - Line Editor
// ============================================================

interface LineEditorProps {
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

const LineEditor: React.FC<LineEditorProps> = ({ lines, onChange, readOnly = false, currency = 'EUR' }) => {
  const [editingLine, setEditingLine] = useState<number | null>(null);

  const addLine = () => {
    const newLine: LineFormData = {
      id: `temp-${Date.now()}`,
      description: '',
      quantity: 1,
      unit: 'unité',
      unit_price: 0,
      discount_percent: 0,
      tax_rate: 20,
    };
    onChange([...lines, newLine]);
    setEditingLine(lines.length);
  };

  const updateLine = (index: number, updates: Partial<LineFormData>) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], ...updates };
    onChange(newLines);
  };

  const removeLine = (index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
    setEditingLine(null);
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

  return (
    <div className="azals-line-editor">
      <div className="azals-line-editor__header">
        <h3>Lignes du document</h3>
        {!readOnly && (
          <Button
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={addLine}
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
              <th style={{ width: '40%' }}>Description</th>
              <th style={{ width: '10%' }}>Qté</th>
              <th style={{ width: '15%' }}>Prix unit. HT</th>
              <th style={{ width: '10%' }}>Remise</th>
              <th style={{ width: '10%' }}>TVA</th>
              <th style={{ width: '10%' }}>Total HT</th>
              {!readOnly && <th style={{ width: '5%' }}></th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line);
              const isEditing = editingLine === index && !readOnly;

              return (
                <tr key={line.id || index} className={isEditing ? 'editing' : ''}>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        className="azals-input azals-input--sm"
                        value={line.description}
                        onChange={(e) => updateLine(index, { description: e.target.value })}
                        placeholder="Description"
                        autoFocus
                      />
                    ) : (
                      <span
                        className={readOnly ? '' : 'clickable'}
                        onClick={() => !readOnly && setEditingLine(index)}
                      >
                        {line.description || <em className="text-muted">Cliquez pour éditer</em>}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.quantity}
                        onChange={(e) => updateLine(index, { quantity: parseFloat(e.target.value) || 0 })}
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.quantity}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.unit_price}
                        onChange={(e) => updateLine(index, { unit_price: parseFloat(e.target.value) || 0 })}
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {formatCurrency(line.unit_price, currency)}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.discount_percent}
                        onChange={(e) => updateLine(index, { discount_percent: parseFloat(e.target.value) || 0 })}
                        min="0"
                        max="100"
                        step="0.1"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.discount_percent}%
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select
                        className="azals-select azals-select--sm"
                        value={line.tax_rate}
                        onChange={(e) => updateLine(index, { tax_rate: parseFloat(e.target.value) })}
                      >
                        {TVA_RATES.map((rate) => (
                          <option key={rate.value} value={rate.value}>
                            {rate.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.tax_rate}%
                      </span>
                    )}
                  </td>
                  <td className="text-right font-medium">
                    {formatCurrency(calc.subtotal, currency)}
                  </td>
                  {!readOnly && (
                    <td>
                      <button
                        type="button"
                        className="azals-btn-icon azals-btn-icon--danger"
                        onClick={() => removeLine(index)}
                        title="Supprimer"
                      >
                        <Trash2 size={14} />
                      </button>
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
    </div>
  );
};

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

  const { data, isLoading, refetch } = useDocuments(type, page, pageSize, filters);
  const deleteDocument = useDeleteDocument();
  const validateDocument = useValidateDocument();
  const convertQuote = useConvertQuoteToInvoice();
  const exportDocuments = useExportDocuments();

  const typeConfig = TYPE_CONFIG[type];
  // Utiliser les capabilities générales (invoicing.create) plutôt que granulaires (invoicing.quotes.create)
  const canCreate = useHasCapability('invoicing.create');
  const canEdit = useHasCapability('invoicing.edit');
  const canDelete = useHasCapability('invoicing.delete');
  const canValidate = useHasCapability('invoicing.edit'); // validate = edit permission

  const handleExport = async () => {
    try {
      const blob = await exportDocuments.mutateAsync({ type, filters });
      const url = window.URL.createObjectURL(new Blob([blob as any]));
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
      id: 'validate',
      label: 'Valider',
      icon: 'check',
      onClick: (row) => setValidateTarget(row),
      isHidden: (row) => row.status !== 'DRAFT' || !canValidate,
    },
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

  const typeConfig = TYPE_CONFIG[type];

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
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>Chargement...</span>
        </div>
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
              <label htmlFor="customer">Client *</label>
              <select
                id="customer"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className={`azals-select ${errors.customer ? 'azals-select--error' : ''}`}
                disabled={isEdit}
              >
                <option value="">Sélectionner un client</option>
                {customers?.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name} ({customer.code})
                  </option>
                ))}
              </select>
              {errors.customer && <span className="azals-form-error">{errors.customer}</span>}
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

  const { data: document, isLoading } = useDocument(id || '');
  const validateDocument = useValidateDocument();
  const convertQuote = useConvertQuoteToInvoice();

  const typeConfig = TYPE_CONFIG[type];
  const canEdit = useHasCapability('invoicing.edit');
  const canValidate = useHasCapability('invoicing.edit');

  if (isLoading) {
    return (
      <PageWrapper title={typeConfig.label}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>Chargement...</span>
        </div>
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
// EXPORTS - Page Components
// ============================================================

export const QuotesPage: React.FC = () => <DocumentListPage type="QUOTE" />;
export const InvoicesPage: React.FC = () => <DocumentListPage type="INVOICE" />;

export const QuoteFormPage: React.FC = () => <DocumentFormPage type="QUOTE" />;
export const InvoiceFormPage: React.FC = () => <DocumentFormPage type="INVOICE" />;

export const QuoteDetailPage: React.FC = () => <DocumentDetailPage type="QUOTE" />;
export const InvoiceDetailPageComponent: React.FC = () => <DocumentDetailPage type="INVOICE" />;

// ============================================================
// EXPORTS - Router
// ============================================================

export const InvoicingRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InvoicingDashboard />} />

    <Route path="quotes" element={<QuotesPage />} />
    <Route path="quotes/new" element={<QuoteFormPage />} />
    <Route path="quotes/:id" element={<QuoteDetailPage />} />
    <Route path="quotes/:id/edit" element={<QuoteFormPage />} />

    <Route path="invoices" element={<InvoicesPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailPageComponent />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
  </Routes>
);

export default InvoicingRoutes;
