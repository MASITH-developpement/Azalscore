/**
 * AZALSCORE Module - Qualite Types
 * Types et utilitaires pour la gestion de la qualite
 */

// ============================================================
// TYPES DE BASE
// ============================================================

export type NCType = 'INTERNAL' | 'SUPPLIER' | 'CUSTOMER';
export type NCOrigin = 'PRODUCTION' | 'RECEPTION' | 'FIELD' | 'AUDIT';
export type NCSeverity = 'MINOR' | 'MAJOR' | 'CRITICAL';
export type NCStatus = 'OPEN' | 'IN_ANALYSIS' | 'ACTION_PLANNED' | 'CLOSED' | 'CANCELLED';
export type QCType = 'INCOMING' | 'IN_PROCESS' | 'FINAL';
export type InspectionStatus = 'PENDING' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'PARTIAL';
export type ParameterType = 'NUMERIC' | 'BOOLEAN' | 'TEXT' | 'SELECT';

export interface NonConformance {
  id: string;
  number: string;
  type: NCType;
  origin: NCOrigin;
  product_id?: string;
  product_name?: string;
  lot_number?: string;
  description: string;
  severity: NCSeverity;
  status: NCStatus;
  root_cause?: string;
  corrective_action?: string;
  preventive_action?: string;
  responsible_id?: string;
  responsible_name?: string;
  detected_by_id?: string;
  detected_by_name?: string;
  detected_date: string;
  target_date?: string;
  closed_date?: string;
  cost_estimate?: number;
  documents?: NCDocument[];
  history?: NCHistoryEntry[];
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface NCDocument {
  id: string;
  nc_id: string;
  name: string;
  file_url?: string;
  file_size?: number;
  mime_type?: string;
  doc_type?: 'photo' | 'rapport' | 'autre';
  created_at: string;
}

export interface NCHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface QCRule {
  id: string;
  code: string;
  name: string;
  type: QCType;
  product_id?: string;
  product_name?: string;
  category_id?: string;
  category_name?: string;
  parameters: QCParameter[];
  is_active: boolean;
  created_at: string;
}

export interface QCParameter {
  id: string;
  name: string;
  type: ParameterType;
  unit?: string;
  min_value?: number;
  max_value?: number;
  target_value?: number;
  options?: string[];
  is_critical: boolean;
}

export interface QCInspection {
  id: string;
  number: string;
  rule_id: string;
  rule_name?: string;
  type: QCType;
  reference_type: 'RECEIPT' | 'PRODUCTION_ORDER' | 'PICKING';
  reference_id: string;
  reference_number?: string;
  product_id: string;
  product_name?: string;
  lot_number?: string;
  quantity_inspected: number;
  quantity_accepted: number;
  quantity_rejected: number;
  status: InspectionStatus;
  results: QCResult[];
  inspector_id?: string;
  inspector_name?: string;
  inspection_date: string;
  comments?: string;
  documents?: NCDocument[];
  created_at: string;
}

export interface QCResult {
  id: string;
  parameter_id: string;
  parameter_name?: string;
  value: string | number | boolean;
  is_conformant: boolean;
  comment?: string;
}

export interface QualityDashboard {
  open_non_conformances: number;
  pending_inspections: number;
  inspections_today: number;
  pass_rate: number;
  critical_nc_count: number;
  nc_by_type: { type: string; count: number }[];
  nc_by_origin: { origin: string; count: number }[];
}

// ============================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================

export const NC_TYPE_CONFIG: Record<NCType, { label: string; color: string; description: string }> = {
  INTERNAL: { label: 'Interne', color: 'blue', description: 'Non-conformite detectee en interne' },
  SUPPLIER: { label: 'Fournisseur', color: 'orange', description: 'Non-conformite liee a un fournisseur' },
  CUSTOMER: { label: 'Client', color: 'purple', description: 'Reclamation client' },
};

export const NC_ORIGIN_CONFIG: Record<NCOrigin, { label: string; color: string; description: string }> = {
  PRODUCTION: { label: 'Production', color: 'blue', description: 'Detectee en production' },
  RECEPTION: { label: 'Reception', color: 'green', description: 'Detectee a la reception' },
  FIELD: { label: 'Terrain', color: 'orange', description: 'Detectee sur le terrain' },
  AUDIT: { label: 'Audit', color: 'purple', description: 'Detectee lors d\'un audit' },
};

export const SEVERITY_CONFIG: Record<NCSeverity, { label: string; color: string; description: string }> = {
  MINOR: { label: 'Mineure', color: 'yellow', description: 'Impact faible, correction non urgente' },
  MAJOR: { label: 'Majeure', color: 'orange', description: 'Impact significatif, correction necessaire' },
  CRITICAL: { label: 'Critique', color: 'red', description: 'Impact grave, action immediate requise' },
};

export const NC_STATUS_CONFIG: Record<NCStatus, { label: string; color: string; description: string }> = {
  OPEN: { label: 'Ouverte', color: 'red', description: 'NC en attente de traitement' },
  IN_ANALYSIS: { label: 'En analyse', color: 'orange', description: 'Analyse en cours' },
  ACTION_PLANNED: { label: 'Action planifiee', color: 'blue', description: 'Action corrective definie' },
  CLOSED: { label: 'Cloturee', color: 'green', description: 'NC resolue et cloturee' },
  CANCELLED: { label: 'Annulee', color: 'gray', description: 'NC annulee' },
};

export const QC_TYPE_CONFIG: Record<QCType, { label: string; color: string; description: string }> = {
  INCOMING: { label: 'Reception', color: 'blue', description: 'Controle a la reception' },
  IN_PROCESS: { label: 'En cours', color: 'orange', description: 'Controle en production' },
  FINAL: { label: 'Final', color: 'green', description: 'Controle final avant expedition' },
};

export const INSPECTION_STATUS_CONFIG: Record<InspectionStatus, { label: string; color: string; description: string }> = {
  PENDING: { label: 'En attente', color: 'gray', description: 'Inspection programmee' },
  IN_PROGRESS: { label: 'En cours', color: 'blue', description: 'Inspection en cours' },
  PASSED: { label: 'Conforme', color: 'green', description: 'Tous les controles OK' },
  FAILED: { label: 'Non conforme', color: 'red', description: 'Controles non conformes' },
  PARTIAL: { label: 'Partiel', color: 'orange', description: 'Conformite partielle' },
};

export const NC_TYPES = [
  { value: 'INTERNAL', label: 'Interne' },
  { value: 'SUPPLIER', label: 'Fournisseur' },
  { value: 'CUSTOMER', label: 'Client' },
];

export const NC_ORIGINS = [
  { value: 'PRODUCTION', label: 'Production' },
  { value: 'RECEPTION', label: 'Reception' },
  { value: 'FIELD', label: 'Terrain' },
  { value: 'AUDIT', label: 'Audit' },
];

export const SEVERITIES = [
  { value: 'MINOR', label: 'Mineure', color: 'yellow' },
  { value: 'MAJOR', label: 'Majeure', color: 'orange' },
  { value: 'CRITICAL', label: 'Critique', color: 'red' },
];

export const NC_STATUSES = [
  { value: 'OPEN', label: 'Ouverte', color: 'red' },
  { value: 'IN_ANALYSIS', label: 'En analyse', color: 'orange' },
  { value: 'ACTION_PLANNED', label: 'Action planifiee', color: 'blue' },
  { value: 'CLOSED', label: 'Cloturee', color: 'green' },
  { value: 'CANCELLED', label: 'Annulee', color: 'gray' },
];

export const QC_TYPES = [
  { value: 'INCOMING', label: 'Reception' },
  { value: 'IN_PROCESS', label: 'En cours' },
  { value: 'FINAL', label: 'Final' },
];

export const INSPECTION_STATUSES = [
  { value: 'PENDING', label: 'En attente', color: 'gray' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'blue' },
  { value: 'PASSED', label: 'Conforme', color: 'green' },
  { value: 'FAILED', label: 'Non conforme', color: 'red' },
  { value: 'PARTIAL', label: 'Partiel', color: 'orange' },
];

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Obtenir la configuration du type de NC
 */
export const getNCTypeConfig = (type: NCType) => {
  return NC_TYPE_CONFIG[type] || NC_TYPE_CONFIG.INTERNAL;
};

/**
 * Obtenir la configuration de l'origine de NC
 */
export const getNCOriginConfig = (origin: NCOrigin) => {
  return NC_ORIGIN_CONFIG[origin] || NC_ORIGIN_CONFIG.PRODUCTION;
};

/**
 * Obtenir la configuration de la severite
 */
export const getSeverityConfig = (severity: NCSeverity) => {
  return SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.MINOR;
};

/**
 * Obtenir la configuration du statut NC
 */
export const getNCStatusConfig = (status: NCStatus) => {
  return NC_STATUS_CONFIG[status] || NC_STATUS_CONFIG.OPEN;
};

/**
 * Obtenir la configuration du type QC
 */
export const getQCTypeConfig = (type: QCType) => {
  return QC_TYPE_CONFIG[type] || QC_TYPE_CONFIG.INCOMING;
};

/**
 * Obtenir la configuration du statut d'inspection
 */
export const getInspectionStatusConfig = (status: InspectionStatus) => {
  return INSPECTION_STATUS_CONFIG[status] || INSPECTION_STATUS_CONFIG.PENDING;
};

/**
 * Verifier si la NC peut etre modifiee
 */
export const canEditNC = (nc: NonConformance): boolean => {
  return ['OPEN', 'IN_ANALYSIS', 'ACTION_PLANNED'].includes(nc.status);
};

/**
 * Verifier si la NC peut etre cloturee
 */
export const canCloseNC = (nc: NonConformance): boolean => {
  return nc.status === 'ACTION_PLANNED' && !!nc.corrective_action;
};

/**
 * Calculer l'age de la NC en jours
 */
export const getNCAgeDays = (nc: NonConformance): number => {
  const detected = new Date(nc.detected_date);
  const now = new Date();
  return Math.floor((now.getTime() - detected.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Obtenir l'age formate
 */
export const getNCAge = (nc: NonConformance): string => {
  const days = getNCAgeDays(nc);
  if (days === 0) return 'Aujourd\'hui';
  if (days === 1) return '1 jour';
  if (days < 7) return `${days} jours`;
  if (days < 30) return `${Math.floor(days / 7)} semaine(s)`;
  return `${Math.floor(days / 30)} mois`;
};

/**
 * Verifier si la NC est en retard (objectif depasse)
 */
export const isNCOverdue = (nc: NonConformance): boolean => {
  if (!nc.target_date) return false;
  if (nc.status === 'CLOSED' || nc.status === 'CANCELLED') return false;
  return new Date(nc.target_date) < new Date();
};

/**
 * Calculer le taux de conformite d'une inspection
 */
export const getInspectionPassRate = (inspection: QCInspection): number => {
  if (inspection.quantity_inspected === 0) return 0;
  return (inspection.quantity_accepted / inspection.quantity_inspected) * 100;
};

/**
 * Obtenir le nombre de resultats conformes
 */
export const getConformantResultsCount = (inspection: QCInspection): number => {
  return (inspection.results || []).filter(r => r.is_conformant).length;
};

/**
 * Obtenir le nombre de resultats non conformes
 */
export const getNonConformantResultsCount = (inspection: QCInspection): number => {
  return (inspection.results || []).filter(r => !r.is_conformant).length;
};

/**
 * Obtenir le nombre de documents
 */
export const getDocumentCount = (nc: NonConformance): number => {
  return (nc.documents || []).length;
};
