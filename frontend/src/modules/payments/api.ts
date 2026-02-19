/**
 * AZALSCORE - Payments API
 * ========================
 * API client complet et typé pour le module Paiements.
 * Couvre: Transactions, Remboursements, Moyens de paiement, Statistiques
 */

import { api } from '@/core/api-client';
import type {
  Payment,
  Refund,
  SavedPaymentMethod,
  PaymentStats,
  PaymentStatus,
  PaymentMethod,
  RefundStatus,
} from './types';

// ============================================================================
// TYPES - Re-export des types pour faciliter l'import
// ============================================================================

export type {
  Payment,
  Refund,
  SavedPaymentMethod,
  PaymentStats,
  PaymentStatus,
  PaymentMethod,
  RefundStatus,
};

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

/**
 * Liste paginée de paiements
 */
export interface PaymentList {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Paramètres de filtrage des paiements
 */
export interface PaymentFilters {
  status?: PaymentStatus;
  method?: PaymentMethod;
  date_from?: string;
  date_to?: string;
  customer_id?: string;
  invoice_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

/**
 * Paramètres de filtrage des remboursements
 */
export interface RefundFilters {
  status?: RefundStatus;
  payment_id?: string;
  page?: number;
  page_size?: number;
}

/**
 * Paramètres de filtrage des moyens de paiement
 */
export interface PaymentMethodFilters {
  customer_id?: string;
  type?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

/**
 * Données pour créer un remboursement
 */
export interface RefundCreate {
  payment_id: string;
  amount: number;
  reason: string;
  notes?: string;
}

/**
 * Données pour créer un paiement
 */
export interface PaymentCreate {
  amount: number;
  currency?: string;
  method: PaymentMethod;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  invoice_id?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Résultat d'une tentative de relance de paiement
 */
export interface PaymentRetryResult {
  success: boolean;
  payment: Payment;
  message?: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/payments';

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

export const paymentsApi = {
  // ==========================================================================
  // Dashboard / Statistics
  // ==========================================================================

  /**
   * Récupère les statistiques agrégées des paiements
   */
  getSummary: () =>
    api.get<PaymentStats>(`${BASE_PATH}/summary`),

  // ==========================================================================
  // Payments (Transactions)
  // ==========================================================================

  /**
   * Liste les paiements avec filtres optionnels
   */
  listPayments: (filters?: PaymentFilters) =>
    api.get<PaymentList>(`${BASE_PATH}${buildQueryString(filters || {})}`),

  /**
   * Récupère un paiement par son ID
   */
  getPayment: (paymentId: string) =>
    api.get<Payment>(`${BASE_PATH}/${paymentId}`),

  /**
   * Crée un nouveau paiement
   */
  createPayment: (data: PaymentCreate) =>
    api.post<Payment>(BASE_PATH, data),

  /**
   * Relance un paiement échoué
   */
  retryPayment: (paymentId: string) =>
    api.post<PaymentRetryResult>(`${BASE_PATH}/${paymentId}/retry`, {}),

  /**
   * Annule un paiement en attente
   */
  cancelPayment: (paymentId: string) =>
    api.post<Payment>(`${BASE_PATH}/${paymentId}/cancel`, {}),

  // ==========================================================================
  // Refunds (Remboursements)
  // ==========================================================================

  /**
   * Liste les remboursements avec filtres optionnels
   */
  listRefunds: (filters?: RefundFilters) =>
    api.get<Refund[]>(`${BASE_PATH}/refunds${buildQueryString(filters || {})}`),

  /**
   * Récupère un remboursement par son ID
   */
  getRefund: (refundId: string) =>
    api.get<Refund>(`${BASE_PATH}/refunds/${refundId}`),

  /**
   * Crée un remboursement pour un paiement
   */
  createRefund: (data: RefundCreate) =>
    api.post<Refund>(`${BASE_PATH}/refunds`, data),

  // ==========================================================================
  // Payment Methods (Moyens de paiement enregistrés)
  // ==========================================================================

  /**
   * Liste les moyens de paiement enregistrés
   */
  listPaymentMethods: (filters?: PaymentMethodFilters) =>
    api.get<SavedPaymentMethod[]>(
      `${BASE_PATH}/methods${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un moyen de paiement par son ID
   */
  getPaymentMethod: (methodId: string) =>
    api.get<SavedPaymentMethod>(`${BASE_PATH}/methods/${methodId}`),

  /**
   * Désactive un moyen de paiement
   */
  deactivatePaymentMethod: (methodId: string) =>
    api.post<SavedPaymentMethod>(`${BASE_PATH}/methods/${methodId}/deactivate`, {}),

  /**
   * Définit un moyen de paiement comme par défaut
   */
  setDefaultPaymentMethod: (methodId: string) =>
    api.post<SavedPaymentMethod>(`${BASE_PATH}/methods/${methodId}/set-default`, {}),
};

export default paymentsApi;
