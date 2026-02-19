/**
 * AZALSCORE - E-Commerce API
 * ===========================
 * Client API typé pour la plateforme e-commerce
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const str = query.toString();
  return str ? `?${str}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type ProductType = 'PHYSICAL' | 'DIGITAL' | 'SERVICE' | 'BUNDLE';
export type ProductStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';
export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'REFUNDED';
export type PaymentStatus = 'PENDING' | 'PROCESSING' | 'PAID' | 'FAILED' | 'REFUNDED' | 'CANCELLED';
export type ShippingStatus = 'PENDING' | 'SHIPPED' | 'IN_TRANSIT' | 'DELIVERED' | 'RETURNED';
export type DiscountType = 'PERCENTAGE' | 'FIXED_AMOUNT' | 'FREE_SHIPPING';
export type CartStatus = 'ACTIVE' | 'CONVERTED' | 'ABANDONED';

// ============================================================================
// TYPES - Categories
// ============================================================================

export interface Category {
  id: number;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
  meta_title: string | null;
  meta_description: string | null;
  image_url: string | null;
  sort_order: number;
  is_visible: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  slug: string;
  description?: string | null;
  parent_id?: number | null;
  meta_title?: string | null;
  meta_description?: string | null;
  image_url?: string | null;
  sort_order?: number;
  is_visible?: boolean;
  is_featured?: boolean;
}

export type CategoryUpdate = Partial<CategoryCreate>;

// ============================================================================
// TYPES - Products
// ============================================================================

export interface ProductImage {
  url: string;
  alt?: string | null;
  position?: number;
}

export interface Product {
  id: number;
  tenant_id: string;
  sku: string;
  name: string;
  slug: string;
  barcode: string | null;
  short_description: string | null;
  description: string | null;
  product_type: ProductType;
  status: ProductStatus;
  price: number;
  compare_at_price: number | null;
  cost_price: number | null;
  currency: string;
  tax_class: string;
  is_taxable: boolean;
  track_inventory: boolean;
  stock_quantity: number;
  low_stock_threshold: number;
  allow_backorder: boolean;
  weight: number | null;
  length: number | null;
  width: number | null;
  height: number | null;
  meta_title: string | null;
  meta_description: string | null;
  images: ProductImage[];
  attributes: Record<string, unknown> | null;
  category_ids: number[];
  tags: string[];
  is_visible: boolean;
  is_featured: boolean;
  view_count: number;
  sale_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  sku: string;
  name: string;
  slug: string;
  barcode?: string | null;
  short_description?: string | null;
  description?: string | null;
  product_type?: ProductType;
  price: number;
  compare_at_price?: number | null;
  cost_price?: number | null;
  currency?: string;
  tax_class?: string;
  is_taxable?: boolean;
  track_inventory?: boolean;
  stock_quantity?: number;
  low_stock_threshold?: number;
  allow_backorder?: boolean;
  weight?: number | null;
  images?: ProductImage[];
  category_ids?: number[];
  tags?: string[];
  is_visible?: boolean;
  is_featured?: boolean;
}

export interface ProductUpdate extends Partial<ProductCreate> {
  status?: ProductStatus;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ============================================================================
// TYPES - Variants
// ============================================================================

export interface Variant {
  id: number;
  product_id: number;
  sku: string;
  name: string | null;
  options: Record<string, string>;
  price: number | null;
  compare_at_price: number | null;
  stock_quantity: number;
  weight: number | null;
  image_url: string | null;
  position: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface VariantCreate {
  product_id: number;
  sku: string;
  name?: string | null;
  options?: Record<string, string>;
  price?: number | null;
  stock_quantity?: number;
  is_default?: boolean;
}

export type VariantUpdate = Partial<Omit<VariantCreate, 'product_id'>>;

// ============================================================================
// TYPES - Cart
// ============================================================================

export interface CartItem {
  id: number;
  product_id: number;
  variant_id: number | null;
  product_name: string;
  variant_name: string | null;
  sku: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  image_url: string | null;
}

export interface Cart {
  id: number;
  session_id: string;
  customer_id: number | null;
  status: CartStatus;
  items: CartItem[];
  items_count: number;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  coupon_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface CartItemAdd {
  product_id: number;
  variant_id?: number | null;
  quantity: number;
}

export interface CartItemUpdate {
  quantity: number;
}

// ============================================================================
// TYPES - Orders
// ============================================================================

export interface OrderItem {
  id: number;
  product_id: number;
  variant_id: number | null;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  total: number;
}

export interface OrderAddress {
  first_name: string;
  last_name: string;
  company?: string | null;
  address1: string;
  address2?: string | null;
  city: string;
  postal_code: string;
  country: string;
  phone?: string | null;
}

export interface Order {
  id: number;
  tenant_id: string;
  order_number: string;
  customer_id: number | null;
  customer_email: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  shipping_status: ShippingStatus;
  items: OrderItem[];
  billing_address: OrderAddress;
  shipping_address: OrderAddress;
  shipping_method: string | null;
  shipping_cost: number;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  coupon_code: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CheckoutRequest {
  cart_id: number;
  customer_email: string;
  billing_address: OrderAddress;
  shipping_address: OrderAddress;
  shipping_method_id: number;
  payment_method: string;
  notes?: string | null;
}

// ============================================================================
// TYPES - Coupons
// ============================================================================

export interface Coupon {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  discount_type: DiscountType;
  discount_value: number;
  minimum_order_amount: number | null;
  maximum_discount_amount: number | null;
  usage_limit: number | null;
  usage_count: number;
  valid_from: string;
  valid_until: string | null;
  is_active: boolean;
  product_ids: number[];
  category_ids: number[];
  created_at: string;
}

export interface CouponCreate {
  code: string;
  name: string;
  description?: string | null;
  discount_type: DiscountType;
  discount_value: number;
  minimum_order_amount?: number | null;
  usage_limit?: number | null;
  valid_from: string;
  valid_until?: string | null;
  is_active?: boolean;
  product_ids?: number[];
  category_ids?: number[];
}

export type CouponUpdate = Partial<CouponCreate>;

export interface CouponValidateResponse {
  is_valid: boolean;
  coupon: Coupon | null;
  discount_amount: number;
  message: string;
}

// ============================================================================
// TYPES - Customers
// ============================================================================

export interface Customer {
  id: number;
  tenant_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  is_verified: boolean;
  total_orders: number;
  total_spent: number;
  created_at: string;
}

export interface CustomerAddress {
  id: number;
  customer_id: number;
  address_type: 'BILLING' | 'SHIPPING';
  is_default: boolean;
  first_name: string;
  last_name: string;
  address1: string;
  city: string;
  postal_code: string;
  country: string;
}

// ============================================================================
// TYPES - Shipping
// ============================================================================

export interface ShippingMethod {
  id: number;
  tenant_id: string;
  name: string;
  description: string | null;
  carrier: string | null;
  base_rate: number;
  free_shipping_threshold: number | null;
  estimated_days_min: number;
  estimated_days_max: number;
  is_active: boolean;
}

export interface ShippingRate {
  method_id: number;
  method_name: string;
  carrier: string | null;
  rate: number;
  estimated_days_min: number;
  estimated_days_max: number;
}

// ============================================================================
// TYPES - Reviews
// ============================================================================

export interface Review {
  id: number;
  product_id: number;
  customer_id: number;
  customer_name: string;
  rating: number;
  title: string | null;
  content: string | null;
  is_approved: boolean;
  created_at: string;
}

export interface ReviewCreate {
  product_id: number;
  rating: number;
  title?: string | null;
  content?: string | null;
}

// ============================================================================
// TYPES - Wishlist
// ============================================================================

export interface WishlistItem {
  id: number;
  product_id: number;
  product_name: string;
  product_price: number;
  product_image: string | null;
  in_stock: boolean;
  added_at: string;
}

export interface Wishlist {
  id: number;
  customer_id: number;
  items: WishlistItem[];
  items_count: number;
}

// ============================================================================
// TYPES - Dashboard
// ============================================================================

export interface EcommerceDashboard {
  total_revenue: number;
  orders_count: number;
  average_order_value: number;
  products_count: number;
  customers_count: number;
  conversion_rate: number;
  pending_orders: number;
  low_stock_products: number;
  recent_orders: Order[];
  top_products: Array<{
    product_id: number;
    product_name: string;
    quantity_sold: number;
    revenue: number;
  }>;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/ecommerce';

export const ecommerceApi = {
  // Dashboard
  getDashboard: () =>
    api.get<EcommerceDashboard>(`${BASE_PATH}/dashboard`),

  // Categories
  listCategories: (params?: { visible_only?: boolean; parent_id?: number }) =>
    api.get<Category[]>(`${BASE_PATH}/categories${qs(params || {})}`),

  getCategory: (id: number) =>
    api.get<Category>(`${BASE_PATH}/categories/${id}`),

  createCategory: (data: CategoryCreate) =>
    api.post<Category>(`${BASE_PATH}/categories`, data),

  updateCategory: (id: number, data: CategoryUpdate) =>
    api.patch<Category>(`${BASE_PATH}/categories/${id}`, data),

  deleteCategory: (id: number) =>
    api.delete(`${BASE_PATH}/categories/${id}`),

  // Products
  listProducts: (params?: {
    page?: number;
    page_size?: number;
    category_id?: number;
    status?: ProductStatus;
    search?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }) =>
    api.get<ProductListResponse>(`${BASE_PATH}/products${qs(params || {})}`),

  getProduct: (id: number) =>
    api.get<Product>(`${BASE_PATH}/products/${id}`),

  getProductBySlug: (slug: string) =>
    api.get<Product>(`${BASE_PATH}/products/slug/${slug}`),

  createProduct: (data: ProductCreate) =>
    api.post<Product>(`${BASE_PATH}/products`, data),

  updateProduct: (id: number, data: ProductUpdate) =>
    api.patch<Product>(`${BASE_PATH}/products/${id}`, data),

  deleteProduct: (id: number) =>
    api.delete(`${BASE_PATH}/products/${id}`),

  // Variants
  listVariants: (productId: number) =>
    api.get<Variant[]>(`${BASE_PATH}/products/${productId}/variants`),

  createVariant: (data: VariantCreate) =>
    api.post<Variant>(`${BASE_PATH}/variants`, data),

  updateVariant: (id: number, data: VariantUpdate) =>
    api.patch<Variant>(`${BASE_PATH}/variants/${id}`, data),

  deleteVariant: (id: number) =>
    api.delete(`${BASE_PATH}/variants/${id}`),

  // Cart
  getCart: (sessionId: string) =>
    api.get<Cart>(`${BASE_PATH}/cart/${sessionId}`),

  addToCart: (sessionId: string, data: CartItemAdd) =>
    api.post<Cart>(`${BASE_PATH}/cart/${sessionId}/items`, data),

  updateCartItem: (sessionId: string, itemId: number, data: CartItemUpdate) =>
    api.patch<Cart>(`${BASE_PATH}/cart/${sessionId}/items/${itemId}`, data),

  removeCartItem: (sessionId: string, itemId: number) =>
    api.delete<Cart>(`${BASE_PATH}/cart/${sessionId}/items/${itemId}`),

  clearCart: (sessionId: string) =>
    api.delete<Cart>(`${BASE_PATH}/cart/${sessionId}`),

  applyCoupon: (sessionId: string, couponCode: string) =>
    api.post<Cart>(`${BASE_PATH}/cart/${sessionId}/coupon`, { coupon_code: couponCode }),

  removeCoupon: (sessionId: string) =>
    api.delete<Cart>(`${BASE_PATH}/cart/${sessionId}/coupon`),

  // Orders
  listOrders: (params?: {
    page?: number;
    page_size?: number;
    status?: OrderStatus;
    customer_id?: number;
    date_from?: string;
    date_to?: string;
  }) =>
    api.get<OrderListResponse>(`${BASE_PATH}/orders${qs(params || {})}`),

  getOrder: (id: number) =>
    api.get<Order>(`${BASE_PATH}/orders/${id}`),

  getOrderByNumber: (orderNumber: string) =>
    api.get<Order>(`${BASE_PATH}/orders/number/${orderNumber}`),

  checkout: (data: CheckoutRequest) =>
    api.post<Order>(`${BASE_PATH}/checkout`, data),

  updateOrderStatus: (id: number, status: OrderStatus) =>
    api.patch<Order>(`${BASE_PATH}/orders/${id}/status`, { status }),

  cancelOrder: (id: number, reason?: string) =>
    api.post<Order>(`${BASE_PATH}/orders/${id}/cancel`, { reason }),

  refundOrder: (id: number, amount?: number, reason?: string) =>
    api.post<Order>(`${BASE_PATH}/orders/${id}/refund`, { amount, reason }),

  // Coupons
  listCoupons: (params?: { active_only?: boolean }) =>
    api.get<Coupon[]>(`${BASE_PATH}/coupons${qs(params || {})}`),

  getCoupon: (id: number) =>
    api.get<Coupon>(`${BASE_PATH}/coupons/${id}`),

  createCoupon: (data: CouponCreate) =>
    api.post<Coupon>(`${BASE_PATH}/coupons`, data),

  updateCoupon: (id: number, data: CouponUpdate) =>
    api.patch<Coupon>(`${BASE_PATH}/coupons/${id}`, data),

  deleteCoupon: (id: number) =>
    api.delete(`${BASE_PATH}/coupons/${id}`),

  validateCoupon: (code: string, cartTotal: number) =>
    api.post<CouponValidateResponse>(`${BASE_PATH}/coupons/validate`, { code, cart_total: cartTotal }),

  // Customers
  listCustomers: (params?: { page?: number; page_size?: number; search?: string }) =>
    api.get<{ items: Customer[]; total: number }>(`${BASE_PATH}/customers${qs(params || {})}`),

  getCustomer: (id: number) =>
    api.get<Customer>(`${BASE_PATH}/customers/${id}`),

  getCustomerAddresses: (customerId: number) =>
    api.get<CustomerAddress[]>(`${BASE_PATH}/customers/${customerId}/addresses`),

  // Shipping
  listShippingMethods: () =>
    api.get<ShippingMethod[]>(`${BASE_PATH}/shipping/methods`),

  calculateShippingRates: (data: { items: Array<{ product_id: number; quantity: number; weight: number }>; destination: { country: string; postal_code: string } }) =>
    api.post<ShippingRate[]>(`${BASE_PATH}/shipping/rates`, data),

  // Reviews
  listProductReviews: (productId: number, params?: { approved_only?: boolean }) =>
    api.get<Review[]>(`${BASE_PATH}/products/${productId}/reviews${qs(params || {})}`),

  createReview: (data: ReviewCreate) =>
    api.post<Review>(`${BASE_PATH}/reviews`, data),

  approveReview: (id: number) =>
    api.post<Review>(`${BASE_PATH}/reviews/${id}/approve`),

  deleteReview: (id: number) =>
    api.delete(`${BASE_PATH}/reviews/${id}`),

  // Wishlist
  getWishlist: (customerId: number) =>
    api.get<Wishlist>(`${BASE_PATH}/wishlist/${customerId}`),

  addToWishlist: (customerId: number, productId: number) =>
    api.post<Wishlist>(`${BASE_PATH}/wishlist/${customerId}`, { product_id: productId }),

  removeFromWishlist: (customerId: number, productId: number) =>
    api.delete<Wishlist>(`${BASE_PATH}/wishlist/${customerId}/${productId}`),
};

export default ecommerceApi;
