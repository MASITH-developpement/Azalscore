/**
 * AZALSCORE Module - E-commerce - Order Info Tab
 * Onglet informations de la commande
 */

import React from 'react';
import { ShoppingCart, User, MapPin, CreditCard, Globe } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import {
  ORDER_STATUS_CONFIG, PAYMENT_STATUS_CONFIG,
  ORDER_SOURCES, PAYMENT_METHODS
} from '../types';
import type { Order } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * OrderInfoTab - Informations generales
 */
export const OrderInfoTab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const paymentConfig = PAYMENT_STATUS_CONFIG[order.payment_status];
  const sourceInfo = ORDER_SOURCES.find(s => s.value === order.source);
  const paymentMethodInfo = PAYMENT_METHODS.find(p => p.value === order.payment_method);

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Commande" icon={<ShoppingCart size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Numero</span>
            <div className="azals-field__value font-mono font-semibold">{order.number}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Date</span>
            <div className="azals-field__value">{formatDateTime(order.created_at)}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut commande</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut paiement</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${paymentConfig.color}`}>
                {paymentConfig.label}
              </span>
            </div>
          </div>
        </Grid>

        {/* Source et methode de paiement (ERP only) */}
        <Grid cols={2} gap="md" className="mt-4 azals-std-field--secondary">
          <div className="azals-field">
            <span className="azals-field__label">
              <Globe size={14} className="inline mr-1" />
              Source
            </span>
            <div className="azals-field__value">{sourceInfo?.label || order.source || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">
              <CreditCard size={14} className="inline mr-1" />
              Mode de paiement
            </span>
            <div className="azals-field__value">{paymentMethodInfo?.label || order.payment_method || '-'}</div>
          </div>
          {order.payment_reference && (
            <div className="azals-field">
              <span className="azals-field__label">Reference paiement</span>
              <div className="azals-field__value font-mono text-sm">{order.payment_reference}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Client */}
      <Card title="Client" icon={<User size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Nom</span>
            <div className="azals-field__value font-medium">{order.customer_name}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Email</span>
            <div className="azals-field__value">
              <a href={`mailto:${order.customer_email}`} className="text-primary hover:underline">
                {order.customer_email}
              </a>
            </div>
          </div>
          {order.customer_phone && (
            <div className="azals-field">
              <span className="azals-field__label">Telephone</span>
              <div className="azals-field__value">
                <a href={`tel:${order.customer_phone}`} className="text-primary hover:underline">
                  {order.customer_phone}
                </a>
              </div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Adresses */}
      <Grid cols={2} gap="md" className="mt-4">
        {/* Adresse de livraison */}
        <Card title="Adresse de livraison" icon={<MapPin size={18} />}>
          {order.shipping_address ? (
            <div className="text-sm">
              <p className="font-medium">{order.customer_name}</p>
              <p>{order.shipping_address}</p>
              {order.shipping_postal_code && order.shipping_city && (
                <p>{order.shipping_postal_code} {order.shipping_city}</p>
              )}
              {order.shipping_country && <p>{order.shipping_country}</p>}
            </div>
          ) : (
            <p className="text-muted">Non renseignee</p>
          )}
        </Card>

        {/* Adresse de facturation */}
        <Card title="Adresse de facturation" icon={<MapPin size={18} />} className="azals-std-field--secondary">
          {order.billing_address ? (
            <div className="text-sm">
              <p className="font-medium">{order.customer_name}</p>
              <p>{order.billing_address}</p>
              {order.billing_postal_code && order.billing_city && (
                <p>{order.billing_postal_code} {order.billing_city}</p>
              )}
              {order.billing_country && <p>{order.billing_country}</p>}
            </div>
          ) : (
            <p className="text-muted">Identique a la livraison</p>
          )}
        </Card>
      </Grid>

      {/* Notes */}
      {(order.notes || order.internal_notes) && (
        <Card title="Notes" className="mt-4">
          {order.notes && (
            <div className="azals-field">
              <span className="azals-field__label">Note client</span>
              <div className="azals-field__value text-sm bg-yellow-50 p-3 rounded">
                {order.notes}
              </div>
            </div>
          )}
          {order.internal_notes && (
            <div className="azals-field mt-4 azals-std-field--secondary">
              <span className="azals-field__label">Note interne</span>
              <div className="azals-field__value text-sm bg-blue-50 p-3 rounded">
                {order.internal_notes}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Tracabilite (ERP only) */}
      <Card title="Tracabilite" className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Creee par</span>
            <div className="azals-field__value">{order.created_by_name || 'Client'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Creee le</span>
            <div className="azals-field__value">{formatDateTime(order.created_at)}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Modifiee le</span>
            <div className="azals-field__value">{formatDateTime(order.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default OrderInfoTab;
