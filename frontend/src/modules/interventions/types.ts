/**
 * AZALSCORE Module - INTERVENTIONS Types
 * Types partagés pour le module Interventions terrain
 */

import React from 'react';
import { Calendar, Clock, CheckCircle2, AlertCircle, Play } from 'lucide-react';

// ============================================================
// TYPES PRINCIPAUX
// ============================================================

export type InterventionStatut = 'A_PLANIFIER' | 'PLANIFIEE' | 'EN_COURS' | 'TERMINEE' | 'ANNULEE';
export type InterventionPriorite = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type InterventionType = 'INSTALLATION' | 'MAINTENANCE' | 'REPARATION' | 'INSPECTION' | 'FORMATION' | 'CONSULTATION' | 'AUTRE';

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
  nom: string;
  email?: string;
  telephone?: string;
  entreprise?: string;
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
  A_PLANIFIER: { label: 'À planifier', color: 'gray', icon: React.createElement(AlertCircle, { size: 14 }) },
  PLANIFIEE: { label: 'Planifiée', color: 'blue', icon: React.createElement(Calendar, { size: 14 }) },
  EN_COURS: { label: 'En cours', color: 'orange', icon: React.createElement(Play, { size: 14 }) },
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

// ============================================================
// HELPERS
// ============================================================

export const formatCurrency = (amount?: number, currency = 'EUR'): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

export const formatDateTime = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTime = (dateStr?: string): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDuration = (minutes?: number): string => {
  if (!minutes) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins} min`;
  if (mins === 0) return `${hours}h`;
  return `${hours}h${mins.toString().padStart(2, '0')}`;
};

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
  if (intervention.statut === 'TERMINEE' || intervention.statut === 'ANNULEE') {
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

// ============================================================
// STATISTIQUES
// ============================================================

export interface InterventionStats {
  a_planifier: number;
  planifiees: number;
  en_cours: number;
  terminees_semaine: number;
  terminees_mois: number;
  duree_moyenne_minutes: number;
  interventions_jour: number;
}
