/**
 * AZALS MODULE GAP-086 - API Integration
 * =======================================
 *
 * Client API pour le module Integration.
 */

import type {
  AutocompleteItem,
  ConflictFilters,
  ConflictResolve,
  Connection,
  ConnectionCreate,
  ConnectionFilters,
  ConnectionHealth,
  ConnectionListItem,
  ConnectionStats,
  ConnectionUpdate,
  ConnectorDefinition,
  DataMapping,
  DataMappingCreate,
  ExecutionLog,
  IntegrationStats,
  PaginatedResponse,
  SyncConfiguration,
  SyncConfigurationCreate,
  SyncConflict,
  SyncExecution,
  SyncExecutionCreate,
  SyncExecutionFilters,
  Webhook,
  WebhookDirection,
  WebhookInboundCreate,
  WebhookLog,
  WebhookOutboundCreate,
  WebhookTest,
} from './types';

// Base URL de l'API
const BASE_URL = '/api/v1/integration';

// ============================================================================
// HELPERS
// ============================================================================

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// CONNECTOR DEFINITIONS
// ============================================================================

export async function listConnectors(
  category?: string
): Promise<{ items: ConnectorDefinition[]; total: number }> {
  const qs = buildQueryString({ category });
  return fetchApi(`/connectors${qs}`);
}

export async function getConnector(
  connectorType: string
): Promise<ConnectorDefinition> {
  return fetchApi(`/connectors/${connectorType}`);
}

// ============================================================================
// CONNECTIONS
// ============================================================================

export async function listConnections(
  filters: ConnectionFilters = {},
  page = 1,
  pageSize = 20,
  sortBy = 'created_at',
  sortDir = 'desc'
): Promise<PaginatedResponse<ConnectionListItem>> {
  const qs = buildQueryString({
    search: filters.search,
    connector_type: filters.connector_type,
    status: filters.status,
    health_status: filters.health_status,
    is_active: filters.is_active,
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_dir: sortDir,
  });
  return fetchApi(`/connections${qs}`);
}

export async function getConnection(id: string): Promise<Connection> {
  return fetchApi(`/connections/${id}`);
}

export async function createConnection(
  data: ConnectionCreate
): Promise<Connection> {
  return fetchApi('/connections', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateConnection(
  id: string,
  data: ConnectionUpdate
): Promise<Connection> {
  return fetchApi(`/connections/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteConnection(id: string): Promise<void> {
  return fetchApi(`/connections/${id}`, { method: 'DELETE' });
}

export async function testConnection(id: string): Promise<ConnectionHealth> {
  return fetchApi(`/connections/${id}/test`, { method: 'POST' });
}

export async function refreshConnectionToken(id: string): Promise<{ success: boolean }> {
  return fetchApi(`/connections/${id}/refresh-token`, { method: 'POST' });
}

export async function getConnectionStats(id: string): Promise<ConnectionStats> {
  return fetchApi(`/connections/${id}/stats`);
}

export async function autocompleteConnections(
  query: string,
  limit = 10
): Promise<{ items: AutocompleteItem[] }> {
  const qs = buildQueryString({ q: query, limit });
  return fetchApi(`/connections/autocomplete${qs}`);
}

// ============================================================================
// DATA MAPPINGS
// ============================================================================

export async function listMappings(
  connectionId: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<DataMapping>> {
  const qs = buildQueryString({ page, page_size: pageSize });
  return fetchApi(`/connections/${connectionId}/mappings${qs}`);
}

export async function getMapping(id: string): Promise<DataMapping> {
  return fetchApi(`/mappings/${id}`);
}

export async function createMapping(
  data: DataMappingCreate
): Promise<DataMapping> {
  return fetchApi('/mappings', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateMapping(
  id: string,
  data: Partial<DataMappingCreate>
): Promise<DataMapping> {
  return fetchApi(`/mappings/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteMapping(id: string): Promise<void> {
  return fetchApi(`/mappings/${id}`, { method: 'DELETE' });
}

// ============================================================================
// SYNC CONFIGURATIONS
// ============================================================================

export async function listSyncConfigs(
  connectionId?: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<SyncConfiguration>> {
  const qs = buildQueryString({ connection_id: connectionId, page, page_size: pageSize });
  return fetchApi(`/sync-configs${qs}`);
}

export async function getSyncConfig(id: string): Promise<SyncConfiguration> {
  return fetchApi(`/sync-configs/${id}`);
}

export async function createSyncConfig(
  data: SyncConfigurationCreate
): Promise<SyncConfiguration> {
  return fetchApi('/sync-configs', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateSyncConfig(
  id: string,
  data: Partial<SyncConfigurationCreate>
): Promise<SyncConfiguration> {
  return fetchApi(`/sync-configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteSyncConfig(id: string): Promise<void> {
  return fetchApi(`/sync-configs/${id}`, { method: 'DELETE' });
}

// ============================================================================
// SYNC EXECUTIONS
// ============================================================================

export async function listExecutions(
  filters: SyncExecutionFilters = {},
  page = 1,
  pageSize = 20,
  sortBy = 'started_at',
  sortDir = 'desc'
): Promise<PaginatedResponse<SyncExecution>> {
  const qs = buildQueryString({
    connection_id: filters.connection_id,
    config_id: filters.config_id,
    status: filters.status,
    direction: filters.direction,
    entity_type: filters.entity_type,
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_dir: sortDir,
  });
  return fetchApi(`/executions${qs}`);
}

export async function getExecution(id: string): Promise<SyncExecution> {
  return fetchApi(`/executions/${id}`);
}

export async function startExecution(
  data: SyncExecutionCreate
): Promise<SyncExecution> {
  return fetchApi('/executions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function cancelExecution(id: string): Promise<SyncExecution> {
  return fetchApi(`/executions/${id}/cancel`, { method: 'POST' });
}

export async function retryExecution(id: string): Promise<SyncExecution> {
  return fetchApi(`/executions/${id}/retry`, { method: 'POST' });
}

export async function getExecutionLogs(
  executionId: string,
  limit = 100,
  offset = 0
): Promise<PaginatedResponse<ExecutionLog>> {
  const qs = buildQueryString({ limit, offset });
  return fetchApi(`/executions/${executionId}/logs${qs}`);
}

// ============================================================================
// CONFLICTS
// ============================================================================

export async function listConflicts(
  filters: ConflictFilters = {},
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<SyncConflict>> {
  const qs = buildQueryString({
    execution_id: filters.execution_id,
    entity_type: filters.entity_type,
    is_resolved: filters.is_resolved,
    page,
    page_size: pageSize,
  });
  return fetchApi(`/conflicts${qs}`);
}

export async function getConflict(id: string): Promise<SyncConflict> {
  return fetchApi(`/conflicts/${id}`);
}

export async function resolveConflict(
  id: string,
  data: ConflictResolve
): Promise<SyncConflict> {
  return fetchApi(`/conflicts/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// WEBHOOKS
// ============================================================================

export async function listWebhooks(
  connectionId?: string,
  direction?: WebhookDirection,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<Webhook>> {
  const qs = buildQueryString({
    connection_id: connectionId,
    direction,
    page,
    page_size: pageSize,
  });
  return fetchApi(`/webhooks${qs}`);
}

export async function getWebhook(id: string): Promise<Webhook> {
  return fetchApi(`/webhooks/${id}`);
}

export async function createInboundWebhook(
  data: WebhookInboundCreate
): Promise<Webhook> {
  return fetchApi('/webhooks/inbound', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createOutboundWebhook(
  data: WebhookOutboundCreate
): Promise<Webhook> {
  return fetchApi('/webhooks/outbound', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateWebhook(
  id: string,
  data: Partial<WebhookOutboundCreate>
): Promise<Webhook> {
  return fetchApi(`/webhooks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteWebhook(id: string): Promise<void> {
  return fetchApi(`/webhooks/${id}`, { method: 'DELETE' });
}

export async function testWebhook(
  id: string,
  samplePayload?: Record<string, unknown>
): Promise<WebhookTest> {
  return fetchApi(`/webhooks/${id}/test`, {
    method: 'POST',
    body: JSON.stringify({ sample_payload: samplePayload }),
  });
}

export async function getWebhookLogs(
  webhookId: string,
  limit = 100,
  offset = 0
): Promise<PaginatedResponse<WebhookLog>> {
  const qs = buildQueryString({ limit, offset });
  return fetchApi(`/webhooks/${webhookId}/logs${qs}`);
}

// ============================================================================
// STATISTICS
// ============================================================================

export async function getStats(): Promise<IntegrationStats> {
  return fetchApi('/stats');
}

// ============================================================================
// EXPORT DEFAULT API OBJECT
// ============================================================================

const integrationApi = {
  // Connectors
  listConnectors,
  getConnector,

  // Connections
  listConnections,
  getConnection,
  createConnection,
  updateConnection,
  deleteConnection,
  testConnection,
  refreshConnectionToken,
  getConnectionStats,
  autocompleteConnections,

  // Mappings
  listMappings,
  getMapping,
  createMapping,
  updateMapping,
  deleteMapping,

  // Sync Configs
  listSyncConfigs,
  getSyncConfig,
  createSyncConfig,
  updateSyncConfig,
  deleteSyncConfig,

  // Executions
  listExecutions,
  getExecution,
  startExecution,
  cancelExecution,
  retryExecution,
  getExecutionLogs,

  // Conflicts
  listConflicts,
  getConflict,
  resolveConflict,

  // Webhooks
  listWebhooks,
  getWebhook,
  createInboundWebhook,
  createOutboundWebhook,
  updateWebhook,
  deleteWebhook,
  testWebhook,
  getWebhookLogs,

  // Stats
  getStats,
};

export default integrationApi;
