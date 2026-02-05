/**
 * AZALSCORE Module - Maintenance Types
 * Types et helpers pour la gestion de maintenance
 */

// ============================================================================
// TYPES DE BASE
// ============================================================================

export type AssetType = 'EQUIPMENT' | 'VEHICLE' | 'TOOL' | 'BUILDING' | 'IT';
export type AssetStatus = 'OPERATIONAL' | 'UNDER_MAINTENANCE' | 'OUT_OF_SERVICE' | 'SCRAPPED';
export type Criticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type MaintenanceOrderType = 'PREVENTIVE' | 'CORRECTIVE' | 'PREDICTIVE' | 'CONDITION_BASED';
export type MaintenanceOrderStatus = 'DRAFT' | 'PLANNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
export type Priority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type Frequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'HOURS_BASED' | 'CYCLES_BASED';

// ============================================================================
// INTERFACES PRINCIPALES
// ============================================================================

export interface Asset {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: AssetType;
  category_id?: string;
  category_name?: string;
  location?: string;
  department_id?: string;
  department_name?: string;
  serial_number?: string;
  manufacturer?: string;
  model?: string;
  purchase_date?: string;
  purchase_cost?: number;
  warranty_end_date?: string;
  status: AssetStatus;
  criticality: Criticality;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  total_maintenance_cost?: number;
  maintenance_orders?: MaintenanceOrder[];
  maintenance_plans?: MaintenancePlan[];
  documents?: AssetDocument[];
  spare_parts?: SparePart[];
  meters?: AssetMeter[];
  history?: AssetHistoryEntry[];
  notes?: string;
  created_at: string;
  created_by?: string;
  updated_at?: string;
}

export interface MaintenanceOrder {
  id: string;
  number: string;
  asset_id: string;
  asset_name?: string;
  asset_code?: string;
  type: MaintenanceOrderType;
  priority: Priority;
  status: MaintenanceOrderStatus;
  description: string;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  team_members?: string[];
  parts_used: PartUsage[];
  labor_hours: number;
  labor_cost?: number;
  parts_cost?: number;
  total_cost: number;
  failure_cause?: string;
  failure_code?: string;
  resolution?: string;
  checklist?: ChecklistItem[];
  created_at: string;
  created_by?: string;
}

export interface PartUsage {
  id: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  quantity: number;
  unit_cost: number;
  total_cost?: number;
}

export interface MaintenancePlan {
  id: string;
  code: string;
  name: string;
  description?: string;
  asset_id?: string;
  asset_name?: string;
  asset_type?: string;
  frequency: Frequency;
  frequency_value: number;
  tasks: MaintenanceTask[];
  estimated_duration_hours?: number;
  estimated_cost?: number;
  last_execution_date?: string;
  next_execution_date?: string;
  is_active: boolean;
  created_at?: string;
}

export interface MaintenanceTask {
  id: string;
  sequence: number;
  description: string;
  duration_minutes: number;
  instructions?: string;
  parts_required: { product_id: string; product_name?: string; quantity: number }[];
  tools_required?: string[];
  safety_notes?: string;
}

export interface ChecklistItem {
  id: string;
  description: string;
  is_completed: boolean;
  completed_at?: string;
  completed_by?: string;
  notes?: string;
}

export interface AssetDocument {
  id: string;
  asset_id: string;
  name: string;
  type: 'manual' | 'certificate' | 'warranty' | 'inspection' | 'photo' | 'other';
  file_url?: string;
  file_size?: number;
  expiry_date?: string;
  uploaded_by?: string;
  created_at: string;
}

export interface SparePart {
  id: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  quantity_on_hand: number;
  minimum_quantity: number;
  reorder_point?: number;
  average_consumption?: number;
}

export interface AssetMeter {
  id: string;
  name: string;
  type: 'HOURS' | 'CYCLES' | 'KILOMETERS' | 'OTHER';
  current_value: number;
  unit: string;
  last_reading_date?: string;
}

export interface AssetHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_id?: string;
  user_name?: string;
  field?: string;
  old_value?: string;
  new_value?: string;
  details?: string;
}

export interface MaintenanceDashboard {
  assets_operational: number;
  assets_under_maintenance: number;
  assets_out_of_service: number;
  orders_in_progress: number;
  orders_overdue: number;
  upcoming_preventive: number;
  mtbf: number;
  mttr: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const ASSET_TYPE_CONFIG: Record<AssetType, { label: string; color: string; icon?: string }> = {
  EQUIPMENT: { label: 'Equipement', color: 'blue' },
  VEHICLE: { label: 'Vehicule', color: 'green' },
  TOOL: { label: 'Outil', color: 'purple' },
  BUILDING: { label: 'Batiment', color: 'orange' },
  IT: { label: 'IT', color: 'cyan' }
};

export const ASSET_STATUS_CONFIG: Record<AssetStatus, { label: string; color: string; description: string }> = {
  OPERATIONAL: { label: 'Operationnel', color: 'green', description: 'En fonctionnement normal' },
  UNDER_MAINTENANCE: { label: 'En maintenance', color: 'orange', description: 'En cours de maintenance' },
  OUT_OF_SERVICE: { label: 'Hors service', color: 'red', description: 'Non fonctionnel' },
  SCRAPPED: { label: 'Mis au rebut', color: 'gray', description: 'Retire du service' }
};

export const CRITICALITY_CONFIG: Record<Criticality, { label: string; color: string; description: string }> = {
  LOW: { label: 'Faible', color: 'gray', description: 'Impact minimal' },
  MEDIUM: { label: 'Moyenne', color: 'blue', description: 'Impact modere' },
  HIGH: { label: 'Haute', color: 'orange', description: 'Impact important' },
  CRITICAL: { label: 'Critique', color: 'red', description: 'Impact majeur sur la production' }
};

export const ORDER_TYPE_CONFIG: Record<MaintenanceOrderType, { label: string; color: string; description: string }> = {
  PREVENTIVE: { label: 'Preventive', color: 'blue', description: 'Maintenance planifiee' },
  CORRECTIVE: { label: 'Corrective', color: 'orange', description: 'Reparation apres panne' },
  PREDICTIVE: { label: 'Predictive', color: 'purple', description: 'Basee sur les donnees' },
  CONDITION_BASED: { label: 'Conditionnelle', color: 'cyan', description: 'Selon etat mesure' }
};

export const ORDER_STATUS_CONFIG: Record<MaintenanceOrderStatus, { label: string; color: string; description: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'En preparation' },
  PLANNED: { label: 'Planifie', color: 'blue', description: 'Programme' },
  IN_PROGRESS: { label: 'En cours', color: 'orange', description: 'Travaux en cours' },
  ON_HOLD: { label: 'En attente', color: 'yellow', description: 'Suspendu temporairement' },
  COMPLETED: { label: 'Termine', color: 'green', description: 'Travaux termines' },
  CANCELLED: { label: 'Annule', color: 'red', description: 'Ordre annule' }
};

export const PRIORITY_CONFIG: Record<Priority, { label: string; color: string }> = {
  LOW: { label: 'Basse', color: 'gray' },
  NORMAL: { label: 'Normale', color: 'blue' },
  HIGH: { label: 'Haute', color: 'orange' },
  URGENT: { label: 'Urgente', color: 'red' }
};

export const FREQUENCY_CONFIG: Record<Frequency, { label: string; unit?: string }> = {
  DAILY: { label: 'Quotidienne', unit: 'jours' },
  WEEKLY: { label: 'Hebdomadaire', unit: 'semaines' },
  MONTHLY: { label: 'Mensuelle', unit: 'mois' },
  QUARTERLY: { label: 'Trimestrielle', unit: 'trimestres' },
  YEARLY: { label: 'Annuelle', unit: 'ans' },
  HOURS_BASED: { label: 'Par heures', unit: 'heures' },
  CYCLES_BASED: { label: 'Par cycles', unit: 'cycles' }
};

export const DOCUMENT_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  manual: { label: 'Manuel', color: 'blue' },
  certificate: { label: 'Certificat', color: 'green' },
  warranty: { label: 'Garantie', color: 'purple' },
  inspection: { label: 'Inspection', color: 'orange' },
  photo: { label: 'Photo', color: 'cyan' },
  other: { label: 'Autre', color: 'gray' }
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Calcule l'age de l'equipement en annees
 */
export const getAssetAge = (asset: Asset): number | null => {
  if (!asset.purchase_date) return null;
  const purchase = new Date(asset.purchase_date);
  const now = new Date();
  return Math.floor((now.getTime() - purchase.getTime()) / (1000 * 60 * 60 * 24 * 365));
};

/**
 * Verifie si la garantie est expiree
 */
export const isWarrantyExpired = (asset: Asset): boolean => {
  if (!asset.warranty_end_date) return true;
  return new Date(asset.warranty_end_date) < new Date();
};

/**
 * Verifie si la garantie expire bientot
 */
export const isWarrantyExpiringSoon = (asset: Asset, days = 30): boolean => {
  if (!asset.warranty_end_date) return false;
  const warranty = new Date(asset.warranty_end_date);
  const now = new Date();
  const daysUntil = (warranty.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return daysUntil > 0 && daysUntil <= days;
};

/**
 * Calcule les jours jusqu'a la prochaine maintenance
 */
export const getDaysUntilMaintenance = (asset: Asset): number | null => {
  if (!asset.next_maintenance_date) return null;
  const next = new Date(asset.next_maintenance_date);
  const now = new Date();
  return Math.ceil((next.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Verifie si la maintenance est en retard
 */
export const isMaintenanceOverdue = (asset: Asset): boolean => {
  const days = getDaysUntilMaintenance(asset);
  return days !== null && days < 0;
};

/**
 * Verifie si la maintenance est proche
 */
export const isMaintenanceDueSoon = (asset: Asset, days = 7): boolean => {
  const daysUntil = getDaysUntilMaintenance(asset);
  return daysUntil !== null && daysUntil >= 0 && daysUntil <= days;
};

/**
 * Verifie si l'equipement est operationnel
 */
export const isAssetOperational = (asset: Asset): boolean => {
  return asset.status === 'OPERATIONAL';
};

/**
 * Verifie si l'equipement est en maintenance
 */
export const isAssetUnderMaintenance = (asset: Asset): boolean => {
  return asset.status === 'UNDER_MAINTENANCE';
};

/**
 * Compte les ordres de maintenance par statut
 */
export const getOrderCountByStatus = (asset: Asset): Record<MaintenanceOrderStatus, number> => {
  const counts: Record<MaintenanceOrderStatus, number> = {
    DRAFT: 0,
    PLANNED: 0,
    IN_PROGRESS: 0,
    ON_HOLD: 0,
    COMPLETED: 0,
    CANCELLED: 0
  };
  asset.maintenance_orders?.forEach(order => {
    counts[order.status]++;
  });
  return counts;
};

/**
 * Calcule le cout total de maintenance
 */
export const getTotalMaintenanceCost = (asset: Asset): number => {
  return asset.maintenance_orders?.reduce((sum, order) => sum + (order.total_cost || 0), 0) || 0;
};

/**
 * Calcule les heures de main d'oeuvre totales
 */
export const getTotalLaborHours = (asset: Asset): number => {
  return asset.maintenance_orders?.reduce((sum, order) => sum + (order.labor_hours || 0), 0) || 0;
};

/**
 * Obtient les pieces de rechange en rupture
 */
export const getLowStockParts = (asset: Asset): SparePart[] => {
  return asset.spare_parts?.filter(part => part.quantity_on_hand <= part.minimum_quantity) || [];
};

/**
 * Obtient les documents expires ou expirant
 */
export const getExpiringDocuments = (asset: Asset, days = 30): AssetDocument[] => {
  const now = new Date();
  return asset.documents?.filter(doc => {
    if (!doc.expiry_date) return false;
    const expiry = new Date(doc.expiry_date);
    const daysUntil = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntil <= days;
  }) || [];
};

/**
 * Formate la frequence de maintenance
 */
export const formatFrequency = (plan: MaintenancePlan): string => {
  const config = FREQUENCY_CONFIG[plan.frequency];
  return `${config.label} (${plan.frequency_value} ${config.unit || ''})`;
};

/**
 * Calcule le temps moyen entre pannes (MTBF)
 */
export const calculateMTBF = (asset: Asset): number | null => {
  const correctiveOrders = asset.maintenance_orders?.filter(o => o.type === 'CORRECTIVE' && o.status === 'COMPLETED') || [];
  if (correctiveOrders.length < 2) return null;

  const age = getAssetAge(asset);
  if (!age) return null;

  return Math.round((age * 8760) / correctiveOrders.length); // heures par an
};

/**
 * Calcule le temps moyen de reparation (MTTR)
 */
export const calculateMTTR = (asset: Asset): number | null => {
  const completedOrders = asset.maintenance_orders?.filter(o => o.status === 'COMPLETED' && o.labor_hours > 0) || [];
  if (completedOrders.length === 0) return null;

  const totalHours = completedOrders.reduce((sum, o) => sum + o.labor_hours, 0);
  return Math.round(totalHours / completedOrders.length * 10) / 10;
};

export default {
  ASSET_TYPE_CONFIG,
  ASSET_STATUS_CONFIG,
  CRITICALITY_CONFIG,
  ORDER_TYPE_CONFIG,
  ORDER_STATUS_CONFIG,
  PRIORITY_CONFIG,
};
