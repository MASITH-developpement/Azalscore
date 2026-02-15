/**
 * AZALSCORE Module - Payments - Payment Documents Tab
 * Onglet documents lies au paiement
 */

import React from 'react';
import {
  FileText, Download, ExternalLink, Receipt, Mail, Printer
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Payment } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * PaymentDocumentsTab - Documents
 */
export const PaymentDocumentsTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const handleDownloadReceipt = async () => {
    try {
      const response = await fetch(`/api/v3/payments/${payment.id}/receipt`, {
        method: 'GET',
        headers: { 'Accept': 'application/pdf' }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `recu-${payment.reference}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch {
      // Fallback: Open print dialog
      window.print();
    }
  };

  const handleSendReceipt = async () => {
    if (!payment.customer_email) return;
    try {
      await fetch(`/api/v3/payments/${payment.id}/send-receipt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: payment.customer_email })
      });
      window.dispatchEvent(new CustomEvent('azals:toast', {
        detail: { type: 'success', message: 'Reçu envoyé par email' }
      }));
    } catch {
      window.dispatchEvent(new CustomEvent('azals:toast', {
        detail: { type: 'error', message: 'Erreur lors de l\'envoi' }
      }));
    }
  };

  const handleViewInvoice = () => {
    if (payment.invoice_id) {
      window.dispatchEvent(new CustomEvent('azals:navigate', {
        detail: { view: 'factures', params: { id: payment.invoice_id } }
      }));
    }
  };

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Recu de paiement */}
        <Card title="Recu de paiement" icon={<Receipt size={18} />}>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-center">
                <Receipt size={48} className="text-muted mx-auto mb-3" />
                <div className="font-medium">Recu #{payment.reference}</div>
                <div className="text-2xl font-bold text-primary mt-2">
                  {formatCurrency(payment.amount, payment.currency)}
                </div>
                <div className="text-sm text-muted mt-1">
                  {formatDate(payment.created_at)}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                leftIcon={<Download size={16} />}
                onClick={handleDownloadReceipt}
                className="flex-1"
              >
                Telecharger
              </Button>
              <Button
                variant="secondary"
                leftIcon={<Printer size={16} />}
                onClick={() => window.print()}
                className="flex-1"
              >
                Imprimer
              </Button>
            </div>
            {payment.customer_email && (
              <Button
                variant="ghost"
                leftIcon={<Mail size={16} />}
                onClick={handleSendReceipt}
                className="w-full"
              >
                Envoyer par email
              </Button>
            )}
          </div>
        </Card>

        {/* Facture liee */}
        <Card title="Facture associee" icon={<FileText size={18} />}>
          {payment.invoice_id ? (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <FileText size={48} className="text-primary mx-auto mb-3" />
                  <div className="font-medium">Facture {payment.invoice_number}</div>
                  <div className="text-sm text-muted mt-1">
                    Document lie a ce paiement
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  leftIcon={<ExternalLink size={16} />}
                  onClick={handleViewInvoice}
                  className="flex-1"
                >
                  Voir la facture
                </Button>
                <Button
                  variant="secondary"
                  leftIcon={<Download size={16} />}
                  className="flex-1"
                  onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'downloadInvoicePDF', invoiceId: payment.invoice_id } })); }}
                >
                  Telecharger PDF
                </Button>
              </div>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <FileText size={32} className="text-muted" />
              <p className="text-muted">Aucune facture associee</p>
              <p className="text-xs text-muted mt-1">
                Ce paiement n'est pas lie a une facture
              </p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Documents supplementaires (ERP only) */}
      <Card
        title="Documents supplementaires"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-empty azals-empty--sm">
          <FileText size={32} className="text-muted" />
          <p className="text-muted">Aucun document supplementaire</p>
          <Button variant="ghost" size="sm" className="mt-2" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addPaymentDocument', paymentId: payment.id } })); }}>
            Ajouter un document
          </Button>
        </div>
      </Card>

      {/* Informations d'envoi */}
      {payment.customer_email && (
        <Card
          title="Historique d'envoi"
          icon={<Mail size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <div className="text-sm text-muted">
            <p>Email du client: {payment.customer_email}</p>
            <p className="mt-2">Aucun envoi enregistre pour ce paiement.</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PaymentDocumentsTab;
