/**
 * AZALSCORE Module - AFFAIRES - Financial Tab
 * Onglet financier de l'affaire (budget, facturation, rentabilité)
 */

import React from 'react';
import {
  Euro, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2,
  PieChart, BarChart3, FileText, CreditCard
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatPercent } from '@/utils/formatters';
import { getBudgetStatus } from '../types';
import type { Affaire } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AffaireFinancialTab - Budget et facturation de l'affaire
 */
export const AffaireFinancialTab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const budgetTotal = affaire.budget_total || 0;
  const budgetSpent = affaire.budget_spent || 0;
  const budgetRemaining = affaire.budget_remaining ?? (budgetTotal - budgetSpent);

  const totalInvoiced = affaire.total_invoiced || 0;
  const totalPaid = affaire.total_paid || 0;
  const totalRemaining = affaire.total_remaining ?? (totalInvoiced - totalPaid);

  const budgetStatus = getBudgetStatus(affaire);
  const budgetPct = budgetTotal > 0 ? (budgetSpent / budgetTotal) * 100 : 0;
  const invoicePct = budgetTotal > 0 ? (totalInvoiced / budgetTotal) * 100 : 0;
  const paidPct = totalInvoiced > 0 ? (totalPaid / totalInvoiced) * 100 : 0;

  // Calcul marge estimée
  const margeEstimee = budgetTotal > 0 && budgetSpent > 0
    ? ((budgetTotal - budgetSpent) / budgetTotal) * 100
    : null;

  return (
    <div className="azals-std-tab-content">
      {/* Alerte budget */}
      {budgetStatus === 'danger' && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Budget dépassé</strong>
            <p>Les dépenses ont dépassé le budget initial de {formatCurrency(Math.abs(budgetRemaining))}.</p>
          </div>
        </div>
      )}
      {budgetStatus === 'warning' && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Budget presque épuisé</strong>
            <p>Plus de 90% du budget a été consommé. Il reste {formatCurrency(budgetRemaining)}.</p>
          </div>
        </div>
      )}

      {/* Résumé financier */}
      <Card title="Résumé financier" icon={<Euro size={18} />} className="mb-4">
        <Grid cols={3} gap="lg">
          {/* Budget */}
          <div className="azals-financial-card">
            <div className="azals-financial-card__header">
              <PieChart size={20} className="text-primary" />
              <span>Budget</span>
            </div>
            <div className="azals-financial-card__amount">{formatCurrency(budgetTotal)}</div>
            <div className="azals-progress-bar">
              <div
                className={`azals-progress-bar__fill azals-progress-bar__fill--${budgetStatus}`}
                style={{ width: `${Math.min(budgetPct, 100)}%` }}
              />
            </div>
            <div className="azals-financial-card__details">
              <span className="text-muted">Consommé: {formatCurrency(budgetSpent)}</span>
              <span className={`${budgetRemaining < 0 ? 'text-danger' : 'text-success'}`}>
                Reste: {formatCurrency(budgetRemaining)}
              </span>
            </div>
          </div>

          {/* Facturation */}
          <div className="azals-financial-card">
            <div className="azals-financial-card__header">
              <FileText size={20} className="text-purple" />
              <span>Facturé</span>
            </div>
            <div className="azals-financial-card__amount">{formatCurrency(totalInvoiced)}</div>
            <div className="azals-progress-bar">
              <div
                className="azals-progress-bar__fill azals-progress-bar__fill--ok"
                style={{ width: `${Math.min(invoicePct, 100)}%` }}
              />
            </div>
            <div className="azals-financial-card__details">
              <span className="text-muted">{formatPercent(invoicePct)} du budget</span>
              <span>{formatCurrency(budgetTotal - totalInvoiced)} à facturer</span>
            </div>
          </div>

          {/* Encaissé */}
          <div className="azals-financial-card">
            <div className="azals-financial-card__header">
              <CreditCard size={20} className="text-success" />
              <span>Encaissé</span>
            </div>
            <div className="azals-financial-card__amount text-success">{formatCurrency(totalPaid)}</div>
            <div className="azals-progress-bar">
              <div
                className="azals-progress-bar__fill azals-progress-bar__fill--ok"
                style={{ width: `${Math.min(paidPct, 100)}%` }}
              />
            </div>
            <div className="azals-financial-card__details">
              <span className="text-muted">{formatPercent(paidPct)} encaissé</span>
              <span className="text-warning">Reste: {formatCurrency(totalRemaining)}</span>
            </div>
          </div>
        </Grid>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Détail budget */}
        <Card title="Détail budget" icon={<BarChart3 size={18} />}>
          <table className="azals-table azals-table--simple">
            <tbody>
              <tr>
                <td>Budget total</td>
                <td className="text-right font-medium">{formatCurrency(budgetTotal)}</td>
              </tr>
              <tr>
                <td>Dépenses engagées</td>
                <td className="text-right text-danger">- {formatCurrency(budgetSpent)}</td>
              </tr>
              <tr className="azals-table__total">
                <td className="font-medium">Reste disponible</td>
                <td className={`text-right font-medium ${budgetRemaining < 0 ? 'text-danger' : 'text-success'}`}>
                  {formatCurrency(budgetRemaining)}
                </td>
              </tr>
            </tbody>
          </table>

          {/* Actions */}
          <div className="azals-card-actions mt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('azals:navigate', {
                  detail: { view: 'factures', params: { affaire_id: affaire.id } }
                }));
              }}
            >
              Voir les factures
            </Button>
          </div>
        </Card>

        {/* Facturation */}
        <Card title="État de facturation" icon={<FileText size={18} />}>
          <table className="azals-table azals-table--simple">
            <tbody>
              <tr>
                <td>Montant facturé</td>
                <td className="text-right font-medium">{formatCurrency(totalInvoiced)}</td>
              </tr>
              <tr>
                <td>Montant encaissé</td>
                <td className="text-right text-success">{formatCurrency(totalPaid)}</td>
              </tr>
              <tr className="azals-table__total">
                <td className="font-medium">Reste à encaisser</td>
                <td className={`text-right font-medium ${totalRemaining > 0 ? 'text-warning' : 'text-success'}`}>
                  {formatCurrency(totalRemaining)}
                </td>
              </tr>
            </tbody>
          </table>

          {/* Actions */}
          {affaire.status === 'TERMINE' && totalInvoiced < budgetTotal && (
            <div className="azals-card-actions mt-4">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<FileText size={14} />}
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'factures', params: { action: 'create', affaire_id: affaire.id } }
                  }));
                }}
              >
                Créer une facture
              </Button>
            </div>
          )}
        </Card>
      </Grid>

      {/* Analyse rentabilité (ERP only) */}
      <Card title="Analyse de rentabilité" icon={<TrendingUp size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={4} gap="md">
          <div className="azals-kpi-mini">
            <span className="azals-kpi-mini__label">Marge brute estimée</span>
            <span className={`azals-kpi-mini__value ${margeEstimee !== null && margeEstimee < 0 ? 'text-danger' : margeEstimee !== null && margeEstimee > 20 ? 'text-success' : ''}`}>
              {margeEstimee !== null ? formatPercent(margeEstimee) : '-'}
            </span>
          </div>
          <div className="azals-kpi-mini">
            <span className="azals-kpi-mini__label">Taux facturation</span>
            <span className="azals-kpi-mini__value">{formatPercent(invoicePct)}</span>
          </div>
          <div className="azals-kpi-mini">
            <span className="azals-kpi-mini__label">Taux encaissement</span>
            <span className="azals-kpi-mini__value">{formatPercent(paidPct)}</span>
          </div>
          <div className="azals-kpi-mini">
            <span className="azals-kpi-mini__label">Consommation budget</span>
            <span className={`azals-kpi-mini__value ${budgetPct > 100 ? 'text-danger' : budgetPct > 90 ? 'text-warning' : ''}`}>
              {formatPercent(budgetPct)}
            </span>
          </div>
        </Grid>

        {/* Indicateurs */}
        <div className="azals-indicators mt-4">
          {budgetStatus === 'ok' && (
            <div className="azals-indicator azals-indicator--success">
              <CheckCircle2 size={16} />
              <span>Budget maîtrisé</span>
            </div>
          )}
          {paidPct >= 100 && (
            <div className="azals-indicator azals-indicator--success">
              <CheckCircle2 size={16} />
              <span>Facturation entièrement encaissée</span>
            </div>
          )}
          {margeEstimee !== null && margeEstimee < 10 && (
            <div className="azals-indicator azals-indicator--warning">
              <TrendingDown size={16} />
              <span>Marge faible</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default AffaireFinancialTab;
