/**
 * AZALSCORE - Design Tokens (JS)
 * ===============================
 *
 * Source unique pour les couleurs utilisees en JSX/props.
 * Les CSS variables (--azals-primary-*) restent la reference principale.
 * Ce fichier sert uniquement pour les cas ou var() CSS n'est pas utilisable
 * (ex: props de composants, SVG fill, canvas, etc.)
 *
 * CHARTE AZALSCORE:
 * - Primaire: #1E6EFF
 * - Fond sombre: #0E1420
 * - Blanc: #FFFFFF
 * - Police: Inter
 */

export const COLORS = {
  // Primaire (charte normative)
  primary: '#1E6EFF',
  primaryHover: '#1A5FDB',
  primaryDark: '#1650B8',
  primaryLight: '#DBEAFE',

  // Semantique
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#1E6EFF',

  // Modules (palette cockpit)
  crm: '#8b5cf6',
  devis: '#1E6EFF',
  commandes: '#10b981',
  ods: '#f59e0b',
  affaires: '#6366f1',
  factures: '#ec4899',

  // Neutres
  text: '#1a1d21',
  textMuted: '#6b7280',
  textLight: '#9ca3af',
  border: '#e2e5e9',
  bg: '#f5f6f8',
  surface: '#ffffff',
} as const;

export type ColorToken = keyof typeof COLORS;
