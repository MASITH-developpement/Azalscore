/**
 * AZALSCORE Module - Invoicing - Risk Tab
 * Onglet Analyse de Risque pour le client du document
 */

import React, { useEffect, useState } from 'react';
import {
  Shield, ShieldAlert, ShieldCheck, ShieldX,
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  Building2, Lock, RefreshCw, AlertCircle,
  ChevronDown, ChevronUp, Info, CreditCard
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import {
  useRiskAnalysis,
  useInternalScore,
  ScoreGauge
} from '@/modules/enrichment';
import type { RiskLevel } from '@/modules/enrichment';
import { formatCurrency } from '@/utils/formatters';
import type { Document } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * Banniere d'alerte risque
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
            {level === 'high' ? 'RISQUE ELEVE - VIGILANCE REQUISE' : level === 'elevated' ? 'Risque eleve' : 'Attention requise'}
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
 * Score de paiement interne
 */
interface InternalScoreDisplayProps {
  customerId: string;
}

const InternalScoreDisplay: React.FC<InternalScoreDisplayProps> = ({ customerId }) => {
  const { score, isLoading, error, analyze } = useInternalScore();

  useEffect(() => {
    if (customerId) {
      analyze(customerId);
    }
  }, [customerId, analyze]);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <RefreshCw size={16} className="animate-spin" />
        Calcul du score...
      </div>
    );
  }

  if (error || !score) {
    return (
      <div className="text-gray-400 text-sm">
        Score interne non disponible
      </div>
    );
  }

  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-600';
    if (s >= 60) return 'text-yellow-600';
    if (s >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className={`text-3xl font-bold ${getScoreColor(score.score)}`}>
          {score.score}
          <span className="text-lg text-gray-400">/100</span>
        </div>
        <div className="flex-1">
          <div className={`font-medium ${getScoreColor(score.score)}`}>
            {score.level_label}
          </div>
          <div className="text-sm text-gray-500">
            Score base sur l&apos;historique client
          </div>
        </div>
      </div>

      {score.metrics && (
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-200">
          <div className="text-sm">
            <span className="text-gray-500">Factures totales:</span>
            <span className="ml-2 font-medium">{score.metrics.total_invoices}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Factures payees:</span>
            <span className="ml-2 font-medium text-green-600">{score.metrics.paid_invoices}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Anciennete:</span>
            <span className="ml-2 font-medium">{Math.floor((score.metrics.account_age_days || 0) / 30)} mois</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Retards:</span>
            <span className={`ml-2 font-medium ${(score.metrics.overdue_invoices || 0) > 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {score.metrics.overdue_invoices || 0}
            </span>
          </div>
          {score.metrics.outstanding !== undefined && score.metrics.outstanding > 0 && (
            <div className="text-sm col-span-2">
              <span className="text-gray-500">Encours:</span>
              <span className="ml-2 font-medium text-orange-600">
                {formatCurrency(score.metrics.outstanding)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * InvoicingRiskTab - Onglet Analyse de Risque
 */
export const InvoicingRiskTab: React.FC<TabContentProps<Document>> = ({ data: document }) => {
  const [showDetails, setShowDetails] = useState(true);

  // Recuperer SIREN ou SIRET du client
  const identifier = document.customer_siret || document.customer_siren || '';

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
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-amber-600 text-sm">
            <Lock size={16} />
            <span>Donnees confidentielles - Acces restreint</span>
          </div>
          {identifier && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
              Actualiser
            </Button>
          )}
        </div>

        <Grid cols={2} gap="lg">
          {/* Score interne */}
          <Card title="Score Client Interne" icon={<CreditCard size={18} />}>
            <InternalScoreDisplay customerId={document.customer_id} />
          </Card>

          {/* Score externe */}
          <Card title="Score Entreprise" icon={<Shield size={18} />}>
            {!identifier || identifier.length < 9 ? (
              <div className="text-center py-4">
                <Building2 className="mx-auto mb-2 text-gray-400" size={32} />
                <p className="text-gray-500 text-sm">
                  SIREN/SIRET non renseigne pour ce client
                </p>
              </div>
            ) : isLoading ? (
              <div className="flex items-center justify-center gap-2 py-4 text-gray-500">
                <RefreshCw size={20} className="animate-spin" />
                Analyse en cours...
              </div>
            ) : error ? (
              <div className="text-red-600 text-sm py-2">
                <AlertCircle size={16} className="inline mr-1" />
                {error}
              </div>
            ) : analysis ? (
              <div className="flex items-center gap-4">
                <ScoreGauge score={analysis.score} size="md" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {analysis.level === 'low' && <ShieldCheck className="text-green-500" size={18} />}
                    {analysis.level === 'medium' && <Shield className="text-yellow-500" size={18} />}
                    {analysis.level === 'elevated' && <ShieldAlert className="text-orange-500" size={18} />}
                    {analysis.level === 'high' && <ShieldX className="text-red-500" size={18} />}
                    <span className="font-semibold">{analysis.level_label}</span>
                  </div>
                  {analysis.cotation_bdf && (
                    <div className="text-sm text-gray-600">
                      Cotation BdF: <strong>{analysis.cotation_bdf}</strong>
                    </div>
                  )}
                  {cached && (
                    <div className="text-xs text-gray-400 mt-1">
                      Donnees en cache
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </Card>
        </Grid>

        {/* Alerte si risque eleve */}
        {analysis && (
          <div className="mt-4">
            <RiskAlertBanner
              level={analysis.level}
              alerts={analysis.alerts}
              recommendation={analysis.recommendation}
            />
          </div>
        )}

        {/* Informations entreprise enrichies */}
        {enrichedFields && (
          <Card title="Informations Entreprise" icon={<Building2 size={18} />} className="mt-4">
            <Grid cols={3} gap="md">
              {enrichedFields.name && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Raison sociale</span>
                  <span className="azals-info-block__value font-medium">{enrichedFields.name}</span>
                </div>
              )}
              {enrichedFields.siret && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">SIRET</span>
                  <span className="azals-info-block__value font-mono">{enrichedFields.siret}</span>
                </div>
              )}
              {enrichedFields.siren && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">SIREN</span>
                  <span className="azals-info-block__value font-mono">{enrichedFields.siren}</span>
                </div>
              )}
              {enrichedFields.legal_form && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Forme juridique</span>
                  <span className="azals-info-block__value">{enrichedFields.legal_form}</span>
                </div>
              )}
              {enrichedFields.capital && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Capital</span>
                  <span className="azals-info-block__value">{enrichedFields.capital.toLocaleString()} EUR</span>
                </div>
              )}
              {enrichedFields.effectif && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Effectif</span>
                  <span className="azals-info-block__value">{enrichedFields.effectif} employes</span>
                </div>
              )}
              {enrichedFields.industry_code && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Code NAF</span>
                  <span className="azals-info-block__value font-mono">{enrichedFields.industry_code}</span>
                </div>
              )}
              {enrichedFields.industry_label && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Secteur</span>
                  <span className="azals-info-block__value">{enrichedFields.industry_label}</span>
                </div>
              )}
              {enrichedFields.city && (
                <div className="azals-info-block">
                  <span className="azals-info-block__label">Ville</span>
                  <span className="azals-info-block__value">{enrichedFields.city}</span>
                </div>
              )}
            </Grid>
          </Card>
        )}

        {/* Facteurs de risque */}
        {analysis && analysis.factors.length > 0 && (
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
        )}

        {/* Note analyse simplifiee */}
        {analysis?._limited_data && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2 text-blue-700 text-sm">
              <Info size={16} className="mt-0.5" />
              <div>
                <p className="font-medium">Analyse simplifiee</p>
                <p>
                  Cette analyse utilise les donnees INSEE publiques.
                  Pour une analyse complete, configurez une cle API Pappers.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </CapabilityGuard>
  );
};

export default InvoicingRiskTab;
