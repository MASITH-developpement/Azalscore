/**
 * AZALSCORE - Application Unifiée
 * ================================
 *
 * Un seul point d'entrée pour les deux modes d'interface :
 * - Mode "azalscore" : interface simplifiée avec menu déroulant
 * - Mode "erp" : interface complète avec sidebar
 *
 * Les modules sont les mêmes, seul le layout change.
 */

import React, { Suspense, lazy, useState, useEffect, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { ShieldX } from 'lucide-react';
import { LoadingState } from './ui-engine/components/StateViews';
import { tokenManager, setTenantId } from '@core/api-client';
import { useAuthStore } from '@core/auth';
import LandingPage from './pages/LandingPage';
import { MentionsLegales, Confidentialite, CGV, Contact } from './pages/legal';
import { TrialRegistration } from './pages/trial';
import { useCapabilities, useIsCapabilitiesReady, useCapabilitiesStore } from '@core/capabilities';
import { UnifiedLayout, type ViewKey } from './components/UnifiedLayout';
import './styles/main.css';
import './styles/unified-layout.css';
import './styles/azalscore.css';
import './modules/saisie/saisie.css';

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
const ProductionModule = lazy(() => import('./modules/production'));
const MaintenanceModule = lazy(() => import('./modules/maintenance'));
const QualityModule = lazy(() => import('./modules/qualite'));
const POSModule = lazy(() => import('./modules/pos'));
const EcommerceModule = lazy(() => import('./modules/ecommerce'));
const MarketplaceModule = lazy(() => import('./modules/marketplace'));
const SubscriptionsModule = lazy(() => import('./modules/subscriptions'));
const HelpdeskModule = lazy(() => import('./modules/helpdesk'));
const BIModule = lazy(() => import('./modules/bi'));
const ComplianceModule = lazy(() => import('./modules/compliance'));
const WebModule = lazy(() => import('./modules/web'));
const ProfileModule = lazy(() => import('./modules/profile'));
const SettingsModule = lazy(() => import('./modules/settings'));
const MarceauModule = lazy(() => import('./modules/marceau'));
const SaisieModule = lazy(() => import('./modules/saisie'));

// Import modules
const OdooImport = lazy(() => import('./modules/import').then(m => ({ default: m.OdooImportModule })));
const AxonautImport = lazy(() => import('./modules/import').then(m => ({ default: m.AxonautImportModule })));
const PennylaneImport = lazy(() => import('./modules/import').then(m => ({ default: m.PennylaneImportModule })));
const SageImport = lazy(() => import('./modules/import').then(m => ({ default: m.SageImportModule })));
const ChorusImport = lazy(() => import('./modules/import').then(m => ({ default: m.ChorusImportModule })));

// ============================================================
// VIEW KEY → CAPABILITY MAPPING
// Maps each ViewKey to the capability required to access it.
// Views not listed here (e.g. 'saisie', 'profile', 'settings')
// are accessible to all authenticated users.
// ============================================================

const VIEW_CAPABILITY_MAP: Partial<Record<ViewKey, string>> = {
  'cockpit': 'cockpit.view',
  'gestion-devis': 'invoicing.view',
  'gestion-commandes': 'invoicing.view',
  'gestion-factures': 'invoicing.view',
  'gestion-paiements': 'invoicing.view',
  'gestion-interventions': 'interventions.view',
  'affaires': 'invoicing.view',
  'crm': 'partners.view',
  'stock': 'inventory.view',
  'achats': 'purchases.view',
  'projets': 'projects.view',
  'rh': 'hr.view',
  'vehicules': 'inventory.view',
  'production': 'production.view',
  'maintenance': 'maintenance.view',
  'quality': 'quality.view',
  'pos': 'pos.view',
  'ecommerce': 'ecommerce.view',
  'marketplace': 'marketplace.view',
  'subscriptions': 'subscriptions.view',
  'helpdesk': 'helpdesk.view',
  'web': 'web.view',
  'bi': 'bi.view',
  'compliance': 'compliance.view',
  'compta': 'accounting.view',
  'tresorerie': 'treasury.view',
  'admin': 'admin.view',
  'import-odoo': 'import.odoo.config',
  'import-axonaut': 'import.axonaut.config',
  'import-pennylane': 'import.pennylane.config',
  'import-sage': 'import.sage.config',
  'import-chorus': 'import.chorus.config',
};

// ============================================================
// UNAUTHORIZED VIEW
// Shown when a user lacks the capability for the requested module.
// ============================================================

const UnauthorizedView: React.FC = () => (
  <div className="azals-unauthorized">
    <ShieldX size={48} className="azals-unauthorized__icon" />
    <h2 className="azals-unauthorized__title">Acces non autorise</h2>
    <p className="azals-unauthorized__message">
      Vous n'avez pas les permissions necessaires pour acceder a ce module.
      Contactez votre administrateur si vous pensez qu'il s'agit d'une erreur.
    </p>
  </div>
);

// ============================================================
// ERROR BOUNDARY
// Catches unhandled React errors and displays a recovery UI.
// ============================================================

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('[AZALSCORE] Unhandled error:', error, errorInfo);
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="azals-error-boundary">
          <div className="azals-error-boundary__card">
            <h1 className="azals-error-boundary__brand">AZALSCORE</h1>
            <h2 className="azals-error-boundary__title">
              Une erreur inattendue s'est produite
            </h2>
            <p className="azals-error-boundary__message">
              {this.state.error?.message || "L'application a rencontre un probleme."}
            </p>
            <button
              className="azals-error-boundary__button"
              onClick={this.handleReload}
            >
              Recharger l'application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================================
// QUERY CLIENT
// ============================================================

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        // Ne pas retry les erreurs d'auth (évite des 401 en boucle)
        if (error instanceof Error && error.message.includes('AUTH_NOT_READY')) return false;
        return failureCount < 1;
      },
      refetchOnWindowFocus: false,
    },
  },
});

// Quand l'auth est invalidée (401 / logout forcé), vider le cache React Query
// pour éviter des données stales ou des requêtes orphelines
if (typeof window !== 'undefined') {
  window.addEventListener('azals:auth:logout', () => {
    queryClient.clear();
  });
}

// ============================================================
// LOGIN COMPONENT
// ============================================================

const Login: React.FC = () => {
  const [tenant, setTenant] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!tenant.trim()) {
      setError('Veuillez saisir l\'identifiant de votre société');
      return;
    }
    if (!email.trim()) {
      setError('Veuillez saisir votre email');
      return;
    }
    if (!password) {
      setError('Veuillez saisir votre mot de passe');
      return;
    }

    setLoading(true);

    try {
      // Définir le tenant AVANT le login
      const normalizedTenant = tenant.toLowerCase().trim();
      setTenantId(normalizedTenant);

      // Utiliser la fonction login du store qui gère tout (tokens + user data)
      await login({ email, password });
    } catch (err) {
      console.error('[LOGIN] Erreur:', err);
      setError(err instanceof Error ? err.message : 'Identifiants invalides');
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
            <label htmlFor="tenant">Société</label>
            <input
              id="tenant"
              type="text"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
              placeholder="identifiant-societe"
              autoComplete="organization"
              autoFocus
            />
          </div>
          <div className="azals-login__field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="votre@email.com"
              autoComplete="email"
            />
          </div>
          <div className="azals-login__field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="azals-login__submit" disabled={loading}>
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ============================================================
// MODULE ROUTE CONTEXT
// Maps ViewKeys to their ERP base paths so that modules with
// internal <Routes> (navigate('/invoicing/quotes') etc.) work
// correctly inside UnifiedApp's single-page ViewKey approach.
// ============================================================

const VIEW_BASE_PATH: Partial<Record<ViewKey, string>> = {
  'gestion-devis': '/invoicing',
  'gestion-commandes': '/invoicing',
  'gestion-factures': '/invoicing',
  'gestion-paiements': '/invoicing',
  'gestion-interventions': '/interventions',
  'crm': '/partners',
  'achats': '/purchases',
  'compta': '/accounting',
  'tresorerie': '/treasury',
  'ecommerce': '/ecommerce',
  'pos': '/pos',
  'compliance': '/compliance',
  'admin': '/admin',
};

// Reverse mapping: URL path → ViewKey (for URL-based navigation)
// Uses the FIRST matching ViewKey for each unique path
const PATH_TO_VIEW: Record<string, ViewKey> = {};
for (const [viewKey, path] of Object.entries(VIEW_BASE_PATH)) {
  if (path && !PATH_TO_VIEW[path]) {
    PATH_TO_VIEW[path] = viewKey as ViewKey;
  }
}

/** Determine the ViewKey from the current URL pathname */
function getViewFromPath(pathname: string): ViewKey | null {
  // Exact match first, then prefix match (longest prefix wins)
  for (const [path, viewKey] of Object.entries(PATH_TO_VIEW).sort((a, b) => b[0].length - a[0].length)) {
    if (pathname === path || pathname.startsWith(path + '/')) {
      return viewKey;
    }
  }
  return null;
}

/**
 * Wrapper for modules that use React Router <Routes> internally.
 * Ensures the URL matches the module's expected base path, so that
 * navigate('/invoicing/quotes') works inside UnifiedApp.
 */
const ModuleRouteContext: React.FC<{ basePath: string; children: React.ReactNode }> = ({ basePath, children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!location.pathname.startsWith(basePath)) {
      navigate(basePath, { replace: true });
    }
  }, [basePath, location.pathname, navigate]);

  return (
    <Routes>
      <Route path={`${basePath}/*`} element={<>{children}</>} />
    </Routes>
  );
};

// ============================================================
// VIEW RENDERER
// ============================================================

const ViewRenderer: React.FC<{ viewKey: ViewKey }> = ({ viewKey }) => {
  const { hasCapability } = useCapabilities();
  const capabilitiesReady = useIsCapabilitiesReady();

  const LoadingFallback = <LoadingState />;

  // Check capability access for the current view
  const requiredCapability = VIEW_CAPABILITY_MAP[viewKey];
  if (requiredCapability) {
    // Wait for capabilities to load before deciding access
    if (!capabilitiesReady) {
      return LoadingFallback;
    }
    if (!hasCapability(requiredCapability)) {
      return <UnauthorizedView />;
    }
  }

  const renderView = () => {
    switch (viewKey) {
      // Saisie rapide
      case 'saisie':
        return <SaisieModule />;

      // Gestion documents
      case 'gestion-devis':
      case 'gestion-commandes':
      case 'gestion-factures':
      case 'gestion-paiements':
        return <InvoicingModule />;
      case 'gestion-interventions':
        return <InterventionsModule />;

      // Affaires
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

      // Logistique & Production
      case 'production':
        return <ProductionModule />;
      case 'maintenance':
        return <MaintenanceModule />;
      case 'quality':
        return <QualityModule />;

      // Commerce
      case 'pos':
        return <POSModule />;
      case 'ecommerce':
        return <EcommerceModule />;
      case 'marketplace':
        return <MarketplaceModule />;
      case 'subscriptions':
        return <SubscriptionsModule />;

      // Services
      case 'helpdesk':
        return <HelpdeskModule />;

      // Digital
      case 'web':
        return <WebModule />;
      case 'bi':
        return <BIModule />;
      case 'compliance':
        return <ComplianceModule />;

      // Finance
      case 'compta':
        return <AccountingModule />;
      case 'tresorerie':
        return <TreasuryModule />;

      // Direction
      case 'cockpit':
        return <CockpitView />;

      // IA
      case 'marceau':
        return <MarceauModule />;

      // Import
      case 'import-odoo':
        return <OdooImport />;
      case 'import-axonaut':
        return <AxonautImport />;
      case 'import-pennylane':
        return <PennylaneImport />;
      case 'import-sage':
        return <SageImport />;
      case 'import-chorus':
        return <ChorusImport />;

      // Système
      case 'admin':
        return <AdminModule />;

      // Utilisateur
      case 'profile':
        return <ProfileModule />;
      case 'settings':
        return <SettingsModule />;

      default:
        return <WorksheetView />;
    }
  };

  // Wrap modules that have internal <Routes> in a route context
  const basePath = VIEW_BASE_PATH[viewKey];
  const content = renderView();

  if (basePath) {
    return (
      <Suspense fallback={LoadingFallback}>
        <div className={`azals-view azals-view--${viewKey}`}>
          <ModuleRouteContext basePath={basePath}>
            {content}
          </ModuleRouteContext>
        </div>
      </Suspense>
    );
  }

  return (
    <Suspense fallback={LoadingFallback}>
      <div className={`azals-view azals-view--${viewKey}`}>
        {content}
      </div>
    </Suspense>
  );
};

// ============================================================
// APP CONTENT
// ============================================================

const AppContent: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Initialize view from URL (or default to 'saisie')
  const [currentView, setCurrentView] = useState<ViewKey>(
    () => getViewFromPath(location.pathname) || 'saisie'
  );
  const logout = useAuthStore((state) => state.logout);
  const loadCapabilities = useCapabilitiesStore((state) => state.loadCapabilities);
  const capStatus = useCapabilitiesStore((state) => state.status);

  // Charger les capabilities au montage (production : appel API /v3/auth/capabilities)
  useEffect(() => {
    if (capStatus === 'idle') {
      loadCapabilities();
    }
  }, [capStatus, loadCapabilities]);

  // Sync URL → ViewKey when browser navigates (back/forward)
  useEffect(() => {
    const viewFromUrl = getViewFromPath(location.pathname);
    if (viewFromUrl && viewFromUrl !== currentView) {
      setCurrentView(viewFromUrl);
    }
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  // View change handler: update state + URL
  const handleViewChange = useCallback((view: ViewKey) => {
    setCurrentView(view);
    const basePath = VIEW_BASE_PATH[view];
    if (basePath) {
      navigate(basePath);
    } else {
      navigate('/');
    }
  }, [navigate]);

  const handleLogout = useCallback(async () => {
    await logout();
    queryClient.clear();
  }, [logout]);

  return (
    <UnifiedLayout
      currentView={currentView}
      onViewChange={handleViewChange}
      onLogout={handleLogout}
    >
      <ViewRenderer viewKey={currentView} />
    </UnifiedLayout>
  );
};

// ============================================================
// MAIN APP
// ============================================================

const UnifiedApp: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const status = useAuthStore((state) => state.status);
  const refreshUser = useAuthStore((state) => state.refreshUser);

  // Initialiser l'auth au démarrage
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // En cours de vérification
  if (status === 'idle' || status === 'loading') {
    return (
      <div className="azals-app-init">
        <div className="azals-app-init__spinner" />
        <span>AZALSCORE</span>
      </div>
    );
  }

  // Non authentifié - afficher landing page, pages légales ou login
  if (!isAuthenticated) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/essai-gratuit" element={<TrialRegistration />} />
            <Route path="/essai-gratuit/verify" element={<TrialRegistration />} />
            <Route path="/mentions-legales" element={<MentionsLegales />} />
            <Route path="/confidentialite" element={<Confidentialite />} />
            <Route path="/cgv" element={<CGV />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="*" element={<LandingPage />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    );
  }

  // Authentifié
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default UnifiedApp;
