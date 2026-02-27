/**
 * AZALSCORE Module - Country Packs France - TVA View
 * Vue TVA (taux et declarations)
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate, formatCurrency } from '@/utils/formatters';
import { useVATRates, useVATDeclarations, useCalculateVATDeclaration } from '../hooks';
import { VAT_DECLARATION_STATUS } from '../constants';
import { Badge } from './LocalComponents';
import type { FRVATRate, VATDeclaration } from '../api';

export const TVAView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: rates = [] } = useVATRates();
  const { data: declarations = [], isLoading, error, refetch } = useVATDeclarations({
    status: filterStatus || undefined
  });
  const calculateDeclaration = useCalculateVATDeclaration();

  const ratesColumns: TableColumn<FRVATRate>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Libelle', accessor: 'name' },
    {
      id: 'rate',
      header: 'Taux',
      accessor: 'rate',
      align: 'right',
      render: (v) => <span className="font-bold">{(v as number).toFixed(1)}%</span>
    },
    {
      id: 'rate_type',
      header: 'Type',
      accessor: 'rate_type',
      render: (v) => {
        const typeColors: Record<string, string> = {
          NORMAL: 'blue',
          REDUCED: 'green',
          SUPER_REDUCED: 'purple',
          ZERO: 'gray',
          EXEMPT: 'orange'
        };
        return <Badge color={typeColors[v as string] || 'gray'}>{v as string}</Badge>;
      }
    }
  ];

  const declarationsColumns: TableColumn<VATDeclaration>[] = [
    { id: 'declaration_number', header: 'Reference', accessor: 'declaration_number', render: (v) => <code className="font-mono">{v as string}</code> },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period_start',
      render: (_, row) => `${formatDate(row.period_start)} - ${formatDate(row.period_end)}`
    },
    { id: 'regime', header: 'Regime', accessor: 'regime', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'total_tva_collectee', header: 'TVA Collectee', accessor: 'total_tva_collectee', align: 'right', render: (v) => formatCurrency(v as number) },
    { id: 'total_tva_deductible', header: 'TVA Deductible', accessor: 'total_tva_deductible', align: 'right', render: (v) => formatCurrency(v as number) },
    {
      id: 'tva_nette',
      header: 'TVA Nette',
      accessor: 'tva_nette',
      align: 'right',
      render: (v) => <span className="font-bold">{formatCurrency(v as number)}</span>
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const info = VAT_DECLARATION_STATUS.find((s: { value: string; label: string; color: string }) => s.value === v);
        return <Badge color={info?.color || 'gray'}>{info?.label || (v as string)}</Badge>;
      }
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'DRAFT' && (
            <Button size="sm" onClick={() => calculateDeclaration.mutate(row.id)}>
              Calculer
            </Button>
          )}
          <Button size="sm" variant="secondary">Detail</Button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Taux de TVA</h3>
        </div>
        <DataTable columns={ratesColumns} data={rates} keyField="id" />
      </Card>

      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Declarations de TVA</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatus}
              onChange={(v) => setFilterStatus(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...VAT_DECLARATION_STATUS]}
              className="w-36"
            />
            <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createVATDeclaration' } })); }}>
              Nouvelle declaration
            </Button>
          </div>
        </div>
        <DataTable
          columns={declarationsColumns}
          data={declarations}
          isLoading={isLoading}
          keyField="id"
          filterable
          error={error instanceof Error ? error : null}
          onRetry={() => refetch()}
        />
      </Card>
    </div>
  );
};

export default TVAView;
