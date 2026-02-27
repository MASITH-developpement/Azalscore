/**
 * AZALSCORE - POS React Query Hooks
 * ==================================
 * Hooks pour le module Point de Vente (POS)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serializeFilters } from '@core/query-keys';
import { posApi } from './api';
import type {
  POSStore,
  POSTerminal,
  POSTransaction,
  POSDashboard,
  SessionFilters,
  OpenSessionData,
} from './api';
import type { POSSession } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { POSStore, POSTerminal, POSTransaction, POSDashboard };

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const posKeys = {
  all: ['pos'] as const,

  // Dashboard
  dashboard: () => [...posKeys.all, 'dashboard'] as const,

  // Stores
  stores: () => [...posKeys.all, 'stores'] as const,
  storesList: () => [...posKeys.stores(), 'list'] as const,
  storeDetail: (id: string) => [...posKeys.stores(), id] as const,

  // Terminals
  terminals: () => [...posKeys.all, 'terminals'] as const,
  terminalsList: (storeId?: string) => [...posKeys.terminals(), 'list', storeId ?? null] as const,
  terminalDetail: (id: string) => [...posKeys.terminals(), id] as const,

  // Sessions
  sessions: () => [...posKeys.all, 'sessions'] as const,
  sessionsList: (filters?: SessionFilters) => [...posKeys.sessions(), 'list', serializeFilters(filters)] as const,
  sessionDetail: (id: string) => [...posKeys.sessions(), id] as const,

  // Transactions
  transactions: () => [...posKeys.all, 'transactions'] as const,
  transactionsList: (sessionId?: string) => [...posKeys.transactions(), 'list', sessionId ?? null] as const,
  transactionDetail: (id: string) => [...posKeys.transactions(), id] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const usePOSDashboard = () => {
  return useQuery({
    queryKey: posKeys.dashboard(),
    queryFn: async () => {
      const response = await posApi.getDashboard();
      return response.data;
    },
  });
};

// ============================================================================
// STORE HOOKS
// ============================================================================

export const useStores = () => {
  return useQuery({
    queryKey: posKeys.storesList(),
    queryFn: async () => {
      const response = await posApi.listStores();
      return response.data;
    },
  });
};

// ============================================================================
// TERMINAL HOOKS
// ============================================================================

export const useTerminals = (storeId?: string) => {
  return useQuery({
    queryKey: posKeys.terminalsList(storeId),
    queryFn: async () => {
      const response = await posApi.listTerminals(storeId ? { store_id: storeId } : undefined);
      return response.data;
    },
  });
};

// ============================================================================
// SESSION HOOKS
// ============================================================================

export const useSessions = (filters?: { status?: string; store_id?: string }) => {
  return useQuery({
    queryKey: posKeys.sessionsList(filters as SessionFilters),
    queryFn: async () => {
      const response = await posApi.listSessions(filters as SessionFilters);
      return response.data;
    },
  });
};

export const useSession = (id: string) => {
  return useQuery({
    queryKey: posKeys.sessionDetail(id),
    queryFn: async () => {
      const response = await posApi.getSession(id);
      return response.data as POSSession;
    },
    enabled: !!id,
  });
};

export const useOpenSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OpenSessionData) => {
      const response = await posApi.openSession(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: posKeys.all });
    },
  });
};

export const useCloseSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, closing_balance }: { id: string; closing_balance: number }) => {
      const response = await posApi.closeSession(id, { closing_balance });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: posKeys.all });
    },
  });
};

// ============================================================================
// TRANSACTION HOOKS
// ============================================================================

export const useTransactions = (sessionId?: string) => {
  return useQuery({
    queryKey: posKeys.transactionsList(sessionId),
    queryFn: async () => {
      const response = await posApi.listTransactions(sessionId ? { session_id: sessionId } : undefined);
      return response.data;
    },
  });
};
