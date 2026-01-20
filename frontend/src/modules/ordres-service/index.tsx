/**
 * AZALSCORE Module - ORDRES DE SERVICE (ODS)
 * Gestion des interventions et travaux
 * Flux : CRM → DEV → [ODS] → AFF → FAC/AVO → CPT
 * Numérotation : ODS-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Wrench, Plus, Edit, Search, Check, X,
  Euro, Calendar, Building2, MapPin, User, Clock,
  CheckCircle2, AlertTriangle, Play, Pause, Camera,
  FileText, Download, ChevronRight
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// ============================================================
// TYPES
// ============================================================

type InterventionStatut = 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'TERMINEE' | 'ANNULEE';
type InterventionPriorite = 'BASSE' | 'NORMALE' | 'HAUTE' | 'URGENTE';

interface Intervention {
  id: string;
  reference: string; // ODS-YY-MM-XXXX
  titre: string;
  description?: string;
  statut: InterventionStatut;
  priorite: InterventionPriorite;
  client_id?: string;
  client_nom?: string;
  donneur_ordre_id?: string;
  donneur_ordre_nom?: string;
  projet_id?: string;
  projet_nom?: string;
  adresse_intervention?: string;
  ville?: string;
  code_postal?: string;
  intervenant_id?: string;
  intervenant_nom?: string;
  date_prevue?: string;
  heure_debut?: string;
  heure_fin?: string;
  duree_estimee_minutes?: number;
  duree_reelle_minutes?: number;
  date_arrivee?: string;
  date_debut_intervention?: string;
  date_fin_intervention?: string;
  commentaire_cloture?: string;
  photos?: string[];
  signature_client?: string;
  montant_estime?: number;
  montant_reel?: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface DonneurOrdre {
  id: string;
  nom: string;
  code?: string;
  contact_nom?: string;
  contact_email?: string;
  contact_telephone?: string;
}

interface InterventionStats {
  total: number;
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  terminees: number;
  annulees: number;
}

// ============================================================
// CONSTANTS
// ============================================================

const STATUT_CONFIG: Record<InterventionStatut, { label: string; color: string; icon: React.ReactNode }> = {
  A_PLANIFIER: { label: 'À planifier', color: 'gray', icon: <Calendar size={14} /> },
  PLANIFIEE: { label: 'Planifiée', color: 'blue', icon: <Clock size={14} /> },
  EN_COURS: { label: 'En cours', color: 'yellow', icon: <Play size={14} /> },
  TERMINEE: { label: 'Terminée', color: 'green', icon: <CheckCircle2 size={14} /> },
  ANNULEE: { label: 'Annulée', color: 'red', icon: <X size={14} /> },
};

const PRIORITE_CONFIG: Record<InterventionPriorite, { label: string; color: string }> = {
  BASSE: { label: 'Basse', color: 'gray' },
  NORMALE: { label: 'Normale', color: 'blue' },
  HAUTE: { label: 'Haute', color: 'orange' },
  URGENTE: { label: 'Urgente', color: 'red' },
};

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (value: number): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);

const formatDate = (date: string): string =>
  new Date(date).toLocaleDateString('fr-FR');

const formatDateTime = (date: string): string =>
  new Date(date).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });

const formatDuration = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h${mins > 0 ? mins : ''}` : `${mins}min`;
};

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

const usePlanifierIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { date_prevue: string; heure_debut?: string; intervenant_id?: string } }) => {
      const response = await api.post<Intervention>(`/v1/interventions/${id}/planifier`, data);
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
// COMPONENTS
// ============================================================

const StatutBadge: React.FC<{ statut: InterventionStatut }> = ({ statut }) => {
  const config = STATUT_CONFIG[statut];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
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
    { id: 'planifier', label: 'À planifier', value: stats.a_planifier, icon: <Calendar size={20} />, variant: stats.a_planifier > 0 ? 'warning' : undefined },
    { id: 'planifiees', label: 'Planifiées', value: stats.planifiees, icon: <Clock size={20} /> },
    { id: 'encours', label: 'En cours', value: stats.en_cours, icon: <Play size={20} /> },
    { id: 'terminees', label: 'Terminées', value: stats.terminees, icon: <CheckCircle2 size={20} /> },
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
// LIST
// ============================================================

const ODSListInternal: React.FC<{
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
      header: 'Référence',
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
      header: 'Priorité',
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
      header: 'Date prévue',
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
            {Object.entries(STATUT_CONFIG).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
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
// DETAIL
// ============================================================

const ODSDetailInternal: React.FC<{
  interventionId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ interventionId, onBack, onEdit }) => {
  const { data: intervention, isLoading } = useIntervention(interventionId);
  const demarrer = useDemarrerIntervention();
  const terminer = useTerminerIntervention();
  const [showTerminer, setShowTerminer] = useState(false);
  const [commentaire, setCommentaire] = useState('');

  const handleDemarrer = async () => {
    if (window.confirm('Démarrer l\'intervention ?')) {
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

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!intervention) {
    return (
      <PageWrapper title="Intervention non trouvée">
        <Card><p>Cette intervention n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const canEdit = ['A_PLANIFIER', 'PLANIFIEE'].includes(intervention.statut);
  const canDemarrer = intervention.statut === 'PLANIFIEE';
  const canTerminer = intervention.statut === 'EN_COURS';
  const canFacturer = intervention.statut === 'TERMINEE';

  return (
    <PageWrapper
      title={intervention.reference}
      subtitle={intervention.titre}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <ButtonGroup>
          {canFacturer && (
            <Button leftIcon={<FileText size={16} />} onClick={handleCreateFacture}>
              Créer facture
            </Button>
          )}
          {canTerminer && (
            <Button leftIcon={<CheckCircle2 size={16} />} onClick={() => setShowTerminer(true)}>
              Terminer
            </Button>
          )}
          {canDemarrer && (
            <Button variant="secondary" leftIcon={<Play size={16} />} onClick={handleDemarrer} isLoading={demarrer.isPending}>
              Démarrer
            </Button>
          )}
          {canEdit && (
            <Button variant="ghost" leftIcon={<Edit size={16} />} onClick={onEdit}>Modifier</Button>
          )}
          <Button variant="ghost" leftIcon={<Download size={16} />}>PDF</Button>
        </ButtonGroup>
      }
    >
      <Grid cols={4} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <StatutBadge statut={intervention.statut} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Priorité</span>
            <PrioriteBadge priorite={intervention.priorite} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Date prévue</span>
            <span className="azals-stat__value">
              {intervention.date_prevue ? formatDate(intervention.date_prevue) : '-'}
            </span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Durée</span>
            <span className="azals-stat__value">
              {intervention.duree_reelle_minutes
                ? formatDuration(intervention.duree_reelle_minutes)
                : intervention.duree_estimee_minutes
                  ? `~${formatDuration(intervention.duree_estimee_minutes)}`
                  : '-'}
            </span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg" className="mb-4">
        <Card title="Client / Donneur d'ordre">
          <dl className="azals-dl">
            {intervention.client_nom && (
              <><dt><Building2 size={14} /> Client</dt><dd>{intervention.client_nom}</dd></>
            )}
            {intervention.donneur_ordre_nom && (
              <><dt><User size={14} /> Donneur d'ordre</dt><dd>{intervention.donneur_ordre_nom}</dd></>
            )}
            {intervention.adresse_intervention && (
              <>
                <dt><MapPin size={14} /> Lieu d'intervention</dt>
                <dd>
                  <div>{intervention.adresse_intervention}</div>
                  {intervention.ville && <div>{intervention.code_postal} {intervention.ville}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Planning">
          <dl className="azals-dl">
            {intervention.intervenant_nom && (
              <><dt><User size={14} /> Intervenant</dt><dd>{intervention.intervenant_nom}</dd></>
            )}
            {intervention.date_prevue && (
              <>
                <dt><Calendar size={14} /> Date prévue</dt>
                <dd>
                  {formatDate(intervention.date_prevue)}
                  {intervention.heure_debut && ` à ${intervention.heure_debut}`}
                </dd>
              </>
            )}
            {intervention.date_arrivee && (
              <><dt>Arrivée</dt><dd>{formatDateTime(intervention.date_arrivee)}</dd></>
            )}
            {intervention.date_fin_intervention && (
              <><dt>Fin</dt><dd>{formatDateTime(intervention.date_fin_intervention)}</dd></>
            )}
          </dl>
        </Card>
      </Grid>

      <Card title="Description">
        <p className="text-muted">{intervention.description || 'Aucune description'}</p>
      </Card>

      {intervention.commentaire_cloture && (
        <Card title="Compte-rendu" className="mt-4">
          <p className="text-muted">{intervention.commentaire_cloture}</p>
        </Card>
      )}

      {intervention.photos && intervention.photos.length > 0 && (
        <Card title="Photos" className="mt-4">
          <div className="azals-photo-grid">
            {intervention.photos.map((url, i) => (
              <img key={i} src={url} alt={`Photo ${i + 1}`} className="azals-photo-grid__item" />
            ))}
          </div>
        </Card>
      )}

      {canFacturer && (
        <Card className="mt-4">
          <div className="azals-action-card">
            <div>
              <h4>Prochaine étape</h4>
              <p className="text-muted">Cette intervention est terminée, vous pouvez créer la facture</p>
            </div>
            <Button leftIcon={<ChevronRight size={16} />} onClick={handleCreateFacture}>
              Créer facture
            </Button>
          </div>
        </Card>
      )}

      {showTerminer && (
        <div className="azals-modal-overlay">
          <div className="azals-modal">
            <h3>Terminer l'intervention</h3>
            <div className="azals-form-field">
              <label>Commentaire de clôture</label>
              <textarea
                className="azals-textarea"
                value={commentaire}
                onChange={(e) => setCommentaire(e.target.value)}
                rows={4}
                placeholder="Travaux effectués, remarques..."
              />
            </div>
            <div className="azals-modal__actions">
              <Button variant="ghost" onClick={() => setShowTerminer(false)}>Annuler</Button>
              <Button onClick={handleTerminer} isLoading={terminer.isPending}>Terminer</Button>
            </div>
          </div>
        </div>
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORM
// ============================================================

const ODSFormInternal: React.FC<{
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
                <option value="">-- Sélectionner --</option>
                {donneursOrdre?.map(d => (
                  <option key={d.id} value={d.id}>{d.nom}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Priorité</label>
              <select
                className="azals-select"
                value={form.priorite}
                onChange={(e) => setForm({ ...form, priorite: e.target.value as InterventionPriorite })}
              >
                {Object.entries(PRIORITE_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
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
              <label>Durée estimée (minutes)</label>
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
              <label>Montant estimé (€)</label>
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
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Créer' : 'Enregistrer'}</Button>
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
        <ODSDetailInternal
          interventionId={navState.interventionId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.interventionId)}
        />
      );
    case 'form':
      return (
        <ODSFormInternal
          interventionId={navState.interventionId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.interventionId!)}
          onSaved={navigateToDetail}
        />
      );
    default:
      return (
        <ODSListInternal
          onSelectODS={navigateToDetail}
          onCreateODS={() => navigateToForm()}
        />
      );
  }
};

export default OrdresServiceModule;
