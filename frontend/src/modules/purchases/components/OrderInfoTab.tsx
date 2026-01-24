/**
 * AZALSCORE Module - Purchases - Order Info Tab
 * Onglet informations generales de la commande
 */

import React from 'react';
import { FileText, Building2, Calendar, Tag } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseOrder } from '../types';
import { ORDER_STATUS_CONFIG, formatDate, formatDateTime } from '../types';

/**
 * OrderInfoTab - Informations generales
 */
export const OrderInfoTab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
  const statusConfig = ORDER_STATUS_CONFIG[order.status];

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Identification" icon={<FileText size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Numero</label>
            <div className="azals-field__value font-mono font-medium">{order.number}</div>
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
            <div className="azals-field__value">{order.reference || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Fournisseur */}
      <Card title="Fournisseur" icon={<Building2 size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Code</label>
            <div className="azals-field__value font-mono">{order.supplier_code}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom</label>
            <div className="azals-field__value font-medium">{order.supplier_name}</div>
          </div>
        </Grid>
      </Card>

      {/* Dates */}
      <Card title="Dates" icon={<Calendar size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Date de commande</label>
            <div className="azals-field__value">{formatDate(order.date)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Livraison prevue</label>
            <div className="azals-field__value">
              {order.expected_date ? formatDate(order.expected_date) : '-'}
            </div>
          </div>
          {order.validated_at && (
            <div className="azals-field">
              <label className="azals-field__label">Validee le</label>
              <div className="azals-field__value">{formatDateTime(order.validated_at)}</div>
            </div>
          )}
          {order.sent_at && (
            <div className="azals-field">
              <label className="azals-field__label">Envoyee le</label>
              <div className="azals-field__value">{formatDateTime(order.sent_at)}</div>
            </div>
          )}
          {order.confirmed_at && (
            <div className="azals-field">
              <label className="azals-field__label">Confirmee le</label>
              <div className="azals-field__value">{formatDateTime(order.confirmed_at)}</div>
            </div>
          )}
          {order.received_at && (
            <div className="azals-field">
              <label className="azals-field__label">Recue le</label>
              <div className="azals-field__value">{formatDateTime(order.received_at)}</div>
            </div>
          )}
        </Grid>
      </Card>

      {/* Notes */}
      {order.notes && (
        <Card title="Notes" icon={<Tag size={18} />} className="mt-4">
          <p className="text-muted whitespace-pre-wrap">{order.notes}</p>
        </Card>
      )}

      {/* Metadata (ERP only) */}
      <Card title="Metadata" className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDateTime(order.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{order.created_by_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifie le</label>
            <div className="azals-field__value">{formatDateTime(order.updated_at)}</div>
          </div>
          {order.validated_by_name && (
            <div className="azals-field">
              <label className="azals-field__label">Valide par</label>
              <div className="azals-field__value">{order.validated_by_name}</div>
            </div>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default OrderInfoTab;
