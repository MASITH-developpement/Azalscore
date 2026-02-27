/**
 * AZALSCORE Module - NOTIFICATIONS - API Client
 * ==============================================
 * Client API pour les endpoints de notifications
 */

import { api } from '@/core/api-client';
import type {
  Notification,
  NotificationPreferences,
  NotificationTemplate,
  NotificationStats,
  NotificationType,
  NotificationStatus,
  NotificationChannel,
} from './types';

const BASE_URL = '/notifications';

// ============================================================================
// TYPES API
// ============================================================================

export interface NotificationFilters {
  type?: NotificationType;
  status?: NotificationStatus;
  channel?: NotificationChannel;
  is_read?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface NotificationCreate {
  template_code?: string;
  notification_type: NotificationType;
  channel: NotificationChannel;
  priority?: string;
  user_id?: string;
  recipient_email?: string;
  recipient_phone?: string;
  subject?: string;
  title?: string;
  body: string;
  data?: Record<string, unknown>;
  reference_type?: string;
  reference_id?: string;
  scheduled_at?: string;
}

export interface TemplateFilters {
  type?: NotificationType;
  status?: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  channel?: NotificationChannel;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface TemplateCreate {
  code: string;
  name: string;
  description?: string;
  notification_type: NotificationType;
  channels: NotificationChannel[];
  email_subject?: string;
  email_html?: string;
  email_text?: string;
  sms_text?: string;
  push_title?: string;
  push_body?: string;
  in_app_title?: string;
  in_app_body?: string;
  in_app_icon?: string;
  in_app_action_url?: string;
  variables?: string[];
}

// ============================================================================
// NOTIFICATIONS API
// ============================================================================

async function listNotifications(filters?: NotificationFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<Notification>>(`${BASE_URL}?${params.toString()}`);
}

async function getNotification(id: string) {
  return api.get<Notification>(`${BASE_URL}/${id}`);
}

async function sendNotification(data: NotificationCreate) {
  return api.post<Notification>(`${BASE_URL}/send`, data);
}

async function markAsRead(id: string) {
  return api.post<Notification>(`${BASE_URL}/${id}/read`);
}

async function markAllAsRead() {
  return api.post<{ count: number }>(`${BASE_URL}/read-all`);
}

async function deleteNotification(id: string) {
  return api.delete(`${BASE_URL}/${id}`);
}

async function getUnreadCount() {
  return api.get<{ count: number }>(`${BASE_URL}/unread-count`);
}

async function getStats(days = 30) {
  return api.get<NotificationStats>(`${BASE_URL}/stats?days=${days}`);
}

// ============================================================================
// PREFERENCES API
// ============================================================================

async function getPreferences() {
  return api.get<NotificationPreferences>(`${BASE_URL}/preferences`);
}

async function updatePreferences(data: Partial<NotificationPreferences>) {
  return api.put<NotificationPreferences>(`${BASE_URL}/preferences`, data);
}

// ============================================================================
// TEMPLATES API
// ============================================================================

async function listTemplates(filters?: TemplateFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<NotificationTemplate>>(`${BASE_URL}/templates?${params.toString()}`);
}

async function getTemplate(id: string) {
  return api.get<NotificationTemplate>(`${BASE_URL}/templates/${id}`);
}

async function createTemplate(data: TemplateCreate) {
  return api.post<NotificationTemplate>(`${BASE_URL}/templates`, data);
}

async function updateTemplate(id: string, data: Partial<TemplateCreate>) {
  return api.put<NotificationTemplate>(`${BASE_URL}/templates/${id}`, data);
}

async function deleteTemplate(id: string) {
  return api.delete(`${BASE_URL}/templates/${id}`);
}

async function activateTemplate(id: string) {
  return api.post<NotificationTemplate>(`${BASE_URL}/templates/${id}/activate`);
}

async function archiveTemplate(id: string) {
  return api.post<NotificationTemplate>(`${BASE_URL}/templates/${id}/archive`);
}

async function previewTemplate(id: string, variables: Record<string, unknown>) {
  return api.post<{ subject?: string; body: string; html_body?: string }>(
    `${BASE_URL}/templates/${id}/preview`,
    { variables }
  );
}

// ============================================================================
// EXPORT
// ============================================================================

export const notificationsApi = {
  // Notifications
  listNotifications,
  getNotification,
  sendNotification,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  getUnreadCount,
  getStats,

  // Preferences
  getPreferences,
  updatePreferences,

  // Templates
  listTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  activateTemplate,
  archiveTemplate,
  previewTemplate,
};

export default notificationsApi;
