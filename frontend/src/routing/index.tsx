/**
 * AZALSCORE UI Engine - Routing System
 * Routes principales de l'application
 * Accès contrôlé par capacités backend
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useIsAuthenticated } from '@core/auth';
import { CapabilityGuard } from '@core/capabilities';
import { LoadingState } from '@ui/components/StateViews';
import { MainLayout, AuthLayout } from '@ui/layout';

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

// Modules métier additionnels
const ContactsRoutes = lazy(() => import('@modules/contacts'));
const HRRoutes = lazy(() => import('@modules/hr'));
const CRMRoutes = lazy(() => import('@modules/crm'));
const InventoryRoutes = lazy(() => import('@modules/inventory'));
const ProductionRoutes = lazy(() => import('@modules/production'));
const MaintenanceRoutes = lazy(() => import('@modules/maintenance'));
const QualityRoutes = lazy(() => import('@modules/qualite'));
const POSRoutes = lazy(() => import('@modules/pos'));
const SubscriptionsRoutes = lazy(() => import('@modules/subscriptions'));
const HelpdeskRoutes = lazy(() => import('@modules/helpdesk'));
const BIRoutes = lazy(() => import('@modules/bi'));
const ComplianceRoutes = lazy(() => import('@modules/compliance'));
const MarceauRoutes = lazy(() => import('@modules/marceau'));
const AffairesRoutes = lazy(() => import('@modules/affaires'));
const AiAssistantRoutes = lazy(() => import('@modules/ai-assistant'));
const AssetsRoutes = lazy(() => import('@modules/assets'));
const AuditRoutes = lazy(() => import('@modules/audit'));
const AutoconfigRoutes = lazy(() => import('@modules/autoconfig'));
const AutomatedAccountingRoutes = lazy(() => import('@modules/automated-accounting'));
const BackupRoutes = lazy(() => import('@modules/backup'));
const BroadcastRoutes = lazy(() => import('@modules/broadcast'));
const CommandesRoutes = lazy(() => import('@modules/commandes'));
const CommercialRoutes = lazy(() => import('@modules/commercial'));
const ComplaintsRoutes = lazy(() => import('@modules/complaints'));
const ComptabiliteRoutes = lazy(() => import('@modules/comptabilite'));
const ConsolidationRoutes = lazy(() => import('@modules/consolidation'));
const ContractsRoutes = lazy(() => import('@modules/contracts'));
const CountryPacksRoutes = lazy(() => import('@modules/country-packs'));
const CountryPacksFranceRoutes = lazy(() => import('@modules/country-packs-france'));
const DevisRoutes = lazy(() => import('@modules/devis'));
const EmailRoutes = lazy(() => import('@modules/email'));
const EsignatureRoutes = lazy(() => import('@modules/esignature'));
const ExpensesRoutes = lazy(() => import('@modules/expenses'));
const FacturesRoutes = lazy(() => import('@modules/factures'));
const FieldServiceRoutes = lazy(() => import('@modules/field-service'));
const FinanceRoutes = lazy(() => import('@modules/finance'));
const GuardianRoutes = lazy(() => import('@modules/guardian'));
const HrVaultRoutes = lazy(() => import('@modules/hr-vault'));
const IamRoutes = lazy(() => import('@modules/iam'));
const ImportRoutes = lazy(() => import('@modules/import'));
const ImportGatewaysRoutes = lazy(() => import('@modules/import-gateways'));
const OdooImportRoutes = lazy(() => import('@modules/odoo-import'));
const OrdresServiceRoutes = lazy(() => import('@modules/ordres-service'));
const ProcurementRoutes = lazy(() => import('@modules/procurement'));
const ProfileRoutes = lazy(() => import('@modules/profile'));
const QcRoutes = lazy(() => import('@modules/qc'));
const QualityModuleRoutes = lazy(() => import('@modules/quality'));
const RfqRoutes = lazy(() => import('@modules/rfq'));
const SaisieRoutes = lazy(() => import('@modules/saisie'));
const SettingsRoutes = lazy(() => import('@modules/settings'));
const SocialNetworksRoutes = lazy(() => import('@modules/social-networks'));
const StripeIntegrationRoutes = lazy(() => import('@modules/stripe-integration'));
const TenantsRoutes = lazy(() => import('@modules/tenants'));
const TimesheetRoutes = lazy(() => import('@modules/timesheet'));
const TriggersRoutes = lazy(() => import('@modules/triggers'));
const VehiclesRoutes = lazy(() => import('@modules/vehicles'));
const WarrantyRoutes = lazy(() => import('@modules/warranty'));
const WebsiteRoutes = lazy(() => import('@modules/website'));
const WorksheetRoutes = lazy(() => import('@modules/worksheet'));

// Pages Auth
const LoginPage = lazy(() => import('@/pages/auth/Login'));
const TwoFactorPage = lazy(() => import('@/pages/auth/TwoFactor'));
const ForgotPasswordPage = lazy(() => import('@/pages/auth/ForgotPassword'));

// Pages publiques - import direct pour page d'accueil (performance critique)
import LandingPage from '@/pages/LandingPage';

// Pages publiques additionnelles (lazy)
const TrialPage = lazy(() => import('@/pages/trial'));
const FeaturesPage = lazy(() => import('@/pages/public/Features'));
const PricingPage = lazy(() => import('@/pages/public/Pricing'));
const AboutPage = lazy(() => import('@/pages/public/About'));
const DemoPage = lazy(() => import('@/pages/public/Demo'));
const DocsPage = lazy(() => import('@/pages/public/Docs'));

// Pages légales
const MentionsLegales = lazy(() => import('@/pages/legal/MentionsLegales'));
const Confidentialite = lazy(() => import('@/pages/legal/Confidentialite'));
const CGV = lazy(() => import('@/pages/legal/CGV'));
const ContactPage = lazy(() => import('@/pages/legal/Contact'));

// Pages communes
const NotFoundPage = lazy(() => import('@/pages/NotFound'));
const ProfilePage = lazy(() => import('@/pages/Profile'));
const SettingsPage = lazy(() => import('@/pages/Settings'));

// ============================================================
// LOADING FALLBACK
// ============================================================

const LoadingFallback: React.FC = () => (
  <div className="azals-loading azals-loading--page">
    <LoadingState
      onRetry={() => window.location.reload()}
      message="Chargement du module..."
    />
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
// HOME ROUTE WRAPPER (landing page or cockpit)
// ============================================================

const HomeRoute: React.FC = () => {
  const isAuthenticated = useIsAuthenticated();

  if (isAuthenticated) {
    return <Navigate to="/cockpit" replace />;
  }

  return <LandingPage />;
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
          {/* Page d'accueil publique */}
          <Route path="/" element={<HomeRoute />} />

          {/* Pages publiques marketing */}
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/essai-gratuit" element={<TrialPage />} />
          <Route path="/contact" element={<ContactPage />} />

          {/* Pages légales */}
          <Route path="/mentions-legales" element={<MentionsLegales />} />
          <Route path="/confidentialite" element={<Confidentialite />} />
          <Route path="/cgv" element={<CGV />} />

          {/* Routes publiques (Auth) */}
          <Route element={<PublicRoute><AuthLayout /></PublicRoute>}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/2fa" element={<TwoFactorPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          </Route>

          {/* Routes protégées (App) */}
          <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>

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

            {/* Ressources Humaines */}
            <Route path="/hr/*" element={
              <CapabilityRoute capability="hr.view">
                <HRRoutes />
              </CapabilityRoute>
            } />

            {/* Contacts Unifiés */}
            <Route path="/contacts/*" element={
              <CapabilityRoute capability="contacts.view">
                <ContactsRoutes />
              </CapabilityRoute>
            } />

            {/* CRM */}
            <Route path="/crm/*" element={
              <CapabilityRoute capability="crm.view">
                <CRMRoutes />
              </CapabilityRoute>
            } />

            {/* Inventaire / Stock */}
            <Route path="/inventory/*" element={
              <CapabilityRoute capability="inventory.view">
                <InventoryRoutes />
              </CapabilityRoute>
            } />

            {/* Production */}
            <Route path="/production/*" element={
              <CapabilityRoute capability="production.view">
                <ProductionRoutes />
              </CapabilityRoute>
            } />

            {/* Maintenance */}
            <Route path="/maintenance/*" element={
              <CapabilityRoute capability="maintenance.view">
                <MaintenanceRoutes />
              </CapabilityRoute>
            } />

            {/* Qualité */}
            <Route path="/quality/*" element={
              <CapabilityRoute capability="quality.view">
                <QualityRoutes />
              </CapabilityRoute>
            } />

            {/* Point de Vente */}
            <Route path="/pos/*" element={
              <CapabilityRoute capability="pos.view">
                <POSRoutes />
              </CapabilityRoute>
            } />

            {/* Abonnements */}
            <Route path="/subscriptions/*" element={
              <CapabilityRoute capability="subscriptions.view">
                <SubscriptionsRoutes />
              </CapabilityRoute>
            } />

            {/* Helpdesk */}
            <Route path="/helpdesk/*" element={
              <CapabilityRoute capability="helpdesk.view">
                <HelpdeskRoutes />
              </CapabilityRoute>
            } />

            {/* Business Intelligence */}
            <Route path="/bi/*" element={
              <CapabilityRoute capability="bi.view">
                <BIRoutes />
              </CapabilityRoute>
            } />

            {/* Conformité */}
            <Route path="/compliance/*" element={
              <CapabilityRoute capability="compliance.view">
                <ComplianceRoutes />
              </CapabilityRoute>
            } />

            {/* Marceau AI Assistant */}
            <Route path="/marceau/*" element={
              <CapabilityRoute capability="marceau.view">
                <MarceauRoutes />
              </CapabilityRoute>
            } />

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

            
            {/* Affaires */}
            <Route path="/affaires/*" element={
              <CapabilityRoute capability="affaires.view">
                <AffairesRoutes />
              </CapabilityRoute>
            } />

            {/* Assistant IA */}
            <Route path="/ai-assistant/*" element={
              <CapabilityRoute capability="ai_assistant.view">
                <AiAssistantRoutes />
              </CapabilityRoute>
            } />

            {/* Immobilisations */}
            <Route path="/assets/*" element={
              <CapabilityRoute capability="assets.view">
                <AssetsRoutes />
              </CapabilityRoute>
            } />

            {/* Audit */}
            <Route path="/audit/*" element={
              <CapabilityRoute capability="audit.view">
                <AuditRoutes />
              </CapabilityRoute>
            } />

            {/* Configuration Auto */}
            <Route path="/autoconfig/*" element={
              <CapabilityRoute capability="autoconfig.view">
                <AutoconfigRoutes />
              </CapabilityRoute>
            } />

            {/* Comptabilité Auto */}
            <Route path="/automated-accounting/*" element={
              <CapabilityRoute capability="automated_accounting.view">
                <AutomatedAccountingRoutes />
              </CapabilityRoute>
            } />

            {/* Sauvegardes */}
            <Route path="/backup/*" element={
              <CapabilityRoute capability="backup.view">
                <BackupRoutes />
              </CapabilityRoute>
            } />

            {/* Diffusion */}
            <Route path="/broadcast/*" element={
              <CapabilityRoute capability="broadcast.view">
                <BroadcastRoutes />
              </CapabilityRoute>
            } />

            {/* Commandes */}
            <Route path="/commandes/*" element={
              <CapabilityRoute capability="commandes.view">
                <CommandesRoutes />
              </CapabilityRoute>
            } />

            {/* Commercial */}
            <Route path="/commercial/*" element={
              <CapabilityRoute capability="commercial.view">
                <CommercialRoutes />
              </CapabilityRoute>
            } />

            {/* Réclamations */}
            <Route path="/complaints/*" element={
              <CapabilityRoute capability="complaints.view">
                <ComplaintsRoutes />
              </CapabilityRoute>
            } />

            {/* Comptabilité */}
            <Route path="/comptabilite/*" element={
              <CapabilityRoute capability="comptabilite.view">
                <ComptabiliteRoutes />
              </CapabilityRoute>
            } />

            {/* Consolidation */}
            <Route path="/consolidation/*" element={
              <CapabilityRoute capability="consolidation.view">
                <ConsolidationRoutes />
              </CapabilityRoute>
            } />

            {/* Contrats */}
            <Route path="/contracts/*" element={
              <CapabilityRoute capability="contracts.view">
                <ContractsRoutes />
              </CapabilityRoute>
            } />

            {/* Packs Pays */}
            <Route path="/country-packs/*" element={
              <CapabilityRoute capability="country_packs.view">
                <CountryPacksRoutes />
              </CapabilityRoute>
            } />

            {/* Pack France */}
            <Route path="/country-packs-france/*" element={
              <CapabilityRoute capability="country_packs_france.view">
                <CountryPacksFranceRoutes />
              </CapabilityRoute>
            } />

            {/* Devis */}
            <Route path="/devis/*" element={
              <CapabilityRoute capability="devis.view">
                <DevisRoutes />
              </CapabilityRoute>
            } />

            {/* Email */}
            <Route path="/email/*" element={
              <CapabilityRoute capability="email.view">
                <EmailRoutes />
              </CapabilityRoute>
            } />

            {/* Signature Électronique */}
            <Route path="/esignature/*" element={
              <CapabilityRoute capability="esignature.view">
                <EsignatureRoutes />
              </CapabilityRoute>
            } />

            {/* Notes de Frais */}
            <Route path="/expenses/*" element={
              <CapabilityRoute capability="expenses.view">
                <ExpensesRoutes />
              </CapabilityRoute>
            } />

            {/* Factures */}
            <Route path="/factures/*" element={
              <CapabilityRoute capability="factures.view">
                <FacturesRoutes />
              </CapabilityRoute>
            } />

            {/* Service Terrain */}
            <Route path="/field-service/*" element={
              <CapabilityRoute capability="field_service.view">
                <FieldServiceRoutes />
              </CapabilityRoute>
            } />

            {/* Finance */}
            <Route path="/finance/*" element={
              <CapabilityRoute capability="finance.view">
                <FinanceRoutes />
              </CapabilityRoute>
            } />

            {/* Guardian (Sécurité) */}
            <Route path="/guardian/*" element={
              <CapabilityRoute capability="guardian.view">
                <GuardianRoutes />
              </CapabilityRoute>
            } />

            {/* Coffre-fort RH */}
            <Route path="/hr-vault/*" element={
              <CapabilityRoute capability="hr_vault.view">
                <HrVaultRoutes />
              </CapabilityRoute>
            } />

            {/* Gestion des Accès */}
            <Route path="/iam/*" element={
              <CapabilityRoute capability="iam.view">
                <IamRoutes />
              </CapabilityRoute>
            } />

            {/* Import Données */}
            <Route path="/import/*" element={
              <CapabilityRoute capability="import.view">
                <ImportRoutes />
              </CapabilityRoute>
            } />

            {/* Passerelles Import */}
            <Route path="/import-gateways/*" element={
              <CapabilityRoute capability="import_gateways.view">
                <ImportGatewaysRoutes />
              </CapabilityRoute>
            } />

            {/* Import Odoo */}
            <Route path="/odoo-import/*" element={
              <CapabilityRoute capability="odoo_import.view">
                <OdooImportRoutes />
              </CapabilityRoute>
            } />

            {/* Ordres de Service */}
            <Route path="/ordres-service/*" element={
              <CapabilityRoute capability="ordres_service.view">
                <OrdresServiceRoutes />
              </CapabilityRoute>
            } />

            {/* Approvisionnement */}
            <Route path="/procurement/*" element={
              <CapabilityRoute capability="procurement.view">
                <ProcurementRoutes />
              </CapabilityRoute>
            } />

            {/* Profil */}
            <Route path="/profile/*" element={
              <CapabilityRoute capability="profile.view">
                <ProfileRoutes />
              </CapabilityRoute>
            } />

            {/* Contrôle Qualité */}
            <Route path="/qc/*" element={
              <CapabilityRoute capability="qc.view">
                <QcRoutes />
              </CapabilityRoute>
            } />

            {/* Appels d'Offres */}
            <Route path="/rfq/*" element={
              <CapabilityRoute capability="rfq.view">
                <RfqRoutes />
              </CapabilityRoute>
            } />

            {/* Saisie */}
            <Route path="/saisie/*" element={
              <CapabilityRoute capability="saisie.view">
                <SaisieRoutes />
              </CapabilityRoute>
            } />

            {/* Paramètres */}
            <Route path="/settings/*" element={
              <CapabilityRoute capability="settings.view">
                <SettingsRoutes />
              </CapabilityRoute>
            } />

            {/* Réseaux Sociaux */}
            <Route path="/social-networks/*" element={
              <CapabilityRoute capability="social_networks.view">
                <SocialNetworksRoutes />
              </CapabilityRoute>
            } />

            {/* Intégration Stripe */}
            <Route path="/stripe-integration/*" element={
              <CapabilityRoute capability="stripe_integration.view">
                <StripeIntegrationRoutes />
              </CapabilityRoute>
            } />

            {/* Multi-Tenants */}
            <Route path="/tenants/*" element={
              <CapabilityRoute capability="tenants.view">
                <TenantsRoutes />
              </CapabilityRoute>
            } />

            {/* Feuilles de Temps */}
            <Route path="/timesheet/*" element={
              <CapabilityRoute capability="timesheet.view">
                <TimesheetRoutes />
              </CapabilityRoute>
            } />

            {/* Déclencheurs */}
            <Route path="/triggers/*" element={
              <CapabilityRoute capability="triggers.view">
                <TriggersRoutes />
              </CapabilityRoute>
            } />

            {/* Véhicules */}
            <Route path="/vehicles/*" element={
              <CapabilityRoute capability="vehicles.view">
                <VehiclesRoutes />
              </CapabilityRoute>
            } />

            {/* Garanties */}
            <Route path="/warranty/*" element={
              <CapabilityRoute capability="warranty.view">
                <WarrantyRoutes />
              </CapabilityRoute>
            } />

            {/* Site Web Builder */}
            <Route path="/website/*" element={
              <CapabilityRoute capability="website.view">
                <WebsiteRoutes />
              </CapabilityRoute>
            } />

            {/* Fiches de Travail */}
            <Route path="/worksheet/*" element={
              <CapabilityRoute capability="worksheet.view">
                <WorksheetRoutes />
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
