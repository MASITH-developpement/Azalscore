/**
 * AZALSCORE Module - INTERVENTIONS Types
 * Types partagés pour le module Interventions terrain
 */

import React from 'react';
import { Calendar, Clock, CheckCircle2, AlertCircle, Play, FileEdit, Lock } from 'lucide-react';

// ============================================================
// TYPES PRINCIPAUX
// ============================================================

export type InterventionStatut = 'DRAFT' | 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'BLOQUEE' | 'TERMINEE' | 'ANNULEE';
export type InterventionPriorite = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type InterventionType = 'INSTALLATION' | 'MAINTENANCE' | 'REPARATION' | 'INSPECTION' | 'FORMATION' | 'CONSULTATION' | 'AUTRE';
export type CorpsEtat = 'ELECTRICITE' | 'PLOMBERIE' | 'ELECTRICITE_PLOMBERIE';

export interface Intervention {
  id: string;
  reference: string;

  // Client
  client_id: string;
  client_name?: string;
  client_code?: string;

  // Donneur d'ordre
  donneur_ordre_id?: string;
  donneur_ordre_name?: string;

  // Projet/Affaire
  projet_id?: string;
  projet_name?: string;
  affaire_id?: string;
  affaire_reference?: string;

  // Type et priorité
  type_intervention: InterventionType;
  priorite: InterventionPriorite;
  corps_etat?: CorpsEtat;

  // Détails
  titre: string;
  description?: string;

  // Planification
  date_prevue?: string;
  heure_prevue?: string;
  date_prevue_debut?: string;
  date_prevue_fin?: string;
  duree_prevue_minutes?: number;

  // Intervenant
  intervenant_id?: string;
  intervenant_name?: string;
  equipe?: InterventionEquipeMembre[];

  // Statut
  statut: InterventionStatut;

  // Blocage
  motif_blocage?: string;
  date_blocage?: string;
  date_deblocage?: string;

  // Indicateurs métier (calculés par le backend)
  indicateurs?: InterventionIndicateurs;

  // Réalisation
  date_debut_reelle?: string;
  date_fin_reelle?: string;
  duree_reelle_minutes?: number;

  // Adresse
  adresse_intervention?: string;
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  ville?: string;
  code_postal?: string;
  latitude?: number;
  longitude?: number;

  // Contact sur place
  contact_sur_place?: string;
  telephone_contact?: string;
  email_contact?: string;

  // Notes et matériel
  notes_internes?: string;
  notes_client?: string;
  materiel_necessaire?: string;
  materiel_utilise?: string;

  // Rapport
  rapport?: RapportIntervention;

  // Documents
  documents?: InterventionDocument[];

  // Historique
  history?: InterventionHistoryEntry[];

  // Facturation
  facturable?: boolean;
  montant_ht?: number;
  montant_ttc?: number;
  facture_id?: string;
  facture_reference?: string;

  // Meta
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface InterventionEquipeMembre {
  id: string;
  user_id: string;
  name: string;
  role?: string;
  is_principal?: boolean;
}

export interface RapportIntervention {
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

export interface InterventionDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url?: string;
  size?: number;
  created_at: string;
  created_by?: string;
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

export interface DonneurOrdre {
  id: string;
  code: string;
  nom: string;
  type?: string;
  email?: string;
  telephone?: string;
  is_active: boolean;
}

export interface InterventionFormData {
  // Section 1: Informations Client
  client_id: string;
  donneur_ordre_id?: string;
  reference_externe?: string;
  facturer_a: 'donneur_ordre' | 'client_final';
  adresse_ligne1?: string;
  adresse_ligne2?: string;
  code_postal?: string;
  ville?: string;

  // Section 2: Intervention
  type_intervention: InterventionType;
  priorite: InterventionPriorite;
  corps_etat?: CorpsEtat;
  titre?: string;
  date_prevue_debut?: string;
  duree_prevue_heures?: number;
  intervenant_id?: string;

  // Section 3: Description
  description?: string;
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
}

// ============================================================
// CONFIGURATIONS
// ============================================================

export const STATUT_CONFIG: Record<InterventionStatut, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', icon: React.createElement(FileEdit, { size: 14 }) },
  A_PLANIFIER: { label: 'À planifier', color: 'gray', icon: React.createElement(AlertCircle, { size: 14 }) },
  PLANIFIEE: { label: 'Planifiée', color: 'blue', icon: React.createElement(Calendar, { size: 14 }) },
  EN_COURS: { label: 'En cours', color: 'orange', icon: React.createElement(Play, { size: 14 }) },
  BLOQUEE: { label: 'Bloquée', color: 'red', icon: React.createElement(Lock, { size: 14 }) },
  TERMINEE: { label: 'Terminée', color: 'green', icon: React.createElement(CheckCircle2, { size: 14 }) },
  ANNULEE: { label: 'Annulée', color: 'gray', icon: React.createElement(AlertCircle, { size: 14 }) },
};

export const PRIORITE_CONFIG: Record<InterventionPriorite, { label: string; color: string }> = {
  LOW: { label: 'Basse', color: 'gray' },
  NORMAL: { label: 'Normale', color: 'blue' },
  HIGH: { label: 'Haute', color: 'orange' },
  URGENT: { label: 'Urgente', color: 'red' },
};

export const TYPE_CONFIG: Record<InterventionType, { label: string; color: string }> = {
  INSTALLATION: { label: 'Installation', color: 'purple' },
  MAINTENANCE: { label: 'Maintenance', color: 'blue' },
  REPARATION: { label: 'Réparation', color: 'orange' },
  INSPECTION: { label: 'Inspection', color: 'green' },
  FORMATION: { label: 'Formation', color: 'purple' },
  CONSULTATION: { label: 'Consultation', color: 'blue' },
  AUTRE: { label: 'Autre', color: 'gray' },
};

export const CORPS_ETAT_CONFIG: Record<CorpsEtat, { label: string; color: string }> = {
  ELECTRICITE: { label: 'Électricité', color: 'yellow' },
  PLOMBERIE: { label: 'Plomberie', color: 'blue' },
  ELECTRICITE_PLOMBERIE: { label: 'Électricité + Plomberie', color: 'purple' },
};

// ============================================================
// HELPERS
// ============================================================

export const formatAddress = (intervention: Intervention): string => {
  const parts = [
    intervention.adresse_ligne1,
    intervention.adresse_ligne2,
    intervention.code_postal && intervention.ville
      ? `${intervention.code_postal} ${intervention.ville}`
      : intervention.ville,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : intervention.adresse_intervention || '-';
};

export const isLate = (intervention: Intervention): boolean => {
  if (['TERMINEE', 'ANNULEE', 'DRAFT'].includes(intervention.statut)) {
    return false;
  }
  if (!intervention.date_prevue && !intervention.date_prevue_fin) {
    return false;
  }
  const now = new Date();
  const dueDate = new Date(intervention.date_prevue_fin || intervention.date_prevue!);
  return now > dueDate;
};

export const getDaysUntilIntervention = (intervention: Intervention): number | null => {
  if (!intervention.date_prevue && !intervention.date_prevue_debut) return null;
  const targetDate = intervention.date_prevue_debut || intervention.date_prevue;
  if (!targetDate) return null;
  const now = new Date();
  const date = new Date(targetDate);
  const diffTime = date.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const getDurationVariance = (intervention: Intervention): number | null => {
  if (!intervention.duree_prevue_minutes || !intervention.duree_reelle_minutes) {
    return null;
  }
  return intervention.duree_reelle_minutes - intervention.duree_prevue_minutes;
};

export const canStart = (intervention: Intervention): boolean => {
  return intervention.statut === 'PLANIFIEE';
};

export const canComplete = (intervention: Intervention): boolean => {
  return intervention.statut === 'EN_COURS';
};

export const canPlan = (intervention: Intervention): boolean => {
  return intervention.statut === 'A_PLANIFIER';
};

export const canValidate = (intervention: Intervention): boolean => {
  return intervention.statut === 'DRAFT';
};

export const canBlock = (intervention: Intervention): boolean => {
  return intervention.statut === 'EN_COURS';
};

export const canUnblock = (intervention: Intervention): boolean => {
  return intervention.statut === 'BLOQUEE';
};

// ============================================================
// INDICATEURS MÉTIER
// ============================================================

export interface InterventionIndicateurs {
  en_retard: boolean;
  jours_retard: number;
  derive_duree_minutes: number | null;
  derive_duree_pct: number | null;
  indicateur_risque: 'FAIBLE' | 'MOYEN' | 'ELEVE' | 'CRITIQUE';
  risque_justification: string;
}

export interface AnalyseIA {
  indicateurs: InterventionIndicateurs;
  resume_ia: string;
  actions_suggerees: { action: string; label: string; confiance: number }[];
  score_preparation: number;
  score_deductions: string[];
  generated_at: string;
}

// ============================================================
// STATISTIQUES
// ============================================================

export interface InterventionStats {
  brouillons: number;
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  bloquees: number;
  terminees_semaine: number;
  terminees_mois: number;
  duree_moyenne_minutes: number;
  interventions_jour: number;
}
