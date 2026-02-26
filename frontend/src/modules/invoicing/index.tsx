/**
 * AZALSCORE Module - Facturation (VENTES T0)
 * ===========================================
 *
 * Module complet de gestion des devis et factures.
 *
 * Fonctionnalites:
 * - Creation/modification de devis et factures
 * - Gestion des lignes de document
 * - Calculs automatiques HT/TVA/TTC
 * - Validation des documents (DRAFT -> VALIDATED)
 * - Conversion devis -> facture
 * - Export CSV
 * - Filtres et recherche
 *
 * Statuts T0: DRAFT (Brouillon), VALIDATED (Valide)
 * Types T0: QUOTE (Devis), INVOICE (Facture)
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  DocumentListPage,
  DocumentFormPage,
  InvoicingDashboard,
  InvoicingDetailView
} from './components';

// ============================================================
// PAGE COMPONENTS
// ============================================================

export const QuotesPage: React.FC = () => <DocumentListPage type="QUOTE" />;
export const OrdersPage: React.FC = () => <DocumentListPage type="ORDER" />;
export const InvoicesPage: React.FC = () => <DocumentListPage type="INVOICE" />;

export const QuoteFormPage: React.FC = () => <DocumentFormPage type="QUOTE" />;
export const OrderFormPage: React.FC = () => <DocumentFormPage type="ORDER" />;
export const InvoiceFormPage: React.FC = () => <DocumentFormPage type="INVOICE" />;

// BaseViewStandard detail views
export const QuoteDetailViewStandard: React.FC = () => <InvoicingDetailView type="QUOTE" />;
export const OrderDetailViewStandard: React.FC = () => <InvoicingDetailView type="ORDER" />;
export const InvoiceDetailViewStandard: React.FC = () => <InvoicingDetailView type="INVOICE" />;

// ============================================================
// ROUTER
// ============================================================

export const InvoicingRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InvoicingDashboard />} />

    <Route path="quotes" element={<QuotesPage />} />
    <Route path="quotes/new" element={<QuoteFormPage />} />
    <Route path="quotes/:id" element={<QuoteDetailViewStandard />} />
    <Route path="quotes/:id/edit" element={<QuoteFormPage />} />

    <Route path="orders" element={<OrdersPage />} />
    <Route path="orders/new" element={<OrderFormPage />} />
    <Route path="orders/:id" element={<OrderDetailViewStandard />} />
    <Route path="orders/:id/edit" element={<OrderFormPage />} />

    <Route path="invoices" element={<InvoicesPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailViewStandard />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
  </Routes>
);

export default InvoicingRoutes;
