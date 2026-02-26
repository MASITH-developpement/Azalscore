import type { ReactNode } from 'react';

/**
 * AZALSCORE - Types centralisés
 * ==============================
 *
 * Ce fichier réexporte tous les types API et métier.
 *
 * Usage:
 *   import type { User, Invoice } from '@/types';
 *
 * Génération des types API:
 *   npm run generate:api-types
 *
 * Cela génère api.generated.ts depuis le schema OpenAPI du backend.
 */

// Types API générés depuis OpenAPI (à générer avec npm run generate:api-types)
// export type * from './api.generated';

// ============================================================================
// TYPES DE BASE
// ============================================================================

/**
 * Réponse API paginée standard
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
}

/**
 * Réponse API standard
 */
export interface ApiResponse<T> {
  data?: T;
  items?: T[];
  total?: number;
  message?: string;
  success?: boolean;
}

/**
 * Erreur API standard
 */
export interface ApiError {
  code: string;
  message: string;
  field?: string;
  trace_id?: string;
  path?: string;
}

/**
 * Configuration de requête API
 */
export interface ApiRequestConfig {
  timeout?: number;
  retries?: number;
  skipAuth?: boolean;
  headers?: Record<string, string>;
  responseType?: 'json' | 'blob' | 'text';
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Décompresse une réponse API en extrayant les données.
 * Gère les formats: { data: T }, { items: T[] }, ou T directement.
 */
export function unwrapApiResponse<T>(response: ApiResponse<T> | T): T | undefined {
  if (!response) return undefined;

  // Si c'est déjà le type attendu (pas un wrapper)
  if (typeof response !== 'object') return response as T;

  const r = response as ApiResponse<T>;

  // Format { data: T }
  if ('data' in r && r.data !== undefined) {
    return r.data;
  }

  // Format { items: T[] } - retourne le tableau
  if ('items' in r && Array.isArray(r.items)) {
    return r as unknown as T;
  }

  // Sinon retourne tel quel
  return response as T;
}

// ============================================================================
// TYPES MÉTIER COMMUNS
// ============================================================================

/**
 * Entité avec tenant_id (base multi-tenant)
 */
export interface TenantEntity {
  id: string;
  tenant_id: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Utilisateur simplifié
 */
export interface User extends TenantEntity {
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  display_name?: string;
  name?: string;
  role?: string;
  roles?: string[];
  is_active: boolean;
  requires_2fa?: boolean;
  capabilities?: string[];
  default_view?: string;
  preferences?: Record<string, unknown>;
}

/**
 * Tokens d'authentification
 */
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * État d'authentification
 */
export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * État d'authentification typé avec status
 */
export interface TypedAuthState extends AuthState {
  status: 'idle' | 'loading' | 'ready' | 'error';
}

// ============================================================================
// TYPES CAPACITÉS (RBAC)
// ============================================================================

/**
 * Capacité utilisateur
 */
export interface Capability {
  id: string;
  name: string;
  description?: string;
  module?: string;
  is_sensitive?: boolean;
}

/**
 * État des capacités
 */
export interface CapabilitiesState {
  capabilities: string[];
  isLoading: boolean;
  hasCapability: (cap: string) => boolean;
  hasAnyCapability: (caps: string[]) => boolean;
  hasAllCapabilities: (caps: string[]) => boolean;
}

// ============================================================================
// TYPES RECHERCHE
// ============================================================================

/**
 * Résultat recherche client
 */
export interface SearchClientResult {
  id: string;
  code?: string;
  name: string;
  type?: string;
  city?: string;
  email?: string;
  phone?: string;
}

/**
 * Résultat recherche document
 */
export interface SearchDocumentResult {
  id: string;
  number: string;
  type: string;
  document_type?: string;
  status?: string;
  client_name?: string;
  customer_name?: string;
  total?: number;
  total_ttc?: number;
  date?: string;
}

/**
 * Résultat recherche produit
 */
export interface SearchProductResult {
  id: string;
  code?: string;
  sku?: string;
  name: string;
  price?: number;
  stock_qty?: number;
  category?: string;
}

// ============================================================================
// TYPES ERREURS
// ============================================================================

/**
 * Erreur de mutation API
 */
export interface ApiMutationError {
  message: string;
  code?: string;
  field?: string;
  details?: Record<string, unknown>;
}

/**
 * Type Result pour gestion d'erreurs fonctionnelle
 */
export type Result<T, E = { code: string; message: string }> =
  | { ok: true; data: T; error?: never }
  | { ok: false; data?: never; error: E };

// ============================================================================
// TYPES AUDIT
// ============================================================================

/**
 * Événement d'audit UI
 */
export interface UIAuditEvent {
  type?: string;
  event_type?: string;
  action?: string;
  component?: string;
  target?: string;
  metadata?: Record<string, unknown>;
  timestamp?: string;
  user_id?: string;
  session_id?: string;
  success?: boolean;
  error?: string;
  duration?: number;
}

/**
 * Tenant
 */
export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  subscription_tier?: string;
  created_at?: string;
}

/**
 * Statuts de workflow génériques
 */
export type WorkflowStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'BLOCKED';

/**
 * Niveaux de priorité
 */
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

/**
 * Devises supportées
 */
export type Currency = 'EUR' | 'USD' | 'GBP' | 'CHF';

// ============================================================================
// TYPES UI ENGINE
// ============================================================================

/**
 * Colonne de tableau générique
 */
export interface TableColumn<T> {
  id: string;
  header: string;
  accessor: keyof T | string | ((row: T) => unknown);
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  width?: string | number;
  render?: (value: unknown, row: T) => ReactNode;
}

/**
 * Action de tableau (menu contextuel)
 */
export interface TableAction<T> {
  id: string;
  label: string;
  icon?: string | ReactNode;
  onClick: (row: T) => void;
  visible?: (row: T) => boolean;
  isHidden?: (row: T) => boolean;
  disabled?: (row: T) => boolean;
  isDisabled?: (row: T) => boolean;
  variant?: 'default' | 'danger' | 'warning';
  capability?: string;
}

/**
 * Badge de menu
 */
export interface MenuBadge {
  count: number | string;
  color?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  pulse?: boolean;
}

/**
 * Item de menu navigation
 */
export interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  capability?: string;
  children?: MenuItem[];
  badge?: MenuBadge;
  external?: boolean;
}

/**
 * Section de menu navigation
 */
export interface MenuSection {
  id: string;
  title: string;
  items: MenuItem[];
  capability?: string;
}

/**
 * Entité générique avec ID
 */
export interface EntityItem {
  id: string;
  [key: string]: unknown;
}

/**
 * Information module ERP
 */
export interface ModuleInfo {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  is_active: boolean;
  is_available: boolean;
  version?: string;
  capabilities?: string[];
}

// ============================================================================
// TYPES DASHBOARD
// ============================================================================

/**
 * Sévérité des alertes
 */
export type AlertSeverity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | 'SUCCESS' | 'RED' | 'ORANGE' | 'GREEN';

/**
 * KPI Dashboard
 */
export interface DashboardKPI {
  id: string;
  label: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  trend_value?: number;
  period?: string;
  severity?: AlertSeverity;
  link?: string;
  icon?: ReactNode;
}

/**
 * Widget Dashboard
 */
export interface DashboardWidget {
  id: string;
  type: 'kpi' | 'chart' | 'table' | 'list' | 'custom';
  title: string;
  span?: number;
  data?: unknown;
  config?: Record<string, unknown>;
  capability?: string;
}

/**
 * Alerte système
 */
export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  timestamp?: string;
  created_at?: string;
  read?: boolean;
  acknowledged?: boolean;
  requires_action?: boolean;
  link?: string;
  source?: string;
  module?: string;
}

/**
 * Bouton d'action configurable
 */
export interface ActionButton {
  id: string;
  label: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'ghost' | 'success';
  icon?: string;
  capability?: string;
  onClick?: () => void | Promise<void>;
  confirm?: {
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
  };
  disabled?: boolean;
  loading?: boolean;
}

// ============================================================================
// TYPES FORMULAIRES
// ============================================================================

/**
 * Option de select
 */
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  group?: string;
}

/**
 * Champ de formulaire
 */
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'time' | 'datetime' | 'file' | 'hidden';
  required?: boolean;
  placeholder?: string;
  helpText?: string;
  defaultValue?: unknown;
  options?: SelectOption[];
  validation?: {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    pattern?: string;
  };
  disabled?: boolean;
  readOnly?: boolean;
  className?: string;
}
