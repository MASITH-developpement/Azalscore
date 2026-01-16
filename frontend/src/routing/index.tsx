/**
 * AZALSCORE UI Engine - Routing System
 * Routes principales de l'application
 * VERSION SIMPLIFIÉE - Affichage immédiat
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { MainLayout, AuthLayout } from '@ui/layout';
import { useAuthStore } from '@core/auth';

// ============================================================
// LAZY LOADING DES MODULES
// ============================================================

const CockpitPage = lazy(() => import('@modules/cockpit'));
const PartnersRoutes = lazy(() => import('@modules/partners'));
const InvoicingRoutes = lazy(() => import('@modules/invoicing'));
const TreasuryRoutes = lazy(() => import('@modules/treasury'));
const AccountingRoutes = lazy(() => import('@modules/accounting'));
const PurchasesRoutes = lazy(() => import('@modules/purchases'));
const ProjectsRoutes = lazy(() => import('@modules/projects'));
const InterventionsRoutes = lazy(() => import('@modules/interventions'));
const WebRoutes = lazy(() => import('@modules/web'));
const EcommerceRoutes = lazy(() => import('@modules/ecommerce'));
const MarketplaceRoutes = lazy(() => import('@modules/marketplace'));
const PaymentsRoutes = lazy(() => import('@modules/payments'));
const MobileRoutes = lazy(() => import('@modules/mobile'));
const AdminRoutes = lazy(() => import('@modules/admin'));
const BreakGlassPage = lazy(() => import('@modules/break-glass'));

// Pages Auth
const LoginPage = lazy(() => import('@/pages/auth/Login'));
const TwoFactorPage = lazy(() => import('@/pages/auth/TwoFactor'));
const ForgotPasswordPage = lazy(() => import('@/pages/auth/ForgotPassword'));

// Pages communes
const NotFoundPage = lazy(() => import('@/pages/NotFound'));
const ProfilePage = lazy(() => import('@/pages/Profile'));
const SettingsPage = lazy(() => import('@/pages/Settings'));

// ============================================================
// LOADING FALLBACK
// ============================================================

const LoadingFallback: React.FC = () => (
  <div className="azals-loading azals-loading--page">
    <div className="azals-spinner azals-spinner--lg" />
    <p>Chargement...</p>
  </div>
);

// ============================================================
// PROTECTED ROUTE WRAPPER - Gère l'état loading
// ============================================================

const ProtectedRoute: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const authStatus = useAuthStore((state) => state.status);

  // Si auth en cours, afficher loading
  if (authStatus === 'loading' || authStatus === 'idle') {
    return <LoadingFallback />;
  }

  // Si non authentifié, rediriger vers login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children || <Outlet />}</>;
};

// ============================================================
// PUBLIC ROUTE WRAPPER - Pas de redirection pendant loading
// ============================================================

const PublicRoute: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const authStatus = useAuthStore((state) => state.status);

  // Pendant loading, afficher le contenu (pas de redirection prématurée)
  if (authStatus === 'loading' || authStatus === 'idle') {
    return <>{children || <Outlet />}</>;
  }

  // Si authentifié, rediriger vers cockpit
  if (isAuthenticated) {
    return <Navigate to="/cockpit" replace />;
  }

  return <>{children || <Outlet />}</>;
};

// ============================================================
// MAIN ROUTER - Simplifié sans capability guards bloquants
// ============================================================

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Routes publiques (Auth) */}
          <Route element={<PublicRoute><AuthLayout /></PublicRoute>}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/2fa" element={<TwoFactorPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          </Route>

          {/* Routes protégées (App) */}
          <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
            {/* Redirect racine vers cockpit */}
            <Route path="/" element={<Navigate to="/cockpit" replace />} />

            {/* Cockpit Dirigeant */}
            <Route path="/cockpit" element={<CockpitPage />} />

            {/* ROUTE OBLIGATOIRE: /clients (alias vers partners/clients) */}
            <Route path="/clients" element={<Navigate to="/partners/clients" replace />} />

            {/* Partenaires */}
            <Route path="/partners/*" element={<PartnersRoutes />} />

            {/* Facturation */}
            <Route path="/invoicing/*" element={<InvoicingRoutes />} />

            {/* Trésorerie */}
            <Route path="/treasury/*" element={<TreasuryRoutes />} />

            {/* Comptabilité */}
            <Route path="/accounting/*" element={<AccountingRoutes />} />

            {/* Achats */}
            <Route path="/purchases/*" element={<PurchasesRoutes />} />

            {/* Projets */}
            <Route path="/projects/*" element={<ProjectsRoutes />} />

            {/* ROUTE OBLIGATOIRE: /interventions */}
            <Route path="/interventions/*" element={<InterventionsRoutes />} />

            {/* Site Web */}
            <Route path="/web/*" element={<WebRoutes />} />

            {/* E-commerce */}
            <Route path="/ecommerce/*" element={<EcommerceRoutes />} />

            {/* Marketplace */}
            <Route path="/marketplace/*" element={<MarketplaceRoutes />} />

            {/* Paiements */}
            <Route path="/payments/*" element={<PaymentsRoutes />} />

            {/* Mobile */}
            <Route path="/mobile/*" element={<MobileRoutes />} />

            {/* Administration */}
            <Route path="/admin/*" element={<AdminRoutes />} />

            {/* Break-Glass */}
            <Route path="/admin/break-glass" element={<BreakGlassPage />} />

            {/* Profil et Paramètres */}
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default AppRouter;
