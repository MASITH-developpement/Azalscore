/**
 * AZALSCORE UI Engine - Layout System
 * Structure de mise en page responsive Web + Mobile
 */

import React, { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { clsx } from 'clsx';
import { Menu, X, Bell, User, LogOut, Settings } from 'lucide-react';
import { useAuth } from '@core/auth';
import { useCapabilities } from '@core/capabilities';
import { DynamicMenu } from '@ui/menu-dynamic';
import { ErrorToaster } from '@ui/components/ErrorToaster';

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

  const handleLogout = useCallback(async () => {
    await logout();
  }, [logout]);

  return (
    <header className="azals-header">
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
  const { isLoading: isCapLoading } = useCapabilities();

  const toggleMenu = useCallback(() => {
    setMobileMenuOpen((prev) => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);

  if (isCapLoading) {
    return (
      <div className="azals-layout__loading">
        <div className="azals-spinner" />
        <p>Chargement...</p>
      </div>
    );
  }

  return (
    <div className="azals-layout">
      <Header onMenuToggle={toggleMenu} isMobileMenuOpen={isMobileMenuOpen} />

      <div className="azals-layout__body">
        <Sidebar isOpen={isMobileMenuOpen} onClose={closeMenu} />

        <main className="azals-main">
          <div className="azals-main__content">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      <ErrorToaster />
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
}

export const PageWrapper: React.FC<PageWrapperProps> = ({
  title,
  subtitle,
  actions,
  children,
}) => {
  return (
    <div className="azals-page">
      <header className="azals-page__header">
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
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  actions,
  children,
  className,
  noPadding,
}) => {
  return (
    <div className={clsx('azals-card', className)}>
      {(title || actions) && (
        <div className="azals-card__header">
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
  gap?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const Grid: React.FC<GridProps> = ({
  cols = 1,
  gap = 'md',
  children,
}) => {
  return (
    <div
      className={clsx('azals-grid', `azals-grid--cols-${cols}`, `azals-grid--gap-${gap}`)}
    >
      {children}
    </div>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default MainLayout;
