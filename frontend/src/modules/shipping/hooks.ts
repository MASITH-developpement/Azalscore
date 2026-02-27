/**
 * AZALSCORE Module - Shipping Hooks
 * React Query hooks pour le module d'expedition
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  zoneApi, carrierApi, rateApi, shipmentApi, packageApi,
  pickupPointApi, returnApi, statsApi,
} from './api';
import type {
  ZoneCreate, ZoneUpdate,
  CarrierCreate, CarrierUpdate,
  RateCreate, RateUpdate,
  ShipmentCreate, ShipmentUpdate, ShipmentFilters,
  PackageCreate,
  TrackingUpdate,
  PickupPointCreate, PickupPointSearch,
  ReturnCreate, ReturnUpdate, ReturnFilters,
  ReturnApproval, ReturnReceipt, ReturnRefund,
  RateCalculationRequest,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const shippingKeys = {
  all: ['shipping'] as const,

  // Zones
  zones: () => [...shippingKeys.all, 'zones'] as const,
  zoneDetail: (id: string) => [...shippingKeys.zones(), 'detail', id] as const,

  // Carriers
  carriers: () => [...shippingKeys.all, 'carriers'] as const,
  carrierDetail: (id: string) => [...shippingKeys.carriers(), 'detail', id] as const,

  // Rates
  rates: (carrierId?: string) => [...shippingKeys.all, 'rates', carrierId] as const,
  rateDetail: (id: string) => [...shippingKeys.all, 'rate', id] as const,

  // Shipments
  shipments: () => [...shippingKeys.all, 'shipments'] as const,
  shipmentList: (filters?: ShipmentFilters) => [...shippingKeys.shipments(), 'list', filters] as const,
  shipmentDetail: (id: string) => [...shippingKeys.shipments(), 'detail', id] as const,
  shipmentTracking: (id: string) => [...shippingKeys.shipments(), 'tracking', id] as const,
  shipmentPackages: (id: string) => [...shippingKeys.shipments(), 'packages', id] as const,

  // Pickup Points
  pickupPoints: (carrierId?: string) => [...shippingKeys.all, 'pickup-points', carrierId] as const,

  // Returns
  returns: () => [...shippingKeys.all, 'returns'] as const,
  returnList: (filters?: ReturnFilters) => [...shippingKeys.returns(), 'list', filters] as const,
  returnDetail: (id: string) => [...shippingKeys.returns(), 'detail', id] as const,

  // Stats
  stats: () => [...shippingKeys.all, 'stats'] as const,
  dashboard: () => [...shippingKeys.all, 'dashboard'] as const,
};

// ============================================================================
// ZONE HOOKS
// ============================================================================

export function useZones() {
  return useQuery({
    queryKey: shippingKeys.zones(),
    queryFn: () => zoneApi.list(),
    select: (data) => data.items,
  });
}

export function useZone(id: string) {
  return useQuery({
    queryKey: shippingKeys.zoneDetail(id),
    queryFn: () => zoneApi.get(id),
    enabled: !!id,
  });
}

export function useCreateZone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ZoneCreate) => zoneApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.zones() });
    },
  });
}

export function useUpdateZone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ZoneUpdate }) => zoneApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.zoneDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.zones() });
    },
  });
}

export function useDeleteZone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => zoneApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.zones() });
    },
  });
}

// ============================================================================
// CARRIER HOOKS
// ============================================================================

export function useCarriers() {
  return useQuery({
    queryKey: shippingKeys.carriers(),
    queryFn: () => carrierApi.list(),
    select: (data) => data.items,
  });
}

export function useCarrier(id: string) {
  return useQuery({
    queryKey: shippingKeys.carrierDetail(id),
    queryFn: () => carrierApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCarrier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CarrierCreate) => carrierApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.carriers() });
    },
  });
}

export function useUpdateCarrier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CarrierUpdate }) => carrierApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.carrierDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.carriers() });
    },
  });
}

export function useDeleteCarrier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => carrierApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.carriers() });
    },
  });
}

export function useTestCarrier() {
  return useMutation({
    mutationFn: (id: string) => carrierApi.test(id),
  });
}

// ============================================================================
// RATE HOOKS
// ============================================================================

export function useRates(carrierId?: string) {
  return useQuery({
    queryKey: shippingKeys.rates(carrierId),
    queryFn: () => rateApi.list(carrierId),
    select: (data) => data.items,
  });
}

export function useRate(id: string) {
  return useQuery({
    queryKey: shippingKeys.rateDetail(id),
    queryFn: () => rateApi.get(id),
    enabled: !!id,
  });
}

export function useCreateRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RateCreate) => rateApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.rates() });
    },
  });
}

export function useUpdateRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RateUpdate }) => rateApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.rateDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.rates() });
    },
  });
}

export function useDeleteRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => rateApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.rates() });
    },
  });
}

export function useCalculateRates() {
  return useMutation({
    mutationFn: (request: RateCalculationRequest) => rateApi.calculate(request),
  });
}

// ============================================================================
// SHIPMENT HOOKS
// ============================================================================

export function useShipmentList(filters?: ShipmentFilters) {
  return useQuery({
    queryKey: shippingKeys.shipmentList(filters),
    queryFn: () => shipmentApi.list(filters),
  });
}

export function useShipment(id: string) {
  return useQuery({
    queryKey: shippingKeys.shipmentDetail(id),
    queryFn: () => shipmentApi.get(id),
    enabled: !!id,
  });
}

export function useShipmentTracking(id: string) {
  return useQuery({
    queryKey: shippingKeys.shipmentTracking(id),
    queryFn: () => shipmentApi.getTracking(id),
    enabled: !!id,
  });
}

export function useCreateShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ShipmentCreate) => shipmentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipments() });
    },
  });
}

export function useUpdateShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ShipmentUpdate }) => shipmentApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipments() });
    },
  });
}

export function useConfirmShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => shipmentApi.confirm(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipments() });
    },
  });
}

export function useGenerateLabel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => shipmentApi.generateLabel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
    },
  });
}

export function useCancelShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => shipmentApi.cancel(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipments() });
    },
  });
}

export function useSchedulePickup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, pickupDate }: { id: string; pickupDate: string }) =>
      shipmentApi.schedulePickup(id, pickupDate),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
    },
  });
}

export function useUpdateTracking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TrackingUpdate }) => shipmentApi.updateTracking(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentTracking(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(id) });
    },
  });
}

export function useTrackByNumber() {
  return useMutation({
    mutationFn: ({ trackingNumber, carrierId }: { trackingNumber: string; carrierId?: string }) =>
      shipmentApi.trackByNumber(trackingNumber, carrierId),
  });
}

// ============================================================================
// PACKAGE HOOKS
// ============================================================================

export function useShipmentPackages(shipmentId: string) {
  return useQuery({
    queryKey: shippingKeys.shipmentPackages(shipmentId),
    queryFn: () => packageApi.list(shipmentId),
    enabled: !!shipmentId,
  });
}

export function useAddPackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ shipmentId, data }: { shipmentId: string; data: PackageCreate }) =>
      packageApi.add(shipmentId, data),
    onSuccess: (_, { shipmentId }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentPackages(shipmentId) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(shipmentId) });
    },
  });
}

export function useDeletePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ shipmentId, packageId }: { shipmentId: string; packageId: string }) =>
      packageApi.delete(shipmentId, packageId),
    onSuccess: (_, { shipmentId }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentPackages(shipmentId) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.shipmentDetail(shipmentId) });
    },
  });
}

// ============================================================================
// PICKUP POINT HOOKS
// ============================================================================

export function usePickupPoints(carrierId?: string) {
  return useQuery({
    queryKey: shippingKeys.pickupPoints(carrierId),
    queryFn: () => pickupPointApi.list(carrierId),
    select: (data) => data.items,
  });
}

export function useSearchPickupPoints() {
  return useMutation({
    mutationFn: (request: PickupPointSearch) => pickupPointApi.search(request),
  });
}

export function useCreatePickupPoint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PickupPointCreate) => pickupPointApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.pickupPoints() });
    },
  });
}

// ============================================================================
// RETURN HOOKS
// ============================================================================

export function useReturnList(filters?: ReturnFilters) {
  return useQuery({
    queryKey: shippingKeys.returnList(filters),
    queryFn: () => returnApi.list(filters),
  });
}

export function useReturn(id: string) {
  return useQuery({
    queryKey: shippingKeys.returnDetail(id),
    queryFn: () => returnApi.get(id),
    enabled: !!id,
  });
}

export function useCreateReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ReturnCreate) => returnApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

export function useApproveReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ReturnApproval }) => returnApi.approve(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

export function useRejectReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => returnApi.reject(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

export function useGenerateReturnLabel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => returnApi.generateLabel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
    },
  });
}

export function useReceiveReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReturnReceipt }) => returnApi.receive(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

export function useProcessRefund() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReturnRefund }) => returnApi.processRefund(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

export function useCompleteReturn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => returnApi.complete(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shippingKeys.returnDetail(id) });
      queryClient.invalidateQueries({ queryKey: shippingKeys.returns() });
    },
  });
}

// ============================================================================
// STATS HOOKS
// ============================================================================

export function useShippingStats(periodStart: string, periodEnd: string) {
  return useQuery({
    queryKey: shippingKeys.stats(),
    queryFn: () => statsApi.getStats(periodStart, periodEnd),
    enabled: !!periodStart && !!periodEnd,
  });
}

export function useShippingDashboard() {
  return useQuery({
    queryKey: shippingKeys.dashboard(),
    queryFn: () => statsApi.getDashboard(),
  });
}
