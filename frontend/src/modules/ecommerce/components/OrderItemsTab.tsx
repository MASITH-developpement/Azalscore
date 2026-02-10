/**
 * AZALSCORE Module - E-commerce - Order Items Tab
 * Onglet articles de la commande
 */

import React from 'react';
import { Package, Percent, Calculator } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Order, OrderItem } from '../types';
import { formatCurrency } from '@/utils/formatters';

/**
 * OrderItemsTab - Articles commandes
 */
export const OrderItemsTab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Liste des articles */}
      <Card title={`Articles (${order.items.length})`} icon={<Package size={18} />}>
        {order.items.length > 0 ? (
          <table className="azals-table azals-table--simple w-full">
            <thead>
              <tr>
                <th className="text-left">Produit</th>
                <th className="text-left azals-std-field--secondary">SKU</th>
                <th className="text-right">Quantite</th>
                <th className="text-right">Prix unitaire</th>
                <th className="text-right azals-std-field--secondary">Remise</th>
                <th className="text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item, index) => (
                <OrderItemRow key={item.id || index} item={item} currency={order.currency} />
              ))}
            </tbody>
            <tfoot className="border-t-2 font-semibold">
              <tr>
                <td colSpan={3}></td>
                <td className="text-right pt-4">Sous-total</td>
                <td></td>
                <td className="text-right pt-4">{formatCurrency(order.subtotal, order.currency)}</td>
              </tr>
              {order.discount > 0 && (
                <tr className="text-green-600">
                  <td colSpan={3}></td>
                  <td className="text-right">Remise{order.discount_code ? ` (${order.discount_code})` : ''}</td>
                  <td></td>
                  <td className="text-right">-{formatCurrency(order.discount, order.currency)}</td>
                </tr>
              )}
              <tr>
                <td colSpan={3}></td>
                <td className="text-right">Livraison</td>
                <td></td>
                <td className="text-right">{formatCurrency(order.shipping_cost, order.currency)}</td>
              </tr>
              <tr className="azals-std-field--secondary">
                <td colSpan={3}></td>
                <td className="text-right">TVA</td>
                <td></td>
                <td className="text-right">{formatCurrency(order.tax, order.currency)}</td>
              </tr>
              <tr className="text-lg">
                <td colSpan={3}></td>
                <td className="text-right pt-2">Total</td>
                <td></td>
                <td className="text-right pt-2 text-primary">{formatCurrency(order.total, order.currency)}</td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Package size={32} className="text-muted" />
            <p className="text-muted">Aucun article</p>
          </div>
        )}
      </Card>

      {/* Resume financier */}
      <Card title="Resume financier" icon={<Calculator size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Articles</label>
            <div className="azals-field__value text-lg font-medium">
              {order.items.reduce((sum, item) => sum + item.quantity, 0)} articles
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Sous-total</label>
            <div className="azals-field__value text-lg font-medium">
              {formatCurrency(order.subtotal, order.currency)}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Total TTC</label>
            <div className="azals-field__value text-lg font-bold text-primary">
              {formatCurrency(order.total, order.currency)}
            </div>
          </div>
        </Grid>

        {/* Details (ERP only) */}
        <div className="mt-4 p-4 bg-gray-50 rounded azals-std-field--secondary">
          <Grid cols={4} gap="md">
            {order.discount > 0 && (
              <div className="azals-field">
                <label className="azals-field__label">
                  <Percent size={14} className="inline mr-1" />
                  Remise
                </label>
                <div className="azals-field__value text-green-600">
                  -{formatCurrency(order.discount, order.currency)}
                </div>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Livraison</label>
              <div className="azals-field__value">
                {formatCurrency(order.shipping_cost, order.currency)}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">TVA</label>
              <div className="azals-field__value">
                {formatCurrency(order.tax, order.currency)}
              </div>
            </div>
            {order.shipping_method && (
              <div className="azals-field">
                <label className="azals-field__label">Mode livraison</label>
                <div className="azals-field__value">{order.shipping_method}</div>
              </div>
            )}
          </Grid>
        </div>
      </Card>

      {/* Code promo (si utilise) */}
      {order.discount_code && (
        <Card title="Code promotionnel" icon={<Percent size={18} />} className="mt-4">
          <div className="flex items-center gap-4 p-4 bg-green-50 rounded border border-green-200">
            <Percent size={24} className="text-green-500" />
            <div className="flex-1">
              <div className="font-medium font-mono">{order.discount_code}</div>
              <div className="text-sm text-muted">
                Remise appliquee: {formatCurrency(order.discount, order.currency)}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

/**
 * Ligne d'article
 */
interface OrderItemRowProps {
  item: OrderItem;
  currency: string;
}

const OrderItemRow: React.FC<OrderItemRowProps> = ({ item, currency }) => {
  return (
    <tr>
      <td>
        <div className="font-medium">{item.product_name}</div>
        {item.variant && (
          <div className="text-sm text-muted">{item.variant}</div>
        )}
        {item.notes && (
          <div className="text-xs text-muted italic mt-1">{item.notes}</div>
        )}
      </td>
      <td className="font-mono text-sm text-muted azals-std-field--secondary">{item.sku}</td>
      <td className="text-right">{item.quantity}</td>
      <td className="text-right">{formatCurrency(item.unit_price, currency)}</td>
      <td className="text-right text-green-600 azals-std-field--secondary">
        {item.discount > 0 ? `-${formatCurrency(item.discount, currency)}` : '-'}
      </td>
      <td className="text-right font-medium">{formatCurrency(item.total, currency)}</td>
    </tr>
  );
};

export default OrderItemsTab;
