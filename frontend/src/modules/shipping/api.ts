/**
 * AZALSCORE Module - Shipping API
 * Client API pour le module d'expedition
 */

import { api } from '@/core/api-client';
import type {
  Zone, ZoneCreate, ZoneUpdate, ZoneListResponse,
  Carrier, CarrierCreate, CarrierUpdate, CarrierListResponse,
  ShippingRate, RateCreate, RateUpdate, RateListResponse,
  Shipment, ShipmentCreate, ShipmentUpdate, ShipmentListResponse, ShipmentFilters,
  Package, PackageCreate,
  TrackingEvent, TrackingUpdate,
  PickupPoint, PickupPointCreate, PickupPointSearch, PickupPointListResponse,
  Return, ReturnCreate, ReturnUpdate, ReturnListResponse, ReturnFilters,
  ReturnApproval, ReturnReceipt, ReturnRefund,
  RateCalculationRequest, RateCalculationResponse,
  ShippingStats,
} from './types';

const BASE_URL = '/shipping';

// ============================================================================
// ZONE API
// ============================================================================

export const zoneApi = {
  list: async (): Promise<ZoneListResponse> => {
    return api.get(`${BASE_URL}/zones`);
  },

  get: async (id: string): Promise<Zone> => {
    return api.get(`${BASE_URL}/zones/${id}`);
  },

  create: async (data: ZoneCreate): Promise<Zone> => {
    return api.post(`${BASE_URL}/zones`, data);
  },

  update: async (id: string, data: ZoneUpdate): Promise<Zone> => {
    return api.put(`${BASE_URL}/zones/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/zones/${id}`);
  },
};

// ============================================================================
// CARRIER API
// ============================================================================

export const carrierApi = {
  list: async (): Promise<CarrierListResponse> => {
    return api.get(`${BASE_URL}/carriers`);
  },

  get: async (id: string): Promise<Carrier> => {
    return api.get(`${BASE_URL}/carriers/${id}`);
  },

  create: async (data: CarrierCreate): Promise<Carrier> => {
    return api.post(`${BASE_URL}/carriers`, data);
  },

  update: async (id: string, data: CarrierUpdate): Promise<Carrier> => {
    return api.put(`${BASE_URL}/carriers/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/carriers/${id}`);
  },

  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    return api.post(`${BASE_URL}/carriers/${id}/test`);
  },
};

// ============================================================================
// RATE API
// ============================================================================

export const rateApi = {
  list: async (carrierId?: string): Promise<RateListResponse> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    return api.get(`${BASE_URL}/rates${params}`);
  },

  get: async (id: string): Promise<ShippingRate> => {
    return api.get(`${BASE_URL}/rates/${id}`);
  },

  create: async (data: RateCreate): Promise<ShippingRate> => {
    return api.post(`${BASE_URL}/rates`, data);
  },

  update: async (id: string, data: RateUpdate): Promise<ShippingRate> => {
    return api.put(`${BASE_URL}/rates/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/rates/${id}`);
  },

  calculate: async (request: RateCalculationRequest): Promise<RateCalculationResponse[]> => {
    return api.post(`${BASE_URL}/rates/calculate`, request);
  },
};

// ============================================================================
// SHIPMENT API
// ============================================================================

export const shipmentApi = {
  list: async (filters?: ShipmentFilters): Promise<ShipmentListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.carrier_id) params.set('carrier_id', filters.carrier_id);
    if (filters?.shipping_method) params.set('shipping_method', filters.shipping_method);
    if (filters?.order_id) params.set('order_id', filters.order_id);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.skip) params.set('skip', String(filters.skip));
    if (filters?.limit) params.set('limit', String(filters.limit));
    return api.get(`${BASE_URL}/shipments?${params}`);
  },

  get: async (id: string): Promise<Shipment> => {
    return api.get(`${BASE_URL}/shipments/${id}`);
  },

  create: async (data: ShipmentCreate): Promise<Shipment> => {
    return api.post(`${BASE_URL}/shipments`, data);
  },

  update: async (id: string, data: ShipmentUpdate): Promise<Shipment> => {
    return api.put(`${BASE_URL}/shipments/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/shipments/${id}`);
  },

  // Actions
  confirm: async (id: string): Promise<Shipment> => {
    return api.post(`${BASE_URL}/shipments/${id}/confirm`);
  },

  generateLabel: async (id: string): Promise<{ label_url: string; tracking_number: string }> => {
    return api.post(`${BASE_URL}/shipments/${id}/label`);
  },

  cancel: async (id: string, reason?: string): Promise<Shipment> => {
    return api.post(`${BASE_URL}/shipments/${id}/cancel`, { reason });
  },

  schedulePickup: async (id: string, pickupDate: string): Promise<Shipment> => {
    return api.post(`${BASE_URL}/shipments/${id}/pickup`, { pickup_date: pickupDate });
  },

  // Tracking
  getTracking: async (id: string): Promise<TrackingEvent[]> => {
    return api.get(`${BASE_URL}/shipments/${id}/tracking`);
  },

  updateTracking: async (id: string, data: TrackingUpdate): Promise<void> => {
    return api.post(`${BASE_URL}/shipments/${id}/tracking`, data);
  },

  trackByNumber: async (trackingNumber: string, carrierId?: string): Promise<TrackingEvent[]> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    return api.get(`${BASE_URL}/track/${trackingNumber}${params}`);
  },
};

// ============================================================================
// PACKAGE API
// ============================================================================

export const packageApi = {
  list: async (shipmentId: string): Promise<Package[]> => {
    return api.get(`${BASE_URL}/shipments/${shipmentId}/packages`);
  },

  add: async (shipmentId: string, data: PackageCreate): Promise<Package> => {
    return api.post(`${BASE_URL}/shipments/${shipmentId}/packages`, data);
  },

  update: async (shipmentId: string, packageId: string, data: Partial<PackageCreate>): Promise<Package> => {
    return api.put(`${BASE_URL}/shipments/${shipmentId}/packages/${packageId}`, data);
  },

  delete: async (shipmentId: string, packageId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/shipments/${shipmentId}/packages/${packageId}`);
  },
};

// ============================================================================
// PICKUP POINT API
// ============================================================================

export const pickupPointApi = {
  list: async (carrierId?: string): Promise<PickupPointListResponse> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    return api.get(`${BASE_URL}/pickup-points${params}`);
  },

  get: async (id: string): Promise<PickupPoint> => {
    return api.get(`${BASE_URL}/pickup-points/${id}`);
  },

  create: async (data: PickupPointCreate): Promise<PickupPoint> => {
    return api.post(`${BASE_URL}/pickup-points`, data);
  },

  update: async (id: string, data: Partial<PickupPointCreate>): Promise<PickupPoint> => {
    return api.put(`${BASE_URL}/pickup-points/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/pickup-points/${id}`);
  },

  search: async (request: PickupPointSearch): Promise<PickupPoint[]> => {
    return api.post(`${BASE_URL}/pickup-points/search`, request);
  },
};

// ============================================================================
// RETURN API
// ============================================================================

export const returnApi = {
  list: async (filters?: ReturnFilters): Promise<ReturnListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.order_id) params.set('order_id', filters.order_id);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.skip) params.set('skip', String(filters.skip));
    if (filters?.limit) params.set('limit', String(filters.limit));
    return api.get(`${BASE_URL}/returns?${params}`);
  },

  get: async (id: string): Promise<Return> => {
    return api.get(`${BASE_URL}/returns/${id}`);
  },

  create: async (data: ReturnCreate): Promise<Return> => {
    return api.post(`${BASE_URL}/returns`, data);
  },

  update: async (id: string, data: ReturnUpdate): Promise<Return> => {
    return api.put(`${BASE_URL}/returns/${id}`, data);
  },

  // Workflow actions
  approve: async (id: string, data?: ReturnApproval): Promise<Return> => {
    return api.post(`${BASE_URL}/returns/${id}/approve`, data);
  },

  reject: async (id: string, reason?: string): Promise<Return> => {
    return api.post(`${BASE_URL}/returns/${id}/reject`, { reason });
  },

  generateLabel: async (id: string): Promise<{ label_url: string; tracking_number: string }> => {
    return api.post(`${BASE_URL}/returns/${id}/label`);
  },

  receive: async (id: string, data: ReturnReceipt): Promise<Return> => {
    return api.post(`${BASE_URL}/returns/${id}/receive`, data);
  },

  processRefund: async (id: string, data: ReturnRefund): Promise<Return> => {
    return api.post(`${BASE_URL}/returns/${id}/refund`, data);
  },

  complete: async (id: string): Promise<Return> => {
    return api.post(`${BASE_URL}/returns/${id}/complete`);
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (periodStart: string, periodEnd: string): Promise<ShippingStats> => {
    return api.get(`${BASE_URL}/stats?period_start=${periodStart}&period_end=${periodEnd}`);
  },

  getDashboard: async (): Promise<{ stats: ShippingStats; recent_shipments: Shipment[]; pending_returns: Return[] }> => {
    return api.get(`${BASE_URL}/dashboard`);
  },
};
