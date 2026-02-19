/**
 * AZALSCORE Module - Partners - Transactions Tab
 * Onglet transactions et activite commerciale
 */

import React from 'react';
import {
  ShoppingCart, Receipt, TrendingUp, DollarSign, Clock, AlertCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import type { Partner, Client } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PartnerTransactionsTab - Transactions
 */
export const PartnerTransactionsTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const isClient = partner.type === 'client';
  const client = partner as Client;
  const stats = partner.stats;

  return (
    <div className="azals-std-tab-content">
      {/* KPIs */}
      {isClient && (
        <Grid cols={4} gap="md" className="mb-4">
          <Card>
            <div className="text-center">
              <ShoppingCart size={24} className="text-primary mx-auto mb-2" />
              <div className="text-2xl font-bold">{client.total_orders || stats?.total_orders || 0}</div>
              <div className="text-sm text-muted">Commandes</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <DollarSign size={24} className="text-success mx-auto mb-2" />
              <div className="text-2xl font-bold">
                {formatCurrency(client.total_revenue || stats?.total_revenue || 0)}
              </div>
              <div className="text-sm text-muted">CA Total</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <TrendingUp size={24} className="text-blue-500 mx-auto mb-2" />
              <div className="text-2xl font-bold">
                {formatCurrency(stats?.average_order_value || 0)}
              </div>
              <div className="text-sm text-muted">Panier moyen</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <Receipt size={24} className={`mx-auto mb-2 ${(stats?.overdue_invoices || 0) > 0 ? 'text-danger' : 'text-muted'}`} />
              <div className={`text-2xl font-bold ${(stats?.overdue_invoices || 0) > 0 ? 'text-danger' : ''}`}>
                {stats?.overdue_invoices || 0}
              </div>
              <div className="text-sm text-muted">Factures en retard</div>
            </div>
          </Card>
        </Grid>
      )}

      <Grid cols={2} gap="lg">
        {/* Dernieres commandes */}
        <Card title="Dernieres commandes" icon={<ShoppingCart size={18} />}>
          <div className="azals-empty azals-empty--sm">
            <ShoppingCart size={32} className="text-muted" />
            <p className="text-muted">Aucune commande recente</p>
            {isClient && (
              <Button variant="ghost" size="sm" className="mt-2" onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'partners', type: 'order', partnerId: partner.id } })); }}>
                Creer une commande
              </Button>
            )}
          </div>
        </Card>

        {/* Factures en cours */}
        <Card title="Factures en cours" icon={<Receipt size={18} />}>
          {stats?.open_invoices ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>Factures ouvertes</span>
                <span className="font-bold">{stats.open_invoices}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Montant total du</span>
                <span className="font-bold text-primary">
                  {formatCurrency(stats.total_outstanding || 0)}
                </span>
              </div>
              {(stats.overdue_invoices || 0) > 0 && (
                <div className="flex justify-between items-center text-danger">
                  <span className="flex items-center gap-1">
                    <AlertCircle size={14} />
                    Factures en retard
                  </span>
                  <span className="font-bold">{stats.overdue_invoices}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Receipt size={32} className="text-muted" />
              <p className="text-muted">Aucune facture en cours</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Historique des paiements (ERP only) */}
      <Card
        title="Historique des paiements"
        icon={<DollarSign size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        {stats?.total_paid ? (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>Total paye</span>
              <span className="text-xl font-bold text-success">
                {formatCurrency(stats.total_paid)}
              </span>
            </div>
            <div className="text-sm text-muted">
              Derniere activite: {stats.last_activity_date ? formatDate(stats.last_activity_date) : 'N/A'}
            </div>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <DollarSign size={32} className="text-muted" />
            <p className="text-muted">Aucun paiement enregistre</p>
          </div>
        )}
      </Card>

      {/* Actions rapides */}
      {isClient && (
        <Card title="Actions rapides" icon={<Clock size={18} />} className="mt-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'partners', type: 'quote', partnerId: partner.id } })); }}>
              Nouveau devis
            </Button>
            <Button variant="secondary" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'partners', type: 'order', partnerId: partner.id } })); }}>
              Nouvelle commande
            </Button>
            <Button variant="secondary" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'partners', type: 'invoice', partnerId: partner.id } })); }}>
              Nouvelle facture
            </Button>
            <Button variant="ghost" size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'partner-history', params: { partnerId: partner.id } } })); }}>
              Voir tout l'historique
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PartnerTransactionsTab;
