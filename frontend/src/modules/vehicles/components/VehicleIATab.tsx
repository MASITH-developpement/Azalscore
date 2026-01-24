/**
 * AZALSCORE Module - Vehicles - Vehicle IA Tab
 * Onglet Assistant IA pour le vehicule
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Calendar, Wrench, Fuel, Shield, Leaf, Euro
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Vehicule } from '../types';
import {
  formatDate, formatCurrency, formatKilometers,
  calculCoutKm, getCO2Km, calculateAverageConsumption,
  getTotalMaintenanceCost, isInspectionDueSoon, isInspectionExpired,
  isInsuranceDueSoon, isRevisionDueSoon, getExpiringDocuments,
  getVehicleAge, FUEL_TYPE_CONFIG
} from '../types';

/**
 * VehicleIATab - Assistant IA pour le vehicule
 */
export const VehicleIATab: React.FC<TabContentProps<Vehicule>> = ({ data: vehicle }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(vehicle);

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
            J'ai analyse ce vehicule et identifie{' '}
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

      {/* Score sante vehicule */}
      <Card title="Sante du vehicule" icon={<TrendingUp size={18} />} className="mb-4">
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
            {isInspectionExpired(vehicle) && (
              <SuggestedAction
                title="Controle technique urgent"
                description="Le controle technique est expire."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {isInspectionDueSoon(vehicle) && !isInspectionExpired(vehicle) && (
              <SuggestedAction
                title="Planifier controle technique"
                description="Le controle technique expire bientot."
                confidence={95}
                icon={<Calendar size={16} />}
              />
            )}
            {isInsuranceDueSoon(vehicle) && (
              <SuggestedAction
                title="Renouveler assurance"
                description="L'assurance expire bientot."
                confidence={90}
                icon={<Shield size={16} />}
              />
            )}
            {isRevisionDueSoon(vehicle) && (
              <SuggestedAction
                title="Planifier revision"
                description="La prochaine revision approche."
                confidence={85}
                icon={<Wrench size={16} />}
              />
            )}
            {getExpiringDocuments(vehicle).length > 0 && (
              <SuggestedAction
                title="Renouveler documents"
                description={`${getExpiringDocuments(vehicle).length} document(s) a renouveler.`}
                confidence={80}
                icon={<Shield size={16} />}
              />
            )}
            {vehicle.is_active && (
              <SuggestedAction
                title="Optimiser les couts"
                description="Analyser les donnees pour reduire le cout/km."
                confidence={70}
                icon={<Euro size={16} />}
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
            <h4>Type carburant</h4>
            <p className={`text-lg font-medium text-${FUEL_TYPE_CONFIG[vehicle.type_carburant].color}`}>
              {FUEL_TYPE_CONFIG[vehicle.type_carburant].label}
            </p>
            <p className="text-sm text-muted">
              {vehicle.type_carburant === 'electrique'
                ? 'Faibles emissions'
                : vehicle.type_carburant === 'hybride'
                ? 'Emissions reduites'
                : 'Emissions standard'
              }
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Cout au kilometre</h4>
            <p className="text-lg font-medium text-primary">
              {calculCoutKm(vehicle).total.toFixed(3)} Euro/km
            </p>
            <p className="text-sm text-muted">
              {calculCoutKm(vehicle).total < 0.40 ? 'Economique' : calculCoutKm(vehicle).total < 0.55 ? 'Moyen' : 'Eleve'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Emissions CO2</h4>
            <p className="text-lg font-medium text-green-600">
              {getCO2Km(vehicle).toFixed(3)} kg/km
            </p>
            <p className="text-sm text-muted">
              {getCO2Km(vehicle) < 0.10 ? 'Tres faible' : getCO2Km(vehicle) < 0.18 ? 'Faible' : 'Moyen'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Cout maintenance total</h4>
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
 * Generer les insights bases sur le vehicule
 */
function generateInsights(vehicle: Vehicule): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (vehicle.is_active) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Vehicule actif',
      description: 'Le vehicule est operationnel.',
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'warning',
      title: 'Vehicule inactif',
      description: 'Le vehicule n\'est pas en service.',
    });
  }

  // Controle technique
  if (isInspectionExpired(vehicle)) {
    insights.push({
      id: 'inspection-expired',
      type: 'warning',
      title: 'Controle technique expire',
      description: 'Le controle technique doit etre effectue immediatement.',
    });
  } else if (isInspectionDueSoon(vehicle)) {
    insights.push({
      id: 'inspection-soon',
      type: 'warning',
      title: 'Controle technique proche',
      description: 'Le controle technique expire dans moins de 30 jours.',
    });
  }

  // Assurance
  if (isInsuranceDueSoon(vehicle)) {
    insights.push({
      id: 'insurance-soon',
      type: 'warning',
      title: 'Assurance a renouveler',
      description: 'L\'assurance expire dans moins de 30 jours.',
    });
  }

  // Revision
  if (isRevisionDueSoon(vehicle)) {
    insights.push({
      id: 'revision-soon',
      type: 'suggestion',
      title: 'Revision a planifier',
      description: 'La prochaine revision approche.',
    });
  } else if (vehicle.date_derniere_revision) {
    insights.push({
      id: 'revision-ok',
      type: 'success',
      title: 'Entretien a jour',
      description: `Derniere revision le ${formatDate(vehicle.date_derniere_revision)}.`,
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
        title: 'Consommation elevee',
        description: `+${diff.toFixed(0)}% par rapport a la valeur theorique.`,
      });
    } else if (diff < -5) {
      insights.push({
        id: 'consumption-good',
        type: 'success',
        title: 'Bonne consommation',
        description: `${Math.abs(diff).toFixed(0)}% sous la valeur theorique.`,
      });
    }
  }

  // Documents
  const expiringDocs = getExpiringDocuments(vehicle);
  if (expiringDocs.length > 0) {
    insights.push({
      id: 'docs-expiring',
      type: 'warning',
      title: 'Documents a renouveler',
      description: `${expiringDocs.length} document(s) expire(s) ou expirant bientot.`,
    });
  }

  // Age du vehicule
  const age = getVehicleAge(vehicle);
  if (age !== null && age >= 10) {
    insights.push({
      id: 'old-vehicle',
      type: 'suggestion',
      title: 'Vehicule ancien',
      description: `${age} ans - envisager le remplacement.`,
    });
  }

  // Emissions CO2
  const co2 = getCO2Km(vehicle);
  if (co2 < 0.10) {
    insights.push({
      id: 'low-co2',
      type: 'success',
      title: 'Faibles emissions',
      description: 'Vehicule ecologique avec emissions reduites.',
    });
  } else if (co2 > 0.20) {
    insights.push({
      id: 'high-co2',
      type: 'suggestion',
      title: 'Emissions elevees',
      description: 'Envisager un vehicule moins polluant.',
    });
  }

  // Cout au kilometre
  const coutKm = calculCoutKm(vehicle).total;
  if (coutKm < 0.35) {
    insights.push({
      id: 'low-cost',
      type: 'success',
      title: 'Cout kilometrique faible',
      description: 'Vehicule economique a l\'usage.',
    });
  } else if (coutKm > 0.55) {
    insights.push({
      id: 'high-cost',
      type: 'suggestion',
      title: 'Cout kilometrique eleve',
      description: 'Analyser les postes de depenses.',
    });
  }

  return insights;
}

export default VehicleIATab;
