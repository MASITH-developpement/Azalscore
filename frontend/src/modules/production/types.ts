/**
 * AZALSCORE Module - Production - Types
 * Types et helpers pour le module production/fabrication
 */

// ============================================================================
// TYPES DE BASE
// ============================================================================

export type WorkCenterType = 'MACHINE' | 'WORKSTATION' | 'LINE' | 'AREA';
export type BOMStatus = 'DRAFT' | 'ACTIVE' | 'OBSOLETE';
export type OrderStatus = 'DRAFT' | 'CONFIRMED' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
export type OrderPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type WorkOrderStatus = 'PENDING' | 'READY' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';

// ============================================================================
// INTERFACES
// ============================================================================

/**
 * Poste de travail / Centre de charge
 */
export interface WorkCenter {
  id: string;
  code: string;
  name: string;
  type: WorkCenterType;
  description?: string;
  capacity: number;
  capacity_unit?: string;
  efficiency: number;
  cost_per_hour: number;
  setup_time_default?: number;
  is_active: boolean;
  location?: string;
  responsible_id?: string;
  responsible_name?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Ligne de nomenclature (composant)
 */
export interface BOMLine {
  id: string;
  bom_id: string;
  component_id: string;
  component_code?: string;
  component_name?: string;
  quantity: number;
  unit: string;
  scrap_rate: number;
  is_critical?: boolean;
  notes?: string;
}

/**
 * Operation de nomenclature
 */
export interface BOMOperation {
  id: string;
  bom_id: string;
  sequence: number;
  work_center_id: string;
  work_center_code?: string;
  work_center_name?: string;
  name: string;
  description?: string;
  duration: number;
  setup_time: number;
  cost_per_unit?: number;
}

/**
 * Nomenclature (Bill of Materials)
 */
export interface BillOfMaterials {
  id: string;
  code: string;
  name?: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  version: string;
  status: BOMStatus;
  quantity_base?: number;
  unit_base?: string;
  lines: BOMLine[];
  operations: BOMOperation[];
  total_cost?: number;
  total_duration?: number;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

/**
 * Ordre de travail (Work Order)
 */
export interface WorkOrder {
  id: string;
  production_order_id: string;
  operation_id: string;
  work_center_id: string;
  work_center_code?: string;
  work_center_name?: string;
  sequence: number;
  name: string;
  description?: string;
  status: WorkOrderStatus;
  duration_planned: number;
  duration_actual: number;
  quantity_planned?: number;
  quantity_produced?: number;
  start_time?: string;
  end_time?: string;
  operator_id?: string;
  operator_name?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Consommation de materiau
 */
export interface MaterialConsumption {
  id: string;
  production_order_id: string;
  work_order_id?: string;
  component_id: string;
  component_code?: string;
  component_name?: string;
  quantity_planned: number;
  quantity_consumed: number;
  unit: string;
  lot_id?: string;
  lot_number?: string;
  consumed_at?: string;
  consumed_by?: string;
}

/**
 * Production realisee (Output)
 */
export interface ProductionOutput {
  id: string;
  production_order_id: string;
  work_order_id?: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  quantity: number;
  unit: string;
  lot_id?: string;
  lot_number?: string;
  quality_status?: 'OK' | 'NOK' | 'PENDING';
  produced_at: string;
  produced_by?: string;
}

/**
 * Historique d'un ordre de production
 */
export interface OrderHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_id?: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

/**
 * Document lie a un ordre
 */
export interface OrderDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'excel' | 'other';
  category?: string;
  size?: number;
  url?: string;
  created_at: string;
  created_by?: string;
}

/**
 * Ordre de fabrication (Production Order)
 */
export interface ProductionOrder {
  id: string;
  number: string;
  name?: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  bom_id: string;
  bom_code?: string;
  bom_version?: string;
  quantity_planned: number;
  quantity_produced: number;
  quantity_scrapped?: number;
  unit?: string;
  start_date: string;
  end_date?: string;
  due_date?: string;
  actual_start?: string;
  actual_end?: string;
  status: OrderStatus;
  priority: OrderPriority;
  progress?: number;
  cost_planned?: number;
  cost_actual?: number;
  duration_planned?: number;
  duration_actual?: number;
  work_orders: WorkOrder[];
  material_consumptions?: MaterialConsumption[];
  outputs?: ProductionOutput[];
  history?: OrderHistoryEntry[];
  documents?: OrderDocument[];
  notes?: string;
  customer_order_id?: string;
  customer_order_number?: string;
  warehouse_id?: string;
  warehouse_name?: string;
  responsible_id?: string;
  responsible_name?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

/**
 * Dashboard production
 */
export interface ProductionDashboard {
  orders_in_progress: number;
  orders_planned: number;
  orders_completed_today: number;
  efficiency_rate: number;
  work_centers_active: number;
  work_centers_total: number;
  pending_work_orders: number;
  scrap_rate?: number;
  on_time_delivery_rate?: number;
}

// ============================================================================
// CONFIGURATIONS
// ============================================================================

export const WORK_CENTER_TYPE_CONFIG: Record<WorkCenterType, { label: string; color: string; description: string }> = {
  MACHINE: { label: 'Machine', color: 'blue', description: 'Equipement automatise' },
  WORKSTATION: { label: 'Poste de travail', color: 'green', description: 'Poste manuel' },
  LINE: { label: 'Ligne', color: 'purple', description: 'Ligne de production' },
  AREA: { label: 'Zone', color: 'gray', description: 'Zone de travail' }
};

export const BOM_STATUS_CONFIG: Record<BOMStatus, { label: string; color: string; description: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'En preparation' },
  ACTIVE: { label: 'Actif', color: 'green', description: 'Utilisable en production' },
  OBSOLETE: { label: 'Obsolete', color: 'red', description: 'Ne plus utiliser' }
};

export const ORDER_STATUS_CONFIG: Record<OrderStatus, { label: string; color: string; description: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'En preparation' },
  CONFIRMED: { label: 'Confirme', color: 'blue', description: 'Pret a demarrer' },
  IN_PROGRESS: { label: 'En cours', color: 'orange', description: 'Production en cours' },
  DONE: { label: 'Termine', color: 'green', description: 'Production terminee' },
  CANCELLED: { label: 'Annule', color: 'red', description: 'Ordre annule' }
};

export const ORDER_PRIORITY_CONFIG: Record<OrderPriority, { label: string; color: string; description: string }> = {
  LOW: { label: 'Basse', color: 'gray', description: 'Non urgent' },
  NORMAL: { label: 'Normale', color: 'blue', description: 'Standard' },
  HIGH: { label: 'Haute', color: 'orange', description: 'Prioritaire' },
  URGENT: { label: 'Urgente', color: 'red', description: 'Tres urgent' }
};

export const WORK_ORDER_STATUS_CONFIG: Record<WorkOrderStatus, { label: string; color: string; description: string }> = {
  PENDING: { label: 'En attente', color: 'gray', description: 'Non demarre' },
  READY: { label: 'Pret', color: 'blue', description: 'Peut demarrer' },
  IN_PROGRESS: { label: 'En cours', color: 'orange', description: 'En execution' },
  DONE: { label: 'Termine', color: 'green', description: 'Termine' },
  CANCELLED: { label: 'Annule', color: 'red', description: 'Annule' }
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Formater une date
 */
export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

/**
 * Formater une date avec heure
 */
export const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

/**
 * Formater un montant en euros
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

/**
 * Formater une duree en minutes
 */
export const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
};

/**
 * Formater un pourcentage
 */
export const formatPercent = (value: number, decimals: number = 0): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Formater une quantite
 */
export const formatQuantity = (qty: number, unit?: string): string => {
  const formatted = new Intl.NumberFormat('fr-FR').format(qty);
  return unit ? `${formatted} ${unit}` : formatted;
};

/**
 * Verifier si l'ordre est en brouillon
 */
export const isDraft = (order: ProductionOrder): boolean => {
  return order.status === 'DRAFT';
};

/**
 * Verifier si l'ordre est confirme
 */
export const isConfirmed = (order: ProductionOrder): boolean => {
  return order.status === 'CONFIRMED';
};

/**
 * Verifier si l'ordre est en cours
 */
export const isInProgress = (order: ProductionOrder): boolean => {
  return order.status === 'IN_PROGRESS';
};

/**
 * Verifier si l'ordre est termine
 */
export const isDone = (order: ProductionOrder): boolean => {
  return order.status === 'DONE';
};

/**
 * Verifier si l'ordre est annule
 */
export const isCancelled = (order: ProductionOrder): boolean => {
  return order.status === 'CANCELLED';
};

/**
 * Verifier si l'ordre peut etre confirme
 */
export const canConfirm = (order: ProductionOrder): boolean => {
  return order.status === 'DRAFT';
};

/**
 * Verifier si l'ordre peut demarrer
 */
export const canStart = (order: ProductionOrder): boolean => {
  return order.status === 'CONFIRMED';
};

/**
 * Verifier si l'ordre peut etre termine
 */
export const canComplete = (order: ProductionOrder): boolean => {
  return order.status === 'IN_PROGRESS';
};

/**
 * Verifier si l'ordre est en retard
 */
export const isLate = (order: ProductionOrder): boolean => {
  if (!order.due_date) return false;
  if (order.status === 'DONE' || order.status === 'CANCELLED') return false;
  return new Date(order.due_date) < new Date();
};

/**
 * Verifier si l'ordre est urgent
 */
export const isUrgent = (order: ProductionOrder): boolean => {
  return order.priority === 'URGENT' || order.priority === 'HIGH';
};

/**
 * Calculer le taux de completion
 */
export const getCompletionRate = (order: ProductionOrder): number => {
  if (order.quantity_planned === 0) return 0;
  return order.quantity_produced / order.quantity_planned;
};

/**
 * Calculer le taux de rebut
 */
export const getScrapRate = (order: ProductionOrder): number => {
  const total = order.quantity_produced + (order.quantity_scrapped || 0);
  if (total === 0) return 0;
  return (order.quantity_scrapped || 0) / total;
};

/**
 * Calculer l'ecart de cout
 */
export const getCostVariance = (order: ProductionOrder): number | null => {
  if (order.cost_planned === undefined || order.cost_actual === undefined) return null;
  return order.cost_actual - order.cost_planned;
};

/**
 * Calculer l'ecart de duree
 */
export const getDurationVariance = (order: ProductionOrder): number | null => {
  if (order.duration_planned === undefined || order.duration_actual === undefined) return null;
  return order.duration_actual - order.duration_planned;
};

/**
 * Obtenir la couleur selon le statut
 */
export const getStatusColor = (status: OrderStatus): string => {
  return ORDER_STATUS_CONFIG[status]?.color || 'gray';
};

/**
 * Obtenir la couleur selon la priorite
 */
export const getPriorityColor = (priority: OrderPriority): string => {
  return ORDER_PRIORITY_CONFIG[priority]?.color || 'gray';
};

/**
 * Obtenir le niveau de progression
 */
export const getProgressLevel = (order: ProductionOrder): 'low' | 'medium' | 'high' | 'complete' => {
  const rate = getCompletionRate(order);
  if (rate >= 1) return 'complete';
  if (rate >= 0.75) return 'high';
  if (rate >= 0.25) return 'medium';
  return 'low';
};
