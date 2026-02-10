/**
 * AZALSCORE Module - STOCK - Product Financial Tab
 * Onglet données financières de l'article
 */

import React from 'react';
import {
  Euro, TrendingUp, TrendingDown, Package,
  Calculator, PieChart, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product, Movement } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  formatQuantity,
  MOVEMENT_TYPE_CONFIG, getStockValue
} from '../types';

/**
 * ProductFinancialTab - Données financières de l'article
 */
export const ProductFinancialTab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const stockValue = getStockValue(product);
  const movements = product.movements || [];

  // Calculer les statistiques de mouvement
  const movementsIn = movements.filter(m => m.type === 'IN' && m.status === 'VALIDATED');
  const movementsOut = movements.filter(m => m.type === 'OUT' && m.status === 'VALIDATED');
  const totalIn = movementsIn.reduce((sum, m) => sum + m.quantity, 0);
  const totalOut = movementsOut.reduce((sum, m) => sum + m.quantity, 0);
  const valueIn = movementsIn.reduce((sum, m) => sum + (m.total_cost || m.quantity * product.cost_price), 0);
  const valueOut = movementsOut.reduce((sum, m) => sum + (m.total_cost || m.quantity * product.cost_price), 0);

  // Marge
  const margin = product.sale_price - product.cost_price;
  const marginPercent = product.cost_price > 0 ? (margin / product.cost_price) * 100 : 0;

  return (
    <div className="azals-std-tab-content">
      {/* KPIs financiers */}
      <Grid cols={4} gap="md" className="mb-4">
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--blue">
            <Euro size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Prix d'achat</span>
            <span className="azals-kpi-card__value">{formatCurrency(product.cost_price)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--green">
            <TrendingUp size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Prix de vente</span>
            <span className="azals-kpi-card__value">{formatCurrency(product.sale_price)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className={`azals-kpi-card__icon azals-kpi-card__icon--${margin >= 0 ? 'green' : 'red'}`}>
            {margin >= 0 ? <ArrowUpRight size={24} /> : <ArrowDownRight size={24} />}
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Marge unitaire</span>
            <span className={`azals-kpi-card__value ${margin >= 0 ? 'text-success' : 'text-danger'}`}>
              {formatCurrency(margin)}
              <small className="ml-1">({marginPercent.toFixed(1)}%)</small>
            </span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--purple">
            <Package size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Valeur du stock</span>
            <span className="azals-kpi-card__value">{formatCurrency(stockValue)}</span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg">
        {/* Détail des prix */}
        <Card title="Détail des prix" icon={<Calculator size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <label className="azals-std-field__label">Prix d'achat HT</label>
              <div className="azals-std-field__value">{formatCurrency(product.cost_price)}</div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Prix de vente HT</label>
              <div className="azals-std-field__value">{formatCurrency(product.sale_price)}</div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Marge brute</label>
              <div className={`azals-std-field__value font-medium ${margin >= 0 ? 'text-success' : 'text-danger'}`}>
                {formatCurrency(margin)}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Taux de marge</label>
              <div className={`azals-std-field__value font-medium ${marginPercent >= 0 ? 'text-success' : 'text-danger'}`}>
                {marginPercent.toFixed(2)}%
              </div>
            </div>
          </div>
        </Card>

        {/* Valorisation du stock */}
        <Card title="Valorisation du stock" icon={<PieChart size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <label className="azals-std-field__label">Quantité en stock</label>
              <div className="azals-std-field__value">
                {formatQuantity(product.current_stock, product.unit)}
              </div>
            </div>
            <div className="azals-std-field">
              <label className="azals-std-field__label">Coût unitaire moyen</label>
              <div className="azals-std-field__value">{formatCurrency(product.cost_price)}</div>
            </div>
            <div className="azals-std-field azals-std-field--full">
              <label className="azals-std-field__label">Valeur totale du stock</label>
              <div className="azals-std-field__value text-lg font-semibold text-primary">
                {formatCurrency(stockValue)}
              </div>
            </div>
            <div className="azals-std-field azals-std-field--secondary">
              <label className="azals-std-field__label">Valeur au prix de vente</label>
              <div className="azals-std-field__value">
                {formatCurrency(product.current_stock * product.sale_price)}
              </div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Mouvements financiers */}
      <Card title="Synthèse des mouvements" icon={<TrendingUp size={18} />} className="mt-4">
        <Grid cols={2} gap="lg">
          <div className="azals-movement-summary azals-movement-summary--in">
            <div className="azals-movement-summary__header">
              <ArrowUpRight size={20} className="text-success" />
              <h4>Entrées</h4>
            </div>
            <div className="azals-movement-summary__stats">
              <div className="azals-movement-summary__stat">
                <span className="label">Quantité totale</span>
                <span className="value">{formatQuantity(totalIn, product.unit)}</span>
              </div>
              <div className="azals-movement-summary__stat">
                <span className="label">Valeur totale</span>
                <span className="value text-success">{formatCurrency(valueIn)}</span>
              </div>
              <div className="azals-movement-summary__stat">
                <span className="label">Nb mouvements</span>
                <span className="value">{movementsIn.length}</span>
              </div>
            </div>
          </div>
          <div className="azals-movement-summary azals-movement-summary--out">
            <div className="azals-movement-summary__header">
              <ArrowDownRight size={20} className="text-danger" />
              <h4>Sorties</h4>
            </div>
            <div className="azals-movement-summary__stats">
              <div className="azals-movement-summary__stat">
                <span className="label">Quantité totale</span>
                <span className="value">{formatQuantity(totalOut, product.unit)}</span>
              </div>
              <div className="azals-movement-summary__stat">
                <span className="label">Valeur totale</span>
                <span className="value text-danger">{formatCurrency(valueOut)}</span>
              </div>
              <div className="azals-movement-summary__stat">
                <span className="label">Nb mouvements</span>
                <span className="value">{movementsOut.length}</span>
              </div>
            </div>
          </div>
        </Grid>
      </Card>

      {/* Derniers mouvements (ERP only) */}
      <Card
        title="Derniers mouvements valorisés"
        icon={<Euro size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        {movements.length > 0 ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Référence</th>
                <th className="text-right">Quantité</th>
                <th className="text-right">Coût unit.</th>
                <th className="text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {movements.slice(0, 10).map((movement) => {
                const typeConfig = MOVEMENT_TYPE_CONFIG[movement.type];
                const totalCost = movement.total_cost || movement.quantity * product.cost_price;
                return (
                  <tr key={movement.id}>
                    <td className="text-muted">{formatDate(movement.date)}</td>
                    <td>
                      <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                        {typeConfig.label}
                      </span>
                    </td>
                    <td className="font-mono text-sm">{movement.number}</td>
                    <td className="text-right">
                      <span className={movement.type === 'IN' ? 'text-success' : movement.type === 'OUT' ? 'text-danger' : ''}>
                        {movement.type === 'IN' ? '+' : movement.type === 'OUT' ? '-' : ''}
                        {formatQuantity(movement.quantity, product.unit)}
                      </span>
                    </td>
                    <td className="text-right">{formatCurrency(movement.cost_price || product.cost_price)}</td>
                    <td className="text-right font-medium">{formatCurrency(totalCost)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Euro size={32} className="text-muted" />
            <p className="text-muted">Aucun mouvement enregistré</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ProductFinancialTab;
