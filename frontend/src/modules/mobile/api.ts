/**
 * AZALSCORE - Mobile API
 * ======================
 * API client pour le module Mobile/PWA
 * Couvre: Appareils, Sessions, Notifications, Preferences
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export type DeviceType = 'mobile' | 'tablet' | 'desktop' | 'watch';

export interface Device {
  id: string;
  device_type: DeviceType;
  device_name: string;
  platform: string;
  os_version?: string;
  app_version?: string;
  push_token?: string;
  is_active: boolean;
  last_seen_at?: string;
  created_at: string;
}

export interface MobileSession {
  id: string;
  device_id: string;
  is_active: boolean;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  expires_at?: string;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
}

export interface MobileStats {
  total_devices: number;
  active_devices: number;
  total_sessions: number;
  active_sessions: number;
  unread_notifications: number;
  last_sync_at?: string;
}

export interface Preferences {
  notifications_enabled: boolean;
  dark_mode: boolean;
  offline_mode: boolean;
  auto_sync: boolean;
  sync_interval_minutes: number;
  language: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/mobile';

// ============================================================================
// API CLIENT
// ============================================================================

export const mobileApi = {
  // ==========================================================================
  // Stats
  // ==========================================================================

  /**
   * Recupere les statistiques mobile
   */
  getStats: () =>
    api.get<MobileStats>(`${BASE_PATH}/stats`),

  // ==========================================================================
  // Devices
  // ==========================================================================

  /**
   * Liste les appareils enregistres
   */
  listDevices: () =>
    api.get<Device[]>(`${BASE_PATH}/devices`),

  /**
   * Recupere un appareil par son ID
   */
  getDevice: (id: string) =>
    api.get<Device>(`${BASE_PATH}/devices/${id}`),

  /**
   * Enregistre un nouvel appareil
   */
  registerDevice: (data: Partial<Device>) =>
    api.post<Device>(`${BASE_PATH}/devices`, data),

  /**
   * Met a jour un appareil
   */
  updateDevice: (id: string, data: Partial<Device>) =>
    api.put<Device>(`${BASE_PATH}/devices/${id}`, data),

  /**
   * Supprime un appareil
   */
  deleteDevice: (id: string) =>
    api.delete(`${BASE_PATH}/devices/${id}`),

  // ==========================================================================
  // Sessions
  // ==========================================================================

  /**
   * Liste les sessions actives
   */
  listSessions: () =>
    api.get<MobileSession[]>(`${BASE_PATH}/sessions`),

  /**
   * Termine une session
   */
  deleteSession: (id: string) =>
    api.delete(`${BASE_PATH}/sessions/${id}`),

  /**
   * Termine toutes les sessions
   */
  deleteAllSessions: () =>
    api.delete(`${BASE_PATH}/sessions`),

  // ==========================================================================
  // Notifications
  // ==========================================================================

  /**
   * Liste les notifications
   */
  listNotifications: () =>
    api.get<Notification[]>(`${BASE_PATH}/notifications`),

  /**
   * Marque une notification comme lue
   */
  markNotificationRead: (id: string) =>
    api.put(`${BASE_PATH}/notifications/${id}/read`),

  /**
   * Marque toutes les notifications comme lues
   */
  markAllNotificationsRead: () =>
    api.put(`${BASE_PATH}/notifications/read-all`),

  /**
   * Supprime une notification
   */
  deleteNotification: (id: string) =>
    api.delete(`${BASE_PATH}/notifications/${id}`),

  // ==========================================================================
  // Preferences
  // ==========================================================================

  /**
   * Recupere les preferences
   */
  getPreferences: () =>
    api.get<Preferences>(`${BASE_PATH}/preferences`),

  /**
   * Met a jour les preferences
   */
  updatePreferences: (data: Partial<Preferences>) =>
    api.put<Preferences>(`${BASE_PATH}/preferences`, data),

  // ==========================================================================
  // Sync
  // ==========================================================================

  /**
   * Declenche une synchronisation
   */
  triggerSync: () =>
    api.post(`${BASE_PATH}/sync`, {}),

  /**
   * Recupere le statut de synchronisation
   */
  getSyncStatus: () =>
    api.get<{ last_sync: string; pending_changes: number }>(`${BASE_PATH}/sync/status`),
};

export default mobileApi;
