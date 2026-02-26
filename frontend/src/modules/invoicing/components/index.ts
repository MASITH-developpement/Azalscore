/**
 * AZALSCORE Module - Invoicing - Components Index
 * Re-exports all components
 */

// Onglets de detail
export { InvoicingInfoTab } from './InvoicingInfoTab';
export { InvoicingLinesTab } from './InvoicingLinesTab';
export { InvoicingFinancialTab } from './InvoicingFinancialTab';
export { InvoicingDocumentsTab } from './InvoicingDocumentsTab';
export { InvoicingHistoryTab } from './InvoicingHistoryTab';
export { InvoicingIATab } from './InvoicingIATab';
export { InvoicingRiskTab } from './InvoicingRiskTab';

// Line Editor avec ProductAutocomplete
export { LineEditor } from './LineEditor';
export type { LineEditorProps } from './LineEditor';

// Composants UI
export { default as StatusBadge } from './StatusBadge';
export { default as FilterBar } from './FilterBar';
export { default as LinesEditor } from './LinesEditor';

// Pages
export { default as DocumentListPage } from './DocumentListPage';
export { default as DocumentFormPage } from './DocumentFormPage';
export { default as InvoicingDashboard } from './InvoicingDashboard';
export { default as InvoicingDetailView } from './InvoicingDetailView';
