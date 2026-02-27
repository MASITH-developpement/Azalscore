/**
 * AZALSCORE Module - Partenaires (Clients, Fournisseurs, Contacts)
 *
 * Structure:
 * - types.ts: Types, constantes et utilitaires
 * - hooks.ts: React Query hooks
 * - components/: Composants UI et pages
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  PartnersDashboard,
  ClientsPage,
  SuppliersPage,
  ContactsPage,
  ClientFormPage,
  ClientDetailView,
  SupplierDetailView,
  ContactDetailView
} from './components';

// Re-exports
export * from './types';
export * from './hooks';
export * from './components';

// ============================================================================
// MODULE ROUTES
// ============================================================================

export const PartnersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PartnersDashboard />} />
    <Route path="clients" element={<ClientsPage />} />
    <Route path="clients/new" element={<ClientFormPage />} />
    <Route path="clients/:id" element={<ClientDetailView />} />
    <Route path="clients/:id/edit" element={<ClientFormPage />} />
    <Route path="suppliers" element={<SuppliersPage />} />
    <Route path="suppliers/:id" element={<SupplierDetailView />} />
    <Route path="contacts" element={<ContactsPage />} />
    <Route path="contacts/:id" element={<ContactDetailView />} />
  </Routes>
);

export default PartnersRoutes;
