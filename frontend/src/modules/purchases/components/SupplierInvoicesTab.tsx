/**
 * AZALSCORE Module - Purchases - Supplier Invoices Tab
 * Onglet factures du fournisseur
 */

import React from 'react';
import { FileText, ExternalLink, AlertTriangle } from 'lucide-react';
import { Card } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Supplier, PurchaseInvoice } from '../types';
import { INVOICE_STATUS_CONFIG, isOverdue, getDaysUntilDue } from '../types';
import { formatCurrency, formatDate } from '@/utils/formatters';

/**
 * SupplierInvoicesTab - Factures du fournisseur
 */
export const SupplierInvoicesTab: React.FC<TabContentProps<Supplier & { invoices?: PurchaseInvoice[] }>> = ({ data }) => {
  const invoices = data.invoices || [];
  const pendingInvoices = invoices.filter((i) => i.status === 'VALIDATED' || i.status === 'PARTIAL');
  const overdueInvoices = pendingInvoices.filter((i) => isOverdue(i.due_date));

  return (
    <div className="azals-std-tab-content">
      {/* Alerte factures en retard */}
      {overdueInvoices.length > 0 && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <span>
            {overdueInvoices.length} facture(s) en retard de paiement pour un total de{' '}
            {formatCurrency(overdueInvoices.reduce((sum, i) => sum + (i.amount_remaining || i.total_ttc), 0))}
          </span>
        </div>
      )}

      <Card
        title="Factures"
        icon={<FileText size={18} />}
        actions={
          <Button variant="secondary" size="sm" leftIcon={<FileText size={14} />}>
            Nouvelle facture
          </Button>
        }
      >
        {invoices.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>N°</th>
                <th>Ref. fournisseur</th>
                <th>Date</th>
                <th>Echeance</th>
                <th>Statut</th>
                <th className="text-right">Total TTC</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => {
                const statusConfig = INVOICE_STATUS_CONFIG[invoice.status];
                const overdue = isOverdue(invoice.due_date);
                const daysUntilDue = getDaysUntilDue(invoice.due_date);

                return (
                  <tr key={invoice.id} className={overdue ? 'bg-red-50' : ''}>
                    <td className="font-mono">{invoice.number}</td>
                    <td className="text-muted">{invoice.supplier_reference || '-'}</td>
                    <td>{formatDate(invoice.date)}</td>
                    <td>
                      {invoice.due_date ? (
                        <span className={overdue ? 'text-danger font-medium' : ''}>
                          {formatDate(invoice.due_date)}
                          {overdue && <AlertTriangle size={12} className="inline ml-1" />}
                          {!overdue && daysUntilDue !== null && daysUntilDue <= 7 && (
                            <span className="text-warning text-xs ml-1">({daysUntilDue}j)</span>
                          )}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="text-right font-medium">
                      {formatCurrency(invoice.total_ttc, invoice.currency)}
                    </td>
                    <td className="text-right">
                      <Button variant="ghost" size="sm" leftIcon={<ExternalLink size={14} />}>
                        Voir
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <FileText size={32} className="text-muted" />
            <p className="text-muted">Aucune facture pour ce fournisseur</p>
          </div>
        )}
      </Card>

      {/* Statistiques (ERP only) */}
      <Card title="Statistiques factures" className="mt-4 azals-std-field--secondary">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-2xl font-bold">{invoices.length}</div>
            <div className="text-sm text-muted">Total factures</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">{pendingInvoices.length}</div>
            <div className="text-sm text-muted">A payer</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">{overdueInvoices.length}</div>
            <div className="text-sm text-muted">En retard</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(invoices.filter((i) => i.status === 'PAID').reduce((sum, i) => sum + i.total_ttc, 0))}
            </div>
            <div className="text-sm text-muted">Total paye</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SupplierInvoicesTab;
