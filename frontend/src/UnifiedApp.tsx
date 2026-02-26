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
import { ShieldX } from 'lucide-react';
import { HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { setTenantId } from '@core/api-client';
import { useAuthStore } from '@core/auth';
import { useCapabilities, useIsCapabilitiesReady, useCapabilitiesStore } from '@core/capabilities';
import { UnifiedLayout, type ViewKey } from './components/UnifiedLayout';
import LandingPage from './pages/LandingPage';
import { MentionsLegales, Confidentialite, CGV, Contact } from './pages/legal';
import { TrialRegistration } from './pages/trial';
import { LoadingState } from './ui-engine/components/StateViews';
import './styles/main.css';
import './styles/unified-layout.css';
import './styles/azalscore.css';
import './styles/blog.css';
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

// Blog pages
const BlogIndex = lazy(() => import('./pages/blog'));
const BlogFacturation2026 = lazy(() => import('./pages/blog/FacturationElectronique2026'));
const BlogErpPmeGuide = lazy(() => import('./pages/blog/ErpPmeGuideComplet'));
const BlogRgpdErp = lazy(() => import('./pages/blog/ConformiteRgpdErp'));
const BlogTresorerie = lazy(() => import('./pages/blog/GestionTresoreriePme'));
const BlogCrm = lazy(() => import('./pages/blog/CrmRelationClient'));
const BlogStock = lazy(() => import('./pages/blog/GestionStockOptimisation'));

// Comparatif pages (SEO)
const VsOdoo = lazy(() => import('./pages/comparatif/VsOdoo'));
const VsSage = lazy(() => import('./pages/comparatif/VsSage'));
const VsEbp = lazy(() => import('./pages/comparatif/VsEbp'));

// Secteurs pages (SEO)
const SecteurCommerce = lazy(() => import('./pages/secteurs/Commerce'));
const SecteurServices = lazy(() => import('./pages/secteurs/Services'));
const SecteurIndustrie = lazy(() => import('./pages/secteurs/Industrie'));

// Feature detail pages (SEO)
const FeatureDetail = lazy(() => import('./pages/features/FeatureDetail'));

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
  'crm': 'crm.view',
  'partners': 'partners.view',
  'inventory': 'inventory.view',
  'purchases': 'purchases.view',
  'projects': 'projects.view',
  'hr': 'hr.view',
  'production': 'production.view',
  'maintenance': 'maintenance.view',
  'quality': 'quality.view',
  'qc': 'qc.view',
  'pos': 'pos.view',
  'ecommerce': 'ecommerce.view',
  'marketplace': 'marketplace.view',
  'subscriptions': 'subscriptions.view',
  'commercial': 'commercial.view',
  'helpdesk': 'helpdesk.view',
  'web': 'web.view',
  'website': 'website.view',
  'bi': 'bi.view',
  'compliance': 'compliance.view',
  'broadcast': 'broadcast.view',
  'social-networks': 'social_networks.view',
  'accounting': 'accounting.view',
  'treasury': 'treasury.view',
  'assets': 'assets.view',
  'expenses': 'expenses.view',
  'finance': 'finance.view',
  'consolidation': 'consolidation.view',
  'automated-accounting': 'automated_accounting.view',
  'contracts': 'contracts.view',
  'timesheet': 'timesheet.view',
  'field-service': 'field_service.view',
  'complaints': 'complaints.view',
  'warranty': 'warranty.view',
  'rfq': 'rfq.view',
  'procurement': 'procurement.view',
  'esignature': 'esignature.view',
  'email': 'email.view',
  'ai-assistant': 'ai_assistant.view',
  'marceau': 'marceau.view',
  'admin': 'admin.view',
  'audit': 'audit.view',
  'backup': 'backup.view',
  'guardian': 'guardian.view',
  'iam': 'iam.view',
  'tenants': 'tenants.view',
  'triggers': 'triggers.view',
  'autoconfig': 'autoconfig.view',
  'hr-vault': 'hr_vault.view',
  'stripe-integration': 'stripe_integration.view',
  'country-packs': 'country_packs.view',
  'import-odoo': 'import_data.odoo',
  'import-axonaut': 'import_data.axonaut',
  'import-pennylane': 'import_data.pennylane',
  'import-sage': 'import_data.sage',
  'import-chorus': 'import_data.chorus',
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
      Vous n&apos;avez pas les permissions necessaires pour acceder a ce module.
      Contactez votre administrateur si vous pensez qu&apos;il s&apos;agit d&apos;une erreur.
    </p>
  </div>
);

// ============================================================
// PLACEHOLDER MODULE
// Shown for modules that are not yet implemented.
// ============================================================

const PlaceholderModule: React.FC<{ name: string }> = ({ name }) => (
  <div className="azals-placeholder">
    <div className="azals-placeholder__content">
      <h2 className="azals-placeholder__title">{name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h2>
      <p className="azals-placeholder__message">
        Ce module est en cours de développement. Il sera disponible prochainement.
      </p>
    </div>
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
              Une erreur inattendue s&apos;est produite
            </h2>
            <p className="azals-error-boundary__message">
              {this.state.error?.message || "L&apos;application a rencontre un probleme."}
            </p>
            <button
              className="azals-error-boundary__button"
              onClick={this.handleReload}
            >
              Recharger l&apos;application
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
  // Saisie rapide
  'saisie': '/saisie',

  // Gestion documents
  'gestion-devis': '/invoicing',
  'gestion-commandes': '/invoicing',
  'gestion-factures': '/invoicing',
  'gestion-paiements': '/invoicing',
  'gestion-interventions': '/interventions',

  // Affaires
  'affaires': '/affaires',

  // Modules métier
  'partners': '/partners',
  'crm': '/crm',
  'inventory': '/inventory',
  'purchases': '/purchases',
  'projects': '/projects',
  'hr': '/hr',
  'contracts': '/contracts',
  'timesheet': '/timesheet',
  'field-service': '/field-service',
  'complaints': '/complaints',
  'warranty': '/warranty',
  'rfq': '/rfq',
  'procurement': '/procurement',

  // Logistique & Production
  'production': '/production',
  'maintenance': '/maintenance',
  'quality': '/quality',
  'qc': '/qc',

  // Commerce
  'pos': '/pos',
  'ecommerce': '/ecommerce',
  'marketplace': '/marketplace',
  'subscriptions': '/subscriptions',
  'commercial': '/commercial',

  // Services
  'helpdesk': '/helpdesk',

  // Digital
  'web': '/web',
  'website': '/website',
  'bi': '/bi',
  'compliance': '/compliance',
  'broadcast': '/broadcast',
  'social-networks': '/social-networks',

  // Communication
  'esignature': '/esignature',
  'email': '/email',

  // Finance
  'accounting': '/accounting',
  'treasury': '/treasury',
  'assets': '/assets',
  'expenses': '/expenses',
  'finance': '/finance',
  'consolidation': '/consolidation',
  'automated-accounting': '/automated-accounting',

  // Direction
  'cockpit': '/cockpit',

  // Système
  'audit': '/audit',
  'backup': '/backup',
  'guardian': '/guardian',
  'iam': '/iam',
  'tenants': '/tenants',
  'triggers': '/triggers',
  'autoconfig': '/autoconfig',
  'hr-vault': '/hr-vault',
  'stripe-integration': '/stripe-integration',
  'country-packs': '/country-packs',

  // IA
  'marceau': '/marceau',

  // Import
  'import-odoo': '/import/odoo',
  'import-axonaut': '/import/axonaut',
  'import-pennylane': '/import/pennylane',
  'import-sage': '/import/sage',
  'import-chorus': '/import/chorus',

  // Système
  'admin': '/admin',

  // Utilisateur
  'profile': '/profile',
  'settings': '/settings',
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
      case 'partners':
        return <PartnersModule />;
      case 'crm':
        return <PartnersModule />; // CRM avancé utilise le même module
      case 'inventory':
        return <InventoryModule />;
      case 'purchases':
        return <PurchasesModule />;
      case 'projects':
        return <ProjectsModule />;
      case 'hr':
        return <HRModule />;
      case 'contracts':
      case 'timesheet':
      case 'field-service':
      case 'complaints':
      case 'warranty':
      case 'rfq':
      case 'procurement':
        return <PlaceholderModule name={viewKey} />;

      // Logistique & Production
      case 'production':
        return <ProductionModule />;
      case 'maintenance':
        return <MaintenanceModule />;
      case 'quality':
      case 'qc':
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
      case 'commercial':
        return <PlaceholderModule name="Commercial" />;

      // Services
      case 'helpdesk':
        return <HelpdeskModule />;

      // Digital
      case 'web':
      case 'website':
        return <WebModule />;
      case 'bi':
        return <BIModule />;
      case 'compliance':
        return <ComplianceModule />;
      case 'broadcast':
      case 'social-networks':
        return <PlaceholderModule name={viewKey} />;

      // Communication
      case 'esignature':
      case 'email':
        return <PlaceholderModule name={viewKey} />;

      // Finance
      case 'accounting':
        return <AccountingModule />;
      case 'treasury':
        return <TreasuryModule />;
      case 'assets':
      case 'expenses':
      case 'finance':
      case 'consolidation':
      case 'automated-accounting':
        return <PlaceholderModule name={viewKey} />;

      // Direction
      case 'cockpit':
        return <CockpitView />;

      // IA
      case 'marceau':
      case 'ai-assistant':
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
      case 'audit':
      case 'backup':
      case 'guardian':
      case 'iam':
      case 'tenants':
      case 'triggers':
      case 'autoconfig':
      case 'hr-vault':
      case 'stripe-integration':
      case 'country-packs':
        return <PlaceholderModule name={viewKey} />;

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

  // Charger les capabilities au montage (production : appel API /auth/capabilities)
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
      <HelmetProvider>
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
            <Route path="/blog" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogIndex /></Suspense>} />
            <Route path="/blog/facturation-electronique-2026" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogFacturation2026 /></Suspense>} />
            <Route path="/blog/erp-pme-guide-complet" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogErpPmeGuide /></Suspense>} />
            <Route path="/blog/conformite-rgpd-erp" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogRgpdErp /></Suspense>} />
            <Route path="/blog/gestion-tresorerie-pme" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogTresorerie /></Suspense>} />
            <Route path="/blog/crm-relation-client" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogCrm /></Suspense>} />
            <Route path="/blog/gestion-stock-optimisation" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><BlogStock /></Suspense>} />

            {/* Comparatif pages */}
            <Route path="/comparatif/azalscore-vs-odoo" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><VsOdoo /></Suspense>} />
            <Route path="/comparatif/azalscore-vs-sage" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><VsSage /></Suspense>} />
            <Route path="/comparatif/azalscore-vs-ebp" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><VsEbp /></Suspense>} />

            {/* Secteurs pages */}
            <Route path="/secteurs/commerce" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><SecteurCommerce /></Suspense>} />
            <Route path="/secteurs/services" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><SecteurServices /></Suspense>} />
            <Route path="/secteurs/industrie" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><SecteurIndustrie /></Suspense>} />

            {/* Feature detail pages */}
            <Route path="/features/:feature" element={<Suspense fallback={<div className="azals-loading">Chargement...</div>}><FeatureDetail /></Suspense>} />

            <Route path="*" element={<LandingPage />} />
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </HelmetProvider>
    );
  }

  // Authentifié
  return (
    <HelmetProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    </HelmetProvider>
  );
};

export default UnifiedApp;
