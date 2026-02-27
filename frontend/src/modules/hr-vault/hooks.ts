/**
 * AZALSCORE Module - HR Vault Hooks
 * React Query hooks for HR Vault
 */

import { useQuery } from '@tanstack/react-query';
import { hrVaultApi } from './api';
import type { VaultDocumentFilters } from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const hrVaultKeys = {
  all: ['hr-vault'] as const,
  dashboard: () => [...hrVaultKeys.all, 'dashboard', 'stats'] as const,
  documents: (filters: VaultDocumentFilters, page: number, pageSize: number) =>
    [...hrVaultKeys.all, 'documents', filters, page, pageSize] as const,
  document: (id: string) => [...hrVaultKeys.all, 'documents', id] as const,
  documentVersions: (id: string) => [...hrVaultKeys.all, 'documents', id, 'versions'] as const,
  categories: () => [...hrVaultKeys.all, 'categories'] as const,
  gdpr: (status?: string) => [...hrVaultKeys.all, 'gdpr', status] as const,
  alerts: (unreadOnly: boolean) => [...hrVaultKeys.all, 'alerts', unreadOnly] as const,
  expiring: () => [...hrVaultKeys.all, 'expiring'] as const,
  pendingSignatures: () => [...hrVaultKeys.all, 'pending-signatures'] as const,
  accessLogs: (documentId?: string) => [...hrVaultKeys.all, 'access-logs', documentId] as const,
};

// ============================================================================
// DASHBOARD & STATS
// ============================================================================

export const useDashboardStats = () => {
  return useQuery({
    queryKey: hrVaultKeys.dashboard(),
    queryFn: async () => {
      const response = await hrVaultApi.getDashboardStats();
      return response.data;
    },
  });
};

export const useExpiringDocuments = () => {
  return useQuery({
    queryKey: hrVaultKeys.expiring(),
    queryFn: async () => {
      const response = await hrVaultApi.getExpiringDocuments(30);
      return response.data;
    },
  });
};

export const usePendingSignatures = () => {
  return useQuery({
    queryKey: hrVaultKeys.pendingSignatures(),
    queryFn: async () => {
      const response = await hrVaultApi.getPendingSignatures();
      return response.data;
    },
  });
};

// ============================================================================
// DOCUMENTS
// ============================================================================

export const useDocuments = (filters: VaultDocumentFilters, page: number, pageSize: number) => {
  return useQuery({
    queryKey: hrVaultKeys.documents(filters, page, pageSize),
    queryFn: async () => {
      const response = await hrVaultApi.listDocuments(filters, page, pageSize);
      return response.data;
    },
  });
};

export const useDocument = (id: string) => {
  return useQuery({
    queryKey: hrVaultKeys.document(id),
    queryFn: async () => {
      const response = await hrVaultApi.getDocument(id);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useDocumentVersions = (id: string) => {
  return useQuery({
    queryKey: hrVaultKeys.documentVersions(id),
    queryFn: async () => {
      const response = await hrVaultApi.getDocumentVersions(id);
      return response.data;
    },
    enabled: !!id,
  });
};

// ============================================================================
// CATEGORIES
// ============================================================================

export const useCategories = () => {
  return useQuery({
    queryKey: hrVaultKeys.categories(),
    queryFn: async () => {
      const response = await hrVaultApi.listCategories();
      return response.data;
    },
  });
};

// ============================================================================
// GDPR
// ============================================================================

export const useGDPRRequests = (status?: string) => {
  return useQuery({
    queryKey: hrVaultKeys.gdpr(status),
    queryFn: async () => {
      const response = await hrVaultApi.listGDPRRequests(undefined, undefined, status);
      return response.data;
    },
  });
};

// ============================================================================
// ALERTS & ACCESS LOGS
// ============================================================================

export const useAlerts = (unreadOnly = false) => {
  return useQuery({
    queryKey: hrVaultKeys.alerts(unreadOnly),
    queryFn: async () => {
      const response = await hrVaultApi.listAlerts(unreadOnly);
      return response.data;
    },
  });
};

export const useAccessLogs = (documentId?: string) => {
  return useQuery({
    queryKey: hrVaultKeys.accessLogs(documentId),
    queryFn: async () => {
      const response = await hrVaultApi.listAccessLogs(documentId);
      return response.data;
    },
    enabled: !!documentId,
  });
};
