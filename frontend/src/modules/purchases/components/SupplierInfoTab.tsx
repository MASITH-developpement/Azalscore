/**
 * AZALSCORE Module - Purchases - Supplier Info Tab
 * Onglet informations generales du fournisseur
 */

import React from 'react';
import { Building2, Mail, Phone, MapPin, CreditCard, FileText } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import { SUPPLIER_STATUS_CONFIG, getPaymentTermsLabel } from '../types';
import type { Supplier } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * SupplierInfoTab - Informations generales
 */
export const SupplierInfoTab: React.FC<TabContentProps<Supplier>> = ({ data: supplier }) => {
  const statusConfig = SUPPLIER_STATUS_CONFIG[supplier.status];

  return (
    <div className="azals-std-tab-content">
      {/* Informations principales */}
      <Card title="Identification" icon={<Building2 size={18} />}>
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Code</span>
            <div className="azals-field__value font-mono">{supplier.code}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Nom</span>
            <div className="azals-field__value font-medium">{supplier.name}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Statut</span>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Contact principal</span>
            <div className="azals-field__value">{supplier.contact_name || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Contact */}
      <Card title="Contact" icon={<Mail size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">
              <Mail size={14} className="inline mr-1" />
              Email
            </span>
            <div className="azals-field__value">
              {supplier.email ? (
                <a href={`mailto:${supplier.email}`} className="text-primary hover:underline">
                  {supplier.email}
                </a>
              ) : (
                '-'
              )}
            </div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">
              <Phone size={14} className="inline mr-1" />
              Telephone
            </span>
            <div className="azals-field__value">
              {supplier.phone ? (
                <a href={`tel:${supplier.phone}`} className="text-primary hover:underline">
                  {supplier.phone}
                </a>
              ) : (
                '-'
              )}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Adresse */}
      <Card title="Adresse" icon={<MapPin size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field" style={{ gridColumn: 'span 2' }}>
            <span className="azals-field__label">Adresse</span>
            <div className="azals-field__value">{supplier.address || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Code postal</span>
            <div className="azals-field__value">{supplier.postal_code || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Ville</span>
            <div className="azals-field__value">{supplier.city || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Pays</span>
            <div className="azals-field__value">{supplier.country || '-'}</div>
          </div>
        </Grid>
      </Card>

      {/* Informations fiscales et paiement */}
      <Card title="Informations fiscales" icon={<CreditCard size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">N° TVA / SIRET</span>
            <div className="azals-field__value font-mono">{supplier.tax_id || '-'}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Conditions de paiement</span>
            <div className="azals-field__value">{getPaymentTermsLabel(supplier.payment_terms)}</div>
          </div>
        </Grid>
      </Card>

      {/* Notes */}
      {supplier.notes && (
        <Card title="Notes" icon={<FileText size={18} />} className="mt-4">
          <p className="text-muted whitespace-pre-wrap">{supplier.notes}</p>
        </Card>
      )}

      {/* Metadata (ERP only) */}
      <Card title="Metadata" className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <span className="azals-field__label">Cree le</span>
            <div className="azals-field__value">{formatDate(supplier.created_at)}</div>
          </div>
          <div className="azals-field">
            <span className="azals-field__label">Modifie le</span>
            <div className="azals-field__value">{formatDate(supplier.updated_at)}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default SupplierInfoTab;
