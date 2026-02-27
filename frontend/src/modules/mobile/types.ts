/**
 * AZALSCORE Module - Mobile PWA Types
 * Types TypeScript pour le module mobile
 */

// ============================================================================
// ENUMS
// ============================================================================

export type Platform =
  | 'ios'
  | 'android'
  | 'web';

export type NotificationType =
  | 'info'
  | 'warning'
  | 'error'
  | 'success'
  | 'alert'
  | 'reminder';

export type NotificationPriority =
  | 'low'
  | 'normal'
  | 'high'
  | 'urgent';

export type NotificationStatus =
  | 'pending'
  | 'sent'
  | 'delivered'
  | 'read'
  | 'failed';

export type SyncOperation =
  | 'create'
  | 'update'
  | 'delete';

export type SyncEntityType =
  | 'intervention'
  | 'contact'
  | 'product'
  | 'invoice'
  | 'quote'
  | 'task'
  | 'timesheet';

// ============================================================================
// DEVICE
// ============================================================================

export interface MobileDevice {
  id: number;
  device_id: string;
  device_name?: string;
  platform: Platform;
  os_version?: string;
  app_version?: string;
  model?: string;
  push_token?: string;
  push_enabled: boolean;
  is_trusted: boolean;
  is_active: boolean;
  last_active?: string;
  registered_at: string;
}

export interface DeviceRegister {
  device_id: string;
  device_name?: string;
  platform: Platform;
  os_version?: string;
  app_version?: string;
  model?: string;
  push_token?: string;
}

export interface DeviceUpdate {
  device_name?: string;
  push_token?: string;
  push_enabled?: boolean;
  app_version?: string;
}

// ============================================================================
// SESSION
// ============================================================================

export interface MobileSession {
  id: number;
  device_id: number;
  user_id: number;
  session_token: string;
  refresh_token?: string;
  is_active: boolean;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  expires_at: string;
  last_used_at?: string;
}

export interface SessionCreate {
  device_id: string;
}

export interface SessionResponse {
  session_token: string;
  refresh_token?: string;
  expires_at: string;
  device_id: number;
}

export interface SessionRefresh {
  refresh_token: string;
}

// ============================================================================
// NOTIFICATION
// ============================================================================

export interface MobileNotification {
  id: number;
  user_id: number;
  title: string;
  body?: string;
  image_url?: string;
  notification_type: NotificationType;
  category?: string;
  priority: NotificationPriority;
  status: NotificationStatus;
  data?: Record<string, unknown>;
  action_url?: string;
  scheduled_at?: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationCreate {
  user_id: number;
  title: string;
  body?: string;
  image_url?: string;
  notification_type?: NotificationType;
  category?: string;
  priority?: NotificationPriority;
  data?: Record<string, unknown>;
  action_url?: string;
  scheduled_at?: string;
}

export interface NotificationBulk {
  user_ids: number[];
  title: string;
  body?: string;
  notification_type?: NotificationType;
  data?: Record<string, unknown>;
}

export interface NotificationUpdate {
  is_read?: boolean;
}

// ============================================================================
// SYNC
// ============================================================================

export interface SyncItem {
  entity_type: SyncEntityType;
  entity_id?: string;
  operation: SyncOperation;
  data: Record<string, unknown>;
  local_version?: number;
}

export interface SyncRequest {
  entity_type: SyncEntityType;
  since_version?: number;
  limit?: number;
}

export interface SyncBatch {
  items: SyncItem[];
  device_id?: string;
}

export interface SyncResponse {
  entity_type: SyncEntityType;
  items: SyncResponseItem[];
  server_version: number;
  has_more: boolean;
}

export interface SyncResponseItem {
  entity_id: string;
  operation: SyncOperation;
  data: Record<string, unknown>;
  version: number;
  synced_at: string;
}

export interface SyncConflict {
  entity_type: SyncEntityType;
  entity_id: string;
  local_data: Record<string, unknown>;
  server_data: Record<string, unknown>;
  local_version: number;
  server_version: number;
}

export interface SyncStatus {
  entity_type: SyncEntityType;
  last_sync_at?: string;
  pending_items: number;
  failed_items: number;
  conflicts: number;
}

// ============================================================================
// OFFLINE STORAGE
// ============================================================================

export interface OfflineAction {
  id: string;
  entity_type: SyncEntityType;
  entity_id?: string;
  operation: SyncOperation;
  data: Record<string, unknown>;
  created_at: string;
  retry_count: number;
  last_error?: string;
}

export interface OfflineData<T = unknown> {
  entity_type: SyncEntityType;
  entity_id: string;
  data: T;
  version: number;
  synced_at?: string;
  is_dirty: boolean;
}

// ============================================================================
// APP CONFIG
// ============================================================================

export interface MobileAppConfig {
  min_app_version: string;
  current_app_version: string;
  force_update: boolean;
  maintenance_mode: boolean;
  maintenance_message?: string;
  features: MobileFeatureFlags;
  sync_config: MobileSyncConfig;
}

export interface MobileFeatureFlags {
  offline_mode: boolean;
  push_notifications: boolean;
  biometric_auth: boolean;
  camera_scan: boolean;
  gps_tracking: boolean;
  voice_input: boolean;
}

export interface MobileSyncConfig {
  auto_sync: boolean;
  sync_interval_minutes: number;
  sync_on_wifi_only: boolean;
  max_offline_days: number;
  entities_to_sync: SyncEntityType[];
}

// ============================================================================
// STATS
// ============================================================================

export interface MobileStats {
  total_devices: number;
  active_devices: number;
  active_sessions: number;
  notifications_sent_today: number;
  notifications_pending: number;
  sync_errors_today: number;
  platforms: PlatformStats[];
}

export interface PlatformStats {
  platform: Platform;
  device_count: number;
  active_count: number;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type DeviceListResponse = PaginatedResponse<MobileDevice>;
export type SessionListResponse = PaginatedResponse<MobileSession>;
export type NotificationListResponse = PaginatedResponse<MobileNotification>;

// ============================================================================
// FILTERS
// ============================================================================

export interface DeviceFilters {
  platform?: Platform;
  is_active?: boolean;
  is_trusted?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface NotificationFilters {
  notification_type?: NotificationType;
  status?: NotificationStatus;
  is_read?: boolean;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}
