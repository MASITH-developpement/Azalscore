/**
 * AZALSCORE Module - Audit - Benchmarks Page
 * Liste des benchmarks
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw, Play, Eye, CheckCircle, XCircle } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { useBenchmarks, useRunBenchmark } from '../hooks';
import { BENCHMARK_STATUS_CONFIG } from '../types';
import type { Benchmark } from '../types';

export const BenchmarksPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useBenchmarks();
  const runBenchmark = useRunBenchmark();

  const columns: TableColumn<Benchmark>[] = [
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
      id: 'benchmark_type',
      header: 'Type',
      accessor: 'benchmark_type',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = BENCHMARK_STATUS_CONFIG[value as keyof typeof BENCHMARK_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'last_run_at',
      header: 'Dernier run',
      accessor: 'last_run_at',
      render: (value) => (value ? formatDate(value as string) : 'Jamais'),
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <XCircle size={16} className="azals-text--gray" />
        ),
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
            onClick={() => navigate(`/audit/benchmarks/${row.id}`)}
          >
            <Eye size={14} />
          </Button>
          <CapabilityGuard capability="audit.benchmarks.execute">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => runBenchmark.mutate(row.id)}
              disabled={runBenchmark.isPending || row.status === 'RUNNING'}
            >
              <Play size={14} />
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Benchmarks"
      subtitle="Tests de performance et securite"
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
          <CapabilityGuard capability="audit.benchmarks.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/audit/benchmarks/new')}>
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
          emptyMessage="Aucun benchmark"
        />
      </Card>
    </PageWrapper>
  );
};

export default BenchmarksPage;
