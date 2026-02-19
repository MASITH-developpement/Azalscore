/**
 * AZALSCORE Module - Partners - Risk Tab
 * Onglet Analyse de Risque pour le partenaire
 *
 * IMPORTANT: Donnees confidentielles - Acces restreint par capability
 */

import React, { useEffect, useState } from 'react';
import {
  Shield, ShieldAlert, ShieldCheck, ShieldX,
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  Building2, Lock, RefreshCw, AlertCircle,
  ChevronDown, ChevronUp, Info
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { useRiskAnalysis, ScoreGauge } from '@/modules/enrichment';
import type { RiskLevel } from '@/modules/enrichment';
import type { Partner } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * Composant d'alerte pour risque eleve
 */
interface RiskAlertBannerProps {
  level: RiskLevel;
  alerts: string[];
  recommendation: string;
}

const RiskAlertBanner: React.FC<RiskAlertBannerProps> = ({ level, alerts, recommendation }) => {
  if (level === 'low') return null;

  const config: Record<string, { bg: string; border: string; text: string; icon: React.ReactNode }> = {
    medium: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-300',
      text: 'text-yellow-800',
      icon: <Shield className="text-yellow-500" size={24} />
    },
    elevated: {
      bg: 'bg-orange-50',
      border: 'border-orange-300',
      text: 'text-orange-800',
      icon: <ShieldAlert className="text-orange-500" size={24} />
    },
    high: {
      bg: 'bg-red-50',
      border: 'border-red-400',
      text: 'text-red-800',
      icon: <ShieldX className="text-red-500" size={24} />
    }
  };

  const c = config[level] || config.medium;

  return (
    <div className={`${c.bg} ${c.border} border-2 rounded-lg p-4 mb-4`}>
      <div className="flex items-start gap-3">
        {c.icon}
        <div className="flex-1">
          <h3 className={`font-semibold ${c.text}`}>
            {level === 'high' ? 'RISQUE ELEVE' : level === 'elevated' ? 'Risque eleve' : 'Attention requise'}
          </h3>
          {alerts.length > 0 && (
            <ul className={`mt-2 space-y-1 ${c.text}`}>
              {alerts.map((alert, idx) => (
                <li key={idx} className="flex items-center gap-2 text-sm">
                  <AlertCircle size={14} />
                  {alert}
                </li>
              ))}
            </ul>
          )}
          <p className={`mt-2 text-sm ${c.text}`}>
            <strong>Recommandation:</strong> {recommendation}
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * PartnerRiskTab - Onglet Analyse de Risque
 */
export const PartnerRiskTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const [showDetails, setShowDetails] = useState(true);

  // Recuperer SIREN ou SIRET du partenaire
  const identifier = partner.siret || partner.siren || partner.registration_number || '';

  const {
    analysis,
    enrichedFields,
    isLoading,
    error,
    cached,
    analyze,
    reset
  } = useRiskAnalysis();

  // Auto-load si identifiant disponible
  useEffect(() => {
    if (identifier && identifier.length >= 9) {
      analyze(identifier);
    }
  }, [identifier]);

  const handleRefresh = () => {
    if (identifier) {
      reset();
      analyze(identifier);
    }
  };

  // Pas d'identifiant SIREN/SIRET
  if (!identifier || identifier.length < 9) {
    return (
      <div className="azals-std-tab-content">
        <Card className="text-center py-8">
          <Building2 className="mx-auto mb-4 text-gray-400" size={48} />
          <h3 className="text-lg font-medium text-gray-700 mb-2">
            Analyse de risque non disponible
          </h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Pour analyser le risque de ce partenaire, veuillez d'abord renseigner
            son numero SIREN (9 chiffres) ou SIRET (14 chiffres).
          </p>
        </Card>
      </div>
    );
  }

  return (
    <CapabilityGuard
      capability="enrichment.risk_analysis"
      fallback={
        <div className="azals-std-tab-content">
          <Card className="text-center py-8">
            <Lock className="mx-auto mb-4 text-gray-400" size={48} />
            <h3 className="text-lg font-medium text-gray-700 mb-2">
              Acces restreint
            </h3>
            <p className="text-gray-500">
              Vous n'avez pas la permission d'acceder a l'analyse de risque.
              Contactez votre administrateur.
            </p>
          </Card>
        </div>
      }
    >
      <div className="azals-std-tab-content">
        {/* Header avec avertissement confidentialite */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-amber-600 text-sm">
            <Lock size={16} />
            <span>Donnees confidentielles - Acces restreint</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            Actualiser
          </Button>
        </div>

        {/* Loading */}
        {isLoading && (
          <Card className="text-center py-8">
            <RefreshCw className="mx-auto mb-4 text-blue-500 animate-spin" size={48} />
            <p className="text-gray-500">Analyse en cours...</p>
          </Card>
        )}

        {/* Error */}
        {error && !isLoading && (
          <Card className="border-red-200 bg-red-50">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle size={24} />
              <div>
                <p className="font-medium">Erreur d'analyse</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </Card>
        )}

        {/* Results */}
        {analysis && !isLoading && (
          <>
            {/* Alerte si risque */}
            <RiskAlertBanner
              level={analysis.level}
              alerts={analysis.alerts}
              recommendation={analysis.recommendation}
            />

            <Grid cols={2} gap="lg">
              {/* Score principal */}
              <Card title="Score de risque" icon={<Shield size={18} />}>
                <div className="flex items-center gap-6 py-4">
                  <ScoreGauge score={analysis.score} size="lg" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {analysis.level === 'low' && <ShieldCheck className="text-green-500" size={20} />}
                      {analysis.level === 'medium' && <Shield className="text-yellow-500" size={20} />}
                      {analysis.level === 'elevated' && <ShieldAlert className="text-orange-500" size={20} />}
                      {analysis.level === 'high' && <ShieldX className="text-red-500" size={20} />}
                      <span className="text-lg font-semibold">{analysis.level_label}</span>
                    </div>
                    {analysis.cotation_bdf && (
                      <div className="text-sm text-gray-600 mt-1">
                        Cotation Banque de France: <strong>{analysis.cotation_bdf}</strong>
                      </div>
                    )}
                    {cached && (
                      <div className="text-xs text-gray-400 mt-2">
                        Donnees en cache
                      </div>
                    )}
                  </div>
                </div>
              </Card>

              {/* Info entreprise */}
              <Card title="Entreprise" icon={<Building2 size={18} />}>
                <div className="space-y-2 py-2">
                  {enrichedFields?.name && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Nom</span>
                      <span className="font-medium">{enrichedFields.name}</span>
                    </div>
                  )}
                  {enrichedFields?.siret && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">SIRET</span>
                      <span className="font-mono">{enrichedFields.siret}</span>
                    </div>
                  )}
                  {enrichedFields?.legal_form && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Forme juridique</span>
                      <span>{enrichedFields.legal_form}</span>
                    </div>
                  )}
                  {enrichedFields?.capital && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Capital</span>
                      <span>{enrichedFields.capital.toLocaleString()} EUR</span>
                    </div>
                  )}
                  {enrichedFields?.city && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Ville</span>
                      <span>{enrichedFields.city}</span>
                    </div>
                  )}
                </div>
              </Card>
            </Grid>

            {/* Facteurs de risque */}
            <Card
              title="Facteurs d'analyse"
              icon={<TrendingUp size={18} />}
              className="mt-4"
              actions={
                <button
                  className="text-sm text-gray-500 flex items-center gap-1"
                  onClick={() => setShowDetails(!showDetails)}
                >
                  {showDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  {showDetails ? 'Masquer' : 'Afficher'}
                </button>
              }
            >
              {showDetails && (
                <div className="space-y-2 py-2">
                  {analysis.factors.map((factor, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 p-2 rounded-lg border ${
                        factor.severity === 'positive' ? 'bg-green-50 border-green-200' :
                        factor.severity === 'critical' ? 'bg-red-50 border-red-200' :
                        factor.severity === 'high' ? 'bg-orange-50 border-orange-200' :
                        factor.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                        'bg-gray-50 border-gray-200'
                      }`}
                    >
                      {factor.impact > 0 ? (
                        <TrendingUp className="text-green-500" size={16} />
                      ) : factor.impact < -20 ? (
                        <TrendingDown className="text-red-500" size={16} />
                      ) : factor.impact < 0 ? (
                        <AlertTriangle className="text-yellow-500" size={16} />
                      ) : (
                        <Minus className="text-gray-400" size={16} />
                      )}
                      <span className="flex-1 text-sm">{factor.factor}</span>
                      <span className={`font-mono text-sm ${
                        factor.impact > 0 ? 'text-green-600' :
                        factor.impact < 0 ? 'text-red-600' : 'text-gray-500'
                      }`}>
                        {factor.impact > 0 ? '+' : ''}{factor.impact}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Note sur les donnees limitees */}
            {analysis._limited_data && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2 text-blue-700 text-sm">
                  <Info size={16} className="mt-0.5" />
                  <div>
                    <p className="font-medium">Analyse simplifiee</p>
                    <p>
                      Cette analyse utilise les donnees INSEE publiques.
                      Pour une analyse complete (procedures collectives, cotation Banque de France),
                      configurez une cle API Pappers dans les parametres.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </CapabilityGuard>
  );
};

export default PartnerRiskTab;
