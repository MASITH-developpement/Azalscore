/**
 * AZALSCORE Module - E-commerce - Types
 * Types, constantes et helpers pour le module e-commerce
 */

// ============================================================================
// TYPES PRINCIPAUX
// ============================================================================

export interface Product {
  id: string;
  sku: string;
  name: string;
  description?: string;
  price: number;
  compare_price?: number;
  cost?: number;
  stock: number;
  reserved_stock?: number;
  min_stock?: number;
  max_stock?: number;
  status: ProductStatus;
  category_id?: string;
  category_name?: string;
  currency: string;
  image_url?: string;
  images?: string[];
  weight?: number;
  dimensions?: { length: number; width: number; height: number };
  is_featured: boolean;
  is_taxable: boolean;
  tax_rate?: number;
  barcode?: string;
  supplier_id?: string;
  supplier_name?: string;
  tags?: string[];
  attributes?: Record<string, string>;
  seo_title?: string;
  seo_description?: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  // Computed
  total_sales?: number;
  total_revenue?: number;
  views_count?: number;
  conversion_rate?: number;
  history?: ProductHistoryEntry[];
  documents?: ProductDocument[];
}

export type ProductStatus = 'ACTIVE' | 'DRAFT' | 'ARCHIVED' | 'OUT_OF_STOCK';

export interface Order {
  id: string;
  number: string;
  customer_id?: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  shipping_address?: string;
  shipping_city?: string;
  shipping_postal_code?: string;
  shipping_country?: string;
  billing_address?: string;
  billing_city?: string;
  billing_postal_code?: string;
  billing_country?: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  payment_method?: string;
  payment_reference?: string;
  subtotal: number;
  discount: number;
  discount_code?: string;
  shipping_cost: number;
  shipping_method?: string;
  tax: number;
  total: number;
  currency: string;
  items: OrderItem[];
  tracking_number?: string;
  carrier?: string;
  shipped_at?: string;
  delivered_at?: string;
  notes?: string;
  internal_notes?: string;
  source?: 'WEB' | 'MOBILE' | 'API' | 'MANUAL';
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  // Computed
  history?: OrderHistoryEntry[];
  documents?: OrderDocument[];
}

export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'REFUNDED';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED' | 'PARTIAL';

export interface OrderItem {
  id?: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax: number;
  total: number;
  variant?: string;
  notes?: string;
}

export interface Category {
  id: string;
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  parent_name?: string;
  image_url?: string;
  products_count: number;
  is_active: boolean;
  position: number;
  seo_title?: string;
  seo_description?: string;
  created_at: string;
}

export interface Shipping {
  id: string;
  order_id: string;
  order_number: string;
  carrier: string;
  tracking_number: string;
  tracking_url?: string;
  status: ShippingStatus;
  weight?: number;
  estimated_delivery?: string;
  shipped_at?: string;
  delivered_at?: string;
  delivery_notes?: string;
  signature_required: boolean;
  signature_url?: string;
}

export type ShippingStatus = 'PENDING' | 'PICKED_UP' | 'IN_TRANSIT' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'FAILED' | 'RETURNED';

// ============================================================================
// TYPES HISTORIQUE
// ============================================================================

export interface ProductHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  field?: string;
  old_value?: string;
  new_value?: string;
}

export interface OrderHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_status?: string;
  new_status?: string;
}

export interface ProductDocument {
  id: string;
  name: string;
  type: string;
  url: string;
  size: number;
  uploaded_at: string;
  uploaded_by?: string;
}

export interface OrderDocument {
  id: string;
  name: string;
  type: 'INVOICE' | 'DELIVERY_NOTE' | 'RETURN_LABEL' | 'OTHER';
  url: string;
  size: number;
  created_at: string;
}

// ============================================================================
// CONSTANTES DE CONFIGURATION
// ============================================================================

export const PRODUCT_STATUS_CONFIG: Record<ProductStatus, { label: string; color: string }> = {
  ACTIVE: { label: 'Actif', color: 'green' },
  DRAFT: { label: 'Brouillon', color: 'orange' },
  ARCHIVED: { label: 'Archive', color: 'gray' },
  OUT_OF_STOCK: { label: 'Rupture', color: 'red' }
};

export const ORDER_STATUS_CONFIG: Record<OrderStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  CONFIRMED: { label: 'Confirmee', color: 'blue' },
  PROCESSING: { label: 'En preparation', color: 'blue' },
  SHIPPED: { label: 'Expediee', color: 'purple' },
  DELIVERED: { label: 'Livree', color: 'green' },
  CANCELLED: { label: 'Annulee', color: 'red' },
  REFUNDED: { label: 'Remboursee', color: 'gray' }
};

export const PAYMENT_STATUS_CONFIG: Record<PaymentStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  PAID: { label: 'Paye', color: 'green' },
  FAILED: { label: 'Echoue', color: 'red' },
  REFUNDED: { label: 'Rembourse', color: 'gray' },
  PARTIAL: { label: 'Partiel', color: 'blue' }
};

export const SHIPPING_STATUS_CONFIG: Record<ShippingStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  PICKED_UP: { label: 'Enleve', color: 'blue' },
  IN_TRANSIT: { label: 'En transit', color: 'purple' },
  OUT_FOR_DELIVERY: { label: 'En livraison', color: 'cyan' },
  DELIVERED: { label: 'Livre', color: 'green' },
  FAILED: { label: 'Echec', color: 'red' },
  RETURNED: { label: 'Retourne', color: 'gray' }
};

export const ORDER_SOURCES = [
  { value: 'WEB', label: 'Site web' },
  { value: 'MOBILE', label: 'Application mobile' },
  { value: 'API', label: 'API' },
  { value: 'MANUAL', label: 'Saisie manuelle' }
];

export const PAYMENT_METHODS = [
  { value: 'CARD', label: 'Carte bancaire' },
  { value: 'PAYPAL', label: 'PayPal' },
  { value: 'BANK_TRANSFER', label: 'Virement' },
  { value: 'CASH', label: 'Especes' },
  { value: 'CHECK', label: 'Cheque' }
];

export const CARRIERS = [
  { value: 'COLISSIMO', label: 'Colissimo' },
  { value: 'CHRONOPOST', label: 'Chronopost' },
  { value: 'UPS', label: 'UPS' },
  { value: 'FEDEX', label: 'FedEx' },
  { value: 'DHL', label: 'DHL' },
  { value: 'MONDIAL_RELAY', label: 'Mondial Relay' },
  { value: 'OTHER', label: 'Autre' }
];

// ============================================================================
// HELPERS FORMATAGE
// ============================================================================

export const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

export const formatDate = (date?: string): string => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
};

export const formatDateTime = (date?: string): string => {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
};

export const formatWeight = (weight?: number): string => {
  if (!weight) return '-';
  if (weight >= 1000) {
    return `${(weight / 1000).toFixed(2)} kg`;
  }
  return `${weight} g`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
};

// ============================================================================
// HELPERS CALCULS
// ============================================================================

export const calculateOrderSubtotal = (items: OrderItem[]): number => {
  return items.reduce((sum, item) => sum + item.unit_price * item.quantity, 0);
};

export const calculateOrderDiscount = (items: OrderItem[]): number => {
  return items.reduce((sum, item) => sum + item.discount, 0);
};

export const calculateOrderTax = (items: OrderItem[]): number => {
  return items.reduce((sum, item) => sum + item.tax, 0);
};

export const calculateOrderTotal = (order: Order): number => {
  return order.subtotal - order.discount + order.shipping_cost + order.tax;
};

export const calculateMargin = (price: number, cost?: number): number => {
  if (!cost || cost === 0) return 0;
  return ((price - cost) / price) * 100;
};

export const calculateMarkup = (price: number, cost?: number): number => {
  if (!cost || cost === 0) return 0;
  return ((price - cost) / cost) * 100;
};

// ============================================================================
// HELPERS STATUT
// ============================================================================

export const isProductAvailable = (product: Product): boolean => {
  return product.status === 'ACTIVE' && product.stock > 0;
};

export const isLowStock = (product: Product): boolean => {
  if (!product.min_stock) return false;
  return product.stock <= product.min_stock;
};

export const isOutOfStock = (product: Product): boolean => {
  return product.stock <= 0;
};

export const canShipOrder = (order: Order): boolean => {
  return order.status === 'PROCESSING' && order.payment_status === 'PAID';
};

export const canCancelOrder = (order: Order): boolean => {
  return ['PENDING', 'CONFIRMED', 'PROCESSING'].includes(order.status);
};

export const canRefundOrder = (order: Order): boolean => {
  return ['DELIVERED', 'SHIPPED'].includes(order.status) && order.payment_status === 'PAID';
};

export const getAvailableStock = (product: Product): number => {
  return product.stock - (product.reserved_stock || 0);
};

export const getNextOrderStatus = (currentStatus: OrderStatus): OrderStatus | null => {
  const flow: Record<OrderStatus, OrderStatus | null> = {
    PENDING: 'CONFIRMED',
    CONFIRMED: 'PROCESSING',
    PROCESSING: 'SHIPPED',
    SHIPPED: 'DELIVERED',
    DELIVERED: null,
    CANCELLED: null,
    REFUNDED: null
  };
  return flow[currentStatus];
};

// ============================================================================
// HELPERS ANALYTICS
// ============================================================================

export const getConversionRate = (product: Product): string => {
  if (!product.views_count || product.views_count === 0) return '-';
  const rate = ((product.total_sales || 0) / product.views_count) * 100;
  return `${rate.toFixed(1)}%`;
};

export const getAverageOrderValue = (orders: Order[]): number => {
  if (orders.length === 0) return 0;
  const total = orders.reduce((sum, order) => sum + order.total, 0);
  return total / orders.length;
};
