/**
 * AZALSCORE Module - Country Packs France - PCG View
 * Vue Plan Comptable Général
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { usePCGAccounts } from '../hooks';
import { PCG_CLASSES } from '../constants';
import { Badge } from './LocalComponents';
import type { PCGAccount } from '../api';

export const PCGView: React.FC = () => {
  const [filterClass, setFilterClass] = useState<string>('');
  const { data: accounts = [], isLoading, error, refetch } = usePCGAccounts({
    pcg_class: filterClass || undefined
  });

  const columns: TableColumn<PCGAccount>[] = [
    {
      id: 'account_number',
      header: 'Numero',
      accessor: 'account_number',
      render: (v) => <code className="font-mono font-bold">{v as string}</code>
    },
    { id: 'account_label', header: 'Libelle', accessor: 'account_label' },
    {
      id: 'pcg_class',
      header: 'Classe',
      accessor: 'pcg_class',
      render: (v) => <Badge color="blue">Classe {v as string}</Badge>
    },
    { id: 'parent_account', header: 'Compte parent', accessor: 'parent_account', render: (v) => (v as string) || '-' },
    {
      id: 'normal_balance',
      header: 'Nature',
      accessor: 'normal_balance',
      render: (v) => <Badge color={(v as string) === 'D' ? 'orange' : 'green'}>{(v as string) === 'D' ? 'Debit' : 'Credit'}</Badge>
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    },
    {
      id: 'is_custom',
      header: 'Personnalise',
      accessor: 'is_custom',
      render: (v) => (v as boolean) ? <Badge color="purple">Custom</Badge> : <Badge color="gray">PCG</Badge>
    }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Plan Comptable General (PCG 2024)</h3>
        <div className="flex gap-2">
          <Select
            value={filterClass}
            onChange={(v) => setFilterClass(v)}
            options={[{ value: '', label: 'Toutes classes' }, ...PCG_CLASSES]}
            className="w-48"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createPCGAccount' } })); }}>
            Nouveau compte
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={accounts}
        isLoading={isLoading}
        keyField="id"
        filterable
        error={error instanceof Error ? error : null}
        onRetry={() => refetch()}
      />
    </Card>
  );
};

export default PCGView;
