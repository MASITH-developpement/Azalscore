/**
 * AZALSCORE Module - Shipping Types
 * Types TypeScript pour le module d'expedition
 */

// ============================================================================
// ENUMS
// ============================================================================

export type ShipmentStatus =
  | 'draft'
  | 'pending'
  | 'confirmed'
  | 'label_created'
  | 'picked_up'
  | 'in_transit'
  | 'out_for_delivery'
  | 'delivered'
  | 'failed'
  | 'returned'
  | 'cancelled';

export type CarrierType =
  | 'postal'
  | 'express'
  | 'freight'
  | 'local'
  | 'international';

export type ShippingMethod =
  | 'standard'
  | 'express'
  | 'overnight'
  | 'economy'
  | 'pickup_point';

export type CalculationMethod =
  | 'weight'
  | 'volume'
  | 'price'
  | 'fixed'
  | 'tiered';

export type ReturnStatus =
  | 'requested'
  | 'approved'
  | 'label_sent'
  | 'in_transit'
  | 'received'
  | 'inspected'
  | 'completed'
  | 'rejected';

export type ReturnCondition =
  | 'new'
  | 'like_new'
  | 'good'
  | 'fair'
  | 'damaged'
  | 'defective';

// ============================================================================
// ADDRESS
// ============================================================================

export interface Address {
  name: string;
  company?: string;
  street1: string;
  street2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country_code: string;
  phone?: string;
  email?: string;
  is_residential?: boolean;
  instructions?: string;
}

// ============================================================================
// ZONE
// ============================================================================

export interface Zone {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  description?: string;
  countries: string[];
  postal_codes: string[];
  excluded_postal_codes: string[];
  sort_order: number;
  is_active: boolean;
  created_at: string;
}

export interface ZoneCreate {
  name: string;
  code: string;
  description?: string;
  countries?: string[];
  postal_codes?: string[];
  excluded_postal_codes?: string[];
  sort_order?: number;
}

export interface ZoneUpdate {
  name?: string;
  code?: string;
  description?: string;
  countries?: string[];
  postal_codes?: string[];
  excluded_postal_codes?: string[];
  sort_order?: number;
  is_active?: boolean;
}

// ============================================================================
// CARRIER
// ============================================================================

export interface Carrier {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  description?: string;
  carrier_type: CarrierType;
  supports_tracking: boolean;
  supports_labels: boolean;
  supports_returns: boolean;
  supports_pickup: boolean;
  supports_insurance: boolean;
  min_delivery_days: number;
  max_delivery_days: number;
  max_weight_kg: number | string;
  max_length_cm: number;
  max_girth_cm: number;
  logo_url?: string;
  tracking_url_template?: string;
  is_active: boolean;
  created_at: string;
  // API integration flags
  api_integration?: boolean;
  tracking_integration?: boolean;
}

export interface CarrierCreate {
  name: string;
  code: string;
  description?: string;
  carrier_type?: CarrierType;
  api_endpoint?: string;
  api_key?: string;
  api_secret?: string;
  account_number?: string;
  supports_tracking?: boolean;
  supports_labels?: boolean;
  supports_returns?: boolean;
  supports_pickup?: boolean;
  supports_insurance?: boolean;
  min_delivery_days?: number;
  max_delivery_days?: number;
  max_weight_kg?: number;
  logo_url?: string;
  tracking_url_template?: string;
}

export interface CarrierUpdate {
  name?: string;
  description?: string;
  carrier_type?: CarrierType;
  api_endpoint?: string;
  api_key?: string;
  api_secret?: string;
  account_number?: string;
  supports_tracking?: boolean;
  supports_labels?: boolean;
  supports_returns?: boolean;
  supports_pickup?: boolean;
  supports_insurance?: boolean;
  min_delivery_days?: number;
  max_delivery_days?: number;
  max_weight_kg?: number;
  logo_url?: string;
  tracking_url_template?: string;
  is_active?: boolean;
}

// ============================================================================
// SHIPPING RATE
// ============================================================================

export interface ShippingRate {
  id: string;
  tenant_id: string;
  carrier_id: string;
  zone_id?: string;
  name: string;
  code: string;
  shipping_method: ShippingMethod;
  calculation_method: CalculationMethod;
  base_rate: number | string;
  per_kg_rate: number | string;
  per_item_rate: number | string;
  percent_of_order: number | string;
  currency: string;
  weight_tiers: WeightTier[];
  price_tiers: PriceTier[];
  fuel_surcharge_percent: number | string;
  residential_surcharge: number | string;
  oversized_surcharge: number | string;
  free_shipping_threshold?: number | string;
  min_days: number;
  max_days: number;
  valid_from?: string;
  valid_until?: string;
  is_active: boolean;
  created_at: string;
  // Display fields (derived from relations)
  carrier_name?: string;
  zone_name?: string;
  // Alias for display
  base_price?: number | string;
  price_per_kg?: number | string;
  estimated_days_min?: number;
  estimated_days_max?: number;
}

export interface WeightTier {
  min_weight: number;
  max_weight: number;
  rate: number;
}

export interface PriceTier {
  min_price: number;
  max_price: number;
  rate: number;
}

export interface RateCreate {
  carrier_id: string;
  zone_id?: string;
  name: string;
  code?: string;
  shipping_method?: ShippingMethod;
  calculation_method?: CalculationMethod;
  base_rate?: number;
  per_kg_rate?: number;
  per_item_rate?: number;
  percent_of_order?: number;
  weight_tiers?: WeightTier[];
  price_tiers?: PriceTier[];
  fuel_surcharge_percent?: number;
  residential_surcharge?: number;
  oversized_surcharge?: number;
  free_shipping_threshold?: number;
  min_days?: number;
  max_days?: number;
  valid_from?: string;
  valid_until?: string;
}

export interface RateUpdate {
  zone_id?: string;
  name?: string;
  shipping_method?: ShippingMethod;
  calculation_method?: CalculationMethod;
  base_rate?: number;
  per_kg_rate?: number;
  per_item_rate?: number;
  percent_of_order?: number;
  weight_tiers?: WeightTier[];
  price_tiers?: PriceTier[];
  fuel_surcharge_percent?: number;
  residential_surcharge?: number;
  oversized_surcharge?: number;
  free_shipping_threshold?: number;
  min_days?: number;
  max_days?: number;
  valid_from?: string;
  valid_until?: string;
  is_active?: boolean;
}

// ============================================================================
// PACKAGE
// ============================================================================

export interface Package {
  id: string;
  shipment_id: string;
  package_type: string;
  length: number | string;
  width: number | string;
  height: number | string;
  weight: number | string;
  dimensional_weight: number | string;
  billable_weight: number | string;
  items: PackageItem[];
  declared_value: number | string;
  currency: string;
  tracking_number?: string;
  label_url?: string;
  label_format: string;
}

export interface PackageItem {
  product_id?: string;
  sku?: string;
  name: string;
  quantity: number;
  value: number;
  weight?: number;
}

export interface PackageCreate {
  package_type?: string;
  length?: number;
  width?: number;
  height?: number;
  weight?: number;
  items?: PackageItem[];
  declared_value?: number;
  label_format?: string;
}

// ============================================================================
// SHIPMENT
// ============================================================================

export interface Shipment {
  id: string;
  tenant_id: string;
  shipment_number: string;
  order_id?: string;
  order_number?: string;
  status: ShipmentStatus;
  carrier_id?: string;
  carrier_name?: string;
  shipping_method: ShippingMethod;
  service_code?: string;
  ship_from: Address;
  ship_to: Address;
  packages: Package[];
  total_packages: number;
  total_weight: number | string;
  master_tracking_number?: string;
  tracking_number?: string;
  tracking_url?: string;
  label_url?: string;
  shipping_cost: number | string;
  insurance_cost: number | string;
  surcharges: number | string;
  total_cost: number | string;
  currency: string;
  is_insured: boolean;
  insured_value: number | string;
  signature_required: boolean;
  saturday_delivery: boolean;
  hold_at_location: boolean;
  ship_date?: string;
  estimated_delivery?: string;
  actual_delivery?: string;
  pickup_scheduled: boolean;
  pickup_date?: string;
  pickup_confirmation?: string;
  pickup_point_id?: string;
  pickup_point_name?: string;
  pickup_point_address?: string;
  last_event?: string;
  last_event_at?: string;
  notes?: string;
  created_at: string;
  // Convenience fields (derived from ship_to)
  recipient_name?: string;
  recipient_city?: string;
}

export interface ShipmentCreate {
  order_id?: string;
  order_number?: string;
  carrier_id: string;
  shipping_method?: ShippingMethod;
  service_code?: string;
  ship_from: Address;
  ship_to: Address;
  packages: PackageCreate[];
  shipping_cost?: number;
  is_insured?: boolean;
  insured_value?: number;
  signature_required?: boolean;
  saturday_delivery?: boolean;
  hold_at_location?: boolean;
  pickup_point_id?: string;
  notes?: string;
}

export interface ShipmentUpdate {
  ship_to?: Address;
  is_insured?: boolean;
  insured_value?: number;
  signature_required?: boolean;
  saturday_delivery?: boolean;
  hold_at_location?: boolean;
  pickup_point_id?: string;
  notes?: string;
  internal_notes?: string;
}

// ============================================================================
// TRACKING
// ============================================================================

export interface TrackingEvent {
  timestamp: string;
  status: string;
  description: string;
  location?: string;
}

export interface TrackingUpdate {
  status: string;
  event_description: string;
  location?: string;
  event_time?: string;
}

// ============================================================================
// PICKUP POINT
// ============================================================================

export interface PickupPoint {
  id: string;
  tenant_id: string;
  carrier_id: string;
  external_id: string;
  name: string;
  address: Address;
  opening_hours: Record<string, string>;
  is_locker: boolean;
  has_parking: boolean;
  wheelchair_accessible: boolean;
  latitude?: number | string;
  longitude?: number | string;
  is_active: boolean;
  created_at: string;
  // Derived/display fields
  carrier_name?: string;
  city?: string;
  postal_code?: string;
}

export interface PickupPointCreate {
  carrier_id: string;
  external_id: string;
  name: string;
  address: Address;
  opening_hours?: Record<string, string>;
  is_locker?: boolean;
  has_parking?: boolean;
  wheelchair_accessible?: boolean;
  latitude?: number;
  longitude?: number;
}

export interface PickupPointSearch {
  carrier_id: string;
  country_code: string;
  postal_code: string;
  latitude?: number;
  longitude?: number;
  max_results?: number;
  max_distance_km?: number;
}

// ============================================================================
// RETURN
// ============================================================================

export interface Return {
  id: string;
  tenant_id: string;
  return_number: string;
  order_id?: string;
  shipment_id?: string;
  status: ReturnStatus;
  reason: string;
  reason_code?: string;
  customer_notes?: string;
  items: ReturnItem[];
  return_carrier_id?: string;
  return_tracking_number?: string;
  return_label_url?: string;
  return_address: Address;
  requested_at: string;
  approved_at?: string;
  received_at?: string;
  inspected_at?: string;
  completed_at?: string;
  inspection_notes?: string;
  condition?: ReturnCondition;
  refund_amount: number | string;
  refund_method?: string;
  refund_reference?: string;
  currency: string;
  return_shipping_cost: number | string;
  restocking_fee: number | string;
  processed_by?: string;
  created_at: string;
}

export interface ReturnItem {
  product_id?: string;
  sku?: string;
  name: string;
  quantity: number;
  reason?: string;
}

export interface ReturnCreate {
  order_id?: string;
  shipment_id?: string;
  reason: string;
  reason_code?: string;
  customer_notes?: string;
  items: ReturnItem[];
  return_address?: Address;
}

export interface ReturnUpdate {
  reason?: string;
  reason_code?: string;
  customer_notes?: string;
  items?: ReturnItem[];
  return_address?: Address;
}

export interface ReturnApproval {
  notes?: string;
}

export interface ReturnReceipt {
  condition: ReturnCondition;
  inspection_notes?: string;
}

export interface ReturnRefund {
  refund_amount: number;
  refund_method: string;
  restocking_fee?: number;
  refund_reference?: string;
}

// ============================================================================
// RATE CALCULATION
// ============================================================================

export interface RateCalculationRequest {
  destination: Address;
  packages: PackageCreate[];
  order_total?: number;
  currency?: string;
}

export interface RateCalculationResponse {
  rate_id: string;
  carrier_id: string;
  carrier_name: string;
  carrier_code: string;
  method: ShippingMethod;
  rate_name: string;
  cost: number | string;
  currency: string;
  min_days: number;
  max_days: number;
  is_free_shipping: boolean;
  zone_id?: string;
  zone_name?: string;
}

// ============================================================================
// STATS
// ============================================================================

export interface ShippingStats {
  period_start: string;
  period_end: string;
  total_shipments: number;
  total_packages: number;
  total_weight_kg: number;
  status_counts: Record<string, number>;
  on_time_delivery_rate: number;
  avg_delivery_days: number;
  total_shipping_cost: number;
  avg_cost_per_shipment: number;
  shipments_by_carrier: Record<string, number>;
  cost_by_carrier: Record<string, number>;
  shipments_by_method: Record<string, number>;
  total_returns: number;
  return_rate: number;
  // Dashboard stats
  in_transit?: number;
  delivered_today?: number;
  pending_returns?: number;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export type ZoneListResponse = PaginatedResponse<Zone>;
export type CarrierListResponse = PaginatedResponse<Carrier>;
export type RateListResponse = PaginatedResponse<ShippingRate>;
export type ShipmentListResponse = PaginatedResponse<Shipment>;
export type PickupPointListResponse = PaginatedResponse<PickupPoint>;
export type ReturnListResponse = PaginatedResponse<Return>;

// ============================================================================
// FILTERS
// ============================================================================

export interface ShipmentFilters {
  status?: ShipmentStatus;
  carrier_id?: string;
  shipping_method?: ShippingMethod;
  order_id?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface ReturnFilters {
  status?: ReturnStatus;
  order_id?: string;
  from_date?: string;
  to_date?: string;
  skip?: number;
  limit?: number;
}

// ============================================================================
// CONFIG CONSTANTS
// ============================================================================

export const SHIPMENT_STATUS_CONFIG: Record<ShipmentStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  pending: { label: 'En attente', color: 'yellow' },
  confirmed: { label: 'Confirmee', color: 'blue' },
  label_created: { label: 'Etiquette creee', color: 'blue' },
  picked_up: { label: 'Enlevee', color: 'purple' },
  in_transit: { label: 'En transit', color: 'orange' },
  out_for_delivery: { label: 'En livraison', color: 'orange' },
  delivered: { label: 'Livree', color: 'green' },
  failed: { label: 'Echec', color: 'red' },
  returned: { label: 'Retournee', color: 'purple' },
  cancelled: { label: 'Annulee', color: 'gray' },
};

export const CARRIER_TYPE_CONFIG: Record<CarrierType, { label: string; color: string }> = {
  postal: { label: 'Postal', color: 'blue' },
  express: { label: 'Express', color: 'green' },
  freight: { label: 'Fret', color: 'orange' },
  local: { label: 'Local', color: 'purple' },
  international: { label: 'International', color: 'red' },
};

export const SHIPPING_METHOD_CONFIG: Record<ShippingMethod, { label: string; color: string }> = {
  standard: { label: 'Standard', color: 'blue' },
  express: { label: 'Express', color: 'green' },
  overnight: { label: 'Express 24h', color: 'orange' },
  economy: { label: 'Economique', color: 'gray' },
  pickup_point: { label: 'Point relais', color: 'purple' },
};

export const RETURN_STATUS_CONFIG: Record<ReturnStatus, { label: string; color: string }> = {
  requested: { label: 'Demande', color: 'yellow' },
  approved: { label: 'Approuve', color: 'blue' },
  label_sent: { label: 'Etiquette envoyee', color: 'blue' },
  in_transit: { label: 'En transit', color: 'orange' },
  received: { label: 'Recu', color: 'purple' },
  inspected: { label: 'Inspecte', color: 'purple' },
  completed: { label: 'Termine', color: 'green' },
  rejected: { label: 'Rejete', color: 'red' },
};
