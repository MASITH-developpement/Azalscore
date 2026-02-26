/**
 * AZALSCORE - Types Module Cache
 * ===============================
 * Types TypeScript pour la gestion du cache applicatif.
 */

// ============================================================================
// ENUMS
// ============================================================================

export type CacheLevel = 'L1_MEMORY' | 'L2_REDIS' | 'L3_PERSISTENT';
export type EvictionPolicy = 'LRU' | 'LFU' | 'FIFO' | 'TTL' | 'RANDOM';
export type CacheStatus = 'ACTIVE' | 'STALE' | 'EXPIRED' | 'INVALIDATED';
export type InvalidationType = 'KEY' | 'PATTERN' | 'TAG' | 'ENTITY' | 'TENANT' | 'ALL';
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';

// ============================================================================
// CONFIG
// ============================================================================

export interface CacheConfig {
  id: string;
  tenant_id: string;
  l1_enabled: boolean;
  l2_enabled: boolean;
  l3_enabled: boolean;
  default_ttl_seconds: number;
  stale_ttl_seconds: number;
  l1_max_items: number;
  l1_max_size_mb: number;
  l2_max_size_mb: number;
  eviction_policy: EvictionPolicy;
  compression_enabled: boolean;
  compression_threshold_bytes: number;
  preload_enabled: boolean;
  alert_hit_rate_threshold: number;
  alert_memory_threshold_percent: number;
  alert_eviction_rate_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CacheConfigCreate {
  l1_enabled?: boolean;
  l2_enabled?: boolean;
  l3_enabled?: boolean;
  default_ttl_seconds?: number;
  stale_ttl_seconds?: number;
  l1_max_items?: number;
  l1_max_size_mb?: number;
  l2_max_size_mb?: number;
  eviction_policy?: EvictionPolicy;
  compression_enabled?: boolean;
  compression_threshold_bytes?: number;
  preload_enabled?: boolean;
  alert_hit_rate_threshold?: number;
  alert_memory_threshold_percent?: number;
  alert_eviction_rate_threshold?: number;
}

export interface CacheConfigUpdate extends Partial<CacheConfigCreate> {
  is_active?: boolean;
}

// ============================================================================
// REGIONS
// ============================================================================

export interface CacheRegion {
  id: string;
  tenant_id: string;
  config_id: string;
  code: string;
  name: string;
  description?: string;
  ttl_seconds: number;
  stale_ttl_seconds: number;
  max_items: number;
  default_tags: string[];
  entity_types: string[];
  preload_enabled: boolean;
  preload_keys: string[];
  preload_cron?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CacheRegionCreate {
  code: string;
  name: string;
  description?: string;
  ttl_seconds?: number;
  stale_ttl_seconds?: number;
  max_items?: number;
  default_tags?: string[];
  entity_types?: string[];
  preload_enabled?: boolean;
  preload_keys?: string[];
  preload_cron?: string;
}

export interface CacheRegionUpdate extends Partial<Omit<CacheRegionCreate, 'code'>> {
  is_active?: boolean;
}

// ============================================================================
// CACHE OPERATIONS
// ============================================================================

export interface CacheSetRequest {
  key: string;
  value: unknown;
  ttl_seconds?: number;
  tags?: string[];
  region?: string;
  entity_type?: string;
  entity_id?: string;
}

export interface CacheGetResponse {
  key: string;
  value: unknown;
  found: boolean;
  is_stale: boolean;
  cache_level?: CacheLevel;
  expires_at?: string;
  hit_count: number;
}

export interface CacheMGetResponse {
  items: Record<string, unknown>;
  found_keys: string[];
  missing_keys: string[];
}

// ============================================================================
// INVALIDATION
// ============================================================================

export interface InvalidationResponse {
  id: string;
  invalidation_type: InvalidationType;
  keys_invalidated: number;
  levels_affected: CacheLevel[];
  duration_ms: number;
  timestamp: string;
}

// ============================================================================
// STATISTICS
// ============================================================================

export interface CacheStats {
  tenant_id: string;
  cache_level: CacheLevel;
  period_start: string;
  period_end: string;
  hits: number;
  misses: number;
  stale_hits: number;
  hit_rate: number;
  sets: number;
  deletes: number;
  evictions_ttl: number;
  evictions_capacity: number;
  total_evictions: number;
  invalidations_total: number;
  current_items: number;
  current_size_bytes: number;
  max_items: number;
  max_size_bytes: number;
  fill_rate: number;
  avg_get_time_ms: number;
  avg_set_time_ms: number;
  p95_get_time_ms: number;
  p99_get_time_ms: number;
}

export interface CacheStatsAggregated {
  l1_stats?: CacheStats;
  l2_stats?: CacheStats;
  l3_stats?: CacheStats;
  total_hits: number;
  total_misses: number;
  overall_hit_rate: number;
  total_size_bytes: number;
  total_items: number;
}

// ============================================================================
// ENTRIES
// ============================================================================

export interface CacheEntry {
  id: string;
  tenant_id: string;
  cache_key: string;
  region_code?: string;
  original_size_bytes: number;
  compressed_size_bytes: number;
  is_compressed: boolean;
  created_at: string;
  expires_at?: string;
  tags: string[];
  entity_type?: string;
  entity_id?: string;
  hit_count: number;
  last_accessed_at?: string;
  cache_level: CacheLevel;
  status: CacheStatus;
}

// ============================================================================
// PRELOAD
// ============================================================================

export interface PreloadTask {
  id: string;
  tenant_id: string;
  region_id?: string;
  region_code?: string;
  name: string;
  description?: string;
  keys_pattern?: string;
  keys_list: string[];
  loader_type: string;
  loader_config: Record<string, unknown>;
  schedule_cron?: string;
  next_run_at?: string;
  last_run_at?: string;
  last_run_status?: string;
  last_run_keys_loaded: number;
  last_run_duration_ms: number;
  last_run_error?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PreloadTaskCreate {
  name: string;
  description?: string;
  region_code?: string;
  keys_pattern?: string;
  keys_list?: string[];
  loader_type: string;
  loader_config?: Record<string, unknown>;
  schedule_cron?: string;
  is_active?: boolean;
}

export interface PreloadRunResponse {
  task_id: string;
  status: string;
  keys_loaded: number;
  duration_ms: number;
  error?: string;
}

// ============================================================================
// ALERTS
// ============================================================================

export interface CacheAlert {
  id: string;
  tenant_id: string;
  alert_type: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  threshold_value?: number;
  actual_value?: number;
  cache_level?: CacheLevel;
  region_code?: string;
  triggered_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface TopKey {
  key: string;
  hit_count: number;
  region_code?: string;
  entity_type?: string;
}

export interface RecentInvalidation {
  id: string;
  invalidation_type: InvalidationType;
  keys_invalidated: number;
  created_at: string;
}

export interface CacheDashboard {
  config?: CacheConfig;
  stats: CacheStatsAggregated;
  top_keys: TopKey[];
  recent_invalidations: RecentInvalidation[];
  active_alerts: CacheAlert[];
  regions_count: number;
  preload_tasks_count: number;
  entries_count: number;
}

// ============================================================================
// PURGE
// ============================================================================

export interface PurgeRequest {
  level?: CacheLevel;
  region_code?: string;
  expired_only?: boolean;
  confirm: boolean;
}

export interface PurgeResponse {
  keys_purged: number;
  size_freed_bytes: number;
  levels_affected: CacheLevel[];
  duration_ms: number;
}

// ============================================================================
// AUDIT
// ============================================================================

export interface CacheAuditLog {
  id: string;
  tenant_id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  description?: string;
  success: boolean;
  error_message?: string;
  user_id?: string;
  user_email?: string;
  ip_address?: string;
  created_at: string;
}

// ============================================================================
// UTILITIES
// ============================================================================

export const EVICTION_POLICIES: { value: EvictionPolicy; label: string }[] = [
  { value: 'LRU', label: 'Least Recently Used' },
  { value: 'LFU', label: 'Least Frequently Used' },
  { value: 'FIFO', label: 'First In First Out' },
  { value: 'TTL', label: 'Time To Live' },
  { value: 'RANDOM', label: 'Random' },
];

export const CACHE_LEVELS: { value: CacheLevel; label: string; color: string }[] = [
  { value: 'L1_MEMORY', label: 'L1 Memoire', color: 'green' },
  { value: 'L2_REDIS', label: 'L2 Redis', color: 'blue' },
  { value: 'L3_PERSISTENT', label: 'L3 Persistant', color: 'purple' },
];

export const ALERT_SEVERITIES: { value: AlertSeverity; label: string; color: string }[] = [
  { value: 'INFO', label: 'Info', color: 'blue' },
  { value: 'WARNING', label: 'Attention', color: 'yellow' },
  { value: 'CRITICAL', label: 'Critique', color: 'red' },
];

export const ALERT_STATUSES: { value: AlertStatus; label: string; color: string }[] = [
  { value: 'ACTIVE', label: 'Active', color: 'red' },
  { value: 'ACKNOWLEDGED', label: 'Acquittee', color: 'yellow' },
  { value: 'RESOLVED', label: 'Resolue', color: 'green' },
];

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatHitRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function formatDuration(ms: number): string {
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function getCacheLevelColor(level: CacheLevel): string {
  const found = CACHE_LEVELS.find(l => l.value === level);
  return found?.color || 'gray';
}

export function getAlertSeverityColor(severity: AlertSeverity): string {
  const found = ALERT_SEVERITIES.find(s => s.value === severity);
  return found?.color || 'gray';
}
