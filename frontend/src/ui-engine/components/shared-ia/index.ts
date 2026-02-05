/**
 * AZALSCORE - Shared IA Components
 * =================================
 * Composants partagés pour les onglets IA.
 *
 * Usage:
 * import { InsightItem, SuggestedAction, IAScoreCircle } from '@ui/components/shared-ia';
 */

export {
  InsightItem,
  InsightList,
  useInsightStats,
  type Insight,
  type InsightType,
  type InsightItemProps,
  type InsightListProps,
} from './InsightItem';

export {
  SuggestedAction,
  SuggestedActionList,
  useSortedActions,
  getConfidenceLevel,
  type SuggestedActionData,
  type SuggestedActionProps,
  type SuggestedActionListProps,
  type ConfidenceLevel,
} from './SuggestedAction';

export {
  IAScoreCircle,
  IAScoreGrid,
  type IAScoreCircleProps,
  type IAScoreGridProps,
  type ScoreData,
} from './IAScoreCircle';

export {
  IAPanelHeader,
  type IAPanelHeaderProps,
} from './IAPanelHeader';
