/**
 * AZALSCORE Module - COMMANDES - Info Tab
 * Onglet informations générales de la commande
 */

import React from 'react';
import {
  Building2, MapPin, FileText, Calendar, User, Truck,
  Package, Hash, Mail, Phone
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Commande } from '../types';
import { formatAddress, STATUS_CONFIG } from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * CommandeInfoTab - Informations générales de la commande
 */
export const CommandeInfoTab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  return (
    <div className="azals-std-tab-content">
      {/* Lien avec le devis source */}
      {commande.parent_number && (
        <div className="azals-alert azals-alert--info mb-4">
          <FileText size={20} />
          <div>
            <strong>Issue du devis</strong>
            <p className="text-muted">{commande.parent_number}</p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations client */}
        <Card title="Client" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            <dt><Building2 size={14} /> Raison sociale</dt>
            <dd><strong>{commande.customer_name}</strong></dd>

            {commande.customer_code && (
              <>
                <dt className="azals-std-field--secondary"><Hash size={14} /> Code client</dt>
                <dd className="azals-std-field--secondary">{commande.customer_code}</dd>
              </>
            )}

            {commande.billing_address && (
              <>
                <dt><MapPin size={14} /> Adresse de facturation</dt>
                <dd>
                  {commande.billing_address.line1 && <div>{commande.billing_address.line1}</div>}
                  {commande.billing_address.line2 && <div>{commande.billing_address.line2}</div>}
                  <div>
                    {commande.billing_address.postal_code} {commande.billing_address.city}
                  </div>
                  {commande.billing_address.country && <div>{commande.billing_address.country}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        {/* Informations livraison */}
        <Card title="Livraison" icon={<Truck size={18} />}>
          <dl className="azals-dl">
            {commande.delivery_date && (
              <>
                <dt><Calendar size={14} /> Date de livraison prévue</dt>
                <dd>{formatDate(commande.delivery_date)}</dd>
              </>
            )}

            {commande.delivered_at && (
              <>
                <dt><Calendar size={14} /> Livré le</dt>
                <dd className="text-success">{formatDate(commande.delivered_at)}</dd>
              </>
            )}

            {commande.shipping_method && (
              <>
                <dt><Truck size={14} /> Mode de livraison</dt>
                <dd>{commande.shipping_method}</dd>
              </>
            )}

            {commande.tracking_number && (
              <>
                <dt><Package size={14} /> N° de suivi</dt>
                <dd>
                  <code className="azals-code">{commande.tracking_number}</code>
                </dd>
              </>
            )}

            {commande.shipping_address && (
              <>
                <dt><MapPin size={14} /> Adresse de livraison</dt>
                <dd>
                  {commande.shipping_address.line1 && <div>{commande.shipping_address.line1}</div>}
                  {commande.shipping_address.line2 && <div>{commande.shipping_address.line2}</div>}
                  <div>
                    {commande.shipping_address.postal_code} {commande.shipping_address.city}
                  </div>
                  {commande.shipping_address.country && <div>{commande.shipping_address.country}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>
      </Grid>

      {/* Informations document */}
      <Card title="Informations document" icon={<FileText size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-info-block">
            <span className="azals-info-block__label">Référence client</span>
            <span className="azals-info-block__value">{commande.reference || '-'}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Date de commande</span>
            <span className="azals-info-block__value">{formatDate(commande.date)}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Statut</span>
            <span className={`azals-badge azals-badge--${STATUS_CONFIG[commande.status].color}`}>
              {STATUS_CONFIG[commande.status].icon}
              <span className="ml-1">{STATUS_CONFIG[commande.status].label}</span>
            </span>
          </div>
        </Grid>
      </Card>

      {/* Notes */}
      {(commande.notes || commande.internal_notes || commande.terms) && (
        <Card title="Notes et conditions" icon={<FileText size={18} />} className="mt-4">
          <Grid cols={2} gap="md">
            {commande.notes && (
              <div className="azals-note-block">
                <h4>Notes</h4>
                <p>{commande.notes}</p>
              </div>
            )}

            {commande.terms && (
              <div className="azals-note-block">
                <h4>Conditions</h4>
                <p>{commande.terms}</p>
              </div>
            )}

            {commande.internal_notes && (
              <div className="azals-note-block azals-std-field--secondary">
                <h4>Notes internes</h4>
                <p className="text-muted">{commande.internal_notes}</p>
              </div>
            )}
          </Grid>
        </Card>
      )}

      {/* Métadonnées (ERP only) */}
      <Card
        title="Métadonnées"
        icon={<User size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-info-block">
            <span className="azals-info-block__label">Créé par</span>
            <span className="azals-info-block__value">{commande.created_by || 'Système'}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Créé le</span>
            <span className="azals-info-block__value">{formatDate(commande.created_at)}</span>
          </div>

          {commande.validated_by && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Validé par</span>
              <span className="azals-info-block__value">{commande.validated_by}</span>
            </div>
          )}

          {commande.validated_at && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Validé le</span>
              <span className="azals-info-block__value">{formatDate(commande.validated_at)}</span>
            </div>
          )}

          {commande.assigned_to && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Assigné à</span>
              <span className="azals-info-block__value">{commande.assigned_to}</span>
            </div>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default CommandeInfoTab;
