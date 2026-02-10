/**
 * AZALSCORE - Shared IA Component - InsightItem
 * ==============================================
 * Composant partagé pour afficher un insight IA.
 * Réutilisable dans tous les onglets IA de l'application.
 */

import React from 'react';
import { ThumbsUp, AlertTriangle, Lightbulb, Info } from 'lucide-react';

/**
 * Types d'insight supportés
 */
export type InsightType = 'success' | 'warning' | 'suggestion' | 'info';

/**
 * Interface d'un insight
 */
export interface Insight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  metadata?: Record<string, unknown>;
}

/**
 * Props du composant InsightItem
 */
export interface InsightItemProps {
  insight: Insight;
  onClick?: (insight: Insight) => void;
  className?: string;
}

/**
 * Mapping des icônes par type d'insight
 */
const INSIGHT_ICONS: Record<InsightType, React.ReactNode> = {
  success: <ThumbsUp size={16} className="text-success" />,
  warning: <AlertTriangle size={16} className="text-warning" />,
  suggestion: <Lightbulb size={16} className="text-primary" />,
  info: <Info size={16} className="text-blue" />,
};

/**
 * InsightItem - Composant d'affichage d'un insight IA
 */
export const InsightItem: React.FC<InsightItemProps> = ({
  insight,
  onClick,
  className = '',
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(insight);
    }
  };

  return (
    <div
      className={`azals-insight azals-insight--${insight.type} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={handleClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="azals-insight__icon">
        {INSIGHT_ICONS[insight.type]}
      </div>
      <div className="azals-insight__content">
        <h4 className="azals-insight__title">{insight.title}</h4>
        <p className="azals-insight__description">{insight.description}</p>
      </div>
    </div>
  );
};

/**
 * Composant pour afficher une liste d'insights
 */
export interface InsightListProps {
  insights: Insight[];
  onInsightClick?: (insight: Insight) => void;
  emptyMessage?: string;
  className?: string;
}

export const InsightList: React.FC<InsightListProps> = ({
  insights,
  onInsightClick,
  emptyMessage = 'Aucun insight disponible',
  className = '',
}) => {
  if (insights.length === 0) {
    return (
      <div className={`azals-empty azals-empty--sm ${className}`}>
        <Lightbulb size={32} className="text-muted" />
        <p className="text-muted">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`azals-insights-list ${className}`}>
      {insights.map((insight) => (
        <InsightItem
          key={insight.id}
          insight={insight}
          onClick={onInsightClick}
        />
      ))}
    </div>
  );
};

/**
 * Hook utilitaire pour compter les insights par type
 */
export function useInsightStats(insights: Insight[]) {
  return {
    total: insights.length,
    success: insights.filter(i => i.type === 'success').length,
    warning: insights.filter(i => i.type === 'warning').length,
    suggestion: insights.filter(i => i.type === 'suggestion').length,
    info: insights.filter(i => i.type === 'info').length,
    score: Math.round(
      (insights.filter(i => i.type !== 'warning').length / Math.max(insights.length, 1)) * 100
    ),
  };
}

export default InsightItem;
