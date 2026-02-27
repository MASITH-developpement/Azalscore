/**
 * AZALSCORE Module - NOTIFICATIONS - React Query Hooks
 * =====================================================
 * Hooks pour la gestion des notifications
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from './api';
import type { NotificationFilters, TemplateFilters, NotificationCreate, TemplateCreate } from './api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const notificationsKeys = {
  all: ['notifications'] as const,

  // Notifications
  notifications: () => [...notificationsKeys.all, 'list'] as const,
  notificationsList: (filters?: NotificationFilters) =>
    [...notificationsKeys.notifications(), filters] as const,
  notification: (id: string) => [...notificationsKeys.all, 'detail', id] as const,
  unreadCount: () => [...notificationsKeys.all, 'unread-count'] as const,
  stats: (days?: number) => [...notificationsKeys.all, 'stats', days] as const,

  // Preferences
  preferences: () => [...notificationsKeys.all, 'preferences'] as const,

  // Templates
  templates: () => [...notificationsKeys.all, 'templates'] as const,
  templatesList: (filters?: TemplateFilters) =>
    [...notificationsKeys.templates(), 'list', filters] as const,
  template: (id: string) => [...notificationsKeys.templates(), id] as const,
};

// ============================================================================
// NOTIFICATIONS HOOKS
// ============================================================================

export function useNotifications(filters?: NotificationFilters) {
  return useQuery({
    queryKey: notificationsKeys.notificationsList(filters),
    queryFn: async () => {
      const response = await notificationsApi.listNotifications(filters);
      return response.data;
    },
  });
}

export function useNotification(id: string) {
  return useQuery({
    queryKey: notificationsKeys.notification(id),
    queryFn: async () => {
      const response = await notificationsApi.getNotification(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationsKeys.unreadCount(),
    queryFn: async () => {
      const response = await notificationsApi.getUnreadCount();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useNotificationStats(days = 30) {
  return useQuery({
    queryKey: notificationsKeys.stats(days),
    queryFn: async () => {
      const response = await notificationsApi.getStats(days);
      return response.data;
    },
  });
}

export function useSendNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: NotificationCreate) => {
      const response = await notificationsApi.sendNotification(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.stats() });
    },
  });
}

export function useMarkAsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await notificationsApi.markAsRead(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.notification(id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.unreadCount() });
    },
  });
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const response = await notificationsApi.markAllAsRead();
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.unreadCount() });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await notificationsApi.deleteNotification(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.unreadCount() });
    },
  });
}

// ============================================================================
// PREFERENCES HOOKS
// ============================================================================

export function useNotificationPreferences() {
  return useQuery({
    queryKey: notificationsKeys.preferences(),
    queryFn: async () => {
      const response = await notificationsApi.getPreferences();
      return response.data;
    },
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Parameters<typeof notificationsApi.updatePreferences>[0]) => {
      const response = await notificationsApi.updatePreferences(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.preferences() });
    },
  });
}

// ============================================================================
// TEMPLATES HOOKS
// ============================================================================

export function useNotificationTemplates(filters?: TemplateFilters) {
  return useQuery({
    queryKey: notificationsKeys.templatesList(filters),
    queryFn: async () => {
      const response = await notificationsApi.listTemplates(filters);
      return response.data;
    },
  });
}

export function useNotificationTemplate(id: string) {
  return useQuery({
    queryKey: notificationsKeys.template(id),
    queryFn: async () => {
      const response = await notificationsApi.getTemplate(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateNotificationTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TemplateCreate) => {
      const response = await notificationsApi.createTemplate(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.templates() });
    },
  });
}

export function useUpdateNotificationTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<TemplateCreate> }) => {
      const response = await notificationsApi.updateTemplate(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.template(id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.templates() });
    },
  });
}

export function useDeleteNotificationTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await notificationsApi.deleteTemplate(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.templates() });
    },
  });
}

export function useActivateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await notificationsApi.activateTemplate(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.template(id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.templates() });
    },
  });
}

export function useArchiveTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await notificationsApi.archiveTemplate(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: notificationsKeys.template(id) });
      queryClient.invalidateQueries({ queryKey: notificationsKeys.templates() });
    },
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: async ({ id, variables }: { id: string; variables: Record<string, unknown> }) => {
      const response = await notificationsApi.previewTemplate(id, variables);
      return response.data;
    },
  });
}
