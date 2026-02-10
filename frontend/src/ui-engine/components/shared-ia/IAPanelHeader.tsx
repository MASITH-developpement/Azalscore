/**
 * AZALSCORE - Shared IA Component - IAPanelHeader
 * ================================================
 * Composant partagé pour l'en-tête du panel IA.
 * Réutilisable dans tous les onglets IA de l'application.
 */

import React, { useState } from 'react';
import { Sparkles, RefreshCw, MessageSquare, Settings } from 'lucide-react';
import { Button } from '@ui/actions';

/**
 * Props du composant IAPanelHeader
 */
export interface IAPanelHeaderProps {
  title?: string;
  subtitle?: string;
  insightCount?: number;
  warningCount?: number;
  onRefresh?: () => Promise<void> | void;
  onAskQuestion?: () => void;
  onSettings?: () => void;
  isLoading?: boolean;
  className?: string;
}

/**
 * IAPanelHeader - En-tête du panel IA avec actions
 */
export const IAPanelHeader: React.FC<IAPanelHeaderProps> = ({
  title = 'Assistant AZALSCORE IA',
  subtitle,
  insightCount,
  warningCount,
  onRefresh,
  onAskQuestion,
  onSettings,
  isLoading = false,
  className = '',
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh) return;

    setIsAnalyzing(true);
    try {
      await onRefresh();
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loading = isLoading || isAnalyzing;

  return (
    <div className={`azals-std-ia-panel azals-std-azalscore-only ${className}`}>
      <div className="azals-std-ia-panel__header">
        <Sparkles size={24} className="azals-std-ia-panel__icon" />
        <h3 className="azals-std-ia-panel__title">{title}</h3>
      </div>
      <div className="azals-std-ia-panel__content">
        <p>
          {subtitle || (
            <>
              J'ai analysé ces données et identifié{' '}
              <strong>{insightCount ?? 0} points d'attention</strong>.
              {warningCount !== undefined && warningCount > 0 && (
                <span className="text-warning ml-1">
                  ({warningCount} alertes)
                </span>
              )}
            </>
          )}
        </p>
      </div>
      <div className="azals-std-ia-panel__actions">
        {onRefresh && (
          <Button
            variant="secondary"
            leftIcon={<RefreshCw size={16} className={loading ? 'azals-spin' : ''} />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Relancer l'analyse
          </Button>
        )}
        {onAskQuestion && (
          <Button
            variant="ghost"
            leftIcon={<MessageSquare size={16} />}
            onClick={onAskQuestion}
            disabled={loading}
          >
            Poser une question
          </Button>
        )}
        {onSettings && (
          <Button
            variant="ghost"
            leftIcon={<Settings size={16} />}
            onClick={onSettings}
            disabled={loading}
          >
            Paramètres
          </Button>
        )}
      </div>
    </div>
  );
};

export default IAPanelHeader;
