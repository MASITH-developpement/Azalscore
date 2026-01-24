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
  Calendar, Clock, Play, CheckCircle2, X
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
  InterventionStatut, InterventionPriorite
} from './types';
import {
  formatDate, formatDateTime, formatCurrency, formatDuration,
  STATUT_CONFIG, PRIORITE_CONFIG, STATUTS, PRIORITES,
  canEditIntervention, canStartIntervention, canCompleteIntervention, canInvoiceIntervention,
  getInterventionAge, getActualDuration, getPhotoCount, getFullAddress
} from './types';
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
      const response = await api.get<PaginatedResponse<Intervention>>(`/v1/interventions?${params}`);
      return response.data;
    },
  });
};

const useIntervention = (id: string) => {
  return useQuery({
    queryKey: ['interventions', id],
    queryFn: async () => {
      const response = await api.get<Intervention>(`/v1/interventions/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useInterventionStats = () => {
  return useQuery({
    queryKey: ['interventions', 'stats'],
    queryFn: async () => {
      const response = await api.get<InterventionStats>('/v1/interventions/stats');
      return response.data;
    },
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<DonneurOrdre[]>('/v1/interventions/donneurs-ordre');
      return response.data;
    },
  });
};

const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      const response = await api.post<Intervention>('/v1/interventions', data);
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
      const response = await api.put<Intervention>(`/v1/interventions/${id}`, data);
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
      const response = await api.post<Intervention>(`/v1/interventions/${id}/demarrer`);
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
      const response = await api.post<Intervention>(`/v1/interventions/${id}/terminer`, data);
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

type ODSView = 'list' | 'detail' | 'form';

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
}> = ({ onSelectODS, onCreateODS }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ statut?: string; search?: string }>({});

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
      id: 'client',
      header: 'Client',
      accessor: 'client_nom',
      render: (value, row) => (
        <div>
          <div>{value as string || row.donneur_ordre_nom || '-'}</div>
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
      accessor: 'date_prevue',
      render: (value, row) => {
        if (!value) return <span className="text-muted">-</span>;
        const dateStr = formatDate(value as string);
        const heureStr = row.heure_debut || '';
        return (
          <span>
            {dateStr}
            {heureStr && <span className="text-muted"> {heureStr}</span>}
          </span>
        );
      },
    },
    {
      id: 'intervenant',
      header: 'Intervenant',
      accessor: 'intervenant_nom',
      render: (value) => (value ? String(value) : <span className="text-muted">-</span>),
    },
  ];

  return (
    <PageWrapper
      title="Ordres de Service"
      subtitle="Gestion des interventions et travaux"
      actions={<Button leftIcon={<Plus size={16} />} onClick={onCreateODS}>Nouvelle intervention</Button>}
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
      label: 'IA',
      icon: <Wrench size={16} />,
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
      value: intervention.date_prevue ? formatDate(intervention.date_prevue) : '-',
    },
    {
      id: 'duree',
      label: 'Duree',
      value: getActualDuration(intervention) || (intervention.duree_estimee_minutes ? `~${formatDuration(intervention.duree_estimee_minutes)}` : '-'),
    },
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'intervention',
      title: 'Intervention',
      items: [
        { id: 'reference', label: 'Reference', value: intervention.reference },
        { id: 'age', label: 'Age', value: getInterventionAge(intervention) },
        { id: 'photos', label: 'Photos', value: `${getPhotoCount(intervention)} photo(s)` },
      ],
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'client', label: 'Client', value: intervention.client_nom || '-' },
        { id: 'donneur', label: 'Donneur ordre', value: intervention.donneur_ordre_nom || '-' },
        { id: 'lieu', label: 'Lieu', value: getFullAddress(intervention) || '-' },
      ],
    },
    {
      id: 'planning',
      title: 'Planning',
      items: [
        { id: 'intervenant', label: 'Intervenant', value: intervention.intervenant_nom || 'Non assigne', highlight: !intervention.intervenant_nom },
        { id: 'heure', label: 'Heure', value: intervention.heure_debut || '-' },
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
      onClick: () => console.log('Download PDF'),
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
  const createIntervention = useCreateIntervention();
  const updateIntervention = useUpdateIntervention();

  const [form, setForm] = useState({
    titre: '',
    description: '',
    priorite: 'NORMALE' as InterventionPriorite,
    donneur_ordre_id: '',
    adresse_intervention: '',
    ville: '',
    code_postal: '',
    duree_estimee_minutes: 60,
    montant_estime: 0,
  });

  React.useEffect(() => {
    if (intervention) {
      setForm({
        titre: intervention.titre || '',
        description: intervention.description || '',
        priorite: intervention.priorite,
        donneur_ordre_id: intervention.donneur_ordre_id || '',
        adresse_intervention: intervention.adresse_intervention || '',
        ville: intervention.ville || '',
        code_postal: intervention.code_postal || '',
        duree_estimee_minutes: intervention.duree_estimee_minutes || 60,
        montant_estime: intervention.montant_estime || 0,
      });
    }
  }, [intervention]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.titre) {
      alert('Veuillez saisir un titre');
      return;
    }
    try {
      if (isNew) {
        const result = await createIntervention.mutateAsync(form);
        onSaved(result.id);
      } else {
        await updateIntervention.mutateAsync({ id: interventionId!, data: form });
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
        <Card title="Informations">
          <Grid cols={2} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Titre *</label>
              <input
                type="text"
                className="azals-input"
                value={form.titre}
                onChange={(e) => setForm({ ...form, titre: e.target.value })}
                required
              />
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
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Description</label>
              <textarea
                className="azals-textarea"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Lieu d'intervention">
          <Grid cols={3} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 3' }}>
              <label>Adresse</label>
              <input
                type="text"
                className="azals-input"
                value={form.adresse_intervention}
                onChange={(e) => setForm({ ...form, adresse_intervention: e.target.value })}
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

        <Card title="Estimation">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Duree estimee (minutes)</label>
              <input
                type="number"
                className="azals-input"
                value={form.duree_estimee_minutes}
                onChange={(e) => setForm({ ...form, duree_estimee_minutes: parseInt(e.target.value) || 0 })}
                min="0"
                step="15"
              />
            </div>
            <div className="azals-form-field">
              <label>Montant estime (EUR)</label>
              <input
                type="number"
                className="azals-input"
                value={form.montant_estime}
                onChange={(e) => setForm({ ...form, montant_estime: parseFloat(e.target.value) || 0 })}
                min="0"
                step="10"
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
    window.addEventListener('azals:navigate:ods', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:ods', handleNavigate as EventListener);
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
    default:
      return (
        <ODSListView
          onSelectODS={navigateToDetail}
          onCreateODS={() => navigateToForm()}
        />
      );
  }
};

export default OrdresServiceModule;
