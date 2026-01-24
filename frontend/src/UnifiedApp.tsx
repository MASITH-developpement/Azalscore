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
import { BrowserRouter } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { tokenManager, setTenantId } from '@core/api-client';
import { useAuthStore } from '@core/auth';
import { UnifiedLayout, type ViewKey } from './components/UnifiedLayout';
import './styles/unified-layout.css';
import './styles/azalscore.css';
import './styles/top-menu.css';
import './styles/command-palette.css';

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

// ============================================================
// QUERY CLIENT
// ============================================================

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

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
      console.log('[LOGIN] Tenant défini:', normalizedTenant);

      // Utiliser la fonction login du store qui gère tout (tokens + user data)
      await login({ email, password });
      console.log('[LOGIN] Connexion réussie');
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
      // Saisie
      case 'saisie':
        return <WorksheetView />;

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

      // Système
      case 'admin':
        return <AdminModule />;

      default:
        return <WorksheetView />;
    }
  };

  return (
    <Suspense fallback={LoadingFallback}>
      <div className={`azals-view azals-view--${viewKey}`}>
        {renderView()}
      </div>
    </Suspense>
  );
};

// ============================================================
// APP CONTENT
// ============================================================

const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewKey>('saisie');
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = useCallback(async () => {
    await logout();
    queryClient.clear();
  }, [logout]);

  return (
    <UnifiedLayout
      currentView={currentView}
      onViewChange={setCurrentView}
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

  // Non authentifié
  if (!isAuthenticated) {
    return <Login />;
  }

  // Authentifié
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default UnifiedApp;
