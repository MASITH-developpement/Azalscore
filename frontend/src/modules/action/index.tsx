/**
 * AZALSCORE - Module ACTION
 * Vue unique de saisie conforme aux principes AZALSCORE
 *
 * RÈGLES AZALSCORE APPLIQUÉES :
 * - UN formulaire universel unique
 * - Sélecteur de type = état, pas route
 * - Injection automatique TOUS les champs à la sélection
 * - Création contextuelle minimale
 * - Aucun changement de page
 * - i18n obligatoire
 * - Calculs côté frontend
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  ShoppingCart,
  Receipt,
  User,
  Building,
  Plus,
  Trash2,
  Check,
  Save,
  AlertCircle,
  Search,
  X,
  ChevronDown,
} from 'lucide-react';
import { api } from '@core/api-client';
import {
  useSharedClients,
  useSharedSuppliers,
  useInvalidateSharedCache,
  type CachedClient,
  type CachedSupplier,
} from '@core/shared-cache';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button, Modal, ConfirmDialog } from '@ui/actions';
import type { PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

type DocumentType = 'QUOTE' | 'INVOICE' | 'PURCHASE_ORDER' | 'PURCHASE_INVOICE';

interface DocumentTypeConfig {
  id: DocumentType;
  icon: React.ReactNode;
  apiEndpoint: string;
  partnerType: 'client' | 'supplier';
  hasValidity: boolean;
  hasDueDate: boolean;
}

interface Partner {
  id: string;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  country_code?: string;
  vat_number?: string;
  tax_id?: string;
  payment_terms?: string;
  is_active: boolean;
  type?: string;
}

interface DocumentLine {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

interface DocumentFormState {
  type: DocumentType;
  partner_id: string;
  partner: Partner | null;
  date: string;
  due_date: string;
  validity_date: string;
  reference: string;
  notes: string;
  lines: DocumentLine[];
}

// ============================================================
// CONFIGURATION DES TYPES DE DOCUMENT
// ============================================================

const DOCUMENT_TYPES: DocumentTypeConfig[] = [
  {
    id: 'QUOTE',
    icon: <FileText size={20} />,
    apiEndpoint: '/v1/commercial/documents',
    partnerType: 'client',
    hasValidity: true,
    hasDueDate: false,
  },
  {
    id: 'INVOICE',
    icon: <Receipt size={20} />,
    apiEndpoint: '/v1/commercial/documents',
    partnerType: 'client',
    hasValidity: false,
    hasDueDate: true,
  },
  {
    id: 'PURCHASE_ORDER',
    icon: <ShoppingCart size={20} />,
    apiEndpoint: '/v1/purchases/orders',
    partnerType: 'supplier',
    hasValidity: false,
    hasDueDate: false,
  },
  {
    id: 'PURCHASE_INVOICE',
    icon: <Receipt size={20} />,
    apiEndpoint: '/v1/purchases/invoices',
    partnerType: 'supplier',
    hasValidity: false,
    hasDueDate: true,
  },
];

const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

// ============================================================
// UTILITAIRES
// ============================================================

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(amount);
};

const generateTempId = () => `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

const calculateLineTotal = (line: DocumentLine) => {
  const baseAmount = line.quantity * line.unit_price;
  const discountAmount = baseAmount * (line.discount_percent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (line.tax_rate / 100);
  const total = subtotal + taxAmount;
  return { subtotal, taxAmount, total };
};

// ============================================================
// API HOOKS - Utilise le cache partagé AZALSCORE
// ============================================================

// Note: useSharedClients et useSharedSuppliers sont importés de @core/shared-cache
// Ils utilisent un cache de 30 minutes pour éviter les appels réseau inutiles

const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ type, data }: { type: DocumentType; data: any }) => {
      const config = DOCUMENT_TYPES.find((t) => t.id === type);
      if (!config) throw new Error('Type de document invalide');

      // Adapter les données selon le type
      const payload = type.startsWith('PURCHASE_')
        ? {
            supplier_id: data.partner_id,
            date: data.date,
            expected_date: data.due_date || undefined,
            reference: data.reference || undefined,
            notes: data.notes || undefined,
            lines: data.lines.map((l: DocumentLine) => ({
              description: l.description,
              quantity: l.quantity,
              unit_price: l.unit_price,
              tax_rate: l.tax_rate,
              discount_percent: l.discount_percent,
            })),
          }
        : {
            type: type,
            customer_id: data.partner_id,
            date: data.date,
            due_date: data.due_date || undefined,
            validity_date: data.validity_date || undefined,
            notes: data.notes || undefined,
            lines: data.lines.map((l: DocumentLine) => ({
              description: l.description,
              quantity: l.quantity,
              unit: l.unit,
              unit_price: l.unit_price,
              tax_rate: l.tax_rate,
              discount_percent: l.discount_percent,
            })),
          };

      const response = await api.post(config.apiEndpoint, payload);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['purchases'] });
    },
  });
};

const useCreateClient = () => {
  const { invalidateClients } = useInvalidateSharedCache();

  return useMutation({
    mutationFn: async (data: Partial<Partner>) => {
      const response = await api.post<Partner>('/v1/partners/clients', {
        name: data.name,
        email: data.email || undefined,
        phone: data.phone || undefined,
        address_line1: data.address || data.address_line1 || undefined,
        city: data.city || undefined,
        postal_code: data.postal_code || undefined,
        country_code: data.country_code || data.country || 'FR',
        type: 'CUSTOMER',
      });
      return response as unknown as Partner;
    },
    onSuccess: () => {
      invalidateClients();
    },
  });
};

const useCreateSupplier = () => {
  const { invalidateSuppliers } = useInvalidateSharedCache();

  return useMutation({
    mutationFn: async (data: Partial<Partner>) => {
      const response = await api.post<Partner>('/v1/purchases/suppliers', {
        name: data.name,
        email: data.email || undefined,
        phone: data.phone || undefined,
        address: data.address || data.address_line1 || undefined,
        city: data.city || undefined,
        postal_code: data.postal_code || undefined,
        country: data.country_code || data.country || 'France',
        payment_terms: 'NET30',
      });
      return response as unknown as Partner;
    },
    onSuccess: () => {
      invalidateSuppliers();
    },
  });
};

// ============================================================
// COMPOSANT - Sélecteur de type de document
// ============================================================

interface DocumentTypeSelectorProps {
  value: DocumentType;
  onChange: (type: DocumentType) => void;
}

const DocumentTypeSelector: React.FC<DocumentTypeSelectorProps> = ({ value, onChange }) => {
  const { t } = useTranslation();

  const getLabel = (type: DocumentType) => {
    switch (type) {
      case 'QUOTE':
        return t('documentType.quote');
      case 'INVOICE':
        return t('documentType.invoice');
      case 'PURCHASE_ORDER':
        return t('documentType.purchaseOrder');
      case 'PURCHASE_INVOICE':
        return t('documentType.purchaseInvoice');
    }
  };

  return (
    <div className="azals-action__type-selector">
      {DOCUMENT_TYPES.map((config) => (
        <button
          key={config.id}
          type="button"
          className={`azals-action__type-btn ${value === config.id ? 'azals-action__type-btn--active' : ''}`}
          onClick={() => onChange(config.id)}
        >
          {config.icon}
          <span>{getLabel(config.id)}</span>
        </button>
      ))}
    </div>
  );
};

// ============================================================
// COMPOSANT - Sélecteur de partenaire avec injection automatique
// ============================================================

interface PartnerSelectorProps {
  type: 'client' | 'supplier';
  value: Partner | null;
  onSelect: (partner: Partner) => void;
  onCreate: () => void;
}

const PartnerSelector: React.FC<PartnerSelectorProps> = ({ type, value, onSelect, onCreate }) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  // Utilise le cache partagé AZALSCORE pour éviter les appels réseau inutiles
  const { data: clients, isLoading: loadingClients } = useSharedClients();
  const { data: suppliers, isLoading: loadingSuppliers } = useSharedSuppliers();

  const partners = type === 'client' ? clients : suppliers;
  const isLoading = type === 'client' ? loadingClients : loadingSuppliers;

  const filteredPartners = useMemo(() => {
    if (!partners) return [];
    if (!search) return partners;

    const searchLower = search.toLowerCase();
    return partners.filter(
      (p) =>
        p.name.toLowerCase().includes(searchLower) ||
        p.code?.toLowerCase().includes(searchLower) ||
        p.email?.toLowerCase().includes(searchLower)
    );
  }, [partners, search]);

  const handleSelect = (partner: Partner) => {
    // RÈGLE AZALSCORE : Injection automatique de TOUS les champs
    onSelect(partner);
    setIsOpen(false);
    setSearch('');
  };

  const label = type === 'client' ? t('action.selectClient') : t('action.selectSupplier');
  const newLabel = type === 'client' ? t('action.newClient') : t('action.newSupplier');

  return (
    <div className="azals-action__partner-selector">
      {/* Bouton principal */}
      <button
        type="button"
        className={`azals-action__partner-btn ${value ? 'azals-action__partner-btn--selected' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        {type === 'client' ? <User size={18} /> : <Building size={18} />}
        <span className="azals-action__partner-btn-text">
          {value ? (
            <>
              <strong>{value.name}</strong>
              {value.code && <span className="azals-action__partner-code">{value.code}</span>}
            </>
          ) : (
            label
          )}
        </span>
        <ChevronDown size={18} className={isOpen ? 'rotate-180' : ''} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="azals-action__partner-dropdown">
          {/* Recherche */}
          <div className="azals-action__partner-search">
            <Search size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('action.searchPlaceholder')}
              autoFocus
            />
            {search && (
              <button type="button" onClick={() => setSearch('')}>
                <X size={14} />
              </button>
            )}
          </div>

          {/* Liste */}
          <div className="azals-action__partner-list">
            {isLoading ? (
              <div className="azals-action__partner-loading">{t('common.loading')}</div>
            ) : filteredPartners.length === 0 ? (
              <div className="azals-action__partner-empty">
                {search ? t('empty.noResults') : t('empty.noData')}
              </div>
            ) : (
              filteredPartners.map((partner) => (
                <button
                  key={partner.id}
                  type="button"
                  className="azals-action__partner-item"
                  onClick={() => handleSelect(partner)}
                >
                  <div className="azals-action__partner-item-main">
                    <strong>{partner.name}</strong>
                    {partner.code && <span className="code">{partner.code}</span>}
                  </div>
                  <div className="azals-action__partner-item-sub">
                    {partner.email && <span>{partner.email}</span>}
                    {partner.city && <span>{partner.city}</span>}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Option création contextuelle */}
          <button
            type="button"
            className="azals-action__partner-new"
            onClick={() => {
              setIsOpen(false);
              onCreate();
            }}
          >
            <Plus size={16} />
            <span>{newLabel}</span>
          </button>
        </div>
      )}

      {/* Aperçu des données injectées */}
      {value && (
        <div className="azals-action__partner-preview">
          <div className="azals-action__partner-preview-grid">
            {value.email && (
              <div className="azals-action__partner-preview-item">
                <span className="label">{t('field.email')}</span>
                <span className="value">{value.email}</span>
              </div>
            )}
            {value.phone && (
              <div className="azals-action__partner-preview-item">
                <span className="label">{t('field.phone')}</span>
                <span className="value">{value.phone}</span>
              </div>
            )}
            {(value.address || value.address_line1) && (
              <div className="azals-action__partner-preview-item">
                <span className="label">{t('field.address')}</span>
                <span className="value">{value.address || value.address_line1}</span>
              </div>
            )}
            {value.city && (
              <div className="azals-action__partner-preview-item">
                <span className="label">{t('field.city')}</span>
                <span className="value">
                  {value.postal_code} {value.city}
                </span>
              </div>
            )}
            {(value.vat_number || value.tax_id) && (
              <div className="azals-action__partner-preview-item">
                <span className="label">{t('field.vatNumber')}</span>
                <span className="value">{value.vat_number || value.tax_id}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// COMPOSANT - Éditeur de lignes universel
// ============================================================

interface LineEditorProps {
  lines: DocumentLine[];
  onChange: (lines: DocumentLine[]) => void;
  currency?: string;
}

const LineEditor: React.FC<LineEditorProps> = ({ lines, onChange, currency = 'EUR' }) => {
  const { t } = useTranslation();
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const addLine = () => {
    const newLine: DocumentLine = {
      id: generateTempId(),
      description: '',
      quantity: 1,
      unit: 'unité',
      unit_price: 0,
      discount_percent: 0,
      tax_rate: 20,
    };
    onChange([...lines, newLine]);
    setEditingIndex(lines.length);
  };

  const updateLine = (index: number, updates: Partial<DocumentLine>) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], ...updates };
    onChange(newLines);
  };

  const removeLine = (index: number) => {
    onChange(lines.filter((_, i) => i !== index));
    setEditingIndex(null);
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
    <div className="azals-action__lines">
      <div className="azals-action__lines-header">
        <h3>{t('action.documentLines')}</h3>
        <Button size="sm" leftIcon={<Plus size={14} />} onClick={addLine}>
          {t('action.addLine')}
        </Button>
      </div>

      {lines.length === 0 ? (
        <div className="azals-action__lines-empty">
          <AlertCircle size={24} />
          <p>{t('action.noLines')}</p>
          <small>{t('action.noLinesHint')}</small>
        </div>
      ) : (
        <table className="azals-action__lines-table">
          <thead>
            <tr>
              <th style={{ width: '40%' }}>{t('field.description')}</th>
              <th style={{ width: '10%' }}>{t('field.quantity')}</th>
              <th style={{ width: '15%' }}>{t('field.unitPriceHT')}</th>
              <th style={{ width: '10%' }}>{t('field.discountPercent')}</th>
              <th style={{ width: '10%' }}>{t('field.taxRate')}</th>
              <th style={{ width: '10%' }}>{t('field.totalHT')}</th>
              <th style={{ width: '5%' }}></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line);
              const isEditing = editingIndex === index;

              return (
                <tr key={line.id} className={isEditing ? 'editing' : ''}>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        className="azals-input azals-input--sm"
                        value={line.description}
                        onChange={(e) => updateLine(index, { description: e.target.value })}
                        placeholder={t('field.description')}
                        autoFocus
                      />
                    ) : (
                      <span
                        className="clickable"
                        onClick={() => setEditingIndex(index)}
                      >
                        {line.description || (
                          <em className="text-muted">{t('action.clickToEdit')}</em>
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
                        onChange={(e) =>
                          updateLine(index, { quantity: parseFloat(e.target.value) || 0 })
                        }
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => setEditingIndex(index)}>{line.quantity}</span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.unit_price}
                        onChange={(e) =>
                          updateLine(index, { unit_price: parseFloat(e.target.value) || 0 })
                        }
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => setEditingIndex(index)}>
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
                        onChange={(e) =>
                          updateLine(index, {
                            discount_percent: parseFloat(e.target.value) || 0,
                          })
                        }
                        min="0"
                        max="100"
                        step="0.1"
                      />
                    ) : (
                      <span onClick={() => setEditingIndex(index)}>
                        {line.discount_percent}%
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select
                        className="azals-select azals-select--sm"
                        value={line.tax_rate}
                        onChange={(e) =>
                          updateLine(index, { tax_rate: parseFloat(e.target.value) })
                        }
                      >
                        {TVA_RATES.map((rate) => (
                          <option key={rate.value} value={rate.value}>
                            {rate.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span onClick={() => setEditingIndex(index)}>{line.tax_rate}%</span>
                    )}
                  </td>
                  <td className="text-right font-medium">
                    {formatCurrency(calc.subtotal, currency)}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="azals-btn-icon azals-btn-icon--danger"
                      onClick={() => removeLine(index)}
                      title={t('action.removeLine')}
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {/* Totaux */}
      <div className="azals-action__lines-totals">
        <div className="azals-action__lines-total-row">
          <span>{t('field.totalHT')}</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        <div className="azals-action__lines-total-row">
          <span>{t('field.totalTVA')}</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="azals-action__lines-total-row azals-action__lines-total-row--main">
          <span>{t('field.totalTTC')}</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// COMPOSANT - Modal création contextuelle partenaire
// ============================================================

interface CreatePartnerModalProps {
  type: 'client' | 'supplier';
  isOpen: boolean;
  onClose: () => void;
  onCreated: (partner: Partner) => void;
}

const CreatePartnerModal: React.FC<CreatePartnerModalProps> = ({
  type,
  isOpen,
  onClose,
  onCreated,
}) => {
  const { t } = useTranslation();
  const createClient = useCreateClient();
  const createSupplier = useCreateSupplier();

  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      let partner: Partner;
      if (type === 'client') {
        partner = await createClient.mutateAsync(form);
      } else {
        partner = await createSupplier.mutateAsync(form);
      }
      // RÈGLE AZALSCORE : Sélection automatique après création
      // Injection immédiate de TOUS les champs
      onCreated(partner);
      onClose();
      setForm({ name: '', email: '', phone: '', address: '', city: '', postal_code: '' });
    } catch (error) {
      console.error('Erreur création:', error);
    }
  };

  const isLoading = createClient.isPending || createSupplier.isPending;
  const title = type === 'client' ? t('action.newClient') : t('action.newSupplier');

  if (!isOpen) return null;

  return (
    <Modal isOpen onClose={onClose} title={title} size="md">
      <form onSubmit={handleSubmit}>
        <div className="azals-form-grid">
          <div className="azals-field azals-field--full">
            <label className="azals-field__label">
              {t('field.name')} <span className="required">*</span>
            </label>
            <input
              type="text"
              className="azals-input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              autoFocus
            />
          </div>
          <div className="azals-field">
            <label className="azals-field__label">{t('field.email')}</label>
            <input
              type="email"
              className="azals-input"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          <div className="azals-field">
            <label className="azals-field__label">{t('field.phone')}</label>
            <input
              type="text"
              className="azals-input"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </div>
          <div className="azals-field azals-field--full">
            <label className="azals-field__label">{t('field.address')}</label>
            <input
              type="text"
              className="azals-input"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
          </div>
          <div className="azals-field">
            <label className="azals-field__label">{t('field.postalCode')}</label>
            <input
              type="text"
              className="azals-input"
              value={form.postal_code}
              onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
            />
          </div>
          <div className="azals-field">
            <label className="azals-field__label">{t('field.city')}</label>
            <input
              type="text"
              className="azals-input"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
            />
          </div>
        </div>

        <div className="azals-modal__actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" isLoading={isLoading} leftIcon={<Check size={16} />}>
            {t('common.create')}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================
// PAGE PRINCIPALE - ACTION
// ============================================================

export const ActionPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createDocument = useCreateDocument();

  // État du formulaire
  const [form, setForm] = useState<DocumentFormState>({
    type: 'QUOTE',
    partner_id: '',
    partner: null,
    date: new Date().toISOString().split('T')[0],
    due_date: '',
    validity_date: '',
    reference: '',
    notes: '',
    lines: [],
  });

  // États modaux
  const [showCreatePartner, setShowCreatePartner] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Configuration du type actuel
  const typeConfig = DOCUMENT_TYPES.find((t) => t.id === form.type)!;

  // Gestion du changement de type
  const handleTypeChange = (newType: DocumentType) => {
    const newConfig = DOCUMENT_TYPES.find((t) => t.id === newType)!;
    const currentConfig = DOCUMENT_TYPES.find((t) => t.id === form.type)!;

    // Si le type de partenaire change, réinitialiser la sélection
    if (newConfig.partnerType !== currentConfig.partnerType) {
      setForm({
        ...form,
        type: newType,
        partner_id: '',
        partner: null,
      });
    } else {
      setForm({ ...form, type: newType });
    }
  };

  // RÈGLE AZALSCORE : Injection automatique TOUS les champs à la sélection
  const handlePartnerSelect = (partner: Partner) => {
    setForm({
      ...form,
      partner_id: partner.id,
      partner: partner, // Tous les champs sont conservés
    });
    setErrors({ ...errors, partner: '' });
  };

  // Création contextuelle partenaire
  const handlePartnerCreated = (partner: Partner) => {
    // Sélection automatique + injection immédiate
    handlePartnerSelect(partner);
  };

  // Validation du formulaire
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!form.partner_id) {
      newErrors.partner =
        typeConfig.partnerType === 'client'
          ? t('errors.selectClient')
          : t('errors.selectSupplier');
    }
    if (!form.date) {
      newErrors.date = t('errors.dateRequired');
    }
    if (form.lines.length === 0) {
      newErrors.lines = t('errors.addLine');
    }
    if (form.lines.some((l) => !l.description.trim())) {
      newErrors.lines = t('errors.lineDescription');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Soumission du formulaire
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await createDocument.mutateAsync({
        type: form.type,
        data: form,
      });

      // Redirection vers la liste appropriée
      if (form.type === 'QUOTE') {
        navigate('/invoicing/quotes');
      } else if (form.type === 'INVOICE') {
        navigate('/invoicing/invoices');
      } else if (form.type === 'PURCHASE_ORDER') {
        navigate('/purchases/orders');
      } else {
        navigate('/purchases/invoices');
      }
    } catch (error) {
      console.error('Erreur création document:', error);
    }
  };

  return (
    <PageWrapper
      title={t('action.pageTitle')}
      subtitle={t('action.pageSubtitle')}
    >
      <form onSubmit={handleSubmit}>
        {/* Sélecteur de type de document */}
        <Card className="mb-4">
          <label className="azals-label mb-2">{t('action.selectDocumentType')}</label>
          <DocumentTypeSelector value={form.type} onChange={handleTypeChange} />
        </Card>

        {/* Sélecteur de partenaire */}
        <Card className="mb-4">
          <PartnerSelector
            type={typeConfig.partnerType}
            value={form.partner}
            onSelect={handlePartnerSelect}
            onCreate={() => setShowCreatePartner(true)}
          />
          {errors.partner && (
            <div className="azals-form-error mt-2">
              <AlertCircle size={14} />
              <span>{errors.partner}</span>
            </div>
          )}
        </Card>

        {/* Informations générales */}
        <Card className="mb-4">
          <h3 className="azals-card__title mb-4">{t('action.generalInfo')}</h3>
          <Grid cols={3} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">
                {t('field.date')} <span className="required">*</span>
              </label>
              <input
                type="date"
                className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
              {errors.date && <span className="azals-form-error">{errors.date}</span>}
            </div>

            {typeConfig.hasValidity && (
              <div className="azals-field">
                <label className="azals-field__label">{t('field.validityDate')}</label>
                <input
                  type="date"
                  className="azals-input"
                  value={form.validity_date}
                  onChange={(e) => setForm({ ...form, validity_date: e.target.value })}
                />
              </div>
            )}

            {typeConfig.hasDueDate && (
              <div className="azals-field">
                <label className="azals-field__label">{t('field.dueDate')}</label>
                <input
                  type="date"
                  className="azals-input"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </div>
            )}

            <div className="azals-field">
              <label className="azals-field__label">{t('field.reference')}</label>
              <input
                type="text"
                className="azals-input"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                placeholder={t('field.reference')}
              />
            </div>
          </Grid>
        </Card>

        {/* Éditeur de lignes */}
        <Card className="mb-4">
          {errors.lines && (
            <div className="azals-alert azals-alert--error mb-4">
              <AlertCircle size={16} />
              <span>{errors.lines}</span>
            </div>
          )}
          <LineEditor
            lines={form.lines}
            onChange={(lines) => setForm({ ...form, lines })}
          />
        </Card>

        {/* Notes */}
        <Card className="mb-4">
          <div className="azals-field">
            <label className="azals-field__label">{t('field.notes')}</label>
            <textarea
              className="azals-textarea"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={3}
              placeholder={t('field.notes')}
            />
          </div>
        </Card>

        {/* Actions */}
        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
            {t('common.cancel')}
          </Button>
          <Button
            type="submit"
            isLoading={createDocument.isPending}
            leftIcon={<Save size={16} />}
          >
            {t('action.createDocument')}
          </Button>
        </div>
      </form>

      {/* Modal création partenaire contextuelle */}
      <CreatePartnerModal
        type={typeConfig.partnerType}
        isOpen={showCreatePartner}
        onClose={() => setShowCreatePartner(false)}
        onCreated={handlePartnerCreated}
      />
    </PageWrapper>
  );
};

// ============================================================
// EXPORT
// ============================================================

export default ActionPage;
