/**
 * AZALSCORE Module - COMMANDES - Types partagés
 * Types, interfaces et constantes pour le module Commandes
 */

import React from 'react';
import { Edit, Clock, Check, Truck, FileText, X } from 'lucide-react';

// ============================================================
// TYPES DE BASE
// ============================================================

export type DocumentStatus = 'DRAFT' | 'PENDING' | 'VALIDATED' | 'DELIVERED' | 'INVOICED' | 'CANCELLED';

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

export interface Commande {
  id: string;
  number: string; // COM-YY-MM-XXXX
  reference?: string;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  parent_id?: string; // ID du devis source
  parent_number?: string;
  date: string;
  delivery_date?: string;
  delivered_at?: string;
  billing_address?: Address;
  shipping_address?: Address;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  shipping_method?: string;
  shipping_cost: number;
  tracking_number?: string;
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

export interface Address {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
}

export interface CommandeDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url: string;
  size?: number;
  created_at: string;
}

export interface CommandeHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface CommandeFormData {
  customer_id: string;
  reference?: string;
  delivery_date?: string;
  shipping_method?: string;
  shipping_cost?: number;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
}

// ============================================================
// CONFIGURATION DES STATUTS
// ============================================================

export const STATUS_CONFIG: Record<DocumentStatus, {
  label: string;
  color: string;
  icon: React.ReactNode;
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    icon: React.createElement(Edit, { size: 14 }),
    description: 'Commande en cours de création',
  },
  PENDING: {
    label: 'En attente',
    color: 'yellow',
    icon: React.createElement(Clock, { size: 14 }),
    description: 'En attente de validation',
  },
  VALIDATED: {
    label: 'Validée',
    color: 'blue',
    icon: React.createElement(Check, { size: 14 }),
    description: 'Commande validée, prête pour traitement',
  },
  DELIVERED: {
    label: 'Livrée',
    color: 'green',
    icon: React.createElement(Truck, { size: 14 }),
    description: 'Commande livrée au client',
  },
  INVOICED: {
    label: 'Facturée',
    color: 'purple',
    icon: React.createElement(FileText, { size: 14 }),
    description: 'Commande facturée',
  },
  CANCELLED: {
    label: 'Annulée',
    color: 'red',
    icon: React.createElement(X, { size: 14 }),
    description: 'Commande annulée',
  },
};

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

export const formatAddress = (address?: Address): string => {
  if (!address) return '';
  const parts = [
    address.line1,
    address.line2,
    [address.postal_code, address.city].filter(Boolean).join(' '),
    address.country,
  ].filter(Boolean);
  return parts.join(', ');
};
