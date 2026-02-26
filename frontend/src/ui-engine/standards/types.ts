/**
 * AZALSCORE UI Standards - TypeScript Types
 * Interfaces et types pour les composants standardisés
 */

import React from 'react';

// ============================================================
// BASE TYPES
// ============================================================

/**
 * Mode d'interface utilisateur
 */
export type UIMode = 'azalscore' | 'erp';

/**
 * Type de vue
 */
export type ViewType = 'list' | 'detail' | 'form';

/**
 * Couleurs sémantiques pour les statuts et badges
 */
export type SemanticColor =
  | 'gray'
  | 'blue'
  | 'green'
  | 'orange'
  | 'red'
  | 'purple'
  | 'yellow'
  | 'cyan';

/**
 * Tailles standard
 */
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

/**
 * Variantes de boutons
 */
export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'danger'
  | 'warning'
  | 'ghost'
  | 'success';

// ============================================================
// STATUS
// ============================================================

/**
 * Définition d'un statut (badge)
 */
export interface StatusDefinition {
  label: string;
  color: SemanticColor;
  icon?: React.ReactNode;
}

// ============================================================
// ACTIONS
// ============================================================

/**
 * Définition d'une action (bouton)
 */
export interface ActionDefinition {
  id: string;
  label: string;
  icon?: React.ReactNode;
  variant?: ButtonVariant;
  onClick?: () => void | Promise<void>;
  href?: string;
  disabled?: boolean;
  loading?: boolean;
  hidden?: boolean;
  /** Capabilité requise pour afficher cette action */
  capability?: string;
  /** Confirmation requise avant exécution */
  confirm?: {
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
  };
}

// ============================================================
// TABS
// ============================================================

/**
 * Props pour le contenu d'un onglet
 */
export interface TabContentProps<T = unknown> {
  data: T;
  isActive: boolean;
  onDataChange?: (data: Partial<T>) => void;
}

/**
 * Définition d'un onglet
 */
export interface TabDefinition<T = unknown> {
  /** Identifiant unique de l'onglet */
  id: string;
  /** Label affiché */
  label: string;
  /** Icône de l'onglet */
  icon?: React.ReactNode;
  /** Badge (nombre) sur l'onglet */
  badge?: number;
  /** Couleur du badge */
  badgeColor?: SemanticColor;
  /** Onglet masqué (CSS hidden, jamais supprimé du DOM) */
  hidden?: boolean;
  /** Onglet désactivé */
  disabled?: boolean;
  /** Onglet IA (styling spécial en mode AZALSCORE) */
  isIA?: boolean;
  /** Composant à rendre pour ce tab */
  component?: React.ComponentType<TabContentProps<T>>;
  /** Contenu JSX direct (alternative à component) */
  content?: React.ReactNode;
}

/**
 * Props pour TabsStandard
 */
export interface TabsStandardProps<T = unknown> {
  tabs: TabDefinition<T>[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  data: T;
  onDataChange?: (data: Partial<T>) => void;
  className?: string;
}

// ============================================================
// HEADER
// ============================================================

/**
 * Props pour HeaderStandard
 */
export interface HeaderStandardProps {
  /** Titre principal */
  title: string;
  /** Sous-titre (ex: numéro de document) */
  subtitle?: string;
  /** Statut du document */
  status?: StatusDefinition;
  /** Actions du header */
  actions?: ActionDefinition[];
  /** Action de retour */
  backAction?: {
    label: string;
    onClick: () => void;
  };
  /** Classes CSS additionnelles */
  className?: string;
  /** Contenu supplémentaire dans le header */
  children?: React.ReactNode;
}

// ============================================================
// INFO BAR (KPIs)
// ============================================================

/**
 * Tendance d'un KPI
 */
export type TrendDirection = 'up' | 'down' | 'neutral';

/**
 * Item de la barre d'information (KPI)
 */
export interface InfoBarItem {
  /** Identifiant unique */
  id: string;
  /** Label du KPI */
  label: string;
  /** Valeur affichée */
  value: string | number;
  /** Couleur de la valeur */
  valueColor?: SemanticColor | 'positive' | 'negative' | 'warning';
  /** Tendance */
  trend?: {
    direction: TrendDirection;
    value: string;
  };
  /** Champ secondaire (masqué en mode AZALSCORE) */
  secondary?: boolean;
  /** Icône */
  icon?: React.ReactNode;
}

/**
 * Props pour MainInfoBar
 */
export interface MainInfoBarProps {
  items: InfoBarItem[];
  className?: string;
}

// ============================================================
// SIDEBAR SUMMARY
// ============================================================

/**
 * Item du résumé sidebar
 */
export interface SidebarSummaryItem {
  /** Identifiant unique */
  id: string;
  /** Label de l'item */
  label: string;
  /** Valeur affichée */
  value: string | number;
  /** Mise en évidence de la valeur */
  highlight?: boolean;
  /** Format (ex: 'currency', 'percent', 'date') */
  format?: 'currency' | 'percent' | 'date' | 'number' | 'text';
  /** Champ secondaire (masqué en mode AZALSCORE) */
  secondary?: boolean;
}

/**
 * Section de la sidebar
 */
export interface SidebarSection {
  /** Identifiant unique */
  id: string;
  /** Titre de la section */
  title: string;
  /** Items de la section */
  items: SidebarSummaryItem[];
  /** Total de la section */
  total?: {
    label: string;
    value: string | number;
  };
}

/**
 * Props pour SidebarSummary
 */
export interface SidebarSummaryProps {
  sections: SidebarSection[];
  className?: string;
}

// ============================================================
// FOOTER ACTIONS
// ============================================================

/**
 * Props pour FooterActions
 */
export interface FooterActionsProps {
  /** Actions secondaires (gauche) */
  secondaryActions?: ActionDefinition[];
  /** Actions primaires (droite) */
  primaryActions?: ActionDefinition[];
  className?: string;
}

// ============================================================
// BASE VIEW STANDARD
// ============================================================

/**
 * Props pour BaseViewStandard - le composant principal
 */
export interface BaseViewStandardProps<T = unknown> {
  /** Titre de la vue */
  title: string;
  /** Sous-titre */
  subtitle?: string;
  /** Statut */
  status?: StatusDefinition;
  /** Données de la vue */
  data: T;
  /** Type de vue */
  view: ViewType;
  /** Définition des onglets */
  tabs: TabDefinition<T>[];
  /** Onglet actif par défaut */
  defaultTab?: string;
  /** Items de la barre d'info (KPIs) */
  infoBarItems?: InfoBarItem[];
  /** Sections de la sidebar */
  sidebarSections?: SidebarSection[];
  /** Actions du header */
  headerActions?: ActionDefinition[];
  /** Actions secondaires du footer */
  secondaryActions?: ActionDefinition[];
  /** Actions primaires du footer */
  primaryActions?: ActionDefinition[];
  /** Action de retour */
  backAction?: {
    label: string;
    onClick: () => void;
  };
  /** Callback sur changement de données */
  onDataChange?: (data: Partial<T>) => void;
  /** Callback sur changement d'onglet */
  onTabChange?: (tabId: string) => void;
  /** État de chargement */
  isLoading?: boolean;
  /** Error object from React Query */
  error?: Error | null;
  /** Retry callback */
  onRetry?: () => void;
  /** Whether data is empty (overrides auto-detection) */
  isEmpty?: boolean;
  /** Empty state title */
  emptyTitle?: string;
  /** Empty state message */
  emptyMessage?: string;
  /** Empty state action */
  emptyAction?: { label: string; onClick: () => void; icon?: React.ReactNode };
  /** Classes CSS additionnelles */
  className?: string;
}

// ============================================================
// UTILITY TYPES
// ============================================================

/**
 * Props communes pour les composants standardisés
 */
export interface StandardComponentProps {
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Props pour les champs avec support de visibilité mode
 */
export interface FieldVisibilityProps {
  /** Champ secondaire (masqué en mode AZALSCORE) */
  secondary?: boolean;
  /** Visible uniquement en mode ERP */
  erpOnly?: boolean;
  /** Visible uniquement en mode AZALSCORE */
  azalscoreOnly?: boolean;
}

/**
 * Formatter pour les valeurs
 */
export type ValueFormatter = (value: unknown) => string;

/**
 * Configuration de formatage
 */
export interface FormatConfig {
  currency?: string;
  locale?: string;
  decimals?: number;
}
