/**
 * AZALSCORE Module - Marketplace - Types
 * Types, constantes et helpers pour le module marketplace
 */

// ============================================================================
// TYPES PRINCIPAUX
// ============================================================================

export interface Seller {
  id: string;
  code: string;
  name: string;
  email: string;
  phone?: string;
  company_name?: string;
  siret?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  status: SellerStatus;
  commission_rate: number;
  products_count: number;
  orders_count?: number;
  total_sales: number;
  total_revenue: number;
  pending_payout?: number;
  rating?: number;
  reviews_count?: number;
  joined_at: string;
  is_verified: boolean;
  verified_at?: string;
  bank_iban?: string;
  bank_bic?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  products?: MarketplaceProduct[];
  orders?: MarketplaceOrder[];
  payouts?: Payout[];
  history?: SellerHistoryEntry[];
}

export type SellerStatus = 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'REJECTED';

export interface MarketplaceProduct {
  id: string;
  seller_id: string;
  seller_name: string;
  name: string;
  sku: string;
  description?: string;
  price: number;
  cost_price?: number;
  currency: string;
  stock: number;
  min_stock?: number;
  status: ProductStatus;
  category: string;
  images?: string[];
  weight?: number;
  dimensions?: string;
  created_at: string;
  updated_at: string;
}

export type ProductStatus = 'DRAFT' | 'PENDING' | 'ACTIVE' | 'REJECTED' | 'SUSPENDED';

export interface MarketplaceOrder {
  id: string;
  number: string;
  seller_id: string;
  seller_name: string;
  customer_name: string;
  customer_email?: string;
  status: OrderStatus;
  total: number;
  subtotal?: number;
  shipping_cost?: number;
  commission: number;
  commission_rate?: number;
  net_amount: number;
  currency: string;
  items?: MarketplaceOrderItem[];
  shipping_address?: string;
  tracking_number?: string;
  shipped_at?: string;
  delivered_at?: string;
  created_at: string;
  updated_at: string;
}

export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'DISPUTED';

export interface MarketplaceOrderItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Payout {
  id: string;
  seller_id: string;
  seller_name: string;
  amount: number;
  currency: string;
  status: PayoutStatus;
  period_start: string;
  period_end: string;
  orders_count?: number;
  gross_amount?: number;
  commission_amount?: number;
  reference?: string;
  bank_reference?: string;
  created_at: string;
  paid_at?: string;
  notes?: string;
}

export type PayoutStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface SellerHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_status?: string;
  new_status?: string;
}

export interface MarketplaceStats {
  total_sellers: number;
  active_sellers: number;
  pending_sellers: number;
  total_products: number;
  active_products: number;
  pending_products: number;
  orders_today: number;
  orders_this_month: number;
  revenue_today: number;
  revenue_this_month: number;
  commission_this_month: number;
  pending_payouts: number;
}

// ============================================================================
// CONFIGURATIONS DE STATUT
// ============================================================================

export const SELLER_STATUS_CONFIG: Record<SellerStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  ACTIVE: { label: 'Actif', color: 'green' },
  SUSPENDED: { label: 'Suspendu', color: 'red' },
  REJECTED: { label: 'Refuse', color: 'red' }
};

export const PRODUCT_STATUS_CONFIG: Record<ProductStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  PENDING: { label: 'En attente', color: 'orange' },
  ACTIVE: { label: 'Actif', color: 'green' },
  REJECTED: { label: 'Refuse', color: 'red' },
  SUSPENDED: { label: 'Suspendu', color: 'red' }
};

export const ORDER_STATUS_CONFIG: Record<OrderStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  CONFIRMED: { label: 'Confirmee', color: 'blue' },
  SHIPPED: { label: 'Expediee', color: 'purple' },
  DELIVERED: { label: 'Livree', color: 'green' },
  CANCELLED: { label: 'Annulee', color: 'red' },
  DISPUTED: { label: 'Litige', color: 'orange' }
};

export const PAYOUT_STATUS_CONFIG: Record<PayoutStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  PROCESSING: { label: 'En cours', color: 'blue' },
  COMPLETED: { label: 'Effectue', color: 'green' },
  FAILED: { label: 'Echoue', color: 'red' }
};

// ============================================================================
// HELPERS DE FORMATAGE
// ============================================================================

export const formatRating = (rating: number | undefined): string => {
  if (rating === undefined || rating === null) return '-';
  return `${rating.toFixed(1)}/5`;
};

// ============================================================================
// HELPERS METIER
// ============================================================================

export const isSellerActive = (seller: Seller): boolean => {
  return seller.status === 'ACTIVE';
};

export const isSellerPending = (seller: Seller): boolean => {
  return seller.status === 'PENDING';
};

export const canApproveSeller = (seller: Seller): boolean => {
  return seller.status === 'PENDING';
};

export const canSuspendSeller = (seller: Seller): boolean => {
  return seller.status === 'ACTIVE';
};

export const canReactivateSeller = (seller: Seller): boolean => {
  return seller.status === 'SUSPENDED';
};

export const getSellerCommissionAmount = (seller: Seller): number => {
  return seller.total_revenue * (seller.commission_rate / 100);
};

export const getSellerNetRevenue = (seller: Seller): number => {
  return seller.total_revenue - getSellerCommissionAmount(seller);
};

export const calculateOrderCommission = (order: MarketplaceOrder): number => {
  return order.commission_rate
    ? order.total * (order.commission_rate / 100)
    : order.commission;
};

export const isProductActive = (product: MarketplaceProduct): boolean => {
  return product.status === 'ACTIVE';
};

export const isProductLowStock = (product: MarketplaceProduct): boolean => {
  const threshold = product.min_stock || 5;
  return product.stock > 0 && product.stock <= threshold;
};

export const isProductOutOfStock = (product: MarketplaceProduct): boolean => {
  return product.stock <= 0;
};

export const canProcessPayout = (payout: Payout): boolean => {
  return payout.status === 'PENDING';
};

export const getNextSellerStatus = (status: SellerStatus): SellerStatus | null => {
  switch (status) {
    case 'PENDING':
      return 'ACTIVE';
    case 'SUSPENDED':
      return 'ACTIVE';
    default:
      return null;
  }
};
