/**
 * AZALSCORE Module - Triggers - Scheduled Reports Page
 * Rapports planifies
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { REPORT_FREQUENCY_LABELS } from '../types';
import type { ScheduledReport } from '../types';
import { useScheduledReports } from '../hooks';

export const ScheduledReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [includeInactive, setIncludeInactive] = useState(false);
  const { data, isLoading, error, refetch } = useScheduledReports(includeInactive);

  const columns: TableColumn<ScheduledReport>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'frequency',
      header: 'Frequence',
      accessor: 'frequency',
      render: (value) => REPORT_FREQUENCY_LABELS[value as keyof typeof REPORT_FREQUENCY_LABELS],
    },
    {
      id: 'output_format',
      header: 'Format',
      accessor: 'output_format',
    },
    {
      id: 'generation_count',
      header: 'Generations',
      accessor: 'generation_count',
      align: 'right',
    },
    {
      id: 'next_generation_at',
      header: 'Prochaine',
      accessor: 'next_generation_at',
      render: (value) => (value ? formatDate(value as string) : '-'),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  return (
    <PageWrapper
      title="Rapports planifies"
      subtitle="Rapports periodiques automatiques"
      actions={
        <ButtonGroup>
          <Button
            variant={includeInactive ? 'secondary' : 'ghost'}
            onClick={() => setIncludeInactive(!includeInactive)}
          >
            {includeInactive ? 'Masquer inactifs' : 'Afficher inactifs'}
          </Button>
          <CapabilityGuard capability="triggers.reports.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/reports/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun rapport planifie"
        />
      </Card>
    </PageWrapper>
  );
};

export default ScheduledReportsPage;
