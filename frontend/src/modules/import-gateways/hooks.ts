/**
 * AZALSCORE Module - Import Gateways - React Query Hooks
 * Hooks pour la gestion des connexions d'import multi-sources
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { odooApi } from './api';
import type { OdooConnectionConfig, ImportHistory, ScheduleMode, SyncType } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const importGatewaysKeys = {
  all: ['import-gateways'] as const,

  // Configs
  configs: () => [...importGatewaysKeys.all, 'configs'] as const,
  configDetail: (id: string) => [...importGatewaysKeys.configs(), id] as const,

  // History
  history: () => [...importGatewaysKeys.all, 'history'] as const,
  historyList: (configId?: string, limit?: number) =>
    [...importGatewaysKeys.history(), configId, limit] as const,

  // Schedule
  nextRuns: (configId: string, count?: number) =>
    [...importGatewaysKeys.all, 'next-runs', configId, count] as const,
};

// ============================================================================
// CONFIG HOOKS
// ============================================================================

export const useOdooConfigs = () => {
  return useQuery({
    queryKey: importGatewaysKeys.configs(),
    queryFn: () => odooApi.config.list(),
  });
};

export const useOdooConfig = (id: string) => {
  return useQuery({
    queryKey: importGatewaysKeys.configDetail(id),
    queryFn: () => odooApi.config.get(id),
    enabled: !!id,
  });
};

export const useCreateOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof odooApi.config.create>[0]) =>
      odooApi.config.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

export const useUpdateOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof odooApi.config.update>[1] }) =>
      odooApi.config.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

export const useDeleteOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => odooApi.config.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

// ============================================================================
// CONNECTION HOOKS
// ============================================================================

export const useTestConnection = () => {
  return useMutation({
    mutationFn: (params: {
      odoo_url: string;
      odoo_database: string;
      auth_method: 'password' | 'api_key';
      username: string;
      credential: string;
    }) => odooApi.connection.test(params),
  });
};

export const useTestOdooConfig = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => odooApi.connection.testConfig(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

// ============================================================================
// HISTORY HOOKS
// ============================================================================

export const useImportHistory = (configId?: string, limit = 50) => {
  return useQuery({
    queryKey: importGatewaysKeys.historyList(configId, limit),
    queryFn: () => odooApi.history.list(configId, limit),
  });
};

// ============================================================================
// SCHEDULE HOOKS
// ============================================================================

export const useNextRuns = (configId: string, count = 5) => {
  return useQuery({
    queryKey: importGatewaysKeys.nextRuns(configId, count),
    queryFn: () => odooApi.schedule.getNextRuns(configId, count),
    enabled: !!configId,
  });
};

export const useConfigureSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ configId, data }: {
      configId: string;
      data: {
        mode: ScheduleMode;
        cron_expression?: string;
        interval_minutes?: number;
        timezone: string;
      };
    }) => odooApi.schedule.configure(configId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

export const usePauseSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (configId: string) => odooApi.schedule.pause(configId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

export const useResumeSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (configId: string) => odooApi.schedule.resume(configId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() }),
  });
};

// ============================================================================
// IMPORT HOOKS
// ============================================================================

export const useSelectiveImport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ configId, data }: {
      configId: string;
      data: { types: SyncType[]; full_sync: boolean };
    }) => odooApi.import.selectiveImport(configId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() });
      queryClient.invalidateQueries({ queryKey: importGatewaysKeys.history() });
    },
  });
};

export const useFullImport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (configId: string) => odooApi.import.fullSync(configId, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importGatewaysKeys.configs() });
      queryClient.invalidateQueries({ queryKey: importGatewaysKeys.history() });
    },
  });
};
