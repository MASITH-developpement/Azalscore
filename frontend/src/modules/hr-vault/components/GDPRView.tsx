/**
 * AZALSCORE Module - HR Vault - GDPR View
 * Gestion des demandes RGPD
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, RefreshCw } from 'lucide-react';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { hrVaultApi } from '../api';
import { useGDPRRequests, hrVaultKeys } from '../hooks';
import { GDPR_TYPE_CONFIG, GDPR_STATUS_CONFIG } from '../types';
import type { VaultGDPRRequest } from '../types';
import { Badge } from './LocalComponents';

export const GDPRView: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const { data: requests = [], isLoading, refetch } = useGDPRRequests(statusFilter || undefined);
  const queryClient = useQueryClient();

  const processRequestMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      await hrVaultApi.processGDPRRequest(id, status);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: hrVaultKeys.gdpr() });
    },
  });

  const columns: TableColumn<VaultGDPRRequest>[] = [
    {
      id: 'code',
      header: 'Reference',
      accessor: 'request_code',
      render: (v) => <code className="font-mono">{v as string}</code>,
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'request_type',
      render: (type) => {
        const config = GDPR_TYPE_CONFIG[type as keyof typeof GDPR_TYPE_CONFIG];
        return <Badge color={config?.color || 'gray'}>{config?.label || String(type)}</Badge>;
      },
    },
    {
      id: 'employee',
      header: 'Employe',
      accessor: 'employee_name',
      render: (name) => String(name || '-'),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (status) => {
        const config = GDPR_STATUS_CONFIG[status as keyof typeof GDPR_STATUS_CONFIG];
        return <Badge color={config?.color || 'gray'}>{config?.label || String(status)}</Badge>;
      },
    },
    {
      id: 'requested_at',
      header: 'Date demande',
      accessor: 'requested_at',
      render: (date) => formatDate(date as string),
    },
    {
      id: 'due_date',
      header: 'Echeance',
      accessor: 'due_date',
      render: (date, row) => {
        const isOverdue = new Date(date as string) < new Date() && row.status === 'PENDING';
        return (
          <span className={isOverdue ? 'text-red-600 font-bold' : ''}>
            {formatDate(date as string)}
          </span>
        );
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          {row.status === 'PENDING' && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => processRequestMutation.mutate({ id: row.id, status: 'PROCESSING' })}
            >
              Traiter
            </Button>
          )}
          {row.status === 'PROCESSING' && (
            <Button
              size="sm"
              variant="success"
              onClick={() => processRequestMutation.mutate({ id: row.id, status: 'COMPLETED' })}
            >
              Terminer
            </Button>
          )}
        </div>
      ),
    },
  ];

  const statusOptions = [
    { value: '', label: 'Tous les statuts' },
    ...Object.entries(GDPR_STATUS_CONFIG).map(([value, config]) => ({
      value,
      label: config.label,
    })),
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Shield size={20} />
          Demandes RGPD
        </h3>
        <div className="flex gap-2">
          <Select
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
            options={statusOptions}
            className="w-40"
          />
          <Button variant="secondary" onClick={() => { void refetch(); }}>
            <RefreshCw size={16} />
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={requests}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

export default GDPRView;
