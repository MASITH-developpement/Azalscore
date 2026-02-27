/**
 * AZALSCORE Module - NOTIFICATIONS - Types
 * =========================================
 * Types TypeScript pour le module Notifications
 */

// ============================================================================
// ENUMS
// ============================================================================

export type NotificationChannel = 'EMAIL' | 'SMS' | 'PUSH' | 'IN_APP' | 'WEBHOOK' | 'SLACK' | 'TEAMS';

export type NotificationStatus =
  | 'PENDING'
  | 'QUEUED'
  | 'SENDING'
  | 'SENT'
  | 'DELIVERED'
  | 'READ'
  | 'FAILED'
  | 'BOUNCED'
  | 'CANCELLED';

export type NotificationPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export type NotificationType =
  | 'TRANSACTIONAL'
  | 'SYSTEM'
  | 'MARKETING'
  | 'REMINDER'
  | 'ALERT'
  | 'WORKFLOW'
  | 'SOCIAL';

// ============================================================================
// INTERFACES
// ============================================================================

export interface Notification {
  id: string;
  tenant_id: string;
  user_id?: string;
  template_id?: string;
  template_code?: string;
  notification_type: NotificationType;
  channel: NotificationChannel;
  priority: NotificationPriority;
  status: NotificationStatus;

  // Contenu
  subject?: string;
  title?: string;
  body: string;
  html_body?: string;
  data?: Record<string, unknown>;

  // Reference
  reference_type?: string;
  reference_id?: string;

  // Tracking
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  clicked_at?: string;
  failed_at?: string;
  failure_reason?: string;

  // Metadata
  created_at: string;
  updated_at?: string;
}

export interface NotificationPreferences {
  id: string;
  user_id: string;

  // Canaux activés
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;

  // Types de notifications
  transactional_enabled: boolean;
  system_enabled: boolean;
  marketing_enabled: boolean;
  reminder_enabled: boolean;
  alert_enabled: boolean;
  workflow_enabled: boolean;
  social_enabled: boolean;

  // Horaires silencieux
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;

  // Digest
  digest_enabled: boolean;
  digest_frequency?: 'DAILY' | 'WEEKLY';
}

export interface NotificationTemplate {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  notification_type: NotificationType;
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
  channels: NotificationChannel[];

  // Contenu email
  email_subject?: string;
  email_html?: string;
  email_text?: string;

  // Contenu SMS
  sms_text?: string;

  // Contenu Push
  push_title?: string;
  push_body?: string;

  // Contenu In-App
  in_app_title?: string;
  in_app_body?: string;
  in_app_icon?: string;
  in_app_action_url?: string;

  // Variables
  variables?: string[];

  created_at: string;
  updated_at?: string;
}

export interface NotificationStats {
  total_sent: number;
  total_delivered: number;
  total_read: number;
  total_clicked: number;
  total_failed: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const NOTIFICATION_TYPE_CONFIG: Record<NotificationType, { label: string; color: string; icon: string }> = {
  TRANSACTIONAL: { label: 'Transactionnel', color: 'blue', icon: 'receipt' },
  SYSTEM: { label: 'Systeme', color: 'gray', icon: 'settings' },
  MARKETING: { label: 'Marketing', color: 'purple', icon: 'megaphone' },
  REMINDER: { label: 'Rappel', color: 'orange', icon: 'clock' },
  ALERT: { label: 'Alerte', color: 'red', icon: 'alert-triangle' },
  WORKFLOW: { label: 'Workflow', color: 'green', icon: 'git-branch' },
  SOCIAL: { label: 'Social', color: 'pink', icon: 'users' },
};

export const NOTIFICATION_STATUS_CONFIG: Record<NotificationStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'gray' },
  QUEUED: { label: 'En file', color: 'blue' },
  SENDING: { label: 'Envoi en cours', color: 'blue' },
  SENT: { label: 'Envoyee', color: 'green' },
  DELIVERED: { label: 'Delivree', color: 'green' },
  READ: { label: 'Lue', color: 'green' },
  FAILED: { label: 'Echec', color: 'red' },
  BOUNCED: { label: 'Rebond', color: 'orange' },
  CANCELLED: { label: 'Annulee', color: 'gray' },
};

export const NOTIFICATION_PRIORITY_CONFIG: Record<NotificationPriority, { label: string; color: string }> = {
  LOW: { label: 'Basse', color: 'gray' },
  NORMAL: { label: 'Normale', color: 'blue' },
  HIGH: { label: 'Haute', color: 'orange' },
  URGENT: { label: 'Urgente', color: 'red' },
};

export const NOTIFICATION_CHANNEL_CONFIG: Record<NotificationChannel, { label: string; icon: string }> = {
  EMAIL: { label: 'Email', icon: 'mail' },
  SMS: { label: 'SMS', icon: 'smartphone' },
  PUSH: { label: 'Push', icon: 'bell' },
  IN_APP: { label: 'In-App', icon: 'layout' },
  WEBHOOK: { label: 'Webhook', icon: 'link' },
  SLACK: { label: 'Slack', icon: 'hash' },
  TEAMS: { label: 'Teams', icon: 'users' },
};
