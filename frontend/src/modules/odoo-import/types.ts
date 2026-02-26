/**
 * AZALSCORE - Types Module Odoo Import
 * Conformité AZA-FE-META
 */

// ============================================================
// STATUS & ENUMS
// ============================================================

export type ItemStatus = 'draft' | 'active' | 'archived';

export const STATUS_CONFIG: Record<ItemStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  active: { label: 'Actif', color: 'green' },
  archived: { label: 'Archivé', color: 'gray' },
};

// ============================================================
// MAIN TYPES
// ============================================================

export interface Item {
  id: string;
  name: string;
  status: ItemStatus;
  created_at: string;
  updated_at: string;
}

// ============================================================
// API TYPES
// ============================================================

export interface ItemsResponse {
  items: Item[];
  total: number;
}

export interface ItemCreateInput {
  name: string;
}

export interface ItemUpdateInput {
  name?: string;
  status?: ItemStatus;
}

// ============================================================
// UTILITIES
// ============================================================

export function getStatusLabel(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.label || status;
}

export function getStatusColor(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.color || 'gray';
}
