/**
 * AZALS MODULE GAP-086 - Integration Hub - Status Badges
 * Badges de statut et icones de categories
 */

import React from 'react';
import {
  Plug, FileText, Mail, Users, Building2,
  Database, ShoppingCart, CreditCard, Cloud, Server
} from 'lucide-react';
import type { ConnectionStatus, HealthStatus, SyncStatus } from '../types';
import { CONNECTION_STATUS_COLORS, HEALTH_STATUS_COLORS, SYNC_STATUS_COLORS } from '../types';

// ============================================================================
// BADGE COMPONENTS
// ============================================================================

export const ConnectionStatusBadge: React.FC<{ status: ConnectionStatus }> = ({ status }) => {
  const color = CONNECTION_STATUS_COLORS[status] || 'gray';
  const labels: Record<ConnectionStatus, string> = {
    pending: 'En attente',
    configuring: 'Configuration',
    connected: 'Connecte',
    disconnected: 'Deconnecte',
    error: 'Erreur',
    expired: 'Expire',
    rate_limited: 'Limite atteinte',
    maintenance: 'Maintenance',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

export const HealthStatusBadge: React.FC<{ status: HealthStatus }> = ({ status }) => {
  const color = HEALTH_STATUS_COLORS[status] || 'gray';
  const labels: Record<HealthStatus, string> = {
    healthy: 'Sain',
    degraded: 'Degrade',
    unhealthy: 'Non sain',
    unknown: 'Inconnu',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

export const SyncStatusBadge: React.FC<{ status: SyncStatus }> = ({ status }) => {
  const color = SYNC_STATUS_COLORS[status] || 'gray';
  const labels: Record<SyncStatus, string> = {
    pending: 'En attente',
    queued: 'En file',
    running: 'En cours',
    completed: 'Termine',
    partial: 'Partiel',
    failed: 'Echec',
    cancelled: 'Annule',
    timeout: 'Timeout',
    retrying: 'Nouvelle tentative',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

// ============================================================================
// HELPERS
// ============================================================================

export const getCategoryIcon = (category: string): React.ReactNode => {
  const icons: Record<string, React.ReactNode> = {
    productivity: <FileText size={20} />,
    communication: <Mail size={20} />,
    crm: <Users size={20} />,
    accounting: <Building2 size={20} />,
    erp: <Database size={20} />,
    ecommerce: <ShoppingCart size={20} />,
    payment: <CreditCard size={20} />,
    banking: <Building2 size={20} />,
    marketing: <Mail size={20} />,
    storage: <Cloud size={20} />,
    custom: <Server size={20} />,
  };
  return icons[category] || <Plug size={20} />;
};
