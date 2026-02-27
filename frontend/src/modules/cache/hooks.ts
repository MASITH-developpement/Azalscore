/**
 * AZALSCORE Module - Cache - React Query Hooks
 * Hooks pour la gestion du cache applicatif
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cacheApi } from './api';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const cacheKeys = {
  all: ['cache'] as const,
  dashboard: () => [...cacheKeys.all, 'dashboard'] as const,
  regions: () => [...cacheKeys.all, 'regions'] as const,
  alerts: () => [...cacheKeys.all, 'alerts'] as const,
  preload: () => [...cacheKeys.all, 'preload'] as const,
  audit: () => [...cacheKeys.all, 'audit'] as const,
};

// ============================================================================
// DASHBOARD
// ============================================================================

export const useCacheDashboard = () => {
  return useQuery({
    queryKey: cacheKeys.dashboard(),
    queryFn: async () => {
      const response = await cacheApi.getDashboard();
      return response.data;
    },
    refetchInterval: 30000, // Refresh toutes les 30s
  });
};

// ============================================================================
// REGIONS
// ============================================================================

export const useCacheRegions = () => {
  return useQuery({
    queryKey: cacheKeys.regions(),
    queryFn: async () => {
      const response = await cacheApi.listRegions();
      return response.data;
    },
  });
};

export const useDeleteRegion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (regionId: string) => cacheApi.deleteRegion(regionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.regions() });
    },
  });
};

// ============================================================================
// ALERTS
// ============================================================================

export const useCacheAlerts = () => {
  return useQuery({
    queryKey: cacheKeys.alerts(),
    queryFn: async () => {
      const response = await cacheApi.listAlerts();
      return response.data;
    },
  });
};

export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => cacheApi.acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.alerts() });
    },
  });
};

export const useResolveAlert = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => cacheApi.resolveAlert(alertId, 'Resolu via admin'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.alerts() });
    },
  });
};

export const useCheckThresholds = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cacheApi.checkThresholds(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.alerts() });
    },
  });
};

// ============================================================================
// PRELOAD TASKS
// ============================================================================

export const usePreloadTasks = () => {
  return useQuery({
    queryKey: cacheKeys.preload(),
    queryFn: async () => {
      const response = await cacheApi.listPreloadTasks();
      return response.data;
    },
  });
};

export const useRunPreloadTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => cacheApi.runPreloadTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.preload() });
    },
  });
};

// ============================================================================
// AUDIT
// ============================================================================

export const useAuditLogs = () => {
  return useQuery({
    queryKey: cacheKeys.audit(),
    queryFn: async () => {
      const response = await cacheApi.getAuditLogs();
      return response.data;
    },
  });
};

// ============================================================================
// CACHE OPERATIONS
// ============================================================================

export const useInvalidateAll = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cacheApi.invalidateAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

export const usePurgeCache = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cacheApi.purge({ expired_only: true, confirm: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

export const useInvalidateByKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (key: string) => cacheApi.invalidateByKey(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

export const useInvalidateByPattern = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pattern: string) => cacheApi.invalidateByPattern(pattern),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

export const useInvalidateByTag = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tag: string) => cacheApi.invalidateByTag(tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

export const useInvalidateByEntity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entityType, entityId }: { entityType: string; entityId?: string }) =>
      cacheApi.invalidateByEntity(entityType, entityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};

// ============================================================================
// CONFIG
// ============================================================================

export const useUpdateCacheConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => cacheApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.dashboard() });
    },
  });
};

export const useCreateCacheConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cacheApi.createConfig({}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: cacheKeys.all });
    },
  });
};
