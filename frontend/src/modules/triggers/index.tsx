/**
 * AZALSCORE Module - Triggers & Diffusion
 * Gestion des declencheurs, alertes, notifications et rapports planifies
 * Donnees fournies par API - AUCUNE logique metier
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';

import {
  TriggersDashboard,
  TriggersListPage,
  TriggerDetailPage,
  EventsPage,
  NotificationsPage,
  TemplatesPage,
  ScheduledReportsPage,
  WebhooksPage,
  LogsPage,
  PlaceholderPage,
} from './components';

// Re-export types
export * from './types';

// Re-export hooks
export * from './hooks';

// Re-export components
export * from './components';

// ============================================================
// MODULE ROUTES
// ============================================================

export const TriggersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<TriggersDashboard />} />
    <Route path="list" element={<TriggersListPage />} />
    <Route path="new" element={<PlaceholderPage title="Nouveau Trigger" />} />
    <Route path=":id" element={<TriggerDetailPage />} />
    <Route path=":id/edit" element={<PlaceholderPage title="Modifier Trigger" />} />
    <Route path="events" element={<EventsPage />} />
    <Route path="notifications" element={<NotificationsPage />} />
    <Route path="templates" element={<TemplatesPage />} />
    <Route path="templates/new" element={<PlaceholderPage title="Nouveau Template" />} />
    <Route path="reports" element={<ScheduledReportsPage />} />
    <Route path="reports/new" element={<PlaceholderPage title="Nouveau Rapport" />} />
    <Route path="webhooks" element={<WebhooksPage />} />
    <Route path="webhooks/new" element={<PlaceholderPage title="Nouveau Webhook" />} />
    <Route path="subscriptions" element={<PlaceholderPage title="Abonnements" />} />
    <Route path="logs" element={<LogsPage />} />
  </Routes>
);

export default TriggersRoutes;
