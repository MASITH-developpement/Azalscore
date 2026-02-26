/**
 * AZALSCORE Module - Vehicles - Vehicle IA Tab
 * Onglet Assistant IA pour le véhicule
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, Calendar, Wrench, Shield, Euro } from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatCurrency } from '@/utils/formatters';
import {
  formatKilometers,
  calculCoutKm, getCO2Km, calculateAverageConsumption,
  getTotalMaintenanceCost, isInspectionDueSoon, isInspectionExpired,
  isInsuranceDueSoon, isRevisionDueSoon, getExpiringDocuments,
  getVehicleAge, FUEL_TYPE_CONFIG
} from '../types';
import type { Vehicule } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * VehicleIATab - Assistant IA pour le véhicule
 */
export const VehicleIATab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(vehicle);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(vehicle);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce véhicule et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score santé véhicule - Composant partagé */}
      <Card title="Santé du véhicule" icon={<TrendingUp size={18} />} className="mb-4">
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
            <h4>Type carburant</h4>
            <p className={`text-lg font-medium text-${FUEL_TYPE_CONFIG[vehicle.type_carburant].color}`}>
              {FUEL_TYPE_CONFIG[vehicle.type_carburant].label}
            </p>
            <p className="text-sm text-muted">
              {vehicle.type_carburant === 'electrique'
                ? 'Faibles émissions'
                : vehicle.type_carburant === 'hybride'
                ? 'Émissions réduites'
                : 'Émissions standard'
              }
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Coût au kilomètre</h4>
            <p className="text-lg font-medium text-primary">
              {calculCoutKm(vehicle).total.toFixed(3)} €/km
            </p>
            <p className="text-sm text-muted">
              {calculCoutKm(vehicle).total < 0.40 ? 'Économique' : calculCoutKm(vehicle).total < 0.55 ? 'Moyen' : 'Élevé'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Émissions CO2</h4>
            <p className="text-lg font-medium text-green-600">
              {getCO2Km(vehicle).toFixed(3)} kg/km
            </p>
            <p className="text-sm text-muted">
              {getCO2Km(vehicle) < 0.10 ? 'Très faible' : getCO2Km(vehicle) < 0.18 ? 'Faible' : 'Moyen'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Coût maintenance total</h4>
            <p className="text-lg font-medium">
              {formatCurrency(getTotalMaintenanceCost(vehicle))}
            </p>
            <p className="text-sm text-muted">
              {formatKilometers(vehicle.kilometrage_actuel)} parcourus
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
 * Générer les actions suggérées basées sur le véhicule
 */
function generateSuggestedActions(vehicle: Vehicule): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isInspectionExpired(vehicle)) {
    actions.push({
      id: 'urgent-inspection',
      title: 'Contrôle technique urgent',
      description: 'Le contrôle technique est expiré.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Planifier',
    });
  }

  if (isInspectionDueSoon(vehicle) && !isInspectionExpired(vehicle)) {
    actions.push({
      id: 'plan-inspection',
      title: 'Planifier contrôle technique',
      description: 'Le contrôle technique expire bientôt.',
      confidence: 95,
      icon: <Calendar size={16} />,
      actionLabel: 'Planifier',
    });
  }

  if (isInsuranceDueSoon(vehicle)) {
    actions.push({
      id: 'renew-insurance',
      title: 'Renouveler assurance',
      description: "L'assurance expire bientôt.",
      confidence: 90,
      icon: <Shield size={16} />,
      actionLabel: 'Renouveler',
    });
  }

  if (isRevisionDueSoon(vehicle)) {
    actions.push({
      id: 'plan-revision',
      title: 'Planifier révision',
      description: 'La prochaine révision approche.',
      confidence: 85,
      icon: <Wrench size={16} />,
      actionLabel: 'Planifier',
    });
  }

  if (getExpiringDocuments(vehicle).length > 0) {
    actions.push({
      id: 'renew-docs',
      title: 'Renouveler documents',
      description: `${getExpiringDocuments(vehicle).length} document(s) à renouveler.`,
      confidence: 80,
      icon: <Shield size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (vehicle.is_active) {
    actions.push({
      id: 'optimize-costs',
      title: 'Optimiser les coûts',
      description: 'Analyser les données pour réduire le coût/km.',
      confidence: 70,
      icon: <Euro size={16} />,
      actionLabel: 'Analyser',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le véhicule
 */
function generateInsights(vehicle: Vehicule): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (vehicle.is_active) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Véhicule actif',
      description: 'Le véhicule est opérationnel.',
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'warning',
      title: 'Véhicule inactif',
      description: "Le véhicule n'est pas en service.",
    });
  }

  // Contrôle technique
  if (isInspectionExpired(vehicle)) {
    insights.push({
      id: 'inspection-expired',
      type: 'warning',
      title: 'Contrôle technique expiré',
      description: 'Le contrôle technique doit être effectué immédiatement.',
    });
  } else if (isInspectionDueSoon(vehicle)) {
    insights.push({
      id: 'inspection-soon',
      type: 'warning',
      title: 'Contrôle technique proche',
      description: 'Le contrôle technique expire dans moins de 30 jours.',
    });
  }

  // Assurance
  if (isInsuranceDueSoon(vehicle)) {
    insights.push({
      id: 'insurance-soon',
      type: 'warning',
      title: 'Assurance à renouveler',
      description: "L'assurance expire dans moins de 30 jours.",
    });
  }

  // Révision
  if (isRevisionDueSoon(vehicle)) {
    insights.push({
      id: 'revision-soon',
      type: 'suggestion',
      title: 'Révision à planifier',
      description: 'La prochaine révision approche.',
    });
  } else if (vehicle.date_derniere_revision) {
    insights.push({
      id: 'revision-ok',
      type: 'success',
      title: 'Entretien à jour',
      description: `Dernière révision le ${formatDate(vehicle.date_derniere_revision)}.`,
    });
  }

  // Consommation
  const avgConsumption = calculateAverageConsumption(vehicle);
  if (avgConsumption) {
    const diff = ((avgConsumption - vehicle.conso_100km) / vehicle.conso_100km) * 100;
    if (diff > 15) {
      insights.push({
        id: 'consumption-high',
        type: 'warning',
        title: 'Consommation élevée',
        description: `+${diff.toFixed(0)}% par rapport à la valeur théorique.`,
      });
    } else if (diff < -5) {
      insights.push({
        id: 'consumption-good',
        type: 'success',
        title: 'Bonne consommation',
        description: `${Math.abs(diff).toFixed(0)}% sous la valeur théorique.`,
      });
    }
  }

  // Documents
  const expiringDocs = getExpiringDocuments(vehicle);
  if (expiringDocs.length > 0) {
    insights.push({
      id: 'docs-expiring',
      type: 'warning',
      title: 'Documents à renouveler',
      description: `${expiringDocs.length} document(s) expiré(s) ou expirant bientôt.`,
    });
  }

  // Âge du véhicule
  const age = getVehicleAge(vehicle);
  if (age !== null && age >= 10) {
    insights.push({
      id: 'old-vehicle',
      type: 'suggestion',
      title: 'Véhicule ancien',
      description: `${age} ans - envisager le remplacement.`,
    });
  }

  // Émissions CO2
  const co2 = getCO2Km(vehicle);
  if (co2 < 0.10) {
    insights.push({
      id: 'low-co2',
      type: 'success',
      title: 'Faibles émissions',
      description: 'Véhicule écologique avec émissions réduites.',
    });
  } else if (co2 > 0.20) {
    insights.push({
      id: 'high-co2',
      type: 'suggestion',
      title: 'Émissions élevées',
      description: 'Envisager un véhicule moins polluant.',
    });
  }

  // Coût au kilomètre
  const coutKm = calculCoutKm(vehicle).total;
  if (coutKm < 0.35) {
    insights.push({
      id: 'low-cost',
      type: 'success',
      title: 'Coût kilométrique faible',
      description: "Véhicule économique à l'usage.",
    });
  } else if (coutKm > 0.55) {
    insights.push({
      id: 'high-cost',
      type: 'suggestion',
      title: 'Coût kilométrique élevé',
      description: 'Analyser les postes de dépenses.',
    });
  }

  return insights;
}

export default VehicleIATab;
