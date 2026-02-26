/**
 * AZALSCORE Module - Triggers - Recent Events List
 * Liste des evenements recents
 */

import React from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '@ui/actions';
import { formatDate } from '@/utils/formatters';
import { ALERT_SEVERITY_CONFIG } from '../types';
import type { TriggerEvent } from '../types';
import { useResolveEvent } from '../hooks';

export interface RecentEventsListProps {
  events: TriggerEvent[];
}

export const RecentEventsList: React.FC<RecentEventsListProps> = ({ events }) => {
  const resolveEvent = useResolveEvent();

  if (events.length === 0) {
    return <p className="azals-text--muted">Aucun evenement recent</p>;
  }

  return (
    <div className="azals-events-list">
      {events.map((event) => {
        const severityConfig = ALERT_SEVERITY_CONFIG[event.severity];
        return (
          <div key={event.id} className="azals-event-item">
            <div
              className="azals-event-item__severity"
              style={{ backgroundColor: `var(--color-${severityConfig.color}-100)` }}
            >
              <AlertTriangle
                size={16}
                style={{ color: `var(--color-${severityConfig.color}-600)` }}
              />
            </div>
            <div className="azals-event-item__content">
              <div className="azals-event-item__header">
                <span className={`azals-badge azals-badge--${severityConfig.color}`}>
                  {severityConfig.label}
                </span>
                <span className="azals-text--muted">{formatDate(event.triggered_at)}</span>
              </div>
              <p className="azals-event-item__value">
                {event.triggered_value || 'Declenchement automatique'}
              </p>
            </div>
            <div className="azals-event-item__actions">
              {event.resolved ? (
                <span className="azals-badge azals-badge--green">
                  <CheckCircle size={12} /> Resolu
                </span>
              ) : (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => resolveEvent.mutate({ id: event.id })}
                  disabled={resolveEvent.isPending}
                >
                  Resoudre
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RecentEventsList;
