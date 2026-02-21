/**
 * AZALSCORE Module - DEVIS - Info Tab
 * Onglet informations générales du devis
 */

import React from 'react';
import { Building2, MapPin, Calendar, FileText, Tag } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import type { Devis } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * DevisInfoTab - Affichage des informations générales du devis
 */
export const DevisInfoTab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Client */}
        <Card title="Client" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt><Building2 size={14} /> Raison sociale</dt>
              <dd>
                <strong>{devis.customer_name}</strong>
                {devis.customer_code && (
                  <span className="text-muted"> ({devis.customer_code})</span>
                )}
              </dd>
            </div>

            {devis.billing_address && (
              <div className="azals-dl__row">
                <dt><MapPin size={14} /> Adresse facturation</dt>
                <dd>
                  {devis.billing_address.line1 && <div>{devis.billing_address.line1}</div>}
                  {devis.billing_address.line2 && <div>{devis.billing_address.line2}</div>}
                  {(devis.billing_address.postal_code || devis.billing_address.city) && (
                    <div>
                      {devis.billing_address.postal_code} {devis.billing_address.city}
                    </div>
                  )}
                  {devis.billing_address.country && <div>{devis.billing_address.country}</div>}
                </dd>
              </div>
            )}

            {devis.shipping_address && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt><MapPin size={14} /> Adresse livraison</dt>
                <dd>
                  {devis.shipping_address.line1 && <div>{devis.shipping_address.line1}</div>}
                  {devis.shipping_address.line2 && <div>{devis.shipping_address.line2}</div>}
                  {(devis.shipping_address.postal_code || devis.shipping_address.city) && (
                    <div>
                      {devis.shipping_address.postal_code} {devis.shipping_address.city}
                    </div>
                  )}
                </dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Informations document */}
        <Card title="Informations" icon={<FileText size={18} />}>
          <dl className="azals-dl">
            <div className="azals-dl__row">
              <dt><Calendar size={14} /> Date du devis</dt>
              <dd>{formatDate(devis.date)}</dd>
            </div>

            {devis.validity_date && (
              <div className="azals-dl__row">
                <dt><Calendar size={14} /> Date de validité</dt>
                <dd>
                  {formatDate(devis.validity_date)}
                  {new Date(devis.validity_date) < new Date() && (
                    <span className="azals-badge azals-badge--red ml-2">Expiré</span>
                  )}
                </dd>
              </div>
            )}

            {devis.reference && (
              <div className="azals-dl__row">
                <dt><Tag size={14} /> Référence client</dt>
                <dd>{devis.reference}</dd>
              </div>
            )}

            {devis.opportunity_id && (
              <div className="azals-dl__row azals-std-field--secondary">
                <dt>Opportunité CRM</dt>
                <dd>
                  <a href={`/crm/opportunities/${devis.opportunity_id}`} className="azals-link">
                    Voir l&apos;opportunité
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Notes */}
        {devis.notes && (
          <Card title="Notes" icon={<FileText size={18} />}>
            <p className="azals-text-content">{devis.notes}</p>
          </Card>
        )}

        {/* Conditions */}
        {devis.terms && (
          <Card title="Conditions" icon={<FileText size={18} />}>
            <p className="azals-text-content">{devis.terms}</p>
          </Card>
        )}

        {/* Notes internes (ERP only) */}
        {devis.internal_notes && (
          <Card
            title="Notes internes"
            icon={<FileText size={18} />}
            className="azals-std-field--secondary"
          >
            <p className="azals-text-content text-muted">{devis.internal_notes}</p>
          </Card>
        )}

        {/* Métadonnées (ERP only) */}
        <Card title="Métadonnées" className="azals-std-field--secondary">
          <dl className="azals-dl azals-dl--compact">
            <div className="azals-dl__row">
              <dt>Créé le</dt>
              <dd>{formatDate(devis.created_at)}</dd>
            </div>
            {devis.created_by && (
              <div className="azals-dl__row">
                <dt>Créé par</dt>
                <dd>{devis.created_by}</dd>
              </div>
            )}
            <div className="azals-dl__row">
              <dt>Modifié le</dt>
              <dd>{formatDate(devis.updated_at)}</dd>
            </div>
            {devis.validated_at && (
              <div className="azals-dl__row">
                <dt>Validé le</dt>
                <dd>{formatDate(devis.validated_at)}</dd>
              </div>
            )}
            {devis.validated_by && (
              <div className="azals-dl__row">
                <dt>Validé par</dt>
                <dd>{devis.validated_by}</dd>
              </div>
            )}
            {devis.assigned_to && (
              <div className="azals-dl__row">
                <dt>Assigné à</dt>
                <dd>{devis.assigned_to}</dd>
              </div>
            )}
          </dl>
        </Card>
      </Grid>
    </div>
  );
};

export default DevisInfoTab;
