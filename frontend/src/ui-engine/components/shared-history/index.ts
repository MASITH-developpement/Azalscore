/**
 * AZALSCORE - Shared History Components
 * ======================================
 * Composants partagés pour les onglets historique et activités.
 *
 * Usage:
 * import { HistoryEntry, HistoryTimeline, ActivityItem } from '@ui/components/shared-history';
 */

export {
  HistoryEntry,
  HistoryTimeline,
  useSortedHistory,
  type HistoryEntryData,
  type HistoryEntryProps,
  type HistoryTimelineProps,
  type HistoryActionType,
} from './HistoryEntry';

export {
  ActivityItem,
  ActivityList,
  useActivityGroups,
  ACTIVITY_TYPE_CONFIG,
  ACTIVITY_STATUS_CONFIG,
  type ActivityData,
  type ActivityItemProps,
  type ActivityListProps,
  type ActivityType,
  type ActivityStatus,
} from './ActivityItem';

export {
  AuditLogTable,
  type AuditLogTableProps,
} from './AuditLogTable';
