/**
 * AZALSCORE Module - Country Packs France - DSN View
 * Vue Declaration Sociale Nominative
 */

import React, { useState } from 'react';
import { Upload } from 'lucide-react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatCurrency } from '@/utils/formatters';
import { useDSNDeclarations, useSubmitDSN } from '../hooks';
import { DSN_STATUS } from '../constants';
import { Badge } from './LocalComponents';
import type { DSNDeclaration } from '../api';

export const DSNView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: declarations = [], isLoading, error, refetch } = useDSNDeclarations({
    status: filterStatus || undefined
  });
  const submitDSN = useSubmitDSN();

  const columns: TableColumn<DSNDeclaration>[] = [
    { id: 'dsn_number', header: 'Reference', accessor: 'dsn_number', render: (v) => <code className="font-mono font-bold">{v as string}</code> },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period_month',
      render: (_, row) => <Badge color="blue">{`${String(row.period_month).padStart(2, '0')}/${row.period_year}`}</Badge>
    },
    {
      id: 'dsn_type',
      header: 'Type',
      accessor: 'dsn_type',
      render: (v) => <Badge color={(v as string) === 'MENSUELLE' ? 'green' : 'orange'}>{v as string}</Badge>
    },
    { id: 'employees_count', header: 'Salaries', accessor: 'employees_count', align: 'right' },
    { id: 'total_brut', header: 'Brut total', accessor: 'total_brut', align: 'right', render: (v) => formatCurrency(v as number) },
    { id: 'total_cotisations', header: 'Cotisations', accessor: 'total_cotisations', align: 'right', render: (v) => formatCurrency(v as number) },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = DSN_STATUS.find(s => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'READY' && (
            <Button size="sm" variant="primary" onClick={() => submitDSN.mutate(row.id)}>
              <Upload size={14} className="mr-1" />
              Soumettre
            </Button>
          )}
          <Button size="sm" variant="secondary">Detail</Button>
        </div>
      )
    }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Declarations Sociales Nominatives (DSN)</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...DSN_STATUS]}
            className="w-36"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createDSN' } })); }}>
            Nouvelle DSN
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={declarations}
        isLoading={isLoading}
        keyField="id"
        filterable
        error={error instanceof Error ? error : null}
        onRetry={() => refetch()}
      />
    </Card>
  );
};

export default DSNView;
