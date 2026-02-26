/**
 * AZALSCORE Module - Purchases - Status Badges
 * =============================================
 * Composants de badges de statut pour les achats
 */

import React from 'react';
import {
  ORDER_STATUS_CONFIG,
  INVOICE_STATUS_CONFIG,
  SUPPLIER_STATUS_CONFIG,
} from '../types';

// ============================================================================
// Order Status Badge
// ============================================================================

interface OrderStatusBadgeProps {
  status: string;
}

export const OrderStatusBadge: React.FC<OrderStatusBadgeProps> = ({ status }) => {
  const config = ORDER_STATUS_CONFIG[status as keyof typeof ORDER_STATUS_CONFIG] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

// ============================================================================
// Invoice Status Badge
// ============================================================================

interface InvoiceStatusBadgeProps {
  status: string;
}

export const InvoiceStatusBadge: React.FC<InvoiceStatusBadgeProps> = ({ status }) => {
  const config = INVOICE_STATUS_CONFIG[status as keyof typeof INVOICE_STATUS_CONFIG] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

// ============================================================================
// Supplier Status Badge
// ============================================================================

interface SupplierStatusBadgeProps {
  status: string;
}

export const SupplierStatusBadge: React.FC<SupplierStatusBadgeProps> = ({ status }) => {
  const config = SUPPLIER_STATUS_CONFIG[status as keyof typeof SUPPLIER_STATUS_CONFIG] || { label: status, color: 'gray' };
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};
