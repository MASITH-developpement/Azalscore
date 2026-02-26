/**
 * AZALS MODULE GAP-086 - Integration Hub - Conflicts List
 * Liste des conflits de synchronisation
 */

import React, { useState } from 'react';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { SyncConflict } from '../types';
import { useConflicts } from '../hooks';

export interface ConflictsListProps {
  onBack: () => void;
}

export const ConflictsList: React.FC<ConflictsListProps> = ({ onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [showResolved, setShowResolved] = useState(false);

  const { data, isLoading, refetch } = useConflicts(page, pageSize, showResolved ? undefined : false);

  const columns: TableColumn<SyncConflict>[] = [
    {
      id: 'entity_type',
      header: 'Type',
      accessor: 'entity_type',
    },
    {
      id: 'source_id',
      header: 'Source',
      accessor: 'source_id',
    },
    {
      id: 'target_id',
      header: 'Cible',
      accessor: 'target_id',
    },
    {
      id: 'conflicting_fields',
      header: 'Champs en conflit',
      accessor: 'conflicting_fields',
      render: (v) => (v as string[]).join(', '),
    },
    {
      id: 'is_resolved',
      header: 'Statut',
      accessor: 'is_resolved',
      render: (v) => (
        <span className={`azals-badge azals-badge--${v ? 'green' : 'yellow'}`}>
          {v ? 'Resolu' : 'En attente'}
        </span>
      ),
    },
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      render: (v) => formatDate(v as string),
    },
  ];

  return (
    <PageWrapper
      title="Conflits de synchronisation"
      subtitle="Gerez les conflits de donnees"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <label className="azals-checkbox">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
            />
            <span>Afficher les conflits resolus</span>
          </label>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucun conflit"
        />
      </Card>
    </PageWrapper>
  );
};

export default ConflictsList;
