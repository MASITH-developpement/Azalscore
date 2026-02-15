/**
 * AZALSCORE Module - ORDRES DE SERVICE (ODS)
 * Gestion des interventions et travaux
 * Flux : CRM → DEV → [ODS] → AFF → FAC/AVO → CPT
 * Numerotation : ODS-YY-MM-XXXX
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Wrench, Plus, Edit, Search, Download, FileText,
  Calendar, Clock, Play, CheckCircle2, X, Trash2, Users, Sparkles
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';
import type {
  Intervention, DonneurOrdre, InterventionStats,
  InterventionStatut, InterventionPriorite, TypeIntervention, CorpsEtat, CanalDemande
} from './types';
import {
  STATUT_CONFIG, PRIORITE_CONFIG, STATUTS, PRIORITES,
  TYPES_INTERVENTION, CORPS_ETATS, CANAUX_DEMANDE,
  TYPE_INTERVENTION_CONFIG,
  canEditIntervention, canStartIntervention, canCompleteIntervention, canInvoiceIntervention,
  getInterventionAge, getActualDuration, getPhotoCount, getFullAddress
} from './types';
import { formatDate, formatDateTime, formatCurrency, formatDuration } from '@/utils/formatters';
import {
  InterventionInfoTab,
  InterventionPlanningTab,
  InterventionPhotosTab,
  InterventionReportTab,
  InterventionHistoryTab,
  InterventionIATab
} from './components';

// ============================================================
// API HOOKS
// ============================================================

const useInterventionsList = (page = 1, pageSize = 25, filters?: { statut?: string; priorite?: string; search?: string }) => {
  return useQuery({
    queryKey: ['interventions', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (filters?.statut) params.append('statut', filters.statut);
      if (filters?.priorite) params.append('priorite', filters.priorite);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Intervention>>(`/v3/interventions?${params}`);
      return response.data;
    },
  });
};

const useIntervention = (id: string) => {
  return useQuery({
    queryKey: ['interventions', id],
    queryFn: async () => {
      const response = await api.get<Intervention>(`/v3/interventions/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useInterventionStats = () => {
  return useQuery({
    queryKey: ['interventions', 'stats'],
    queryFn: async () => {
      const response = await api.get<InterventionStats>('/v3/interventions/stats');
      return response.data;
    },
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<DonneurOrdre[]>('/v3/interventions/donneurs-ordre');
      return response.data;
    },
  });
};

interface Client {
  id: string;
  code: string;
  name: string;
}

const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get<Client[] | { items: Client[] }>('/v3/crm/customers');
      const data = response.data;
      return Array.isArray(data) ? data : (data?.items || []);
    },
  });
};

interface Intervenant {
  id: string;
  first_name: string;
  last_name: string;
}

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<Intervenant[] | { items: Intervenant[] }>('/v3/hr/employees');
      const data = response.data;
      return Array.isArray(data) ? data : (data?.items || []);
    },
  });
};

// CRUD Donneurs d'ordre
const useCreateDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<DonneurOrdre>) => {
      const response = await api.post<DonneurOrdre>('/v3/interventions/donneurs-ordre', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

const useUpdateDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DonneurOrdre> }) => {
      const response = await api.put<DonneurOrdre>(`/v3/interventions/donneurs-ordre/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

const useDeleteDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v3/interventions/donneurs-ordre/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

// Delete Intervention
const useDeleteIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v3/interventions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      const response = await api.post<Intervention>('/v3/interventions', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

const useUpdateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Intervention> }) => {
      const response = await api.put<Intervention>(`/v3/interventions/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

const useDemarrerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Intervention>(`/v3/interventions/${id}/demarrer`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

const useTerminerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { commentaire_cloture?: string; montant_reel?: number } }) => {
      const response = await api.post<Intervention>(`/v3/interventions/${id}/terminer`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

// ============================================================
// LOCAL COMPONENTS
// ============================================================

const StatutBadge: React.FC<{ statut: InterventionStatut }> = ({ statut }) => {
  const config = STATUT_CONFIG[statut];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {statut === 'A_PLANIFIER' && <Calendar size={14} />}
      {statut === 'PLANIFIEE' && <Clock size={14} />}
      {statut === 'EN_COURS' && <Play size={14} />}
      {statut === 'TERMINEE' && <CheckCircle2 size={14} />}
      {statut === 'ANNULEE' && <X size={14} />}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

const PrioriteBadge: React.FC<{ priorite: InterventionPriorite }> = ({ priorite }) => {
  const config = PRIORITE_CONFIG[priorite];
  return (
    <span className={`azals-badge azals-badge--${config.color} azals-badge--outline`}>
      {config.label}
    </span>
  );
};

const ODSStats: React.FC = () => {
  const { data: stats } = useInterventionStats();

  const kpis: DashboardKPI[] = stats ? [
    { id: 'planifier', label: 'A planifier', value: stats.a_planifier, icon: <Calendar size={20} />, variant: stats.a_planifier > 0 ? 'warning' : undefined },
    { id: 'planifiees', label: 'Planifiees', value: stats.planifiees, icon: <Clock size={20} /> },
    { id: 'encours', label: 'En cours', value: stats.en_cours, icon: <Play size={20} /> },
    { id: 'terminees', label: 'Terminees', value: stats.terminees, icon: <CheckCircle2 size={20} /> },
  ] : [];

  return (
    <Grid cols={4} gap="md">
      {kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
    </Grid>
  );
};

// ============================================================
// NAVIGATION
// ============================================================

type ODSView = 'list' | 'detail' | 'form' | 'donneurs-ordre';

interface ODSNavState {
  view: ODSView;
  interventionId?: string;
  isNew?: boolean;
}

// ============================================================
// LIST VIEW
// ============================================================

const ODSListView: React.FC<{
  onSelectODS: (id: string) => void;
  onCreateODS: () => void;
  onEditODS: (id: string) => void;
}> = ({ onSelectODS, onCreateODS, onEditODS }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ statut?: string; search?: string }>({});
  const deleteIntervention = useDeleteIntervention();

  const { data, isLoading, error, refetch } = useInterventionsList(page, pageSize, filters);

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
      render: (value, row) => {
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
      render: (value, row) => {
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

// ============================================================
// DETAIL VIEW (BaseViewStandard)
// ============================================================

const InterventionDetailView: React.FC<{
  interventionId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
}> = ({ interventionId, onBack, onEdit }) => {
  const { data: intervention, isLoading } = useIntervention(interventionId);
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const [showTerminer, setShowTerminer] = useState(false);
  const [commentaire, setCommentaire] = useState('');

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!intervention) {
    return (
      <PageWrapper title="Intervention non trouvee">
        <Card><p>Cette intervention n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const statutConfig = STATUT_CONFIG[intervention.statut];
  const prioriteConfig = PRIORITE_CONFIG[intervention.priorite];
  const canEdit = canEditIntervention(intervention);
  const canStart = canStartIntervention(intervention);
  const canComplete = canCompleteIntervention(intervention);
  const canInvoice = canInvoiceIntervention(intervention);

  const handleDemarrer = async () => {
    if (window.confirm('Demarrer l\'intervention ?')) {
      await demarrer.mutateAsync(interventionId);
    }
  };

  const handleTerminer = async () => {
    await terminer.mutateAsync({ id: interventionId, data: { commentaire_cloture: commentaire } });
    setShowTerminer(false);
  };

  const handleCreateFacture = () => {
    window.dispatchEvent(new CustomEvent('azals:navigate', {
      detail: { view: 'factures', params: { interventionId, action: 'new' } }
    }));
  };

  // Tab definitions
  const tabs: TabDefinition<Intervention>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Wrench size={16} />,
      component: InterventionInfoTab,
    },
    {
      id: 'planning',
      label: 'Planning',
      icon: <Calendar size={16} />,
      component: InterventionPlanningTab,
    },
    {
      id: 'photos',
      label: 'Photos',
      icon: <FileText size={16} />,
      badge: getPhotoCount(intervention),
      component: InterventionPhotosTab,
    },
    {
      id: 'report',
      label: 'Compte-rendu',
      icon: <CheckCircle2 size={16} />,
      component: InterventionReportTab,
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: InterventionHistoryTab,
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: InterventionIATab,
    },
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'statut',
      label: 'Statut',
      value: statutConfig.label,
      valueColor: statutConfig.color as SemanticColor,
    },
    {
      id: 'priorite',
      label: 'Priorite',
      value: prioriteConfig.label,
      valueColor: prioriteConfig.color as SemanticColor,
    },
    {
      id: 'date',
      label: 'Date prevue',
      value: intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-',
    },
    {
      id: 'duree',
      label: 'Duree',
      value: getActualDuration(intervention) || (intervention.duree_prevue_minutes ? `~${formatDuration(intervention.duree_prevue_minutes)}` : '-'),
    },
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'intervention',
      title: 'Intervention',
      items: [
        { id: 'reference', label: 'Reference', value: intervention.reference },
        { id: 'type', label: 'Type', value: TYPE_INTERVENTION_CONFIG[intervention.type_intervention]?.label || intervention.type_intervention },
        { id: 'age', label: 'Age', value: getInterventionAge(intervention) },
        { id: 'photos', label: 'Photos', value: `${getPhotoCount(intervention)} photo(s)` },
      ],
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'client', label: 'Client', value: intervention.client_name || '-' },
        { id: 'donneur', label: 'Donneur ordre', value: intervention.donneur_ordre_name || '-' },
        { id: 'lieu', label: 'Lieu', value: getFullAddress(intervention) || '-' },
        { id: 'contact', label: 'Contact', value: intervention.contact_sur_place || '-' },
      ],
    },
    {
      id: 'planning',
      title: 'Planning',
      items: [
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_name || 'Non assigne', highlight: !intervention.intervenant_name },
        { id: 'date', label: 'Date', value: intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-' },
        { id: 'duree', label: 'Duree prevue', value: intervention.duree_prevue_minutes ? formatDuration(intervention.duree_prevue_minutes) : '-' },
      ],
    },
    {
      id: 'facturation',
      title: 'Facturation',
      items: [
        { id: 'facturable', label: 'Facturable', value: intervention.facturable !== false ? 'Oui' : 'Non' },
        { id: 'montant', label: 'Montant HT', value: intervention.montant_ht ? formatCurrency(intervention.montant_ht) : '-' },
        { id: 'facture', label: 'Facture', value: intervention.facture_reference || '-' },
      ],
    },
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      variant: 'ghost',
      onClick: onBack,
    },
    ...(canInvoice ? [{
      id: 'invoice',
      label: 'Creer facture',
      icon: <FileText size={16} />,
      onClick: handleCreateFacture,
    }] : []),
    ...(canComplete ? [{
      id: 'complete',
      label: 'Terminer',
      icon: <CheckCircle2 size={16} />,
      onClick: () => setShowTerminer(true),
    }] : []),
    ...(canStart ? [{
      id: 'start',
      label: 'Demarrer',
      variant: 'secondary' as const,
      icon: <Play size={16} />,
      onClick: handleDemarrer,
    }] : []),
    ...(canEdit ? [{
      id: 'edit',
      label: 'Modifier',
      variant: 'ghost' as const,
      icon: <Edit size={16} />,
      onClick: () => onEdit(interventionId),
    }] : []),
    {
      id: 'pdf',
      label: 'PDF',
      variant: 'ghost',
      icon: <Download size={16} />,
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'downloadPDF', interventionId } })); },
    },
  ];

  return (
    <>
      <BaseViewStandard<Intervention>
        title={intervention.reference}
        subtitle={intervention.titre}
        status={{
          label: statutConfig.label,
          color: statutConfig.color as SemanticColor,
        }}
        data={intervention}
        view="detail"
        tabs={tabs}
        infoBarItems={infoBarItems}
        sidebarSections={sidebarSections}
        headerActions={headerActions}
      />

      {/* Modal Terminer */}
      {showTerminer && (
        <div className="azals-modal-overlay">
          <div className="azals-modal">
            <h3>Terminer l'intervention</h3>
            <div className="azals-form-field">
              <label>Commentaire de cloture</label>
              <textarea
                className="azals-textarea"
                value={commentaire}
                onChange={(e) => setCommentaire(e.target.value)}
                rows={4}
                placeholder="Travaux effectues, remarques..."
              />
            </div>
            <div className="azals-modal__actions">
              <Button variant="ghost" onClick={() => setShowTerminer(false)}>Annuler</Button>
              <Button onClick={handleTerminer} isLoading={terminer.isPending}>Terminer</Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ============================================================
// FORM VIEW
// ============================================================

const ODSFormView: React.FC<{
  interventionId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ interventionId, onBack, onSaved }) => {
  const isNew = !interventionId;
  const { data: intervention } = useIntervention(interventionId || '');
  const { data: donneursOrdre } = useDonneursOrdre();
  const { data: clients } = useClients();
  const { data: intervenants } = useIntervenants();
  const createIntervention = useCreateIntervention();
  const updateIntervention = useUpdateIntervention();

  const [form, setForm] = useState({
    // Obligatoire
    client_id: '',
    // Classification
    type_intervention: 'AUTRE' as TypeIntervention,
    priorite: 'NORMAL' as InterventionPriorite,
    corps_etat: '' as CorpsEtat | '',
    canal_demande: '' as CanalDemande | '',
    reference_externe: '',
    // Details
    titre: '',
    description: '',
    notes_internes: '',
    notes_client: '',
    // Relations
    donneur_ordre_id: '',
    projet_id: '',
    affaire_id: '',
    // Adresse
    adresse_ligne1: '',
    adresse_ligne2: '',
    ville: '',
    code_postal: '',
    // Contact sur place
    contact_sur_place: '',
    telephone_contact: '',
    email_contact: '',
    // Planification
    date_prevue_debut: '',
    date_prevue_fin: '',
    duree_prevue_minutes: 60,
    intervenant_id: '',
    // Materiel
    materiel_necessaire: '',
    // Facturation
    facturable: true,
    montant_ht: 0,
    montant_ttc: 0,
  });

  React.useEffect(() => {
    if (intervention) {
      setForm({
        client_id: intervention.client_id || '',
        type_intervention: intervention.type_intervention || 'AUTRE',
        priorite: intervention.priorite || 'NORMAL',
        corps_etat: intervention.corps_etat || '',
        canal_demande: intervention.canal_demande || '',
        reference_externe: intervention.reference_externe || '',
        titre: intervention.titre || '',
        description: intervention.description || '',
        notes_internes: intervention.notes_internes || '',
        notes_client: intervention.notes_client || '',
        donneur_ordre_id: intervention.donneur_ordre_id || '',
        projet_id: intervention.projet_id || '',
        affaire_id: intervention.affaire_id || '',
        adresse_ligne1: intervention.adresse_ligne1 || '',
        adresse_ligne2: intervention.adresse_ligne2 || '',
        ville: intervention.ville || '',
        code_postal: intervention.code_postal || '',
        contact_sur_place: intervention.contact_sur_place || '',
        telephone_contact: intervention.telephone_contact || '',
        email_contact: intervention.email_contact || '',
        date_prevue_debut: intervention.date_prevue_debut ? intervention.date_prevue_debut.slice(0, 16) : '',
        date_prevue_fin: intervention.date_prevue_fin ? intervention.date_prevue_fin.slice(0, 16) : '',
        duree_prevue_minutes: intervention.duree_prevue_minutes || 60,
        intervenant_id: intervention.intervenant_id || '',
        materiel_necessaire: intervention.materiel_necessaire || '',
        facturable: intervention.facturable !== false,
        montant_ht: intervention.montant_ht || 0,
        montant_ttc: intervention.montant_ttc || 0,
      });
    }
  }, [intervention]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.titre) {
      alert('Veuillez saisir un titre');
      return;
    }
    // Convertir les valeurs vides en undefined pour la compatibilite avec le type
    const submitData: Partial<Intervention> = {
      ...form,
      corps_etat: form.corps_etat || undefined,
      canal_demande: form.canal_demande || undefined,
    };
    try {
      if (isNew) {
        const result = await createIntervention.mutateAsync(submitData);
        onSaved(result.id);
      } else {
        await updateIntervention.mutateAsync({ id: interventionId!, data: submitData });
        onSaved(interventionId!);
      }
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const isSubmitting = createIntervention.isPending || updateIntervention.isPending;

  return (
    <PageWrapper
      title={isNew ? 'Nouvel ordre de service' : 'Modifier l\'intervention'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Card title="Classification">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Client *</label>
              <select
                className="azals-select"
                value={form.client_id}
                onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                required
              >
                <option value="">-- Selectionner --</option>
                {clients?.map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Donneur d'ordre</label>
              <select
                className="azals-select"
                value={form.donneur_ordre_id}
                onChange={(e) => setForm({ ...form, donneur_ordre_id: e.target.value })}
              >
                <option value="">-- Selectionner --</option>
                {donneursOrdre?.map(d => (
                  <option key={d.id} value={d.id}>{d.nom}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Reference externe</label>
              <input
                type="text"
                className="azals-input"
                value={form.reference_externe}
                onChange={(e) => setForm({ ...form, reference_externe: e.target.value })}
                placeholder="Ref. client..."
              />
            </div>
            <div className="azals-form-field">
              <label>Type d'intervention</label>
              <select
                className="azals-select"
                value={form.type_intervention}
                onChange={(e) => setForm({ ...form, type_intervention: e.target.value as TypeIntervention })}
              >
                {TYPES_INTERVENTION.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Priorite</label>
              <select
                className="azals-select"
                value={form.priorite}
                onChange={(e) => setForm({ ...form, priorite: e.target.value as InterventionPriorite })}
              >
                {PRIORITES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Corps d'etat</label>
              <select
                className="azals-select"
                value={form.corps_etat}
                onChange={(e) => setForm({ ...form, corps_etat: e.target.value as CorpsEtat })}
              >
                <option value="">-- Selectionner --</option>
                {CORPS_ETATS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Canal de demande</label>
              <select
                className="azals-select"
                value={form.canal_demande}
                onChange={(e) => setForm({ ...form, canal_demande: e.target.value as CanalDemande })}
              >
                <option value="">-- Selectionner --</option>
                {CANAUX_DEMANDE.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Details">
          <Grid cols={2} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Titre</label>
              <input
                type="text"
                className="azals-input"
                value={form.titre}
                onChange={(e) => setForm({ ...form, titre: e.target.value })}
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Description</label>
              <textarea
                className="azals-textarea"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="azals-form-field">
              <label>Notes internes</label>
              <textarea
                className="azals-textarea"
                value={form.notes_internes}
                onChange={(e) => setForm({ ...form, notes_internes: e.target.value })}
                rows={2}
                placeholder="Notes visibles uniquement en interne..."
              />
            </div>
            <div className="azals-form-field">
              <label>Notes client</label>
              <textarea
                className="azals-textarea"
                value={form.notes_client}
                onChange={(e) => setForm({ ...form, notes_client: e.target.value })}
                rows={2}
                placeholder="Notes visibles par le client..."
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Materiel necessaire</label>
              <textarea
                className="azals-textarea"
                value={form.materiel_necessaire}
                onChange={(e) => setForm({ ...form, materiel_necessaire: e.target.value })}
                rows={2}
                placeholder="Liste du materiel a prevoir..."
              />
            </div>
          </Grid>
        </Card>

        <Card title="Lieu d'intervention">
          <Grid cols={3} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Adresse ligne 1</label>
              <input
                type="text"
                className="azals-input"
                value={form.adresse_ligne1}
                onChange={(e) => setForm({ ...form, adresse_ligne1: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Adresse ligne 2</label>
              <input
                type="text"
                className="azals-input"
                value={form.adresse_ligne2}
                onChange={(e) => setForm({ ...form, adresse_ligne2: e.target.value })}
                placeholder="Batiment, etage..."
              />
            </div>
            <div className="azals-form-field">
              <label>Code postal</label>
              <input
                type="text"
                className="azals-input"
                value={form.code_postal}
                onChange={(e) => setForm({ ...form, code_postal: e.target.value })}
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Ville</label>
              <input
                type="text"
                className="azals-input"
                value={form.ville}
                onChange={(e) => setForm({ ...form, ville: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Contact sur place">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Nom du contact</label>
              <input
                type="text"
                className="azals-input"
                value={form.contact_sur_place}
                onChange={(e) => setForm({ ...form, contact_sur_place: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Telephone</label>
              <input
                type="tel"
                className="azals-input"
                value={form.telephone_contact}
                onChange={(e) => setForm({ ...form, telephone_contact: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Email</label>
              <input
                type="email"
                className="azals-input"
                value={form.email_contact}
                onChange={(e) => setForm({ ...form, email_contact: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Planification">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label>Date/heure debut</label>
              <input
                type="datetime-local"
                className="azals-input"
                value={form.date_prevue_debut}
                onChange={(e) => setForm({ ...form, date_prevue_debut: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Date/heure fin</label>
              <input
                type="datetime-local"
                className="azals-input"
                value={form.date_prevue_fin}
                onChange={(e) => setForm({ ...form, date_prevue_fin: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Duree prevue (minutes)</label>
              <input
                type="number"
                className="azals-input"
                value={form.duree_prevue_minutes}
                onChange={(e) => setForm({ ...form, duree_prevue_minutes: parseInt(e.target.value) || 0 })}
                min="0"
                step="15"
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 3' }}>
              <label>Intervenant</label>
              <select
                className="azals-select"
                value={form.intervenant_id}
                onChange={(e) => setForm({ ...form, intervenant_id: e.target.value })}
              >
                <option value="">-- Non assigne --</option>
                {intervenants?.map(i => (
                  <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                ))}
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Facturation">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.facturable}
                  onChange={(e) => setForm({ ...form, facturable: e.target.checked })}
                />
                Intervention facturable
              </label>
            </div>
            <div className="azals-form-field">
              <label>Montant HT (EUR)</label>
              <input
                type="number"
                className="azals-input"
                value={form.montant_ht}
                onChange={(e) => setForm({ ...form, montant_ht: parseFloat(e.target.value) || 0 })}
                min="0"
                step="10"
                disabled={!form.facturable}
              />
            </div>
            <div className="azals-form-field">
              <label>Montant TTC (EUR)</label>
              <input
                type="number"
                className="azals-input"
                value={form.montant_ttc}
                onChange={(e) => setForm({ ...form, montant_ttc: parseFloat(e.target.value) || 0 })}
                min="0"
                step="10"
                disabled={!form.facturable}
              />
            </div>
          </Grid>
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Creer' : 'Enregistrer'}</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// DONNEURS D'ORDRE VIEW
// ============================================================

const DonneursOrdreView: React.FC<{
  onBack: () => void;
}> = ({ onBack }) => {
  const { data: donneursOrdre, isLoading, refetch } = useDonneursOrdre();
  const { data: clients } = useClients();
  const createDonneurOrdre = useCreateDonneurOrdre();
  const updateDonneurOrdre = useUpdateDonneurOrdre();
  const deleteDonneurOrdre = useDeleteDonneurOrdre();

  const [showModal, setShowModal] = useState(false);
  const [editingDonneur, setEditingDonneur] = useState<DonneurOrdre | null>(null);
  const [form, setForm] = useState({
    code: '',
    nom: '',
    type: '',
    client_id: '',
    email: '',
    telephone: '',
    adresse: '',
    is_active: true,
  });

  const resetForm = () => {
    setForm({
      code: '',
      nom: '',
      type: '',
      client_id: '',
      email: '',
      telephone: '',
      adresse: '',
      is_active: true,
    });
    setEditingDonneur(null);
  };

  const openCreate = () => {
    resetForm();
    setShowModal(true);
  };

  const openEdit = (donneur: DonneurOrdre) => {
    setEditingDonneur(donneur);
    setForm({
      code: donneur.code || '',
      nom: donneur.nom || '',
      type: donneur.type || '',
      client_id: donneur.client_id || '',
      email: donneur.email || '',
      telephone: donneur.telephone || '',
      adresse: donneur.adresse || '',
      is_active: donneur.is_active !== false,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code || !form.nom) {
      alert('Veuillez remplir le code et le nom');
      return;
    }
    try {
      if (editingDonneur) {
        await updateDonneurOrdre.mutateAsync({ id: editingDonneur.id, data: form });
      } else {
        await createDonneurOrdre.mutateAsync(form);
      }
      setShowModal(false);
      resetForm();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const handleDelete = async (donneur: DonneurOrdre) => {
    if (window.confirm(`Supprimer le donneur d'ordre "${donneur.nom}" ?`)) {
      await deleteDonneurOrdre.mutateAsync(donneur.id);
    }
  };

  const columns: TableColumn<DonneurOrdre>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
    },
    {
      id: 'nom',
      header: 'Nom',
      accessor: 'nom',
      sortable: true,
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (value) => (value ? String(value) : <span className="text-muted">-</span>),
    },
    {
      id: 'email',
      header: 'Email',
      accessor: 'email',
      render: (value) => (value ? String(value) : <span className="text-muted">-</span>),
    },
    {
      id: 'telephone',
      header: 'Telephone',
      accessor: 'telephone',
      render: (value) => (value ? String(value) : <span className="text-muted">-</span>),
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (value) => (
        <span className={`azals-badge azals-badge--${value !== false ? 'green' : 'gray'}`}>
          {value !== false ? 'Oui' : 'Non'}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (value, row) => (
        <div className="azals-table-actions">
          <button
            className="azals-btn-icon"
            onClick={() => openEdit(row)}
            title="Modifier"
          >
            <Edit size={16} />
          </button>
          <button
            className="azals-btn-icon azals-btn-icon--danger"
            onClick={() => handleDelete(row)}
            title="Supprimer"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ),
    },
  ];

  const isSubmitting = createDonneurOrdre.isPending || updateDonneurOrdre.isPending;

  return (
    <PageWrapper
      title="Donneurs d'ordre"
      subtitle="Gestion des donneurs d'ordre"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={openCreate}>
          Nouveau donneur d'ordre
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={donneursOrdre || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          onRefresh={refetch}
          emptyMessage="Aucun donneur d'ordre"
        />
      </Card>

      {/* Modal creation/edition */}
      {showModal && (
        <div className="azals-modal-overlay">
          <div className="azals-modal">
            <h3>{editingDonneur ? 'Modifier le donneur d\'ordre' : 'Nouveau donneur d\'ordre'}</h3>
            <form onSubmit={handleSubmit}>
              <Grid cols={2} gap="md">
                <div className="azals-form-field">
                  <label>Code *</label>
                  <input
                    type="text"
                    className="azals-input"
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value })}
                    required
                    disabled={!!editingDonneur}
                  />
                </div>
                <div className="azals-form-field">
                  <label>Nom *</label>
                  <input
                    type="text"
                    className="azals-input"
                    value={form.nom}
                    onChange={(e) => setForm({ ...form, nom: e.target.value })}
                    required
                  />
                </div>
                <div className="azals-form-field">
                  <label>Type</label>
                  <select
                    className="azals-select"
                    value={form.type}
                    onChange={(e) => setForm({ ...form, type: e.target.value })}
                  >
                    <option value="">-- Selectionner --</option>
                    <option value="client">Client</option>
                    <option value="fournisseur">Fournisseur</option>
                    <option value="partenaire">Partenaire</option>
                    <option value="autre">Autre</option>
                  </select>
                </div>
                <div className="azals-form-field">
                  <label>Client associe</label>
                  <select
                    className="azals-select"
                    value={form.client_id}
                    onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                  >
                    <option value="">-- Aucun --</option>
                    {clients?.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                    ))}
                  </select>
                </div>
                <div className="azals-form-field">
                  <label>Email</label>
                  <input
                    type="email"
                    className="azals-input"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                  />
                </div>
                <div className="azals-form-field">
                  <label>Telephone</label>
                  <input
                    type="tel"
                    className="azals-input"
                    value={form.telephone}
                    onChange={(e) => setForm({ ...form, telephone: e.target.value })}
                  />
                </div>
                <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
                  <label>Adresse</label>
                  <textarea
                    className="azals-textarea"
                    value={form.adresse}
                    onChange={(e) => setForm({ ...form, adresse: e.target.value })}
                    rows={2}
                  />
                </div>
                <div className="azals-form-field">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                    />
                    Actif
                  </label>
                </div>
              </Grid>
              <div className="azals-modal__actions">
                <Button type="button" variant="ghost" onClick={() => { setShowModal(false); resetForm(); }}>
                  Annuler
                </Button>
                <Button type="submit" isLoading={isSubmitting}>
                  {editingDonneur ? 'Enregistrer' : 'Creer'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const OrdresServiceModule: React.FC = () => {
  const [navState, setNavState] = useState<ODSNavState>({ view: 'list' });

  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.id) {
        setNavState({ view: 'detail', interventionId: params.id });
      }
    };
    const handleNavigateDonneurs = () => {
      setNavState({ view: 'donneurs-ordre' });
    };
    window.addEventListener('azals:navigate:ods', handleNavigate as EventListener);
    window.addEventListener('azals:navigate:ods:donneurs', handleNavigateDonneurs as EventListener);
    return () => {
      window.removeEventListener('azals:navigate:ods', handleNavigate as EventListener);
      window.removeEventListener('azals:navigate:ods:donneurs', handleNavigateDonneurs as EventListener);
    };
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', interventionId: id }), []);
  const navigateToForm = useCallback((id?: string) => setNavState({ view: 'form', interventionId: id, isNew: !id }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <InterventionDetailView
          interventionId={navState.interventionId!}
          onBack={navigateToList}
          onEdit={navigateToForm}
        />
      );
    case 'form':
      return (
        <ODSFormView
          interventionId={navState.interventionId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.interventionId!)}
          onSaved={navigateToDetail}
        />
      );
    case 'donneurs-ordre':
      return (
        <DonneursOrdreView
          onBack={navigateToList}
        />
      );
    default:
      return (
        <ODSListView
          onSelectODS={navigateToDetail}
          onCreateODS={() => navigateToForm()}
          onEditODS={navigateToForm}
        />
      );
  }
};

export default OrdresServiceModule;
