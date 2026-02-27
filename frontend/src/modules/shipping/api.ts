/**
 * AZALSCORE Module - Shipping API
 * Client API pour le module d'expedition
 */

import { api } from '@core/api-client';
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
    const response = await api.get<ZoneListResponse>(`${BASE_URL}/zones`);
    return response as unknown as ZoneListResponse;
  },

  get: async (id: string): Promise<Zone> => {
    const response = await api.get<Zone>(`${BASE_URL}/zones/${id}`);
    return response as unknown as Zone;
  },

  create: async (data: ZoneCreate): Promise<Zone> => {
    const response = await api.post<Zone>(`${BASE_URL}/zones`, data);
    return response as unknown as Zone;
  },

  update: async (id: string, data: ZoneUpdate): Promise<Zone> => {
    const response = await api.put<Zone>(`${BASE_URL}/zones/${id}`, data);
    return response as unknown as Zone;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/zones/${id}`);
  },
};

// ============================================================================
// CARRIER API
// ============================================================================

export const carrierApi = {
  list: async (): Promise<CarrierListResponse> => {
    const response = await api.get<CarrierListResponse>(`${BASE_URL}/carriers`);
    return response as unknown as CarrierListResponse;
  },

  get: async (id: string): Promise<Carrier> => {
    const response = await api.get<Carrier>(`${BASE_URL}/carriers/${id}`);
    return response as unknown as Carrier;
  },

  create: async (data: CarrierCreate): Promise<Carrier> => {
    const response = await api.post<Carrier>(`${BASE_URL}/carriers`, data);
    return response as unknown as Carrier;
  },

  update: async (id: string, data: CarrierUpdate): Promise<Carrier> => {
    const response = await api.put<Carrier>(`${BASE_URL}/carriers/${id}`, data);
    return response as unknown as Carrier;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/carriers/${id}`);
  },

  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string }>(`${BASE_URL}/carriers/${id}/test`);
    return response as unknown as { success: boolean; message: string };
  },
};

// ============================================================================
// RATE API
// ============================================================================

export const rateApi = {
  list: async (carrierId?: string): Promise<RateListResponse> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    const response = await api.get<RateListResponse>(`${BASE_URL}/rates${params}`);
    return response as unknown as RateListResponse;
  },

  get: async (id: string): Promise<ShippingRate> => {
    const response = await api.get<ShippingRate>(`${BASE_URL}/rates/${id}`);
    return response as unknown as ShippingRate;
  },

  create: async (data: RateCreate): Promise<ShippingRate> => {
    const response = await api.post<ShippingRate>(`${BASE_URL}/rates`, data);
    return response as unknown as ShippingRate;
  },

  update: async (id: string, data: RateUpdate): Promise<ShippingRate> => {
    const response = await api.put<ShippingRate>(`${BASE_URL}/rates/${id}`, data);
    return response as unknown as ShippingRate;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/rates/${id}`);
  },

  calculate: async (request: RateCalculationRequest): Promise<RateCalculationResponse[]> => {
    const response = await api.post<RateCalculationResponse[]>(`${BASE_URL}/rates/calculate`, request);
    return response as unknown as RateCalculationResponse[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/shipments${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<ShipmentListResponse>(url);
    return response as unknown as ShipmentListResponse;
  },

  get: async (id: string): Promise<Shipment> => {
    const response = await api.get<Shipment>(`${BASE_URL}/shipments/${id}`);
    return response as unknown as Shipment;
  },

  create: async (data: ShipmentCreate): Promise<Shipment> => {
    const response = await api.post<Shipment>(`${BASE_URL}/shipments`, data);
    return response as unknown as Shipment;
  },

  update: async (id: string, data: ShipmentUpdate): Promise<Shipment> => {
    const response = await api.put<Shipment>(`${BASE_URL}/shipments/${id}`, data);
    return response as unknown as Shipment;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/shipments/${id}`);
  },

  // Actions
  confirm: async (id: string): Promise<Shipment> => {
    const response = await api.post<Shipment>(`${BASE_URL}/shipments/${id}/confirm`);
    return response as unknown as Shipment;
  },

  generateLabel: async (id: string): Promise<{ label_url: string; tracking_number: string }> => {
    const response = await api.post<{ label_url: string; tracking_number: string }>(`${BASE_URL}/shipments/${id}/label`);
    return response as unknown as { label_url: string; tracking_number: string };
  },

  cancel: async (id: string, reason?: string): Promise<Shipment> => {
    const response = await api.post<Shipment>(`${BASE_URL}/shipments/${id}/cancel`, { reason });
    return response as unknown as Shipment;
  },

  schedulePickup: async (id: string, pickupDate: string): Promise<Shipment> => {
    const response = await api.post<Shipment>(`${BASE_URL}/shipments/${id}/pickup`, { pickup_date: pickupDate });
    return response as unknown as Shipment;
  },

  // Tracking
  getTracking: async (id: string): Promise<TrackingEvent[]> => {
    const response = await api.get<TrackingEvent[]>(`${BASE_URL}/shipments/${id}/tracking`);
    return response as unknown as TrackingEvent[];
  },

  updateTracking: async (id: string, data: TrackingUpdate): Promise<void> => {
    await api.post(`${BASE_URL}/shipments/${id}/tracking`, data);
  },

  trackByNumber: async (trackingNumber: string, carrierId?: string): Promise<TrackingEvent[]> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    const response = await api.get<TrackingEvent[]>(`${BASE_URL}/track/${trackingNumber}${params}`);
    return response as unknown as TrackingEvent[];
  },
};

// ============================================================================
// PACKAGE API
// ============================================================================

export const packageApi = {
  list: async (shipmentId: string): Promise<Package[]> => {
    const response = await api.get<Package[]>(`${BASE_URL}/shipments/${shipmentId}/packages`);
    return response as unknown as Package[];
  },

  add: async (shipmentId: string, data: PackageCreate): Promise<Package> => {
    const response = await api.post<Package>(`${BASE_URL}/shipments/${shipmentId}/packages`, data);
    return response as unknown as Package;
  },

  update: async (shipmentId: string, packageId: string, data: Partial<PackageCreate>): Promise<Package> => {
    const response = await api.put<Package>(`${BASE_URL}/shipments/${shipmentId}/packages/${packageId}`, data);
    return response as unknown as Package;
  },

  delete: async (shipmentId: string, packageId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/shipments/${shipmentId}/packages/${packageId}`);
  },
};

// ============================================================================
// PICKUP POINT API
// ============================================================================

export const pickupPointApi = {
  list: async (carrierId?: string): Promise<PickupPointListResponse> => {
    const params = carrierId ? `?carrier_id=${carrierId}` : '';
    const response = await api.get<PickupPointListResponse>(`${BASE_URL}/pickup-points${params}`);
    return response as unknown as PickupPointListResponse;
  },

  get: async (id: string): Promise<PickupPoint> => {
    const response = await api.get<PickupPoint>(`${BASE_URL}/pickup-points/${id}`);
    return response as unknown as PickupPoint;
  },

  create: async (data: PickupPointCreate): Promise<PickupPoint> => {
    const response = await api.post<PickupPoint>(`${BASE_URL}/pickup-points`, data);
    return response as unknown as PickupPoint;
  },

  update: async (id: string, data: Partial<PickupPointCreate>): Promise<PickupPoint> => {
    const response = await api.put<PickupPoint>(`${BASE_URL}/pickup-points/${id}`, data);
    return response as unknown as PickupPoint;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/pickup-points/${id}`);
  },

  search: async (request: PickupPointSearch): Promise<PickupPoint[]> => {
    const response = await api.post<PickupPoint[]>(`${BASE_URL}/pickup-points/search`, request);
    return response as unknown as PickupPoint[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/returns${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<ReturnListResponse>(url);
    return response as unknown as ReturnListResponse;
  },

  get: async (id: string): Promise<Return> => {
    const response = await api.get<Return>(`${BASE_URL}/returns/${id}`);
    return response as unknown as Return;
  },

  create: async (data: ReturnCreate): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns`, data);
    return response as unknown as Return;
  },

  update: async (id: string, data: ReturnUpdate): Promise<Return> => {
    const response = await api.put<Return>(`${BASE_URL}/returns/${id}`, data);
    return response as unknown as Return;
  },

  // Workflow actions
  approve: async (id: string, data?: ReturnApproval): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns/${id}/approve`, data);
    return response as unknown as Return;
  },

  reject: async (id: string, reason?: string): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns/${id}/reject`, { reason });
    return response as unknown as Return;
  },

  generateLabel: async (id: string): Promise<{ label_url: string; tracking_number: string }> => {
    const response = await api.post<{ label_url: string; tracking_number: string }>(`${BASE_URL}/returns/${id}/label`);
    return response as unknown as { label_url: string; tracking_number: string };
  },

  receive: async (id: string, data: ReturnReceipt): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns/${id}/receive`, data);
    return response as unknown as Return;
  },

  processRefund: async (id: string, data: ReturnRefund): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns/${id}/refund`, data);
    return response as unknown as Return;
  },

  complete: async (id: string): Promise<Return> => {
    const response = await api.post<Return>(`${BASE_URL}/returns/${id}/complete`);
    return response as unknown as Return;
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (periodStart: string, periodEnd: string): Promise<ShippingStats> => {
    const response = await api.get<ShippingStats>(`${BASE_URL}/stats?period_start=${periodStart}&period_end=${periodEnd}`);
    return response as unknown as ShippingStats;
  },

  getDashboard: async (): Promise<{ stats: ShippingStats; recent_shipments: Shipment[]; pending_returns: Return[] }> => {
    const response = await api.get<{ stats: ShippingStats; recent_shipments: Shipment[]; pending_returns: Return[] }>(`${BASE_URL}/dashboard`);
    return response as unknown as { stats: ShippingStats; recent_shipments: Shipment[]; pending_returns: Return[] };
  },
};
