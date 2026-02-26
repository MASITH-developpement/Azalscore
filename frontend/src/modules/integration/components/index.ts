/**
 * AZALS MODULE GAP-086 - Integration Hub - Components Index
 * Re-exports tous les composants
 */

// Status Badges & Helpers
export {
  ConnectionStatusBadge,
  HealthStatusBadge,
  SyncStatusBadge,
  getCategoryIcon
} from './StatusBadges';

// Dashboard
export { IntegrationDashboard } from './IntegrationDashboard';
export type { IntegrationDashboardProps } from './IntegrationDashboard';

// Lists
export { ConnectorsList } from './ConnectorsList';
export type { ConnectorsListProps } from './ConnectorsList';

export { ConnectionsList } from './ConnectionsList';
export type { ConnectionsListProps } from './ConnectionsList';

export { ExecutionsList } from './ExecutionsList';
export type { ExecutionsListProps } from './ExecutionsList';

export { ConflictsList } from './ConflictsList';
export type { ConflictsListProps } from './ConflictsList';

// Detail & Form
export { ConnectionDetail } from './ConnectionDetail';
export type { ConnectionDetailProps } from './ConnectionDetail';

export { ConnectionForm } from './ConnectionForm';
export type { ConnectionFormProps } from './ConnectionForm';
