/**
 * AZALSCORE Module - AFFAIRES Types
 * Types partagés pour le module Affaires (projets/chantiers)
 */

import React from 'react';
import { Calendar, Clock, CheckCircle2, XCircle, PauseCircle } from 'lucide-react';

// ============================================================
// TYPES PRINCIPAUX
// ============================================================

export type AffaireStatus = 'PLANIFIE' | 'EN_COURS' | 'EN_PAUSE' | 'TERMINE' | 'ANNULE';
export type AffairePriority = 'BASSE' | 'NORMALE' | 'HAUTE' | 'URGENTE';

export interface Affaire {
  id: string;
  reference: string;          // AFF-YY-MM-XXXX
  code: string;
  name: string;
  description?: string;

  // Client
  customer_id?: string;
  customer_code?: string;
  customer_name?: string;

  // Origine
  commande_id?: string;
  commande_reference?: string;
  ods_id?: string;
  ods_reference?: string;
  devis_id?: string;
  devis_reference?: string;

  // Dates
  start_date?: string;
  end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;

  // Status
  status: AffaireStatus;
  priority: AffairePriority;
  progress: number;           // 0-100

  // Budget
  budget_total?: number;
  budget_spent?: number;
  budget_remaining?: number;
  currency?: string;

  // Facturation
  total_invoiced?: number;
  total_paid?: number;
  total_remaining?: number;

  // Ressources
  project_manager_id?: string;
  project_manager_name?: string;
  team_members?: TeamMember[];

  // Interventions liées
  interventions?: AffaireIntervention[];

  // Documents
  documents?: AffaireDocument[];

  // Historique
  history?: AffaireHistoryEntry[];

  // Notes
  notes?: string;
  internal_notes?: string;

  // Meta
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface TeamMember {
  id: string;
  user_id: string;
  name: string;
  role?: string;
  hours_allocated?: number;
  hours_spent?: number;
}

export interface AffaireIntervention {
  id: string;
  reference: string;
  date: string;
  status: string;
  technician_name?: string;
  duration_hours?: number;
  description?: string;
}

export interface AffaireDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url?: string;
  size?: number;
  created_at: string;
  created_by?: string;
}

export interface AffaireHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface AffaireFormData {
  name: string;
  description?: string;
  customer_id?: string;
  status: AffaireStatus;
  priority: AffairePriority;
  start_date?: string;
  end_date?: string;
  budget_total?: number;
  progress?: number;
  project_manager_id?: string;
  notes?: string;
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

export const STATUS_CONFIG: Record<AffaireStatus, { label: string; color: string; icon: React.ReactNode }> = {
  PLANIFIE: { label: 'Planifié', color: 'purple', icon: React.createElement(Calendar, { size: 14 }) },
  EN_COURS: { label: 'En cours', color: 'blue', icon: React.createElement(Clock, { size: 14 }) },
  EN_PAUSE: { label: 'En pause', color: 'orange', icon: React.createElement(PauseCircle, { size: 14 }) },
  TERMINE: { label: 'Terminé', color: 'green', icon: React.createElement(CheckCircle2, { size: 14 }) },
  ANNULE: { label: 'Annulé', color: 'gray', icon: React.createElement(XCircle, { size: 14 }) },
};

export const PRIORITY_CONFIG: Record<AffairePriority, { label: string; color: string }> = {
  BASSE: { label: 'Basse', color: 'gray' },
  NORMALE: { label: 'Normale', color: 'blue' },
  HAUTE: { label: 'Haute', color: 'orange' },
  URGENTE: { label: 'Urgente', color: 'red' },
};

// ============================================================
// HELPERS
// ============================================================

export const formatDuration = (hours?: number): string => {
  if (!hours) return '-';
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 24) return `${hours.toFixed(1)} h`;
  const days = Math.floor(hours / 8);
  const remainingHours = hours % 8;
  return remainingHours > 0 ? `${days} j ${remainingHours.toFixed(1)} h` : `${days} j`;
};

export const generateReference = (): string => {
  const now = new Date();
  const yy = String(now.getFullYear()).slice(-2);
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const xxxx = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
  return `AFF-${yy}-${mm}-${xxxx}`;
};

export const isLate = (affaire: Affaire): boolean => {
  if (!affaire.end_date || affaire.status === 'TERMINE' || affaire.status === 'ANNULE') {
    return false;
  }
  const now = new Date();
  const endDate = new Date(affaire.end_date);
  return now > endDate;
};

export const getDaysRemaining = (endDate?: string): number | null => {
  if (!endDate) return null;
  const now = new Date();
  const end = new Date(endDate);
  const diffTime = end.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const getBudgetStatus = (affaire: Affaire): 'ok' | 'warning' | 'danger' => {
  if (!affaire.budget_total || !affaire.budget_spent) return 'ok';
  const ratio = affaire.budget_spent / affaire.budget_total;
  if (ratio > 1) return 'danger';
  if (ratio > 0.9) return 'warning';
  return 'ok';
};

export const getProgressStatus = (affaire: Affaire): 'ok' | 'warning' | 'danger' => {
  if (!affaire.end_date || affaire.status === 'TERMINE') return 'ok';

  const daysRemaining = getDaysRemaining(affaire.end_date);
  if (daysRemaining === null) return 'ok';

  // Si en retard
  if (daysRemaining < 0 && affaire.progress < 100) return 'danger';

  // Estimation si on va finir à temps
  const totalDays = affaire.start_date
    ? Math.ceil((new Date(affaire.end_date).getTime() - new Date(affaire.start_date).getTime()) / (1000 * 60 * 60 * 24))
    : null;

  if (totalDays && totalDays > 0) {
    const daysElapsed = totalDays - daysRemaining;
    const expectedProgress = (daysElapsed / totalDays) * 100;
    if (affaire.progress < expectedProgress - 20) return 'danger';
    if (affaire.progress < expectedProgress - 10) return 'warning';
  }

  return 'ok';
};
