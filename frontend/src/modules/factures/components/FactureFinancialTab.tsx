/**
 * AZALSCORE Module - FACTURES - Financial Tab
 * Onglet récapitulatif financier et paiements
 */

import React from 'react';
import {
  Euro, Percent, Calculator, TrendingUp,
  CreditCard, Receipt, CheckCircle2, Clock, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Facture, Payment } from '../types';
import { PAYMENT_METHODS, isOverdue } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * FactureFinancialTab - Récapitulatif financier et paiements
 */
export const FactureFinancialTab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const isCreditNote = facture.type === 'CREDIT_NOTE';
  const isFactureOverdue = isOverdue(facture);
  const payments = facture.payments || [];

  // Grouper les lignes par taux de TVA
  const taxBreakdown = React.useMemo(() => {
    const breakdown: Record<number, { base: number; amount: number }> = {};

    (facture.lines || []).forEach((line) => {
      const rate = line.tax_rate;
      if (!breakdown[rate]) {
        breakdown[rate] = { base: 0, amount: 0 };
      }
      breakdown[rate].base += line.subtotal;
      breakdown[rate].amount += line.tax_amount;
    });

    return Object.entries(breakdown)
      .map(([rate, values]) => ({
        rate: Number(rate),
        base: values.base,
        amount: values.amount,
      }))
      .sort((a, b) => b.rate - a.rate);
  }, [facture.lines]);

  // Calculer le pourcentage payé
  const paymentPercent = facture.total > 0
    ? Math.round((facture.paid_amount / facture.total) * 100)
    : 0;

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Récapitulatif principal */}
        <Card title="Récapitulatif" icon={<Calculator size={18} />}>
          <table className="azals-table azals-table--simple azals-table--financial">
            <tbody>
              <tr>
                <td>Sous-total HT</td>
                <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                  {isCreditNote && '-'}{formatCurrency(facture.subtotal, facture.currency)}
                </td>
              </tr>

              {facture.discount_amount > 0 && (
                <tr className="text-warning">
                  <td>
                    <Percent size={14} className="mr-2" />
                    Remise ({facture.discount_percent}%)
                  </td>
                  <td className="text-right">
                    -{formatCurrency(facture.discount_amount, facture.currency)}
                  </td>
                </tr>
              )}

              <tr>
                <td>Total HT</td>
                <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                  {isCreditNote && '-'}{formatCurrency(
                    facture.subtotal - facture.discount_amount,
                    facture.currency
                  )}
                </td>
              </tr>

              <tr>
                <td>TVA</td>
                <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                  {isCreditNote && '-'}{formatCurrency(facture.tax_amount, facture.currency)}
                </td>
              </tr>

              <tr className="azals-table__total">
                <td><strong>Total TTC</strong></td>
                <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                  <strong className="text-lg">
                    {isCreditNote && '-'}{formatCurrency(facture.total, facture.currency)}
                  </strong>
                </td>
              </tr>
            </tbody>
          </table>
        </Card>

        {/* Ventilation TVA */}
        <Card title="Ventilation TVA" icon={<Receipt size={18} />}>
          {taxBreakdown.length > 0 ? (
            <table className="azals-table azals-table--simple">
              <thead>
                <tr>
                  <th>Taux</th>
                  <th className="text-right">Base HT</th>
                  <th className="text-right">Montant TVA</th>
                </tr>
              </thead>
              <tbody>
                {taxBreakdown.map(({ rate, base, amount }) => (
                  <tr key={rate}>
                    <td>{rate}%</td>
                    <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                      {isCreditNote && '-'}{formatCurrency(base, facture.currency)}
                    </td>
                    <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                      {isCreditNote && '-'}{formatCurrency(amount, facture.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="azals-table__total">
                  <td><strong>Total</strong></td>
                  <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                    <strong>{isCreditNote && '-'}{formatCurrency(facture.subtotal, facture.currency)}</strong>
                  </td>
                  <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                    <strong>{isCreditNote && '-'}{formatCurrency(facture.tax_amount, facture.currency)}</strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          ) : (
            <p className="text-muted text-center py-4">Aucune ligne</p>
          )}
        </Card>
      </Grid>

      {/* État des paiements (factures uniquement) */}
      {!isCreditNote && (
        <Card title="État des paiements" icon={<CreditCard size={18} />} className="mt-4">
          {/* Barre de progression */}
          <div className="azals-payment-progress mb-4">
            <div className="azals-payment-progress__header">
              <span>
                {facture.status === 'PAID' ? (
                  <><CheckCircle2 size={16} className="text-success mr-1" /> Entièrement payée</>
                ) : isFactureOverdue ? (
                  <><AlertTriangle size={16} className="text-danger mr-1" /> En retard de paiement</>
                ) : facture.paid_amount > 0 ? (
                  <><Clock size={16} className="text-warning mr-1" /> Partiellement payée</>
                ) : (
                  <><Clock size={16} className="text-muted mr-1" /> En attente de paiement</>
                )}
              </span>
              <span>{paymentPercent}%</span>
            </div>
            <div className="azals-payment-progress__bar">
              <div
                className={`azals-payment-progress__fill ${
                  facture.status === 'PAID' ? 'azals-payment-progress__fill--success' :
                  isFactureOverdue ? 'azals-payment-progress__fill--danger' :
                  'azals-payment-progress__fill--warning'
                }`}
                style={{ width: `${paymentPercent}%` }}
              />
            </div>
            <div className="azals-payment-progress__amounts">
              <span>Payé: {formatCurrency(facture.paid_amount, facture.currency)}</span>
              <span>Reste: {formatCurrency(facture.remaining_amount, facture.currency)}</span>
            </div>
          </div>

          {/* Liste des paiements */}
          {payments.length > 0 ? (
            <table className="azals-table azals-table--simple">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Référence</th>
                  <th>Mode</th>
                  <th className="text-right">Montant</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <PaymentRow key={payment.id} payment={payment} currency={facture.currency} />
                ))}
              </tbody>
              <tfoot>
                <tr className="azals-table__total">
                  <td colSpan={3}><strong>Total encaissé</strong></td>
                  <td className="text-right text-success">
                    <strong>{formatCurrency(facture.paid_amount, facture.currency)}</strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CreditCard size={32} className="text-muted" />
              <p className="text-muted">Aucun paiement enregistré</p>
            </div>
          )}
        </Card>
      )}

      {/* Analyse comptable (ERP only) */}
      <Card
        title="Analyse comptable"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Compte client</span>
            <span className="azals-kpi-card__value">411000</span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Compte produits</span>
            <span className="azals-kpi-card__value">707000</span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Compte TVA</span>
            <span className="azals-kpi-card__value">445710</span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Journal</span>
            <span className="azals-kpi-card__value">VT</span>
          </div>
        </Grid>

        <div className="azals-info-banner mt-4">
          <TrendingUp size={16} />
          <span>
            Écritures comptables générées automatiquement lors de la validation.
          </span>
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant ligne de paiement
 */
const PaymentRow: React.FC<{ payment: Payment; currency: string }> = ({ payment, currency }) => {
  return (
    <tr>
      <td>{formatDate(payment.date)}</td>
      <td>{payment.reference || '-'}</td>
      <td>{PAYMENT_METHODS[payment.method].label}</td>
      <td className="text-right text-success">
        <strong>{formatCurrency(payment.amount, currency)}</strong>
      </td>
    </tr>
  );
};

export default FactureFinancialTab;
