/**
 * AZALSCORE Module - INTERVENTIONS Constants
 * Constantes UI pour les listes déroulantes
 */

export const STATUTS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'A_PLANIFIER', label: 'À planifier' },
  { value: 'PLANIFIEE', label: 'Planifiée' },
  { value: 'EN_COURS', label: 'En cours' },
  { value: 'BLOQUEE', label: 'Bloquée' },
  { value: 'TERMINEE', label: 'Terminée' },
  { value: 'ANNULEE', label: 'Annulée' }
];

export const PRIORITES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' },
  { value: 'URGENT', label: 'Urgente' }
];

export const TYPES_INTERVENTION = [
  { value: 'INSTALLATION', label: 'Installation' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'REPARATION', label: 'Réparation' },
  { value: 'INSPECTION', label: 'Inspection' },
  { value: 'FORMATION', label: 'Formation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'AUTRE', label: 'Autre' }
];
