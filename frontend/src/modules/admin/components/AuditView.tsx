/**
 * AZALSCORE Module - Admin - AuditView
 * Vue du journal d'audit
 */

import React, { useState } from 'react';
import { Card } from '@ui/layout';
import { Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { AuditLog } from '../types';
import { useAuditLogs } from '../hooks';

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const AuditView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const { data: logs = [], isLoading } = useAuditLogs({
    resource_type: filterType || undefined
  });

  const resourceTypes = [...new Set(logs.map(l => l.resource_type))].map(t => ({ value: t, label: t }));

  const columns: TableColumn<AuditLog>[] = [
    { id: 'timestamp', header: 'Date', accessor: 'timestamp', render: (v) => formatDateTime(v as string) },
    { id: 'user_name', header: 'Utilisateur', accessor: 'user_name', render: (v) => (v as string) || 'Systeme' },
    { id: 'action', header: 'Action', accessor: 'action' },
    { id: 'resource_type', header: 'Type', accessor: 'resource_type', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'resource_id', header: 'ID Ressource', accessor: 'resource_id', render: (v) => (v as string) ? <code className="font-mono text-xs">{v as string}</code> : '-' },
    { id: 'ip_address', header: 'IP', accessor: 'ip_address', render: (v) => (v as string) || '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Journal d&apos;audit</h3>
        <Select
          value={filterType}
          onChange={(val) => setFilterType(val)}
          options={[{ value: '', label: 'Tous les types' }, ...resourceTypes]}
          className="w-48"
        />
      </div>
      <DataTable columns={columns} data={logs} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

export default AuditView;
