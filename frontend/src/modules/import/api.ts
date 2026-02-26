/**
 * AZALSCORE - Import API
 * =======================
 * Unified API client for Data Import from external sources.
 * Currently supports: Odoo
 * Planned: Axonaut, Pennylane, Sage, Chorus Pro
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// Re-export Odoo Import API for backward compatibility
export * from '../odoo-import/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const importKeys = {
  all: ['import'] as const,
  sources: () => [...importKeys.all, 'sources'] as const,
  odoo: () => [...importKeys.all, 'odoo'] as const,
  odooConfigs: () => [...importKeys.odoo(), 'configs'] as const,
  odooHistory: () => [...importKeys.odoo(), 'history'] as const,
  axonaut: () => [...importKeys.all, 'axonaut'] as const,
  pennylane: () => [...importKeys.all, 'pennylane'] as const,
  sage: () => [...importKeys.all, 'sage'] as const,
  chorus: () => [...importKeys.all, 'chorus'] as const,
};

// ============================================================================
// TYPES - COMMON
// ============================================================================

export type ImportSource = 'odoo' | 'axonaut' | 'pennylane' | 'sage' | 'chorus';

export interface ImportSourceConfig {
  source: ImportSource;
  name: string;
  description: string;
  apiPrefix: string;
  isAvailable: boolean;
  requiredFields: string[];
}

export interface ImportHistoryItem {
  id: string;
  source: ImportSource;
  import_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string | null;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  error_count: number;
  error_message?: string | null;
}

export interface SyncDirection {
  import: boolean;  // Source -> AZALSCORE
  export: boolean;  // AZALSCORE -> Source
}

// ============================================================================
// CONSTANTS
// ============================================================================

export const IMPORT_SOURCES: ImportSourceConfig[] = [
  {
    source: 'odoo',
    name: 'Odoo',
    description: 'Import depuis Odoo (versions 8-18) via XML-RPC',
    apiPrefix: '/odoo',
    isAvailable: true,
    requiredFields: ['url', 'database', 'username', 'apiKey'],
  },
  {
    source: 'axonaut',
    name: 'Axonaut',
    description: 'Import depuis Axonaut via API REST',
    apiPrefix: '/axonaut',
    isAvailable: false,
    requiredFields: ['apiKey'],
  },
  {
    source: 'pennylane',
    name: 'Pennylane',
    description: 'Import depuis Pennylane via API REST',
    apiPrefix: '/pennylane',
    isAvailable: false,
    requiredFields: ['apiKey'],
  },
  {
    source: 'sage',
    name: 'Sage',
    description: 'Import depuis Sage via fichiers export',
    apiPrefix: '/sage',
    isAvailable: false,
    requiredFields: ['url', 'username', 'apiKey'],
  },
  {
    source: 'chorus',
    name: 'Chorus Pro',
    description: 'Import depuis Chorus Pro (factures publiques)',
    apiPrefix: '/chorus',
    isAvailable: false,
    requiredFields: ['username', 'apiKey'],
  },
];

export const DEFAULT_SYNC_DIRECTION: SyncDirection = { import: true, export: false };

// ============================================================================
// HOOKS - SOURCE MANAGEMENT
// ============================================================================

export function useImportSources() {
  return useQuery({
    queryKey: importKeys.sources(),
    queryFn: async () => {
      // For now, return the static configuration
      // In the future, this could fetch from the backend
      return IMPORT_SOURCES;
    },
    staleTime: Infinity, // This data doesn't change
  });
}

export function useAvailableImportSources() {
  return useQuery({
    queryKey: [...importKeys.sources(), 'available'],
    queryFn: async () => {
      return IMPORT_SOURCES.filter(s => s.isAvailable);
    },
    staleTime: Infinity,
  });
}

// ============================================================================
// HOOKS - ODOO (Wrapper hooks for convenience)
// ============================================================================

export function useOdooConfigurations() {
  return useQuery({
    queryKey: importKeys.odooConfigs(),
    queryFn: async () => {
      try {
        const response = await api.get<unknown[]>('/odoo/config');
        return Array.isArray(response) ? response : [];
      } catch {
        return [];
      }
    },
  });
}

export function useOdooImportHistory() {
  return useQuery({
    queryKey: importKeys.odooHistory(),
    queryFn: async () => {
      try {
        const response = await api.get<ImportHistoryItem[]>('/odoo/history');
        return Array.isArray(response) ? response : [];
      } catch {
        return [];
      }
    },
  });
}

export function useSaveOdooConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id?: string; data: {
      name: string;
      odoo_url: string;
      odoo_database: string;
      auth_method: string;
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
    }}) => {
      if (id) {
        return api.put(`/odoo/config/${id}`, data);
      } else {
        return api.post('/odoo/config', data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooConfigs() });
    },
  });
}

export function useTestOdooConnectionDirect() {
  return useMutation({
    mutationFn: async (data: {
      odoo_url: string;
      odoo_database: string;
      username: string;
      credential: string;
      auth_method?: string;
    }) => {
      return api.post<{ success: boolean; message: string; odoo_version?: string }>('/odoo/test', data);
    },
  });
}

export function useTestOdooConfigConnectionDirect() {
  return useMutation({
    mutationFn: async (configId: string) => {
      return api.post<{ success: boolean; message: string }>(`/odoo/config/${configId}/test`);
    },
  });
}

export function useLaunchOdooImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ configId, importType }: { configId: string; importType: string }) => {
      return api.post(`/odoo/import/${importType}?config_id=${configId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooHistory() });
    },
  });
}

export function useDeleteOdooConfiguration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/odoo/config/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooConfigs() });
    },
  });
}

// ============================================================================
// HOOKS - FUTURE SOURCES (Stubs)
// ============================================================================

// Axonaut
export function useAxonautConfig() {
  return useQuery({
    queryKey: importKeys.axonaut(),
    queryFn: async () => {
      // Not implemented yet
      return null;
    },
    enabled: false,
  });
}

// Pennylane
export function usePennylaneConfig() {
  return useQuery({
    queryKey: importKeys.pennylane(),
    queryFn: async () => {
      // Not implemented yet
      return null;
    },
    enabled: false,
  });
}

// Sage
export function useSageConfig() {
  return useQuery({
    queryKey: importKeys.sage(),
    queryFn: async () => {
      // Not implemented yet
      return null;
    },
    enabled: false,
  });
}

// Chorus Pro
export function useChorusConfig() {
  return useQuery({
    queryKey: importKeys.chorus(),
    queryFn: async () => {
      // Not implemented yet
      return null;
    },
    enabled: false,
  });
}
