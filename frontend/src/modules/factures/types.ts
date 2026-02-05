/**
 * AZALSCORE Module - FACTURES - Types partagés
 * Types, interfaces et constantes pour le module Factures & Avoirs
 */

import React from 'react';
import { Edit, Check, Send, CheckCircle2, Clock, AlertTriangle, Ban } from 'lucide-react';

// ============================================================
// TYPES DE BASE
// ============================================================

export type FactureType = 'INVOICE' | 'CREDIT_NOTE';
export type FactureStatus = 'DRAFT' | 'VALIDATED' | 'SENT' | 'PAID' | 'PARTIAL' | 'OVERDUE' | 'CANCELLED';
export type PaymentMethod = 'BANK_TRANSFER' | 'CHECK' | 'CREDIT_CARD' | 'CASH' | 'DIRECT_DEBIT' | 'OTHER';

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

export interface Payment {
  id: string;
  reference?: string;
  method: PaymentMethod;
  amount: number;
  date: string;
  notes?: string;
  created_at?: string;
  created_by?: string;
}

export interface Address {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
}

export interface Facture {
  id: string;
  type: FactureType;
  number: string; // FAC-YY-MM-XXXX ou AVO-YY-MM-XXXX
  reference?: string;
  status: FactureStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  parent_id?: string; // Commande ou intervention source
  parent_number?: string;
  parent_type?: 'ORDER' | 'INTERVENTION';
  date: string;
  due_date?: string;
  billing_address?: Address;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  paid_amount: number;
  remaining_amount: number;
  lines: DocumentLine[];
  payments?: Payment[];
  notes?: string;
  internal_notes?: string;
  terms?: string;
  pdf_url?: string;
  validated_by?: string;
  validated_at?: string;
  sent_at?: string;
  paid_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
}

export interface FactureDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'other';
  url: string;
  size?: number;
  created_at: string;
}

export interface FactureHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface FactureFormData {
  customer_id: string;
  type: FactureType;
  reference?: string;
  due_date?: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
}

export interface PaymentFormData {
  method: PaymentMethod;
  amount: number;
  date: string;
  reference?: string;
  notes?: string;
}

// ============================================================
// CONFIGURATION DES TYPES
// ============================================================

export const TYPE_CONFIG: Record<FactureType, {
  label: string;
  prefix: string;
  color: string;
  description: string;
}> = {
  INVOICE: {
    label: 'Facture',
    prefix: 'FAC',
    color: 'blue',
    description: 'Facture client standard',
  },
  CREDIT_NOTE: {
    label: 'Avoir',
    prefix: 'AVO',
    color: 'orange',
    description: 'Avoir / Note de crédit',
  },
};

// ============================================================
// CONFIGURATION DES STATUTS
// ============================================================

export const STATUS_CONFIG: Record<FactureStatus, {
  label: string;
  color: string;
  icon: React.ReactNode;
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    icon: React.createElement(Edit, { size: 14 }),
    description: 'En cours de création',
  },
  VALIDATED: {
    label: 'Validée',
    color: 'blue',
    icon: React.createElement(Check, { size: 14 }),
    description: 'Validée, prête à envoyer',
  },
  SENT: {
    label: 'Envoyée',
    color: 'purple',
    icon: React.createElement(Send, { size: 14 }),
    description: 'Envoyée au client',
  },
  PAID: {
    label: 'Payée',
    color: 'green',
    icon: React.createElement(CheckCircle2, { size: 14 }),
    description: 'Entièrement payée',
  },
  PARTIAL: {
    label: 'Partielle',
    color: 'yellow',
    icon: React.createElement(Clock, { size: 14 }),
    description: 'Partiellement payée',
  },
  OVERDUE: {
    label: 'En retard',
    color: 'red',
    icon: React.createElement(AlertTriangle, { size: 14 }),
    description: 'Échéance dépassée',
  },
  CANCELLED: {
    label: 'Annulée',
    color: 'gray',
    icon: React.createElement(Ban, { size: 14 }),
    description: 'Annulée',
  },
};

// ============================================================
// MÉTHODES DE PAIEMENT
// ============================================================

export const PAYMENT_METHODS: Record<PaymentMethod, {
  label: string;
  icon?: string;
}> = {
  BANK_TRANSFER: { label: 'Virement bancaire' },
  CHECK: { label: 'Chèque' },
  CREDIT_CARD: { label: 'Carte bancaire' },
  CASH: { label: 'Espèces' },
  DIRECT_DEBIT: { label: 'Prélèvement' },
  OTHER: { label: 'Autre' },
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

export const getDaysUntilDue = (dueDate?: string): number | null => {
  if (!dueDate) return null;
  const due = new Date(dueDate);
  const now = new Date();
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

export const isOverdue = (facture: Facture): boolean => {
  if (!facture.due_date) return false;
  if (['PAID', 'CANCELLED'].includes(facture.status)) return false;
  return new Date(facture.due_date) < new Date();
};
