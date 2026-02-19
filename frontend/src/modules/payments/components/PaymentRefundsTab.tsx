/**
 * AZALSCORE Module - Payments - Payment Refunds Tab
 * Onglet remboursements du paiement
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RotateCcw, Plus, Clock, CheckCircle, XCircle, AlertCircle, Loader2
} from 'lucide-react';
import { api } from '@core/api-client';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { formatCurrency, formatDateTime } from '@/utils/formatters';
import {
  getRefundTotal, canRefund,
  REFUND_STATUS_CONFIG
} from '../types';
import type { Payment, Refund } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PaymentRefundsTab - Remboursements
 */
export const PaymentRefundsTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const [showRefundModal, setShowRefundModal] = useState(false);
  const queryClient = useQueryClient();
  const refunds = payment.refunds || [];
  const refundTotal = getRefundTotal(payment);
  const remainingAmount = payment.amount - refundTotal;
  const canCreateRefund = canRefund(payment) && remainingAmount > 0;

  const createRefund = useMutation({
    mutationFn: async (data: { amount: number; reason: string }) => {
      return api.post(`/payments/${payment.id}/refunds`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', payment.id] });
      setShowRefundModal(false);
      window.dispatchEvent(new CustomEvent('azals:toast', {
        detail: { type: 'success', message: 'Demande de remboursement créée' }
      }));
    },
    onError: () => {
      window.dispatchEvent(new CustomEvent('azals:toast', {
        detail: { type: 'error', message: 'Erreur lors de la création du remboursement' }
      }));
    }
  });

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
            const formData = new FormData(e.currentTarget);
            createRefund.mutate({
              amount: parseFloat(formData.get('amount') as string),
              reason: formData.get('reason') as string
            });
          }}>
            <div className="space-y-4">
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1" htmlFor="refund-amount">Montant a rembourser</label>
                <input
                  id="refund-amount"
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
                <label className="block text-sm font-medium mb-1" htmlFor="refund-reason">Raison du remboursement</label>
                <textarea
                  id="refund-reason"
                  name="reason"
                  placeholder="Expliquez la raison du remboursement..."
                  className="azals-input"
                  rows={4}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={() => setShowRefundModal(false)} disabled={createRefund.isPending}>
                  Annuler
                </Button>
                <Button type="submit" variant="danger" disabled={createRefund.isPending}>
                  {createRefund.isPending ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
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
