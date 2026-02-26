/**
 * AZALSCORE Module - CRM - Customer Financial Tab
 * Onglet données financières du client
 */

import React from 'react';
import {
  Euro, TrendingUp, FileText, Receipt, ShoppingCart,
  Calculator, PieChart, ArrowUpRight, BarChart3
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import type { Customer } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * CustomerFinancialTab - Données financières du client
 */
export const CustomerFinancialTab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  // Valeurs par défaut si non fournies
  const totalRevenue = customer.total_revenue || 0;
  const orderCount = customer.order_count || 0;
  const quoteCount = customer.quote_count || 0;
  const invoiceCount = customer.invoice_count || 0;
  const avgOrderValue = orderCount > 0 ? totalRevenue / orderCount : 0;

  return (
    <div className="azals-std-tab-content">
      {/* KPIs financiers */}
      <Grid cols={4} gap="md" className="mb-4">
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--green">
            <Euro size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">CA Total</span>
            <span className="azals-kpi-card__value">{formatCurrency(totalRevenue)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--blue">
            <ShoppingCart size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Commandes</span>
            <span className="azals-kpi-card__value">{orderCount}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--purple">
            <Calculator size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Panier moyen</span>
            <span className="azals-kpi-card__value">{formatCurrency(avgOrderValue)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--orange">
            <Receipt size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Factures</span>
            <span className="azals-kpi-card__value">{invoiceCount}</span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg">
        {/* Synthèse financière */}
        <Card title="Synthèse financière" icon={<PieChart size={18} />}>
          <div className="azals-std-fields-grid">
            <div className="azals-std-field">
              <span className="azals-std-field__label">Chiffre d&apos;affaires total</span>
              <div className="azals-std-field__value text-lg font-semibold text-success">
                {formatCurrency(totalRevenue)}
              </div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Nombre de commandes</span>
              <div className="azals-std-field__value">{orderCount}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Valeur moyenne commande</span>
              <div className="azals-std-field__value">{formatCurrency(avgOrderValue)}</div>
            </div>
            <div className="azals-std-field">
              <span className="azals-std-field__label">Dernière commande</span>
              <div className="azals-std-field__value">
                {customer.last_order_date ? formatDate(customer.last_order_date) : '-'}
              </div>
            </div>
          </div>
        </Card>

        {/* Documents commerciaux */}
        <Card title="Documents commerciaux" icon={<FileText size={18} />}>
          <div className="azals-stats-grid">
            <div className="azals-stat-item">
              <div className="azals-stat-item__icon text-blue">
                <FileText size={20} />
              </div>
              <div className="azals-stat-item__content">
                <span className="azals-stat-item__value">{quoteCount}</span>
                <span className="azals-stat-item__label">Devis</span>
              </div>
            </div>
            <div className="azals-stat-item">
              <div className="azals-stat-item__icon text-green">
                <ShoppingCart size={20} />
              </div>
              <div className="azals-stat-item__content">
                <span className="azals-stat-item__value">{orderCount}</span>
                <span className="azals-stat-item__label">Commandes</span>
              </div>
            </div>
            <div className="azals-stat-item">
              <div className="azals-stat-item__icon text-purple">
                <Receipt size={20} />
              </div>
              <div className="azals-stat-item__content">
                <span className="azals-stat-item__value">{invoiceCount}</span>
                <span className="azals-stat-item__label">Factures</span>
              </div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Évolution CA (ERP only) */}
      <Card
        title="Évolution du chiffre d&apos;affaires"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-chart-placeholder">
          <BarChart3 size={48} className="text-muted" />
          <p className="text-muted">Graphique d&apos;évolution du CA</p>
          <p className="text-sm text-muted">Données sur les 12 derniers mois</p>
        </div>
      </Card>

      {/* Détails comptables (ERP only) */}
      <Card
        title="Informations comptables"
        icon={<Calculator size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="azals-std-field">
            <span className="azals-std-field__label">Encours autorisé</span>
            <div className="azals-std-field__value">-</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Encours actuel</span>
            <div className="azals-std-field__value">-</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Disponible</span>
            <div className="azals-std-field__value">-</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Mode de règlement</span>
            <div className="azals-std-field__value">-</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Délai de paiement</span>
            <div className="azals-std-field__value">-</div>
          </div>
          <div className="azals-std-field">
            <span className="azals-std-field__label">Retard moyen</span>
            <div className="azals-std-field__value">-</div>
          </div>
        </Grid>
      </Card>

      {/* Actions rapides */}
      <Card title="Actions rapides" icon={<ArrowUpRight size={18} />} className="mt-4">
        <div className="azals-quick-actions">
          <button
            className="azals-quick-action"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'devis', params: { customerId: customer.id, action: 'new' } }
              }));
            }}
          >
            <FileText size={20} />
            <span>Créer un devis</span>
          </button>
          <button
            className="azals-quick-action"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'commandes', params: { customerId: customer.id, action: 'new' } }
              }));
            }}
          >
            <ShoppingCart size={20} />
            <span>Créer une commande</span>
          </button>
          <button
            className="azals-quick-action"
            onClick={() => {
              window.dispatchEvent(new CustomEvent('azals:navigate', {
                detail: { view: 'factures', params: { customerId: customer.id, action: 'new' } }
              }));
            }}
          >
            <Receipt size={20} />
            <span>Créer une facture</span>
          </button>
        </div>
      </Card>
    </div>
  );
};

export default CustomerFinancialTab;
