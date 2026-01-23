/**
 * AZALSCORE UI Engine - Command Palette
 * Palette de commandes rapide (style Notion, Slack, Linear...)
 * Accessible via "/" ou "Cmd/Ctrl + K"
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Search,
  FileText,
  Users,
  Wallet,
  ShoppingCart,
  FolderKanban,
  Wrench,
  LayoutDashboard,
  Settings,
  Package,
  Factory,
  Globe,
  type LucideIcon,
} from 'lucide-react';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// TYPES
// ============================================================

interface Command {
  id: string;
  label: string;
  description?: string;
  icon?: LucideIcon;
  path?: string;
  action?: () => void;
  capability?: string;
  category: 'navigation' | 'action' | 'settings';
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

// ============================================================
// COMMAND REGISTRY
// ============================================================

const ICON_MAP: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  invoicing: FileText,
  partners: Users,
  treasury: Wallet,
  purchases: ShoppingCart,
  projects: FolderKanban,
  interventions: Wrench,
  settings: Settings,
  stock: Package,
  production: Factory,
  web: Globe,
};

const ALL_COMMANDS: Command[] = [
  // Navigation
  {
    id: 'nav-cockpit',
    label: 'Cockpit Dirigeant',
    description: 'Tableau de bord décisionnel',
    icon: ICON_MAP.dashboard,
    path: '/cockpit',
    capability: 'cockpit.view',
    category: 'navigation',
  },
  {
    id: 'nav-partners',
    label: 'Partenaires',
    description: 'Clients et fournisseurs',
    icon: ICON_MAP.partners,
    path: '/partners',
    capability: 'partners.view',
    category: 'navigation',
  },
  {
    id: 'nav-invoicing',
    label: 'Facturation',
    description: 'Devis et factures',
    icon: ICON_MAP.invoicing,
    path: '/invoicing',
    capability: 'invoicing.view',
    category: 'navigation',
  },
  {
    id: 'nav-treasury',
    label: 'Trésorerie',
    description: 'Comptes bancaires et prévisions',
    icon: ICON_MAP.treasury,
    path: '/treasury',
    capability: 'treasury.view',
    category: 'navigation',
  },
  {
    id: 'nav-purchases',
    label: 'Achats',
    description: 'Commandes fournisseurs',
    icon: ICON_MAP.purchases,
    path: '/purchases',
    capability: 'purchases.view',
    category: 'navigation',
  },
  {
    id: 'nav-projects',
    label: 'Projets',
    description: 'Gestion de projets',
    icon: ICON_MAP.projects,
    path: '/projects',
    capability: 'projects.view',
    category: 'navigation',
  },
  {
    id: 'nav-stock',
    label: 'Stock',
    description: 'Inventaire et mouvements',
    icon: ICON_MAP.stock,
    path: '/stock',
    capability: 'inventory.view',
    category: 'navigation',
  },

  // Actions rapides
  {
    id: 'action-new-invoice',
    label: 'Nouvelle facture',
    description: 'Créer une nouvelle facture client',
    icon: ICON_MAP.invoicing,
    path: '/invoicing/invoices/new',
    capability: 'invoicing.create',
    category: 'action',
  },
  {
    id: 'action-new-quote',
    label: 'Nouveau devis',
    description: 'Créer un nouveau devis',
    icon: ICON_MAP.invoicing,
    path: '/invoicing/quotes/new',
    capability: 'invoicing.create',
    category: 'action',
  },
  {
    id: 'action-new-client',
    label: 'Nouveau client',
    description: 'Ajouter un nouveau client',
    icon: ICON_MAP.partners,
    path: '/partners/clients/new',
    capability: 'partners.create',
    category: 'action',
  },
  {
    id: 'action-new-expense',
    label: 'Nouvelle dépense',
    description: 'Enregistrer une dépense',
    icon: ICON_MAP.purchases,
    path: '/purchases/expenses/new',
    capability: 'purchases.create',
    category: 'action',
  },
  {
    id: 'action-new-project',
    label: 'Nouveau projet',
    description: 'Créer un nouveau projet',
    icon: ICON_MAP.projects,
    path: '/projects/new',
    capability: 'projects.create',
    category: 'action',
  },

  // Paramètres
  {
    id: 'settings-profile',
    label: 'Mon profil',
    description: 'Gérer mon compte utilisateur',
    icon: ICON_MAP.settings,
    path: '/profile',
    category: 'settings',
  },
  {
    id: 'settings-general',
    label: 'Paramètres',
    description: 'Configuration générale',
    icon: ICON_MAP.settings,
    path: '/settings',
    category: 'settings',
  },
];

// ============================================================
// HELPER: Recherche fuzzy simple
// ============================================================

const fuzzyMatch = (search: string, text: string): boolean => {
  const searchLower = search.toLowerCase();
  const textLower = text.toLowerCase();

  // Recherche exacte
  if (textLower.includes(searchLower)) return true;

  // Recherche fuzzy (chaque lettre dans l'ordre)
  let searchIndex = 0;
  for (let i = 0; i < textLower.length && searchIndex < searchLower.length; i++) {
    if (textLower[i] === searchLower[searchIndex]) {
      searchIndex++;
    }
  }

  return searchIndex === searchLower.length;
};

// ============================================================
// COMMAND PALETTE COMPONENT
// ============================================================

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { capabilities } = useCapabilities();

  // Filtrer les commandes selon les capacités et la recherche
  const filteredCommands = useMemo(() => {
    return ALL_COMMANDS.filter((cmd) => {
      // Vérifier les capacités
      if (cmd.capability && !capabilities.includes(cmd.capability)) {
        return false;
      }

      // Vérifier la recherche
      if (search) {
        return (
          fuzzyMatch(search, cmd.label) ||
          (cmd.description && fuzzyMatch(search, cmd.description))
        );
      }

      return true;
    });
  }, [search, capabilities]);

  // Grouper par catégorie
  const commandsByCategory = useMemo(() => {
    const groups: Record<string, Command[]> = {
      action: [],
      navigation: [],
      settings: [],
    };

    filteredCommands.forEach((cmd) => {
      groups[cmd.category].push(cmd);
    });

    return groups;
  }, [filteredCommands]);

  // Reset selection quand la recherche change
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  // Focus input quand ouvert
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Gestion du clavier
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const cmd = filteredCommands[selectedIndex];
        if (cmd) {
          executeCommand(cmd);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  const executeCommand = useCallback(
    (cmd: Command) => {
      if (cmd.action) {
        cmd.action();
      } else if (cmd.path) {
        navigate(cmd.path);
      }
      onClose();
      setSearch('');
    },
    [navigate, onClose]
  );

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="azals-command-palette__overlay" onClick={onClose} />

      {/* Palette */}
      <div className="azals-command-palette">
        {/* Search input */}
        <div className="azals-command-palette__search">
          <Search size={20} className="azals-command-palette__search-icon" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Rechercher une action ou un module..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="azals-command-palette__input"
          />
        </div>

        {/* Results */}
        <div className="azals-command-palette__results">
          {filteredCommands.length === 0 ? (
            <div className="azals-command-palette__empty">
              Aucun résultat pour "{search}"
            </div>
          ) : (
            <>
              {/* Actions rapides */}
              {commandsByCategory.action.length > 0 && (
                <div className="azals-command-palette__group">
                  <h4 className="azals-command-palette__group-title">Actions rapides</h4>
                  {commandsByCategory.action.map((cmd, idx) => {
                    const Icon = cmd.icon;
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        className={clsx('azals-command-palette__item', {
                          'azals-command-palette__item--selected': selectedIndex === globalIndex,
                        })}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        {Icon && <Icon size={18} className="azals-command-palette__item-icon" />}
                        <div className="azals-command-palette__item-content">
                          <div className="azals-command-palette__item-label">{cmd.label}</div>
                          {cmd.description && (
                            <div className="azals-command-palette__item-description">
                              {cmd.description}
                            </div>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Navigation */}
              {commandsByCategory.navigation.length > 0 && (
                <div className="azals-command-palette__group">
                  <h4 className="azals-command-palette__group-title">Navigation</h4>
                  {commandsByCategory.navigation.map((cmd) => {
                    const Icon = cmd.icon;
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        className={clsx('azals-command-palette__item', {
                          'azals-command-palette__item--selected': selectedIndex === globalIndex,
                        })}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        {Icon && <Icon size={18} className="azals-command-palette__item-icon" />}
                        <div className="azals-command-palette__item-content">
                          <div className="azals-command-palette__item-label">{cmd.label}</div>
                          {cmd.description && (
                            <div className="azals-command-palette__item-description">
                              {cmd.description}
                            </div>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Paramètres */}
              {commandsByCategory.settings.length > 0 && (
                <div className="azals-command-palette__group">
                  <h4 className="azals-command-palette__group-title">Paramètres</h4>
                  {commandsByCategory.settings.map((cmd) => {
                    const Icon = cmd.icon;
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        className={clsx('azals-command-palette__item', {
                          'azals-command-palette__item--selected': selectedIndex === globalIndex,
                        })}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        {Icon && <Icon size={18} className="azals-command-palette__item-icon" />}
                        <div className="azals-command-palette__item-content">
                          <div className="azals-command-palette__item-label">{cmd.label}</div>
                          {cmd.description && (
                            <div className="azals-command-palette__item-description">
                              {cmd.description}
                            </div>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer hint */}
        <div className="azals-command-palette__footer">
          <kbd>↑↓</kbd> Navigation
          <kbd>↵</kbd> Sélectionner
          <kbd>Esc</kbd> Fermer
        </div>
      </div>
    </>
  );
};

export default CommandPalette;
