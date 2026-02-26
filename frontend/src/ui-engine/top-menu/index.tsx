/**
 * AZALSCORE UI Engine - Top Menu (Mode AZALSCORE)
 * Menu horizontal minimaliste avec 4 items max
 * Cockpit visible uniquement pour dirigeant + admin
 */

import React, { useState } from 'react';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Zap,
  LayoutGrid,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@core/auth';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// TYPES
// ============================================================

interface TopMenuProps {
  onCommandPaletteOpen?: () => void;
}

// ============================================================
// HELPER: Vérifier si l'utilisateur peut voir le Cockpit
// ============================================================

const useCanViewCockpit = () => {
  const { user } = useAuth();
  const { capabilities } = useCapabilities();

  // Cockpit visible uniquement pour:
  // - Utilisateurs avec capacité 'cockpit.view'
  // - Rôles: dirigeant, admin, superadmin
  const canView = React.useMemo(() => {
    if (!user) return false;

    // Vérifier les capacités
    if (capabilities.includes('cockpit.view')) return true;

    // Vérifier les rôles
    const allowedRoles = ['dirigeant', 'admin', 'superadmin', 'root'];
    return user.roles?.some((role: string) => allowedRoles.includes(role.toLowerCase())) ?? false;
  }, [user, capabilities]);

  return canView;
};

// ============================================================
// ACTIONS DROPDOWN
// ============================================================

const ActionsDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { capabilities } = useCapabilities();

  const quickActions = [
    { label: 'Nouvelle facture', path: '/invoicing/invoices/new', capability: 'invoicing.create' },
    { label: 'Nouveau devis', path: '/invoicing/quotes/new', capability: 'invoicing.create' },
    { label: 'Nouveau client', path: '/partners/clients/new', capability: 'partners.create' },
    { label: 'Nouvelle dépense', path: '/purchases/expenses/new', capability: 'purchases.create' },
    { label: 'Nouveau projet', path: '/projects/new', capability: 'projects.create' },
  ].filter(action => !action.capability || capabilities.includes(action.capability));

  return (
    <div className="azals-topmenu__dropdown-wrapper">
      <button
        className={clsx('azals-topmenu__item', {
          'azals-topmenu__item--active': isOpen,
        })}
        onClick={() => setIsOpen(!isOpen)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
      >
        <Zap size={20} className="azals-topmenu__icon" />
        <span>Actions</span>
        <ChevronDown size={16} className="azals-topmenu__chevron" />
      </button>

      {isOpen && (
        <div className="azals-topmenu__dropdown">
          {quickActions.map((action) => (
            <NavLink
              key={action.path}
              to={action.path}
              className="azals-topmenu__dropdown-item"
              onClick={() => setIsOpen(false)}
            >
              {action.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================
// VUE D'ENSEMBLE DROPDOWN
// ============================================================

const OverviewDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { capabilities } = useCapabilities();

  const sections = [
    {
      title: 'Gestion',
      items: [
        { label: 'Partenaires', path: '/partners', capability: 'partners.view' },
        { label: 'Facturation', path: '/invoicing', capability: 'invoicing.view' },
        { label: 'Achats', path: '/purchases', capability: 'purchases.view' },
      ],
    },
    {
      title: 'Finance',
      items: [
        { label: 'Trésorerie', path: '/treasury', capability: 'treasury.view' },
        { label: 'Comptabilité', path: '/accounting', capability: 'accounting.view' },
      ],
    },
    {
      title: 'Opérations',
      items: [
        { label: 'Projets', path: '/projects', capability: 'projects.view' },
        { label: 'Interventions', path: '/interventions', capability: 'interventions.view' },
        { label: 'Inventaire', path: '/inventory', capability: 'inventory.view' },
      ],
    },
  ];

  return (
    <div className="azals-topmenu__dropdown-wrapper">
      <button
        className={clsx('azals-topmenu__item', {
          'azals-topmenu__item--active': isOpen,
        })}
        onClick={() => setIsOpen(!isOpen)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
      >
        <LayoutGrid size={20} className="azals-topmenu__icon" />
        <span>Vue d&apos;ensemble</span>
        <ChevronDown size={16} className="azals-topmenu__chevron" />
      </button>

      {isOpen && (
        <div className="azals-topmenu__dropdown azals-topmenu__dropdown--wide">
          <div className="azals-topmenu__dropdown-sections">
            {sections.map((section) => {
              const visibleItems = section.items.filter(
                (item) => !item.capability || capabilities.includes(item.capability)
              );

              if (visibleItems.length === 0) return null;

              return (
                <div key={section.title} className="azals-topmenu__dropdown-section">
                  <h4 className="azals-topmenu__dropdown-section-title">{section.title}</h4>
                  {visibleItems.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className="azals-topmenu__dropdown-item"
                      onClick={() => setIsOpen(false)}
                    >
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// TOP MENU COMPONENT
// ============================================================

export const TopMenu: React.FC<TopMenuProps> = ({ onCommandPaletteOpen: _onCommandPaletteOpen }) => {
  const canViewCockpit = useCanViewCockpit();

  return (
    <nav className="azals-topmenu">
      <div className="azals-topmenu__container">
        {/* Cockpit (uniquement dirigeant + admin) */}
        {canViewCockpit && (
          <NavLink
            to="/cockpit"
            className={({ isActive }) =>
              clsx('azals-topmenu__item', {
                'azals-topmenu__item--active': isActive,
              })
            }
          >
            <LayoutDashboard size={20} className="azals-topmenu__icon" />
            <span>Cockpit</span>
          </NavLink>
        )}

        {/* Actions (dropdown) */}
        <ActionsDropdown />

        {/* Vue d'ensemble (dropdown) */}
        <OverviewDropdown />

        {/* Paramètres */}
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            clsx('azals-topmenu__item', {
              'azals-topmenu__item--active': isActive,
            })
          }
        >
          <Settings size={20} className="azals-topmenu__icon" />
          <span className="azals-topmenu__label-desktop">Paramètres</span>
        </NavLink>
      </div>

      {/* Hint pour la palette de commandes */}
      <div className="azals-topmenu__hint">
        <kbd>/</kbd> ou <kbd>⌘K</kbd> pour rechercher
      </div>
    </nav>
  );
};

export default TopMenu;
