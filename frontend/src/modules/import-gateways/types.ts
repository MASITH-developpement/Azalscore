/**
 * AZALSCORE - Module Passerelles d'Import - Types
 * ================================================
 */

// ============================================================
// ENUMS
// ============================================================

export type ScheduleMode = 'disabled' | 'cron' | 'interval';
export type ImportStatus = 'pending' | 'running' | 'success' | 'partial' | 'error' | 'cancelled';
export type SyncType = 'products' | 'contacts' | 'suppliers' | 'purchase_orders' | 'sale_orders' | 'invoices' | 'quotes' | 'accounting' | 'bank' | 'interventions' | 'full';
export type TriggerMethod = 'manual' | 'scheduled' | 'api';

// ============================================================
// CONNECTION CONFIG
// ============================================================

export interface OdooConnectionConfig {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  odoo_url: string;
  odoo_database: string;
  odoo_version?: string;
  auth_method: 'password' | 'api_key';
  username: string;

  // Sync options
  sync_products: boolean;
  sync_contacts: boolean;
  sync_suppliers: boolean;
  sync_purchase_orders: boolean;
  sync_sale_orders: boolean;
  sync_invoices: boolean;
  sync_quotes: boolean;
  sync_accounting: boolean;
  sync_bank: boolean;
  sync_interventions: boolean;

  // Last sync timestamps
  products_last_sync_at?: string;
  contacts_last_sync_at?: string;
  suppliers_last_sync_at?: string;
  orders_last_sync_at?: string;

  // Stats
  total_imports: number;
  total_products_imported: number;
  total_contacts_imported: number;
  total_suppliers_imported: number;
  total_orders_imported: number;
  last_error_message?: string;

  // Status
  is_active: boolean;
  is_connected: boolean;
  last_connection_test_at?: string;

  // Scheduling
  schedule_mode: ScheduleMode;
  schedule_cron_expression?: string;
  schedule_interval_minutes?: number;
  schedule_timezone: string;
  schedule_paused: boolean;
  next_scheduled_run?: string;
  last_scheduled_run?: string;

  // Audit
  created_at: string;
  updated_at: string;
}

// ============================================================
// IMPORT HISTORY
// ============================================================

export interface ImportHistory {
  id: string;
  config_id: string;
  sync_type: SyncType;
  status: ImportStatus;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  total_records: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  error_details: ErrorDetail[];
  is_delta_sync: boolean;
  delta_from_date?: string;
  triggered_by?: string;
  trigger_method: TriggerMethod;
  config_name?: string;
  import_summary?: Record<string, unknown>;
}

export interface ErrorDetail {
  record_id?: string;
  field?: string;
  message: string;
  odoo_data?: Record<string, unknown>;
}

// ============================================================
// SCHEDULING
// ============================================================

export interface ScheduleConfig {
  mode: ScheduleMode;
  cron_expression?: string;
  interval_minutes?: number;
  timezone: string;
}

export interface ScheduleConfigResponse {
  config_id: string;
  mode: ScheduleMode;
  cron_expression?: string;
  interval_minutes?: number;
  timezone: string;
  is_paused: boolean;
  next_scheduled_run?: string;
  last_scheduled_run?: string;
  message: string;
}

export interface NextRunsResponse {
  config_id: string;
  mode: ScheduleMode;
  next_runs: string[];
}

// ============================================================
// SELECTIVE IMPORT
// ============================================================

export interface SelectiveImportRequest {
  types: SyncType[];
  full_sync: boolean;
}

// ============================================================
// HISTORY SEARCH
// ============================================================

export interface HistorySearchParams {
  config_id?: string;
  sync_type?: SyncType;
  status?: ImportStatus;
  trigger_method?: TriggerMethod;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface HistorySearchResponse {
  items: ImportHistory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================
// CONFIG CRUD
// ============================================================

export interface CreateConfigRequest {
  name: string;
  description?: string;
  odoo_url: string;
  odoo_database: string;
  auth_method: 'password' | 'api_key';
  username: string;
  credential: string;
  sync_products?: boolean;
  sync_contacts?: boolean;
  sync_suppliers?: boolean;
  sync_purchase_orders?: boolean;
  sync_sale_orders?: boolean;
  sync_invoices?: boolean;
  sync_quotes?: boolean;
  sync_accounting?: boolean;
  sync_bank?: boolean;
  sync_interventions?: boolean;
}

export interface UpdateConfigRequest {
  name?: string;
  description?: string;
  odoo_url?: string;
  odoo_database?: string;
  auth_method?: 'password' | 'api_key';
  username?: string;
  credential?: string;
  sync_products?: boolean;
  sync_contacts?: boolean;
  sync_suppliers?: boolean;
  sync_purchase_orders?: boolean;
  sync_sale_orders?: boolean;
  sync_invoices?: boolean;
  sync_quotes?: boolean;
  sync_accounting?: boolean;
  sync_bank?: boolean;
  sync_interventions?: boolean;
  is_active?: boolean;
}

// ============================================================
// TEST CONNECTION
// ============================================================

export interface TestConnectionRequest {
  odoo_url: string;
  odoo_database: string;
  auth_method: 'password' | 'api_key';
  username: string;
  credential: string;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  odoo_version?: string;
  database_name?: string;
  user_name?: string;
  available_models?: string[];
}

// ============================================================
// UI HELPERS
// ============================================================

export const STATUS_CONFIG: Record<ImportStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'gray' },
  running: { label: 'En cours', color: 'blue' },
  success: { label: 'Succes', color: 'green' },
  partial: { label: 'Partiel', color: 'yellow' },
  error: { label: 'Erreur', color: 'red' },
  cancelled: { label: 'Annule', color: 'gray' },
};

export const SYNC_TYPE_CONFIG: Record<SyncType, { label: string; icon: string }> = {
  products: { label: 'Produits', icon: 'Package' },
  contacts: { label: 'Contacts', icon: 'Users' },
  suppliers: { label: 'Fournisseurs', icon: 'Truck' },
  purchase_orders: { label: 'Commandes achat', icon: 'ShoppingCart' },
  sale_orders: { label: 'Commandes vente', icon: 'ShoppingBag' },
  invoices: { label: 'Factures', icon: 'FileText' },
  quotes: { label: 'Devis', icon: 'FileEdit' },
  accounting: { label: 'Comptabilite', icon: 'Calculator' },
  bank: { label: 'Banque', icon: 'Wallet' },
  interventions: { label: 'Interventions', icon: 'Wrench' },
  full: { label: 'Complet', icon: 'RefreshCw' },
};

export const SCHEDULE_MODE_CONFIG: Record<ScheduleMode, { label: string; description: string }> = {
  disabled: { label: 'Desactive', description: 'Pas de synchronisation automatique' },
  cron: { label: 'Expression Cron', description: 'Planification avancee (ex: 8h tous les jours)' },
  interval: { label: 'Intervalle', description: 'Toutes les X minutes' },
};

export const CRON_PRESETS = [
  { label: 'Toutes les heures', value: '0 * * * *' },
  { label: 'Tous les jours a 8h', value: '0 8 * * *' },
  { label: 'Lun-Ven a 8h', value: '0 8 * * 1-5' },
  { label: 'Lun-Ven a 8h et 18h', value: '0 8,18 * * 1-5' },
  { label: 'Tous les lundis a 8h', value: '0 8 * * 1' },
  { label: 'Premier du mois a 8h', value: '0 8 1 * *' },
];

export const INTERVAL_PRESETS = [
  { label: '5 minutes', value: 5 },
  { label: '15 minutes', value: 15 },
  { label: '30 minutes', value: 30 },
  { label: '1 heure', value: 60 },
  { label: '2 heures', value: 120 },
  { label: '4 heures', value: 240 },
  { label: '12 heures', value: 720 },
  { label: '24 heures', value: 1440 },
];
