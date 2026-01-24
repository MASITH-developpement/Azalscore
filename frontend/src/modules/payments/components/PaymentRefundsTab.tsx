/**
 * AZALSCORE Module - Payments - Payment Refunds Tab
 * Onglet remboursements du paiement
 */

import React, { useState } from 'react';
import {
  RotateCcw, Plus, Clock, CheckCircle, XCircle, AlertCircle
} from 'lucide-react';
import { Card } from '@ui/layout';
import { Button, Modal } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Payment, Refund } from '../types';
import {
  formatCurrency, formatDateTime,
  getRefundTotal, canRefund,
  REFUND_STATUS_CONFIG
} from '../types';

/**
 * PaymentRefundsTab - Remboursements
 */
export const PaymentRefundsTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const [showRefundModal, setShowRefundModal] = useState(false);
  const refunds = payment.refunds || [];
  const refundTotal = getRefundTotal(payment);
  const remainingAmount = payment.amount - refundTotal;
  const canCreateRefund = canRefund(payment) && remainingAmount > 0;

  return (
    <div className="azals-std-tab-content">
      {/* Resume des remboursements */}
      <Card className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted">Remboursements effectues</div>
            <div className="text-2xl font-bold text-danger">
              {formatCurrency(refundTotal, payment.currency)}
            </div>
            <div className="text-sm text-muted mt-1">
              sur {formatCurrency(payment.amount, payment.currency)}
              {remainingAmount > 0 && (
                <span className="ml-2">
                  (reste {formatCurrency(remainingAmount, payment.currency)})
                </span>
              )}
            </div>
          </div>
          {canCreateRefund && (
            <Button
              variant="secondary"
              leftIcon={<Plus size={16} />}
              onClick={() => setShowRefundModal(true)}
            >
              Nouveau remboursement
            </Button>
          )}
        </div>
      </Card>

      {/* Liste des remboursements */}
      <Card title="Historique des remboursements" icon={<RotateCcw size={18} />}>
        {refunds.length > 0 ? (
          <div className="space-y-3">
            {refunds.map((refund) => (
              <RefundItem key={refund.id} refund={refund} currency={payment.currency} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <RotateCcw size={32} className="text-muted" />
            <p className="text-muted">Aucun remboursement pour ce paiement</p>
          </div>
        )}
      </Card>

      {/* Modal de remboursement */}
      {showRefundModal && (
        <Modal
          isOpen={true}
          onClose={() => setShowRefundModal(false)}
          title="Nouveau remboursement"
        >
          <form onSubmit={(e) => {
            e.preventDefault();
            // TODO: Implement refund creation
            setShowRefundModal(false);
          }}>
            <div className="space-y-4">
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Montant a rembourser</label>
                <input
                  type="number"
                  name="amount"
                  defaultValue={remainingAmount}
                  max={remainingAmount}
                  step="0.01"
                  required
                  className="azals-input"
                />
                <div className="text-sm text-muted mt-1">
                  Maximum: {formatCurrency(remainingAmount, payment.currency)}
                </div>
              </div>
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Raison du remboursement</label>
                <textarea
                  name="reason"
                  placeholder="Expliquez la raison du remboursement..."
                  className="azals-input"
                  rows={4}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={() => setShowRefundModal(false)}>
                  Annuler
                </Button>
                <Button type="submit" variant="danger">
                  Rembourser
                </Button>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

/**
 * Composant pour afficher un remboursement
 */
interface RefundItemProps {
  refund: Refund;
  currency: string;
}

const RefundItem: React.FC<RefundItemProps> = ({ refund, currency }) => {
  const statusConfig = REFUND_STATUS_CONFIG[refund.status];

  const getStatusIcon = () => {
    switch (refund.status) {
      case 'COMPLETED':
        return <CheckCircle size={20} className="text-success" />;
      case 'FAILED':
        return <XCircle size={20} className="text-danger" />;
      case 'PROCESSING':
        return <Clock size={20} className="text-blue-500" />;
      default:
        return <AlertCircle size={20} className="text-warning" />;
    }
  };

  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="mt-1">{getStatusIcon()}</div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <div className="font-medium">
            {formatCurrency(refund.amount, currency)}
          </div>
          <span className={`azals-badge azals-badge--${statusConfig.color}`}>
            {statusConfig.label}
          </span>
        </div>
        <div className="text-sm text-muted mt-1">{refund.reason}</div>
        <div className="text-xs text-muted mt-2">
          Demande le {formatDateTime(refund.created_at)}
          {refund.processed_at && (
            <span> • Traite le {formatDateTime(refund.processed_at)}</span>
          )}
        </div>
        {refund.processed_by && (
          <div className="text-xs text-muted azals-std-field--secondary">
            Par: {refund.processed_by}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentRefundsTab;
