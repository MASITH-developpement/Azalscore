/**
 * AZALSCORE Module - HR Vault - API
 * ===================================
 * Client API pour le module Coffre-fort RH
 */

import { api } from '@core/api-client';
import type {
  VaultCategory,
  VaultCategoryCreate,
  VaultDocument,
  VaultDocumentFilters,
  VaultDocumentListResponse,
  VaultDocumentUpdate,
  VaultDashboardStats,
  VaultEmployeeStats,
  VaultGDPRRequest,
  VaultGDPRRequestCreate,
  VaultAccessLog,
  VaultAlert,
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

const BASE_PATH = '/v1/hr-vault';

// ============================================================================
// CATEGORIES
// ============================================================================

export const hrVaultApi = {
  // --------------------------------------------------------------------------
  // Categories
  // --------------------------------------------------------------------------
  listCategories: (includeInactive = false) =>
    api.get<VaultCategory[]>(`${BASE_PATH}/categories${buildQueryString({ include_inactive: includeInactive })}`),

  getCategory: (categoryId: string) =>
    api.get<VaultCategory>(`${BASE_PATH}/categories/${categoryId}`),

  createCategory: (data: VaultCategoryCreate) =>
    api.post<VaultCategory>(`${BASE_PATH}/categories`, data),

  updateCategory: (categoryId: string, data: Partial<VaultCategoryCreate>) =>
    api.put<VaultCategory>(`${BASE_PATH}/categories/${categoryId}`, data),

  deleteCategory: (categoryId: string) =>
    api.delete<void>(`${BASE_PATH}/categories/${categoryId}`),

  // --------------------------------------------------------------------------
  // Documents
  // --------------------------------------------------------------------------
  listDocuments: (filters: VaultDocumentFilters = {}, page = 1, pageSize = 50) =>
    api.get<VaultDocumentListResponse>(
      `${BASE_PATH}/documents${buildQueryString({
        employee_id: filters.employee_id,
        document_type: filters.document_type,
        category_id: filters.category_id,
        status: filters.status,
        signature_status: filters.signature_status,
        date_from: filters.date_from,
        date_to: filters.date_to,
        pay_period: filters.pay_period,
        search: filters.search,
        page,
        page_size: pageSize,
      })}`
    ),

  getDocument: (documentId: string) =>
    api.get<VaultDocument>(`${BASE_PATH}/documents/${documentId}`),

  uploadDocument: (formData: FormData) =>
    api.post<VaultDocument>(`${BASE_PATH}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  updateDocument: (documentId: string, data: VaultDocumentUpdate) =>
    api.put<VaultDocument>(`${BASE_PATH}/documents/${documentId}`, data),

  deleteDocument: (documentId: string, reason?: string, force = false) =>
    api.delete<void>(`${BASE_PATH}/documents/${documentId}${buildQueryString({ reason, force })}`),

  downloadDocument: (documentId: string) =>
    api.get<Blob>(`${BASE_PATH}/documents/${documentId}/download`, {
      responseType: 'blob',
    }),

  getDocumentVersions: (documentId: string) =>
    api.get<Array<{
      id: string;
      version_number: number;
      file_name: string;
      file_size: number;
      created_at: string;
    }>>(`${BASE_PATH}/documents/${documentId}/versions`),

  // --------------------------------------------------------------------------
  // Employee Documents
  // --------------------------------------------------------------------------
  listEmployeeDocuments: (employeeId: string, documentType?: string, page = 1, pageSize = 50) =>
    api.get<VaultDocumentListResponse>(
      `${BASE_PATH}/employees/${employeeId}/documents${buildQueryString({
        document_type: documentType,
        page,
        page_size: pageSize,
      })}`
    ),

  getEmployeeStats: (employeeId: string) =>
    api.get<VaultEmployeeStats>(`${BASE_PATH}/employees/${employeeId}/stats`),

  exportEmployeeFolder: (employeeId: string, documentTypes?: string[], periodStart?: string, periodEnd?: string) =>
    api.post<{
      export_id: string;
      status: string;
      download_url?: string;
      expires_at?: string;
    }>(`${BASE_PATH}/employees/${employeeId}/export`, {
      employee_id: employeeId,
      document_types: documentTypes,
      period_start: periodStart,
      period_end: periodEnd,
    }),

  // --------------------------------------------------------------------------
  // Signature
  // --------------------------------------------------------------------------
  requestSignature: (documentId: string, signers: Array<{ email: string; name: string }>, message?: string) =>
    api.post<{
      document_id: string;
      signature_status: string;
      signature_request_id?: string;
    }>(`${BASE_PATH}/documents/${documentId}/signature`, {
      document_id: documentId,
      signers,
      message,
    }),

  // --------------------------------------------------------------------------
  // GDPR
  // --------------------------------------------------------------------------
  listGDPRRequests: (
    employeeId?: string,
    requestType?: string,
    status?: string,
    page = 1,
    pageSize = 50
  ) =>
    api.get<VaultGDPRRequest[]>(
      `${BASE_PATH}/gdpr-requests${buildQueryString({
        employee_id: employeeId,
        request_type: requestType,
        status,
        page,
        page_size: pageSize,
      })}`
    ),

  getGDPRRequest: (requestId: string) =>
    api.get<VaultGDPRRequest>(`${BASE_PATH}/gdpr-requests/${requestId}`),

  createGDPRRequest: (data: VaultGDPRRequestCreate) =>
    api.post<VaultGDPRRequest>(`${BASE_PATH}/gdpr-requests`, data),

  processGDPRRequest: (requestId: string, status: string, responseDetails?: string) =>
    api.post<VaultGDPRRequest>(`${BASE_PATH}/gdpr-requests/${requestId}/process`, {
      status,
      response_details: responseDetails,
    }),

  downloadGDPRExport: (requestId: string) =>
    api.get<Blob>(`${BASE_PATH}/gdpr-requests/${requestId}/download`, {
      responseType: 'blob',
    }),

  // --------------------------------------------------------------------------
  // Consents
  // --------------------------------------------------------------------------
  createConsent: (employeeId: string, consentType: string, consentVersion: string, given = true) =>
    api.post<{
      id: string;
      consent_type: string;
      given: boolean;
      given_at?: string;
    }>(`${BASE_PATH}/consents`, {
      employee_id: employeeId,
      consent_type: consentType,
      consent_version: consentVersion,
      given,
    }),

  getConsent: (employeeId: string, consentType: string) =>
    api.get<{
      id: string;
      consent_type: string;
      given: boolean;
      given_at?: string;
      revoked_at?: string;
    }>(`${BASE_PATH}/consents/${employeeId}/${consentType}`),

  revokeConsent: (employeeId: string, consentType: string) =>
    api.delete<void>(`${BASE_PATH}/consents/${employeeId}/${consentType}`),

  // --------------------------------------------------------------------------
  // Access Logs
  // --------------------------------------------------------------------------
  listAccessLogs: (
    documentId?: string,
    employeeId?: string,
    accessedBy?: string,
    accessType?: string,
    dateFrom?: string,
    dateTo?: string,
    page = 1,
    pageSize = 100
  ) =>
    api.get<{
      items: VaultAccessLog[];
      total: number;
      page: number;
      page_size: number;
    }>(
      `${BASE_PATH}/access-logs${buildQueryString({
        document_id: documentId,
        employee_id: employeeId,
        accessed_by: accessedBy,
        access_type: accessType,
        date_from: dateFrom,
        date_to: dateTo,
        page,
        page_size: pageSize,
      })}`
    ),

  // --------------------------------------------------------------------------
  // Alerts
  // --------------------------------------------------------------------------
  listAlerts: (unreadOnly = false) =>
    api.get<VaultAlert[]>(`${BASE_PATH}/alerts${buildQueryString({ unread_only: unreadOnly })}`),

  markAlertRead: (alertId: string) =>
    api.post<void>(`${BASE_PATH}/alerts/${alertId}/read`),

  dismissAlert: (alertId: string) =>
    api.post<void>(`${BASE_PATH}/alerts/${alertId}/dismiss`),

  // --------------------------------------------------------------------------
  // Dashboard & Stats
  // --------------------------------------------------------------------------
  getDashboardStats: () =>
    api.get<VaultDashboardStats>(`${BASE_PATH}/dashboard/stats`),

  getExpiringDocuments: (days = 30) =>
    api.get<VaultDocument[]>(`${BASE_PATH}/dashboard/expiring-documents${buildQueryString({ days })}`),

  getPendingSignatures: () =>
    api.get<VaultDocument[]>(`${BASE_PATH}/dashboard/pending-signatures`),
};

export default hrVaultApi;
