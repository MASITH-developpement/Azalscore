/**
 * AZALSCORE Module - Purchases - Components Index
 * Re-exports all components
 */

// ============================================================================
// Shared Components
// ============================================================================

export { OrderStatusBadge, InvoiceStatusBadge, SupplierStatusBadge } from './StatusBadges';
export { LineEditor, type LineFormData } from './LineEditor';
export { FilterBar, type FilterState } from './FilterBar';

// ============================================================================
// Supplier Tabs
// ============================================================================

export { SupplierInfoTab } from './SupplierInfoTab';
export { SupplierOrdersTab } from './SupplierOrdersTab';
export { SupplierInvoicesTab } from './SupplierInvoicesTab';
export { SupplierDocumentsTab } from './SupplierDocumentsTab';
export { SupplierHistoryTab } from './SupplierHistoryTab';
export { SupplierRiskTab } from './SupplierRiskTab';
export { SupplierIATab } from './SupplierIATab';

// ============================================================================
// Order Tabs
// ============================================================================

export { OrderInfoTab } from './OrderInfoTab';
export { OrderLinesTab } from './OrderLinesTab';
export { OrderFinancialTab } from './OrderFinancialTab';
export { OrderDocumentsTab } from './OrderDocumentsTab';
export { OrderHistoryTab } from './OrderHistoryTab';
export { OrderIATab } from './OrderIATab';

// ============================================================================
// Invoice Tabs
// ============================================================================

export { InvoiceInfoTab } from './InvoiceInfoTab';
export { InvoiceLinesTab } from './InvoiceLinesTab';
export { InvoiceFinancialTab } from './InvoiceFinancialTab';
export { InvoiceDocumentsTab } from './InvoiceDocumentsTab';
export { InvoiceHistoryTab } from './InvoiceHistoryTab';
export { InvoiceIATab } from './InvoiceIATab';
