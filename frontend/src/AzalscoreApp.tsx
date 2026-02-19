/**
 * AZALSCORE - Application Unifiée Simplifiée
 * ===========================================
 *
 * Interface ultra-simple:
 * - Logo + Menu déroulant + Déconnexion
 * - Barre d'actions contextuelles (créer client, article, etc.)
 * - Vue unique en dessous
 *
 * Menu: Devis | Facture | Commande | Intervention | CRM | Stock | RH | Compta | Trésorerie | Cockpit
 */

import React, { Suspense, lazy, useState, useEffect, useCallback, useRef } from 'react';
import { QueryClientProvider, useMutation, useQueryClient } from '@tanstack/react-query';
import { LogOut, Loader2, ChevronDown, Plus, Users, Package, Truck, Wrench, X, LayoutGrid, User, Search, FileText, Star, Clock, Database, AlertTriangle } from 'lucide-react';
import { BrowserRouter } from 'react-router-dom';
import { tokenManager, api } from '@core/api-client';
import { useAuthStore } from '@core/auth';
import { COLORS } from '@core/design-tokens';
import { queryClient } from '@core/query-client';
import type { SearchClientResult, SearchDocumentResult, SearchProductResult, ApiMutationError } from '@/types';
import { useTranslation } from './modules/i18n';
import { isDemoMode, setDemoMode } from './utils/demoMode';
import { setInterfaceMode } from './utils/interfaceMode';
import { getRecents, addRecent, getFavorites, toggleFavorite, isFavorite, type RecentItem, type FavoriteItem } from './utils/recentsFavorites';
import './styles/azalscore.css';

// ============================================================
// GLOBAL SEARCH COMPONENT
// ============================================================

interface SearchResult {
  id: string;
  type: 'client' | 'document' | 'article';
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
}

interface GlobalSearchProps {
  onNavigate: (type: string, id: string) => void;
  isOpen: boolean;
  onClose: () => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

const getIconForType = (type: string): React.ReactNode => {
  switch (type) {
    case 'client': return <Users size={16} />;
    case 'document': return <FileText size={16} />;
    case 'article': return <Package size={16} />;
    default: return <FileText size={16} />;
  }
};

const GlobalSearch: React.FC<GlobalSearchProps> = ({ onNavigate, isOpen, onClose, inputRef }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recents, setRecents] = useState<RecentItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);

  // Load recents and favorites on open
  useEffect(() => {
    if (isOpen) {
      setRecents(getRecents());
      setFavorites(getFavorites());
    }
  }, [isOpen]);

  // Search when query changes
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const searchTimeout = setTimeout(async () => {
      setIsSearching(true);
      try {
        const encodedQuery = encodeURIComponent(query);

        // Lancer les 3 recherches en parallèle (Promise.all)
        const [clientsRes, docsRes, productsRes] = await Promise.all([
          api.get<{ items: SearchClientResult[] }>(`/partners/clients?search=${encodedQuery}&page_size=5`).catch(() => ({ items: [] as SearchClientResult[] })),
          api.get<{ items: SearchDocumentResult[] }>(`/commercial/documents?search=${encodedQuery}&page_size=5`).catch(() => ({ items: [] as SearchDocumentResult[] })),
          api.get<{ items: SearchProductResult[] }>(`/inventory/products?search=${encodedQuery}&page_size=5`).catch(() => ({ items: [] as SearchProductResult[] })),
        ]);

        const searchResults: SearchResult[] = [];

        // Process clients
        const clients = (clientsRes as { items?: SearchClientResult[] })?.items || [];
        clients.forEach((c) => {
          searchResults.push({
            id: c.id,
            type: 'client',
            title: c.name,
            subtitle: c.email || c.phone || c.code,
            icon: <Users size={16} />,
          });
        });

        // Process documents
        const docs = (docsRes as { items?: SearchDocumentResult[] })?.items || [];
        docs.forEach((d) => {
          searchResults.push({
            id: d.id,
            type: 'document',
            title: `${d.document_type || 'Document'} ${d.number || d.id.slice(0, 8)}`,
            subtitle: d.customer_name || (d.total_ttc?.toFixed(2) + ' €'),
            icon: <FileText size={16} />,
          });
        });

        // Process products
        const products = (productsRes as { items?: SearchProductResult[] })?.items || [];
        products.forEach((p) => {
          searchResults.push({
            id: p.id,
            type: 'article',
            title: p.name,
            subtitle: p.sku || p.code,
            icon: <Package size={16} />,
          });
        });

        setResults(searchResults);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [query]);

  // Get all displayable items (favorites + recents when no query, results when searching)
  const displayItems = query.length >= 2 ? results : [];
  const totalItems = displayItems.length + (query.length < 2 ? favorites.length + recents.length : 0);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, totalItems - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      // Handle selection based on current view
      if (query.length >= 2 && results[selectedIndex]) {
        const result = results[selectedIndex];
        handleSelect(result.type, result.id, result.title, result.subtitle);
      } else if (query.length < 2) {
        // Navigate favorites then recents
        if (selectedIndex < favorites.length) {
          const fav = favorites[selectedIndex];
          handleSelect(fav.type, fav.id, fav.title, fav.subtitle);
        } else {
          const recentIdx = selectedIndex - favorites.length;
          if (recents[recentIdx]) {
            const rec = recents[recentIdx];
            handleSelect(rec.type, rec.id, rec.title, rec.subtitle);
          }
        }
      }
    } else if (e.key === 'Escape') {
      setQuery('');
      onClose();
    }
  };

  const handleSelect = (type: string, id: string, title: string, subtitle?: string) => {
    // Add to recents
    addRecent({ id, type: type as 'client' | 'document' | 'article', title, subtitle });
    onNavigate(type, id);
    setQuery('');
    onClose();
  };

  const handleToggleFavorite = (e: React.MouseEvent, item: { id: string; type: string; title: string; subtitle?: string }) => {
    e.stopPropagation();
    toggleFavorite({ id: item.id, type: item.type as 'client' | 'document' | 'article', title: item.title, subtitle: item.subtitle });
    setFavorites(getFavorites());
  };

  if (!isOpen) return null;

  return (
    <div className="azals-global-search">
      <div className="azals-global-search__input-wrapper">
        <Search size={18} className="azals-global-search__icon" />
        <input
          ref={inputRef}
          type="text"
          className="azals-global-search__input"
          placeholder="Rechercher clients, documents, articles... (Ctrl+R)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        {isSearching && <Loader2 size={16} className="azals-global-search__spinner spin" />}
        {query && (
          <button className="azals-global-search__clear" onClick={() => { setQuery(''); onClose(); }}>
            <X size={16} />
          </button>
        )}
      </div>

      <div className="azals-global-search__results">
        {/* Show favorites when no query */}
        {query.length < 2 && favorites.length > 0 && (
          <div className="azals-global-search__section">
            <div className="azals-global-search__section-header">
              <Star size={14} />
              <span>Favoris</span>
            </div>
            {favorites.map((fav, index) => (
              <button
                key={`fav-${fav.type}-${fav.id}`}
                className={`azals-global-search__result ${index === selectedIndex ? 'azals-global-search__result--selected' : ''}`}
                onClick={() => handleSelect(fav.type, fav.id, fav.title, fav.subtitle)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <span className="azals-global-search__result-icon">{getIconForType(fav.type)}</span>
                <div className="azals-global-search__result-content">
                  <span className="azals-global-search__result-title">{fav.title}</span>
                  {fav.subtitle && <span className="azals-global-search__result-subtitle">{fav.subtitle}</span>}
                </div>
                <button
                  className="azals-global-search__star azals-global-search__star--active"
                  onClick={(e) => handleToggleFavorite(e, fav)}
                >
                  <Star size={14} fill="currentColor" />
                </button>
              </button>
            ))}
          </div>
        )}

        {/* Show recents when no query */}
        {query.length < 2 && recents.length > 0 && (
          <div className="azals-global-search__section">
            <div className="azals-global-search__section-header">
              <Clock size={14} />
              <span>Récents</span>
            </div>
            {recents.map((rec, index) => {
              const adjustedIndex = favorites.length + index;
              return (
                <button
                  key={`rec-${rec.type}-${rec.id}`}
                  className={`azals-global-search__result ${adjustedIndex === selectedIndex ? 'azals-global-search__result--selected' : ''}`}
                  onClick={() => handleSelect(rec.type, rec.id, rec.title, rec.subtitle)}
                  onMouseEnter={() => setSelectedIndex(adjustedIndex)}
                >
                  <span className="azals-global-search__result-icon">{getIconForType(rec.type)}</span>
                  <div className="azals-global-search__result-content">
                    <span className="azals-global-search__result-title">{rec.title}</span>
                    {rec.subtitle && <span className="azals-global-search__result-subtitle">{rec.subtitle}</span>}
                  </div>
                  <button
                    className={`azals-global-search__star ${isFavorite(rec.id, rec.type) ? 'azals-global-search__star--active' : ''}`}
                    onClick={(e) => handleToggleFavorite(e, rec)}
                  >
                    <Star size={14} fill={isFavorite(rec.id, rec.type) ? 'currentColor' : 'none'} />
                  </button>
                </button>
              );
            })}
          </div>
        )}

        {/* Show search results */}
        {query.length >= 2 && results.length > 0 && (
          <>
            {results.map((result, index) => (
              <button
                key={`${result.type}-${result.id}`}
                className={`azals-global-search__result ${index === selectedIndex ? 'azals-global-search__result--selected' : ''}`}
                onClick={() => handleSelect(result.type, result.id, result.title, result.subtitle)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <span className="azals-global-search__result-icon">{result.icon}</span>
                <div className="azals-global-search__result-content">
                  <span className="azals-global-search__result-title">{result.title}</span>
                  {result.subtitle && <span className="azals-global-search__result-subtitle">{result.subtitle}</span>}
                </div>
                <button
                  className={`azals-global-search__star ${isFavorite(result.id, result.type) ? 'azals-global-search__star--active' : ''}`}
                  onClick={(e) => handleToggleFavorite(e, result)}
                >
                  <Star size={14} fill={isFavorite(result.id, result.type) ? 'currentColor' : 'none'} />
                </button>
              </button>
            ))}
          </>
        )}

        {/* Empty states */}
        {query.length < 2 && favorites.length === 0 && recents.length === 0 && (
          <div className="azals-global-search__empty">
            Tapez pour rechercher ou consultez des éléments pour les voir ici
          </div>
        )}

        {query.length >= 2 && results.length === 0 && !isSearching && (
          <div className="azals-global-search__empty">
            Aucun résultat pour "{query}"
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// LAZY LOADING DES MODULES
// ============================================================

const WorksheetView = lazy(() => import('./modules/worksheet'));
const CockpitView = lazy(() => import('./modules/cockpit'));
const PartnersModule = lazy(() => import('./modules/partners'));
const InterventionsModule = lazy(() => import('./modules/interventions'));
const InvoicingModule = lazy(() => import('./modules/invoicing'));
const AccountingModule = lazy(() => import('./modules/accounting'));
const TreasuryModule = lazy(() => import('./modules/treasury'));
const InventoryModule = lazy(() => import('./modules/inventory'));
const HRModule = lazy(() => import('./modules/hr'));
const AdminModule = lazy(() => import('./modules/admin'));
const PurchasesModule = lazy(() => import('./modules/purchases'));
const ProjectsModule = lazy(() => import('./modules/projects'));
const VehiculesModule = lazy(() => import('./modules/vehicles'));
const AffairesModule = lazy(() => import('./modules/affaires'));

// ============================================================
// CONFIGURATION DU MENU
// ============================================================
// Note: QueryClient importé depuis @core/query-client (singleton)

type ViewKey =
  // Saisie
  | 'saisie'
  // Gestion (workflow documents)
  | 'gestion-devis'
  | 'gestion-commandes'
  | 'gestion-interventions'
  | 'gestion-factures'
  | 'gestion-paiements'
  // Affaires
  | 'affaires'
  // Autres modules
  | 'crm'
  | 'stock'
  | 'achats'
  | 'projets'
  | 'rh'
  | 'vehicules'
  | 'compta'
  | 'tresorerie'
  | 'cockpit'
  | 'admin';

interface MenuItem {
  key: ViewKey;
  label: string;
  group?: string;
}

const MENU_ITEMS: MenuItem[] = [
  // Saisie - Point d'entrée rapide
  { key: 'saisie', label: 'Nouvelle saisie', group: 'Saisie' },

  // Gestion - Workflow et transformations
  { key: 'gestion-devis', label: 'Devis', group: 'Gestion' },
  { key: 'gestion-commandes', label: 'Commandes', group: 'Gestion' },
  { key: 'gestion-interventions', label: 'Interventions', group: 'Gestion' },
  { key: 'gestion-factures', label: 'Factures', group: 'Gestion' },
  { key: 'gestion-paiements', label: 'Paiements', group: 'Gestion' },

  // Affaires - Suivi projets/chantiers
  { key: 'affaires', label: 'Suivi Affaires', group: 'Affaires' },

  // Autres modules métier
  { key: 'crm', label: 'CRM / Clients', group: 'Modules' },
  { key: 'stock', label: 'Stock', group: 'Modules' },
  { key: 'achats', label: 'Achats', group: 'Modules' },
  { key: 'projets', label: 'Projets', group: 'Modules' },
  { key: 'rh', label: 'RH', group: 'Modules' },

  // Finance / Reporting
  { key: 'compta', label: 'Comptabilité', group: 'Finance' },
  { key: 'tresorerie', label: 'Trésorerie', group: 'Finance' },

  // Direction
  { key: 'cockpit', label: 'Cockpit Dirigeant', group: 'Direction' },

  // Système
  { key: 'admin', label: 'Administration', group: 'Système' },
];

// ============================================================
// VUE PAR DÉFAUT SELON LE RÔLE
// ============================================================

/**
 * Détermine la vue par défaut en fonction du rôle de l'utilisateur.
 * Priorité: premier rôle trouvé dans la liste des rôles de l'utilisateur.
 */
const ROLE_DEFAULT_VIEWS: Record<string, ViewKey> = {
  // Rôles direction/management → Cockpit dirigeant
  'dirigeant': 'cockpit',
  'directeur': 'cockpit',
  'gerant': 'cockpit',
  'manager': 'cockpit',
  'executive': 'cockpit',

  // Rôles administration → Administration
  'administrateur': 'admin',
  'admin': 'admin',
  'superadmin': 'admin',
  'root': 'admin',

  // Rôles comptabilité → Comptabilité
  'comptable': 'compta',
  'accountant': 'compta',

  // Rôles trésorerie → Trésorerie
  'tresorier': 'tresorerie',
  'treasurer': 'tresorerie',

  // Rôles RH → RH
  'rh': 'rh',
  'hr': 'rh',

  // Rôles commerciaux → CRM
  'commercial': 'crm',
  'sales': 'crm',
  'vendeur': 'crm',

  // Rôles logistique/stock → Stock
  'logisticien': 'stock',
  'magasinier': 'stock',
  'warehouse': 'stock',

  // Rôles achats → Achats
  'acheteur': 'achats',
  'buyer': 'achats',

  // Rôles techniciens/interventions → Interventions
  'technicien': 'gestion-interventions',
  'technician': 'gestion-interventions',
  'intervenant': 'gestion-interventions',

  // Rôles projets → Projets
  'chef_projet': 'projets',
  'project_manager': 'projets',

  // Rôle par défaut (utilisateur standard) → Saisie
  'user': 'saisie',
  'utilisateur': 'saisie',
};

/**
 * Liste des vues disponibles pour la configuration admin.
 * Utilisée pour le sélecteur de vue par défaut.
 */
export const AVAILABLE_VIEWS: { key: ViewKey; label: string }[] = [
  { key: 'saisie', label: 'Nouvelle saisie' },
  { key: 'cockpit', label: 'Cockpit (Tableau de bord)' },
  { key: 'admin', label: 'Administration' },
  { key: 'gestion-devis', label: 'Gestion - Devis' },
  { key: 'gestion-commandes', label: 'Gestion - Commandes' },
  { key: 'gestion-interventions', label: 'Gestion - Interventions' },
  { key: 'gestion-factures', label: 'Gestion - Factures' },
  { key: 'gestion-paiements', label: 'Gestion - Paiements' },
  { key: 'affaires', label: 'Affaires' },
  { key: 'crm', label: 'CRM' },
  { key: 'stock', label: 'Stock' },
  { key: 'achats', label: 'Achats' },
  { key: 'projets', label: 'Projets' },
  { key: 'rh', label: 'Ressources Humaines' },
  { key: 'vehicules', label: 'Véhicules' },
  { key: 'compta', label: 'Comptabilité' },
  { key: 'tresorerie', label: 'Trésorerie' },
];

/**
 * Retourne la vue par défaut pour un utilisateur.
 * Priorité: 1) default_view configuré par admin, 2) rôle, 3) 'saisie'
 */
const getDefaultViewForUser = (defaultView?: string, roles?: string[]): ViewKey => {
  // 1. Priorité: vue configurée par l'administrateur
  if (defaultView && AVAILABLE_VIEWS.some(v => v.key === defaultView)) {
    return defaultView as ViewKey;
  }

  // 2. Fallback: vue basée sur le rôle
  if (roles && roles.length > 0) {
    const normalizedRoles = roles.map(r => r.toLowerCase().trim());
    for (const role of normalizedRoles) {
      if (ROLE_DEFAULT_VIEWS[role]) {
        return ROLE_DEFAULT_VIEWS[role];
      }
    }
  }

  // 3. Défaut: saisie
  return 'saisie';
};

// ============================================================
// CONTEXT ACTIONS - Configuration par vue
// ============================================================

type ContextAction = 'client' | 'supplier' | 'article' | 'intervenant';

const VIEW_CONTEXT_ACTIONS: Record<ViewKey, ContextAction[]> = {
  'saisie': ['client', 'article'],
  'gestion-devis': ['client', 'article'],
  'gestion-commandes': ['client', 'article'],
  'gestion-interventions': ['client', 'intervenant'],
  'gestion-factures': ['client', 'article'],
  'gestion-paiements': ['client'],
  'affaires': ['client'],
  'crm': ['client'],
  'stock': ['article'],
  'achats': ['supplier', 'article'],
  'projets': ['client'],
  'rh': ['intervenant'],
  'vehicules': [],
  'compta': [],
  'tresorerie': [],
  'cockpit': [],
  'admin': [],
};

const CONTEXT_ACTION_CONFIG: Record<ContextAction, { label: string; icon: React.ReactNode; color: string }> = {
  client: { label: 'Client', icon: <Users size={16} />, color: COLORS.primary },
  supplier: { label: 'Fournisseur', icon: <Truck size={16} />, color: '#8b5cf6' },
  article: { label: 'Article', icon: <Package size={16} />, color: '#10b981' },
  intervenant: { label: 'Intervenant', icon: <Wrench size={16} />, color: '#f59e0b' },
};

// ============================================================
// QUICK CREATE MODAL
// ============================================================

interface QuickCreateModalProps {
  type: ContextAction;
  onClose: () => void;
  onSuccess: () => void;
}

const QuickCreateModal: React.FC<QuickCreateModalProps> = ({ type, onClose, onSuccess }) => {
  const { t: _t } = useTranslation();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const getEndpoint = () => {
    switch (type) {
      case 'client': return '/commercial/customers';
      case 'supplier': return '/commercial/suppliers';
      case 'article': return '/inventory/products';
      case 'intervenant': return '/hr/employees';
    }
  };

  const getFields = (): { key: string; label: string; required?: boolean; type?: string }[] => {
    switch (type) {
      case 'client':
      case 'supplier':
        return [
          { key: 'name', label: 'Nom', required: true },
          { key: 'email', label: 'Email', type: 'email' },
          { key: 'phone', label: 'Téléphone' },
          { key: 'address_line1', label: 'Adresse' },
          { key: 'city', label: 'Ville' },
          { key: 'postal_code', label: 'Code postal' },
        ];
      case 'article':
        return [
          { key: 'code', label: 'Référence', required: true },
          { key: 'name', label: 'Désignation', required: true },
          { key: 'sale_price', label: 'Prix de vente', type: 'number' },
          { key: 'purchase_price', label: 'Prix d\'achat', type: 'number' },
        ];
      case 'intervenant':
        return [
          { key: 'first_name', label: 'Prénom', required: true },
          { key: 'last_name', label: 'Nom', required: true },
          { key: 'email', label: 'Email', type: 'email' },
          { key: 'phone', label: 'Téléphone' },
          { key: 'position', label: 'Poste' },
        ];
    }
  };

  const createMutation = useMutation({
    mutationFn: async (data: Record<string, string>) => {
      // Préparer les données selon le type
      const payload: Record<string, string | number> = { ...data };
      if (type === 'article') {
        if (data.sale_price) payload.sale_price = parseFloat(data.sale_price);
        if (data.purchase_price) payload.purchase_price = parseFloat(data.purchase_price);
      }
      return api.post(getEndpoint(), payload);
    },
    onSuccess: () => {
      // Invalider les caches pertinents
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      queryClient.invalidateQueries({ queryKey: ['partners'] });
      onSuccess();
      onClose();
    },
    onError: (err: ApiMutationError) => {
      setError(err.message || 'Erreur lors de la création');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    createMutation.mutate(formData);
  };

  const config = CONTEXT_ACTION_CONFIG[type];
  const fields = getFields();

  return (
    <div className="azals-modal-overlay" onClick={onClose}>
      <div className="azals-modal" onClick={e => e.stopPropagation()}>
        <div className="azals-modal__header" style={{ borderLeftColor: config.color }}>
          <div className="azals-modal__title">
            {config.icon}
            <span>Nouveau {config.label}</span>
          </div>
          <button className="azals-modal__close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="azals-modal__form">
          {error && <div className="azals-modal__error">{error}</div>}

          {fields.map(field => (
            <div key={field.key} className="azals-modal__field">
              <label>
                {field.label}
                {field.required && <span className="azals-modal__required">*</span>}
              </label>
              <input
                type={field.type || 'text'}
                value={formData[field.key] || ''}
                onChange={e => setFormData({ ...formData, [field.key]: e.target.value })}
                required={field.required}
                autoFocus={field.key === fields[0].key}
              />
            </div>
          ))}

          <div className="azals-modal__actions">
            <button type="button" className="azals-modal__btn azals-modal__btn--cancel" onClick={onClose}>
              Annuler
            </button>
            <button
              type="submit"
              className="azals-modal__btn azals-modal__btn--submit"
              disabled={createMutation.isPending}
              style={{ backgroundColor: config.color }}
            >
              {createMutation.isPending ? <Loader2 className="spin" size={16} /> : <Plus size={16} />}
              <span>Créer</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ============================================================
// CONTEXT ACTION BAR
// ============================================================

interface ContextActionBarProps {
  viewKey: ViewKey;
}

const ContextActionBar: React.FC<ContextActionBarProps> = ({ viewKey }) => {
  const [activeModal, setActiveModal] = useState<ContextAction | null>(null);
  const [showSuccess, setShowSuccess] = useState<ContextAction | null>(null);

  const actions = VIEW_CONTEXT_ACTIONS[viewKey] || [];

  const handleSuccess = () => {
    if (activeModal) {
      setShowSuccess(activeModal);
      setTimeout(() => setShowSuccess(null), 2000);
    }
  };

  if (actions.length === 0) return null;

  return (
    <>
      <div className="azals-context-bar">
        <span className="azals-context-bar__label">Actions rapides :</span>
        {actions.map(action => {
          const config = CONTEXT_ACTION_CONFIG[action];
          const isSuccess = showSuccess === action;
          return (
            <button
              key={action}
              className={`azals-context-bar__btn ${isSuccess ? 'azals-context-bar__btn--success' : ''}`}
              onClick={() => setActiveModal(action)}
              style={{ '--action-color': config.color } as React.CSSProperties}
            >
              {config.icon}
              <span>{config.label}</span>
              <Plus size={14} />
            </button>
          );
        })}
      </div>

      {activeModal && (
        <QuickCreateModal
          type={activeModal}
          onClose={() => setActiveModal(null)}
          onSuccess={handleSuccess}
        />
      )}
    </>
  );
};

// ============================================================
// LOGIN
// ============================================================

const Login: React.FC<{ onLogin: () => void }> = ({ onLogin }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': 'masith',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) throw new Error('Identifiants invalides');

      const data = await response.json();
      tokenManager.setTokens(data.access_token, data.refresh_token);
      sessionStorage.setItem('azals_tenant_id', 'masith');
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="azals-login">
      <div className="azals-login__card">
        <h1 className="azals-login__title">AZALSCORE</h1>
        <p className="azals-login__subtitle">Connexion</p>
        <form onSubmit={handleSubmit} className="azals-login__form">
          {error && <div className="azals-login__error">{error}</div>}
          <div className="azals-login__field">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
              autoFocus
            />
          </div>
          <div className="azals-login__field">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mot de passe"
              required
            />
          </div>
          <button type="submit" className="azals-login__submit" disabled={loading}>
            {loading ? t('common.loading') : 'Connexion'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ============================================================
// TOP BAR SIMPLE
// ============================================================

interface TopBarProps {
  currentView: ViewKey;
  onViewChange: (key: ViewKey) => void;
  onLogout: () => void;
  onOpenSearch: () => void;
  onOpenCreate: () => void;
  searchOpen: boolean;
  onCloseSearch: () => void;
  searchInputRef: React.RefObject<HTMLInputElement>;
}

const TopBar: React.FC<TopBarProps> = ({
  currentView, onViewChange, onLogout,
  onOpenSearch, onOpenCreate, searchOpen, onCloseSearch, searchInputRef
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const currentItem = MENU_ITEMS.find(m => m.key === currentView);

  // Handle search navigation
  const handleSearchNavigate = (type: string, id: string) => {
    // Navigate based on type and dispatch detail view event
    if (type === 'client') {
      onViewChange('crm');
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'crm', params: { id } }
        }));
      }, 100);
    } else if (type === 'document') {
      onViewChange('gestion-factures');
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'factures', params: { id } }
        }));
      }, 100);
    } else if (type === 'article') {
      onViewChange('stock');
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'inventory', params: { id } }
        }));
      }, 100);
    }
  };

  // Grouper les items
  const groups = MENU_ITEMS.reduce((acc, item) => {
    const group = item.group || 'Autre';
    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {} as Record<string, MenuItem[]>);

  return (
    <header className={`azals-header-simple ${isDemoMode() ? 'azals-header-simple--demo' : ''}`}>
      <div className="azals-header-simple__logo">AZALSCORE</div>

      <div className="azals-header-simple__menu">
        <button
          className="azals-header-simple__selector"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span>{currentItem?.label || 'Sélectionner'}</span>
          <ChevronDown size={18} className={isOpen ? 'rotate' : ''} />
        </button>

        {isOpen && (
          <div className="azals-header-simple__dropdown">
            {Object.entries(groups).map(([groupName, items]) => (
              <div key={groupName} className="azals-header-simple__group">
                <div className="azals-header-simple__group-label">{groupName}</div>
                {items.map((item) => (
                  <button
                    key={item.key}
                    className={`azals-header-simple__item ${currentView === item.key ? 'azals-header-simple__item--active' : ''}`}
                    onClick={() => {
                      onViewChange(item.key);
                      setIsOpen(false);
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Global Search */}
      <div className="azals-header-simple__search-container">
        {searchOpen ? (
          <GlobalSearch
            onNavigate={handleSearchNavigate}
            isOpen={searchOpen}
            onClose={onCloseSearch}
            inputRef={searchInputRef}
          />
        ) : (
          <button
            className="azals-header-simple__search-btn"
            onClick={onOpenSearch}
            title="Rechercher (Ctrl+R)"
          >
            <Search size={18} />
            <span className="azals-header-simple__search-hint">Ctrl+R</span>
          </button>
        )}
      </div>

      {/* Quick Create Button */}
      <button
        className="azals-header-simple__create-btn"
        onClick={onOpenCreate}
        title="Nouveau (Ctrl+A)"
      >
        <Plus size={18} />
        <span className="azals-header-simple__create-hint">Ctrl+A</span>
      </button>

      {/* User Menu */}
      <div className="azals-header-simple__user-menu">
        <button
          className="azals-header-simple__user-btn"
          onClick={() => setUserMenuOpen(!userMenuOpen)}
        >
          <User size={20} />
          <ChevronDown size={14} className={userMenuOpen ? 'rotate' : ''} />
        </button>

        {userMenuOpen && (
          <div className="azals-header-simple__user-dropdown">
            <button
              className="azals-header-simple__user-item"
              onClick={() => { setInterfaceMode('erp'); }}
            >
              <LayoutGrid size={16} />
              <span>Mode ERP complet</span>
            </button>
            <button
              className={`azals-header-simple__user-item ${isDemoMode() ? 'azals-header-simple__user-item--active' : ''}`}
              onClick={() => { setDemoMode(!isDemoMode()); }}
            >
              <Database size={16} />
              <span>{isDemoMode() ? 'Désactiver démo' : 'Activer démo'}</span>
            </button>
            <hr className="azals-header-simple__user-divider" />
            <button
              className="azals-header-simple__user-item azals-header-simple__user-item--danger"
              onClick={onLogout}
            >
              <LogOut size={16} />
              <span>Déconnexion</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

// ============================================================
// VIEW RENDERER
// ============================================================

const ViewRenderer: React.FC<{ viewKey: ViewKey }> = ({ viewKey }) => {
  const LoadingFallback = (
    <div className="azals-loading">
      <Loader2 className="azals-loading__spinner" size={32} />
      <span>Chargement...</span>
    </div>
  );

  const renderView = () => {
    switch (viewKey) {
      // Saisie - Point d'entrée rapide (worksheet)
      case 'saisie':
        return <WorksheetView />;

      // Gestion - Workflow documents (module invoicing avec filtres)
      case 'gestion-devis':
      case 'gestion-commandes':
      case 'gestion-factures':
      case 'gestion-paiements':
        return <InvoicingModule />;
      case 'gestion-interventions':
        return <InterventionsModule />;

      // Affaires - Suivi projets/chantiers
      case 'affaires':
        return <AffairesModule />;

      // Modules métier
      case 'crm':
        return <PartnersModule />;
      case 'stock':
        return <InventoryModule />;
      case 'achats':
        return <PurchasesModule />;
      case 'projets':
        return <ProjectsModule />;
      case 'rh':
        return <HRModule />;
      case 'vehicules':
        return <VehiculesModule />;

      // Finance / Reporting
      case 'compta':
        return <AccountingModule />;
      case 'tresorerie':
        return <TreasuryModule />;

      // Direction
      case 'cockpit':
        return <CockpitView />;

      // Système
      case 'admin':
        return <AdminModule />;

      default:
        return <WorksheetView />;
    }
  };

  return (
    <Suspense fallback={LoadingFallback}>
      <ContextActionBar viewKey={viewKey} />
      <div className={`azals-view azals-view--${viewKey}`}>
        {renderView()}
      </div>
    </Suspense>
  );
};

// ============================================================
// APP CONTENT
// ============================================================

const AppContent: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  // Récupérer l'utilisateur du store auth pour déterminer la vue par défaut
  const user = useAuthStore((state) => state.user);
  const computedDefaultView = getDefaultViewForUser(user?.default_view, user?.roles);

  const [currentView, setCurrentView] = useState<ViewKey>(computedDefaultView);
  const [searchOpen, setSearchOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Ref pour tracker si la vue initiale a été appliquée
  const initialViewApplied = useRef(false);

  // Appliquer la vue par défaut au premier chargement
  useEffect(() => {
    if (user && !initialViewApplied.current) {
      const userDefaultView = getDefaultViewForUser(user.default_view, user.roles);
      setCurrentView(userDefaultView);
      initialViewApplied.current = true;
    }
  }, [user]);

  // Listen for custom navigation events from child modules
  useEffect(() => {
    const handleNavigate = (e: CustomEvent<{ view: string }>) => {
      const view = e.detail.view as ViewKey;
      if (view) setCurrentView(view);
    };
    window.addEventListener('azals:navigate', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate', handleNavigate as EventListener);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if in input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        // Allow Escape to close search
        if (e.key === 'Escape' && searchOpen) {
          setSearchOpen(false);
        }
        return;
      }

      // Ctrl+R - Open search
      if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 100);
      }

      // Ctrl+A - Open create menu
      if (e.ctrlKey && e.key === 'a') {
        e.preventDefault();
        setCreateModalOpen(true);
      }

      // Escape - Close modals
      if (e.key === 'Escape') {
        setSearchOpen(false);
        setCreateModalOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchOpen]);

  const demoMode = isDemoMode();

  return (
    <div className={`azals-app-simple ${demoMode ? 'azals-app-simple--demo' : ''}`}>
      <TopBar
        currentView={currentView}
        onViewChange={setCurrentView}
        onLogout={onLogout}
        onOpenSearch={() => {
          setSearchOpen(true);
          setTimeout(() => searchInputRef.current?.focus(), 100);
        }}
        onOpenCreate={() => setCreateModalOpen(true)}
        searchOpen={searchOpen}
        onCloseSearch={() => setSearchOpen(false)}
        searchInputRef={searchInputRef}
      />
      {/* Bannière mode démo */}
      {demoMode && (
        <div className="azals-demo-banner">
          <AlertTriangle size={16} className="azals-demo-banner__icon" />
          MODE DEMONSTRATION - Lecture seule - Aucun enregistrement possible
        </div>
      )}
      <main className="azals-main-simple">
        <ViewRenderer viewKey={currentView} />
      </main>

      {/* Quick Create Modal */}
      {createModalOpen && (
        <div className="azals-quick-create-overlay" onClick={() => setCreateModalOpen(false)}>
          <div className="azals-quick-create-modal" onClick={e => e.stopPropagation()}>
            <h3>Créer rapidement</h3>
            <div className="azals-quick-create-options">
              <button onClick={() => { setCreateModalOpen(false); setCurrentView('saisie'); }}>
                <FileText size={20} />
                <span>Nouveau document</span>
              </button>
              <button onClick={() => { setCreateModalOpen(false); setCurrentView('crm'); }}>
                <Users size={20} />
                <span>Nouveau client</span>
              </button>
              <button onClick={() => { setCreateModalOpen(false); setCurrentView('stock'); }}>
                <Package size={20} />
                <span>Nouvel article</span>
              </button>
              <button onClick={() => { setCreateModalOpen(false); setCurrentView('achats'); }}>
                <Truck size={20} />
                <span>Nouveau fournisseur</span>
              </button>
            </div>
            <div className="azals-quick-create-footer">
              <span>Appuyez sur Echap pour fermer</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// MAIN APP
// ============================================================

const AzalscoreApp: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const token = tokenManager.getAccessToken();
    if (token) setIsAuthenticated(true);
    setIsChecking(false);
  }, []);

  const handleLogin = useCallback(() => setIsAuthenticated(true), []);
  const handleLogout = useCallback(() => {
    tokenManager.clearTokens();
    sessionStorage.removeItem('azals_tenant_id');
    setIsAuthenticated(false);
    queryClient.clear();
  }, []);

  if (isChecking) {
    return (
      <div className="azals-app-init">
        <div className="azals-app-init__spinner" />
        <span>AZALSCORE</span>
      </div>
    );
  }

  if (!isAuthenticated) return <Login onLogin={handleLogin} />;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent onLogout={handleLogout} />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default AzalscoreApp;
