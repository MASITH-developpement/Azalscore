/**
 * AZALSCORE Module - NOUVELLE SAISIE
 * ===================================
 *
 * Formulaire ultra-simplifie pour creer un devis en moins de 30 secondes.
 *
 * OBJECTIFS UX:
 * - Action en 1-2 clics maximum
 * - Autocompletion 90%+ des champs
 * - Zero jargon comptable
 * - Mobile-first responsive
 * - Valeurs par defaut intelligentes
 *
 * FLUX: Saisie rapide -> Devis brouillon -> Validation -> Envoi
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, FileText, User, Package, Euro, Check, X,
  Sparkles, Search, ArrowRight, Clock, Building,
  Phone, Mail, Loader2, ChevronDown, Trash2, AlertCircle
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import { CompanyAutocomplete } from '@/modules/enrichment';
import type { EnrichedContactFields } from '@/modules/enrichment';
import type { PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface QuickCustomer {
  id: string;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
}

interface QuickProduct {
  id: string;
  code: string;
  name: string;
  unit_price: number;
  unit?: string;
  tax_rate?: number;
}

interface QuickLine {
  id: string;
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
}

interface QuickDevisResult {
  id: string;
  number: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useQuickCustomers = (search: string) => {
  return useQuery({
    queryKey: ['quick-customers', search],
    queryFn: async () => {
      if (!search || search.length < 2) return [];
      const params = new URLSearchParams({
        search,
        page_size: '10',
        is_active: 'true'
      });
      try {
        const response = await api.get<PaginatedResponse<QuickCustomer>>(
          `/v1/partners/clients?${params}`
        );
        return (response as unknown as PaginatedResponse<QuickCustomer>).items || [];
      } catch {
        return [];
      }
    },
    enabled: search.length >= 2,
  });
};

const useQuickProducts = (search: string) => {
  return useQuery({
    queryKey: ['quick-products', search],
    queryFn: async () => {
      if (!search || search.length < 2) return [];
      const params = new URLSearchParams({
        search,
        page_size: '10',
        is_active: 'true'
      });
      try {
        const response = await api.get<PaginatedResponse<QuickProduct>>(
          `/v1/inventory/products?${params}`
        );
        return (response as unknown as PaginatedResponse<QuickProduct>).items || [];
      } catch {
        return [];
      }
    },
    enabled: search.length >= 2,
  });
};

const useCreateQuickDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      customer_id: string;
      lines: Omit<QuickLine, 'id'>[];
      notes?: string;
    }) => {
      const payload = {
        type: 'QUOTE',
        customer_id: data.customer_id,
        date: new Date().toISOString().split('T')[0],
        validity_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        notes: data.notes,
        lines: data.lines.map((line, index) => ({
          line_number: index + 1,
          description: line.description,
          quantity: line.quantity,
          unit_price: line.unit_price,
          tax_rate: line.tax_rate,
          discount_percent: 0,
        })),
      };
      const response = await api.post<QuickDevisResult>('/v1/commercial/documents', payload);
      return response as unknown as QuickDevisResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useCreateQuickCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      name: string;
      email?: string;
      phone?: string;
      siret?: string;
      address?: string;
      city?: string;
      postal_code?: string;
    }) => {
      const response = await api.post<QuickCustomer>('/v1/partners/clients', {
        ...data,
        type: 'CUSTOMER',
        is_active: true,
      });
      return response as unknown as QuickCustomer;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quick-customers'] });
      queryClient.invalidateQueries({ queryKey: ['partners', 'clients'] });
    },
  });
};

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount);
};

const generateTempId = () => `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// ============================================================
// COMPONENTS
// ============================================================

/**
 * CustomerSelector - Selection ou creation rapide de client
 */
interface CustomerSelectorProps {
  value: QuickCustomer | null;
  onChange: (customer: QuickCustomer | null) => void;
  onCreateNew: () => void;
}

const CustomerSelector: React.FC<CustomerSelectorProps> = ({
  value,
  onChange,
  onCreateNew
}) => {
  const [search, setSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: customers, isLoading } = useQuickCustomers(search);

  const handleSelect = (customer: QuickCustomer) => {
    onChange(customer);
    setSearch('');
    setShowDropdown(false);
  };

  const handleClear = () => {
    onChange(null);
    setSearch('');
    inputRef.current?.focus();
  };

  // Si un client est selectionne, afficher son info
  if (value) {
    return (
      <div className="azals-quick-customer-selected">
        <div className="azals-quick-customer-selected__info">
          <Building size={18} className="azals-quick-customer-selected__icon" />
          <div>
            <div className="azals-quick-customer-selected__name">{value.name}</div>
            {value.email && (
              <div className="azals-quick-customer-selected__detail">
                <Mail size={12} /> {value.email}
              </div>
            )}
          </div>
        </div>
        <button
          type="button"
          className="azals-quick-customer-selected__clear"
          onClick={handleClear}
          aria-label="Changer de client"
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="azals-quick-customer">
      <div className="azals-quick-customer__search">
        <Search size={18} className="azals-quick-customer__search-icon" />
        <input
          ref={inputRef}
          type="text"
          className="azals-quick-customer__input"
          placeholder="Rechercher un client ou taper un nouveau nom..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => setShowDropdown(true)}
          autoComplete="off"
        />
        {isLoading && <Loader2 size={16} className="azals-quick-customer__loading animate-spin" />}
      </div>

      {showDropdown && search.length >= 2 && (
        <div className="azals-quick-customer__dropdown">
          {customers && customers.length > 0 ? (
            <>
              {customers.map((customer) => (
                <button
                  key={customer.id}
                  type="button"
                  className="azals-quick-customer__option"
                  onClick={() => handleSelect(customer)}
                >
                  <Building size={16} />
                  <div>
                    <div className="azals-quick-customer__option-name">{customer.name}</div>
                    {customer.email && (
                      <div className="azals-quick-customer__option-email">{customer.email}</div>
                    )}
                  </div>
                </button>
              ))}
              <div className="azals-quick-customer__divider" />
            </>
          ) : !isLoading && (
            <div className="azals-quick-customer__empty">
              Aucun client trouve
            </div>
          )}
          <button
            type="button"
            className="azals-quick-customer__create"
            onClick={onCreateNew}
          >
            <Plus size={16} />
            <span>Creer "{search}" comme nouveau client</span>
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * QuickLineEditor - Ajout rapide de lignes de devis
 */
interface QuickLineEditorProps {
  lines: QuickLine[];
  onChange: (lines: QuickLine[]) => void;
}

const QuickLineEditor: React.FC<QuickLineEditorProps> = ({ lines, onChange }) => {
  const [newLine, setNewLine] = useState({
    description: '',
    quantity: 1,
    unit_price: 0,
    tax_rate: 20,
  });

  const handleAddLine = () => {
    if (!newLine.description.trim()) return;

    const line: QuickLine = {
      id: generateTempId(),
      ...newLine,
    };
    onChange([...lines, line]);
    setNewLine({ description: '', quantity: 1, unit_price: 0, tax_rate: 20 });
  };

  const handleRemoveLine = (id: string) => {
    onChange(lines.filter(l => l.id !== id));
  };

  const handleUpdateLine = (id: string, field: keyof QuickLine, value: any) => {
    onChange(lines.map(l => l.id === id ? { ...l, [field]: value } : l));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newLine.description.trim()) {
      e.preventDefault();
      handleAddLine();
    }
  };

  const calculateLineTotal = (line: QuickLine) => {
    return line.quantity * line.unit_price;
  };

  const totals = useMemo(() => {
    const subtotal = lines.reduce((sum, l) => sum + calculateLineTotal(l), 0);
    const tax = lines.reduce((sum, l) => sum + (calculateLineTotal(l) * l.tax_rate / 100), 0);
    return { subtotal, tax, total: subtotal + tax };
  }, [lines]);

  return (
    <div className="azals-quick-lines">
      {/* Lignes existantes */}
      {lines.length > 0 && (
        <div className="azals-quick-lines__list">
          {lines.map((line) => (
            <div key={line.id} className="azals-quick-lines__item">
              <div className="azals-quick-lines__item-main">
                <input
                  type="text"
                  className="azals-quick-lines__description"
                  value={line.description}
                  onChange={(e) => handleUpdateLine(line.id, 'description', e.target.value)}
                  placeholder="Description..."
                />
                <div className="azals-quick-lines__item-numbers">
                  <input
                    type="number"
                    className="azals-quick-lines__qty"
                    value={line.quantity}
                    onChange={(e) => handleUpdateLine(line.id, 'quantity', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="1"
                    title="Quantite"
                  />
                  <span className="azals-quick-lines__x">x</span>
                  <input
                    type="number"
                    className="azals-quick-lines__price"
                    value={line.unit_price}
                    onChange={(e) => handleUpdateLine(line.id, 'unit_price', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                    title="Prix unitaire HT"
                  />
                  <span className="azals-quick-lines__eq">=</span>
                  <span className="azals-quick-lines__total">
                    {formatCurrency(calculateLineTotal(line))}
                  </span>
                </div>
              </div>
              <button
                type="button"
                className="azals-quick-lines__remove"
                onClick={() => handleRemoveLine(line.id)}
                aria-label="Supprimer la ligne"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Nouvelle ligne */}
      <div className="azals-quick-lines__add">
        <div className="azals-quick-lines__add-main">
          <input
            type="text"
            className="azals-quick-lines__add-description"
            value={newLine.description}
            onChange={(e) => setNewLine({ ...newLine, description: e.target.value })}
            onKeyPress={handleKeyPress}
            placeholder="Ajouter une prestation ou un produit..."
          />
          <div className="azals-quick-lines__add-numbers">
            <input
              type="number"
              className="azals-quick-lines__qty"
              value={newLine.quantity}
              onChange={(e) => setNewLine({ ...newLine, quantity: parseFloat(e.target.value) || 1 })}
              min="1"
              step="1"
              title="Quantite"
            />
            <span className="azals-quick-lines__x">x</span>
            <input
              type="number"
              className="azals-quick-lines__price"
              value={newLine.unit_price || ''}
              onChange={(e) => setNewLine({ ...newLine, unit_price: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              placeholder="Prix"
              title="Prix unitaire HT"
            />
          </div>
        </div>
        <button
          type="button"
          className="azals-quick-lines__add-btn"
          onClick={handleAddLine}
          disabled={!newLine.description.trim()}
        >
          <Plus size={18} />
        </button>
      </div>

      {/* Totaux */}
      {lines.length > 0 && (
        <div className="azals-quick-lines__totals">
          <div className="azals-quick-lines__totals-row">
            <span>Total HT</span>
            <span>{formatCurrency(totals.subtotal)}</span>
          </div>
          <div className="azals-quick-lines__totals-row">
            <span>TVA (20%)</span>
            <span>{formatCurrency(totals.tax)}</span>
          </div>
          <div className="azals-quick-lines__totals-row azals-quick-lines__totals-row--main">
            <span>Total TTC</span>
            <span>{formatCurrency(totals.total)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * NewCustomerModal - Creation rapide de client depuis enrichissement
 */
interface NewCustomerModalProps {
  initialName: string;
  onSave: (customer: QuickCustomer) => void;
  onCancel: () => void;
}

const NewCustomerModal: React.FC<NewCustomerModalProps> = ({
  initialName,
  onSave,
  onCancel
}) => {
  const [form, setForm] = useState({
    name: initialName,
    email: '',
    phone: '',
    siret: '',
    address: '',
    city: '',
    postal_code: '',
  });

  const createCustomer = useCreateQuickCustomer();

  const handleCompanySelect = (fields: EnrichedContactFields) => {
    setForm(prev => ({
      ...prev,
      name: fields.name || fields.company_name || prev.name,
      address: fields.address_line1 || fields.address || prev.address,
      city: fields.city || prev.city,
      postal_code: fields.postal_code || prev.postal_code,
      siret: fields.siret || fields.siren || prev.siret,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      const customer = await createCustomer.mutateAsync(form);
      onSave(customer);
    } catch (error) {
      console.error('Erreur creation client:', error);
    }
  };

  return (
    <div className="azals-modal-overlay">
      <div className="azals-modal azals-modal--quick">
        <div className="azals-modal__header">
          <h3>Nouveau client</h3>
          <button type="button" onClick={onCancel} className="azals-modal__close">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="azals-modal__body">
          <div className="azals-field">
            <label>Nom / Raison sociale *</label>
            <CompanyAutocomplete
              value={form.name}
              onChange={(value) => setForm({ ...form, name: value })}
              onSelect={handleCompanySelect}
              placeholder="Rechercher ou saisir le nom..."
            />
          </div>

          <div className="azals-field-row">
            <div className="azals-field">
              <label>Email</label>
              <input
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="contact@exemple.fr"
              />
            </div>
            <div className="azals-field">
              <label>Telephone</label>
              <input
                type="tel"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="01 23 45 67 89"
              />
            </div>
          </div>

          <div className="azals-field">
            <label>Adresse</label>
            <input
              type="text"
              className="azals-input"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              placeholder="Adresse..."
            />
          </div>

          <div className="azals-field-row">
            <div className="azals-field">
              <label>Code postal</label>
              <input
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
                placeholder="75001"
              />
            </div>
            <div className="azals-field">
              <label>Ville</label>
              <input
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                placeholder="Paris"
              />
            </div>
          </div>
        </form>

        <div className="azals-modal__footer">
          <Button variant="ghost" onClick={onCancel}>
            Annuler
          </Button>
          <Button
            type="submit"
            onClick={() => {
              if (!form.name.trim()) return;
              createCustomer.mutateAsync(form).then(onSave).catch(console.error);
            }}
            isLoading={createCustomer.isPending}
            disabled={!form.name.trim()}
          >
            Creer le client
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const SaisieModule: React.FC = () => {
  const [customer, setCustomer] = useState<QuickCustomer | null>(null);
  const [lines, setLines] = useState<QuickLine[]>([]);
  const [notes, setNotes] = useState('');
  const [showNewCustomerModal, setShowNewCustomerModal] = useState(false);
  const [newCustomerName, setNewCustomerName] = useState('');
  const [success, setSuccess] = useState<QuickDevisResult | null>(null);

  const createDevis = useCreateQuickDevis();

  const canSubmit = customer && lines.length > 0;

  const handleCreateNewCustomer = () => {
    const searchInput = document.querySelector('.azals-quick-customer__input') as HTMLInputElement;
    setNewCustomerName(searchInput?.value || '');
    setShowNewCustomerModal(true);
  };

  const handleCustomerCreated = (newCustomer: QuickCustomer) => {
    setCustomer(newCustomer);
    setShowNewCustomerModal(false);
    setNewCustomerName('');
  };

  const handleSubmit = async () => {
    if (!canSubmit || !customer) return;

    try {
      const result = await createDevis.mutateAsync({
        customer_id: customer.id,
        lines: lines.map(({ id, ...rest }) => rest),
        notes: notes || undefined,
      });
      setSuccess(result);
    } catch (error) {
      console.error('Erreur creation devis:', error);
    }
  };

  const handleReset = () => {
    setCustomer(null);
    setLines([]);
    setNotes('');
    setSuccess(null);
  };

  const handleGoToDevis = () => {
    if (success) {
      window.dispatchEvent(new CustomEvent('azals:navigate', {
        detail: { view: 'gestion-devis', params: { id: success.id } }
      }));
    }
  };

  // Ecran de succes
  if (success) {
    return (
      <PageWrapper title="Devis cree !">
        <div className="azals-quick-success">
          <div className="azals-quick-success__icon">
            <Check size={48} />
          </div>
          <h2 className="azals-quick-success__title">
            Devis {success.number} cree avec succes
          </h2>
          <p className="azals-quick-success__subtitle">
            Votre devis est enregistre en brouillon. Vous pouvez le modifier, le valider puis l'envoyer a votre client.
          </p>
          <div className="azals-quick-success__actions">
            <Button variant="ghost" onClick={handleReset}>
              Nouveau devis
            </Button>
            <Button onClick={handleGoToDevis}>
              Voir le devis <ArrowRight size={16} />
            </Button>
          </div>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Nouvelle saisie"
      subtitle="Creez un devis en quelques secondes"
    >
      <div className="azals-quick-saisie">
        {/* Etape 1: Client */}
        <Card className="azals-quick-step">
          <div className="azals-quick-step__header">
            <span className="azals-quick-step__number">1</span>
            <h3>Pour quel client ?</h3>
          </div>
          <CustomerSelector
            value={customer}
            onChange={setCustomer}
            onCreateNew={handleCreateNewCustomer}
          />
        </Card>

        {/* Etape 2: Lignes */}
        <Card className="azals-quick-step">
          <div className="azals-quick-step__header">
            <span className="azals-quick-step__number">2</span>
            <h3>Quels produits ou services ?</h3>
          </div>
          <QuickLineEditor lines={lines} onChange={setLines} />
        </Card>

        {/* Etape 3: Notes (optionnel) */}
        <Card className="azals-quick-step azals-quick-step--optional">
          <div className="azals-quick-step__header">
            <span className="azals-quick-step__number">3</span>
            <h3>Notes (optionnel)</h3>
          </div>
          <textarea
            className="azals-textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Conditions particulieres, delais, remarques..."
            rows={2}
          />
        </Card>

        {/* Action principale */}
        <div className="azals-quick-action">
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!canSubmit}
            isLoading={createDevis.isPending}
          >
            <FileText size={20} />
            Creer le devis
          </Button>
          {!canSubmit && (
            <p className="azals-quick-action__hint">
              {!customer ? 'Selectionnez un client' : 'Ajoutez au moins une ligne'}
            </p>
          )}
        </div>
      </div>

      {/* Modal creation client */}
      {showNewCustomerModal && (
        <NewCustomerModal
          initialName={newCustomerName}
          onSave={handleCustomerCreated}
          onCancel={() => setShowNewCustomerModal(false)}
        />
      )}
    </PageWrapper>
  );
};

export default SaisieModule;
