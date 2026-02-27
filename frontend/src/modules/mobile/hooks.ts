/**
 * AZALSCORE - Mobile PWA React Query Hooks
 * =========================================
 * Hooks pour le module Mobile (appareils, sessions, notifications)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';

// ============================================================================
// TYPES
// ============================================================================

interface Device {
  id: string;
  device_type: 'mobile' | 'tablet' | 'desktop' | 'watch';
  device_name: string;
  platform: string;
  os_version?: string;
  app_version?: string;
  push_token?: string;
  is_active: boolean;
  last_seen_at?: string;
  created_at: string;
}

interface MobileSession {
  id: string;
  device_id: string;
  is_active: boolean;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  expires_at?: string;
}

interface MobileNotification {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
}

interface MobileStats {
  total_devices: number;
  active_devices: number;
  total_sessions: number;
  active_sessions: number;
  unread_notifications: number;
  last_sync_at?: string;
}

interface MobilePreferences {
  notifications_enabled: boolean;
  dark_mode: boolean;
  offline_mode: boolean;
  auto_sync: boolean;
  sync_interval_minutes: number;
  language: string;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const mobileKeys = {
  all: ['mobile'] as const,
  stats: () => [...mobileKeys.all, 'stats'] as const,
  devices: () => [...mobileKeys.all, 'devices'] as const,
  sessions: () => [...mobileKeys.all, 'sessions'] as const,
  notifications: () => [...mobileKeys.all, 'notifications'] as const,
  preferences: () => [...mobileKeys.all, 'preferences'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useMobileStats = () => {
  return useQuery({
    queryKey: mobileKeys.stats(),
    queryFn: () => api.get<MobileStats>('/mobile/stats').then(r => r.data),
  });
};

export const useDevices = () => {
  return useQuery({
    queryKey: mobileKeys.devices(),
    queryFn: () => api.get<Device[]>('/mobile/devices').then(r => r.data || []),
  });
};

export const useSessions = () => {
  return useQuery({
    queryKey: mobileKeys.sessions(),
    queryFn: () => api.get<MobileSession[]>('/mobile/sessions').then(r => r.data || []),
  });
};

export const useMobileNotifications = () => {
  return useQuery({
    queryKey: mobileKeys.notifications(),
    queryFn: () => api.get<MobileNotification[]>('/mobile/notifications').then(r => r.data || []),
  });
};

export const useMobilePreferences = () => {
  return useQuery({
    queryKey: mobileKeys.preferences(),
    queryFn: () => api.get<MobilePreferences>('/mobile/preferences').then(r => r.data),
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useDeleteDevice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/mobile/devices/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mobileKeys.devices() });
    },
  });
};

export const useDeleteSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/mobile/sessions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mobileKeys.sessions() });
    },
  });
};

export const useMarkNotificationRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.put(`/mobile/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mobileKeys.notifications() });
    },
  });
};

export const useMarkAllNotificationsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.put('/mobile/notifications/read-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mobileKeys.notifications() });
    },
  });
};

export const useUpdateMobilePreferences = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<MobilePreferences>) => api.put('/mobile/preferences', data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mobileKeys.preferences() });
    },
  });
};

// Re-export types
export type { Device, MobileSession, MobileNotification, MobileStats, MobilePreferences };
