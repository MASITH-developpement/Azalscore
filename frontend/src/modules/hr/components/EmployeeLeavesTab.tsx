/**
 * AZALSCORE Module - HR - Employee Leaves Tab
 * Onglet conges et absences de l'employe
 */

import React from 'react';
import {
  Calendar, Clock, CheckCircle, XCircle, AlertCircle,
  Sun, Thermometer, Baby, CalendarDays
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee, LeaveRequest, LeaveBalance, LeaveType } from '../types';
import {
  formatDate,
  LEAVE_TYPE_CONFIG, LEAVE_STATUS_CONFIG,
  getRemainingLeave, getTotalRemainingLeave, getPendingLeaveRequests
} from '../types';

/**
 * EmployeeLeavesTab - Conges et absences
 */
export const EmployeeLeavesTab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const balances = employee.leave_balances || [];
  const requests = employee.leave_requests || [];
  const pendingRequests = getPendingLeaveRequests(employee);

  // Demandes recentes (dernieres 10)
  const recentRequests = [...requests]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10);

  return (
    <div className="azals-std-tab-content">
      {/* Resume des soldes */}
      <div className="azals-leave-summary mb-4">
        <Grid cols={4} gap="md">
          <div className="azals-stat-mini azals-stat-mini--primary">
            <span className="azals-stat-mini__value">{getTotalRemainingLeave(employee)}</span>
            <span className="azals-stat-mini__label">Jours restants</span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">{getRemainingLeave(employee, 'PAID')}</span>
            <span className="azals-stat-mini__label">Conges payes</span>
          </div>
          <div className="azals-stat-mini azals-stat-mini--warning">
            <span className="azals-stat-mini__value">{pendingRequests.length}</span>
            <span className="azals-stat-mini__label">En attente</span>
          </div>
          <div className="azals-stat-mini">
            <span className="azals-stat-mini__value">
              {requests.filter(r => r.status === 'APPROVED').reduce((sum, r) => sum + r.days, 0)}
            </span>
            <span className="azals-stat-mini__label">Jours pris</span>
          </div>
        </Grid>
      </div>

      <Grid cols={2} gap="lg">
        {/* Soldes de conges */}
        <Card title="Soldes de conges" icon={<Calendar size={18} />}>
          {balances.length > 0 ? (
            <div className="azals-leave-balances">
              {balances.map((balance, index) => (
                <LeaveBalanceItem key={index} balance={balance} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Calendar size={32} className="text-muted" />
              <p className="text-muted">Aucun solde de conges</p>
            </div>
          )}
        </Card>

        {/* Demandes en attente */}
        <Card title="Demandes en attente" icon={<Clock size={18} />}>
          {pendingRequests.length > 0 ? (
            <div className="azals-leave-requests">
              {pendingRequests.map((request) => (
                <LeaveRequestItem key={request.id} request={request} showActions />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CheckCircle size={32} className="text-success" />
              <p className="text-muted">Aucune demande en attente</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Historique des demandes */}
      <Card title="Historique des demandes" icon={<CalendarDays size={18} />} className="mt-4">
        {recentRequests.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Type</th>
                <th>Du</th>
                <th>Au</th>
                <th>Jours</th>
                <th>Statut</th>
                <th>Motif</th>
              </tr>
            </thead>
            <tbody>
              {recentRequests.map((request) => {
                const typeConfig = LEAVE_TYPE_CONFIG[request.type];
                const statusConfig = LEAVE_STATUS_CONFIG[request.status];
                return (
                  <tr key={request.id}>
                    <td>
                      <span className={`azals-badge azals-badge--${typeConfig.color} azals-badge--sm`}>
                        {typeConfig.label}
                      </span>
                    </td>
                    <td>{formatDate(request.start_date)}</td>
                    <td>{formatDate(request.end_date)}</td>
                    <td className="text-center">{request.days}</td>
                    <td>
                      <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="text-muted">{request.reason || '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Calendar size={32} className="text-muted" />
            <p className="text-muted">Aucune demande de conge</p>
          </div>
        )}
      </Card>

      {/* Actions */}
      <div className="azals-std-tab-actions mt-4">
        <Button variant="primary" leftIcon={<Calendar size={16} />}>
          Nouvelle demande de conge
        </Button>
      </div>
    </div>
  );
};

/**
 * Composant solde de conge
 */
interface LeaveBalanceItemProps {
  balance: LeaveBalance;
}

const LeaveBalanceItem: React.FC<LeaveBalanceItemProps> = ({ balance }) => {
  const config = LEAVE_TYPE_CONFIG[balance.type];
  const progress = balance.entitled > 0 ? ((balance.entitled - balance.remaining) / balance.entitled) * 100 : 0;

  const getIcon = () => {
    switch (balance.type) {
      case 'PAID':
        return <Sun size={16} />;
      case 'SICK':
        return <Thermometer size={16} />;
      case 'MATERNITY':
      case 'PATERNITY':
        return <Baby size={16} />;
      default:
        return <Calendar size={16} />;
    }
  };

  return (
    <div className="azals-leave-balance-item">
      <div className="azals-leave-balance-item__header">
        <span className={`azals-leave-balance-item__icon text-${config.color}`}>
          {getIcon()}
        </span>
        <span className="azals-leave-balance-item__label">{balance.type_label || config.label}</span>
        <span className="azals-leave-balance-item__remaining font-semibold">
          {balance.remaining} j
        </span>
      </div>
      <div className="azals-progress azals-progress--sm mt-1">
        <div
          className={`azals-progress__bar azals-progress__bar--${config.color}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      <div className="azals-leave-balance-item__details text-sm text-muted mt-1">
        <span>Acquis: {balance.entitled}j</span>
        <span className="mx-2">.</span>
        <span>Pris: {balance.taken}j</span>
        {balance.pending > 0 && (
          <>
            <span className="mx-2">.</span>
            <span className="text-warning">En attente: {balance.pending}j</span>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Composant demande de conge
 */
interface LeaveRequestItemProps {
  request: LeaveRequest;
  showActions?: boolean;
}

const LeaveRequestItem: React.FC<LeaveRequestItemProps> = ({ request, showActions }) => {
  const typeConfig = LEAVE_TYPE_CONFIG[request.type];
  const statusConfig = LEAVE_STATUS_CONFIG[request.status];

  return (
    <div className={`azals-leave-request-item azals-leave-request-item--${request.status.toLowerCase()}`}>
      <div className="azals-leave-request-item__header">
        <span className={`azals-badge azals-badge--${typeConfig.color}`}>
          {typeConfig.label}
        </span>
        <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
          {statusConfig.label}
        </span>
      </div>
      <div className="azals-leave-request-item__dates">
        <Calendar size={14} className="mr-1" />
        {formatDate(request.start_date)} - {formatDate(request.end_date)}
        <span className="font-semibold ml-2">({request.days} jours)</span>
      </div>
      {request.reason && (
        <div className="azals-leave-request-item__reason text-sm text-muted mt-1">
          {request.reason}
        </div>
      )}
      {showActions && request.status === 'PENDING' && (
        <div className="azals-leave-request-item__actions mt-2">
          <Button size="sm" variant="ghost">Modifier</Button>
          <Button size="sm" variant="danger">Annuler</Button>
        </div>
      )}
    </div>
  );
};

export default EmployeeLeavesTab;
