/**
 * AZALS MODULE GAP-086 - Integration Hub - Hooks
 * React Query hooks pour l'API Integration
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import integrationApi from './api';
import type { ConnectionStatus, SyncStatus } from './types';

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useConnectors = (category?: string) => {
  return useQuery({
    queryKey: ['integration', 'connectors', category],
    queryFn: () => integrationApi.listConnectors(category),
  });
};

export const useConnections = (page = 1, pageSize = 20, filters?: { search?: string; status?: string }) => {
  const apiFilters = filters ? {
    search: filters.search,
    status: filters.status ? [filters.status as ConnectionStatus] : undefined,
  } : undefined;
  return useQuery({
    queryKey: ['integration', 'connections', page, pageSize, filters],
    queryFn: () => integrationApi.listConnections(apiFilters, page, pageSize),
  });
};

export const useConnection = (id: string) => {
  return useQuery({
    queryKey: ['integration', 'connections', id],
    queryFn: () => integrationApi.getConnection(id),
    enabled: !!id,
  });
};

export const useConnectionStats = (id: string) => {
  return useQuery({
    queryKey: ['integration', 'connections', id, 'stats'],
    queryFn: () => integrationApi.getConnectionStats(id),
    enabled: !!id,
  });
};

export const useExecutions = (page = 1, pageSize = 20, filters?: { connection_id?: string; status?: string }) => {
  const apiFilters = filters ? {
    connection_id: filters.connection_id,
    status: filters.status ? [filters.status as SyncStatus] : undefined,
  } : undefined;
  return useQuery({
    queryKey: ['integration', 'executions', page, pageSize, filters],
    queryFn: () => integrationApi.listExecutions(apiFilters, page, pageSize),
  });
};

export const useConflicts = (page = 1, pageSize = 20, isResolved?: boolean) => {
  return useQuery({
    queryKey: ['integration', 'conflicts', page, pageSize, isResolved],
    queryFn: () => integrationApi.listConflicts({ is_resolved: isResolved }, page, pageSize),
  });
};

export const useWebhooks = (connectionId?: string) => {
  return useQuery({
    queryKey: ['integration', 'webhooks', connectionId],
    queryFn: () => integrationApi.listWebhooks(connectionId),
  });
};

export const useIntegrationStats = () => {
  return useQuery({
    queryKey: ['integration', 'stats'],
    queryFn: () => integrationApi.getStats(),
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useDeleteConnection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.deleteConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
    },
  });
};

export const useTestConnection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.testConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
    },
  });
};

export const useCancelExecution = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.cancelExecution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'executions'] });
    },
  });
};

export const useRetryExecution = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.retryExecution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'executions'] });
    },
  });
};
