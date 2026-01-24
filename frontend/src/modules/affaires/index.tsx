/**
 * AZALSCORE Module - AFFAIRES
 * ===========================
 *
 * Module simplifié utilisant SmartField
 * Les permissions contrôlent automatiquement les modes:
 * - projects.view  → lecture seule
 * - projects.edit  → modification
 * - projects.create → création
 */

import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Briefcase, Euro, Calendar, Target, Edit, Eye, Plus, ArrowLeft } from 'lucide-react';
import { api } from '@core/api-client';
import {
  Page, PageHeader, Section, Grid, Stats, SearchBar, SimpleTable,
  Badge, Progress, Totals, Footer, Button, Loading,
  formatCurrency, formatDate,
  SmartField, SmartForm, useModulePermissions,
} from '@ui/simple';
import type { FieldMode, ContextMode, EntityConfig } from '@ui/simple';

// ============================================================
// TYPES & CONFIG
// ============================================================

type Status = 'draft' | 'planning' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled';
type Priority = 'low' | 'medium' | 'high' | 'critical';

interface Affaire {
  id: string;
  reference?: string;
  code?: string;
  name: string;
  description?: string;
  customer_id?: string;
  customer_name?: string;
  status: Status;
  priority: Priority;
  progress_percent?: number;
  planned_budget?: number;
  actual_cost?: number;
  planned_start_date?: string;
  planned_end_date?: string;
}

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'planning', label: 'Planification' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'on_hold', label: 'En pause' },
  { value: 'completed', label: 'Terminé' },
  { value: 'cancelled', label: 'Annulé' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Basse' },
  { value: 'medium', label: 'Normale' },
  { value: 'high', label: 'Haute' },
  { value: 'critical', label: 'Urgente' },
];

// Configuration du sélecteur de client
const CLIENT_ENTITY: EntityConfig = {
  endpoint: '/v1/partners/clients',
  displayField: 'name',
  secondaryField: 'code',
  searchField: 'search',
  createFields: [
    { key: 'name', label: 'Nom du client', type: 'text', required: true },
    { key: 'code', label: 'Code', type: 'text', autoGenerate: true },
    { key: 'email', label: 'Email', type: 'email' },
    { key: 'phone', label: 'Téléphone', type: 'tel' },
  ],
};

const getStatusLabel = (s: Status) => STATUS_OPTIONS.find(x => x.value === s)?.label || s;

// ============================================================
// API HOOKS
// ============================================================

const useAffaires = (search?: string) => useQuery({
  queryKey: ['affaires', search],
  queryFn: async () => {
    const params = search ? `?search=${search}&limit=100` : '?limit=100';
    const res = await api.get(`/v1/projects${params}`);
    return (res as any).items || [];
  },
});

const useAffaire = (id?: string) => useQuery({
  queryKey: ['affaire', id],
  queryFn: () => api.get(`/v1/projects/${id}`),
  enabled: !!id,
});

const useSaveAffaire = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id?: string; data: Partial<Affaire> }) => {
      const payload = id ? data : {
        ...data,
        code: data.code || `AFF-${Date.now().toString(36).toUpperCase()}`,
      };
      return id ? api.put(`/v1/projects/${id}`, payload) : api.post('/v1/projects', payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['affaires'] });
      qc.invalidateQueries({ queryKey: ['affaire'] });
    },
  });
};

// ============================================================
// LIST VIEW
// ============================================================

const List: React.FC<{
  onSelect: (id: string) => void;
  onCreate: () => void;
  canCreate: boolean;
}> = ({ onSelect, onCreate, canCreate }) => {
  const [search, setSearch] = useState('');
  const { data: affaires = [], isLoading } = useAffaires(search);

  const stats = useMemo(() => {
    const a = affaires as Affaire[];
    return [
      { label: 'Total', value: a.length },
      { label: 'En cours', value: a.filter(x => x.status === 'in_progress').length, variant: 'warning' as const },
      { label: 'Terminées', value: a.filter(x => x.status === 'completed').length, variant: 'success' as const },
      { label: 'CA Total', value: formatCurrency(a.reduce((s, x) => s + (x.planned_budget || 0), 0)) },
    ];
  }, [affaires]);

  if (isLoading) return <Loading />;

  return (
    <Page>
      <PageHeader
        title="Affaires"
        icon={<Briefcase size={24} />}
        actions={canCreate && (
          <Button icon={<Plus size={18} />} onClick={onCreate}>
            Nouvelle affaire
          </Button>
        )}
      />

      <Stats items={stats} />

      <Section>
        <SearchBar value={search} onChange={setSearch} placeholder="Rechercher une affaire..." />
      </Section>

      <Section>
        <SimpleTable<Affaire>
          keyField="id"
          data={affaires as Affaire[]}
          onRowClick={(row) => onSelect(row.id)}
          emptyMessage="Aucune affaire"
          columns={[
            {
              key: 'reference',
              header: 'Réf.',
              render: (r) => <span className="azals-ws-table__ref">{r.reference || r.code || r.id.slice(0, 8)}</span>,
            },
            { key: 'name', header: 'Nom' },
            { key: 'customer_name', header: 'Client', render: (r) => r.customer_name || '-' },
            {
              key: 'status',
              header: 'Statut',
              render: (r) => <Badge variant={r.status}>{getStatusLabel(r.status)}</Badge>,
            },
            {
              key: 'progress',
              header: 'Avancement',
              render: (r) => <Progress value={r.progress_percent || 0} />,
            },
            {
              key: 'budget',
              header: 'Budget',
              align: 'right',
              render: (r) => formatCurrency(r.planned_budget),
            },
            { key: 'end_date', header: 'Échéance', render: (r) => formatDate(r.planned_end_date) },
          ]}
        />
      </Section>
    </Page>
  );
};

// ============================================================
// FORM VIEW (Detail & Create)
// ============================================================

interface FormViewProps {
  id?: string;
  onBack: () => void;
  onSaved?: (id: string) => void;
  contextMode: ContextMode;
}

const FormView: React.FC<FormViewProps> = ({ id, onBack, onSaved, contextMode }) => {
  const { data, isLoading } = useAffaire(id);
  const save = useSaveAffaire();
  const permissions = useModulePermissions('projects');

  // Déterminer le mode effectif selon les permissions
  const mode: FieldMode = permissions.getMode(contextMode);

  const [editing, setEditing] = useState(contextMode !== 'view');
  const [form, setForm] = useState<Partial<Affaire>>({
    name: '',
    status: 'draft',
    priority: 'medium',
    progress_percent: 0,
  });
  const [saved, setSaved] = useState(false);

  const affaire = data as Affaire | undefined;

  // Charger les données existantes
  useEffect(() => {
    if (affaire) setForm(affaire);
  }, [affaire]);

  // Sauvegarder
  const handleSave = async () => {
    if (!form.name?.trim()) return;
    const res = await save.mutateAsync({ id, data: form });
    setSaved(true);

    if (contextMode === 'create' && onSaved) {
      setTimeout(() => onSaved((res as any).id), 1000);
    } else {
      setEditing(false);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  // Mode effectif pour les champs
  const fieldMode: FieldMode = editing ? (id ? 'edit' : 'create') : 'view';

  // Chargement
  if (id && isLoading) return <Loading />;
  if (id && !affaire) {
    return (
      <Page>
        <PageHeader title="Affaire non trouvée" onBack={onBack} />
        <Section><p>Cette affaire n'existe pas.</p></Section>
      </Page>
    );
  }

  const reste = (affaire?.planned_budget || 0) - (affaire?.actual_cost || 0);

  return (
    <Page>
      <PageHeader
        title={id ? affaire?.name || 'Affaire' : 'Nouvelle affaire'}
        subtitle={id ? (affaire?.reference || affaire?.code) : undefined}
        onBack={onBack}
        date={!id}
        actions={
          id && !editing && permissions.canEdit ? (
            <Button variant="secondary" icon={<Edit size={16} />} onClick={() => setEditing(true)}>
              Modifier
            </Button>
          ) : id && editing ? (
            <Button variant="ghost" onClick={() => { setEditing(false); if (affaire) setForm(affaire); }}>
              Annuler
            </Button>
          ) : null
        }
      />

      {id && affaire && (
        <Section>
          <Badge variant={affaire.status} size="lg">{getStatusLabel(affaire.status)}</Badge>
        </Section>
      )}

      <Section>
        <SmartForm
          mode={fieldMode}
          onSubmit={handleSave}
          onCancel={id ? () => { setEditing(false); if (affaire) setForm(affaire); } : onBack}
          submitLabel={id ? 'Enregistrer' : 'Créer l\'affaire'}
          loading={save.isPending}
          success={saved}
        >
          <SmartField
            label="Nom"
            type="text"
            mode={fieldMode}
            value={form.name}
            onChange={(v) => setForm({ ...form, name: v })}
            placeholder="Ex: Chantier Dupont"
            required
            full
          />

          <SmartField
            label="Client"
            type="entity"
            mode={fieldMode}
            value={form.customer_id}
            onChange={(v) => setForm({ ...form, customer_id: v })}
            entity={CLIENT_ENTITY}
            placeholder="Sélectionner un client..."
            full
          />

          <SmartField
            label="Statut"
            type="select"
            mode={fieldMode}
            value={form.status}
            onChange={(v) => setForm({ ...form, status: v })}
            options={STATUS_OPTIONS}
          />

          <SmartField
            label="Priorité"
            type="select"
            mode={fieldMode}
            value={form.priority}
            onChange={(v) => setForm({ ...form, priority: v })}
            options={PRIORITY_OPTIONS}
          />

          <SmartField
            label="Budget"
            type="number"
            mode={fieldMode}
            value={form.planned_budget}
            onChange={(v) => setForm({ ...form, planned_budget: v })}
            icon={<Euro size={14} />}
            formatValue={(v) => formatCurrency(v)}
            min={0}
            step={0.01}
          />

          <SmartField
            label="Avancement"
            type="number"
            mode={fieldMode}
            value={form.progress_percent}
            onChange={(v) => setForm({ ...form, progress_percent: v })}
            icon={<Target size={14} />}
            formatValue={(v) => `${v || 0}%`}
            min={0}
            max={100}
          />

          <SmartField
            label="Date début"
            type="date"
            mode={fieldMode}
            value={form.planned_start_date}
            onChange={(v) => setForm({ ...form, planned_start_date: v })}
            icon={<Calendar size={14} />}
          />

          <SmartField
            label="Date fin"
            type="date"
            mode={fieldMode}
            value={form.planned_end_date}
            onChange={(v) => setForm({ ...form, planned_end_date: v })}
            icon={<Calendar size={14} />}
          />

          <SmartField
            label="Description"
            type="textarea"
            mode={fieldMode}
            value={form.description}
            onChange={(v) => setForm({ ...form, description: v })}
            placeholder="Détails de l'affaire..."
            full
          />
        </SmartForm>
      </Section>

      {id && affaire && !editing && (
        <Totals
          rows={[
            { label: 'Budget total', value: formatCurrency(affaire.planned_budget) },
            { label: 'Dépensé', value: `-${formatCurrency(affaire.actual_cost)}`, isNegative: true },
            { label: 'Reste', value: formatCurrency(reste), isMain: true },
          ]}
        />
      )}
    </Page>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

type View = 'list' | 'detail' | 'create';

export const AffairesModule: React.FC = () => {
  const [view, setView] = useState<View>('list');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Permissions du module
  const permissions = useModulePermissions('projects');

  const goToList = () => { setView('list'); setSelectedId(null); };
  const goToDetail = (id: string) => { setSelectedId(id); setView('detail'); };
  const goToCreate = () => setView('create');

  switch (view) {
    case 'detail':
      return selectedId ? (
        <FormView
          id={selectedId}
          onBack={goToList}
          contextMode={permissions.canEdit ? 'edit' : 'view'}
        />
      ) : (
        <List onSelect={goToDetail} onCreate={goToCreate} canCreate={permissions.canCreate} />
      );

    case 'create':
      return (
        <FormView
          onBack={goToList}
          onSaved={goToDetail}
          contextMode="create"
        />
      );

    default:
      return (
        <List onSelect={goToDetail} onCreate={goToCreate} canCreate={permissions.canCreate} />
      );
  }
};

export default AffairesModule;
