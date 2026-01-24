/**
 * AZALSCORE Module - Production - Order Info Tab
 * Onglet informations generales de l'ordre de fabrication
 */

import React from 'react';
import {
  Factory, Package, Calendar, User, Clock, Target,
  FileText, Warehouse, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { ProductionOrder } from '../types';
import {
  formatDate, formatDateTime, formatQuantity, formatDuration, formatCurrency,
  ORDER_STATUS_CONFIG, ORDER_PRIORITY_CONFIG,
  isLate, isUrgent, getCompletionRate
} from '../types';

/**
 * OrderInfoTab - Informations generales de l'ordre de fabrication
 */
export const OrderInfoTab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const priorityConfig = ORDER_PRIORITY_CONFIG[order.priority];
  const completionRate = getCompletionRate(order);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes */}
      {(isLate(order) || isUrgent(order)) && (
        <div className={`azals-alert azals-alert--${isLate(order) ? 'danger' : 'warning'} mb-4`}>
          <AlertTriangle size={18} />
          <span>
            {isLate(order) && 'Cet ordre est en retard par rapport a la date prevue. '}
            {isUrgent(order) && `Priorite ${priorityConfig.label.toLowerCase()}.`}
          </span>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations principales */}
        <Card title="Informations generales" icon={<Factory size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Numero</label>
              <div className="azals-field__value font-mono">{order.number}</div>
            </div>
            {order.name && (
              <div className="azals-field">
                <label className="azals-field__label">Designation</label>
                <div className="azals-field__value">{order.name}</div>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Statut</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Priorite</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${priorityConfig.color}`}>
                  {priorityConfig.label}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Produit a fabriquer */}
        <Card title="Produit a fabriquer" icon={<Package size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Code produit</label>
              <div className="azals-field__value font-mono">{order.product_code || '-'}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Designation</label>
              <div className="azals-field__value">{order.product_name || '-'}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Nomenclature</label>
              <div className="azals-field__value">
                {order.bom_code || '-'}
                {order.bom_version && <span className="text-muted ml-1">v{order.bom_version}</span>}
              </div>
            </div>
          </div>
        </Card>

        {/* Quantites */}
        <Card title="Quantites" icon={<Target size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Quantite planifiee</label>
              <div className="azals-field__value text-lg font-semibold">
                {formatQuantity(order.quantity_planned, order.unit)}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Quantite produite</label>
              <div className={`azals-field__value text-lg font-semibold ${
                completionRate >= 1 ? 'text-success' : completionRate > 0 ? 'text-warning' : ''
              }`}>
                {formatQuantity(order.quantity_produced, order.unit)}
              </div>
            </div>
            {order.quantity_scrapped !== undefined && order.quantity_scrapped > 0 && (
              <div className="azals-field">
                <label className="azals-field__label">Rebuts</label>
                <div className="azals-field__value text-danger">
                  {formatQuantity(order.quantity_scrapped, order.unit)}
                </div>
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label">Avancement</label>
              <div className="azals-field__value">
                <div className="azals-progress">
                  <div
                    className={`azals-progress__bar azals-progress__bar--${
                      completionRate >= 1 ? 'success' : completionRate >= 0.5 ? 'warning' : 'primary'
                    }`}
                    style={{ width: `${Math.min(completionRate * 100, 100)}%` }}
                  />
                </div>
                <span className="text-sm text-muted ml-2">{(completionRate * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Dates */}
        <Card title="Planification" icon={<Calendar size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Date de debut prevue</label>
              <div className="azals-field__value">{formatDate(order.start_date)}</div>
            </div>
            {order.due_date && (
              <div className="azals-field">
                <label className="azals-field__label">Date d'echeance</label>
                <div className={`azals-field__value ${isLate(order) ? 'text-danger' : ''}`}>
                  {formatDate(order.due_date)}
                  {isLate(order) && <AlertTriangle size={14} className="ml-1 inline" />}
                </div>
              </div>
            )}
            {order.actual_start && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Debut reel</label>
                <div className="azals-field__value">{formatDateTime(order.actual_start)}</div>
              </div>
            )}
            {order.actual_end && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Fin reelle</label>
                <div className="azals-field__value">{formatDateTime(order.actual_end)}</div>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Informations complementaires (ERP only) */}
      <Card title="Informations complementaires" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Responsable</label>
            <div className="azals-field__value">
              {order.responsible_name ? (
                <span className="flex items-center gap-1">
                  <User size={14} />
                  {order.responsible_name}
                </span>
              ) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Entrepot</label>
            <div className="azals-field__value">
              {order.warehouse_name ? (
                <span className="flex items-center gap-1">
                  <Warehouse size={14} />
                  {order.warehouse_name}
                </span>
              ) : '-'}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Commande client</label>
            <div className="azals-field__value font-mono">
              {order.customer_order_number || '-'}
            </div>
          </div>
          {order.duration_planned !== undefined && (
            <div className="azals-field">
              <label className="azals-field__label">Duree prevue</label>
              <div className="azals-field__value">
                <Clock size={14} className="inline mr-1" />
                {formatDuration(order.duration_planned)}
              </div>
            </div>
          )}
          {order.duration_actual !== undefined && (
            <div className="azals-field">
              <label className="azals-field__label">Duree reelle</label>
              <div className="azals-field__value">
                <Clock size={14} className="inline mr-1" />
                {formatDuration(order.duration_actual)}
              </div>
            </div>
          )}
          {order.cost_planned !== undefined && (
            <div className="azals-field">
              <label className="azals-field__label">Cout prevu</label>
              <div className="azals-field__value">{formatCurrency(order.cost_planned)}</div>
            </div>
          )}
          {order.cost_actual !== undefined && (
            <div className="azals-field">
              <label className="azals-field__label">Cout reel</label>
              <div className="azals-field__value">{formatCurrency(order.cost_actual)}</div>
            </div>
          )}
        </Grid>
        {order.notes && (
          <div className="azals-field mt-4">
            <label className="azals-field__label">Notes</label>
            <div className="azals-field__value azals-field__value--multiline">{order.notes}</div>
          </div>
        )}
      </Card>

      {/* Metadata */}
      <div className="azals-std-metadata mt-4 azals-std-field--secondary">
        <span>Cree le {formatDateTime(order.created_at)}</span>
        {order.created_by && <span> par {order.created_by}</span>}
        {order.updated_at && <span> - Modifie le {formatDateTime(order.updated_at)}</span>}
      </div>
    </div>
  );
};

export default OrderInfoTab;
