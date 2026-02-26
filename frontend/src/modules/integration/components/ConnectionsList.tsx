/**
 * AZALS MODULE GAP-086 - Integration Hub - Connections List
 * Liste des connexions actives
 */

import React, { useState } from 'react';
import { Search, Plus, Activity, Eye, Trash2 } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { ConnectionListItem, ConnectionStatus, HealthStatus } from '../types';
import { useConnections, useDeleteConnection, useTestConnection } from '../hooks';
import { ConnectionStatusBadge, HealthStatusBadge } from './StatusBadges';

export interface ConnectionsListProps {
  onSelectConnection: (id: string) => void;
  onCreateConnection: () => void;
  onBack: () => void;
}

export const ConnectionsList: React.FC<ConnectionsListProps> = ({
  onSelectConnection,
  onCreateConnection,
  onBack,
}) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, refetch } = useConnections(page, pageSize, {
    search: searchQuery || undefined,
    status: statusFilter || undefined,
  });

  const deleteConnection = useDeleteConnection();
  const testConnection = useTestConnection();

  const handleDelete = async (id: string) => {
    if (window.confirm('Supprimer cette connexion ?')) {
      await deleteConnection.mutateAsync(id);
    }
  };

  const handleTest = async (id: string) => {
    await testConnection.mutateAsync(id);
  };

  const columns: TableColumn<ConnectionListItem>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectConnection(row.id)}>
          {value as string}
        </span>
      ),
    },
    {
      id: 'connector_type',
      header: 'Connecteur',
      accessor: 'connector_type',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <ConnectionStatusBadge status={value as ConnectionStatus} />,
    },
    {
      id: 'health_status',
      header: 'Sante',
      accessor: 'health_status',
      render: (value) => <HealthStatusBadge status={value as HealthStatus} />,
    },
    {
      id: 'last_connected_at',
      header: 'Derniere connexion',
      accessor: 'last_connected_at',
      render: (value) => value ? formatDate(value as string) : '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      width: '120px',
      render: (_, row) => (
        <div className="azals-table-actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { handleTest(row.id); }}
          >
            <Activity size={14} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { onSelectConnection(row.id); }}
          >
            <Eye size={14} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { handleDelete(row.id); }}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Connexions"
      subtitle="Gerez vos integrations actives"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={onCreateConnection}>
          Nouvelle connexion
        </Button>
      }
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="azals-input"
            />
          </div>
          <select
            className="azals-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="connected">Connecte</option>
            <option value="disconnected">Deconnecte</option>
            <option value="error">En erreur</option>
            <option value="expired">Expire</option>
          </select>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucune connexion"
        />
      </Card>
    </PageWrapper>
  );
};

export default ConnectionsList;
