/**
 * AZALSCORE Module - Automated Accounting Meta
 * Metadonnees du module de comptabilite automatisee (M2A)
 */

import type { ModuleMeta } from '@/core/types';

export const automatedAccountingMeta: ModuleMeta = {
  id: 'automated-accounting',
  name: 'Compta Auto',
  description: 'Comptabilite automatisee avec OCR, IA et synchronisation bancaire',
  icon: 'Sparkles',
  route: '/automated-accounting',
  category: 'finance',
  permissions: ['m2a:read', 'm2a:write', 'm2a:admin'],
  features: [
    'ocr',              // OCR documents
    'ai-classification', // Classification IA
    'bank-sync',        // Synchronisation bancaire
    'reconciliation',   // Rapprochement automatique
    'auto-entries',     // Ecritures automatiques
    'alerts',           // Alertes intelligentes
  ],
  navigation: [
    {
      label: 'Tableau de bord',
      path: '/automated-accounting',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Documents',
      path: '/automated-accounting/documents',
      icon: 'FileText',
    },
    {
      label: 'Banque',
      path: '/automated-accounting/bank',
      icon: 'Landmark',
    },
    {
      label: 'Rapprochement',
      path: '/automated-accounting/reconciliation',
      icon: 'GitMerge',
    },
    {
      label: 'Alertes',
      path: '/automated-accounting/alerts',
      icon: 'Bell',
    },
    {
      label: 'Regles',
      path: '/automated-accounting/rules',
      icon: 'Settings',
    },
  ],
  stats: [
    { key: 'documents_pending', label: 'A traiter', icon: 'FileText' },
    { key: 'unreconciled', label: 'A rapprocher', icon: 'GitMerge' },
    { key: 'alerts_unread', label: 'Alertes', icon: 'Bell' },
    { key: 'confidence_avg', label: 'Confiance IA', icon: 'Sparkles' },
  ],
};

export default automatedAccountingMeta;
