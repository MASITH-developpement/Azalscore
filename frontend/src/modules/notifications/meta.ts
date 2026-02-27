/**
 * AZALSCORE Module - NOTIFICATIONS - Metadata
 * ============================================
 * Metadonnees du module Notifications
 */

export const meta = {
  id: 'notifications',
  name: 'Notifications',
  description: 'Gestion des notifications multicanal (email, SMS, push, in-app)',
  version: '1.0.0',
  category: 'communication',
  icon: 'Bell',
  color: '#F59E0B',

  // Navigation
  routes: [
    {
      path: '/notifications',
      label: 'Notifications',
      icon: 'Bell',
    },
    {
      path: '/notifications/preferences',
      label: 'Preferences',
      icon: 'Settings',
    },
    {
      path: '/notifications/templates',
      label: 'Templates',
      icon: 'FileText',
      capability: 'notifications:templates:read',
    },
  ],

  // Capabilities
  capabilities: [
    'notifications:read',
    'notifications:create',
    'notifications:delete',
    'notifications:preferences:read',
    'notifications:preferences:write',
    'notifications:templates:read',
    'notifications:templates:write',
    'notifications:templates:delete',
  ],

  // Dependencies
  dependencies: [],

  // Status
  status: 'active',
  certification: 'B',
};

export default meta;
