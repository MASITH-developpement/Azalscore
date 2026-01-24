/**
 * AZALSCORE Module - Purchases - Invoice Info Tab
 * Onglet informations generales de la facture fournisseur
 */

import React from 'react';
import { FileText, Building2, Calendar, Tag, AlertTriangle } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseInvoice } from '../types';
import { INVOICE_STATUS_CONFIG, formatDate, formatDateTime, isOverdue, getDaysUntilDue } from '../types';

/**
 * InvoiceInfoTab - Informations generales
 */
export const InvoiceInfoTab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const statusConfig = INVOICE_STATUS_CONFIG[invoice.status];
  const overdue = isOverdue(invoice.due_date);
  const daysUntilDue = getDaysUntilDue(invoice.due_date);

  return (
    <div className="azals-std-tab-content">
      {/* Alerte echeance */}
      {overdue && invoice.status !== 'PAID' && invoice.status !== 'CANCELLED' && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={18} />
          <span>Cette facture est en retard de paiement !</span>
        </div>
      )}

      {/* Informations principales */}
      <Card title="Identification" icon={<FileText size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Numero</label>
            <div className="azals-field__value font-mono font-medium">{invoice.number}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Reference fournisseur</label>
            <div className="azals-field__value">{invoice.supplier_reference || '-'}</div>
          </div>
          {invoice.order_number && (
            <div className="azals-field">
              <label className="azals-field__label">Commande liee</label>
              <div className="azals-field__value font-mono text-primary">{invoice.order_number}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Fournisseur */}
      <Card title="Fournisseur" icon={<Building2 size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Code</label>
            <div className="azals-field__value font-mono">{invoice.supplier_code}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom</label>
            <div className="azals-field__value font-medium">{invoice.supplier_name}</div>
          </div>
        </Grid>
      </Card>

      {/* Dates */}
      <Card title="Dates" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Date de facture</label>
            <div className="azals-field__value">{formatDate(invoice.date)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Date d'echeance</label>
            <div className="azals-field__value">
              {invoice.due_date ? (
                <span className={overdue ? 'text-danger font-medium' : ''}>
                  {formatDate(invoice.due_date)}
                  {overdue && <AlertTriangle size={14} className="inline ml-1" />}
                  {!overdue && daysUntilDue !== null && daysUntilDue <= 7 && (
                    <span className="text-warning text-sm ml-1">({daysUntilDue} jours)</span>
                  )}
                </span>
              ) : (
                '-'
              )}
            </div>
          </div>
          {invoice.validated_at && (
            <div className="azals-field">
              <label className="azals-field__label">Validee le</label>
              <div className="azals-field__value">{formatDateTime(invoice.validated_at)}</div>
            </div>
          )}
          {invoice.paid_at && (
            <div className="azals-field">
              <label className="azals-field__label">Payee le</label>
              <div className="azals-field__value">{formatDateTime(invoice.paid_at)}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Notes */}
      {invoice.notes && (
        <Card title="Notes" icon={<Tag size={18} />} className="mt-4">
          <p className="text-muted whitespace-pre-wrap">{invoice.notes}</p>
        </Card>
      )}

      {/* Metadata (ERP only) */}
      <Card title="Metadata" className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDateTime(invoice.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{invoice.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifie le</label>
            <div className="azals-field__value">{formatDateTime(invoice.updated_at)}</div>
          </div>
          {invoice.validated_by_name && (
            <div className="azals-field">
              <label className="azals-field__label">Valide par</label>
              <div className="azals-field__value">{invoice.validated_by_name}</div>
            </div>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default InvoiceInfoTab;
