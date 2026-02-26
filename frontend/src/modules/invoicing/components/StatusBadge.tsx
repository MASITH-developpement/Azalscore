/**
 * AZALSCORE Module - Invoicing - StatusBadge
 * Badge de statut pour les documents
 */

import React from 'react';
import { Clock, CheckCircle2 } from 'lucide-react';
import type { DocumentStatus } from '../types';

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', icon: <Clock size={14} /> },
  PENDING: { label: 'En attente', color: 'yellow', icon: <Clock size={14} /> },
  VALIDATED: { label: 'Valide', color: 'green', icon: <CheckCircle2 size={14} /> },
  SENT: { label: 'Envoye', color: 'purple', icon: <CheckCircle2 size={14} /> },
  ACCEPTED: { label: 'Accepte', color: 'cyan', icon: <CheckCircle2 size={14} /> },
  REJECTED: { label: 'Rejete', color: 'red', icon: <Clock size={14} /> },
  DELIVERED: { label: 'Livre', color: 'blue', icon: <CheckCircle2 size={14} /> },
  INVOICED: { label: 'Facture', color: 'orange', icon: <CheckCircle2 size={14} /> },
  PAID: { label: 'Paye', color: 'green', icon: <CheckCircle2 size={14} /> },
  CANCELLED: { label: 'Annule', color: 'red', icon: <Clock size={14} /> },
};

interface StatusBadgeProps {
  status: DocumentStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'gray', icon: null };

  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

export default StatusBadge;
