/**
 * AZALSCORE UI Engine - Types Globaux
 * Aucune logique métier - Types uniquement
 */

// ============================================================
// TYPES D'AUTHENTIFICATION
// ============================================================

export interface User {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
  roles: string[];
  capabilities: string[];
  is_active: boolean;
  requires_2fa: boolean;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// ============================================================
// TYPES DE CAPACITÉS
// ============================================================

export interface Capability {
  code: string;
  name: string;
  description: string;
  module: string;
  is_sensitive: boolean;
}

export interface CapabilitiesState {
  capabilities: string[];
  isLoading: boolean;
  hasCapability: (cap: string) => boolean;
  hasAnyCapability: (caps: string[]) => boolean;
  hasAllCapabilities: (caps: string[]) => boolean;
}

// ============================================================
// TYPES API
// ============================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  errors?: ApiError[];
}

export interface ApiError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiRequestConfig {
  skipAuth?: boolean;
  timeout?: number;
  retries?: number;
}

// ============================================================
// TYPES MENU / NAVIGATION
// ============================================================

export interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  capability?: string;
  children?: MenuItem[];
  badge?: MenuBadge;
  isExternal?: boolean;
}

export interface MenuBadge {
  count?: number;
  color: 'red' | 'orange' | 'green' | 'blue' | 'gray';
  pulse?: boolean;
}

export interface MenuSection {
  id: string;
  title: string;
  items: MenuItem[];
  capability?: string;
}

// ============================================================
// TYPES ALERTES / DASHBOARD
// ============================================================

export type AlertSeverity = 'RED' | 'ORANGE' | 'GREEN';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  module: string;
  created_at: string;
  requires_action: boolean;
  action_url?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

export interface DashboardKPI {
  id: string;
  label: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trend_value?: number;
  severity?: AlertSeverity;
  period?: string;
}

export interface DashboardWidget {
  id: string;
  type: 'kpi' | 'chart' | 'table' | 'alerts' | 'actions';
  title: string;
  capability?: string;
  data?: unknown;
  config?: Record<string, unknown>;
}

// ============================================================
// TYPES TABLES
// ============================================================

export interface TableColumn<T> {
  id: string;
  header: string;
  accessor: keyof T | ((row: T) => unknown);
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, row: T) => React.ReactNode;
}

export interface TableAction<T> {
  id: string;
  label: string;
  icon?: string;
  capability?: string;
  onClick: (row: T) => void;
  isDisabled?: (row: T) => boolean;
  isHidden?: (row: T) => boolean;
  variant?: 'default' | 'danger' | 'warning';
}

export interface TableState {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filters: Record<string, unknown>;
  search?: string;
}

// ============================================================
// TYPES FORMULAIRES
// ============================================================

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'checkbox' | 'date' | 'textarea' | 'file';
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  options?: SelectOption[];
  validation?: FormValidation;
  capability?: string;
  helpText?: string;
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface FormValidation {
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  custom?: (value: unknown) => string | undefined;
}

// ============================================================
// TYPES ACTIONS / WORKFLOW
// ============================================================

export interface ActionButton {
  id: string;
  label: string;
  icon?: string;
  capability?: string;
  variant: 'primary' | 'secondary' | 'danger' | 'warning' | 'ghost';
  onClick: () => void | Promise<void>;
  isLoading?: boolean;
  isDisabled?: boolean;
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
}

export interface WorkflowStep {
  id: string;
  label: string;
  status: 'pending' | 'current' | 'completed' | 'error';
  description?: string;
}

// ============================================================
// TYPES BREAK-GLASS
// ============================================================

export interface BreakGlassScope {
  tenant_id?: string;
  module?: string;
  start_date?: string;
  end_date?: string;
}

export interface BreakGlassRequest {
  scope: BreakGlassScope;
  confirmation_phrase: string;
  reason?: string;
  password: string;
  totp_code?: string;
}

export interface BreakGlassChallenge {
  challenge_id: string;
  confirmation_phrase: string;
  expires_at: string;
}

// ============================================================
// TYPES MODULE
// ============================================================

export interface ModuleInfo {
  id: string;
  name: string;
  version: string;
  is_active: boolean;
  is_available: boolean;
  required_capability: string;
  icon?: string;
  description?: string;
}

export interface ModuleState {
  modules: ModuleInfo[];
  isLoading: boolean;
  isModuleActive: (moduleId: string) => boolean;
  isModuleAvailable: (moduleId: string) => boolean;
}

// ============================================================
// TYPES TENANT
// ============================================================

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  plan: string;
  modules: string[];
  settings: Record<string, unknown>;
  created_at: string;
}

// ============================================================
// TYPES AUDIT UI
// ============================================================

export interface UIAuditEvent {
  event_type: string;
  component: string;
  action: string;
  metadata?: Record<string, unknown>;
}

// ============================================================
// TYPES UTILITAIRES
// ============================================================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  status: LoadingState;
  error: string | null;
}

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
