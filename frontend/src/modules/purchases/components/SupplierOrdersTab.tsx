/**
 * AZALSCORE Module - Purchases - Supplier Orders Tab
 * Onglet commandes du fournisseur
 */

import React from 'react';
import { ShoppingCart, ExternalLink } from 'lucide-react';
import { Card } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Supplier, PurchaseOrder } from '../types';
import { ORDER_STATUS_CONFIG } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * SupplierOrdersTab - Commandes du fournisseur
 */
export const SupplierOrdersTab: React.FC<TabContentProps<Supplier & { orders?: PurchaseOrder[] }>> = ({ data }) => {
  const orders = data.orders || [];

  return (
    <div className="azals-std-tab-content">
      <Card
        title="Commandes"
        icon={<ShoppingCart size={18} />}
        actions={
          <Button variant="secondary" size="sm" leftIcon={<ShoppingCart size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'purchases', type: 'order', supplierId: data.id } })); }}>
            Nouvelle commande
          </Button>
        }
      >
        {orders.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>N°</th>
                <th>Date</th>
                <th>Statut</th>
                <th className="text-right">Total TTC</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const statusConfig = ORDER_STATUS_CONFIG[order.status];
                return (
                  <tr key={order.id}>
                    <td className="font-mono">{order.number}</td>
                    <td>{formatDate(order.date)}</td>
                    <td>
                      <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="text-right font-medium">
                      {formatCurrency(order.total_ttc, order.currency)}
                    </td>
                    <td className="text-right">
                      <Button variant="ghost" size="sm" leftIcon={<ExternalLink size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:view', { detail: { module: 'purchases', type: 'order', id: order.id } })); }}>
                        Voir
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <ShoppingCart size={32} className="text-muted" />
            <p className="text-muted">Aucune commande pour ce fournisseur</p>
            <Button variant="secondary" size="sm" leftIcon={<ShoppingCart size={14} />} className="mt-2" onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'purchases', type: 'order', supplierId: data.id } })); }}>
              Creer une commande
            </Button>
          </div>
        )}
      </Card>

      {/* Statistiques (ERP only) */}
      <Card title="Statistiques commandes" className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-2xl font-bold">{orders.length}</div>
            <div className="text-sm text-muted">Total commandes</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {orders.filter((o) => o.status === 'DRAFT' || o.status === 'SENT').length}
            </div>
            <div className="text-sm text-muted">En cours</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(orders.reduce((sum, o) => sum + o.total_ttc, 0))}
            </div>
            <div className="text-sm text-muted">Volume total</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SupplierOrdersTab;
