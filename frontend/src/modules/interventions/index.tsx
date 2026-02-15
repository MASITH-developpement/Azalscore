/**
 * AZALSCORE Module - INTERVENTIONS
 * Gestion des interventions terrain - Migré vers BaseViewStandard
 */

import React, { useState, useCallback, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { Badge } from '@ui/simple';
import { BaseViewStandard } from '@ui/standards';
import type { TableColumn } from '@/types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition } from '@ui/standards';
import {
  ClipboardList, Calendar, Wrench, CheckCircle, BarChart3, Clock, MapPin,
  User, FileText, History, Sparkles, Package, Euro, AlertTriangle, Play, X,
  FileEdit, Lock, Unlock, CheckSquare, Edit, Trash2
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';

// Import API hooks (AZA-FE-003: api.ts)
import {
  useInterventionStats,
  useInterventions,
  useDonneursOrdre,
  useIntervenants,
  useDeleteIntervention,
  useUpdateDonneurOrdre,
  useDeleteDonneurOrdre,
  interventionKeys,
} from './api';

// Import workflow hooks
import { usePlanifierIntervention } from './hooks/usePlanningActions';
import {
  useValiderIntervention, useDemarrerIntervention, useTerminerIntervention,
  useBloquerIntervention, useDebloquerIntervention, useAnnulerIntervention
} from './hooks/useWorkflowActions';

// Import tab components
import {
  InterventionInfoTab,
  InterventionLinesTab,
  InterventionFinancialTab,
  InterventionDocsTab,
  InterventionHistoryTab,
  InterventionIATab,
  InterventionFormView,
  PlanningView
} from './components';

// Import shared types
import type { Intervention, InterventionType, InterventionPriorite, CorpsEtat, DonneurOrdre, InterventionStats } from './types';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, TYPE_CONFIG, CORPS_ETAT_CONFIG,
  isLate, canValidate, canBlock, canUnblock
} from './types';
import { formatDate, formatDuration, formatCurrency } from '@/utils/formatters';

// ============================================================================
// CONSTANTES
// ============================================================================

const STATUTS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'A_PLANIFIER', label: 'À planifier' },
  { value: 'PLANIFIEE', label: 'Planifiée' },
  { value: 'EN_COURS', label: 'En cours' },
  { value: 'BLOQUEE', label: 'Bloquée' },
  { value: 'TERMINEE', label: 'Terminée' },
  { value: 'ANNULEE', label: 'Annulée' }
];

const PRIORITES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' },
  { value: 'URGENT', label: 'Urgente' }
];

const TYPES_INTERVENTION = [
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Réparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' }
];

// ============================================================================
// DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface InterventionDetailViewProps {
  intervention: Intervention;
  onClose: () => void;
}

const InterventionDetailView: React.FC<InterventionDetailViewProps> = ({ intervention, onClose }) => {
  // Workflow hooks
  const valider = useValiderIntervention();
  const planifier = usePlanifierIntervention();
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const bloquer = useBloquerIntervention();
  const debloquer = useDebloquerIntervention();
  const annuler = useAnnulerIntervention();
  const { data: intervenants = [] } = useIntervenants();

  // Workflow modals state
  const [showPlanifierModal, setShowPlanifierModal] = useState(false);
  const [showBloquerModal, setShowBloquerModal] = useState(false);
  const [showConfirmAnnuler, setShowConfirmAnnuler] = useState(false);
  const [motifBlocage, setMotifBlocage] = useState('');
  const [planDate, setPlanDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [planHeureDebut, setPlanHeureDebut] = useState('08:00');
  const [planHeureFin, setPlanHeureFin] = useState('17:00');
  const [planIntervenantId, setPlanIntervenantId] = useState('');
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const typeConfig = TYPE_CONFIG[intervention.type_intervention];

  // Tabs definition
  const tabs: TabDefinition<Intervention>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <ClipboardList size={16} />,
      component: InterventionInfoTab
    },
    {
      id: 'lignes',
      label: 'Détails',
      icon: <Package size={16} />,
      component: InterventionLinesTab
    },
    {
      id: 'financier',
      label: 'Financier',
      icon: <Euro size={16} />,
      component: InterventionFinancialTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: intervention.rapport ? 1 : 0,
      component: InterventionDocsTab
    },
    {
      id: 'historique',
      label: 'Historique',
      icon: <History size={16} />,
      component: InterventionHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: InterventionIATab
    }
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'client',
      label: 'Client',
      value: intervention.client_name || '-',
      icon: <User size={14} />
    },
    {
      id: 'type',
      label: 'Type',
      value: typeConfig?.label || intervention.type_intervention,
      icon: <Wrench size={14} />
    },
    {
      id: 'date_prevue',
      label: 'Date prévue',
      value: intervention.date_prevue ? formatDate(intervention.date_prevue) : 'Non planifiée',
      icon: <Calendar size={14} />,
      valueColor: isLate(intervention) ? 'red' : undefined
    },
    {
      id: 'duree',
      label: 'Durée',
      value: formatDuration(intervention.duree_reelle_minutes || intervention.duree_prevue_minutes),
      icon: <Clock size={14} />
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'resume',
      title: 'Résumé',
      items: [
        { id: 'reference', label: 'Référence', value: intervention.reference },
        { id: 'priorite', label: 'Priorité', value: prioriteConfig?.label || intervention.priorite },
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_name || 'Non assigné' },
        { id: 'created_at', label: 'Créé le', value: formatDate(intervention.created_at) }
      ]
    },
    {
      id: 'localisation',
      title: 'Localisation',
      items: [
        { id: 'adresse', label: 'Adresse', value: intervention.adresse_intervention || intervention.adresse_ligne1 || '-' },
        { id: 'ville', label: 'Ville', value: intervention.ville || '-' },
        { id: 'contact', label: 'Contact', value: intervention.contact_sur_place || '-' }
      ]
    },
    {
      id: 'facturation',
      title: 'Facturation',
      items: [
        { id: 'facturable', label: 'Facturable', value: intervention.facturable !== false ? 'Oui' : 'Non' },
        { id: 'montant_ht', label: 'Montant HT', value: formatCurrency(intervention.montant_ht || 0) },
        { id: 'facture', label: 'Facture', value: intervention.facture_reference || '-' }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'close',
      label: 'Fermer',
      variant: 'secondary' as const,
      onClick: onClose
    }
  ];

  // Footer actions based on status (state machine 7 états)
  const primaryActions: ActionDefinition[] = [];

  if (canValidate(intervention)) {
    primaryActions.push({
      id: 'valider',
      label: 'Valider',
      icon: <CheckSquare size={16} />,
      variant: 'primary' as const,
      onClick: () => {
        valider.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur validation'),
        });
      }
    });
  }

  if (intervention.statut === 'A_PLANIFIER') {
    primaryActions.push({
      id: 'planifier',
      label: 'Planifier',
      icon: <Calendar size={16} />,
      variant: 'primary' as const,
      onClick: () => setShowPlanifierModal(true)
    });
  }

  if (intervention.statut === 'PLANIFIEE') {
    primaryActions.push({
      id: 'demarrer',
      label: 'Démarrer',
      icon: <Play size={16} />,
      variant: 'warning' as const,
      onClick: () => {
        demarrer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur'),
        });
      }
    });
  }

  if (intervention.statut === 'EN_COURS') {
    primaryActions.push({
      id: 'terminer',
      label: 'Terminer',
      icon: <CheckCircle size={16} />,
      variant: 'success' as const,
      onClick: () => {
        terminer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur'),
        });
      }
    });
    primaryActions.push({
      id: 'bloquer',
      label: 'Bloquer',
      icon: <Lock size={16} />,
      variant: 'danger' as const,
      onClick: () => setShowBloquerModal(true)
    });
  }

  if (canUnblock(intervention)) {
    primaryActions.push({
      id: 'debloquer',
      label: 'Débloquer',
      icon: <Unlock size={16} />,
      variant: 'warning' as const,
      onClick: () => {
        debloquer.mutate(intervention.id, {
          onSuccess: () => onClose(),
          onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur déblocage'),
        });
      }
    });
  }

  if (!['TERMINEE', 'ANNULEE', 'DRAFT'].includes(intervention.statut)) {
    primaryActions.push({
      id: 'annuler',
      label: 'Annuler',
      icon: <X size={16} />,
      variant: 'danger' as const,
      onClick: () => setShowConfirmAnnuler(true)
    });
  }

  const handlePlanifierSubmit = () => {
    if (!planIntervenantId) {
      setWorkflowError('Veuillez sélectionner un intervenant');
      return;
    }
    const debut = new Date(`${planDate}T${planHeureDebut}:00`);
    const fin = new Date(`${planDate}T${planHeureFin}:00`);
    planifier.mutate({
      id: intervention.id,
      data: {
        date_prevue_debut: debut.toISOString(),
        date_prevue_fin: fin.toISOString(),
        intervenant_id: planIntervenantId,
      }
    }, {
      onSuccess: () => { setShowPlanifierModal(false); onClose(); },
      onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur planification'),
    });
  };

  const handleAnnulerConfirm = () => {
    annuler.mutate(intervention.id, {
      onSuccess: () => { setShowConfirmAnnuler(false); onClose(); },
      onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur annulation'),
    });
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="" size="xl">
      <BaseViewStandard<Intervention>
        title={intervention.titre}
        subtitle={`Intervention ${intervention.reference}`}
        status={{
          label: statutConfig?.label || intervention.statut,
          color: (statutConfig?.color || 'gray') as 'gray' | 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'yellow' | 'cyan',
          icon: statutConfig?.icon
        }}
        data={intervention}
        view="detail"
        tabs={tabs}
        infoBarItems={infoBarItems}
        sidebarSections={sidebarSections}
        headerActions={headerActions}
        primaryActions={primaryActions}
      />

      {/* Workflow error toast */}
      {workflowError && (
        <div className="azals-planning__toast">
          <AlertTriangle size={16} />
          <span>{workflowError}</span>
          <button className="azals-btn azals-btn--ghost azals-btn--icon-only" onClick={() => setWorkflowError(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Modal Planifier */}
      {showPlanifierModal && (
        <Modal isOpen onClose={() => setShowPlanifierModal(false)} title="Planifier l'intervention">
          <div className="azals-modal__body">
            <p className="text-muted mb-4">
              {intervention.reference} — {intervention.titre || 'Sans titre'}
            </p>
            <div className="azals-field">
              <label className="azals-field__label">Date <span className="azals-field__required">*</span></label>
              <input className="azals-input" type="date" value={planDate} onChange={e => setPlanDate(e.target.value)} />
            </div>
            <div className="azals-grid azals-grid--cols-2">
              <div className="azals-field">
                <label className="azals-field__label">Heure début</label>
                <input className="azals-input" type="time" value={planHeureDebut} onChange={e => setPlanHeureDebut(e.target.value)} />
              </div>
              <div className="azals-field">
                <label className="azals-field__label">Heure fin</label>
                <input className="azals-input" type="time" value={planHeureFin} onChange={e => setPlanHeureFin(e.target.value)} />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Intervenant <span className="azals-field__required">*</span></label>
              <select className="azals-select" value={planIntervenantId} onChange={e => setPlanIntervenantId(e.target.value)}>
                <option value="">Choisir un intervenant...</option>
                {intervenants.map((i: any) => (
                  <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => setShowPlanifierModal(false)}>Annuler</Button>
            <Button onClick={handlePlanifierSubmit} disabled={planifier.isPending}>
              {planifier.isPending ? 'Planification...' : 'Planifier'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal Bloquer */}
      {showBloquerModal && (
        <Modal isOpen onClose={() => { setShowBloquerModal(false); setMotifBlocage(''); }} title="Bloquer l'intervention">
          <div className="azals-modal__body">
            <p className="text-muted mb-4">
              {intervention.reference} — {intervention.titre || 'Sans titre'}
            </p>
            <div className="azals-field">
              <label className="azals-field__label">Motif du blocage <span className="azals-field__required">*</span></label>
              <textarea
                className="azals-input"
                rows={3}
                value={motifBlocage}
                onChange={e => setMotifBlocage(e.target.value)}
                placeholder="Décrivez le motif du blocage (min. 5 caractères)..."
              />
              {motifBlocage.length > 0 && motifBlocage.length < 5 && (
                <p className="text-danger text-sm mt-1">Le motif doit contenir au moins 5 caractères.</p>
              )}
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => { setShowBloquerModal(false); setMotifBlocage(''); }}>Annuler</Button>
            <Button
              variant="danger"
              onClick={() => {
                bloquer.mutate({ id: intervention.id, motif: motifBlocage }, {
                  onSuccess: () => { setShowBloquerModal(false); setMotifBlocage(''); onClose(); },
                  onError: (err: any) => setWorkflowError(err?.response?.data?.detail || err?.message || 'Erreur blocage'),
                });
              }}
              disabled={motifBlocage.length < 5 || bloquer.isPending}
            >
              {bloquer.isPending ? 'Blocage...' : 'Confirmer le blocage'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal Confirmer annulation */}
      {showConfirmAnnuler && (
        <Modal isOpen onClose={() => setShowConfirmAnnuler(false)} title="Confirmer l'annulation">
          <div className="azals-modal__body">
            <p>
              Êtes-vous sûr de vouloir annuler l'intervention <strong>{intervention.reference}</strong> ?
            </p>
            <p className="text-muted mt-2">
              Cette action est irréversible.
            </p>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={() => setShowConfirmAnnuler(false)}>Non, garder</Button>
            <Button variant="danger" onClick={handleAnnulerConfirm} disabled={annuler.isPending}>
              {annuler.isPending ? 'Annulation...' : 'Oui, annuler'}
            </Button>
          </div>
        </Modal>
      )}
    </Modal>
  );
};

// ============================================================================
// LIST VIEW
// ============================================================================

// Import column filter types
import type { ColumnFilterConfig, ColumnFilters } from '@ui/tables';

const InterventionsListView: React.FC<{ onNewIntervention?: () => void; onEditIntervention?: (id: string) => void }> = ({ onNewIntervention, onEditIntervention }) => {
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
    setColumnFilters(prev => {
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
              <label className="azals-field__label">Date <span className="azals-field__required">*</span></label>
              <input className="azals-input" type="date" value={listPlanDate} onChange={e => setListPlanDate(e.target.value)} />
            </div>
            <div className="azals-grid azals-grid--cols-2">
              <div className="azals-field">
                <label className="azals-field__label">Heure début</label>
                <input className="azals-input" type="time" value={listPlanHeureDebut} onChange={e => setListPlanHeureDebut(e.target.value)} />
              </div>
              <div className="azals-field">
                <label className="azals-field__label">Heure fin</label>
                <input className="azals-input" type="time" value={listPlanHeureFin} onChange={e => setListPlanHeureFin(e.target.value)} />
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Intervenant <span className="azals-field__required">*</span></label>
              <select className="azals-select" value={listPlanIntervenantId} onChange={e => setListPlanIntervenantId(e.target.value)}>
                <option value="">Choisir un intervenant...</option>
                {intervenantsList.map((i: any) => (
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


// ============================================================================
// DONNEURS D'ORDRE VIEW
// ============================================================================

const DonneursOrdreView: React.FC = () => {
  const { data: donneursOrdre = [], isLoading, error: donneursError, refetch: refetchDonneurs } = useDonneursOrdre();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingDonneur, setEditingDonneur] = useState<DonneurOrdre | null>(null);
  const [formData, setFormData] = useState({ code: '', nom: '', email: '', telephone: '' });
  const [createError, setCreateError] = useState('');

  const updateFormField = useCallback((field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const closeCreateModal = useCallback(() => {
    setShowCreate(false);
    setCreateError('');
  }, []);

  const closeEditModal = useCallback(() => {
    setShowEdit(false);
    setEditingDonneur(null);
  }, []);

  const [editFormData, setEditFormData] = useState({ nom: '', code: '', email: '', telephone: '' });
  const updateEditFormField = useCallback((field: string, value: string) => {
    setEditFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const updateDonneur = useUpdateDonneurOrdre();
  const deleteDonneur = useDeleteDonneurOrdre();

  const handleEdit = (donneur: DonneurOrdre) => {
    setEditingDonneur(donneur);
    setEditFormData({
      nom: donneur.nom || '',
      code: donneur.code || '',
      email: donneur.email || '',
      telephone: donneur.telephone || '',
    });
    setShowEdit(true);
  };

  const handleDelete = async (donneur: DonneurOrdre) => {
    if (window.confirm(`Supprimer le donneur d'ordre "${donneur.nom}" ?`)) {
      try {
        await deleteDonneur.mutateAsync(donneur.id);
      } catch (error: any) {
        alert(`Erreur lors de la suppression: ${error?.response?.data?.detail || error?.message || 'Erreur inconnue'}`);
      }
    }
  };

  const handleSaveEdit = async () => {
    if (!editingDonneur) return;
    await updateDonneur.mutateAsync({ id: editingDonneur.id, data: editFormData });
    setShowEdit(false);
    setEditingDonneur(null);
  };

  const createDonneur = useMutation({
    mutationFn: async (data: typeof formData) => {
      return api.post('/v3/interventions/donneurs-ordre', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.donneursOrdre() });
      setShowCreate(false);
      setFormData({ nom: '', code: '', email: '', telephone: '' });
      setCreateError('');
    },
    onError: (error: any) => {
      setCreateError(error?.response?.data?.detail || error?.message || 'Erreur lors de la création');
    },
  });

  const handleCreate = () => {
    if (!formData.nom.trim()) {
      setCreateError('Le nom est obligatoire');
      return;
    }
    setCreateError('');
    // Le code sera auto-généré par le backend si non fourni
    createDonneur.mutate(formData);
  };

  const columns: TableColumn<DonneurOrdre>[] = [
    { id: 'code', header: 'Code', accessor: 'code' },
    { id: 'nom', header: 'Nom', accessor: 'nom' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => (v as string) || '-' },
    { id: 'telephone', header: 'Téléphone', accessor: 'telephone', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge variant={(v as boolean) ? 'green' : 'default'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <div className="flex gap-1 items-center">
        <button
          className="p-1 hover:bg-gray-100 rounded"
          onClick={() => handleEdit(row)}
          title="Modifier"
        >
          <Edit size={14} className="text-gray-600" />
        </button>
        <button
          className="p-1 hover:bg-red-100 rounded"
          onClick={() => handleDelete(row)}
          title="Supprimer"
        >
          <Trash2 size={14} className="text-red-500" />
        </button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Donneurs d'ordre</h3>
        <Button onClick={() => setShowCreate(true)}>Nouveau donneur d'ordre</Button>
      </div>
      <DataTable columns={columns} data={donneursOrdre} isLoading={isLoading} keyField="id"
          filterable error={donneursError instanceof Error ? donneursError : null} onRetry={() => refetchDonneurs()} />

      {showCreate && (
        <Modal isOpen onClose={closeCreateModal} title="Nouveau donneur d'ordre">
          <div className="azals-modal__body">
            {createError && (
              <div className="azals-alert azals-alert--error mb-4">
                {createError}
              </div>
            )}
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-nom">Nom <span className="azals-field__required">*</span></label>
              <input id="donneur-nom" className="azals-input" value={formData.nom} onChange={e => updateFormField('nom', e.target.value)} placeholder="Nom du donneur d'ordre" autoFocus />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-code">Code <span className="text-gray-400 text-xs">(auto si vide)</span></label>
              <input id="donneur-code" className="azals-input" value={formData.code} onChange={e => updateFormField('code', e.target.value)} placeholder="Auto: DO-0001" />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-email">Email</label>
              <input id="donneur-email" className="azals-input" type="email" value={formData.email} onChange={e => updateFormField('email', e.target.value)} placeholder="email@example.com" />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="donneur-telephone">Téléphone</label>
              <input id="donneur-telephone" className="azals-input" type="tel" value={formData.telephone} onChange={e => updateFormField('telephone', e.target.value)} placeholder="0612345678" />
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={closeCreateModal}>Annuler</Button>
            <Button onClick={handleCreate} disabled={createDonneur.isPending}>
              {createDonneur.isPending ? 'Création...' : 'Créer'}
            </Button>
          </div>
        </Modal>
      )}

      {/* Modal édition */}
      {showEdit && editingDonneur && (
        <Modal isOpen onClose={closeEditModal} title="Modifier le donneur d'ordre">
          <div className="azals-modal__body">
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-code">Code</label>
              <input id="edit-donneur-code" className="azals-input" value={editFormData.code} disabled />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-nom">Nom <span className="azals-field__required">*</span></label>
              <input id="edit-donneur-nom" className="azals-input" value={editFormData.nom} onChange={e => updateEditFormField('nom', e.target.value)} autoFocus />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-email">Email</label>
              <input id="edit-donneur-email" className="azals-input" type="email" value={editFormData.email} onChange={e => updateEditFormField('email', e.target.value)} />
            </div>
            <div className="azals-field">
              <label className="azals-field__label" htmlFor="edit-donneur-telephone">Téléphone</label>
              <input id="edit-donneur-telephone" className="azals-input" type="tel" value={editFormData.telephone} onChange={e => updateEditFormField('telephone', e.target.value)} />
            </div>
          </div>
          <div className="azals-modal__footer">
            <Button variant="secondary" onClick={closeEditModal}>Annuler</Button>
            <Button onClick={handleSaveEdit} disabled={updateDonneur.isPending}>
              {updateDonneur.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>
        </Modal>
      )}
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'interventions' | 'planning' | 'donneurs-ordre' | 'form';

const InterventionsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [editInterventionId, setEditInterventionId] = useState<string | undefined>(undefined);
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useInterventionStats();

  const navigateToForm = (interventionId?: string) => {
    setEditInterventionId(interventionId);
    setCurrentView('form');
  };

  const navigateToList = () => {
    setEditInterventionId(undefined);
    setCurrentView('interventions');
  };

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'interventions', label: 'Interventions' },
    { id: 'planning', label: 'Planning' },
    { id: 'donneurs-ordre', label: 'Donneurs d\'ordre' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'form':
        return (
          <InterventionFormView
            interventionId={editInterventionId}
            onBack={navigateToList}
            onSaved={() => navigateToList()}
          />
        );
      case 'interventions':
        return <InterventionsListView onNewIntervention={() => navigateToForm()} onEditIntervention={(id) => navigateToForm(id)} />;
      case 'planning':
        return <PlanningView />;
      case 'donneurs-ordre':
        return <DonneursOrdreView />;
      default:
        if (statsLoading) {
          return <LoadingState onRetry={() => refetchStats()} message="Chargement des statistiques..." />;
        }
        if (statsError) {
          return (
            <ErrorState
              message="Impossible de charger les statistiques"
              onRetry={() => refetchStats()}
            />
          );
        }
        return (
          <div className="space-y-4">
            <Grid cols={3}>
              <StatCard
                title="Brouillons"
                value={String(stats?.brouillons || 0)}
                icon={<FileEdit size={20} />}
                variant="default"
                onClick={() => setCurrentView('interventions')}
              />
              <StatCard
                title="À planifier"
                value={String(stats?.a_planifier || 0)}
                icon={<ClipboardList size={20} />}
                variant="default"
                onClick={() => setCurrentView('interventions')}
              />
              <StatCard
                title="Planifiées"
                value={String(stats?.planifiees || 0)}
                icon={<Calendar size={20} />}
                variant="default"
                onClick={() => setCurrentView('planning')}
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="En cours"
                value={String(stats?.en_cours || 0)}
                icon={<Wrench size={20} />}
                variant="warning"
              />
              <StatCard
                title="Bloquées"
                value={String(stats?.bloquees || 0)}
                icon={<Lock size={20} />}
                variant="danger"
              />
              <StatCard
                title="Terminées (semaine)"
                value={String(stats?.terminees_semaine || 0)}
                icon={<CheckCircle size={20} />}
                variant="success"
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Terminées (mois)"
                value={String(stats?.terminees_mois || 0)}
                icon={<BarChart3 size={20} />}
                variant="default"
              />
              <StatCard
                title="Durée moyenne"
                value={stats?.duree_moyenne_minutes ? formatDuration(stats.duree_moyenne_minutes) : '-'}
                icon={<Clock size={20} />}
                variant="default"
              />
              <StatCard
                title="Aujourd'hui"
                value={String(stats?.interventions_jour || 0)}
                icon={<MapPin size={20} />}
                variant="success"
              />
            </Grid>
          </div>
        );
    }
  };

  // Form view renders its own PageWrapper
  if (currentView === 'form') {
    return renderContent();
  }

  return (
    <PageWrapper title="Interventions" subtitle="Gestion des interventions terrain">
      <div className="azals-tab-nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`azals-tab-nav__item ${currentView === tab.id ? 'azals-tab-nav__item--active' : ''}`}
            onClick={() => setCurrentView(tab.id as View)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default InterventionsModule;
