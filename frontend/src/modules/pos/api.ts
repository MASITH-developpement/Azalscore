/**
 * AZALSCORE - POS API
 * ===================
 * API client pour le module Point de Vente (POS)
 * Couvre: Magasins, Terminaux, Sessions, Transactions
 */

import { api } from '@/core/api-client';
import type { POSSession } from './types';

// ============================================================================
// TYPES
// ============================================================================

export interface POSStore {
  id: string;
  code: string;
  name: string;
  address?: string;
  city?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  created_at: string;
}

export interface POSTerminal {
  id: string;
  code: string;
  name: string;
  store_id: string;
  store_name?: string;
  status: 'OFFLINE' | 'ONLINE' | 'IN_USE';
  last_activity?: string;
  is_active: boolean;
}

export interface POSTransaction {
  id: string;
  number: string;
  session_id: string;
  type: 'SALE' | 'RETURN' | 'EXCHANGE';
  customer_id?: string;
  customer_name?: string;
  items: POSTransactionItem[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  payment_method: 'CASH' | 'CARD' | 'CHECK' | 'VOUCHER' | 'MIXED';
  amount_paid: number;
  change: number;
  status: 'COMPLETED' | 'VOIDED' | 'REFUNDED';
  created_at: string;
}

export interface POSTransactionItem {
  id: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax_rate: number;
  total: number;
}

export interface POSDashboard {
  active_sessions: number;
  sales_today: number;
  transactions_today: number;
  average_ticket: number;
  top_products: Array<{
    product_id: string;
    product_name: string;
    quantity: number;
    amount: number;
  }>;
  sales_by_hour: Array<{
    hour: number;
    amount: number;
    transactions: number;
  }>;
}

export interface POSCashMovement {
  id: string;
  session_id: string;
  type: 'OPENING' | 'CLOSING' | 'DEPOSIT' | 'WITHDRAWAL';
  amount: number;
  reason?: string;
  created_at: string;
  created_by?: string;
}

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { POSSession };

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface StoreFilters {
  is_active?: boolean;
  search?: string;
}

export interface TerminalFilters {
  store_id?: string;
  status?: 'OFFLINE' | 'ONLINE' | 'IN_USE';
}

export interface SessionFilters {
  store_id?: string;
  terminal_id?: string;
  status?: 'OPEN' | 'CLOSED';
  date_from?: string;
  date_to?: string;
}

export interface TransactionFilters {
  session_id?: string;
  type?: 'SALE' | 'RETURN' | 'EXCHANGE';
  status?: 'COMPLETED' | 'VOIDED' | 'REFUNDED';
  payment_method?: string;
  date_from?: string;
  date_to?: string;
}

export interface OpenSessionData {
  terminal_id: string;
  opening_balance: number;
}

export interface CloseSessionData {
  closing_balance: number;
  notes?: string;
}

export interface TransactionItemCreate {
  product_id: string;
  quantity: number;
  unit_price?: number;
  discount?: number;
}

export interface TransactionCreate {
  session_id: string;
  type?: 'SALE' | 'RETURN' | 'EXCHANGE';
  customer_id?: string;
  items: TransactionItemCreate[];
  discount?: number;
  payment_method: 'CASH' | 'CARD' | 'CHECK' | 'VOUCHER' | 'MIXED';
  amount_paid: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/pos';

function buildQueryString<T extends object>(params: T): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const posApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère le tableau de bord POS
   */
  getDashboard: () =>
    api.get<POSDashboard>(`${BASE_PATH}/dashboard`),

  // ==========================================================================
  // Stores (Magasins)
  // ==========================================================================

  /**
   * Liste les magasins
   */
  listStores: (filters?: StoreFilters) =>
    api.get<POSStore[]>(`${BASE_PATH}/stores${buildQueryString(filters || {})}`),

  /**
   * Récupère un magasin par son ID
   */
  getStore: (id: string) =>
    api.get<POSStore>(`${BASE_PATH}/stores/${id}`),

  /**
   * Crée un nouveau magasin
   */
  createStore: (data: Partial<POSStore>) =>
    api.post<POSStore>(`${BASE_PATH}/stores`, data),

  /**
   * Met à jour un magasin
   */
  updateStore: (id: string, data: Partial<POSStore>) =>
    api.put<POSStore>(`${BASE_PATH}/stores/${id}`, data),

  // ==========================================================================
  // Terminals (Terminaux)
  // ==========================================================================

  /**
   * Liste les terminaux
   */
  listTerminals: (filters?: TerminalFilters) =>
    api.get<POSTerminal[]>(`${BASE_PATH}/terminals${buildQueryString(filters || {})}`),

  /**
   * Récupère un terminal par son ID
   */
  getTerminal: (id: string) =>
    api.get<POSTerminal>(`${BASE_PATH}/terminals/${id}`),

  /**
   * Crée un nouveau terminal
   */
  createTerminal: (data: Partial<POSTerminal>) =>
    api.post<POSTerminal>(`${BASE_PATH}/terminals`, data),

  /**
   * Met à jour un terminal
   */
  updateTerminal: (id: string, data: Partial<POSTerminal>) =>
    api.put<POSTerminal>(`${BASE_PATH}/terminals/${id}`, data),

  // ==========================================================================
  // Sessions (Caisses)
  // ==========================================================================

  /**
   * Liste les sessions de caisse
   */
  listSessions: (filters?: SessionFilters) =>
    api.get<POSSession[]>(`${BASE_PATH}/sessions${buildQueryString(filters || {})}`),

  /**
   * Récupère une session par son ID
   */
  getSession: (id: string) =>
    api.get<POSSession>(`${BASE_PATH}/sessions/${id}`),

  /**
   * Ouvre une nouvelle session de caisse
   */
  openSession: (data: OpenSessionData) =>
    api.post<POSSession>(`${BASE_PATH}/sessions`, data),

  /**
   * Ferme une session de caisse
   */
  closeSession: (id: string, data: CloseSessionData) =>
    api.post<POSSession>(`${BASE_PATH}/sessions/${id}/close`, data),

  /**
   * Liste les mouvements de caisse d'une session
   */
  listCashMovements: (sessionId: string) =>
    api.get<POSCashMovement[]>(`${BASE_PATH}/sessions/${sessionId}/movements`),

  /**
   * Ajoute un mouvement de caisse
   */
  addCashMovement: (sessionId: string, data: {
    type: 'DEPOSIT' | 'WITHDRAWAL';
    amount: number;
    reason?: string;
  }) =>
    api.post<POSCashMovement>(`${BASE_PATH}/sessions/${sessionId}/movements`, data),

  // ==========================================================================
  // Transactions
  // ==========================================================================

  /**
   * Liste les transactions
   */
  listTransactions: (filters?: TransactionFilters) =>
    api.get<POSTransaction[]>(`${BASE_PATH}/transactions${buildQueryString(filters || {})}`),

  /**
   * Récupère une transaction par son ID
   */
  getTransaction: (id: string) =>
    api.get<POSTransaction>(`${BASE_PATH}/transactions/${id}`),

  /**
   * Crée une nouvelle transaction (vente)
   */
  createTransaction: (data: TransactionCreate) =>
    api.post<POSTransaction>(`${BASE_PATH}/transactions`, data),

  /**
   * Annule une transaction
   */
  voidTransaction: (id: string, reason?: string) =>
    api.post<POSTransaction>(`${BASE_PATH}/transactions/${id}/void`, { reason }),

  /**
   * Rembourse une transaction
   */
  refundTransaction: (id: string, data?: {
    items?: Array<{ item_id: string; quantity: number }>;
    amount?: number;
    reason?: string;
  }) =>
    api.post<POSTransaction>(`${BASE_PATH}/transactions/${id}/refund`, data || {}),

  /**
   * Imprime un ticket
   */
  printReceipt: (transactionId: string) =>
    api.post<{ url: string }>(`${BASE_PATH}/transactions/${transactionId}/receipt`, {}),
};

export default posApi;
