/**
 * AZALSCORE Module - Interventions v1
 * ====================================
 *
 * Module complet de gestion des interventions terrain.
 *
 * Fonctionnalités:
 * - Liste avec filtres (statut, client, intervenant, date)
 * - Création rapide (<1 min)
 * - Vue détaillée avec workflow
 * - Actions terrain (arrivée, démarrage, fin)
 * - Rapports d'intervention avec signature
 * - Planning/calendrier
 * - Statistiques et KPIs
 *
 * Workflow: A_PLANIFIER -> PLANIFIEE -> EN_COURS -> TERMINEE
 * Format référence: INT-YYYY-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Wrench, Calendar, FileText, Clock, MapPin,
  Play, Square, Check, AlertCircle, CheckCircle2,
  RefreshCw, Filter, Search, X, Eye, Edit, Trash2,
  User, Building, Phone, Mail, Camera, PenLine,
  ChevronRight, ArrowRight, Timer, Flag, CalendarDays
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard, useHasCapability } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, TableAction, DashboardKPI } from '@/types';

// ============================================================
// TYPES - Alignés avec le backend
// ============================================================

type InterventionStatut = 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'TERMINEE';
type InterventionPriorite = 'LOW' | 'NORMAL' | 'HIGH';
type InterventionType = 'INSTALLATION' | 'MAINTENANCE' | 'REPARATION' | 'DIAGNOSTIC' | 'FORMATION' | 'AUTRE';

interface Intervention {
  id: string;
  tenant_id: string;
  reference: string;
  client_id: string;
  client_name?: string;
  donneur_ordre_id?: string;
  donneur_ordre_name?: string;
  projet_id?: string;
  projet_name?: string;
  devis_id?: string;
  facture_client_id?: string;
  commande_fournisseur_id?: string;
  type_intervention: InterventionType;
  priorite: InterventionPriorite;
  titre: string;
  description?: string;
  date_prevue?: string;
  heure_prevue?: string;
  duree_prevue_minutes?: number;
  intervenant_id?: string;
  intervenant_name?: string;
  statut: InterventionStatut;
  date_debut_reelle?: string;
  date_fin_reelle?: string;
  duree_reelle_minutes?: number;
  adresse_intervention?: string;
  contact_sur_place?: string;
  telephone_contact?: string;
  notes_internes?: string;
  materiel_necessaire?: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  // Terrain tracking
  heure_arrivee?: string;
  heure_depart?: string;
  geolocalisation_arrivee?: { lat: number; lng: number };
  geolocalisation_depart?: { lat: number; lng: number };
  // Relations
  rapport?: RapportIntervention;
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
  date_signature?: string;
  is_signed: boolean;
  created_at: string;
  updated_at: string;
}

interface RapportFinal {
  id: string;
  titre: string;
  type_rapport: 'PROJET' | 'DONNEUR_ORDRE' | 'PERIODE';
  projet_id?: string;
  donneur_ordre_id?: string;
  date_debut: string;
  date_fin: string;
  nombre_interventions: number;
  duree_totale_minutes: number;
  interventions_ids: string[];
  resume?: string;
  is_finalized: boolean;
  created_at: string;
}

interface DonneurOrdre {
  id: string;
  nom: string;
  email?: string;
  telephone?: string;
  entreprise?: string;
  adresse?: string;
  is_active: boolean;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  email?: string;
}

interface Project {
  id: string;
  name: string;
  client_id: string;
}

interface InterventionSummary {
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  terminees_semaine: number;
  terminees_mois: number;
  duree_moyenne_minutes: number;
  interventions_jour: number;
}

interface InterventionFilters {
  statut?: InterventionStatut;
  client_id?: string;
  intervenant_id?: string;
  type_intervention?: InterventionType;
  priorite?: InterventionPriorite;
  date_from?: string;
  date_to?: string;
  search?: string;
}

interface CreateInterventionData {
  client_id: string;
  donneur_ordre_id?: string;
  projet_id?: string;
  type_intervention: InterventionType;
  priorite: InterventionPriorite;
  titre: string;
  description?: string;
  date_prevue?: string;
  heure_prevue?: string;
  duree_prevue_minutes?: number;
  intervenant_id?: string;
  adresse_intervention?: string;
  contact_sur_place?: string;
  telephone_contact?: string;
  notes_internes?: string;
  materiel_necessaire?: string;
}

// ============================================================
// CONSTANTES
// ============================================================

const STATUT_CONFIG: Record<InterventionStatut, { label: string; color: string; icon: React.ReactNode; nextAction?: string }> = {
  A_PLANIFIER: {
    label: 'À planifier',
    color: 'gray',
    icon: <Clock size={14} />,
    nextAction: 'Planifier',
  },
  PLANIFIEE: {
    label: 'Planifiée',
    color: 'blue',
    icon: <Calendar size={14} />,
    nextAction: 'Arrivée sur site',
  },
  EN_COURS: {
    label: 'En cours',
    color: 'orange',
    icon: <Play size={14} />,
    nextAction: 'Terminer',
  },
  TERMINEE: {
    label: 'Terminée',
    color: 'green',
    icon: <CheckCircle2 size={14} />,
  },
};

const PRIORITE_CONFIG: Record<InterventionPriorite, { label: string; color: string; severity: 'GREEN' | 'ORANGE' | 'RED' }> = {
  LOW: { label: 'Basse', color: 'gray', severity: 'GREEN' },
  NORMAL: { label: 'Normale', color: 'blue', severity: 'ORANGE' },
  HIGH: { label: 'Haute', color: 'red', severity: 'RED' },
};

const TYPE_CONFIG: Record<InterventionType, { label: string; icon: React.ReactNode }> = {
  INSTALLATION: { label: 'Installation', icon: <Wrench size={14} /> },
  MAINTENANCE: { label: 'Maintenance', icon: <Wrench size={14} /> },
  REPARATION: { label: 'Réparation', icon: <Wrench size={14} /> },
  DIAGNOSTIC: { label: 'Diagnostic', icon: <Eye size={14} /> },
  FORMATION: { label: 'Formation', icon: <User size={14} /> },
  AUTRE: { label: 'Autre', icon: <Wrench size={14} /> },
};

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

const formatDateTime = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatDuration = (minutes?: number): string => {
  if (!minutes) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}min`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h${mins.toString().padStart(2, '0')}`;
};

// ============================================================
// API HOOKS
// ============================================================

const useInterventionSummary = () => {
  return useQuery({
    queryKey: ['interventions', 'summary'],
    queryFn: async () => {
      const response = await api.get<InterventionSummary>('/v1/interventions/statistiques');
      return response.data;
    },
  });
};

const useInterventions = (
  page = 1,
  pageSize = 25,
  filters: InterventionFilters = {}
) => {
  const queryParams = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ...(filters.statut && { statut: filters.statut }),
    ...(filters.client_id && { client_id: filters.client_id }),
    ...(filters.intervenant_id && { intervenant_id: filters.intervenant_id }),
    ...(filters.type_intervention && { type_intervention: filters.type_intervention }),
    ...(filters.priorite && { priorite: filters.priorite }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
    ...(filters.search && { search: filters.search }),
  });

  return useQuery({
    queryKey: ['interventions', 'list', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Intervention>>(
        `/v1/interventions?${queryParams}`
      );
      return response.data;
    },
  });
};

const useIntervention = (id: string) => {
  return useQuery({
    queryKey: ['intervention', id],
    queryFn: async () => {
      const response = await api.get<Intervention>(`/v1/interventions/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
};

const useCustomers = () => {
  return useQuery({
    queryKey: ['customers', 'list'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        '/v1/commercial/customers?page_size=500&is_active=true'
      );
      return response.data.items;
    },
  });
};

const useProjects = (clientId?: string) => {
  return useQuery({
    queryKey: ['projects', 'list', clientId],
    queryFn: async () => {
      const params = clientId ? `?client_id=${clientId}&page_size=100` : '?page_size=100';
      const response = await api.get<PaginatedResponse<Project>>(`/v1/projects${params}`);
      return response.data.items;
    },
    enabled: true,
  });
};

const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['donneurs_ordre', 'list'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<DonneurOrdre>>(
        '/v1/interventions/donneurs-ordre?page_size=500&is_active=true'
      );
      return response.data.items;
    },
  });
};

const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants', 'list'],
    queryFn: async () => {
      const response = await api.get<{ id: string; name: string; email: string }[]>(
        '/v1/admin/users?role=intervenant&page_size=100'
      );
      return response.data;
    },
  });
};

const useCreateIntervention = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateInterventionData) => {
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
    mutationFn: async ({ id, data }: { id: string; data: Partial<CreateInterventionData> }) => {
      const response = await api.put<Intervention>(`/v1/interventions/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      queryClient.invalidateQueries({ queryKey: ['intervention', data.id] });
    },
  });
};

const useDeleteIntervention = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/interventions/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

// Terrain Actions
const usePlanifierIntervention = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data: { date_prevue: string; heure_prevue?: string; intervenant_id: string }
    }) => {
      const response = await api.post<Intervention>(`/v1/interventions/${id}/planifier`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      queryClient.invalidateQueries({ queryKey: ['intervention', data.id] });
    },
  });
};

const useArriveSurSite = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, geolocalisation }: {
      id: string;
      geolocalisation?: { lat: number; lng: number }
    }) => {
      const response = await api.post<Intervention>(`/v1/interventions/${id}/arrivee-sur-site`, {
        geolocalisation,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      queryClient.invalidateQueries({ queryKey: ['intervention', data.id] });
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
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      queryClient.invalidateQueries({ queryKey: ['intervention', data.id] });
    },
  });
};

const useTerminerIntervention = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data: {
        travaux_realises?: string;
        observations?: string;
        recommandations?: string;
        pieces_remplacees?: string;
        materiel_utilise?: string;
        geolocalisation?: { lat: number; lng: number };
      }
    }) => {
      const response = await api.post<Intervention>(`/v1/interventions/${id}/terminer`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
      queryClient.invalidateQueries({ queryKey: ['intervention', data.id] });
    },
  });
};

const useRapport = (interventionId: string) => {
  return useQuery({
    queryKey: ['rapport', interventionId],
    queryFn: async () => {
      const response = await api.get<RapportIntervention>(
        `/v1/interventions/${interventionId}/rapport`
      );
      return response.data;
    },
    enabled: !!interventionId,
  });
};

const useSignerRapport = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ interventionId, data }: {
      interventionId: string;
      data: { signature_client: string; nom_signataire: string }
    }) => {
      const response = await api.post<RapportIntervention>(
        `/v1/interventions/${interventionId}/rapport/signer`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rapport', variables.interventionId] });
      queryClient.invalidateQueries({ queryKey: ['intervention', variables.interventionId] });
    },
  });
};

const useUpdateRapport = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ interventionId, data }: {
      interventionId: string;
      data: Partial<RapportIntervention>
    }) => {
      const response = await api.put<RapportIntervention>(
        `/v1/interventions/${interventionId}/rapport`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rapport', variables.interventionId] });
    },
  });
};

// Planning
const usePlanningInterventions = (dateDebut: string, dateFin: string) => {
  return useQuery({
    queryKey: ['interventions', 'planning', dateDebut, dateFin],
    queryFn: async () => {
      const response = await api.get<Intervention[]>(
        `/v1/interventions/planning?date_debut=${dateDebut}&date_fin=${dateFin}`
      );
      return response.data;
    },
  });
};

// ============================================================
// COMPONENTS - Status Badge
// ============================================================

interface StatusBadgeProps {
  statut: InterventionStatut;
  size?: 'sm' | 'md';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ statut, size = 'md' }) => {
  const config = STATUT_CONFIG[statut];

  return (
    <span className={`azals-badge azals-badge--${config.color} ${size === 'sm' ? 'azals-badge--sm' : ''}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

// ============================================================
// COMPONENTS - Priority Badge
// ============================================================

interface PriorityBadgeProps {
  priorite: InterventionPriorite;
}

const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priorite }) => {
  const config = PRIORITE_CONFIG[priorite];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

// ============================================================
// COMPONENTS - Filter Bar
// ============================================================

interface FilterBarProps {
  filters: InterventionFilters;
  onChange: (filters: InterventionFilters) => void;
  customers?: Customer[];
  intervenants?: { id: string; name: string }[];
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange, customers, intervenants }) => {
  const [showFilters, setShowFilters] = useState(false);

  const activeFiltersCount = [
    filters.statut,
    filters.client_id,
    filters.intervenant_id,
    filters.type_intervention,
    filters.priorite,
    filters.date_from,
  ].filter(Boolean).length;

  return (
    <div className="azals-filter-bar">
      <div className="azals-filter-bar__search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Rechercher par référence, titre, client..."
          value={filters.search || ''}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="azals-input"
        />
        {filters.search && (
          <button
            className="azals-filter-bar__clear"
            onClick={() => onChange({ ...filters, search: '' })}
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="azals-filter-bar__actions">
        <Button
          variant="ghost"
          leftIcon={<Filter size={16} />}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filtres
          {activeFiltersCount > 0 && (
            <span className="azals-filter-bar__badge">{activeFiltersCount}</span>
          )}
        </Button>
      </div>

      {showFilters && (
        <div className="azals-filter-bar__panel">
          <div className="azals-filter-bar__field">
            <label>Statut</label>
            <select
              value={filters.statut || ''}
              onChange={(e) => onChange({
                ...filters,
                statut: e.target.value as InterventionStatut || undefined
              })}
              className="azals-select"
            >
              <option value="">Tous</option>
              {Object.entries(STATUT_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Client</label>
            <select
              value={filters.client_id || ''}
              onChange={(e) => onChange({ ...filters, client_id: e.target.value || undefined })}
              className="azals-select"
            >
              <option value="">Tous</option>
              {customers?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Intervenant</label>
            <select
              value={filters.intervenant_id || ''}
              onChange={(e) => onChange({ ...filters, intervenant_id: e.target.value || undefined })}
              className="azals-select"
            >
              <option value="">Tous</option>
              {intervenants?.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Priorité</label>
            <select
              value={filters.priorite || ''}
              onChange={(e) => onChange({
                ...filters,
                priorite: e.target.value as InterventionPriorite || undefined
              })}
              className="azals-select"
            >
              <option value="">Toutes</option>
              {Object.entries(PRIORITE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Type</label>
            <select
              value={filters.type_intervention || ''}
              onChange={(e) => onChange({
                ...filters,
                type_intervention: e.target.value as InterventionType || undefined
              })}
              className="azals-select"
            >
              <option value="">Tous</option>
              {Object.entries(TYPE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>

          <div className="azals-filter-bar__field">
            <label>Date début</label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
              className="azals-input"
            />
          </div>

          <div className="azals-filter-bar__field">
            <label>Date fin</label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
              className="azals-input"
            />
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange({})}
          >
            Réinitialiser
          </Button>
        </div>
      )}
    </div>
  );
};

// ============================================================
// COMPONENTS - Terrain Action Buttons
// ============================================================

interface TerrainActionsProps {
  intervention: Intervention;
  onPlanifier: () => void;
  onArrivee: () => void;
  onDemarrer: () => void;
  onTerminer: () => void;
  isLoading?: boolean;
}

const TerrainActions: React.FC<TerrainActionsProps> = ({
  intervention,
  onPlanifier,
  onArrivee,
  onDemarrer,
  onTerminer,
  isLoading,
}) => {
  const canManage = useHasCapability('interventions.manage');
  const canTerrain = useHasCapability('interventions.terrain');

  const { statut, heure_arrivee, date_debut_reelle } = intervention;

  // Logique des boutons selon le statut
  if (statut === 'A_PLANIFIER' && canManage) {
    return (
      <Button
        leftIcon={<Calendar size={16} />}
        onClick={onPlanifier}
        isLoading={isLoading}
      >
        Planifier
      </Button>
    );
  }

  if (statut === 'PLANIFIEE' && canTerrain) {
    return (
      <Button
        leftIcon={<MapPin size={16} />}
        onClick={onArrivee}
        isLoading={isLoading}
        variant="primary"
      >
        Arrivée sur site
      </Button>
    );
  }

  if (statut === 'EN_COURS' && canTerrain) {
    // Si arrivé mais pas encore démarré
    if (heure_arrivee && !date_debut_reelle) {
      return (
        <Button
          leftIcon={<Play size={16} />}
          onClick={onDemarrer}
          isLoading={isLoading}
          variant="primary"
        >
          Démarrer intervention
        </Button>
      );
    }

    // Si démarré, afficher terminer
    if (date_debut_reelle) {
      return (
        <Button
          leftIcon={<Square size={16} />}
          onClick={onTerminer}
          isLoading={isLoading}
          variant="warning"
        >
          Terminer intervention
        </Button>
      );
    }
  }

  return null;
};

// ============================================================
// COMPONENTS - Quick Create Modal
// ============================================================

interface QuickCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (intervention: Intervention) => void;
}

const QuickCreateModal: React.FC<QuickCreateModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { data: customers, isLoading: loadingCustomers } = useCustomers();
  const { data: projects } = useProjects();
  const { data: donneursOrdre } = useDonneursOrdre();
  const createIntervention = useCreateIntervention();

  const [formData, setFormData] = useState<CreateInterventionData>({
    client_id: '',
    type_intervention: 'MAINTENANCE',
    priorite: 'NORMAL',
    titre: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: Record<string, string> = {};
    if (!formData.client_id) newErrors.client_id = 'Client requis';
    if (!formData.titre.trim()) newErrors.titre = 'Titre requis';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const result = await createIntervention.mutateAsync(formData);
      onSuccess(result);
      onClose();
      // Reset form
      setFormData({
        client_id: '',
        type_intervention: 'MAINTENANCE',
        priorite: 'NORMAL',
        titre: '',
      });
    } catch (error) {
      console.error('Creation failed:', error);
    }
  };

  const updateField = <K extends keyof CreateInterventionData>(
    field: K,
    value: CreateInterventionData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Nouvelle intervention"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="azals-quick-form">
        <div className="azals-form-row">
          <div className="azals-form-field azals-form-field--required">
            <label htmlFor="client">Client</label>
            <select
              id="client"
              value={formData.client_id}
              onChange={(e) => updateField('client_id', e.target.value)}
              className={`azals-select ${errors.client_id ? 'azals-select--error' : ''}`}
              disabled={loadingCustomers}
            >
              <option value="">Sélectionner un client</option>
              {customers?.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
              ))}
            </select>
            {errors.client_id && <span className="azals-form-error">{errors.client_id}</span>}
          </div>

          <div className="azals-form-field">
            <label htmlFor="type">Type</label>
            <select
              id="type"
              value={formData.type_intervention}
              onChange={(e) => updateField('type_intervention', e.target.value as InterventionType)}
              className="azals-select"
            >
              {Object.entries(TYPE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="azals-form-field azals-form-field--required">
          <label htmlFor="titre">Titre</label>
          <input
            id="titre"
            type="text"
            value={formData.titre}
            onChange={(e) => updateField('titre', e.target.value)}
            className={`azals-input ${errors.titre ? 'azals-input--error' : ''}`}
            placeholder="Ex: Maintenance préventive climatisation"
          />
          {errors.titre && <span className="azals-form-error">{errors.titre}</span>}
        </div>

        <div className="azals-form-row">
          <div className="azals-form-field">
            <label htmlFor="priorite">Priorité</label>
            <select
              id="priorite"
              value={formData.priorite}
              onChange={(e) => updateField('priorite', e.target.value as InterventionPriorite)}
              className="azals-select"
            >
              {Object.entries(PRIORITE_CONFIG).map(([key, config]) => (
                <option key={key} value={key}>{config.label}</option>
              ))}
            </select>
          </div>

          <div className="azals-form-field">
            <label htmlFor="projet">Projet (optionnel)</label>
            <select
              id="projet"
              value={formData.projet_id || ''}
              onChange={(e) => updateField('projet_id', e.target.value || undefined)}
              className="azals-select"
            >
              <option value="">Aucun</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="azals-form-field">
          <label htmlFor="donneur">Donneur d'ordre (optionnel)</label>
          <select
            id="donneur"
            value={formData.donneur_ordre_id || ''}
            onChange={(e) => updateField('donneur_ordre_id', e.target.value || undefined)}
            className="azals-select"
          >
            <option value="">Aucun</option>
            {donneursOrdre?.map((d) => (
              <option key={d.id} value={d.id}>{d.nom} {d.entreprise ? `(${d.entreprise})` : ''}</option>
            ))}
          </select>
        </div>

        <div className="azals-form-field">
          <label htmlFor="description">Description (optionnel)</label>
          <textarea
            id="description"
            value={formData.description || ''}
            onChange={(e) => updateField('description', e.target.value)}
            className="azals-textarea"
            rows={2}
            placeholder="Description de l'intervention..."
          />
        </div>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={createIntervention.isPending}
            leftIcon={<Plus size={16} />}
          >
            Créer l'intervention
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================
// COMPONENTS - Planifier Modal
// ============================================================

interface PlanifierModalProps {
  intervention: Intervention;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const PlanifierModal: React.FC<PlanifierModalProps> = ({ intervention, isOpen, onClose, onSuccess }) => {
  const { data: intervenants } = useIntervenants();
  const planifier = usePlanifierIntervention();

  const [datePrevue, setDatePrevue] = useState(
    intervention.date_prevue || new Date().toISOString().split('T')[0]
  );
  const [heurePrevue, setHeurePrevue] = useState(intervention.heure_prevue || '09:00');
  const [intervenantId, setIntervenantId] = useState(intervention.intervenant_id || '');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: Record<string, string> = {};
    if (!datePrevue) newErrors.date = 'Date requise';
    if (!intervenantId) newErrors.intervenant = 'Intervenant requis';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await planifier.mutateAsync({
        id: intervention.id,
        data: {
          date_prevue: datePrevue,
          heure_prevue: heurePrevue,
          intervenant_id: intervenantId,
        },
      });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Planification failed:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Planifier ${intervention.reference}`}
      size="md"
    >
      <form onSubmit={handleSubmit}>
        <div className="azals-form-field azals-form-field--required">
          <label htmlFor="date">Date prévue</label>
          <input
            id="date"
            type="date"
            value={datePrevue}
            onChange={(e) => setDatePrevue(e.target.value)}
            className={`azals-input ${errors.date ? 'azals-input--error' : ''}`}
          />
          {errors.date && <span className="azals-form-error">{errors.date}</span>}
        </div>

        <div className="azals-form-field">
          <label htmlFor="heure">Heure prévue</label>
          <input
            id="heure"
            type="time"
            value={heurePrevue}
            onChange={(e) => setHeurePrevue(e.target.value)}
            className="azals-input"
          />
        </div>

        <div className="azals-form-field azals-form-field--required">
          <label htmlFor="intervenant">Intervenant</label>
          <select
            id="intervenant"
            value={intervenantId}
            onChange={(e) => setIntervenantId(e.target.value)}
            className={`azals-select ${errors.intervenant ? 'azals-select--error' : ''}`}
          >
            <option value="">Sélectionner un intervenant</option>
            {intervenants?.map((i) => (
              <option key={i.id} value={i.id}>{i.name}</option>
            ))}
          </select>
          {errors.intervenant && <span className="azals-form-error">{errors.intervenant}</span>}
        </div>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={planifier.isPending}
            leftIcon={<Calendar size={16} />}
          >
            Planifier
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================
// COMPONENTS - Terminer Modal
// ============================================================

interface TerminerModalProps {
  intervention: Intervention;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const TerminerModal: React.FC<TerminerModalProps> = ({ intervention, isOpen, onClose, onSuccess }) => {
  const terminer = useTerminerIntervention();

  const [travauxRealises, setTravauxRealises] = useState('');
  const [observations, setObservations] = useState('');
  const [recommandations, setRecommandations] = useState('');
  const [piecesRemplacees, setPiecesRemplacees] = useState('');
  const [materielUtilise, setMaterielUtilise] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Get current geolocation if available
      let geolocalisation: { lat: number; lng: number } | undefined;
      if (navigator.geolocation) {
        try {
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
          });
          geolocalisation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
        } catch {
          // Geolocation not available or denied
        }
      }

      await terminer.mutateAsync({
        id: intervention.id,
        data: {
          travaux_realises: travauxRealises || undefined,
          observations: observations || undefined,
          recommandations: recommandations || undefined,
          pieces_remplacees: piecesRemplacees || undefined,
          materiel_utilise: materielUtilise || undefined,
          geolocalisation,
        },
      });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Termination failed:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Terminer ${intervention.reference}`}
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <div className="azals-alert azals-alert--info mb-4">
          <Timer size={16} />
          <span>
            L'intervention sera marquée comme terminée et le temps sera calculé automatiquement.
          </span>
        </div>

        <div className="azals-form-field">
          <label htmlFor="travaux">Travaux réalisés</label>
          <textarea
            id="travaux"
            value={travauxRealises}
            onChange={(e) => setTravauxRealises(e.target.value)}
            className="azals-textarea"
            rows={3}
            placeholder="Décrivez les travaux effectués..."
          />
        </div>

        <div className="azals-form-row">
          <div className="azals-form-field">
            <label htmlFor="pieces">Pièces remplacées</label>
            <textarea
              id="pieces"
              value={piecesRemplacees}
              onChange={(e) => setPiecesRemplacees(e.target.value)}
              className="azals-textarea"
              rows={2}
              placeholder="Liste des pièces..."
            />
          </div>

          <div className="azals-form-field">
            <label htmlFor="materiel">Matériel utilisé</label>
            <textarea
              id="materiel"
              value={materielUtilise}
              onChange={(e) => setMaterielUtilise(e.target.value)}
              className="azals-textarea"
              rows={2}
              placeholder="Matériel utilisé..."
            />
          </div>
        </div>

        <div className="azals-form-field">
          <label htmlFor="observations">Observations</label>
          <textarea
            id="observations"
            value={observations}
            onChange={(e) => setObservations(e.target.value)}
            className="azals-textarea"
            rows={2}
            placeholder="Observations sur l'état du site, équipement..."
          />
        </div>

        <div className="azals-form-field">
          <label htmlFor="recommandations">Recommandations</label>
          <textarea
            id="recommandations"
            value={recommandations}
            onChange={(e) => setRecommandations(e.target.value)}
            className="azals-textarea"
            rows={2}
            placeholder="Recommandations pour le client..."
          />
        </div>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={terminer.isPending}
            leftIcon={<Check size={16} />}
          >
            Terminer l'intervention
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// ============================================================
// PAGES - Dashboard
// ============================================================

const InterventionsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useInterventionSummary();
  const canCreate = useHasCapability('interventions.create');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const kpis: DashboardKPI[] = summary
    ? [
        {
          id: 'a_planifier',
          label: 'À planifier',
          value: summary.a_planifier,
          severity: summary.a_planifier > 5 ? 'RED' : summary.a_planifier > 0 ? 'ORANGE' : 'GREEN',
        },
        {
          id: 'planifiees',
          label: 'Planifiées',
          value: summary.planifiees,
        },
        {
          id: 'en_cours',
          label: 'En cours',
          value: summary.en_cours,
          severity: 'ORANGE',
        },
        {
          id: 'terminees',
          label: 'Terminées (semaine)',
          value: summary.terminees_semaine,
          severity: 'GREEN',
        },
      ]
    : [];

  return (
    <PageWrapper
      title="Interventions"
      subtitle="Gestion des interventions terrain"
      actions={
        canCreate && (
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreateModal(true)}>
            Nouvelle intervention
          </Button>
        )
      }
    >
      {isLoading ? (
        <div className="azals-loading"><div className="azals-spinner" /></div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
            </Grid>
          </section>

          {summary && (
            <section className="azals-section">
              <Grid cols={2} gap="md">
                <Card>
                  <div className="azals-stat-inline">
                    <Timer size={24} className="azals-text--primary" />
                    <div>
                      <span className="azals-stat-inline__label">Durée moyenne</span>
                      <span className="azals-stat-inline__value">
                        {formatDuration(summary.duree_moyenne_minutes)}
                      </span>
                    </div>
                  </div>
                </Card>
                <Card>
                  <div className="azals-stat-inline">
                    <CalendarDays size={24} className="azals-text--primary" />
                    <div>
                      <span className="azals-stat-inline__label">Interventions aujourd'hui</span>
                      <span className="azals-stat-inline__value">{summary.interventions_jour}</span>
                    </div>
                  </div>
                </Card>
              </Grid>
            </section>
          )}

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Liste des interventions"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/interventions/list')}>
                    Voir tout
                  </Button>
                }
              >
                <Wrench size={32} className="azals-text--primary" />
                <p>Toutes les interventions</p>
              </Card>

              <Card
                title="Planning"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/interventions/planning')}>
                    Voir
                  </Button>
                }
              >
                <Calendar size={32} className="azals-text--primary" />
                <p>Vue calendrier</p>
              </Card>

              <Card
                title="Rapports"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/interventions/rapports')}>
                    Voir
                  </Button>
                }
              >
                <FileText size={32} className="azals-text--primary" />
                <p>Rapports finaux</p>
              </Card>
            </Grid>
          </section>
        </>
      )}

      <QuickCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={(intervention) => {
          navigate(`/interventions/${intervention.id}`);
        }}
      />
    </PageWrapper>
  );
};

// ============================================================
// PAGES - List
// ============================================================

const InterventionsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<InterventionFilters>({});
  const [deleteTarget, setDeleteTarget] = useState<Intervention | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data, isLoading, refetch } = useInterventions(page, pageSize, filters);
  const { data: customers } = useCustomers();
  const { data: intervenants } = useIntervenants();
  const deleteIntervention = useDeleteIntervention();

  const canCreate = useHasCapability('interventions.create');
  const canDelete = useHasCapability('interventions.delete');

  const columns: TableColumn<Intervention>[] = [
    {
      id: 'reference',
      header: 'Référence',
      accessor: 'reference',
      sortable: true,
      render: (value, row): React.ReactNode => (
        <Link to={`/interventions/${row.id}`} className="azals-link azals-link--primary">
          {String(value)}
        </Link>
      ),
    },
    {
      id: 'titre',
      header: 'Titre',
      accessor: 'titre',
      sortable: true,
    },
    {
      id: 'client_name',
      header: 'Client',
      accessor: 'client_name',
      sortable: true,
    },
    {
      id: 'type_intervention',
      header: 'Type',
      accessor: 'type_intervention',
      render: (value): React.ReactNode => TYPE_CONFIG[value as InterventionType]?.label || String(value),
    },
    {
      id: 'priorite',
      header: 'Priorité',
      accessor: 'priorite',
      render: (value): React.ReactNode => <PriorityBadge priorite={value as InterventionPriorite} />,
    },
    {
      id: 'statut',
      header: 'Statut',
      accessor: 'statut',
      render: (value): React.ReactNode => <StatusBadge statut={value as InterventionStatut} size="sm" />,
    },
    {
      id: 'date_prevue',
      header: 'Date prévue',
      accessor: 'date_prevue',
      sortable: true,
      render: (value): React.ReactNode => formatDate(value as string),
    },
    {
      id: 'intervenant_name',
      header: 'Intervenant',
      accessor: 'intervenant_name',
      render: (value): React.ReactNode => (value ? String(value) : '-'),
    },
  ];

  const actions: TableAction<Intervention>[] = [
    {
      id: 'view',
      label: 'Voir',
      icon: 'eye',
      onClick: (row) => navigate(`/interventions/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: 'edit',
      onClick: (row) => navigate(`/interventions/${row.id}/edit`),
      isHidden: (row) => row.statut === 'TERMINEE',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      icon: 'trash',
      variant: 'danger',
      onClick: (row) => setDeleteTarget(row),
      isHidden: (row) => row.statut !== 'A_PLANIFIER' || !canDelete,
    },
  ];

  return (
    <PageWrapper
      title="Liste des interventions"
      actions={
        canCreate && (
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreateModal(true)}>
            Nouvelle intervention
          </Button>
        )
      }
    >
      <Card>
        <FilterBar
          filters={filters}
          onChange={setFilters}
          customers={customers}
          intervenants={intervenants}
        />

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          actions={actions}
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

      {/* Delete Confirmation */}
      {deleteTarget && (
        <ConfirmDialog
          title="Confirmer la suppression"
          message={`Êtes-vous sûr de vouloir supprimer l'intervention ${deleteTarget.reference} ?`}
          variant="danger"
          onConfirm={async () => {
            await deleteIntervention.mutateAsync(deleteTarget.id);
            setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
          isLoading={deleteIntervention.isPending}
        />
      )}

      <QuickCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={(intervention) => {
          navigate(`/interventions/${intervention.id}`);
        }}
      />
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Detail
// ============================================================

const InterventionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: intervention, isLoading, refetch } = useIntervention(id || '');
  const arriveSurSite = useArriveSurSite();
  const demarrerIntervention = useDemarrerIntervention();

  const [showPlanifierModal, setShowPlanifierModal] = useState(false);
  const [showTerminerModal, setShowTerminerModal] = useState(false);

  const canManage = useHasCapability('interventions.manage');
  const canTerrain = useHasCapability('interventions.terrain');

  const handleArrivee = async () => {
    if (!intervention) return;

    // Get geolocation if available
    let geolocalisation: { lat: number; lng: number } | undefined;
    if (navigator.geolocation) {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
        });
        geolocalisation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
      } catch {
        // Geolocation not available
      }
    }

    await arriveSurSite.mutateAsync({ id: intervention.id, geolocalisation });
    refetch();
  };

  const handleDemarrer = async () => {
    if (!intervention) return;
    await demarrerIntervention.mutateAsync(intervention.id);
    refetch();
  };

  if (isLoading) {
    return (
      <PageWrapper title="Intervention">
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>Chargement...</span>
        </div>
      </PageWrapper>
    );
  }

  if (!intervention) {
    return (
      <PageWrapper title="Intervention">
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <h3>Intervention non trouvée</h3>
            <Button onClick={() => navigate('/interventions/list')}>
              Retour à la liste
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const statutConfig = STATUT_CONFIG[intervention.statut];
  const isActionLoading = arriveSurSite.isPending || demarrerIntervention.isPending;

  return (
    <PageWrapper
      title={intervention.reference}
      subtitle={intervention.titre}
      actions={
        <ButtonGroup>
          {intervention.statut !== 'TERMINEE' && canManage && (
            <Button
              variant="ghost"
              leftIcon={<Edit size={16} />}
              onClick={() => navigate(`/interventions/${id}/edit`)}
            >
              Modifier
            </Button>
          )}
          <TerrainActions
            intervention={intervention}
            onPlanifier={() => setShowPlanifierModal(true)}
            onArrivee={handleArrivee}
            onDemarrer={handleDemarrer}
            onTerminer={() => setShowTerminerModal(true)}
            isLoading={isActionLoading}
          />
        </ButtonGroup>
      }
    >
      {/* Status Header */}
      <Card className="mb-4">
        <div className="azals-intervention-header">
          <div className="azals-intervention-header__status">
            <StatusBadge statut={intervention.statut} />
            {statutConfig.nextAction && intervention.statut !== 'TERMINEE' && (
              <span className="azals-intervention-header__next">
                <ChevronRight size={14} />
                Prochaine action: {statutConfig.nextAction}
              </span>
            )}
          </div>
          <div className="azals-intervention-header__priority">
            <Flag size={14} />
            <PriorityBadge priorite={intervention.priorite} />
          </div>
        </div>
      </Card>

      {/* Main Info */}
      <section className="mb-4">
      <Grid cols={2} gap="md">
        <Card title="Informations générales">
          <dl className="azals-dl">
            <dt>Type</dt>
            <dd>{TYPE_CONFIG[intervention.type_intervention]?.label}</dd>

            <dt>Client</dt>
            <dd>
              {intervention.client_name || '-'}
              {intervention.client_id && (
                <Link to={`/partners/customers/${intervention.client_id}`} className="azals-link ml-2">
                  <Eye size={12} />
                </Link>
              )}
            </dd>

            {intervention.projet_name && (
              <>
                <dt>Projet</dt>
                <dd>
                  {intervention.projet_name}
                  {intervention.projet_id && (
                    <Link to={`/projects/${intervention.projet_id}`} className="azals-link ml-2">
                      <Eye size={12} />
                    </Link>
                  )}
                </dd>
              </>
            )}

            {intervention.donneur_ordre_name && (
              <>
                <dt>Donneur d'ordre</dt>
                <dd>{intervention.donneur_ordre_name}</dd>
              </>
            )}

            {intervention.description && (
              <>
                <dt>Description</dt>
                <dd>{intervention.description}</dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Planning & Contact">
          <dl className="azals-dl">
            <dt>Date prévue</dt>
            <dd>
              {formatDate(intervention.date_prevue)}
              {intervention.heure_prevue && ` à ${intervention.heure_prevue}`}
            </dd>

            {intervention.duree_prevue_minutes && (
              <>
                <dt>Durée prévue</dt>
                <dd>{formatDuration(intervention.duree_prevue_minutes)}</dd>
              </>
            )}

            <dt>Intervenant</dt>
            <dd>{intervention.intervenant_name || <em className="text-muted">Non assigné</em>}</dd>

            {intervention.adresse_intervention && (
              <>
                <dt>Adresse</dt>
                <dd>
                  <MapPin size={12} className="inline mr-1" />
                  {intervention.adresse_intervention}
                </dd>
              </>
            )}

            {intervention.contact_sur_place && (
              <>
                <dt>Contact sur place</dt>
                <dd>
                  {intervention.contact_sur_place}
                  {intervention.telephone_contact && (
                    <a href={`tel:${intervention.telephone_contact}`} className="azals-link ml-2">
                      <Phone size={12} /> {intervention.telephone_contact}
                    </a>
                  )}
                </dd>
              </>
            )}
          </dl>
        </Card>
      </Grid>
      </section>

      {/* Time Tracking */}
      {(intervention.heure_arrivee || intervention.date_debut_reelle || intervention.date_fin_reelle) && (
        <Card title="Suivi temps" className="mb-4">
          <div className="azals-time-tracking">
            {intervention.heure_arrivee && (
              <div className="azals-time-tracking__item">
                <MapPin size={16} />
                <div>
                  <span className="azals-time-tracking__label">Arrivée sur site</span>
                  <span className="azals-time-tracking__value">{intervention.heure_arrivee}</span>
                </div>
              </div>
            )}

            {intervention.date_debut_reelle && (
              <div className="azals-time-tracking__item">
                <Play size={16} />
                <div>
                  <span className="azals-time-tracking__label">Début intervention</span>
                  <span className="azals-time-tracking__value">
                    {formatDateTime(intervention.date_debut_reelle)}
                  </span>
                </div>
              </div>
            )}

            {intervention.date_fin_reelle && (
              <div className="azals-time-tracking__item">
                <Square size={16} />
                <div>
                  <span className="azals-time-tracking__label">Fin intervention</span>
                  <span className="azals-time-tracking__value">
                    {formatDateTime(intervention.date_fin_reelle)}
                  </span>
                </div>
              </div>
            )}

            {intervention.duree_reelle_minutes && (
              <div className="azals-time-tracking__item azals-time-tracking__item--highlight">
                <Timer size={16} />
                <div>
                  <span className="azals-time-tracking__label">Durée totale</span>
                  <span className="azals-time-tracking__value">
                    {formatDuration(intervention.duree_reelle_minutes)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Linked Documents (Read-only) */}
      {(intervention.devis_id || intervention.facture_client_id || intervention.commande_fournisseur_id) && (
        <Card title="Documents liés" className="mb-4">
          <div className="azals-linked-docs">
            {intervention.devis_id && (
              <Link to={`/invoicing/quotes/${intervention.devis_id}`} className="azals-linked-doc">
                <FileText size={16} />
                <span>Devis lié</span>
                <ArrowRight size={14} />
              </Link>
            )}
            {intervention.facture_client_id && (
              <Link to={`/invoicing/invoices/${intervention.facture_client_id}`} className="azals-linked-doc">
                <FileText size={16} />
                <span>Facture liée</span>
                <ArrowRight size={14} />
              </Link>
            )}
            {intervention.commande_fournisseur_id && (
              <Link to={`/purchases/orders/${intervention.commande_fournisseur_id}`} className="azals-linked-doc">
                <FileText size={16} />
                <span>Commande fournisseur</span>
                <ArrowRight size={14} />
              </Link>
            )}
          </div>
        </Card>
      )}

      {/* Rapport (if TERMINEE) */}
      {intervention.statut === 'TERMINEE' && intervention.rapport && (
        <Card
          title="Rapport d'intervention"
          actions={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/interventions/${id}/rapport`)}
            >
              Voir le rapport complet
            </Button>
          }
        >
          <div className="azals-rapport-preview">
            {intervention.rapport.is_signed ? (
              <div className="azals-rapport-preview__signed">
                <CheckCircle2 size={20} className="text-success" />
                <span>Rapport signé par {intervention.rapport.nom_signataire}</span>
                <span className="text-muted">le {formatDate(intervention.rapport.date_signature)}</span>
              </div>
            ) : (
              <div className="azals-rapport-preview__unsigned">
                <AlertCircle size={20} className="text-warning" />
                <span>Rapport en attente de signature</span>
                <Button
                  size="sm"
                  leftIcon={<PenLine size={14} />}
                  onClick={() => navigate(`/interventions/${id}/rapport`)}
                >
                  Signer
                </Button>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Notes internes */}
      {intervention.notes_internes && (
        <Card title="Notes internes" className="mt-4">
          <p className="text-muted">{intervention.notes_internes}</p>
        </Card>
      )}

      {/* Modals */}
      {showPlanifierModal && (
        <PlanifierModal
          intervention={intervention}
          isOpen={showPlanifierModal}
          onClose={() => setShowPlanifierModal(false)}
          onSuccess={() => refetch()}
        />
      )}

      {showTerminerModal && (
        <TerminerModal
          intervention={intervention}
          isOpen={showTerminerModal}
          onClose={() => setShowTerminerModal(false)}
          onSuccess={() => refetch()}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Edit Form
// ============================================================

const InterventionFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== 'new';

  const { data: intervention, isLoading: loadingIntervention } = useIntervention(id || '');
  const { data: customers, isLoading: loadingCustomers } = useCustomers();
  const { data: projects } = useProjects();
  const { data: donneursOrdre } = useDonneursOrdre();
  const { data: intervenants } = useIntervenants();

  const createIntervention = useCreateIntervention();
  const updateIntervention = useUpdateIntervention();

  const [formData, setFormData] = useState<CreateInterventionData>({
    client_id: '',
    type_intervention: 'MAINTENANCE',
    priorite: 'NORMAL',
    titre: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load existing data
  React.useEffect(() => {
    if (intervention) {
      setFormData({
        client_id: intervention.client_id,
        donneur_ordre_id: intervention.donneur_ordre_id,
        projet_id: intervention.projet_id,
        type_intervention: intervention.type_intervention,
        priorite: intervention.priorite,
        titre: intervention.titre,
        description: intervention.description,
        date_prevue: intervention.date_prevue,
        heure_prevue: intervention.heure_prevue,
        duree_prevue_minutes: intervention.duree_prevue_minutes,
        intervenant_id: intervention.intervenant_id,
        adresse_intervention: intervention.adresse_intervention,
        contact_sur_place: intervention.contact_sur_place,
        telephone_contact: intervention.telephone_contact,
        notes_internes: intervention.notes_internes,
        materiel_necessaire: intervention.materiel_necessaire,
      });
    }
  }, [intervention]);

  // Redirect if completed
  React.useEffect(() => {
    if (isEdit && intervention && intervention.statut === 'TERMINEE') {
      navigate(`/interventions/${id}`);
    }
  }, [intervention, isEdit, id, navigate]);

  const updateField = <K extends keyof CreateInterventionData>(
    field: K,
    value: CreateInterventionData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.client_id) newErrors.client_id = 'Client requis';
    if (!formData.titre.trim()) newErrors.titre = 'Titre requis';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      if (isEdit) {
        await updateIntervention.mutateAsync({ id: id!, data: formData });
        navigate(`/interventions/${id}`);
      } else {
        const result = await createIntervention.mutateAsync(formData);
        navigate(`/interventions/${result.id}`);
      }
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  if ((isEdit && loadingIntervention) || loadingCustomers) {
    return (
      <PageWrapper title={isEdit ? 'Modifier intervention' : 'Nouvelle intervention'}>
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>Chargement...</span>
        </div>
      </PageWrapper>
    );
  }

  const isSubmitting = createIntervention.isPending || updateIntervention.isPending;

  return (
    <PageWrapper
      title={isEdit ? `Modifier ${intervention?.reference}` : 'Nouvelle intervention'}
      actions={
        <Button variant="ghost" onClick={() => navigate('/interventions/list')}>
          Annuler
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card className="mb-4">
          <h3 className="mb-4">Informations principales</h3>

          <Grid cols={2} gap="md">
            <div className="azals-form-field azals-form-field--required">
              <label htmlFor="client">Client</label>
              <select
                id="client"
                value={formData.client_id}
                onChange={(e) => updateField('client_id', e.target.value)}
                className={`azals-select ${errors.client_id ? 'azals-select--error' : ''}`}
                disabled={isEdit}
              >
                <option value="">Sélectionner un client</option>
                {customers?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                ))}
              </select>
              {errors.client_id && <span className="azals-form-error">{errors.client_id}</span>}
            </div>

            <div className="azals-form-field">
              <label htmlFor="type">Type d'intervention</label>
              <select
                id="type"
                value={formData.type_intervention}
                onChange={(e) => updateField('type_intervention', e.target.value as InterventionType)}
                className="azals-select"
              >
                {Object.entries(TYPE_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
          </Grid>

          <div className="azals-form-field azals-form-field--required mt-4">
            <label htmlFor="titre">Titre</label>
            <input
              id="titre"
              type="text"
              value={formData.titre}
              onChange={(e) => updateField('titre', e.target.value)}
              className={`azals-input ${errors.titre ? 'azals-input--error' : ''}`}
              placeholder="Ex: Maintenance préventive climatisation"
            />
            {errors.titre && <span className="azals-form-error">{errors.titre}</span>}
          </div>

          <div className="azals-form-field mt-4">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => updateField('description', e.target.value)}
              className="azals-textarea"
              rows={3}
              placeholder="Description détaillée de l'intervention..."
            />
          </div>

          <div className="mt-4">
          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label htmlFor="priorite">Priorité</label>
              <select
                id="priorite"
                value={formData.priorite}
                onChange={(e) => updateField('priorite', e.target.value as InterventionPriorite)}
                className="azals-select"
              >
                {Object.entries(PRIORITE_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>

            <div className="azals-form-field">
              <label htmlFor="projet">Projet</label>
              <select
                id="projet"
                value={formData.projet_id || ''}
                onChange={(e) => updateField('projet_id', e.target.value || undefined)}
                className="azals-select"
              >
                <option value="">Aucun</option>
                {projects?.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div className="azals-form-field">
              <label htmlFor="donneur">Donneur d'ordre</label>
              <select
                id="donneur"
                value={formData.donneur_ordre_id || ''}
                onChange={(e) => updateField('donneur_ordre_id', e.target.value || undefined)}
                className="azals-select"
              >
                <option value="">Aucun</option>
                {donneursOrdre?.map((d) => (
                  <option key={d.id} value={d.id}>{d.nom}</option>
                ))}
              </select>
            </div>
          </Grid>
          </div>
        </Card>

        <Card className="mb-4">
          <h3 className="mb-4">Planning</h3>

          <Grid cols={3} gap="md">
            <div className="azals-form-field">
              <label htmlFor="date_prevue">Date prévue</label>
              <input
                id="date_prevue"
                type="date"
                value={formData.date_prevue || ''}
                onChange={(e) => updateField('date_prevue', e.target.value)}
                className="azals-input"
              />
            </div>

            <div className="azals-form-field">
              <label htmlFor="heure_prevue">Heure prévue</label>
              <input
                id="heure_prevue"
                type="time"
                value={formData.heure_prevue || ''}
                onChange={(e) => updateField('heure_prevue', e.target.value)}
                className="azals-input"
              />
            </div>

            <div className="azals-form-field">
              <label htmlFor="duree_prevue">Durée prévue (minutes)</label>
              <input
                id="duree_prevue"
                type="number"
                value={formData.duree_prevue_minutes || ''}
                onChange={(e) => updateField('duree_prevue_minutes', parseInt(e.target.value) || undefined)}
                className="azals-input"
                min="0"
                step="15"
                placeholder="Ex: 120"
              />
            </div>
          </Grid>

          <div className="azals-form-field mt-4">
            <label htmlFor="intervenant">Intervenant assigné</label>
            <select
              id="intervenant"
              value={formData.intervenant_id || ''}
              onChange={(e) => updateField('intervenant_id', e.target.value || undefined)}
              className="azals-select"
            >
              <option value="">Non assigné</option>
              {intervenants?.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          </div>
        </Card>

        <Card className="mb-4">
          <h3 className="mb-4">Lieu d'intervention</h3>

          <div className="azals-form-field">
            <label htmlFor="adresse">Adresse</label>
            <input
              id="adresse"
              type="text"
              value={formData.adresse_intervention || ''}
              onChange={(e) => updateField('adresse_intervention', e.target.value)}
              className="azals-input"
              placeholder="Adresse complète..."
            />
          </div>

          <div className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label htmlFor="contact">Contact sur place</label>
              <input
                id="contact"
                type="text"
                value={formData.contact_sur_place || ''}
                onChange={(e) => updateField('contact_sur_place', e.target.value)}
                className="azals-input"
                placeholder="Nom du contact..."
              />
            </div>

            <div className="azals-form-field">
              <label htmlFor="telephone">Téléphone contact</label>
              <input
                id="telephone"
                type="tel"
                value={formData.telephone_contact || ''}
                onChange={(e) => updateField('telephone_contact', e.target.value)}
                className="azals-input"
                placeholder="Ex: 06 12 34 56 78"
              />
            </div>
          </Grid>
          </div>
        </Card>

        <Card className="mb-4">
          <h3 className="mb-4">Notes & Matériel</h3>

          <div className="azals-form-field">
            <label htmlFor="materiel">Matériel nécessaire</label>
            <textarea
              id="materiel"
              value={formData.materiel_necessaire || ''}
              onChange={(e) => updateField('materiel_necessaire', e.target.value)}
              className="azals-textarea"
              rows={2}
              placeholder="Liste du matériel à prévoir..."
            />
          </div>

          <div className="azals-form-field mt-4">
            <label htmlFor="notes">Notes internes</label>
            <textarea
              id="notes"
              value={formData.notes_internes || ''}
              onChange={(e) => updateField('notes_internes', e.target.value)}
              className="azals-textarea"
              rows={2}
              placeholder="Notes internes (non visibles sur le rapport)..."
            />
          </div>
        </Card>

        <div className="azals-form-actions">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate('/interventions/list')}
          >
            Annuler
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            leftIcon={<Check size={16} />}
          >
            {isEdit ? 'Enregistrer' : 'Créer l\'intervention'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Rapport
// ============================================================

const RapportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: intervention, isLoading: loadingIntervention } = useIntervention(id || '');
  const { data: rapport, isLoading: loadingRapport, refetch } = useRapport(id || '');
  const updateRapport = useUpdateRapport();
  const signerRapport = useSignerRapport();

  const [isEditing, setIsEditing] = useState(false);
  const [showSignModal, setShowSignModal] = useState(false);
  const [editData, setEditData] = useState({
    travaux_realises: '',
    observations: '',
    recommandations: '',
    pieces_remplacees: '',
    materiel_utilise: '',
  });
  const [signatureData, setSignatureData] = useState({
    nom_signataire: '',
    signature_client: '',
  });

  React.useEffect(() => {
    if (rapport) {
      setEditData({
        travaux_realises: rapport.travaux_realises || '',
        observations: rapport.observations || '',
        recommandations: rapport.recommandations || '',
        pieces_remplacees: rapport.pieces_remplacees || '',
        materiel_utilise: rapport.materiel_utilise || '',
      });
    }
  }, [rapport]);

  const handleSaveEdit = async () => {
    if (!id) return;
    await updateRapport.mutateAsync({
      interventionId: id,
      data: editData,
    });
    setIsEditing(false);
    refetch();
  };

  const handleSign = async () => {
    if (!id || !signatureData.nom_signataire) return;
    await signerRapport.mutateAsync({
      interventionId: id,
      data: signatureData,
    });
    setShowSignModal(false);
    refetch();
  };

  if (loadingIntervention || loadingRapport) {
    return (
      <PageWrapper title="Rapport d'intervention">
        <div className="azals-loading">
          <RefreshCw className="animate-spin" size={24} />
          <span>Chargement...</span>
        </div>
      </PageWrapper>
    );
  }

  if (!intervention || !rapport) {
    return (
      <PageWrapper title="Rapport d'intervention">
        <Card>
          <div className="azals-empty">
            <AlertCircle size={48} />
            <h3>Rapport non trouvé</h3>
            <p>Le rapport n'existe pas ou l'intervention n'est pas terminée.</p>
            <Button onClick={() => navigate(`/interventions/${id}`)}>
              Retour à l'intervention
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const canEdit = !rapport.is_signed;

  return (
    <PageWrapper
      title={`Rapport ${intervention.reference}`}
      subtitle={intervention.titre}
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            onClick={() => navigate(`/interventions/${id}`)}
          >
            Retour
          </Button>
          {canEdit && !isEditing && (
            <Button
              variant="ghost"
              leftIcon={<Edit size={16} />}
              onClick={() => setIsEditing(true)}
            >
              Modifier
            </Button>
          )}
          {canEdit && (
            <Button
              leftIcon={<PenLine size={16} />}
              onClick={() => setShowSignModal(true)}
            >
              Faire signer
            </Button>
          )}
        </ButtonGroup>
      }
    >
      {/* Status */}
      <Card className="mb-4">
        {rapport.is_signed ? (
          <div className="azals-rapport-signed">
            <CheckCircle2 size={24} className="text-success" />
            <div>
              <h3>Rapport signé</h3>
              <p>
                Signé par <strong>{rapport.nom_signataire}</strong> le{' '}
                {formatDate(rapport.date_signature)}
              </p>
            </div>
          </div>
        ) : (
          <div className="azals-rapport-unsigned">
            <AlertCircle size={24} className="text-warning" />
            <div>
              <h3>En attente de signature</h3>
              <p>Ce rapport doit être signé par le client.</p>
            </div>
          </div>
        )}
      </Card>

      {/* Intervention Summary */}
      <Card title="Résumé de l'intervention" className="mb-4">
        <Grid cols={3} gap="md">
          <div>
            <span className="text-muted">Date</span>
            <p>{formatDate(intervention.date_prevue)}</p>
          </div>
          <div>
            <span className="text-muted">Durée</span>
            <p>{formatDuration(intervention.duree_reelle_minutes)}</p>
          </div>
          <div>
            <span className="text-muted">Intervenant</span>
            <p>{intervention.intervenant_name || '-'}</p>
          </div>
        </Grid>
      </Card>

      {/* Rapport Content */}
      <Card title="Détails du rapport" className="mb-4">
        {isEditing ? (
          <div className="azals-rapport-edit">
            <div className="azals-form-field">
              <label>Travaux réalisés</label>
              <textarea
                value={editData.travaux_realises}
                onChange={(e) => setEditData({ ...editData, travaux_realises: e.target.value })}
                className="azals-textarea"
                rows={4}
              />
            </div>

            <Grid cols={2} gap="md">
              <div className="azals-form-field">
                <label>Pièces remplacées</label>
                <textarea
                  value={editData.pieces_remplacees}
                  onChange={(e) => setEditData({ ...editData, pieces_remplacees: e.target.value })}
                  className="azals-textarea"
                  rows={3}
                />
              </div>

              <div className="azals-form-field">
                <label>Matériel utilisé</label>
                <textarea
                  value={editData.materiel_utilise}
                  onChange={(e) => setEditData({ ...editData, materiel_utilise: e.target.value })}
                  className="azals-textarea"
                  rows={3}
                />
              </div>
            </Grid>

            <div className="azals-form-field">
              <label>Observations</label>
              <textarea
                value={editData.observations}
                onChange={(e) => setEditData({ ...editData, observations: e.target.value })}
                className="azals-textarea"
                rows={3}
              />
            </div>

            <div className="azals-form-field">
              <label>Recommandations</label>
              <textarea
                value={editData.recommandations}
                onChange={(e) => setEditData({ ...editData, recommandations: e.target.value })}
                className="azals-textarea"
                rows={3}
              />
            </div>

            <div className="azals-form-actions">
              <Button variant="ghost" onClick={() => setIsEditing(false)}>
                Annuler
              </Button>
              <Button
                onClick={handleSaveEdit}
                isLoading={updateRapport.isPending}
                leftIcon={<Check size={16} />}
              >
                Enregistrer
              </Button>
            </div>
          </div>
        ) : (
          <dl className="azals-dl azals-dl--wide">
            <dt>Travaux réalisés</dt>
            <dd>{rapport.travaux_realises || <em className="text-muted">Non renseigné</em>}</dd>

            <dt>Pièces remplacées</dt>
            <dd>{rapport.pieces_remplacees || <em className="text-muted">Aucune</em>}</dd>

            <dt>Matériel utilisé</dt>
            <dd>{rapport.materiel_utilise || <em className="text-muted">Non renseigné</em>}</dd>

            <dt>Observations</dt>
            <dd>{rapport.observations || <em className="text-muted">Aucune</em>}</dd>

            <dt>Recommandations</dt>
            <dd>{rapport.recommandations || <em className="text-muted">Aucune</em>}</dd>

            {rapport.temps_passe_minutes && (
              <>
                <dt>Temps passé</dt>
                <dd>{formatDuration(rapport.temps_passe_minutes)}</dd>
              </>
            )}
          </dl>
        )}
      </Card>

      {/* Photos */}
      {rapport.photos && rapport.photos.length > 0 && (
        <Card title="Photos" className="mb-4">
          <div className="azals-photos-grid">
            {rapport.photos.map((photo, index) => (
              <div key={index} className="azals-photo-item">
                <img src={photo} alt={`Photo ${index + 1}`} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Signature Modal */}
      {showSignModal && (
        <Modal
          isOpen={showSignModal}
          onClose={() => setShowSignModal(false)}
          title="Signature du rapport"
          size="md"
        >
          <div className="azals-sign-modal">
            <div className="azals-form-field azals-form-field--required">
              <label>Nom du signataire</label>
              <input
                type="text"
                value={signatureData.nom_signataire}
                onChange={(e) => setSignatureData({ ...signatureData, nom_signataire: e.target.value })}
                className="azals-input"
                placeholder="Nom et prénom du client"
              />
            </div>

            <div className="azals-form-field">
              <label>Signature</label>
              <div className="azals-signature-pad">
                <textarea
                  value={signatureData.signature_client}
                  onChange={(e) => setSignatureData({ ...signatureData, signature_client: e.target.value })}
                  className="azals-textarea"
                  rows={4}
                  placeholder="Zone de signature (dans une version future: canvas de signature tactile)"
                />
              </div>
              <p className="text-muted text-sm mt-1">
                En signant, le client confirme la bonne réalisation des travaux.
              </p>
            </div>

            <div className="azals-form-actions">
              <Button variant="ghost" onClick={() => setShowSignModal(false)}>
                Annuler
              </Button>
              <Button
                onClick={handleSign}
                isLoading={signerRapport.isPending}
                leftIcon={<PenLine size={16} />}
                isDisabled={!signatureData.nom_signataire}
              >
                Valider la signature
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Planning (Calendar View)
// ============================================================

const PlanningPage: React.FC = () => {
  const navigate = useNavigate();
  const today = new Date();
  const [currentWeekStart, setCurrentWeekStart] = useState(() => {
    const date = new Date(today);
    date.setDate(date.getDate() - date.getDay() + 1); // Monday
    return date.toISOString().split('T')[0];
  });

  const weekEnd = useMemo(() => {
    const date = new Date(currentWeekStart);
    date.setDate(date.getDate() + 6);
    return date.toISOString().split('T')[0];
  }, [currentWeekStart]);

  const { data: interventions, isLoading } = usePlanningInterventions(currentWeekStart, weekEnd);

  const weekDays = useMemo(() => {
    const days = [];
    const start = new Date(currentWeekStart);
    for (let i = 0; i < 7; i++) {
      const date = new Date(start);
      date.setDate(date.getDate() + i);
      days.push({
        date: date.toISOString().split('T')[0],
        label: date.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }),
        isToday: date.toDateString() === today.toDateString(),
      });
    }
    return days;
  }, [currentWeekStart, today]);

  const interventionsByDay = useMemo(() => {
    const byDay: Record<string, Intervention[]> = {};
    weekDays.forEach((day) => {
      byDay[day.date] = [];
    });
    interventions?.forEach((int) => {
      if (int.date_prevue && byDay[int.date_prevue]) {
        byDay[int.date_prevue].push(int);
      }
    });
    return byDay;
  }, [interventions, weekDays]);

  const goToWeek = (direction: 'prev' | 'next') => {
    const date = new Date(currentWeekStart);
    date.setDate(date.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentWeekStart(date.toISOString().split('T')[0]);
  };

  return (
    <PageWrapper
      title="Planning des interventions"
      actions={
        <ButtonGroup>
          <Button variant="ghost" onClick={() => goToWeek('prev')}>
            Semaine précédente
          </Button>
          <Button variant="ghost" onClick={() => {
            const date = new Date();
            date.setDate(date.getDate() - date.getDay() + 1);
            setCurrentWeekStart(date.toISOString().split('T')[0]);
          }}>
            Aujourd'hui
          </Button>
          <Button variant="ghost" onClick={() => goToWeek('next')}>
            Semaine suivante
          </Button>
        </ButtonGroup>
      }
    >
      {isLoading ? (
        <div className="azals-loading"><div className="azals-spinner" /></div>
      ) : (
        <Card>
          <div className="azals-planning-grid">
            {weekDays.map((day) => (
              <div
                key={day.date}
                className={`azals-planning-day ${day.isToday ? 'azals-planning-day--today' : ''}`}
              >
                <div className="azals-planning-day__header">
                  <span>{day.label}</span>
                  {interventionsByDay[day.date]?.length > 0 && (
                    <span className="azals-planning-day__count">
                      {interventionsByDay[day.date].length}
                    </span>
                  )}
                </div>
                <div className="azals-planning-day__content">
                  {interventionsByDay[day.date]?.map((int) => (
                    <div
                      key={int.id}
                      className={`azals-planning-item azals-planning-item--${STATUT_CONFIG[int.statut].color}`}
                      onClick={() => navigate(`/interventions/${int.id}`)}
                    >
                      <span className="azals-planning-item__time">{int.heure_prevue || '—'}</span>
                      <span className="azals-planning-item__ref">{int.reference}</span>
                      <span className="azals-planning-item__client">{int.client_name}</span>
                    </div>
                  ))}
                  {interventionsByDay[day.date]?.length === 0 && (
                    <div className="azals-planning-day__empty">
                      Aucune intervention
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAGES - Rapports Finaux List
// ============================================================

const RapportsFinalList: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageWrapper title="Rapports finaux">
      <Card>
        <div className="azals-empty">
          <FileText size={48} />
          <h3>Rapports consolidés</h3>
          <p>Générez des rapports consolidés par projet ou donneur d'ordre.</p>
          <Button onClick={() => navigate('/interventions/rapports/generate')}>
            Générer un rapport
          </Button>
        </div>
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// EXPORTS - Router
// ============================================================

export const InterventionsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InterventionsDashboard />} />
    <Route path="list" element={<InterventionsListPage />} />
    <Route path="new" element={<InterventionFormPage />} />
    <Route path="planning" element={<PlanningPage />} />
    <Route path="rapports" element={<RapportsFinalList />} />
    <Route path=":id" element={<InterventionDetailPage />} />
    <Route path=":id/edit" element={<InterventionFormPage />} />
    <Route path=":id/rapport" element={<RapportPage />} />
  </Routes>
);

export default InterventionsRoutes;
