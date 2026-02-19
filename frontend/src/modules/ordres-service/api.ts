/**
 * AZALSCORE - Ordres de Service API
 * ==================================
 * API client pour le module Ordres de Service (ODS)
 * Couvre: Interventions, Donneurs d'ordre, Rapports
 *
 * Numérotation: ODS-YY-MM-XXXX
 * Flux: CRM → DEV → [ODS] → AFF → FAC/AVO → CPT
 */

import { api } from '@/core/api-client';
import type {
  Intervention,
  DonneurOrdre,
  InterventionStats,
  InterventionDocument,
  RapportIntervention,
  InterventionStatut,
  InterventionPriorite,
  TypeIntervention,
  CorpsEtat,
  CanalDemande,
} from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type {
  Intervention,
  DonneurOrdre,
  InterventionStats,
  InterventionDocument,
  RapportIntervention,
  InterventionStatut,
  InterventionPriorite,
  TypeIntervention,
  CorpsEtat,
  CanalDemande,
};

// ============================================================================
// TYPES - Request/Response
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface InterventionFilters {
  statut?: InterventionStatut;
  priorite?: InterventionPriorite;
  type_intervention?: TypeIntervention;
  client_id?: string;
  donneur_ordre_id?: string;
  intervenant_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InterventionCreate {
  client_id: string;
  donneur_ordre_id?: string;
  type_intervention: TypeIntervention;
  priorite?: InterventionPriorite;
  corps_etat?: CorpsEtat;
  canal_demande?: CanalDemande;
  reference_externe?: string;
  titre?: string;
  description?: string;
  notes_internes?: string;
  date_prevue_debut?: string;
  date_prevue_fin?: string;
  duree_prevue_minutes?: number;
  intervenant_id?: string;
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  ville?: string;
  code_postal?: string;
  pays?: string;
  contact_sur_place?: string;
  telephone_contact?: string;
  materiel_necessaire?: string;
  facturable?: boolean;
}

export interface InterventionUpdate extends Partial<InterventionCreate> {
  statut?: InterventionStatut;
  motif_blocage?: string;
}

export interface DonneurOrdreCreate {
  code?: string;
  nom: string;
  type?: string;
  client_id?: string;
  fournisseur_id?: string;
  email?: string;
  telephone?: string;
  adresse?: string;
}

export interface RapportCreate {
  travaux_realises?: string;
  observations?: string;
  recommandations?: string;
  pieces_remplacees?: string;
  temps_passe_minutes?: number;
  materiel_utilise?: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/interventions';

function buildQueryString<T extends object>(params: T): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const ordresServiceApi = {
  // ==========================================================================
  // Dashboard & Stats
  // ==========================================================================

  /**
   * Récupère les statistiques des interventions
   */
  getStats: () =>
    api.get<InterventionStats>(`${BASE_PATH}/stats`),

  // ==========================================================================
  // Interventions
  // ==========================================================================

  /**
   * Liste les interventions avec filtres
   */
  list: (filters?: InterventionFilters) =>
    api.get<PaginatedResponse<Intervention>>(
      `${BASE_PATH}${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une intervention par son ID
   */
  get: (id: string) =>
    api.get<Intervention>(`${BASE_PATH}/${id}`),

  /**
   * Crée une nouvelle intervention
   */
  create: (data: InterventionCreate) =>
    api.post<Intervention>(BASE_PATH, data),

  /**
   * Met à jour une intervention
   */
  update: (id: string, data: InterventionUpdate) =>
    api.put<Intervention>(`${BASE_PATH}/${id}`, data),

  /**
   * Supprime une intervention (brouillon uniquement)
   */
  delete: (id: string) =>
    api.delete(`${BASE_PATH}/${id}`),

  // ==========================================================================
  // Workflow
  // ==========================================================================

  /**
   * Planifie une intervention
   */
  planifier: (id: string, data: {
    date_prevue_debut: string;
    date_prevue_fin?: string;
    intervenant_id?: string;
  }) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/planifier`, data),

  /**
   * Démarre une intervention
   */
  demarrer: (id: string, data?: {
    date_arrivee_site?: string;
    geoloc_lat?: number;
    geoloc_lng?: number;
  }) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/demarrer`, data || {}),

  /**
   * Bloque une intervention
   */
  bloquer: (id: string, motif: string) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/bloquer`, { motif }),

  /**
   * Débloque une intervention
   */
  debloquer: (id: string) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/debloquer`, {}),

  /**
   * Termine une intervention
   */
  terminer: (id: string, data?: {
    commentaire_cloture?: string;
    duree_reelle_minutes?: number;
  }) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/terminer`, data || {}),

  /**
   * Annule une intervention
   */
  annuler: (id: string, motif?: string) =>
    api.post<Intervention>(`${BASE_PATH}/${id}/annuler`, { motif }),

  // ==========================================================================
  // Rapport
  // ==========================================================================

  /**
   * Crée ou met à jour le rapport d'intervention
   */
  saveRapport: (interventionId: string, data: RapportCreate) =>
    api.post<RapportIntervention>(`${BASE_PATH}/${interventionId}/rapport`, data),

  /**
   * Signe le rapport (client)
   */
  signerRapport: (interventionId: string, data: {
    signature_client: string;
    nom_signataire: string;
  }) =>
    api.post<RapportIntervention>(`${BASE_PATH}/${interventionId}/rapport/signer`, data),

  /**
   * Verrouille le rapport
   */
  verrouillerRapport: (interventionId: string) =>
    api.post<RapportIntervention>(`${BASE_PATH}/${interventionId}/rapport/verrouiller`, {}),

  // ==========================================================================
  // Photos
  // ==========================================================================

  /**
   * Upload une photo
   */
  uploadPhoto: (interventionId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<InterventionDocument>(
      `${BASE_PATH}/${interventionId}/photos`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  /**
   * Supprime une photo
   */
  deletePhoto: (interventionId: string, photoId: string) =>
    api.delete(`${BASE_PATH}/${interventionId}/photos/${photoId}`),

  // ==========================================================================
  // Facturation
  // ==========================================================================

  /**
   * Crée une facture depuis l'intervention
   */
  createFacture: (interventionId: string) =>
    api.post<{ id: string; number: string }>(`${BASE_PATH}/${interventionId}/facturer`, {}),

  // ==========================================================================
  // Donneurs d'ordre
  // ==========================================================================

  /**
   * Liste les donneurs d'ordre
   */
  listDonneursOrdre: () =>
    api.get<DonneurOrdre[]>(`${BASE_PATH}/donneurs-ordre`),

  /**
   * Crée un donneur d'ordre
   */
  createDonneurOrdre: (data: DonneurOrdreCreate) =>
    api.post<DonneurOrdre>(`${BASE_PATH}/donneurs-ordre`, data),

  /**
   * Met à jour un donneur d'ordre
   */
  updateDonneurOrdre: (id: string, data: Partial<DonneurOrdreCreate>) =>
    api.put<DonneurOrdre>(`${BASE_PATH}/donneurs-ordre/${id}`, data),

  /**
   * Supprime un donneur d'ordre
   */
  deleteDonneurOrdre: (id: string) =>
    api.delete(`${BASE_PATH}/donneurs-ordre/${id}`),
};

export default ordresServiceApi;
