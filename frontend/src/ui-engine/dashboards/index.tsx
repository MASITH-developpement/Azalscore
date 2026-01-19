/**
 * AZALSCORE UI Engine - Dashboard System
 * Composants de tableaux de bord avec KPIs et alertes
 * Données fournies par API - AUCUNE logique métier
 */

import React from 'react';
import { clsx } from 'clsx';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Bell,
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import type { DashboardKPI, DashboardWidget, Alert, AlertSeverity } from '@/types';

// ============================================================
// KPI CARD
// ============================================================

interface KPICardProps {
  kpi: DashboardKPI;
  onClick?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({ kpi, onClick }) => {
  const TrendIcon =
    kpi.trend === 'up'
      ? TrendingUp
      : kpi.trend === 'down'
      ? TrendingDown
      : Minus;

  const trendColor =
    kpi.trend === 'up'
      ? 'text-green-600'
      : kpi.trend === 'down'
      ? 'text-red-600'
      : 'text-gray-500';

  return (
    <div
      className={clsx('azals-kpi-card', {
        'azals-kpi-card--clickable': !!onClick,
        [`azals-kpi-card--${kpi.severity?.toLowerCase()}`]: kpi.severity,
      })}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="azals-kpi-card__header">
        <span className="azals-kpi-card__label">{kpi.label}</span>
        {kpi.period && <span className="azals-kpi-card__period">{kpi.period}</span>}
      </div>

      <div className="azals-kpi-card__value">
        <span className="azals-kpi-card__number">{kpi.value}</span>
        {kpi.unit && <span className="azals-kpi-card__unit">{kpi.unit}</span>}
      </div>

      {kpi.trend && (
        <div className={clsx('azals-kpi-card__trend', trendColor)}>
          <TrendIcon size={16} />
          {kpi.trend_value !== undefined && (
            <span>
              {kpi.trend_value > 0 ? '+' : ''}
              {kpi.trend_value}%
            </span>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================
// KPI GRID
// ============================================================

interface KPIGridProps {
  kpis: DashboardKPI[];
  columns?: 2 | 3 | 4;
  onKPIClick?: (kpi: DashboardKPI) => void;
}

export const KPIGrid: React.FC<KPIGridProps> = ({
  kpis,
  columns = 4,
  onKPIClick,
}) => {
  return (
    <div className={clsx('azals-kpi-grid', `azals-kpi-grid--cols-${columns}`)}>
      {kpis.map((kpi) => (
        <KPICard
          key={kpi.id}
          kpi={kpi}
          onClick={onKPIClick ? () => onKPIClick(kpi) : undefined}
        />
      ))}
    </div>
  );
};

// ============================================================
// ALERT CARD
// ============================================================

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (alert: Alert) => void;
  onAction?: (alert: Alert) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onAction,
}) => {
  const Icon =
    alert.severity === 'RED'
      ? AlertCircle
      : alert.severity === 'ORANGE'
      ? AlertTriangle
      : CheckCircle;

  return (
    <div
      className={clsx(
        'azals-alert-card',
        `azals-alert-card--${alert.severity.toLowerCase()}`,
        {
          'azals-alert-card--acknowledged': alert.acknowledged,
        }
      )}
    >
      <div className="azals-alert-card__icon">
        <Icon size={20} />
      </div>

      <div className="azals-alert-card__content">
        <div className="azals-alert-card__header">
          <span className="azals-alert-card__title">{alert.title}</span>
          <span className="azals-alert-card__module">{alert.module}</span>
        </div>
        <p className="azals-alert-card__message">{alert.message}</p>
        <span className="azals-alert-card__time">
          {new Date(alert.created_at).toLocaleString('fr-FR')}
        </span>
      </div>

      <div className="azals-alert-card__actions">
        {alert.requires_action && onAction && !alert.acknowledged && (
          <button
            className="azals-btn azals-btn--sm azals-btn--primary"
            onClick={() => onAction(alert)}
          >
            Action
            <ArrowRight size={14} />
          </button>
        )}
        {onAcknowledge && !alert.acknowledged && (
          <button
            className="azals-btn azals-btn--sm azals-btn--ghost"
            onClick={() => onAcknowledge(alert)}
          >
            Acquitter
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================
// ALERT LIST
// ============================================================

interface AlertListProps {
  alerts: Alert[];
  maxItems?: number;
  onAcknowledge?: (alert: Alert) => void;
  onAction?: (alert: Alert) => void;
  onViewAll?: () => void;
  emptyMessage?: string;
}

export const AlertList: React.FC<AlertListProps> = ({
  alerts,
  maxItems,
  onAcknowledge,
  onAction,
  onViewAll,
  emptyMessage = 'Aucune alerte',
}) => {
  const displayedAlerts = maxItems ? alerts.slice(0, maxItems) : alerts;
  const hasMore = maxItems && alerts.length > maxItems;

  return (
    <div className="azals-alert-list">
      {displayedAlerts.length === 0 ? (
        <div className="azals-alert-list__empty">
          <Bell size={24} />
          <span>{emptyMessage}</span>
        </div>
      ) : (
        <>
          <div className="azals-alert-list__items">
            {displayedAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={onAcknowledge}
                onAction={onAction}
              />
            ))}
          </div>
          {hasMore && onViewAll && (
            <button
              className="azals-alert-list__view-all azals-btn azals-btn--ghost"
              onClick={onViewAll}
            >
              Voir toutes les alertes ({alerts.length})
            </button>
          )}
        </>
      )}
    </div>
  );
};

// ============================================================
// SEVERITY BADGE
// ============================================================

interface SeverityBadgeProps {
  severity: AlertSeverity;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = 'md',
  pulse,
}) => {
  return (
    <span
      className={clsx(
        'azals-severity-badge',
        `azals-severity-badge--${severity.toLowerCase()}`,
        `azals-severity-badge--${size}`,
        {
          'azals-severity-badge--pulse': pulse,
        }
      )}
    >
      {severity}
    </span>
  );
};

// ============================================================
// DASHBOARD WIDGET
// ============================================================

interface WidgetContainerProps {
  widget: DashboardWidget;
  children: React.ReactNode;
}

export const WidgetContainer: React.FC<WidgetContainerProps> = ({
  widget,
  children,
}) => {
  return (
    <CapabilityGuard capability={widget.capability}>
      <div className={clsx('azals-widget', `azals-widget--${widget.type}`)}>
        <div className="azals-widget__header">
          <h3 className="azals-widget__title">{widget.title}</h3>
        </div>
        <div className="azals-widget__body">{children}</div>
      </div>
    </CapabilityGuard>
  );
};

// ============================================================
// STATUS INDICATOR
// ============================================================

interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  label?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
}) => {
  return (
    <div className={clsx('azals-status', `azals-status--${status}`)}>
      <span className="azals-status__dot" />
      {label && <span className="azals-status__label">{label}</span>}
    </div>
  );
};

// ============================================================
// METRIC COMPARISON
// ============================================================

interface MetricComparisonProps {
  label: string;
  current: number;
  previous: number;
  unit?: string;
  format?: 'number' | 'currency' | 'percent';
}

export const MetricComparison: React.FC<MetricComparisonProps> = ({
  label,
  current,
  previous,
  unit,
  format = 'number',
}) => {
  const diff = current - previous;
  const percentChange = previous !== 0 ? ((diff / previous) * 100).toFixed(1) : 0;
  const isPositive = diff > 0;
  const isNegative = diff < 0;

  const formatValue = (value: number): string => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('fr-FR', {
          style: 'currency',
          currency: 'EUR',
        }).format(value);
      case 'percent':
        return `${value.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('fr-FR').format(value);
    }
  };

  return (
    <div className="azals-metric-comparison">
      <span className="azals-metric-comparison__label">{label}</span>
      <div className="azals-metric-comparison__values">
        <span className="azals-metric-comparison__current">
          {formatValue(current)}
          {unit && <span className="azals-metric-comparison__unit">{unit}</span>}
        </span>
        <span
          className={clsx('azals-metric-comparison__change', {
            'azals-metric-comparison__change--positive': isPositive,
            'azals-metric-comparison__change--negative': isNegative,
          })}
        >
          {isPositive ? '+' : ''}
          {percentChange}%
          {isPositive ? <TrendingUp size={14} /> : isNegative ? <TrendingDown size={14} /> : null}
        </span>
      </div>
      <span className="azals-metric-comparison__previous">
        vs. {formatValue(previous)} (période précédente)
      </span>
    </div>
  );
};

// ============================================================
// PROGRESS BAR
// ============================================================

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showValue = true,
  variant = 'default',
}) => {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="azals-progress">
      {(label || showValue) && (
        <div className="azals-progress__header">
          {label && <span className="azals-progress__label">{label}</span>}
          {showValue && (
            <span className="azals-progress__value">
              {value} / {max}
            </span>
          )}
        </div>
      )}
      <div className="azals-progress__track">
        <div
          className={clsx('azals-progress__bar', `azals-progress__bar--${variant}`)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// ============================================================
// STATUS BADGE (alias pour compatibilité)
// ============================================================

interface StatusBadgeProps {
  status?: string;
  children?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'default';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  children,
  size = 'md',
  variant = 'default',
}) => {
  return (
    <span
      className={clsx(
        'azals-status-badge',
        `azals-status-badge--${variant}`,
        `azals-status-badge--${size}`
      )}
    >
      {children ?? status}
    </span>
  );
};

// ============================================================
// STAT CARD
// ============================================================

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  variant = 'default',
  onClick,
}) => {
  const TrendIcon =
    trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  return (
    <div
      className={clsx('azals-stat-card', `azals-stat-card--${variant}`, {
        'azals-stat-card--clickable': !!onClick,
      })}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
    >
      {icon && <div className="azals-stat-card__icon">{icon}</div>}
      <div className="azals-stat-card__content">
        <span className="azals-stat-card__title">{title}</span>
        <span className="azals-stat-card__value">{value}</span>
        {subtitle && <span className="azals-stat-card__subtitle">{subtitle}</span>}
      </div>
      {trend && (
        <div className={clsx('azals-stat-card__trend', `azals-stat-card__trend--${trend}`)}>
          <TrendIcon size={16} />
          {trendValue !== undefined && <span>{trendValue}%</span>}
        </div>
      )}
    </div>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default {
  KPICard,
  KPIGrid,
  AlertCard,
  AlertList,
  SeverityBadge,
  StatusBadge,
  StatCard,
  WidgetContainer,
  StatusIndicator,
  MetricComparison,
  ProgressBar,
};
