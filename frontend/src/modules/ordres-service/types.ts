/**
 * AZALSCORE Module - Ordres de Service Types
 * Types et utilitaires pour les interventions et travaux
 */

// ============================================================
// TYPES DE BASE
// ============================================================

export type InterventionStatut = 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'TERMINEE' | 'ANNULEE';
export type InterventionPriorite = 'BASSE' | 'NORMALE' | 'HAUTE' | 'URGENTE';

export interface Intervention {
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
  documents?: InterventionDocument[];
  history?: InterventionHistoryEntry[];
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DonneurOrdre {
  id: string;
  nom: string;
  code?: string;
  contact_nom?: string;
  contact_email?: string;
  contact_telephone?: string;
}

export interface InterventionDocument {
  id: string;
  intervention_id: string;
  name: string;
  file_url?: string;
  file_size?: number;
  mime_type?: string;
  doc_type?: 'photo' | 'rapport' | 'signature' | 'autre';
  created_at: string;
}

export interface InterventionHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface InterventionStats {
  total: number;
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  terminees: number;
  annulees: number;
}

// ============================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================

export const STATUT_CONFIG: Record<InterventionStatut, { label: string; color: string; description: string }> = {
  A_PLANIFIER: { label: 'A planifier', color: 'gray', description: 'Intervention en attente de planification' },
  PLANIFIEE: { label: 'Planifiee', color: 'blue', description: 'Intervention planifiee, prete a demarrer' },
  EN_COURS: { label: 'En cours', color: 'yellow', description: 'Intervention en cours d\'execution' },
  TERMINEE: { label: 'Terminee', color: 'green', description: 'Intervention terminee avec succes' },
  ANNULEE: { label: 'Annulee', color: 'red', description: 'Intervention annulee' },
};

export const PRIORITE_CONFIG: Record<InterventionPriorite, { label: string; color: string; description: string }> = {
  BASSE: { label: 'Basse', color: 'gray', description: 'Intervention non urgente' },
  NORMALE: { label: 'Normale', color: 'blue', description: 'Traitement standard' },
  HAUTE: { label: 'Haute', color: 'orange', description: 'Traitement prioritaire' },
  URGENTE: { label: 'Urgente', color: 'red', description: 'Intervention immediate requise' },
};

export const STATUTS = [
  { value: 'A_PLANIFIER', label: 'A planifier', color: 'gray' },
  { value: 'PLANIFIEE', label: 'Planifiee', color: 'blue' },
  { value: 'EN_COURS', label: 'En cours', color: 'yellow' },
  { value: 'TERMINEE', label: 'Terminee', color: 'green' },
  { value: 'ANNULEE', label: 'Annulee', color: 'red' },
];

export const PRIORITES = [
  { value: 'BASSE', label: 'Basse', color: 'gray' },
  { value: 'NORMALE', label: 'Normale', color: 'blue' },
  { value: 'HAUTE', label: 'Haute', color: 'orange' },
  { value: 'URGENTE', label: 'Urgente', color: 'red' },
];

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Formatage monnaie
 */
export const formatCurrency = (value: number): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);

/**
 * Formatage date
 */
export const formatDate = (date: string | undefined): string => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
};

/**
 * Formatage date/heure
 */
export const formatDateTime = (date: string | undefined): string => {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
};

/**
 * Formatage duree en minutes
 */
export const formatDuration = (minutes: number): string => {
  if (!minutes || minutes <= 0) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h${mins > 0 ? mins : ''}` : `${mins}min`;
};

/**
 * Obtenir la configuration du statut
 */
export const getStatutConfig = (statut: InterventionStatut) => {
  return STATUT_CONFIG[statut] || STATUT_CONFIG.A_PLANIFIER;
};

/**
 * Obtenir la configuration de la priorite
 */
export const getPrioriteConfig = (priorite: InterventionPriorite) => {
  return PRIORITE_CONFIG[priorite] || PRIORITE_CONFIG.NORMALE;
};

/**
 * Verifier si l'intervention peut etre modifiee
 */
export const canEditIntervention = (intervention: Intervention): boolean => {
  return ['A_PLANIFIER', 'PLANIFIEE'].includes(intervention.statut);
};

/**
 * Verifier si l'intervention peut demarrer
 */
export const canStartIntervention = (intervention: Intervention): boolean => {
  return intervention.statut === 'PLANIFIEE';
};

/**
 * Verifier si l'intervention peut etre terminee
 */
export const canCompleteIntervention = (intervention: Intervention): boolean => {
  return intervention.statut === 'EN_COURS';
};

/**
 * Verifier si l'intervention peut etre facturee
 */
export const canInvoiceIntervention = (intervention: Intervention): boolean => {
  return intervention.statut === 'TERMINEE';
};

/**
 * Calculer le temps ecoule depuis la creation
 */
export const getInterventionAge = (intervention: Intervention): string => {
  const created = new Date(intervention.created_at);
  const now = new Date();
  const hours = Math.round((now.getTime() - created.getTime()) / (1000 * 60 * 60));

  if (hours < 24) return `${hours}h`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}j`;
  const weeks = Math.round(days / 7);
  return `${weeks}sem`;
};

/**
 * Calculer la duree effective de l'intervention
 */
export const getActualDuration = (intervention: Intervention): string | null => {
  if (intervention.duree_reelle_minutes) {
    return formatDuration(intervention.duree_reelle_minutes);
  }
  if (intervention.date_debut_intervention && intervention.date_fin_intervention) {
    const start = new Date(intervention.date_debut_intervention);
    const end = new Date(intervention.date_fin_intervention);
    const minutes = Math.round((end.getTime() - start.getTime()) / (1000 * 60));
    return formatDuration(minutes);
  }
  return null;
};

/**
 * Calculer l'ecart entre estimee et reelle
 */
export const getDurationVariance = (intervention: Intervention): number | null => {
  if (!intervention.duree_estimee_minutes || !intervention.duree_reelle_minutes) {
    return null;
  }
  return intervention.duree_reelle_minutes - intervention.duree_estimee_minutes;
};

/**
 * Calculer l'ecart de montant
 */
export const getAmountVariance = (intervention: Intervention): number | null => {
  if (!intervention.montant_estime || !intervention.montant_reel) {
    return null;
  }
  return intervention.montant_reel - intervention.montant_estime;
};

/**
 * Obtenir le nombre de photos
 */
export const getPhotoCount = (intervention: Intervention): number => {
  return (intervention.photos || []).length;
};

/**
 * Obtenir l'adresse complete
 */
export const getFullAddress = (intervention: Intervention): string | null => {
  const parts = [];
  if (intervention.adresse_intervention) parts.push(intervention.adresse_intervention);
  if (intervention.code_postal || intervention.ville) {
    parts.push([intervention.code_postal, intervention.ville].filter(Boolean).join(' '));
  }
  return parts.length > 0 ? parts.join(', ') : null;
};

/**
 * Verifier si l'intervention est en retard (planifiee mais date passee)
 */
export const isInterventionLate = (intervention: Intervention): boolean => {
  if (intervention.statut !== 'PLANIFIEE') return false;
  if (!intervention.date_prevue) return false;
  return new Date(intervention.date_prevue) < new Date();
};

/**
 * Verifier si l'intervention est planifiee pour aujourd'hui
 */
export const isInterventionToday = (intervention: Intervention): boolean => {
  if (!intervention.date_prevue) return false;
  const today = new Date().toDateString();
  return new Date(intervention.date_prevue).toDateString() === today;
};
