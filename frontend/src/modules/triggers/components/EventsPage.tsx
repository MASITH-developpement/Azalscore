/**
 * AZALSCORE Module - Triggers - Events Page
 * Historique des evenements/declenchements
 */

import React, { useState } from 'react';
import { CheckCircle, RefreshCw } from 'lucide-react';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { ALERT_SEVERITY_CONFIG } from '../types';
import type { TriggerEvent } from '../types';
import { useEvents, useResolveEvent } from '../hooks';

export const EventsPage: React.FC = () => {
  const [showResolved, setShowResolved] = useState(false);
  const { data, isLoading, error, refetch } = useEvents({
    resolved: showResolved ? undefined : false,
    limit: 100,
  });
  const resolveEvent = useResolveEvent();

  const columns: TableColumn<TriggerEvent>[] = [
    {
      id: 'triggered_at',
      header: 'Date',
      accessor: 'triggered_at',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (value) => {
        const config = ALERT_SEVERITY_CONFIG[value as keyof typeof ALERT_SEVERITY_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'triggered_value',
      header: 'Valeur',
      accessor: 'triggered_value',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'escalation_level',
      header: 'Niveau',
      accessor: 'escalation_level',
    },
    {
      id: 'resolved',
      header: 'Statut',
      accessor: 'resolved',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">
            <CheckCircle size={12} /> Resolu
          </span>
        ) : (
          <span className="azals-badge azals-badge--orange">En cours</span>
        ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          {!row.resolved && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => resolveEvent.mutate({ id: row.id })}
              disabled={resolveEvent.isPending}
            >
              Resoudre
            </Button>
          )}
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Evenements"
      subtitle="Historique des declenchements"
      actions={
        <ButtonGroup>
          <Button
            variant={showResolved ? 'secondary' : 'ghost'}
            onClick={() => setShowResolved(!showResolved)}
          >
            {showResolved ? 'Masquer resolus' : 'Afficher resolus'}
          </Button>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.events || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun evenement"
        />
      </Card>
    </PageWrapper>
  );
};

export default EventsPage;
