/**
 * AZALS Module - Auto-Enrichment - RiskAnalysis Component
 * ========================================================
 * Composant d'affichage de l'analyse de risque entreprise.
 *
 * IMPORTANT: Donnees confidentielles.
 * Requiert capability 'enrichment.risk_analysis'.
 */

import React, { useEffect } from 'react';
import {
  AlertTriangle,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  TrendingDown,
  TrendingUp,
  Minus,
  Loader2,
  Search,
  AlertCircle,
  Building2,
  Lock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useRiskAnalysis } from '../hooks/useRiskAnalysis';
import type { RiskAnalysis as RiskAnalysisType, RiskAnalysisProps, RiskFactor, RiskLevel } from '../types';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getRiskIcon(level: RiskLevel) {
  switch (level) {
    case 'low':
      return <ShieldCheck className="text-green-500" size={24} />;
    case 'medium':
      return <Shield className="text-yellow-500" size={24} />;
    case 'elevated':
      return <ShieldAlert className="text-orange-500" size={24} />;
    case 'high':
      return <ShieldX className="text-red-500" size={24} />;
    default:
      return <Shield className="text-gray-400" size={24} />;
  }
}

function _getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'low':
      return 'green';
    case 'medium':
      return 'yellow';
    case 'elevated':
      return 'orange';
    case 'high':
      return 'red';
    default:
      return 'gray';
  }
}

function getFactorIcon(severity: string, impact: number) {
  if (severity === 'positive' || impact > 0) {
    return <TrendingUp className="text-green-500" size={14} />;
  }
  if (severity === 'critical' || impact < -40) {
    return <AlertTriangle className="text-red-500" size={14} />;
  }
  if (impact < -20) {
    return <TrendingDown className="text-orange-500" size={14} />;
  }
  if (impact < 0) {
    return <Minus className="text-yellow-500" size={14} />;
  }
  return <Minus className="text-gray-400" size={14} />;
}

// ============================================================================
// SCORE GAUGE COMPONENT
// ============================================================================

interface ScoreGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

function ScoreGauge({ score, size = 'md' }: ScoreGaugeProps) {
  const radius = size === 'lg' ? 50 : size === 'md' ? 40 : 30;
  const stroke = size === 'lg' ? 8 : size === 'md' ? 6 : 4;
  const circumference = 2 * Math.PI * radius;
  const progress = ((100 - score) / 100) * circumference;

  // Determiner la couleur selon le score
  let color = 'text-red-500';
  if (score >= 80) color = 'text-green-500';
  else if (score >= 60) color = 'text-yellow-500';
  else if (score >= 40) color = 'text-orange-500';

  const textSize = size === 'lg' ? 'text-2xl' : size === 'md' ? 'text-xl' : 'text-lg';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        width={(radius + stroke) * 2}
        height={(radius + stroke) * 2}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={progress}
          strokeLinecap="round"
          className={color}
        />
      </svg>
      <span className={`absolute font-bold ${textSize} ${color}`}>
        {score}
      </span>
    </div>
  );
}

// ============================================================================
// RISK FACTOR ITEM
// ============================================================================

interface FactorItemProps {
  factor: RiskFactor;
}

function FactorItem({ factor }: FactorItemProps) {
  const severityColors: Record<string, string> = {
    positive: 'bg-green-50 border-green-200 text-green-700',
    low: 'bg-gray-50 border-gray-200 text-gray-600',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    high: 'bg-orange-50 border-orange-200 text-orange-700',
    critical: 'bg-red-50 border-red-200 text-red-700',
  };

  const colorClass = severityColors[factor.severity] || severityColors.low;

  return (
    <div className={`flex items-center gap-2 px-2 py-1 rounded border text-sm ${colorClass}`}>
      {getFactorIcon(factor.severity, factor.impact)}
      <span className="flex-1">{factor.factor}</span>
      <span className="font-mono text-xs">
        {factor.impact > 0 ? '+' : ''}{factor.impact}
      </span>
    </div>
  );
}

// ============================================================================
// RISK ANALYSIS DISPLAY (Read-only)
// ============================================================================

interface RiskDisplayProps {
  analysis: RiskAnalysisType;
  compact?: boolean;
  showDetails?: boolean;
}

function RiskDisplay({ analysis, compact = false, showDetails = true }: RiskDisplayProps) {
  const [expanded, setExpanded] = React.useState(!compact);

  if (compact) {
    return (
      <div
        className="flex items-center gap-3 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <ScoreGauge score={analysis.score} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {getRiskIcon(analysis.level)}
            <span className="font-medium">{analysis.level_label}</span>
          </div>
          {analysis.cotation_bdf && (
            <span className="text-xs text-gray-500">
              BDF: {analysis.cotation_bdf}
            </span>
          )}
        </div>
        {showDetails && (
          expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Score principal */}
      <div className="flex items-center gap-6 p-4 bg-gray-50 rounded-lg">
        <ScoreGauge score={analysis.score} size="lg" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {getRiskIcon(analysis.level)}
            <span className="text-lg font-semibold">{analysis.level_label}</span>
          </div>
          {analysis.cotation_bdf && (
            <div className="text-sm text-gray-600">
              Cotation Banque de France: <strong>{analysis.cotation_bdf}</strong>
            </div>
          )}
          <p className="text-sm text-gray-600 mt-2">{analysis.recommendation}</p>
        </div>
      </div>

      {/* Alertes */}
      {analysis.alerts.length > 0 && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
            <AlertTriangle size={18} />
            Alertes
          </div>
          <ul className="space-y-1">
            {analysis.alerts.map((alert, idx) => (
              <li key={idx} className="text-sm text-red-600 flex items-center gap-2">
                <AlertCircle size={14} />
                {alert}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Facteurs de risque */}
      {showDetails && analysis.factors.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">Facteurs d'analyse</h4>
          <div className="space-y-1">
            {analysis.factors.map((factor, idx) => (
              <FactorItem key={idx} factor={factor} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function RiskAnalysis({
  siren,
  siret,
  onAnalysis,
  compact = false,
  autoLoad = false,
  showDetails = true,
  className = '',
}: RiskAnalysisProps) {
  const [inputValue, setInputValue] = React.useState(siret || siren || '');
  const {
    analysis,
    enrichedFields,
    isLoading,
    error,
    cached,
    analyze,
    reset: _reset,
  } = useRiskAnalysis({
    onSuccess: onAnalysis,
  });

  // Auto-load si demande et identifiant fourni
  useEffect(() => {
    if (autoLoad && (siret || siren)) {
      analyze(siret || siren!);
    }
  }, [autoLoad, siret, siren]);

  // Mettre a jour inputValue si props changent
  useEffect(() => {
    if (siret) setInputValue(siret);
    else if (siren) setInputValue(siren);
  }, [siret, siren]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      analyze(inputValue.trim());
    }
  };

  return (
    <div className={`azals-risk-analysis ${className}`}>
      {/* Header avec avertissement confidentialite */}
      <div className="flex items-center gap-2 mb-3 text-amber-600 text-xs">
        <Lock size={14} />
        <span>Donnees confidentielles - Acces restreint</span>
      </div>

      {/* Formulaire de recherche */}
      {!autoLoad && (
        <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="SIREN (9 chiffres) ou SIRET (14 chiffres)"
              className="w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={18} />
            ) : (
              <Search size={18} />
            )}
            Analyser
          </button>
        </form>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-8 text-gray-500">
          <Loader2 className="animate-spin mr-2" size={24} />
          Analyse en cours...
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Analysis result */}
      {analysis && !isLoading && (
        <>
          {cached && (
            <div className="text-xs text-gray-500 mb-2">
              Donnees en cache
            </div>
          )}
          <RiskDisplay
            analysis={analysis}
            compact={compact}
            showDetails={showDetails}
          />

          {/* Company info summary */}
          {enrichedFields && !compact && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
              <h4 className="font-medium text-gray-700 mb-2">Entreprise</h4>
              <div className="grid grid-cols-2 gap-2 text-gray-600">
                {enrichedFields.name && (
                  <div>
                    <span className="text-gray-400">Nom:</span> {enrichedFields.name}
                  </div>
                )}
                {enrichedFields.siret && (
                  <div>
                    <span className="text-gray-400">SIRET:</span> {enrichedFields.siret}
                  </div>
                )}
                {enrichedFields.legal_form && (
                  <div>
                    <span className="text-gray-400">Forme:</span> {enrichedFields.legal_form}
                  </div>
                )}
                {enrichedFields.capital && (
                  <div>
                    <span className="text-gray-400">Capital:</span> {enrichedFields.capital.toLocaleString()} EUR
                  </div>
                )}
                {enrichedFields.city && (
                  <div>
                    <span className="text-gray-400">Ville:</span> {enrichedFields.city}
                  </div>
                )}
                {enrichedFields.effectif && (
                  <div>
                    <span className="text-gray-400">Effectif:</span> {enrichedFields.effectif} salaries
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ============================================================================
// EXPORT READ-ONLY DISPLAY FOR USE IN OTHER COMPONENTS
// ============================================================================

export { RiskDisplay, ScoreGauge, FactorItem };

export default RiskAnalysis;
