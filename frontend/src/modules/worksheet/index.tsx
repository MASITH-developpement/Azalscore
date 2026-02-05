/**
 * AZALSCORE - Feuille de Travail Unique
 * =====================================
 *
 * Vue unique de saisie — PAS un ERP.
 *
 * Principes :
 * - Une seule page de travail
 * - Aucune navigation pendant la saisie
 * - Sélection = injection automatique complète
 * - Simplicité maximale
 * - NO-CODE côté utilisateur
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Check, Plus, Trash2, ChevronDown, Loader2, X, UserPlus, Package } from 'lucide-react';
import { api } from '@core/api-client';
import { useTranslation } from '../i18n';
import { ErrorState } from '../../ui-engine/components/StateViews';

// ============================================================
// TYPES
// ============================================================

type DocumentType = 'QUOTE' | 'INVOICE' | 'ORDER' | 'INTERVENTION';

interface Client {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
}

interface LineData {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
}

interface DocumentData {
  type: DocumentType;
  client_id: string;
  client?: Client;
  date: string;
  lines: LineData[];
  notes?: string;
}

interface Product {
  id: string;
  code: string;
  name: string;
  sale_price?: number;
  purchase_price?: number;
}

// ============================================================
// HOOKS API
// ============================================================

const useClients = () => {
  return useQuery({
    queryKey: ['clients', 'lookup'],
    queryFn: async () => {
      const response = await api.get<{ items: Client[] }>(
        '/v1/commercial/customers?page_size=100&is_active=true'
      );
      return (response as any).items || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });
};

const useSaveDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: DocumentData) => {
      const endpoint = data.type === 'INTERVENTION'
        ? '/v1/interventions'
        : '/v1/commercial/documents';

      const payload = data.type === 'INTERVENTION'
        ? {
            client_id: data.client_id,
            titre: data.lines[0]?.description || 'Intervention',
            description: data.notes,
            type_intervention: 'MAINTENANCE',
            priorite: 'NORMAL',
          }
        : {
            type: data.type,
            customer_id: data.client_id,
            date: data.date,
            notes: data.notes,
            lines: data.lines.map(l => ({
              description: l.description,
              quantity: l.quantity,
              unit_price: l.unit_price,
              tax_rate: l.tax_rate,
              discount_percent: 0,
            })),
          };

      return api.post(endpoint, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

const useCreateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Client>) => {
      const response = await api.post<Client>('/v1/commercial/customers', data);
      return response as unknown as Client;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });
};

const useProducts = () => {
  return useQuery({
    queryKey: ['products', 'lookup'],
    queryFn: async () => {
      const response = await api.get<{ items: Product[] }>(
        '/v1/inventory/products?page_size=100&is_active=true'
      );
      return (response as any).items || [];
    },
    staleTime: 5 * 60 * 1000,
  });
};

const useCreateProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Product>) => {
      const response = await api.post<Product>('/v1/inventory/products', data);
      return response as unknown as Product;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};

// ============================================================
// COMPOSANTS INTERNES
// ============================================================

interface ClientSelectorProps {
  clients: Client[];
  selectedClient: Client | null;
  onSelect: (client: Client) => void;
  onClientCreated: (client: Client) => void;
  t: (key: string) => string;
}

const ClientSelector: React.FC<ClientSelectorProps> = ({
  clients,
  selectedClient,
  onSelect,
  onClientCreated,
  t
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newClient, setNewClient] = useState({ name: '', email: '', phone: '', city: '' });
  const [createError, setCreateError] = useState('');

  const createClient = useCreateClient();

  const filtered = useMemo(() => {
    if (!search) return clients.slice(0, 20);
    const lower = search.toLowerCase();
    return clients.filter(c =>
      c.name.toLowerCase().includes(lower) ||
      c.code.toLowerCase().includes(lower)
    ).slice(0, 20);
  }, [clients, search]);

  const handleCreateClient = async () => {
    if (!newClient.name.trim()) {
      setCreateError('Le nom est obligatoire');
      return;
    }
    setCreateError('');
    try {
      const created = await createClient.mutateAsync(newClient);
      onClientCreated(created);
      setShowCreate(false);
      setIsOpen(false);
      setNewClient({ name: '', email: '', phone: '', city: '' });
    } catch (err: any) {
      setCreateError(err.message || 'Erreur lors de la création');
    }
  };

  return (
    <div className="azals-ws-client">
      <div
        className="azals-ws-client__selected"
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedClient ? (
          <div className="azals-ws-client__info">
            <span className="azals-ws-client__name">{selectedClient.name}</span>
            <span className="azals-ws-client__details">
              {selectedClient.city && `${selectedClient.city} `}
              {selectedClient.phone && `• ${selectedClient.phone}`}
            </span>
          </div>
        ) : (
          <span className="azals-ws-client__placeholder">
            {t('worksheet.selectClient')}
          </span>
        )}
        <ChevronDown size={20} className={isOpen ? 'rotate-180' : ''} />
      </div>

      {isOpen && (
        <div className="azals-ws-client__dropdown">
          {/* Option Nouveau Client en premier */}
          <div
            className="azals-ws-client__new"
            onClick={() => setShowCreate(!showCreate)}
          >
            <UserPlus size={16} />
            <span>Nouveau client</span>
            <Plus size={14} />
          </div>

          {/* Formulaire de création inline */}
          {showCreate && (
            <div className="azals-ws-client__create-form">
              {createError && <div className="azals-ws-client__error">{createError}</div>}
              <input
                type="text"
                placeholder="Nom du client *"
                value={newClient.name}
                onChange={e => setNewClient({ ...newClient, name: e.target.value })}
                autoFocus
              />
              <div className="azals-ws-client__create-row">
                <input
                  type="email"
                  placeholder="Email"
                  value={newClient.email}
                  onChange={e => setNewClient({ ...newClient, email: e.target.value })}
                />
                <input
                  type="tel"
                  placeholder="Téléphone"
                  value={newClient.phone}
                  onChange={e => setNewClient({ ...newClient, phone: e.target.value })}
                />
              </div>
              <input
                type="text"
                placeholder="Ville"
                value={newClient.city}
                onChange={e => setNewClient({ ...newClient, city: e.target.value })}
              />
              <div className="azals-ws-client__create-actions">
                <button
                  type="button"
                  className="azals-ws-client__btn-cancel"
                  onClick={() => { setShowCreate(false); setCreateError(''); }}
                >
                  Annuler
                </button>
                <button
                  type="button"
                  className="azals-ws-client__btn-create"
                  onClick={handleCreateClient}
                  disabled={createClient.isPending}
                >
                  {createClient.isPending ? <Loader2 size={14} className="spin" /> : <Check size={14} />}
                  Créer
                </button>
              </div>
            </div>
          )}

          {!showCreate && (
            <>
              <input
                type="text"
                className="azals-ws-client__search"
                placeholder={t('worksheet.searchClient')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
              <div className="azals-ws-client__list">
                {filtered.map(client => (
                  <div
                    key={client.id}
                    className="azals-ws-client__item"
                    onClick={() => {
                      onSelect(client);
                      setIsOpen(false);
                      setSearch('');
                    }}
                  >
                    <span className="azals-ws-client__item-name">{client.name}</span>
                    <span className="azals-ws-client__item-code">{client.code}</span>
                  </div>
                ))}
                {filtered.length === 0 && (
                  <div className="azals-ws-client__empty">
                    {t('worksheet.noClientFound')}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================
// PRODUCT SELECTOR INLINE
// ============================================================

interface ProductSelectorInlineProps {
  products: Product[];
  value: string;
  onSelect: (product: Product) => void;
  onChange: (value: string) => void;
  onProductCreated: (product: Product) => void;
  placeholder: string;
}

const ProductSelectorInline: React.FC<ProductSelectorInlineProps> = ({
  products,
  value,
  onSelect,
  onChange,
  onProductCreated,
  placeholder
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newProduct, setNewProduct] = useState({ code: '', name: '', sale_price: '' });
  const [createError, setCreateError] = useState('');

  const createProduct = useCreateProduct();

  const filtered = useMemo(() => {
    const searchTerm = search || value;
    if (!searchTerm) return products.slice(0, 10);
    const lower = searchTerm.toLowerCase();
    return products.filter(p =>
      p.name.toLowerCase().includes(lower) ||
      p.code.toLowerCase().includes(lower)
    ).slice(0, 10);
  }, [products, search, value]);

  const handleCreateProduct = async () => {
    if (!newProduct.code.trim() || !newProduct.name.trim()) {
      setCreateError('Code et nom obligatoires');
      return;
    }
    setCreateError('');
    try {
      const payload: Partial<Product> = {
        code: newProduct.code,
        name: newProduct.name,
      };
      if (newProduct.sale_price) {
        payload.sale_price = parseFloat(newProduct.sale_price);
      }
      const created = await createProduct.mutateAsync(payload);
      onProductCreated(created);
      setShowCreate(false);
      setIsOpen(false);
      setNewProduct({ code: '', name: '', sale_price: '' });
    } catch (err: any) {
      setCreateError(err.message || 'Erreur lors de la création');
    }
  };

  return (
    <div className="azals-ws-product-selector">
      <input
        type="text"
        className="azals-ws-input"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setSearch(e.target.value);
          if (!isOpen && e.target.value) setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder}
      />

      {isOpen && (
        <div className="azals-ws-product-dropdown">
          {/* Option Nouveau Article */}
          <div
            className="azals-ws-product-dropdown__new"
            onClick={() => setShowCreate(!showCreate)}
          >
            <Package size={14} />
            <span>Nouveau article</span>
            <Plus size={12} />
          </div>

          {showCreate && (
            <div className="azals-ws-product-dropdown__create">
              {createError && <div className="azals-ws-product-dropdown__error">{createError}</div>}
              <div className="azals-ws-product-dropdown__create-row">
                <input
                  type="text"
                  placeholder="Code *"
                  value={newProduct.code}
                  onChange={e => setNewProduct({ ...newProduct, code: e.target.value })}
                  autoFocus
                />
                <input
                  type="number"
                  placeholder="Prix"
                  value={newProduct.sale_price}
                  onChange={e => setNewProduct({ ...newProduct, sale_price: e.target.value })}
                />
              </div>
              <input
                type="text"
                placeholder="Désignation *"
                value={newProduct.name}
                onChange={e => setNewProduct({ ...newProduct, name: e.target.value })}
              />
              <div className="azals-ws-product-dropdown__actions">
                <button type="button" onClick={() => { setShowCreate(false); setCreateError(''); }}>
                  Annuler
                </button>
                <button
                  type="button"
                  className="primary"
                  onClick={handleCreateProduct}
                  disabled={createProduct.isPending}
                >
                  {createProduct.isPending ? <Loader2 size={12} className="spin" /> : <Check size={12} />}
                  Créer
                </button>
              </div>
            </div>
          )}

          {!showCreate && filtered.length > 0 && (
            <div className="azals-ws-product-dropdown__list">
              {filtered.map(product => (
                <div
                  key={product.id}
                  className="azals-ws-product-dropdown__item"
                  onClick={() => {
                    onSelect(product);
                    setIsOpen(false);
                    setSearch('');
                  }}
                >
                  <span className="code">{product.code}</span>
                  <span className="name">{product.name}</span>
                  {product.sale_price && (
                    <span className="price">{product.sale_price.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {isOpen && <div className="azals-ws-product-backdrop" onClick={() => setIsOpen(false)} />}
    </div>
  );
};

// ============================================================
// LINES EDITOR
// ============================================================

interface LinesEditorProps {
  lines: LineData[];
  products: Product[];
  onChange: (lines: LineData[]) => void;
  t: (key: string) => string;
}

const LinesEditor: React.FC<LinesEditorProps> = ({ lines, products, onChange, t }) => {
  const addLine = useCallback(() => {
    onChange([
      ...lines,
      {
        id: `line-${Date.now()}`,
        description: '',
        quantity: 1,
        unit_price: 0,
        tax_rate: 20,
      },
    ]);
  }, [lines, onChange]);

  const updateLine = useCallback((index: number, field: keyof LineData, value: any) => {
    const updated = [...lines];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  }, [lines, onChange]);

  const applyProduct = useCallback((index: number, product: Product) => {
    const updated = [...lines];
    updated[index] = {
      ...updated[index],
      description: product.name,
      unit_price: product.sale_price || 0,
    };
    onChange(updated);
  }, [lines, onChange]);

  const removeLine = useCallback((index: number) => {
    onChange(lines.filter((_, i) => i !== index));
  }, [lines, onChange]);

  return (
    <div className="azals-ws-lines">
      <table className="azals-ws-lines__table">
        <thead>
          <tr>
            <th className="azals-ws-lines__th-desc">{t('worksheet.description')}</th>
            <th className="azals-ws-lines__th-qty">{t('worksheet.qty')}</th>
            <th className="azals-ws-lines__th-price">{t('worksheet.unitPrice')}</th>
            <th className="azals-ws-lines__th-tax">{t('worksheet.tax')}</th>
            <th className="azals-ws-lines__th-total">{t('worksheet.total')}</th>
            <th className="azals-ws-lines__th-action"></th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line, index) => {
            const lineTotal = line.quantity * line.unit_price * (1 + line.tax_rate / 100);
            return (
              <tr key={line.id}>
                <td>
                  <ProductSelectorInline
                    products={products}
                    value={line.description}
                    onSelect={(product) => applyProduct(index, product)}
                    onChange={(value) => updateLine(index, 'description', value)}
                    onProductCreated={(product) => applyProduct(index, product)}
                    placeholder={t('worksheet.descriptionPlaceholder')}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    className="azals-ws-input azals-ws-input--number"
                    value={line.quantity}
                    onChange={(e) => updateLine(index, 'quantity', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="1"
                  />
                </td>
                <td>
                  <input
                    type="number"
                    className="azals-ws-input azals-ws-input--number"
                    value={line.unit_price}
                    onChange={(e) => updateLine(index, 'unit_price', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                  />
                </td>
                <td>
                  <select
                    className="azals-ws-select"
                    value={line.tax_rate}
                    onChange={(e) => updateLine(index, 'tax_rate', parseFloat(e.target.value))}
                  >
                    <option value="0">0%</option>
                    <option value="5.5">5,5%</option>
                    <option value="10">10%</option>
                    <option value="20">20%</option>
                  </select>
                </td>
                <td className="azals-ws-lines__total">
                  {lineTotal.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
                </td>
                <td>
                  <button
                    type="button"
                    className="azals-ws-btn-icon"
                    onClick={() => removeLine(index)}
                    aria-label={t('worksheet.removeLine')}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <button
        type="button"
        className="azals-ws-add-line"
        onClick={addLine}
      >
        <Plus size={16} />
        {t('worksheet.addLine')}
      </button>
    </div>
  );
};

// ============================================================
// COMPOSANT PRINCIPAL — FEUILLE DE TRAVAIL
// ============================================================

interface WorksheetProps {
  defaultType?: string;
}

export const Worksheet: React.FC<WorksheetProps> = ({ defaultType }) => {
  const { t } = useTranslation();
  const { data: clients = [], isLoading: loadingClients, error: clientsError, refetch: refetchClients } = useClients();
  const { data: products = [], isLoading: loadingProducts, error: productsError, refetch: refetchProducts } = useProducts();
  const saveDocument = useSaveDocument();

  // Mapper defaultType vers DocumentType
  const getInitialType = (): DocumentType => {
    if (defaultType) {
      const mapping: Record<string, DocumentType> = {
        'DEVIS': 'QUOTE',
        'FACTURE': 'INVOICE',
        'COMMANDE': 'ORDER',
      };
      return mapping[defaultType] || 'QUOTE';
    }
    return 'QUOTE';
  };

  // État du document en cours
  const [docType, setDocType] = useState<DocumentType>(getInitialType());
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [lines, setLines] = useState<LineData[]>([]);
  const [notes, setNotes] = useState('');
  const [saved, setSaved] = useState(false);

  // Calculs totaux
  const totals = useMemo(() => {
    const subtotal = lines.reduce((sum, l) => sum + l.quantity * l.unit_price, 0);
    const tax = lines.reduce((sum, l) => sum + l.quantity * l.unit_price * l.tax_rate / 100, 0);
    return { subtotal, tax, total: subtotal + tax };
  }, [lines]);

  // Sélection client = injection automatique complète
  const handleClientSelect = useCallback((client: Client) => {
    setSelectedClient(client);
    // Règle AZALSCORE : tous les champs sont injectés sans filtrage
  }, []);

  // Enregistrement
  const handleSave = useCallback(async () => {
    if (!selectedClient || lines.length === 0) return;

    try {
      await saveDocument.mutateAsync({
        type: docType,
        client_id: selectedClient.id,
        client: selectedClient,
        date: new Date().toISOString().split('T')[0],
        lines,
        notes: notes || undefined,
      });

      // Reset pour nouveau document
      setSaved(true);
      setTimeout(() => {
        setSelectedClient(null);
        setLines([]);
        setNotes('');
        setSaved(false);
      }, 2000);
    } catch (error) {
      console.error('Save error:', error);
    }
  }, [docType, selectedClient, lines, notes, saveDocument]);

  // Changement type = état interne uniquement, pas de navigation
  const handleTypeChange = useCallback((type: DocumentType) => {
    setDocType(type);
  }, []);

  if (loadingClients || loadingProducts) {
    return (
      <div className="azals-ws-loading">
        <Loader2 className="azals-ws-loading__spinner" size={32} />
        <span>{t('worksheet.loading')}</span>
      </div>
    );
  }

  if (clientsError || productsError) {
    return (
      <ErrorState
        message={
          clientsError instanceof Error
            ? clientsError.message
            : productsError instanceof Error
            ? productsError.message
            : undefined
        }
        onRetry={() => { refetchClients(); refetchProducts(); }}
      />
    );
  }

  return (
    <div className="azals-worksheet">
      {/* En-tête simple */}
      <header className="azals-ws-header">
        <div className="azals-ws-type">
          {(['QUOTE', 'INVOICE', 'ORDER', 'INTERVENTION'] as DocumentType[]).map(type => (
            <button
              key={type}
              className={`azals-ws-type__btn ${docType === type ? 'azals-ws-type__btn--active' : ''}`}
              onClick={() => handleTypeChange(type)}
            >
              {t(`worksheet.type.${type.toLowerCase()}`)}
            </button>
          ))}
        </div>
        <div className="azals-ws-date">
          {new Date().toLocaleDateString('fr-FR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
          })}
        </div>
      </header>

      {/* Zone client */}
      <section className="azals-ws-section">
        <ClientSelector
          clients={clients}
          selectedClient={selectedClient}
          onSelect={handleClientSelect}
          onClientCreated={handleClientSelect}
          t={t}
        />

        {selectedClient && (
          <div className="azals-ws-client-details">
            {selectedClient.address_line1 && (
              <span>{selectedClient.address_line1}</span>
            )}
            {selectedClient.postal_code && selectedClient.city && (
              <span>{selectedClient.postal_code} {selectedClient.city}</span>
            )}
            {selectedClient.email && (
              <span>{selectedClient.email}</span>
            )}
            {selectedClient.tax_id && (
              <span>{t('worksheet.taxId')}: {selectedClient.tax_id}</span>
            )}
          </div>
        )}
      </section>

      {/* Zone lignes */}
      <section className="azals-ws-section azals-ws-section--lines">
        <LinesEditor lines={lines} products={products} onChange={setLines} t={t} />
      </section>

      {/* Zone notes (optionnel) */}
      <section className="azals-ws-section azals-ws-section--notes">
        <textarea
          className="azals-ws-notes"
          placeholder={t('worksheet.notesPlaceholder')}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
        />
      </section>

      {/* Zone totaux */}
      <section className="azals-ws-totals">
        <div className="azals-ws-totals__row">
          <span>{t('worksheet.subtotal')}</span>
          <span>{totals.subtotal.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</span>
        </div>
        <div className="azals-ws-totals__row">
          <span>{t('worksheet.taxTotal')}</span>
          <span>{totals.tax.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</span>
        </div>
        <div className="azals-ws-totals__row azals-ws-totals__row--main">
          <span>{t('worksheet.total')}</span>
          <span>{totals.total.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</span>
        </div>
      </section>

      {/* Action principale */}
      <footer className="azals-ws-footer">
        <button
          className={`azals-ws-save ${saved ? 'azals-ws-save--success' : ''}`}
          onClick={handleSave}
          disabled={!selectedClient || lines.length === 0 || saveDocument.isPending}
        >
          {saveDocument.isPending ? (
            <Loader2 className="azals-ws-save__spinner" size={20} />
          ) : saved ? (
            <Check size={20} />
          ) : null}
          <span>
            {saved
              ? t('worksheet.saved')
              : t(`worksheet.save.${docType.toLowerCase()}`)}
          </span>
        </button>
      </footer>
    </div>
  );
};

export default Worksheet;
