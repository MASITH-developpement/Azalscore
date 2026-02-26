/**
 * AZALSCORE Module - Ordres de Service - List View
 * Liste des interventions
 */

import React, { useState } from 'react';
import { Plus, Edit, Search, Trash2, Users } from 'lucide-react';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDateTime } from '@/utils/formatters';
import {
  STATUTS, TYPE_INTERVENTION_CONFIG, canEditIntervention
} from '../types';
import type { Intervention, InterventionStatut, InterventionPriorite, TypeIntervention } from '../types';
import { useInterventionsList, useDeleteIntervention } from '../hooks';
import { StatutBadge, PrioriteBadge } from './StatusBadges';
import { ODSStats } from './ODSStats';

export interface ODSListViewProps {
  onSelectODS: (id: string) => void;
  onCreateODS: () => void;
  onEditODS: (id: string) => void;
}

export const ODSListView: React.FC<ODSListViewProps> = ({ onSelectODS, onCreateODS, onEditODS }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ statut?: string; search?: string }>({});
  const deleteIntervention = useDeleteIntervention();

  const { data, isLoading, refetch } = useInterventionsList(page, pageSize, filters);

  const columns: TableColumn<Intervention>[] = [
    {
      id: 'reference',
      header: 'Reference',
      accessor: 'reference',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectODS(row.id)}>{value as string}</span>
      ),
    },
    {
      id: 'titre',
      header: 'Titre',
      accessor: 'titre',
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type_intervention',
      render: (value) => {
        const config = TYPE_INTERVENTION_CONFIG[value as TypeIntervention];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'client',
      header: 'Client',
      accessor: 'client_name',
      render: (value, row) => (
        <div>
          <div>{value as string || row.donneur_ordre_name || '-'}</div>
          {row.ville && <div className="text-muted text-sm">{row.ville}</div>}
        </div>
      ),
    },
    {
      id: 'priorite',
      header: 'Priorite',
      accessor: 'priorite',
      render: (value) => <PrioriteBadge priorite={value as InterventionPriorite} />,
    },
    {
      id: 'statut',
      header: 'Statut',
      accessor: 'statut',
      render: (value) => <StatutBadge statut={value as InterventionStatut} />,
    },
    {
      id: 'date_prevue',
      header: 'Date prevue',
      accessor: 'date_prevue_debut',
      render: (value) => {
        if (!value) return <span className="text-muted">-</span>;
        return formatDateTime(value as string);
      },
    },
    {
      id: 'intervenant',
      header: 'Intervenant',
      accessor: 'intervenant_name',
      render: (value) => (value ? String(value) : <span className="text-muted">-</span>),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => {
        const canEdit = canEditIntervention(row);
        const handleDelete = async (e: React.MouseEvent) => {
          e.stopPropagation();
          if (window.confirm(`Supprimer l'intervention ${row.reference} ?`)) {
            await deleteIntervention.mutateAsync(row.id);
          }
        };
        return (
          <div className="azals-table-actions" onClick={(e) => e.stopPropagation()}>
            {canEdit && (
              <button
                className="azals-btn-icon"
                onClick={() => onEditODS(row.id)}
                title="Modifier"
              >
                <Edit size={16} />
              </button>
            )}
            {canEdit && (
              <button
                className="azals-btn-icon azals-btn-icon--danger"
                onClick={handleDelete}
                title="Supprimer"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <PageWrapper
      title="Ordres de Service"
      subtitle="Gestion des interventions et travaux"
      actions={
        <ButtonGroup>
          <Button variant="secondary" leftIcon={<Users size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:navigate:ods:donneurs')); }}>
            Donneurs d'ordre
          </Button>
          <Button leftIcon={<Plus size={16} />} onClick={onCreateODS}>Nouvelle intervention</Button>
        </ButtonGroup>
      }
    >
      <section className="azals-section">
        <ODSStats />
      </section>

      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Rechercher..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="azals-input"
            />
          </div>
          <select
            className="azals-select"
            value={filters.statut || ''}
            onChange={(e) => setFilters({ ...filters, statut: e.target.value || undefined })}
          >
            <option value="">Tous les statuts</option>
            {STATUTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
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
          emptyMessage="Aucune intervention"
        />
      </Card>
    </PageWrapper>
  );
};

export default ODSListView;
