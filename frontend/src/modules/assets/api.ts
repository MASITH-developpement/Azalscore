/**
 * AZALSCORE - Assets API
 * ======================
 * Complete typed API client for Assets (Immobilisations) module.
 * Covers: Assets, Categories, Depreciation, Maintenance, Inventory, Insurance
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const assetsKeys = {
  all: ['assets'] as const,
  list: () => [...assetsKeys.all, 'list'] as const,
  detail: (id: string) => [...assetsKeys.all, id] as const,
  categories: () => [...assetsKeys.all, 'categories'] as const,
  depreciation: (id: string) => [...assetsKeys.all, id, 'depreciation'] as const,
  maintenance: () => [...assetsKeys.all, 'maintenance'] as const,
  inventory: () => [...assetsKeys.all, 'inventory'] as const,
  insurance: () => [...assetsKeys.all, 'insurance'] as const,
  movements: (id: string) => [...assetsKeys.all, id, 'movements'] as const,
  stats: () => [...assetsKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type AssetType =
  | 'INTANGIBLE_GOODWILL' | 'INTANGIBLE_PATENT' | 'INTANGIBLE_LICENSE'
  | 'INTANGIBLE_SOFTWARE' | 'INTANGIBLE_TRADEMARK' | 'INTANGIBLE_RD' | 'INTANGIBLE_OTHER'
  | 'TANGIBLE_LAND' | 'TANGIBLE_BUILDING' | 'TANGIBLE_TECHNICAL'
  | 'TANGIBLE_INDUSTRIAL' | 'TANGIBLE_TRANSPORT' | 'TANGIBLE_OFFICE'
  | 'TANGIBLE_IT' | 'TANGIBLE_FURNITURE' | 'TANGIBLE_FIXTURE'
  | 'TANGIBLE_TOOLS' | 'TANGIBLE_OTHER'
  | 'FINANCIAL_PARTICIPATION' | 'FINANCIAL_LOAN' | 'FINANCIAL_DEPOSIT' | 'FINANCIAL_OTHER'
  | 'IN_PROGRESS';

export type DepreciationMethod =
  | 'LINEAR' | 'DECLINING_BALANCE' | 'UNITS_OF_PRODUCTION'
  | 'SUM_OF_YEARS_DIGITS' | 'EXCEPTIONAL' | 'NONE';

export type AssetStatus =
  | 'DRAFT' | 'ORDERED' | 'RECEIVED' | 'IN_SERVICE'
  | 'UNDER_MAINTENANCE' | 'OUT_OF_SERVICE' | 'FULLY_DEPRECIATED'
  | 'DISPOSED' | 'SCRAPPED' | 'TRANSFERRED' | 'STOLEN' | 'DESTROYED';

export type DisposalType =
  | 'SALE' | 'SCRAP' | 'DONATION' | 'THEFT'
  | 'DESTRUCTION' | 'TRANSFER_INTRAGROUP' | 'EXCHANGE' | 'LOSS';

export type MovementType =
  | 'ACQUISITION' | 'IMPROVEMENT' | 'REVALUATION_UP' | 'REVALUATION_DOWN'
  | 'IMPAIRMENT' | 'IMPAIRMENT_REVERSAL' | 'DEPRECIATION'
  | 'DISPOSAL' | 'TRANSFER' | 'SPLIT' | 'MERGE';

export type MaintenanceType =
  | 'PREVENTIVE' | 'CORRECTIVE' | 'PREDICTIVE'
  | 'REGULATORY' | 'CALIBRATION' | 'INSPECTION' | 'UPGRADE';

export type MaintenanceStatus =
  | 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'OVERDUE';

export type InventoryStatus =
  | 'DRAFT' | 'IN_PROGRESS' | 'COMPLETED' | 'VALIDATED' | 'CANCELLED';

export type InsuranceStatus = 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'PENDING';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface AssetCategory {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
  default_asset_type?: AssetType | null;
  default_depreciation_method: DepreciationMethod;
  default_useful_life_years?: number | null;
  default_useful_life_months: number;
  pcg_account_asset?: string | null;
  pcg_account_depreciation?: string | null;
  pcg_account_expense?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Asset {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  category_id: string;
  asset_type: AssetType;
  status: AssetStatus;
  acquisition_date: string;
  acquisition_value: number;
  residual_value: number;
  current_value: number;
  accumulated_depreciation: number;
  depreciation_method: DepreciationMethod;
  useful_life_years?: number | null;
  useful_life_months: number;
  depreciation_start_date?: string | null;
  location?: string | null;
  serial_number?: string | null;
  barcode?: string | null;
  supplier_id?: string | null;
  invoice_number?: string | null;
  warranty_end_date?: string | null;
  assigned_to?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetMovement {
  id: string;
  tenant_id: string;
  asset_id: string;
  movement_type: MovementType;
  movement_date: string;
  amount: number;
  description?: string | null;
  reference?: string | null;
  value_before: number;
  value_after: number;
  created_by?: string | null;
  created_at: string;
}

export interface DepreciationSchedule {
  id: string;
  asset_id: string;
  period_start: string;
  period_end: string;
  depreciation_amount: number;
  accumulated_depreciation: number;
  net_book_value: number;
  is_posted: boolean;
  posted_at?: string | null;
}

export interface MaintenanceRecord {
  id: string;
  tenant_id: string;
  asset_id: string;
  maintenance_type: MaintenanceType;
  status: MaintenanceStatus;
  scheduled_date: string;
  completed_date?: string | null;
  description: string;
  cost?: number | null;
  performed_by?: string | null;
  notes?: string | null;
  next_maintenance_date?: string | null;
  created_at: string;
}

export interface InventorySession {
  id: string;
  tenant_id: string;
  name: string;
  status: InventoryStatus;
  start_date: string;
  end_date?: string | null;
  location?: string | null;
  assigned_to?: string | null;
  total_assets: number;
  verified_assets: number;
  discrepancies: number;
  notes?: string | null;
  created_at: string;
}

export interface AssetInsurance {
  id: string;
  tenant_id: string;
  asset_id: string;
  policy_number: string;
  provider: string;
  coverage_type: string;
  coverage_amount: number;
  premium_amount: number;
  start_date: string;
  end_date: string;
  status: InsuranceStatus;
  notes?: string | null;
}

export interface AssetStats {
  total_assets: number;
  total_acquisition_value: number;
  total_current_value: number;
  total_depreciation: number;
  by_status: Record<AssetStatus, number>;
  by_type: Record<AssetType, number>;
  maintenance_due: number;
  insurance_expiring_soon: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface AssetCreate {
  code: string;
  name: string;
  description?: string;
  category_id: string;
  asset_type: AssetType;
  acquisition_date: string;
  acquisition_value: number;
  residual_value?: number;
  depreciation_method?: DepreciationMethod;
  useful_life_years?: number;
  useful_life_months?: number;
  depreciation_start_date?: string;
  location?: string;
  serial_number?: string;
  barcode?: string;
  supplier_id?: string;
  invoice_number?: string;
  warranty_end_date?: string;
  notes?: string;
}

export interface AssetUpdate {
  name?: string;
  description?: string;
  category_id?: string;
  status?: AssetStatus;
  residual_value?: number;
  location?: string;
  assigned_to?: string;
  notes?: string;
}

export interface MaintenanceCreate {
  asset_id: string;
  maintenance_type: MaintenanceType;
  scheduled_date: string;
  description: string;
  performed_by?: string;
  notes?: string;
}

// ============================================================================
// HOOKS - ASSETS
// ============================================================================

export function useAssets(filters?: {
  status?: AssetStatus;
  asset_type?: AssetType;
  category_id?: string;
  location?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...assetsKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.asset_type) params.append('asset_type', filters.asset_type);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      if (filters?.location) params.append('location', filters.location);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Asset[]; total: number }>(
        `/assets${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useAsset(id: string) {
  return useQuery({
    queryKey: assetsKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Asset>(`/assets/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AssetCreate) => {
      return api.post<Asset>('/assets', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.list() });
    },
  });
}

export function useUpdateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: AssetUpdate }) => {
      return api.put<Asset>(`/assets/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.list() });
      queryClient.invalidateQueries({ queryKey: assetsKeys.detail(id) });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/assets/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.list() });
    },
  });
}

// ============================================================================
// HOOKS - CATEGORIES
// ============================================================================

export function useAssetCategories() {
  return useQuery({
    queryKey: assetsKeys.categories(),
    queryFn: async () => {
      const response = await api.get<{ items: AssetCategory[] }>('/assets/categories');
      return response;
    },
  });
}

export function useCreateAssetCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Omit<AssetCategory, 'id' | 'tenant_id' | 'is_active' | 'created_at'>) => {
      return api.post<AssetCategory>('/assets/categories', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.categories() });
    },
  });
}

// ============================================================================
// HOOKS - DEPRECIATION
// ============================================================================

export function useDepreciationSchedule(assetId: string) {
  return useQuery({
    queryKey: assetsKeys.depreciation(assetId),
    queryFn: async () => {
      const response = await api.get<{ items: DepreciationSchedule[] }>(
        `/assets/${assetId}/depreciation`
      );
      return response;
    },
    enabled: !!assetId,
  });
}

export function useCalculateDepreciation() {
  return useMutation({
    mutationFn: async (data: {
      acquisition_value: number;
      residual_value: number;
      depreciation_method: DepreciationMethod;
      useful_life_months: number;
      start_date: string;
    }) => {
      return api.post<{ schedule: DepreciationSchedule[] }>('/assets/depreciation/calculate', data);
    },
  });
}

export function usePostDepreciation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { asset_ids?: string[]; period_end: string }) => {
      return api.post<{ posted_count: number; total_amount: number }>('/assets/depreciation/post', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.all });
    },
  });
}

// ============================================================================
// HOOKS - MOVEMENTS
// ============================================================================

export function useAssetMovements(assetId: string) {
  return useQuery({
    queryKey: assetsKeys.movements(assetId),
    queryFn: async () => {
      const response = await api.get<{ items: AssetMovement[] }>(`/assets/${assetId}/movements`);
      return response;
    },
    enabled: !!assetId,
  });
}

export function useDisposeAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      asset_id: string;
      disposal_type: DisposalType;
      disposal_date: string;
      disposal_value?: number;
      description?: string;
    }) => {
      return api.post<AssetMovement>(`/assets/${data.asset_id}/dispose`, data);
    },
    onSuccess: (_, { asset_id }) => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.list() });
      queryClient.invalidateQueries({ queryKey: assetsKeys.detail(asset_id) });
    },
  });
}

// ============================================================================
// HOOKS - MAINTENANCE
// ============================================================================

export function useMaintenanceRecords(filters?: {
  asset_id?: string;
  status?: MaintenanceStatus;
  maintenance_type?: MaintenanceType;
}) {
  return useQuery({
    queryKey: [...assetsKeys.maintenance(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.asset_id) params.append('asset_id', filters.asset_id);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.maintenance_type) params.append('maintenance_type', filters.maintenance_type);
      const queryString = params.toString();
      const response = await api.get<{ items: MaintenanceRecord[] }>(
        `/assets/maintenance${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateMaintenance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: MaintenanceCreate) => {
      return api.post<MaintenanceRecord>('/assets/maintenance', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.maintenance() });
    },
  });
}

export function useCompleteMaintenance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { cost?: number; notes?: string } }) => {
      return api.post<MaintenanceRecord>(`/assets/maintenance/${id}/complete`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.maintenance() });
    },
  });
}

// ============================================================================
// HOOKS - INVENTORY
// ============================================================================

export function useInventorySessions(filters?: { status?: InventoryStatus }) {
  return useQuery({
    queryKey: [...assetsKeys.inventory(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<{ items: InventorySession[] }>(
        `/assets/inventory${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateInventorySession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; location?: string; assigned_to?: string }) => {
      return api.post<InventorySession>('/assets/inventory', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.inventory() });
    },
  });
}

export function useScanAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { session_id: string; barcode: string; location?: string }) => {
      return api.post<{ asset: Asset; status: 'found' | 'not_found' | 'discrepancy' }>(
        '/assets/inventory/scan',
        data
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetsKeys.inventory() });
    },
  });
}

// ============================================================================
// HOOKS - INSURANCE
// ============================================================================

export function useAssetInsurances(assetId?: string) {
  return useQuery({
    queryKey: [...assetsKeys.insurance(), assetId],
    queryFn: async () => {
      const params = assetId ? `?asset_id=${assetId}` : '';
      const response = await api.get<{ items: AssetInsurance[] }>(`/assets/insurance${params}`);
      return response;
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useAssetStats() {
  return useQuery({
    queryKey: assetsKeys.stats(),
    queryFn: async () => {
      const response = await api.get<AssetStats>('/assets/stats');
      return response;
    },
  });
}
