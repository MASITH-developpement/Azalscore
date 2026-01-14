/**
 * AZALSCORE - Module Documents Unifié
 * Badge de statut universel
 */

import React, { memo } from 'react';
import { Clock, CheckCircle2, Send, DollarSign, XCircle, Package, FileText } from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { STATUS_CONFIG, PARTNER_STATUS_CONFIG } from '../constants';
import type { DocumentStatus, PartnerStatus } from '../types';

// ============================================================
// ICÔNES PAR STATUT
// ============================================================

const STATUS_ICONS: Record<string, React.ReactNode> = {
  DRAFT: <Clock size={14} />,
  VALIDATED: <CheckCircle2 size={14} />,
  SENT: <Send size={14} />,
  CONFIRMED: <CheckCircle2 size={14} />,
  PARTIAL: <Package size={14} />,
  RECEIVED: <Package size={14} />,
  INVOICED: <FileText size={14} />,
  PAID: <DollarSign size={14} />,
  CANCELLED: <XCircle size={14} />,
};

// ============================================================
// COMPOSANT - DocumentStatusBadge
// ============================================================

interface DocumentStatusBadgeProps {
  status: DocumentStatus;
}

export const DocumentStatusBadge: React.FC<DocumentStatusBadgeProps> = memo(({ status }) => {
  const { t } = useTranslation();
  const config = STATUS_CONFIG[status];

  if (!config) {
    return <span className="azals-badge azals-badge--gray">{status}</span>;
  }

  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {STATUS_ICONS[status]}
      <span className="ml-1">{t(config.labelKey)}</span>
    </span>
  );
});

DocumentStatusBadge.displayName = 'DocumentStatusBadge';

// ============================================================
// COMPOSANT - PartnerStatusBadge
// ============================================================

interface PartnerStatusBadgeProps {
  status: PartnerStatus;
}

export const PartnerStatusBadge: React.FC<PartnerStatusBadgeProps> = memo(({ status }) => {
  const { t } = useTranslation();
  const config = PARTNER_STATUS_CONFIG[status];

  if (!config) {
    return <span className="azals-badge azals-badge--gray">{status}</span>;
  }

  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {t(config.labelKey)}
    </span>
  );
});

PartnerStatusBadge.displayName = 'PartnerStatusBadge';

// ============================================================
// EXPORTS
// ============================================================

export default DocumentStatusBadge;
