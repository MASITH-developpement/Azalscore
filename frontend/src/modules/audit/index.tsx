/**
 * AZALSCORE Module - Audit & Benchmark
 * Logs d'audit, sessions, metriques, benchmarks, conformite
 *
 * Structure:
 * - types.ts: Types et configurations
 * - hooks.ts: React Query hooks
 * - components/: Composants UI
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  AuditDashboard,
  LogsPage,
  LogDetailPage,
  SessionsPage,
  BenchmarksPage,
  CompliancePage,
  PlaceholderPage,
} from './components';

// Re-exports
export * from './types';
export * from './hooks';
export * from './components';

// ============================================================================
// MODULE ROUTES
// ============================================================================

export const AuditRoutes: React.FC = () => (
  <Routes>
    <Route index element={<AuditDashboard />} />
    <Route path="logs" element={<LogsPage />} />
    <Route path="logs/:id" element={<LogDetailPage />} />
    <Route path="sessions" element={<SessionsPage />} />
    <Route path="metrics" element={<PlaceholderPage title="Metriques" />} />
    <Route path="metrics/:code" element={<PlaceholderPage title="Detail Metrique" />} />
    <Route path="benchmarks" element={<BenchmarksPage />} />
    <Route path="benchmarks/new" element={<PlaceholderPage title="Nouveau Benchmark" />} />
    <Route path="benchmarks/:id" element={<PlaceholderPage title="Detail Benchmark" />} />
    <Route path="compliance" element={<CompliancePage />} />
    <Route path="compliance/new" element={<PlaceholderPage title="Nouveau Controle" />} />
    <Route path="retention" element={<PlaceholderPage title="Regles de Retention" />} />
    <Route path="exports" element={<PlaceholderPage title="Exports" />} />
  </Routes>
);

export default AuditRoutes;
