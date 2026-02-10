/**
 * AZALSCORE Module - Marketplace - Seller Orders Tab
 * Onglet commandes du vendeur
 */

import React from 'react';
import { ShoppingCart, ArrowRight, AlertTriangle } from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Seller, MarketplaceOrder } from '../types';
import { ORDER_STATUS_CONFIG } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * SellerOrdersTab - Commandes du vendeur
 */
export const SellerOrdersTab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const orders = seller.orders || [];

  const pendingOrders = orders.filter(o => o.status === 'PENDING').length;
  const disputedOrders = orders.filter(o => o.status === 'DISPUTED').length;
  const totalRevenue = orders.reduce((sum, o) => sum + o.total, 0);
  const totalCommission = orders.reduce((sum, o) => sum + o.commission, 0);
  const totalNet = orders.reduce((sum, o) => sum + o.net_amount, 0);

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <Card title="Resume des commandes" icon={<ShoppingCart size={18} />}>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-primary">{orders.length}</div>
            <div className="text-sm text-muted">Total commandes</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(totalRevenue)}
            </div>
            <div className="text-sm text-muted">CA total</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(totalCommission)}
            </div>
            <div className="text-sm text-muted">Commissions</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded">
            <div className="text-2xl font-bold text-purple-600">
              {formatCurrency(totalNet)}
            </div>
            <div className="text-sm text-muted">Net vendeur</div>
          </div>
        </div>
      </Card>

      {/* Alertes */}
      {(pendingOrders > 0 || disputedOrders > 0) && (
        <Card className="mt-4 border-orange-200 bg-orange-50">
          <div className="flex items-center gap-2 text-orange-700">
            <AlertTriangle size={18} />
            <span className="font-medium">
              {pendingOrders > 0 && `${pendingOrders} commande(s) en attente`}
              {pendingOrders > 0 && disputedOrders > 0 && ' - '}
              {disputedOrders > 0 && `${disputedOrders} litige(s) en cours`}
            </span>
          </div>
        </Card>
      )}

      {/* Liste des commandes */}
      <Card title={`Commandes (${orders.length})`} icon={<ShoppingCart size={18} />} className="mt-4">
        {orders.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>N° Commande</th>
                <th>Client</th>
                <th className="text-right">Total</th>
                <th className="text-right">Commission</th>
                <th className="text-right">Net</th>
                <th className="text-center">Statut</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <OrderRow key={order.id} order={order} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <ShoppingCart size={32} className="text-muted" />
            <p className="text-muted">Aucune commande enregistree</p>
          </div>
        )}
      </Card>

      {/* Stats par statut (ERP only) */}
      <Card title="Repartition par statut" icon={<ShoppingCart size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-6 gap-2">
          {Object.entries(ORDER_STATUS_CONFIG).map(([status, config]) => {
            const count = orders.filter(o => o.status === status).length;
            const amount = orders
              .filter(o => o.status === status)
              .reduce((sum, o) => sum + o.total, 0);
            return (
              <div key={status} className="text-center p-2 bg-gray-50 rounded">
                <span className={`azals-badge azals-badge--${config.color} mb-1`}>
                  {config.label}
                </span>
                <div className="text-lg font-bold">{count}</div>
                <div className="text-xs text-muted">{formatCurrency(amount)}</div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant ligne commande
 */
const OrderRow: React.FC<{ order: MarketplaceOrder }> = ({ order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];

  return (
    <tr>
      <td>
        <code className="font-mono">{order.number}</code>
      </td>
      <td>{order.customer_name}</td>
      <td className="text-right font-medium">
        {formatCurrency(order.total, order.currency)}
      </td>
      <td className="text-right text-muted">
        {formatCurrency(order.commission, order.currency)}
      </td>
      <td className="text-right font-medium text-green-600">
        {formatCurrency(order.net_amount, order.currency)}
      </td>
      <td className="text-center">
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </td>
      <td className="text-muted text-sm">{formatDate(order.created_at)}</td>
    </tr>
  );
};

export default SellerOrdersTab;
