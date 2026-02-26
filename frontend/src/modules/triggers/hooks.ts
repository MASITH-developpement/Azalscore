/**
 * AZALSCORE Module - Triggers & Diffusion - Hooks
 * React Query hooks pour l'API Triggers
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type {
  Trigger,
  TriggerListResponse,
  TriggerDashboard,
  TriggerEvent,
  EventListResponse,
  NotificationListResponse,
  NotificationTemplate,
  ScheduledReport,
  WebhookEndpoint,
  TriggerLogListResponse,
  TriggerFilters,
  EventFilters,
  TriggerCreateInput,
  TriggerUpdateInput,
} from './types';

// ============================================================
// QUERY HOOKS
// ============================================================

export const useTriggerDashboard = () => {
  return useQuery({
    queryKey: ['triggers', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<TriggerDashboard>('/triggers/dashboard');
      return response.data;
    },
  });
};

export const useTriggers = (filters?: TriggerFilters) => {
  return useQuery({
    queryKey: ['triggers', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.source_module) params.append('source_module', filters.source_module);
      if (filters?.trigger_type) params.append('trigger_type', filters.trigger_type);
      if (filters?.include_inactive) params.append('include_inactive', 'true');
      const url = `/triggers/${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<TriggerListResponse>(url);
      return response.data;
    },
  });
};

export const useTrigger = (id: string) => {
  return useQuery({
    queryKey: ['triggers', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Trigger>(`/triggers/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useEvents = (filters?: EventFilters) => {
  return useQuery({
    queryKey: ['triggers', 'events', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.trigger_id) params.append('trigger_id', filters.trigger_id);
      if (filters?.resolved !== undefined) params.append('resolved', String(filters.resolved));
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.limit) params.append('limit', String(filters.limit));
      const url = `/triggers/events${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<EventListResponse>(url);
      return response.data;
    },
  });
};

export const useMyNotifications = (unreadOnly = false) => {
  return useQuery({
    queryKey: ['triggers', 'notifications', unreadOnly],
    queryFn: async () => {
      const response = await api.get<NotificationListResponse>(
        `/triggers/notifications?unread_only=${unreadOnly}`
      );
      return response.data;
    },
  });
};

export const useTemplates = () => {
  return useQuery({
    queryKey: ['triggers', 'templates'],
    queryFn: async () => {
      const response = await api.get<NotificationTemplate[]>('/triggers/templates');
      return response.data;
    },
  });
};

export const useScheduledReports = (includeInactive = false) => {
  return useQuery({
    queryKey: ['triggers', 'reports', includeInactive],
    queryFn: async () => {
      const response = await api.get<ScheduledReport[]>(
        `/triggers/reports?include_inactive=${includeInactive}`
      );
      return response.data;
    },
  });
};

export const useWebhooks = () => {
  return useQuery({
    queryKey: ['triggers', 'webhooks'],
    queryFn: async () => {
      const response = await api.get<WebhookEndpoint[]>('/triggers/webhooks');
      return response.data;
    },
  });
};

export const useTriggerLogs = (filters?: { action?: string; limit?: number }) => {
  return useQuery({
    queryKey: ['triggers', 'logs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.limit) params.append('limit', String(filters.limit));
      const url = `/triggers/logs${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<TriggerLogListResponse>(url);
      return response.data;
    },
  });
};

// ============================================================
// MUTATIONS
// ============================================================

export const useCreateTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TriggerCreateInput) => {
      const response = await api.post<Trigger>('/triggers/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const useUpdateTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TriggerUpdateInput }) => {
      const response = await api.put<Trigger>(`/triggers/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const useDeleteTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/triggers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const usePauseTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Trigger>(`/triggers/${id}/pause`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const useResumeTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Trigger>(`/triggers/${id}/resume`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const useFireTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data?: { triggered_value?: string } }) => {
      const response = await api.post<TriggerEvent>(`/triggers/${id}/fire`, data || {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

export const useResolveEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      const response = await api.post<TriggerEvent>(`/triggers/events/${id}/resolve`, {
        resolution_notes: notes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'events'] });
      queryClient.invalidateQueries({ queryKey: ['triggers', 'dashboard'] });
    },
  });
};

export const useMarkNotificationRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Notification>(`/triggers/notifications/${id}/read`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'notifications'] });
    },
  });
};

export const useMarkAllNotificationsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/triggers/notifications/read-all');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'notifications'] });
    },
  });
};
