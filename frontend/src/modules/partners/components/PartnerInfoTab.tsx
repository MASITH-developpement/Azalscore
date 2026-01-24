/**
 * AZALSCORE Module - Partners - Info Tab
 * Onglet informations generales du partenaire
 */

import React from 'react';
import {
  User, Mail, Phone, MapPin, Building, Globe, Tag, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Partner, Client } from '../types';
import {
  formatDate, formatDateTime, formatCurrency,
  getFullAddress, getPartnerAge,
  CLIENT_TYPE_CONFIG
} from '../types';

/**
 * PartnerInfoTab - Informations generales
 */
export const PartnerInfoTab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const isClient = partner.type === 'client';
  const client = partner as Client;

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Identite */}
        <Card title="Identite" icon={<User size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <label>Nom / Raison sociale</label>
              <div className="font-medium text-lg">{partner.name}</div>
            </div>
            {partner.code && (
              <div className="azals-std-field">
                <label>Code</label>
                <div className="font-mono">{partner.code}</div>
              </div>
            )}
            {isClient && client.client_type && (
              <div className="azals-std-field">
                <label>Type de client</label>
                <div className={`font-medium text-${CLIENT_TYPE_CONFIG[client.client_type]?.color || 'gray'}`}>
                  {CLIENT_TYPE_CONFIG[client.client_type]?.label || client.client_type}
                </div>
              </div>
            )}
            <div className="azals-std-field">
              <label>Statut</label>
              <div className={`font-medium ${partner.is_active ? 'text-success' : 'text-muted'}`}>
                {partner.is_active ? 'Actif' : 'Inactif'}
              </div>
            </div>
            {partner.industry && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Secteur d'activite</label>
                <div>{partner.industry}</div>
              </div>
            )}
          </div>
        </Card>

        {/* Coordonnees */}
        <Card title="Coordonnees" icon={<Phone size={18} />}>
          <div className="space-y-3">
            {partner.email && (
              <div className="azals-std-field">
                <label>Email</label>
                <div className="flex items-center gap-2">
                  <Mail size={14} className="text-muted" />
                  <a href={`mailto:${partner.email}`} className="text-primary hover:underline">
                    {partner.email}
                  </a>
                </div>
              </div>
            )}
            {partner.phone && (
              <div className="azals-std-field">
                <label>Telephone</label>
                <div className="flex items-center gap-2">
                  <Phone size={14} className="text-muted" />
                  <a href={`tel:${partner.phone}`} className="text-primary hover:underline">
                    {partner.phone}
                  </a>
                </div>
              </div>
            )}
            {partner.mobile && (
              <div className="azals-std-field">
                <label>Mobile</label>
                <div className="flex items-center gap-2">
                  <Phone size={14} className="text-muted" />
                  {partner.mobile}
                </div>
              </div>
            )}
            {partner.website && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Site web</label>
                <div className="flex items-center gap-2">
                  <Globe size={14} className="text-muted" />
                  <a href={partner.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    {partner.website}
                  </a>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Adresse */}
        <Card title="Adresse" icon={<MapPin size={18} />}>
          <div className="space-y-3">
            {(partner.address_line1 || partner.address) && (
              <div className="azals-std-field">
                <label>Adresse</label>
                <div>{partner.address_line1 || partner.address}</div>
                {partner.address_line2 && <div>{partner.address_line2}</div>}
              </div>
            )}
            <div className="azals-std-field">
              <label>Ville</label>
              <div>
                {partner.postal_code && <span>{partner.postal_code} </span>}
                {partner.city || '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <label>Pays</label>
              <div>{partner.country || partner.country_code || 'France'}</div>
            </div>
            {getFullAddress(partner) && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Adresse complete</label>
                <div className="text-sm text-muted">{getFullAddress(partner)}</div>
              </div>
            )}
          </div>
        </Card>

        {/* Informations fiscales */}
        <Card title="Informations fiscales" icon={<Building size={18} />}>
          <div className="space-y-3">
            {(partner.vat_number || partner.tax_id) && (
              <div className="azals-std-field">
                <label>N TVA / SIRET</label>
                <div className="font-mono">{partner.vat_number || partner.tax_id}</div>
              </div>
            )}
            {isClient && client.payment_terms !== undefined && (
              <div className="azals-std-field">
                <label>Delai de paiement</label>
                <div>{client.payment_terms} jours</div>
              </div>
            )}
            {isClient && client.credit_limit !== undefined && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Limite de credit</label>
                <div>{formatCurrency(client.credit_limit, client.currency)}</div>
              </div>
            )}
            {isClient && client.discount_rate !== undefined && client.discount_rate > 0 && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Remise standard</label>
                <div>{client.discount_rate}%</div>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Dates et tags */}
      <Grid cols={2} gap="lg" className="mt-4">
        <Card title="Dates" icon={<Calendar size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <label>Date de creation</label>
              <div>{formatDateTime(partner.created_at)}</div>
            </div>
            <div className="azals-std-field">
              <label>Anciennete</label>
              <div>{getPartnerAge(partner)}</div>
            </div>
            {partner.updated_at && (
              <div className="azals-std-field azals-std-field--secondary">
                <label>Derniere modification</label>
                <div>{formatDateTime(partner.updated_at)}</div>
              </div>
            )}
            {isClient && client.first_order_date && (
              <div className="azals-std-field">
                <label>Premiere commande</label>
                <div>{formatDate(client.first_order_date)}</div>
              </div>
            )}
            {isClient && client.last_order_date && (
              <div className="azals-std-field">
                <label>Derniere commande</label>
                <div>{formatDate(client.last_order_date)}</div>
              </div>
            )}
          </div>
        </Card>

        {/* Tags et notes */}
        <Card title="Tags et notes" icon={<Tag size={18} />} className="azals-std-field--secondary">
          <div className="space-y-3">
            {partner.tags && partner.tags.length > 0 && (
              <div className="azals-std-field">
                <label>Tags</label>
                <div className="flex flex-wrap gap-1">
                  {partner.tags.map((tag, index) => (
                    <span key={index} className="azals-badge azals-badge--blue">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {partner.source && (
              <div className="azals-std-field">
                <label>Source</label>
                <div>{partner.source}</div>
              </div>
            )}
            {partner.assigned_to_name && (
              <div className="azals-std-field">
                <label>Responsable</label>
                <div>{partner.assigned_to_name}</div>
              </div>
            )}
            {partner.notes && (
              <div className="azals-std-field">
                <label>Notes</label>
                <div className="text-sm text-muted whitespace-pre-wrap">{partner.notes}</div>
              </div>
            )}
          </div>
        </Card>
      </Grid>
    </div>
  );
};

export default PartnerInfoTab;
