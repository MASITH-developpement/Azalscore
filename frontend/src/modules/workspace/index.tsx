/**
 * AZALSCORE - Workspace (Feuille de travail unique)
 * ================================================
 *
 * Vue unique de saisie selon la logique AZALSCORE :
 * - Pas de navigation pendant la saisie
 * - Sélection = injection automatique complète
 * - Simplicité maximale
 * - NO-CODE côté utilisateur
 *
 * Structure :
 * 1. Sélecteur de type document (état interne)
 * 2. Zone client (sélection simple → injection auto)
 * 3. Zone lignes centrale
 * 4. Zone totaux lisible
 * 5. Action principale claire
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Trash2, Check, AlertCircle, ChevronDown,
  FileText, Receipt, User, Calendar
} from 'lucide-react';
import { api } from '@core/api-client';
import { useTranslation } from '@core/i18n';
import type { PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

type DocumentType = 'QUOTE' | 'INVOICE';

interface Customer {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  vat_number?: string;
}

interface LineData {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

interface DocumentData {
  type: DocumentType;
  customer_id: string;
  date: string;
  due_date?: string;
  validity_date?: string;
  notes?: string;
  lines: Omit<LineData, 'id'>[];
}

// ============================================================
// API HOOKS
// ============================================================

const useCustomers = () => {
  return useQuery({
    queryKey: ['workspace', 'customers'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        '/v1/partners/clients?page_size=500&is_active=true'
      );
      return (response as unknown as PaginatedResponse<Customer>).items;
    },
    staleTime: 5 * 60 * 1000, // Cache 5 minutes
  });
};

const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: DocumentData) => {
      const response = await api.post('/v1/commercial/documents', data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

// ============================================================
// CONSTANTES
// ============================================================

const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount);
};

// ============================================================
// COMPOSANT - Sélecteur de type document
// ============================================================

interface TypeSelectorProps {
  value: DocumentType;
  onChange: (type: DocumentType) => void;
}

const TypeSelector: React.FC<TypeSelectorProps> = ({ value, onChange }) => {
  const { t } = useTranslation();

  return (
    <div className="azals-ws-type-selector">
      <button
        type="button"
        className={`azals-ws-type-btn ${value === 'QUOTE' ? 'azals-ws-type-btn--active' : ''}`}
        onClick={() => onChange('QUOTE')}
      >
        <FileText size={18} />
        <span>{t('document.types.quote')}</span>
      </button>
      <button
        type="button"
        className={`azals-ws-type-btn ${value === 'INVOICE' ? 'azals-ws-type-btn--active' : ''}`}
        onClick={() => onChange('INVOICE')}
      >
        <Receipt size={18} />
        <span>{t('document.types.invoice')}</span>
      </button>
    </div>
  );
};

// ============================================================
// COMPOSANT - Zone Client (injection automatique)
// ============================================================

interface CustomerZoneProps {
  customers: Customer[];
  selectedId: string;
  onSelect: (id: string) => void;
  isLoading: boolean;
}

const CustomerZone: React.FC<CustomerZoneProps> = ({
  customers,
  selectedId,
  onSelect,
  isLoading
}) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const selectedCustomer = customers.find(c => c.id === selectedId);

  const filteredCustomers = useMemo(() => {
    if (!search) return customers;
    const searchLower = search.toLowerCase();
    return customers.filter(c =>
      c.name.toLowerCase().includes(searchLower) ||
      c.code.toLowerCase().includes(searchLower)
    );
  }, [customers, search]);

  const handleSelect = (customer: Customer) => {
    // RÈGLE AZALSCORE : Sélection = injection automatique COMPLÈTE
    onSelect(customer.id);
    setIsOpen(false);
    setSearch('');
  };

  if (isLoading) {
    return (
      <div className="azals-ws-customer azals-ws-customer--loading">
        <div className="azals-spinner azals-spinner--sm" />
        <span>{t('common.loading')}</span>
      </div>
    );
  }

  return (
    <div className="azals-ws-customer">
      <div className="azals-ws-customer__header">
        <User size={16} />
        <span>{t('workspace.customer')}</span>
      </div>

      {/* Sélecteur dropdown */}
      <div className="azals-ws-customer__selector">
        <button
          type="button"
          className="azals-ws-customer__trigger"
          onClick={() => setIsOpen(!isOpen)}
        >
          {selectedCustomer ? (
            <span className="azals-ws-customer__selected">
              {selectedCustomer.name}
              <span className="azals-ws-customer__code">{selectedCustomer.code}</span>
            </span>
          ) : (
            <span className="azals-ws-customer__placeholder">
              {t('workspace.selectCustomer')}
            </span>
          )}
          <ChevronDown size={16} className={isOpen ? 'rotated' : ''} />
        </button>

        {isOpen && (
          <div className="azals-ws-customer__dropdown">
            <input
              type="text"
              className="azals-ws-customer__search"
              placeholder={t('common.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
            <div className="azals-ws-customer__list">
              {filteredCustomers.map(customer => (
                <button
                  key={customer.id}
                  type="button"
                  className="azals-ws-customer__item"
                  onClick={() => handleSelect(customer)}
                >
                  <span className="azals-ws-customer__item-name">{customer.name}</span>
                  <span className="azals-ws-customer__item-code">{customer.code}</span>
                </button>
              ))}
              {filteredCustomers.length === 0 && (
                <div className="azals-ws-customer__empty">
                  {t('common.none')}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Informations injectées automatiquement */}
      {selectedCustomer && (
        <div className="azals-ws-customer__info">
          {selectedCustomer.email && (
            <div className="azals-ws-customer__field">
              <span>{selectedCustomer.email}</span>
            </div>
          )}
          {selectedCustomer.phone && (
            <div className="azals-ws-customer__field">
              <span>{selectedCustomer.phone}</span>
            </div>
          )}
          {selectedCustomer.address && (
            <div className="azals-ws-customer__field">
              <span>
                {selectedCustomer.address}
                {selectedCustomer.postal_code && `, ${selectedCustomer.postal_code}`}
                {selectedCustomer.city && ` ${selectedCustomer.city}`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================
// COMPOSANT - Éditeur de lignes simplifié
// ============================================================

interface LinesEditorProps {
  lines: LineData[];
  onChange: (lines: LineData[]) => void;
}

const LinesEditor: React.FC<LinesEditorProps> = ({ lines, onChange }) => {
  const { t } = useTranslation();

  const addLine = () => {
    const newLine: LineData = {
      id: `line-${Date.now()}`,
      description: '',
      quantity: 1,
      unit: 'unité',
      unit_price: 0,
      discount_percent: 0,
      tax_rate: 20,
    };
    onChange([...lines, newLine]);
  };

  const updateLine = (index: number, updates: Partial<LineData>) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], ...updates };
    onChange(newLines);
  };

  const removeLine = (index: number) => {
    onChange(lines.filter((_, i) => i !== index));
  };

  const calculateLineTotal = (line: LineData) => {
    const baseAmount = line.quantity * line.unit_price;
    const discountAmount = baseAmount * (line.discount_percent / 100);
    return baseAmount - discountAmount;
  };

  const totals = useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        const subtotal = calculateLineTotal(line);
        const taxAmount = subtotal * (line.tax_rate / 100);
        return {
          subtotal: acc.subtotal + subtotal,
          taxAmount: acc.taxAmount + taxAmount,
          total: acc.total + subtotal + taxAmount,
        };
      },
      { subtotal: 0, taxAmount: 0, total: 0 }
    );
  }, [lines]);

  return (
    <div className="azals-ws-lines">
      <div className="azals-ws-lines__header">
        <span>{t('lines.title')}</span>
        <button
          type="button"
          className="azals-ws-lines__add"
          onClick={addLine}
        >
          <Plus size={16} />
          {t('lines.add')}
        </button>
      </div>

      {lines.length === 0 ? (
        <div className="azals-ws-lines__empty">
          <AlertCircle size={20} />
          <span>{t('lines.empty')}</span>
          <span className="azals-ws-lines__hint">{t('lines.emptyHint')}</span>
        </div>
      ) : (
        <div className="azals-ws-lines__table">
          <div className="azals-ws-lines__row azals-ws-lines__row--header">
            <div className="azals-ws-lines__col azals-ws-lines__col--desc">{t('lines.description')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--qty">{t('lines.quantity')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--price">{t('lines.unitPrice')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--discount">{t('lines.discount')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--vat">{t('lines.vat')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--total">{t('lines.totalHT')}</div>
            <div className="azals-ws-lines__col azals-ws-lines__col--actions"></div>
          </div>

          {lines.map((line, index) => (
            <div key={line.id} className="azals-ws-lines__row">
              <div className="azals-ws-lines__col azals-ws-lines__col--desc">
                <input
                  type="text"
                  value={line.description}
                  onChange={(e) => updateLine(index, { description: e.target.value })}
                  placeholder={t('lines.description')}
                  className="azals-ws-input"
                />
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--qty">
                <input
                  type="number"
                  value={line.quantity}
                  onChange={(e) => updateLine(index, { quantity: parseFloat(e.target.value) || 0 })}
                  min="0"
                  step="0.01"
                  className="azals-ws-input azals-ws-input--number"
                />
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--price">
                <input
                  type="number"
                  value={line.unit_price}
                  onChange={(e) => updateLine(index, { unit_price: parseFloat(e.target.value) || 0 })}
                  min="0"
                  step="0.01"
                  className="azals-ws-input azals-ws-input--number"
                />
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--discount">
                <input
                  type="number"
                  value={line.discount_percent}
                  onChange={(e) => updateLine(index, { discount_percent: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="100"
                  step="0.1"
                  className="azals-ws-input azals-ws-input--number"
                />
                <span className="azals-ws-lines__suffix">%</span>
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--vat">
                <select
                  value={line.tax_rate}
                  onChange={(e) => updateLine(index, { tax_rate: parseFloat(e.target.value) })}
                  className="azals-ws-select"
                >
                  {TVA_RATES.map((rate) => (
                    <option key={rate.value} value={rate.value}>
                      {rate.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--total">
                <span className="azals-ws-lines__amount">
                  {formatCurrency(calculateLineTotal(line))}
                </span>
              </div>
              <div className="azals-ws-lines__col azals-ws-lines__col--actions">
                <button
                  type="button"
                  className="azals-ws-lines__delete"
                  onClick={() => removeLine(index)}
                  title={t('common.delete')}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Zone totaux */}
      <div className="azals-ws-totals">
        <div className="azals-ws-totals__row">
          <span>{t('document.totalHT')}</span>
          <span>{formatCurrency(totals.subtotal)}</span>
        </div>
        <div className="azals-ws-totals__row">
          <span>{t('document.totalTVA')}</span>
          <span>{formatCurrency(totals.taxAmount)}</span>
        </div>
        <div className="azals-ws-totals__row azals-ws-totals__row--main">
          <span>{t('document.totalTTC')}</span>
          <span>{formatCurrency(totals.total)}</span>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// COMPOSANT PRINCIPAL - Workspace
// ============================================================

const Workspace: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // État du document
  const [documentType, setDocumentType] = useState<DocumentType>('QUOTE');
  const [customerId, setCustomerId] = useState('');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState('');
  const [validityDate, setValidityDate] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<LineData[]>([]);

  // État UI
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState('');

  // Données
  const { data: customers = [], isLoading: loadingCustomers } = useCustomers();
  const createDocument = useCreateDocument();

  // Reset du formulaire après création réussie
  const resetForm = useCallback(() => {
    setCustomerId('');
    setDocDate(new Date().toISOString().split('T')[0]);
    setDueDate('');
    setValidityDate('');
    setNotes('');
    setLines([]);
    setErrors({});
  }, []);

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!customerId) {
      newErrors.customer = t('validation.customerRequired');
    }
    if (!docDate) {
      newErrors.date = t('validation.dateRequired');
    }
    if (lines.length === 0) {
      newErrors.lines = t('validation.linesRequired');
    }
    if (lines.some((l) => !l.description.trim())) {
      newErrors.lines = t('validation.descriptionRequired');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Soumission
  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      await createDocument.mutateAsync({
        type: documentType,
        customer_id: customerId,
        date: docDate,
        due_date: dueDate || undefined,
        validity_date: validityDate || undefined,
        notes: notes || undefined,
        lines: lines.map(({ id, ...line }) => line),
      });

      setSuccessMessage(t('workspace.documentCreated'));
      resetForm();

      // Effacer le message après 3 secondes
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Save failed:', error);
      setErrors({ submit: t('errors.saveFailed') });
    }
  };

  return (
    <div className="azals-workspace">
      {/* Message de succès */}
      {successMessage && (
        <div className="azals-ws-success">
          <Check size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Surface de travail */}
      <div className="azals-ws-sheet">
        {/* En-tête : Type de document */}
        <div className="azals-ws-section">
          <TypeSelector value={documentType} onChange={setDocumentType} />
        </div>

        {/* Zone client */}
        <div className="azals-ws-section">
          <CustomerZone
            customers={customers}
            selectedId={customerId}
            onSelect={setCustomerId}
            isLoading={loadingCustomers}
          />
          {errors.customer && (
            <div className="azals-ws-error">{errors.customer}</div>
          )}
        </div>

        {/* Date */}
        <div className="azals-ws-section azals-ws-section--dates">
          <div className="azals-ws-date">
            <label>
              <Calendar size={14} />
              {t('workspace.date')}
            </label>
            <input
              type="date"
              value={docDate}
              onChange={(e) => setDocDate(e.target.value)}
              className="azals-ws-input"
            />
          </div>

          {documentType === 'QUOTE' && (
            <div className="azals-ws-date">
              <label>{t('workspace.validityDate')}</label>
              <input
                type="date"
                value={validityDate}
                onChange={(e) => setValidityDate(e.target.value)}
                className="azals-ws-input"
              />
            </div>
          )}

          {documentType === 'INVOICE' && (
            <div className="azals-ws-date">
              <label>{t('workspace.dueDate')}</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="azals-ws-input"
              />
            </div>
          )}
        </div>

        {/* Zone lignes */}
        <div className="azals-ws-section">
          <LinesEditor lines={lines} onChange={setLines} />
          {errors.lines && (
            <div className="azals-ws-error">{errors.lines}</div>
          )}
        </div>

        {/* Notes */}
        <div className="azals-ws-section">
          <label className="azals-ws-label">{t('workspace.notes')}</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="azals-ws-textarea"
            rows={2}
            placeholder={t('workspace.notesPlaceholder')}
          />
        </div>

        {/* Erreur de soumission */}
        {errors.submit && (
          <div className="azals-ws-error azals-ws-error--submit">
            <AlertCircle size={16} />
            {errors.submit}
          </div>
        )}

        {/* Action principale */}
        <div className="azals-ws-action">
          <button
            type="button"
            className="azals-ws-submit"
            onClick={handleSubmit}
            disabled={createDocument.isPending}
          >
            {createDocument.isPending ? (
              <>
                <div className="azals-spinner azals-spinner--sm" />
                {t('common.loading')}
              </>
            ) : (
              <>
                <Check size={18} />
                {t('workspace.createDocument')}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
