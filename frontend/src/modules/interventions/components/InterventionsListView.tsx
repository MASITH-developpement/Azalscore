/**
 * AZALSCORE Module - INTERVENTIONS - List View
 * Liste des interventions avec filtres et actions workflow
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Edit, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { Card } from '@ui/layout';
import { Badge } from '@ui/simple';
import { DataTable } from '@ui/tables';
import type { TableColumn, Intervenant } from '@/types';
import type { ColumnFilterConfig, ColumnFilters } from '@ui/tables';
import { formatDate, formatDuration } from '@/utils/formatters';
import {
  useInterventions,
  useIntervenants,
  useDeleteIntervention,
} from '../api';
import { usePlanifierIntervention } from '../hooks/usePlanningActions';
import {
  useValiderIntervention, useDemarrerIntervention, useTerminerIntervention,
  useDebloquerIntervention
} from '../hooks/useWorkflowActions';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_CONFIG, CORPS_ETAT_CONFIG,
} from '../types';
import type { Intervention, InterventionType, InterventionPriorite, CorpsEtat } from '../types';
import { STATUTS, PRIORITES, TYPES_INTERVENTION } from '../constants';
import { InterventionDetailView } from './InterventionDetailView';

export interface InterventionsListViewProps {
  onNewIntervention?: () => void;
  onEditIntervention?: (id: string) => void;
}

export const InterventionsListView: React.FC<InterventionsListViewProps> = ({ onNewIntervention, onEditIntervention }) => {
  const [filterStatut, setFilterStatut] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterPriorite, setFilterPriorite] = useState<string>('');

  // Column filters state
  const [columnFilters, setColumnFilters] = useState<ColumnFilters>({});
  const [selectedIntervention, setSelectedIntervention] = useState<Intervention | null>(null);

  // Workflow: planifier modal from list
  const [workflowTarget, setWorkflowTarget] = useState<Intervention | null>(null);
  const [showListPlanifierModal, setShowListPlanifierModal] = useState(false);
  const [listPlanDate, setListPlanDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [listPlanHeureDebut, setListPlanHeureDebut] = useState('08:00');
  const [listPlanHeureFin, setListPlanHeureFin] = useState('17:00');
  const [listPlanIntervenantId, setListPlanIntervenantId] = useState('');

  const { data: interventions = [], isLoading, error: interventionsError, refetch: refetchInterventions } = useInterventions({
    statut: filterStatut || undefined,
    type_intervention: filterType || undefined,
    priorite: filterPriorite || undefined
  });
  const { data: intervenantsList = [] } = useIntervenants();
  const validerList = useValiderIntervention();
  const planifier = usePlanifierIntervention();
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const debloquerList = useDebloquerIntervention();
  const deleteIntervention = useDeleteIntervention();

  const canEdit = (row: Intervention) => ['DRAFT', 'A_PLANIFIER', 'PLANIFIEE'].includes(row.statut);

  const handleDelete = async (row: Intervention) => {
    if (window.confirm(`Supprimer l'intervention ${row.reference} ?`)) {
      await deleteIntervention.mutateAsync(row.id);
    }
  };

  // Column filter configurations
  const columnFilterConfigs: Record<string, ColumnFilterConfig> = {
    reference: { type: 'text', placeholder: 'Filtrer par référence...' },
    titre: { type: 'text', placeholder: 'Filtrer par titre...' },
    client_name: { type: 'text', placeholder: 'Filtrer par client...' },
    type_intervention: {
      type: 'select',
      options: TYPES_INTERVENTION,
    },
    corps_etat: {
      type: 'select',
      options: Object.entries(CORPS_ETAT_CONFIG).map(([value, config]) => ({
        value,
        label: config.label,
      })),
    },
    priorite: {
      type: 'select',
      options: PRIORITES,
    },
    intervenant_name: { type: 'text', placeholder: 'Filtrer par intervenant...' },
    statut: {
      type: 'select',
      options: STATUTS,
    },
  };

  // Handle column filter change
  const handleColumnFilterChange = useCallback((columnId: string, value: string | string[] | null) => {
    setColumnFilters((prev: ColumnFilters) => {
      if (value === null || value === '') {
        const { [columnId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [columnId]: value };
    });
  }, []);

  // Clear all column filters
  const handleClearAllFilters = useCallback(() => {
    setColumnFilters({});
  }, []);

  // Filter data based on column filters
  const filteredInterventions = useMemo(() => {
    if (Object.keys(columnFilters).length === 0) {
      return interventions;
    }

    return interventions.filter((row) => {
      return Object.entries(columnFilters).every(([columnId, filterValue]) => {
        if (!filterValue) return true;

        const cellValue = row[columnId as keyof Intervention];
        if (cellValue === null || cellValue === undefined) {
          return filterValue === '';
        }

        const config = columnFilterConfigs[columnId];
        if (config?.type === 'select') {
          return String(cellValue) === filterValue;
        }

        // Text filter - case insensitive contains
        return String(cellValue).toLowerCase().includes(String(filterValue).toLowerCase());
      });
    });
  }, [interventions, columnFilters]);

  const columns: TableColumn<Intervention>[] = [
    { id: 'reference', header: 'Référence', accessor: 'reference', render: (v) => (
      <code className="font-mono text-sm">{v as string}</code>
    )},
    { id: 'titre', header: 'Titre', accessor: 'titre' },
    { id: 'client_name', header: 'Client', accessor: 'client_name', render: (v) => (v as string) || '-' },
    { id: 'type_intervention', header: 'Type', accessor: 'type_intervention', render: (v) => {
      const config = TYPE_CONFIG[v as InterventionType];
      return config?.label || (v as string);
    }},
    { id: 'corps_etat', header: "Corps d'état", accessor: 'corps_etat', render: (v) => {
      if (!v) return '-';
      const config = CORPS_ETAT_CONFIG[v as CorpsEtat];
      return <Badge variant={config?.color || 'default'}>{config?.label || (v as string)}</Badge>;
    }},
    { id: 'priorite', header: 'Priorité', accessor: 'priorite', render: (v) => {
      const config = PRIORITE_CONFIG[v as InterventionPriorite];
      return <Badge variant={config?.color || 'default'}>{config?.label || (v as string)}</Badge>;
    }},
    { id: 'date_prevue', header: 'Date prévue', accessor: 'date_prevue', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'intervenant_name', header: 'Intervenant', accessor: 'intervenant_name', render: (v) => (v as string) || '-' },
    { id: 'statut', header: 'Statut', accessor: 'statut', render: (v) => {
      const config = STATUT_CONFIG[v as keyof typeof STATUT_CONFIG];
      return <Badge variant={config?.color || 'default'}>{config?.label || (v as string)}</Badge>;
    }},
    { id: 'duree_prevue_minutes', header: 'Durée', accessor: 'duree_prevue_minutes', render: (v) => (v as number) ? formatDuration(v as number) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <div className="flex gap-1 items-center">
        <Button size="sm" variant="secondary" onClick={() => setSelectedIntervention(row)}>Détail</Button>
        {canEdit(row) && onEditIntervention && (
          <button
            className="p-1 hover:bg-gray-100 rounded"
            onClick={() => onEditIntervention(row.id)}
            title="Modifier"
          >
            <Edit size={14} className="text-gray-600" />
          </button>
        )}
        {canEdit(row) && (
          <button
            className="p-1 hover:bg-red-100 rounded"
            onClick={() => handleDelete(row)}
            title="Supprimer"
          >
            <Trash2 size={14} className="text-red-500" />
          </button>
        )}
        {row.statut === 'DRAFT' && (
          <Button size="sm" variant="primary" onClick={() => validerList.mutate(row.id)}>Valider</Button>
        )}
        {row.statut === 'A_PLANIFIER' && (
          <Button size="sm" variant="primary" onClick={() => { setWorkflowTarget(row); setShowListPlanifierModal(true); }}>Planifier</Button>
        )}
        {row.statut === 'PLANIFIEE' && (
          <Button size="sm" variant="warning" onClick={() => demarrer.mutate(row.id)}>Démarrer</Button>
        )}
        {row.statut === 'EN_COURS' && (
          <Button size="sm" variant="success" onClick={() => terminer.mutate(row.id)}>Terminer</Button>
        )}
        {row.statut === 'BLOQUEE' && (
          <Button size="sm" variant="warning" onClick={() => debloquerList.mutate(row.id)}>Débloquer</Button>
        )}
      </div>
    )}
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Interventions</h3>
          <div className="flex gap-2">
            <Select
              value={filterStatut}
              onChange={(v) => setFilterStatut(v)}
              options={[{ value: '', label: 'Tous statuts' }, ...STATUTS]}
              className="w-32"
            />
            <Select
              value={filterType}
              onChange={(v) => setFilterType(v)}
              options={[{ value: '', label: 'Tous types' }, ...TYPES_INTERVENTION]}
              className="w-36"
            />
            <Select
              value={filterPriorite}
              onChange={(v) => setFilterPriorite(v)}
              options={[{ value: '', label: 'Toutes priorités' }, ...PRIORITES]}
              className="w-36"
            />
            <Button onClick={onNewIntervention}>Nouvelle intervention</Button>
          </div>
        </div>
        <DataTable
          columns={columns}
          data={filteredInterventions}
          isLoading={isLoading}
          keyField="id"
          error={interventionsError instanceof Error ? interventionsError : null}
          onRetry={() => refetchInterventions()}
          columnFilters={{
            filters: columnFilters,
            configs: columnFilterConfigs,
            onFilterChange: handleColumnFilterChange,
            onClearAllFilters: handleClearAllFilters,
          }}
        />
      </Card>

      {/* Detail View with BaseViewStandard */}
      {selectedIntervention && (
        <InterventionDetailView
          intervention={selectedIntervention}
          onClose={() => setSelectedIntervention(null)}
        />
      )}

      {/* Modal Planifier depuis la liste */}
      {showListPlanifierModal && workflowTarget && (
        <Modal isOpen onClose={() => { setShowListPlanifierModal(false); setWorkflowTarget(null); }} title="Planifier l'intervention">
          <div className="azals-modal__body">
            <p className="text-muted mb-4">
              {workflowTarget.reference} — {workflowTarget.titre || 'Sans titre'}
            </p>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="list-plan-date">Date <span className="azals-field__required">*</span></label>
              <input id="list-plan-date" className="azals-input" type="date" value={listPlanDate} onChange={e => setListPlanDate(e.target.value)} />
            </div>
            <div className="azals-grid azals-grid--cols-2">
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="list-plan-heure-debut">Heure début</label>
                <input id="list-plan-heure-debut" className="azals-input" type="time" value={listPlanHeureDebut} onChange={e => setListPlanHeureDebut(e.target.value)} />
              </div>
              <div className="azals-field">
                <label className="azals-field__label" htmlFor="list-plan-heure-fin">Heure fin</label>
                <input id="list-plan-heure-fin" className="azals-input" type="time" value={listPlanHeureFin} onChange={e => setListPlanHeureFin(e.target.value)} />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="list-plan-intervenant">Intervenant <span className="azals-field__required">*</span></label>
              <select id="list-plan-intervenant" className="azals-select" value={listPlanIntervenantId} onChange={e => setListPlanIntervenantId(e.target.value)}>
                <option value="">Choisir un intervenant...</option>
                {intervenantsList.map((i: Intervenant) => (
                  <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => { setShowListPlanifierModal(false); setWorkflowTarget(null); }}>Annuler</Button>
            <Button onClick={() => {
              if (!listPlanIntervenantId) return;
              const debut = new Date(`${listPlanDate}T${listPlanHeureDebut}:00`);
              const fin = new Date(`${listPlanDate}T${listPlanHeureFin}:00`);
              planifier.mutate({
                id: workflowTarget.id,
                data: {
                  date_prevue_debut: debut.toISOString(),
                  date_prevue_fin: fin.toISOString(),
                  intervenant_id: listPlanIntervenantId,
                }
              }, {
                onSuccess: () => { setShowListPlanifierModal(false); setWorkflowTarget(null); },
              });
            }} disabled={!listPlanIntervenantId || planifier.isPending}>
              {planifier.isPending ? 'Planification...' : 'Planifier'}
            </Button>
          </div>
        </Modal>
      )}

    </>
  );
};

export default InterventionsListView;
