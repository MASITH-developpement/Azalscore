/**
 * AZALSCORE Module - Achats V1
 * Fournisseurs, Commandes, Factures fournisseurs
 *
 * V1 Scope: CRUD simple avec workflow BROUILLON → VALIDÉ
 * Exclusions: Paiements, comptabilité, PDF, réceptions, devis
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  ShoppingCart,
  FileText,
  Users,
  Edit,
  Trash2,
  Eye,
  CheckCircle2,
  Download,
  Search,
  Filter,
  X,
  ArrowLeft,
  Save,
  AlertTriangle,
  AlertCircle,
  Clock,
  RefreshCw,
  Building2,
} from 'lucide-react';
import { api } from '@core/api-client';
import { SmartSelector, FieldConfig } from '@/components/SmartSelector';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup, Modal, ConfirmDialog, DropdownMenu } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, TableAction, DashboardKPI } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

interface Supplier {
  id: string;
  code: string;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  notes?: string;
  status: 'PROSPECT' | 'PENDING' | 'APPROVED' | 'BLOCKED' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

interface SupplierCreate {
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  notes?: string;
}

interface PurchaseOrderLine {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent: number;
}

interface PurchaseOrder {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  date: string;
  expected_date?: string;
  status: 'DRAFT' | 'SENT' | 'CONFIRMED' | 'PARTIAL' | 'RECEIVED' | 'INVOICED' | 'CANCELLED';
  reference?: string;
  notes?: string;
  lines: PurchaseOrderLine[];
  total_ht: number;
  total_tax: number;
  total_ttc: number;
  currency: string;
  validated_at?: string;
  validated_by?: string;
  created_at: string;
  updated_at: string;
}

interface PurchaseInvoice {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  order_id?: string;
  order_number?: string;
  date: string;
  due_date?: string;
  status: 'DRAFT' | 'VALIDATED' | 'PAID' | 'PARTIAL' | 'CANCELLED';
  supplier_reference?: string;
  notes?: string;
  lines: PurchaseOrderLine[];
  total_ht: number;
  total_tax: number;
  total_ttc: number;
  currency: string;
  validated_at?: string;
  validated_by?: string;
  created_at: string;
  updated_at: string;
}

interface PurchaseSummary {
  pending_orders: number;
  pending_value: number;
  validated_this_month: number;
  pending_invoices: number;
  total_suppliers: number;
  active_suppliers: number;
}

interface FilterState {
  search?: string;
  status?: string;
  supplier_id?: string;
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// CONSTANTS & HELPERS
// ============================================================================

const ORDER_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  SENT: { label: 'Validée', color: 'blue' },
  CONFIRMED: { label: 'Confirmée', color: 'orange' },
  PARTIAL: { label: 'Partielle', color: 'yellow' },
  RECEIVED: { label: 'Reçue', color: 'green' },
  INVOICED: { label: 'Facturée', color: 'purple' },
  CANCELLED: { label: 'Annulée', color: 'red' },
};

const INVOICE_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  VALIDATED: { label: 'Validée', color: 'blue' },
  PAID: { label: 'Payée', color: 'green' },
  PARTIAL: { label: 'Partielle', color: 'yellow' },
  CANCELLED: { label: 'Annulée', color: 'red' },
};

const SUPPLIER_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  PROSPECT: { label: 'Prospect', color: 'gray' },
  PENDING: { label: 'En attente', color: 'yellow' },
  APPROVED: { label: 'Approuvé', color: 'green' },
  BLOCKED: { label: 'Bloqué', color: 'red' },
  INACTIVE: { label: 'Inactif', color: 'gray' },
};

const PAYMENT_TERMS_OPTIONS = [
  { value: 'IMMEDIATE', label: 'Paiement immédiat' },
  { value: 'NET15', label: 'Net 15 jours' },
  { value: 'NET30', label: 'Net 30 jours' },
  { value: 'NET45', label: 'Net 45 jours' },
  { value: 'NET60', label: 'Net 60 jours' },
  { value: 'EOM', label: 'Fin de mois' },
  { value: 'EOM30', label: 'Fin de mois + 30' },
];

const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5.5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

// Configuration pour création inline de fournisseur
const SUPPLIER_CREATE_FIELDS: FieldConfig[] = [
  { key: 'name', label: 'Nom', type: 'text', required: true },
  { key: 'contact_name', label: 'Contact', type: 'text' },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Téléphone', type: 'tel' },
];

const formatCurrency = (value: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(value);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

// ============================================================================
// API HOOKS - Suppliers
// ============================================================================

const useSuppliers = (page = 1, pageSize = 25, filters?: FilterState) => {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);

  return useQuery({
    queryKey: ['purchases', 'suppliers', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Supplier>>(
        `/v1/purchases/suppliers?${params.toString()}`
      );
      return response.data;
    },
  });
};

const useSupplier = (id: string) => {
  return useQuery({
    queryKey: ['purchases', 'suppliers', id],
    queryFn: async () => {
      const response = await api.get<Supplier>(`/v1/purchases/suppliers/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
};

const useSuppliersLookup = () => {
  return useQuery({
    queryKey: ['purchases', 'suppliers', 'lookup'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Supplier>>(
        '/v1/purchases/suppliers?page_size=500&status=APPROVED'
      );
      return response.data.items;
    },
  });
};

const useCreateSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SupplierCreate) => {
      const response = await api.post<Supplier>('/v1/purchases/suppliers', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'suppliers'] });
    },
  });
};

const useUpdateSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<SupplierCreate> }) => {
      const response = await api.put<Supplier>(`/v1/purchases/suppliers/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'suppliers'] });
    },
  });
};

const useDeleteSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/suppliers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'suppliers'] });
    },
  });
};

// ============================================================================
// API HOOKS - Purchase Orders
// ============================================================================

const usePurchaseSummary = () => {
  return useQuery({
    queryKey: ['purchases', 'summary'],
    queryFn: async () => {
      const response = await api.get<PurchaseSummary>('/v1/purchases/summary');
      return response.data;
    },
  });
};

const usePurchaseOrders = (page = 1, pageSize = 25, filters?: FilterState) => {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.supplier_id) params.append('supplier_id', filters.supplier_id);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);

  return useQuery({
    queryKey: ['purchases', 'orders', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PurchaseOrder>>(
        `/v1/purchases/orders?${params.toString()}`
      );
      return response.data;
    },
  });
};

const usePurchaseOrder = (id: string) => {
  return useQuery({
    queryKey: ['purchases', 'orders', id],
    queryFn: async () => {
      const response = await api.get<PurchaseOrder>(`/v1/purchases/orders/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
};

const useCreatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      supplier_id: string;
      date: string;
      expected_date?: string;
      reference?: string;
      notes?: string;
      lines: Omit<PurchaseOrderLine, 'id'>[];
    }) => {
      const response = await api.post<PurchaseOrder>('/v1/purchases/orders', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

const useUpdatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<PurchaseOrder> }) => {
      const response = await api.put<PurchaseOrder>(`/v1/purchases/orders/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders', id] });
    },
  });
};

const useDeletePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/orders/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

const useValidatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<PurchaseOrder>(`/v1/purchases/orders/${id}/validate`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders', id] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

const useCreateInvoiceFromOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<PurchaseInvoice>(
        `/v1/purchases/orders/${orderId}/create-invoice`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

// ============================================================================
// API HOOKS - Purchase Invoices
// ============================================================================

const usePurchaseInvoices = (page = 1, pageSize = 25, filters?: FilterState) => {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters?.search) params.append('search', filters.search);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.supplier_id) params.append('supplier_id', filters.supplier_id);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);

  return useQuery({
    queryKey: ['purchases', 'invoices', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PurchaseInvoice>>(
        `/v1/purchases/invoices?${params.toString()}`
      );
      return response.data;
    },
  });
};

const usePurchaseInvoice = (id: string) => {
  return useQuery({
    queryKey: ['purchases', 'invoices', id],
    queryFn: async () => {
      const response = await api.get<PurchaseInvoice>(`/v1/purchases/invoices/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
};

const useCreatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      supplier_id: string;
      order_id?: string;
      date: string;
      due_date?: string;
      supplier_reference?: string;
      notes?: string;
      lines: Omit<PurchaseOrderLine, 'id'>[];
    }) => {
      const response = await api.post<PurchaseInvoice>('/v1/purchases/invoices', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

const useUpdatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<PurchaseInvoice> }) => {
      const response = await api.put<PurchaseInvoice>(`/v1/purchases/invoices/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices', id] });
    },
  });
};

const useDeletePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/invoices/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

const useValidatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<PurchaseInvoice>(`/v1/purchases/invoices/${id}/validate`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'invoices', id] });
      queryClient.invalidateQueries({ queryKey: ['purchases', 'summary'] });
    },
  });
};

// ============================================================================
// COMPONENTS - Status Badges
// ============================================================================

const OrderStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config = ORDER_STATUS_CONFIG[status] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

const InvoiceStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config = INVOICE_STATUS_CONFIG[status] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

const SupplierStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config = SUPPLIER_STATUS_CONFIG[status] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

// ============================================================================
// COMPONENTS - Line Editor
// ============================================================================

interface LineFormData {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent: number;
}

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
        <h3>Lignes</h3>
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

// ============================================================================
// COMPONENTS - Filter Bar
// ============================================================================

interface FilterBarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  suppliers?: Supplier[];
  statusOptions: { value: string; label: string }[];
  showSupplierFilter?: boolean;
}

const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onChange,
  suppliers = [],
  statusOptions,
  showSupplierFilter = true,
}) => {
  const [showFilters, setShowFilters] = useState(false);

  const hasActiveFilters = !!(
    filters.status ||
    filters.supplier_id ||
    filters.date_from ||
    filters.date_to
  );

  const clearFilters = () => {
    onChange({ search: filters.search });
  };

  return (
    <div className="azals-filter-bar">
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Rechercher..."
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
          Filtres {hasActiveFilters && '•'}
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X size={14} /> Effacer
          </Button>
        )}
      </div>

      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__grid">
            <div className="azals-field">
              <label className="azals-field__label">Statut</label>
              <select
                className="azals-select"
                value={filters.status || ''}
                onChange={(e) => onChange({ ...filters, status: e.target.value || undefined })}
              >
                <option value="">Tous les statuts</option>
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {showSupplierFilter && suppliers.length > 0 && (
              <div className="azals-field">
                <label className="azals-field__label">Fournisseur</label>
                <select
                  className="azals-select"
                  value={filters.supplier_id || ''}
                  onChange={(e) => onChange({ ...filters, supplier_id: e.target.value || undefined })}
                >
                  <option value="">Tous les fournisseurs</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Date du</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_from || ''}
                onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date au</label>
              <input
                type="date"
                className="azals-input"
                value={filters.date_to || ''}
                onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// PAGES - Dashboard
// ============================================================================

export const PurchasesDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = usePurchaseSummary();

  const kpis: DashboardKPI[] = summary
    ? [
        {
          id: 'suppliers',
          label: 'Fournisseurs actifs',
          value: summary.active_suppliers,
        },
        {
          id: 'pending',
          label: 'Commandes en cours',
          value: summary.pending_orders,
        },
        {
          id: 'value',
          label: 'Valeur en attente',
          value: formatCurrency(summary.pending_value),
        },
        {
          id: 'invoices',
          label: 'Factures à traiter',
          value: summary.pending_invoices,
        },
      ]
    : [];

  return (
    <PageWrapper
      title="Achats"
      subtitle="Gestion des fournisseurs et des achats"
    >
      {isLoading ? (
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => (
                <KPICard key={kpi.id} kpi={kpi} />
              ))}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Fournisseurs"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/purchases/suppliers')}
                  >
                    Gérer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <Users size={32} className="azals-text--primary" />
                  <p>Carnet fournisseurs</p>
                </div>
              </Card>

              <Card
                title="Commandes"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/purchases/orders')}>
                    Gérer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <ShoppingCart size={32} className="azals-text--primary" />
                  <p>Commandes fournisseurs</p>
                </div>
              </Card>

              <Card
                title="Factures"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/purchases/invoices')}>
                    Gérer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <FileText size={32} className="azals-text--primary" />
                  <p>Factures fournisseurs</p>
                </div>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Suppliers List
// ============================================================================

export const SuppliersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({});

  const { data, isLoading, refetch } = useSuppliers(page, pageSize, filters);
  const deleteMutation = useDeleteSupplier();

  const handleDelete = async (supplier: Supplier) => {
    if (window.confirm(`Supprimer le fournisseur "${supplier.name}" ?`)) {
      await deleteMutation.mutateAsync(supplier.id);
    }
  };

  const columns: TableColumn<Supplier>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'contact_name', header: 'Contact', accessor: 'contact_name' },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <SupplierStatusBadge status={value as string} />,
    },
  ];

  const actions: TableAction<Supplier>[] = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row) => navigate(`/purchases/suppliers/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      onClick: (row) => navigate(`/purchases/suppliers/${row.id}/edit`),
      capability: 'purchases.edit',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      onClick: (row) => handleDelete(row),
      capability: 'purchases.delete',
      variant: 'danger',
    },
  ];

  const statusOptions = Object.entries(SUPPLIER_STATUS_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <PageWrapper
      title="Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/suppliers/new')}>
            Nouveau fournisseur
          </Button>
        </CapabilityGuard>
      }
    >
      <FilterBar
        filters={filters}
        onChange={setFilters}
        statusOptions={statusOptions}
        showSupplierFilter={false}
      />
      <Card noPadding>
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
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Supplier Form
// ============================================================================

export const SupplierFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = id === 'new';

  const { data: supplier, isLoading } = useSupplier(id || '');
  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();

  const [form, setForm] = useState<SupplierCreate>({
    name: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'France',
    tax_id: '',
    payment_terms: 'NET30',
    notes: '',
  });

  useEffect(() => {
    if (supplier) {
      setForm({
        name: supplier.name,
        contact_name: supplier.contact_name || '',
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        city: supplier.city || '',
        postal_code: supplier.postal_code || '',
        country: supplier.country || 'France',
        tax_id: supplier.tax_id || '',
        payment_terms: supplier.payment_terms || 'NET30',
        notes: supplier.notes || '',
      });
    }
  }, [supplier]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isNew) {
      const result = await createMutation.mutateAsync(form);
      navigate(`/purchases/suppliers/${result.id}`);
    } else {
      await updateMutation.mutateAsync({ id: id!, data: form });
      navigate(`/purchases/suppliers/${id}`);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouveau fournisseur' : `Modifier ${supplier?.name}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations générales">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Nom *</label>
              <input
                type="text"
                className="azals-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Contact</label>
              <input
                type="text"
                className="azals-input"
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Email</label>
              <input
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Téléphone</label>
              <input
                type="text"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">N° TVA / SIRET</label>
              <input
                type="text"
                className="azals-input"
                value={form.tax_id}
                onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Conditions de paiement</label>
              <select
                className="azals-select"
                value={form.payment_terms}
                onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}
              >
                {PAYMENT_TERMS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Adresse">
          <Grid cols={2} gap="md">
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <label className="azals-field__label">Adresse</label>
              <input
                type="text"
                className="azals-input"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Code postal</label>
              <input
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Ville</label>
              <input
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Pays</label>
              <input
                type="text"
                className="azals-input"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Notes">
          <div className="azals-field">
            <textarea
              className="azals-textarea"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={4}
              placeholder="Notes internes sur ce fournisseur..."
            />
          </div>
        </Card>

        <div className="azals-form__actions">
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Annuler
          </Button>
          <Button
            type="submit"
            leftIcon={<Save size={16} />}
            isLoading={isSubmitting}
          >
            {isNew ? 'Créer le fournisseur' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Supplier Detail
// ============================================================================

export const SupplierDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { data: supplier, isLoading } = useSupplier(id || '');
  const deleteMutation = useDeleteSupplier();

  const handleDelete = async () => {
    if (window.confirm(`Supprimer le fournisseur "${supplier?.name}" ?`)) {
      await deleteMutation.mutateAsync(id!);
      navigate('/purchases/suppliers');
    }
  };

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!supplier) {
    return (
      <PageWrapper title="Fournisseur introuvable">
        <Card>
          <p>Ce fournisseur n'existe pas ou a été supprimé.</p>
          <Button onClick={() => navigate('/purchases/suppliers')}>Retour à la liste</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`${supplier.code} - ${supplier.name}`}
      subtitle={SUPPLIER_STATUS_CONFIG[supplier.status]?.label}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
            Retour
          </Button>
          <CapabilityGuard capability="purchases.edit">
            <Button
              variant="secondary"
              leftIcon={<Edit size={16} />}
              onClick={() => navigate(`/purchases/suppliers/${id}/edit`)}
            >
              Modifier
            </Button>
          </CapabilityGuard>
          <CapabilityGuard capability="purchases.delete">
            <Button variant="danger" leftIcon={<Trash2 size={16} />} onClick={handleDelete}>
              Supprimer
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      <Grid cols={2} gap="md">
        <Card title="Informations générales">
          <dl className="azals-detail-list">
            <dt>Code</dt>
            <dd>{supplier.code}</dd>
            <dt>Nom</dt>
            <dd>{supplier.name}</dd>
            <dt>Contact</dt>
            <dd>{supplier.contact_name || '-'}</dd>
            <dt>Email</dt>
            <dd>{supplier.email || '-'}</dd>
            <dt>Téléphone</dt>
            <dd>{supplier.phone || '-'}</dd>
            <dt>N° TVA / SIRET</dt>
            <dd>{supplier.tax_id || '-'}</dd>
            <dt>Conditions de paiement</dt>
            <dd>
              {PAYMENT_TERMS_OPTIONS.find((o) => o.value === supplier.payment_terms)?.label || '-'}
            </dd>
          </dl>
        </Card>

        <Card title="Adresse">
          <dl className="azals-detail-list">
            <dt>Adresse</dt>
            <dd>{supplier.address || '-'}</dd>
            <dt>Code postal</dt>
            <dd>{supplier.postal_code || '-'}</dd>
            <dt>Ville</dt>
            <dd>{supplier.city || '-'}</dd>
            <dt>Pays</dt>
            <dd>{supplier.country || '-'}</dd>
          </dl>
        </Card>
      </Grid>

      {supplier.notes && (
        <Card title="Notes">
          <p className="azals-text--muted">{supplier.notes}</p>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Orders List
// ============================================================================

export const OrdersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({});

  const { data, isLoading, refetch } = usePurchaseOrders(page, pageSize, filters);
  const { data: suppliers } = useSuppliersLookup();
  const deleteMutation = useDeletePurchaseOrder();
  const validateMutation = useValidatePurchaseOrder();

  const handleDelete = async (order: PurchaseOrder) => {
    if (order.status !== 'DRAFT') {
      alert('Seules les commandes en brouillon peuvent être supprimées');
      return;
    }
    if (window.confirm(`Supprimer la commande "${order.number}" ?`)) {
      await deleteMutation.mutateAsync(order.id);
    }
  };

  const handleValidate = async (order: PurchaseOrder) => {
    if (order.status !== 'DRAFT') {
      alert('Seules les commandes en brouillon peuvent être validées');
      return;
    }
    if (window.confirm(`Valider la commande "${order.number}" ? Cette action est irréversible.`)) {
      await validateMutation.mutateAsync(order.id);
    }
  };

  const columns: TableColumn<PurchaseOrder>[] = [
    { id: 'number', header: 'N°', accessor: 'number', sortable: true },
    {
      id: 'supplier',
      header: 'Fournisseur',
      accessor: 'supplier_name',
      render: (_, row) => `${row.supplier_code} - ${row.supplier_name}`,
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <OrderStatusBadge status={value as string} />,
    },
    {
      id: 'total_ttc',
      header: 'Total TTC',
      accessor: 'total_ttc',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  const actions: TableAction<PurchaseOrder>[] = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row) => navigate(`/purchases/orders/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      onClick: (row) => navigate(`/purchases/orders/${row.id}/edit`),
      capability: 'purchases.edit',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'validate',
      label: 'Valider',
      onClick: (row) => handleValidate(row),
      capability: 'purchases.validate',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      onClick: (row) => handleDelete(row),
      capability: 'purchases.delete',
      variant: 'danger',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
  ];

  const statusOptions = Object.entries(ORDER_STATUS_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <PageWrapper
      title="Commandes Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/orders/new')}>
            Nouvelle commande
          </Button>
        </CapabilityGuard>
      }
    >
      <FilterBar
        filters={filters}
        onChange={setFilters}
        suppliers={suppliers || []}
        statusOptions={statusOptions}
      />
      <Card noPadding>
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
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Order Form
// ============================================================================

export const OrderFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = id === 'new';

  const { data: order, isLoading } = usePurchaseOrder(id || '');
  const { data: suppliers } = useSuppliersLookup();
  const createMutation = useCreatePurchaseOrder();
  const updateMutation = useUpdatePurchaseOrder();

  const [supplierId, setSupplierId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [expectedDate, setExpectedDate] = useState('');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);

  useEffect(() => {
    if (order) {
      setSupplierId(order.supplier_id);
      setDate(order.date.split('T')[0]);
      setExpectedDate(order.expected_date?.split('T')[0] || '');
      setReference(order.reference || '');
      setNotes(order.notes || '');
      setLines(order.lines.map((l) => ({
        id: l.id,
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })));
    }
  }, [order]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) {
      alert('Veuillez sélectionner un fournisseur');
      return;
    }
    if (lines.length === 0) {
      alert('Veuillez ajouter au moins une ligne');
      return;
    }

    const data = {
      supplier_id: supplierId,
      date,
      expected_date: expectedDate || undefined,
      reference: reference || undefined,
      notes: notes || undefined,
      lines: lines.map((l) => ({
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })),
    };

    if (isNew) {
      const result = await createMutation.mutateAsync(data);
      navigate(`/purchases/orders/${result.id}`);
    } else {
      await updateMutation.mutateAsync({ id: id!, data });
      navigate(`/purchases/orders/${id}`);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;
  const canEdit = isNew || order?.status === 'DRAFT';

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!isNew && order && order.status !== 'DRAFT') {
    return (
      <PageWrapper title="Modification impossible">
        <Card>
          <AlertTriangle size={48} className="azals-text--warning" />
          <p>Cette commande ne peut plus être modifiée car elle a été validée.</p>
          <Button onClick={() => navigate(`/purchases/orders/${id}`)}>Voir la commande</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle commande' : `Modifier ${order?.number}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations générales">
          <Grid cols={3} gap="md">
            <div className="azals-field">
              <SmartSelector
                items={(suppliers || []).map(s => ({ ...s, id: s.id, name: s.name }))}
                value={supplierId}
                onChange={(value) => setSupplierId(value)}
                label="Fournisseur *"
                placeholder="Sélectionner un fournisseur..."
                displayField="name"
                secondaryField="code"
                entityName="fournisseur"
                entityIcon={<Building2 size={16} />}
                createEndpoint="/v1/purchases/suppliers"
                createFields={SUPPLIER_CREATE_FIELDS}
                queryKeys={['purchases', 'suppliers']}
                disabled={!canEdit}
                allowCreate={canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date *</label>
              <input
                type="date"
                className="azals-input"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Livraison prévue</label>
              <input
                type="date"
                className="azals-input"
                value={expectedDate}
                onChange={(e) => setExpectedDate(e.target.value)}
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Référence fournisseur</label>
              <input
                type="text"
                className="azals-input"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                disabled={!canEdit}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Lignes de commande">
          <LineEditor
            lines={lines}
            onChange={setLines}
            readOnly={!canEdit}
          />
        </Card>

        <Card title="Notes">
          <div className="azals-field">
            <textarea
              className="azals-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Notes internes sur cette commande..."
              disabled={!canEdit}
            />
          </div>
        </Card>

        {canEdit && (
          <div className="azals-form__actions">
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Annuler
            </Button>
            <Button
              type="submit"
              leftIcon={<Save size={16} />}
              isLoading={isSubmitting}
            >
              {isNew ? 'Créer la commande' : 'Enregistrer'}
            </Button>
          </div>
        )}
      </form>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Order Detail
// ============================================================================

export const OrderDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { data: order, isLoading } = usePurchaseOrder(id || '');
  const deleteMutation = useDeletePurchaseOrder();
  const validateMutation = useValidatePurchaseOrder();
  const createInvoiceMutation = useCreateInvoiceFromOrder();

  const [showValidateDialog, setShowValidateDialog] = useState(false);

  const handleDelete = async () => {
    if (order?.status !== 'DRAFT') {
      alert('Seules les commandes en brouillon peuvent être supprimées');
      return;
    }
    if (window.confirm(`Supprimer la commande "${order?.number}" ?`)) {
      await deleteMutation.mutateAsync(id!);
      navigate('/purchases/orders');
    }
  };

  const handleValidate = async () => {
    await validateMutation.mutateAsync(id!);
    setShowValidateDialog(false);
  };

  const handleCreateInvoice = async () => {
    const invoice = await createInvoiceMutation.mutateAsync(id!);
    navigate(`/purchases/invoices/${invoice.id}`);
  };

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!order) {
    return (
      <PageWrapper title="Commande introuvable">
        <Card>
          <p>Cette commande n'existe pas ou a été supprimée.</p>
          <Button onClick={() => navigate('/purchases/orders')}>Retour à la liste</Button>
        </Card>
      </PageWrapper>
    );
  }

  const isDraft = order.status === 'DRAFT';
  const isValidated = order.status === 'SENT' || order.status === 'CONFIRMED';

  return (
    <PageWrapper
      title={order.number}
      subtitle={`${order.supplier_code} - ${order.supplier_name}`}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
            Retour
          </Button>
          {isDraft && (
            <>
              <CapabilityGuard capability="purchases.edit">
                <Button
                  variant="secondary"
                  leftIcon={<Edit size={16} />}
                  onClick={() => navigate(`/purchases/orders/${id}/edit`)}
                >
                  Modifier
                </Button>
              </CapabilityGuard>
              <CapabilityGuard capability="purchases.validate">
                <Button
                  leftIcon={<CheckCircle2 size={16} />}
                  onClick={() => setShowValidateDialog(true)}
                >
                  Valider
                </Button>
              </CapabilityGuard>
              <CapabilityGuard capability="purchases.delete">
                <Button variant="danger" leftIcon={<Trash2 size={16} />} onClick={handleDelete}>
                  Supprimer
                </Button>
              </CapabilityGuard>
            </>
          )}
          {isValidated && (
            <CapabilityGuard capability="purchases.create">
              <Button
                variant="secondary"
                leftIcon={<FileText size={16} />}
                onClick={handleCreateInvoice}
                isLoading={createInvoiceMutation.isPending}
              >
                Créer facture
              </Button>
            </CapabilityGuard>
          )}
        </ButtonGroup>
      }
    >
      <Card>
        <Grid cols={4} gap="md">
          <div>
            <span className="azals-label">Statut</span>
            <OrderStatusBadge status={order.status} />
          </div>
          <div>
            <span className="azals-label">Date</span>
            <span>{formatDate(order.date)}</span>
          </div>
          <div>
            <span className="azals-label">Livraison prévue</span>
            <span>{order.expected_date ? formatDate(order.expected_date) : '-'}</span>
          </div>
          <div>
            <span className="azals-label">Référence</span>
            <span>{order.reference || '-'}</span>
          </div>
        </Grid>
      </Card>

      <Card title="Lignes de commande">
        <LineEditor lines={order.lines} onChange={() => {}} readOnly />
      </Card>

      {order.notes && (
        <Card title="Notes">
          <p className="azals-text--muted">{order.notes}</p>
        </Card>
      )}

      {order.validated_at && (
        <Card title="Historique">
          <p className="azals-text--muted">
            Validée le {formatDate(order.validated_at)}
          </p>
        </Card>
      )}

      {showValidateDialog && (
        <ConfirmDialog
          title="Valider la commande"
          message="Êtes-vous sûr de vouloir valider cette commande ? Cette action est irréversible."
          onConfirm={handleValidate}
          onCancel={() => setShowValidateDialog(false)}
          variant="warning"
          isLoading={validateMutation.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Invoices List
// ============================================================================

export const InvoicesListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({});

  const { data, isLoading, refetch } = usePurchaseInvoices(page, pageSize, filters);
  const { data: suppliers } = useSuppliersLookup();
  const deleteMutation = useDeletePurchaseInvoice();
  const validateMutation = useValidatePurchaseInvoice();

  const handleDelete = async (invoice: PurchaseInvoice) => {
    if (invoice.status !== 'DRAFT') {
      alert('Seules les factures en brouillon peuvent être supprimées');
      return;
    }
    if (window.confirm(`Supprimer la facture "${invoice.number}" ?`)) {
      await deleteMutation.mutateAsync(invoice.id);
    }
  };

  const handleValidate = async (invoice: PurchaseInvoice) => {
    if (invoice.status !== 'DRAFT') {
      alert('Seules les factures en brouillon peuvent être validées');
      return;
    }
    if (window.confirm(`Valider la facture "${invoice.number}" ? Cette action est irréversible.`)) {
      await validateMutation.mutateAsync(invoice.id);
    }
  };

  const columns: TableColumn<PurchaseInvoice>[] = [
    { id: 'number', header: 'N°', accessor: 'number', sortable: true },
    {
      id: 'supplier',
      header: 'Fournisseur',
      accessor: 'supplier_name',
      render: (_, row) => `${row.supplier_code} - ${row.supplier_name}`,
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'due_date',
      header: 'Échéance',
      accessor: 'due_date',
      render: (value) => (value ? formatDate(value as string) : '-'),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <InvoiceStatusBadge status={value as string} />,
    },
    {
      id: 'total_ttc',
      header: 'Total TTC',
      accessor: 'total_ttc',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  const actions: TableAction<PurchaseInvoice>[] = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row) => navigate(`/purchases/invoices/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      onClick: (row) => navigate(`/purchases/invoices/${row.id}/edit`),
      capability: 'purchases.edit',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'validate',
      label: 'Valider',
      onClick: (row) => handleValidate(row),
      capability: 'purchases.validate',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      onClick: (row) => handleDelete(row),
      capability: 'purchases.delete',
      variant: 'danger',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
  ];

  const statusOptions = Object.entries(INVOICE_STATUS_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <PageWrapper
      title="Factures Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/invoices/new')}>
            Nouvelle facture
          </Button>
        </CapabilityGuard>
      }
    >
      <FilterBar
        filters={filters}
        onChange={setFilters}
        suppliers={suppliers || []}
        statusOptions={statusOptions}
      />
      <Card noPadding>
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
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Invoice Form
// ============================================================================

export const InvoiceFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = id === 'new';

  const { data: invoice, isLoading } = usePurchaseInvoice(id || '');
  const { data: suppliers } = useSuppliersLookup();
  const createMutation = useCreatePurchaseInvoice();
  const updateMutation = useUpdatePurchaseInvoice();

  const [supplierId, setSupplierId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [supplierReference, setSupplierReference] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineFormData[]>([]);

  useEffect(() => {
    if (invoice) {
      setSupplierId(invoice.supplier_id);
      setDate(invoice.date.split('T')[0]);
      setDueDate(invoice.due_date?.split('T')[0] || '');
      setSupplierReference(invoice.supplier_reference || '');
      setNotes(invoice.notes || '');
      setLines(invoice.lines.map((l) => ({
        id: l.id,
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })));
    }
  }, [invoice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) {
      alert('Veuillez sélectionner un fournisseur');
      return;
    }
    if (lines.length === 0) {
      alert('Veuillez ajouter au moins une ligne');
      return;
    }

    const data = {
      supplier_id: supplierId,
      date,
      due_date: dueDate || undefined,
      supplier_reference: supplierReference || undefined,
      notes: notes || undefined,
      lines: lines.map((l) => ({
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent,
      })),
    };

    if (isNew) {
      const result = await createMutation.mutateAsync(data);
      navigate(`/purchases/invoices/${result.id}`);
    } else {
      await updateMutation.mutateAsync({ id: id!, data });
      navigate(`/purchases/invoices/${id}`);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;
  const canEdit = isNew || invoice?.status === 'DRAFT';

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!isNew && invoice && invoice.status !== 'DRAFT') {
    return (
      <PageWrapper title="Modification impossible">
        <Card>
          <AlertTriangle size={48} className="azals-text--warning" />
          <p>Cette facture ne peut plus être modifiée car elle a été validée.</p>
          <Button onClick={() => navigate(`/purchases/invoices/${id}`)}>Voir la facture</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle facture' : `Modifier ${invoice?.number}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations générales">
          <Grid cols={3} gap="md">
            <div className="azals-field">
              <SmartSelector
                items={(suppliers || []).map(s => ({ ...s, id: s.id, name: s.name }))}
                value={supplierId}
                onChange={(value) => setSupplierId(value)}
                label="Fournisseur *"
                placeholder="Sélectionner un fournisseur..."
                displayField="name"
                secondaryField="code"
                entityName="fournisseur"
                entityIcon={<Building2 size={16} />}
                createEndpoint="/v1/purchases/suppliers"
                createFields={SUPPLIER_CREATE_FIELDS}
                queryKeys={['purchases', 'suppliers']}
                disabled={!canEdit}
                allowCreate={canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date *</label>
              <input
                type="date"
                className="azals-input"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date d'échéance</label>
              <input
                type="date"
                className="azals-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                disabled={!canEdit}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Réf. fournisseur</label>
              <input
                type="text"
                className="azals-input"
                value={supplierReference}
                onChange={(e) => setSupplierReference(e.target.value)}
                placeholder="N° facture fournisseur"
                disabled={!canEdit}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Lignes de facture">
          <LineEditor
            lines={lines}
            onChange={setLines}
            readOnly={!canEdit}
          />
        </Card>

        <Card title="Notes">
          <div className="azals-field">
            <textarea
              className="azals-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Notes internes sur cette facture..."
              disabled={!canEdit}
            />
          </div>
        </Card>

        {canEdit && (
          <div className="azals-form__actions">
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Annuler
            </Button>
            <Button
              type="submit"
              leftIcon={<Save size={16} />}
              isLoading={isSubmitting}
            >
              {isNew ? 'Créer la facture' : 'Enregistrer'}
            </Button>
          </div>
        )}
      </form>
    </PageWrapper>
  );
};

// ============================================================================
// PAGES - Invoice Detail
// ============================================================================

export const InvoiceDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { data: invoice, isLoading } = usePurchaseInvoice(id || '');
  const deleteMutation = useDeletePurchaseInvoice();
  const validateMutation = useValidatePurchaseInvoice();

  const [showValidateDialog, setShowValidateDialog] = useState(false);

  const handleDelete = async () => {
    if (invoice?.status !== 'DRAFT') {
      alert('Seules les factures en brouillon peuvent être supprimées');
      return;
    }
    if (window.confirm(`Supprimer la facture "${invoice?.number}" ?`)) {
      await deleteMutation.mutateAsync(id!);
      navigate('/purchases/invoices');
    }
  };

  const handleValidate = async () => {
    await validateMutation.mutateAsync(id!);
    setShowValidateDialog(false);
  };

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!invoice) {
    return (
      <PageWrapper title="Facture introuvable">
        <Card>
          <p>Cette facture n'existe pas ou a été supprimée.</p>
          <Button onClick={() => navigate('/purchases/invoices')}>Retour à la liste</Button>
        </Card>
      </PageWrapper>
    );
  }

  const isDraft = invoice.status === 'DRAFT';

  return (
    <PageWrapper
      title={invoice.number}
      subtitle={`${invoice.supplier_code} - ${invoice.supplier_name}`}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
            Retour
          </Button>
          {isDraft && (
            <>
              <CapabilityGuard capability="purchases.edit">
                <Button
                  variant="secondary"
                  leftIcon={<Edit size={16} />}
                  onClick={() => navigate(`/purchases/invoices/${id}/edit`)}
                >
                  Modifier
                </Button>
              </CapabilityGuard>
              <CapabilityGuard capability="purchases.validate">
                <Button
                  leftIcon={<CheckCircle2 size={16} />}
                  onClick={() => setShowValidateDialog(true)}
                >
                  Valider
                </Button>
              </CapabilityGuard>
              <CapabilityGuard capability="purchases.delete">
                <Button variant="danger" leftIcon={<Trash2 size={16} />} onClick={handleDelete}>
                  Supprimer
                </Button>
              </CapabilityGuard>
            </>
          )}
        </ButtonGroup>
      }
    >
      <Card>
        <Grid cols={4} gap="md">
          <div>
            <span className="azals-label">Statut</span>
            <InvoiceStatusBadge status={invoice.status} />
          </div>
          <div>
            <span className="azals-label">Date</span>
            <span>{formatDate(invoice.date)}</span>
          </div>
          <div>
            <span className="azals-label">Échéance</span>
            <span>{invoice.due_date ? formatDate(invoice.due_date) : '-'}</span>
          </div>
          <div>
            <span className="azals-label">Réf. fournisseur</span>
            <span>{invoice.supplier_reference || '-'}</span>
          </div>
        </Grid>
        {invoice.order_number && (
          <div style={{ marginTop: '1rem' }}>
            <span className="azals-label">Commande liée</span>
            <Link to={`/purchases/orders/${invoice.order_id}`} className="azals-link">
              {invoice.order_number}
            </Link>
          </div>
        )}
      </Card>

      <Card title="Lignes de facture">
        <LineEditor lines={invoice.lines} onChange={() => {}} readOnly />
      </Card>

      {invoice.notes && (
        <Card title="Notes">
          <p className="azals-text--muted">{invoice.notes}</p>
        </Card>
      )}

      {invoice.validated_at && (
        <Card title="Historique">
          <p className="azals-text--muted">
            Validée le {formatDate(invoice.validated_at)}
          </p>
        </Card>
      )}

      {showValidateDialog && (
        <ConfirmDialog
          title="Valider la facture"
          message="Êtes-vous sûr de vouloir valider cette facture ? Cette action est irréversible."
          onConfirm={handleValidate}
          onCancel={() => setShowValidateDialog(false)}
          variant="warning"
          isLoading={validateMutation.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

export const PurchasesRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PurchasesDashboard />} />
    {/* Suppliers */}
    <Route path="suppliers" element={<SuppliersListPage />} />
    <Route path="suppliers/new" element={<SupplierFormPage />} />
    <Route path="suppliers/:id" element={<SupplierDetailPage />} />
    <Route path="suppliers/:id/edit" element={<SupplierFormPage />} />
    {/* Orders */}
    <Route path="orders" element={<OrdersListPage />} />
    <Route path="orders/new" element={<OrderFormPage />} />
    <Route path="orders/:id" element={<OrderDetailPage />} />
    <Route path="orders/:id/edit" element={<OrderFormPage />} />
    {/* Invoices */}
    <Route path="invoices" element={<InvoicesListPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailPage />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
  </Routes>
);

export default PurchasesRoutes;
