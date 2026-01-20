import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { ClipboardList, Calendar, Wrench, CheckCircle, BarChart3, Clock, MapPin } from 'lucide-react';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map(tab => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// TYPES
// ============================================================================

type InterventionStatut = 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'TERMINEE';
type InterventionPriorite = 'LOW' | 'NORMAL' | 'HIGH';
type InterventionType = 'INSTALLATION' | 'MAINTENANCE' | 'REPARATION' | 'INSPECTION' | 'FORMATION' | 'CONSULTATION' | 'AUTRE';

interface Intervention {
  id: string;
  reference: string;
  client_id: string;
  client_name?: string;
  donneur_ordre_id?: string;
  donneur_ordre_name?: string;
  projet_id?: string;
  projet_name?: string;
  type_intervention: InterventionType;
  priorite: InterventionPriorite;
  titre: string;
  description?: string;
  date_prevue?: string;
  heure_prevue?: string;
  date_prevue_debut?: string;
  date_prevue_fin?: string;
  duree_prevue_minutes?: number;
  intervenant_id?: string;
  intervenant_name?: string;
  statut: InterventionStatut;
  date_debut_reelle?: string;
  date_fin_reelle?: string;
  duree_reelle_minutes?: number;
  adresse_intervention?: string;
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  ville?: string;
  code_postal?: string;
  contact_sur_place?: string;
  telephone_contact?: string;
  notes_internes?: string;
  materiel_necessaire?: string;
  created_at: string;
}

interface RapportIntervention {
  id: string;
  intervention_id: string;
  travaux_realises?: string;
  observations?: string;
  recommandations?: string;
  pieces_remplacees?: string;
  temps_passe_minutes?: number;
  materiel_utilise?: string;
  photos: string[];
  signature_client?: string;
  nom_signataire?: string;
  is_signed: boolean;
  created_at: string;
}

interface DonneurOrdre {
  id: string;
  nom: string;
  email?: string;
  telephone?: string;
  entreprise?: string;
  is_active: boolean;
}

interface InterventionStats {
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  terminees_semaine: number;
  terminees_mois: number;
  duree_moyenne_minutes: number;
  interventions_jour: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const STATUTS = [
  { value: 'A_PLANIFIER', label: 'A planifier' },
  { value: 'PLANIFIEE', label: 'Planifiee' },
  { value: 'EN_COURS', label: 'En cours' },
  { value: 'TERMINEE', label: 'Terminee' }
];

const PRIORITES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' }
];

const TYPES_INTERVENTION = [
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Reparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' }
];

const STATUT_COLORS: Record<string, string> = {
  A_PLANIFIER: 'gray',
  PLANIFIEE: 'blue',
  EN_COURS: 'orange',
  TERMINEE: 'green'
};

const PRIORITE_COLORS: Record<string, string> = {
  LOW: 'gray',
  NORMAL: 'blue',
  HIGH: 'red'
};

// ============================================================================
// HELPERS
// ============================================================================

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const formatDuration = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h${mins.toString().padStart(2, '0')}` : `${mins}min`;
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useInterventionStats = () => {
  return useQuery({
    queryKey: ['interventions', 'stats'],
    queryFn: async () => {
      const response = await api.get<{ data: InterventionStats }>('/v1/interventions/stats').then(r => r.data);
      return response as unknown as InterventionStats;
    }
  });
};

const useInterventions = (filters?: { statut?: string; type_intervention?: string; priorite?: string; client_id?: string }) => {
  return useQuery({
    queryKey: ['interventions', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.statut) params.append('statut', filters.statut);
      if (filters?.type_intervention) params.append('type_intervention', filters.type_intervention);
      if (filters?.priorite) params.append('priorite', filters.priorite);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      const queryString = params.toString();
      const url = `/v1/interventions${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<{ data: { items?: Intervention[] } }>(url).then(r => r.data);
      return (response as any)?.items || response as unknown as Intervention[];
    }
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<{ data: DonneurOrdre[] }>('/v1/interventions/donneurs-ordre').then(r => r.data);
      return response as unknown as DonneurOrdre[];
    }
  });
};

const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; name: string }[] }>('/v1/commercial/customers').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; first_name: string; last_name: string }[] }>('/v1/hr/employees').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      return api.post('/v1/interventions', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    }
  });
};

const useUpdateStatut = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, statut }: { id: string; statut: string }) => {
      return api.put(`/v1/interventions/${id}`, { statut }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const InterventionsListView: React.FC = () => {
  const [filterStatut, setFilterStatut] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterPriorite, setFilterPriorite] = useState<string>('');
  const [selectedIntervention, setSelectedIntervention] = useState<Intervention | null>(null);
  const [showNewModal, setShowNewModal] = useState(false);

  const { data: interventions = [], isLoading } = useInterventions({
    statut: filterStatut || undefined,
    type_intervention: filterType || undefined,
    priorite: filterPriorite || undefined
  });
  const updateStatut = useUpdateStatut();

  const columns: TableColumn<Intervention>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => (
      <code className="font-mono text-sm">{v as string}</code>
    )},
    { id: 'titre', header: 'Titre', accessor: 'titre' },
    { id: 'client_name', header: 'Client', accessor: 'client_name', render: (v) => (v as string) || '-' },
    { id: 'type_intervention', header: 'Type', accessor: 'type_intervention', render: (v) => {
      const info = TYPES_INTERVENTION.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'priorite', header: 'Priorite', accessor: 'priorite', render: (v) => {
      const info = PRIORITES.find(p => p.value === v);
      return <Badge color={PRIORITE_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'date_prevue', header: 'Date prevue', accessor: 'date_prevue', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'intervenant_name', header: 'Intervenant', accessor: 'intervenant_name', render: (v) => (v as string) || '-' },
    { id: 'statut', header: 'Statut', accessor: 'statut', render: (v) => {
      const info = STATUTS.find(s => s.value === v);
      return <Badge color={STATUT_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'duree_prevue_minutes', header: 'Duree', accessor: 'duree_prevue_minutes', render: (v) => (v as number) ? formatDuration(v as number) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary" onClick={() => setSelectedIntervention(row)}>Detail</Button>
        {row.statut === 'A_PLANIFIER' && (
          <Button size="sm" variant="primary" onClick={() => updateStatut.mutate({ id: row.id, statut: 'PLANIFIEE' })}>Planifier</Button>
        )}
        {row.statut === 'PLANIFIEE' && (
          <Button size="sm" variant="warning" onClick={() => updateStatut.mutate({ id: row.id, statut: 'EN_COURS' })}>Demarrer</Button>
        )}
        {row.statut === 'EN_COURS' && (
          <Button size="sm" variant="success" onClick={() => updateStatut.mutate({ id: row.id, statut: 'TERMINEE' })}>Terminer</Button>
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
              options={[{ value: '', label: 'Toutes priorites' }, ...PRIORITES]}
              className="w-36"
            />
            <Button onClick={() => setShowNewModal(true)}>Nouvelle intervention</Button>
          </div>
        </div>
        <DataTable columns={columns} data={interventions} isLoading={isLoading} keyField="id" />
      </Card>

      {/* Modal Detail */}
      {selectedIntervention && (
        <InterventionDetailModal
          intervention={selectedIntervention}
          onClose={() => setSelectedIntervention(null)}
        />
      )}

      {/* Modal Creation */}
      {showNewModal && (
        <NewInterventionModal onClose={() => setShowNewModal(false)} />
      )}
    </>
  );
};

const InterventionDetailModal: React.FC<{
  intervention: Intervention;
  onClose: () => void;
}> = ({ intervention, onClose }) => {
  const updateStatut = useUpdateStatut();

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Intervention ${intervention.reference}`}
      size="lg"
    >
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-xl font-bold">{intervention.titre}</h3>
            <div className="flex gap-2 mt-2">
              <Badge color={STATUT_COLORS[intervention.statut] || 'gray'}>
                {STATUTS.find(s => s.value === intervention.statut)?.label}
              </Badge>
              <Badge color={PRIORITE_COLORS[intervention.priorite] || 'gray'}>
                {PRIORITES.find(p => p.value === intervention.priorite)?.label}
              </Badge>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Type</div>
            <div>{TYPES_INTERVENTION.find(t => t.value === intervention.type_intervention)?.label}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Client</div>
            <div className="font-medium">{intervention.client_name || '-'}</div>
          </div>
          <div>
            <div className="text-gray-500">Donneur d'ordre</div>
            <div className="font-medium">{intervention.donneur_ordre_name || '-'}</div>
          </div>
          <div>
            <div className="text-gray-500">Intervenant</div>
            <div className="font-medium">{intervention.intervenant_name || 'Non assigne'}</div>
          </div>
          <div>
            <div className="text-gray-500">Projet</div>
            <div className="font-medium">{intervention.projet_name || '-'}</div>
          </div>
          <div>
            <div className="text-gray-500">Date prevue</div>
            <div className="font-medium">{intervention.date_prevue ? formatDate(intervention.date_prevue) : '-'} {intervention.heure_prevue || ''}</div>
          </div>
          <div>
            <div className="text-gray-500">Duree prevue</div>
            <div className="font-medium">{intervention.duree_prevue_minutes ? formatDuration(intervention.duree_prevue_minutes) : '-'}</div>
          </div>
        </div>

        {intervention.adresse_intervention && (
          <div>
            <div className="text-sm text-gray-500">Adresse d'intervention</div>
            <div>{intervention.adresse_intervention}</div>
          </div>
        )}

        {intervention.contact_sur_place && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-500">Contact sur place</div>
              <div>{intervention.contact_sur_place}</div>
            </div>
            {intervention.telephone_contact && (
              <div>
                <div className="text-gray-500">Telephone</div>
                <div>{intervention.telephone_contact}</div>
              </div>
            )}
          </div>
        )}

        {intervention.description && (
          <div>
            <div className="text-sm text-gray-500">Description</div>
            <div className="bg-gray-50 p-3 rounded">{intervention.description}</div>
          </div>
        )}

        {intervention.materiel_necessaire && (
          <div>
            <div className="text-sm text-gray-500">Materiel necessaire</div>
            <div className="bg-yellow-50 p-3 rounded">{intervention.materiel_necessaire}</div>
          </div>
        )}

        {intervention.notes_internes && (
          <div>
            <div className="text-sm text-gray-500">Notes internes</div>
            <div className="bg-blue-50 p-3 rounded text-sm">{intervention.notes_internes}</div>
          </div>
        )}

        {/* Suivi reel */}
        {(intervention.date_debut_reelle || intervention.date_fin_reelle) && (
          <div className="border-t pt-4">
            <h4 className="font-semibold mb-2">Suivi reel</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              {intervention.date_debut_reelle && (
                <div>
                  <div className="text-gray-500">Demarrage</div>
                  <div>{formatDateTime(intervention.date_debut_reelle)}</div>
                </div>
              )}
              {intervention.date_fin_reelle && (
                <div>
                  <div className="text-gray-500">Fin</div>
                  <div>{formatDateTime(intervention.date_fin_reelle)}</div>
                </div>
              )}
              {intervention.duree_reelle_minutes && (
                <div>
                  <div className="text-gray-500">Duree reelle</div>
                  <div>{formatDuration(intervention.duree_reelle_minutes)}</div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-between items-center pt-4 border-t">
          <div className="flex gap-2">
            {intervention.statut === 'A_PLANIFIER' && (
              <Button variant="primary" onClick={() => {
                updateStatut.mutate({ id: intervention.id, statut: 'PLANIFIEE' });
                onClose();
              }}>Planifier</Button>
            )}
            {intervention.statut === 'PLANIFIEE' && (
              <Button variant="warning" onClick={() => {
                updateStatut.mutate({ id: intervention.id, statut: 'EN_COURS' });
                onClose();
              }}>Demarrer l'intervention</Button>
            )}
            {intervention.statut === 'EN_COURS' && (
              <Button variant="success" onClick={() => {
                updateStatut.mutate({ id: intervention.id, statut: 'TERMINEE' });
                onClose();
              }}>Terminer l'intervention</Button>
            )}
          </div>
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
        </div>
      </div>
    </Modal>
  );
};

const NewInterventionModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { data: clients = [] } = useClients();
  const { data: intervenants = [] } = useIntervenants();
  const { data: donneursOrdre = [] } = useDonneursOrdre();
  const createIntervention = useCreateIntervention();

  const [formData, setFormData] = useState({
    client_id: '',
    donneur_ordre_id: '',
    type_intervention: '',
    priorite: 'NORMAL',
    titre: '',
    description: '',
    date_prevue: '',
    heure_prevue: '',
    duree_prevue_minutes: '',
    intervenant_id: '',
    adresse_intervention: '',
    contact_sur_place: '',
    telephone_contact: '',
    materiel_necessaire: ''
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Combiner date et heure pour date_prevue_debut
    let date_prevue_debut: string | undefined;
    if (formData.date_prevue) {
      const time = formData.heure_prevue || '09:00';
      date_prevue_debut = `${formData.date_prevue}T${time}:00`;
    }

    const data = {
      client_id: formData.client_id,
      donneur_ordre_id: formData.donneur_ordre_id || undefined,
      type_intervention: (formData.type_intervention || 'AUTRE') as InterventionType,
      priorite: (formData.priorite || 'NORMAL') as InterventionPriorite,
      titre: formData.titre || undefined,
      description: formData.description || undefined,
      date_prevue_debut: date_prevue_debut,
      intervenant_id: formData.intervenant_id || undefined,
      adresse_ligne1: formData.adresse_intervention || undefined,
      notes_internes: [
        formData.contact_sur_place ? `Contact: ${formData.contact_sur_place}` : '',
        formData.telephone_contact ? `Tél: ${formData.telephone_contact}` : '',
        formData.materiel_necessaire ? `Matériel: ${formData.materiel_necessaire}` : '',
      ].filter(Boolean).join('\n') || undefined,
    };

    createIntervention.mutate(data, {
      onSuccess: () => onClose()
    });
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Nouvelle intervention" size="lg">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Client *</label>
              <Select
                value={formData.client_id}
                onChange={(v) => setFormData({ ...formData, client_id: v })}
                options={[
                  { value: '', label: 'Selectionner...' },
                  ...clients.map((c: any) => ({ value: c.id, label: c.name }))
                ]}
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Donneur d'ordre</label>
              <Select
                value={formData.donneur_ordre_id}
                onChange={(v) => setFormData({ ...formData, donneur_ordre_id: v })}
                options={[
                  { value: '', label: 'Aucun' },
                  ...donneursOrdre.map(d => ({ value: d.id, label: d.nom }))
                ]}
              />
            </div>
          </div>

          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Titre *</label>
            <Input
              value={formData.titre}
              onChange={(v) => setFormData({ ...formData, titre: v })}
              placeholder="Titre de l'intervention"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Type *</label>
              <Select
                value={formData.type_intervention}
                onChange={(v) => setFormData({ ...formData, type_intervention: v })}
                options={[{ value: '', label: 'Selectionner...' }, ...TYPES_INTERVENTION]}
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Priorite *</label>
              <Select
                value={formData.priorite}
                onChange={(v) => setFormData({ ...formData, priorite: v })}
                options={PRIORITES}
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Duree prevue (min)</label>
              <Input
                type="number"
                value={formData.duree_prevue_minutes}
                onChange={(v) => setFormData({ ...formData, duree_prevue_minutes: v })}
                placeholder="60"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Date prevue</label>
              <input
                type="date"
                className="azals-input"
                value={formData.date_prevue}
                onChange={(e) => setFormData({ ...formData, date_prevue: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Heure prevue</label>
              <input
                type="time"
                className="azals-input"
                value={formData.heure_prevue}
                onChange={(e) => setFormData({ ...formData, heure_prevue: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Intervenant</label>
              <Select
                value={formData.intervenant_id}
                onChange={(v) => setFormData({ ...formData, intervenant_id: v })}
                options={[
                  { value: '', label: 'Non assigne' },
                  ...intervenants.map((i: any) => ({ value: i.id, label: `${i.first_name} ${i.last_name}` }))
                ]}
              />
            </div>
          </div>

          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Adresse d'intervention</label>
            <Input
              value={formData.adresse_intervention}
              onChange={(v) => setFormData({ ...formData, adresse_intervention: v })}
              placeholder="Adresse complete"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Contact sur place</label>
              <Input
                value={formData.contact_sur_place}
                onChange={(v) => setFormData({ ...formData, contact_sur_place: v })}
                placeholder="Nom du contact"
              />
            </div>
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Telephone contact</label>
              <Input
                value={formData.telephone_contact}
                onChange={(v) => setFormData({ ...formData, telephone_contact: v })}
                placeholder="06 XX XX XX XX"
              />
            </div>
          </div>

          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Description</label>
            <TextArea
              value={formData.description}
              onChange={(v) => setFormData({ ...formData, description: v })}
              rows={3}
              placeholder="Description detaillee de l'intervention..."
            />
          </div>

          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Materiel necessaire</label>
            <TextArea
              value={formData.materiel_necessaire}
              onChange={(v) => setFormData({ ...formData, materiel_necessaire: v })}
              rows={2}
              placeholder="Liste du materiel requis..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>Annuler</Button>
            <Button type="submit" disabled={createIntervention.isPending}>Creer l'intervention</Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};

const DonneursOrdreView: React.FC = () => {
  const { data: donneursOrdre = [], isLoading } = useDonneursOrdre();

  const columns: TableColumn<DonneurOrdre>[] = [
    { id: 'nom', header: 'Nom', accessor: 'nom' },
    { id: 'entreprise', header: 'Entreprise', accessor: 'entreprise', render: (v) => (v as string) || '-' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => (v as string) || '-' },
    { id: 'telephone', header: 'Telephone', accessor: 'telephone', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Donneurs d'ordre</h3>
        <Button>Nouveau donneur d'ordre</Button>
      </div>
      <DataTable columns={columns} data={donneursOrdre} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const PlanningView: React.FC = () => {
  const { data: interventions = [] } = useInterventions({ statut: 'PLANIFIEE' });

  // Grouper par date
  const interventionsByDate = interventions.reduce((acc: Record<string, Intervention[]>, int: Intervention) => {
    const date = int.date_prevue || 'Non planifiee';
    if (!acc[date]) acc[date] = [];
    acc[date].push(int);
    return acc;
  }, {});

  const dates = Object.keys(interventionsByDate).sort();

  return (
    <div className="space-y-4">
      {dates.length === 0 ? (
        <Card>
          <div className="text-center py-8 text-gray-500">
            Aucune intervention planifiee
          </div>
        </Card>
      ) : (
        dates.map(date => (
          <Card key={date}>
            <h4 className="font-semibold mb-3">
              {date === 'Non planifiee' ? date : formatDate(date)}
              <Badge color="blue">{interventionsByDate[date].length}</Badge>
            </h4>
            <div className="space-y-2">
              {interventionsByDate[date].map((int: Intervention) => (
                <div key={int.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{int.titre}</div>
                    <div className="text-sm text-gray-500">
                      {int.heure_prevue || '-'} - {int.client_name} - {int.intervenant_name || 'Non assigne'}
                    </div>
                  </div>
                  <Badge color={PRIORITE_COLORS[int.priorite] || 'gray'}>
                    {PRIORITES.find(p => p.value === int.priorite)?.label}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        ))
      )}
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'interventions' | 'planning' | 'donneurs-ordre';

const InterventionsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useInterventionStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'interventions', label: 'Interventions' },
    { id: 'planning', label: 'Planning' },
    { id: 'donneurs-ordre', label: 'Donneurs d\'ordre' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'interventions':
        return <InterventionsListView />;
      case 'planning':
        return <PlanningView />;
      case 'donneurs-ordre':
        return <DonneursOrdreView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="A planifier"
                value={String(stats?.a_planifier || 0)}
                icon={<ClipboardList size={20} />}
                variant="default"
                onClick={() => setCurrentView('interventions')}
              />
              <StatCard
                title="Planifiees"
                value={String(stats?.planifiees || 0)}
                icon={<Calendar size={20} />}
                variant="default"
                onClick={() => setCurrentView('planning')}
              />
              <StatCard
                title="En cours"
                value={String(stats?.en_cours || 0)}
                icon={<Wrench size={20} />}
                variant="warning"
              />
              <StatCard
                title="Terminees (semaine)"
                value={String(stats?.terminees_semaine || 0)}
                icon={<CheckCircle size={20} />}
                variant="success"
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Terminees (mois)"
                value={String(stats?.terminees_mois || 0)}
                icon={<BarChart3 size={20} />}
                variant="default"
              />
              <StatCard
                title="Duree moyenne"
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

  return (
    <PageWrapper title="Interventions" subtitle="Gestion des interventions terrain">
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default InterventionsModule;
