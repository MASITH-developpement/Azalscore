/**
 * AZALSCORE Module - STOCK - Types et Helpers
 * Types partagés pour la gestion des stocks
 */

// ============================================================================
// TYPES - Entités principales
// ============================================================================

export interface Category {
  id: string;
  code: string;
  name: string;
  parent_id?: string;
  is_active: boolean;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  address?: string;
  city?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Location {
  id: string;
  code: string;
  name: string;
  warehouse_id: string;
  warehouse_name?: string;
  type: LocationType;
  aisle?: string;
  rack?: string;
  shelf?: string;
  bin?: string;
  is_active: boolean;
  created_at: string;
}

export type LocationType = 'STORAGE' | 'RECEPTION' | 'SHIPPING' | 'PRODUCTION';

export interface Product {
  id: string;
  code: string;
  name: string;
  description?: string;
  category_id?: string;
  category_name?: string;
  unit: string;
  cost_price: number;
  sale_price: number;
  min_stock: number;
  max_stock: number;
  current_stock: number;
  reserved_stock?: number;
  available_stock?: number;
  weight?: number;
  volume?: number;
  barcode?: string;
  supplier_id?: string;
  supplier_name?: string;
  lead_time_days?: number;
  is_serialized?: boolean;
  is_lot_tracked?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  // Relations
  lots?: Lot[];
  serials?: Serial[];
  movements?: Movement[];
  stock_by_location?: StockByLocation[];
  history?: ProductHistoryEntry[];
  documents?: ProductDocument[];
}

export interface StockByLocation {
  id: string;
  location_id: string;
  location_name: string;
  warehouse_id: string;
  warehouse_name: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface Lot {
  id: string;
  number: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  reserved_quantity?: number;
  expiry_date?: string;
  manufacturing_date?: string;
  warehouse_id: string;
  warehouse_name?: string;
  location_id?: string;
  location_name?: string;
  status: LotStatus;
  notes?: string;
  created_at: string;
}

export type LotStatus = 'AVAILABLE' | 'RESERVED' | 'QUARANTINE' | 'EXPIRED' | 'SCRAPPED';

export interface Serial {
  id: string;
  number: string;
  product_id: string;
  product_name?: string;
  lot_id?: string;
  lot_number?: string;
  status: SerialStatus;
  warehouse_id: string;
  warehouse_name?: string;
  location_id?: string;
  location_name?: string;
  warranty_end_date?: string;
  notes?: string;
  created_at: string;
}

export type SerialStatus = 'AVAILABLE' | 'RESERVED' | 'SOLD' | 'RETURNED' | 'SCRAPPED';

export interface Movement {
  id: string;
  number: string;
  type: MovementType;
  date: string;
  product_id: string;
  product_name?: string;
  product_code?: string;
  quantity: number;
  unit?: string;
  source_location_id?: string;
  source_location_name?: string;
  source_warehouse_name?: string;
  dest_location_id?: string;
  dest_location_name?: string;
  dest_warehouse_name?: string;
  lot_id?: string;
  lot_number?: string;
  serial_id?: string;
  serial_number?: string;
  reference?: string;
  reference_type?: string;
  notes?: string;
  cost_price?: number;
  total_cost?: number;
  status: MovementStatus;
  validated_at?: string;
  validated_by?: string;
  created_at: string;
  created_by?: string;
}

export type MovementType = 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
export type MovementStatus = 'DRAFT' | 'VALIDATED' | 'CANCELLED';

export interface InventoryCount {
  id: string;
  number: string;
  warehouse_id: string;
  warehouse_name?: string;
  date: string;
  status: InventoryCountStatus;
  lines: InventoryCountLine[];
  total_products?: number;
  total_differences?: number;
  total_value_difference?: number;
  notes?: string;
  created_at: string;
  created_by?: string;
  validated_at?: string;
  validated_by?: string;
}

export type InventoryCountStatus = 'DRAFT' | 'IN_PROGRESS' | 'VALIDATED' | 'CANCELLED';

export interface InventoryCountLine {
  id: string;
  product_id: string;
  product_name?: string;
  product_code?: string;
  location_id?: string;
  location_name?: string;
  lot_id?: string;
  lot_number?: string;
  theoretical_qty: number;
  counted_qty: number;
  difference: number;
  unit_cost?: number;
  value_difference?: number;
}

export interface Picking {
  id: string;
  number: string;
  type: PickingType;
  date: string;
  status: PickingStatus;
  source_location_id?: string;
  source_location_name?: string;
  dest_location_id?: string;
  dest_location_name?: string;
  reference?: string;
  reference_type?: string;
  priority?: PickingPriority;
  assigned_to?: string;
  assigned_to_name?: string;
  lines: PickingLine[];
  notes?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  created_by?: string;
}

export type PickingType = 'INCOMING' | 'OUTGOING' | 'INTERNAL';
export type PickingStatus = 'DRAFT' | 'READY' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
export type PickingPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface PickingLine {
  id: string;
  product_id: string;
  product_name?: string;
  product_code?: string;
  quantity_planned: number;
  quantity_done: number;
  lot_id?: string;
  lot_number?: string;
  serial_id?: string;
  serial_number?: string;
  source_location_id?: string;
  dest_location_id?: string;
}

// ============================================================================
// TYPES - Dashboard et Stats
// ============================================================================

export interface InventoryDashboard {
  total_products: number;
  active_products: number;
  low_stock_products: number;
  out_of_stock_products: number;
  total_value: number;
  total_warehouses: number;
  total_locations: number;
  pending_movements: number;
  pending_pickings: number;
  movements_today: number;
  movements_week: number;
  stock_alerts: StockAlert[];
}

export interface StockAlert {
  id?: string;
  product_id: string;
  product_name: string;
  product_code?: string;
  current_stock: number;
  min_stock: number;
  max_stock?: number;
  unit?: string;
  alert_type: 'LOW_STOCK' | 'OUT_OF_STOCK' | 'OVERSTOCK' | 'EXPIRING';
  severity: 'warning' | 'danger';
}

export interface ProductStats {
  total_movements: number;
  movements_in: number;
  movements_out: number;
  total_lots: number;
  total_serials: number;
  avg_cost: number;
  total_value: number;
  turnover_rate?: number;
  last_movement_date?: string;
}

// ============================================================================
// TYPES - Historique et Documents
// ============================================================================

export interface ProductHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
  field?: string;
}

export interface ProductDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url?: string;
  size?: number;
  created_at: string;
  created_by?: string;
}

// ============================================================================
// CONSTANTES - Configurations statuts
// ============================================================================

export const MOVEMENT_TYPE_CONFIG: Record<MovementType, { label: string; color: string }> = {
  IN: { label: 'Entrée', color: 'green' },
  OUT: { label: 'Sortie', color: 'red' },
  TRANSFER: { label: 'Transfert', color: 'blue' },
  ADJUSTMENT: { label: 'Ajustement', color: 'orange' }
};

export const MOVEMENT_STATUS_CONFIG: Record<MovementStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  VALIDATED: { label: 'Validé', color: 'green' },
  CANCELLED: { label: 'Annulé', color: 'red' }
};

export const PICKING_TYPE_CONFIG: Record<PickingType, { label: string; color: string }> = {
  INCOMING: { label: 'Réception', color: 'green' },
  OUTGOING: { label: 'Expédition', color: 'blue' },
  INTERNAL: { label: 'Interne', color: 'purple' }
};

export const PICKING_STATUS_CONFIG: Record<PickingStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  READY: { label: 'Prêt', color: 'blue' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' },
  DONE: { label: 'Terminé', color: 'green' },
  CANCELLED: { label: 'Annulé', color: 'red' }
};

export const LOT_STATUS_CONFIG: Record<LotStatus, { label: string; color: string }> = {
  AVAILABLE: { label: 'Disponible', color: 'green' },
  RESERVED: { label: 'Réservé', color: 'blue' },
  QUARANTINE: { label: 'Quarantaine', color: 'orange' },
  EXPIRED: { label: 'Expiré', color: 'red' },
  SCRAPPED: { label: 'Rebuté', color: 'gray' }
};

export const SERIAL_STATUS_CONFIG: Record<SerialStatus, { label: string; color: string }> = {
  AVAILABLE: { label: 'Disponible', color: 'green' },
  RESERVED: { label: 'Réservé', color: 'blue' },
  SOLD: { label: 'Vendu', color: 'purple' },
  RETURNED: { label: 'Retourné', color: 'orange' },
  SCRAPPED: { label: 'Rebuté', color: 'gray' }
};

export const LOCATION_TYPE_CONFIG: Record<LocationType, { label: string; color: string }> = {
  STORAGE: { label: 'Stockage', color: 'blue' },
  RECEPTION: { label: 'Réception', color: 'green' },
  SHIPPING: { label: 'Expédition', color: 'purple' },
  PRODUCTION: { label: 'Production', color: 'orange' }
};

export const INVENTORY_COUNT_STATUS_CONFIG: Record<InventoryCountStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' },
  VALIDATED: { label: 'Validé', color: 'green' },
  CANCELLED: { label: 'Annulé', color: 'red' }
};

// ============================================================================
// HELPERS - Formatage
// ============================================================================

export const formatQuantity = (qty: number, unit?: string): string => {
  const formatted = new Intl.NumberFormat('fr-FR').format(qty);
  return unit ? `${formatted} ${unit}` : formatted;
};

// ============================================================================
// HELPERS - Calculs et vérifications
// ============================================================================

export const isLowStock = (product: Product): boolean => {
  return product.current_stock <= product.min_stock;
};

export const isOutOfStock = (product: Product): boolean => {
  return product.current_stock <= 0;
};

export const isOverstock = (product: Product): boolean => {
  return product.max_stock > 0 && product.current_stock > product.max_stock;
};

export const getStockLevel = (product: Product): 'danger' | 'warning' | 'success' | 'info' => {
  if (isOutOfStock(product)) return 'danger';
  if (isLowStock(product)) return 'warning';
  if (isOverstock(product)) return 'info';
  return 'success';
};

export const getStockLevelLabel = (product: Product): string => {
  if (isOutOfStock(product)) return 'Rupture';
  if (isLowStock(product)) return 'Stock bas';
  if (isOverstock(product)) return 'Surstock';
  return 'Normal';
};

export const getAvailableStock = (product: Product): number => {
  return product.available_stock ?? (product.current_stock - (product.reserved_stock || 0));
};

export const getStockValue = (product: Product): number => {
  return product.current_stock * product.cost_price;
};

export const getMovementSign = (type: MovementType): number => {
  switch (type) {
    case 'IN': return 1;
    case 'OUT': return -1;
    case 'TRANSFER': return 0;
    case 'ADJUSTMENT': return 0;
  }
};

export const isLotExpired = (lot: Lot): boolean => {
  if (!lot.expiry_date) return false;
  return new Date(lot.expiry_date) < new Date();
};

export const isLotExpiringSoon = (lot: Lot, daysThreshold = 30): boolean => {
  if (!lot.expiry_date) return false;
  const expiryDate = new Date(lot.expiry_date);
  const thresholdDate = new Date();
  thresholdDate.setDate(thresholdDate.getDate() + daysThreshold);
  return expiryDate <= thresholdDate && expiryDate > new Date();
};

export const getDaysUntilExpiry = (lot: Lot): number | null => {
  if (!lot.expiry_date) return null;
  const now = new Date();
  const expiry = new Date(lot.expiry_date);
  const diffTime = expiry.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const getPickingProgress = (picking: Picking): number => {
  if (!picking.lines || picking.lines.length === 0) return 0;
  const totalPlanned = picking.lines.reduce((sum, l) => sum + l.quantity_planned, 0);
  const totalDone = picking.lines.reduce((sum, l) => sum + l.quantity_done, 0);
  if (totalPlanned === 0) return 0;
  return Math.round((totalDone / totalPlanned) * 100);
};

export const getInventoryCountProgress = (count: InventoryCount): number => {
  if (!count.lines || count.lines.length === 0) return 0;
  const counted = count.lines.filter(l => l.counted_qty > 0).length;
  return Math.round((counted / count.lines.length) * 100);
};

// ============================================================================
// HELPERS - Navigation
// ============================================================================

export const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};
