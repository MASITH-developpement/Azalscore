/**
 * AZALSCORE Module - Ordres de Service Types
 * Types et utilitaires pour les interventions et travaux
 */

// ============================================================
// TYPES DE BASE
// ============================================================

export type InterventionStatut = 'DRAFT' | 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'BLOQUEE' | 'TERMINEE' | 'ANNULEE';
export type InterventionPriorite = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type TypeIntervention = 'INSTALLATION' | 'MAINTENANCE' | 'REPARATION' | 'INSPECTION' | 'FORMATION' | 'CONSULTATION' | 'AUTRE';
export type CorpsEtat = 'ELECTRICITE' | 'PLOMBERIE' | 'ELECTRICITE_PLOMBERIE';
export type CanalDemande = 'TELEPHONE' | 'EMAIL' | 'PORTAIL' | 'DIRECT' | 'CONTRAT' | 'AUTRE';

/**
 * Rapport d'intervention
 */
export interface RapportIntervention {
  id: string;
  intervention_id: string;
  reference_intervention?: string;

  // Contenu
  travaux_realises?: string;
  observations?: string;
  recommandations?: string;
  pieces_remplacees?: string;
  temps_passe_minutes?: number;
  materiel_utilise?: string;
  photos: string[];

  // Signature
  signature_client?: string;
  nom_signataire?: string;
  date_signature?: string;
  is_signed: boolean;
  is_locked: boolean;

  created_at: string;
  updated_at?: string;
}

export interface Intervention {
  id: string;
  reference: string;

  // Client & Donneur d'ordre
  client_id: string;
  client_name?: string;
  client_code?: string;
  donneur_ordre_id?: string;
  donneur_ordre_name?: string;

  // Projet & Affaire
  projet_id?: string;
  projet_name?: string;
  affaire_id?: string;
  affaire_reference?: string;

  // Type & Classification
  type_intervention: TypeIntervention;
  priorite: InterventionPriorite;
  corps_etat?: CorpsEtat;
  canal_demande?: CanalDemande;
  reference_externe?: string;

  // Details
  titre?: string;
  description?: string;
  notes_internes?: string;
  notes_client?: string;

  // Planification
  date_prevue?: string;
  heure_prevue?: string;
  date_prevue_debut?: string;
  date_prevue_fin?: string;
  duree_prevue_minutes?: number;

  // Intervenant & Equipe
  intervenant_id?: string;
  intervenant_name?: string;
  equipe?: Array<{ id: string; name: string; role?: string }>;

  // Statut
  statut: InterventionStatut;
  motif_blocage?: string;
  date_blocage?: string;
  date_deblocage?: string;

  // Execution reelle
  date_arrivee_site?: string;
  date_demarrage?: string;
  date_fin?: string;
  date_debut_reelle?: string;
  date_fin_reelle?: string;
  duree_reelle_minutes?: number;

  // Adresse
  adresse_intervention?: string;
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  ville?: string;
  code_postal?: string;
  pays?: string;

  // Contact sur place
  contact_sur_place?: string;
  telephone_contact?: string;
  email_contact?: string;

  // Materiel
  materiel_necessaire?: string;
  materiel_utilise?: string;

  // Rapport integre
  rapport?: RapportIntervention;

  // Cloture directe (anciens champs)
  commentaire_cloture?: string;
  photos?: string[];
  signature_client?: string;

  // Facturation
  facturable?: boolean;
  montant_ht?: number;
  montant_ttc?: number;
  facture_id?: string;
  facture_reference?: string;

  // Documents & Historique
  documents?: InterventionDocument[];
  history?: InterventionHistoryEntry[];

  // Geolocalisation
  geoloc_arrivee_lat?: number;
  geoloc_arrivee_lng?: number;

  // Meta
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DonneurOrdre {
  id: string;
  code: string;
  nom: string;
  type?: string;
  client_id?: string;
  fournisseur_id?: string;
  email?: string;
  telephone?: string;
  adresse?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
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
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'Intervention en cours de creation' },
  A_PLANIFIER: { label: 'A planifier', color: 'orange', description: 'Intervention en attente de planification' },
  PLANIFIEE: { label: 'Planifiee', color: 'blue', description: 'Intervention planifiee, prete a demarrer' },
  EN_COURS: { label: 'En cours', color: 'yellow', description: 'Intervention en cours d\'execution' },
  BLOQUEE: { label: 'Bloquee', color: 'red', description: 'Intervention bloquee' },
  TERMINEE: { label: 'Terminee', color: 'green', description: 'Intervention terminee avec succes' },
  ANNULEE: { label: 'Annulee', color: 'gray', description: 'Intervention annulee' },
};

export const PRIORITE_CONFIG: Record<InterventionPriorite, { label: string; color: string; description: string }> = {
  LOW: { label: 'Basse', color: 'gray', description: 'Intervention non urgente' },
  NORMAL: { label: 'Normale', color: 'blue', description: 'Traitement standard' },
  HIGH: { label: 'Haute', color: 'orange', description: 'Traitement prioritaire' },
  URGENT: { label: 'Urgente', color: 'red', description: 'Intervention immediate requise' },
};

export const TYPE_INTERVENTION_CONFIG: Record<TypeIntervention, { label: string; color: string }> = {
  INSTALLATION: { label: 'Installation', color: 'blue' },
  MAINTENANCE: { label: 'Maintenance', color: 'green' },
  REPARATION: { label: 'Reparation', color: 'orange' },
  INSPECTION: { label: 'Inspection', color: 'purple' },
  FORMATION: { label: 'Formation', color: 'cyan' },
  CONSULTATION: { label: 'Consultation', color: 'gray' },
  AUTRE: { label: 'Autre', color: 'gray' },
};

export const CORPS_ETAT_CONFIG: Record<CorpsEtat, { label: string; color: string }> = {
  ELECTRICITE: { label: 'Electricite', color: 'yellow' },
  PLOMBERIE: { label: 'Plomberie', color: 'blue' },
  ELECTRICITE_PLOMBERIE: { label: 'Elec. & Plomb.', color: 'purple' },
};

export const CANAL_DEMANDE_CONFIG: Record<CanalDemande, { label: string }> = {
  TELEPHONE: { label: 'Telephone' },
  EMAIL: { label: 'Email' },
  PORTAIL: { label: 'Portail client' },
  DIRECT: { label: 'Direct' },
  CONTRAT: { label: 'Contrat' },
  AUTRE: { label: 'Autre' },
};

export const STATUTS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'A_PLANIFIER', label: 'A planifier', color: 'orange' },
  { value: 'PLANIFIEE', label: 'Planifiee', color: 'blue' },
  { value: 'EN_COURS', label: 'En cours', color: 'yellow' },
  { value: 'BLOQUEE', label: 'Bloquee', color: 'red' },
  { value: 'TERMINEE', label: 'Terminee', color: 'green' },
  { value: 'ANNULEE', label: 'Annulee', color: 'gray' },
];

export const PRIORITES = [
  { value: 'LOW', label: 'Basse', color: 'gray' },
  { value: 'NORMAL', label: 'Normale', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'URGENT', label: 'Urgente', color: 'red' },
];

export const TYPES_INTERVENTION = [
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Reparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' },
];

export const CORPS_ETATS = [
  { value: 'ELECTRICITE', label: 'Electricite' },
  { value: 'PLOMBERIE', label: 'Plomberie' },
  { value: 'ELECTRICITE_PLOMBERIE', label: 'Elec. & Plomb.' },
];

export const CANAUX_DEMANDE = [
  { value: 'TELEPHONE', label: 'Telephone' },
  { value: 'EMAIL', label: 'Email' },
  { value: 'PORTAIL', label: 'Portail client' },
  { value: 'DIRECT', label: 'Direct' },
  { value: 'CONTRAT', label: 'Contrat' },
  { value: 'AUTRE', label: 'Autre' },
];

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Formater une duree en minutes en texte lisible
 */
export const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) return `${hours}h`;
  return `${hours}h${mins}`;
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
  return PRIORITE_CONFIG[priorite] || PRIORITE_CONFIG.NORMAL;
};

/**
 * Obtenir la configuration du type d'intervention
 */
export const getTypeInterventionConfig = (type: TypeIntervention) => {
  return TYPE_INTERVENTION_CONFIG[type] || TYPE_INTERVENTION_CONFIG.AUTRE;
};

/**
 * Verifier si l'intervention peut etre modifiee
 */
export const canEditIntervention = (intervention: Intervention): boolean => {
  return ['DRAFT', 'A_PLANIFIER', 'PLANIFIEE'].includes(intervention.statut);
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
  return intervention.statut === 'TERMINEE' && intervention.facturable !== false;
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
  if (intervention.date_demarrage && intervention.date_fin) {
    const start = new Date(intervention.date_demarrage);
    const end = new Date(intervention.date_fin);
    const minutes = Math.round((end.getTime() - start.getTime()) / (1000 * 60));
    return formatDuration(minutes);
  }
  return null;
};

/**
 * Calculer l'ecart entre estimee et reelle
 */
export const getDurationVariance = (intervention: Intervention): number | null => {
  if (!intervention.duree_prevue_minutes || !intervention.duree_reelle_minutes) {
    return null;
  }
  return intervention.duree_reelle_minutes - intervention.duree_prevue_minutes;
};

/**
 * Calculer l'ecart de montant
 */
export const getAmountVariance = (intervention: Intervention): number | null => {
  if (!intervention.montant_ht) {
    return null;
  }
  // On compare le montant prevu vs reel si disponible dans le rapport
  return null;
};

/**
 * Obtenir le nombre de photos
 */
export const getPhotoCount = (intervention: Intervention): number => {
  return (intervention.rapport?.photos || []).length;
};

/**
 * Obtenir l'adresse complete
 */
export const getFullAddress = (intervention: Intervention): string | null => {
  const parts = [];
  if (intervention.adresse_ligne1) parts.push(intervention.adresse_ligne1);
  if (intervention.adresse_ligne2) parts.push(intervention.adresse_ligne2);
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
  if (!intervention.date_prevue_debut) return false;
  return new Date(intervention.date_prevue_debut) < new Date();
};

/**
 * Verifier si l'intervention est planifiee pour aujourd'hui
 */
export const isInterventionToday = (intervention: Intervention): boolean => {
  if (!intervention.date_prevue_debut) return false;
  const today = new Date().toDateString();
  return new Date(intervention.date_prevue_debut).toDateString() === today;
};
