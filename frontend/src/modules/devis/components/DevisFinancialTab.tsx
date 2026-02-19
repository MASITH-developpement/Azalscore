/**
 * AZALSCORE Module - DEVIS - Financial Tab
 * Onglet récapitulatif financier du devis
 */

import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Percent, Calculator } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import type { Devis } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * DevisFinancialTab - Récapitulatif financier du devis
 */
export const DevisFinancialTab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  // Calculs détaillés
  const financialDetails = useMemo(() => {
    const lines = devis.lines || [];

    // Grouper par taux de TVA
    const taxBreakdown = lines.reduce((acc, line) => {
      const rate = line.tax_rate;
      if (!acc[rate]) {
        acc[rate] = { base: 0, tax: 0 };
      }
      acc[rate].base += line.subtotal;
      acc[rate].tax += line.tax_amount;
      return acc;
    }, {} as Record<number, { base: number; tax: number }>);

    // Marge estimée (si disponible)
    const totalCost = lines.reduce((sum, l) => {
      // Estimation: coût = 60% du prix de vente (placeholder)
      return sum + (l.subtotal * 0.6);
    }, 0);
    const margin = devis.subtotal - totalCost;
    const marginPercent = devis.subtotal > 0 ? (margin / devis.subtotal) * 100 : 0;

    return {
      taxBreakdown,
      totalCost,
      margin,
      marginPercent,
    };
  }, [devis]);

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Récapitulatif principal */}
        <Card title="Récapitulatif" icon={<Calculator size={18} />}>
          <div className="azals-financial-summary">
            <div className="azals-financial-summary__row">
              <span>Sous-total HT</span>
              <span className="font-medium">{formatCurrency(devis.subtotal, devis.currency)}</span>
            </div>

            {devis.discount_amount > 0 && (
              <div className="azals-financial-summary__row azals-financial-summary__row--discount">
                <span>
                  Remise globale
                  {devis.discount_percent > 0 && ` (${devis.discount_percent}%)`}
                </span>
                <span className="text-success">
                  -{formatCurrency(devis.discount_amount, devis.currency)}
                </span>
              </div>
            )}

            <div className="azals-financial-summary__row">
              <span>Base HT après remise</span>
              <span>{formatCurrency(devis.subtotal - devis.discount_amount, devis.currency)}</span>
            </div>

            <div className="azals-financial-summary__row">
              <span>TVA</span>
              <span>{formatCurrency(devis.tax_amount, devis.currency)}</span>
            </div>

            <div className="azals-financial-summary__row azals-financial-summary__row--total">
              <span>Total TTC</span>
              <span>{formatCurrency(devis.total, devis.currency)}</span>
            </div>
          </div>
        </Card>

        {/* Détail TVA */}
        <Card title="Détail TVA" icon={<Percent size={18} />}>
          <div className="azals-financial-summary">
            {Object.entries(financialDetails.taxBreakdown)
              .sort(([a], [b]) => Number(b) - Number(a))
              .map(([rate, values]) => (
                <div key={rate} className="azals-financial-summary__row">
                  <span>TVA {rate}%</span>
                  <span>
                    <span className="text-muted mr-2">
                      (base: {formatCurrency(values.base, devis.currency)})
                    </span>
                    {formatCurrency(values.tax, devis.currency)}
                  </span>
                </div>
              ))}
            <div className="azals-financial-summary__row azals-financial-summary__row--subtotal">
              <span>Total TVA</span>
              <span>{formatCurrency(devis.tax_amount, devis.currency)}</span>
            </div>
          </div>
        </Card>

        {/* Marge estimée (ERP only) */}
        <Card
          title="Marge estimée"
          icon={<TrendingUp size={18} />}
          className="azals-std-field--secondary"
        >
          <div className="azals-financial-summary">
            <div className="azals-financial-summary__row">
              <span>Chiffre d'affaires HT</span>
              <span>{formatCurrency(devis.subtotal, devis.currency)}</span>
            </div>
            <div className="azals-financial-summary__row">
              <span>Coût estimé</span>
              <span className="text-muted">
                {formatCurrency(financialDetails.totalCost, devis.currency)}
              </span>
            </div>
            <div className="azals-financial-summary__row azals-financial-summary__row--total">
              <span>
                Marge brute
                <span className={`ml-2 ${financialDetails.marginPercent >= 30 ? 'text-success' : financialDetails.marginPercent >= 15 ? 'text-warning' : 'text-danger'}`}>
                  ({financialDetails.marginPercent.toFixed(1)}%)
                </span>
              </span>
              <span className={financialDetails.margin >= 0 ? 'text-success' : 'text-danger'}>
                {financialDetails.margin >= 0 ? (
                  <TrendingUp size={14} className="mr-1" />
                ) : (
                  <TrendingDown size={14} className="mr-1" />
                )}
                {formatCurrency(financialDetails.margin, devis.currency)}
              </span>
            </div>
          </div>
        </Card>

        {/* Statistiques lignes (ERP only) */}
        <Card
          title="Statistiques lignes"
          icon={<Calculator size={18} />}
          className="azals-std-field--secondary"
        >
          <div className="azals-financial-summary">
            <div className="azals-financial-summary__row">
              <span>Nombre de lignes</span>
              <span>{devis.lines?.length || 0}</span>
            </div>
            <div className="azals-financial-summary__row">
              <span>Prix unitaire moyen</span>
              <span>
                {devis.lines && devis.lines.length > 0
                  ? formatCurrency(
                      devis.lines.reduce((s, l) => s + l.unit_price, 0) / devis.lines.length,
                      devis.currency
                    )
                  : '-'}
              </span>
            </div>
            <div className="azals-financial-summary__row">
              <span>Ligne la plus élevée</span>
              <span>
                {devis.lines && devis.lines.length > 0
                  ? formatCurrency(
                      Math.max(...devis.lines.map((l) => l.subtotal)),
                      devis.currency
                    )
                  : '-'}
              </span>
            </div>
            <div className="azals-financial-summary__row">
              <span>Remise totale lignes</span>
              <span>
                {formatCurrency(
                  devis.lines?.reduce((s, l) => s + l.discount_amount, 0) || 0,
                  devis.currency
                )}
              </span>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Informations devise */}
      <div className="azals-std-field--secondary mt-4">
        <p className="text-muted text-sm">
          Devise: {devis.currency} | Tous les montants sont exprimés en {devis.currency}
        </p>
      </div>
    </div>
  );
};

export default DevisFinancialTab;
