/**
 * AZALSCORE UI Engine - Layout System
 * Structure de mise en page responsive Web + Mobile
 */

import React, { useState, useCallback, useEffect } from 'react';
import { clsx } from 'clsx';
import { Menu, X, Bell, User, LogOut, Settings, LayoutList, Monitor, Database, AlertTriangle } from 'lucide-react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '@core/auth';
import { useCapabilities } from '@core/capabilities';
import { MarceauChat } from '@modules/marceau/components/MarceauChat';
import { CommandPalette } from '@ui/command-palette';
import { ErrorToaster } from '@ui/components/ErrorToaster';
import { GuardianPanelContainer } from '@ui/components/GuardianPanelContainer';
import { useUIMode } from '@ui/hooks/useUIMode';
import { DynamicMenu } from '@ui/menu-dynamic';
import { TopMenu } from '@ui/top-menu';
import { isDemoMode, setDemoMode } from '../../utils/demoMode';

// ============================================================
// TYPES
// ============================================================

interface LayoutProps {
  children?: React.ReactNode;
}

// ============================================================
// HEADER COMPONENT
// ============================================================

const Header: React.FC<{
  onMenuToggle: () => void;
  isMobileMenuOpen: boolean;
}> = ({ onMenuToggle, isMobileMenuOpen }) => {
  const { user, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { mode: _mode, setMode, isAzalscore, isERP } = useUIMode();

  const handleLogout = useCallback(async () => {
    await logout();
  }, [logout]);

  const demoMode = isDemoMode();

  return (
    <header className={clsx('azals-header', { 'azals-header--demo': demoMode })}>
      <div className="azals-header__left">
        <button
          className="azals-header__menu-toggle"
          onClick={onMenuToggle}
          aria-label={isMobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <div className="azals-header__logo">
          <span className="azals-header__logo-text">AZALSCORE</span>
          {isERP && <span className="azals-header__mode-badge">ERP</span>}
        </div>
      </div>

      <div className="azals-header__right">
        {/* Notifications */}
        <button className="azals-header__icon-btn" aria-label="Notifications">
          <Bell size={20} />
          <span className="azals-header__badge">3</span>
        </button>

        {/* User Menu */}
        <div className="azals-header__user-menu">
          <button
            className="azals-header__user-btn"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            aria-expanded={userMenuOpen}
          >
            <User size={20} />
            <span className="azals-header__user-name">{user?.name}</span>
          </button>

          {userMenuOpen && (
            <div className="azals-header__dropdown">
              <a href="/profile" className="azals-header__dropdown-item">
                <User size={16} />
                <span>Mon profil</span>
              </a>
              <a href="/settings" className="azals-header__dropdown-item">
                <Settings size={16} />
                <span>Paramètres</span>
              </a>
              <hr className="azals-header__dropdown-divider" />
              <div className="azals-header__dropdown-label">Mode d&apos;interface</div>
              <button
                className={clsx('azals-header__dropdown-item', { 'azals-header__dropdown-item--active': isAzalscore })}
                onClick={() => setMode('azalscore')}
              >
                <LayoutList size={16} />
                <span>Mode AZALSCORE</span>
              </button>
              <button
                className={clsx('azals-header__dropdown-item', { 'azals-header__dropdown-item--active': isERP })}
                onClick={() => setMode('erp')}
              >
                <Monitor size={16} />
                <span>Mode ERP</span>
              </button>
              <hr className="azals-header__dropdown-divider" />
              <button
                className={clsx('azals-header__dropdown-item', { 'azals-header__dropdown-item--active': demoMode })}
                onClick={() => setDemoMode(!demoMode)}
              >
                <Database size={16} />
                <span>{demoMode ? 'Désactiver démo' : 'Activer démo'}</span>
              </button>
              <hr className="azals-header__dropdown-divider" />
              <button
                className="azals-header__dropdown-item azals-header__dropdown-item--danger"
                onClick={handleLogout}
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
// SIDEBAR COMPONENT
// ============================================================

const Sidebar: React.FC<{
  isOpen: boolean;
  onClose: () => void;
}> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Overlay mobile */}
      {isOpen && (
        <div
          className="azals-sidebar__overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={clsx('azals-sidebar', {
          'azals-sidebar--open': isOpen,
        })}
      >
        <nav className="azals-sidebar__nav">
          <DynamicMenu onItemClick={onClose} />
        </nav>

        <div className="azals-sidebar__footer">
          <span className="azals-sidebar__version">v1.0.0</span>
        </div>
      </aside>
    </>
  );
};

// ============================================================
// MAIN LAYOUT COMPONENT
// ============================================================

export const MainLayout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isCommandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const { isLoading: isCapLoading } = useCapabilities();
  const { mode, isAzalscore } = useUIMode();
  const demoMode = isDemoMode();

  const toggleMenu = useCallback(() => {
    setMobileMenuOpen((prev) => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);

  const openCommandPalette = useCallback(() => {
    setCommandPaletteOpen(true);
  }, []);

  const closeCommandPalette = useCallback(() => {
    setCommandPaletteOpen(false);
  }, []);

  // Raccourcis clavier pour la Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K ou /
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openCommandPalette();
      } else if (e.key === '/' && !isCommandPaletteOpen) {
        // Ignorer si focus dans un input
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

        e.preventDefault();
        openCommandPalette();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openCommandPalette, isCommandPaletteOpen]);

  if (isCapLoading) {
    return (
      <div className="azals-layout__loading" data-ui-mode={mode}>
        <div className="azals-spinner" />
        <p>Chargement...</p>
      </div>
    );
  }

  return (
    <div
      className={clsx('azals-layout', { 'azals-layout--demo': demoMode })}
      data-ui-mode={mode}
    >
      <Header onMenuToggle={toggleMenu} isMobileMenuOpen={isMobileMenuOpen} />

      {/* Bannière mode démo */}
      {demoMode && (
        <div className="azals-demo-banner">
          <AlertTriangle size={16} className="azals-demo-banner__icon" />
          MODE DEMONSTRATION - Lecture seule - Aucun enregistrement possible
        </div>
      )}

      {/* Top Menu (Mode AZALSCORE uniquement) */}
      {isAzalscore && <TopMenu onCommandPaletteOpen={openCommandPalette} />}

      <div className="azals-layout__body">
        {/* Sidebar (Mode ERP uniquement) */}
        {!isAzalscore && <Sidebar isOpen={isMobileMenuOpen} onClose={closeMenu} />}

        <main className="azals-main">
          <div className="azals-main__content">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette isOpen={isCommandPaletteOpen} onClose={closeCommandPalette} />

      <ErrorToaster />
      <GuardianPanelContainer />

      {/* Marceau AI Chat Widget */}
      <MarceauChat position="bottom-right" />
    </div>
  );
};

// ============================================================
// AUTH LAYOUT (LOGIN, 2FA, etc.)
// ============================================================

export const AuthLayout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="azals-auth-layout">
      <div className="azals-auth-layout__container">
        <div className="azals-auth-layout__logo">
          <span className="azals-auth-layout__logo-text">AZALSCORE</span>
          <span className="azals-auth-layout__logo-subtitle">ERP SaaS</span>
        </div>

        <div className="azals-auth-layout__card">
          {children || <Outlet />}
        </div>

        <div className="azals-auth-layout__footer">
          <p>&copy; 2026 MASITH - Tous droits réservés</p>
        </div>
      </div>

      <ErrorToaster />
    </div>
  );
};

// ============================================================
// PAGE WRAPPER
// ============================================================

interface PageWrapperProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  backAction?: {
    label: string;
    onClick: () => void;
  };
}

export const PageWrapper: React.FC<PageWrapperProps> = ({
  title,
  subtitle,
  actions,
  children,
  backAction,
}) => {
  return (
    <div className="azals-page">
      <header className="azals-page__header">
        {backAction && (
          <button
            className="azals-page__back-btn azals-btn azals-btn--ghost"
            onClick={backAction.onClick}
          >
            ← {backAction.label}
          </button>
        )}
        <div className="azals-page__header-text">
          <h1 className="azals-page__title">{title}</h1>
          {subtitle && <p className="azals-page__subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="azals-page__actions">{actions}</div>}
      </header>

      <div className="azals-page__body">{children}</div>
    </div>
  );
};

// ============================================================
// CARD COMPONENT
// ============================================================

interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
  icon?: React.ReactNode;
  style?: React.CSSProperties;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  actions,
  children,
  className,
  noPadding,
  icon,
  style,
  onClick,
}) => {
  return (
    <div
      className={clsx('azals-card', className, { 'azals-card--clickable': !!onClick })}
      style={style}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
    >
      {(title || actions || icon) && (
        <div className="azals-card__header">
          {icon && <div className="azals-card__icon">{icon}</div>}
          <div className="azals-card__header-text">
            {title && <h2 className="azals-card__title">{title}</h2>}
            {subtitle && <p className="azals-card__subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="azals-card__actions">{actions}</div>}
        </div>
      )}
      <div
        className={clsx('azals-card__body', {
          'azals-card__body--no-padding': noPadding,
        })}
      >
        {children}
      </div>
    </div>
  );
};

// ============================================================
// GRID SYSTEM
// ============================================================

interface GridProps {
  cols?: 1 | 2 | 3 | 4;
  columns?: 1 | 2 | 3 | 4; // Alias pour cols
  gap?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

export const Grid: React.FC<GridProps> = ({
  cols,
  columns,
  gap = 'md',
  children,
  className,
}) => {
  const colCount = cols ?? columns ?? 1;
  return (
    <div
      className={clsx('azals-grid', `azals-grid--cols-${colCount}`, `azals-grid--gap-${gap}`, className)}
    >
      {children}
    </div>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default MainLayout;
