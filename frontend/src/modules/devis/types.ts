/**
 * AZALSCORE Module - DEVIS Types
 * Types partagés pour le module Devis
 */

import React from 'react';

// ============================================================
// ENUMS & STATUS
// ============================================================

export type DocumentStatus = 'DRAFT' | 'PENDING' | 'VALIDATED' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED';

export const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon?: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  PENDING: { label: 'En attente', color: 'orange' },
  VALIDATED: { label: 'Validé', color: 'blue' },
  SENT: { label: 'Envoyé', color: 'purple' },
  ACCEPTED: { label: 'Accepté', color: 'green' },
  REJECTED: { label: 'Refusé', color: 'red' },
  CANCELLED: { label: 'Annulé', color: 'gray' },
};

// ============================================================
// DATA TYPES
// ============================================================

export interface DocumentLine {
  id: string;
  line_number: number;
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

export interface Address {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
}

export interface Devis {
  id: string;
  number: string; // DEV-YY-MM-XXXX
  reference?: string;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  opportunity_id?: string;
  date: string;
  validity_date?: string;
  billing_address?: Address;
  shipping_address?: Address;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  lines: DocumentLine[];
  pdf_url?: string;
  assigned_to?: string;
  validated_by?: string;
  validated_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DevisFormData {
  customer_id: string;
  reference?: string;
  validity_date?: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
}

// ============================================================
// HISTORY & AUDIT
// ============================================================

export interface DevisHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  user_id?: string;
  old_value?: string;
  new_value?: string;
  details?: string;
}

// ============================================================
// DOCUMENTS
// ============================================================

export interface DevisDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url: string;
  size?: number;
  created_at: string;
  created_by?: string;
}

// ============================================================
// HELPERS
// ============================================================

export const formatCurrency = (value: number, currency = 'EUR'): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);

export const formatDate = (date: string): string =>
  new Date(date).toLocaleDateString('fr-FR');

export const formatDateTime = (date: string): string =>
  new Date(date).toLocaleString('fr-FR');
