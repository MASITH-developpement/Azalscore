/**
 * AZALSCORE Module - E-commerce - Order Shipping Tab
 * Onglet expedition de la commande
 */

import React from 'react';
import { Truck, MapPin, Package, Clock, CheckCircle2 } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Order } from '../types';
import {
  ORDER_STATUS_CONFIG, SHIPPING_STATUS_CONFIG, CARRIERS,
  formatDateTime, canShipOrder
} from '../types';

/**
 * OrderShippingTab - Expedition
 */
export const OrderShippingTab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const carrierInfo = CARRIERS.find(c => c.value === order.carrier);
  const readyToShip = canShipOrder(order);

  const handleCreateShipment = () => {
    console.log('Create shipment for order:', order.id);
  };

  const handlePrintLabel = () => {
    console.log('Print label for order:', order.id);
  };

  return (
    <div className="azals-std-tab-content">
      {/* Statut expedition */}
      <Card title="Statut expedition" icon={<Truck size={18} />}>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded">
          <div className={`p-3 rounded-full bg-${statusConfig.color}-100`}>
            <Truck size={24} className={`text-${statusConfig.color}-600`} />
          </div>
          <div className="flex-1">
            <div className="font-medium text-lg">{statusConfig.label}</div>
            <div className="text-sm text-muted">
              {order.status === 'PENDING' && 'En attente de confirmation'}
              {order.status === 'CONFIRMED' && 'Commande confirmee, en attente de preparation'}
              {order.status === 'PROCESSING' && 'En cours de preparation'}
              {order.status === 'SHIPPED' && 'Colis expedie'}
              {order.status === 'DELIVERED' && 'Colis livre'}
              {order.status === 'CANCELLED' && 'Commande annulee'}
              {order.status === 'REFUNDED' && 'Commande remboursee'}
            </div>
          </div>
          {readyToShip && (
            <Button onClick={handleCreateShipment}>
              Creer l'expedition
            </Button>
          )}
        </div>

        {/* Timeline expedition */}
        <div className="mt-6">
          <ShippingTimeline order={order} />
        </div>
      </Card>

      {/* Informations de suivi */}
      {order.tracking_number && (
        <Card title="Suivi colis" icon={<Package size={18} />} className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Transporteur</label>
              <div className="azals-field__value">{carrierInfo?.label || order.carrier || '-'}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Numero de suivi</label>
              <div className="azals-field__value font-mono">{order.tracking_number}</div>
            </div>
            {order.shipped_at && (
              <div className="azals-field">
                <label className="azals-field__label">Expedie le</label>
                <div className="azals-field__value">{formatDateTime(order.shipped_at)}</div>
              </div>
            )}
            {order.delivered_at && (
              <div className="azals-field">
                <label className="azals-field__label">Livre le</label>
                <div className="azals-field__value text-green-600 font-medium">
                  {formatDateTime(order.delivered_at)}
                </div>
              </div>
            )}
          </Grid>

          <div className="mt-4 flex gap-2">
            <Button variant="secondary" leftIcon={<Truck size={16} />}>
              Suivre le colis
            </Button>
            <Button variant="ghost" onClick={handlePrintLabel}>
              Imprimer l'etiquette
            </Button>
          </div>
        </Card>
      )}

      {/* Adresse de livraison */}
      <Card title="Adresse de livraison" icon={<MapPin size={18} />} className="mt-4">
        <div className="p-4 bg-blue-50 rounded border border-blue-200">
          <div className="font-medium mb-2">{order.customer_name}</div>
          {order.shipping_address && <p>{order.shipping_address}</p>}
          {order.shipping_postal_code && order.shipping_city && (
            <p>{order.shipping_postal_code} {order.shipping_city}</p>
          )}
          {order.shipping_country && <p>{order.shipping_country}</p>}
          {order.customer_phone && (
            <p className="mt-2 text-sm text-muted">Tel: {order.customer_phone}</p>
          )}
        </div>
      </Card>

      {/* Mode de livraison (ERP only) */}
      <Card title="Details expedition" icon={<Truck size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Mode de livraison</label>
            <div className="azals-field__value">{order.shipping_method || 'Standard'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Frais de port</label>
            <div className="azals-field__value">
              {order.shipping_cost > 0
                ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: order.currency }).format(order.shipping_cost)
                : 'Gratuit'}
            </div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Timeline de l'expedition
 */
const ShippingTimeline: React.FC<{ order: Order }> = ({ order }) => {
  const steps = [
    { key: 'PENDING', label: 'Commande recue', date: order.created_at },
    { key: 'CONFIRMED', label: 'Confirmee', date: order.status !== 'PENDING' ? order.updated_at : null },
    { key: 'PROCESSING', label: 'En preparation', date: ['PROCESSING', 'SHIPPED', 'DELIVERED'].includes(order.status) ? order.updated_at : null },
    { key: 'SHIPPED', label: 'Expediee', date: order.shipped_at },
    { key: 'DELIVERED', label: 'Livree', date: order.delivered_at },
  ];

  const statusOrder = ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'];
  const currentIndex = statusOrder.indexOf(order.status);

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => {
        const isCompleted = index <= currentIndex && order.status !== 'CANCELLED' && order.status !== 'REFUNDED';
        const isCurrent = index === currentIndex;

        return (
          <React.Fragment key={step.key}>
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                isCompleted ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {isCompleted ? (
                  <CheckCircle2 size={20} />
                ) : (
                  <Clock size={20} />
                )}
              </div>
              <div className={`mt-2 text-sm font-medium ${isCurrent ? 'text-primary' : ''}`}>
                {step.label}
              </div>
              {step.date && isCompleted && (
                <div className="text-xs text-muted">
                  {new Date(step.date).toLocaleDateString('fr-FR')}
                </div>
              )}
            </div>
            {index < steps.length - 1 && (
              <div className={`flex-1 h-1 mx-2 ${
                index < currentIndex ? 'bg-green-500' : 'bg-gray-200'
              }`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default OrderShippingTab;
