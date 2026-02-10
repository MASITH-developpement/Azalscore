/**
 * AZALSCORE Module - Maintenance - Asset IA Tab
 * Onglet Assistant IA pour l'équipement
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Calendar, Wrench, Package, Shield } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Asset } from '../types';
import { formatDate, formatCurrency, formatHours } from '@/utils/formatters';
import {
  ASSET_STATUS_CONFIG, CRITICALITY_CONFIG,
  isMaintenanceOverdue, isMaintenanceDueSoon, isWarrantyExpired, isWarrantyExpiringSoon,
  getDaysUntilMaintenance, getAssetAge, getLowStockParts, getExpiringDocuments,
  getTotalMaintenanceCost, getTotalLaborHours, calculateMTBF, calculateMTTR
} from '../types';

// Composants partagés IA (AZA-NF-REUSE)
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';

/**
 * AssetIATab - Assistant IA pour l'équipement
 */
export const AssetIATab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(asset);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(asset);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cet équipement et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score santé équipement - Composant partagé */}
      <Card title="Santé de l'équipement" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={healthScore}
          label="Santé"
          details={`${positiveCount} points positifs, ${warningCount} alertes, ${suggestionCount} suggestions`}
        />
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights - Composant partagé */}
        <Card title="Insights IA">
          <InsightList insights={sharedInsights} />
        </Card>

        {/* Actions suggérées - Composant partagé */}
        <Card title="Actions suggérées">
          <SuggestedActionList
            actions={suggestedActions}
            emptyMessage="Aucune action suggérée pour le moment"
          />
        </Card>
      </Grid>

      {/* Analyse détaillée (ERP only) */}
      <Card
        title="Analyse détaillée"
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
            <h4>Criticité</h4>
            <p className={`text-lg font-medium text-${CRITICALITY_CONFIG[asset.criticality].color}`}>
              {CRITICALITY_CONFIG[asset.criticality].label}
            </p>
            <p className="text-sm text-muted">
              {CRITICALITY_CONFIG[asset.criticality].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Coût maintenance</h4>
            <p className="text-lg font-medium text-primary">
              {formatCurrency(getTotalMaintenanceCost(asset))}
            </p>
            <p className="text-sm text-muted">
              {formatHours(getTotalLaborHours(asset))} de main d'oeuvre
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Fiabilité (MTBF)</h4>
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'équipement
 */
function generateSuggestedActions(asset: Asset): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isMaintenanceOverdue(asset)) {
    actions.push({
      id: 'urgent-maintenance',
      title: 'Planifier maintenance urgente',
      description: 'La maintenance préventive est en retard.',
      confidence: 95,
      icon: <Wrench size={16} />,
      actionLabel: 'Planifier',
    });
  }

  if (isMaintenanceDueSoon(asset) && !isMaintenanceOverdue(asset)) {
    actions.push({
      id: 'prepare-maintenance',
      title: 'Préparer prochaine maintenance',
      description: `Maintenance prévue dans ${getDaysUntilMaintenance(asset)} jours.`,
      confidence: 90,
      icon: <Calendar size={16} />,
      actionLabel: 'Préparer',
    });
  }

  if (getLowStockParts(asset).length > 0) {
    actions.push({
      id: 'order-parts',
      title: 'Commander pièces de rechange',
      description: `${getLowStockParts(asset).length} pièce(s) à réapprovisionner.`,
      confidence: 85,
      icon: <Package size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (isWarrantyExpiringSoon(asset) && !isWarrantyExpired(asset)) {
    actions.push({
      id: 'check-warranty',
      title: 'Vérifier extension garantie',
      description: 'La garantie expire bientôt.',
      confidence: 80,
      icon: <Shield size={16} />,
      actionLabel: 'Vérifier',
    });
  }

  if (getExpiringDocuments(asset).length > 0) {
    actions.push({
      id: 'renew-docs',
      title: 'Renouveler documents',
      description: `${getExpiringDocuments(asset).length} document(s) à renouveler.`,
      confidence: 75,
      icon: <Shield size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (asset.status === 'OPERATIONAL') {
    actions.push({
      id: 'optimize-maintenance',
      title: 'Optimiser le plan de maintenance',
      description: 'Analyser les données pour ajuster les fréquences.',
      confidence: 70,
      icon: <TrendingUp size={16} />,
      actionLabel: 'Analyser',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'équipement
 */
function generateInsights(asset: Asset): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (asset.status === 'OPERATIONAL') {
    insights.push({
      id: 'operational',
      type: 'success',
      title: 'Équipement opérationnel',
      description: "L'équipement fonctionne normalement.",
    });
  } else if (asset.status === 'UNDER_MAINTENANCE') {
    insights.push({
      id: 'under-maintenance',
      type: 'warning',
      title: 'En maintenance',
      description: "L'équipement est actuellement en maintenance.",
    });
  } else if (asset.status === 'OUT_OF_SERVICE') {
    insights.push({
      id: 'out-of-service',
      type: 'warning',
      title: 'Hors service',
      description: "L'équipement est hors service.",
    });
  }

  // Maintenance
  if (isMaintenanceOverdue(asset)) {
    const days = Math.abs(getDaysUntilMaintenance(asset) || 0);
    insights.push({
      id: 'maintenance-overdue',
      type: 'warning',
      title: 'Maintenance en retard',
      description: `${days} jour(s) de retard sur la maintenance préventive.`,
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
      title: 'Planning maintenance respecté',
      description: 'La maintenance préventive est à jour.',
    });
  }

  // Garantie
  if (isWarrantyExpired(asset)) {
    insights.push({
      id: 'warranty-expired',
      type: 'warning',
      title: 'Garantie expirée',
      description: "L'équipement n'est plus sous garantie.",
    });
  } else if (isWarrantyExpiringSoon(asset)) {
    insights.push({
      id: 'warranty-expiring',
      type: 'warning',
      title: 'Garantie bientôt expirée',
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

  // Pièces de rechange
  const lowStockParts = getLowStockParts(asset);
  if (lowStockParts.length > 0) {
    const criticalParts = lowStockParts.filter(p => p.quantity_on_hand === 0);
    if (criticalParts.length > 0) {
      insights.push({
        id: 'parts-critical',
        type: 'warning',
        title: 'Pièces en rupture',
        description: `${criticalParts.length} pièce(s) de rechange en rupture de stock.`,
      });
    } else {
      insights.push({
        id: 'parts-low',
        type: 'suggestion',
        title: 'Stock pièces faible',
        description: `${lowStockParts.length} pièce(s) sous le seuil minimum.`,
      });
    }
  }

  // Documents
  const expiringDocs = getExpiringDocuments(asset);
  if (expiringDocs.length > 0) {
    insights.push({
      id: 'docs-expiring',
      type: 'warning',
      title: 'Documents à renouveler',
      description: `${expiringDocs.length} document(s) expiré(s) ou expirant bientôt.`,
    });
  }

  // Âge de l'équipement
  const age = getAssetAge(asset);
  if (age !== null && age >= 10) {
    insights.push({
      id: 'old-asset',
      type: 'suggestion',
      title: 'Équipement ancien',
      description: `${age} ans - envisager le remplacement ou la rénovation.`,
    });
  }

  // Criticité
  if (asset.criticality === 'CRITICAL') {
    insights.push({
      id: 'critical-asset',
      type: 'suggestion',
      title: 'Équipement critique',
      description: 'Surveillance renforcée recommandée.',
    });
  }

  // Fiabilité
  const mtbf = calculateMTBF(asset);
  const mttr = calculateMTTR(asset);
  if (mtbf && mtbf < 1000) {
    insights.push({
      id: 'low-mtbf',
      type: 'warning',
      title: 'Fiabilité faible',
      description: `MTBF de ${mtbf}h - pannes fréquentes.`,
    });
  }
  if (mttr && mttr > 8) {
    insights.push({
      id: 'high-mttr',
      type: 'suggestion',
      title: 'Temps de réparation élevé',
      description: `MTTR de ${mttr}h - optimiser les procédures.`,
    });
  }

  return insights;
}

export default AssetIATab;
