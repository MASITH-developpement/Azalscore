/**
 * AZALSCORE Module - Triggers - List Page
 * Liste des triggers configures
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Pause, Play, Trash2 } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import {
  TRIGGER_TYPE_LABELS,
  TRIGGER_STATUS_CONFIG,
  ALERT_SEVERITY_CONFIG,
} from '../types';
import type { Trigger } from '../types';
import { useTriggers, usePauseTrigger, useResumeTrigger, useDeleteTrigger } from '../hooks';

export const TriggersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [includeInactive, setIncludeInactive] = useState(false);
  const { data, isLoading, error, refetch } = useTriggers({ include_inactive: includeInactive });
  const pauseTrigger = usePauseTrigger();
  const resumeTrigger = useResumeTrigger();
  const deleteTrigger = useDeleteTrigger();

  const columns: TableColumn<Trigger>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
    },
    {
      id: 'trigger_type',
      header: 'Type',
      accessor: 'trigger_type',
      render: (value) => TRIGGER_TYPE_LABELS[value as keyof typeof TRIGGER_TYPE_LABELS],
    },
    {
      id: 'source_module',
      header: 'Module source',
      accessor: 'source_module',
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
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = TRIGGER_STATUS_CONFIG[value as keyof typeof TRIGGER_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'trigger_count',
      header: 'Declenchements',
      accessor: 'trigger_count',
      align: 'right',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/triggers/${row.id}`)}
          >
            <Eye size={14} />
          </Button>
          {row.status === 'ACTIVE' ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => pauseTrigger.mutate(row.id)}
              disabled={pauseTrigger.isPending}
            >
              <Pause size={14} />
            </Button>
          ) : row.status === 'PAUSED' ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => resumeTrigger.mutate(row.id)}
              disabled={resumeTrigger.isPending}
            >
              <Play size={14} />
            </Button>
          ) : null}
          <CapabilityGuard capability="triggers.delete">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (window.confirm('Supprimer ce trigger ?')) {
                  deleteTrigger.mutate(row.id);
                }
              }}
              disabled={deleteTrigger.isPending}
            >
              <Trash2 size={14} />
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Triggers"
      subtitle="Liste des declencheurs configures"
      actions={
        <ButtonGroup>
          <Button
            variant={includeInactive ? 'secondary' : 'ghost'}
            onClick={() => setIncludeInactive(!includeInactive)}
          >
            {includeInactive ? 'Masquer inactifs' : 'Afficher inactifs'}
          </Button>
          <CapabilityGuard capability="triggers.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.triggers || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          onRowClick={(row) => navigate(`/triggers/${row.id}`)}
          emptyMessage="Aucun trigger configure"
        />
      </Card>
    </PageWrapper>
  );
};

export default TriggersListPage;
