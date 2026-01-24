/**
 * AZALSCORE Module - Maintenance - Asset IA Tab
 * Onglet Assistant IA pour l'equipement
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Calendar, Wrench, Package, Shield, Euro
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset } from '../types';
import {
  formatDate, formatCurrency, formatHours,
  ASSET_STATUS_CONFIG, CRITICALITY_CONFIG,
  isMaintenanceOverdue, isMaintenanceDueSoon, isWarrantyExpired, isWarrantyExpiringSoon,
  getDaysUntilMaintenance, getAssetAge, getLowStockParts, getExpiringDocuments,
  getTotalMaintenanceCost, getTotalLaborHours, calculateMTBF, calculateMTTR
} from '../types';

/**
 * AssetIATab - Assistant IA pour l'equipement
 */
export const AssetIATab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(asset);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tete IA (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analyse cet equipement et identifie{' '}
            <strong>{insights.length} points d'attention</strong>.
            {insights.filter(i => i.type === 'warning').length > 0 && (
              <span className="text-warning ml-1">
                ({insights.filter(i => i.type === 'warning').length} alertes)
              </span>
            )}
          </p>
        </div>
        <div className="azals-std-ia-panel__actions">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw size={16} className={isAnalyzing ? 'azals-spin' : ''} />}
            onClick={handleRefreshAnalysis}
            disabled={isAnalyzing}
          >
            Relancer l'analyse
          </Button>
          <Button variant="ghost" leftIcon={<MessageSquare size={16} />}>
            Poser une question
          </Button>
        </div>
      </div>

      {/* Score sante equipement */}
      <Card title="Sante de l'equipement" icon={<TrendingUp size={18} />} className="mb-4">
        <div className="azals-score-display">
          <div className="azals-score-display__circle">
            <svg viewBox="0 0 36 36" className="azals-score-display__svg">
              <path
                className="azals-score-display__bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                className="azals-score-display__fg"
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 20}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="var(--azals-primary-500)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {Math.round((insights.filter(i => i.type !== 'warning').length / Math.max(insights.length, 1)) * 100)}%
            </span>
          </div>
          <div className="azals-score-display__details">
            <p>
              {insights.filter(i => i.type === 'success').length} points positifs,{' '}
              {insights.filter(i => i.type === 'warning').length} alertes,{' '}
              {insights.filter(i => i.type === 'suggestion').length} suggestions
            </p>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights */}
        <Card title="Insights IA" icon={<Lightbulb size={18} />}>
          <div className="azals-insights-list">
            {insights.map((insight) => (
              <InsightItem key={insight.id} insight={insight} />
            ))}
          </div>
        </Card>

        {/* Actions suggerees */}
        <Card title="Actions suggerees" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {isMaintenanceOverdue(asset) && (
              <SuggestedAction
                title="Planifier maintenance urgente"
                description="La maintenance preventive est en retard."
                confidence={95}
                icon={<Wrench size={16} />}
              />
            )}
            {isMaintenanceDueSoon(asset) && !isMaintenanceOverdue(asset) && (
              <SuggestedAction
                title="Preparer prochaine maintenance"
                description={`Maintenance prevue dans ${getDaysUntilMaintenance(asset)} jours.`}
                confidence={90}
                icon={<Calendar size={16} />}
              />
            )}
            {getLowStockParts(asset).length > 0 && (
              <SuggestedAction
                title="Commander pieces de rechange"
                description={`${getLowStockParts(asset).length} piece(s) a reapprovisionner.`}
                confidence={85}
                icon={<Package size={16} />}
              />
            )}
            {isWarrantyExpiringSoon(asset) && !isWarrantyExpired(asset) && (
              <SuggestedAction
                title="Verifier extension garantie"
                description="La garantie expire bientot."
                confidence={80}
                icon={<Shield size={16} />}
              />
            )}
            {getExpiringDocuments(asset).length > 0 && (
              <SuggestedAction
                title="Renouveler documents"
                description={`${getExpiringDocuments(asset).length} document(s) a renouveler.`}
                confidence={75}
                icon={<Shield size={16} />}
              />
            )}
            {asset.status === 'OPERATIONAL' && (
              <SuggestedAction
                title="Optimiser le plan de maintenance"
                description="Analyser les donnees pour ajuster les frequences."
                confidence={70}
                icon={<TrendingUp size={16} />}
              />
            )}
          </div>
        </Card>
      </Grid>

      {/* Analyse detaillee (ERP only) */}
      <Card
        title="Analyse detaillee"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${ASSET_STATUS_CONFIG[asset.status].color}`}>
              {ASSET_STATUS_CONFIG[asset.status].label}
            </p>
            <p className="text-sm text-muted">
              {ASSET_STATUS_CONFIG[asset.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Criticite</h4>
            <p className={`text-lg font-medium text-${CRITICALITY_CONFIG[asset.criticality].color}`}>
              {CRITICALITY_CONFIG[asset.criticality].label}
            </p>
            <p className="text-sm text-muted">
              {CRITICALITY_CONFIG[asset.criticality].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Cout maintenance</h4>
            <p className="text-lg font-medium text-primary">
              {formatCurrency(getTotalMaintenanceCost(asset))}
            </p>
            <p className="text-sm text-muted">
              {formatHours(getTotalLaborHours(asset))} de main d'oeuvre
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Fiabilite (MTBF)</h4>
            <p className="text-lg font-medium">
              {calculateMTBF(asset) ? `${calculateMTBF(asset)}h` : 'N/A'}
            </p>
            <p className="text-sm text-muted">
              MTTR: {calculateMTTR(asset) ? `${calculateMTTR(asset)}h` : 'N/A'}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Types pour les insights
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Composant item d'insight
 */
const InsightItem: React.FC<{ insight: Insight }> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case 'success':
        return <ThumbsUp size={16} className="text-success" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-warning" />;
      case 'suggestion':
        return <Lightbulb size={16} className="text-primary" />;
    }
  };

  return (
    <div className={`azals-insight azals-insight--${insight.type}`}>
      <div className="azals-insight__icon">{getIcon()}</div>
      <div className="azals-insight__content">
        <h4 className="azals-insight__title">{insight.title}</h4>
        <p className="azals-insight__description">{insight.description}</p>
      </div>
    </div>
  );
};

/**
 * Composant action suggeree
 */
interface SuggestedActionProps {
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
}

const SuggestedAction: React.FC<SuggestedActionProps> = ({ title, description, confidence, icon }) => {
  return (
    <div className="azals-suggested-action">
      <div className="azals-suggested-action__content">
        <h4>
          {icon && <span className="mr-2">{icon}</span>}
          {title}
        </h4>
        <p className="text-muted text-sm">{description}</p>
      </div>
      <div className="azals-suggested-action__confidence">
        <span className={`azals-confidence azals-confidence--${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`}>
          {confidence}%
        </span>
      </div>
    </div>
  );
};

/**
 * Generer les insights bases sur l'equipement
 */
function generateInsights(asset: Asset): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (asset.status === 'OPERATIONAL') {
    insights.push({
      id: 'operational',
      type: 'success',
      title: 'Equipement operationnel',
      description: 'L\'equipement fonctionne normalement.',
    });
  } else if (asset.status === 'UNDER_MAINTENANCE') {
    insights.push({
      id: 'under-maintenance',
      type: 'warning',
      title: 'En maintenance',
      description: 'L\'equipement est actuellement en maintenance.',
    });
  } else if (asset.status === 'OUT_OF_SERVICE') {
    insights.push({
      id: 'out-of-service',
      type: 'warning',
      title: 'Hors service',
      description: 'L\'equipement est hors service.',
    });
  }

  // Maintenance
  if (isMaintenanceOverdue(asset)) {
    const days = Math.abs(getDaysUntilMaintenance(asset) || 0);
    insights.push({
      id: 'maintenance-overdue',
      type: 'warning',
      title: 'Maintenance en retard',
      description: `${days} jour(s) de retard sur la maintenance preventive.`,
    });
  } else if (isMaintenanceDueSoon(asset)) {
    insights.push({
      id: 'maintenance-soon',
      type: 'suggestion',
      title: 'Maintenance proche',
      description: `Prochaine maintenance dans ${getDaysUntilMaintenance(asset)} jours.`,
    });
  } else if (asset.next_maintenance_date) {
    insights.push({
      id: 'maintenance-ok',
      type: 'success',
      title: 'Planning maintenance respecte',
      description: 'La maintenance preventive est a jour.',
    });
  }

  // Garantie
  if (isWarrantyExpired(asset)) {
    insights.push({
      id: 'warranty-expired',
      type: 'warning',
      title: 'Garantie expiree',
      description: 'L\'equipement n\'est plus sous garantie.',
    });
  } else if (isWarrantyExpiringSoon(asset)) {
    insights.push({
      id: 'warranty-expiring',
      type: 'warning',
      title: 'Garantie bientot expiree',
      description: `La garantie expire le ${formatDate(asset.warranty_end_date)}.`,
    });
  } else if (asset.warranty_end_date) {
    insights.push({
      id: 'warranty-ok',
      type: 'success',
      title: 'Sous garantie',
      description: `Garantie valide jusqu'au ${formatDate(asset.warranty_end_date)}.`,
    });
  }

  // Pieces de rechange
  const lowStockParts = getLowStockParts(asset);
  if (lowStockParts.length > 0) {
    const criticalParts = lowStockParts.filter(p => p.quantity_on_hand === 0);
    if (criticalParts.length > 0) {
      insights.push({
        id: 'parts-critical',
        type: 'warning',
        title: 'Pieces en rupture',
        description: `${criticalParts.length} piece(s) de rechange en rupture de stock.`,
      });
    } else {
      insights.push({
        id: 'parts-low',
        type: 'suggestion',
        title: 'Stock pieces faible',
        description: `${lowStockParts.length} piece(s) sous le seuil minimum.`,
      });
    }
  }

  // Documents
  const expiringDocs = getExpiringDocuments(asset);
  if (expiringDocs.length > 0) {
    insights.push({
      id: 'docs-expiring',
      type: 'warning',
      title: 'Documents a renouveler',
      description: `${expiringDocs.length} document(s) expire(s) ou expirant bientot.`,
    });
  }

  // Age de l'equipement
  const age = getAssetAge(asset);
  if (age !== null && age >= 10) {
    insights.push({
      id: 'old-asset',
      type: 'suggestion',
      title: 'Equipement ancien',
      description: `${age} ans - envisager le remplacement ou la renovation.`,
    });
  }

  // Criticite
  if (asset.criticality === 'CRITICAL') {
    insights.push({
      id: 'critical-asset',
      type: 'suggestion',
      title: 'Equipement critique',
      description: 'Surveillance renforcee recommandee.',
    });
  }

  // Fiabilite
  const mtbf = calculateMTBF(asset);
  const mttr = calculateMTTR(asset);
  if (mtbf && mtbf < 1000) {
    insights.push({
      id: 'low-mtbf',
      type: 'warning',
      title: 'Fiabilite faible',
      description: `MTBF de ${mtbf}h - pannes frequentes.`,
    });
  }
  if (mttr && mttr > 8) {
    insights.push({
      id: 'high-mttr',
      type: 'suggestion',
      title: 'Temps de reparation eleve',
      description: `MTTR de ${mttr}h - optimiser les procedures.`,
    });
  }

  return insights;
}

export default AssetIATab;
