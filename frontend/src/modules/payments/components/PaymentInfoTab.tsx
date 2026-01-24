/**
 * AZALSCORE Module - Payments - Payment Info Tab
 * Onglet informations generales du paiement
 */

import React from 'react';
import {
  DollarSign, User, Mail, FileText, Calendar, CreditCard
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Payment } from '../types';
import {
  formatCurrency, formatDate, formatDateTime,
  getMethodLabel, getMethodIcon, getNetAmount, getRefundTotal,
  PAYMENT_STATUS_CONFIG
} from '../types';

/**
 * PaymentInfoTab - Informations generales
 */
export const PaymentInfoTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const statusConfig = PAYMENT_STATUS_CONFIG[payment.status];
  const netAmount = getNetAmount(payment);
  const refundTotal = getRefundTotal(payment);

  return (
    <div className="azals-std-tab-content">
      {/* Montant principal */}
      <Card className="mb-4">
        <div className="text-center py-4">
          <div className="text-sm text-muted mb-1">Montant du paiement</div>
          <div className="text-4xl font-bold text-primary">
            {formatCurrency(payment.amount, payment.currency)}
          </div>
          {refundTotal > 0 && (
            <div className="mt-2 text-sm">
              <span className="text-danger">-{formatCurrency(refundTotal, payment.currency)} rembourse</span>
              <span className="mx-2">|</span>
              <span className="text-success font-medium">Net: {formatCurrency(netAmount, payment.currency)}</span>
            </div>
          )}
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Informations de base */}
        <Card title="Informations de base" icon={<DollarSign size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <label>Reference</label>
              <div className="font-mono">{payment.reference}</div>
            </div>
            <div className="azals-std-field">
              <label>Methode de paiement</label>
              <div>
                <span className="mr-2">{getMethodIcon(payment.method)}</span>
                {getMethodLabel(payment.method)}
              </div>
            </div>
            <div className="azals-std-field">
              <label>Statut</label>
              <div className={`font-medium text-${statusConfig.color}`}>
                {statusConfig.label}
              </div>
            </div>
            {payment.description && (
              <div className="azals-std-field">
                <label>Description</label>
                <div className="text-muted">{payment.description}</div>
              </div>
            )}
          </div>
        </Card>

        {/* Client */}
        <Card title="Client" icon={<User size={18} />}>
          <div className="space-y-3">
            {payment.customer_name ? (
              <>
                <div className="azals-std-field">
                  <label>Nom</label>
                  <div className="font-medium">{payment.customer_name}</div>
                </div>
                {payment.customer_email && (
                  <div className="azals-std-field">
                    <label>Email</label>
                    <div className="flex items-center gap-2">
                      <Mail size={14} className="text-muted" />
                      {payment.customer_email}
                    </div>
                  </div>
                )}
                {payment.customer_id && (
                  <div className="azals-std-field azals-std-field--secondary">
                    <label>ID Client</label>
                    <div className="font-mono text-sm">{payment.customer_id}</div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-muted text-center py-4">
                Paiement sans client associe
              </div>
            )}
          </div>
        </Card>

        {/* Facture liee */}
        {payment.invoice_id && (
          <Card title="Facture liee" icon={<FileText size={18} />}>
            <div className="space-y-3">
              <div className="azals-std-field">
                <label>Numero de facture</label>
                <div className="font-mono">{payment.invoice_number || payment.invoice_id}</div>
              </div>
              <div className="azals-std-field azals-std-field--secondary">
                <label>ID Facture</label>
                <div className="font-mono text-sm">{payment.invoice_id}</div>
              </div>
            </div>
          </Card>
        )}

        {/* Dates */}
        <Card title="Dates" icon={<Calendar size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <label>Date de creation</label>
              <div>{formatDateTime(payment.created_at)}</div>
            </div>
            {payment.processed_at && (
              <div className="azals-std-field">
                <label>Date de traitement</label>
                <div>{formatDateTime(payment.processed_at)}</div>
              </div>
            )}
            {payment.updated_at && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Derniere modification</label>
                <div>{formatDateTime(payment.updated_at)}</div>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Message d'erreur si echoue */}
      {payment.error_message && (
        <Card className="mt-4 border-danger">
          <div className="flex items-start gap-3">
            <div className="text-danger mt-1">
              <CreditCard size={20} />
            </div>
            <div>
              <div className="font-medium text-danger">Erreur de paiement</div>
              <div className="text-muted mt-1">{payment.error_message}</div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PaymentInfoTab;
