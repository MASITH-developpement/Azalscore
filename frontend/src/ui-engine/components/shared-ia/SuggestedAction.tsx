/**
 * AZALSCORE - Shared IA Component - SuggestedAction
 * ==================================================
 * Composant partagé pour afficher une action suggérée par l'IA.
 * Réutilisable dans tous les onglets IA de l'application.
 */

import React from 'react';
import { ChevronRight, Sparkles } from 'lucide-react';
import { Button } from '@ui/actions';

/**
 * Niveaux de confiance
 */
export type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Interface d'une action suggérée
 */
export interface SuggestedActionData {
  id?: string;
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
  actionLabel?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Props du composant SuggestedAction
 */
export interface SuggestedActionProps {
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
  actionLabel?: string;
  onClick?: () => void;
  onAction?: () => void;
  className?: string;
}

/**
 * Détermine le niveau de confiance basé sur le score
 */
export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 80) return 'high';
  if (confidence >= 60) return 'medium';
  return 'low';
}

/**
 * SuggestedAction - Composant d'affichage d'une action suggérée
 */
export const SuggestedAction: React.FC<SuggestedActionProps> = ({
  title,
  description,
  confidence,
  icon,
  actionLabel,
  onClick,
  onAction,
  className = '',
}) => {
  const level = getConfidenceLevel(confidence);

  return (
    <div
      className={`azals-suggested-action ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="azals-suggested-action__content">
        <h4>
          {icon && <span className="mr-2">{icon}</span>}
          {title}
        </h4>
        <p className="text-muted text-sm">{description}</p>
      </div>
      <div className="azals-suggested-action__meta">
        <span className={`azals-confidence azals-confidence--${level}`}>
          {confidence}%
        </span>
        {actionLabel && onAction && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onAction()}
          >
            {actionLabel}
            <ChevronRight size={14} className="ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
};

/**
 * Composant pour afficher une liste d'actions suggérées
 */
export interface SuggestedActionListProps {
  actions: SuggestedActionData[];
  onActionClick?: (action: SuggestedActionData) => void;
  onActionExecute?: (action: SuggestedActionData) => void;
  emptyMessage?: string;
  className?: string;
}

export const SuggestedActionList: React.FC<SuggestedActionListProps> = ({
  actions,
  onActionClick,
  onActionExecute,
  emptyMessage = 'Aucune action suggérée',
  className = '',
}) => {
  if (actions.length === 0) {
    return (
      <div className={`azals-empty azals-empty--sm ${className}`}>
        <Sparkles size={32} className="text-muted" />
        <p className="text-muted">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`azals-suggested-actions ${className}`}>
      {actions.map((action, index) => (
        <SuggestedAction
          key={action.id || index}
          title={action.title}
          description={action.description}
          confidence={action.confidence}
          icon={action.icon}
          actionLabel={action.actionLabel}
          onClick={onActionClick ? () => onActionClick(action) : undefined}
          onAction={onActionExecute ? () => onActionExecute(action) : undefined}
        />
      ))}
    </div>
  );
};

/**
 * Hook utilitaire pour trier les actions par confiance
 */
export function useSortedActions(actions: SuggestedActionData[]) {
  return [...actions].sort((a, b) => b.confidence - a.confidence);
}

export default SuggestedAction;
