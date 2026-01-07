/**
 * AZALSCORE UI Engine - Dynamic Menu System
 * Menus générés dynamiquement selon les capacités backend
 * AUCUNE décision d'accès côté UI - uniquement affichage
 */

import React, { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Users,
  FileText,
  Wallet,
  Calculator,
  ShoppingCart,
  FolderKanban,
  Wrench,
  Globe,
  Store,
  CreditCard,
  Smartphone,
  Settings,
  Shield,
  ChevronDown,
  ChevronRight,
  type LucideIcon,
} from 'lucide-react';
import { useCapabilities, CapabilityGuard } from '@core/capabilities';
import type { MenuItem, MenuSection } from '@/types';

// ============================================================
// ICON MAP
// ============================================================

const ICON_MAP: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  users: Users,
  invoicing: FileText,
  treasury: Wallet,
  accounting: Calculator,
  purchases: ShoppingCart,
  projects: FolderKanban,
  interventions: Wrench,
  web: Globe,
  ecommerce: Store,
  payments: CreditCard,
  mobile: Smartphone,
  settings: Settings,
  admin: Shield,
};

// ============================================================
// MENU CONFIGURATION
// ============================================================

const MENU_SECTIONS: MenuSection[] = [
  {
    id: 'main',
    title: 'Principal',
    items: [
      {
        id: 'cockpit',
        label: 'Cockpit Dirigeant',
        icon: 'dashboard',
        path: '/cockpit',
        capability: 'cockpit.view',
      },
    ],
  },
  {
    id: 'gestion',
    title: 'Gestion',
    items: [
      {
        id: 'partners',
        label: 'Partenaires',
        icon: 'users',
        path: '/partners',
        capability: 'partners.view',
        children: [
          { id: 'clients', label: 'Clients', path: '/partners/clients' },
          { id: 'suppliers', label: 'Fournisseurs', path: '/partners/suppliers' },
          { id: 'contacts', label: 'Contacts', path: '/partners/contacts' },
        ],
      },
      {
        id: 'invoicing',
        label: 'Facturation',
        icon: 'invoicing',
        path: '/invoicing',
        capability: 'invoicing.view',
        children: [
          { id: 'quotes', label: 'Devis', path: '/invoicing/quotes' },
          { id: 'invoices', label: 'Factures', path: '/invoicing/invoices' },
          { id: 'credits', label: 'Avoirs', path: '/invoicing/credits' },
        ],
      },
      {
        id: 'purchases',
        label: 'Achats',
        icon: 'purchases',
        path: '/purchases',
        capability: 'purchases.view',
        children: [
          { id: 'orders', label: 'Commandes', path: '/purchases/orders' },
          { id: 'receipts', label: 'Réceptions', path: '/purchases/receipts' },
          { id: 'supplier-invoices', label: 'Factures fournisseurs', path: '/purchases/invoices' },
        ],
      },
    ],
  },
  {
    id: 'finance',
    title: 'Finance',
    items: [
      {
        id: 'treasury',
        label: 'Trésorerie',
        icon: 'treasury',
        path: '/treasury',
        capability: 'treasury.view',
        children: [
          { id: 'bank-accounts', label: 'Comptes bancaires', path: '/treasury/accounts' },
          { id: 'transactions', label: 'Transactions', path: '/treasury/transactions' },
          { id: 'reconciliation', label: 'Rapprochement', path: '/treasury/reconciliation' },
          { id: 'forecast', label: 'Prévisions', path: '/treasury/forecast' },
        ],
      },
      {
        id: 'accounting',
        label: 'Comptabilité',
        icon: 'accounting',
        path: '/accounting',
        capability: 'accounting.view',
        children: [
          { id: 'journal', label: 'Journal', path: '/accounting/journal' },
          { id: 'ledger', label: 'Grand livre', path: '/accounting/ledger' },
          { id: 'balance', label: 'Balance', path: '/accounting/balance' },
          { id: 'reports', label: 'États financiers', path: '/accounting/reports' },
        ],
      },
    ],
  },
  {
    id: 'operations',
    title: 'Opérations',
    items: [
      {
        id: 'projects',
        label: 'Projets',
        icon: 'projects',
        path: '/projects',
        capability: 'projects.view',
        children: [
          { id: 'project-list', label: 'Liste projets', path: '/projects/list' },
          { id: 'tasks', label: 'Tâches', path: '/projects/tasks' },
          { id: 'timesheet', label: 'Feuilles de temps', path: '/projects/timesheet' },
        ],
      },
      {
        id: 'interventions',
        label: 'Interventions',
        icon: 'interventions',
        path: '/interventions',
        capability: 'interventions.view',
        children: [
          { id: 'tickets', label: 'Tickets', path: '/interventions/tickets' },
          { id: 'planning', label: 'Planning', path: '/interventions/planning' },
          { id: 'reports', label: 'Rapports', path: '/interventions/reports' },
        ],
      },
    ],
  },
  {
    id: 'digital',
    title: 'Digital',
    items: [
      {
        id: 'web',
        label: 'Site Web',
        icon: 'web',
        path: '/web',
        capability: 'web.view',
        children: [
          { id: 'pages', label: 'Pages', path: '/web/pages' },
          { id: 'blog', label: 'Blog', path: '/web/blog' },
          { id: 'seo', label: 'SEO', path: '/web/seo' },
        ],
      },
      {
        id: 'ecommerce',
        label: 'E-commerce',
        icon: 'ecommerce',
        path: '/ecommerce',
        capability: 'ecommerce.view',
        children: [
          { id: 'products', label: 'Produits', path: '/ecommerce/products' },
          { id: 'orders', label: 'Commandes', path: '/ecommerce/orders' },
          { id: 'shipping', label: 'Expéditions', path: '/ecommerce/shipping' },
        ],
      },
      {
        id: 'marketplace',
        label: 'Marketplace',
        icon: 'ecommerce',
        path: '/marketplace',
        capability: 'marketplace.view',
      },
      {
        id: 'payments',
        label: 'Paiements',
        icon: 'payments',
        path: '/payments',
        capability: 'payments.view',
        children: [
          { id: 'online', label: 'Paiements en ligne', path: '/payments/online' },
          { id: 'tap-to-pay', label: 'Tap-to-Pay', path: '/payments/tap-to-pay' },
          { id: 'history', label: 'Historique', path: '/payments/history' },
        ],
      },
    ],
  },
  {
    id: 'admin',
    title: 'Administration',
    capability: 'admin.view',
    items: [
      {
        id: 'admin-users',
        label: 'Utilisateurs',
        icon: 'users',
        path: '/admin/users',
        capability: 'admin.users.view',
      },
      {
        id: 'admin-roles',
        label: 'Rôles & Capacités',
        icon: 'admin',
        path: '/admin/roles',
        capability: 'admin.roles.view',
      },
      {
        id: 'admin-tenants',
        label: 'Tenants',
        icon: 'settings',
        path: '/admin/tenants',
        capability: 'admin.tenants.view',
      },
      {
        id: 'admin-modules',
        label: 'Modules',
        icon: 'settings',
        path: '/admin/modules',
        capability: 'admin.modules.view',
      },
      {
        id: 'admin-logs',
        label: 'Journaux',
        icon: 'settings',
        path: '/admin/logs',
        capability: 'admin.logs.view',
      },
    ],
  },
];

// ============================================================
// MENU ITEM COMPONENT
// ============================================================

interface MenuItemComponentProps {
  item: MenuItem;
  depth?: number;
  onItemClick?: () => void;
}

const MenuItemComponent: React.FC<MenuItemComponentProps> = ({
  item,
  depth = 0,
  onItemClick,
}) => {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = React.useState(false);
  const Icon = item.icon ? ICON_MAP[item.icon] : null;
  const hasChildren = item.children && item.children.length > 0;

  // Auto-expand si un enfant est actif
  const isChildActive = useMemo(() => {
    if (!item.children) return false;
    return item.children.some((child) => location.pathname.startsWith(child.path || ''));
  }, [item.children, location.pathname]);

  React.useEffect(() => {
    if (isChildActive) {
      setIsExpanded(true);
    }
  }, [isChildActive]);

  const handleClick = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    } else if (onItemClick) {
      onItemClick();
    }
  };

  if (hasChildren) {
    return (
      <div className="azals-menu-item-wrapper">
        <button
          className={clsx('azals-menu-item', `azals-menu-item--depth-${depth}`, {
            'azals-menu-item--expanded': isExpanded,
            'azals-menu-item--child-active': isChildActive,
          })}
          onClick={handleClick}
          aria-expanded={isExpanded}
        >
          {Icon && <Icon className="azals-menu-item__icon" size={20} />}
          <span className="azals-menu-item__label">{item.label}</span>
          {isExpanded ? (
            <ChevronDown className="azals-menu-item__chevron" size={16} />
          ) : (
            <ChevronRight className="azals-menu-item__chevron" size={16} />
          )}
        </button>

        {isExpanded && (
          <div className="azals-menu-submenu">
            {item.children?.map((child) => (
              <CapabilityGuard key={child.id} capability={child.capability}>
                <MenuItemComponent
                  item={child}
                  depth={depth + 1}
                  onItemClick={onItemClick}
                />
              </CapabilityGuard>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <NavLink
      to={item.path || '#'}
      className={({ isActive }) =>
        clsx('azals-menu-item', `azals-menu-item--depth-${depth}`, {
          'azals-menu-item--active': isActive,
        })
      }
      onClick={onItemClick}
    >
      {Icon && <Icon className="azals-menu-item__icon" size={20} />}
      <span className="azals-menu-item__label">{item.label}</span>
      {item.badge && (
        <span
          className={clsx('azals-menu-item__badge', `azals-menu-item__badge--${item.badge.color}`, {
            'azals-menu-item__badge--pulse': item.badge.pulse,
          })}
        >
          {item.badge.count}
        </span>
      )}
    </NavLink>
  );
};

// ============================================================
// MENU SECTION COMPONENT
// ============================================================

interface MenuSectionComponentProps {
  section: MenuSection;
  onItemClick?: () => void;
}

const MenuSectionComponent: React.FC<MenuSectionComponentProps> = ({
  section,
  onItemClick,
}) => {
  const { hasCapability, hasAnyCapability } = useCapabilities();

  // Filtrer les items selon les capacités
  const visibleItems = useMemo(() => {
    return section.items.filter((item) => {
      if (!item.capability) return true;
      return hasCapability(item.capability);
    });
  }, [section.items, hasCapability]);

  // Ne pas afficher la section si aucun item visible
  if (visibleItems.length === 0) {
    return null;
  }

  // Vérifier la capacité de la section
  if (section.capability && !hasCapability(section.capability)) {
    return null;
  }

  return (
    <div className="azals-menu-section">
      <h3 className="azals-menu-section__title">{section.title}</h3>
      <ul className="azals-menu-section__list">
        {visibleItems.map((item) => (
          <li key={item.id}>
            <MenuItemComponent item={item} onItemClick={onItemClick} />
          </li>
        ))}
      </ul>
    </div>
  );
};

// ============================================================
// DYNAMIC MENU COMPONENT
// ============================================================

interface DynamicMenuProps {
  onItemClick?: () => void;
}

export const DynamicMenu: React.FC<DynamicMenuProps> = ({ onItemClick }) => {
  const { capabilities, isLoading } = useCapabilities();

  // Debug logging
  React.useEffect(() => {
    console.log('[DynamicMenu] Capabilities state:', {
      isLoading,
      count: capabilities.length,
      capabilities: capabilities.slice(0, 10),
    });
  }, [capabilities, isLoading]);

  if (isLoading) {
    return (
      <nav className="azals-menu">
        <div className="azals-menu__loading">Chargement du menu...</div>
      </nav>
    );
  }

  if (capabilities.length === 0) {
    console.warn('[DynamicMenu] No capabilities available, menu will be empty');
  }

  return (
    <nav className="azals-menu">
      {MENU_SECTIONS.map((section) => (
        <MenuSectionComponent
          key={section.id}
          section={section}
          onItemClick={onItemClick}
        />
      ))}
    </nav>
  );
};

export default DynamicMenu;
