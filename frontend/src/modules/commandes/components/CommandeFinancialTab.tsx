/**
 * AZALSCORE Module - COMMANDES - Financial Tab
 * Onglet récapitulatif financier de la commande
 */

import React from 'react';
import {
  Euro, Percent, Calculator, TrendingUp,
  CreditCard, Truck, Receipt
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Commande } from '../types';
import { formatCurrency } from '../types';

/**
 * CommandeFinancialTab - Récapitulatif financier
 */
export const CommandeFinancialTab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  // Calcul de la marge estimée (simulation)
  const estimatedMargin = commande.subtotal * 0.30; // 30% de marge estimée
  const marginPercent = 30;

  // Grouper les lignes par taux de TVA
  const taxBreakdown = React.useMemo(() => {
    const breakdown: Record<number, { base: number; amount: number }> = {};

    (commande.lines || []).forEach((line) => {
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
  }, [commande.lines]);

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Récapitulatif principal */}
        <Card title="Récapitulatif" icon={<Calculator size={18} />}>
          <table className="azals-table azals-table--simple azals-table--financial">
            <tbody>
              <tr>
                <td>Sous-total HT</td>
                <td className="text-right">{formatCurrency(commande.subtotal, commande.currency)}</td>
              </tr>

              {commande.shipping_cost > 0 && (
                <tr>
                  <td>
                    <Truck size={14} className="mr-2" />
                    Frais de port
                  </td>
                  <td className="text-right">{formatCurrency(commande.shipping_cost, commande.currency)}</td>
                </tr>
              )}

              {commande.discount_amount > 0 && (
                <tr className="text-warning">
                  <td>
                    <Percent size={14} className="mr-2" />
                    Remise ({commande.discount_percent}%)
                  </td>
                  <td className="text-right">-{formatCurrency(commande.discount_amount, commande.currency)}</td>
                </tr>
              )}

              <tr>
                <td>Total HT</td>
                <td className="text-right">
                  {formatCurrency(
                    commande.subtotal + commande.shipping_cost - commande.discount_amount,
                    commande.currency
                  )}
                </td>
              </tr>

              <tr>
                <td>TVA</td>
                <td className="text-right">{formatCurrency(commande.tax_amount, commande.currency)}</td>
              </tr>

              <tr className="azals-table__total">
                <td><strong>Total TTC</strong></td>
                <td className="text-right">
                  <strong className="text-lg">{formatCurrency(commande.total, commande.currency)}</strong>
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
                    <td className="text-right">{formatCurrency(base, commande.currency)}</td>
                    <td className="text-right">{formatCurrency(amount, commande.currency)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="azals-table__total">
                  <td><strong>Total</strong></td>
                  <td className="text-right">
                    <strong>{formatCurrency(commande.subtotal, commande.currency)}</strong>
                  </td>
                  <td className="text-right">
                    <strong>{formatCurrency(commande.tax_amount, commande.currency)}</strong>
                  </td>
                </tr>
              </tfoot>
            </table>
          ) : (
            <p className="text-muted text-center py-4">Aucune ligne</p>
          )}
        </Card>
      </Grid>

      {/* Analyse de marge (ERP only) */}
      <Card
        title="Analyse de rentabilité"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Coût de revient estimé</span>
            <span className="azals-kpi-card__value">
              {formatCurrency(commande.subtotal - estimatedMargin, commande.currency)}
            </span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Marge brute estimée</span>
            <span className="azals-kpi-card__value text-success">
              {formatCurrency(estimatedMargin, commande.currency)}
            </span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Taux de marge</span>
            <span className="azals-kpi-card__value text-success">{marginPercent}%</span>
          </div>

          <div className="azals-kpi-card">
            <span className="azals-kpi-card__label">Coefficient</span>
            <span className="azals-kpi-card__value">1.43</span>
          </div>
        </Grid>

        <div className="azals-info-banner mt-4">
          <TrendingUp size={16} />
          <span>
            Ces données sont des estimations basées sur les prix de revient catalogue.
            Consultez le module Affaires pour une analyse détaillée.
          </span>
        </div>
      </Card>

      {/* Conditions de paiement */}
      {commande.terms && (
        <Card title="Conditions de paiement" icon={<CreditCard size={18} />} className="mt-4">
          <p>{commande.terms}</p>
        </Card>
      )}
    </div>
  );
};

export default CommandeFinancialTab;
