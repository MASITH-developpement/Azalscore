/**
 * AZALSCORE Module - Partners - Info Tab
 * Onglet informations generales du partenaire
 */

import React from 'react';
import {
  User, Mail, Phone, MapPin, Building, Globe, Tag, Calendar
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatDateTime, formatCurrency } from '@/utils/formatters';
import {
  getFullAddress, getPartnerAge,
  CLIENT_TYPE_CONFIG
} from '../types';
import type { Partner, Client } from '../types';
import type { TabContentProps } from '@ui/standards';

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
              <span>Nom / Raison sociale</span>
              <div className="font-medium text-lg">{partner.name}</div>
            </div>
            {partner.code && (
              <div className="azals-std-field">
                <span>Code</span>
                <div className="font-mono">{partner.code}</div>
              </div>
            )}
            {isClient && client.client_type && (
              <div className="azals-std-field">
                <span>Type de client</span>
                <div className={`font-medium text-${CLIENT_TYPE_CONFIG[client.client_type]?.color || 'gray'}`}>
                  {CLIENT_TYPE_CONFIG[client.client_type]?.label || client.client_type}
                </div>
              </div>
            )}
            <div className="azals-std-field">
              <span>Statut</span>
              <div className={`font-medium ${partner.is_active ? 'text-success' : 'text-muted'}`}>
                {partner.is_active ? 'Actif' : 'Inactif'}
              </div>
            </div>
            {partner.industry && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Secteur d&apos;activite</span>
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
                <span>Email</span>
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
                <span>Telephone</span>
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
                <span>Mobile</span>
                <div className="flex items-center gap-2">
                  <Phone size={14} className="text-muted" />
                  {partner.mobile}
                </div>
              </div>
            )}
            {partner.website && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Site web</span>
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
                <span>Adresse</span>
                <div>{partner.address_line1 || partner.address}</div>
                {partner.address_line2 && <div>{partner.address_line2}</div>}
              </div>
            )}
            <div className="azals-std-field">
              <span>Ville</span>
              <div>
                {partner.postal_code && <span>{partner.postal_code} </span>}
                {partner.city || '-'}
              </div>
            </div>
            <div className="azals-std-field">
              <span>Pays</span>
              <div>{partner.country || partner.country_code || 'France'}</div>
            </div>
            {getFullAddress(partner) && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Adresse complete</span>
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
                <span>N TVA / SIRET</span>
                <div className="font-mono">{partner.vat_number || partner.tax_id}</div>
              </div>
            )}
            {isClient && client.payment_terms !== undefined && (
              <div className="azals-std-field">
                <span>Delai de paiement</span>
                <div>{client.payment_terms} jours</div>
              </div>
            )}
            {isClient && client.credit_limit !== undefined && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Limite de credit</span>
                <div>{formatCurrency(client.credit_limit, client.currency)}</div>
              </div>
            )}
            {isClient && client.discount_rate !== undefined && client.discount_rate > 0 && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Remise standard</span>
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
              <span>Date de creation</span>
              <div>{formatDateTime(partner.created_at)}</div>
            </div>
            <div className="azals-std-field">
              <span>Anciennete</span>
              <div>{getPartnerAge(partner)}</div>
            </div>
            {partner.updated_at && (
              <div className="azals-std-field azals-std-field--secondary">
                <span>Derniere modification</span>
                <div>{formatDateTime(partner.updated_at)}</div>
              </div>
            )}
            {isClient && client.first_order_date && (
              <div className="azals-std-field">
                <span>Premiere commande</span>
                <div>{formatDate(client.first_order_date)}</div>
              </div>
            )}
            {isClient && client.last_order_date && (
              <div className="azals-std-field">
                <span>Derniere commande</span>
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
                <span>Tags</span>
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
                <span>Source</span>
                <div>{partner.source}</div>
              </div>
            )}
            {partner.assigned_to_name && (
              <div className="azals-std-field">
                <span>Responsable</span>
                <div>{partner.assigned_to_name}</div>
              </div>
            )}
            {partner.notes && (
              <div className="azals-std-field">
                <span>Notes</span>
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
