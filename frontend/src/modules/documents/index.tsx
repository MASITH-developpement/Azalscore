/**
 * AZALSCORE - Module Documents Unifié
 *
 * VUE UNIQUE pour tous les documents commerciaux :
 * - Devis (QUOTE)
 * - Factures (INVOICE)
 * - Commandes (ORDER)
 * - Avoirs (CREDIT_NOTE)
 * - Commandes fournisseurs (PURCHASE_ORDER)
 * - Factures fournisseurs (PURCHASE_INVOICE)
 *
 * Principes :
 * - Une seule page de travail
 * - Un seul formulaire universel
 * - Type de document = état (pas une route)
 * - Saisie ultra rapide
 * - Aucun changement de page pendant la saisie
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  FileText,
  List,
  Edit3,
  Check,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Save,
  X,
  ChevronDown,
} from 'lucide-react';

import { api } from '@core/api-client';
import { useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ConfirmDialog } from '@ui/actions';

import { useTranslation } from '@/i18n';
import {
  useDocumentsStore,
  DocumentType,
  DocumentStatus,
  Document,
  DocumentLine,
  DocumentFilters,
  DOCUMENT_TYPE_CONFIG,
  calculateLineTotal,
  calculateDocumentTotals,
} from './store';

import type { PaginatedResponse, TableColumn, TableAction } from '@/types';

// ============================================================
// TYPES API
// ============================================================

interface Partner {
  id: string;
  code: string;
  name: string;
  email?: string;
}

interface ApiDocument {
  id: string;
  number: string;
  type: string;
  status: string;
  customer_id?: string;
  supplier_id?: string;
  customer_name?: string;
  supplier_name?: string;
  customer_code?: string;
  supplier_code?: string;
  date: string;
  due_date?: string;
  validity_date?: string;
  expected_date?: string;
  reference?: string;
  parent_id?: string;
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  lines: ApiDocumentLine[];
  validated_at?: string;
  validated_by?: string;
  created_at: string;
  created_by: string;
  updated_at: string;
}

interface ApiDocumentLine {
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
}

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(amount);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

/**
 * Convertir un document API vers le format du store
 */
const apiToStoreDocument = (api: ApiDocument): Document => {
  const isSales = ['QUOTE', 'INVOICE', 'ORDER', 'CREDIT_NOTE', 'PROFORMA', 'DELIVERY'].includes(api.type);

  return {
    id: api.id,
    number: api.number,
    type: api.type as DocumentType,
    status: api.status as DocumentStatus,
    partnerId: isSales ? api.customer_id! : api.supplier_id!,
    partnerName: isSales ? api.customer_name : api.supplier_name,
    partnerCode: isSales ? api.customer_code : api.supplier_code,
    date: api.date,
    dueDate: api.due_date,
    validityDate: api.validity_date,
    expectedDate: api.expected_date,
    reference: api.reference,
    parentId: api.parent_id,
    subtotal: api.subtotal,
    discountPercent: api.discount_percent,
    discountAmount: api.discount_amount,
    taxAmount: api.tax_amount,
    total: api.total,
    currency: api.currency,
    notes: api.notes,
    internalNotes: api.internal_notes,
    lines: api.lines.map((l) => ({
      id: l.id,
      lineNumber: l.line_number,
      productId: l.product_id,
      productCode: l.product_code,
      description: l.description,
      quantity: l.quantity,
      unit: l.unit,
      unitPrice: l.unit_price,
      discountPercent: l.discount_percent,
      taxRate: l.tax_rate,
      subtotal: l.subtotal,
      taxAmount: l.tax_amount,
      total: l.total,
      notes: l.notes,
    })),
    validatedAt: api.validated_at,
    validatedBy: api.validated_by,
    createdAt: api.created_at,
    createdBy: api.created_by,
    updatedAt: api.updated_at,
  };
};

/**
 * Convertir un document store vers le format API
 */
const storeToApiDocument = (doc: Document): Record<string, unknown> => {
  const config = DOCUMENT_TYPE_CONFIG[doc.type];
  const isSales = config.category === 'SALES';

  return {
    type: doc.type,
    [isSales ? 'customer_id' : 'supplier_id']: doc.partnerId,
    date: doc.date,
    due_date: doc.dueDate,
    validity_date: doc.validityDate,
    expected_date: doc.expectedDate,
    reference: doc.reference,
    notes: doc.notes,
    internal_notes: doc.internalNotes,
    lines: doc.lines.map((l) => ({
      description: l.description,
      quantity: l.quantity,
      unit: l.unit,
      unit_price: l.unitPrice,
      discount_percent: l.discountPercent,
      tax_rate: l.taxRate,
    })),
  };
};

// ============================================================
// API HOOKS
// ============================================================

/**
 * Obtenir l'endpoint API selon le type de document
 */
const getApiEndpoint = (type: DocumentType): string => {
  const config = DOCUMENT_TYPE_CONFIG[type];
  if (config.category === 'PURCHASES') {
    return type === 'PURCHASE_ORDER' ? '/v1/purchases/orders' : '/v1/purchases/invoices';
  }
  return '/v1/commercial/documents';
};

/**
 * Hook pour charger la liste des documents
 */
const useDocumentsList = (type: DocumentType, page: number, pageSize: number, filters: DocumentFilters) => {
  const config = DOCUMENT_TYPE_CONFIG[type];
  const endpoint = getApiEndpoint(type);

  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  // Ajouter le type pour les documents commerciaux
  if (config.category === 'SALES') {
    params.append('type', type);
  }

  if (filters.status) params.append('status', filters.status);
  if (filters.search) params.append('search', filters.search);
  if (filters.partnerId) {
    params.append(config.partnerType === 'customer' ? 'customer_id' : 'supplier_id', filters.partnerId);
  }
  if (filters.dateFrom) params.append('date_from', filters.dateFrom);
  if (filters.dateTo) params.append('date_to', filters.dateTo);

  return useQuery({
    queryKey: ['documents', type, page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ApiDocument>>(
        `${endpoint}?${params.toString()}`
      );
      return response as unknown as PaginatedResponse<ApiDocument>;
    },
  });
};

/**
 * Hook pour charger un document unique
 * Note: Préparé pour l'édition de documents existants (usage futur)
 */
const _useDocumentDetail = (type: DocumentType, id: string) => {
  const endpoint = getApiEndpoint(type);

  return useQuery({
    queryKey: ['document', type, id],
    queryFn: async () => {
      const response = await api.get<ApiDocument>(`${endpoint}/${id}`);
      return apiToStoreDocument(response as unknown as ApiDocument);
    },
    enabled: !!id,
  });
};

/**
 * Hook pour charger les partenaires (clients ou fournisseurs)
 */
const usePartners = (type: 'customer' | 'supplier') => {
  const endpoint = type === 'customer'
    ? '/v1/partners/clients?page_size=500&is_active=true'
    : '/v1/purchases/suppliers?page_size=500&status=APPROVED';

  return useQuery({
    queryKey: ['partners', type],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Partner>>(endpoint);
      return (response as unknown as PaginatedResponse<Partner>).items;
    },
    staleTime: 5 * 60 * 1000, // Cache 5 minutes
  });
};

/**
 * Hook pour créer un document
 */
const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (doc: Document) => {
      const endpoint = getApiEndpoint(doc.type);
      const payload = storeToApiDocument(doc);
      const response = await api.post<ApiDocument>(endpoint, payload);
      return apiToStoreDocument(response as unknown as ApiDocument);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

/**
 * Hook pour mettre à jour un document
 */
const useUpdateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, doc }: { id: string; doc: Document }) => {
      const endpoint = getApiEndpoint(doc.type);
      const payload = storeToApiDocument(doc);
      const response = await api.put<ApiDocument>(`${endpoint}/${id}`, payload);
      return apiToStoreDocument(response as unknown as ApiDocument);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.type, data.id] });
    },
  });
};

/**
 * Hook pour supprimer un document
 */
const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ type, id }: { type: DocumentType; id: string }) => {
      const endpoint = getApiEndpoint(type);
      await api.delete(`${endpoint}/${id}`);
      return { type, id };
    },
    onSuccess: ({ type }) => {
      queryClient.invalidateQueries({ queryKey: ['documents', type] });
    },
  });
};

/**
 * Hook pour valider un document
 */
const useValidateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ type, id }: { type: DocumentType; id: string }) => {
      const endpoint = getApiEndpoint(type);
      const response = await api.post<ApiDocument>(`${endpoint}/${id}/validate`);
      return apiToStoreDocument(response as unknown as ApiDocument);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.type, data.id] });
    },
  });
};

// ============================================================
// COMPOSANTS - Status Badge
// ============================================================

interface StatusBadgeProps {
  status: DocumentStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const { t } = useTranslation();

  const colorMap: Record<DocumentStatus, string> = {
    DRAFT: 'gray',
    PENDING: 'yellow',
    VALIDATED: 'blue',
    SENT: 'blue',
    ACCEPTED: 'green',
    REJECTED: 'red',
    DELIVERED: 'green',
    INVOICED: 'purple',
    PAID: 'green',
    PARTIAL: 'yellow',
    CANCELLED: 'red',
    CONFIRMED: 'blue',
    RECEIVED: 'green',
  };

  const iconMap: Record<DocumentStatus, React.ReactNode> = {
    DRAFT: <Clock size={14} />,
    PENDING: <Clock size={14} />,
    VALIDATED: <CheckCircle2 size={14} />,
    SENT: <CheckCircle2 size={14} />,
    ACCEPTED: <CheckCircle2 size={14} />,
    REJECTED: <X size={14} />,
    DELIVERED: <CheckCircle2 size={14} />,
    INVOICED: <FileText size={14} />,
    PAID: <CheckCircle2 size={14} />,
    PARTIAL: <Clock size={14} />,
    CANCELLED: <X size={14} />,
    CONFIRMED: <CheckCircle2 size={14} />,
    RECEIVED: <CheckCircle2 size={14} />,
  };

  return (
    <span className={`azals-badge azals-badge--${colorMap[status]}`}>
      {iconMap[status]}
      <span className="ml-1">{t(`documents.status.${status}`)}</span>
    </span>
  );
};

// ============================================================
// COMPOSANTS - Type Selector
// ============================================================

interface TypeSelectorProps {
  value: DocumentType;
  onChange: (type: DocumentType) => void;
  disabled?: boolean;
}

const TypeSelector: React.FC<TypeSelectorProps> = ({ value, onChange, disabled }) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const categories = {
    SALES: ['QUOTE', 'INVOICE', 'ORDER', 'CREDIT_NOTE'] as DocumentType[],
    PURCHASES: ['PURCHASE_ORDER', 'PURCHASE_INVOICE'] as DocumentType[],
  };

  const canAccessSales = useHasCapability('invoicing.view');
  const canAccessPurchases = useHasCapability('purchases.view');

  return (
    <div className="azals-type-selector">
      <button
        type="button"
        className="azals-type-selector__trigger"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
      >
        <FileText size={18} />
        <span>{t(`documents.types.${value}`)}</span>
        <ChevronDown size={16} className={isOpen ? 'rotate-180' : ''} />
      </button>

      {isOpen && (
        <>
          <div
            className="azals-type-selector__overlay"
            onClick={() => setIsOpen(false)}
          />
          <div className="azals-type-selector__dropdown">
            {canAccessSales && (
              <div className="azals-type-selector__group">
                <div className="azals-type-selector__group-label">
                  {t('partners.customers')}
                </div>
                {categories.SALES.map((type) => (
                  <button
                    key={type}
                    type="button"
                    className={`azals-type-selector__option ${value === type ? 'active' : ''}`}
                    onClick={() => {
                      onChange(type);
                      setIsOpen(false);
                    }}
                  >
                    {t(`documents.types.${type}`)}
                  </button>
                ))}
              </div>
            )}

            {canAccessPurchases && (
              <div className="azals-type-selector__group">
                <div className="azals-type-selector__group-label">
                  {t('partners.suppliers')}
                </div>
                {categories.PURCHASES.map((type) => (
                  <button
                    key={type}
                    type="button"
                    className={`azals-type-selector__option ${value === type ? 'active' : ''}`}
                    onClick={() => {
                      onChange(type);
                      setIsOpen(false);
                    }}
                  >
                    {t(`documents.types.${type}`)}
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// ============================================================
// COMPOSANTS - Mode Toggle
// ============================================================

interface ModeToggleProps {
  mode: 'entry' | 'list';
  onChange: (mode: 'entry' | 'list') => void;
}

const ModeToggle: React.FC<ModeToggleProps> = ({ mode, onChange }) => {
  const { t } = useTranslation();

  return (
    <div className="azals-mode-toggle">
      <button
        type="button"
        className={`azals-mode-toggle__btn ${mode === 'entry' ? 'active' : ''}`}
        onClick={() => onChange('entry')}
      >
        <Edit3 size={16} />
        <span>{t('documents.modes.entry')}</span>
      </button>
      <button
        type="button"
        className={`azals-mode-toggle__btn ${mode === 'list' ? 'active' : ''}`}
        onClick={() => onChange('list')}
      >
        <List size={16} />
        <span>{t('documents.modes.list')}</span>
      </button>
    </div>
  );
};

// ============================================================
// COMPOSANTS - Line Editor
// ============================================================

interface LineEditorProps {
  lines: DocumentLine[];
  onAddLine: () => void;
  onUpdateLine: (index: number, updates: Partial<DocumentLine>) => void;
  onRemoveLine: (index: number) => void;
  readOnly?: boolean;
  currency?: string;
}

const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

const LineEditor: React.FC<LineEditorProps> = ({
  lines,
  onAddLine,
  onUpdateLine,
  onRemoveLine,
  readOnly = false,
  currency = 'EUR',
}) => {
  const { t } = useTranslation();
  const [editingLine, setEditingLine] = useState<number | null>(null);

  const totals = useMemo(() => calculateDocumentTotals(lines), [lines]);

  return (
    <div className="azals-line-editor">
      <div className="azals-line-editor__header">
        <h3>{t('documents.lines.title')}</h3>
        {!readOnly && (
          <Button size="sm" leftIcon={<Plus size={14} />} onClick={onAddLine}>
            {t('documents.lines.addLine')}
          </Button>
        )}
      </div>

      {lines.length === 0 ? (
        <div className="azals-line-editor__empty">
          <AlertCircle size={24} />
          <p>
            {t('documents.lines.noLines')}
            {!readOnly && `. ${t('documents.lines.clickToAdd')}`}
          </p>
        </div>
      ) : (
        <table className="azals-line-editor__table">
          <thead>
            <tr>
              <th style={{ width: '40%' }}>{t('documents.lines.description')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.quantity')}</th>
              <th style={{ width: '15%' }}>{t('documents.lines.unitPrice')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.discount')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.tax')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.lineTotal')}</th>
              {!readOnly && <th style={{ width: '5%' }}></th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line);
              const isEditing = editingLine === index && !readOnly;

              return (
                <tr key={line.id || line.tempId || index} className={isEditing ? 'editing' : ''}>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        className="azals-input azals-input--sm"
                        value={line.description}
                        onChange={(e) => onUpdateLine(index, { description: e.target.value })}
                        placeholder={t('documents.lines.description')}
                        autoFocus
                      />
                    ) : (
                      <span
                        className={readOnly ? '' : 'clickable'}
                        onClick={() => !readOnly && setEditingLine(index)}
                      >
                        {line.description || (
                          <em className="text-muted">{t('documents.lines.clickToEdit')}</em>
                        )}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.quantity}
                        onChange={(e) => onUpdateLine(index, { quantity: parseFloat(e.target.value) || 0 })}
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
                        value={line.unitPrice}
                        onChange={(e) => onUpdateLine(index, { unitPrice: parseFloat(e.target.value) || 0 })}
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {formatCurrency(line.unitPrice, currency)}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.discountPercent}
                        onChange={(e) => onUpdateLine(index, { discountPercent: parseFloat(e.target.value) || 0 })}
                        min="0"
                        max="100"
                        step="0.1"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.discountPercent}%
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select
                        className="azals-select azals-select--sm"
                        value={line.taxRate}
                        onChange={(e) => onUpdateLine(index, { taxRate: parseFloat(e.target.value) })}
                      >
                        {TVA_RATES.map((rate) => (
                          <option key={rate.value} value={rate.value}>
                            {rate.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.taxRate}%
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
                        onClick={() => onRemoveLine(index)}
                        title={t('documents.lines.removeLine')}
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
          <span>{t('documents.fields.totalHT')}</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row">
          <span>{t('documents.fields.totalTVA')}</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row azals-line-editor__total-row--main">
          <span>{t('documents.fields.totalTTC')}</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// COMPOSANTS - Document Form (Formulaire Universel)
// ============================================================

const DocumentForm: React.FC = () => {
  const { t } = useTranslation();

  // Store
  const {
    currentDocument,
    isDirty,
    setCurrentDocument,
    updateCurrentDocument,
    resetCurrentDocument,
    addLine,
    updateLine,
    removeLine,
    getTypeConfig,
    isEditable,
  } = useDocumentsStore();

  // Config du type actuel
  const typeConfig = getTypeConfig();
  const editable = isEditable();

  // Charger les partenaires selon le type
  const { data: partners, isLoading: loadingPartners } = usePartners(typeConfig.partnerType);

  // Mutations
  const createDocument = useCreateDocument();
  const updateDocument = useUpdateDocument();
  const validateDocument = useValidateDocument();

  // États locaux pour les modals
  const [showValidateModal, setShowValidateModal] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialiser un nouveau document si nécessaire
  useEffect(() => {
    if (!currentDocument) {
      resetCurrentDocument();
    }
  }, [currentDocument, resetCurrentDocument]);

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    const doc = currentDocument;

    if (!doc) return false;

    if (!doc.partnerId) {
      newErrors.partner = t('validation.selectOption');
    }
    if (!doc.date) {
      newErrors.date = t('validation.required');
    }
    if (doc.lines.length === 0) {
      newErrors.lines = t('validation.addAtLeastOneLine');
    }
    if (doc.lines.some((l) => !l.description.trim())) {
      newErrors.lines = t('validation.allLinesMustHaveDescription');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Enregistrer
  const handleSave = async () => {
    if (!validate() || !currentDocument) return;

    try {
      if (currentDocument.id) {
        const updated = await updateDocument.mutateAsync({
          id: currentDocument.id,
          doc: currentDocument,
        });
        setCurrentDocument(updated);
      } else {
        const created = await createDocument.mutateAsync(currentDocument);
        setCurrentDocument(created);
      }
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  // Valider
  const handleValidate = async () => {
    if (!currentDocument?.id) return;

    try {
      const validated = await validateDocument.mutateAsync({
        type: currentDocument.type,
        id: currentDocument.id,
      });
      setCurrentDocument(validated);
      setShowValidateModal(false);
    } catch (error) {
      console.error('Validate failed:', error);
    }
  };

  const isSubmitting = createDocument.isPending || updateDocument.isPending;
  const isValidating = validateDocument.isPending;

  if (!currentDocument) {
    return (
      <div className="azals-loading">
        <RefreshCw className="animate-spin" size={24} />
        <span>{t('common.loading')}</span>
      </div>
    );
  }

  return (
    <div className="azals-document-form">
      {/* En-tête du document */}
      <Card className="mb-4">
        <div className="azals-document-form__header">
          {currentDocument.number && (
            <div className="azals-document-form__number">
              <span className="azals-label">{t('documents.fields.number')}</span>
              <strong>{currentDocument.number}</strong>
              <StatusBadge status={currentDocument.status} />
            </div>
          )}
        </div>

        <Grid cols={typeConfig.hasDueDate || typeConfig.hasValidityDate || typeConfig.hasExpectedDate ? 3 : 2} gap="md">
          {/* Partenaire */}
          <div className="azals-form-field">
            <label htmlFor="partner">
              {t(typeConfig.partnerType === 'customer' ? 'documents.fields.customer' : 'documents.fields.supplier')} *
            </label>
            <select
              id="partner"
              value={currentDocument.partnerId}
              onChange={(e) => updateCurrentDocument({ partnerId: e.target.value })}
              className={`azals-select ${errors.partner ? 'azals-select--error' : ''}`}
              disabled={!editable || loadingPartners}
            >
              <option value="">
                {t(typeConfig.partnerType === 'customer' ? 'documents.placeholders.selectCustomer' : 'documents.placeholders.selectSupplier')}
              </option>
              {partners?.map((partner) => (
                <option key={partner.id} value={partner.id}>
                  {partner.name} ({partner.code})
                </option>
              ))}
            </select>
            {errors.partner && <span className="azals-form-error">{errors.partner}</span>}
          </div>

          {/* Date */}
          <div className="azals-form-field">
            <label htmlFor="date">{t('documents.fields.date')} *</label>
            <input
              type="date"
              id="date"
              value={currentDocument.date}
              onChange={(e) => updateCurrentDocument({ date: e.target.value })}
              className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
              disabled={!editable}
            />
            {errors.date && <span className="azals-form-error">{errors.date}</span>}
          </div>

          {/* Date de validité (devis) */}
          {typeConfig.hasValidityDate && (
            <div className="azals-form-field">
              <label htmlFor="validityDate">{t('documents.fields.validityDate')}</label>
              <input
                type="date"
                id="validityDate"
                value={currentDocument.validityDate || ''}
                onChange={(e) => updateCurrentDocument({ validityDate: e.target.value })}
                className="azals-input"
                disabled={!editable}
              />
            </div>
          )}

          {/* Date d'échéance (factures) */}
          {typeConfig.hasDueDate && (
            <div className="azals-form-field">
              <label htmlFor="dueDate">{t('documents.fields.dueDate')}</label>
              <input
                type="date"
                id="dueDate"
                value={currentDocument.dueDate || ''}
                onChange={(e) => updateCurrentDocument({ dueDate: e.target.value })}
                className="azals-input"
                disabled={!editable}
              />
            </div>
          )}

          {/* Date prévue (commandes) */}
          {typeConfig.hasExpectedDate && (
            <div className="azals-form-field">
              <label htmlFor="expectedDate">{t('documents.fields.expectedDate')}</label>
              <input
                type="date"
                id="expectedDate"
                value={currentDocument.expectedDate || ''}
                onChange={(e) => updateCurrentDocument({ expectedDate: e.target.value })}
                className="azals-input"
                disabled={!editable}
              />
            </div>
          )}
        </Grid>

        {/* Notes */}
        <div className="azals-form-field mt-4">
          <label htmlFor="notes">{t('documents.fields.notes')}</label>
          <textarea
            id="notes"
            value={currentDocument.notes || ''}
            onChange={(e) => updateCurrentDocument({ notes: e.target.value })}
            className="azals-textarea"
            rows={2}
            placeholder={t('documents.placeholders.notesPlaceholder')}
            disabled={!editable}
          />
        </div>
      </Card>

      {/* Lignes */}
      <Card className="mb-4">
        {errors.lines && (
          <div className="azals-alert azals-alert--error mb-4">
            <AlertCircle size={16} />
            <span>{errors.lines}</span>
          </div>
        )}
        <LineEditor
          lines={currentDocument.lines}
          onAddLine={addLine}
          onUpdateLine={updateLine}
          onRemoveLine={removeLine}
          readOnly={!editable}
          currency={currentDocument.currency}
        />
      </Card>

      {/* Actions */}
      <div className="azals-form-actions">
        <Button
          variant="ghost"
          onClick={resetCurrentDocument}
          disabled={!isDirty}
        >
          {t('common.cancel')}
        </Button>

        {editable && (
          <>
            <Button
              variant="secondary"
              leftIcon={<Save size={16} />}
              onClick={handleSave}
              isLoading={isSubmitting}
              disabled={!isDirty}
            >
              {t('common.save')}
            </Button>

            {currentDocument.id && currentDocument.status === 'DRAFT' && (
              <Button
                leftIcon={<Check size={16} />}
                onClick={() => setShowValidateModal(true)}
                disabled={isDirty}
              >
                {t('documents.actions.validate')}
              </Button>
            )}
          </>
        )}
      </div>

      {/* Modal de validation */}
      {showValidateModal && (
        <ConfirmDialog
          title={t('documents.actions.validate')}
          message={
            <>
              <p>{t('documents.messages.confirmValidate')}</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                {t('documents.messages.validationWarning')}
              </p>
            </>
          }
          variant="warning"
          confirmLabel={t('documents.actions.validate')}
          onConfirm={handleValidate}
          onCancel={() => setShowValidateModal(false)}
          isLoading={isValidating}
        />
      )}
    </div>
  );
};

// ============================================================
// COMPOSANTS - Document List
// ============================================================

const DocumentList: React.FC = () => {
  const { t } = useTranslation();

  // Store
  const {
    documentType,
    filters,
    pagination,
    setFilters,
    resetFilters,
    setPage,
    setPageSize,
    setTotal,
    setCurrentDocument,
    setMode,
    newDocument,
    getTypeConfig,
  } = useDocumentsStore();

  const typeConfig = getTypeConfig();

  // Charger les documents
  const { data, isLoading, refetch } = useDocumentsList(
    documentType,
    pagination.page,
    pagination.pageSize,
    filters
  );

  // Charger les partenaires pour le filtre
  const { data: partners } = usePartners(typeConfig.partnerType);

  // Mutations
  const deleteDocument = useDeleteDocument();
  const validateDocument = useValidateDocument();

  // États locaux
  const [deleteTarget, setDeleteTarget] = useState<ApiDocument | null>(null);
  const [validateTarget, setValidateTarget] = useState<ApiDocument | null>(null);

  // Mettre à jour le total de pagination
  useEffect(() => {
    if (data?.total !== undefined) {
      setTotal(data.total);
    }
  }, [data?.total, setTotal]);

  // Ouvrir un document pour édition
  const handleOpenDocument = (doc: ApiDocument) => {
    setCurrentDocument(apiToStoreDocument(doc));
    setMode('entry');
  };

  // Créer un nouveau document
  const handleNewDocument = () => {
    newDocument();
  };

  // Colonnes du tableau
  const columns: TableColumn<ApiDocument>[] = [
    {
      id: 'number',
      header: t('documents.fields.number'),
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <button
          type="button"
          className="azals-link"
          onClick={() => handleOpenDocument(row)}
        >
          {value as string}
        </button>
      ),
    },
    {
      id: 'partner',
      header: t(typeConfig.partnerType === 'customer' ? 'documents.fields.customer' : 'documents.fields.supplier'),
      accessor: typeConfig.partnerType === 'customer' ? 'customer_name' : 'supplier_name',
      sortable: true,
    },
    {
      id: 'date',
      header: t('documents.fields.date'),
      accessor: 'date',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: t('documents.fields.status'),
      accessor: 'status',
      render: (value) => <StatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'total',
      header: t('documents.fields.totalTTC'),
      accessor: 'total',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  // Actions du tableau
  const actions: TableAction<ApiDocument>[] = [
    {
      id: 'view',
      label: t('common.view'),
      icon: 'eye',
      onClick: handleOpenDocument,
    },
    {
      id: 'edit',
      label: t('common.edit'),
      icon: 'edit',
      onClick: handleOpenDocument,
      isHidden: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'validate',
      label: t('documents.actions.validate'),
      icon: 'check',
      onClick: (row) => setValidateTarget(row),
      isHidden: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'delete',
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: (row) => row.status !== 'DRAFT',
    },
  ];

  // Options de statut pour le filtre
  const statusOptions = typeConfig.allowedStatuses.map((status) => ({
    value: status,
    label: t(`documents.status.${status}`),
  }));

  return (
    <div className="azals-document-list">
      {/* Barre de filtres */}
      <div className="azals-filter-bar mb-4">
        <div className="azals-filter-bar__search">
          <input
            type="text"
            placeholder={t('documents.placeholders.searchDocuments')}
            value={filters.search || ''}
            onChange={(e) => setFilters({ search: e.target.value })}
            className="azals-input"
          />
        </div>

        <div className="azals-filter-bar__fields">
          <select
            value={filters.status || ''}
            onChange={(e) => setFilters({ status: (e.target.value as DocumentStatus) || undefined })}
            className="azals-select"
          >
            <option value="">{t('documents.filters.allStatuses')}</option>
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          {partners && partners.length > 0 && (
            <select
              value={filters.partnerId || ''}
              onChange={(e) => setFilters({ partnerId: e.target.value || undefined })}
              className="azals-select"
            >
              <option value="">
                {t(typeConfig.partnerType === 'customer' ? 'partners.customers' : 'partners.suppliers')}
              </option>
              {partners.map((p) => (
                <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
              ))}
            </select>
          )}
        </div>

        <div className="azals-filter-bar__actions">
          <Button variant="ghost" onClick={resetFilters}>
            {t('common.reset')}
          </Button>
          <Button leftIcon={<Plus size={16} />} onClick={handleNewDocument}>
            {t('documents.newDocument')}
          </Button>
        </div>
      </div>

      {/* Tableau */}
      <Card>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page: pagination.page,
            pageSize: pagination.pageSize,
            total: pagination.total,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage={t(`documents.empty.noDocuments`)}
        />
      </Card>

      {/* Modal de suppression */}
      {deleteTarget && (
        <ConfirmDialog
          title={t('common.delete')}
          message={t('documents.messages.confirmDelete')}
          variant="danger"
          onConfirm={async () => {
            await deleteDocument.mutateAsync({
              type: documentType,
              id: deleteTarget.id,
            });
            setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteDocument.isPending}
        />
      )}

      {/* Modal de validation */}
      {validateTarget && (
        <ConfirmDialog
          title={t('documents.actions.validate')}
          message={
            <>
              <p>{t('documents.messages.confirmValidate')}</p>
              <p className="text-warning mt-2">
                <AlertCircle size={14} className="inline mr-1" />
                {t('documents.messages.validationWarning')}
              </p>
            </>
          }
          variant="warning"
          confirmLabel={t('documents.actions.validate')}
          onConfirm={async () => {
            await validateDocument.mutateAsync({
              type: documentType,
              id: validateTarget.id,
            });
            setValidateTarget(null);
          }}
          onCancel={() => setValidateTarget(null)}
          isLoading={validateDocument.isPending}
        />
      )}
    </div>
  );
};

// ============================================================
// PAGE PRINCIPALE
// ============================================================

const DocumentsPage: React.FC = () => {
  const { t } = useTranslation();

  // Store
  const {
    mode,
    documentType,
    isDirty,
    setMode,
    setDocumentType,
  } = useDocumentsStore();

  // Avertissement avant de changer de type si le document n'est pas sauvegardé
  const handleTypeChange = (newType: DocumentType) => {
    if (isDirty) {
      if (!window.confirm(t('common.warning') + ': ' + t('documents.messages.cannotEdit'))) {
        return;
      }
    }
    setDocumentType(newType);
  };

  return (
    <PageWrapper
      title={t('documents.title')}
      actions={
        <div className="azals-page-actions">
          <TypeSelector
            value={documentType}
            onChange={handleTypeChange}
          />
          <ModeToggle
            mode={mode}
            onChange={setMode}
          />
        </div>
      }
    >
      {mode === 'entry' ? <DocumentForm /> : <DocumentList />}
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

export const DocumentsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<DocumentsPage />} />
  </Routes>
);

export default DocumentsRoutes;
