/**
 * AZALSCORE - Cache API Client
 * =============================
 * Client API type pour la gestion du cache applicatif.
 */

import { api } from '@core/api-client';
import type {
  CacheConfig,
  CacheConfigCreate,
  CacheConfigUpdate,
  CacheRegion,
  CacheRegionCreate,
  CacheRegionUpdate,
  CacheGetResponse,
  CacheMGetResponse,
  CacheSetRequest,
  InvalidationResponse,
  CacheStatsAggregated,
  CacheDashboard,
  PreloadTask,
  PreloadTaskCreate,
  PreloadRunResponse,
  CacheAlert,
  PurgeRequest,
  PurgeResponse,
  CacheAuditLog,
  CacheLevel,
  AlertStatus,
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/cache';

export const cacheApi = {
  // --------------------------------------------------------------------------
  // Configuration
  // --------------------------------------------------------------------------

  getConfig: () =>
    api.get<CacheConfig>(`${BASE_PATH}/config`),

  createConfig: (data: CacheConfigCreate) =>
    api.post<CacheConfig>(`${BASE_PATH}/config`, data),

  updateConfig: (data: CacheConfigUpdate) =>
    api.patch<CacheConfig>(`${BASE_PATH}/config`, data),

  // --------------------------------------------------------------------------
  // Regions
  // --------------------------------------------------------------------------

  listRegions: (skip = 0, limit = 50) =>
    api.get<CacheRegion[]>(`${BASE_PATH}/regions${buildQueryString({ skip, limit })}`),

  getRegion: (regionId: string) =>
    api.get<CacheRegion>(`${BASE_PATH}/regions/${regionId}`),

  createRegion: (data: CacheRegionCreate) =>
    api.post<CacheRegion>(`${BASE_PATH}/regions`, data),

  updateRegion: (regionId: string, data: CacheRegionUpdate) =>
    api.patch<CacheRegion>(`${BASE_PATH}/regions/${regionId}`, data),

  deleteRegion: (regionId: string) =>
    api.delete(`${BASE_PATH}/regions/${regionId}`),

  // --------------------------------------------------------------------------
  // Cache Operations
  // --------------------------------------------------------------------------

  getEntry: (key: string, region?: string) =>
    api.get<CacheGetResponse>(
      `${BASE_PATH}/entries/${encodeURIComponent(key)}${buildQueryString({ region })}`
    ),

  setEntry: (data: CacheSetRequest) =>
    api.post<{ success: boolean; key: string }>(`${BASE_PATH}/entries`, data),

  deleteEntry: (key: string) =>
    api.delete(`${BASE_PATH}/entries/${encodeURIComponent(key)}`),

  checkEntry: (key: string) =>
    api.get<{ exists: boolean }>(`${BASE_PATH}/entries/${encodeURIComponent(key)}/exists`),

  mgetEntries: (keys: string[]) =>
    api.post<CacheMGetResponse>(`${BASE_PATH}/entries/mget`, keys),

  msetEntries: (data: {
    items: Record<string, unknown>;
    ttl_seconds?: number;
    tags?: string[];
    region?: string;
  }) =>
    api.post<{ success: boolean; count: number }>(`${BASE_PATH}/entries/mset`, data),

  // --------------------------------------------------------------------------
  // Invalidation
  // --------------------------------------------------------------------------

  invalidateByKey: (key: string) =>
    api.post<InvalidationResponse>(`${BASE_PATH}/invalidate/key`, { key }),

  invalidateByPattern: (pattern: string) =>
    api.post<InvalidationResponse>(`${BASE_PATH}/invalidate/pattern`, { pattern }),

  invalidateByTag: (tag: string) =>
    api.post<InvalidationResponse>(`${BASE_PATH}/invalidate/tag`, { tag }),

  invalidateByEntity: (entityType: string, entityId?: string) =>
    api.post<InvalidationResponse>(`${BASE_PATH}/invalidate/entity`, {
      entity_type: entityType,
      entity_id: entityId,
    }),

  invalidateAll: () =>
    api.post<InvalidationResponse>(`${BASE_PATH}/invalidate/all`),

  // --------------------------------------------------------------------------
  // Purge
  // --------------------------------------------------------------------------

  purge: (data: PurgeRequest) =>
    api.post<PurgeResponse>(`${BASE_PATH}/purge`, data),

  // --------------------------------------------------------------------------
  // Statistics
  // --------------------------------------------------------------------------

  getStats: (level?: CacheLevel) =>
    api.get<CacheStatsAggregated>(`${BASE_PATH}/stats${buildQueryString({ level })}`),

  // --------------------------------------------------------------------------
  // Preload
  // --------------------------------------------------------------------------

  listPreloadTasks: (skip = 0, limit = 50) =>
    api.get<PreloadTask[]>(`${BASE_PATH}/preload${buildQueryString({ skip, limit })}`),

  createPreloadTask: (data: PreloadTaskCreate) =>
    api.post<PreloadTask>(`${BASE_PATH}/preload`, data),

  runPreloadTask: (taskId: string) =>
    api.post<PreloadRunResponse>(`${BASE_PATH}/preload/${taskId}/run`),

  // --------------------------------------------------------------------------
  // Alerts
  // --------------------------------------------------------------------------

  listAlerts: (status?: AlertStatus, limit = 50) =>
    api.get<CacheAlert[]>(`${BASE_PATH}/alerts${buildQueryString({ status, limit })}`),

  acknowledgeAlert: (alertId: string, notes?: string) =>
    api.post<CacheAlert>(`${BASE_PATH}/alerts/${alertId}/acknowledge`, { notes }),

  resolveAlert: (alertId: string, resolutionNotes: string) =>
    api.post<CacheAlert>(`${BASE_PATH}/alerts/${alertId}/resolve`, {
      resolution_notes: resolutionNotes,
    }),

  checkThresholds: () =>
    api.post<CacheAlert[]>(`${BASE_PATH}/alerts/check`),

  // --------------------------------------------------------------------------
  // Dashboard
  // --------------------------------------------------------------------------

  getDashboard: () =>
    api.get<CacheDashboard>(`${BASE_PATH}/dashboard`),

  // --------------------------------------------------------------------------
  // Audit
  // --------------------------------------------------------------------------

  getAuditLogs: (skip = 0, limit = 50) =>
    api.get<CacheAuditLog[]>(`${BASE_PATH}/audit${buildQueryString({ skip, limit })}`),
};

export default cacheApi;
