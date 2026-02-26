/**
 * AZALSCORE Module - HR - Constants
 * Constantes pour le module Ressources Humaines
 */

// ============================================================================
// TYPES DE CONTRAT
// ============================================================================

export const CONTRACT_TYPES = [
  { value: 'CDI', label: 'CDI' },
  { value: 'CDD', label: 'CDD' },
  { value: 'INTERIM', label: 'Interim' },
  { value: 'APPRENTICE', label: 'Apprenti' },
  { value: 'INTERN', label: 'Stagiaire' }
] as const;

// ============================================================================
// STATUTS EMPLOYES
// ============================================================================

export const EMPLOYEE_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'ON_LEAVE', label: 'En conge', color: 'blue' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'orange' },
  { value: 'TERMINATED', label: 'Termine', color: 'red' }
] as const;

// ============================================================================
// TYPES DE CONGES
// ============================================================================

export const LEAVE_TYPES = [
  { value: 'PAID', label: 'Conges payes' },
  { value: 'UNPAID', label: 'Sans solde' },
  { value: 'SICK', label: 'Maladie' },
  { value: 'MATERNITY', label: 'Maternite' },
  { value: 'PATERNITY', label: 'Paternite' },
  { value: 'OTHER', label: 'Autre' }
] as const;

// ============================================================================
// STATUTS DE CONGES
// ============================================================================

export const LEAVE_STATUSES = [
  { value: 'PENDING', label: 'En attente', color: 'orange' },
  { value: 'APPROVED', label: 'Approuve', color: 'green' },
  { value: 'REJECTED', label: 'Rejete', color: 'red' },
  { value: 'CANCELLED', label: 'Annule', color: 'gray' }
] as const;

// ============================================================================
// STATUTS FEUILLES DE TEMPS
// ============================================================================

export const TIMESHEET_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'SUBMITTED', label: 'Soumis', color: 'blue' },
  { value: 'APPROVED', label: 'Approuve', color: 'green' },
  { value: 'REJECTED', label: 'Rejete', color: 'red' }
] as const;

// ============================================================================
// CATEGORIES DE POSTES
// ============================================================================

export const POSITION_CATEGORIES = [
  { value: 'CADRE', label: 'Cadre' },
  { value: 'NON_CADRE', label: 'Non-cadre' },
  { value: 'AGENT_MAITRISE', label: 'Agent de maitrise' },
  { value: 'TECHNICIEN', label: 'Technicien' },
  { value: 'OUVRIER', label: 'Ouvrier' },
  { value: 'EMPLOYE', label: 'Employe' }
] as const;

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Obtenir les informations d'un statut
 */
export const getStatusInfo = (
  statuses: readonly { value: string; label: string; color: string }[],
  status: string
): { label: string; color: string } => {
  const found = statuses.find(s => s.value === status);
  return found || { label: status, color: 'gray' };
};
