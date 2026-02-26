/**
 * AZALSCORE Module - Admin
 * ========================
 * Module d'administration du systeme
 *
 * Architecture modulaire refactorisee depuis un fichier monolithique (2,506 lignes)
 * vers une structure avec separation des responsabilites.
 *
 * Structure:
 * - types.ts: Types et interfaces
 * - hooks.ts: React Query hooks
 * - api.ts: Client API
 * - components/: Composants React
 *   - UsersView.tsx: Gestion des utilisateurs
 *   - RolesView.tsx: Gestion des roles
 *   - TenantsView.tsx: Gestion des tenants
 *   - AuditView.tsx: Journal d'audit
 *   - BackupsView.tsx: Sauvegardes
 *   - UserDetailView.tsx: Detail utilisateur
 *   - UsersPermissionsView.tsx: Permissions par utilisateur
 *   - UserPermissionsModal.tsx: Modal permissions
 *   - AdminDashboardView.tsx: Tableau de bord principal
 *   - UserInfoTab.tsx, UserPermissionsTab.tsx, etc.: Tabs utilisateur
 *   - SequencesView.tsx: Numerotation
 *   - EnrichmentProvidersView.tsx: Enrichissement
 *   - CSSCustomizationView.tsx: Apparence
 *
 * @module admin
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { UserDetailView, AdminDashboardView } from './components';

/**
 * Module Admin - Point d'entree
 * Gere le routing entre le dashboard et le detail utilisateur
 */
const AdminModule: React.FC = () => {
  return (
    <Routes>
      <Route path="users/:id" element={<UserDetailView />} />
      <Route path="*" element={<AdminDashboardView />} />
    </Routes>
  );
};

export default AdminModule;
