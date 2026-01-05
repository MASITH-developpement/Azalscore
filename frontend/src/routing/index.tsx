/**
 * AZALSCORE UI Engine - Routing System
 * Routes principales de l'application
 * Accès contrôlé par capacités backend
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { MainLayout, AuthLayout } from '@ui/layout';
import { CapabilityGuard } from '@core/capabilities';
import { useIsAuthenticated } from '@core/auth';

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
// PROTECTED ROUTE WRAPPER
// ============================================================

const ProtectedRoute: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useIsAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children || <Outlet />}</>;
};

// ============================================================
// PUBLIC ROUTE WRAPPER (redirect if authenticated)
// ============================================================

const PublicRoute: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useIsAuthenticated();

  if (isAuthenticated) {
    return <Navigate to="/cockpit" replace />;
  }

  return <>{children || <Outlet />}</>;
};

// ============================================================
// CAPABILITY ROUTE WRAPPER
// ============================================================

interface CapabilityRouteProps {
  capability: string;
  children: React.ReactNode;
}

const CapabilityRoute: React.FC<CapabilityRouteProps> = ({ capability, children }) => {
  return (
    <CapabilityGuard capability={capability} fallback={<Navigate to="/cockpit" replace />}>
      {children}
    </CapabilityGuard>
  );
};

// ============================================================
// MAIN ROUTER
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
            <Route path="/cockpit" element={
              <CapabilityRoute capability="cockpit.view">
                <CockpitPage />
              </CapabilityRoute>
            } />

            {/* Partenaires */}
            <Route path="/partners/*" element={
              <CapabilityRoute capability="partners.view">
                <PartnersRoutes />
              </CapabilityRoute>
            } />

            {/* Facturation */}
            <Route path="/invoicing/*" element={
              <CapabilityRoute capability="invoicing.view">
                <InvoicingRoutes />
              </CapabilityRoute>
            } />

            {/* Trésorerie */}
            <Route path="/treasury/*" element={
              <CapabilityRoute capability="treasury.view">
                <TreasuryRoutes />
              </CapabilityRoute>
            } />

            {/* Comptabilité */}
            <Route path="/accounting/*" element={
              <CapabilityRoute capability="accounting.view">
                <AccountingRoutes />
              </CapabilityRoute>
            } />

            {/* Achats */}
            <Route path="/purchases/*" element={
              <CapabilityRoute capability="purchases.view">
                <PurchasesRoutes />
              </CapabilityRoute>
            } />

            {/* Projets */}
            <Route path="/projects/*" element={
              <CapabilityRoute capability="projects.view">
                <ProjectsRoutes />
              </CapabilityRoute>
            } />

            {/* Interventions */}
            <Route path="/interventions/*" element={
              <CapabilityRoute capability="interventions.view">
                <InterventionsRoutes />
              </CapabilityRoute>
            } />

            {/* Site Web */}
            <Route path="/web/*" element={
              <CapabilityRoute capability="web.view">
                <WebRoutes />
              </CapabilityRoute>
            } />

            {/* E-commerce */}
            <Route path="/ecommerce/*" element={
              <CapabilityRoute capability="ecommerce.view">
                <EcommerceRoutes />
              </CapabilityRoute>
            } />

            {/* Marketplace */}
            <Route path="/marketplace/*" element={
              <CapabilityRoute capability="marketplace.view">
                <MarketplaceRoutes />
              </CapabilityRoute>
            } />

            {/* Paiements */}
            <Route path="/payments/*" element={
              <CapabilityRoute capability="payments.view">
                <PaymentsRoutes />
              </CapabilityRoute>
            } />

            {/* Mobile */}
            <Route path="/mobile/*" element={<MobileRoutes />} />

            {/* Administration */}
            <Route path="/admin/*" element={
              <CapabilityRoute capability="admin.view">
                <AdminRoutes />
              </CapabilityRoute>
            } />

            {/* Break-Glass (route spéciale - invisible si pas de capacité) */}
            <Route path="/admin/break-glass" element={
              <CapabilityRoute capability="admin.root.break_glass">
                <BreakGlassPage />
              </CapabilityRoute>
            } />

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
