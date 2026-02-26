/**
 * AZALSCORE - Layout Unifié
 * =========================
 *
 * Un seul composant de layout avec deux modes d'affichage :
 * - Mode "azalscore" : interface simplifiée avec menu déroulant
 * - Mode "erp" : interface complète avec sidebar
 *
 * Le mode démo fonctionne sur les deux.
 *
 * FUTURE : Permettre à l'utilisateur de personnaliser son interface
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { clsx } from 'clsx';
import {
  Menu, X, Bell, User, LogOut, Settings, ChevronDown,
  LayoutList, LayoutGrid, Database, AlertTriangle,
  Sparkles
} from 'lucide-react';
import { useAuth } from '@core/auth';
import { useCapabilities } from '@core/capabilities';
import { useTheo } from '@core/theo';
import { ErrorToaster } from '@ui/components/ErrorToaster';
import { GuardianPanelContainer } from '@ui/components/GuardianPanelContainer';
import { TheoPanelContainer } from '@ui/components/TheoPanel';
import { isDemoMode, setDemoMode } from '../utils/demoMode';
import { setInterfaceMode, getCurrentMode, type InterfaceMode } from '../utils/interfaceMode';

// ============================================================
// TYPES
// ============================================================

export type ViewKey =
  | 'saisie'
  | 'gestion-devis'
  | 'gestion-commandes'
  | 'gestion-interventions'
  | 'gestion-factures'
  | 'gestion-paiements'
  | 'affaires'
  | 'accounting'
  | 'treasury'
  | 'partners'
  | 'projects'
  | 'inventory'
  | 'purchases'
  | 'hr'
  | 'production'
  | 'maintenance'
  | 'quality'
  | 'pos'
  | 'ecommerce'
  | 'helpdesk'
  | 'bi'
  | 'compliance'
  | 'ai-assistant'
  | 'assets'
  | 'contracts'
  | 'expenses'
  | 'timesheet'
  | 'field-service'
  | 'complaints'
  | 'warranty'
  | 'rfq'
  | 'procurement'
  | 'subscriptions'
  | 'marketplace'
  | 'esignature'
  | 'email'
  | 'broadcast'
  | 'web'
  | 'website'
  | 'crm'
  | 'commercial'
  | 'finance'
  | 'consolidation'
  | 'qc'
  | 'automated-accounting'
  | 'social-networks'
  | 'marceau'
  | 'cockpit'
  | 'admin'
  | 'audit'
  | 'backup'
  | 'guardian'
  | 'iam'
  | 'tenants'
  | 'triggers'
  | 'autoconfig'
  | 'hr-vault'
  | 'stripe-integration'
  | 'country-packs'
  | 'odoo-import'
  | 'import-odoo'
  | 'import-axonaut'
  | 'import-pennylane'
  | 'import-sage'
  | 'import-chorus'
  | 'profile'
  | 'settings';

interface MenuItem {
  key: ViewKey;
  label: string;
  group?: string;
  capability?: string; // Capability requise pour voir cet item
}

interface UnifiedLayoutProps {
  children: React.ReactNode;
  currentView: ViewKey;
  onViewChange: (view: ViewKey) => void;
  onLogout: () => void;
}

// ============================================================
// CONFIGURATION DU MENU
// ============================================================

const MENU_ITEMS: MenuItem[] = [
  { key: 'saisie', label: 'Nouvelle saisie', group: 'Saisie' },
  { key: 'gestion-devis', label: 'Devis', group: 'Gestion', capability: 'invoicing.view' },
  { key: 'gestion-commandes', label: 'Commandes', group: 'Gestion', capability: 'invoicing.view' },
  { key: 'gestion-interventions', label: 'Interventions', group: 'Gestion', capability: 'interventions.view' },
  { key: 'gestion-factures', label: 'Factures', group: 'Gestion', capability: 'invoicing.view' },
  { key: 'gestion-paiements', label: 'Paiements', group: 'Gestion', capability: 'payments.view' },
  { key: 'affaires', label: 'Suivi Affaires', group: 'Affaires', capability: 'projects.view' },
  { key: 'partners', label: 'CRM / Clients', group: 'Modules', capability: 'partners.view' },
  { key: 'projects', label: 'Projets', group: 'Modules', capability: 'projects.view' },
  { key: 'inventory', label: 'Stock', group: 'Modules', capability: 'inventory.view' },
  { key: 'purchases', label: 'Achats', group: 'Modules', capability: 'purchases.view' },
  { key: 'hr', label: 'Ressources Humaines', group: 'Modules', capability: 'hr.view' },
  { key: 'contracts', label: 'Contrats', group: 'Modules', capability: 'contracts.view' },
  { key: 'timesheet', label: 'Feuilles de Temps', group: 'Modules', capability: 'timesheet.view' },
  { key: 'field-service', label: 'Service Terrain', group: 'Modules', capability: 'field_service.view' },
  { key: 'complaints', label: 'Réclamations', group: 'Modules', capability: 'complaints.view' },
  { key: 'warranty', label: 'Garanties', group: 'Modules', capability: 'warranty.view' },
  { key: 'rfq', label: 'Appels d\'Offres', group: 'Modules', capability: 'rfq.view' },
  { key: 'procurement', label: 'Approvisionnement', group: 'Modules', capability: 'procurement.view' },
  { key: 'crm', label: 'CRM Avancé', group: 'Modules', capability: 'crm.view' },
  { key: 'production', label: 'Production', group: 'Logistique', capability: 'production.view' },
  { key: 'maintenance', label: 'Maintenance', group: 'Logistique', capability: 'maintenance.view' },
  { key: 'quality', label: 'Qualité', group: 'Logistique', capability: 'quality.view' },
  { key: 'qc', label: 'Contrôle Qualité', group: 'Logistique', capability: 'qc.view' },
  { key: 'pos', label: 'Point de Vente', group: 'Commerce', capability: 'pos.view' },
  { key: 'ecommerce', label: 'E-commerce', group: 'Commerce', capability: 'ecommerce.view' },
  { key: 'subscriptions', label: 'Abonnements', group: 'Commerce', capability: 'subscriptions.view' },
  { key: 'marketplace', label: 'Marketplace', group: 'Commerce', capability: 'marketplace.view' },
  { key: 'commercial', label: 'Commercial', group: 'Commerce', capability: 'commercial.view' },
  { key: 'helpdesk', label: 'Support Client', group: 'Services', capability: 'helpdesk.view' },
  { key: 'bi', label: 'Reporting & BI', group: 'Digital', capability: 'bi.view' },
  { key: 'compliance', label: 'Conformité', group: 'Digital', capability: 'compliance.view' },
  { key: 'broadcast', label: 'Diffusion', group: 'Digital', capability: 'broadcast.view' },
  { key: 'web', label: 'Site Web', group: 'Digital', capability: 'web.view' },
  { key: 'website', label: 'Site Web Builder', group: 'Digital', capability: 'website.view' },
  { key: 'social-networks', label: 'Réseaux Sociaux', group: 'Digital', capability: 'social_networks.view' },
  { key: 'esignature', label: 'Signature Électronique', group: 'Communication', capability: 'esignature.view' },
  { key: 'email', label: 'Emails', group: 'Communication', capability: 'email.view' },
  { key: 'accounting', label: 'Comptabilité', group: 'Finance', capability: 'accounting.view' },
  { key: 'treasury', label: 'Trésorerie', group: 'Finance', capability: 'treasury.view' },
  { key: 'assets', label: 'Immobilisations', group: 'Finance', capability: 'assets.view' },
  { key: 'expenses', label: 'Notes de Frais', group: 'Finance', capability: 'expenses.view' },
  { key: 'finance', label: 'Finance', group: 'Finance', capability: 'finance.view' },
  { key: 'consolidation', label: 'Consolidation', group: 'Finance', capability: 'consolidation.view' },
  { key: 'automated-accounting', label: 'Comptabilité Auto', group: 'Finance', capability: 'automated_accounting.view' },
  { key: 'cockpit', label: 'Cockpit Dirigeant', group: 'Direction', capability: 'cockpit.view' },
  { key: 'ai-assistant', label: 'Assistant IA', group: 'IA', capability: 'ai_assistant.view' },
  { key: 'marceau', label: 'Marceau IA', group: 'IA', capability: 'marceau.view' },
  { key: 'admin', label: 'Administration', group: 'Système', capability: 'admin.view' },
  { key: 'audit', label: 'Audit & Logs', group: 'Système', capability: 'audit.view' },
  { key: 'backup', label: 'Sauvegardes', group: 'Système', capability: 'backup.view' },
  { key: 'guardian', label: 'Sécurité', group: 'Système', capability: 'guardian.view' },
  { key: 'iam', label: 'Gestion des Accès', group: 'Système', capability: 'iam.view' },
  { key: 'tenants', label: 'Multi-Tenants', group: 'Système', capability: 'tenants.view' },
  { key: 'triggers', label: 'Automatisations', group: 'Système', capability: 'triggers.view' },
  { key: 'autoconfig', label: 'Configuration Auto', group: 'Système', capability: 'autoconfig.view' },
  { key: 'hr-vault', label: 'Coffre-fort RH', group: 'Système', capability: 'hr_vault.view' },
  { key: 'stripe-integration', label: 'Intégration Stripe', group: 'Système', capability: 'stripe_integration.view' },
  { key: 'country-packs', label: 'Packs Pays', group: 'Système', capability: 'country_packs.view' },
  { key: 'import-odoo', label: 'Import Odoo', group: 'Import', capability: 'import_data.odoo' },
  { key: 'import-axonaut', label: 'Import Axonaut', group: 'Import', capability: 'import_data.axonaut' },
  { key: 'import-pennylane', label: 'Import Pennylane', group: 'Import', capability: 'import_data.pennylane' },
  { key: 'import-sage', label: 'Import Sage', group: 'Import', capability: 'import_data.sage' },
  { key: 'import-chorus', label: 'Import Chorus', group: 'Import', capability: 'import_data.chorus' },
];

// ============================================================
// HEADER COMPONENT (Partagé entre les deux modes)
// ============================================================

interface HeaderProps {
  mode: InterfaceMode;
  currentView: ViewKey;
  onViewChange: (view: ViewKey) => void;
  onLogout: () => void;
  onMenuToggle?: () => void;
  isMobileMenuOpen?: boolean;
}

const Header: React.FC<HeaderProps> = ({
  mode,
  currentView,
  onViewChange,
  onLogout,
  onMenuToggle,
  isMobileMenuOpen = false,
}) => {
  const { user } = useAuth();
  const { capabilities } = useCapabilities();
  const { toggle: toggleTheo, isOpen: isTheoOpen } = useTheo();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const demoMode = isDemoMode();

  const currentItem = useMemo(
    () => MENU_ITEMS.find(m => m.key === currentView),
    [currentView]
  );

  // Filtrer les items selon les capabilities (mémorisé pour éviter recalcul)
  const visibleItems = useMemo(() => {
    return MENU_ITEMS.filter(item => {
      if (!item.capability) return true;
      return capabilities.includes(item.capability);
    });
  }, [capabilities]);

  // Grouper les items filtrés pour le dropdown (mémorisé)
  const groups = useMemo(() => {
    return visibleItems.reduce((acc, item) => {
      const group = item.group || 'Autre';
      if (!acc[group]) acc[group] = [];
      acc[group].push(item);
      return acc;
    }, {} as Record<string, MenuItem[]>);
  }, [visibleItems]);

  // Handlers mémorisés pour éviter re-renders enfants
  const handleModeSwitch = useCallback(() => {
    const newMode = mode === 'azalscore' ? 'erp' : 'azalscore';
    setInterfaceMode(newMode);
  }, [mode]);

  const toggleDropdown = useCallback(() => {
    setDropdownOpen(prev => !prev);
  }, []);

  const handleItemClick = useCallback((key: ViewKey) => {
    onViewChange(key);
    setDropdownOpen(false);
  }, [onViewChange]);

  return (
    <header className={clsx('azals-unified-header', {
      'azals-unified-header--demo': demoMode,
      'azals-unified-header--erp': mode === 'erp',
      'azals-unified-header--azalscore': mode === 'azalscore',
    })}>
      {/* Left side */}
      <div className="azals-unified-header__left">
        {/* Mobile menu toggle (ERP mode only) */}
        {mode === 'erp' && (
          <button
            className="azals-unified-header__menu-toggle"
            onClick={onMenuToggle}
            aria-label={isMobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        )}

        <div className="azals-unified-header__logo">AZALSCORE</div>

        {/* Module selector (Azalscore mode) */}
        {mode === 'azalscore' && (
          <div className="azals-unified-header__selector-container">
            <button
              className="azals-unified-header__selector"
              onClick={toggleDropdown}
            >
              <span>{currentItem?.label || 'Sélectionner'}</span>
              <ChevronDown size={18} className={dropdownOpen ? 'rotate' : ''} />
            </button>

            {dropdownOpen && (
              <div className="azals-unified-header__dropdown">
                {Object.entries(groups).map(([groupName, items]) => (
                  <div key={groupName} className="azals-unified-header__group">
                    <div className="azals-unified-header__group-label">{groupName}</div>
                    {items.map((item) => (
                      <button
                        key={item.key}
                        className={clsx('azals-unified-header__item', {
                          'azals-unified-header__item--active': currentView === item.key
                        })}
                        onClick={() => handleItemClick(item.key)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right side */}
      <div className="azals-unified-header__right">
        {/* Assistance IA Theo */}
        <button
          className={clsx('azals-unified-header__icon-btn azals-unified-header__theo-btn', {
            'azals-unified-header__theo-btn--active': isTheoOpen
          })}
          onClick={toggleTheo}
          aria-label="Assistance IA"
          title="Assistance IA Theo"
        >
          <Sparkles size={20} />
        </button>

        {/* Notifications */}
        <button className="azals-unified-header__icon-btn" aria-label="Notifications">
          <Bell size={20} />
        </button>

        {/* User Menu */}
        <div className="azals-unified-header__user-menu">
          <button
            className="azals-unified-header__user-btn"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <User size={20} />
            {user?.name && <span className="azals-unified-header__user-name">{user.name}</span>}
            <ChevronDown size={14} className={userMenuOpen ? 'rotate' : ''} />
          </button>

          {userMenuOpen && (
            <div className="azals-unified-header__user-dropdown">
              <button
                className="azals-unified-header__user-item"
                onClick={() => {
                  onViewChange('profile' as ViewKey);
                  setUserMenuOpen(false);
                }}
              >
                <User size={16} />
                <span>Mon profil</span>
              </button>
              <button
                className="azals-unified-header__user-item"
                onClick={() => {
                  onViewChange('settings' as ViewKey);
                  setUserMenuOpen(false);
                }}
              >
                <Settings size={16} />
                <span>Paramètres</span>
              </button>

              <hr className="azals-unified-header__divider" />

              {/* Mode switch */}
              <button
                className="azals-unified-header__user-item"
                onClick={handleModeSwitch}
              >
                {mode === 'azalscore' ? <LayoutGrid size={16} /> : <LayoutList size={16} />}
                <span>{mode === 'azalscore' ? 'Mode ERP complet' : 'Mode AZALSCORE'}</span>
              </button>

              {/* Demo mode toggle */}
              <button
                className={clsx('azals-unified-header__user-item', {
                  'azals-unified-header__user-item--active': demoMode
                })}
                onClick={() => setDemoMode(!demoMode)}
              >
                <Database size={16} />
                <span>{demoMode ? 'Désactiver démo' : 'Activer démo'}</span>
              </button>

              <hr className="azals-unified-header__divider" />

              <button
                className="azals-unified-header__user-item azals-unified-header__user-item--danger"
                onClick={onLogout}
              >
                <LogOut size={16} />
                <span>Déconnexion</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

// ============================================================
// SIDEBAR COMPONENT (ERP mode only)
// ============================================================

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: ViewKey;
  onViewChange: (view: ViewKey) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, currentView, onViewChange }) => {
  const { capabilities } = useCapabilities();

  // Filtrer les items selon les capabilities (mémorisé)
  const visibleItems = useMemo(() => {
    return MENU_ITEMS.filter(item => {
      if (!item.capability) return true;
      return capabilities.includes(item.capability);
    });
  }, [capabilities]);

  // Grouper les items filtrés (mémorisé)
  const groups = useMemo(() => {
    return visibleItems.reduce((acc, item) => {
      const group = item.group || 'Autre';
      if (!acc[group]) acc[group] = [];
      acc[group].push(item);
      return acc;
    }, {} as Record<string, MenuItem[]>);
  }, [visibleItems]);

  return (
    <>
      {/* Overlay mobile */}
      {isOpen && (
        <div
          className="azals-unified-sidebar__overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside className={clsx('azals-unified-sidebar', { 'azals-unified-sidebar--open': isOpen })}>
        <nav className="azals-unified-sidebar__nav">
          {Object.entries(groups).map(([groupName, items]) => (
            <div key={groupName} className="azals-unified-sidebar__group">
              <div className="azals-unified-sidebar__group-label">{groupName}</div>
              {items.map((item) => (
                <button
                  key={item.key}
                  className={clsx('azals-unified-sidebar__item', {
                    'azals-unified-sidebar__item--active': currentView === item.key
                  })}
                  onClick={() => {
                    onViewChange(item.key);
                    onClose();
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="azals-unified-sidebar__footer">
          <span className="azals-unified-sidebar__version">v1.0.0</span>
        </div>
      </aside>
    </>
  );
};

// ============================================================
// DEMO BANNER
// ============================================================

const DemoBanner: React.FC = () => (
  <div className="azals-demo-banner">
    <AlertTriangle size={16} className="azals-demo-banner__icon" />
    MODE DEMONSTRATION - Lecture seule - Aucun enregistrement possible
  </div>
);

// ============================================================
// UNIFIED LAYOUT COMPONENT
// ============================================================

export const UnifiedLayout: React.FC<UnifiedLayoutProps> = ({
  children,
  currentView,
  onViewChange,
  onLogout,
}) => {
  const mode = getCurrentMode();
  const demoMode = isDemoMode();
  const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMenu = useCallback(() => {
    setMobileMenuOpen(prev => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);

  // Listen for custom navigation events from child modules
  useEffect(() => {
    const handleNavigate = (e: CustomEvent<{ view: string }>) => {
      const view = e.detail.view as ViewKey;
      if (view) onViewChange(view);
    };
    window.addEventListener('azals:navigate', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate', handleNavigate as EventListener);
  }, [onViewChange]);

  return (
    <div className={clsx('azals-unified-layout', {
      'azals-unified-layout--demo': demoMode,
      'azals-unified-layout--erp': mode === 'erp',
      'azals-unified-layout--azalscore': mode === 'azalscore',
    })}>
      <Header
        mode={mode}
        currentView={currentView}
        onViewChange={onViewChange}
        onLogout={onLogout}
        onMenuToggle={toggleMenu}
        isMobileMenuOpen={isMobileMenuOpen}
      />

      {/* Demo banner */}
      {demoMode && <DemoBanner />}

      <div className="azals-unified-layout__body">
        {/* Sidebar (ERP mode only) */}
        {mode === 'erp' && (
          <Sidebar
            isOpen={isMobileMenuOpen}
            onClose={closeMenu}
            currentView={currentView}
            onViewChange={onViewChange}
          />
        )}

        {/* Main content */}
        <main className="azals-unified-main">
          <div className="azals-unified-main__content">
            {children}
          </div>
        </main>
      </div>

      <ErrorToaster />
      <GuardianPanelContainer />
      <TheoPanelContainer />
    </div>
  );
};

export default UnifiedLayout;
