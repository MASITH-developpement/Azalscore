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

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import {
  Menu, X, Bell, User, LogOut, Settings, ChevronDown,
  Search, Plus, LayoutList, LayoutGrid, Database, AlertTriangle,
  FileText, Users, Package, Truck, Star, Clock
} from 'lucide-react';
import { useAuth } from '@core/auth';
import { DynamicMenu } from '@ui/menu-dynamic';
import { ErrorToaster } from '@ui/components/ErrorToaster';
import { GuardianPanelContainer } from '@ui/components/GuardianPanelContainer';
import { isDemoMode, setDemoMode } from '../utils/demoMode';
import { setInterfaceMode, getCurrentMode, type InterfaceMode } from '../utils/interfaceMode';

// ============================================================
// TYPES
// ============================================================

export type ViewKey =
  | 'saisie'
  | 'gestion-devis' | 'gestion-commandes' | 'gestion-interventions' | 'gestion-factures' | 'gestion-paiements'
  | 'affaires'
  | 'crm' | 'stock' | 'achats' | 'projets' | 'rh' | 'vehicules'
  | 'compta' | 'tresorerie'
  | 'cockpit'
  | 'admin';

interface MenuItem {
  key: ViewKey;
  label: string;
  group?: string;
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
  { key: 'gestion-devis', label: 'Devis', group: 'Gestion' },
  { key: 'gestion-commandes', label: 'Commandes', group: 'Gestion' },
  { key: 'gestion-interventions', label: 'Interventions', group: 'Gestion' },
  { key: 'gestion-factures', label: 'Factures', group: 'Gestion' },
  { key: 'gestion-paiements', label: 'Paiements', group: 'Gestion' },
  { key: 'affaires', label: 'Suivi Affaires', group: 'Affaires' },
  { key: 'crm', label: 'CRM / Clients', group: 'Modules' },
  { key: 'stock', label: 'Stock', group: 'Modules' },
  { key: 'achats', label: 'Achats', group: 'Modules' },
  { key: 'projets', label: 'Projets', group: 'Modules' },
  { key: 'rh', label: 'RH', group: 'Modules' },
  { key: 'compta', label: 'Comptabilité', group: 'Finance' },
  { key: 'tresorerie', label: 'Trésorerie', group: 'Finance' },
  { key: 'cockpit', label: 'Cockpit Dirigeant', group: 'Direction' },
  { key: 'admin', label: 'Administration', group: 'Système' },
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
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const demoMode = isDemoMode();

  const currentItem = MENU_ITEMS.find(m => m.key === currentView);

  // Grouper les items pour le dropdown
  const groups = MENU_ITEMS.reduce((acc, item) => {
    const group = item.group || 'Autre';
    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {} as Record<string, MenuItem[]>);

  const handleModeSwitch = () => {
    const newMode = mode === 'azalscore' ? 'erp' : 'azalscore';
    setInterfaceMode(newMode);
  };

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
              onClick={() => setDropdownOpen(!dropdownOpen)}
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
                        onClick={() => {
                          onViewChange(item.key);
                          setDropdownOpen(false);
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
        )}
      </div>

      {/* Right side */}
      <div className="azals-unified-header__right">
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
              <a href="/profile" className="azals-unified-header__user-item">
                <User size={16} />
                <span>Mon profil</span>
              </a>
              <a href="/settings" className="azals-unified-header__user-item">
                <Settings size={16} />
                <span>Paramètres</span>
              </a>

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
  // Grouper les items
  const groups = MENU_ITEMS.reduce((acc, item) => {
    const group = item.group || 'Autre';
    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {} as Record<string, MenuItem[]>);

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
    </div>
  );
};

export default UnifiedLayout;
