/**
 * AZALSCORE Module - Invoicing - Info Tab
 * Onglet informations generales du document
 */

import React from 'react';
import {
  FileText, User, Calendar, Clock, CreditCard, MapPin, Mail, Phone
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Document } from '../types';
import {
  formatDate, formatCurrency, DOCUMENT_TYPE_CONFIG, DOCUMENT_STATUS_CONFIG,
  PAYMENT_TERMS, PAYMENT_METHODS
} from '../types';

/**
 * InvoicingInfoTab - Informations generales
 */
export const InvoicingInfoTab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const typeConfig = DOCUMENT_TYPE_CONFIG[doc.type];
  const statusConfig = DOCUMENT_STATUS_CONFIG[doc.status];

  const getPaymentTermLabel = (value?: string): string => {
    if (!value) return '-';
    return PAYMENT_TERMS.find(t => t.value === value)?.label || value;
  };

  const getPaymentMethodLabel = (value?: string): string => {
    if (!value) return '-';
    return PAYMENT_METHODS.find(m => m.value === value)?.label || value;
  };

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Informations du document" icon={<FileText size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Numero</label>
            <div className="azals-field__value font-medium">{doc.number}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Type</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${typeConfig.color}`}>
                {typeConfig.label}
              </span>
            </div>
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
            <label className="azals-field__label">Reference</label>
            <div className="azals-field__value">{doc.reference || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Client */}
      <Card title="Client" icon={<User size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Nom</label>
            <div className="azals-field__value font-medium">{doc.customer_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Email</label>
            <div className="azals-field__value">
              {doc.customer_email ? (
                <a href={`mailto:${doc.customer_email}`} className="azals-link flex items-center gap-1">
                  <Mail size={14} />
                  {doc.customer_email}
                </a>
              ) : '-'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Dates */}
      <Card title="Dates" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Date du document</label>
            <div className="azals-field__value">{formatDate(doc.date)}</div>
          </div>
          {doc.type === 'QUOTE' && (
            <div className="azals-field">
              <label className="azals-field__label">Date de validite</label>
              <div className="azals-field__value">
                {doc.validity_date ? formatDate(doc.validity_date) : '-'}
              </div>
            </div>
          )}
          {(doc.type === 'INVOICE' || doc.type === 'ORDER') && (
            <div className="azals-field">
              <label className="azals-field__label">Date d'echeance</label>
              <div className={`azals-field__value ${doc.is_overdue ? 'text-danger' : ''}`}>
                {doc.due_date ? formatDate(doc.due_date) : '-'}
                {doc.is_overdue && <span className="ml-2 text-danger">(En retard)</span>}
              </div>
            </div>
          )}
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDate(doc.created_at)}</div>
          </div>
        </Grid>
      </Card>

      {/* Conditions de paiement (ERP only) */}
      <Card
        title="Conditions de paiement"
        icon={<CreditCard size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Conditions</label>
            <div className="azals-field__value">{getPaymentTermLabel(doc.payment_terms)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Mode de paiement</label>
            <div className="azals-field__value">{getPaymentMethodLabel(doc.payment_method)}</div>
          </div>
        </Grid>
      </Card>

      {/* Notes */}
      {(doc.notes || doc.internal_notes) && (
        <Card title="Notes" icon={<FileText size={18} />} className="mt-4">
          {doc.notes && (
            <div className="azals-field mb-4">
              <label className="azals-field__label">Notes (visibles sur le document)</label>
              <div className="azals-field__value whitespace-pre-wrap">{doc.notes}</div>
            </div>
          )}
          {doc.internal_notes && (
            <div className="azals-field azals-std-field--secondary">
              <label className="azals-field__label">Notes internes</label>
              <div className="azals-field__value whitespace-pre-wrap text-muted">
                {doc.internal_notes}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Validation (si valide) */}
      {doc.validated_at && (
        <Card title="Validation" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Valide le</label>
              <div className="azals-field__value">{formatDate(doc.validated_at)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Valide par</label>
              <div className="azals-field__value">{doc.validated_by_name || '-'}</div>
            </div>
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default InvoicingInfoTab;
