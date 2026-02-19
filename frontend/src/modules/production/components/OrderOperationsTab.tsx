/**
 * AZALSCORE Module - Production - Order Operations Tab
 * Onglet operations/ordres de travail de l'ordre de fabrication
 */

import React from 'react';
import {
  Settings, Play, Pause, CheckCircle, Clock,
  User, Factory, AlertTriangle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDuration, formatDateTime } from '@/utils/formatters';
import {
  WORK_ORDER_STATUS_CONFIG
} from '../types';
import type { ProductionOrder, WorkOrder } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * OrderOperationsTab - Operations/Ordres de travail
 */
export const OrderOperationsTab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const workOrders = order.work_orders || [];

  // Regrouper par statut
  const pending = workOrders.filter(wo => wo.status === 'PENDING' || wo.status === 'READY');
  const inProgress = workOrders.filter(wo => wo.status === 'IN_PROGRESS');
  const done = workOrders.filter(wo => wo.status === 'DONE');

  // Calculer les totaux
  const totalPlanned = workOrders.reduce((sum, wo) => sum + wo.duration_planned, 0);
  const totalActual = workOrders.reduce((sum, wo) => sum + wo.duration_actual, 0);

  return (
    <div className="azals-std-tab-content">
      {/* Resume */}
      <div className="azals-operations-summary mb-4">
        <Grid cols={4} gap="md">
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">{workOrders.length}</span>
            <span className="azals-stat-mini__label">Operations</span>
          </div>
          <div className="azals-stat-mini azals-stat-mini--warning">
            <span className="azals-stat-mini__value">{inProgress.length}</span>
            <span className="azals-stat-mini__label">En cours</span>
          </div>
          <div className="azals-stat-mini azals-stat-mini--success">
            <span className="azals-stat-mini__value">{done.length}</span>
            <span className="azals-stat-mini__label">Terminees</span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">{formatDuration(totalPlanned)}</span>
            <span className="azals-stat-mini__label">Duree totale prevue</span>
          </div>
        </Grid>
      </div>

      {/* Operations en cours */}
      {inProgress.length > 0 && (
        <Card title="Operations en cours" icon={<Play size={18} />} className="mb-4">
          <div className="azals-work-orders-list">
            {inProgress.map((wo) => (
              <WorkOrderCard key={wo.id} workOrder={wo} highlight />
            ))}
          </div>
        </Card>
      )}

      {/* Operations a venir */}
      {pending.length > 0 && (
        <Card title="Operations a venir" icon={<Clock size={18} />} className="mb-4">
          <div className="azals-work-orders-list">
            {pending.map((wo) => (
              <WorkOrderCard key={wo.id} workOrder={wo} />
            ))}
          </div>
        </Card>
      )}

      {/* Operations terminees */}
      {done.length > 0 && (
        <Card title="Operations terminees" icon={<CheckCircle size={18} />} className="mb-4">
          <div className="azals-work-orders-list">
            {done.map((wo) => (
              <WorkOrderCard key={wo.id} workOrder={wo} />
            ))}
          </div>
        </Card>
      )}

      {/* Liste vide */}
      {workOrders.length === 0 && (
        <div className="azals-empty">
          <Settings size={48} className="text-muted" />
          <h3>Aucune operation</h3>
          <p className="text-muted">Cet ordre n'a pas encore d'operations definies.</p>
        </div>
      )}

      {/* Tableau detaille (ERP only) */}
      {workOrders.length > 0 && (
        <Card title="Detail des operations" icon={<Settings size={18} />} className="azals-std-field--secondary">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Seq.</th>
                <th>Operation</th>
                <th>Poste de travail</th>
                <th>Duree prevue</th>
                <th>Duree reelle</th>
                <th>Ecart</th>
                <th>Operateur</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {workOrders.sort((a, b) => a.sequence - b.sequence).map((wo) => {
                const statusConfig = WORK_ORDER_STATUS_CONFIG[wo.status];
                const variance = wo.duration_actual - wo.duration_planned;
                return (
                  <tr key={wo.id}>
                    <td className="text-center">{wo.sequence}</td>
                    <td>{wo.name}</td>
                    <td>
                      <span className="flex items-center gap-1">
                        <Factory size={14} />
                        {wo.work_center_name || wo.work_center_code || '-'}
                      </span>
                    </td>
                    <td>{formatDuration(wo.duration_planned)}</td>
                    <td>{wo.duration_actual > 0 ? formatDuration(wo.duration_actual) : '-'}</td>
                    <td className={variance > 0 ? 'text-danger' : variance < 0 ? 'text-success' : ''}>
                      {wo.duration_actual > 0 ? (
                        <>
                          {variance > 0 ? '+' : ''}{formatDuration(Math.abs(variance))}
                        </>
                      ) : '-'}
                    </td>
                    <td>{wo.operator_name || '-'}</td>
                    <td>
                      <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
                        {statusConfig.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="font-semibold">
                <td colSpan={3}>Total</td>
                <td>{formatDuration(totalPlanned)}</td>
                <td>{totalActual > 0 ? formatDuration(totalActual) : '-'}</td>
                <td className={totalActual - totalPlanned > 0 ? 'text-danger' : 'text-success'}>
                  {totalActual > 0 ? (
                    <>
                      {totalActual - totalPlanned > 0 ? '+' : ''}
                      {formatDuration(Math.abs(totalActual - totalPlanned))}
                    </>
                  ) : '-'}
                </td>
                <td colSpan={2}></td>
              </tr>
            </tfoot>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant carte d'ordre de travail
 */
interface WorkOrderCardProps {
  workOrder: WorkOrder;
  highlight?: boolean;
}

const WorkOrderCard: React.FC<WorkOrderCardProps> = ({ workOrder, highlight }) => {
  const statusConfig = WORK_ORDER_STATUS_CONFIG[workOrder.status];
  const isOvertime = workOrder.duration_actual > workOrder.duration_planned;

  return (
    <div className={`azals-work-order-card ${highlight ? 'azals-work-order-card--highlight' : ''}`}>
      <div className="azals-work-order-card__header">
        <div className="azals-work-order-card__sequence">
          <span className="azals-badge azals-badge--gray">{workOrder.sequence}</span>
        </div>
        <div className="azals-work-order-card__title">
          <h4>{workOrder.name}</h4>
          {workOrder.description && (
            <p className="text-sm text-muted">{workOrder.description}</p>
          )}
        </div>
        <div className="azals-work-order-card__status">
          <span className={`azals-badge azals-badge--${statusConfig.color}`}>
            {statusConfig.label}
          </span>
        </div>
      </div>

      <div className="azals-work-order-card__content">
        <div className="azals-work-order-card__info">
          <span className="flex items-center gap-1">
            <Factory size={14} />
            {workOrder.work_center_name || workOrder.work_center_code || 'Non assigne'}
          </span>
          <span className="flex items-center gap-1">
            <Clock size={14} />
            {formatDuration(workOrder.duration_planned)}
            {workOrder.duration_actual > 0 && (
              <span className={isOvertime ? 'text-danger' : 'text-success'}>
                ({formatDuration(workOrder.duration_actual)})
              </span>
            )}
          </span>
          {workOrder.operator_name && (
            <span className="flex items-center gap-1">
              <User size={14} />
              {workOrder.operator_name}
            </span>
          )}
        </div>

        {workOrder.start_time && (
          <div className="azals-work-order-card__times text-sm text-muted">
            Debut: {formatDateTime(workOrder.start_time)}
            {workOrder.end_time && <span> - Fin: {formatDateTime(workOrder.end_time)}</span>}
          </div>
        )}

        {isOvertime && workOrder.status !== 'DONE' && (
          <div className="azals-work-order-card__alert mt-2">
            <AlertTriangle size={14} className="text-warning" />
            <span className="text-sm text-warning">Depassement du temps prevu</span>
          </div>
        )}
      </div>

      {workOrder.status === 'READY' && (
        <div className="azals-work-order-card__actions">
          <Button size="sm" leftIcon={<Play size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'startWorkOrder', workOrderId: workOrder.id } })); }}>Demarrer</Button>
        </div>
      )}
      {workOrder.status === 'IN_PROGRESS' && (
        <div className="azals-work-order-card__actions">
          <Button size="sm" variant="secondary" leftIcon={<Pause size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'pauseWorkOrder', workOrderId: workOrder.id } })); }}>Pause</Button>
          <Button size="sm" leftIcon={<CheckCircle size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'completeWorkOrder', workOrderId: workOrder.id } })); }}>Terminer</Button>
        </div>
      )}
    </div>
  );
};

export default OrderOperationsTab;
