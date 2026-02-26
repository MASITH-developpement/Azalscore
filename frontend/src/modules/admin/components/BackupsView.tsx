/**
 * AZALSCORE Module - Admin - BackupsView
 * Vue de gestion des sauvegardes
 */

import React from 'react';
import { Card } from '@ui/layout';
import { Button } from '@ui/actions';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { BackupConfig } from '../types';
import { useBackupConfigs, useRunBackup } from '../hooks';

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const BACKUP_TYPES = [
  { value: 'FULL', label: 'Complete' },
  { value: 'INCREMENTAL', label: 'Incrementale' },
  { value: 'DIFFERENTIAL', label: 'Differentielle' }
];

const BACKUP_DESTINATIONS = [
  { value: 'LOCAL', label: 'Local' },
  { value: 'S3', label: 'AWS S3' },
  { value: 'GCS', label: 'Google Cloud' },
  { value: 'AZURE', label: 'Azure Blob' }
];

const BackupsView: React.FC = () => {
  const { data: backups = [], isLoading } = useBackupConfigs();
  const runBackup = useRunBackup();

  const columns: TableColumn<BackupConfig>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = BACKUP_TYPES.find(t => t.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'schedule', header: 'Planification', accessor: 'schedule' },
    { id: 'destination', header: 'Destination', accessor: 'destination', render: (v) => {
      const info = BACKUP_DESTINATIONS.find(d => d.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'retention_days', header: 'Retention', accessor: 'retention_days', render: (v) => `${v as number} jours` },
    { id: 'last_backup', header: 'Derniere', accessor: 'last_backup', render: (v) => (v as string) ? formatDateTime(v as string) : '-' },
    { id: 'last_status', header: 'Statut', accessor: 'last_status', render: (v) => {
      if (!v) return '-';
      const colors: Record<string, string> = { SUCCESS: 'green', FAILED: 'red', IN_PROGRESS: 'orange' };
      return <Badge color={colors[v as string] || 'gray'}>{v as string}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      (row as BackupConfig).is_active ? (
        <Button size="sm" onClick={() => runBackup.mutate((row as BackupConfig).id)}>Lancer</Button>
      ) : null
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Sauvegardes</h3>
        <Button>Nouvelle config</Button>
      </div>
      <DataTable columns={columns} data={backups} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

export default BackupsView;
