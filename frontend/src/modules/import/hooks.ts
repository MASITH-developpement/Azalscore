/**
 * AZALSCORE - Import Module React Query Hooks
 * ============================================
 * Hooks pour le module Import de donnees (Odoo, Axonaut, etc.)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type { ApiMutationError } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

export interface ImportHistoryItem {
  id: string;
  import_type: string;
  status: string;
  started_at: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  error_count: number;
  records_failed?: number;
}

export interface SyncDirection {
  import: boolean;
  export: boolean;
}

export interface OdooConfig {
  id?: string;
  name: string;
  odoo_url: string;
  database: string;
  username: string;
  api_key: string;
  odoo_version?: number;
  sync_products: boolean;
  sync_products_direction: SyncDirection;
  sync_contacts: boolean;
  sync_contacts_direction: SyncDirection;
  sync_suppliers: boolean;
  sync_suppliers_direction: SyncDirection;
  sync_purchase_orders: boolean;
  sync_purchase_orders_direction: SyncDirection;
  sync_sale_orders: boolean;
  sync_sale_orders_direction: SyncDirection;
  sync_invoices: boolean;
  sync_invoices_direction: SyncDirection;
  sync_quotes: boolean;
  sync_quotes_direction: SyncDirection;
  sync_accounting: boolean;
  sync_accounting_direction: SyncDirection;
  sync_bank: boolean;
  sync_bank_direction: SyncDirection;
  sync_interventions: boolean;
  sync_interventions_direction: SyncDirection;
}

export type ImportType = 'products' | 'contacts' | 'suppliers' | 'purchase_orders' | 'sale_orders' | 'invoices' | 'quotes' | 'accounting' | 'bank' | 'interventions' | 'full';

export type ImportSource = 'odoo' | 'axonaut' | 'pennylane' | 'sage' | 'chorus';

interface OdooConfigResponse {
  id: string;
  name?: string;
  odoo_url?: string;
  odoo_database?: string;
  username?: string;
  sync_products?: boolean;
  sync_products_direction?: SyncDirection;
  sync_contacts?: boolean;
  sync_contacts_direction?: SyncDirection;
  sync_suppliers?: boolean;
  sync_suppliers_direction?: SyncDirection;
  sync_purchase_orders?: boolean;
  sync_purchase_orders_direction?: SyncDirection;
  sync_sale_orders?: boolean;
  sync_sale_orders_direction?: SyncDirection;
  sync_invoices?: boolean;
  sync_invoices_direction?: SyncDirection;
  sync_quotes?: boolean;
  sync_quotes_direction?: SyncDirection;
  sync_accounting?: boolean;
  sync_accounting_direction?: SyncDirection;
  sync_bank?: boolean;
  sync_bank_direction?: SyncDirection;
  sync_interventions?: boolean;
  sync_interventions_direction?: SyncDirection;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const importKeys = {
  all: ['import'] as const,
  odoo: () => [...importKeys.all, 'odoo'] as const,
  odooConfigs: () => [...importKeys.odoo(), 'configs'] as const,
  odooHistory: () => [...importKeys.odoo(), 'history'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useOdooConfigs = () => {
  return useQuery({
    queryKey: importKeys.odooConfigs(),
    queryFn: async () => {
      try {
        const response = await api.get<OdooConfigResponse[]>('/odoo/config');
        return Array.isArray(response) ? response : [];
      } catch {
        return [];
      }
    },
  });
};

export const useOdooHistory = () => {
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
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useSaveOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OdooConfig) => {
      const payload = {
        name: data.name,
        odoo_url: data.odoo_url,
        odoo_database: data.database,
        auth_method: 'api_key',
        username: data.username,
        credential: data.api_key,
        sync_products: data.sync_products,
        sync_contacts: data.sync_contacts,
        sync_suppliers: data.sync_suppliers,
        sync_purchase_orders: data.sync_purchase_orders,
        sync_sale_orders: data.sync_sale_orders,
        sync_invoices: data.sync_invoices,
        sync_quotes: data.sync_quotes,
        sync_accounting: data.sync_accounting,
        sync_bank: data.sync_bank,
        sync_interventions: data.sync_interventions,
      };
      if (data.id) {
        return api.put(`/odoo/config/${data.id}`, payload);
      } else {
        return api.post('/odoo/config', payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooConfigs() });
    },
  });
};

export const useTestOdooConnection = () => {
  return useMutation({
    mutationFn: async (params: { configId?: string; config?: OdooConfig }) => {
      if (params.configId) {
        return api.post<{ success?: boolean; message?: string }>(`/odoo/config/${params.configId}/test`);
      } else if (params.config) {
        return api.post<{ success?: boolean; message?: string }>('/odoo/test', {
          odoo_url: params.config.odoo_url,
          odoo_database: params.config.database,
          username: params.config.username,
          credential: params.config.api_key,
          auth_method: 'api_key',
        });
      }
      throw new Error('Either configId or config must be provided');
    },
  });
};

export const useOdooImport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { configId: string; type: ImportType }) => {
      return api.post(`/odoo/import/${params.type}?config_id=${params.configId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooHistory() });
    },
  });
};

export const useDeleteOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/odoo/config/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importKeys.odooConfigs() });
    },
  });
};
