/**
 * AZALSCORE Module - Maintenance - Asset Orders Tab
 * Onglet ordres de maintenance de l'equipement
 */

import React, { useState } from 'react';
import {
  Wrench, User, Calendar, Clock, Euro,
  AlertTriangle, CheckCircle, Play, Pause
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatCurrency, formatHours } from '@/utils/formatters';
import {
  ORDER_TYPE_CONFIG, ORDER_STATUS_CONFIG, PRIORITY_CONFIG,
  getOrderCountByStatus
} from '../types';
import type { Asset, MaintenanceOrder, MaintenanceOrderStatus } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AssetOrdersTab - Ordres de maintenance de l'equipement
 */
export const AssetOrdersTab: React.FC<TabContentProps<Asset>> = ({ data: asset }) => {
  const [filterStatus, setFilterStatus] = useState<MaintenanceOrderStatus | 'ALL'>('ALL');
  const orders = asset.maintenance_orders || [];
  const orderCounts = getOrderCountByStatus(asset);

  const filteredOrders = filterStatus === 'ALL'
    ? orders
    : orders.filter(o => o.status === filterStatus);

  // Ordres en retard
  const overdueOrders = orders.filter(o => {
    if (o.status === 'COMPLETED' || o.status === 'CANCELLED') return false;
    if (!o.planned_end_date) return false;
    return new Date(o.planned_end_date) < new Date();
  });

  return (
    <div className="azals-std-tab-content">
      {/* Alertes ordres en retard */}
      {overdueOrders.length > 0 && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <span>
            {overdueOrders.length} ordre(s) de maintenance en retard.
          </span>
        </div>
      )}

      {/* Resume des ordres */}
      <Grid cols={3} gap="md" className="mb-4">
        <OrderStatCard
          label="Brouillon"
          count={orderCounts.DRAFT}
          color="gray"
          active={filterStatus === 'DRAFT'}
          onClick={() => setFilterStatus(filterStatus === 'DRAFT' ? 'ALL' : 'DRAFT')}
        />
        <OrderStatCard
          label="Planifie"
          count={orderCounts.PLANNED}
          color="blue"
          active={filterStatus === 'PLANNED'}
          onClick={() => setFilterStatus(filterStatus === 'PLANNED' ? 'ALL' : 'PLANNED')}
        />
        <OrderStatCard
          label="En cours"
          count={orderCounts.IN_PROGRESS}
          color="orange"
          active={filterStatus === 'IN_PROGRESS'}
          onClick={() => setFilterStatus(filterStatus === 'IN_PROGRESS' ? 'ALL' : 'IN_PROGRESS')}
        />
        <OrderStatCard
          label="En attente"
          count={orderCounts.ON_HOLD}
          color="yellow"
          active={filterStatus === 'ON_HOLD'}
          onClick={() => setFilterStatus(filterStatus === 'ON_HOLD' ? 'ALL' : 'ON_HOLD')}
        />
        <OrderStatCard
          label="Termine"
          count={orderCounts.COMPLETED}
          color="green"
          active={filterStatus === 'COMPLETED'}
          onClick={() => setFilterStatus(filterStatus === 'COMPLETED' ? 'ALL' : 'COMPLETED')}
        />
        <OrderStatCard
          label="Annule"
          count={orderCounts.CANCELLED}
          color="red"
          active={filterStatus === 'CANCELLED'}
          onClick={() => setFilterStatus(filterStatus === 'CANCELLED' ? 'ALL' : 'CANCELLED')}
        />
      </Grid>

      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Wrench size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createMaintenanceOrder', assetId: asset.id } })); }}>
          Nouvel ordre
        </Button>
      </div>

      {/* Liste des ordres */}
      <Card title={`Ordres de maintenance${filterStatus !== 'ALL' ? ` - ${ORDER_STATUS_CONFIG[filterStatus].label}` : ''}`} icon={<Wrench size={18} />}>
        {filteredOrders.length > 0 ? (
          <div className="azals-orders-list">
            {filteredOrders.map((order) => (
              <OrderItem key={order.id} order={order} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Wrench size={32} className="text-muted" />
            <p className="text-muted">Aucun ordre de maintenance{filterStatus !== 'ALL' ? ' dans ce statut' : ''}</p>
            <Button size="sm" variant="ghost" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createMaintenanceOrder', assetId: asset.id } })); }}>
              Creer un ordre
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Carte statistique ordre
 */
interface OrderStatCardProps {
  label: string;
  count: number;
  color: string;
  active?: boolean;
  onClick?: () => void;
}

const OrderStatCard: React.FC<OrderStatCardProps> = ({ label, count, color, active, onClick }) => {
  return (
    <div
      className={`azals-stat-card azals-stat-card--${color} ${active ? 'azals-stat-card--active' : ''} cursor-pointer`}
      onClick={onClick}
    >
      <div className="azals-stat-card__value">{count}</div>
      <div className="azals-stat-card__label text-xs">{label}</div>
    </div>
  );
};

/**
 * Composant item d'ordre
 */
const OrderItem: React.FC<{ order: MaintenanceOrder }> = ({ order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const typeConfig = ORDER_TYPE_CONFIG[order.type];
  const priorityConfig = PRIORITY_CONFIG[order.priority];

  const isOverdue = order.planned_end_date &&
    new Date(order.planned_end_date) < new Date() &&
    order.status !== 'COMPLETED' &&
    order.status !== 'CANCELLED';

  const getStatusIcon = () => {
    switch (order.status) {
      case 'DRAFT':
        return <Wrench size={16} className="text-gray-400" />;
      case 'PLANNED':
        return <Calendar size={16} className="text-blue-500" />;
      case 'IN_PROGRESS':
        return <Play size={16} className="text-orange-500" />;
      case 'ON_HOLD':
        return <Pause size={16} className="text-yellow-500" />;
      case 'COMPLETED':
        return <CheckCircle size={16} className="text-green-500" />;
      default:
        return <Wrench size={16} className="text-gray-400" />;
    }
  };

  return (
    <div className={`azals-order-item ${isOverdue ? 'azals-order-item--overdue' : ''}`}>
      <div className="azals-order-item__status">{getStatusIcon()}</div>
      <div className="azals-order-item__content">
        <div className="azals-order-item__header">
          <span className="azals-order-item__number font-mono">{order.number}</span>
          <div className="azals-order-item__badges">
            <span className={`azals-badge azals-badge--${typeConfig.color} azals-badge--sm`}>
              {typeConfig.label}
            </span>
            <span className={`azals-badge azals-badge--${priorityConfig.color} azals-badge--sm`}>
              {priorityConfig.label}
            </span>
            <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
        <p className="azals-order-item__description text-sm">
          {order.description.length > 100 ? order.description.substring(0, 100) + '...' : order.description}
        </p>
        <div className="azals-order-item__meta">
          {order.assigned_to_name && (
            <span className="text-sm">
              <User size={12} className="inline mr-1" />
              {order.assigned_to_name}
            </span>
          )}
          {order.planned_start_date && (
            <span className={`text-sm ${isOverdue ? 'text-danger' : ''}`}>
              <Calendar size={12} className="inline mr-1" />
              {formatDate(order.planned_start_date)}
              {order.planned_end_date && ` - ${formatDate(order.planned_end_date)}`}
              {isOverdue && ' (En retard)'}
            </span>
          )}
          {order.labor_hours > 0 && (
            <span className="text-sm">
              <Clock size={12} className="inline mr-1" />
              {formatHours(order.labor_hours)}
            </span>
          )}
          {order.total_cost > 0 && (
            <span className="text-sm">
              <Euro size={12} className="inline mr-1" />
              {formatCurrency(order.total_cost)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssetOrdersTab;
